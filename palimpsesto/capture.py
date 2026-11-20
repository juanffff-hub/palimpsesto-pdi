"""Calidad de la captura: ¿conviene repetir la foto antes de salir de la sala?

Mide la pieza, no la escena: usa la máscara de la U-Net para mirar solo la zona
de la pieza. Los umbrales se calibraron con las fotos reales de desarrollo
(scripts/calibrate_capture.py, results/capture/).
"""
import cv2
import numpy as np

VIEW = 960


def _view(rgb, prob):
    h, w = rgb.shape[:2]; s = min(1., VIEW / max(h, w))
    small = cv2.resize(rgb, (max(1, round(w * s)), max(1, round(h * s))), interpolation=cv2.INTER_AREA) if s < 1 else rgb
    mask = None
    if prob is not None:
        mask = cv2.resize((prob > .5).astype(np.uint8), small.shape[1::-1], interpolation=cv2.INTER_NEAREST).astype(bool)
        n, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
        mask = labels == (1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))) if n > 1 else None
    return small, mask


def measure(rgb, prob):
    """Medidas de la pieza en la vista de 960 px. `prob` es la salida de la U-Net (o None)."""
    small, mask = _view(rgb, prob)
    gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY); h, w = gray.shape
    piece = mask if mask is not None and mask.mean() > .01 else np.ones_like(gray, bool)
    inner = cv2.erode(piece.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
    inner = inner if inner.sum() > 500 else piece
    g = gray.astype(np.float32)
    # Segunda derivada por separado en x y en y: el temblor borra una sola dirección.
    k = np.array([[1, -2, 1]], np.float32)
    dx = cv2.filter2D(g, cv2.CV_32F, k); dy = cv2.filter2D(g, cv2.CV_32F, k.T)
    # Nitidez por bloques de la pieza y su borde: se toma el bloque nítido (p90) para no
    # castigar las zonas lisas de una pintura; un desenfoque real baja todos los bloques.
    region = cv2.dilate(piece.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool)
    t = 48; vx = []; vy = []
    for y in range(0, h - t + 1, t):
        for x in range(0, w - t + 1, t):
            if region[y:y + t, x:x + t].mean() >= .6:
                vx.append(float(dx[y:y + t, x:x + t].var())); vy.append(float(dy[y:y + t, x:x + t].var()))
    sx = float(np.percentile(vx, 90)) if vx else 0.; sy = float(np.percentile(vy, 90)) if vy else 0.
    sharp = min(sx, sy); ratio = max(sx, sy) / max(sharp, 1e-3)
    values = g[inner]
    # Reflejo: mancha saturada compacta dentro de la pieza. Las franjas finas (un paspartú
    # blanco) o los puntos sueltos de pintura blanca no cuentan.
    sat = ((gray >= 250) & inner).astype(np.uint8); glare = 0.
    n, _, stats, _ = cv2.connectedComponentsWithStats(sat, 8)
    for x0, y0, bw, bh, area in stats[1:]:
        if min(bw, bh) >= 8 and area / (bw * bh) >= .35:
            glare = max(glare, area / max(inner.sum(), 1) * 100)
    border = 0.
    if mask is not None:
        e = max(2, round(.006 * max(h, w)))
        sides = [mask[:e].any(0).mean(), mask[-e:].any(0).mean(), mask[:, :e].any(1).mean(), mask[:, -e:].any(1).mean()]
        border = float(max(sides))
    side = None
    if mask is not None:
        ys, xs = np.nonzero(mask); scale = max(rgb.shape[:2]) / max(h, w)
        side = float(min(xs.max() - xs.min(), ys.max() - ys.min()) * scale)
    return {'piece_min_side_px': side, 'piece_fraction': float(mask.mean()) if mask is not None else None,
            'border_contact': border if mask is not None else None,
            'sharpness': sharp, 'direction_ratio': ratio,
            'median_luminance': float(np.median(values)),
            'p95_luminance': float(np.percentile(values, 95)),
            'bright_percent': float((values >= 250).mean() * 100),
            'glare_percent': float(glare),
            'dark_percent': float((values <= 25).mean() * 100),
            'mask_available': mask is not None}


# Umbrales calibrados con las 480 fotos reales y degradaciones sintéticas controladas
# (scripts/calibrate_capture.py, results/capture/). Nitidez en la vista de 960 px.
SHARP_BAD = 8.0
SHARP_WARN = {'documento_impreso': 20.0, 'manuscrito': 20.0, 'pintura': 12.0}
MOTION_RATIO = 10.0                         # una dirección 10 veces más nítida que la otra: temblor
LIGHT_BAD, LIGHT_WARN = 40.0, 70.0          # percentil 95 de luminancia de la pieza
OVEREXPOSED = 10.0                          # % de la pieza saturada (>= 250)
GLARE_WARN = 1.2                            # % de la pieza en una mancha saturada compacta
BORDER_WARN, BORDER_BAD = .05, .25          # fracción de un lado de la foto que toca la pieza
SMALL_FRACTION, SMALL_SIDE = .10, 450       # fracción del encuadre; lado menor de la pieza en px

KINDS = ('documento_impreso', 'manuscrito', 'pintura')


def _check(key, title, level, message, value):
    return {'id': key, 'title': title, 'level': level, 'message': message, 'value': None if value is None else round(float(value), 3)}


def checks_for(m, kind):
    """Cinco chequeos de la captura para un tipo de pieza: ok, warn (revisar) o bad (repetir)."""
    out = []
    s = m['sharpness']
    if s < SHARP_BAD:
        out.append(_check('sharpness', 'Nitidez', 'bad', 'La foto está borrosa: los trazos finos no se recuperan después. Repítela con el celular quieto y enfocando la pieza.', s))
    elif s < SHARP_WARN[kind]:
        out.append(_check('sharpness', 'Nitidez', 'warn', 'Puede haber desenfoque o movimiento. Amplía el detalle; si se ve borroso, repite la foto.', s))
    elif m['direction_ratio'] > MOTION_RATIO:
        out.append(_check('sharpness', 'Nitidez', 'warn', 'Parece que el celular se movió al tomar la foto: los trazos se ven corridos en una dirección. Repítela apoyando los codos o el celular.', m['direction_ratio']))
    else:
        out.append(_check('sharpness', 'Nitidez', 'ok', 'Bordes nítidos.', s))
    if m['bright_percent'] >= OVEREXPOSED:
        out.append(_check('light', 'Luz', 'bad', 'Hay zonas de la pieza quemadas por exceso de luz. Repite la foto con menos luz directa o sin flash.', m['bright_percent']))
    elif m['p95_luminance'] < LIGHT_BAD:
        out.append(_check('light', 'Luz', 'bad', 'La foto está muy oscura: hasta las zonas claras de la pieza salen grises. Repítela con más luz.', m['p95_luminance']))
    elif m['p95_luminance'] < LIGHT_WARN:
        out.append(_check('light', 'Luz', 'warn', 'Hay poca luz. Se puede corregir en parte, pero con más luz se conservarán mejor los detalles.', m['p95_luminance']))
    else:
        out.append(_check('light', 'Luz', 'ok', 'Exposición suficiente.', m['p95_luminance']))
    if m['glare_percent'] >= GLARE_WARN:
        out.append(_check('glare', 'Reflejos', 'warn', 'Hay un reflejo sobre la pieza: esa zona no tiene información. Inclina un poco el celular o apaga el flash y repite la foto.', m['glare_percent']))
    else:
        out.append(_check('glare', 'Reflejos', 'ok', 'Sin reflejos grandes.', m['glare_percent']))
    if m['mask_available']:
        b = m['border_contact']
        if b > BORDER_BAD:
            out.append(_check('framing', 'Pieza completa', 'bad', 'La pieza parece salirse de la foto: una parte quedó fuera del encuadre. Aléjate un poco y repite la foto.', b))
        elif b > BORDER_WARN:
            out.append(_check('framing', 'Pieza completa', 'warn', 'La pieza toca el borde de la foto: comprueba que no falte un borde o una esquina.', b))
        else:
            out.append(_check('framing', 'Pieza completa', 'ok', 'La pieza entra completa en la foto.', b))
        if m['piece_fraction'] < SMALL_FRACTION:
            out.append(_check('size', 'Tamaño', 'warn', 'La pieza ocupa poco de la foto. Acércate para que llene el encuadre y se conserven los trazos finos.', m['piece_fraction']))
        elif m['piece_min_side_px'] < SMALL_SIDE:
            out.append(_check('size', 'Tamaño', 'warn', f"La pieza mide solo {round(m['piece_min_side_px'])} px de lado: la foto tiene poca resolución. Usa la foto original del celular (no una reenviada por chat) o acércate.", m['piece_min_side_px']))
        else:
            out.append(_check('size', 'Tamaño', 'ok', 'La pieza ocupa buena parte del encuadre.', m['piece_fraction']))
    return out


def assess(rgb, prob, suggested_kind=None):
    """Informe de la captura para la interfaz: chequeos por tipo de pieza y veredicto."""
    m = measure(rgb, prob)
    by_kind = {}
    for kind in KINDS:
        checks = checks_for(m, kind); levels = {c['level'] for c in checks}
        by_kind[kind] = {'verdict': 'repetir' if 'bad' in levels else 'revisar' if 'warn' in levels else 'ok', 'checks': checks}
    kind = suggested_kind if suggested_kind in KINDS else 'documento_impreso'
    return {'kind_used': kind, **by_kind[kind], 'by_kind': by_kind, 'metrics': {k: (round(v, 4) if isinstance(v, float) else v) for k, v in m.items()},
            'piece_mask': m['mask_available'],
            'note': 'Revisión orientativa calibrada con fotos reales del proyecto; la decisión final es de la persona.'}
