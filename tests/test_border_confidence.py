"""Confianza del borde de la U-Net y máscara superpuesta en el paso 3."""
import io
import numpy as np, cv2
from PIL import Image
from palimpsesto import server
from palimpsesto.imaging import border_confidence, detect_quad, encode_png, mask_overlay


def photo():
    rgb = np.full((600, 800, 3), (70, 55, 45), np.uint8); rgb[100:500, 150:650] = 230
    return rgb


def rect_prob(blur=0):
    p = np.zeros((256, 256), np.float32); p[43:213, 48:208] = 1  # misma pieza que photo(), a 256 px
    return cv2.GaussianBlur(p, (0, 0), blur) if blur else p


class Seg:
    def __init__(self, prob): self.prob = prob
    def classify(self, rgb): return {'class': 'documento_impreso', 'available': True, 'scores': dict(documento_impreso=.9, manuscrito=.05, pintura=.05)}
    def segment(self, rgb): return self.prob


def test_clean_rectangle_is_confident():
    r = detect_quad(photo(), Seg(rect_prob()), 'documento_impreso', 'unet')
    assert r['method'] == 'unet' and r['confidence']['level'] == 'segura' and r['confidence']['fit'] > .95


def test_fuzzy_contour_is_doubtful():
    c = detect_quad(photo(), Seg(rect_prob(blur=8)), 'documento_impreso', 'unet')['confidence']
    assert c['level'] == 'dudosa' and c['band'] > 5 and any('difuso' in x for x in c['reasons'])


def test_points_that_do_not_fit_the_mask_are_doubtful():
    p = rect_prob(); q = np.array([[.2, .2], [.8, .2], [.8, .55], [.2, .55]], np.float32)  # solo media pieza
    c = border_confidence(p, q, (600, 800))
    assert c['level'] == 'dudosa' and c['fit'] < .92


def test_contours_and_manual_have_no_confidence():
    assert detect_quad(photo(), Seg(None), 'pintura', 'auto')['confidence'] is None
    assert detect_quad(photo(), Seg(rect_prob()), 'pintura', 'manual')['confidence'] is None


def test_overlay_png_marks_piece_and_doubt():
    im = Image.open(io.BytesIO(mask_overlay(rect_prob(blur=3), (300, 400))))
    a = np.asarray(im); assert im.mode == 'RGBA' and a.shape == (300, 400, 4)
    assert a[150, 200, 3] > 0 and a[5, 5, 3] == 0  # dentro de la pieza se pinta, el fondo queda transparente


def test_api_detect_returns_confidence_and_mask():
    server.app.config['TESTING'] = True; server.models = Seg(rect_prob()); client = server.app.test_client()
    r = client.post('/api/upload', data={'image': (io.BytesIO(encode_png(photo())), 'p.png')}); assert r.status_code == 200
    assert r.json['detection']['confidence']['level'] == 'segura'
    d = client.post('/api/detect', json={'kind': 'documento_impreso', 'method': 'auto', 'scope_confirmed': True})
    assert d.status_code == 200 and d.json['confidence']['level'] == 'segura'
    m = client.get('/api/image/mask'); assert m.status_code == 200 and m.mimetype == 'image/png'
    assert Image.open(io.BytesIO(m.data)).mode == 'RGBA'
    server.models = Seg(None); client2 = server.app.test_client()
    client2.post('/api/upload', data={'image': (io.BytesIO(encode_png(photo())), 'p.png')})
    assert client2.get('/api/image/mask').status_code == 400
