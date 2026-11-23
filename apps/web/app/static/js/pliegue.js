/* Pliegue: cliente sin credenciales; autorización, CSRF y persistencia en Flask. */
(function(){'use strict';
const boot=document.getElementById('pliegue-boot');if(!boot)return;
let cfg;try{cfg=JSON.parse(boot.textContent)}catch(e){return}
let draft=null,csrf=null,open=false,selected=null;
const url='/pliegue';
function isReturns(){return location.pathname.indexOf('/devoluciones')!==-1}
function updateView(data){
  const c=data||{};
  let s=document.getElementById('pliegue-applied-style');if(!s){s=document.createElement('style');s.id='pliegue-applied-style';document.head.appendChild(s)}
  s.textContent='';
  if(c.title_color){ const h=[...document.querySelectorAll('main h1')].find(x=>/panel general/i.test(x.textContent));if(h)h.style.setProperty('color',c.title_color,'important') }
  else {const h=[...document.querySelectorAll('main h1')].find(x=>/panel general/i.test(x.textContent));if(h)h.style.removeProperty('color')}
  // Reaplicar operaciones publicadas o borrador únicamente a la ruta pertinente.
  const edits=Array.isArray(c.edits)?c.edits:[];
  document.querySelectorAll('[data-pliegue-note]').forEach(n=>n.remove());
  edits.forEach(edit=>{
    if(edit.page!==location.pathname || !edit.selector) return;
    let el;try{el=document.querySelector(edit.selector)}catch(e){return}
    if(!el || !el.closest('main'))return;
    if(edit.kind==='text')el.textContent=String(edit.value||'');
    if(edit.kind==='hidden')el.style.display=edit.value?'none':'';
    if(edit.kind==='color'){
      if(edit.value)el.style.setProperty('color',edit.value,'important');
      else el.style.removeProperty('color');
    }
    if(edit.kind==='note' && edit.value){
      const n=document.createElement('p');n.dataset.pliegueNote='1';
      n.className='pliegue-inserted-note';n.textContent=String(edit.value);
      el.insertAdjacentElement('afterend',n);
    }
  });
  if((isReturns() || location.pathname==='/panel')&&c.group_returns){
    document.querySelectorAll('table').forEach(table=>{
      const hs=[...table.querySelectorAll('thead th')].map(x=>x.textContent.trim().toLowerCase());const i=hs.findIndex(x=>x.includes('estado'));if(i<0)return;
      const body=table.tBodies[0];if(!body)return;
      const rows=[...body.rows];if(rows.length<2)return;
      const order=t=> /inspecci[oó]n/.test(t)?0:/solicitad|recibid/.test(t)?1:/autorizad/.test(t)?2:/recolecci/.test(t)?3:/resuelt/.test(t)?4:/cerrad/.test(t)?5:6;
      rows.sort((a,b)=>order((a.cells[i]?.textContent||'').toLowerCase())-order((b.cells[i]?.textContent||'').toLowerCase()));
      rows.forEach(r=>body.appendChild(r));
    });
  }
}
function createDock() {
 const dock = document.createElement('aside');
 dock.className = 'pliegue-dock';
 dock.hidden = true;
 dock.setAttribute('aria-label', 'Asistente Pliegue');
 dock.innerHTML=`<div class="pliegue-head"><img src="/static/img/pliegue.png" alt="" width="24" height="24"><div class="pliegue-heading"><h2>Pliegue</h2><small>Borrador privado · Administrador</small></div><button class="pliegue-close" aria-label="Cerrar Pliegue">×</button></div>`;
 return dock;
}
function createLaunch() {
 const launch = document.createElement('button');
 launch.type = 'button';
 launch.className = 'pliegue-launch';
 launch.title = 'Abrir Pliegue';
 launch.setAttribute('aria-label', 'Abrir Pliegue');
 const logo = document.createElement('img');
 logo.src = '/static/img/pliegue.png';
 logo.alt = '';
 launch.append(logo);
 return launch;
}
function showDock(dock, launch, visible) {
 dock.hidden = !visible;
 launch.setAttribute('aria-expanded', String(visible));
 document.body.classList.toggle('pliegue-open', visible && !dock.classList.contains('pliegue-dock-global'));
}
function mountLaunch(launch) {
 const relocate = () => {
  const bell = Array.from(document.querySelectorAll('.campanita')).find(node => node.getClientRects().length);
  const slot = [...document.querySelectorAll('#ov-real-bell, #pliegue-lab-launch')]
   .find(node => node.getClientRects().length);
  const anchor = bell || slot;
  if (anchor === bell && bell) {
   if (bell.previousElementSibling !== launch) bell.before(launch);
  } else {
   const parent = anchor || document.body;
   if (launch.parentElement !== parent) parent.append(launch);
  }
  launch.classList.toggle('pliegue-launch-floating', !anchor);
 };
 relocate();
 window.addEventListener('resize', relocate);
 const watcher = new MutationObserver(relocate);
 watcher.observe(document.body, {childList: true, subtree: true});
}

if (cfg.lab || document.querySelector('#pliegue-codigo[data-visual-global]')) {
 if (!cfg.is_admin) return;
 const code = document.getElementById('pliegue-codigo');
 if (!code) return;
 // Cached phase 6.5 templates still expose the old inline composer until Flask restarts.
 if (code.hasAttribute('data-visual-inline')) {
  const launch = createLaunch();
  launch.setAttribute('aria-controls', code.id);
  mountLaunch(launch);
  launch.addEventListener('click', () => code.querySelector('textarea').focus());
  return;
 }
 const dock = createDock();
 const launch = createLaunch();
 dock.classList.add('pliegue-dock-code');
 dock.id = 'pliegue-panel';
 launch.setAttribute('aria-controls', dock.id);
 dock.append(code);
 document.body.append(dock);
 mountLaunch(launch);
 const close = dock.querySelector('.pliegue-close');
 const global = code.hasAttribute('data-visual-global');
 const controls = document.createElement('div');
 controls.className = 'pliegue-dock-controls';
 const makeControl = (label, symbol) => {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'pliegue-dock-control';
  button.setAttribute('aria-label', label);
  button.title = label;
  button.innerHTML = '<span class="pliegue-icon icon-' + symbol + '" aria-hidden="true"></span>';
  controls.append(button);
  return button;
 };
 let minimized;
 let expand;
 let minimize;
 function setMinimized(value) {
  dock.classList.toggle('pliegue-minimized', value);
  code.inert = value;
  if (minimize) {
   const label = value ? 'Restaurar Pliegue' : 'Minimizar Pliegue';
   minimize.setAttribute('aria-label', label);
   minimize.title = label;
   minimize.firstElementChild.className = 'pliegue-icon icon-' + (value ? 'restore' : 'minimize');
  }
  minimized = value;
 }
 function open(focus = true) {
  setMinimized(false);
  showDock(dock, launch, true);
  if (focus) (global ? close : code.querySelector('textarea')).focus({preventScroll: true});
  code.dispatchEvent(new Event('pliegue:open'));
 }
 function closePanel() {
  code.dispatchEvent(new Event('pliegue:close'));
  dock.querySelector('#pliegue-account-popover:popover-open')?.hidePopover();
  window.pliegueVisual?.deactivate();
  setMinimized(false);
  showDock(dock, launch, false);
  launch.focus({preventScroll: true});
 }
 if (global) {
  dock.classList.add('pliegue-dock-global');
  const alignBelowHeader = () => {
   if (dock.hidden) return;
   const header = launch.closest('header');
   dock.style.setProperty('--pliegue-top', Math.max(0, header?.getBoundingClientRect().bottom || 0) + 'px');
  };
  code.addEventListener('pliegue:open', alignBelowHeader);
  window.addEventListener('resize', alignBelowHeader);
  window.addEventListener('scroll', alignBelowHeader, {passive: true});
  dock.querySelector('.pliegue-head small').textContent = code.dataset.currentScreen;
  const status = code.querySelector('#pliegue-codigo-worker');
  const heading = dock.querySelector('.pliegue-heading');
  const account = code.querySelector('[data-codex-account-template]');
  if (account) {
   heading.append(account.content.cloneNode(true));
   status.hidden = true;
  } else if (status) {
   heading.append(status);
  }
  const history = code.querySelector('#pliegue-historial');
  const historyButton = makeControl('Historial de solicitudes', 'history');
  historyButton.setAttribute('aria-controls', history.id);
  historyButton.setAttribute('aria-expanded', 'false');
  historyButton.addEventListener('click', () => {
   if (minimized) open(false);
   history.hidden = !history.hidden;
   historyButton.setAttribute('aria-expanded', String(!history.hidden));
   if (!history.hidden) history.scrollIntoView({block: 'nearest'});
  });
  expand = makeControl('Expandir Pliegue', 'expand');
  expand.setAttribute('aria-pressed', 'false');
  minimize = makeControl('Minimizar Pliegue', 'minimize');
  dock.querySelector('.pliegue-head').append(controls);
  controls.append(close);
  close.type = 'button';
  close.title = 'Cerrar Pliegue';
  close.innerHTML = '<span class="pliegue-icon icon-close" aria-hidden="true"></span>';
  expand.addEventListener('click', () => {
   const expanded = !dock.classList.contains('pliegue-expanded');
   dock.classList.toggle('pliegue-expanded', expanded);
   expand.setAttribute('aria-pressed', String(expanded));
   if (minimized) open(false);
  });
  minimize.addEventListener('click', () => minimized ? open(false) : setMinimized(true));
  document.addEventListener('pliegue:selection-mode', event => {
   if (event.detail.canvas && !dock.hidden) {
    dock.querySelector('.pliegue-head small').textContent =
     code.dataset.currentScreen + (event.detail.enabled ? ' · Selección activa' : '');
    setMinimized(event.detail.enabled && matchMedia('(max-width: 700px)').matches);
   }
  });
  document.addEventListener('pliegue:selection-picked', event => {
   if (event.detail.canvas && minimized && !event.detail.multiple) open(false);
  });
 }
 launch.addEventListener('click', () => {
  if (dock.hidden || minimized) open();
  else closePanel();
 });
 close.addEventListener('click', closePanel);
 dock.addEventListener('keydown', event => {
  if (event.key === 'Escape' && !event.defaultPrevented &&
      !code.querySelector('dialog[open]:is([data-media-dialog], [data-voice-dialog])')) closePanel();
 });
 if (location.pathname === '/pliegue/codigo') open(false);
 else showDock(dock, launch, false);
 updateView(cfg.draft||cfg.published);
 return;
}
updateView(cfg.draft||cfg.published);
// La vista previa en iframe es un origen aislado: sin formularios ni acceso a cookies desde JS.
if(cfg.draft_id){document.documentElement.dataset.plieguePreview='true';document.addEventListener('submit',e=>{e.preventDefault();alert('Vista previa de solo lectura: no se guardan datos reales')},true);document.addEventListener('click',e=>{let a=e.target.closest('a[href]');if(a&&a.origin===location.origin&&a.pathname!='/logout'&&a.pathname.indexOf('/pliegue/')!==0){a.href=new URL(a.href).pathname+'?pliegue_preview='+encodeURIComponent(cfg.draft_id)}},true)}
if (cfg.draft_id) return;
if(!cfg.is_admin){let known=cfg.version;setInterval(async()=>{try{const r=await fetch('/pliegue/live',{credentials:'same-origin',cache:'no-store'});if(!r.ok)return;const d=await r.json();if(d.version!==known)location.reload()}catch(e){}},15000);return}
const dock = createDock();
dock.insertAdjacentHTML("beforeend", `<div class="pliegue-chat" aria-live="polite"><div class="pliegue-msg">Selecciona un título o texto para renombrarlo, cambiar su color, ocultarlo o agregar una nota. También puedes pedir: “Agrupa las devoluciones por estado y pon primero las que están en inspección”.</div></div><div class="pliegue-toolbar"><button data-act="select">Seleccionar elemento</button><button data-act="preview">Vista previa</button><button data-act="undo">Deshacer publicación</button></div><div class="pliegue-actions"><button class="pliegue-primary" data-act="apply">Aplicar</button><button data-act="discard">Descartar</button></div><form class="pliegue-compose"><textarea maxlength="1000" placeholder="Pide un cambio para esta pantalla..." aria-label="Mensaje para Pliegue"></textarea><button type="submit">Enviar</button></form><div class="pliegue-hint">Edición visual reversible. No modifica Python, JavaScript, consultas ni datos. Para cambios funcionales se necesita un entorno Codex aislado.</div>`);
const prev=document.createElement('section');prev.className='pliegue-preview';prev.hidden=true;prev.innerHTML='<header><span>Vista previa privada — sin guardar datos</span><button aria-label="Cerrar vista previa" type="button">Cerrar</button></header><iframe title="Vista previa Pliegue" sandbox="allow-scripts"></iframe>';
document.body.append(dock,prev);
const chat=dock.querySelector('.pliegue-chat');const textarea=dock.querySelector('textarea');
prev.querySelector('iframe').addEventListener('load',async()=>{if(!draft||!csrf)return;try{await call('/preview/'+encodeURIComponent(draft.id),{method:'POST',body:'{}'});msg('Vista previa abierta: puedes revisar esta versión antes de aplicar.')}catch(e){msg('No se pudo validar la vista previa: '+e.message)}});
function msg(t,who){const e=document.createElement('div');e.className='pliegue-msg'+(who?' user':'');e.textContent=t;chat.appendChild(e);chat.scrollTop=chat.scrollHeight}
async function call(path,opt){let r=await fetch(url+path,{credentials:'same-origin',cache:'no-store',...opt,headers:{'Content-Type':'application/json','X-Pliegue-CSRF':csrf||'',...(opt&&opt.headers||{})}});let d=await r.json().catch(()=>({error:'Respuesta inesperada'}));if(!r.ok)throw Error(d.error||`HTTP ${r.status}`);return d}
async function init(){const d=await call('/status');csrf=d.csrf;draft=d.drafts.length?d.drafts[d.drafts.length-1]:null;return d}
function showPreview(){if(!draft){msg('Primero solicita un cambio.');return}const u=new URL(location.href);u.searchParams.set('pliegue_preview',draft.id);prev.querySelector('iframe').src=u.toString();prev.hidden=false}
function selectorFor(el){
 let parts=[];let node=el;
 while(node&&node.tagName&&node.tagName.toLowerCase()!=='main'&&parts.length<14){
   const tag=node.tagName.toLowerCase();
   const siblings=[...node.parentElement.children].filter(x=>x.tagName===node.tagName);
   parts.unshift(tag+':nth-of-type('+(siblings.indexOf(node)+1)+')');node=node.parentElement;
 }
 return node&&node.tagName.toLowerCase()==='main'?'main > '+parts.join(' > '):null;
}
const launch = createLaunch();
mountLaunch(launch);
launch.addEventListener('click',async()=>{
 dock.hidden=!dock.hidden;open=!dock.hidden;
 document.body.classList.toggle('pliegue-open',open);
 if(open){try{await init()}catch(e){msg('Error de acceso: '+e.message)}}
});
dock.querySelector('.pliegue-close').onclick=()=>{dock.hidden=true;open=false;document.body.classList.remove('pliegue-open')};
prev.querySelector('button').onclick=()=>prev.hidden=true;
dock.querySelector('form').addEventListener('submit',async e=>{e.preventDefault();let t=textarea.value.trim();if(!t)return;msg(t,true);textarea.value='';try{if(!csrf)await init();let data=await call('/chat',{method:'POST',body:JSON.stringify({message:t,draft_id:draft?.id||'',target:selected,path:location.pathname})});draft=data.draft;msg(data.reply);showPreview()}catch(err){msg('No se aplicó: '+err.message)}});
dock.querySelectorAll('[data-act]').forEach(b=>b.onclick=async()=>{let action=b.dataset.act;try{
if(action==='preview'){showPreview();return}
if(action==='select'){
 dock.hidden=true;document.body.classList.remove('pliegue-open');
 document.body.classList.add('pliegue-selecting');
 const handler=e=>{
  const h=e.target.closest('main h1, main h2, main h3, main p, main .ov-title, main .ov-subtitle');
  if(!h)return;const selector=selectorFor(h);if(!selector)return;
  e.preventDefault();e.stopPropagation();
  selected={selector,label:h.textContent.trim().slice(0,160)};
  document.body.classList.remove('pliegue-selecting');
  document.removeEventListener('click',handler,true);
  dock.hidden=false;open=true;document.body.classList.add('pliegue-open');
  msg('Seleccionaste: '+selected.label+'. Prueba: Cambia el texto por «Nuevo título», hazlo azul, ocúltalo o agrega texto: «Una nota».');
 };document.addEventListener('click',handler,true);return
}
if(!csrf)await init();if(action==='apply'||action==='discard'){if(!draft){msg('No hay borrador.');return}let d=await call('/'+(action==='apply'?'apply':'discard')+'/'+encodeURIComponent(draft.id),{method:'POST',body:'{}'});draft=null;prev.hidden=true;msg(action==='apply'?'Revisión publicada.':'Borrador descartado.');if(action==='apply')location.reload();}
if(action==='undo'){await call('/undo',{method:'POST',body:'{}'});msg('Última publicación deshecha.');location.reload()}
}catch(err){msg('No se pudo completar: '+err.message)}});
let seen=cfg.version;setInterval(async()=>{if(cfg.draft_id)return;try{let d=await call('/live');if(d.version!==seen){seen=d.version;location.reload()}}catch(e){}},15000);
})();
