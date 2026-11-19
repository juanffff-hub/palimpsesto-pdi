"""Servidor local. Las imágenes permanecen en memoria durante la sesión."""
import io,secrets,time,threading,os,json
from pathlib import Path
from flask import Flask,request,jsonify,send_file,session,render_template,g
from werkzeug.exceptions import HTTPException
from .models import ModelService,CLASSES
from .imaging import load_image,resize_long,encode_png,detect_quad,rectify,enhance,compare_metrics,PRESETS
from .exporting import build_report,create_pdf,create_bundle
from .validation import object_payload,choice,number,assess_input

ROOT=Path(__file__).resolve().parents[1]
app=Flask(__name__,template_folder=str(ROOT/'templates'),static_folder=str(ROOT/'static'))
app.secret_key=secrets.token_hex(32)
app.config.update(MAX_CONTENT_LENGTH=42*1024*1024,SESSION_COOKIE_SAMESITE='Strict',SESSION_COOKIE_HTTPONLY=True)
models=None;states={};lock=threading.RLock();model_lock=threading.RLock()
operation_lock=threading.RLock()

@app.before_request
def serialize_image_operations():
    # A local CPU application: serialize stateful operations, including exports,
    # so a second tab cannot rotate pixels halfway through an existing request.
    if request.path.startswith('/api/') and request.path!='/api/status':
        operation_lock.acquire();g.palimpsesto_operation_locked=True

@app.teardown_request
def release_image_operation(error=None):
    if g.pop('palimpsesto_operation_locked',False):operation_lock.release()

def current():
    sid=session.get('sid')
    with lock:
        state=states.get(sid)
        if not state:raise ValueError('La sesión no tiene una imagen. Carga una foto para comenzar.')
        if time.monotonic()-state['access']>3600:
            states.pop(sid,None);raise ValueError('La sesión expiró tras una hora sin actividad. Vuelve a cargar la fotografía.')
        expected=request.headers.get('X-Palimpsesto-Image') or request.args.get('image_key')
        if expected and expected!=sid:raise ValueError('La imagen cambió en otra pestaña. Vuelve a cargar la foto en esta pestaña antes de continuar.')
        state['access']=time.monotonic();return state

@app.before_request
def local_origin():
    if request.method=='POST':
        origin=request.headers.get('Origin')
        if origin and origin!=request.host_url.rstrip('/'):
            return jsonify(error='Origen de solicitud no permitido.'),403

@app.errorhandler(Exception)
def handle_error(error):
    if isinstance(error,HTTPException):
        messages={400:'La solicitud no tiene un formato válido.',404:'Ese recurso no existe.',405:'Esta operación no admite ese método.',413:'El archivo o la solicitud supera el tamaño permitido.',415:'Envía los parámetros como JSON válido.'}
        return jsonify(error=messages.get(error.code,error.description),code='http_'+str(error.code)),error.code
    if isinstance(error,(ValueError,KeyError,TypeError)):return jsonify(error=str(error)),400
    app.logger.exception('Error de procesamiento');return jsonify(error='No se pudo completar la operación. Cambia la imagen o reinicia los ajustes.'),500

@app.get('/')
def home():return render_template('index.html')

@app.get('/api/status')
def status():return jsonify(version='0.2.0',classifier=models is not None and models.classifier is not None,segmenter=models is not None and models.segmenter is not None,scope_screen=models is not None and getattr(models,'scope_bank',None) is not None,model_warnings=getattr(models,'errors',[]),presets=PRESETS,local=True)

@app.post('/api/upload')
def upload():
    f=request.files.get('image')
    if not f:raise ValueError('Selecciona una imagen.')
    data=f.read();rgb,meta=load_image(data);sid=secrets.token_urlsafe(24);t=time.perf_counter()
    with model_lock:
        prediction=models.classify(rgb);assessment=assess_input(rgb,prediction);kind=prediction['class'] or 'documento_impreso';corners=detect_quad(rgb,models,kind)
    state={'original_bytes':data,'rgb':rgb,'metadata':meta,'name':Path(f.filename or 'imagen').name[:180],'classification':prediction,'detection':corners,'assessment':assessment,'scope_confirmed':False,'access':time.monotonic(),'result':None}
    with lock:
        old=session.get('sid')
        if old:states.pop(old,None)
        now=time.monotonic()
        for key in [k for k,v in states.items() if now-v['access']>3600]:states.pop(key,None)
        if len(states)>=8:raise ValueError('Hay demasiadas sesiones activas. Cierra una sesión antes de continuar.')
        states[sid]=state;session['sid']=sid
    visible_prediction=prediction.copy()
    if assessment['requires_confirmation']:visible_prediction.update({'class':None,'scores':None})
    return jsonify(metadata=meta,name=state['name'],classification=visible_prediction,assessment=assessment,detection=corners,presets=PRESETS,image_key=sid,elapsed_ms=round(1000*(time.perf_counter()-t)),image_url='/api/image/original?image_key='+sid)

