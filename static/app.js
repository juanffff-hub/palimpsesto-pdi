'use strict';
/*
  Interfaz de Palimpsesto: cargar → identificar → encuadrar → mejorar → guardar.
  El sistema de avisos está en feedback.js (objeto Feedback).
*/
const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
const names = { documento_impreso: 'Impreso', manuscrito: 'Manuscrito', pintura: 'Pintura' };
const methodNames = { unet: 'Segmentación U-Net', contornos: 'Detección por contornos', manual: 'Borde manual' };
const sliders = ['illumination', 'contrast', 'denoise', 'sharpness'];

let step = 1, maxStep = 1, upload = null, kind = 'documento_impreso', points = [], presets = {}, params = {}, history = [];
let maskImage = null, showMask = false;  // salida de la U-Net superpuesta en el paso 3
let originalImage = null, activeCorner = 0, dragging = false, processing = false, pending = false, lastResult = null;
let lastFile = null;          // última foto intentada, para «Reintentar» la carga
let currentAbort = null, userCancelled = false;

// ---------------------------------------------------------------- utilidades
/** Segundos en formato local: «0,4 s»; por debajo de 0,1 s no se finge precisión. */
function seconds(ms) { return ms < 100 ? 'menos de 0,1 s' : (ms / 1000).toLocaleString('es-CO', { maximumFractionDigits: 1 }) + ' s'; }
function apiError(message, kind, status) { const e = Error(message); e.kind = kind; e.status = status; return e; }

/** Muestra un error con título, efecto y la acción que lo resuelve. */
function showError(e, { key, title, effect, retry, field } = {}) {
  const kind = e.kind || 'invalid';
  const actions = [];
  if (kind === 'session') actions.push({ label: 'Cargar otra foto', onClick: () => resetImage(true) });
  else if (['network', 'timeout', 'server', 'cancelled'].includes(kind) && retry) actions.push({ label: 'Reintentar', onClick: retry });
  if (field) actions.push({ label: 'Ir al campo', onClick: () => Feedback.focusField(field) });
  const titles = {
    network: 'Sin conexión con Palimpsesto',
    timeout: 'La operación tardó demasiado',
    server: 'No se pudo completar la operación',
    session: 'La sesión ya no tiene esta foto',
    cancelled: 'Dejaste de esperar la respuesta',
  };
  Feedback.notify({
    type: kind === 'cancelled' ? 'info' : 'error',
    key: key || 'error:' + kind,
    title: titles[kind] || title || 'Revisa los datos',
    text: e.message,
    detail: effect,
    actions,
  });
}

// ---------------------------------------------------------------- espera
let busyTimer = null;
function busy(on, text = 'Procesando la imagen…') {
  const box = $('#busy');
  clearInterval(busyTimer);
  document.querySelector('main').inert = on;
  document.querySelector('main').setAttribute('aria-busy', on ? 'true' : 'false');
  if (!on) { box.hidden = true; return; }
  $('#busy-text').textContent = text;
  $('#busy-elapsed').hidden = true; $('#busy-slow').hidden = true; $('#busy-cancel').hidden = true;
  box.hidden = false;
  const start = Date.now();
  // Solo se muestra el tiempo real transcurrido: el servidor no informa porcentajes.
  busyTimer = setInterval(() => {
    const s = Math.floor((Date.now() - start) / 1000);
    if (s >= 2) { $('#busy-elapsed').hidden = false; $('#busy-elapsed').textContent = `Lleva ${s} s`; }
    if (s >= 8) $('#busy-cancel').hidden = false;
    if (s >= 20) $('#busy-slow').hidden = false;
  }, 500);
}
$('#busy-cancel').onclick = () => { userCancelled = true; currentAbort?.abort(); };

async function api(url, body, form = false) {
  const abort = new AbortController(), timeout = setTimeout(() => abort.abort(), 90000);
  currentAbort = abort; userCancelled = false;
  try {
    const headers = body && !form ? { 'Content-Type': 'application/json' } : {};
    if (upload?.image_key) headers['X-Palimpsesto-Image'] = upload.image_key;
    const r = await fetch(url, {
      method: body === undefined ? 'GET' : 'POST', headers,
      body: body === undefined ? undefined : form ? body : JSON.stringify(body), signal: abort.signal,
    });
    let data;
    try { data = await r.json(); }
    catch { throw apiError('El servidor no devolvió una respuesta válida. Comprueba que Palimpsesto siga abierto.', 'server', r.status); }
    if (!r.ok) throw apiError(data.error || 'No se pudo completar la operación.', data.code === 'session' ? 'session' : r.status >= 500 ? 'server' : 'invalid', r.status);
    return data;
  } catch (e) {
    if (e.name === 'AbortError') {
      if (userCancelled) throw apiError('El servidor puede terminar la operación por su cuenta; puedes volver a intentarlo.', 'cancelled');
      throw apiError('Pasaron 90 segundos sin respuesta. Intenta con una foto más pequeña o reinicia el servidor.', 'timeout');
    }
    if (e instanceof TypeError) throw apiError('Comprueba tu conexión y que Palimpsesto siga abierto en el computador que lo ejecuta. Después, inténtalo de nuevo.', 'network');
    throw e;
  } finally { clearTimeout(timeout); if (currentAbort === abort) currentAbort = null; }
}

