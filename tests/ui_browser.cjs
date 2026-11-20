// Browser integration tests. Start run.py first; npm install; npm run test:ui.
const fs=require('fs'),path=require('path'),assert=require('assert');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..'),out=path.join(root,'results/browser');fs.mkdirSync(out,{recursive:true});
const base=process.env.PALIMPSESTO_BASE_URL||'http://127.0.0.1:8765';
const chrome=process.env.CHROME_PATH||(process.platform==='win32'?'C:/Program Files/Google/Chrome/Application/chrome.exe':undefined);
const launchOptions={headless:true,...(chrome&&fs.existsSync(chrome)?{executablePath:chrome}:{})};

// --- utilidades del sistema de avisos (static/feedback.js) ---
const toast=(page,type)=>page.locator(`#toasts .toast${type?'.toast-'+type:''}:not(.leaving)`);
const toastText=async(page,type)=>(await toast(page,type).allInnerTexts()).join(' | ');
// Un aviso cuenta como visible solo si queda entero dentro de la ventana actual.
const inViewport=loc=>loc.evaluate(el=>{const r=el.getBoundingClientRect();return r.top>=0&&r.left>=0&&r.bottom<=innerHeight&&r.right<=innerWidth&&r.height>0});
// Los errores de red provocados a propósito aparecen en consola como recurso fallido; no son errores de la página.
const ignoredConsole=t=>/Failed to load resource/.test(t);

