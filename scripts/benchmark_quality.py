"""Benchmark sintético de las funciones REALES de mejora y una comparación FFT."""
from pathlib import Path
import sys,csv,json
ROOT=Path(__file__).resolve().parents[1]
deps=ROOT.parent.parent/'work/pydeps'
if deps.exists():sys.path.insert(0,str(deps))
sys.path.insert(0,str(ROOT))
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
from skimage.metrics import structural_similarity,peak_signal_noise_ratio
from palimpsesto.imaging import enhance,PRESETS

def page():
    im=Image.new('RGB',(600,800),(235,235,235));d=ImageDraw.Draw(im)
    candidates=['C:/Windows/Fonts/arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
    font=next((ImageFont.truetype(p,18) for p in candidates if Path(p).exists()),ImageFont.load_default(size=18))
    lines=['PALIMPSESTO - referencia construida','Tinta, acentos, puntos y bordes finos.','Una copia de consulta conserva el original.','La nitidez no recupera información perdida.']
    for j in range(23):d.text((30,30+j*31),lines[j%4],fill=(35,35,35),font=font)
    return np.asarray(im).copy()

def fft_highboost(rgb,amount=.3,cutoff=.06):
    a=rgb.astype(np.float32);h,w=a.shape[:2];fy=np.fft.fftfreq(h)[:,None];fx=np.fft.fftfreq(w)[None,:];low=np.exp(-(fx*fx+fy*fy)/(2*cutoff**2))
    smooth=np.fft.ifft2(np.fft.fft2(a,axes=(0,1))*low[:,:,None],axes=(0,1)).real
    return np.clip(a+amount*(a-smooth),0,255).astype(np.uint8)

def main():
    out=ROOT/'results/quality';out.mkdir(parents=True,exist_ok=True);ref=page();rng=np.random.default_rng(2026);h,w=ref.shape[:2];yy,xx=np.mgrid[:h,:w];field=.45+.5*xx/w+.08*np.sin(yy/h*2*np.pi)
    degraded={'clean':ref,'shadow':np.clip(ref*field[:,:,None],0,255).astype(np.uint8),'noise':np.clip(ref.astype(float)+rng.normal(0,10,ref.shape),0,255).astype(np.uint8),'blur':cv2.GaussianBlur(ref,(0,0),1.4)}
    neutral=dict(illumination=0,contrast=0,denoise=0,sharpness=0,binary='off',background='gaussian');methods={'identity':neutral,'preset_printed':PRESETS['documento_impreso'],'illumination_only':{**neutral,'illumination':1},'clahe_only':{**neutral,'contrast':1},'denoise_only':{**neutral,'denoise':1},'unsharp_only':{**neutral,'sharpness':.5}}
    records=[];panels=[]
    for case,a in degraded.items():
        for name,p in methods.items():
            b,_=enhance(a,p,'documento_impreso');psnr=peak_signal_noise_ratio(ref,b,data_range=255);ssim=structural_similarity(ref,b,channel_axis=2,data_range=255)
            records.append({'case':case,'method':name,'psnr_db':float(psnr) if np.isfinite(psnr) else 'infinite','ssim':float(ssim)})
            if case=='shadow' and name in ['identity','preset_printed','illumination_only','clahe_only']:panels.append((name,b))
        b=fft_highboost(a);records.append({'case':case,'method':'FFT_highboost_signed','psnr_db':float(peak_signal_noise_ratio(ref,b,data_range=255)),'ssim':float(structural_similarity(ref,b,channel_axis=2,data_range=255))})
    with (out/'metrics.csv').open('w',newline='',encoding='utf8') as f:wr=csv.DictWriter(f,fieldnames=records[0]);wr.writeheader();wr.writerows(records)
    Image.fromarray(ref).save(out/'reference_synthetic.png');Image.fromarray(degraded['shadow']).save(out/'shadow_synthetic.png')
    sheet=Image.new('RGB',(5*240,350),'#f1f2ed');d=ImageDraw.Draw(sheet)
    for i,(name,a) in enumerate([('synthetic_reference',ref)]+panels):
        im=Image.fromarray(a);im.thumbnail((230,310));sheet.paste(im,(240*i,0));d.text((240*i+5,318),name,fill='black')
    sheet.save(out/'comparison.png');(out/'protocol.json').write_text(json.dumps({'seed':2026,'reference':'Constructed page, not cultural heritage ground truth','metrics':'Aligned same-sized RGB; data_range=255; SSIM channel_axis=2','intent':'Probe method behavior, not universal ranking; font may vary across OS','fft':'Real signed inverse; no abs() on derivative; periodic boundary assumptions'},indent=2),encoding='utf8')
    print('Saved',len(records),'quality comparisons to',out)
if __name__=='__main__':main()
