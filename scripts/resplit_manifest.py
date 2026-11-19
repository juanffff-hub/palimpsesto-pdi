"""Validar identidades revisadas y crear split nuevo sin sobrescribir el vigente.

python scripts/resplit_manifest.py manifest_revisado.csv --output data/manifest_verificado.csv
Después de revisar el resumen, sustituir manifest.csv y reentrenar AMBOS modelos
si se pretende evaluar el pipeline como sistema independiente de las piezas.
"""
from pathlib import Path
import csv,argparse,random,collections,json

def main():
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('--output',required=True);ap.add_argument('--seed',type=int,default=2026);args=ap.parse_args()
    src,dst=Path(args.input),Path(args.output)
    if src.resolve()==dst.resolve():raise SystemExit('Utiliza una salida distinta para conservar la revisión original.')
    rows=list(csv.DictReader(src.open(encoding='utf-8-sig')));groups=collections.defaultdict(list)
    if not rows or any(r.get('group_verified','').lower()!='true' for r in rows):raise SystemExit('Faltan fotografías cuya identidad física haya sido revisada.')
    if len({r['image_id'] for r in rows})!=len(rows):raise SystemExit('Hay IDs de imagen duplicados.')
    for r in rows:
        if not r['group_id'].strip():raise SystemExit('Hay un ID de pieza vacío.')
        groups[r['group_id']].append(r)
    hashes={}
    for r in rows:
        if r['sha256'] in hashes and hashes[r['sha256']]!=r['group_id']:raise SystemExit('Un mismo archivo está asignado a dos piezas.')
        hashes[r['sha256']]=r['group_id']
    for g,m in groups.items():
        if len({r['class'] for r in m})!=1:raise SystemExit('Una pieza tiene etiquetas contradictorias: '+g)
    rng=random.Random(args.seed)
    for cls in sorted({r['class'] for r in rows}):
        gs=sorted(g for g,m in groups.items() if m[0]['class']==cls);rng.shuffle(gs)
        if len(gs)<7:raise SystemExit('Se requieren al menos 7 piezas por clase para esta separación: '+cls)
        n=max(1,round(len(gs)*.15))
        for i,g in enumerate(gs):
            for r in groups[g]:r['split']='test' if i<n else 'val' if i<2*n else 'train';r['group_basis']='human_verified'
    dst.parent.mkdir(parents=True,exist_ok=True)
    with dst.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    print(json.dumps({s:{'photos':sum(r['split']==s for r in rows),'groups':len({r['group_id'] for r in rows if r['split']==s})} for s in ['train','val','test']},indent=2));print('Los pesos anteriores NO quedan validados con esta nueva separación. Reentrenar y registrar el hash del manifiesto.')
if __name__=='__main__':main()
