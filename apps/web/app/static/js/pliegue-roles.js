/* Pliegue: asistente de consultas por rol, sin historial para no administradores.
   La seguridad reside en Flask, no en estas decisiones visuales. */
(() => {
  'use strict';
  const boot = document.querySelector('#pliegue-boot');
  if (!boot) return;
  let state;
  try { state = JSON.parse(boot.textContent); } catch { return; }
  if (state.is_admin) return; // El administrador conserva su Pliegue/Codex.
  if (document.querySelector('#pliegue-roles-panel')) return;

  const icons = {
    eye: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/></svg>',
    paint: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M12 3a9 9 0 1 0 0 18h2a2 2 0 0 0 1.7-3.1c-.5-.8 0-1.9 1-1.9h1.5A4.8 4.8 0 0 0 23 11.2 9 9 0 0 0 12 3Z"/><circle cx="7" cy="11" r="1"/><circle cx="11" cy="7" r="1"/><circle cx="17" cy="9" r="1"/></svg>',
    send: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>',
    close: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M18 6 6 18M6 6l12 12"/></svg>',
    undo: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M3 10h11a7 7 0 1 1 0 14" transform="translate(0 -3)"/><path d="m7 3-4 4 4 4"/></svg>'
  };
  const panel = document.createElement('aside');
  panel.id = 'pliegue-roles-panel';
  panel.className = 'pliegue-role-dock';
  panel.hidden = true;
  panel.setAttribute('aria-label', 'Asistente Pliegue');
  panel.innerHTML = `
    <header class="pr-head">
      <img src="/static/img/pliegue.png" width="27" height="27" alt="">
      <div><h2>Pliegue</h2><small data-role-name>Asistente de Orvia</small></div>
      <button class="pr-icon" data-close aria-label="Cerrar panel" title="Cerrar">${icons.close}</button>
    </header>
    <nav class="pr-modes" aria-label="Modo de Pliegue">
      <button type="button" data-mode="consult" aria-pressed="true">${icons.eye}<span>Consultar</span></button>
      <button type="button" data-mode="theme" aria-pressed="false">${icons.paint}<span>Diseño</span></button>
    </nav>
    <section class="pr-consult" data-section="consult">
      <p class="pr-hint" data-help></p>
      <div class="pr-messages" role="log" aria-label="Conversación temporal" aria-live="polite"></div>
      <form data-chat-form><label class="pr-sr" for="pr-question">Consulta para Pliegue</label>
        <textarea id="pr-question" maxlength="600" rows="2" required placeholder="Pregunta por tus datos autorizados..."></textarea>
        <button aria-label="Enviar consulta" title="Enviar consulta" class="pr-send">${icons.send}</button>
      </form>
      <small class="pr-privacy">Sin historial · Consultas de solo lectura</small>
    </section>
    <section class="pr-theme" data-section="theme" hidden>
      <p class="pr-hint">Personaliza únicamente tu vista. No afecta otros usuarios ni funcionalidades.</p>
      <div class="pr-fields">
        <label>Color <select data-palette><option value="esmeralda">Esmeralda</option><option value="azul">Azul</option><option value="morado">Morado</option><option value="grafito">Grafito</option><option value="turquesa">Turquesa</option></select></label>
        <label>Tipografía <select data-font><option value="inter">Inter</option><option value="sistema">Sistema</option><option value="serif">Serif</option></select></label>
        <label>Bordes <select data-radius><option value="suave">Suaves</option><option value="recto">Rectos</option></select></label>
      </div>
      <div class="pr-compare" aria-label="Comparación de apariencia">
        <div data-before><small>ANTES</small><div class="pr-example"><span>Vista actual</span><span class="pr-chip">Ejemplo</span></div></div>
        <div data-after><small>DESPUÉS</small><div class="pr-example"><span>Tu propuesta</span><span class="pr-chip">Ejemplo</span></div></div>
      </div>
      <div class="pr-theme-actions"><button data-theme-save class="pr-primary">Aceptar</button><button data-theme-undo>${icons.undo} Deshacer</button></div>
      <p class="pr-status" data-theme-status role="status"></p>
    </section>`;
  document.body.append(panel);

  // Reutilizar el icono global de Pliegue, sin generar un segundo botón.
  const existing = document.querySelector('.pliegue-launch');
  const trigger = existing || document.createElement('button');
  if (!existing) {
    trigger.type = 'button';
    trigger.className = 'pliegue-launch pliegue-launch-roles';
    trigger.innerHTML = '<img src="/static/img/pliegue.png" alt="" width="26" height="26">';
    trigger.setAttribute('aria-label', 'Abrir Pliegue');
    trigger.setAttribute('title', 'Abrir Pliegue');
    const bell = [...document.querySelectorAll('.campanita, #ov-real-bell')].find(x => x.getClientRects().length);
    if (bell) bell.before(trigger);
    else document.querySelector('.orvia-topbar, .ov-topbar, header.barra, header')?.append(trigger);
  }
  trigger.setAttribute('aria-controls', panel.id);
  trigger.setAttribute('aria-expanded', 'false');
  const close = () => { panel.hidden = true; trigger.setAttribute('aria-expanded', 'false'); };
  trigger.addEventListener('click', () => {
    panel.hidden = !panel.hidden;
    trigger.setAttribute('aria-expanded', String(!panel.hidden));
    if (!panel.hidden) panel.querySelector('textarea')?.focus({preventScroll:true});
  });
  panel.querySelector('[data-close]').onclick = close;
  panel.addEventListener('keydown', e => { if (e.key === 'Escape') close(); });

  let csrf = '';
  const api = async (path, opts = {}) => {
    const r = await fetch('/pliegue-asistente/' + path, {
      credentials: 'same-origin', cache: 'no-store', ...opts,
      headers: {...(opts.body ? {'Content-Type':'application/json'} : {}),
        ...(opts.method && opts.method !== 'GET' ? {'X-Pliegue-Roles-CSRF':csrf} : {}), ...opts.headers}
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(data.error || 'Solicitud rechazada (HTTP ' + r.status + ')');
    return data;
  };
  let initialTheme;
  const palette = {esmeralda:'#087f5b', azul:'#2563eb', morado:'#7545b8', grafito:'#334155', turquesa:'#087f8c'};
  const soft = {esmeralda:'#e5f5ed', azul:'#eaf1ff', morado:'#f1eaff', grafito:'#eff2f5', turquesa:'#e4f7f8'};
  const fonts = {inter:'Inter,"Segoe UI",sans-serif', sistema:'system-ui,sans-serif', serif:'Georgia,serif'};
  const getDraft = () => ({palette:panel.querySelector('[data-palette]').value,
      font: panel.querySelector('[data-font]').value, radius:panel.querySelector('[data-radius]').value});
  const paintExample = (parent, theme) => {
    const root = panel.querySelector(parent + ' .pr-example');
    root.style.borderColor = palette[theme.palette] || palette.esmeralda;
    root.style.fontFamily = fonts[theme.font] || fonts.inter;
    root.style.borderRadius = theme.radius === 'recto'?'5px':'14px';
    root.querySelector('.pr-chip').style.background = soft[theme.palette] || soft.esmeralda;
    root.querySelector('.pr-chip').style.color = palette[theme.palette] || palette.esmeralda;
  };
  const showTheme = (theme) => {
    document.documentElement.style.setProperty('--pliegue-personal-accent',palette[theme.palette] || palette.esmeralda);
    document.documentElement.style.setProperty('--pliegue-personal-tint',soft[theme.palette] || soft.esmeralda);
    document.documentElement.style.setProperty('--pliegue-personal-font',fonts[theme.font] || fonts.inter);
    document.documentElement.style.setProperty('--pliegue-personal-radius',theme.radius === 'recto'?'5px':'14px');
    paintExample('[data-before]', initialTheme || theme);
    paintExample('[data-after]', theme);
  };
  const populate = (theme) => {
    panel.querySelector('[data-palette]').value = theme.palette;
    panel.querySelector('[data-font]').value = theme.font;
    panel.querySelector('[data-radius]').value = theme.radius;
    showTheme(theme);
  };
  api('config').then(data => {
    csrf = data.csrf;
    initialTheme = data.theme;
    populate(data.theme);
    panel.querySelector('[data-role-name]').textContent = data.role;
    panel.querySelector('[data-help]').textContent = 'Puedes preguntar por: ' + data.topics.join(' · ');
  }).catch(() => {
    panel.querySelector('[data-help]').textContent = 'No se pudo verificar tu sesión. Recarga la página.';
    panel.querySelector('button.pr-send').disabled = true;
  });

  panel.querySelectorAll('[data-mode]').forEach(button => button.onclick = () => {
    const active = button.dataset.mode;
    panel.querySelectorAll('[data-mode]').forEach(b => b.setAttribute('aria-pressed', String(b === button)));
    panel.querySelectorAll('[data-section]').forEach(s => s.hidden = s.dataset.section !== active);
    if (active === 'theme') panel.querySelector('[data-palette]').focus();
    else panel.querySelector('textarea').focus();
  });
  const messages = panel.querySelector('.pr-messages');
  function bubble(value, isUser = false) {
    const message = document.createElement('p');
    message.className = 'pr-bubble' + (isUser ? ' pr-you' : '');
    message.textContent = value;
    messages.append(message);
    messages.scrollTop = messages.scrollHeight;
    return message;
  }
  panel.querySelector('[data-chat-form]').addEventListener('submit', async event => {
    event.preventDefault();
    const field = panel.querySelector('textarea');
    const question = field.value.trim();
    if (!csrf || !question) return;
    field.value = '';
    bubble(question, true);
    const waiting = bubble('Consultando datos autorizados…');
    const button = panel.querySelector('.pr-send');
    button.disabled = true;
    try {
      const result = await api('consulta', {method:'POST',body:JSON.stringify({message:question})});
      waiting.textContent = result.reply + '\n\nFuente: ' + result.source + ' · ' + new Date(result.as_of).toLocaleString('es-MX');
    } catch(error) { waiting.textContent = error.message; }
    finally {button.disabled = false; field.focus();}
  });
  panel.querySelectorAll('.pr-fields select').forEach(item => item.addEventListener('change', () => {
    const draft = getDraft();
    // Modificar solo la muestra DESPUÉS hasta que el usuario confirme.
    paintExample('[data-after]',draft);
    panel.querySelector('[data-theme-status]').textContent = 'Vista previa lista. Nada se ha guardado.';
  }));
  panel.querySelector('[data-theme-save]').onclick = async () => {
    if (!csrf) return;
    const status = panel.querySelector('[data-theme-status]');
    try {
      const result = await api('tema', {method:'PUT',body:JSON.stringify(getDraft())});
      initialTheme = result.theme; showTheme(result.theme);
      status.textContent = 'Diseño personal aplicado. Los demás usuarios no se ven afectados.';
    } catch(error) {status.textContent = error.message;}
  };
  panel.querySelector('[data-theme-undo]').onclick = async () => {
    if (!csrf) return;
    try {
      const result = await api('tema',{method:'DELETE'});
      initialTheme = result.theme; populate(result.theme);
      panel.querySelector('[data-theme-status]').textContent = 'Apariencia personal restaurada.';
    } catch(error) {panel.querySelector('[data-theme-status]').textContent = error.message;}
  };
})();
