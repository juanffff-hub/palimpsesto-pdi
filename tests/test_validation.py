"""Contratos adversos: datos malformados, alcance, sesiones y recuperación.

Los stubs aíslan contratos de software; evaluate_scope.py comprueba imágenes reales.
"""
import io,time,json
from pathlib import Path
import numpy as np,pytest
from PIL import Image
from palimpsesto import server,imaging
from palimpsesto.models import ModelService
from palimpsesto.imaging import encode_png,load_image,enhance,validate_quad

class Models:
    classifier=True;segmenter=None;scope_bank=None;errors=[]
    def __init__(self,flag=False):self.flag=flag
    def classify(self,rgb):return {'class':'documento_impreso','available':True,'scores':dict(documento_impreso=.9,manuscrito=.05,pintura=.05),'scope':{'available':True,'flagged':self.flag}}
    def segment(self,rgb):return None

@pytest.fixture
def raw():
    a=np.full((220,300,3),220,np.uint8);a[35:70,40:245]=20;a[100:130,40:230]=[40,130,80];return encode_png(a)

@pytest.fixture
def client(raw,monkeypatch):
    monkeypatch.setattr(server,'models',Models());monkeypatch.setattr(server,'states',{});c=server.app.test_client();res=c.post('/api/upload',data={'image':(io.BytesIO(raw),'valid.png')});assert res.status_code==200;return c

def body(**updates):return {'kind':'documento_impreso','points':[[.05,.05],[.95,.05],[.95,.95],[.05,.95]],'parameters':{},'aspect':0,**updates}

@pytest.mark.parametrize('payload',[[],True,42,'hello',None])
def test_non_object_json(client,payload):
    r=client.post('/api/process',data=json.dumps(payload),content_type='application/json');assert r.status_code==400;assert r.json['error']

def test_broken_json_and_content_type(client):
    assert client.post('/api/process',data='{broken',content_type='application/json').status_code==400
    assert client.post('/api/process',data='hello',content_type='text/plain').status_code==415

@pytest.mark.parametrize('value',[None,True,False,[],{},'', 'texto','NaN','Infinity',-1,11,.01])
def test_invalid_aspect(client,value):
    r=client.post('/api/process',json=body(aspect=value));assert r.status_code==400,r.json

@pytest.mark.parametrize('value',[None,True,[],{},'', 'texto',float('nan'),float('inf'),-0.1,1.1])
def test_invalid_filter_value(client,value):
    r=client.post('/api/process',json=body(parameters={'sharpness':value}));assert r.status_code==400,r.json

@pytest.mark.parametrize('value',[None,[],True,'auto',{'unknown':1},{'binary':'invented'},{'background':'invented'}])
def test_invalid_parameters(client,value):assert client.post('/api/process',json=body(parameters=value)).status_code==400

@pytest.mark.parametrize('value',[None,[],{},True,'documento','unknown'])
def test_invalid_class(client,value):assert client.post('/api/process',json=body(kind=value)).status_code==400

@pytest.mark.parametrize('points',[None,[],[1,2,3,4],[[0,0],[1]],[[0,0],[1,0],[.2,.2],[0,1]],[[0,0],[0,1],[1,1],[1,0]],[[False,False],[True,False],[True,True],[False,True]],[['0','0'],['1','0'],['1','1'],['0','1']]])
def test_invalid_corner_contract(client,points):assert client.post('/api/process',json=body(points=points)).status_code==400

def test_unknown_and_missing_fields(client):
    assert client.post('/api/process',json=body(unexpected='x')).status_code==400
    assert client.post('/api/process',json={'kind':'pintura'}).status_code==400
    assert client.post('/api/detect',json={'kind':[]}).status_code==400
    assert client.post('/api/rotate',json={'kind':'pintura','direction':None}).status_code==400

def test_scope_alert_is_not_forced_class(raw,monkeypatch):
    monkeypatch.setattr(server,'models',Models(flag=True));monkeypatch.setattr(server,'states',{});c=server.app.test_client();r=c.post('/api/upload',data={'image':(io.BytesIO(raw),'outside.png')})
    assert r.status_code==200 and r.json['assessment']['requires_confirmation'];assert r.json['classification']['class'] is None;assert r.json['classification']['scores'] is None
    assert c.post('/api/process',json=body()).status_code==400
    assert c.post('/api/detect',json={'kind':'pintura','scope_confirmed':'true'}).status_code==400
    assert c.post('/api/detect',json={'kind':'pintura','scope_confirmed':False}).status_code==400
    assert c.post('/api/detect',json={'kind':'pintura','scope_confirmed':True}).status_code==200
    assert c.post('/api/process',json=body(kind='pintura')).status_code==200

def test_empty_uniform_and_unknown_files(client):
    assert client.post('/api/upload',data={}).status_code==400
    assert client.post('/api/upload',data={'image':(io.BytesIO(b''),'empty.png')}).status_code==400
    r=client.post('/api/upload',data={'image':(io.BytesIO(encode_png(np.zeros((200,200,3),np.uint8))),'black.png')});assert r.status_code==400 and 'uniforme' in r.json['error']
    b=io.BytesIO();Image.new('RGB',(100,100),'red').save(b,'BMP');assert client.post('/api/upload',data={'image':(io.BytesIO(b.getvalue()),'fake.jpg')}).status_code==400

