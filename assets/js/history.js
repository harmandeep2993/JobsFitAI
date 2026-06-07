// assets/js/history.js
// History tab — every job ever scored, with an applied/open filter.
// Reuses window.matchCardHTML and window.toggleApplied from matches.js.

window._histData   = [];
window._histFilter = 'all';   // all | applied | open

window.loadHistory = function() {
  fetch('/api/match/state')
    .then(r => r.json())
    .then(d => {
      if (!d.ok) return;
      window._histData = d.results || [];
      renderHistory();
      renderEvents(d.events || []);
    })
    .catch(() => {});
};

function renderEvents(events) {
  const box = document.getElementById('hist-events');
  if (!box) return;
  if (!events.length) { box.innerHTML = ''; return; }
  box.innerHTML = '<div class="hist-ev-title">Recent activity</div>' +
    events.slice(0, 15).map(e => {
      const t = (e.created_at || '').replace('T', ' ').slice(0, 16);
      const d = e.detail || e.job_id || '';
      return '<div class="hist-ev">' +
        '<span class="hist-ev-type ev-' + e.type + '">' + e.type + '</span>' +
        '<span class="hist-ev-d">' + mtEsc(d) + '</span>' +
        '<span class="hist-ev-t">' + t + '</span>' +
      '</div>';
    }).join('');
}

window.setHistFilter = function(f) {
  window._histFilter = f;
  document.querySelectorAll('#hist-filters .hist-fbtn').forEach(b => {
    b.classList.toggle('active', b.dataset.f === f);
  });
  renderHistory();
};

function renderHistory() {
  const box = document.getElementById('hist-results');
  if (!box) return;

  const all     = window._histData || [];
  const applied = all.filter(x => x.applied);
  const open    = all.filter(x => !x.applied);

  // counts on the filter buttons
  const setCount = (f, n) => {
    const el = document.querySelector('#hist-filters .hist-fbtn[data-f="' + f + '"] .hist-count');
    if (el) el.textContent = n;
  };
  setCount('all', all.length);
  setCount('applied', applied.length);
  setCount('open', open.length);

  let items = all;
  if (window._histFilter === 'applied') items = applied;
  else if (window._histFilter === 'open') items = open;

  if (!items.length) {
    box.innerHTML = '<div class="fetch-empty">Nothing here yet. Score some jobs on the Job Matches tab.</div>';
    return;
  }

  box.innerHTML = items.map(r => window.matchCardHTML(r, false)).join('');
}

// Load when the History elements exist (so counts render on first open).
(function bindHistory() {
  if (document.getElementById('hist-results')) {
    loadHistory();
  } else {
    setTimeout(bindHistory, 100);
  }
})();