function imageUrl(which, revision = '') {
  return '/api/image/' + which + '?image_key=' + encodeURIComponent(upload.image_key) + '&v=' + encodeURIComponent(revision);
}

// ---------------------------------------------------------------- navegación
function show(n) {
  const changed = n !== step;
  step = n; maxStep = Math.max(maxStep, n);
  $$('.step-section').forEach((el, i) => {
    el.hidden = i !== n - 1;
    if (i === n - 1 && changed) { el.classList.remove('step-enter'); void el.offsetWidth; el.classList.add('step-enter'); }
  });
  $$('.steps button').forEach((b, i) => {
    b.classList.toggle('active', i === n - 1);
    b.disabled = i + 1 > maxStep;
    if (i === n - 1) b.setAttribute('aria-current', 'step'); else b.removeAttribute('aria-current');
  });
  $('#back-button').hidden = n === 1;
  if (n === 3) drawCorners();
  if (n === 4) compare();
  if (changed) window.scrollTo({ top: 0, behavior: 'smooth' });
}
$$('.steps button').forEach(b => b.onclick = () => show(Number(b.dataset.step)));
$('#back-button').onclick = () => show(Math.max(1, step - 1));
$('#help-button').onclick = () => $('#help').showModal();
$('#close-help').onclick = () => $('#help').close();

// ---------------------------------------------------------------- 1 · cargar
function fileProblem(text) {
  Feedback.fieldMessage($('#file-input'), text);
  Feedback.notify({ type: 'error', key: 'upload', title: 'No se cargó la fotografía', text, detail: 'Sigues en el paso 1; elige otra foto.' });
}

async function loadFile(file) {
  if (!file) return;
  lastFile = file;
  Feedback.clearField($('#file-input'));
  if (file.size === 0) { fileProblem('El archivo está vacío. Selecciona otra fotografía.'); return; }
  if (file.size > 40 * 1024 * 1024) { fileProblem('El archivo supera 40 MB. Usa una copia más pequeña.'); return; }
  busy(true, 'Leyendo la fotografía y proponiendo su borde…');
  try {
    const f = new FormData(); f.append('image', file);
    upload = await api('/api/upload', f, true);
    presets = upload.presets || presets;
    kind = upload.classification.class || 'documento_impreso';
    points = upload.detection.points; maxStep = 2; lastResult = null; history = [];
    maskImage = null; showMask = false;
    $('#class-image').src = upload.image_url;
    $('#file-info').textContent = `${upload.name} · ${upload.metadata.width} × ${upload.metadata.height} px`;
    $('#prediction-label').textContent = upload.classification.class ? names[kind] : 'Selecciona una pieza admitida';
    renderScores(upload.classification.scores);
    setKind(kind);
    $('#confirm-scope').checked = false; Feedback.clearField($('#confirm-scope'));
    const assessment = upload.assessment || {};
    $('#scope-warning').hidden = !assessment.requires_confirmation;
    $('#scope-reasons').textContent = (assessment.reasons || []).join(' ');
    $('#input-warnings').textContent = (assessment.warnings || []).join(' ');
    $('#input-warnings').hidden = !assessment.warnings?.length;
    await loadOriginal();
    Feedback.clear((o, key) => key === 'upload' || key.startsWith('error:') || key === 'scope' || key === 'classification');
    show(2);
    if (assessment.requires_confirmation) {
      Feedback.notify({ type: 'warning', key: 'scope', title: 'Puede que la foto no sea una pieza admitida',
        text: (assessment.reasons || []).join(' ') || 'El contenido se aleja de las piezas conocidas.',
        detail: 'Se ocultó la sugerencia de la red. Si es una pieza válida, márcalo y elige la categoría a mano; si no, carga otra foto.',
        actions: [{ label: 'Cargar otra foto', onClick: () => resetImage(true) }] });
    } else if (!upload.classification.available) {
      Feedback.notify({ type: 'warning', key: 'classification', title: 'Clasificador no disponible',
        text: 'No se cargó la red. Elige la categoría a mano; el resto del proceso funciona igual.' });
    } else if (upload.classification.low_score) {
      Feedback.notify({ type: 'warning', key: 'classification', title: 'Sugerencia con puntuación baja',
        text: 'La red no se inclina con claridad por una categoría. Confírmala tú antes de continuar.' });
    } else {
      Feedback.notify({ type: 'success', key: 'upload-ok', title: 'Fotografía cargada',
        text: `${upload.metadata.width} × ${upload.metadata.height} px. Revisa la categoría sugerida y confirma.` });
    }
    if (assessment.warnings?.length) {
      Feedback.notify({ type: 'info', key: 'capture', title: 'Observaciones de la captura',
        text: assessment.warnings.join(' '), detail: 'Puedes continuar; revisa el detalle al final o repite la foto.' });
    }
    const capture = upload.capture?.by_kind?.[kind];
    if (capture?.verdict === 'repetir') {
      const problems = capture.checks.filter(c => c.level === 'bad').map(c => c.title.toLowerCase()).join(' y ');
      Feedback.notify({ type: 'warning', key: 'capture-quality', title: 'Conviene repetir la foto',
        text: `Problema de ${problems}. Si sigues, la copia final perderá detalle.`,
        detail: 'Tomarla de nuevo ahora evita volver al archivo después.',
        actions: [{ label: 'Cargar otra foto', onClick: () => resetImage(true) }] });
    }
  } catch (e) {
    if (e.kind === 'invalid') fileProblem(e.message);
    else showError(e, { key: 'upload', effect: 'La foto no se cargó; sigues en el paso 1.', retry: () => loadFile(lastFile) });
  } finally { busy(false); }
}

