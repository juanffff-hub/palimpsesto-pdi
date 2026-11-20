"""Modelos del curso. La CNN adapta el Parcial práctico 2 del equipo."""
from pathlib import Path
import hashlib
import numpy as np
import cv2
import torch
from torch import nn

CLASSES = ['documento_impreso', 'manuscrito', 'pintura']

class CNNDocumentos(nn.Module):
    def __init__(self, dropout=.5):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3,16,3,padding=1),nn.ReLU(),nn.MaxPool2d(2),
            nn.Conv2d(16,32,3,padding=1),nn.ReLU(),nn.MaxPool2d(2),
            nn.Conv2d(32,64,3,padding=1),nn.ReLU(),nn.MaxPool2d(2),
            nn.Conv2d(64,128,3,padding=1),nn.ReLU(),nn.AdaptiveAvgPool2d((4,4)))
        self.classifier = nn.Sequential(nn.Flatten(),nn.Linear(2048,64),nn.ReLU(),nn.Dropout(dropout),nn.Linear(64,3))
    def forward(self,x): return self.classifier(self.features(x))

class ModelService:
    def __init__(self, directory):
        torch.set_num_threads(4)
        self.directory=Path(directory);self.classifier=None;self.segmenter=None;self.info={};self.scope_bank=None;self.scope_threshold=None;self.encoder=None;self.errors=[]
        try:
            path=self.directory/'classifier.pt'
            if path.exists():
                cp=torch.load(path,map_location='cpu',weights_only=True)
                if cp.get('classes')!=CLASSES or len(cp.get('mean',[]))!=3 or len(cp.get('std',[]))!=3 or not np.isfinite(cp['mean']+cp['std']).all() or min(cp['std'])<=0 or not 64<=cp.get('image_size',0)<=512:
                    raise ValueError('Metadatos del clasificador inválidos.')
                if cp.get('architecture')=='resnet18_frozen':
                    from torchvision.models import resnet18
                    self.classifier=resnet18(weights=None);self.classifier.fc=nn.Linear(512,3)
                else:self.classifier=CNNDocumentos(cp.get('dropout',.5))
                self.classifier.load_state_dict(cp['state_dict'],strict=True);self.classifier.eval()
                self.info={k:v for k,v in cp.items() if k!='state_dict'}
                if cp.get('architecture')=='resnet18_frozen':
                    self.encoder=nn.Sequential(*list(self.classifier.children())[:-1]).eval()
                    scope_path=self.directory/'scope_reference.npz'
                    if scope_path.exists():
                        with np.load(scope_path,allow_pickle=False) as ref:
                            if str(ref['manifest_sha256'])==cp.get('manifest_sha256') and 'classifier_sha256' in ref and str(ref['classifier_sha256'])==hashlib.sha256(path.read_bytes()).hexdigest():
                                bank=ref['features'].astype(np.float32);threshold=float(ref['threshold'])
                                if bank.ndim!=2 or bank.shape[1]!=512 or len(bank)<3 or not np.isfinite(bank).all() or not -1<=threshold<=1:raise ValueError('Referencia de alcance inválida.')
                                self.scope_bank=bank;self.scope_threshold=threshold
                            else:self.errors.append('La referencia de alcance no corresponde a los pesos actuales. Ejecuta calibrate_scope.py.')
        except Exception:
            self.classifier=None;self.encoder=None;self.scope_bank=None
            self.errors.append('No se pudo cargar el clasificador. Comprueba los pesos y sus metadatos.')
        if not path.exists():self.errors.append('Falta el archivo del clasificador; la selección será manual.')
        try:
            path=self.directory/'unet_resnet18_3clases.pth'
            if path.exists():
                import segmentation_models_pytorch as smp
                self.segmenter=smp.Unet(encoder_name='resnet18',encoder_weights=None,in_channels=3,classes=1)
                cp=torch.load(path,map_location='cpu',weights_only=True)
                self.segmenter.load_state_dict(cp['state_dict'],strict=True);self.segmenter.eval()
        except Exception:
            self.segmenter=None
            self.errors.append('No se pudo cargar U-Net. Se utilizarán contornos y edición manual.')
        if not path.exists():self.errors.append('Faltan los pesos de U-Net; el borde se propondrá por contornos.')
    @torch.inference_mode()
    def classify(self,rgb):
        if self.classifier is None:return {'class':None,'scores':None,'needs_confirmation':True,'available':False}
        size=self.info.get('image_size',128)
        a=cv2.resize(rgb,(size,size),interpolation=cv2.INTER_AREA).astype(np.float32)/255
        a=(a-np.asarray(self.info['mean'],np.float32))/np.asarray(self.info['std'],np.float32)
        x=torch.from_numpy(a.transpose(2,0,1).copy()).unsqueeze(0)
        scope={'available':False,'flagged':False}
        if self.encoder is not None:
            features=self.encoder(x).flatten(1);logits=self.classifier.fc(features)
            if self.scope_bank is not None:
                f=features[0].numpy();f=f/max(float(np.linalg.norm(f)),1e-8)
                similarity=float(np.sort(self.scope_bank@f)[-3:].mean())
                scope={'available':True,'flagged':similarity<self.scope_threshold,'similarity':similarity,'threshold':self.scope_threshold,'method':'top3 cosine of frozen features; provisional scope screen'}
        else:logits=self.classifier(x)
        scores=logits.softmax(1)[0].numpy()
        return {'class':CLASSES[int(scores.argmax())],'scores':{c:float(v) for c,v in zip(CLASSES,scores)},'needs_confirmation':True,'low_score':float(scores.max())<.7,'available':True,'scope':scope,'evaluation_status':self.info.get('evaluation_status','provisional')}
    @torch.inference_mode()
    def segment(self,rgb):
        if self.segmenter is None:return None
        a=cv2.resize(rgb,(256,256),interpolation=cv2.INTER_AREA).astype(np.float32)/255
        a=(a-np.array([.485,.456,.406],np.float32))/np.array([.229,.224,.225],np.float32)
        x=torch.from_numpy(a.transpose(2,0,1).copy()).unsqueeze(0)
        return self.segmenter(x).sigmoid()[0,0].numpy()
