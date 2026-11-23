"""Prueba pequeña de alertas de alcance: NO certifica detección universal OOD."""
from pathlib import Path
import sys,json,csv,argparse
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageOps
from palimpsesto.models import ModelService
from palimpsesto.validation import assess_input

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);args=ap.parse_args();model=ModelService(ROOT/'models');records=[]
    cases=[('negative',p.stem,p) for p in (ROOT/'results/scope').glob('*.png') if p.stem!='page']
    cases.append(('positive_external_scan','page',ROOT/'results/scope/page.png'))
    for r in csv.DictReader(open(ROOT/'data/manifest.csv',encoding='utf-8-sig')):
        if r['split']=='test':cases.append(('positive_dataset',r['image_id'],Path(args.root)/r['path'].replace('\\','/')))
    for kind,name,path in cases:
        a=np.asarray(ImageOps.exif_transpose(Image.open(path)).convert('RGB'));prediction=model.classify(a);assessment=assess_input(a,prediction)
        records.append({'set':kind,'image_id':name,'flagged':assessment['requires_confirmation'],'reasons':assessment['reasons'],'similarity':prediction.get('scope',{}).get('similarity'),'raw_class':prediction['class']})
    summary={kind:{'n':sum(r['set']==kind for r in records),'flagged':sum(r['set']==kind and r['flagged'] for r in records)} for kind in ['negative','positive_dataset','positive_external_scan']}
    report={'summary':summary,'cases':records,'limitations':'Convenience negative examples and provisional positive split. Face warning deliberately also flags some portrait paintings. Human confirmation remains mandatory. Not an open-world accuracy claim.','source':'https://scikit-image.org/docs/stable/api/skimage.data.html'}
    (ROOT/'results/scope/evaluation.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