(async()=>{
const browser=await chromium.launch(launchOptions);
const context=await browser.newContext({viewport:{width:1440,height:1080}}),page=await context.newPage(),errors=[],checks=[];
page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error'&&!ignoredConsole(m.text()))errors.push(m.text())});
const done=async(p=page)=>{await p.locator('#busy').waitFor({state:'hidden',timeout:60000})};
const check=async(name,fn)=>{await fn();checks.push(name)};
try{
await page.goto(base);await page.waitForLoadState('networkidle');
await check('ready_models',async()=>{const status=await(await page.request.get(base+'/api/status')).json();assert(status.classifier&&status.segmenter&&status.scope_screen)});
await check('responsive_home',async()=>{for(const width of [320,390,768,1440]){await page.setViewportSize({width,height:900});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),'horizontal overflow '+width)}});
await page.setViewportSize({width:1440,height:1080});
await page.locator('#load-demo').click();await page.locator('#step-2').waitFor({state:'visible'});await done();
await check('upload_success_toast',async()=>{assert((await toastText(page,'success')).includes('Fotografía cargada'));assert(await inViewport(toast(page,'success').first()))});
await check('capture_quality_traffic_light',async()=>{const box=page.locator('#capture-quality');assert(await box.isVisible(),'semáforo visible en el paso 2');
  assert.equal(await box.getAttribute('data-verdict'),'ok');assert.equal(await page.locator('#cq-checks li').count(),5);assert(await page.locator('#cq-retake').isHidden())});
await check('explicit_scope_confirmation',async()=>{await page.locator('#confirm-kind').click();assert(await page.locator('#step-2').isVisible());
  assert((await toastText(page,'warning')).includes('confirmación'));
  assert(await page.locator('#confirm-scope-feedback').isVisible(),'mensaje junto a la casilla');
  assert.equal(await page.evaluate(()=>document.activeElement.id),'confirm-scope','el foco va a la casilla')});
await check('no_duplicate_toasts',async()=>{await page.locator('#confirm-kind').click();await page.locator('#confirm-kind').click();assert.equal(await page.locator('#toasts .toast[data-key="confirm-scope"]').count(),1)});
await page.locator('#confirm-scope').check();await page.locator('[data-kind="documento_impreso"]').click();await page.locator('#confirm-kind').click();await page.locator('#step-3').waitFor({state:'visible'});await done();
await check('field_feedback_cleared',async()=>{assert(await page.locator('#confirm-scope-feedback').isHidden());assert.equal(await page.locator('#toasts .toast[data-key="confirm-scope"]').count(),0)});
await check('invalid_aspect_and_recovery',async()=>{await page.locator('#aspect').fill('-1');await page.locator('#confirm-corners').click();await done();assert(await page.locator('#step-3').isVisible());
  assert((await toastText(page,'error')).includes('proporción'));assert(await page.locator('#aspect-feedback').isVisible());assert.equal(await page.locator('#aspect').getAttribute('aria-invalid'),'true');
  await page.locator('#aspect').fill('0');assert(await page.locator('#aspect-feedback').isHidden())});
await check('network_error_retry_action',async()=>{await page.route('**/api/process',route=>route.abort());await page.locator('#confirm-corners').click();await done();
  const err=toast(page,'error').filter({hasText:'Sin conexión'});assert(await err.isVisible());assert(await inViewport(err));
  await page.unroute('**/api/process');await err.getByRole('button',{name:'Reintentar'}).click();await page.locator('#step-4').waitFor({state:'visible'});await done();
  assert.equal(await toast(page,'error').count(),0,'el error se cierra al resolverse');assert((await toastText(page,'success')).includes('Vista frontal lista'))});
await check('slow_operation_feedback',async()=>{await page.route('**/api/process',route=>setTimeout(()=>route.continue().catch(()=>{}),3200));
  await page.locator('#sharpness').fill('30');await page.locator('#sharpness').dispatchEvent('change');
  await page.locator('#busy-elapsed').waitFor({state:'visible',timeout:5000});assert(/Lleva \d+ s/.test(await page.locator('#busy-elapsed').innerText()));
  await done();await page.unroute('**/api/process')});
await check('stale_preview_and_retry',async()=>{await page.route('**/api/process',route=>route.abort());await page.locator('#sharpness').fill('20');await page.locator('#sharpness').dispatchEvent('change');await done();
  assert(await page.locator('#stale-banner').isVisible());assert(await page.locator('.compare-card').evaluate(el=>el.classList.contains('stale')));
  await page.locator('#confirm-result').click();assert(await page.locator('#step-4').isVisible(),'no exporta un resultado viejo');
  await page.unroute('**/api/process');await page.locator('#stale-retry').click();await done();assert(await page.locator('#stale-banner').isHidden())});
await check('error_persists_success_expires',async()=>{await page.evaluate(()=>{Feedback.notify({type:'error',key:'t-err',title:'Prueba persistente'});Feedback.notify({type:'success',key:'t-ok',title:'Prueba breve',timeout:800})});
  await page.mouse.move(5,1000);await page.waitForTimeout(1500);
  assert.equal(await page.locator('#toasts [data-key="t-ok"]').count(),0,'la confirmación se cierra sola');assert(await page.locator('#toasts [data-key="t-err"]').isVisible(),'el error permanece');
  await page.locator('#toasts [data-key="t-err"]').focus();await page.keyboard.press('Escape');await page.waitForTimeout(500);assert.equal(await page.locator('#toasts [data-key="t-err"]').count(),0,'Escape cierra el aviso')});
await check('screen_reader_regions',async()=>{assert.equal(await page.locator('#live-assertive').getAttribute('role'),'alert');assert.equal(await page.locator('#live-polite').getAttribute('aria-live'),'polite');
  await page.evaluate(()=>Feedback.notify({type:'error',key:'sr',title:'Aviso para lector'}));await page.waitForTimeout(150);assert((await page.locator('#live-assertive').innerText()).includes('Aviso para lector'));await page.evaluate(()=>Feedback.dismiss('sr'))});
await check('detail_at_output_resolution',async()=>{await page.locator('#open-detail').click();assert(await page.locator('#detail-dialog').isVisible());await page.locator('#detail-image').evaluate(im=>im.decode());assert(await page.locator('#detail-image').evaluate(im=>im.naturalWidth>100));await page.locator('[data-detail="before"]').click();await page.locator('#detail-image').evaluate(im=>im.decode());await page.locator('#close-detail').click()});
await check('adjust_undo_and_zero',async()=>{await page.locator('#sharpness').fill('45');await page.locator('#sharpness').dispatchEvent('change');await done();await page.locator('#undo-adjustment').click();await done();await page.locator('#reset-adjustments').click();await done();assert.equal(await page.locator('#sharpness').inputValue(),'0');assert((await toastText(page,'success')).includes('Mejoras en cero'))});
await check('discard_needs_confirmation',async()=>{await page.locator('#reject-result').click();assert(await page.locator('#confirm-dialog').isVisible());assert.equal(await page.evaluate(()=>document.activeElement.id),'confirm-cancel','la opción segura queda enfocada');
  await page.keyboard.press('Escape');assert(await page.locator('#confirm-dialog').isHidden());assert(await page.locator('#step-4').isVisible(),'cancelar conserva el trabajo')});
await page.locator('#confirm-result').click();await page.locator('#step-5').waitFor({state:'visible'});
await check('export_four_formats',async()=>{for(const fmt of ['zip','png','pdf','json']){const selector=fmt==='zip'?'.download-link':'.export-links a[href*="/api/export/'+fmt+'"]';const [download]=await Promise.all([page.waitForEvent('download'),page.locator(selector).click()]);const failure=await download.failure();assert(!failure,failure);await download.saveAs(path.join(out,'browser_export.'+fmt))}
  assert((await toastText(page,'info')).includes('Descarga solicitada'));assert.equal(await page.locator('#toasts [data-key="download"]').count(),1)});
await check('stale_export_step_disabled',async()=>{await page.locator('[data-step="3"]').click();await page.locator('#aspect').fill('.75');assert(await page.locator('[data-step="5"]').isDisabled())});
await page.locator('[data-step="2"]').click();await page.locator('#replace-image').click();await page.locator('#confirm-ok').click();await page.locator('#step-1').waitFor({state:'visible'});
await check('outside_scope_cat',async()=>{await page.locator('#file-input').setInputFiles(path.join(root,'results/scope/chelsea.png'));await page.locator('#step-2').waitFor({state:'visible'});await done();assert(await page.locator('#scope-warning').isVisible());assert.equal(await page.locator('#scores .score-row').count(),0);
  assert((await toastText(page,'warning')).includes('pieza admitida'));await page.screenshot({path:path.join(out,'scope_warning.png'),fullPage:true});await page.locator('#replace-image').click();await page.locator('#step-1').waitFor({state:'visible'})});
await check('invalid_and_empty_file',async()=>{await page.locator('#file-input').setInputFiles({name:'invalid.png',mimeType:'image/png',buffer:Buffer.from('not a png')});await done();assert(await toast(page,'error').first().isVisible());assert(await page.locator('#file-input-feedback').isVisible());
  await page.locator('#file-input').setInputFiles({name:'empty.png',mimeType:'image/png',buffer:Buffer.alloc(0)});assert((await toastText(page,'error')).includes('vacío'));assert.equal(await page.locator('#toasts [data-key="upload"]').count(),1)});
await check('responsive_mobile',async()=>{await page.setViewportSize({width:390,height:844});await page.screenshot({path:path.join(out,'home_mobile.png'),fullPage:true});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1))});

