"""Figuras del README a partir de los JSON de results/ (no recalcula modelos).

Uso:  python scripts/make_figures.py [--root RUTA_DATOS]
Con --root también genera la muestra visual del dataset (miniaturas de las fotos reales).
"""
from pathlib import Path
import sys, json, csv, argparse, collections
ROOT = Path(__file__).resolve().parents[1]
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

GREEN, BRASS, SAGE, INK, BG = '#23594f', '#c4955b', '#8aa89a', '#173d36', '#f8f8f5'
NAMES = {'documento_impreso': 'Impreso', 'manuscrito': 'Manuscrito', 'pintura': 'Pintura'}
FIG = ROOT / 'results/figures'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'axes.edgecolor': INK, 'axes.labelcolor': INK, 'xtick.color': INK,
                     'ytick.color': INK, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.facecolor': BG, 'axes.facecolor': BG})
load = lambda p: json.loads((ROOT / p).read_text(encoding='utf8'))


def robustness():
    old, new = load('results/robustness/evaluation_v0.2.0.json')['scenarios'], load('results/robustness/evaluation.json')['scenarios']
    labels = {'original': 'Original', 'resized_960_control': 'Control 960 px', 'dark_065': 'Oscurecer', 'bright_125': 'Aclarar',
              'rotation_90': 'Giro 90°', 'blur_sigma_2': 'Desenfoque', 'noise_sigma_8': 'Ruido', 'central_crop_90': 'Recorte 90 %'}
    keys = list(labels)[::-1]; y = np.arange(len(keys)); h = .38
    fig, ax = plt.subplots(figsize=(8.4, 5.8))
    a = ax.barh(y + h / 2, [old[k]['macro_f1'] for k in keys], h, color=SAGE, label='v0.2.0 · cabeza sin giros')
    b = ax.barh(y - h / 2, [new[k]['macro_f1'] for k in keys], h, color=GREEN, label='v0.3.0 · cabeza con giros 90/180/270')
    for bars in (a, b):
        for r in bars: ax.text(r.get_width() + .005, r.get_y() + r.get_height() / 2, f'{r.get_width():.3f}', va='center', fontsize=8.5, color=INK)
    ax.set_yticks(y, [labels[k] for k in keys]); ax.set_xlim(0, 1.09); ax.set_xlabel('Macro-F1 · diagnóstico secundario (72 fotos ya abiertas)', labelpad=2)
    ax.set_title('Sensibilidad a perturbaciones sintéticas', fontweight='bold', color=INK)
    ax.legend(loc='upper center', bbox_to_anchor=(.5, -.11), ncol=2, fontsize=8.5, frameon=False); fig.text(.01, .01, 'Perturbaciones sintéticas sobre fotos ya vistas: no son fotos nuevas independientes.', fontsize=7.5, color='#5a6f64')
    fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(FIG / 'robustness.png', dpi=150); plt.close(fig)


def confusion():
    cnn = load('results/classification/selected_test.json')['confusion_matrix']
    old = load('results/robustness/evaluation_v0.2.0.json')['scenarios']['original']['confusion_matrix']
    new = load('results/robustness/evaluation.json')['scenarios']['original']['confusion_matrix']
    panels = [('CNN del curso · prueba inicial', cnn), ('Transferencia v0.2.0', old), ('Transferencia v0.3.0', new)]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.1))
    ticks = [NAMES[c] for c in NAMES]
    for ax, (title, m) in zip(axes, panels):
        m = np.array(m); ax.imshow(m, cmap='Greens', vmin=0, vmax=24)
        for i in range(3):
            for j in range(3): ax.text(j, i, m[i, j], ha='center', va='center', fontsize=14, color='white' if m[i, j] > 14 else INK)
        ax.set_xticks(range(3), ticks, rotation=20); ax.set_yticks(range(3), ticks)
        ax.set_title(f'{title}\n{np.trace(m)}/72 aciertos', fontsize=10.5, fontweight='bold', color=INK); ax.set_xlabel('Predicción'); ax.set_ylabel('Clase real')
        for s in ax.spines.values(): s.set_visible(False)
    fig.text(.5, .01, '72 fotos / 9 bloques provisionales. Los diagnósticos de transferencia reutilizan ese test: no son prueba ciega nueva.', ha='center', fontsize=8, color='#5a6f64')
    fig.tight_layout(rect=(0, .04, 1, 1)); fig.savefig(FIG / 'confusion.png', dpi=150); plt.close(fig)


