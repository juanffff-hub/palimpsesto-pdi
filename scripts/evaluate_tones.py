"""¿Cuánto detalle recortan los ajustes de mejora? (histograma y aviso del paso 4)

Para 240 fotos reales (una de cada dos del manifiesto, las tres clases) se propone
el borde, se rectifica y se aplica cada ajuste con imaging.enhance; luego se mide
con imaging.compare_metrics el porcentaje de la imagen que el ajuste llevó a negro
(<= 2) o blanco (>= 253) puros. El aviso del paso 4 salta si supera imaging.CLIP_WARN.

  python scripts/evaluate_tones.py --root "C:\\ruta\\datos"
"""
from pathlib import Path
import argparse, csv, json, sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
from PIL import Image, ImageOps
from palimpsesto.models import ModelService, CLASSES
from palimpsesto.imaging import detect_quad, rectify, enhance, compare_metrics, PRESETS, CLIP_WARN

OUT = ROOT / 'results/tones'
SETTINGS = {'preajuste': {}, 'todo_al_50': dict(illumination=.5, contrast=.5, sharpness=.5),
            'iluminacion_100': dict(illumination=1, contrast=0, sharpness=0), 'contraste_100': dict(illumination=0, contrast=1, sharpness=0),
            'nitidez_100': dict(illumination=0, contrast=0, sharpness=1), 'todo_al_100': dict(illumination=1, contrast=1, sharpness=1)}
LABELS = {'preajuste': 'Preajuste de la clase', 'todo_al_50': 'Iluminación, contraste y nitidez al 50 %', 'iluminacion_100': 'Iluminación al 100 %',
          'contraste_100': 'Contraste local al 100 %', 'nitidez_100': 'Nitidez al 100 %', 'todo_al_100': 'Los tres al 100 %'}
NAMES = {'documento_impreso': 'Impreso', 'manuscrito': 'Manuscrito', 'pintura': 'Pintura'}


def figure(ev):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    INK, BG, COLORS = '#173d36', '#f8f8f5', {'documento_impreso': '#8aa89a', 'manuscrito': '#23594f', 'pintura': '#c4955b'}
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'axes.spines.top': False, 'axes.spines.right': False, 'figure.facecolor': BG, 'axes.facecolor': BG,
                         'axes.edgecolor': INK, 'axes.labelcolor': INK, 'xtick.color': INK, 'ytick.color': INK})
    keys = list(SETTINGS)[::-1]; y = np.arange(len(keys)); h = .26
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    for i, c in enumerate(CLASSES):
        vals = [ev['ajustes'][k]['por_clase'][c]['fotos_con_aviso_pct'] for k in keys]
        bars = ax.barh(y + (1 - i) * h, vals, h, color=COLORS[c], label=NAMES[c])
        for b in bars:
            ax.text(b.get_width() + .4, b.get_y() + b.get_height() / 2, f'{b.get_width():.0f} %', va='center', fontsize=7.5, color=INK)
    ax.set_yticks(y, [LABELS[k] for k in keys]); ax.set_xlim(0, max(25, max(ev['ajustes'][k]['por_clase'][c]['fotos_con_aviso_pct'] for k in keys for c in CLASSES) + 6))
    ax.set_xlabel(f'Fotos en las que el ajuste quema u oscurece más del {CLIP_WARN:g} % de la imagen')
    ax.set_title('¿Cuándo un ajuste destruye detalle?', fontweight='bold', color=INK)
    ax.legend(loc='lower right', fontsize=8.5, frameon=False)
    fig.text(.01, .01, '240 fotos reales (80 por clase), rectificadas con el borde de la U-Net. Recorte = píxeles que el ajuste llevó a ≤ 2 o ≥ 253 y antes no lo estaban.', fontsize=7.2, color='#5a6f64')
    fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(ROOT / 'results/figures/tonos_recortados.png', dpi=150); plt.close(fig)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--root', required=True); args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True); ms = ModelService(ROOT / 'models'); rows = []
    for r in list(csv.DictReader(open(ROOT / 'data/manifest.csv', encoding='utf-8-sig')))[::2]:
        rgb = np.asarray(ImageOps.exif_transpose(Image.open(Path(args.root) / r['path'].replace(chr(92), '/'))).convert('RGB'))
        before, _ = rectify(rgb, detect_quad(rgb, ms, r['class'])['points'], 0, max_side=2400)
        for name, s in SETTINGS.items():
            after, p = enhance(before, {**PRESETS[r['class']], **s}, r['class']); c = compare_metrics(before, after)['clipping']
            rows.append({'image_id': r['image_id'], 'class': r['class'], 'ajuste': name, 'recorte_blanco_pct': c['new_bright_percent'],
                         'recorte_negro_pct': c['new_dark_percent'], 'aviso': c['warning']})
    with open(OUT / 'per_image.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, list(rows[0]), lineterminator='\n'); w.writeheader(); w.writerows(rows)
    def stats(xs):
        t = np.array([x['recorte_blanco_pct'] + x['recorte_negro_pct'] for x in xs])
        return {'fotos': len(xs), 'fotos_con_aviso': int(sum(x['aviso'] for x in xs)), 'fotos_con_aviso_pct': round(100 * float(np.mean([x['aviso'] for x in xs])), 1),
                'recorte_mediano_pct': round(float(np.median(t)), 3), 'recorte_p90_pct': round(float(np.percentile(t, 90)), 3), 'recorte_max_pct': round(float(t.max()), 3)}
    ev = {'umbral_aviso_pct': CLIP_WARN, 'ajustes': {k: {**stats([x for x in rows if x['ajuste'] == k]),
                                                    'por_clase': {c: stats([x for x in rows if x['ajuste'] == k and x['class'] == c]) for c in CLASSES}} for k in SETTINGS}}
    (OUT / 'evaluation.json').write_text(json.dumps(ev, indent=2, ensure_ascii=False), encoding='utf-8')
    figure(ev); print(json.dumps(ev, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
