'use strict';
/*
  Sistema de avisos de Palimpsesto.

  - Avisos flotantes (toasts) fijos dentro de la ventana: se ven aunque la página
    esté desplazada. Cuatro tipos: éxito, información, advertencia y error.
  - Cada aviso tiene icono + título + texto (no depende solo del color) y puede
    traer acciones (Reintentar, Ir al campo...).
  - Los errores y advertencias permanecen hasta resolverse o cerrarse; los éxitos
    y la información se cierran solos (el tiempo se pausa con el mouse o el foco).
  - Un aviso con la misma clave reemplaza al anterior: no hay duplicados.
  - Mensajes junto al campo afectado (fieldMessage) para corregir en el sitio.
  - Lectores de pantalla: regiones vivas separadas (polite / assertive).
  - Diálogo de confirmación solo para decisiones que descartan trabajo.
*/
const Feedback = (() => {
  const ICONS = {
    success: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9.2"/><path d="M7.6 12.4l3 3 5.8-6.2"/></svg>',
    info: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9.2"/><path d="M12 11v5.6M12 7.4v.2"/></svg>',
    warning: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3.4l9.4 16.4H2.6z"/><path d="M12 9.6v4.8M12 17.2v.2"/></svg>',
    error: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8.2 2.8h7.6l5.4 5.4v7.6l-5.4 5.4H8.2l-5.4-5.4V8.2z"/><path d="M9 9l6 6M15 9l-6 6"/></svg>',
  };
  const LABELS = { success: 'Listo', info: 'Información', warning: 'Advertencia', error: 'Error' };
  // Tiempo visible por defecto (ms). 0 = permanece hasta que se resuelva o se cierre.
  const DEFAULT_TIMEOUT = { success: 5000, info: 7000, warning: 0, error: 0 };
  const maxVisible = () => (window.matchMedia('(max-width: 600px)').matches ? 2 : 4);
  const reducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  let stack, livePolite, liveAssertive;
  const active = new Map(); // clave → {el, timer, remaining, started, options}

  function init() {
    stack = document.getElementById('toasts');
    livePolite = document.getElementById('live-polite');
    liveAssertive = document.getElementById('live-assertive');
    // Mientras la cabecera está a la vista, los avisos se ubican debajo para no tapar sus botones.
    const header = document.querySelector('.topbar');
    const place = () => { const bottom = header ? Math.max(0, header.getBoundingClientRect().bottom) : 0; stack.style.setProperty('--toast-top', bottom + 'px'); };
    window.addEventListener('scroll', place, { passive: true }); window.addEventListener('resize', place); place();
  }
  document.addEventListener('DOMContentLoaded', () => { if (!stack) init(); });

  function announce(type, title, text) {
    // Vaciar y volver a escribir hace que el lector repita mensajes iguales.
    const region = type === 'error' ? liveAssertive : livePolite;
    region.textContent = '';
    setTimeout(() => { region.textContent = `${LABELS[type]}: ${title}. ${text || ''}`; }, 60);
  }

  function startTimer(entry) {
    clearTimeout(entry.timer);
    if (!entry.remaining) return;
    entry.started = Date.now();
    entry.el.style.setProperty('--toast-time', entry.remaining + 'ms');
    entry.el.classList.remove('timing'); void entry.el.offsetWidth; entry.el.classList.add('timing');
    entry.timer = setTimeout(() => dismiss(entry.key), entry.remaining);
  }
  function pauseTimer(entry) {
    if (!entry.remaining || !entry.started) return;
    clearTimeout(entry.timer);
    entry.remaining = Math.max(1500, entry.remaining - (Date.now() - entry.started));
    entry.started = 0;
    entry.el.classList.add('paused');
  }
  function resumeTimer(entry) {
    if (!entry.remaining || entry.started) return;
    entry.el.classList.remove('paused');
    startTimer(entry);
  }

  function build(entry) {
    const { type, title, text, detail, actions = [] } = entry.options;
    const el = entry.el;
    el.className = `toast toast-${type}`;
    el.dataset.type = type;
    el.dataset.key = entry.key;
    el.replaceChildren();
    const icon = document.createElement('span'); icon.className = 'toast-icon'; icon.innerHTML = ICONS[type];
    const body = document.createElement('div'); body.className = 'toast-body';
    const kicker = document.createElement('span'); kicker.className = 'toast-kicker'; kicker.textContent = LABELS[type];
    const h = document.createElement('strong'); h.className = 'toast-title'; h.textContent = title;
    body.append(kicker, h);
    if (text) { const p = document.createElement('p'); p.className = 'toast-text'; p.textContent = text; body.append(p); }
    if (detail) { const p = document.createElement('p'); p.className = 'toast-detail'; p.textContent = detail; body.append(p); }
    if (actions.length) {
      const row = document.createElement('div'); row.className = 'toast-actions';
      actions.forEach((a, i) => {
        const b = document.createElement('button'); b.type = 'button';
        b.className = i === 0 ? 'toast-action primary-action' : 'toast-action';
        b.textContent = a.label;
        b.onclick = () => { if (a.keepOpen !== true) dismiss(entry.key); a.onClick?.(); };
        row.append(b);
      });
      body.append(row);
    }
    const close = document.createElement('button');
    close.type = 'button'; close.className = 'toast-close';
    close.setAttribute('aria-label', `Cerrar aviso: ${title}`);
    close.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>';
    close.onclick = () => dismiss(entry.key);
    const bar = document.createElement('span'); bar.className = 'toast-timer'; bar.setAttribute('aria-hidden', 'true');
    el.append(icon, body, close, bar);
  }

  /**
   * Muestra o actualiza un aviso.
   * @param {object} o type, title, text, detail, key, actions[{label,onClick}], timeout (ms, 0 = permanente)
   */
  function notify(o) {
    if (!stack) init();
    const options = { type: 'info', ...o };
    const key = options.key || `${options.type}:${options.title}`;
    let entry = active.get(key);
    const fresh = !entry;
    if (fresh) {
      const el = document.createElement('section');
      el.setAttribute('aria-label', options.title);
      el.tabIndex = -1;
      entry = { key, el };
      el.addEventListener('mouseenter', () => pauseTimer(entry));
      el.addEventListener('mouseleave', () => { if (!el.contains(document.activeElement)) resumeTimer(entry); });
      el.addEventListener('focusin', () => pauseTimer(entry));
      el.addEventListener('focusout', e => { if (!el.contains(e.relatedTarget)) resumeTimer(entry); });
      el.addEventListener('keydown', e => { if (e.key === 'Escape') { e.stopPropagation(); dismiss(key); } });
      active.set(key, entry);
    }
    clearTimeout(entry.timer);
    // Una advertencia o un error nuevo vuelve obsoletas las confirmaciones anteriores.
    if (options.type === 'error' || options.type === 'warning') clear((o, k) => k !== key && (o.type === 'success' || o.type === 'info'));
    entry.options = options;
    entry.remaining = options.timeout ?? DEFAULT_TIMEOUT[options.type];
    entry.started = 0;
    build(entry);
    if (fresh) {
      // Los más nuevos van arriba; los errores siempre por encima de confirmaciones.
      const firstNonError = [...stack.children].find(c => c.dataset.type !== 'error' && !c.classList.contains('leaving'));
      if (options.type === 'error' || !firstNonError) stack.prepend(entry.el);
      else stack.insertBefore(entry.el, firstNonError);
      entry.el.classList.add('entering');
      entry.el.addEventListener('animationend', () => entry.el.classList.remove('entering'), { once: true });
      trim();
    } else {
      // Mismo aviso repetido: se actualiza y se resalta, sin duplicarlo.
      entry.el.classList.remove('bump'); void entry.el.offsetWidth; entry.el.classList.add('bump');
    }
    startTimer(entry);
    announce(options.type, options.title, options.text);
    return key;
  }

  function trim() {
    const visible = [...active.values()];
    if (visible.length <= maxVisible()) return;
    // Primero salen los avisos temporales más antiguos; los errores se conservan.
    const removable = visible.filter(e => e.options.type !== 'error');
    const victim = (removable.length ? removable : visible)[0];
    dismiss(victim.key);
  }

  function dismiss(key) {
    const entry = active.get(key);
    if (!entry) return;
    active.delete(key);
    clearTimeout(entry.timer);
    const el = entry.el;
    const hadFocus = el.contains(document.activeElement);
    const remove = () => { el.remove(); };
    if (reducedMotion()) remove();
    else { el.classList.add('leaving'); el.addEventListener('animationend', remove, { once: true }); setTimeout(remove, 400); }
    if (hadFocus) document.querySelector('main')?.focus?.({ preventScroll: true });
  }

  /** Cierra todos los avisos que cumplan el filtro (por defecto, todos). */
  function clear(filter = () => true) {
    [...active.values()].filter(e => filter(e.options, e.key)).forEach(e => dismiss(e.key));
  }
  const has = key => active.has(key);

  // ---- Mensajes junto al campo ----
  function fieldMessage(field, text, type = 'error') {
    const holder = field.closest('.control, .scope-check, .upload-zone, label') || field.parentElement;
    const id = (field.id || 'campo') + '-feedback';
    let msg = document.getElementById(id);
    if (!msg) {
      msg = document.createElement('p'); msg.id = id; msg.className = 'field-msg';
      if (holder.matches('.scope-check')) holder.after(msg); else holder.append(msg);
    }
    msg.dataset.type = type;
    msg.innerHTML = `<span class="field-msg-icon">${ICONS[type]}</span>`;
    const span = document.createElement('span'); span.textContent = text; msg.append(span);
    msg.hidden = false;
    field.setAttribute('aria-invalid', type === 'error' ? 'true' : 'false');
    const described = new Set((field.getAttribute('aria-describedby') || '').split(' ').filter(Boolean));
    described.add(id); field.setAttribute('aria-describedby', [...described].join(' '));
    holder.classList.add('has-' + type);
    return msg;
  }
  function clearField(field) {
    const id = (field.id || 'campo') + '-feedback';
    const msg = document.getElementById(id);
    if (msg) msg.hidden = true;
    field.removeAttribute('aria-invalid');
    const holder = field.closest('.control, .scope-check, .upload-zone, label') || field.parentElement;
    holder?.classList.remove('has-error', 'has-warning', 'has-info', 'has-success');
  }
  function focusField(field) {
    field.scrollIntoView({ block: 'center', behavior: reducedMotion() ? 'auto' : 'smooth' });
    field.focus({ preventScroll: true });
  }

  // ---- Diálogo de confirmación (solo para descartar trabajo) ----
  function confirmAction({ title, text, confirmLabel = 'Continuar', cancelLabel = 'Cancelar', danger = false }) {
    const dialog = document.getElementById('confirm-dialog');
    dialog.querySelector('#confirm-title').textContent = title;
    dialog.querySelector('#confirm-text').textContent = text;
    const ok = dialog.querySelector('#confirm-ok'), cancel = dialog.querySelector('#confirm-cancel');
    ok.textContent = confirmLabel; cancel.textContent = cancelLabel;
    ok.classList.toggle('danger', danger);
    return new Promise(resolve => {
      const finish = value => { dialog.close(); resolve(value); };
      ok.onclick = () => finish(true);
      cancel.onclick = () => finish(false);
      dialog.oncancel = e => { e.preventDefault(); finish(false); };
      dialog.showModal();
      cancel.focus(); // La opción segura queda enfocada.
    });
  }

  return { notify, dismiss, clear, has, fieldMessage, clearField, focusField, confirmAction };
})();
