"""Histograma y tonos recortados por el ajuste (paso 4)."""
import io
import numpy as np
from PIL import Image
from palimpsesto import server
from palimpsesto.imaging import compare_metrics, clipping_overlay, descriptors, encode_png, HIST_BINS, PRESETS


def gradient():
    """Rampa de grises sin negro ni blanco puros."""
    g = np.tile(np.linspace(20, 235, 400, dtype=np.float32), (300, 1)).astype(np.uint8)
    return np.repeat(g[:, :, None], 3, axis=2)


def test_histogram_is_a_distribution():
    h = descriptors(gradient())['histogram']
    assert len(h) == HIST_BINS and abs(sum(h) - 1) < 1e-3 and h[0] == 0 and h[-1] == 0


def test_no_adjustment_clips_nothing():
    m = compare_metrics(gradient(), gradient())['clipping']
    assert m['available'] and m['new_bright_percent'] == 0 and m['new_dark_percent'] == 0 and not m['warning']


def test_burnt_highlights_are_counted_and_warned():
    before = gradient(); after = before.copy(); after[:, -60:] = 255  # 15 % de la imagen llevado a blanco puro
    m = compare_metrics(before, after)['clipping']
    assert 14 < m['new_bright_percent'] < 16 and m['warning']
    a = np.asarray(Image.open(io.BytesIO(clipping_overlay(before, after))))
    assert a[150, -10, 3] > 0 and a[150, 10, 3] == 0  # solo se marca la zona recortada


def test_pixels_already_white_before_do_not_count():
    before = gradient(); before[:, -60:] = 255; after = before.copy()
    assert compare_metrics(before, after)['clipping']['new_bright_percent'] == 0


def test_binarization_is_reported_as_intended():
    m = compare_metrics(gradient(), gradient(), binary=True)['clipping']
    assert m['available'] is False and 'a propósito' in m['note']


def test_api_returns_tones_and_clipping_image():
    class Stub:
        def classify(self, rgb): return {'class': 'documento_impreso', 'available': True, 'scores': dict(documento_impreso=.9, manuscrito=.05, pintura=.05)}
        def segment(self, rgb): return None
    server.app.config['TESTING'] = True; server.models = Stub(); c = server.app.test_client()
    assert c.post('/api/upload', data={'image': (io.BytesIO(encode_png(gradient())), 'g.png')}).status_code == 200
    assert c.get('/api/image/clipping').status_code == 400  # todavía no hay resultado
    q = [[.02, .02], [.98, .02], [.98, .98], [.02, .98]]
    r = c.post('/api/process', json={'kind': 'documento_impreso', 'points': q, 'aspect': 0, 'parameters': PRESETS['documento_impreso']})
    assert r.status_code == 200 and len(r.json['metrics']['after']['histogram']) == HIST_BINS and r.json['metrics']['clipping']['available']
    img = c.get('/api/image/clipping?v=' + r.json['revision']); assert img.status_code == 200 and Image.open(io.BytesIO(img.data)).mode == 'RGBA'
    assert c.get('/api/image/clipping?v=viejo').status_code == 400
