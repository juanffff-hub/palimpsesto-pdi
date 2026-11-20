"""Figuras de la ampliación de la U-Net a 3 clases (README §7).

Lee results/segmentation/ (no recalcula modelos). Con --data también dibuja
ejemplos de prueba con el borde de cada sistema sobre la foto.

  python scripts/make_segmentation_figures.py --data "C:\\ruta\\PDI_Segmentacion_3clases"
"""
from pathlib import Path
import argparse, csv, json, sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np, cv2
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

GREEN, BRASS, SAGE, INK, BG, RED = '#23594f', '#c4955b', '#8aa89a', '#173d36', '#f8f8f5', '#b5523b'
NAMES = {'documento_impreso': 'Impreso', 'manuscrito': 'Manuscrito', 'pintura': 'Pintura'}
SYSTEMS = {'contornos': ('Contornos clásicos', SAGE), 'unet_anterior': ('U-Net anterior (solo impresos)', BRASS),
           'sistema_actual': ('Sistema v0.3.0 (modo automático)', '#5a6f64'), 'unet_3clases': ('U-Net 3 clases (v0.4.0)', GREEN)}
SEG = ROOT / 'results/segmentation'; FIG = ROOT / 'results/figures'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'axes.edgecolor': INK, 'axes.labelcolor': INK, 'xtick.color': INK,
                     'ytick.color': INK, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.facecolor': BG, 'axes.facecolor': BG})


def comparison(ev):
    test = ev['summary']['test']; classes = list(NAMES); x = np.arange(len(classes) + 1); w = .2
    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    for i, (key, (label, color)) in enumerate(SYSTEMS.items()):
        vals = [test[c][key]['quad_iou_mean'] for c in classes] + [ev['macro_test'][key]]
        bars = ax.bar(x + (i - 1.5) * w, vals, w, color=color, label=label)
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + .012, f'{b.get_height():.2f}', ha='center', fontsize=7.6, color=INK)
    n = [test[c]['unet_3clases']['n'] for c in classes]
    ax.set_xticks(x, [f'{NAMES[c]}\n({k} fotos de prueba)' for c, k in zip(classes, n)] + ['Media de\nlas 3 clases'])
    ax.set_ylim(0, 1.12); ax.set_ylabel('IoU media del cuadrilátero propuesto')
    ax.set_title('Borde propuesto en fotos de prueba (piezas no vistas en el entrenamiento)', fontweight='bold', color=INK)
    ax.legend(loc='upper center', bbox_to_anchor=(.5, -.17), ncol=2, fontsize=8.5, frameon=False)
    fig.text(.01, .01, 'Sin borde válido cuenta como IoU 0. Prueba por bloques de pieza: 12 impresos (los mismos del Parcial 3), 16 manuscritos y 12 pinturas.', fontsize=7.3, color='#5a6f64')
    fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(FIG / 'unet_3clases_comparacion.png', dpi=150); plt.close(fig)


def learning():
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    for seed, style in ((42, '-'), (7, ':'), (2026, '--')):
        rows = list(csv.DictReader(open(SEG / f'history_seed{seed}.csv', encoding='utf-8')))
        e = [int(r['epoch']) for r in rows]
        lab = f'semilla {seed}' + (' (desplegada)' if seed == 42 else '')
        axes[0].plot(e, [float(r['loss_train']) for r in rows], style, color=SAGE, lw=1.4)
        axes[0].plot(e, [float(r['loss_val']) for r in rows], style, color=GREEN, lw=1.6, label=lab)
        axes[1].plot(e, [float(r['dice_val']) for r in rows], style, color=GREEN, lw=1.6, label=lab)
    axes[0].set_title('Pérdida Soft Dice (gris: entrenamiento · verde: validación)', fontsize=10, color=INK)
    axes[1].set_title('Dice de validación (40 fotos, 3 clases)', fontsize=10, color=INK)
    for ax in axes: ax.set_xlabel('Época'); ax.legend(fontsize=8, frameon=False)
    axes[1].set_ylim(.85, 1)
    fig.tight_layout(); fig.savefig(FIG / 'unet_3clases_aprendizaje.png', dpi=150); plt.close(fig)


def examples(data, ev):
    from PIL import Image, ImageOps
    from palimpsesto.imaging import detect_quad, resize_long
    from evaluate_unet import Segmenter
    rows = list(csv.DictReader(open(SEG / 'per_image.csv', encoding='utf-8')))
    old = Segmenter(ROOT / 'models/unet_resnet18_imagenet.pth'); new = Segmenter(ROOT / 'models/unet_resnet18_3clases.pth')
    picks = []
    for c in ('manuscrito', 'pintura'):  # las dos fotos de prueba donde más cambió el borde
        part = [r for r in rows if r['split'] == 'test' and r['class'] == c]
        part.sort(key=lambda r: float(r['unet_3clases_quad_iou']) - float(r['sistema_actual_quad_iou']), reverse=True)
        picks += part[:2]
    fig, axes = plt.subplots(2, len(picks), figsize=(3.3 * len(picks), 6.6))
    for j, r in enumerate(picks):
        img = next((data / 'images').glob(r['file'] + '.*'))
        rgb = resize_long(np.asarray(ImageOps.exif_transpose(Image.open(img)).convert('RGB')), 960)
        gt = cv2.resize(cv2.imread(str(data / 'masks' / (r['file'] + '.png')), 0), rgb.shape[1::-1], interpolation=cv2.INTER_NEAREST)
        contours, _ = cv2.findContours((gt > 0).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        method = 'contornos' if r['class'] == 'pintura' else 'unet'
        for i, (title, model, m, key, color) in enumerate((('Sistema v0.3.0', old, method, 'sistema_actual', (196, 149, 91)),
                                                            ('U-Net 3 clases', new, 'unet', 'unet_3clases', (35, 89, 79)))):
            # Los documentos se difuminan, como en la muestra del dataset: algunos contienen nombres.
            canvas = cv2.GaussianBlur(rgb, (0, 0), 4) if r['class'] != 'pintura' else rgb.copy()
            cv2.drawContours(canvas, contours, -1, (255, 255, 255), 5)
            res = detect_quad(rgb, model, r['class'], m); h, w = rgb.shape[:2]
            if res['method'] != 'manual':
                q = np.round(np.asarray(res['points']) * [w - 1, h - 1]).astype(np.int32)
                cv2.polylines(canvas, [q], True, color, 7)
            ax = axes[i, j]; ax.imshow(canvas); ax.set_xticks([]); ax.set_yticks([])
            for s in ax.spines.values(): s.set_visible(False)
            src = {'unet': 'U-Net', 'contornos': 'contornos', 'manual': 'sin borde'}[res['method']]
            head = f"{NAMES[r['class']]}\n" if i == 0 else ''
            ax.set_title(f"{head}{title} · {src} · IoU {float(r[key + '_quad_iou']):.2f}", fontsize=9, color=INK)
    fig.text(.5, .005, 'Blanco: máscara de referencia. Color: cuadrilátero propuesto. Fotos de prueba de piezas que la U-Net nueva no vio.', ha='center', fontsize=8, color='#5a6f64')
    fig.tight_layout(rect=(0, .02, 1, .97)); fig.savefig(FIG / 'unet_3clases_ejemplos.jpg', dpi=110, pil_kwargs={'quality': 85}); plt.close(fig)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--data'); args = ap.parse_args()
    ev = json.loads((SEG / 'evaluation.json').read_text(encoding='utf-8'))
    comparison(ev); learning()
    if args.data:
        sys.path.insert(0, str(ROOT / 'scripts')); examples(Path(args.data), ev)


if __name__ == '__main__':
    main()
