import io,json,zipfile,hashlib
import numpy as np,pytest,cv2
from PIL import Image
from palimpsesto.imaging import load_image,encode_png,validate_quad,rectify,enhance,compare_metrics,PRESETS
from palimpsesto.exporting import create_pdf,create_bundle
from palimpsesto import server

@pytest.fixture
def photo():
    a=np.full((360,480,3),230,np.uint8)
    a[60:120,70:400]=[210,40,25];a[140:180,80:380]=[20,130,210]
    return a

def test_rgb_roundtrip(photo):
    raw=encode_png(photo);out,meta=load_image(raw)
    assert np.array_equal(out,photo)
    assert meta['sha256']==hashlib.sha256(raw).hexdigest()

def test_orientation_exif(photo):
    im=Image.fromarray(photo);exif=im.getexif();exif[274]=6;b=io.BytesIO();im.save(b,'JPEG',exif=exif)
    out,meta=load_image(b.getvalue());assert out.shape[:2]==(480,360);assert meta['exif_orientation']==6

@pytest.mark.parametrize('raw',[b'not an image',b'',b'%PDF-1.5'])
def test_invalid_input(raw):
    with pytest.raises(ValueError):load_image(raw)

def test_transparent_background():
    a=np.zeros((100,100,4),np.uint8);out,_=load_image(encode_png(a));assert (out==255).all()

@pytest.mark.parametrize('points',[
    [[0,0],[1,1],[1,0],[0,1]],[[0,0],[0,0],[1,1],[0,1]],
    [[-.1,0],[1,0],[1,1],[0,1]],[[0,0],[.01,0],[.01,.01],[0,.01]],
    [[float('nan'),0],[1,0],[1,1],[0,1]]])
def test_reject_invalid_quad(points):
    with pytest.raises(ValueError):validate_quad(points)

def test_homography_corner_correspondence(photo):
    q=np.array([[.1,.15],[.8,.05],[.9,.85],[.15,.9]],np.float32)
    out,H=rectify(photo,q,aspect=.75)
    src=q*np.array([479,359]);dest=cv2.perspectiveTransform(src.astype(np.float32)[None],H)[0]
    expected=np.array([[0,0],[out.shape[1]-1,0],[out.shape[1]-1,out.shape[0]-1],[0,out.shape[0]-1]])
    assert np.max(np.abs(dest-expected))<.001
    assert abs(out.shape[1]/out.shape[0]-.75)<.01

@pytest.mark.parametrize('kind',list(PRESETS))
def test_zero_adjustments_preserve_pixels(photo,kind):
    out,_=enhance(photo,{'illumination':0,'contrast':0,'denoise':0,'sharpness':0,'binary':'off'},kind)
    assert np.array_equal(out,photo)

@pytest.mark.parametrize('binary',['otsu','sauvola'])
def test_text_derivative(photo,binary):
    out,_=enhance(photo,{'binary':binary},'documento_impreso');assert set(np.unique(out))<={0,255}
    with pytest.raises(ValueError):enhance(photo,{'binary':binary},'pintura')

def test_no_reference_no_reference_metrics(photo):
    m=compare_metrics(photo,photo);assert m['ssim'] is None and m['psnr'] is None

class StubModels:
    def classify(self,rgb):return {'class':'documento_impreso','available':True,'scores':dict(documento_impreso=.7,manuscrito=.2,pintura=.1)}
    def segment(self,rgb):return None

def test_api_complete_and_isolated(photo):
    server.app.config['TESTING']=True;server.models=StubModels();client=server.app.test_client();other=server.app.test_client();raw=encode_png(photo)
    assert other.get('/api/export/png').status_code==400
    r=client.post('/api/upload',data={'image':(io.BytesIO(raw),'example.png')});assert r.status_code==200
    q=[[.02,.02],[.98,.02],[.98,.98],[.02,.98]]
    r=client.post('/api/process',json={'kind':'documento_impreso','points':q,'aspect':0,'parameters':PRESETS['documento_impreso']});assert r.status_code==200
    metrics=r.json['metrics'];assert metrics['ssim'] is None
    zipped=client.get('/api/export/zip');assert zipped.status_code==200
    with zipfile.ZipFile(io.BytesIO(zipped.data)) as z:
        assert z.read('original.png')==raw
        report=json.loads(z.read('registro.json'));assert report['original']['sha256']==hashlib.sha256(raw).hexdigest()
        assert z.read('palimpsesto_consulta.pdf').startswith(b'%PDF-')
        out=Image.open(io.BytesIO(z.read('palimpsesto_mejorada.png')));assert out.width>100
    assert other.get('/api/image/original').status_code==400
    bad=client.post('/api/process',json={'kind':'documento_impreso','points':[[0,0]]*4,'parameters':{}})
    assert bad.status_code==400
    assert client.get('/api/export/png').status_code==400
    assert client.post('/api/detect',json={'kind':'pintura','method':'manual'}).status_code==200
    assert client.get('/api/export/png').status_code==400
    assert client.post('/api/rotate',json={'kind':'pintura','direction':'right'}).status_code==200
    assert client.post('/api/reset',json={}).status_code==200
    assert client.get('/api/image/original').status_code==400

def test_cross_origin_post_rejected():
    client=server.app.test_client();r=client.post('/api/reset',json={},headers={'Origin':'https://unrelated.example'});assert r.status_code==403
