"""Prueba ciega única del control de alcance v2. NO ejecutar sin autorización expresa.

Comprueba que el código, los pesos, la cabeza y el umbral coinciden con los congelados en
results/scope_v2/protocol_blind.json; se niega a correr si ya existe un resultado ciego.
Usa la misma ruta de la aplicación: carga validada, U-Net, recorte de la pieza y cabeza v2.
Regla de adopción (fijada antes de abrir la carpeta): ver el protocolo.

  python scripts/evaluate_scope_blind_v2.py --blind "C:\\ruta\\02_prueba_ciega_negativos_v2_NO_ABRIR" --root "C:\\ruta\\datos" --autorizado
"""
from pathlib import Path
import argparse, csv, hashlib, json, sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'results/scope_v2'
PROTOCOL = OUT / 'protocol_blind.json'


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--blind', required=True); ap.add_argument('--root', required=True)
    ap.add_argument('--autorizado', action='store_true', help='Confirmación de que el equipo autorizó la única ejecución')
    args = ap.parse_args()
    if not args.autorizado:
        raise SystemExit('La prueba ciega solo se ejecuta una vez y con autorización expresa (--autorizado).')
    if (OUT / 'blind.json').exists():
        raise SystemExit('La prueba ciega ya se ejecutó: no se repite ni se reajusta sobre ella.')
    protocol = json.loads(PROTOCOL.read_text(encoding='utf-8'))
    changed = [f for f, h in protocol['congelado_sha256'].items() if sha256(ROOT / f) != h]
    if changed:
        raise SystemExit('Cambió algo congelado desde el protocolo: ' + ', '.join(changed))
    import numpy as np
    from PIL import Image, ImageOps
    from palimpsesto.imaging import load_image, MAX_PIXELS
    from palimpsesto.models import ModelService

    def load_dev(path):
        # Enmienda 1: mismo cargador que scripts/develop_scope_v2.py (sin el límite de 40 MP de la app).
        with Image.open(path) as im:
            big = im.width * im.height > MAX_PIXELS
            return np.asarray(ImageOps.exif_transpose(im).convert('RGB')), big
    Image.MAX_IMAGE_PIXELS = None
    ms = ModelService(ROOT / 'models'); assert ms.scope_head is not None and ms.segmenter is not None
    blind = Path(args.blind); rows = []
    manifest = blind / 'manifest.csv'
    entries = ([(r.get('label') or Path(r['final_path']).parent.name, blind / r['final_path'], r.get('image_id', Path(r['final_path']).stem))
                for r in csv.DictReader(open(manifest, encoding='utf-8-sig'))] if manifest.exists()
               else [(p.parent.name, p, p.stem) for p in sorted(blind.glob('*/*')) if p.suffix.lower() in ('.jpg', '.jpeg', '.png')])
    for label, path, image_id in entries:
        rgb, big = load_dev(path); prob = ms.segment(rgb); s = ms.scope_screen(rgb, prob)
        rows.append({'image_id': image_id, 'label': label, 'alertada': bool(s['flagged']), 'p_valida': round(s['valid_probability'], 4),
                     'supera_40MP_de_la_app': big, 'sha256': sha256(path)})
    # Regresión positiva: 72 fotos de diagnóstico (reutilizadas), misma ruta de la app.
    pos = [r for r in csv.DictReader(open(ROOT / 'data/manifest.csv', encoding='utf-8-sig')) if r['split'] == 'test']; accepted = 0
    for r in pos:
        rgb, _ = load_image((Path(args.root) / r['path'].replace(chr(92), '/')).read_bytes())
        accepted += not ms.scope_screen(rgb, ms.segment(rgb))['flagged']
    labels = sorted({r['label'] for r in rows}); rule = protocol['regla_prueba_ciega']
    per = {l: sum(r['alertada'] for r in rows if r['label'] == l) for l in labels}; n = {l: sum(r['label'] == l for r in rows) for l in labels}
    total = sum(per.values()); pos_acc = accepted / len(pos)
    checks = {'total': total >= rule['negativos_alertados_min'], 'por_grupo': all(per[l] >= rule['alertados_por_grupo_min'] for l in labels),
              'regresion_positiva': pos_acc >= rule['aceptacion_positiva_min']}
    result = {'imagenes': len(rows), 'alertadas': f'{total}/{len(rows)}', 'por_grupo': {l: f'{per[l]}/{n[l]}' for l in labels},
              'regresion_positiva_72': f'{accepted}/{len(pos)}', 'aceptacion_positiva': round(pos_acc, 4), 'comprobaciones': checks,
              'decision': 'adoptar' if all(checks.values()) else 'no_adoptar', 'regla': rule, 'unica_ejecucion': True,
              'imagenes_que_la_app_rechazaria_por_tamano': sum(r['supera_40MP_de_la_app'] for r in rows),
              'enmienda': protocol.get('enmienda_1', {}).get('resumen')}
    (OUT / 'blind.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    with open(OUT / 'blind_per_image.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, list(rows[0]), lineterminator='\n'); w.writeheader(); w.writerows(rows)
    print(json.dumps(result, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
