"""Pesos de la versión vigente: descarga verificada desde una release simulada en disco."""
import hashlib, json, zipfile
import pytest
from palimpsesto.weights import ensure_models, outdated, REQUIRED


def fake_release(tmp_path, corrupt_zip=False):
    files = {name: f'pesos de prueba {name}'.encode() for name in REQUIRED}
    manifest = tmp_path / 'manifest'; manifest.mkdir()
    archive = tmp_path / 'modelos.zip'
    with zipfile.ZipFile(archive, 'w') as z:
        for name, data in files.items():
            z.writestr(f'models/{name}', data)
    checks = {n: {'bytes': len(d), 'sha256': hashlib.sha256(d).hexdigest()} for n, d in files.items()}
    (manifest / 'checksums.json').write_text(json.dumps(checks), encoding='utf-8')
    zip_sha = '0' * 64 if corrupt_zip else hashlib.sha256(archive.read_bytes()).hexdigest()
    release = {'version': 'vtest', 'asset': 'modelos.zip', 'url': archive.as_uri(), 'bytes': archive.stat().st_size, 'sha256': zip_sha}
    (manifest / 'release.json').write_text(json.dumps(release), encoding='utf-8')
    return manifest, files


def test_missing_weights_are_downloaded_and_verified(tmp_path):
    manifest, files = fake_release(tmp_path); target = tmp_path / 'models'; target.mkdir()
    assert sorted(ensure_models(target, manifest, log=lambda *_: None)) == sorted(REQUIRED)
    assert all((target / n).read_bytes() == d for n, d in files.items())
    assert outdated(target, manifest) == [] and ensure_models(target, manifest, log=lambda *_: None) == []


def test_old_version_is_replaced(tmp_path):
    manifest, files = fake_release(tmp_path); target = tmp_path / 'models'; target.mkdir()
    for n in REQUIRED:
        (target / n).write_bytes(files[n])
    (target / 'unet_resnet18_3clases.pth').write_bytes(b'pesos de la version anterior')
    assert ensure_models(target, manifest, log=lambda *_: None) == ['unet_resnet18_3clases.pth']
    assert (target / 'unet_resnet18_3clases.pth').read_bytes() == files['unet_resnet18_3clases.pth']


def test_corrupt_download_installs_nothing(tmp_path):
    manifest, _ = fake_release(tmp_path, corrupt_zip=True); target = tmp_path / 'models'; target.mkdir()
    (target / 'classifier.pt').write_bytes(b'lo que habia')
    with pytest.raises(RuntimeError):
        ensure_models(target, manifest, log=lambda *_: None)
    assert (target / 'classifier.pt').read_bytes() == b'lo que habia'
    assert not (target / 'unet_resnet18_3clases.pth').exists()
