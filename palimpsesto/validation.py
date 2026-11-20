"""Validaciones explícitas de contratos y plausibilidad de entrada.

El control de alcance no es un clasificador universal de objetos desconocidos.
Una alerta requiere decisión humana; no convierte una distancia en certeza.
"""
import math
from pathlib import Path
import cv2,numpy as np

def object_payload(body,allowed,required=()):
    if not isinstance(body,dict):raise ValueError('La solicitud debe contener un objeto JSON válido.')
    extra=set(body)-set(allowed)
    if extra:raise ValueError('La solicitud contiene campos no admitidos: '+', '.join(sorted(extra)))
    missing=set(required)-set(body)
    if missing:raise ValueError('Faltan campos obligatorios: '+', '.join(sorted(missing)))
    return body

def number(value,name,minimum=0,maximum=1):
    if isinstance(value,bool) or not isinstance(value,(int,float,str)):raise ValueError(f'{name}: escribe un número válido.')
    if isinstance(value,str) and (not value.strip() or len(value)>40):raise ValueError(f'{name}: escribe un número válido.')
    try:v=float(value)
    except (ValueError,OverflowError):raise ValueError(f'{name}: escribe un número válido.')
    if not math.isfinite(v) or not minimum<=v<=maximum:raise ValueError(f'{name}: el valor debe estar entre {minimum:g} y {maximum:g}.')
    return v

def choice(value,allowed,name):
    if not isinstance(value,str) or value not in allowed:raise ValueError(name+': selecciona una opción válida.')
    return value

def assess_input(rgb,prediction):
    h,w=rgb.shape[:2];scale=min(1,480/max(h,w));small=cv2.resize(rgb,(max(1,round(w*scale)),max(1,round(h*scale))),interpolation=cv2.INTER_AREA);gray=cv2.cvtColor(small,cv2.COLOR_RGB2GRAY)
    std=float(gray.std());edge=float((cv2.Canny(gray,50,150)>0).mean());warnings=[];reasons=[]
    if std<1.2 and edge<.0005:raise ValueError('La imagen está vacía o es casi uniforme. Carga una foto donde se vea el contenido de una pieza.')
    if min(h,w)<200:warnings.append('La resolución es baja. Una captura más grande conservará mejor los trazos finos.')
    # Luz, nitidez, reflejos y encuadre se revisan en capture.py, sobre la pieza y con umbrales calibrados.
    sharp=float(cv2.Laplacian(gray,cv2.CV_64F).var())
    if prediction.get('scope',{}).get('flagged'):reasons.append('El contenido se aleja de las piezas usadas para entrenar el sistema.')
    # Presence only, no identification. Portrait paintings may also trigger review.
    cascade_path=Path(cv2.data.haarcascades)/'haarcascade_frontalface_default.xml'
    faces=[]
    if cascade_path.exists():
        detector=cv2.CascadeClassifier(str(cascade_path));faces=detector.detectMultiScale(gray,scaleFactor=1.15,minNeighbors=5,minSize=(35,35))
    if len(faces):reasons.append('Se detecta un posible rostro: comprueba que sea la fotografía de una pieza plana, no una escena o un retrato fotográfico común.')
    return {'requires_confirmation':bool(reasons),'reasons':reasons,'warnings':warnings,'scope_screen_available':prediction.get('scope',{}).get('available',False),'metrics':{'gray_std':std,'edge_fraction':edge,'sharpness_480':sharp},'limitations':'Control orientativo: algunas escenas pueden pasar y piezas legítimas pueden activar una alerta. Confirma una única pieza plana.'}
