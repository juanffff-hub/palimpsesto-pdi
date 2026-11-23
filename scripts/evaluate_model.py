"""Diagnóstico congelado del modelo desplegado; no reajusta pesos."""
from pathlib import Path
import sys,json,csv,argparse,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np,cv2,torch
from PIL import Image,ImageOps,ImageDraw,ImageFont
from palimpsesto.models import ModelService,CLASSES
from train_classifier import classification_metrics

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);args=ap.parse_args()
    model=ModelService(ROOT/'models');rows=[r for r in csv.DictReader(open(ROOT/'data/manifest.csv',encoding='utf-8-sig')) if r['split']=='test'];out=ROOT/'results/robustness';out.mkdir(parents=True,exist_ok=True)
    scenarios=['original','resized_960_control','dark_065','bright_125','rotation_90','blur_sigma_2','noise_sigma_8','central_crop_90'];results={k:[] for k in scenarios};truth=[];timings=[];errors=[];rng=np.random.default_rng(2026)
    for r in rows:
        raw=np.asarray(ImageOps.exif_transpose(Image.open(Path(args.root)/r['path'].replace('\\','/'))).convert('RGB'));h,w=raw.shape[:2];im=cv2.resize(raw,(int(w*min(1,960/max(h,w))),int(h*min(1,960/max(h,w)))),interpolation=cv2.INTER_AREA);h,w=im.shape[:2];truth.append(CLASSES.index(r['class']))
        variants={'original':raw,'resized_960_control':im,'dark_065':np.clip(im.astype(float)*.65,0,255).astype(np.uint8),'bright_125':np.clip(im.astype(float)*1.25,0,255).astype(np.uint8),'rotation_90':cv2.rotate(im,cv2.ROTATE_90_CLOCKWISE),'blur_sigma_2':cv2.GaussianBlur(im,(0,0),2),'noise_sigma_8':np.clip(im.astype(float)+rng.normal(0,8,im.shape),0,255).astype(np.uint8),'central_crop_90':im[int(h*.05):int(h*.95),int(w*.05):int(w*.95)]}
        for k,a in variants.items():
            start=time.perf_counter();p=model.classify(a);dt=time.perf_counter()-start;results[k].append([p['scores'][c] for c in CLASSES])
            if k=='original':
                timings.append(dt)
                if p['class']!=r['class']:errors.append((r,p,im))
    report={'status':'Secondary diagnostic on previously opened test, 72 correlated photos in 9 provisional blocks; perturbations are synthetic, not new independent photos','scenarios':{k:classification_metrics(truth,np.array(v).argmax(1)) for k,v in results.items()},'latency_ms':{'median':float(np.median(timings)*1000),'p95':float(np.percentile(timings,95)*1000),'scope':'classification only, warm CPU 4 threads; no image decoding'},'errors':[{'image_id':r['image_id'],'group_id':r['group_id'],'true':r['class'],'predicted':p['class'],'max_score':max(p['scores'].values())} for r,p,a in errors]}
    (out/'evaluation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    if errors:
        sheet=Image.new('RGB',(min(5,len(errors))*300,350),'#edf2ef');d=ImageDraw.Draw(sheet)
        for i,(r,p,a) in enumerate(errors[:5]):
            im=Image.fromarray(a);im.thumbnail((290,280));sheet.paste(im,(i*300,0));d.text((i*300+4,285),r['image_id']+' / '+r['group_id'],fill='black');d.text((i*300+4,305),r['class']+' -> '+p['class'],fill='black');d.text((i*300+4,325),'score %.3f'%max(p['scores'].values()),fill='black')
        sheet.save(out/'errors.private.jpg')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
