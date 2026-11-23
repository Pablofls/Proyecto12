(() => {
  // El hash autoriza únicamente este código fijo. El iframe tiene origen opaco.
  const pageRuntime = `'use strict';
function formResult(form) {
  return form && Element.prototype.querySelector.call(form, '[data-form-result]');
}
function validateDemo(form) {
  const result = formResult(form);
  if (result && HTMLFormElement.prototype.reportValidity.call(form)) {
    result.textContent = Element.prototype.getAttribute.call(form, 'data-success-message')
      || 'Validación correcta. Demostración completada.';
  }
}
document.addEventListener('submit', event => event.preventDefault());
document.addEventListener('keydown', event => {
  if (event.defaultPrevented || event.key !== 'Enter' || event.isComposing || !event.target.matches('input:not([type="checkbox"]):not([type="radio"]):not([type="range"])')) return;
  const form = event.target.closest('form');
  if (!form) return;
  const button = Element.prototype.querySelector.call(form, 'button[type="submit"]:enabled');
  if (!button) return;
  event.preventDefault();
  validateDemo(form);
});
function applyFilter(control) {
  document.querySelectorAll('[data-group][data-value]').forEach(item => {
    if (item.dataset.group === control.dataset.filter) {
      item.hidden = control.value !== '' && control.value !== item.dataset.value;
    }
  });
}
document.addEventListener('change', event => {
  if (event.target.matches('select[data-filter]')) applyFilter(event.target);
});
document.querySelectorAll('select[data-filter]').forEach(control => {
  if (control.value !== '') applyFilter(control);
});
document.addEventListener('click', event => {
  const anchor = event.target.closest('a[href]');
  if (anchor) {
    event.preventDefault();
    document.getElementById(anchor.hash.slice(1))?.scrollIntoView({block: 'nearest'});
    return;
  }
  const button = event.target.closest('button');
  if (!button || button.disabled) return;
  if (button.type === 'submit' && button.closest('form')) {
    event.preventDefault();
    validateDemo(button.closest('form'));
    return;
  }
  if (button.type !== 'button') return;
  const tabs = button.closest('[data-tabs]');
  if (tabs && button.hasAttribute('data-tab')) {
    tabs.querySelectorAll('[data-panel]').forEach(panel => {
      if (panel.closest('[data-tabs]') === tabs) panel.hidden = panel.dataset.panel !== button.dataset.tab;
    });
    tabs.querySelectorAll('button[data-tab]').forEach(tab => {
      if (tab.closest('[data-tabs]') === tabs) tab.setAttribute('aria-pressed', String(tab === button));
    });
  }
  const dialog = document.getElementById(button.dataset.open || '');
  if (dialog instanceof HTMLDialogElement && !dialog.open) dialog.showModal();
  if (button.hasAttribute('data-close')) button.closest('dialog')?.close();
});
document.addEventListener('invalid', event => {
  const result = formResult(event.target.closest('form'));
  if (result) result.textContent = 'Corrige los campos marcados antes de continuar.';
}, true);

const tableCollator = new Intl.Collator('es', {numeric: true, sensitivity: 'base'});
const searchable = text => Array.from(text.toLocaleLowerCase('es').normalize('NFD'))
  .filter(mark => mark.codePointAt(0) < 0x0300 || mark.codePointAt(0) > 0x036f).join('');
document.querySelectorAll('table[data-interactive-table]').forEach(table => {
  const rows = Array.from(table.tBodies[0].rows);
  const headers = Array.from(table.tHead.rows[0].cells);
  const label = document.createElement('label');
  const search = document.createElement('input');
  search.type = 'search';
  const clear = document.createElement('button');
  clear.type = 'button';
  clear.textContent = 'Limpiar búsqueda';
  const status = document.createElement('p');
  status.setAttribute('role', 'status');
  label.append(table.dataset.interactiveTable + ' ', search);
  const captionName = table.caption?.textContent.trim();
  if (captionName && !table.hasAttribute('aria-label') && !table.hasAttribute('aria-labelledby')) {
    table.setAttribute('aria-label', captionName);
  }
  (table.caption || table.createCaption()).append(label, clear, status);
  search.addEventListener('keydown', event => {
    if (event.key === 'Enter') event.preventDefault();
  });
  function updateResults() {
    const query = searchable(search.value.trim());
    let visible = 0;
    rows.forEach(row => {
      const matches = Array.from(row.cells).some(cell => searchable(cell.textContent).includes(query));
      row.toggleAttribute('data-pliegue-table-filtered', !matches);
      if (matches && !row.hidden) visible++;
    });
    status.textContent = visible + ' de ' + rows.length + ' registros' +
      (visible ? '' : '. Sin resultados.');
  }
  search.addEventListener('input', updateResults);
  clear.addEventListener('click', () => {
    search.value = '';
    updateResults();
    search.focus();
  });
  const groups = new Set(rows.filter(row => row.hasAttribute('data-value')).map(row => row.dataset.group));
  document.addEventListener('change', event => {
    const control = event.target;
    if (control.matches('select[data-filter]') && groups.has(control.dataset.filter)) updateResults();
  });
  updateResults();
  headers.forEach((header, column) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = header.textContent;
    header.replaceChildren(button);
    button.addEventListener('click', () => {
      const descending = header.getAttribute('aria-sort') === 'ascending';
      headers.forEach(cell => cell.removeAttribute('aria-sort'));
      header.setAttribute('aria-sort', descending ? 'descending' : 'ascending');
      const ordered = [...rows].sort((a, b) => (descending ? -1 : 1) *
        tableCollator.compare(a.cells[column].textContent.trim(), b.cells[column].textContent.trim()));
      table.tBodies[0].append(...ordered);
    });
  });
});
`;
  const runtimeHash = 'sha256-U1h6wKj+4i7LLCNR/z7UH4RpNL1/XCOYzAtkymCFCYE=';
  const pageStyles = '<style>:where(body){font:16px system-ui,sans-serif;margin:0;padding:1rem;color:#102a25;background:#f2f8f5}' +
    ':where(.orvia-chart){margin:0;padding:1rem;border:1px solid #c9ddd5;border-radius:1rem;background:white}' +
    ':where(.orvia-chart small){display:block}:where(.orvia-plot svg){display:block;width:100%;max-height:240px}' +
    ':where(table[data-interactive-table] caption label){display:block}' +
    '[hidden],[data-pliegue-table-filtered]{display:none!important}</style>';

  function previewDocument(markup, builder = false, interactive = builder, visual) {
    const scripts = interactive ? `'${runtimeHash}'${visual ? ` '${visual.hash}'` : ''}` : "'none'";
    const policy = "default-src 'none'; connect-src 'none'; style-src 'unsafe-inline'; img-src data:; " +
      "base-uri 'none'; form-action 'none'; script-src " + scripts;
    return '<!doctype html><html lang="es"><head><meta charset="utf-8">' +
      `<meta http-equiv="Content-Security-Policy" content="${policy}">` +
      '<meta name="referrer" content="no-referrer">' +
      '<meta name="viewport" content="width=device-width, initial-scale=1">' +
      (builder ? pageStyles : '') + (visual?.head || '') + '</head>' + markup +
      (interactive ? '<script>' + pageRuntime + '</script>' : '') +
      (visual ? '<script>' + visual.runtime + '</script>' : '') + '</html>';
  }

  const visualEditor = window.pliegueVisual;
  document.querySelectorAll('iframe[data-pliegue-page]').forEach(frame => {
    if (visualEditor && frame.dataset.visualManifest) {
      const channel = visualEditor.connect(frame, JSON.parse(frame.dataset.visualManifest),
        (head, runtime, hash) => previewDocument(frame.dataset.plieguePage, true, true, {head, runtime, hash}));
      visualEditor.bind(document.querySelector("[data-visual-main]") || frame.previousElementSibling, channel);
    } else {
      frame.srcdoc = previewDocument(frame.dataset.plieguePage, true);
    }
  });

  const page = document.getElementById('pliegue-codigo');
  if (!page) return;

  const find = selector => page.querySelector(selector);
  const form = find('form');
  const submit = form.querySelector('[type=submit]');
  const input = form.querySelector('textarea');
  let mode = 'edit';
  const modeButtons = form.querySelectorAll('[data-request-mode]');
  modeButtons.forEach(button => button.addEventListener('click', () => {
    const nextMode = button.dataset.requestMode;
    if (mode !== nextMode) setContinuation(null);
    mode = nextMode;
    modeButtons.forEach(option => option.setAttribute('aria-pressed', String(option === button)));
  }));
  const mentions = page.dataset.mentions && window.pliegueMentions?.(input, page.dataset.mentions);
  find('[data-visual-describe]')?.addEventListener('click', () => {
    visualEditor?.deactivate();
    input.focus();
  });
  const list = find('#pliegue-codigo-lista');
  const feedback = find('#pliegue-codigo-feedback');
  const worker = document.getElementById('pliegue-codigo-worker');
  const article = find('article');
  const welcome = find('[data-welcome]');
  const thread = find('.pliegue-thread');
  const review = find('[data-job-review]');
  const preview = find('[data-job-preview]');
  const frame = preview.querySelector('iframe');
  const comparisonButton = find('[data-comparison-open]');
  const comparison = find('.pliegue-comparison');
  const panes = comparison.querySelector('.pliegue-comparison-panes');
  const comparisonFrames = panes.querySelectorAll('iframe');
  let comparisonRequest;
  let draftChannel;
  let draftSelectionRequest;
  const draftSelection = find('[data-visual-draft]');
  const draftTools = comparison.querySelector('[data-visual-tools]');
  const draftCompose = find('[data-visual-compose]');

  function clearDraftSelection() {
    draftSelectionRequest?.abort();
    if (draftSelection) draftSelection.hidden = true;
    if (draftCompose) draftCompose.hidden = true;
    if (draftTools) draftTools.hidden = true;
    visualEditor?.detach(draftChannel);
    draftChannel = null;
  }

  draftCompose?.addEventListener('click', () => {
    closeComparison();
    input.focus();
  });
  const versionPanel = find('[data-version-panel]');
  const viewActive = find('[data-version-view]');
  const undo = find('[data-version-undo]');
  const redo = find('[data-version-redo]');
  const approve = find('[data-job-approve]');
  const continueDraft = find('[data-job-continue]');
  const reject = find('[data-job-reject]');
  // Orden UX: primero comparar, después aceptar/rechazar, finalmente deshacer.
  const resultActions = find('article .pliegue-result > .pliegue-actions');
  if (resultActions) {
    review.after(resultActions);
    resultActions.after(versionPanel);
  }
  const pairSection = document.createElement('section');
  pairSection.className = 'pliegue-code-pair-v7';
  pairSection.setAttribute('aria-label', 'Antes y después del código');
  pairSection.innerHTML = '<div class="pliegue-code-pair-head"><strong>Antes / Después</strong><small>Fragmentos del código modificado · no son datos PostgreSQL</small></div>' +
    '<div class="pliegue-code-pair-cols"><div><b>ANTES</b><pre data-code-before tabindex="0"></pre></div>' +
    '<div><b>DESPUÉS</b><pre data-code-after tabindex="0"></pre></div></div>';
  review.prepend(pairSection);
  function renderSourcePair(job) {
    const diff = job && typeof job.diff === 'string' ? job.diff : '';
    pairSection.hidden = job?.mode === 'consult' || !job?.changed;
    if (pairSection.hidden) return;
    const before = [], after = [];
    for (const line of diff.split('\n')) {
      if (line.startsWith('---') || line.startsWith('+++')) continue;
      if (line.startsWith('Archivo "') || line.startsWith('@@')) {
        before.push(line); after.push(line);
      } else if (line.startsWith('-')) before.push(line.slice(1));
      else if (line.startsWith('+')) after.push(line.slice(1));
      else { before.push(line.startsWith(' ') ? line.slice(1) : line);
             after.push(line.startsWith(' ') ? line.slice(1) : line); }
    }
    pairSection.querySelector('[data-code-before]').textContent = before.join('\n') || 'Sin fragmentos disponibles';
    pairSection.querySelector('[data-code-after]').textContent = after.join('\n') || 'Sin fragmentos disponibles';
    const title = pairSection.querySelector('small');
    title.textContent = job.diff_truncated
      ? 'Diferencias incompletas: aprobación bloqueada por el worker'
      : 'Fragmentos de código. Para cambios de pantalla, abre la comparación visual aislada.';
  }
  const decision = find('.pliegue-decision');
  const confirm = find('[data-decision-confirm]');
  const cancel = find('[data-decision-cancel]');
  const warningsCheck = find('[data-decision-warnings] input');
  const reason = find('[data-decision-reason] textarea');
  const csrfHeaders = {'Content-Type': 'application/json', 'X-Pliegue-CSRF': page.dataset.csrf};
  let reviewed;
  let currentJob;
  let continuation = null;
  let currentRevision;
  let pendingDecision;
  let decisionBusy = false;
  const states = {
    queued: 'Borrador pendiente', editing: 'Codex está editando', testing: 'Ejecutando pruebas',
    ready: 'Listo para revisar', failed: 'Error al procesar', tests_failed: 'Pruebas fallidas',
    answered: 'Consulta respondida', approved: 'Aprobado', rejected: 'Rechazado', reverted: 'Revertido',
    cancelled: 'Solicitud detenida'
  };
  function stateLabel(job) {
    if (job.cancelling) return 'Deteniendo solicitud';
    if (job.mode === 'consult' && job.state === 'queued') return 'Consulta pendiente';
    if (job.mode === 'consult' && job.state === 'editing') return 'Codex está consultando';
    return states[job.state] || job.state;
  }

  const active = new Set(['queued', 'editing', 'testing']);
  const date = new Intl.DateTimeFormat('es-MX', {dateStyle: 'short', timeStyle: 'short'});
  const historyKey = 'pliegue.selected-job';
  let selected = null;
  let remembered = null;
  try { remembered = sessionStorage.getItem(historyKey); } catch {}
  function rememberSelection(id) {
    try {
      if (id) sessionStorage.setItem(historyKey, id);
      else sessionStorage.removeItem(historyKey);
    } catch {}
  }
  let rendered = '';
  let previousList = '';
  let drafts = [];
  const historySearch = find('#pliegue-codigo-buscar');
  const historyResults = find('[data-history-results]');
  let previousJob = '';
  let sequence = 0;
  let timer;
  let connected = false;
  let posting = false;
  let pendingSubmission;
  let postError = '';
  let refreshError = '';

  function renderHistory() {
    const query = historySearch.value.trim().toLocaleLowerCase('es');
    const options = [new Option('Nueva solicitud', '')];
    const groups = new Map();
    let matches = 0;
    for (const draft of drafts) {
      const timestamp = new Date(draft.created_at);
      const when = Number.isNaN(timestamp.getTime()) ? '' : date.format(timestamp) + ' · ';
      const state = stateLabel(draft);
      const warnings = draft.warnings?.length ? ' · Con advertencias' : '';
      const title = draft.conversation?.title || '';
      const matched = (when + state + warnings + ' ' + title + ' ' + draft.message)
        .toLocaleLowerCase('es').includes(query);
      if (matched) matches++;
      if (matched || draft.id === selected) {
        const option = new Option(when + state + warnings + ' · ' + draft.message.slice(0, 90) +
          (matched ? '' : ' · Solicitud abierta'), draft.id);
        if (draft.conversation) {
          const id = draft.conversation.id;
          if (!groups.has(id)) {
            const group = document.createElement('optgroup');
            group.label = title;
            groups.set(id, group);
            options.push(group);
          }
          groups.get(id).append(option);
        } else {
          options.push(option);
        }
      }
    }
    historyResults.textContent = query ? (matches ? matches + ' coincidencias' : 'Sin coincidencias') : '';
    list.replaceChildren(...options);
    list.value = selected;
  }
  historySearch.addEventListener('input', renderHistory);

  function updateComposer() {
    submit.disabled = !connected || posting || readingFiles;
    submit.querySelector('[data-submit-label]').textContent = posting ? 'Enviando…' :
      continuation ? (mode === 'consult' ? 'Enviar seguimiento' : 'Enviar corrección') : 'Enviar solicitud';
    const message = postError || refreshError;
    feedback.hidden = !message;
    if (feedback.textContent !== message) feedback.textContent = message;
  }

  function setContinuation(id) {
    continuation = id;
    continueDraft.setAttribute('aria-pressed', String(Boolean(id)));
    updateComposer();
  }

  continueDraft.addEventListener('click', () => {
    const next = continuation ? null : currentJob.id;
    const kind = currentJob.mode === 'consult' ? 'consult' : 'edit';
    modeButtons.forEach(button => {
      if (button.dataset.requestMode === kind) button.click();
    });
    setContinuation(next);
    input.focus();
  });

  async function request(url, options) {
    const response = await fetch(url, {cache: 'no-store', ...options});
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || 'No se pudo consultar Pliegue.');
    return data;
  }

  async function submissionId(body) {
    if (pendingSubmission?.body === body) return pendingSubmission.id;
    let signature;
    try {
      const bytes = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(body));
      signature = Array.from(new Uint8Array(bytes)).join(',');
      const saved = JSON.parse(sessionStorage.getItem('pliegue.pending-send') || 'null');
      if (saved?.signature === signature && /^[a-f0-9]{32}$/.test(saved.id)) {
        pendingSubmission = {body, id: saved.id};
        return saved.id;
      }
    } catch {}
    const id = Array.from(crypto.getRandomValues(new Uint8Array(16)),
      byte => byte.toString(16).padStart(2, '0')).join('');
    pendingSubmission = {body, id};
    if (signature) {
      try { sessionStorage.setItem('pliegue.pending-send', JSON.stringify({signature, id})); } catch {}
    }
    return id;
  }

  const stopJob = find('[data-job-stop]');
  stopJob.addEventListener('click', async () => {
    const id = currentJob?.id;
    if (!id || stopJob.disabled) return;
    const restoreFocus = document.activeElement === stopJob;
    stopJob.disabled = true;
    try {
      await request(`${page.dataset.drafts}/${id}/cancel`, {method: 'POST', headers: csrfHeaders});
      if (restoreFocus && currentJob?.id === id && [stopJob, document.body].includes(document.activeElement)) {
        input.focus();
      }
    } catch (error) {
      postError = error.message;
      updateComposer();
    }
    if (currentJob?.id === id) stopJob.disabled = false;
    refresh();
  });

  function output(run) {
    return run.timed_out ? 'Tiempo agotado' : `Código de salida ${run.exit_code}`;
  }

  function setText(selector, value) {
    const element = find(selector);
    if (element.textContent !== value) element.textContent = value;
    element.hidden = !value;
  }

  function setAnswer(selector, value) {
    const element = find(selector);
    const content = document.createDocumentFragment();
    let offset = 0;
    for (const match of value.matchAll(/(?<![\\`])`([^`\n]+)`(?!`)|(?<![\\*])\*\*([^*\n]+)\*\*(?!\*)/g)) {
      content.append(value.slice(offset, match.index));
      const segment = document.createElement(match[1] ? 'code' : 'strong');
      segment.textContent = match[1] || match[2];
      content.append(segment);
      offset = match.index + match[0].length;
    }
    content.append(value.slice(offset));
    element.replaceChildren(content);
    element.hidden = !value;
  }

  function showDiff(job) {
    const files = document.createDocumentFragment();
    const lines = document.createDocumentFragment();
    const visible = new Set();
    const changes = new Map((job.files || []).map(file => [file.path, file.change]));
    const diff = job.diff || (job.changed === 0 ? 'Sin cambios.' : 'Diferencias pendientes.');
    for (const line of diff.split('\n')) {
      const row = document.createElement('span');
      row.textContent = line + '\n';
      if (line.startsWith('Archivo "')) {
        try {
          const name = JSON.parse(line.slice(8));
          const file = document.createElement('li');
          const change = changes.get(name);
          file.textContent = change ? `${name} · ${change}` : name;
          files.append(file);
          visible.add(name);
        } catch {
          // Un encabezado puede quedar incompleto al truncarse el diff.
        }
        row.className = 'diff-file';
      } else if (line.startsWith('@@')) row.className = 'diff-hunk';
      else if (line.startsWith('+++') || line.startsWith('---')) row.className = 'diff-hunk';
      else if (line.startsWith('+')) row.className = 'diff-add';
      else if (line.startsWith('-')) row.className = 'diff-remove';
      lines.append(row);
    }
    if (job.diff_truncated) lines.append('[Diferencias truncadas por el worker]');
    find('[data-job-file-list]').replaceChildren(files);
    find('[data-job-diff]').replaceChildren(lines);
    const count = job.changed ?? visible.size;
    setText('[data-job-files]', `Archivos del borrador · ${count}`);
  }

  function render(job) {
    const serialized = JSON.stringify(job);
    if (serialized === previousJob) return;
    previousJob = serialized;
    currentJob = job;
    if (reviewed?.id !== job.id || reviewed?.url !== job.comparison_url || !job.can_approve) reviewed = null;
    approve.hidden = !job.can_approve;
    approve.disabled = !reviewed;
    continueDraft.hidden = !job.can_continue;
    continueDraft.textContent = job.mode === 'consult' ? 'Continuar conversación' : 'Continuar borrador';
    if (continuation && (continuation !== job.id || !job.can_continue)) setContinuation(null);
    reject.hidden = !job.can_reject;
    setText('[data-approval-reason]', job.approval_reason ||
      (job.can_approve && !reviewed ? 'Abre la comparación para habilitar la aprobación.' : ''));
    const audit = job.decision;
    setText('[data-job-decision]', audit ? [
      audit.revision && `Revisión ${audit.revision}`,
      job.targets?.length && job.state !== 'rejected' ?
        `Selección verificada · ${job.targets.map(target => target.type).join(', ')}` : audit.reason,
      audit.reverted_by || audit.owner, date.format(new Date(audit.reverted_at || audit.at))
    ].filter(Boolean).join(' · ') : '');
    const changedSelection = rendered !== job.id;
    if (changedSelection) {
      rendered = job.id;
      frame.removeAttribute('src');
      review.querySelectorAll('details').forEach(details => { details.open = false; });
      thread.scrollTop = 0;
    }
    const timestamp = new Date(job.created_at);
    const time = find('[data-job-date]');
    time.hidden = Number.isNaN(timestamp.getTime());
    if (!time.hidden) {
      time.dateTime = timestamp.toISOString();
      time.textContent = date.format(timestamp);
    }
    setText('[data-job-message]', [job.message, ...(job.attachments || []).map(file =>
      `Adjunto · ${file.name} · ${file.bytes} B`), ...(job.mentions || []).map(item =>
      `${item.kind === 'service' ? '/' : item.kind === 'endpoint' ? '' : '@'}${item.label}`)].join('\n'));
    const state = find('[data-job-state]');
    state.dataset.state = job.state;
    setText('[data-job-state]', stateLabel(job));
    stopJob.hidden = !active.has(job.state);
    stopJob.disabled = Boolean(job.cancelling);
    const progress = active.has(job.state) ? job.progress || [] : [];
    const notice = progress.filter(event => event.kind !== 'text').at(-1);
    const generated = progress.filter(event => event.kind === 'text').at(-1);
    setText('[data-job-progress]', notice?.text || '');
    const noChangeReport = job.changed === 0 && job.codex?.output;
    const answer = (generated?.text || job.codex?.output || '').trim();
    const breakAt = answer.search(/\n\s*\n/);
    const end = breakAt > 0 && breakAt < 360 ? breakAt :
      answer.length > 360 ? answer.lastIndexOf(' ', 300) : answer.length;
    const split = end > 0 ? end : 300;
    const details = find('[data-answer-details]');
    const rest = job.error && !noChangeReport ? answer : answer.slice(split).trim();
    details.hidden = !rest;
    setAnswer('[data-answer-rest]', rest);
    const summary = answer.slice(0, split).trim() + (rest && end !== breakAt ? '…' : '');
    setAnswer('[data-job-summary]', job.error ? [job.error, noChangeReport && summary].filter(Boolean).join('\n') :
      summary || (job.state === 'ready' ? 'Revisa las diferencias y los resultados de pruebas.' : ''));
    refreshVoice();
    if (voiceJob === job.id && !active.has(job.state) && job.state !== 'cancelled') {
      voiceJob = null;
      speakSummary();
    }
    const warnings = find('[data-job-warnings]');
    warnings.hidden = !job.warnings?.length;
    warnings.querySelector('ul').replaceChildren(...(job.warnings || []).map(message => {
      const item = document.createElement('li');
      item.textContent = message;
      return item;
    }));
    review.hidden = job.mode === "consult" || !job.diff && job.changed == null && !job.codex && !job.tests;
    showDiff(job);
    renderSourcePair(job);
    const pages = job.visual_preview?.pages || [];
    const pageDetails = find('[data-job-pages]');
    pageDetails.hidden = !pages.length;
    pageDetails.querySelector('ul').replaceChildren(...pages.map(item => {
      const row = document.createElement('li');
      const charts = item.charts.map(chart =>
        `${chart.title}: ${chart.x} × ${chart.y} · ${chart.color}${chart.group ? ` · ${chart.group}` : ''}`);
      const interactions = {details: 'desplegables', form: 'validación local', dialog: 'modal',
        'data-filter': 'filtros', 'data-tab': 'pestañas'};
      row.textContent = [`${item.icon} ${item.sidebar} · ${item.route}`,
        ...(item.static ? ['Vista estática'] : item.features.map(feature => interactions[feature] || feature)),
        ...charts].join(' | ');
      return row;
    }));
    setText('[data-job-test-summary]', 'Resultados de pruebas' + (job.tests ? (job.tests.exit_code === 0 && !job.tests.timed_out ? ' · Aprobadas' : ' · Fallidas') : ''));
    setText('[data-job-tests]', job.tests ? [output(job.tests), job.tests.output].filter(Boolean).join('\n') : 'Pruebas pendientes.');
    setText('[data-job-codex]', job.codex ? [output(job.codex), job.codex.diagnostic, job.codex.output].filter(Boolean).join('\n') : 'Salida pendiente.');
    preview.hidden = !job.preview_url;
    preview.dataset.url = job.preview_url || '';
    if (preview.hidden) frame.removeAttribute('src');
    const comparisonURL = job.comparison_url || '';
    if (comparisonButton.dataset.url !== comparisonURL && comparison.open) closeComparison();
    comparisonButton.dataset.url = comparisonURL;
    comparisonButton.hidden = !comparisonURL;
    setText('[data-comparison-reason]', job.comparison_reason || '');
    welcome.hidden = true;
    article.hidden = false;
  }

  const answerDetails = find('[data-answer-details]');
  answerDetails.addEventListener('toggle', () => {
    answerDetails.querySelector('summary').textContent = answerDetails.open ? 'Menos información' : 'Más información';
  });

  preview.addEventListener('toggle', () => {
    if (!preview.open || preview.hidden || frame.hasAttribute('src')) return;
    const url = new URL(preview.dataset.url, location.href);
    if (url.origin === location.origin) frame.src = url.href;
  });

  function clearComparison() {
    comparisonRequest?.abort();
    comparisonRequest = null;
    panes.hidden = true;
    delete panes.dataset.active;
    panes.firstElementChild.hidden = false;
    panes.lastElementChild.querySelector('h3').textContent = 'DESPUÉS';
    find('[data-comparison-width]').hidden = false;
    clearDraftSelection();
    comparisonFrames.forEach(frame => frame.removeAttribute('srcdoc'));
    find('[data-comparison-pages]').hidden = true;
    find('[data-comparison-pages] select').onchange = null;
    setText('[data-comparison-navigation]', '');
  }

  function closeComparison() {
    clearComparison();
    comparison.close();
  }

  function displayScreens(screens, onVisit) {
    const label = find('[data-comparison-pages]');
    const select = label.querySelector('select');
    select.replaceChildren(...screens.map(screen => new Option(screen.title, screen.key)));
    label.hidden = screens.length < 2;
    function show() {
      const screen = screens.find(entry => entry.key === select.value);
      if (!screen) return;
      clearDraftSelection();
      comparisonFrames.forEach((frame, index) => {
        const interactive = Boolean(screen.builder && !screen.static);
        frame.setAttribute('sandbox', interactive ? 'allow-scripts' : '');
        frame.srcdoc = previewDocument(index ? screen.after : screen.before, screen.builder, interactive);
      });
      setText('[data-comparison-navigation]', screen.navigation || '');
      onVisit?.(screen.key);
    }
    select.onchange = show;
    show();
  }

  function prepareVisualComparison(slug, expected) {
    if (!draftSelection || !visualEditor) return;
    draftSelection.textContent = expected.draft ? 'Preparar selección en el borrador' : 'Preparar selección en la versión activa';
    draftSelection.hidden = false;
    draftSelection.onclick = async () => {
      draftSelection.hidden = true;
      const controller = new AbortController();
      draftSelectionRequest = controller;
      try {
        const path = '/pliegue/codex/visual/' + slug + (expected.draft ? '/' + expected.draft : '');
        const item = await request(path, {signal: controller.signal});
        if (controller.signal.aborted || !comparison.open) return;
        if (!item.selection) throw new Error(item.selection_reason || 'La vista no tiene referencias visuales compatibles.');
        if (item.selection.slug !== slug || !Object.entries(expected).every(([key, value]) =>
          item.selection.revision[key] === value)) throw new Error('La revisión cambió. Vuelve a abrir la vista.');
        draftChannel = visualEditor.connect(comparisonFrames[1], item.selection,
          (head, runtime, hash) => previewDocument(item.markup, true, true, {head, runtime, hash}));
        visualEditor.bind(draftTools, draftChannel);
        draftCompose.hidden = false;
      } catch (error) {
        if (!controller.signal.aborted) {
          setText('[data-comparison-status]', error.message);
          draftSelection.hidden = false;
        }
      }
    };
  }

  comparisonButton.addEventListener('click', async () => {
    const url = new URL(comparisonButton.dataset.url, location.href);
    if (url.origin !== location.origin || comparison.open) return;
    clearComparison();
    const controller = new AbortController();
    comparisonRequest = controller;
    const jobId = currentJob?.id;
    comparison.showModal();
    setText('[data-comparison-status]', 'Cargando la comparación…');
    try {
      const pair = await request(url, {
        method: 'POST', signal: controller.signal,
        headers: csrfHeaders,
        body: '{}'
      });
      if (comparisonRequest !== controller || !comparison.open) return;
      if (typeof pair.before !== 'string' || typeof pair.after !== 'string') {
        throw new Error('La comparación no está disponible.');
      }
      const screens = pair.panel === false ? [] : [
        {key: 'panel', title: 'Panel general', before: pair.before, after: pair.after}
      ];
      for (const [slug, item] of Object.entries(pair.pages || {})) {
        screens.push({
          key: `page:${slug}`, title: item.page.title, builder: true, static: pair.static_pages, before: item.before, after: item.after,
          navigation: `Sidebar · ANTES: ${(item.sidebar_before ? [item.icon_before, item.sidebar_before].filter(Boolean).join(' ') : 'Sin enlace')} · DESPUÉS: ${(item.sidebar_after ? [item.icon_after, item.sidebar_after].filter(Boolean).join(' ') : 'Sin enlace')} · ${item.page.route}`
        });
      }
      if (pair.functional) screens.push({
        key: 'functional', title: 'Dashboard · pruebas de contrato',
        before: pair.functional.before, after: pair.functional.after,
        navigation: pair.functional.evidence
      });
      for (const screen of pair.generic_screens || []) {
        if (!screen || typeof screen.before !== 'string' || typeof screen.after !== 'string') continue;
        screens.push({
          key: `generic:${screen.title}`,
          title: `${screen.title} · maqueta segura`,
          before: screen.before,
          after: screen.after,
          builder: false,
          interactive: false,
          navigation: 'Vista previa estática aislada · datos ficticios · sin ejecutar la ruta, JS ni PostgreSQL',
        });
      }
      if (!screens.length) throw new Error('La comparación no está disponible.');
      const visited = new Set();
      displayScreens(screens, key => {
        visited.add(key);
        if (pair.ticket && key.startsWith('page:') && pair.pages[key.slice(5)]?.sidebar_after) {
          prepareVisualComparison(key.slice(5), {draft: jobId, version: url.pathname.split('/').at(-1)});
        }
        if (pair.ticket && currentJob?.id === jobId && currentJob.can_approve) {
          if (visited.size === screens.length) {
            reviewed = {id: jobId, url: comparisonButton.dataset.url, ticket: pair.ticket};
            approve.disabled = false;
            setText('[data-approval-reason]', '');
          } else {
            setText('[data-approval-reason]', 'Recorre todas las pantallas para habilitar la aprobación.');
          }
        }
        setText('[data-comparison-status]', pair.limitation ||
          (visited.size < screens.length ? `Pantallas revisadas: ${visited.size} de ${screens.length}` : ''));
      });
      panes.hidden = false;
    } catch (error) {
      if (comparisonRequest === controller) setText('[data-comparison-status]', error.message);
    }
  });
  const widthButton = find('[data-comparison-width]');
  widthButton.addEventListener('click', () => {
    const expanded = panes.classList.toggle('pliegue-comparison-full');
    widthButton.setAttribute('aria-pressed', String(expanded));
  });
  comparison.addEventListener('keydown', event => {
    if (event.key === 'Escape') event.stopPropagation();
  });
  find('[data-comparison-close]').addEventListener('click', closeComparison);
  comparison.addEventListener('close', () => {
    if (!comparison.open) clearComparison();
  });

  function renderRevision(revision) {
    currentRevision = revision;
    versionPanel.hidden = !revision;
    viewActive.hidden = !revision?.revision;
    undo.hidden = !revision?.previous;
    redo.hidden = !revision?.redo;
    setText('[data-version-label]', revision?.revision ? `Versión activa · ${revision.revision}` :
      'La primera aprobación creará la versión activa.');
  }

  viewActive.addEventListener('click', async () => {
    if (comparison.open) return;
    clearComparison();
    const controller = new AbortController();
    comparisonRequest = controller;
    comparison.showModal();
    setText('[data-comparison-status]', 'Cargando la versión activa…');
    try {
      const result = await request(versionPanel.dataset.activeUrl, {signal: controller.signal});
      if (comparisonRequest !== controller || !comparison.open) return;
      if (typeof result.markup !== 'string') throw new Error('La vista activa no está disponible.');
      panes.dataset.active = '';
      panes.firstElementChild.hidden = true;
      panes.lastElementChild.querySelector('h3').textContent = 'ACTIVA';
      find('[data-comparison-width]').hidden = true;
      const screens = result.panel === false ? [] :
        [{key: 'panel', title: 'Panel general', before: '', after: result.markup}];
      for (const [slug, item] of Object.entries(result.pages || {})) {
        screens.push({key: `page:${slug}`, title: item.title, builder: true, before: '', after: item.markup,
          navigation: `Sidebar · ${item.sidebar} · ${item.route}`});
      }
      if (result.functional) screens.push({
        key: 'functional', title: 'Dashboard · revisión funcional privada',
        before: '', after: result.functional,
        navigation: 'Captura de la revisión probada con un contrato HTTP simulado y datos ficticios.'
      });
      if (!screens.length) screens.push({key: 'empty', title: 'Revisión', before: '', after: result.markup});
      displayScreens(screens, key => {
        if (key.startsWith('page:')) prepareVisualComparison(key.slice(5), {
          revision: result.revision, generation: result.generation
        });
      });
      panes.hidden = false;
      setText('[data-comparison-status]', `Revisión ${result.revision}`);
    } catch (error) {
      if (comparisonRequest === controller) setText('[data-comparison-status]', error.message);
    }
  });

  function openDecision(title, description, url, payload, {warnings = false, reject = false} = {}) {
    confirm.disabled = warnings;
    warningsCheck.checked = false;
    warningsCheck.parentElement.hidden = !warnings;
    reason.value = '';
    reason.parentElement.hidden = !reject;
    setText('#pliegue-decision-title', title);
    setText('[data-decision-description]', description);
    setText('[data-decision-error]', '');
    pendingDecision = {url, payload, warnings, reject};
    decision.showModal();
  }

  approve.addEventListener('click', () => {
    if (!currentJob?.can_approve || reviewed?.id !== currentJob.id) return;
    openDecision('Aceptar cambio',
      'Confirma que revisaste las diferencias y la vista ANTES y DESPUÉS. Se activará una revisión privada del laboratorio.',
      `${page.dataset.drafts}/${currentJob.id}/approve`, {ticket: reviewed.ticket},
      {warnings: Boolean(currentJob.warnings?.length)});
  });
  reject.addEventListener('click', () => {
    if (!currentJob?.can_reject) return;
    openDecision('Rechazar borrador',
      'El borrador quedará cerrado para aprobación y seguirá en el historial.',
      `${page.dataset.drafts}/${currentJob.id}/reject`, {}, {reject: true});
  });
  undo.addEventListener('click', () => {
    if (!currentRevision?.previous) return;
    openDecision('Deshacer última aprobación',
      `Se restaurará la revisión ${currentRevision.previous} en el laboratorio.`,
      versionPanel.dataset.rollbackUrl, {...currentRevision});
  });
  redo.addEventListener('click', () => {
    if (!currentRevision?.redo) return;
    openDecision('Rehacer última aprobación',
      `Se recuperará la revisión ${currentRevision.redo} en el laboratorio, si no hubo cambios posteriores.`,
      versionPanel.dataset.redoUrl, {...currentRevision});
  });

  warningsCheck.addEventListener('change', () => {
    confirm.disabled = decisionBusy || !warningsCheck.checked;
  });
  cancel.addEventListener('click', () => decision.close());
  decision.addEventListener('cancel', event => {
    if (decisionBusy) event.preventDefault();
  });
  decision.addEventListener('keydown', event => {
    if (event.key === 'Escape') event.stopPropagation();
  });
  confirm.addEventListener('click', async () => {
    const operation = pendingDecision;
    if (!operation || confirm.disabled || decisionBusy) return;
    decisionBusy = true;
    confirm.disabled = true;
    cancel.disabled = true;
    try {
      const result = await request(operation.url, {method: 'POST', headers: csrfHeaders,
        body: JSON.stringify({confirm: true, ...operation.payload,
          confirm_warnings: warningsCheck.checked, ...(operation.reject ? {reason: reason.value} : {})})});
      if (pendingDecision === operation) decision.close();
      renderRevision(result);
      await refresh();
    } catch (error) {
      if (pendingDecision === operation) {
        setText('[data-decision-error]', error.message);
        confirm.disabled = operation.warnings && !warningsCheck.checked;
      }
      await refresh();
    } finally {
      decisionBusy = false;
      cancel.disabled = false;
    }
  });

  const account = page.closest('.pliegue-dock')?.querySelector('[data-codex-account]');
  if (account) {
    const trigger = account.querySelector('.pliegue-account-trigger');
    const popover = account.querySelector('[popover]');
    const label = account.querySelector('[data-account-label]');
    const message = account.querySelector('[data-account-message]');
    const login = account.querySelector('[data-account-login]');
    const logout = account.querySelector('[data-account-logout]');
    const device = account.querySelector('[data-account-device]');
    const code = account.querySelector('[data-account-code]');
    const link = account.querySelector('[data-account-link]');
    let timer;
    let updating = false;
    let posting = false;

    function positionAccount() {
      const anchor = trigger.getBoundingClientRect();
      const width = Math.min(272, document.documentElement.clientWidth - 16);
      popover.style.left = Math.max(8, Math.min(anchor.left, document.documentElement.clientWidth - width - 8)) + 'px';
      popover.style.top = anchor.bottom + 6 + 'px';
      popover.style.maxHeight = Math.max(72, window.innerHeight - anchor.bottom - 14) + 'px';
    }

    async function refreshAccount() {
      if (updating || posting) return;
      clearTimeout(timer);
      updating = true;
      let busy = false;
      try {
        const status = await request(account.dataset.codexAccount);
        const authenticated = ['chatgpt', 'authenticated'].includes(status.session);
        const available = status.session !== 'unavailable';
        const expired = status.session === 'expired';
        busy = status.busy;
        trigger.dataset.authenticated = String(authenticated);
        label.textContent = authenticated ? 'Codex conectado' : expired ? 'Sesión caducada' :
          available ? 'Conectar Codex' : 'Codex no disponible';
        const detail = status.session === 'chatgpt' ? 'Sesión de ChatGPT activa en el laboratorio.' :
          authenticated ? 'Sesión activa en el laboratorio.' : expired ? 'Reconecta tu cuenta de ChatGPT.' :
          available ? 'Conecta tu cuenta de ChatGPT.' : 'La sesión de Codex no está disponible.';
        message.textContent = status.error || (busy ?
          status.action === 'logout' ? 'Cerrando sesión…' :
          status.action === 'login' ? 'Esperando confirmación en ChatGPT…' : 'Hay otra operación de cuenta en curso.' : detail);
        device.hidden = !(status.code && status.url === 'https://auth.openai.com/codex/device');
        code.textContent = device.hidden ? '' : status.code;
        if (device.hidden) link.removeAttribute('href');
        else link.href = status.url;
        login.hidden = busy || !available;
        logout.hidden = busy || !authenticated;
        login.textContent = authenticated || expired ? 'Reconectar con ChatGPT' : 'Continuar con ChatGPT';
      } catch {
        trigger.dataset.authenticated = 'false';
        label.textContent = 'Codex no disponible';
        message.textContent = 'No se pudo comprobar la sesión de Codex.';
        login.hidden = logout.hidden = device.hidden = true;
        code.textContent = '';
        link.removeAttribute('href');
      } finally {
        updating = false;
        timer = setTimeout(() => {
          if (!document.hidden && !account.closest('[hidden]')) refreshAccount();
        }, busy ? 2000 : 12000);
      }
    }

    async function changeAccount(action) {
      if (posting) return;
      posting = true;
      login.disabled = logout.disabled = true;
      try {
        await request(account.dataset.codexAccount, {
          method: 'POST', headers: csrfHeaders, body: JSON.stringify({action})
        });
      } catch (error) {
        message.textContent = error.message;
        return;
      } finally {
        posting = false;
        login.disabled = logout.disabled = false;
      }
      refreshAccount();
    }

    login.addEventListener('click', () => changeAccount('login'));
    logout.addEventListener('click', () => changeAccount('logout'));
    popover.addEventListener('beforetoggle', event => {
      if (event.newState === 'open') {
        positionAccount();
        refreshAccount();
      }
    });
    window.addEventListener('resize', () => {
      if (popover.matches(':popover-open')) positionAccount();
    });
    page.addEventListener('pliegue:open', refreshAccount);
    if (!account.closest('[hidden]')) refreshAccount();
  }

  async function refresh() {
    clearTimeout(timer);
    const version = ++sequence;
    let interval = 12000;
    try {
      const [status, history] = await Promise.all([
        request(page.dataset.status), request(page.dataset.drafts)
      ]);
      if (version !== sequence) return;
      connected = Boolean(status.connected && status.installed);
      renderRevision(status.lab_revision);
      worker.dataset.connected = String(connected);
      worker.textContent = connected ? 'Worker disponible · Codex CLI instalado' : status.connected ?
        'Codex CLI no disponible en WSL' : 'Conexión con Codex no disponible';
      if (history.drafts.some(draft => active.has(draft.state))) interval = 2500;
      if (selected === null) {
        selected = history.drafts.some(draft => draft.id === remembered)
          ? remembered : history.drafts[0]?.id || '';
      }
      if (!history.drafts.some(draft => draft.id === selected)) selected = '';
      const serialized = JSON.stringify(history.drafts);
      if (serialized !== previousList) {
        previousList = serialized;
        drafts = history.drafts;
        renderHistory();
      }
      list.value = selected;
      if (selected) {
        const job = await request(`${page.dataset.drafts}/${encodeURIComponent(selected)}`);
        if (version !== sequence) return;
        render(job);
        if (active.has(job.state)) interval = 750;
      } else {
        currentJob = null;
        reviewed = null;
        article.hidden = true;
        welcome.hidden = false;
      }
      refreshError = '';
    } catch (error) {
      if (version !== sequence) return;
      connected = false;
      worker.dataset.connected = 'false';
      worker.textContent = 'Conexión con Codex no disponible';
      refreshError = error.message;
    } finally {
      if (version === sequence) {
        updateComposer();
        timer = setTimeout(resume, interval);
      }
    }
  }

  function resume() {
    if (!document.hidden && !page.closest('[hidden]')) refresh();
  }

  const fileInput = find('#pliegue-code-files');
  const attachmentList = find('[data-attachment-list]');
  const attachmentError = find('[data-attachment-error]');
  const attachments = [];
  let readingFiles = false;
  const imageTypes = new Map([['.png', 'image/png'], ['.jpg', 'image/jpeg'],
    ['.jpeg', 'image/jpeg'], ['.webp', 'image/webp']]);
  const documentTypes = new Set(['.docx', '.xlsx', '.pptx', '.pdf']);
  const filesButton = find('[data-attachment-open]');
  const clearFiles = find('[data-attachment-clear]');
  const cancelFiles = find('[data-attachment-cancel]');
  const media = find('[data-media-dialog]');
  const mediaTitle = find('#pliegue-media-title');
  const picture = find('[data-media-image]');
  const video = find('[data-camera-video]');
  const cameraButton = find('[data-camera-open]');
  const cameraStatus = find('[data-camera-status]');
  const take = find('[data-camera-take]');
  const changeCamera = find('[data-camera-switch]');
  const retake = find('[data-camera-retake]');
  const attachPhoto = find('[data-camera-attach]');
  const fallback = find('[data-camera-fallback]');
  const replaceFile = find('[data-media-replace]');
  let reader;
  let stream;
  let captureVersion = 0;
  let captured;
  let captureURL;
  let cameraDevices = [];
  let selectedCamera;
  let dialogOpener;
  let previewedFile;
  let replacingFile;

  function removeFiles(index) {
    if (posting || readingFiles) return;
    const removed = index == null ? attachments.splice(0) : attachments.splice(index, 1);
    for (const file of removed) if (file.url) URL.revokeObjectURL(file.url);
    showAttachments();
    (attachmentList.querySelector('[data-remove-file]') || filesButton).focus();
  }

  function showAttachments() {
    clearFiles.hidden = attachments.length === 0;
    clearFiles.textContent = 'Quitar todos (' + attachments.length + ')';
    attachmentList.replaceChildren(...attachments.map((file, index) => {
      const row = document.createElement('li');
      const label = document.createElement('span');
      label.textContent = `${file.name} · ${file.extension} · ${file.bytes} B`;
      const preview = document.createElement('button');
      preview.type = 'button';
      preview.setAttribute('aria-label', 'Ver ' + file.name);
      if (file.url) {
        const thumbnail = document.createElement('img');
        thumbnail.alt = '';
        thumbnail.src = file.url;
        preview.append(thumbnail);
      } else {
        preview.textContent = 'Ver';
      }
      preview.onclick = () => {
        previewedFile = file;
        dialogOpener = preview;
        mediaTitle.textContent = file.name;
        cameraStatus.textContent = label.textContent;
        replaceFile.hidden = false;
        if (file.url) {
          picture.src = file.url;
          picture.hidden = false;
        }
        media.showModal();
      };
      row.append(preview);
      const remove = document.createElement('button');
      remove.type = 'button';
      remove.textContent = '×';
      remove.dataset.removeFile = '';
      remove.setAttribute('aria-label', 'Quitar ' + file.name);
      remove.onclick = () => removeFiles(index);
      row.append(label, remove);
      return row;
    }));
  }

  function readFile(file) {
    return new Promise((resolve, reject) => {
      reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = () => reject(Error('No se pudo leer el archivo.'));
      reader.onabort = () => reject(Error('Lectura cancelada.'));
      reader.readAsArrayBuffer(file);
    });
  }

  async function addFiles(files, replacement) {
    if (posting || readingFiles || !files.length) return;
    readingFiles = true;
    cancelFiles.hidden = false;
    updateComposer();
    attachmentError.textContent = 'Validando adjuntos…';
    const entries = [];
    let accepted = false;
    try {
      const sizes = {text: 0, document: 0, image: 0};
      const maxima = {text: 3072, document: 65536, image: 196608};
      const kept = attachments.filter(file => file !== replacement);
      for (const file of kept) sizes[file.kind] += file.bytes;
      for (const file of files) {
        const extension = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
        if (!file.size || !fileInput.accept.split(',').includes(extension)) {
          throw Error('El formato o el contenido del archivo no es compatible.');
        }
        const kind = imageTypes.has(extension) ? 'image' : documentTypes.has(extension) ? 'document' : 'text';
        if (file.size > maxima[kind]) throw Error('Límites por mensaje: texto 3 KiB, documentos 64 KiB e imágenes 192 KiB.');
        const buffer = await readFile(file);
        if (kind === 'image') {
          const bytes = new Uint8Array(buffer);
          const format = imageTypes.get(extension);
          const matches = format === 'image/png' ? [137, 80, 78, 71, 13, 10, 26, 10].every((byte, index) => bytes[index] === byte)
            : format === 'image/jpeg' ? bytes[0] === 255 && bytes[1] === 216 && bytes[2] === 255
            : String.fromCharCode(...bytes.slice(0, 4)) === 'RIFF' && String.fromCharCode(...bytes.slice(8, 12)) === 'WEBP';
          if (!matches) throw Error('El contenido de la imagen no coincide con su formato.');
        }
        let data;
        if (kind === 'text') {
          data = {text: new TextDecoder('utf-8', {fatal: true}).decode(buffer)};
        } else {
          let bytes = '';
          for (const byte of new Uint8Array(buffer)) bytes += String.fromCharCode(byte);
          data = {base64: btoa(bytes)};
        }
        const content = data.base64 || data.text;
        if ([...kept, ...entries].some(item => item.kind === kind && (item.data.base64 || item.data.text) === content)) continue;
        sizes[kind] += file.size;
        if (sizes[kind] > maxima[kind]) throw Error('Límites por mensaje: texto 3 KiB, documentos 64 KiB e imágenes 192 KiB.');
        if (kept.length + entries.length >= 4) throw Error('Adjunta hasta 4 archivos.');
        const url = kind === 'image' ? URL.createObjectURL(new Blob([buffer], {type: imageTypes.get(extension)})) : null;
        entries.push({name: file.name, data, bytes: file.size, extension, kind, url});
      }
      if (entries.length && replacement && attachments.includes(replacement)) {
        attachments.splice(attachments.indexOf(replacement), 1, entries[0]);
        if (replacement.url) URL.revokeObjectURL(replacement.url);
      } else {
        attachments.push(...entries);
      }
      accepted = true;
      showAttachments();
      attachmentError.textContent = entries.length ? '' : 'Estos archivos ya están adjuntos.';
    } catch (error) {
      attachmentError.textContent = error.message;
    } finally {
      if (!accepted) for (const entry of entries) if (entry.url) URL.revokeObjectURL(entry.url);
      reader = null;
      readingFiles = false;
      cancelFiles.hidden = true;
      fileInput.value = '';
      updateComposer();
    }
  }
  clearFiles.onclick = () => removeFiles(null);
  cancelFiles.onclick = () => reader?.abort();
  filesButton.onclick = () => {
    replacingFile = null;
    fileInput.multiple = true;
    fileInput.click();
  };
  fileInput.addEventListener('change', () => {
    const replacement = replacingFile;
    replacingFile = null;
    addFiles(Array.from(fileInput.files).slice(0, replacement ? 1 : undefined), replacement);
  });
  fileInput.addEventListener('cancel', () => { replacingFile = null; });
  input.addEventListener('paste', event => {
    const extensions = new Map([['image/png', 'png'], ['image/jpeg', 'jpg'], ['image/webp', 'webp']]);
    const clipboard = event.clipboardData;
    const files = clipboard?.files.length ? Array.from(clipboard.files) :
      Array.from(clipboard?.items || [], item => item.kind === 'file' ? item.getAsFile() : null);
    const images = files.filter(file => file && extensions.has(file.type));
    if (images.length) {
      event.preventDefault();
      addFiles(images.map((file, index) => new File([file], `captura-${Date.now()}-${index + 1}.${extensions.get(file.type)}`,
        {type: file.type})));
    }
  });

  function stopCamera() {
    captureVersion++;
    stream?.getTracks().forEach(track => track.stop());
    stream = null;
    video.srcObject = null;
    video.hidden = true;
    take.hidden = changeCamera.hidden = true;
  }

  function clearPhoto() {
    if (captureURL) URL.revokeObjectURL(captureURL);
    captureURL = captured = null;
    picture.removeAttribute('src');
    picture.hidden = true;
    attachPhoto.hidden = retake.hidden = true;
  }

  async function openCamera() {
    stopCamera();
    clearPhoto();
    fallback.hidden = true;
    cameraStatus.textContent = 'Solicitando acceso a la cámara…';
    const version = captureVersion;
    try {
      const request = await navigator.mediaDevices.getUserMedia({audio: false, video: {
        width: {ideal: 1280}, height: {ideal: 720},
        ...(selectedCamera ? {deviceId: {exact: selectedCamera}} : {facingMode: {ideal: 'environment'}})
      }});
      if (!media.open || version !== captureVersion) {
        request.getTracks().forEach(track => track.stop());
        return;
      }
      stream = request;
      video.srcObject = request;
      video.hidden = false;
      const track = request.getVideoTracks()[0];
      const deviceId = track.getSettings().deviceId;
      track.addEventListener('ended', () => {
        if (version === captureVersion) {
          stopCamera();
          cameraStatus.textContent = 'Se perdió la conexión con la cámara.';
          fallback.hidden = false;
        }
      });
      try {
        cameraDevices = (await navigator.mediaDevices.enumerateDevices()).filter(device => device.kind === 'videoinput');
      } catch {
        cameraDevices = [];
      }
      if (version !== captureVersion) return;
      selectedCamera = cameraDevices.find(device => device.deviceId === deviceId)?.deviceId;
      changeCamera.hidden = cameraDevices.length < 2;
      cameraStatus.textContent = 'Cámara activa';
      if (video.videoWidth) take.hidden = false;
    } catch (error) {
      if (version !== captureVersion) return;
      stopCamera();
      cameraStatus.textContent = ({
        NotAllowedError: 'Permiso de cámara denegado.',
        NotFoundError: 'No se encontró una cámara.',
        NotReadableError: 'La cámara está ocupada o no se puede abrir.',
        NotSupportedError: 'Este navegador no puede abrir la cámara.'
      })[error.name] || 'No se pudo abrir la cámara.';
      fallback.hidden = false;
    }
  }

  cameraButton.hidden = !navigator.mediaDevices?.getUserMedia;
  cameraButton.onclick = () => {
    dialogOpener = cameraButton;
    mediaTitle.textContent = 'Cámara';
    media.showModal();
    openCamera();
  };
  video.addEventListener('loadeddata', () => { if (stream) take.hidden = false; });
  changeCamera.onclick = () => {
    const current = cameraDevices.findIndex(device => device.deviceId === selectedCamera);
    selectedCamera = cameraDevices[(current + 1) % cameraDevices.length]?.deviceId;
    openCamera();
  };
  take.onclick = () => {
    if (!stream || !video.videoWidth) return;
    const canvas = document.createElement('canvas');
    const scale = Math.min(1, 960 / Math.max(video.videoWidth, video.videoHeight));
    canvas.width = Math.round(video.videoWidth * scale);
    canvas.height = Math.round(video.videoHeight * scale);
    canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
    stopCamera();
    const version = captureVersion;
    canvas.toBlob(blob => {
      if (!media.open || version !== captureVersion) return;
      if (!blob) {
        cameraStatus.textContent = 'No se pudo capturar la foto.';
        retake.hidden = false;
        return;
      }
      captured = new File([blob], `foto-${Date.now()}.jpg`, {type: 'image/jpeg'});
      captureURL = URL.createObjectURL(captured);
      picture.src = captureURL;
      picture.hidden = attachPhoto.hidden = retake.hidden = false;
      cameraStatus.textContent = 'Foto lista para revisar';
    }, 'image/jpeg', 0.72);
  };
  retake.onclick = openCamera;
  attachPhoto.onclick = () => {
    if (captured) addFiles([captured]);
    media.close();
  };
  fallback.onclick = () => { media.close(); filesButton.click(); };
  replaceFile.onclick = () => {
    replacingFile = previewedFile;
    media.close();
    fileInput.multiple = false;
    fileInput.click();
  };
  find('[data-media-close]').onclick = () => media.close();
  media.addEventListener('close', () => {
    stopCamera();
    clearPhoto();
    fallback.hidden = true;
    replaceFile.hidden = true;
    previewedFile = null;
    cameraStatus.textContent = '';
    if (dialogOpener?.isConnected && !page.closest('[hidden]')) dialogOpener.focus();
  });
  page.addEventListener('dragover', event => {
    if (Array.from(event.dataTransfer.types).includes('Files')) event.preventDefault();
  });
  page.addEventListener('drop', event => {
    if (!event.dataTransfer.files.length) return;
    event.preventDefault();
    addFiles(Array.from(event.dataTransfer.files));
  });

  const voiceDialog = find('[data-voice-dialog]');
  const voiceButton = find('[data-voice-open]');
  const voiceStatus = find('[data-voice-status]');
  const voiceStart = find('[data-voice-start]');
  const voiceStop = find('[data-voice-stop]');
  const voiceAbort = find('[data-voice-abort]');
  const voiceRead = find('[data-voice-read]');
  const voiceSilence = find('[data-voice-silence]');
  const voiceLanguage = find('[data-voice-language]');
  const voiceAuto = find('[data-voice-auto]');
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const synthesis = window.speechSynthesis;
  let recognition;
  let utterance;
  let voiceJob;

  function localVoice() {
    const prefix = voiceLanguage.value.split('-')[0];
    return synthesis?.getVoices().find(voice => voice.localService && voice.lang.toLowerCase().startsWith(prefix));
  }

  function refreshVoice() {
    voiceButton.hidden = !Recognition && !localVoice();
    voiceStart.hidden = !Recognition || Boolean(recognition);
    voiceStop.hidden = voiceAbort.hidden = !recognition;
    voiceRead.hidden = !localVoice() || !currentJob || active.has(currentJob.state);
    find('[data-voice-auto-label]').hidden = !localVoice();
    voiceSilence.hidden = !utterance;
  }

  function cancelSpeech() {
    if (utterance) {
      utterance = null;
      synthesis.cancel();
      voiceStatus.textContent = 'Lectura detenida';
    }
    refreshVoice();
  }

  function abortDictation() {
    if (recognition) {
      const current = recognition;
      recognition = null;
      current.abort();
      voiceStatus.textContent = 'Dictado cancelado';
    }
    refreshVoice();
  }

  function speakSummary() {
    const voice = localVoice();
    const summary = find('[data-job-summary]').textContent.trim().split('\n')[0].slice(0, 280);
    if (!voice || !summary || recognition) return;
    cancelSpeech();
    const speech = new SpeechSynthesisUtterance(summary);
    speech.voice = voice;
    speech.lang = voice.lang;
    utterance = speech;
    voiceStatus.textContent = 'Preparando lectura…';
    speech.onstart = () => {
      if (utterance === speech) voiceStatus.textContent = 'Reproduciendo voz';
    };
    const finish = message => {
      if (utterance !== speech) return;
      utterance = null;
      voiceStatus.textContent = message;
      refreshVoice();
    };
    speech.onend = () => finish('Lectura terminada');
    speech.onerror = () => finish('No se pudo reproducir la respuesta.');
    synthesis.speak(speech);
    refreshVoice();
  }

  voiceStart.onclick = () => {
    if (!Recognition || recognition) return;
    cancelSpeech();
    const current = new Recognition();
    recognition = current;
    current.lang = voiceLanguage.value;
    current.continuous = false;
    current.interimResults = true;
    const results = new Map();
    let failed = false;
    voiceStatus.textContent = 'Solicitando acceso al micrófono…';
    current.onaudiostart = () => {
      if (recognition === current) voiceStatus.textContent = 'Escuchando';
    };
    current.onaudioend = () => {
      if (recognition === current && !failed) voiceStatus.textContent = 'Transcribiendo…';
    };
    current.onresult = event => {
      if (recognition !== current) return;
      for (let index = event.resultIndex; index < event.results.length; index++) {
        const result = event.results[index];
        if (result.isFinal) results.set(index, result[0].transcript.trim());
      }
    };
    current.onerror = event => {
      if (recognition !== current) return;
      failed = true;
      voiceStatus.textContent = ({
        'not-allowed': 'Permiso de micrófono denegado.',
        'audio-capture': 'No se pudo acceder al micrófono.',
        'no-speech': 'No se detectó voz.',
        network: 'El reconocedor del navegador no está disponible.'
      })[event.error] || 'No se pudo transcribir el dictado.';
    };
    current.onend = () => {
      if (recognition !== current) return;
      recognition = null;
      const text = [...results.values()].join(' ');
      if (text && !failed) {
        const separator = input.value && !/\s$/.test(input.value) ? ' ' : '';
        const available = input.maxLength - input.value.length;
        input.value += (separator + text).slice(0, Math.max(available, 0));
        input.dispatchEvent(new Event('input', {bubbles: true}));
        voiceDialog.close();
        input.focus();
      } else if (!failed) {
        voiceStatus.textContent = 'No se detectó voz.';
      }
      refreshVoice();
    };
    try {
      current.start();
      refreshVoice();
    } catch {
      recognition = null;
      voiceStatus.textContent = 'No se pudo iniciar el reconocedor del navegador.';
      refreshVoice();
    }
  };
  voiceStop.onclick = () => recognition?.stop();
  voiceAbort.onclick = abortDictation;
  voiceRead.onclick = speakSummary;
  voiceSilence.onclick = cancelSpeech;
  voiceButton.onclick = () => {
    refreshVoice();
    voiceDialog.showModal();
  };
  find('[data-voice-close]').onclick = () => voiceDialog.close();
  voiceDialog.addEventListener('close', abortDictation);
  voiceLanguage.addEventListener('change', refreshVoice);
  synthesis?.addEventListener('voiceschanged', refreshVoice);
  refreshVoice();

  function releaseMedia() {
    if (media.open) media.close();
    stopCamera();
    abortDictation();
    cancelSpeech();
    voiceJob = null;
    voiceAuto.checked = false;
    if (voiceDialog.open) voiceDialog.close();
  }
  page.addEventListener('pliegue:close', releaseMedia);
  document.addEventListener('visibilitychange', () => { if (document.hidden) releaseMedia(); });
  window.addEventListener('pagehide', () => {
    releaseMedia();
    for (const file of attachments) if (file.url) URL.revokeObjectURL(file.url);
    reader?.abort();
  });

  form.addEventListener('submit', async event => {
    event.preventDefault();
    const message = input.value.trim();
    if (!connected || posting || readingFiles || !message) return;
    const references = mentions?.payload();
    posting = true;
    postError = '';
    updateComposer();
    try {
      const payload = {message, mode, ...visualEditor?.payload(), ...references,
        ...(continuation ? {continuation} : {}),
        attachments: attachments.map(({name, data}) => ({name, ...data}))};
      const requestId = await submissionId(JSON.stringify(payload));
      const job = await request(page.dataset.drafts, {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'X-Pliegue-CSRF': page.dataset.csrf},
        body: JSON.stringify({...payload, request_id: requestId})
      });
      if (voiceAuto.checked && localVoice()) {
        voiceJob = job.id;
        voiceAuto.checked = false;
      }
      pendingSubmission = null;
      try { sessionStorage.removeItem('pliegue.pending-send'); } catch {}
      if (input.value.trim() === message && JSON.stringify(references) === JSON.stringify(mentions?.payload())) {
        input.value = '';
        mentions?.clear();
      }
      for (const file of attachments.splice(0)) if (file.url) URL.revokeObjectURL(file.url);
      showAttachments();
      selected = job.id;
      rememberSelection(selected);
      render(job);
      await refresh();
    } catch (error) {
      postError = error.message;
    } finally {
      posting = false;
      updateComposer();
    }
  });

  list.addEventListener('change', () => {
    if (comparison.open) closeComparison();
    selected = list.value;
    renderHistory();
    setContinuation(null);
    rememberSelection(selected);
    currentJob = null;
    reviewed = null;
    article.hidden = true;
    welcome.hidden = Boolean(selected);
    if (!selected) input.focus();
    // Restaurar también el artículo al volver al último borrador consultado.
    previousJob = '';
    refresh();
  });
  find('#pliegue-codigo-refresh').addEventListener('click', refresh);
  document.addEventListener('visibilitychange', resume);
  page.addEventListener('pliegue:open', refresh);
  refresh();
})();
