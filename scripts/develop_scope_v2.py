"""Control de alcance v2: desarrollo y comparación de métodos (sin la prueba ciega).

Datos permitidos:
- Positivos: data/manifest.csv. Las 408 de desarrollo (split train/val) ajustan; las 72 de
  diagnóstico (split test) solo se usan como comprobación de regresión (conjunto reutilizado).
- Negativos de desarrollo v2: data/scope_negatives_dev_v2.csv (88 fotos en 47 grupos de identidad).
- Los 30 negativos v1 (ya abiertos) solo se informan como referencia; no ajustan nada.
- La prueba ciega v2 no se lee aquí.

Rasgos: encoder ResNet18 congelado del clasificador v0.3.0 (512, normalizados L2), calculados
(1) sobre la foto entera, como la v0.4.0, y (2) sobre el recorte de la pieza que propone la U-Net
(models.piece_crop). Métodos: filtro v0.4.0 (similitud top-3), regresión logística binaria con
clases ponderadas, distancia de Mahalanobis (covarianza Ledoit-Wolf) y, como alternativa más
compleja, regresión sobre recorte + 5 descriptores de la máscara.
Validación cruzada por grupos (5 folds, StratifiedGroupKFold, semilla 2026). Umbral de cada
método: el que acepta el 97 % de los positivos de desarrollo fuera de fold (criterio de la v0.4.0).
Elección predeclarada: la familia más sencilla que cumple la puerta de desarrollo; dentro de ella,
la C con mayor sensibilidad a negativos (empate: menor C).

  python scripts/develop_scope_v2.py --root "C:\\ruta\\datos" --neg "C:\\ruta\\01_desarrollo_negativos_v2" [--v1 "C:\\ruta\\negativos_alcance_v1"] [--save]
"""
from pathlib import Path
import argparse, csv, hashlib, json, sys, time
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np, torch
from PIL import Image, ImageOps
from sklearn.linear_model import LogisticRegression
from sklearn.covariance import LedoitWolf
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from palimpsesto.models import ModelService, CLASSES, piece_crop
from palimpsesto.imaging import detect_quad

OUT = ROOT / 'results/scope_v2'
SEED, FOLDS, ACCEPT = 2026, 5, .97
C_GRID = [.01, .1, 1., 10.]
GATE = {'negativos_alertados_min': .85, 'positivos_aceptados_min': .95, 'aceptacion_por_clase_min': .90}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    with Image.open(path) as im:
        return np.asarray(ImageOps.exif_transpose(im).convert('RGB'))


def describe(ms, rgb):
    """Rasgos de la foto entera, del recorte de la pieza y 5 descriptores de la máscara."""
    prob = ms.segment(rgb); res = detect_quad(rgb, ms, 'documento_impreso', 'unet', prob=prob); c = res['confidence']
    m = prob > .5
    desc = [float(m.mean()), c['fit'] if c else 0., min(c['band'], 20) / 20 if c else 1., float(res['method'] == 'unet'), float(np.abs(prob - .5).mean() * 2)]
    return ms.features(rgb), ms.features(piece_crop(rgb, prob)), np.array(desc, np.float32)


def all_features(ms, args, pos_rows, neg_rows, v1_rows):
    cache = OUT / 'features.npz'
    key = ''.join(sha256(p) for p in (ROOT / 'data/manifest.csv', ROOT / 'data/scope_negatives_dev_v2.csv', ROOT / 'models/classifier.pt',
                                      ROOT / 'models/unet_resnet18_3clases.pth', ROOT / 'palimpsesto/models.py')) + str(len(v1_rows))
    if cache.exists():
        with np.load(cache, allow_pickle=False) as c:
            if str(c['key']) == key:
                return {k: c[k] for k in c.files if k != 'key'}
    paths = [Path(args.root) / r['path'].replace(chr(92), '/') for r in pos_rows]
    for r in neg_rows:
        p = next(Path(args.neg).glob(f"*/{r['image_id']}_*.jpg")); assert sha256(p) == r['sha256'], p; paths.append(p)
    paths += [Path(args.v1) / r['final_path'] for r in v1_rows]
    full, crop, desc = zip(*[describe(ms, load(p)) for p in paths])
    data = {'full': np.stack(full), 'crop': np.stack(crop), 'desc': np.stack(desc)}
    np.savez_compressed(cache, key=key, **data)
    return data


