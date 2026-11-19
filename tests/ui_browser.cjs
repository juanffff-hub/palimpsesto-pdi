// Browser integration tests. Start run.py first; npm install; npm run test:ui.
const fs=require('fs'),path=require('path'),assert=require('assert');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..'),out=path.join(root,'results/browser');fs.mkdirSync(out,{recursive:true});
const base=process.env.PALIMPSESTO_BASE_URL||'http://127.0.0.1:8765';
const chrome=process.env.CHROME_PATH||(process.platform==='win32'?'C:/Program Files/Google/Chrome/Application/chrome.exe':undefined);
(async()=>{
const browser=await chromium.launch({headless:true,...(chrome&&fs.existsSync(chrome)?{executablePath:chrome}:{})});
const context=await browser.newContext({viewport:{width:1440,height:1080}}),page=await context.newPage(),errors=[],checks=[];page.on('pageerror',e=>errors.push(e.message));
const done=async()=>{await page.locator('#busy').waitFor({state:'hidden',timeout:60000})};
const check=async(name,fn)=>{await fn();checks.push(name)};
try{
await page.goto(base);await page.waitForLoadState('networkidle');
await check('ready_models',async()=>{const status=await(await page.request.get(base+'/api/status')).json();assert(status.classifier&&status.segmenter&&status.scope_screen)});
await check('responsive_home',async()=>{for(const width of [320,390,768,1440]){await page.setViewportSize({width,height:900});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),'horizontal overflow '+width)}});
await page.locator('#load-demo').click();await page.locator('#step-2').waitFor({state:'visible'});await done();
await check('explicit_scope_confirmation',async()=>{await page.locator('#confirm-kind').click();assert(await page.locator('#step-2').isVisible());assert((await page.locator('#message').innerText()).includes('Confirma'))});
await page.locator('#confirm-scope').check();await page.locator('[data-kind="documento_impreso"]').click();await page.locator('#confirm-kind').click();await page.locator('#step-3').waitFor({state:'visible'});await done();
await check('invalid_aspect_and_recovery',async()=>{await page.locator('#aspect').fill('-1');await page.locator('#confirm-corners').click();await done();assert(await page.locator('#step-3').isVisible());assert((await page.locator('#message').innerText()).includes('proporción'));await page.locator('#aspect').fill('0')});
await check('network_error_and_retry',async()=>{await page.route('**/api/process',route=>route.abort());await page.locator('#confirm-corners').click();await done();assert((await page.locator('#message').innerText()).includes('conexión'));await page.unroute('**/api/process');await page.locator('#confirm-corners').click();await page.locator('#step-4').waitFor({state:'visible'});await done()});
await check('detail_at_output_resolution',async()=>{await page.locator('#open-detail').click();assert(await page.locator('#detail-dialog').isVisible());await page.locator('#detail-image').evaluate(im=>im.decode());assert(await page.locator('#detail-image').evaluate(im=>im.naturalWidth>100));await page.locator('[data-detail="before"]').click();await page.locator('#detail-image').evaluate(im=>im.decode());await page.locator('#close-detail').click()});
await check('adjust_undo_and_zero',async()=>{await page.locator('#sharpness').fill('45');await page.locator('#sharpness').dispatchEvent('change');await done();await page.locator('#undo-adjustment').click();await done();await page.locator('#reset-adjustments').click();await done();assert.equal(await page.locator('#sharpness').inputValue(),'0')});
await page.locator('#confirm-result').click();await page.locator('#step-5').waitFor({state:'visible'});
await check('export_four_formats',async()=>{for(const fmt of ['zip','png','pdf','json']){const selector=fmt==='zip'?'.download-link':'.export-links a[href*="/api/export/'+fmt+'"]';const [download]=await Promise.all([page.waitForEvent('download'),page.locator(selector).click()]);const failure=await download.failure();assert(!failure,failure);await download.saveAs(path.join(out,'browser_export.'+fmt))}});
await check('stale_export_step_disabled',async()=>{await page.locator('[data-step="3"]').click();await page.locator('#aspect').fill('.75');assert(await page.locator('[data-step="5"]').isDisabled())});
await page.locator('[data-step="2"]').click();await page.locator('#replace-image').click();await page.locator('#step-1').waitFor({state:'visible'});
await check('outside_scope_cat',async()=>{await page.locator('#file-input').setInputFiles(path.join(root,'results/scope/chelsea.png'));await page.locator('#step-2').waitFor({state:'visible'});await done();assert(await page.locator('#scope-warning').isVisible());assert.equal(await page.locator('#scores .score-row').count(),0);await page.screenshot({path:path.join(out,'scope_warning.png'),fullPage:true});await page.locator('#replace-image').click();await page.locator('#step-1').waitFor({state:'visible'})});
await check('invalid_and_empty_file',async()=>{await page.locator('#file-input').setInputFiles({name:'invalid.png',mimeType:'image/png',buffer:Buffer.from('not a png')});await done();assert(await page.locator('#message').isVisible());await page.locator('#file-input').setInputFiles({name:'empty.png',mimeType:'image/png',buffer:Buffer.alloc(0)});assert((await page.locator('#message').innerText()).includes('vacío'))});
await check('responsive_mobile',async()=>{await page.setViewportSize({width:390,height:844});await page.screenshot({path:path.join(out,'home_mobile.png'),fullPage:true});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1))});
assert.deepEqual(errors,[]);
const report={passed:checks.length,checks,page_errors:errors,browser:'Chromium/Chrome headless',note:'Automation, not a human usability study.'};fs.writeFileSync(path.join(out,'verification.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
}catch(e){await page.screenshot({path:path.join(out,'failure.png'),fullPage:true});throw e}finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
