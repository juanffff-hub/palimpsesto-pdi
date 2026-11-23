"""Calibra una alerta de alcance con desarrollo, sin ajustar sobre negativos/test.

No es un detector universal. Repetir después de cambiar pesos o manifiesto.
"""
from pathlib import Path
import sys,argparse,csv,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np,cv2,torch
from PIL import Image,ImageOps
from palimpsesto.models import ModelService

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);args=ap.parse_args()
    model=ModelService(ROOT/'models')
    if model.encoder is None:raise ValueError('Se requiere el clasificador ResNet18 congelado de la entrega.')
    manifest=ROOT/'data/manifest.csv';digest=hashlib.sha256(manifest.read_bytes()).hexdigest()
    if digest!=model.info.get('manifest_sha256'):raise ValueError('El manifiesto no corresponde a estos pesos. Reentrena antes de calibrar.')
    rows=list(csv.DictReader(manifest.open(encoding='utf-8-sig')))
    dev=[r for r in rows if r['split'] in ['train','val']];features=[]
    with torch.inference_mode():
        for row in dev:
            with Image.open(Path(args.root)/row['path'].replace('\\','/')) as image:
                rgb=np.asarray(ImageOps.exif_transpose(image).convert('RGB'))
            x=cv2.resize(rgb,(224,224),interpolation=cv2.INTER_AREA).astype(np.float32)/255
            x=(x-np.asarray(model.info['mean'],np.float32))/np.asarray(model.info['std'],np.float32)
            features.append(model.encoder(torch.from_numpy(x.transpose(2,0,1).copy()).unsqueeze(0)).flatten().numpy())
    features=np.asarray(features,np.float32);features/=np.maximum(np.linalg.norm(features,axis=1,keepdims=True),1e-8)
    groups=np.array([r['group_id'] for r in dev]);similarity=features@features.T
    if any(np.count_nonzero(groups!=g)<3 for g in groups):raise ValueError('Se necesitan al menos tres fotos de otros grupos por pieza.')
    similarity[groups[:,None]==groups[None,:]]=-1
    scores=np.sort(similarity,axis=1)[:,-3:].mean(1);threshold=float(np.quantile(scores,.03))
    model_hash=hashlib.sha256((ROOT/'models/classifier.pt').read_bytes()).hexdigest()
    np.savez_compressed(ROOT/'models/scope_reference.npz',features=features,threshold=threshold,manifest_sha256=digest,classifier_sha256=model_hash)
    out=ROOT/'results/scope';out.mkdir(parents=True,exist_ok=True)
    report={'method':'mean top3 cosine of frozen features; 3rd percentile of development similarities excluding same group','development_n':len(dev),'development_groups':len(set(groups)),'threshold':threshold,'manifest_sha256':digest,'classifier_sha256':model_hash,'negative_examples_used_for_threshold':0,'test_examples_used_for_threshold':0,'limitations':'Provisional groups. Not a universal open-set detector; both false negatives and false positives are possible.'}
    (out/'calibration_protocol.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