def rotation():
    ev = load('results/rotation/evaluation.json')['variants']
    names = {'base': 'Base\n(v0.2.0)', 'giros_originales': 'Giros de la\nvista original\n(v0.3.0)', 'giros_todas': 'Giros de\ntodas las vistas'}
    x = np.arange(len(names)); w = .36
    up = [ev[k]['oof']['0']['macro_f1'] for k in names]; rot = [ev[k]['rotated_mean_macro_f1'] for k in names]
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    a = ax.bar(x - w / 2, up, w, color=GREEN, label='Fotos derechas'); b = ax.bar(x + w / 2, rot, w, color=BRASS, label='Fotos giradas 90/180/270° (media)')
    for bars in (a, b):
        for r in bars: ax.text(r.get_x() + r.get_width() / 2, r.get_height() + .004, f'{r.get_height():.3f}', ha='center', fontsize=9, color=INK)
    ax.set_xticks(x, list(names.values())); ax.set_ylim(.8, 1.0); ax.set_ylabel('Macro-F1 fuera de fold')
    ax.set_title('Experimento de rotación · validación cruzada por bloques', fontweight='bold', color=INK)
    ax.legend(frameon=False, fontsize=9, loc='lower right')
    fig.text(.01, .01, '408 fotos de desarrollo, 5 folds por 41 bloques provisionales. Regla de adopción fijada antes de ejecutar.', fontsize=7.5, color='#5a6f64')
    fig.tight_layout(rect=(0, .04, 1, 1)); fig.savefig(FIG / 'rotation_experiment.png', dpi=150); plt.close(fig)


def dataset(root):
    from PIL import Image, ImageOps, ImageFilter
    rows = list(csv.DictReader(open(ROOT / 'data/manifest.csv', encoding='utf-8-sig')))
    count = collections.Counter((r['class'], r['split']) for r in rows)
    fig, ax = plt.subplots(figsize=(6.4, 3.4)); left = np.zeros(3)
    for split, color, label in [('train', GREEN, 'Entrenamiento'), ('val', SAGE, 'Validación'), ('test', BRASS, 'Diagnóstico')]:
        v = np.array([count[(c, split)] for c in NAMES]); ax.barh(list(NAMES.values()), v, left=left, color=color, label=label)
        for i, (l, n) in enumerate(zip(left, v)): ax.text(l + n / 2, i, str(n), ha='center', va='center', color='white', fontsize=9)
        left += v
    ax.set_xlabel('Fotografías'); ax.set_title('480 fotografías · 160 por clase', fontweight='bold', color=INK); ax.legend(frameon=False, fontsize=8.5, ncol=3, loc='upper center', bbox_to_anchor=(.5, -.25))
    fig.tight_layout(); fig.savefig(FIG / 'dataset_distribution.png', dpi=150); plt.close(fig)
    # Muestra: 6 fotos por clase de bloques distintos, en miniatura (repositorio privado).
    rng = np.random.default_rng(2026); tiles = []
    for c in NAMES:
        seen, pick = set(), []
        for i in rng.permutation(len(rows)):
            r = rows[i]
            if r['class'] == c and r['group_id'] not in seen: seen.add(r['group_id']); pick.append(r)
            if len(pick) == 6: break
        row = []
        for r in pick:
            im = ImageOps.exif_transpose(Image.open(Path(root) / r['path'].replace('\\', '/'))).convert('RGB'); im = ImageOps.fit(im, (180, 240))
            if c != 'pintura': im = im.filter(ImageFilter.GaussianBlur(1.6))  # documentos con datos personales
            row.append(np.asarray(im))
        tiles.append(np.concatenate([np.pad(t, ((4, 4), (4, 4), (0, 0)), constant_values=248) for t in row], 1))
    fig, axes = plt.subplots(3, 1, figsize=(9.2, 8.6), gridspec_kw={'hspace': .12})
    for ax, c, t in zip(axes, NAMES, tiles):
        ax.imshow(t); ax.set_axis_off(); ax.set_title(NAMES[c], loc='left', fontweight='bold', color=INK)
    fig.suptitle('Muestra del dataset · una foto por bloque (documentos difuminados por privacidad)', fontweight='bold', color=INK)
    fig.subplots_adjust(left=.02, right=.98, top=.93, bottom=.02); fig.savefig(FIG / 'dataset_muestras.jpg', dpi=110, pil_kwargs={'quality': 82}); plt.close(fig)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--root'); args = ap.parse_args()
    robustness(); confusion(); rotation()
    if args.root: dataset(args.root)
    print('Figuras en', FIG)