// --- celular con la página desplazada: el aviso debe verse sin buscarlo ---
await check('mobile_scrolled_feedback_visible',async()=>{const m=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true});m.on('pageerror',e=>errors.push(e.message));
  await m.goto(base);await m.locator('#load-demo').click();await m.locator('#step-2').waitFor({state:'visible'});await done(m);
  await m.locator('#confirm-kind').scrollIntoViewIfNeeded();assert(await m.evaluate(()=>scrollY>300),'la página está desplazada');await m.locator('#confirm-kind').click();await m.waitForTimeout(400);
  const w=toast(m,'warning').first();assert(await inViewport(w),'aviso dentro de la ventana');
  const box=await w.boundingBox(),btn=await m.locator('#confirm-kind').boundingBox();assert(box.y+box.height<=btn.y||btn.y+btn.height<=box.y,'el aviso no tapa el botón principal');
  assert(await m.locator('#toasts .toast').count()<=2,'como máximo dos avisos en el celular');
  await m.screenshot({path:path.join(out,'mobile_scrolled_feedback.png')});await m.close()});
await check('reduced_motion',async()=>{const ctx=await browser.newContext({viewport:{width:1024,height:800},reducedMotion:'reduce'}),r=await ctx.newPage();r.on('pageerror',e=>errors.push(e.message));
  await r.goto(base);await r.evaluate(()=>Feedback.notify({type:'success',title:'Sin movimiento'}));
  const anim=await r.locator('#toasts .toast').first().evaluate(el=>getComputedStyle(el).animationName);assert.equal(anim,'none');await ctx.close()});
assert.deepEqual(errors,[]);
const report={passed:checks.length,checks,page_errors:errors,browser:'Chromium/Chrome headless',viewports:[320,390,768,1024,1440],note:'Automation, not a human usability study.'};fs.writeFileSync(path.join(out,'verification.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
}catch(e){await page.screenshot({path:path.join(out,'failure.png'),fullPage:true});throw e}finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
