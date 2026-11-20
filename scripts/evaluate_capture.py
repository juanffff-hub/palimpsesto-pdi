"""Evalúa el semáforo de la captura (palimpsesto/capture.py) con fotos reales.

1. Fotos reales (data/manifest.csv, 480): cuántas reciben cada aviso.
2. Las mismas fotos con un defecto controlado (desenfoque, temblor, poca luz,
   exceso de luz, pieza cortada): cuántas veces el chequeo correspondiente avisa.
3. Pieza completa y tamaño medidos con la máscara de la U-Net frente a la máscara
   de referencia (data/segmentation_manifest.csv, 240 fotos).

  python scripts/evaluate_capture.py --root "C:\\ruta\\datos" --seg "C:\\ruta\\segmentacion_3clases"
"""
from pathlib import Path
import argparse, csv, json, sys, collections
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np, cv2
from PIL import Image, ImageOps
from palimpsesto.models import ModelService
from palimpsesto.capture import measure, checks_for, BORDER_WARN, SMALL_FRACTION

OUT = ROOT / 'results/capture'
DEFECTS = {  # defecto -> chequeo que debe avisar
    'desenfoque': 'sharpness', 'temblor_horizontal': 'sharpness', 'temblor_vertical': 'sharpness',
    'poca_luz': 'light', 'exceso_de_luz': 'light', 'pieza_cortada': 'framing'}


def degrade(small, kind, mask):
    if kind == 'desenfoque': return cv2.GaussianBlur(small, (0, 0), 1.4)
    if kind.startswith('temblor'):
        k = np.zeros((11, 11), np.float32)
        if kind.endswith('horizontal'): k[5, :] = 1 / 11
        else: k[:, 5] = 1 / 11
        return cv2.filter2D(small, -1, k)
    if kind == 'poca_luz': return np.clip(small.astype(np.float32) * .28, 0, 255).astype(np.uint8)
    if kind == 'exceso_de_luz': return np.clip(small.astype(np.float32) * 2.3, 0, 255).astype(np.uint8)
    ys, xs = np.nonzero(mask); cut = int(xs.min() + .25 * (xs.max() - xs.min()))  # quita un 25 % de la pieza
    return small[:, cut:].copy()