const verdicts = {
  ok: 'Buena captura: puedes continuar.',
  revisar: 'Revisa estos puntos antes de seguir.',
  repetir: 'Conviene repetir la foto ahora, mientras tienes la pieza.' };
function renderCapture() {
  const box = $('#capture-quality'), report = upload?.capture?.by_kind?.[kind];
  box.hidden = !report;
  if (!report) return;
  box.dataset.verdict = report.verdict;
  $('#cq-verdict').textContent = verdicts[report.verdict];
  const icons = { ok: '✓', warn: '!', bad: '✕' };
  $('#cq-checks').replaceChildren(...report.checks.map(c => {
    const li = document.createElement('li'); li.className = 'cq-' + c.level;
    const icon = document.createElement('span'); icon.className = 'cq-icon'; icon.textContent = icons[c.level]; icon.setAttribute('aria-hidden', 'true');
    const text = document.createElement('span'); const t = document.createElement('b'); t.textContent = c.title;
    text.append(t, c.level === 'ok' ? '' : ' · ' + c.message);
    li.append(icon, text); li.setAttribute('aria-label', `${c.title}: ${c.level === 'ok' ? 'bien' : c.message}`);
    return li;
  }));
  $('#cq-retake').hidden = report.verdict === 'ok';
}
$('#cq-retake').onclick = () => resetImage(true);

function renderScores(scores) {
  $('#scores').replaceChildren();
  if (!scores) return;
  Object.entries(scores).sort((a, b) => b[1] - a[1]).forEach(([c, v]) => {
    const row = document.createElement('div'); row.className = 'score-row';
    const title = document.createElement('span'); title.textContent = names[c];
    const track = document.createElement('div'); track.className = 'score-track';
    const fill = document.createElement('div'); fill.className = 'score-fill'; fill.style.width = v * 100 + '%';
    track.append(fill);
    const val = document.createElement('span'); val.textContent = (v * 100).toFixed(1) + ' %';
    row.append(title, track, val); $('#scores').append(row);
  });
}

$('#file-input').onchange = e => { const file = e.target.files[0]; e.target.value = ''; loadFile(file); };
const drop = $('#drop-zone');
['dragenter', 'dragover'].forEach(e => drop.addEventListener(e, v => { v.preventDefault(); drop.classList.add('dragover'); }));
['dragleave', 'drop'].forEach(e => drop.addEventListener(e, v => { v.preventDefault(); drop.classList.remove('dragover'); }));
drop.addEventListener('drop', e => {
  if (e.dataTransfer.files.length !== 1) { fileProblem('Carga una sola fotografía cada vez.'); return; }
  loadFile(e.dataTransfer.files[0]);
});

