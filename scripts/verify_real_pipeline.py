"""Prueba de integración con ambos modelos reales y fotografías del conjunto."""
from pathlib import Path
import sys,json,csv,io,zipfile,argparse,time,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from PIL import Image
from palimpsesto import server
from palimpsesto.models import ModelService,CLASSES

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);args=ap.parse_args();server.models=ModelService(ROOT/'models')
    assert server.models.classifier is not None and server.models.segmenter is not None
    rows=list(csv.DictReader(open(ROOT/'data/manifest.csv',encoding='utf-8-sig')));selected=[]
    for cls in CLASSES:
        candidates=[r for r in rows if r['split']=='test' and r['class']==cls];seen=set()
        for r in candidates:
            if r['group_id'] not in seen:selected.append(r);seen.add(r['group_id'])
    out=ROOT/'results/integration';out.mkdir(parents=True,exist_ok=True);records=[]
    for r in selected:
        data=(Path(args.root)/r['path'].replace('\\','/')).read_bytes();client=server.app.test_client();start=time.perf_counter();res=client.post('/api/upload',data={'image':(io.BytesIO(data),'input.jpg')},content_type='multipart/form-data');assert res.status_code==200,res.json;upload=res.json;assert upload['classification']['available']
        # Ground-truth label substitutes the user's explicit confirmation in this AUTOMATED test.
        detect=client.post('/api/detect',json={'kind':r['class'],'method':'auto','scope_confirmed':True});assert detect.status_code==200
        result=client.post('/api/process',json={'kind':r['class'],'points':detect.json['points'],'parameters':{},'aspect':0});assert result.status_code==200,result.json
        exported=client.get('/api/export/zip');assert exported.status_code==200
        with zipfile.ZipFile(io.BytesIO(exported.data)) as z:
            original=next(n for n in z.namelist() if n.startswith('original.'));assert z.read(original)==data
            png=Image.open(io.BytesIO(z.read('palimpsesto_mejorada.png')));png.verify();assert z.read('palimpsesto_consulta.pdf').startswith(b'%PDF')
            report=json.loads(z.read('registro.json'));assert report['metrics']['ssim'] is None;assert report['original']['sha256']==hashlib.sha256(data).hexdigest()
        records.append({'image_id':r['image_id'],'group_id':r['group_id'],'true_class':r['class'],'suggested_class':upload['classification']['class'],'geometry':detect.json['method'],'width':result.json['width'],'height':result.json['height'],'end_to_end_seconds':time.perf_counter()-start,'export_valid':True,'visual_acceptance':'not assessed by a human'})
        client.post('/api/reset',json={})
    report={'models':'real checkpoint inference, no stub','cases':records,'passed':len(records),'note':'Tests execution and export integrity, not visual fidelity or independent generalization.'};(out/'real_pipeline.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
