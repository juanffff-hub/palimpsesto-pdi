"""Entrenamiento reproducible: cinco variantes CNN y baseline ANN.

Ejemplo: python scripts/train_classifier.py --root "C:/.../Material Proyecto de PDI"
El manifiesto es la única fuente de particiones. No se usan los nombres de carpetas.
"""
from pathlib import Path
import sys,argparse,json,csv,time,copy,random
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np,cv2,torch
from torch import nn
from PIL import Image,ImageOps
from palimpsesto.models import CNNDocumentos,CLASSES

def classification_metrics(y,p):
    cm=np.zeros((3,3),int)
    for a,b in zip(y,p):cm[int(a),int(b)]+=1
    precision=np.divide(cm.diagonal(),cm.sum(0),out=np.zeros(3,float),where=cm.sum(0)!=0)
    recall=np.divide(cm.diagonal(),cm.sum(1),out=np.zeros(3,float),where=cm.sum(1)!=0)
    f1=np.divide(2*precision*recall,precision+recall,out=np.zeros(3,float),where=precision+recall!=0)
    return {'n':len(y),'accuracy':float(cm.trace()/max(1,cm.sum())),'macro_f1':float(f1.mean()),'confusion_matrix':cm.tolist(),'classes':{c:{'precision':float(precision[i]),'recall':float(recall[i]),'f1':float(f1[i]),'support':int(cm[i].sum())} for i,c in enumerate(CLASSES)}}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--manifest',default=str(ROOT/'data/manifest.csv'));ap.add_argument('--epochs',type=int,default=35);ap.add_argument('--size',type=int,default=192);args=ap.parse_args()
    torch.set_num_threads(4);torch.manual_seed(2026);random.seed(2026);np.random.seed(2026);cv2.setNumThreads(2)
    rows=list(csv.DictReader(open(args.manifest,encoding='utf-8-sig')));source=Path(args.root)
    for a in ['train','val','test']:
        for b in ['train','val','test']:
            if a!=b:assert not ({r['group_id'] for r in rows if r['split']==a}&{r['group_id'] for r in rows if r['split']==b})
    images=[];labels=[]
    for r in rows:
        im=ImageOps.exif_transpose(Image.open(source/r['path'].replace('\\','/'))).convert('RGB');im=im.resize((args.size,args.size),Image.Resampling.BOX);images.append(np.asarray(im).copy());labels.append(CLASSES.index(r['class']))
    images=np.stack(images);labels=np.asarray(labels);idx={s:np.array([i for i,r in enumerate(rows) if r['split']==s]) for s in ['train','val','test']}
    mean=(images[idx['train']].astype(np.float32)/255).mean((0,1,2));std=(images[idx['train']].astype(np.float32)/255).std((0,1,2));std=np.maximum(std,.01)
    out=ROOT/'results/classification';out.mkdir(parents=True,exist_ok=True);(ROOT/'models').mkdir(exist_ok=True)
    common={'architecture':'course_cnn','image_size':args.size,'mean':mean.tolist(),'std':std.tolist(),'classes':CLASSES,'seed':2026,'evaluation_status':'provisional: agrupación visual pendiente de confirmación humana','manifest_sha256':__import__('hashlib').sha256(Path(args.manifest).read_bytes()).hexdigest()}
    split_summary={s:{'photos':len(v),'groups':len({rows[i]['group_id'] for i in v}),'classes':{c:int(sum(labels[v]==j)) for j,c in enumerate(CLASSES)}} for s,v in idx.items()}
    (out/'split_summary.json').write_text(json.dumps(split_summary,indent=2),encoding='utf-8');print(split_summary,flush=True)
    def batch(indices,augment,rng):
        arr=images[indices].copy()
        if augment:
            for i,a in enumerate(arr):
                angle=rng.uniform(-12,12);M=cv2.getRotationMatrix2D((args.size/2,args.size/2),angle,rng.uniform(.9,1.05));a=cv2.warpAffine(a,M,(args.size,args.size),borderMode=cv2.BORDER_REFLECT_101)
                a=np.clip(a.astype(np.float32)*rng.uniform(.75,1.2)+rng.uniform(-8,8),0,255)
                if rng.random()<.25:a=cv2.GaussianBlur(a,(3,3),.5)
                arr[i]=a.astype(np.uint8)
        arr=(arr.astype(np.float32)/255-mean)/std
        return torch.from_numpy(arr.transpose(0,3,1,2).copy()),torch.from_numpy(labels[indices]).long()
    def evaluate(model,indices):
        probs=[];losses=[]
        model.eval()
        with torch.inference_mode():
            for start in range(0,len(indices),16):
                x,y=batch(indices[start:start+16],False,None);z=model(x);probs.extend(z.softmax(1).numpy());losses.append((float(nn.functional.cross_entropy(z,y)),len(y)))
        probabilities=np.asarray(probs);m=classification_metrics(labels[indices],probabilities.argmax(1));m['loss']=sum(v*n for v,n in losses)/len(indices);return m,probabilities
    summaries=[];best_checkpoint=None;best_score=(-1,float('-inf'))
    variants=[('base',0.,0.,False),('dropout',.5,0.,False),('l2',0.,1e-4,False),('augmentation',0.,0.,True),('combined',.5,1e-4,True)]
    for name,drop,wd,aug in variants:
        torch.manual_seed(2026);rng=np.random.default_rng(2026);model=CNNDocumentos(drop);opt=torch.optim.Adam(model.parameters(),lr=1e-3,weight_decay=wd);best=(-1,float('-inf'));stale=0;history=[];start_time=time.perf_counter()
        for epoch in range(1,args.epochs+1):
            model.train();order=rng.permutation(idx['train']);loss_sum=0;correct=0
            for start in range(0,len(order),16):
                x,y=batch(order[start:start+16],aug,rng);opt.zero_grad();z=model(x);loss=nn.functional.cross_entropy(z,y);loss.backward();opt.step();loss_sum+=float(loss.detach())*len(y);correct+=int((z.argmax(1)==y).sum())
            met,_=evaluate(model,idx['val']);history.append({'epoch':epoch,'train_loss':loss_sum/len(order),'train_accuracy':correct/len(order),'val_loss':met['loss'],'val_accuracy':met['accuracy'],'val_macro_f1':met['macro_f1']})
            score=(met['macro_f1'],-met['loss'])
            if score>best:
                best=score;stale=0;checkpoint={**common,'state_dict':copy.deepcopy(model.state_dict()),'dropout':drop,'weight_decay':wd,'augmentation':aug,'variant':name,'epoch':epoch,'validation':met}
            else:stale+=1
            if epoch%5==0:print(name,epoch,round(met['macro_f1'],3),round(met['loss'],3),flush=True)
            if epoch>=12 and stale>=8:break
        torch.save(checkpoint,ROOT/'models'/f'cnn_{name}.pt')
        (out/f'{name}_history.json').write_text(json.dumps(history,indent=2),encoding='utf-8')
        summaries.append({'variant':name,'epochs_run':len(history),'best_epoch':checkpoint['epoch'],'seconds':time.perf_counter()-start_time,'validation':checkpoint['validation']})
        if best>best_score:best_score=best;best_checkpoint=checkpoint
        print('DONE',name,summaries[-1],flush=True)
    # Select once on validation, then evaluate test once. No test-driven retraining here.
    model=CNNDocumentos(best_checkpoint['dropout']);model.load_state_dict(best_checkpoint['state_dict']);test,prob=evaluate(model,idx['test'])
    torch.save(best_checkpoint,ROOT/'models/classifier.pt')
    (out/'comparison.json').write_text(json.dumps(summaries,indent=2),encoding='utf-8');(out/'selected_test.json').write_text(json.dumps({'variant':best_checkpoint['variant'],'evaluation_status':common['evaluation_status'],**test},indent=2),encoding='utf-8')
    with (out/'test_predictions.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f);w.writerow(['image_id','group_id','true_class','predicted_class']+CLASSES)
        for i,p in zip(idx['test'],prob):w.writerow([rows[i]['image_id'],rows[i]['group_id'],CLASSES[labels[i]],CLASSES[p.argmax()],*p.tolist()])
    # ANN baseline with 48 RGB histogram bins, edge density and Laplacian variance.
    feats=[]
    for a in images:
        g=cv2.cvtColor(a,cv2.COLOR_RGB2GRAY);v=np.concatenate([np.histogram(a[:,:,c],bins=16,range=(0,256))[0]/(args.size**2) for c in range(3)]+[np.array([(cv2.Canny(g,50,150)>0).mean(),np.log1p(cv2.Laplacian(g,cv2.CV_64F).var())])]);feats.append(v)
    feats=np.asarray(feats,np.float32);mu=feats[idx['train']].mean(0);sd=np.maximum(feats[idx['train']].std(0),1e-5);x=torch.from_numpy((feats-mu)/sd);y=torch.from_numpy(labels).long()
    torch.manual_seed(2026);ann=nn.Sequential(nn.Linear(50,32),nn.ReLU(),nn.Linear(32,3));opt=torch.optim.Adam(ann.parameters(),lr=.01,weight_decay=1e-4);best=(-1,float('-inf'));history=[]
    for epoch in range(1,121):
        ann.train();opt.zero_grad();loss=nn.functional.cross_entropy(ann(x[idx['train']]),y[idx['train']]);loss.backward();opt.step();ann.eval()
        with torch.inference_mode():z=ann(x[idx['val']]);v=classification_metrics(labels[idx['val']],z.argmax(1).numpy());vl=float(nn.functional.cross_entropy(z,y[idx['val']]))
        history.append({'epoch':epoch,'train_loss':float(loss.detach()),'val_loss':vl,'val_macro_f1':v['macro_f1']})
        if (v['macro_f1'],-vl)>best:best=(v['macro_f1'],-vl);astate=copy.deepcopy(ann.state_dict());av=v
    ann.load_state_dict(astate)
    with torch.inference_mode():at=classification_metrics(labels[idx['test']],ann(x[idx['test']]).argmax(1).numpy())
    torch.save({'state_dict':astate,'mean':mu.tolist(),'std':sd.tolist(),'features':'RGB16x3 + density + log_laplacian_variance'},ROOT/'models/ann_baseline.pt')
    (out/'ann_baseline.json').write_text(json.dumps({'validation':av,'test':at,'history':history},indent=2),encoding='utf-8');print('SELECTED',best_checkpoint['variant'],test,flush=True)

if __name__=='__main__':main()
