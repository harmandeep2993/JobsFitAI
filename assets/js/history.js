// assets/js/history.js
// History tab — every job ever scored, shown as a sortable table.

window._histData   = [];
window._histFilter = 'all';   // all | applied | open
window._histSort   = 'score'; // score | newest | company
window._histSortDir = -1;     // -1 = desc, 1 = asc

window.loadHistory = function() {
  fetch('/api/match/state')
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (!d.ok) return;
      window._histData = d.results || [];
      renderHistory();
    })
    .catch(function() {});
};

window.setHistFilter = function(f) {
  window._histFilter = f;
  document.querySelectorAll('#hist-filters .hist-fbtn').forEach(function(b) {
    b.classList.toggle('active', b.dataset.f === f);
  });
  renderHistory();
};

window.setHistSort = function(col) {
  if (window._histSort === col) {
    window._histSortDir *= -1;
  } else {
    window._histSort = col;
    window._histSortDir = col === 'company' ? 1 : -1;
  }
  renderHistory();
};

function sortArrow(col) {
  if (window._histSort !== col) return '<span class="ht-arr">⇅</span>';
  return window._histSortDir === -1
    ? '<span class="ht-arr active">↓</span>'
    : '<span class="ht-arr active">↑</span>';
}

function mtEscH(s) {
  return (s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;')
                  .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function relTimeH(posted) {
  var ts = parseInt(posted, 10);
  if (!ts) return '';
  var days = Math.floor((Date.now() / 1000 - ts) / 86400);
  if (days <= 0)  return 'today';
  if (days === 1) return '1d ago';
  if (days < 7)   return days + 'd ago';
  var weeks = Math.floor(days / 7);
  if (weeks < 5)  return weeks + 'w ago';
  return Math.floor(days / 30) + 'mo ago';
}

function labelClassH(label, score) {
  var l = (label || '').toLowerCase();
  if (l.includes('excellent')) return 'sc-exc';
  if (l.includes('good'))      return 'sc-good';
  if (l.includes('partial'))   return 'sc-partial';
  if (l.includes('poor'))      return 'sc-poor';
  if (score >= 80) return 'sc-exc';
  if (score >= 60) return 'sc-good';
  if (score >= 40) return 'sc-partial';
  return 'sc-poor';
}

function renderHistory() {
  var box = document.getElementById('hist-results');
  if (!box) return;

  var all     = window._histData || [];
  var applied = all.filter(function(x) { return x.applied; });
  var open    = all.filter(function(x) { return !x.applied; });

  // Update filter button counts
  function setCount(f, n) {
    var el = document.querySelector('#hist-filters .hist-fbtn[data-f="' + f + '"] .hist-count');
    if (el) el.textContent = n;
  }
  setCount('all',     all.length);
  setCount('applied', applied.length);
  setCount('open',    open.length);

  var items = all;
  if (window._histFilter === 'applied') items = applied;
  else if (window._histFilter === 'open') items = open;

  if (!items.length) {
    box.innerHTML = '<div class="fetch-empty">Nothing here yet. Score some jobs on the Job Matches tab.</div>';
    return;
  }

  // Sort
  var col = window._histSort || 'score';
  var dir = window._histSortDir || -1;
  items = items.slice().sort(function(a, b) {
    var v;
    if (col === 'score')   v = ((a.score || 0) - (b.score || 0)) * dir;
    else if (col === 'newest') v = ((a.posted_at || 0) - (b.posted_at || 0)) * dir;
    else if (col === 'company') v = (a.company || '').localeCompare(b.company || '') * dir;
    else v = 0;
    return v;
  });

  var rows = items.map(function(r) {
    var sc    = r.status === 'pending' ? '' : (r.status === 'jd_unavailable' ? 'JD?' : Math.round(r.score || 0) + '%');
    var lc    = r.status === 'pending' || r.status === 'jd_unavailable' ? 'sc-na' : labelClassH(r.label, r.score);
    var applied = !!r.applied;

    var detailBtn = r.status === 'jd_unavailable'
      ? ''
      : '<button class="ht-open" onclick="openDetail(\'' + mtEscH(r.id) + '\')">Detail</button>';

    var applyBtn =
      '<button class="ht-apply' + (applied ? ' on' : '') +
      '" onclick="toggleApplied(\'' + mtEscH(r.id) + '\',' + (applied ? 1 : 0) + ')">' +
      (applied ? '✓' : 'Mark') + '</button>';

    return '<tr>' +
      '<td><span class="ht-score ' + lc + '">' + mtEscH(sc) + '</span></td>' +
      '<td class="ht-title">' +
        '<div class="ht-t1">' + mtEscH(r.title || '') + '</div>' +
        '<div class="ht-t2">' + mtEscH(r.company || '') +
          (r.location ? ' &middot; ' + mtEscH(r.location) : '') + '</div>' +
      '</td>' +
      '<td class="ht-age">' + relTimeH(r.posted_at) + '</td>' +
      '<td><div class="ht-actions">' + detailBtn + applyBtn + '</div></td>' +
      '</tr>';
  }).join('');

  box.innerHTML =
    '<div class="hist-tbl-wrap"><table class="hist-tbl">' +
      '<thead><tr>' +
        '<th onclick="setHistSort(\'score\')">' +
          'Score ' + sortArrow('score') + '</th>' +
        '<th onclick="setHistSort(\'company\')">' +
          'Job / Company ' + sortArrow('company') + '</th>' +
        '<th onclick="setHistSort(\'newest\')">' +
          'Posted ' + sortArrow('newest') + '</th>' +
        '<th>Actions</th>' +
      '</tr></thead>' +
      '<tbody>' + rows + '</tbody>' +
    '</table></div>';
}

// Load when History elements exist.
(function bindHistory() {
  if (document.getElementById('hist-results')) {
    loadHistory();
  } else {
    setTimeout(bindHistory, 100);
  }
})();