def previous_warning(rgb):
    """Avisos de luz y desenfoque de la v0.4.0 (foto entera, umbrales fijos), para comparar."""
    h, w = rgb.shape[:2]; s = min(1, 480 / max(h, w))
    g = cv2.cvtColor(cv2.resize(rgb, (max(1, round(w * s)), max(1, round(h * s))), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2GRAY)
    return bool((g < 8).mean() > .85 or (g > 250).mean() > .985 or cv2.Laplacian(g, cv2.CV_64F).var() < 18)


def level(m, kind, check):
    return next((c['level'] for c in checks_for(m, kind) if c['id'] == check), None)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--root', required=True); ap.add_argument('--seg', required=True)
    args = ap.parse_args(); OUT.mkdir(parents=True, exist_ok=True)
    ms = ModelService(ROOT / 'models'); assert ms.segmenter is not None
    rows = list(csv.DictReader(open(ROOT / 'data/manifest.csv', encoding='utf-8-sig'))); per = []
    for r in rows:
        rgb = np.asarray(ImageOps.exif_transpose(Image.open(Path(args.root) / r['path'].replace(chr(92), '/'))).convert('RGB'))
        h, w = rgb.shape[:2]; s = min(1, 960 / max(h, w))
        small = cv2.resize(rgb, (round(w * s), round(h * s)), interpolation=cv2.INTER_AREA)
        prob = ms.segment(rgb); m = measure(rgb, prob); kind = r['class']
        checks = checks_for(m, kind); levels = {c['level'] for c in checks}
        row = {'image_id': r['image_id'], 'class': kind, 'split': r['split'],
               'verdict': 'repetir' if 'bad' in levels else 'revisar' if 'warn' in levels else 'ok',
               'aviso_anterior': previous_warning(rgb), **{'check_' + c['id']: c['level'] for c in checks}, **{k: (round(v, 3) if isinstance(v, float) else v) for k, v in m.items()}}
        mask = cv2.resize((prob > .5).astype(np.uint8), small.shape[1::-1], interpolation=cv2.INTER_NEAREST)
        for defect, check in DEFECTS.items():
            if defect == 'pieza_cortada' and mask.sum() < 1000:
                continue
            d = degrade(small, defect, mask)
            row[f'{defect}_detectado'] = level(measure(d, ms.segment(d)), kind, check) in ('warn', 'bad')
            row[f'{defect}_anterior'] = previous_warning(d)
        per.append(row)
    fields = list(per[0]); [fields.append(k) for r in per for k in r if k not in fields]
    with open(OUT / 'per_image.csv', 'w', newline='', encoding='utf-8') as f:
        wr = csv.DictWriter(f, fields, lineterminator='\n'); wr.writeheader(); wr.writerows(per)

    real = {'veredicto': dict(collections.Counter(r['verdict'] for r in per)), 'con_aviso_anterior': int(sum(r['aviso_anterior'] for r in per)),
            'por_chequeo': {c: dict(collections.Counter(r.get('check_' + c) for r in per if r.get('check_' + c))) for c in ('sharpness', 'light', 'glare', 'framing', 'size')},
            'por_clase': {k: dict(collections.Counter(r['verdict'] for r in per if r['class'] == k)) for k in ('documento_impreso', 'manuscrito', 'pintura')}}
    synthetic = {}
    for defect, check in DEFECTS.items():
        vals = [r[f'{defect}_detectado'] for r in per if f'{defect}_detectado' in r]
        synthetic[defect] = {'chequeo': check, 'fotos': len(vals), 'detectadas': int(sum(vals)), 'tasa': round(float(np.mean(vals)), 3),
                             'tasa_avisos_anteriores': round(float(np.mean([r[f'{defect}_anterior'] for r in per if f'{defect}_anterior' in r])), 3),
                             'por_clase': {k: round(float(np.mean([r[f'{defect}_detectado'] for r in per if r['class'] == k and f'{defect}_detectado' in r])), 3) for k in ('documento_impreso', 'manuscrito', 'pintura')}}

    # Pieza completa y tamaño: máscara de la U-Net frente a la de referencia.
    seg = list(csv.DictReader(open(ROOT / 'data/segmentation_manifest.csv', encoding='utf-8'))); agree = []
    for r in seg:
        img = next((Path(args.seg) / 'images').glob(r['file'] + '.*'))
        rgb = np.asarray(ImageOps.exif_transpose(Image.open(img)).convert('RGB'))
        gt = (cv2.imread(str(Path(args.seg) / 'masks' / (r['file'] + '.png')), 0) > 0).astype(np.float32)
        mp, mg = measure(rgb, ms.segment(rgb)), measure(rgb, gt)
        agree.append({'file': r['file'], 'split': r['split'], 'pred_border': mp['border_contact'], 'ref_border': mg['border_contact'],
                      'pred_fraction': mp['piece_fraction'], 'ref_fraction': mg['piece_fraction']})
    def table(subset):
        tp = sum(a['pred_border'] > BORDER_WARN and a['ref_border'] > BORDER_WARN for a in subset)
        fp = sum(a['pred_border'] > BORDER_WARN and a['ref_border'] <= BORDER_WARN for a in subset)
        fn = sum(a['pred_border'] <= BORDER_WARN and a['ref_border'] > BORDER_WARN for a in subset)
        return {'fotos': len(subset), 'tocan_el_borde_segun_referencia': tp + fn, 'avisos_correctos': tp, 'falsas_alarmas': fp, 'omitidas': fn,
                'error_mediano_fraccion': round(float(np.median([abs(a['pred_fraction'] - a['ref_fraction']) for a in subset])), 4),
                'pequenas_referencia': sum(a['ref_fraction'] < SMALL_FRACTION for a in subset), 'pequenas_unet': sum(a['pred_fraction'] < SMALL_FRACTION for a in subset)}
    framing = {'no_vistas_por_la_unet (val+test)': table([a for a in agree if a['split'] != 'train']), 'todas': table(agree)}
    evaluation = {'fotos_reales': real, 'defectos_controlados': synthetic, 'pieza_completa_vs_referencia': framing,
                  'nota': 'Umbrales elegidos observando fotos reales del proyecto y defectos sintéticos; no es una prueba ciega. Los defectos sintéticos se aplican a la vista de 960 px.'}
    (OUT / 'evaluation.json').write_text(json.dumps(evaluation, indent=2, ensure_ascii=False), encoding='utf-8')
    figure(evaluation)
    print(json.dumps(evaluation, indent=1, ensure_ascii=False))


def figure(evaluation):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    GREEN, SAGE, INK, BG = '#23594f', '#c4955b', '#173d36', '#f8f8f5'
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'axes.spines.top': False, 'axes.spines.right': False, 'figure.facecolor': BG, 'axes.facecolor': BG,
                         'axes.edgecolor': INK, 'axes.labelcolor': INK, 'xtick.color': INK, 'ytick.color': INK})
    names = {'desenfoque': 'Desenfoque', 'temblor_horizontal': 'Temblor horizontal', 'temblor_vertical': 'Temblor vertical',
             'poca_luz': 'Poca luz', 'exceso_de_luz': 'Exceso de luz', 'pieza_cortada': 'Pieza cortada'}
    d = evaluation['defectos_controlados']; keys = list(names)[::-1]; y = np.arange(len(keys)); h = .38
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    a = ax.barh(y + h / 2, [d[k]['tasa_avisos_anteriores'] for k in keys], h, color=SAGE, label='Avisos anteriores (foto entera, umbrales fijos)')
    b = ax.barh(y - h / 2, [d[k]['tasa'] for k in keys], h, color=GREEN, label='Semáforo de la captura (pieza, umbrales calibrados)')
    for bars in (a, b):
        for r in bars: ax.text(r.get_width() + .01, r.get_y() + r.get_height() / 2, f'{r.get_width():.0%}', va='center', fontsize=8.5, color=INK)
    ax.set_yticks(y, [names[k] for k in keys]); ax.set_xlim(0, 1.12); ax.set_xlabel('Fotos con el defecto en las que se avisa (480 fotos reales con el defecto aplicado)')
    ax.set_title('¿Avisa cuando la foto tiene un defecto?', fontweight='bold', color=INK)
    ax.legend(loc='upper center', bbox_to_anchor=(.5, -.16), ncol=1, fontsize=8.5, frameon=False)
    fig.tight_layout(); fig.savefig(ROOT / 'results/figures/semaforo_captura.png', dpi=150); plt.close(fig)


if __name__ == '__main__':
    main()
