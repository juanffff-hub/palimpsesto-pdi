"""Figura de la evolución del control de alcance (README §7). Lee results/scope_v2/ (no recalcula).

  python scripts/make_scope_figures.py
"""
from pathlib import Path
import json
ROOT = Path(__file__).resolve().parents[1]
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

GREEN, SAGE, BRASS, INK, BG = '#23594f', '#8aa89a', '#c4955b', '#173d36', '#f8f8f5'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'axes.spines.top': False, 'axes.spines.right': False, 'figure.facecolor': BG, 'axes.facecolor': BG,
                     'axes.edgecolor': INK, 'axes.labelcolor': INK, 'xtick.color': INK, 'ytick.color': INK})


def frac(s):
    a, b = s.split('/'); return int(a) / int(b)


def main():
    dev = json.loads((ROOT / 'results/scope_v2/development.json').read_text(encoding='utf-8'))
    show = [('v0.4.0 · similitud top-3 (foto)', 'v0.4.0 · similitud\n(foto entera)'), ('regresión logística · foto · C=1', 'Regresión logística\n(foto entera)'),
            ('Mahalanobis · foto', 'Mahalanobis\n(foto entera)'), ('Mahalanobis · recorte', 'Mahalanobis\n(recorte de la pieza)'),
            (dev['metodo_elegido'], 'Regresión logística\n(recorte de la pieza)\nELEGIDA')]
    cats = [('01_escenas', 'Escenas'), ('02_objetos_tridimensionales', 'Objetos 3D'), ('03_negativos_dificiles', 'Negativos difíciles')]
    fig, ax = plt.subplots(figsize=(10, 4.9)); x = np.arange(len(show)); w = .2
    colors = [SAGE, '#5a6f64', BRASS]
    for i, (c, lab) in enumerate(cats):
        vals = [frac(dev['metodos'][k]['fuera_de_fold']['alertas_por_categoria'][c]) for k, _ in show]
        ax.bar(x + (i - 1.5) * w, vals, w, color=colors[i], label=lab)
    tot = [dev['metodos'][k]['fuera_de_fold']['sensibilidad_negativos'] for k, _ in show]
    bars = ax.bar(x + 1.5 * w, tot, w, color=GREEN, label='Total (88)')
    for b in bars: ax.text(b.get_x() + b.get_width() / 2, b.get_height() + .015, f'{b.get_height():.0%}', ha='center', fontsize=8.5, color=INK, fontweight='bold')
    ax.axhline(.85, color=INK, lw=.8, ls='--'); ax.text(-.55, .865, 'puerta de desarrollo 85 %', fontsize=8, color=INK, ha='left')
    ax.set_xticks(x, [s for _, s in show], fontsize=8.5); ax.set_ylim(0, 1.1); ax.set_ylabel('Negativos de desarrollo alertados')
    ax.set_title('Control de alcance v2 · desarrollo (validación por grupos, 97 % de piezas válidas aceptadas)', fontweight='bold', color=INK, fontsize=10.5)
    ax.legend(loc='upper left', fontsize=8, frameon=False, ncol=2)
    fig.text(.01, .01, '408 piezas válidas y 88 negativos nuevos (47 grupos), 5 folds sin repartir piezas ni identidades. No incluye la prueba ciega.', fontsize=7.3, color='#5a6f64')
    fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(ROOT / 'results/figures/alcance_v2_desarrollo.png', dpi=150); plt.close(fig)


if __name__ == '__main__':
    main()
