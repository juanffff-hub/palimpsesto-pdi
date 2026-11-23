"""ResNet18 congelada; selección por CV de grupos en desarrollo, test diagnóstico.

El test anterior ya se abrió al evaluar la CNN: NO es una nueva prueba ciega.
Los grupos automáticos siguen pendientes de verificación humana.
"""
from pathlib import Path
import sys,json,csv,argparse,time,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np,cv2,torch
from torch import nn
from PIL import Image,ImageOps
from torchvision.models import resnet18,ResNet18_Weights
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold
from train_classifier import classification_metrics
from palimpsesto.models import CLASSES

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);args=ap.parse_args()
    start=time.perf_counter();torch.set_num_threads(4);cv2.setNumThreads(2);torch.manual_seed(2026)
    torch.hub.set_dir(str(ROOT/'models/.download_cache'))
    out=ROOT/'results/transfer';out.mkdir(parents=True,exist_ok=True)
    policy={'selection':'5-fold StratifiedGroupKFold on train+val only; C=.01,.1,1; mean fold macro-F1', 'seed':2026,'deployment_gate':{'out_of_fold_macro_f1_min':.85,'each_class_recall_min':.80},'test_status':'Previously opened for course CNN; secondary diagnostic, NOT untouched confirmatory test','group_status':'Provisional conservative blocks; physical identities require human review','augmentations':'Original plus fixed brightness .75, rotation +8 degrees, rotation -8 degrees + brightness 1.12. Within fold only.'}
    (out/'protocol.json').write_text(json.dumps(policy,indent=2),encoding='utf8')
    rows=list(csv.DictReader(open(ROOT/'data/manifest.csv',encoding='utf-8-sig')))
    y=np.array([CLASSES.index(r['class']) for r in rows]);groups=np.array([r['group_id'] for r in rows]);dev=np.array([i for i,r in enumerate(rows) if r['split']!='test']);test=np.array([i for i,r in enumerate(rows) if r['split']=='test'])
    assert not set(groups[dev])&set(groups[test])
    net=resnet18(weights=ResNet18_Weights.IMAGENET1K_V1);net.fc=nn.Identity();net.eval()
    mean=np.array([.485,.456,.406],np.float32);std=np.array([.229,.224,.225],np.float32)
    cache=out/'features.npz'
    manifest_hash=hashlib.sha256((ROOT/'data/manifest.csv').read_bytes()).hexdigest()
    if cache.exists() and str(np.load(cache)['manifest_hash'])==manifest_hash:
        features=np.load(cache)['features']
    else:
        features=[]
        with torch.inference_mode():
            for i,r in enumerate(rows):
                a=np.asarray(ImageOps.exif_transpose(Image.open(Path(args.root)/r['path'].replace('\\','/'))).convert('RGB'))
                a=cv2.resize(a,(224,224),interpolation=cv2.INTER_AREA);views=[a,np.clip(a.astype(float)*.75,0,255).astype(np.uint8)]
                for angle,gain in [(8,1),(-8,1.12)]:
                    b=cv2.warpAffine(a,cv2.getRotationMatrix2D((112,112),angle,1),(224,224),borderMode=cv2.BORDER_REFLECT_101);views.append(np.clip(b.astype(float)*gain,0,255).astype(np.uint8))
                x=(np.stack(views).astype(np.float32)/255-mean)/std
                features.append(net(torch.from_numpy(x.transpose(0,3,1,2).copy())).numpy())
                if (i+1)%80==0:print('features',i+1,flush=True)
        features=np.stack(features);np.savez_compressed(cache,features=features,manifest_hash=manifest_hash)
    folds=list(StratifiedGroupKFold(5,shuffle=True,random_state=2026).split(dev,y[dev],groups[dev]));summaries=[];best=(-1,None,None)
    for C in [.01,.1,1.]:
        pred=np.zeros(len(dev),int);fold_metrics=[]
        for fold,(tr,va) in enumerate(folds):
            ti,vi=dev[tr],dev[va];clf=LogisticRegression(C=C,max_iter=2000,class_weight='balanced',random_state=2026)
            clf.fit(features[ti].reshape(-1,512),np.repeat(y[ti],4));pred[va]=clf.predict(features[vi,0]);m=classification_metrics(y[vi],pred[va]);m.update(fold=fold,train_groups=len(set(groups[ti])),validation_groups=len(set(groups[vi])));fold_metrics.append(m)
        average=float(np.mean([m['macro_f1'] for m in fold_metrics]));item={'C':C,'mean_fold_macro_f1':average,'std_fold_macro_f1':float(np.std([m['macro_f1'] for m in fold_metrics])),'out_of_fold':classification_metrics(y[dev],pred),'folds':fold_metrics};summaries.append(item)
        print('CV',C,average,item['out_of_fold'],flush=True)
        if average>best[0]:best=(average,C,pred.copy())
    C=best[1];clf=LogisticRegression(C=C,max_iter=2000,class_weight='balanced',random_state=2026);clf.fit(features[dev].reshape(-1,512),np.repeat(y[dev],4))
    logits=features[test,0]@clf.coef_.T+clf.intercept_;prob=np.exp(logits-logits.max(1,keepdims=True));prob/=prob.sum(1,keepdims=True)
    diagnostic=classification_metrics(y[test],prob.argmax(1));selected=next(s for s in summaries if s['C']==C)
    gate=selected['out_of_fold']['macro_f1']>=.85 and min(v['recall'] for v in selected['out_of_fold']['classes'].values())>=.8
    net.fc=nn.Linear(512,3)
    with torch.no_grad():net.fc.weight.copy_(torch.tensor(clf.coef_,dtype=torch.float32));net.fc.bias.copy_(torch.tensor(clf.intercept_,dtype=torch.float32))
    cp={'architecture':'resnet18_frozen','state_dict':net.state_dict(),'image_size':224,'mean':mean.tolist(),'std':std.tolist(),'classes':CLASSES,'seed':2026,'C':C,'train_photos':len(dev),'train_groups':len(set(groups[dev])),'manifest_sha256':manifest_hash,'evaluation_status':'provisional: CV por bloques automáticos; identidad física pendiente; test diagnóstico reutilizado','deployment_gate_passed':bool(gate),'validation':selected['out_of_fold']}
    torch.save(cp,ROOT/'models/transfer_candidate.pt')
    if gate:torch.save(cp,ROOT/'models/classifier.pt')
    report={'protocol':policy,'comparisons':summaries,'selected_C':C,'deployment_gate_passed':bool(gate),'secondary_test':diagnostic,'elapsed_seconds':time.perf_counter()-start,'train_photos':len(dev),'train_groups':len(set(groups[dev]))}
    (out/'evaluation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    with (out/'predictions.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.writer(f);w.writerow(['image_id','group_id','true_class','predicted_class','evaluation']+CLASSES)
        for j,i in enumerate(dev):w.writerow([rows[i]['image_id'],groups[i],CLASSES[y[i]],CLASSES[best[2][j]],'out_of_fold',*['']*3])
        for j,i in enumerate(test):w.writerow([rows[i]['image_id'],groups[i],CLASSES[y[i]],CLASSES[prob[j].argmax()],'secondary_test',*prob[j].tolist()])
    print('FINAL',json.dumps({k:v for k,v in report.items() if k not in ['comparisons','protocol']}),flush=True)
if __name__=='__main__':main()
