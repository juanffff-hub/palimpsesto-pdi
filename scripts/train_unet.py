"""U-Net de 3 clases (v0.4.0): misma receta del Parcial 3 con más datos.

Entrena con las fotos de entrenamiento de data/segmentation_manifest.csv y elige
el checkpoint por la pérdida de validación. La prueba no se usa aquí.

  python scripts/train_unet.py --data "C:\\ruta\\PDI_Segmentacion_3clases" --seed 42 --save
"""
from pathlib import Path
import argparse, csv, hashlib, json, random, sys, time
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np, cv2, torch
from PIL import Image, ImageOps
import segmentation_models_pytorch as smp

SIZE, BATCH, EPOCHS, LR = 256, 8, 35, 5e-4
MEAN = np.array([.485, .456, .406], np.float32); STD = np.array([.229, .224, .225], np.float32)
MANIFEST = ROOT / 'data/segmentation_manifest.csv'
WEIGHTS = ROOT / 'models/unet_resnet18_3clases.pth'


def seed_all(seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False; torch.backends.cudnn.deterministic = True


def read_rgb(path):
    return np.asarray(ImageOps.exif_transpose(Image.open(path)).convert('RGB'))


def load_split(data, rows, split):
    """Fotos y máscaras a 256x256: INTER_AREA para la foto y vecino más cercano para la máscara."""
    xs, ys = [], []
    for r in rows:
        if r['split'] != split:
            continue
        img = next((data / 'images').glob(r['file'] + '.*'))
        assert hashlib.sha256(img.read_bytes()).hexdigest() == r['sha256'], img
        rgb = read_rgb(img); mask = cv2.imread(str(data / 'masks' / (r['file'] + '.png')), cv2.IMREAD_GRAYSCALE)
        assert mask.shape == rgb.shape[:2], img
        xs.append(cv2.resize(rgb, (SIZE, SIZE), interpolation=cv2.INTER_AREA))
        ys.append((cv2.resize(mask, (SIZE, SIZE), interpolation=cv2.INTER_NEAREST) > 0).astype(np.uint8))
    return np.stack(xs), np.stack(ys)


def augment(x, y, rng):
    """Aumentos del Parcial 3: volteo horizontal y giro de hasta 12 grados, cada uno con p=0,5."""
    if rng.random() < .5:
        x, y = x[:, ::-1], y[:, ::-1]
    if rng.random() < .5:
        M = cv2.getRotationMatrix2D((SIZE / 2, SIZE / 2), rng.uniform(-12, 12), 1)
        x = cv2.warpAffine(np.ascontiguousarray(x), M, (SIZE, SIZE), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        y = cv2.warpAffine(np.ascontiguousarray(y), M, (SIZE, SIZE), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return x, y


def to_tensor(xs, ys):
    x = ((xs.astype(np.float32) / 255 - MEAN) / STD).transpose(0, 3, 1, 2)
    return torch.from_numpy(np.ascontiguousarray(x)), torch.from_numpy(np.ascontiguousarray(ys[:, None].astype(np.float32)))


def soft_dice_loss(logits, target, eps=1e-6):
    p = logits.sigmoid().flatten(1); t = target.flatten(1)
    return 1 - ((2 * (p * t).sum(1) + eps) / (p.square().sum(1) + t.square().sum(1) + eps)).mean()


def dice(pred, target):
    p = pred.flatten(1).bool(); t = target.flatten(1).bool(); s = p.sum(1) + t.sum(1)
    return torch.where(s > 0, 2. * (p & t).sum(1) / s.clamp_min(1), torch.ones_like(s, dtype=torch.float32))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True); ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--save', action='store_true', help='Guardar el checkpoint en models/ (solo la semilla desplegada)')
    args = ap.parse_args(); data = Path(args.data)
    seed_all(args.seed); device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    torch.hub.set_dir(str(ROOT / 'models/.download_cache'))
    rows = list(csv.DictReader(open(MANIFEST, encoding='utf-8')))
    xtr, ytr = load_split(data, rows, 'train'); xva, yva = load_split(data, rows, 'val')
    print(f'train {len(xtr)} | val {len(xva)} | {device}', flush=True)
    model = smp.Unet(encoder_name='resnet18', encoder_weights='imagenet', in_channels=3, classes=1, activation=None).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, mode='min', factor=.5, patience=3)
    rng = random.Random(args.seed); order = np.random.default_rng(args.seed)
    xv, yv = to_tensor(xva, yva); history = []; best = (float('inf'), None, 0, 0.)
    start = time.perf_counter()
    for epoch in range(1, EPOCHS + 1):
        model.train(); lr = opt.param_groups[0]['lr']; tl = td = 0.
        perm = order.permutation(len(xtr))
        for i in range(0, len(perm), BATCH):
            b = perm[i:i + BATCH]
            pairs = [augment(xtr[j], ytr[j], rng) for j in b]
            x, y = to_tensor(np.stack([p[0] for p in pairs]), np.stack([p[1] for p in pairs]))
            x, y = x.to(device), y.to(device)
            opt.zero_grad(set_to_none=True); logits = model(x); loss = soft_dice_loss(logits, y); loss.backward(); opt.step()
            tl += loss.item() * len(b); td += dice(logits.detach() > 0, y).sum().item()
        model.eval(); vl = vd = 0.
        with torch.inference_mode():
            for i in range(0, len(xv), BATCH):
                x, y = xv[i:i + BATCH].to(device), yv[i:i + BATCH].to(device); logits = model(x)
                vl += soft_dice_loss(logits, y).item() * len(x); vd += dice(logits > 0, y).sum().item()
        tl /= len(xtr); td /= len(xtr); vl /= len(xv); vd /= len(xv); sched.step(vl)
        history.append(dict(epoch=epoch, loss_train=round(tl, 5), dice_train=round(td, 5), loss_val=round(vl, 5), dice_val=round(vd, 5), lr=lr))
        print(f'{epoch:02d}/{EPOCHS} train {tl:.4f}/{td:.4f} val {vl:.4f}/{vd:.4f} lr {lr:.1e}', flush=True)
        if vl < best[0]:
            best = (vl, {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}, epoch, vd)
    out = ROOT / 'results/segmentation'; out.mkdir(parents=True, exist_ok=True)
    with open(out / f'history_seed{args.seed}.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, list(history[0]), lineterminator='\n'); w.writeheader(); w.writerows(history)
    checkpoint = {'state_dict': best[1], 'epoch': best[2], 'val_loss': best[0], 'val_dice': best[3], 'seed': args.seed,
                  'classes': ['documento_impreso', 'manuscrito', 'pintura'], 'version': '0.4.0',
                  'segmentation_manifest_sha256': hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
                  'recipe': 'smp.Unet resnet18 imagenet, 256, flip+rot12, SoftDice, Adam 5e-4, ReduceLROnPlateau, 35 epochs'}
    target = WEIGHTS if args.save else ROOT / f'models/unet_3clases_seed{args.seed}.pth'
    torch.save(checkpoint, target)
    print(json.dumps({'checkpoint': str(target.relative_to(ROOT)), 'best_epoch': best[2], 'val_loss': round(best[0], 5),
                      'val_dice': round(best[3], 5), 'minutes': round((time.perf_counter() - start) / 60, 2)}), flush=True)


if __name__ == '__main__':
    main()
