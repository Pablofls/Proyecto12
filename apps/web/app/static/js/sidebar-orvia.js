/* ORVIA — iconos y enlaces compartidos. Fuente de autorizacion: nav.menu de base.html. */
(function () {
  'use strict';
  var paths = Object.freeze({
    panel: 'M3 10l9-7 9 7v11h-6v-7H9v7H3z',
    ventas: 'M4 20V10m6 10V4m6 16v-8m4 8V6',
    devoluciones: 'm12 2 9 5-9 5-9-5 9-5zM3 7v10l9 5 9-5V7M12 12v10',
    recolecciones: 'M3 7h11v10H3zM14 11h4l3 3v3h-7zM5 19h2m10 0h2',
    inspecciones: 'M20 20l-5-5M17 9a8 8 0 1 0-16 0 8 8 0 0 0 16 0z',
    inventario: 'm12 2 9 5-9 5-9-5 9-5zM3 12l9 5 9-5M3 17l9 5 9-5',
    reembolsos: 'M3 5h18v14H3zM17 12h3M3 9h18',
    causas: 'M6 3h10l4 4v14H6zM15 3v5h5M9 13h7M9 17h6',
    costos: 'M5 3h14v18H5zM8 8h8M8 12h8M8 16h8',
    catalogos: 'M3 12V4h9l9 9-8 8zM8 8h.01',
    usuarios: 'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM16 4a4 4 0 0 1 0 8M22 21v-2a4 4 0 0 0-3-4',
    bitacora: 'M3 12a9 9 0 1 1 3 7M3 17v-5h5M12 7v5l4 3',
    servicios: 'M12 3a3 3 0 0 0-3 3v1l-2 2H6a3 3 0 0 0 0 6h1l2 2v1a3 3 0 0 0 6 0v-1l2-2h1a3 3 0 0 0 0-6h-1l-2-2V6a3 3 0 0 0-3-3z'
  });
  function normalize(label) {
    return String(label || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
  }
  function icon(pathData) {
    var ns = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');
    svg.setAttribute('aria-hidden', 'true');
    var p = document.createElementNS(ns, 'path');
    p.setAttribute('d', pathData);
    svg.appendChild(p);
    return svg;
  }
  function initialize() {
    var original = document.querySelector('body > nav.menu');
    var shared = document.getElementById('orvia-global-sidebar');
    var links = document.getElementById('orvia-global-links');
    // La clase llega desde el servidor; si no se puede armar el menu nuevo, se
    // retira para que el menu anterior siga disponible.
    function revertir() { document.body.classList.remove('orvia-sidebar-unificado'); }
    if (!original || !shared || !links) { revertir(); return; }
    var permitted = original.querySelectorAll('a[href]');
    if (!permitted.length) { revertir(); return; }
    links.replaceChildren();
    var built = 0;
    var candidates = [];
    permitted.forEach(function (a) {
      var label = a.textContent.trim();
      var key = normalize(label);
      var dest = a.getAttribute('href');
      if (!dest) return;
      var item = document.createElement('a');
      item.href = a.href;
      item.appendChild(icon(paths[key] || 'M4 6h16M4 12h16M4 18h16'));
      var text = document.createElement('span'); text.textContent = label;
      item.appendChild(text);
      var currentPath = new URL(item.href, window.location.href).pathname.replace(/\/$/, '');
      var pagePath = window.location.pathname.replace(/\/$/, '');
      /* Guardar rutas para escoger una sola opcion activa (exacta > prefijo). */
      candidates.push({ item: item, path: currentPath, exact: pagePath === currentPath,
        prefix: key !== 'panel' && currentPath && pagePath.indexOf(currentPath + '/') === 0,
        legacy: a.classList.contains('activo') });
      links.appendChild(item); built++;
    });
    if (!built) { revertir(); return; }
    /* Evita dos marcas activas, p. ej. Inspecciones e Inventario. */
    var current = candidates.filter(function (c) { return c.exact; })[0];
    if (!current) {
      var prefixes = candidates.filter(function (c) { return c.prefix; });
      prefixes.sort(function (a,b) { return b.path.length - a.path.length; });
      current = prefixes[0] || candidates.filter(function (c) { return c.legacy; })[0];
    }
    if (current) current.item.setAttribute('aria-current', 'page');
    // Mantener los nodos viejos para JS local (notificaciones, logout, controles),
    // pero dejar visible solamente la unica barra compartida.
    var sidebars = Array.prototype.filter.call(document.querySelectorAll('main aside'), function (el) {
      return !el.closest('.orvia-global-sidebar');
    });
    sidebars.forEach(function (aside) {
      aside.classList.add('orvia-sidebar-antiguo');
      aside.setAttribute('aria-hidden', 'true');
      if (aside.id) {
        document.querySelectorAll('[aria-controls]').forEach(function (btn) {
          if (btn.getAttribute('aria-controls') === aside.id) {
            btn.classList.add('orvia-boton-menu-antiguo');
          }
        });
      }
      var p = aside.parentElement;
      // Los shells personalizados suelen reservar una columna para el aside.
      if (p && p !== document.querySelector('body > main')) {
        p.classList.add('orvia-contenido-unificado');
        if (window.getComputedStyle(p).display === 'grid') {
          p.style.setProperty('grid-template-columns', 'minmax(0,1fr)', 'important');
        }
      }
    });
    var toggle = document.querySelector('.orvia-global-toggle');
    var overlay = document.querySelector('.orvia-global-overlay');
    function setOpen(open) {
      document.body.classList.toggle('orvia-global-menu-open', open);
      toggle.setAttribute('aria-expanded', String(open));
      toggle.setAttribute('aria-label', open ? 'Cerrar menú de Orvia' : 'Abrir menú de Orvia');
    }
    if (toggle && overlay) {
      toggle.addEventListener('click', function () { setOpen(!document.body.classList.contains('orvia-global-menu-open')); });
      overlay.addEventListener('click', function () { setOpen(false); });
      document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setOpen(false); });
      links.addEventListener('click', function () { setOpen(false); });
    }
    // Conserva las referencias al menu original, usadas por scripts antiguos.
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialize);
  else initialize();
})();
