/* Pliegue Admin: selección real simple/múltiple para ajustes visuales reversibles.
   Los cambios de código avanzados siguen en Codex, bajo revisión independiente. */
(() => {
  'use strict';
  const boot = document.querySelector('#pliegue-boot');
  let cfg;
  try { cfg = JSON.parse(boot?.textContent || '{}'); } catch {return;}
  if (!cfg.is_admin) return;
  const code = document.querySelector('#pliegue-codigo[data-visual-global]');
  if (!code) return;
  const form = code.querySelector('form.pliegue-code-compose');
  if (!form) return;
  const field = form.querySelector('textarea');
  if (!field) return;
  const icons = {
    cursor:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M5 3v17l5-5 4 6 3-2-4-6 7-2Z"/></svg>',
    single:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><rect x="4" y="4" width="16" height="16" rx="3"/><path d="m9 12 2 2 4-4"/></svg>',
    multi:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><rect x="3" y="3" width="12" height="12" rx="2"/><rect x="9" y="9" width="12" height="12" rx="2"/></svg>',
    eye:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M2 12s4-6 10-6 10 6 10 6-4 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/></svg>',
    undo:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M3 10h11a6 6 0 0 1 0 12"/><path d="M7 6 3 10l4 4"/></svg>',
    close:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M18 6 6 18M6 6l12 12"/></svg>'
  };
  const holder = code.querySelector('[data-visual-editor]') || code.querySelector('.pliegue-code-navigation');
  if (!holder) return;
  const unavailable = holder.querySelector('.pliegue-visual-unavailable');
  if (unavailable) unavailable.hidden = true;
  const previousTools = holder.querySelector('[data-visual-tools]');
  // El selector previo exige un manifiesto de Fase 7; este funciona en páginas Flask normales.
  if (previousTools && previousTools.querySelector('[data-visual-toggle]:disabled')) previousTools.hidden = true;
  const tools = document.createElement('div');
  tools.id = 'pliegue-live-selector';
  tools.innerHTML = `
    <div class="pls-top">
      <span class="pls-label">Seleccionar en pantalla</span>
      <div class="pls-pills" role="group" aria-label="Tipo de selección">
        <button type="button" data-single aria-pressed="true" title="Selección simple">${icons.single}<span>Uno</span></button>
        <button type="button" data-multi aria-pressed="false" title="Selección múltiple">${icons.multi}<span>Varios</span></button>
      </div>
      <button type="button" class="pls-pick" data-start>${icons.cursor}<span>Seleccionar</span></button>
    </div>
    <p data-select-status class="pls-status">Elige un elemento para indicar qué quieres cambiar.</p>
    <div data-picked class="pls-picked" hidden><div data-chips class="pls-chips"></div>
      <div class="pls-actions"><button type="button" data-visual-preview>${icons.eye} Antes / Después</button>
      <button type="button" data-visual-undo>${icons.undo} Deshacer</button><button type="button" data-clear>Limpiar</button></div>
    </div>
    <dialog class="pls-review" aria-label="Antes y después de la edición">
      <div class="pls-review-head"><strong>Revisar cambio visual</strong><button type="button" data-dismiss aria-label="Cerrar">${icons.close}</button></div>
      <div class="pls-screens"><section><h3>ANTES</h3><iframe sandbox="allow-scripts" title="Antes de aplicar" referrerpolicy="no-referrer"></iframe></section>
      <section><h3>DESPUÉS</h3><iframe sandbox="allow-scripts" title="Después de aplicar" referrerpolicy="no-referrer"></iframe></section></div>
      <p class="pls-review-status" role="status"></p>
      <div class="pls-review-actions"><button type="button" data-accept disabled>Aceptar cambio</button><button type="button" data-reject>Rechazar</button></div>
    </dialog>`;
  holder.prepend(tools);
  const $ = selector => tools.querySelector(selector);
  let multiple = false;
  let active = false;
  let targets = [];
  let lastHover = null;
  let draftId = '';
  let csrf = '';
  let reviewReady = false;
  const rootPath = '/pliegue';
  async function request(path, method='GET', payload) {
    const res = await fetch(rootPath+path, {method, credentials:'same-origin',cache:'no-store',
      headers:{...(method!=='GET'?{'X-Pliegue-CSRF':csrf,'Content-Type':'application/json'}:{})},
      ...(payload===undefined?{}:{body:JSON.stringify(payload)})});
    const data = await res.json().catch(()=>({}));
    if (!res.ok) throw Error(data.error || `HTTP ${res.status}`);
    return data;
  }
  function cssSelector(node) {
    const chain = [];
    let n = node;
    while(n && n.localName !== 'main' && chain.length < 14) {
      if (!n.parentElement) return null;
      const siblings = [...n.parentElement.children].filter(x=>x.localName===n.localName);
      chain.unshift(`${n.localName}:nth-of-type(${siblings.indexOf(n)+1})`);
      n=n.parentElement;
    }
    return n?.localName === 'main' && chain.length ? 'main > ' + chain.join(' > ') : null;
  }
  function candidate(raw) {
    if (!(raw instanceof Element) || raw.closest('.pliegue-dock, .pliegue-role-dock, #pliegue-live-selector, header.barra, nav.menu')) return null;
    const tags = 'h1,h2,h3,h4,p,a,button,label,span,li,td,th,img,section,article,figure,div';
    const node = raw.closest(tags);
    if (!node || !node.closest('main') || node.closest('form') && node.matches('input,textarea,select')) return null;
    const selector = cssSelector(node);
    if (!selector) return null;
    const rawLabel = (node.getAttribute('aria-label') || node.getAttribute('alt') || node.textContent || node.localName).trim();
    return {selector, label:rawLabel.replace(/\s+/g,' ').slice(0,100) || node.localName, tag:node.localName, node};
  }
  function status(text){$('[data-select-status]').textContent=text;}
  function render(){
    $('[data-picked]').hidden = targets.length===0;
    $('[data-chips]').replaceChildren(...targets.map((target,index)=>{
      const tag=document.createElement('button');tag.type='button';tag.className='pls-chip';
      tag.textContent = `${target.tag} · ${target.label.slice(0,40)} ×`;
      tag.title='Quitar elemento seleccionado';
      tag.onclick=()=>{targets.splice(index,1);render();};
      return tag;
    }));
    if(targets.length)status(`${targets.length} elemento${targets.length===1?'':'s'} seleccionado${targets.length===1?'':'s'}. Describe el cambio.`);
    else status('Elige un elemento para indicar qué quieres cambiar.');
  }
  const highlight=document.createElement('div');
  highlight.className='pls-highlight';highlight.hidden=true;
  document.body.append(highlight);
  function moveMark(node){
    if(!node){highlight.hidden=true;return;}
    const r=node.getBoundingClientRect();
    highlight.hidden=false;
    Object.assign(highlight.style,{left:r.left+'px',top:r.top+'px',width:r.width+'px',height:r.height+'px'});
  }
  function stop(){active=false;document.body.classList.remove('pliegue-live-picking');highlight.hidden=true;lastHover=null;
    $('[data-start]').setAttribute('aria-pressed','false');}
  function onPointer(event){
    if(!active) return;
    const entry=candidate(event.target);
    if(lastHover!==entry?.node){lastHover=entry?.node;moveMark(lastHover);}
  }
  function onClick(event){
    if(!active) return;
    const entry=candidate(event.target);
    if(!entry) return;
    event.preventDefault();event.stopImmediatePropagation();
    const existing=targets.findIndex(t=>t.selector===entry.selector);
    if(!multiple){targets=[entry];stop();}
    else if(existing>=0)targets.splice(existing,1);
    else if(targets.length<8)targets.push(entry);
    else status('Máximo ocho elementos por revisión.');
    render();
  }
  document.addEventListener('pointermove',onPointer,true);
  document.addEventListener('click',onClick,true);
  document.addEventListener('keydown',event=>{if(active && event.key==='Escape'){event.preventDefault();stop();}},true);
  $('[data-single]').onclick=()=>{multiple=false;$('[data-single]').setAttribute('aria-pressed','true');$('[data-multi]').setAttribute('aria-pressed','false');if(targets.length>1)targets=targets.slice(-1);render();};
  $('[data-multi]').onclick=()=>{multiple=true;$('[data-single]').setAttribute('aria-pressed','false');$('[data-multi]').setAttribute('aria-pressed','true');render();};
  $('[data-start]').onclick=()=>{active=!active;if(!active){stop();return;}$('[data-start]').setAttribute('aria-pressed','true');status('Haz clic en un elemento de la página. Esc para cancelar.');};
  $('[data-clear]').onclick=()=>{targets=[];stop();render();};
  // Adjuntar referencias descriptivas al mensaje de Codex, sin afirmar que son
  // manifiestos verificables de Fase 7 o permitir al worker escribir fuera de su sandbox.
  form.addEventListener('submit', event=>{
    if(!targets.length) return;
    const value=field.value.trim();
    // Solo contexto; el servidor no confía en estas referencias para autorizar cambios.
    const remaining=1000-value.length;
    const hints=targets.map((t,i)=>`${i+1}) ${location.pathname} ${t.selector}: ${t.label.slice(0,36)}`);
    const suffix='\n\nReferencias visuales indicativas (verificar en el código):\n'+hints.join('\n');
    if (suffix.length<=remaining) {
      field.value=value+suffix;
      // El envío de Codex continúa con sus propias protecciones y borradores.
    } else status('La selección es demasiado extensa; acorta el mensaje antes de enviar.');
  },true);
  async function ensureCsrf(){if(csrf)return;const data=await request('/status');csrf=data.csrf;}
  function reviewUrl(previewId){
    const u=new URL(location.href);u.searchParams.delete('pliegue_preview');
    if(previewId)u.searchParams.set('pliegue_preview',previewId);
    return u.toString();
  }
  const dialog=$('.pls-review');
  const frames=[...dialog.querySelectorAll('iframe')];
  const dialogMessage=$('.pls-review-status');
  function closeReview(){if(dialog.open)dialog.close();frames.forEach(f=>f.removeAttribute('src'));}
  $('[data-dismiss]').onclick=()=> $('[data-reject]').click();
  $('[data-visual-preview]').onclick=async()=>{
    if(!targets.length){status('Selecciona un elemento primero.');return;}
    const message=field.value.trim();
    if(!message){field.focus();status('Describe el cambio visual antes de comparar.');return;}
    stop();reviewReady=false;$('[data-accept]').disabled=true;
    try {
      await ensureCsrf();
      // Solo operaciones declarativas admitidas por el servidor: texto, color, ocultar y nota.
      const result=await request('/chat','POST',{message,target:targets.map(t=>({selector:t.selector,label:t.label})),path:location.pathname});
      draftId=result.draft.id;
      dialogMessage.textContent='Preparando comparación…';
      dialog.showModal();
      frames[0].src=reviewUrl();
      frames[1].onload=async()=>{
        try{await request('/preview/'+encodeURIComponent(draftId),'POST',{});reviewReady=true;
          dialogMessage.textContent='Revisa ambas pantallas antes de aceptar. El cambio aún no está publicado.';
          $('[data-accept]').disabled=false;
        }catch(err){dialogMessage.textContent=err.message;}
      };
      frames[1].src=reviewUrl(draftId);
    }catch(err){status(err.message);}
  };
  $('[data-accept]').onclick=async()=>{
    if(!draftId || !reviewReady)return;
    try{await ensureCsrf(); await request('/apply/'+encodeURIComponent(draftId),'POST',{});
      draftId='';closeReview();location.reload();
    }catch(err){dialogMessage.textContent=err.message;}
  };
  $('[data-reject]').onclick=async()=>{
    try{if(draftId){await ensureCsrf();await request('/discard/'+encodeURIComponent(draftId),'POST',{});}draftId='';closeReview();
      status('Borrador descartado. No se aplicaron cambios.');
    }catch(err){dialogMessage.textContent=err.message;}
  };
  $('[data-visual-undo]').onclick=async()=>{
    if(!window.confirm('¿Deshacer la última revisión visual publicada?'))return;
    try{await ensureCsrf();await request('/undo','POST',{});location.reload();}
    catch(err){status(err.message);}
  };
  // DATOS EN VIVO (V5): Las peticiones operativas nunca pasan por el worker.
  // Incluso si el Administrador había seleccionado "Editar", #datos es SOLO CONSULTA.
  const LIVE_INTERVAL_MS = 30000;
  let rolesCsrf = '';
  let liveEntry = null;
  let activeController = null;
  let lastQueryAt = 0;
  const dataPrompt = q => {
    const s = q.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('es');
    const explicitlyLive = /(?:^|\s)#(?:datos|postgres|bd)(?=\s|:|$)/.test(s);
    if (explicitlyLive) return true;
    // Clasificar preguntas sobre datos, no órdenes de edición de interfaz o código.
    const wantsRead = /(?:\?|\bcuant[oa]s?\b|\btotal\b|\bnumero\b|\bcantidad\b|\bestadisticas?\b|\bresumen\b|\bkpi\b|\bpendientes?\b|\bregistrados?\b|\bpor estado\b|\bestado de\b|\bconsulta\b|\bdime\b|\bmuestrame\b|\blista\b)/.test(s);
    const entity = /devoluc|recolec|inspecc|\bventas?\b|reembols|costos?|usuarios|inventario/.test(s);
    const wantsEdit = /(?:^|\s)(?:crea|modifica|edita|cambia|agrega|elimina|borra|disena|programa|implementa|estiliza)(?:\s|$)/.test(s);
    return wantsRead && entity && !wantsEdit;
  };
  function liveVisible() {
    return document.visibilityState === 'visible' &&
      code.getClientRects().length > 0 &&
      window.getComputedStyle(code).visibility !== 'hidden';
  }
  async function queryLive(entry) {
    if (entry !== liveEntry) return;
    if (activeController) activeController.abort();
    const controller = new AbortController();
    activeController = controller;
    const result = entry.querySelector('[data-live-result]');
    const stamp = entry.querySelector('[data-live-stamp]');
    try {
      if (!rolesCsrf) {
        const auth = await fetch('/pliegue-asistente/config', {
          credentials:'same-origin', cache:'no-store', signal:controller.signal
        });
        if (!auth.ok) throw new Error('Tu sesión no se pudo verificar.');
        const config = await auth.json();
        if (!config.is_admin || !config.csrf) throw new Error('No autorizado para esta consulta.');
        rolesCsrf = config.csrf;
      }
      // Cada petición ejecuta SELECT sobre PostgreSQL al momento; no se usa
      // localStorage, datos precargados, respuestas de Codex ni caché HTTP.
      const response = await fetch('/pliegue-asistente/consulta', {
        method:'POST', credentials:'same-origin', cache:'no-store', signal:controller.signal,
        headers:{'Content-Type':'application/json', 'Cache-Control':'no-store',
          'X-Pliegue-Roles-CSRF':rolesCsrf},
        body:JSON.stringify({message:entry.dataset.question})
      });
      const data = await response.json().catch(()=>({}));
      if (!response.ok || data.read_only !== true || !String(data.source||'').startsWith('PostgreSQL')) {
        throw new Error(data.error || 'No se pudo verificar la consulta con PostgreSQL.');
      }
      if (entry !== liveEntry) return;
      result.textContent = data.reply;
      stamp.textContent = 'PostgreSQL en vivo · ' + new Date(data.as_of).toLocaleString('es-MX') +
        ' · actualización automática';
      entry.dataset.connection = 'live';
    } catch (err) {
      if (entry !== liveEntry) return;
      // Fallo cerrado: ocultar explícitamente cualquier conteo anterior.
      result.textContent = 'No hay datos verificados disponibles en este momento. ' +
        (err && err.message ? err.message : 'Error de conexión.');
      stamp.textContent = 'Sin conexión verificada · reintento automático';
      entry.dataset.connection = 'offline';
      rolesCsrf = '';
    } finally {
      if (activeController === controller) {
        lastQueryAt = Date.now();
        activeController = null;
      }
    }
  }
  function refreshLive() {
    if (liveEntry && liveVisible() && !activeController &&
      Date.now() - lastQueryAt >= 10000) queryLive(liveEntry);
  }
  window.setInterval(refreshLive, LIVE_INTERVAL_MS);
  window.addEventListener('focus', refreshLive);
  document.addEventListener('visibilitychange', refreshLive);
  // Captura antes del listener del formulario de Codex, en ambos modos.
  document.addEventListener('submit', event => {
    if (event.target !== form) return;
    const question = field.value.trim();
    if (!question || !dataPrompt(question)) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    // La UX refleja lo que realmente se ejecutará: una consulta READ ONLY.
    const consult = code.querySelector('[data-request-mode="consult"]');
    if (consult && consult.getAttribute('aria-pressed') !== 'true') consult.click();
    const thread = code.querySelector('.pliegue-thread');
    if (!thread) return;
    const node = document.createElement('article');
    node.className = 'pls-data-answer';
    node.dataset.question = question;
    const user = document.createElement('p');
    user.className = 'pls-data-user';
    user.textContent = question;
    const result = document.createElement('p');
    result.setAttribute('data-live-result','');
    result.textContent = 'Consultando PostgreSQL en vivo…';
    const stamp = document.createElement('small');
    stamp.setAttribute('data-live-stamp','');
    stamp.textContent = 'Solo lectura · sin copia de demostración';
    node.append(user,result,stamp);
    thread.append(node);
    node.scrollIntoView({block:'nearest'});
    field.value = '';
    field.dispatchEvent(new Event('input',{bubbles:true}));
    liveEntry = node; // Solo la consulta más reciente se actualiza automáticamente.
    lastQueryAt = 0;
    queryLive(node);
  }, true);
})();
