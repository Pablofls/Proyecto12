/* Pliegue 20.0 — acabado de interfaz (Admin) y conexión visible a PostgreSQL.
   No modifica permisos ni envía SQL desde el navegador. */
(() => {
  'use strict';
  const ICONS = Object.freeze({
    camera:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 7h4l2-3h4l2 3h4a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2Z"/><circle cx="12" cy="13" r="3.5"/></svg>',
    mic:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10a7 7 0 0 0 14 0M12 17v5m-4 0h8"/></svg>',
    db:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 4 16 4 16 0V5M4 12c0 4 16 4 16 0"/></svg>'
  });
  const normal = str => (str || '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('es');
  function init() {
    const boot = document.querySelector('#pliegue-boot');
    let cfg={};
    try { cfg=JSON.parse(boot?.textContent || '{}'); } catch { return; }

    // El asistente por rol consulta PostgreSQL desde Flask. Mostrar si la fuente
    // está disponible, sin prometer conectividad hasta recibir HTTP 200.
    const dock = cfg.is_admin ? document.querySelector('#pliegue-codigo') : document.querySelector('#pliegue-roles-panel');
    if (!dock) return;
    const sourceParent = cfg.is_admin ? dock.querySelector('.pliegue-attachments') : dock.querySelector('.pr-consult');
    if (sourceParent && !sourceParent.querySelector('.pliegue-db-health')) {
      const db=document.createElement('small');
      db.className='pliegue-db-health';
      db.setAttribute('role','status');
      db.setAttribute('aria-live','polite');
      db.innerHTML=ICONS.db+'<span>Comprobando PostgreSQL…</span>';
      if (cfg.is_admin) sourceParent.append(db);
      else sourceParent.append(db);
      const refresh = async () => {
        const controller = new AbortController();
        try {
          const response=await fetch('/pliegue-asistente/conexion', {
            credentials:'same-origin',cache:'no-store',signal:controller.signal
          });
          const data=await response.json().catch(()=>({}));
          const ok=response.ok && data.connected === true && data.read_only === true;
          db.dataset.ok=String(ok);
          db.querySelector('span').textContent=ok ? 'PostgreSQL · Conectado' : 'PostgreSQL · Sin conexión';
          db.title='Comprobación real desde Flask · Consultas de solo lectura';
        } catch {
          db.dataset.ok='false';
          db.querySelector('span').textContent='PostgreSQL · Sin conexión';
        }
      };
      refresh();
      // No mostrar un estado de BD desactualizado: nueva verificación en vivo.
      window.setInterval(() => { if (document.visibilityState === 'visible') refresh(); }, 30000);
      window.addEventListener('focus', () => { if (document.visibilityState === 'visible') refresh(); });
      dock.addEventListener('focusin',e=>{
        if (e.target.matches('textarea') && db.dataset.ok==='false') refresh();
      });
    }
    if (!cfg.is_admin) return; // Los otros roles no tienen controles multimedia ni historial.

    const form=dock.querySelector('form.pliegue-code-compose');
    if (!form) return;
    const textarea=form.querySelector('textarea#pliegue-codigo-mensaje');
    const actions=form.querySelector('.pliegue-compose-actions');
    if (!textarea || !actions) return;
    textarea.placeholder='Escribe un mensaje. Usa # para contexto y @ para referencias.';
    const camera=actions.querySelector('[data-camera-open]');
    const voice=actions.querySelector('[data-voice-open]');
    for (const [btn,icon,label] of [[camera,ICONS.camera,'Cámara'],[voice,ICONS.mic,'Nota de voz']]) {
      if (!btn) continue;
      btn.innerHTML=icon;
      btn.setAttribute('aria-label',label);
      btn.title=label;
      btn.classList.add('pliegue-media-icon');
    }
    // Dejar que pliegue-codigo.js decida disponibilidad de APIs reales.
    // Los controles no compatibles conservan [hidden] y jamás son botones falsos.

    if (!form.querySelector('.pliegue-syntax-hint')) {
      const hint=document.createElement('div');
      hint.className='pliegue-syntax-hint';
      hint.innerHTML='<span class="pliegue-syntax-mark">#</span> rol, pantalla o HTML <span aria-hidden="true">·</span> <span class="pliegue-syntax-mark">@</span> página o componente <span aria-hidden="true">·</span> <span class="pliegue-syntax-mark">/</span> servicio <span aria-hidden="true">·</span> <strong>#datos</strong> PostgreSQL';
      textarea.before(hint);
    }
    // Sugerencias # de CONTEXTO para Codex, no suplantan identidades ni
    // confieren permisos. La verificación de la sesión permanece en Flask.
    const roles = ['Administrador','Analista de Devoluciones','Cliente',
      'Coordinador de Logistica','Encargado de Reembolsos',
      'Encargado del Centro de Devoluciones','Inspector',
      'Operador de Almacen','Recolector','Supervisor'];
    const routeTemplates = {
      '/panel':'panel/interno.html','/panel/causas':'panel/causas.html',
      '/panel/costos':'panel/costos.html','/panel/bitacora':'panel/bitacora.html',
      '/ventas':'ventas/listar.html','/devoluciones':'devoluciones/listar.html',
      '/inspecciones':'inspecciones/listar.html','/logistica':'logistica/listar.html',
      '/reembolsos':'reembolsos/listar.html','/usuarios':'usuarios/listar.html',
      '/notificaciones':'notificaciones/listar.html'
    };
    const page = location.pathname.replace(/\/$/,'') || '/';
    const options=[
      {label:'Datos de PostgreSQL',value:'#datos',detail:'Consulta operativa autorizada'},
      {label:'Pantalla actual',value:'#pantalla:'+page,detail:'Referencia de esta página'},
      ...((routeTemplates[page])?[{label:'HTML actual',value:'#html:'+routeTemplates[page],detail:'Archivo de referencia'}]:[]),
      ...roles.map(role=>({label:'Rol: '+role,value:'#rol:'+role.replace(/ /g,'_'),detail:'Contexto de diseño; no cambia permisos'}))
    ];
    const popup=document.createElement('div');
    popup.className='pliegue-hash-options';
    popup.setAttribute('role','listbox');
    popup.setAttribute('aria-label','Contextos de Pliegue');
    popup.hidden=true;
    form.append(popup);
    let active=0, shown=[];
    function fragment(){
      if (textarea.selectionStart!==textarea.selectionEnd) return null;
      const cursor=textarea.selectionStart;
      const prefix=textarea.value.slice(0,cursor);
      const match=prefix.match(/(?:^|\s)#([\p{L}\p{N}_.-]*)$/u);
      if (!match) return null;
      return {start:cursor-match[1].length-1,end:cursor,q:normal(match[1])};
    }
    function close(){popup.hidden=true;textarea.removeAttribute('aria-activedescendant');}
    function choose(option){
      const tok=fragment(); if (!tok || !option) return;
      textarea.setRangeText(option.value+' ',tok.start,tok.end,'end');
      close();textarea.focus();textarea.dispatchEvent(new Event('input',{bubbles:true}));
    }
    function render(){
      const tok=fragment();if(!tok)return close();
      shown=options.filter(opt=>normal(opt.label+' '+opt.value).includes(tok.q)).slice(0,9);
      if(!shown.length)return close();
      popup.replaceChildren(...shown.map((opt,i)=>{
        const b=document.createElement('button');b.type='button';b.setAttribute('role','option');
        b.className='pliegue-hash-choice';
        b.setAttribute('aria-selected',String(i===active));
        const primary=document.createElement('span');primary.textContent=opt.label;
        const extra=document.createElement('small');extra.textContent=opt.detail;
        b.append(primary,extra);
        b.addEventListener('mousedown',e=>e.preventDefault());
        b.addEventListener('click',()=>choose(opt));
        return b;
      }));
      active=Math.max(0,Math.min(active,shown.length-1));
      popup.querySelectorAll('[role=option]').forEach((node,i)=>node.setAttribute('aria-selected',String(i===active)));
      popup.hidden=false;
    }
    textarea.addEventListener('input',()=>{active=0;render();});
    textarea.addEventListener('click',render);
    textarea.addEventListener('keydown',e=>{
      if(popup.hidden)return;
      if(e.key==='Escape'){e.preventDefault();close();return;}
      if(e.key==='ArrowDown'||e.key==='ArrowUp'){
        e.preventDefault();active=(active+(e.key==='ArrowDown'?1:-1)+shown.length)%shown.length;render();return;
      }
      if(e.key==='Enter' && !e.shiftKey){e.preventDefault();choose(shown[active]);}
    });
    document.addEventListener('pointerdown',e=>{if(!popup.contains(e.target)&&e.target!==textarea)close();});
  }
  if (document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});
  else init();
})();