def lr(C, scaled=False):
    m = LogisticRegression(C=C, class_weight='balanced', max_iter=5000)
    return make_pipeline(StandardScaler(), m) if scaled else m


def summary(sp, cls, sn, lab, t):
    acc = sp >= t; alert = sn < t
    tp, fn, tn, fp = int(alert.sum()), int((~alert).sum()), int(acc.sum()), int((~acc).sum())
    per_class = {c: round(float(acc[cls == c].mean()), 4) for c in CLASSES}
    out = {'negativos_alertados': f'{tp}/{len(alert)}', 'sensibilidad_negativos': round(tp / len(alert), 4),
           'positivos_aceptados': f'{tn}/{len(acc)}', 'aceptacion_positivos': round(tn / len(acc), 4), 'aceptacion_por_clase': per_class,
           'alertas_por_categoria': {l: f'{int(alert[lab == l].sum())}/{int((lab == l).sum())}' for l in sorted(set(lab))},
           'balanced_accuracy': round((tp / len(alert) + tn / len(acc)) / 2, 4),
           'matriz_confusion': {'valida_aceptada': tn, 'valida_rechazada': fp, 'ajena_alertada': tp, 'ajena_aceptada': fn}}
    out['cumple_puerta_desarrollo'] = bool(out['sensibilidad_negativos'] >= GATE['negativos_alertados_min'] and out['aceptacion_positivos'] >= GATE['positivos_aceptados_min']
                                           and min(per_class.values()) >= GATE['aceptacion_por_clase_min'])
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--root', required=True); ap.add_argument('--neg', required=True); ap.add_argument('--v1')
    ap.add_argument('--save', action='store_true', help='Guardar el método elegido en models/scope_head.npz')
    args = ap.parse_args()
    if any(s in (args.neg + str(args.v1)) for s in ('NO_ABRIR', 'prueba_ciega')):
        raise SystemExit('Este script no admite la prueba ciega.')
    OUT.mkdir(parents=True, exist_ok=True); torch.set_num_threads(4)
    ms = ModelService(ROOT / 'models'); assert ms.encoder is not None and ms.segmenter is not None
    pos_rows = list(csv.DictReader(open(ROOT / 'data/manifest.csv', encoding='utf-8-sig')))
    neg_rows = list(csv.DictReader(open(ROOT / 'data/scope_negatives_dev_v2.csv', encoding='utf-8')))
    v1_rows = list(csv.DictReader(open(ROOT / 'data/external_negative_scope_v1.csv', encoding='utf-8-sig'))) if args.v1 else []
    F = all_features(ms, args, pos_rows, neg_rows, v1_rows)
    P, N = len(pos_rows), len(neg_rows)
    split = np.array([r['split'] for r in pos_rows]); cls = np.array([r['class'] for r in pos_rows]); pgrp = np.array([r['group_id'] for r in pos_rows])
    dev, diag = split != 'test', split == 'test'
    nlab = np.array([r['label'] for r in neg_rows]); ngrp = np.array([r['group_id'] for r in neg_rows])
    pos_idx, neg_idx = np.where(dev)[0], P + np.arange(N)
    idx = np.r_[pos_idx, neg_idx]; y = np.r_[np.ones(len(pos_idx), int), np.zeros(N, int)]; g = np.r_[pgrp[dev], ngrp]
    folds = list(StratifiedGroupKFold(FOLDS, shuffle=True, random_state=SEED).split(idx, y, g))
    assert all(not set(g[tr]) & set(g[va]) for tr, va in folds)
    cd = cls[dev]; npos = len(pos_idx)
    sets = {'foto': F['full'], 'recorte': F['crop'], 'recorte+mascara': np.hstack([F['crop'], F['desc']])}

    methods, oof, final = {}, {}, {}
    # (a) Línea base v0.4.0: banco de positivos de desarrollo; los positivos sin su propio grupo, como en su calibración.
    with np.load(ROOT / 'models/scope_reference.npz', allow_pickle=False) as ref:
        t0 = float(ref['threshold']); bank = ref['features']
    Xd = F['full'][pos_idx]; S = Xd @ Xd.T; S[pgrp[dev][:, None] == pgrp[dev][None, :]] = -1
    sp = np.sort(S, 1)[:, -3:].mean(1); sn = np.sort(F['full'][neg_idx] @ Xd.T, 1)[:, -3:].mean(1)
    methods['v0.4.0 · similitud top-3 (foto)'] = {'familia': 'linea_base', 'umbral': t0, 'fuera_de_fold': summary(sp, cd, sn, nlab, t0)}
    final['v0.4.0 · similitud top-3 (foto)'] = lambda X, B=bank: np.sort(X @ B.T, 1)[:, -3:].mean(1)
    # (b) Regresión logística y (c) Mahalanobis, por conjunto de rasgos.
    for fs in ('foto', 'recorte', 'recorte+mascara'):
        X = sets[fs][idx]; scaled = fs == 'recorte+mascara'
        for C in C_GRID:
            s = np.zeros(len(X))
            for tr, va in folds:
                s[va] = lr(C, scaled).fit(X[tr], y[tr]).predict_proba(X[va])[:, 1]
            t = float(np.quantile(s[:npos], 1 - ACCEPT)); name = f'regresión logística · {fs} · C={C:g}'
            methods[name] = {'familia': f'regresion_{fs}', 'C': C, 'umbral': t, 'fuera_de_fold': summary(s[:npos], cd, s[npos:], nlab, t)}
            oof[name] = s
            m = lr(C, scaled).fit(X, y); final[name] = lambda Z, m=m: m.predict_proba(Z)[:, 1]
        if fs != 'recorte+mascara':
            s = np.zeros(len(X))
            for tr, va in folds:
                pm = X[tr][y[tr] == 1]; mu, Pm = pm.mean(0), LedoitWolf().fit(pm).precision_; d = X[va] - mu
                s[va] = -np.einsum('ij,jk,ik->i', d, Pm, d)
            t = float(np.quantile(s[:npos], 1 - ACCEPT)); name = f'Mahalanobis · {fs}'
            methods[name] = {'familia': f'mahalanobis_{fs}', 'umbral': t, 'fuera_de_fold': summary(s[:npos], cd, s[npos:], nlab, t)}
            pm = X[:npos]; mu, Pm = pm.mean(0), LedoitWolf().fit(pm).precision_
            final[name] = lambda Z, mu=mu, Pm=Pm: -np.einsum('ij,jk,ik->i', Z - mu, Pm, Z - mu)

    # Elección predeclarada: familias de más sencilla a más compleja; dentro, mayor sensibilidad (empate: menor C).
    order = ['linea_base', 'regresion_foto', 'mahalanobis_foto', 'regresion_recorte', 'mahalanobis_recorte', 'regresion_recorte+mascara']
    chosen = None
    for fam in order:
        ok = [n for n, v in methods.items() if v['familia'] == fam and v['fuera_de_fold']['cumple_puerta_desarrollo']]
        if ok:
            chosen = max(ok, key=lambda n: (methods[n]['fuera_de_fold']['sensibilidad_negativos'], -methods[n].get('C', 0))); break

    # Regresión positiva (72 reutilizadas) y referencia v1 (30 ya abiertas) para la línea base y la elegida.
    def feats(name, rows):
        return sets['foto' if 'foto' in name else 'recorte+mascara' if 'mascara' in name else 'recorte'][rows]
    for name in ['v0.4.0 · similitud top-3 (foto)'] + ([chosen] if chosen else []):
        t = methods[name]['umbral']; acc = final[name](feats(name, np.where(diag)[0])) >= t
        methods[name]['regresion_positiva_72'] = {'aceptadas': f'{int(acc.sum())}/{len(acc)}', 'aceptacion': round(float(acc.mean()), 4),
                                                  'por_clase': {c: f'{int(acc[cls[diag] == c].sum())}/{int((cls[diag] == c).sum())}' for c in CLASSES}}
        if v1_rows:
            al = final[name](feats(name, P + N + np.arange(len(v1_rows)))) < t; vl = np.array([r['label'] for r in v1_rows])
            methods[name]['referencia_v1_30_ya_abiertas'] = {'alertadas': f'{int(al.sum())}/30', **{l: f'{int(al[vl == l].sum())}/{int((vl == l).sum())}' for l in sorted(set(vl))}}

    # Tiempo en CPU del control elegido: segmentación ya calculada en la app; se mide recorte + encoder + cabeza.
    timing = None
    if chosen and 'foto' not in chosen:
        rgb = load(Path(args.root) / pos_rows[0]['path'].replace(chr(92), '/')); prob = ms.segment(rgb); ts = []
        for _ in range(20):
            t1 = time.perf_counter(); ms.features(piece_crop(rgb, prob)); ts.append(time.perf_counter() - t1)
        timing = round(1000 * float(np.median(ts)), 1)

    if chosen:  # casos que siguen fallando fuera de fold
        s = oof[chosen]; t = methods[chosen]['umbral']
        methods[chosen]['fallos_fuera_de_fold'] = {
            'validas_rechazadas': [f"{pos_rows[i]['image_id']} ({pos_rows[i]['class']}, {pos_rows[i]['group_id']})" for k, i in enumerate(pos_idx) if s[k] < t],
            'ajenas_no_alertadas': [f"{r['image_id']} {r['content']} ({r['label']})" for k, r in enumerate(neg_rows) if s[npos + k] >= t]}
    report = {'datos': {'positivos_desarrollo': int(dev.sum()), 'grupos_positivos': len(set(pgrp[dev])), 'negativos_desarrollo': N,
                        'grupos_negativos': len(set(ngrp)), 'positivos_regresion_reutilizados': int(diag.sum()),
                        'manifest_sha256': sha256(ROOT / 'data/manifest.csv'), 'negativos_sha256': sha256(ROOT / 'data/scope_negatives_dev_v2.csv'),
                        'classifier_sha256': sha256(ROOT / 'models/classifier.pt'), 'unet_sha256': sha256(ROOT / 'models/unet_resnet18_3clases.pth')},
              'validacion': f'{FOLDS} folds StratifiedGroupKFold por pieza/identidad, semilla {SEED}; umbral = aceptar {ACCEPT:.0%} de positivos fuera de fold',
              'puerta_desarrollo': GATE, 'metodo_elegido': chosen, 'tiempo_control_ms_cpu': timing, 'metodos': methods}
    (OUT / 'development.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    if args.save and chosen:
        m = methods[chosen]; assert m['familia'] == 'regresion_recorte', 'La app solo implementa la regresión sobre el recorte.'
        model = lr(m['C']).fit(sets['recorte'][idx], y)
        np.savez(ROOT / 'models/scope_head.npz', coef=model.coef_[0].astype(np.float64), intercept=float(model.intercept_[0]), threshold=m['umbral'], C=m['C'],
                 classifier_sha256=report['datos']['classifier_sha256'], unet_sha256=report['datos']['unet_sha256'], manifest_sha256=report['datos']['manifest_sha256'],
                 negatives_sha256=report['datos']['negativos_sha256'], method='logistic regression on U-Net piece crop, frozen ResNet18 features; valid if p >= threshold')
    for n, v in methods.items():
        f = v['fuera_de_fold']
        print(f"{n:45s} neg {f['negativos_alertados']:>6s} pos {f['positivos_aceptados']:>7s} min_clase {min(f['aceptacion_por_clase'].values()):.3f} puerta {f['cumple_puerta_desarrollo']}")
    print('elegido:', chosen, '| tiempo ms:', timing)
    if chosen: print(json.dumps({k: methods[chosen].get(k) for k in ('regresion_positiva_72', 'referencia_v1_30_ya_abiertas', 'fallos_fuera_de_fold')}, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