@app.post('/api/detect')
def detect():
    state=current();body=object_payload(request.get_json(),['kind','method','scope_confirmed'],['kind']);kind=choice(body.get('kind'),CLASSES,'Tipo de pieza');method=choice(body.get('method','auto'),['auto','unet','contornos','manual'],'Método de borde')
    if 'scope_confirmed' in body and type(body['scope_confirmed']) is not bool:raise ValueError('La confirmación de alcance debe ser verdadera o falsa.')
    if body.get('scope_confirmed') is True:state['scope_confirmed']=True
    if state['assessment']['requires_confirmation'] and not state['scope_confirmed']:raise ValueError('La imagen parece fuera del alcance. Confirma que contiene una pieza plana o carga otra fotografía.')
    with model_lock:corners=detect_quad(state['rgb'],models,kind,method)
    state['detection']=corners;state['result']=None;return jsonify(corners)

@app.post('/api/rotate')
def rotate():
    import cv2
    state=current();body=object_payload(request.get_json(),['direction','kind'],['direction','kind']);direction=choice(body.get('direction'),['left','right'],'Dirección');kind=choice(body.get('kind'),CLASSES,'Tipo de pieza')
    state['rgb']=cv2.rotate(state['rgb'],cv2.ROTATE_90_COUNTERCLOCKWISE if direction=='left' else cv2.ROTATE_90_CLOCKWISE)
    state['metadata']['user_rotation_degrees']=(state['metadata'].get('user_rotation_degrees',0)+(90 if direction=='right' else -90))%360
    state['metadata']['working_width']=state['rgb'].shape[1];state['metadata']['working_height']=state['rgb'].shape[0]
    with model_lock:corners=detect_quad(state['rgb'],models,kind)
    state['detection']=corners;state['result']=None;return jsonify(detection=corners)

@app.post('/api/process')
def process():
    state=current();body=object_payload(request.get_json(),['kind','points','aspect','parameters'],['kind','points']);kind=body.get('kind')
    state['result']=None
    choice(kind,CLASSES,'Tipo de pieza')
    if state['assessment']['requires_confirmation'] and not state['scope_confirmed']:raise ValueError('Confirma primero que la foto corresponde a una pieza admitida.')
    points=body.get('points');aspect=number(body.get('aspect',0),'Proporción ancho/alto',0,10);params=body.get('parameters',{})
    t=time.perf_counter();before,H=rectify(state['rgb'],points,aspect,max_side=2400);after,p=enhance(before,params,kind);metrics=compare_metrics(before,after)
    report=build_report(state,p,points,H,metrics,kind,state['detection']['method'],aspect)
    revision=secrets.token_hex(12);result={'before':before,'after':after,'report':report,'revision':revision};state['result']=result
    return jsonify(width=after.shape[1],height=after.shape[0],metrics=metrics,parameters=p,elapsed_ms=round(1000*(time.perf_counter()-t)),revision=revision)

@app.get('/api/image/<which>')
def get_image(which):
    state=current()
    if which=='original':im=state['rgb']
    elif which in ['before','after'] and state['result']:
        if request.args.get('v') and request.args['v']!=state['result']['revision']:raise ValueError('La vista previa corresponde a un resultado anterior. Vuelve a procesar la imagen.')
        im=state['result'][which]
    else:raise ValueError('Todavía no hay una imagen procesada.')
    limit=2400 if request.args.get('detail')=='1' and which!='original' else 1200
    response=send_file(io.BytesIO(encode_png(resize_long(im,limit))),mimetype='image/png',max_age=0);response.headers['Cache-Control']='no-store';return response

@app.get('/api/export/<fmt>')
def export(fmt):
    state=current();result=state['result']
    if not result:raise ValueError('Procesa y revisa la imagen antes de exportar.')
    if request.args.get('revision') and request.args['revision']!=result['revision']:raise ValueError('Este enlace corresponde a un resultado anterior. Revisa y exporta la versión actual.')
    rgb=result['after'];report=result['report']
    if fmt=='png':data=encode_png(rgb);mime='image/png';name='palimpsesto_mejorada.png'
    elif fmt=='pdf':data=create_pdf(rgb,report);mime='application/pdf';name='palimpsesto_consulta.pdf'
    elif fmt=='json':data=json.dumps(report,ensure_ascii=False,indent=2).encode('utf-8');mime='application/json';name='registro_palimpsesto.json'
    elif fmt=='zip':data=create_bundle(rgb,report,state['original_bytes']);mime='application/zip';name='palimpsesto_resultado.zip'
    else:raise ValueError('Formato desconocido.')
    return send_file(io.BytesIO(data),mimetype=mime,download_name=name,as_attachment=True,max_age=0)

@app.post('/api/reset')
def reset():
    expected=request.headers.get('X-Palimpsesto-Image')
    if expected and session.get('sid') in states and expected!=session.get('sid'):raise ValueError('La imagen cambió en otra pestaña. Recarga esta pestaña antes de continuar.')
    with lock:states.pop(session.get('sid'),None)
    session.clear();return jsonify(ok=True)

def main():
    global models
    models=ModelService(ROOT/'models')
    print('Palimpsesto local: http://127.0.0.1:8765',flush=True)
    app.run(host='127.0.0.1',port=int(os.environ.get('PALIMPSESTO_PORT','8765')),debug=False,threaded=True)
