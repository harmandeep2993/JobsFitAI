// assets/js/settings.js
// LLM Settings tab - pick the active provider + model at runtime via
// styled button-dropdowns. Loads the catalog from /api/llm-settings and
// applies changes via POST.

window._llmCatalog = null;            // [{name, default_model, models[]}]
window._sel        = { provider: '', model: '' };

// ── Load catalog + current selection ──────────────────────
function loadLlmSettings() {
  fetch('/api/llm-settings')
    .then(r => r.json())
    .then(d => {
      if (!d.ok) return;
      window._llmCatalog = d.providers || [];
      window._sel = {
        provider: (d.current && d.current.provider) || '',
        model:    (d.current && d.current.model)    || '',
      };
      renderProviderMenu();
      renderModelMenu();
      setVal('provider', window._sel.provider);
      setVal('model', window._sel.model);
    })
    .catch(() => {});
}

function setVal(which, val) {
  const el = document.getElementById('dd-' + which + '-val');
  if (el) el.textContent = val || '-';
}

function renderProviderMenu() {
  const menu = document.getElementById('dd-provider-menu');
  if (!menu || !window._llmCatalog) return;
  menu.innerHTML = window._llmCatalog.map(p =>
    '<div class="dd-opt' + (p.name === window._sel.provider ? ' sel' : '') +
    '" onclick="selectProvider(\'' + p.name + '\')">' + p.name + '</div>'
  ).join('');
}

function renderModelMenu() {
  const menu = document.getElementById('dd-model-menu');
  if (!menu || !window._llmCatalog) return;
  const entry  = window._llmCatalog.find(p => p.name === window._sel.provider);
  const models = (entry && entry.models) || [];
  menu.innerHTML = models.map(m =>
    '<div class="dd-opt' + (m === window._sel.model ? ' sel' : '') +
    '" onclick="selectModel(\'' + m + '\')">' + m + '</div>'
  ).join('');
}

// ── Dropdown open/close ───────────────────────────────────
window.ddToggle = function(ev, which) {
  ev.stopPropagation();
  const dd = document.getElementById('dd-' + which);
  const wasOpen = dd.classList.contains('open');
  closeAllDD();
  if (!wasOpen) dd.classList.add('open');
};

function closeAllDD() {
  document.querySelectorAll('.dd.open').forEach(d => d.classList.remove('open'));
}

// Close menus when clicking anywhere outside a dropdown.
document.addEventListener('click', closeAllDD);

// ── Selection ─────────────────────────────────────────────
window.selectProvider = function(name) {
  window._sel.provider = name;
  // Reset model to that provider's default.
  const entry = window._llmCatalog.find(p => p.name === name);
  window._sel.model = (entry && entry.default_model) || '';

  setVal('provider', name);
  setVal('model', window._sel.model);
  renderProviderMenu();
  renderModelMenu();

  const custom = document.getElementById('set-model-custom');
  if (custom) custom.value = '';
  closeAllDD();
};

window.selectModel = function(m) {
  window._sel.model = m;
  setVal('model', m);
  renderModelMenu();
  closeAllDD();
};

// ── Apply selection ───────────────────────────────────────
window.applySettings = function() {
  const custom   = document.getElementById('set-model-custom').value.trim();
  const provider = window._sel.provider;
  const model    = custom || window._sel.model;

  const btn    = document.getElementById('set-apply');
  const status = document.getElementById('set-status');

  if (!provider) return;

  btn.disabled = true;
  status.textContent = 'Applying…';
  status.className = 'set-status';

  fetch('/api/llm-settings', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ provider: provider, model: model }),
  })
    .then(r => r.json())
    .then(d => {
      btn.disabled = false;
      if (!d.ok) {
        status.textContent = '✕ ' + (d.error || 'failed');
        status.className = 'set-status err';
        return;
      }

      window._sel = { provider: d.current.provider, model: d.current.model };
      setVal('provider', d.current.provider);
      setVal('model', d.current.model);

      const onlineTxt = d.online ? 'online' : 'offline (check API key / server)';
      status.textContent = '✓ Using ' + d.current.provider + ' · ' +
                           d.current.model + ' - ' + onlineTxt;
      status.className = 'set-status ' + (d.online ? 'ok' : 'err');

      updateTopbar(d.current, d.online);
    })
    .catch(e => {
      btn.disabled = false;
      status.textContent = '✕ ' + e;
      status.className = 'set-status err';
    });
};

// Reflect the new selection in the topbar chips.
function updateTopbar(current, online) {
  const prov  = document.getElementById('tb-provider');
  const model = document.getElementById('tb-model');
  const bead  = document.getElementById('tb-bead');
  if (prov)  prov.textContent  = current.provider + ' ' + (online ? 'online' : 'offline');
  if (model) model.textContent = current.model;
  if (bead)  bead.className     = 't-bead ' + (online ? 'bon' : 'boff');
}

// ── Test connection ───────────────────────────────────────
window.testConnection = function() {
  var btn    = document.getElementById('set-test');
  var status = document.getElementById('set-status');
  var orig   = btn ? btn.textContent : 'Test connection';

  if (btn) { btn.disabled = true; btn.textContent = 'Testing…'; }
  if (status) { status.textContent = 'Checking…'; status.className = 'set-status'; }

  var controller = new AbortController();
  var timeoutId  = setTimeout(function() { controller.abort(); }, 8000);

  fetch('/api/llm-ping', { signal: controller.signal })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      var cur = d.current || {};
      var provider = cur.provider || window._sel.provider || 'provider';
      if (d.online) {
        toast('Connected - ' + provider + ' / ' + (cur.model || ''), 'ok', 4000);
        updateTopbar(cur, true);
        if (status) { status.textContent = '✓ Online'; status.className = 'set-status ok'; }
      } else {
        toast(provider + ' is offline - check API key or server.', 'warn', 5000);
        updateTopbar(cur, false);
        if (status) { status.textContent = '✕ Offline'; status.className = 'set-status err'; }
      }
    })
    .catch(function(e) {
      var msg = e && e.name === 'AbortError'
        ? 'Test timed out after 8 s - server may be slow.'
        : 'Test failed: ' + e;
      toast(msg, 'err', 5000);
      if (status) { status.textContent = '✕ Error'; status.className = 'set-status err'; }
    })
    .finally(function() {
      clearTimeout(timeoutId);
      if (btn) { btn.disabled = false; btn.textContent = orig; }
    });
};

// Load once the settings elements exist.
(function bindSettings() {
  if (document.getElementById('dd-provider')) {
    loadLlmSettings();
  } else {
    setTimeout(bindSettings, 80);
  }
})();
