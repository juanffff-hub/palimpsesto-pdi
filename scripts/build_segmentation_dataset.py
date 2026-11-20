"""Dataset de segmentación de 3 clases para la U-Net (v0.4.0).

Une las 80 fotos y máscaras de documentos impresos del Parcial 3 con 80 fotos
de manuscritos y 80 de pinturas anotadas con polígonos en makesense.ai (COCO).
Las particiones son por pieza física: las fotos de un mismo bloque del
manifiesto nunca se reparten entre entrenamiento, validación y prueba.
Los impresos conservan exactamente la partición del Parcial 3 para que la
comparación con la U-Net anterior sea justa.

Uso:
  python scripts/build_segmentation_dataset.py --punto1 "...\\PDI_Punto1_Dataset" \
      --manuscrito "...\\Manuscrito" --pintura "...\\Pintura" --out "...\\segmentacion_3clases"
"""
from pathlib import Path
import argparse, csv, hashlib, json, random, shutil
import numpy as np, cv2
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SEED = 2026
PREFIX = {'documento_impreso': 'I', 'manuscrito': 'M', 'pintura': 'P'}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def split_groups(sizes, seed=SEED, share=.15, max_eval_group=8):
    """Reparte bloques completos: prueba y validación reciben ~15 % de las fotos cada una.

    Los bloques grandes (más de 8 fotos, agrupaciones conservadoras de varias
    capturas) quedan en entrenamiento para que una sola pieza no domine la prueba.
    """
    total = sum(sizes.values()); order = sorted(sizes); random.Random(seed).shuffle(order)
    split = {}; counts = {'test': 0, 'val': 0}
    for g in order:
        if sizes[g] > max_eval_group:
            split[g] = 'train'
        elif counts['test'] < share * total:
            split[g] = 'test'; counts['test'] += sizes[g]
        elif counts['val'] < share * total:
            split[g] = 'val'; counts['val'] += sizes[g]
        else:
            split[g] = 'train'
    return split


def polygon_mask(annotations, width, height):
    mask = np.zeros((height, width), np.uint8)
    for a in annotations:
        for poly in a['segmentation']:
            pts = np.round(np.asarray(poly, np.float64).reshape(-1, 2)).astype(np.int32)
            cv2.fillPoly(mask, [pts], 255)
    return mask


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--punto1', required=True, help='Carpeta PDI_Punto1_Dataset del Parcial 3')
    ap.add_argument('--manuscrito', required=True, help='80 fotos + anotaciones COCO de makesense.ai')
    ap.add_argument('--pintura', required=True, help='80 fotos + anotaciones COCO de makesense.ai')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    (out / 'images').mkdir(parents=True); (out / 'masks').mkdir()
    manifest = {r['sha256']: r for r in csv.DictReader(open(ROOT / 'data/manifest.csv', encoding='utf-8-sig'))}
    rows = []

    # 1. Impresos: fotos, máscaras y partición por documento del Parcial 3.
    p1 = Path(args.punto1)
    for r in csv.DictReader(open(p1 / 'particiones.csv', encoding='utf-8-sig')):
        if r['particion'] not in ('train', 'val', 'test'):
            continue
        img = p1 / r['archivo']; mask = p1 / 'masks' / r['particion'] / (img.stem + '.png')
        name = f"I_{img.stem}"
        shutil.copy2(img, out / 'images' / f'{name}.jpg'); shutil.copy2(mask, out / 'masks' / f'{name}.png')
        m = cv2.imread(str(mask), cv2.IMREAD_GRAYSCALE)
        rows.append(dict(file=name, **{'class': 'documento_impreso'}, group_id=r['grupo_documento'], split=r['particion'],
                         source=r['origen'], sha256=sha256(img), width=m.shape[1], height=m.shape[0],
                         mask_fraction=round(float((m > 127).mean()), 4), annotation='Parcial 3 (makesense.ai)'))

    # 2. Manuscritos y pinturas: polígonos COCO, bloques del manifiesto y partición por bloque.
    for kind, folder in (('manuscrito', Path(args.manuscrito)), ('pintura', Path(args.pintura))):
        coco_path = next(folder.glob('*.json'))
        coco = json.loads(coco_path.read_text(encoding='utf-8'))
        anns = {}
        for a in coco['annotations']:
            anns.setdefault(a['image_id'], []).append(a)
        items = []
        for im in coco['images']:
            path = folder / im['file_name']; ref = manifest[sha256(path)]
            assert ref['class'] == kind, (path, ref['class'])
            pil = ImageOps.exif_transpose(Image.open(path))
            assert pil.size == (im['width'], im['height']), path
            items.append((path, ref, polygon_mask(anns[im['id']], im['width'], im['height'])))
        sizes = {}
        for _, ref, _ in items:
            sizes[ref['group_id']] = sizes.get(ref['group_id'], 0) + 1
        split = split_groups(sizes)
        counter = {}
        for path, ref, mask in sorted(items, key=lambda t: (t[1]['group_id'], t[0].name)):
            g = ref['group_id']; counter[g] = counter.get(g, 0) + 1
            name = f"{PREFIX[kind]}_{g}_{counter[g]:02d}"
            shutil.copy2(path, out / 'images' / f'{name}{path.suffix.lower()}')
            cv2.imwrite(str(out / 'masks' / f'{name}.png'), mask)
            rows.append(dict(file=name, **{'class': kind}, group_id=g, split=split[g], source=ref['path'],
                             sha256=ref['sha256'], width=mask.shape[1], height=mask.shape[0],
                             mask_fraction=round(float((mask > 0).mean()), 4), annotation=f'{coco_path.name} (makesense.ai)'))

    fields = ['file', 'class', 'group_id', 'split', 'source', 'sha256', 'width', 'height', 'mask_fraction', 'annotation']
    for target in (out / 'segmentation_manifest.csv', ROOT / 'data/segmentation_manifest.csv'):
        with open(target, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fields, lineterminator='\n'); w.writeheader(); w.writerows(rows)
    summary = {}
    for r in rows:
        s = summary.setdefault(r['class'], {}).setdefault(r['split'], {'photos': 0, 'groups': set()})
        s['photos'] += 1; s['groups'].add(r['group_id'])
    for c in summary:
        for s in summary[c].values():
            s['groups'] = sorted(s['groups'])
    print(json.dumps(summary, indent=1, ensure_ascii=False))
    for c in summary:  # sin fuga de piezas entre particiones
        seen = {}
        for r in rows:
            if r['class'] == c:
                assert seen.setdefault(r['group_id'], r['split']) == r['split']


if __name__ == '__main__':
    main()
