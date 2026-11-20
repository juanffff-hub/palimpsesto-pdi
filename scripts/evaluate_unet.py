"""Compara la U-Net de 3 clases con la U-Net anterior, los contornos y el sistema v0.3.0.

Usa la misma función de la aplicación (imaging.detect_quad) para proponer el
borde, así que la cifra corresponde a lo que ve la persona en el paso 3.
La regla de adopción está fijada en results/segmentation/protocol.json.

  python scripts/evaluate_unet.py --data "C:\\ruta\\PDI_Segmentacion_3clases"
"""
from pathlib import Path
import argparse, csv, json, sys, time
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np, cv2, torch
from PIL import Image, ImageOps
import segmentation_models_pytorch as smp
from palimpsesto.imaging import detect_quad, resize_long

CLASSES = ['documento_impreso', 'manuscrito', 'pintura']
SEEDS = [42, 7, 2026]
OUT = ROOT / 'results/segmentation'


class Segmenter:
    """Mismo preproceso que ModelService.segment."""
    def __init__(self, path):
        self.net = smp.Unet(encoder_name='resnet18', encoder_weights=None, in_channels=3, classes=1)
        self.net.load_state_dict(torch.load(path, map_location='cpu', weights_only=True)['state_dict'], strict=True)
        self.net.eval(); self.seconds = []

    @torch.inference_mode()
    def segment(self, rgb):
        t = time.perf_counter()
        a = cv2.resize(rgb, (256, 256), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
        a = (a - np.array([.485, .456, .406], np.float32)) / np.array([.229, .224, .225], np.float32)
        p = self.net(torch.from_numpy(a.transpose(2, 0, 1).copy()).unsqueeze(0)).sigmoid()[0, 0].numpy()
        self.seconds.append(time.perf_counter() - t)
        return p


def overlap(a, b):
    i = np.logical_and(a, b).sum(); u = np.logical_or(a, b).sum(); s = a.sum() + b.sum()
    return (i / u if u else 1.), (2 * i / s if s else 1.)


def quad_iou(result, gt_small):
    if result['method'] == 'manual':
        return 0., False
    h, w = gt_small.shape
    q = np.round(np.asarray(result['points']) * [w - 1, h - 1]).astype(np.int32)
    pred = np.zeros_like(gt_small); cv2.fillPoly(pred, [q], 1)
    return overlap(pred > 0, gt_small > 0)[0], True


def summarize(rows, key):
    v = np.array([r[f'{key}_quad_iou'] for r in rows])
    out = {'n': len(rows), 'quad_iou_mean': round(float(v.mean()), 4), 'quad_iou_median': round(float(np.median(v)), 4),
           'iou_ge_90': int((v >= .9).sum()), 'iou_ge_95': int((v >= .95).sum()),
           'detected': int(sum(r[f'{key}_detected'] for r in rows))}
    if f'{key}_mask_dice' in rows[0]:
        out['mask_dice_256_mean'] = round(float(np.mean([r[f'{key}_mask_dice'] for r in rows])), 4)
        out['mask_iou_256_mean'] = round(float(np.mean([r[f'{key}_mask_iou'] for r in rows])), 4)
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--data', required=True); args = ap.parse_args()
    data = Path(args.data); torch.set_num_threads(4); cv2.setNumThreads(2)
    protocol = json.loads((OUT / 'protocol.json').read_text(encoding='utf-8'))
    rows = list(csv.DictReader(open(ROOT / 'data/segmentation_manifest.csv', encoding='utf-8')))
    old = Segmenter(ROOT / 'models/unet_resnet18_imagenet.pth'); new = Segmenter(ROOT / 'models/unet_resnet18_3clases.pth')
    seeds = {s: Segmenter(ROOT / ('models/unet_resnet18_3clases.pth' if s == 42 else f'models/unet_3clases_seed{s}.pth')) for s in SEEDS[1:]}
    results = []
    for r in rows:
        img = next((data / 'images').glob(r['file'] + '.*'))
        rgb = np.asarray(ImageOps.exif_transpose(Image.open(img)).convert('RGB'))
        gt = cv2.imread(str(data / 'masks' / (r['file'] + '.png')), cv2.IMREAD_GRAYSCALE) > 0
        small = resize_long(rgb, 960); gt_small = cv2.resize(gt.astype(np.uint8), small.shape[1::-1], interpolation=cv2.INTER_NEAREST)
        gt256 = cv2.resize(gt.astype(np.uint8), (256, 256), interpolation=cv2.INTER_NEAREST) > 0
        kind = r['class']; row = {k: r[k] for k in ('file', 'class', 'group_id', 'split')}
        systems = {
            'sistema_actual': (old, 'contornos' if kind == 'pintura' else 'unet'),
            'unet_anterior': (old, 'unet'),
            'contornos': (old, 'contornos'),
            'unet_3clases': (new, 'unet')}
        if r['split'] == 'test':
            systems.update({f'seed{s}': (m, 'unet') for s, m in seeds.items()})
        for name, (model, method) in systems.items():
            res = detect_quad(rgb, model, kind, method)
            row[f'{name}_quad_iou'], row[f'{name}_detected'] = quad_iou(res, gt_small)
            row[f'{name}_source'] = res['method']
        for name, model in (('unet_anterior', old), ('unet_3clases', new)):
            pred = model.segment(rgb) > .5
            row[f'{name}_mask_iou'], row[f'{name}_mask_dice'] = overlap(pred, gt256)
        results.append(row)
    fields = list(results[0]); [fields.append(k) for r in results for k in r if k not in fields]
    with open(OUT / 'per_image.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fields, lineterminator='\n'); w.writeheader()
        for r in results:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})

    summary = {}
    for split in ('test', 'val', 'train'):
        for c in CLASSES:
            part = [r for r in results if r['split'] == split and r['class'] == c]
            summary.setdefault(split, {})[c] = {s: summarize(part, s) for s in ('sistema_actual', 'unet_anterior', 'contornos', 'unet_3clases')}
    test = summary['test']
    seed_means = {}
    for s in SEEDS:
        key = 'unet_3clases' if s == 42 else f'seed{s}'
        seed_means[s] = {c: float(np.mean([r[f'{key}_quad_iou'] for r in results if r['split'] == 'test' and r['class'] == c])) for c in CLASSES}
    macro = lambda sys_: float(np.mean([test[c][sys_]['quad_iou_mean'] for c in CLASSES]))
    seed_macro = float(np.mean([np.mean(list(v.values())) for v in seed_means.values()]))
    checks = {
        'macro': macro('unet_3clases') >= macro('sistema_actual') + .03,
        'per_class': all(test[c]['unet_3clases']['quad_iou_mean'] >= test[c]['sistema_actual']['quad_iou_mean'] - .01 for c in CLASSES),
        'detections': all(test[c]['unet_3clases']['detected'] >= test[c]['sistema_actual']['detected'] for c in CLASSES),
        'seeds': seed_macro >= macro('sistema_actual') + .03}
    evaluation = {
        'protocol': protocol['adoption_rule'], 'metric': protocol['primary_metric'],
        'macro_test': {s: round(macro(s), 4) for s in ('sistema_actual', 'unet_anterior', 'contornos', 'unet_3clases')},
        'seeds_test': {str(s): {c: round(v, 4) for c, v in m.items()} | {'macro': round(float(np.mean(list(m.values()))), 4)} for s, m in seed_means.items()},
        'seeds_macro_mean': round(seed_macro, 4),
        'seeds_macro_std': round(float(np.std([np.mean(list(m.values())) for m in seed_means.values()])), 4),
        'checks': checks, 'adopted': all(checks),
        'median_ms_cpu': {'unet_anterior': round(1000 * float(np.median(old.seconds)), 1), 'unet_3clases': round(1000 * float(np.median(new.seconds)), 1)},
        'runtime': {'torch': torch.__version__, 'smp': smp.__version__, 'opencv': cv2.__version__, 'threads': 4,
                    'checkpoint': {k: v for k, v in torch.load(ROOT / 'models/unet_resnet18_3clases.pth', map_location='cpu', weights_only=True).items() if k != 'state_dict'}},
        'summary': summary}
    (OUT / 'evaluation.json').write_text(json.dumps(evaluation, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({k: evaluation[k] for k in ('macro_test', 'seeds_test', 'seeds_macro_mean', 'checks', 'adopted', 'median_ms_cpu')}, indent=1))
    for c in CLASSES:
        print(c, {s: (v['quad_iou_mean'], v['detected'], v['iou_ge_95']) for s, v in test[c].items()})


if __name__ == '__main__':
    main()