def test_animated_tiny_and_truncated():
    b=io.BytesIO();Image.new('RGB',(100,100),'red').save(b,'PNG',save_all=True,append_images=[Image.new('RGB',(100,100),'blue')],duration=100,loop=0)
    with pytest.raises(ValueError,match='estática'):load_image(b.getvalue())
    with pytest.raises(ValueError,match='pequeña'):load_image(encode_png(np.zeros((40,40,3),np.uint8)))
    with pytest.raises(ValueError):load_image(b.getvalue()[:35])

def test_size_and_pixel_limits(raw,monkeypatch):
    with pytest.raises(ValueError,match='40 MB'):load_image(b'a'*(40*1024*1024+1))
    monkeypatch.setattr(imaging,'MAX_PIXELS',100)
    with pytest.raises(ValueError,match='megapíxeles'):load_image(raw)

def test_stale_tab_and_result(client,raw):
    first=client.post('/api/upload',data={'image':(io.BytesIO(raw),'one.png')}).json['image_key']
    result=client.post('/api/process',json=body());old_revision=result.json['revision']
    assert client.get('/api/export/png?revision='+old_revision).status_code==200
    client.post('/api/process',json=body(parameters={'sharpness':.3}))
    assert client.get('/api/export/png?revision='+old_revision).status_code==400
    assert client.get('/api/image/after?v='+old_revision).status_code==400
    client.post('/api/upload',data={'image':(io.BytesIO(raw),'two.png')})
    assert client.post('/api/process',json=body(),headers={'X-Palimpsesto-Image':first}).status_code==400
    assert client.get('/api/image/original?image_key='+first).status_code==400
    assert client.post('/api/reset',json={},headers={'X-Palimpsesto-Image':first}).status_code==400

def test_expired_session(client):
    with client.session_transaction() as sess:sid=sess['sid']
    server.states[sid]['access']=time.monotonic()-3601
    r=client.get('/api/image/original');assert r.status_code==400 and 'expiró' in r.json['error']

def test_session_errors_have_machine_code(client):
    # La interfaz ofrece «cargar otra foto» (no «reintentar») solo cuando code=='session'.
    with client.session_transaction() as sess:sid=sess['sid']
    server.states[sid]['access']=time.monotonic()-3601
    r=client.post('/api/process',json=body());assert r.status_code==400 and r.json['code']=='session'
    other=server.app.test_client()
    r=other.post('/api/detect',json={'kind':'manuscrito','method':'auto','scope_confirmed':True})
    assert r.status_code==400 and r.json['code']=='session'

def test_validation_errors_are_not_session_errors(client):
    r=client.post('/api/process',json=body(aspect='wrong'));assert r.status_code==400 and 'code' not in r.json

def test_recovery_after_error(client):
    assert client.post('/api/process',json=body(aspect='wrong')).status_code==400
    assert client.post('/api/process',json=body()).status_code==200
    assert client.get('/api/export/unknown').status_code==400
    assert client.get('/api/export/png').status_code==200

def test_missing_and_corrupt_weights(tmp_path):
    model=ModelService(tmp_path);assert model.classifier is None and model.segmenter is None;assert len(model.errors)==2
    (tmp_path/'classifier.pt').write_bytes(b'bad checkpoint');(tmp_path/'unet_resnet18_imagenet.pth').write_bytes(b'bad checkpoint')
    model=ModelService(tmp_path);assert model.classifier is None and model.segmenter is None;assert len(model.errors)==2

def test_private_preview_not_cached(client):assert client.get('/api/image/original').headers['Cache-Control']=='no-store'

def test_concurrent_rotate_waits_for_processing(client,monkeypatch):
    import threading
    from concurrent.futures import ThreadPoolExecutor
    entered=threading.Event();release=threading.Event();rotated=threading.Event()
    original=server.enhance
    def delayed(*args,**kwargs):
        entered.set();assert release.wait(5);return original(*args,**kwargs)
    monkeypatch.setattr(server,'enhance',delayed)
    cookie=client.get_cookie('session').value
    def call(route,payload):
        other=server.app.test_client();other.set_cookie('session',cookie)
        response=other.post(route,json=payload)
        if route.endswith('rotate'):rotated.set()
        return response.status_code
    with ThreadPoolExecutor(2) as pool:
        processing=pool.submit(call,'/api/process',body());assert entered.wait(5)
        rotation=pool.submit(call,'/api/rotate',{'direction':'right','kind':'documento_impreso'})
        assert not rotated.wait(.15);release.set()
        assert processing.result()==200 and rotation.result()==200
    assert client.get('/api/export/png').status_code==400

def test_no_500_for_malformed_local_requests(client):
    for route in ['/api/process','/api/detect','/api/rotate']:
        for bad in [[],{},False,'x',{'kind':{'bad':1}}]:
            r=client.post(route,json=bad);assert 400<=r.status_code<500,(route,bad,r.status_code)