$('#load-demo').onclick = async () => {
  try {
    const r = await fetch('/static/demo-documento.png');
    if (!r.ok) throw apiError('No se encontró el ejemplo de demostración.', 'server');
    await loadFile(new File([await r.blob()], 'ejemplo_sintetico.png', { type: 'image/png' }));
  } catch (e) {
    showError(e.kind ? e : apiError('No se pudo descargar el ejemplo.', 'network'), { key: 'upload', retry: () => $('#load-demo').click() });
  }
};

// ---------------------------------------------------------------- 2 · identificar
function setKind(k) {
  kind = k; params = { ...presets[k] };
  $$('[data-kind]').forEach(b => { b.classList.toggle('selected', b.dataset.kind === k); b.setAttribute('aria-pressed', b.dataset.kind === k); });
  $('#preset-description').textContent = k === 'pintura'
    ? 'Pintura: comenzaremos sin mejoras de color. Ajusta con cuidado para conservar tonos y textura.'
    : k === 'manuscrito'
      ? 'Manuscrito: ajustes suaves. Comprueba que se mantienen trazos débiles, acentos y anotaciones.'
      : 'Impreso: iluminación y contraste moderados. El blanco y negro es opcional.';
  $('#kind-badge').textContent = names[k];
  renderCapture();
  $('#binary').disabled = k === 'pintura';
  syncControls();
}
$$('[data-kind]').forEach(b => b.onclick = () => { setKind(b.dataset.kind); lastResult = null; maxStep = 2; show(2); });
$('#confirm-scope').onchange = () => { if ($('#confirm-scope').checked) Feedback.clearField($('#confirm-scope')); };

$('#confirm-kind').onclick = async function confirmKind() {
  const box = $('#confirm-scope');
  if (!box.checked) {
    Feedback.fieldMessage(box, 'Marca esta casilla para confirmar que la foto contiene una pieza admitida.');
    Feedback.notify({ type: 'warning', key: 'confirm-scope', title: 'Falta tu confirmación',
      text: 'Confirma que la foto contiene una sola pieza plana: manuscrito, impreso o pintura.',
      detail: 'Sin esa confirmación no se busca el borde.', actions: [{ label: 'Ir a la casilla', onClick: () => Feedback.focusField(box) }] });
    Feedback.focusField(box);
    return;
  }
  Feedback.dismiss('confirm-scope');
  busy(true, 'Localizando la pieza…');
  try {
    const d = await api('/api/detect', { kind, method: 'auto', scope_confirmed: true });
    points = d.points; upload.detection = d; detectionText();
    Feedback.clear((o, key) => ['scope', 'classification', 'detect', 'upload-ok'].includes(key) || key.startsWith('error:'));
    show(3);
    if (d.confidence?.level === 'dudosa') {
      Feedback.notify({ type: 'warning', key: 'detect-ok', title: 'Borde dudoso',
        text: 'La red no está segura del borde. Se muestra su máscara: lleva los puntos a las esquinas reales de la pieza.',
        actions: [{ label: 'Marcar manualmente', onClick: () => detect('manual') }] });
    } else {
      Feedback.notify({ type: 'success', key: 'detect-ok', title: 'Borde propuesto', text: `${methodNames[d.method]}. Revisa que los cuatro puntos coincidan con las esquinas.` });
    }
  } catch (e) { showError(e, { key: 'detect', effect: 'Sigues en el paso 2.', retry: confirmKind }); }
  finally { busy(false); }
};

