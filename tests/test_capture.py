"""Semáforo de la captura: cada defecto controlado activa el chequeo que le corresponde."""
import numpy as np, cv2
from palimpsesto.capture import assess, measure


def page(width=1200, height=900, box=(250, 150, 950, 750)):
    """Página con texto sobre una mesa oscura y su máscara (la salida ideal de la U-Net)."""
    rgb = np.full((height, width, 3), (60, 45, 35), np.uint8)
    x0, y0, x1, y1 = box
    rgb[y0:y1, x0:x1] = 235
    for i, y in enumerate(range(y0 + 40, y1 - 20, 34)):
        cv2.putText(rgb, f'Archivo historico folio {i} tinta y trazos finos', (x0 + 25, y), cv2.FONT_HERSHEY_SIMPLEX, .7, (25, 25, 30), 2, cv2.LINE_AA)
    prob = np.zeros((height, width), np.float32); prob[y0:y1, x0:x1] = 1
    return rgb, prob


def levels(report):
    return {c['id']: c['level'] for c in report['checks']}


def test_good_capture_is_ok():
    rgb, prob = page(); r = assess(rgb, prob, 'manuscrito')
    assert r['verdict'] == 'ok' and set(levels(r).values()) == {'ok'}
    assert set(r['by_kind']) == {'documento_impreso', 'manuscrito', 'pintura'}


def test_blur_and_motion_are_flagged():
    rgb, prob = page()
    assert levels(assess(cv2.GaussianBlur(rgb, (0, 0), 3), prob, 'manuscrito'))['sharpness'] in ('warn', 'bad')
    assert levels(assess(cv2.GaussianBlur(rgb, (0, 0), 8), prob, 'manuscrito'))['sharpness'] == 'bad'
    k = np.zeros((15, 15), np.float32); k[7, :] = 1 / 15
    assert levels(assess(cv2.filter2D(rgb, -1, k), prob, 'manuscrito'))['sharpness'] in ('warn', 'bad')


def test_dark_and_overexposed_are_flagged():
    rgb, prob = page()
    assert levels(assess((rgb * .15).astype(np.uint8), prob, 'documento_impreso'))['light'] == 'bad'
    over = np.clip(rgb.astype(np.float32) * 3, 0, 255).astype(np.uint8)
    assert levels(assess(over, prob, 'documento_impreso'))['light'] == 'bad'


def test_cut_and_small_piece():
    rgb, prob = page(box=(0, 150, 700, 750))
    assert levels(assess(rgb, prob, 'documento_impreso'))['framing'] == 'bad'
    rgb, prob = page(box=(560, 400, 660, 480))
    assert levels(assess(rgb, prob, 'documento_impreso'))['size'] == 'warn'


def test_glare_spot_but_not_thin_white_band():
    rgb, prob = page(); spot = rgb.copy()
    cv2.circle(spot, (600, 450), 70, (255, 255, 255), -1)
    assert levels(assess(spot, prob, 'pintura'))['glare'] == 'warn'
    band = rgb.copy(); band[150:750, 250:262] = 255
    assert levels(assess(band, prob, 'pintura'))['glare'] == 'ok'


def test_without_segmenter_skips_mask_checks():
    rgb, _ = page(); r = assess(rgb, None, 'pintura')
    assert 'framing' not in levels(r) and 'size' not in levels(r) and r['piece_mask'] is False
    assert measure(rgb, None)['border_contact'] is None
