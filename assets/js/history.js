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
    })
    .catch(() => {});
};

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