// ---------------------------------------------------------------- 3 · encuadrar
function detectionText() {
  const d = upload.detection, conf = d.confidence;
  $('#detection-method').textContent = methodNames[d.method] + (conf ? (conf.level === 'segura' ? ' · borde seguro' : ' · borde dudoso') : '');
  // Con la U-Net, el bloque de confianza ya explica el borde; el aviso queda para contornos y modo manual.
  $('#corner-notice').textContent = conf ? '' : d.warnings.join(' ');
  const box = $('#border-confidence'); box.hidden = !conf; $('#toggle-mask').hidden = !conf;
  if (conf) {
    box.dataset.level = conf.level;
    $('#bc-title').textContent = conf.level === 'segura' ? 'Borde seguro' : 'Borde dudoso: revisa las esquinas';
    $('#bc-text').textContent = conf.level === 'segura'
      ? `Los cuatro puntos cubren el ${Math.round(conf.fit * 100)} % de la zona que la red marcó como pieza y su contorno es nítido. Confírmalo de todos modos.`
      : conf.reasons.join(' ');
    loadMask(conf.level === 'dudosa');
  } else { maskImage = null; setMask(false); }
}
function setMask(on) {
  showMask = on && !!maskImage;
  $('#toggle-mask').setAttribute('aria-pressed', String(showMask));
  $('#toggle-mask').textContent = showMask ? 'Ocultar la máscara de la red' : 'Ver lo que vio la red';
  $('#mask-legend').hidden = !showMask;
  drawCorners();
}
function loadMask(autoShow) {
  const img = new Image();
  img.onload = () => { maskImage = img; setMask(autoShow || showMask); };
  img.onerror = () => { maskImage = null; setMask(false); };
  img.src = imageUrl('mask', Date.now());
}
$('#toggle-mask').onclick = () => setMask(!showMask);
function loadOriginal() {
  return new Promise((resolve, reject) => {
    originalImage = new Image();
    originalImage.onload = () => { const c = $('#corner-canvas'); c.width = originalImage.width; c.height = originalImage.height; resolve(); };
    originalImage.onerror = () => reject(apiError('No se pudo cargar la vista previa.', 'server'));
    originalImage.src = upload.image_url;
  });
}
function drawCorners() {
  if (!originalImage || !points.length) return;
  const c = $('#corner-canvas'), ctx = c.getContext('2d'), w = c.width, h = c.height;
  ctx.clearRect(0, 0, w, h); ctx.drawImage(originalImage, 0, 0, w, h);
  if (showMask && maskImage) ctx.drawImage(maskImage, 0, 0, w, h);
  ctx.beginPath();
  points.forEach((p, i) => { const x = p[0] * (w - 1), y = p[1] * (h - 1); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
  ctx.closePath(); ctx.fillStyle = '#b9e1c214'; ctx.fill();
  ctx.strokeStyle = '#a9e1d4'; ctx.lineWidth = Math.max(2, w / 400); ctx.stroke();
  const scale = w / Math.max(1, c.getBoundingClientRect().width), r = 9 * scale;
  points.forEach((p, i) => {
    const x = p[0] * (w - 1), y = p[1] * (h - 1);
    ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fillStyle = i === activeCorner ? '#eac59a' : '#b9d7bf'; ctx.fill();
    ctx.strokeStyle = '#173430'; ctx.lineWidth = 2 * scale; ctx.stroke();
    ctx.fillStyle = '#10221e'; ctx.font = `bold ${10 * scale}px Arial`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(String(i + 1), x, y);
  });
  $$('[data-corner]').forEach(b => b.classList.toggle('selected', Number(b.dataset.corner) === activeCorner));
}
const canvas = $('#corner-canvas');
function canvasPoint(e) {
  const r = canvas.getBoundingClientRect();
  return [Math.max(0, Math.min(1, (e.clientX - r.left) / r.width)), Math.max(0, Math.min(1, (e.clientY - r.top) / r.height))];
}
canvas.onpointerdown = e => {
  const p = canvasPoint(e), r = canvas.getBoundingClientRect(); let best = Infinity;
  points.forEach((q, i) => { const dist = Math.hypot((p[0] - q[0]) * r.width, (p[1] - q[1]) * r.height); if (dist < best) { best = dist; activeCorner = i; } });
  if (best < 40) { dragging = true; canvas.setPointerCapture(e.pointerId); canvas.focus(); }
  drawCorners();
};
canvas.onpointermove = e => { if (dragging) { points[activeCorner] = canvasPoint(e); drawCorners(); invalidate(); } };
canvas.onpointerup = () => dragging = false;
canvas.onpointercancel = () => dragging = false;
$$('[data-corner]').forEach(b => b.onclick = () => { activeCorner = Number(b.dataset.corner); canvas.focus(); drawCorners(); });
canvas.onkeydown = e => {
  const delta = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }[e.key];
  if (delta) {
    e.preventDefault(); const d = e.shiftKey ? .02 : .002;
    points[activeCorner] = points[activeCorner].map((v, i) => Math.max(0, Math.min(1, v + delta[i] * d)));
    drawCorners(); invalidate();
  }
};
window.addEventListener('resize', () => { if (step === 3) drawCorners(); });

/** Un cambio en esquinas/proporción deja obsoleto el resultado: hay que procesar otra vez. */
function invalidate() { lastResult = null; maxStep = Math.min(maxStep, 3); $$('.steps button').forEach((b, i) => b.disabled = i + 1 > maxStep); }
$('#aspect').oninput = () => { invalidate(); if ($('#aspect').checkValidity()) Feedback.clearField($('#aspect')); };

async function detect(method) {
  busy(true, method === 'manual' ? 'Preparando el borde manual…' : 'Buscando de nuevo el borde…');
  try {
    const d = await api('/api/detect', { kind, method, scope_confirmed: $('#confirm-scope').checked });
    upload.detection = d; points = d.points; invalidate(); detectionText(); drawCorners();
    Feedback.dismiss('detect');
    Feedback.notify({ type: 'success', key: 'detect-ok', title: method === 'manual' ? 'Borde manual listo' : 'Borde detectado de nuevo',
      text: method === 'manual' ? 'Arrastra los cuatro puntos hasta las esquinas de la pieza.' : `${methodNames[d.method]}. Revisa las cuatro esquinas.` });
  } catch (e) { showError(e, { key: 'detect', effect: 'Se conserva el borde anterior.', retry: () => detect(method) }); }
  finally { busy(false); }
}
$('#redetect').onclick = () => detect('auto');
$('#manual-border').onclick = () => detect('manual');

async function rotate(direction) {
  busy(true, 'Girando la vista de trabajo…');
  try {
    const d = await api('/api/rotate', { direction, kind });
    points = d.detection.points; upload.detection = d.detection;
    upload.image_url = imageUrl('original', Date.now()); $('#class-image').src = upload.image_url;
    await loadOriginal(); invalidate(); detectionText(); drawCorners();
    Feedback.dismiss('rotate');
    Feedback.notify({ type: 'success', key: 'rotate-ok', title: 'Vista girada', text: 'El borde se volvió a proponer. El archivo original no cambia.' });
  } catch (e) { showError(e, { key: 'rotate', effect: 'La vista quedó como estaba.', retry: () => rotate(direction) }); }
  finally { busy(false); }
}
$('#rotate-left').onclick = () => rotate('left');
$('#rotate-right').onclick = () => rotate('right');

// ---------------------------------------------------------------- 4 · mejorar
function syncControls() {
  sliders.forEach(k => { $('#' + k).value = Math.round(params[k] * 100); $('#' + k + '-value').textContent = Math.round(params[k] * 100) + ' %'; });
  $('#binary').value = params.binary; $('#background').value = params.background;
}
function readControls() {
  return { ...Object.fromEntries(sliders.map(k => [k, Number($('#' + k).value) / 100])), binary: $('#binary').value, background: $('#background').value };
}
function readAspect() {
  const el = $('#aspect');
  if (el.value.trim() === '' || !el.checkValidity()) throw apiError('Escribe una proporción válida: 0 para estimar, o entre 0,1 y 10.', 'field');
  const n = Number(el.value);
  if (!Number.isFinite(n) || (n !== 0 && n < .1)) throw apiError('La proporción debe ser 0 o estar entre 0,1 y 10.', 'field');
  return n;
}
function setStale(on) {
  $('.compare-card').classList.toggle('stale', on);
  $('#stale-banner').hidden = !on;
}

/**
 * Procesa con los parámetros actuales. Si llegan cambios mientras procesa,
 * se encola uno solo y se procesa el estado más reciente.
 * @returns {Promise<boolean>} true si hay un resultado vigente.
 */
async function process({ quiet = false } = {}) {
  if (processing) { pending = true; return false; }
  let aspect;
  try { aspect = readAspect(); }
  catch (e) {
    const field = $('#aspect');
    Feedback.fieldMessage(field, e.message);
    Feedback.notify({ type: 'error', key: 'aspect', title: 'Proporción no válida', text: e.message,
      detail: 'No se procesó la imagen. Corrige el valor o escribe 0.', actions: [{ label: 'Corregir', onClick: () => Feedback.focusField(field) }] });
    if (step === 3) Feedback.focusField(field); else show(3);
    return false;
  }
  Feedback.dismiss('aspect'); Feedback.clearField($('#aspect'));
  processing = true; lastResult = null; maxStep = Math.min(maxStep, 4);
  $$('.steps button').forEach((b, i) => b.disabled = i + 1 > maxStep);
  busy(true, 'Preparando la vista frontal y aplicando tus ajustes…');
  try {
    do {
      pending = false;
      const result = await api('/api/process', { kind, points, aspect, parameters: params });
      if (pending) continue;
      await Promise.all([['#after-image', 'after'], ['#before-image', 'before'], ['#export-image', 'after']].map(async ([selector, which]) => {
        const im = $(selector); im.src = imageUrl(which, result.revision); await im.decode();
      }));
      if (pending) continue;
      lastResult = result;
      $('#processing-time').textContent = `${result.width} × ${result.height} px · ${(result.elapsed_ms / 1000).toFixed(2)} s`;
      renderMetrics(result.metrics);
    } while (pending);
    setStale(false);
    Feedback.dismiss('process');
    if (!quiet) Feedback.notify({ type: 'success', key: 'process-ok', title: step === 4 ? 'Ajuste aplicado' : 'Vista frontal lista',
      text: `${lastResult.width} × ${lastResult.height} px en ${seconds(lastResult.elapsed_ms)}.`, timeout: step === 4 ? 3500 : 5000 });
    return true;
  } catch (e) {
    lastResult = null;
    if (step === 4) setStale(true);
    showError(e.kind ? e : apiError('No se pudo cargar la vista previa. Vuelve a procesar.', 'server'), {
      key: 'process',
      effect: step === 4 ? 'La vista previa mostrada ya no corresponde a los controles actuales.' : 'Sigues en el paso 3; el borde se conserva.',
      retry: () => step === 4 ? process() : $('#confirm-corners').click(),
    });
    return false;
  } finally { processing = false; busy(false); }
}
$('#stale-retry').onclick = () => process();

$('#confirm-corners').onclick = async () => { if (await process()) { history = []; show(4); } };
function changeParameters() { history.push({ ...params }); params = readControls(); process(); }
sliders.forEach(k => {
  $('#' + k).oninput = () => $('#' + k + '-value').textContent = $('#' + k).value + ' %';
  $('#' + k).onchange = changeParameters;
});
$('#binary').onchange = changeParameters;
$('#background').onchange = changeParameters;
$('#undo-adjustment').onclick = async () => {
  if (!history.length) {
    Feedback.notify({ type: 'info', key: 'undo', title: 'Nada que deshacer', text: 'Todavía no has cambiado los ajustes en esta foto.' });
    return;
  }
  params = history.pop(); syncControls();
  if (await process({ quiet: true })) Feedback.notify({ type: 'success', key: 'process-ok', title: 'Se deshizo el último ajuste', text: 'Volviste a los valores anteriores.', timeout: 3500 });
};
$('#reset-adjustments').onclick = async () => {
  history.push({ ...params });
  params = { illumination: 0, contrast: 0, denoise: 0, sharpness: 0, binary: 'off', background: 'gaussian' };
  syncControls();
  if (await process({ quiet: true })) Feedback.notify({ type: 'success', key: 'process-ok', title: 'Mejoras en cero', text: 'El resultado es la vista frontal sin ajustes. Puedes deshacerlo.', timeout: 4000 });
};
function renderMetrics(m) {
  $('#metrics').replaceChildren();
  for (const [k, label, d] of [['laplacian_variance', 'Nitidez · var. Laplaciano', 1], ['rms_contrast', 'Contraste RMS', 3]]) {
    const box = document.createElement('div'); box.className = 'metric';
    const small = document.createElement('small'); small.textContent = label;
    const strong = document.createElement('strong'); strong.textContent = m.after[k].toFixed(d);
    const span = document.createElement('span'); span.textContent = 'Antes ' + m.before[k].toFixed(d);
    box.append(small, strong, span); $('#metrics').append(box);
  }
}
function compare() { const v = $('#compare-slider').value; $('#before-layer').style.clipPath = `inset(0 ${100 - v}% 0 0)`; $('#compare-divider').style.left = v + '%'; }
$('#compare-slider').oninput = compare;

function detail(which) {
  if (!lastResult) return;
  $('#detail-image').src = imageUrl(which, lastResult.revision) + '&detail=1';
  $$('[data-detail]').forEach(b => b.classList.toggle('selected', b.dataset.detail === which));
}
$('#open-detail').onclick = () => {
  if (!lastResult) {
    Feedback.notify({ type: 'warning', key: 'process', title: 'No hay un resultado vigente', text: 'Vuelve a procesar la imagen para ampliar el detalle.', actions: [{ label: 'Procesar', onClick: () => process() }] });
    return;
  }
  detail('after'); $('#detail-dialog').showModal();
};
$('#close-detail').onclick = () => $('#detail-dialog').close();
$$('[data-detail]').forEach(b => b.onclick = () => detail(b.dataset.detail));

$('#confirm-result').onclick = () => {
  if (!lastResult) {
    Feedback.notify({ type: 'warning', key: 'process', title: 'El resultado no está actualizado',
      text: 'Vuelve a procesar la imagen antes de exportar.', detail: 'Así el archivo coincide con los controles que ves.',
      actions: [{ label: 'Procesar ahora', onClick: () => process() }] });
    return;
  }
  $$('.export-links a,.download-link').forEach(a => { a.href = a.href.split('?')[0] + '?image_key=' + encodeURIComponent(upload.image_key) + '&revision=' + lastResult.revision; });
  $('#export-summary').replaceChildren();
  const list = [['Pieza', upload.name], ['Tipo confirmado', names[kind]], ['Resolución', `${lastResult.width} × ${lastResult.height} px`],
    ['Borde inicial', methodNames[upload.detection.method] || upload.detection.method],
    ['Mejoras', `Iluminación ${Math.round(params.illumination * 100)} % · contraste ${Math.round(params.contrast * 100)} % · nitidez ${Math.round(params.sharpness * 100)} %`],
    ['Referencia', 'SSIM / PSNR no calculados']];
  list.forEach(([a, b]) => { const dt = document.createElement('dt'), dd = document.createElement('dd'); dt.textContent = a; dd.textContent = b; $('#export-summary').append(dt, dd); });
  Feedback.clear((o, key) => key.startsWith('process') || key === 'capture');
  show(5);
  Feedback.notify({ type: 'success', key: 'accepted', title: 'Resultado aceptado', text: 'Elige cómo guardarlo. El original se incluye intacto en el ZIP.' });
};

// ---------------------------------------------------------------- 5 · guardar
const formatNames = { zip: 'ZIP completo', png: 'PNG', pdf: 'PDF', json: 'registro JSON' };
$$('.export-links a,.download-link').forEach(a => a.addEventListener('click', () => {
  const fmt = (a.getAttribute('href').match(/export\/(\w+)/) || [])[1];
  // El navegador gestiona la descarga: solo podemos confirmar que se pidió.
  Feedback.notify({ type: 'info', key: 'download', title: `Descarga solicitada · ${formatNames[fmt] || fmt}`,
    text: 'El navegador la guardará en tu carpeta de descargas. Si no aparece, revisa los permisos de descarga.', timeout: 6000 });
}));

async function resetImage(force = false) {
  const hasWork = upload && (maxStep >= 3 || lastResult);
  if (!force && hasWork) {
    const ok = await Feedback.confirmAction({
      title: '¿Descartar esta foto y sus ajustes?',
      text: 'Se borra de la sesión el encuadre y las mejoras de esta foto. Si quieres conservar el resultado, descárgalo antes.',
      confirmLabel: 'Descartar y empezar', cancelLabel: 'Seguir trabajando', danger: true,
    });
    if (!ok) return;
  }
  if (upload) {
    try { await api('/api/reset', {}); }
    catch (e) { if (e.kind !== 'session') { showError(e, { key: 'reset', effect: 'La foto sigue cargada.', retry: () => resetImage(true) }); return; } }
  }
  upload = null; lastResult = null; points = []; maxStep = 1; history = [];
  $('#file-input').value = ''; $('#aspect').value = '0'; $('#confirm-scope').checked = false;
  ['#aspect', '#confirm-scope', '#file-input'].forEach(s => Feedback.clearField($(s)));
  setStale(false);
  Feedback.clear();
  show(1);
  Feedback.notify({ type: 'info', key: 'reset-ok', title: 'Listo para otra fotografía', text: 'Carga un JPG o PNG para comenzar.', timeout: 4000 });
}
$('#new-image').onclick = () => resetImage();
$('#replace-image').onclick = () => resetImage();
$('#reject-result').onclick = () => resetImage();

// ---------------------------------------------------------------- estado del servidor
async function checkStatus() {
  try {
    const s = await api('/api/status');
    presets = s.presets;
    $('#model-status').textContent = s.classifier && s.segmenter ? (s.local ? 'IA lista · en tu equipo' : 'IA lista · demo en línea') : 'Modo manual · revisa modelos';
    document.querySelector('.status-dot').classList.toggle('degraded', !(s.classifier && s.segmenter));
    Feedback.dismiss('status');
    if (!s.classifier) {
      Feedback.notify({ type: 'warning', key: 'status-model', title: 'Trabajarás en modo manual',
        text: 'El clasificador no está disponible. Podrás elegir la categoría a mano.', detail: 'Revisa que los pesos estén en la carpeta models/.' });
    }
  } catch (e) {
    $('#model-status').textContent = 'Sin conexión con el servidor';
    document.querySelector('.status-dot').classList.add('offline');
    showError(e, { key: 'status', effect: 'No podrás cargar fotos hasta reconectar.', retry: checkStatus });
  }
}
checkStatus();
