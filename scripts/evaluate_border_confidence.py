"""¿La etiqueta «borde dudoso» señala de verdad los bordes mal propuestos?

Para cada foto con máscara de referencia se ejecuta la función de la aplicación
(imaging.detect_quad) y se compara su etiqueta de confianza con la IoU real del
cuadrilátero. Un borde es malo si su IoU con la referencia es < 0,90.
Los umbrales (imaging.FIT_MIN, imaging.BAND_MAX) se eligieron con las fotos de
validación; las de prueba solo se usan para medir. Además de la U-Net desplegada
(semilla 42) se usan las de control (semillas 7 y 2026) para tener más casos.

  python scripts/evaluate_border_confidence.py --seg "C:\\ruta\\segmentacion_3clases" [--root "C:\\ruta\\datos"]
"""
from pathlib import Path
import argparse, csv, json, sys, collections
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'scripts'))
import numpy as np, cv2
from PIL import Image, ImageOps
from palimpsesto.imaging import detect_quad, resize_long, FIT_MIN, BAND_MAX
from evaluate_unet import Segmenter, quad_iou

OUT = ROOT / 'results/border_confidence'
MODELS = {'42': 'models/unet_resnet18_3clases.pth', '7': 'models/unet_3clases_seed7.pth', '2026': 'models/unet_3clases_seed2026.pth'}


def table(rows):
    bad = [r for r in rows if r['quad_iou'] < .9]; good = [r for r in rows if r['quad_iou'] >= .9]
    flagged_bad = sum(r['level'] == 'dudosa' for r in bad); flagged_good = sum(r['level'] == 'dudosa' for r in good)
    dudosas = [r for r in rows if r['level'] == 'dudosa']; seguras = [r for r in rows if r['level'] == 'segura']
    return {'bordes': len(rows), 'malos': len(bad), 'malos_marcados_dudosos': flagged_bad, 'buenos': len(good), 'buenos_marcados_dudosos': flagged_good,
            'iou_media_seguros': round(float(np.mean([r['quad_iou'] for r in seguras])), 4) if seguras else None,
            'iou_media_dudosos': round(float(np.mean([r['quad_iou'] for r in dudosas])), 4) if dudosas else None,
            'malos_entre_seguros': sum(r['quad_iou'] < .9 for r in seguras)}


def figure(rows):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    GREEN, ORANGE, INK, BG = '#23594f', '#d08a2a', '#173d36', '#f8f8f5'
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'axes.spines.top': False, 'axes.spines.right': False, 'figure.facecolor': BG, 'axes.facecolor': BG,
                         'axes.edgecolor': INK, 'axes.labelcolor': INK, 'xtick.color': INK, 'ytick.color': INK})
    test = [r for r in rows if r['split'] == 'test']
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    for level, color, label in (('segura', GREEN, 'Etiqueta «borde seguro»'), ('dudosa', ORANGE, 'Etiqueta «borde dudoso»')):
        xs = [r for r in test if r['level'] == level]
        ax.scatter([r['fit'] for r in xs], [r['quad_iou'] for r in xs], s=26, color=color, alpha=.8, label=label, edgecolor='white', linewidth=.4)
    ax.axhline(.9, color=INK, lw=.8, ls='--'); ax.text(.705, .905, 'IoU real 0,90', fontsize=8, color=INK)
    ax.axvline(FIT_MIN, color=ORANGE, lw=.8, ls=':'); ax.text(FIT_MIN - .003, .42, 'encaje ' + f'{FIT_MIN:.2f}'.replace('.', ','), fontsize=8, color=ORANGE, ha='right')
    ax.set_xlim(.7, 1); ax.set_ylim(.4, 1.0)
    ax.set_xlabel('Encaje de los 4 puntos con la máscara de la U-Net (la app lo calcula sin referencia)')
    ax.set_ylabel('IoU real del borde con la referencia')
    ax.set_title('Fotos de prueba: la etiqueta de confianza separa los bordes malos', fontweight='bold', color=INK, fontsize=11)
    ax.legend(loc='lower right', fontsize=8.5, frameon=False)
    fig.text(.01, .01, 'Prueba: 40 fotos de piezas no vistas × 3 U-Net (semillas 42, 7 y 2026). «Dudoso» también se activa por un contorno difuso (franja > 5 px).', fontsize=7.2, color='#5a6f64')
    fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(ROOT / 'results/figures/confianza_borde.png', dpi=150); plt.close(fig)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--seg', required=True); ap.add_argument('--root')
    args = ap.parse_args(); OUT.mkdir(parents=True, exist_ok=True)
    nets = {s: Segmenter(ROOT / p) for s, p in MODELS.items()}
    rows = []
    for r in csv.DictReader(open(ROOT / 'data/segmentation_manifest.csv', encoding='utf-8')):
        img = next((Path(args.seg) / 'images').glob(r['file'] + '.*'))
        rgb = np.asarray(ImageOps.exif_transpose(Image.open(img)).convert('RGB'))
        gt = cv2.imread(str(Path(args.seg) / 'masks' / (r['file'] + '.png')), 0) > 0
        small = resize_long(rgb, 960); gts = cv2.resize(gt.astype(np.uint8), small.shape[1::-1], interpolation=cv2.INTER_NEAREST)
        for seed, net in nets.items():
            if seed != '42' and r['split'] == 'train':
                continue
            res = detect_quad(rgb, net, r['class'], 'unet')
            if res['method'] != 'unet':
                continue
            iou, _ = quad_iou(res, gts); c = res['confidence']
            rows.append({'file': r['file'], 'class': r['class'], 'split': r['split'], 'seed': seed, 'quad_iou': round(float(iou), 4),
                         'level': c['level'], 'fit': c['fit'], 'band': c['band']})
    with open(OUT / 'per_image.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, list(rows[0]), lineterminator='\n'); w.writeheader(); w.writerows(rows)
    ev = {'regla': f'dudosa si encaje < {FIT_MIN} o franja dudosa > {BAND_MAX} px; umbrales elegidos con validación',
          'validacion_3_semillas': table([r for r in rows if r['split'] == 'val']),
          'prueba_3_semillas': table([r for r in rows if r['split'] == 'test']),
          'prueba_unet_desplegada': table([r for r in rows if r['split'] == 'test' and r['seed'] == '42']),
          'prueba_por_clase': {k: table([r for r in rows if r['split'] == 'test' and r['class'] == k]) for k in ('documento_impreso', 'manuscrito', 'pintura')},
          'entrenamiento_unet_desplegada': table([r for r in rows if r['split'] == 'train'])}
    if args.root:  # fotos sin máscara de referencia: con qué frecuencia aparece «dudoso»
        from palimpsesto.models import ModelService
        ms = ModelService(ROOT / 'models'); counts = collections.defaultdict(collections.Counter)
        for r in csv.DictReader(open(ROOT / 'data/manifest.csv', encoding='utf-8-sig')):
            rgb = np.asarray(ImageOps.exif_transpose(Image.open(Path(args.root) / r['path'].replace(chr(92), '/'))).convert('RGB'))
            res = detect_quad(rgb, ms, r['class'], 'auto')
            counts[r['class']][res['confidence']['level'] if res['confidence'] else res['method']] += 1
        ev['fotos_de_clasificacion_sin_referencia'] = {k: dict(v) for k, v in counts.items()}
    (OUT / 'evaluation.json').write_text(json.dumps(ev, indent=2, ensure_ascii=False), encoding='utf-8')
    figure(rows)
    print(json.dumps(ev, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
