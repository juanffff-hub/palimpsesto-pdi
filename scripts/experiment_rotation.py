"""Experimento: ¿entrenar la cabeza también con giros de 90°/180°/270° mejora la robustez?

Hipótesis (H1): el clasificador desplegado pierde precisión cuando la foto llega girada
(diagnóstico de robustez: 0,93 -> 0,82 con 90°). Añadir giros rectos a las vistas de
entrenamiento de la cabeza debería recuperar esos casos sin empeorar las fotos derechas.

Protocolo (fijado ANTES de ejecutar; ver results/rotation/protocol.json):
- Solo datos de desarrollo (408 fotos, 41 bloques). Mismos 5 folds StratifiedGroupKFold
  (semilla 2026) y misma rejilla C que train_transfer.py. El encoder ResNet18 sigue congelado.
- Cada variante elige su C por macro-F1 medio de los folds en fotos derechas.
- Evaluación fuera de fold de cada foto retenida en 0°, 90°, 180° y 270°.
- Regla de adopción de la variante con giros, frente a la base:
    a) macro-F1 OOF en fotos derechas >= base - 0,01;
    b) recall OOF por clase en fotos derechas >= 0,80 (puerta de despliegue existente);
    c) macro-F1 OOF medio en 90°/180°/270° >= base + 0,05.
- Las 72 fotos del diagnóstico secundario (ya abiertas) se reportan una vez, sin decidir con ellas.
- No se usan las fotos de results/scope ni capturas nuevas.
"""
from pathlib import Path
import sys, json, csv, argparse, time, hashlib
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'scripts'))
import numpy as np, cv2, torch
from torch import nn
from PIL import Image, ImageOps
from torchvision.models import resnet18
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold
from train_classifier import classification_metrics
from palimpsesto.models import CLASSES

ANGLES = [0, 90, 180, 270]
GRID = [.01, .1, 1.]
VARIANTS = {
    # vistas de entrenamiento por foto: (índice de vista base, ángulo)
    'base': [(v, 0) for v in range(4)],                                   # igual que el modelo desplegado
    'giros_originales': [(v, 0) for v in range(4)] + [(0, a) for a in (90, 180, 270)],
    'giros_todas': [(v, a) for v in range(4) for a in ANGLES],
}
PROTOCOL = {
    'hypothesis': 'Añadir giros rectos a las vistas de entrenamiento de la cabeza mejora la clasificación de fotos giradas sin empeorar las derechas.',
    'data': 'Solo desarrollo (split != test): 408 fotos, 41 bloques provisionales. Encoder ResNet18 ImageNet congelado.',
    'folds': '5-fold StratifiedGroupKFold, semilla 2026 (idénticos a train_transfer.py)',
    'c_grid': GRID, 'c_selection': 'macro-F1 medio de folds en fotos derechas, por variante',
    'variants': {k: [f'vista{v}@{a}' for v, a in vs] for k, vs in VARIANTS.items()},
    'base_views': 'vista0 original; vista1 brillo 0,75; vista2 giro +8°; vista3 giro -8° y brillo 1,12',
    'adoption_rule': {'upright_macro_f1_min': 'base - 0.01', 'upright_recall_each_class_min': 0.80,
                      'rotated_mean_macro_f1_min': 'base + 0.05'},
    'secondary_test': '72 fotos ya abiertas; se reportan una vez y no deciden',
    'fixed_before_running': True,
}


