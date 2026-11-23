/* Orvia - controles compartidos del encabezado (sin APIs nuevas). */
(function () {
 'use strict';
 function init() {
  const bar=document.getElementById('orvia-topbar');
  if(!bar)return;
  const menu=bar.querySelector('#orvia-account-menu');
  const trigger=bar.querySelector('#orvia-account-trigger');
  const search=bar.querySelector('#orvia-global-search');
  const results=bar.querySelector('#orvia-topbar-results');
  const tableSearch=document.getElementById('ov-search-table');
  const links=[...document.querySelectorAll('body > nav.menu a[href]')];
  const isDashboard=Boolean(tableSearch && document.getElementById('ov-panel'));
  function hideMenu(){menu.hidden=true;trigger.setAttribute('aria-expanded','false');}
  function hideResults(){results.hidden=true;search.setAttribute('aria-expanded','false');}
  trigger.addEventListener('click',()=>{
    const open=menu.hidden;menu.hidden=!open;trigger.setAttribute('aria-expanded',String(open));
    if(open)hideResults();
  });
  if(isDashboard){
    search.placeholder='Buscar folio, producto o cliente...';
    search.setAttribute('aria-label','Buscar en las devoluciones recientes');
  }else{
    search.placeholder='Buscar un módulo de Orvia...';
    search.setAttribute('aria-label','Buscar y abrir un módulo autorizado');
    const normalize=(s)=>String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
    function updateList(){
      const query=normalize(search.value);
      results.replaceChildren();
      if(!query){hideResults();return;}
      const matches=links.filter(a=>normalize(a.textContent).includes(query)).slice(0,10);
      for(const a of matches){const l=document.createElement('a');l.href=a.href;l.textContent=a.textContent.trim();results.append(l);}
      if(!matches.length){const p=document.createElement('p');p.textContent='No hay módulos autorizados con ese nombre.';results.append(p);}
      results.hidden=false;search.setAttribute('aria-expanded','true');
      hideMenu();
    }
    search.addEventListener('input',updateList);
    search.addEventListener('keydown',e=>{
      if(e.key==='Enter'&&!results.hidden){const link=results.querySelector('a');if(link){e.preventDefault();link.click();}}
      if(e.key==='ArrowDown'&&!results.hidden){const link=results.querySelector('a');if(link){e.preventDefault();link.focus();}}
    });
  }
  document.addEventListener('click',e=>{
    if(!bar.querySelector('.orvia-topbar-account').contains(e.target))hideMenu();
    if(!bar.querySelector('.orvia-topbar-search').contains(e.target))hideResults();
  });
  document.addEventListener('keydown',e=>{
    if(e.key==='Escape'){hideMenu();hideResults();}
    if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'&&!e.altKey){
      e.preventDefault();search.focus();search.select();
    }
  });
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);
 else init();
})();
