(() => {
  const labels = {
    web: ['↗', 'Ruta web'], sidebar: ['☰', 'Navegación'], page: ['▤', 'Página aprobada'],
    component: ['◇', 'Componente'], file: ['▧', 'Archivo'], service: ['⬡', 'Microservicio'],
    endpoint: ['⇄', 'Endpoint']
  };
  const searchKey = text => text.normalize('NFD').replace(/\p{M}/gu, '').toLocaleLowerCase('es');
  function element(tag, className, text = '') {
    const node = document.createElement(tag);
    node.className = className;
    node.textContent = text;
    return node;
  }

  // Replica el ajuste de línea del textarea para ubicar el selector en el cursor.
  function caret(input) {
    const box = input.getBoundingClientRect();
    const styles = getComputedStyle(input);
    const mirror = element('div', 'pliegue-caret-mirror');
    for (const name of ['font', 'letterSpacing', 'lineHeight', 'textIndent', 'tabSize', 'padding', 'border',
      'boxSizing', 'direction', 'textAlign']) mirror.style[name] = styles[name];
    mirror.style.width = `${input.clientWidth + parseFloat(styles.borderLeftWidth) + parseFloat(styles.borderRightWidth)}px`;
    mirror.textContent = input.value.slice(0, input.selectionStart);
    const marker = element('span', '', input.value.slice(input.selectionStart) || '\u200b');
    mirror.append(marker);
    document.body.append(mirror);
    const point = marker.getClientRects()[0];
    const origin = mirror.getBoundingClientRect();
    mirror.remove();
    if (!point) return new DOMRect(box.left, box.top, 0, 20);
    return new DOMRect(Math.max(box.left, Math.min(box.right, box.left + point.left - origin.left - input.scrollLeft)),
      Math.max(box.top, Math.min(box.bottom, box.top + point.top - origin.top - input.scrollTop)), 0, point.height);
  }

  window.pliegueMentions = function attach(input, endpoint) {
    const form = input.form;
    const chips = element('div', 'pliegue-mention-chips');
    chips.setAttribute('aria-label', 'Referencias del mensaje');
    input.before(chips);
    const popup = element('div', 'pliegue-mention-popup');
    const options = element('div', 'pliegue-mention-list');
    options.id = 'pliegue-mention-options';
    options.setAttribute('role', 'listbox');
    options.setAttribute('aria-label', 'Referencias de Orvia');
    const status = element('div', 'pliegue-mention-status');
    status.setAttribute('role', 'status');
    popup.append(status, options);
    form.append(popup);
    popup.hidden = true;
    input.setAttribute('aria-controls', options.id);
    input.setAttribute('aria-autocomplete', 'list');
    const items = [];
    let choices = [];
    let active = 0;
    let current;
    let dismissed;
    let request;
    let catalog;
    let failed;
    let exploring;
    let flag;
    const path = location.pathname;

    function token() {
      if (input.selectionStart !== input.selectionEnd) return null;
      const end = input.selectionStart;
      const match = input.value.slice(0, end).match(/(?:^|\s)(?:@([\p{L}\p{N}_.-]*)|\/([\p{L}\p{N}_-]*))$/u);
      if (!match || (input.value[end] && !/\s|[.,;!?)]/.test(input.value[end]))) return null;
      const query = match[1] ?? match[2];
      return {trigger: match[1] === undefined ? '/' : '@', query, start: end - query.length - 1, end};
    }

    function position() {
      if (popup.hidden) return;
      const point = caret(input);
      const viewport = window.visualViewport;
      const left = viewport?.offsetLeft || 0;
      const top = viewport?.offsetTop || 0;
      const right = left + (viewport?.width || document.documentElement.clientWidth);
      const bottom = top + (viewport?.height || innerHeight);
      const width = Math.min(370, right - left - 16);
      const above = Math.max(0, point.top - top - 12);
      const below = Math.max(0, bottom - point.bottom - 12);
      const up = below < 230 && above > below;
      popup.style.width = `${width}px`;
      popup.style.left = `${Math.max(left + 8, Math.min(point.left, right - width - 8))}px`;
      popup.style.maxHeight = `${Math.min(295, up ? above : below)}px`;
      popup.style.top = `${up ? point.top - popup.offsetHeight - 6 : point.bottom + 6}px`;
    }

    function close() {
      popup.hidden = true;
      input.removeAttribute('aria-activedescendant');
    }

    function renderChips() {
      chips.replaceChildren(...items.map(item => {
        const chip = element('span', 'pliegue-mention-chip');
        chip.append(element('span', '', item.label));
        if (item.kind === 'service') {
          const browse = element('button', '', '›');
          browse.type = 'button';
          browse.setAttribute('aria-label', `Explorar endpoints de /${item.service}`);
          browse.addEventListener('click', () => {
            input.focus();
            const cursor = input.selectionStart;
            current = {trigger: '/', query: '', start: cursor, end: cursor, fromChip: true};
            exploring = item.service;
            loadCatalog();
            render();
          });
          chip.append(browse);
        }
        const remove = element('button', '', '×');
        remove.type = 'button';
        remove.setAttribute('aria-label', `Quitar ${item.label}`);
        remove.addEventListener('click', () => {
          items.splice(items.indexOf(item), 1);
          renderChips();
          input.focus();
        });
        chip.append(remove);
        return chip;
      }));
    }

    function highlight(index) {
      active = index;
      [...options.children].forEach((option, i) => option.setAttribute('aria-selected', String(i === active)));
      const option = options.children[active];
      if (!option) return;
      input.setAttribute('aria-activedescendant', option.id);
      if (option.offsetTop < popup.scrollTop) popup.scrollTop = option.offsetTop;
      else if (option.offsetTop + option.offsetHeight > popup.scrollTop + popup.clientHeight) {
        popup.scrollTop = option.offsetTop + option.offsetHeight - popup.clientHeight;
      }
    }

    function select(choice) {
      if (!choice || !current) return;
      if (choice.explore) {
        exploring = choice.item.service;
        render();
        input.focus();
        return;
      }
      if (items.length >= 8) return;
      const actual = token();
      if (!current.fromChip && (!actual || actual.start !== current.start || actual.end !== current.end)) return;
      const {item} = choice;
      items.push(item);
      const {start, end} = current;
      if (!current.fromChip) input.setRangeText('', start, end, 'end');
      renderChips();
      current = null;
      exploring = null;
      flag = null;
      close();
      input.focus();
    }

    function render() {
      if (!current) return close();
      const query = searchKey(current.query);
      const already = new Set(items.map(item => item.id));
      const list = (catalog || []).filter(item => {
        if (exploring) return item.kind === 'endpoint' && item.service === exploring;
        if (current.trigger === '/') return item.kind === 'service' && searchKey(item.label).startsWith(query);
        return !['service', 'endpoint'].includes(item.kind) &&
          searchKey(`${item.label} ${item.detail} ${item.description}`).includes(query);
      });
      if (current.trigger === '/' && query && catalog && !exploring && !list.length) return close();
      if (current.trigger === '@' && !query) {
        const rank = ['sidebar', 'page', 'component', 'web', 'file'];
        list.sort((a, b) => rank.indexOf(a.kind) - rank.indexOf(b.kind));
      }
      choices = [];
      if (items.length < 8) {
        for (const item of list) {
          if (!already.has(item.id)) choices.push({item});
          if (item.kind === 'service') choices.push({item, explore: true});
          if (!exploring && choices.length >= 16) break;
        }
      }
      input.removeAttribute('aria-activedescendant');
      status.textContent = failed ? 'No se pudo cargar el catálogo. Vuelve a escribir @ o / para reintentar.' :
        !catalog ? 'Cargando referencias…' : items.length >= 8 ? 'Puedes adjuntar hasta ocho referencias.' :
        !choices.length ? 'No hay referencias disponibles.' : exploring ? `Endpoints de /${exploring}` : '';
      status.hidden = !status.textContent;
      options.replaceChildren(...choices.map((choice, index) => {
        const {item, explore} = choice;
        const [symbol, type] = labels[item.kind];
        const option = element('div', 'pliegue-mention-option');
        option.id = `pliegue-mention-option-${index}`;
        option.setAttribute('role', 'option');
        option.append(element('span', 'pliegue-mention-icon', explore ? '›' : symbol));
        const text = element('span', 'pliegue-mention-text');
        text.append(element('strong', '', explore ? `Explorar endpoints de /${item.service}` : item.label),
          element('small', '', explore ? item.detail : `${type} · ${item.detail}`));
        if (!explore && item.description !== type) text.append(element('small', '', item.description));
        option.append(text);
        option.addEventListener('mousedown', event => event.preventDefault());
        option.addEventListener('click', () => select(choice));
        return option;
      }));
      popup.hidden = false;
      popup.scrollTop = 0;
      highlight(0);
      position();
    }

    function loadCatalog() {
      catalog = null;
      failed = false;
      request?.abort();
      const controller = new AbortController();
      request = controller;
      const url = new URL(endpoint, location.href);
      url.searchParams.set('path', path);
      fetch(url, {signal: controller.signal, cache: 'no-store'}).then(response => {
        if (!response.ok) throw new Error('Catálogo no disponible');
        return response.json();
      }).then(data => {
        if (request !== controller) return;
        catalog = data.items;
        render();
      }).catch(() => {
        if (request !== controller || controller.signal.aborted) return;
        failed = true;
        render();
      });
    }

    function update() {
      const next = token();
      const key = next && `${next.start}:${next.trigger}`;
      const signature = next && `${key}:${next.query}`;
      if (next && signature === dismissed) return close();
      if (!next) {
        current = null;
        flag = null;
        dismissed = null;
        exploring = null;
        close();
        return;
      }
      if (current?.query !== next.query || flag !== key) exploring = null;
      current = next;
      if (flag !== key) {
        flag = key;
        loadCatalog();
      }
      render();
    }

    input.addEventListener('input', event => {
      if (!event.isComposing) update();
    });
    input.addEventListener('compositionend', update);
    input.addEventListener('click', update);
    input.addEventListener('blur', event => {
      if (popup.contains(event.relatedTarget)) return;
      current = null;
      close();
    });
    document.addEventListener('pointerdown', event => {
      if (event.target !== input && !popup.contains(event.target)) {
        current = null;
        close();
      }
    });
    input.addEventListener('scroll', position);
    window.addEventListener('resize', position);
    window.visualViewport?.addEventListener('resize', position);
    input.addEventListener('keydown', event => {
      if (event.isComposing) return;
      if (popup.hidden) return;
      if (event.key === 'Escape') {
        dismissed = `${flag}:${current.query}`;
        close();
      } else if (choices.length && ['ArrowDown', 'ArrowUp'].includes(event.key)) {
        highlight((active + (event.key === 'ArrowDown' ? 1 : -1) + choices.length) % choices.length);
      } else if (choices.length && event.key === 'Enter' && !event.shiftKey) {
        select(choices[active]);
      } else if (choices[active]?.item.kind === 'service' && event.key === 'ArrowRight') {
        select({...choices[active], explore: true});
      } else return;
      event.preventDefault();
      event.stopPropagation();
    });
    input.addEventListener('keyup', event => {
      if (['Home', 'End', 'ArrowLeft', 'ArrowRight'].includes(event.key) && !exploring) update();
    });
    return {
      payload() {
        return items.length ? {mentions: items.map(({id, revision}) => ({id, revision})), mention_page: path} : {};
      },
      clear() {
        items.length = 0;
        current = null;
        exploring = null;
        flag = null;
        renderChips();
        close();
      }
    };
  };
})();
