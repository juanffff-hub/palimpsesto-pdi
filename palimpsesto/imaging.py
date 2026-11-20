"""PDI determinista: entrada, geometría, mejora y métricas.

RGB es el contrato entre módulos; OpenCV no recibe BGR implícitamente.
Las esquinas viajan normalizadas respecto a la foto orientada por EXIF.
"""
import io,hashlib
import cv2
import numpy as np
from PIL import Image,ImageOps,UnidentifiedImageError
from skimage.filters import threshold_sauvola
from .validation import number,choice,object_payload

MAX_PIXELS=40_000_000
PRESETS={
    'documento_impreso':dict(illumination=.35,contrast=.15,denoise=0.,sharpness=.15,binary='off',background='gaussian'),
    'manuscrito':dict(illumination=.20,contrast=.10,denoise=0.,sharpness=.10,binary='off',background='gaussian'),
    'pintura':dict(illumination=0.,contrast=0.,denoise=0.,sharpness=0.,binary='off',background='gaussian')}

def load_image(data):
    if len(data)>40*1024*1024:raise ValueError('El archivo supera 40 MB. Usa una copia más pequeña.')
    try:
        im=Image.open(io.BytesIO(data))
        if im.format not in ('JPEG','PNG'):raise ValueError('Selecciona una imagen JPG o PNG.')
        if im.width*im.height>MAX_PIXELS:raise ValueError('La imagen supera 40 megapíxeles.')
        if min(im.size)<64:raise ValueError('La imagen es demasiado pequeña (mínimo 64 píxeles por lado).')
        if getattr(im,'is_animated',False):raise ValueError('Usa una imagen estática JPG o PNG, no una animación.')
        im.verify();im=Image.open(io.BytesIO(data))
        orientation=im.getexif().get(274,1);fmt=im.format
        im=ImageOps.exif_transpose(im)
        if im.mode in ('RGBA','LA') or 'transparency' in im.info:
            rgba=im.convert('RGBA');canvas=Image.new('RGBA',im.size,'white');canvas.alpha_composite(rgba);im=canvas.convert('RGB')
        else:im=im.convert('RGB')
        rgb=np.asarray(im).copy()
    except (UnidentifiedImageError,OSError,Image.DecompressionBombError) as e:
        raise ValueError('No se pudo leer la imagen. Prueba otro JPG o PNG.') from e
    return rgb,{'sha256':hashlib.sha256(data).hexdigest(),'source_format':fmt,'exif_orientation':orientation,'width':rgb.shape[1],'height':rgb.shape[0]}

def resize_long(rgb,limit=1200):
    h,w=rgb.shape[:2];s=min(1.,limit/max(h,w))
    return cv2.resize(rgb,(max(1,round(w*s)),max(1,round(h*s))),interpolation=cv2.INTER_AREA) if s<1 else rgb.copy()

def encode_png(rgb):
    stream=io.BytesIO();Image.fromarray(rgb).save(stream,format='PNG');return stream.getvalue()

def order_quad(points):
    q=np.asarray(points,dtype=np.float32)
    if q.shape!=(4,2) or not np.isfinite(q).all():raise ValueError('Se necesitan cuatro esquinas válidas.')
    center=q.mean(0);q=q[np.argsort(np.arctan2(q[:,1]-center[1],q[:,0]-center[0]))]
    q=np.roll(q,-int(np.argmin(q.sum(1))),axis=0)
    return q

def validate_quad(points):
    try:
        raw=np.asarray(points)
        if raw.dtype.kind not in 'fiu':raise ValueError('Las coordenadas deben ser numéricas, sin texto ni valores lógicos.')
        q=raw.astype(np.float32)
    except (ValueError,TypeError,OverflowError) as e:raise ValueError('Se necesitan cuatro pares de coordenadas numéricas.') from e
    if q.shape!=(4,2) or not np.isfinite(q).all():raise ValueError('Se necesitan cuatro esquinas válidas.')
    if np.any(q<0) or np.any(q>1):raise ValueError('Las esquinas deben quedar dentro de la foto.')
    # Do not reorder user input: a crossed polygon must be shown as an error.
    if not cv2.isContourConvex(q.reshape(-1,1,2)):raise ValueError('Las esquinas se cruzan. Mantén el orden de los cuatro puntos.')
    if abs(cv2.contourArea(q))<.01:raise ValueError('La selección ocupa muy poca superficie. Amplía el borde.')
    if cv2.contourArea(q,oriented=True)<0:raise ValueError('Mantén el orden: superior izquierda, superior derecha, inferior derecha, inferior izquierda.')
    if min(np.linalg.norm(q-np.roll(q,1,axis=0),axis=1))<.02:raise ValueError('Hay dos esquinas demasiado próximas.')
    return q

