import io,json,zipfile,datetime,platform
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4
from .imaging import encode_png

def build_report(state,params,points,H,metrics,kind,method,aspect):
    return {'project':'Palimpsesto','version':'0.2.0','timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'original':state['metadata'],'original_name':state['name'],'classification_suggestion':state['classification'],
        'confirmed_class':kind,'corners_normalized':points,'corners_user_accepted':True,'geometry_method':method,'homography':H.tolist(),
        'input_assessment':state.get('assessment'),'capture_quality':(state.get('capture') or {}).get('by_kind',{}).get(kind),'scope_confirmation_override':state.get('scope_confirmed',False),
        'aspect_ratio_input':aspect,'aspect_ratio_status':'declarada por usuario' if aspect else 'estimada; no es medida física',
        'parameters':params,'metrics':metrics,'output_purpose':'derivado de consulta; original conservado',
        'limitations':['No reconstruye información ausente ni certifica fidelidad patrimonial.','La nitidez y el contraste no son una medida universal de calidad.','SSIM/PSNR requieren una referencia alineada.'],
        'runtime':{'python':platform.python_version()}}

def create_pdf(rgb,report):
    out=io.BytesIO();c=canvas.Canvas(out,pagesize=A4);w,h=A4
    c.setTitle('Palimpsesto - imagen y registro de mejora')
    c.setFillColorRGB(.08,.15,.18);c.rect(0,0,w,h,fill=1,stroke=0)
    c.setFillColorRGB(1,1,1);c.setFont('Helvetica-Bold',18);c.drawString(30,h-35,'PALIMPSESTO')
    c.setFont('Helvetica',9);c.drawString(30,h-52,'Copia de consulta · el original se conserva sin cambios')
    iw,ih=rgb.shape[1],rgb.shape[0];s=min((w-60)/iw,(h-110)/ih)
    c.drawImage(ImageReader(Image.fromarray(rgb)),(w-iw*s)/2,35+(h-110-ih*s)/2,iw*s,ih*s)
    c.showPage();c.setFillColorRGB(.08,.15,.18);c.setFont('Helvetica-Bold',18);c.drawString(36,h-45,'Registro de procesamiento')
    c.setFont('Helvetica',10);y=h-75
    lines=[f"Clase confirmada: {report['confirmed_class']}",f"Borde inicial: {report['geometry_method']}",f"Fecha UTC: {report['timestamp_utc'][:19]}",f"Salida: {iw} x {ih} px; disposición en A4, sin escala física certificada.",'','Parámetros:']
    lines.extend(f'  {key}: {value}' for key,value in report['parameters'].items())
    lines.extend(['','Descriptores a escala de evaluación (máximo 960 px):'])
    for name in ['laplacian_variance','rms_contrast','bright_percent']:
        lines.append(f"  {name}: {report['metrics']['before'][name]:.3f} -> {report['metrics']['after'][name]:.3f}")
    lines.extend(['','SSIM/PSNR: no disponibles; falta referencia alineada.','Mayor nitidez o contraste no demuestra recuperación de información.','','SHA-256 del archivo original:'])
    sha=report['original']['sha256'];lines.extend([sha[:32],sha[32:],'','El archivo JSON contiene esquinas, homografía y parámetros completos.','No se ha eliminado ni sobrescrito el original.'])
    for line in lines:c.drawString(36,y,line);y-=17
    c.save();return out.getvalue()

def create_bundle(rgb,report,original=None):
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('palimpsesto_mejorada.png',encode_png(rgb));z.writestr('palimpsesto_consulta.pdf',create_pdf(rgb,report))
        z.writestr('registro.json',json.dumps(report,indent=2,ensure_ascii=False).encode('utf-8'))
        if original is not None:z.writestr('original.'+('jpg' if report['original']['source_format']=='JPEG' else 'png'),original)
    return out.getvalue()
