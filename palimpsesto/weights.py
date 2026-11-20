"""Pesos de la versión vigente: comprobación por SHA-256 y descarga desde la release.

`models/checksums.json` dice qué bytes exactos espera el código y
`models/release.json` de dónde bajarlos. Si falta un archivo o es de otra versión,
se descarga el ZIP público de la release, se comprueba su SHA-256 y solo entonces
se reemplazan los archivos, uno a uno y también verificados. Sin conexión no se
borra nada: la aplicación arranca con lo que haya y avisa.
"""
from pathlib import Path
import hashlib, json, shutil, sys, urllib.request, zipfile

REQUIRED = ('classifier.pt', 'unet_resnet18_3clases.pth', 'scope_reference.npz')


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def outdated(directory, manifest_dir=None, names=REQUIRED):
    """Archivos que faltan o no coinciden con checksums.json."""
    directory = Path(directory); checks = json.loads((Path(manifest_dir or directory) / 'checksums.json').read_text(encoding='utf-8'))
    return [n for n in names if not (directory / n).exists() or sha256(directory / n) != checks[n]['sha256']]


def _download(url, target, log):
    part = target.with_suffix(target.suffix + '.part')
    with urllib.request.urlopen(url, timeout=60) as response, open(part, 'wb') as out:
        total = int(response.headers.get('Content-Length') or 0); done = 0; shown = -1
        while block := response.read(1 << 20):
            out.write(block); done += len(block)
            if total and (pct := done * 100 // total) // 10 != shown:
                shown = pct // 10; log(f'  {pct} % ({done >> 20} de {total >> 20} MB)')
    part.replace(target)


def ensure_models(directory, manifest_dir=None, names=REQUIRED, log=print):
    """Deja en `directory` los pesos que pide el código. Devuelve los archivos instalados."""
    directory = Path(directory); manifest = Path(manifest_dir or directory)
    missing = outdated(directory, manifest, names)
    if not missing:
        return []
    release = json.loads((manifest / 'release.json').read_text(encoding='utf-8'))
    checks = json.loads((manifest / 'checksums.json').read_text(encoding='utf-8'))
    cache = directory / '.download_cache'; cache.mkdir(parents=True, exist_ok=True)
    archive = cache / release['asset']
    if not archive.exists() or sha256(archive) != release['sha256']:
        log(f"Descargando los pesos {release['version']} ({release['bytes'] >> 20} MB) para: {', '.join(missing)}")
        _download(release['url'], archive, log)
        if sha256(archive) != release['sha256']:
            archive.unlink(missing_ok=True)
            raise RuntimeError('El ZIP descargado no coincide con su SHA-256; no se instaló nada.')
    installed = []
    with zipfile.ZipFile(archive) as z:
        for name in missing:
            temporary = directory / (name + '.part')
            with z.open(f'models/{name}') as src, open(temporary, 'wb') as dst:
                shutil.copyfileobj(src, dst, 1 << 20)
            if sha256(temporary) != checks[name]['sha256']:
                temporary.unlink(missing_ok=True)
                raise RuntimeError(f'{name} no coincide con models/checksums.json; no se instaló.')
            temporary.replace(directory / name); installed.append(name)
    log(f"Pesos {release['version']} listos: {', '.join(installed)}")
    return installed


def main():
    """python scripts/fetch_models.py [carpeta_destino] [carpeta_con_checksums]"""
    root = Path(__file__).resolve().parents[1]
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else root / 'models'
    manifest = Path(sys.argv[2]) if len(sys.argv) > 2 else target
    try:
        installed = ensure_models(target, manifest)
    except Exception as error:
        print('No se pudieron preparar los pesos:', error); return 1
    if not installed:
        print('Los pesos ya están al día.')
    return 0