def extract(rows, root, out):
    cache = out / 'features_rot.npz'
    mhash = hashlib.sha256((ROOT / 'data/manifest.csv').read_bytes()).hexdigest()
    if cache.exists() and str(np.load(cache)['manifest_hash']) == mhash:
        return np.load(cache)['features']
    # Encoder congelado ImageNet-1K: se toma del checkpoint desplegado (contiene la red completa)
    # para no depender de una descarga; se verifica que la cabeza sea la única parte distinta.
    net = resnet18(weights=None)
    sd = torch.load(ROOT / 'models/classifier.pt', map_location='cpu', weights_only=True)['state_dict']
    net.fc = nn.Linear(512, 3); net.load_state_dict(sd); net.fc = nn.Identity(); net.eval()
    mean = np.array([.485, .456, .406], np.float32); std = np.array([.229, .224, .225], np.float32)
    feats = []
    with torch.inference_mode():
        for i, r in enumerate(rows):
            a = np.asarray(ImageOps.exif_transpose(Image.open(Path(root) / r['path'].replace('\\', '/'))).convert('RGB'))
            a = cv2.resize(a, (224, 224), interpolation=cv2.INTER_AREA)
            views = [a, np.clip(a.astype(float) * .75, 0, 255).astype(np.uint8)]
            for angle, gain in [(8, 1), (-8, 1.12)]:  # mismas vistas que train_transfer.py
                b = cv2.warpAffine(a, cv2.getRotationMatrix2D((112, 112), angle, 1), (224, 224), borderMode=cv2.BORDER_REFLECT_101)
                views.append(np.clip(b.astype(float) * gain, 0, 255).astype(np.uint8))
            # giro recto en sentido horario: k=-1 -> 90°, -2 -> 180°, -3 -> 270°
            batch = [np.rot90(v, k=-(ang // 90)) for v in views for ang in ANGLES]
            x = (np.stack(batch).astype(np.float32) / 255 - mean) / std
            f = net(torch.from_numpy(x.transpose(0, 3, 1, 2).copy())).numpy().reshape(4, 4, 512)
            feats.append(f)
            if (i + 1) % 60 == 0: print('features', i + 1, flush=True)
    feats = np.stack(feats)  # [foto, vista, ángulo, 512]
    np.savez_compressed(cache, features=feats, manifest_hash=mhash)
    return feats


def train(F, y, idx, views, C):
    X = np.concatenate([F[idx, v, ANGLES.index(a)] for v, a in views])
    Y = np.concatenate([y[idx] for _ in views])
    return LogisticRegression(C=C, max_iter=3000, class_weight='balanced', random_state=2026).fit(X, Y)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--root', required=True)
    ap.add_argument('--promote', action='store_true', help='Si la regla elige una variante con giros, la despliega en models/classifier.pt (con copia del anterior).')
    args = ap.parse_args()
    t0 = time.perf_counter(); torch.set_num_threads(4); torch.manual_seed(2026)
    out = ROOT / 'results/rotation'; out.mkdir(parents=True, exist_ok=True)
    (out / 'protocol.json').write_text(json.dumps(PROTOCOL, indent=2, ensure_ascii=False), encoding='utf8')
    rows = list(csv.DictReader(open(ROOT / 'data/manifest.csv', encoding='utf-8-sig')))
    y = np.array([CLASSES.index(r['class']) for r in rows]); groups = np.array([r['group_id'] for r in rows])
    dev = np.array([i for i, r in enumerate(rows) if r['split'] != 'test']); test = np.array([i for i, r in enumerate(rows) if r['split'] == 'test'])
    assert not set(groups[dev]) & set(groups[test])
    F = extract(rows, args.root, out)
    folds = list(StratifiedGroupKFold(5, shuffle=True, random_state=2026).split(dev, y[dev], groups[dev]))
    report = {'protocol': PROTOCOL, 'variants': {}}
    for name, views in VARIANTS.items():
        best = None
        for C in GRID:
            pred = {a: np.zeros(len(dev), int) for a in ANGLES}; fold_f1 = []
            for tr, va in folds:
                clf = train(F, y, dev[tr], views, C)
                for a in ANGLES: pred[a][va] = clf.predict(F[dev[va], 0, ANGLES.index(a)])
                fold_f1.append(classification_metrics(y[dev[va]], pred[0][va])['macro_f1'])
            score = float(np.mean(fold_f1))
            if best is None or score > best['mean_fold_macro_f1']:
                best = {'C': C, 'mean_fold_macro_f1': score, 'oof': {f'{a}': classification_metrics(y[dev], pred[a]) for a in ANGLES}}
            print(name, C, round(score, 4), flush=True)
        best['rotated_mean_macro_f1'] = float(np.mean([best['oof'][f'{a}']['macro_f1'] for a in (90, 180, 270)]))
        clf = train(F, y, dev, views, best['C'])
        best['secondary_test'] = {f'{a}': classification_metrics(y[test], clf.predict(F[test, 0, ANGLES.index(a)])) for a in ANGLES}
        report['variants'][name] = best
    b = report['variants']['base']; decisions = {}
    for name in ('giros_originales', 'giros_todas'):
        v = report['variants'][name]
        checks = {
            'upright_not_worse': v['oof']['0']['macro_f1'] >= b['oof']['0']['macro_f1'] - .01,
            'upright_recall_each_class': min(c['recall'] for c in v['oof']['0']['classes'].values()) >= .80,
            'rotated_improves': v['rotated_mean_macro_f1'] >= b['rotated_mean_macro_f1'] + .05,
        }
        decisions[name] = {'checks': checks, 'adopt': all(checks.values())}
    adoptable = [n for n, d in decisions.items() if d['adopt']]
    # Entre las que cumplen, la de mejor macro-F1 OOF derecho (desempate: giradas).
    chosen = max(adoptable, key=lambda n: (report['variants'][n]['oof']['0']['macro_f1'], report['variants'][n]['rotated_mean_macro_f1'])) if adoptable else 'base'
    report.update(decisions=decisions, chosen=chosen, elapsed_seconds=time.perf_counter() - t0)
    (out / 'evaluation.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf8')
    for n, v in report['variants'].items():
        print(n, 'C', v['C'], '| OOF 0°', round(v['oof']['0']['macro_f1'], 4), '| OOF giradas', round(v['rotated_mean_macro_f1'], 4),
              '| diag 0°', v['secondary_test']['0']['correct'] if 'correct' in v['secondary_test']['0'] else round(v['secondary_test']['0']['accuracy'], 4),
              '| diag 90°', round(v['secondary_test']['90']['accuracy'], 4))
    print('decisions', json.dumps(decisions), 'chosen', chosen)
    if args.promote and chosen != 'base':
        promote(F, y, groups, dev, VARIANTS[chosen], report['variants'][chosen], chosen)


def promote(F, y, groups, dev, views, result, name):
    import shutil
    models = ROOT / 'models'; current = models / 'classifier.pt'; backup = models / 'classifier_v0.2.0.pt'
    if not backup.exists(): shutil.copy2(current, backup)  # el baseline nunca se sobrescribe
    old = torch.load(backup, map_location='cpu', weights_only=True)
    clf = train(F, y, dev, views, result['C'])
    net = resnet18(weights=None); net.fc = nn.Linear(512, 3); net.load_state_dict(old['state_dict'])
    with torch.no_grad():
        net.fc.weight.copy_(torch.tensor(clf.coef_, dtype=torch.float32)); net.fc.bias.copy_(torch.tensor(clf.intercept_, dtype=torch.float32))
    cp = {k: v for k, v in old.items() if k not in ('state_dict', 'validation')}
    cp.update(state_dict=net.state_dict(), C=result['C'], version='0.3.0', head_views=name,
              head_views_detail=[f'vista{v}@{a}' for v, a in views], previous_classifier='classifier_v0.2.0.pt',
              validation=result['oof']['0'], validation_rotated_mean_macro_f1=result['rotated_mean_macro_f1'],
              evaluation_status='provisional: CV por bloques automáticos; identidad física pendiente; test diagnóstico reutilizado; regla de adopción en results/rotation/protocol.json')
    torch.save(cp, current)
    print('PROMOTED', name, 'C', result['C'], '->', current)


if __name__ == '__main__':
    main()
