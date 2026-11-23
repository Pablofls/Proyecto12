(() => {
  'use strict';
  // This literal is the only extra script allowed by the opaque visual frame's CSP.
  const runtime = `'use strict';
const channel = JSON.parse(decodeURIComponent(document.querySelector('meta[name="pliegue-selection"]').content));
const {origin, ...identity} = channel;
const idPattern = /^[0-9a-f]{32}$/;
let enabled = false;
let selected = new Set();
let hovered = null;
const host = document.createElement('div');
const shadow = host.attachShadow({mode: 'closed'});
const sheet = document.createElement('style');
sheet.textContent = ':host{all:initial!important;position:fixed!important;inset:0!important;pointer-events:none!important;z-index:2147483647!important}' +
  'div{position:absolute;box-sizing:border-box;outline:2px dashed #00875E;pointer-events:none;border-radius:2px}' +
  'span{position:absolute;bottom:100%;left:0;background:#00875E;color:white;padding:2px 6px;font:600 12px system-ui;white-space:nowrap;border-radius:3px}';
shadow.append(sheet);
document.body.append(host);

function send(action, fields = {}) {
  window.parent.postMessage({...identity, action, ...fields}, origin);
}
function targetAt(event) {
  return event.target instanceof Element ? event.target.closest('[data-pliegue-element]') : null;
}
let redrawPending = false;
function schedule() {
  if (redrawPending) return;
  redrawPending = true;
  requestAnimationFrame(() => {
    redrawPending = false;
    const container = document.querySelector('dialog:modal') || document.body;
    if (host.parentNode !== container) container.append(host);
    shadow.querySelectorAll('div').forEach(box => box.remove());
    const targets = Array.from(selected, id => [...document.querySelectorAll('[data-pliegue-element="' + id + '"]')]).flat();
    if (enabled && hovered && !targets.includes(hovered)) targets.push(hovered);
    for (const node of targets) {
      const rect = node.getBoundingClientRect();
      if (!rect.width || !rect.height || rect.bottom < 0 || rect.top > innerHeight) continue;
      const box = document.createElement('div');
      box.style.cssText = 'left:' + rect.left + 'px;top:' + rect.top + 'px;width:' + rect.width + 'px;height:' + rect.height + 'px';
      const caption = document.createElement('span');
      caption.textContent = labels[node.dataset.pliegueElement] || node.localName;
      if (rect.top < 24) { caption.style.bottom = 'auto'; caption.style.top = '0'; }
      box.append(caption);
      shadow.append(box);
    }
  });
}
let labels = {};
window.addEventListener('message', event => {
  const message = event.data;
  if (event.source !== window.parent || event.origin !== origin || !message || typeof message !== 'object' ||
      message.session !== identity.session || message.slug !== identity.slug || message.revision !== identity.revision ||
      message.action !== 'state' || Object.keys(message).length !== 7 || typeof message.enabled !== 'boolean' ||
      !Array.isArray(message.ids) || message.ids.length > 8 || !message.ids.every(id => typeof id === 'string' && idPattern.test(id)) ||
      !message.labels || typeof message.labels !== 'object' || Object.keys(message.labels).length > 16 ||
      !Object.entries(message.labels).every(([id, label]) => idPattern.test(id) && typeof label === 'string' && label.length <= 60)) return;
  enabled = message.enabled;
  labels = message.labels;
  selected = new Set(message.ids);
  if (!enabled) hovered = null;
  document.documentElement.toggleAttribute('data-pliegue-selecting', enabled);
  schedule();
});
document.addEventListener('pointermove', event => {
  if (!enabled) return;
  const target = targetAt(event);
  if (target === hovered) return;
  hovered = target;
  send('hover', {id: target?.dataset.pliegueElement || ''});
  schedule();
}, true);
document.addEventListener('pointerleave', () => { hovered = null; schedule(); });
document.addEventListener('scroll', schedule, true);
window.addEventListener('resize', schedule);
new ResizeObserver(schedule).observe(document.documentElement);
function stop(event) {
  event.preventDefault();
  event.stopImmediatePropagation();
}
document.addEventListener('mousedown', event => {
  if (enabled) stop(event);
}, true);
document.addEventListener('pointerup', event => {
  if (!enabled || event.button !== 0) return;
  const target = targetAt(event);
  if (target) send('pick', {id: target.dataset.pliegueElement, add: event.shiftKey || event.ctrlKey || event.metaKey});
}, true);
for (const type of ['click', 'auxclick', 'contextmenu', 'submit', 'change', 'beforeinput', 'dragstart']) {
  document.addEventListener(type, event => { if (enabled) stop(event); }, true);
}
document.addEventListener('keydown', event => {
  if (!enabled) return;
  if (event.key === 'Escape') {
    stop(event);
    send('cancel');
  } else if (event.key === 'Enter' || event.key === ' ') {
    stop(event);
    const target = targetAt(event);
    if (target) send('pick', {id: target.dataset.pliegueElement, add: event.shiftKey});
  }
}, true);
send('ready');
`;
  const hash = 'sha256-617kF3crcOt4b6pX8J3IDo7auBe9ueBIox6Ex3JFe2Q=';
  const channels = new WeakMap();
  let current;
  let selection = [];
  let enabled = false;
  let adding = false;
  const trail = new Map();
  let hover = '';
  const idPattern = /^[0-9a-f]{32}$/;
  const visualStyles = '<style>html[data-pliegue-selecting],html[data-pliegue-selecting] *{cursor:crosshair!important}</style>';

  function connect(frame, manifest, render) {
    const revision = JSON.stringify(manifest.revision);
    const identity = {slug: manifest.slug, revision, session: [...crypto.getRandomValues(new Uint8Array(24))]
      .map(byte => byte.toString(16).padStart(2, '0')).join('')};
    const channel = {frame, manifest, identity};
    channels.set(frame.contentWindow, channel);
    const metadata = encodeURIComponent(JSON.stringify({...identity, origin: location.origin}));
    frame.srcdoc = render('<meta name="pliegue-selection" content="' + metadata + '">' + visualStyles,
                           runtime, hash);
    return channel;
  }

  function sync(channel, active = false) {
    if (!channel?.frame.isConnected) return;
    const own = channel === current ? selection : [];
    const ids = own.map(id => channel.manifest.elements[id].tag === 'sidebar' ? '' : id).filter(Boolean);
    const labels = Object.fromEntries([...own, hover].filter(id => channel.manifest.elements[id])
      .map(id => [id, channel.manifest.elements[id].type]));
    channel.frame.contentWindow.postMessage({...channel.identity, action: 'state',
      enabled: active, ids, labels}, '*');
  }

  const editor = document.querySelector('[data-visual-editor]');
  const card = editor?.querySelector('[data-visual-card]');
  const status = editor?.querySelector('[data-visual-status]');
  const allow = editor?.querySelector('[data-visual-allow]');
  let toolbar;
  function refresh() {
    document.querySelectorAll('[data-visual-toggle]').forEach(button => {
      const active = enabled && button.closest('[data-visual-tools]') === toolbar;
      button.setAttribute('aria-pressed', String(active));
      button.querySelector('[data-visual-toggle-label]').textContent =
        active ? 'Desactivar selección' : 'Seleccionar elemento';
    });
    document.querySelectorAll('[data-visual-mode]').forEach(indicator => {
      indicator.hidden = !enabled || indicator.closest('[data-visual-tools]') !== toolbar;
    });
    toolbar?.querySelector('[data-visual-add]').setAttribute('aria-pressed', String(adding));
    toolbar?.querySelector('[data-visual-single]').setAttribute('aria-pressed', String(!adding));
    document.querySelectorAll('[data-visual-sidebar]').forEach(node => {
      node.classList.toggle('pliegue-visual-selected', selection.includes(node.dataset.visualSidebar));
      node.classList.toggle('pliegue-visual-point', enabled && current?.manifest.elements[node.dataset.visualSidebar]?.tag === 'sidebar');
    });
    if (!card) return;
    card.hidden = !selection.length;
    card.closest('.pliegue-visual-card').hidden = card.hidden;
    editor.querySelector('[data-visual-total]').textContent =
      selection.length === 1 ? '1 elemento seleccionado' : selection.length + ' elementos seleccionados';
    if (allow) allow.closest('label').hidden = !selection.length;
    const expanded = new Map([...card.children].map(row =>
      [row.dataset.elementId, row.querySelector('details').open]));
    card.replaceChildren(...selection.map(id => {
      const record = current.manifest.elements[id];
      const row = document.createElement('li');
      const title = document.createElement('strong');
      title.textContent = record.label || record.page || record.type;
      const description = document.createElement('small');
      description.textContent = record.type + ' · ' + record.page + ' · ' + record.route + ' · ' +
        record.file + ' · ' + (record.location.length ? record.location.join('.') : record.tag) + ' · ' + id.slice(0, 8);
      const {revision} = current.manifest;
      const revisionId = revision.draft || revision.revision;
      if (revisionId != null) description.textContent += ' · Rev. ' + String(revisionId).slice(0, 8);
      const icon = document.createElement('span');
      const kind = record.chart ? 'chart' : record.tag === 'button' ? 'pointer' :
        ['p', 'h1', 'h2', 'h3', 'span', 'label'].includes(record.tag) ? 'text' : 'layers';
      icon.className = 'pliegue-visual-type pliegue-icon icon-' + kind;
      icon.setAttribute('aria-hidden', 'true');
      const copy = document.createElement('div');
      copy.append(title, description);
      const details = document.createElement('details');
      details.className = 'pliegue-selected-details';
      const summary = document.createElement('summary');
      summary.append(icon, copy);
      details.append(summary);
      details.open = expanded.get(id) ?? true;
      const parent = button('Seleccionar contenedor padre', 'layers', () => {
        const key = record.parents.at(-1);
        if (selection.includes(key)) {
          status.textContent = 'Ese contenedor ya está seleccionado.';
          return;
        }
        trail.set(key, id);
        replace(id, key, 'parent');
      });
      parent.disabled = !record.parents.length;
      const child = button('Volver al hijo', 'restore', () => {
        const key = trail.get(id);
        if (selection.includes(key)) {
          status.textContent = 'Ese elemento hijo ya está seleccionado.';
          return;
        }
        trail.delete(id);
        replace(id, key, 'child');
      });
      child.disabled = !trail.has(id);
      parent.dataset.selectionAction = 'parent';
      child.dataset.selectionAction = 'child';
      const actions = document.createElement('div');
      actions.className = 'pliegue-selection-actions';
      actions.append(parent, child, button('Quitar', 'close', () => remove(id)));
      details.append(actions);
      row.append(details);
      row.dataset.elementId = id;
      return row;
    }));
    document.querySelectorAll('[data-visual-tools]').forEach(tools => {
      const count = tools === toolbar ? selection.length : 0;
      tools.querySelector('[data-visual-count]').textContent = count ? String(count) + ' seleccionados' : '';
      tools.querySelector('[data-visual-jump]')?.toggleAttribute('hidden', !count);
    });
  }

  function button(label, iconName, action) {
    const control = document.createElement('button');
    control.type = 'button';
    const icon = document.createElement('span');
    icon.className = 'pliegue-icon icon-' + iconName;
    icon.setAttribute('aria-hidden', 'true');
    control.append(icon, label);
    control.addEventListener('click', action);
    return control;
  }

  function removeTrail(id) {
    while (trail.has(id)) {
      const child = trail.get(id);
      trail.delete(id);
      id = child;
    }
  }

  function remove(id) {
    removeTrail(id);
    replace(id);
  }

  function replace(old, next, action) {
    selection = [...new Set(selection.flatMap(id => id === old ? (next ? [next] : []) : [id]))];
    changed();
    const row = next && [...card.children].find(item => item.dataset.elementId === next);
    const control = row?.querySelector('[data-selection-action="' + action + '"]:enabled');
    (control || row?.querySelector('summary') || card.querySelector('summary') ||
      toolbar?.querySelector('[data-visual-toggle]'))?.focus({preventScroll: true});
  }

  function changed() {
    if (allow) allow.checked = false;
    if (status) status.textContent = '';
    sync(current, enabled);
    refresh();
  }

  function pick(id, add) {
    if (!current?.manifest.elements[id]) return;
    if ((add || adding) && selection.includes(id)) {
      removeTrail(id);
      selection = selection.filter(key => key !== id);
    }
    else if (!(add || adding)) {
      selection = [id];
      trail.clear();
    } else if (selection.length < 8) selection.push(id);
    else {
      status.textContent = 'Puedes seleccionar hasta 8 elementos.';
      return;
    }
    changed();
    document.dispatchEvent(new CustomEvent('pliegue:selection-picked', {
      detail: {canvas: toolbar?.hasAttribute('data-visual-main'), multiple: add || adding},
    }));
  }

  function bind(tools, channel) {
    if (!tools || !editor) return;
    tools.hidden = false;
    tools.querySelector('[data-visual-toggle]').disabled = false;
    tools.querySelector('[data-visual-toggle]').onclick = () => {
      if (current !== channel) {
        enable(false);
        selection = [];
        trail.clear();
        sync(current);
        current = channel;
      }
      toolbar = tools;
      enable(!enabled);
    };
    tools.querySelector('[data-visual-add]').onclick = () => {
      adding = !adding;
      refresh();
      if (adding && tools.hasAttribute('data-visual-main')) {
        document.dispatchEvent(new CustomEvent('pliegue:selection-mode', {detail: {canvas: true, enabled: true}}));
      }
    };
    tools.querySelector('[data-visual-single]').onclick = () => { adding = false; refresh(); };
    const jump = tools.querySelector('[data-visual-jump]');
    if (jump) jump.onclick = () => editor.querySelector('[data-visual-describe]').click();
  }

  function enable(next) {
    const changed = next !== enabled;
    enabled = next;
    if (!next) adding = false;
    hover = '';
    sync(current, enabled);
    refresh();
    if (changed) document.dispatchEvent(new CustomEvent('pliegue:selection-mode', {
      detail: {canvas: toolbar?.hasAttribute('data-visual-main'), enabled},
    }));
  }

  editor?.querySelector('[data-visual-clear]')?.addEventListener('click', () => {
    selection = [];
    trail.clear();
    changed();
    editor.querySelector('[data-visual-toggle]').focus();
  });
  document.addEventListener('keydown', event => {
    if (enabled && event.key === 'Escape') { event.preventDefault(); enable(false); }
  }, true);
  document.addEventListener('click', event => {
    const link = event.target.closest('nav.menu a, #orvia-global-sidebar a');
    if (!enabled || !link) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    if (link.dataset.visualSidebar) pick(link.dataset.visualSidebar, event.shiftKey || event.ctrlKey || event.metaKey);
    else status.textContent = 'Desactiva el modo selección para navegar a otra página.';
  }, true);
  window.addEventListener('message', event => {
    const channel = channels.get(event.source);
    const message = event.data;
    if (!channel || !channel.frame.isConnected || channel.frame.contentWindow !== event.source ||
        event.origin !== 'null' || !message || typeof message !== 'object' || Array.isArray(message) ||
        message.session !== channel.identity.session || message.slug !== channel.identity.slug ||
        message.revision !== channel.identity.revision) return;
    const size = Object.keys(message).length;
    if (message.action === 'ready' && size === 4) {
      sync(channel, channel === current && enabled);
      return;
    }
    if (channel !== current || !enabled) return;
    if (message.action === 'cancel' && size === 4) enable(false);
    if (message.action === 'hover' && size === 5 &&
        (message.id === '' || (typeof message.id === 'string' && idPattern.test(message.id) && channel.manifest.elements[message.id]))) {
      hover = message.id;
      sync(channel, true);
    }
    if (message.action === 'pick' && size === 6 && typeof message.id === 'string' &&
        idPattern.test(message.id) && typeof message.add === 'boolean' &&
        channel.manifest.elements[message.id]?.tag !== 'sidebar') pick(message.id, message.add);
  });

  window.pliegueVisual = {
    connect, bind, deactivate: () => enable(false),
    detach(channel) {
      if (!channel) return;
      channels.delete(channel.frame.contentWindow);
      if (current === channel) enable(false);
    },
    payload() {
      if (!selection.length) return {};
      const {slug, revision, elements} = current.manifest;
      return {selection: {slug, revision, refs: selection.map(id => elements[id].ref)}, allow_behavior: allow.checked};
    },
  };
})();
