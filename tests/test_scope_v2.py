"""Control de alcance v2: recorte de la pieza y regresión logística sobre sus rasgos."""
import io, hashlib
from pathlib import Path
import numpy as np, pytest, torch
from palimpsesto import server
from palimpsesto.models import ModelService, piece_crop
from palimpsesto.imaging import encode_png

ROOT = Path(__file__).resolve().parents[1]


def test_piece_crop_follows_the_mask():
    rgb = np.zeros((400, 800, 3), np.uint8); prob = np.zeros((256, 256), np.float32); prob[64:192, 32:96] = 1
    crop = piece_crop(rgb, prob)
    assert abs(crop.shape[0] - 400 * 128 / 256 * 1.1) < 8 and abs(crop.shape[1] - 800 * 64 / 256 * 1.1) < 8
    assert piece_crop(rgb, None) is rgb and piece_crop(rgb, np.zeros((256, 256), np.float32)) is rgb


def service(z):
    """ModelService mínimo: rasgos constantes y una cabeza cuya salida logit es z."""
    ms = ModelService.__new__(ModelService)
    ms.encoder = lambda x: torch.ones(1, 512, 1, 1); ms.info = {'image_size': 32, 'mean': [0, 0, 0], 'std': [1, 1, 1]}
    f = np.ones(512, np.float32) / np.sqrt(512)
    ms.scope_head = {'coef': np.zeros(512, np.float32), 'intercept': z, 'threshold': .5}
    return ms


def test_head_flags_low_valid_probability():
    rgb = np.full((300, 300, 3), 128, np.uint8); prob = np.ones((256, 256), np.float32)
    assert service(-3.).scope_screen(rgb, prob)['flagged'] is True
    ok = service(3.).scope_screen(rgb, prob)
    assert ok['flagged'] is False and ok['available'] and ok['valid_probability'] > .9


def test_falls_back_without_head_or_mask():
    rgb = np.full((300, 300, 3), 128, np.uint8); previous = {'available': True, 'flagged': True, 'method': 'anterior'}
    ms = service(3.); ms.scope_head = None
    assert ms.scope_screen(rgb, np.ones((256, 256), np.float32), previous) is previous
    assert service(3.).scope_screen(rgb, None, previous) is previous


def test_server_uses_scope_v2_for_the_confirmation():
    class Stub:
        def classify(self, rgb): return {'class': 'pintura', 'available': True, 'scores': dict(documento_impreso=.1, manuscrito=.1, pintura=.8), 'scope': {'available': True, 'flagged': False}}
        def segment(self, rgb): return np.ones((256, 256), np.float32)
        def scope_screen(self, rgb, prob, previous=None): return {'available': True, 'flagged': True, 'method': 'v2'}
    server.app.config['TESTING'] = True; server.models = Stub(); c = server.app.test_client()
    img = np.random.default_rng(1).integers(0, 255, (300, 300, 3), dtype=np.uint8)
    r = c.post('/api/upload', data={'image': (io.BytesIO(encode_png(img)), 'x.png')})
    assert r.status_code == 200 and r.json['assessment']['requires_confirmation']
    assert c.post('/api/detect', json={'kind': 'pintura', 'scope_confirmed': False}).status_code == 400
    assert c.post('/api/detect', json={'kind': 'pintura', 'scope_confirmed': True}).status_code == 200


@pytest.mark.skipif(not (ROOT / 'models/classifier.pt').exists(), reason='requiere los pesos de la release')
def test_published_head_matches_the_classifier():
    with np.load(ROOT / 'models/scope_head.npz', allow_pickle=False) as h:
        assert str(h['classifier_sha256']) == hashlib.sha256((ROOT / 'models/classifier.pt').read_bytes()).hexdigest()
    assert ModelService(ROOT / 'models').scope_head is not None