def quad_from_mask(mask):
    contours,_=cv2.findContours(mask.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    if not contours:return None,False
    contours=sorted(contours,key=cv2.contourArea,reverse=True)
    multi=len(contours)>1 and cv2.contourArea(contours[1])>.12*mask.size
    hull=cv2.convexHull(contours[0])
    for e in [.005,.01,.015,.02,.03,.04,.06]:
        q=cv2.approxPolyDP(hull,e*cv2.arcLength(hull,True),True)
        if len(q)==4 and cv2.isContourConvex(q):return order_quad(q.reshape(4,2)),multi
    return None,multi

def classical_quad(rgb):
    g=cv2.GaussianBlur(cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY),(5,5),0);h,w=g.shape;candidates=[]
    masks=[]
    for lo,hi in [(50,150),(20,60),(75,200)]:masks.append(cv2.morphologyEx(cv2.Canny(g,lo,hi),cv2.MORPH_CLOSE,np.ones((5,5),np.uint8)))
    _,th=cv2.threshold(g,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    masks.extend([cv2.morphologyEx(th,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8)),cv2.morphologyEx(255-th,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))])
    edge=cv2.dilate(cv2.Canny(g,20,60),np.ones((7,7),np.uint8))>0
    for m in masks:
        contours,_=cv2.findContours(m,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
        for c in sorted(contours,key=cv2.contourArea,reverse=True)[:30]:
            if cv2.contourArea(c)<.05*w*h:continue
            for eps in [.01,.02,.035]:
                q=cv2.approxPolyDP(c,eps*cv2.arcLength(c,True),True)
                if len(q)!=4 or not cv2.isContourConvex(q):continue
                q=q.reshape(4,2);area=cv2.contourArea(q)/(w*h)
                if not .05<area<.97:continue
                b=np.zeros_like(g);cv2.polylines(b,[q],True,255,2);support=float(edge[b>0].mean())
                margin=np.min(np.stack([q[:,0],q[:,1],w-1-q[:,0],h-1-q[:,1]]),axis=0)
                score=.5*area+.5*support-.5*np.mean(margin<5)
                candidates.append((score,q))
    return order_quad(max(candidates,key=lambda x:x[0])[1]) if candidates else None

def detect_quad(rgb,models,kind='documento_impreso',method='auto'):
    small=resize_long(rgb,960);h,w=small.shape[:2];q=None;multi=False;source='manual';warnings=[]
    if method in ('unet','auto'):
        prob=models.segment(rgb)
        if prob is not None:
            mask=cv2.resize((prob>.5).astype(np.uint8),(w,h),interpolation=cv2.INTER_NEAREST)
            q,multi=quad_from_mask(mask);source='unet'
            if multi:warnings.append('Hay varias regiones grandes: elige una sola pieza y revisa el borde.');q=None
    if q is None and not multi and method!='manual':q=classical_quad(small);source='contornos'
    if q is not None:
        q=q/np.array([w-1,h-1],np.float32)
        try:validate_quad(q)
        except ValueError:q=None
    if q is None:
        q=np.array([[.08,.08],[.92,.08],[.92,.92],[.08,.92]],np.float32);source='manual'
        warnings.append('No hay un borde fiable. Coloca los cuatro puntos sobre la pieza.')
    if source=='unet':warnings.append('Borde sugerido por una U-Net entrenada con impresos, manuscritos y pinturas; confirma las cuatro esquinas.')
    elif source=='contornos':warnings.append('Borde sugerido por contraste; puede corresponder al marco o al fondo. Confírmalo.')
    return {'points':q.tolist(),'method':source,'warnings':warnings,'manual_required':source=='manual'}

def rectify(rgb,points,aspect=0.,max_side=2400):
    q=validate_quad(points)*np.array([rgb.shape[1]-1,rgb.shape[0]-1],np.float32)
    width=max(np.linalg.norm(q[1]-q[0]),np.linalg.norm(q[2]-q[3]))
    height=max(np.linalg.norm(q[3]-q[0]),np.linalg.norm(q[2]-q[1]))
    aspect=number(aspect,'Proporción ancho/alto',0,10)
    if not np.isfinite(aspect) or aspect<0 or aspect>10:raise ValueError('La proporción ancho/alto debe estar entre 0,1 y 10, o ser 0 para estimarla.')
    if aspect:
        if aspect<.1:raise ValueError('La proporción es demasiado estrecha.')
        area=width*height;width=np.sqrt(area*aspect);height=width/aspect
    scale=min(1.,float(max_side)/max(width,height));ow=max(32,round(width*scale));oh=max(32,round(height*scale))
    dst=np.float32([[0,0],[ow-1,0],[ow-1,oh-1],[0,oh-1]])
    H=cv2.getPerspectiveTransform(q.astype(np.float32),dst)
    if not np.isfinite(H).all() or abs(np.linalg.det(H))<1e-12:raise ValueError('No se puede transformar este borde. Revisa las esquinas.')
    return cv2.warpPerspective(rgb,H,(ow,oh),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE),H

def sanitize_params(params,kind):
    choice(kind,PRESETS,'Tipo de pieza')
    object_payload(params,['illumination','contrast','denoise','sharpness','binary','background'])
    p=PRESETS[kind].copy()
    for name in ['illumination','contrast','denoise','sharpness']:
        v=number(params.get(name,p[name]),name)
        p[name]=v
    p['background']=params.get('background','gaussian')
    if p['background'] not in ['gaussian','closing']:raise ValueError('Método de fondo desconocido.')
    p['binary']=params.get('binary','off')
    if p['binary'] not in ['off','otsu','sauvola']:raise ValueError('Modo de texto desconocido.')
    if kind=='pintura' and p['binary']!='off':raise ValueError('La binarización está disponible solo para documentos.')
    return p

def enhance(rgb,params,kind):
    p=sanitize_params(params,kind)
    if not any(p[k] for k in ['illumination','contrast','denoise','sharpness']) and p['binary']=='off':return rgb.copy(),p
    lab=cv2.cvtColor(rgb,cv2.COLOR_RGB2LAB);L=lab[:,:,0].astype(np.float32);short=min(L.shape)
    if p['denoise']:
        den=cv2.bilateralFilter(L,5,8+18*p['denoise'],8);L=(1-p['denoise'])*L+p['denoise']*den
    if p['illumination']:
        scale=min(1.,600/max(L.shape))
        small=cv2.resize(L,(max(16,round(L.shape[1]*scale)),max(16,round(L.shape[0]*scale))),interpolation=cv2.INTER_AREA)
        if p['background']=='closing':
            k=max(9,int(min(small.shape)*.04)//2*2+1);small=cv2.morphologyEx(small,cv2.MORPH_CLOSE,np.ones((k,k),np.uint8))
        bg=cv2.GaussianBlur(small,(0,0),max(3,min(small.shape)*.04));bg=cv2.resize(bg,L.shape[::-1],interpolation=cv2.INTER_LINEAR)
        corrected=L/np.maximum(bg,10)*float(np.median(bg));L=np.clip((1-p['illumination'])*L+p['illumination']*corrected,0,255)
    if p['contrast']:
        c=cv2.createCLAHE(clipLimit=2.,tileGridSize=(8,8)).apply(np.clip(L,0,255).astype(np.uint8));L=(1-p['contrast'])*L+p['contrast']*c
    if p['sharpness']:
        low=cv2.GaussianBlur(L,(0,0),max(.7,short/1200));L=np.clip(L+p['sharpness']*(L-low),0,255)
    lab[:,:,0]=np.clip(np.round(L),0,255).astype(np.uint8);out=cv2.cvtColor(lab,cv2.COLOR_LAB2RGB)
    if p['binary']!='off':
        gray=cv2.cvtColor(out,cv2.COLOR_RGB2GRAY)
        if p['binary']=='otsu':binary=cv2.threshold(gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]
        else:
            window=max(15,int(min(gray.shape)*.035)//2*2+1);t=threshold_sauvola(gray,window_size=window,k=.2);binary=(gray>t).astype(np.uint8)*255
        out=np.repeat(binary[:,:,None],3,axis=2)
    return out,p

def descriptors(rgb):
    small=resize_long(rgb,960);g=cv2.cvtColor(small,cv2.COLOR_RGB2GRAY)
    return {'laplacian_variance':float(cv2.Laplacian(g,cv2.CV_64F).var()),'rms_contrast':float(g.std()/255),'dark_percent':float((g<=2).mean()*100),'bright_percent':float((g>=253).mean()*100),'metric_width':g.shape[1],'metric_height':g.shape[0]}

def compare_metrics(before,after):
    return {'before':descriptors(before),'after':descriptors(after),'ssim':None,'psnr':None,'reference_status':'No hay referencia alineada. SSIM y PSNR no se calculan.','interpretation':'Nitidez y contraste son descriptores: subirlos no demuestra recuperar información.'}
