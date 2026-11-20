// Capturas de la interfaz para el README (servidor activo: python run.py).
// Uso: node scripts/capture_gui.cjs   (CHROME_PATH opcional). Usa el ejemplo sintético, no fotos reales.
const path=require('path'),fs=require('fs');const {chromium}=require('playwright');
const base=process.env.PALIMPSESTO_BASE_URL||'http://127.0.0.1:8765',out=path.resolve(__dirname,'../docs/img');fs.mkdirSync(out,{recursive:true});
const chrome=process.env.CHROME_PATH;
(async()=>{const b=await chromium.launch(chrome?{executablePath:chrome}:{});
const p=await b.newPage({viewport:{width:1366,height:860},deviceScaleFactor:1});const idle=()=>p.locator('#busy').waitFor({state:'hidden',timeout:60000});
const shot=async n=>{await p.waitForTimeout(700);await p.screenshot({path:path.join(out,n)})};
await p.goto(base);await p.waitForLoadState('networkidle');await shot('gui_01_cargar.png');
await p.click('#load-demo');await p.locator('#step-2').waitFor();await idle();await p.evaluate(()=>Feedback.clear());await shot('gui_02_identificar.png');
await p.check('#confirm-scope');await p.click('#confirm-kind');await p.locator('#step-3').waitFor();await idle();await p.evaluate(()=>Feedback.clear());await shot('gui_03_encuadrar.png');
await p.click('#confirm-corners');await p.locator('#step-4').waitFor();await idle();await p.evaluate(()=>Feedback.clear());await shot('gui_04_mejorar.png');
await p.click('#confirm-result');await p.locator('#step-5').waitFor();await p.evaluate(()=>Feedback.clear());await shot('gui_05_guardar.png');
// Avisos: error con acción de recuperación
await p.click('[data-step="3"]');await p.fill('#aspect','-1');await p.click('#confirm-corners');await idle();await shot('gui_06_aviso_error.png');
const m=await b.newPage({viewport:{width:390,height:844},deviceScaleFactor:2,isMobile:true});await m.goto(base);await m.click('#load-demo');await m.locator('#step-2').waitFor();await m.locator('#busy').waitFor({state:'hidden'});await m.waitForTimeout(700);await m.screenshot({path:path.join(out,'gui_07_movil.png')});
await b.close();console.log('Capturas en',out)})().catch(e=>{console.error(e);process.exitCode=1});
