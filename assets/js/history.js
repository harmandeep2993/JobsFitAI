// assets/js/history.js
// History view - 3 tabs: Analyser | Fetcher | Applications

function _hEsc(s) {
  return String(s || '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function _hAgo(iso) {
  if (!iso) return '';
  var d = new Date(iso);
  if (isNaN(d)) return iso.slice(0, 10);
  var mins = Math.floor((Date.now() - d.getTime()) / 60000);
  if (mins < 1)   return 'just now';
  if (mins < 60)  return mins + 'm ago';
  var hrs = Math.floor(mins / 60);
  if (hrs < 24)   return hrs + 'h ago';
  var days = Math.floor(hrs / 24);
  if (days < 7)   return days + 'd ago';
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

function _hTierCls(score) {
  if (score >= 80) return 'sc-exc';
  if (score >= 60) return 'sc-good';
  if (score >= 40) return 'sc-partial';
  return 'sc-poor';
}

// ── Tab switching ─────────────────────────────────────────

window.hTab = function(el, tabId) {
  document.querySelectorAll('#hv-tab-row .hv-tab').forEach(function(t) {
    t.classList.remove('active');
  });
  document.querySelectorAll('.hv-panel').forEach(function(p) {
    p.style.display = 'none';
  });
  el.classList.add('active');
  var panel = document.getElementById(tabId);
  if (panel) panel.style.display = '';
};

// ── Load ──────────────────────────────────────────────────

window.loadHistory = window.hvLoad = function() {
  ['hv-analyser', 'hv-fetcher', 'hv-applications'].forEach(function(id) {
    var el = document.getElementById(id);
    if (el) el.innerHTML = '<div class="hv-loading"><div class="up-spinner" style="width:16px;height:16px;border-width:2px;margin:0 auto;"></div></div>';
  });

  fetch('/api/history')
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (!d.ok) return;
      _hvRenderAnalyser(d.analyses || []);
      _hvRenderFetcher(d.fetcher_runs || []);
      _hvRenderApplications(d.applications || []);
      _hvUpdateBadge((d.analyses || []).length + (d.applications || []).length);
    })
    .catch(function() {
      ['hv-analyser', 'hv-fetcher', 'hv-applications'].forEach(function(id) {
        var el = document.getElementById(id);
        if (el) el.innerHTML = '<p class="hv-empty">Could not load history.</p>';
      });
    });
};

// ── Analyser tab ──────────────────────────────────────────

function _hvRenderAnalyser(entries) {
  var el = document.getElementById('hv-analyser');
  if (!el) return;
  if (!entries.length) {
    el.innerHTML = '<p class="hv-empty">No analyses yet. Run your first analysis in the Analyser tab.</p>';
    return;
  }
  el.innerHTML = entries.map(function(e) {
    var tier = _hTierCls(e.score);
    var slot = e.slot != null ? '<span class="hv-slot-badge">' + (e.slot + 1) + '</span>' : '';
    return (
      '<div class="hv-entry">' +
        '<div class="hv-entry-left">' +
          '<span class="hv-icon hv-icon--analyse">' +
            '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' +
              '<circle cx="6" cy="6" r="4"/><path d="M11 11l3 3"/>' +
            '</svg>' +
          '</span>' +
        '</div>' +
        '<div class="hv-entry-body">' +
          '<div class="hv-entry-title">' + _hEsc(e.jd_snippet || 'Analysis') + '</div>' +
          '<div class="hv-entry-meta">' +
            slot + _hEsc(e.resume_label || 'Resume') +
            ' &middot; ' + _hAgo(e.scored_at) +
          '</div>' +
        '</div>' +
        '<div class="hv-entry-right">' +
          '<span class="hv-score ' + tier + '">' + Math.round(e.score) + '%</span>' +
        '</div>' +
      '</div>'
    );
  }).join('');
}

// ── Fetcher tab ───────────────────────────────────────────

function _hvParseFetchDetail(raw) {
  try {
    var d = JSON.parse(raw || '{}');
    if (typeof d === 'object' && d !== null && 'fetched' in d) return d;
  } catch (e) {}
  // Fallback: old "X checked, Y relevant, Z scored" string format
  var parts = (raw || '').match(/(\d+) checked.*?(\d+) relevant.*?(\d+) scored/);
  return parts
    ? { fetched: '?', new: '?', recent: parseInt(parts[1]), relevant: parseInt(parts[2]),
        scored: parseInt(parts[3]), adzuna: '?', arbeitnow: '?', total_seen: '?' }
    : { fetched: '?', new: '?', recent: '?', relevant: '?', scored: 0,
        adzuna: '?', arbeitnow: '?', total_seen: '?' };
}

function _hvFetcherEntry(e) {
  var d = _hvParseFetchDetail(e.detail);
  var scored = d.scored != null ? d.scored : 0;

  var sources = '';
  if (d.adzuna !== '?') {
    sources = '<span class="hv-src-row">' +
      '<span class="hv-src-badge hv-src-az">Adzuna ' + d.adzuna + '</span>' +
      '<span class="hv-src-badge hv-src-arb">Arbeitnow ' + d.arbeitnow + '</span>' +
      '</span>';
  }

  var stats = [
    d.fetched !== '?' ? '<b>' + d.fetched + '</b> fetched' : null,
    d.new     !== '?' ? '<b>' + d.new     + '</b> new'     : null,
    d.recent  !== '?' ? '<b>' + d.recent  + '</b> recent'  : null,
    d.relevant !== '?' ? '<b>' + d.relevant + '</b> passed filter' : null,
    '<b>' + scored + '</b> scored',
    d.total_seen !== '?' ? d.total_seen + ' total seen' : null,
  ].filter(Boolean).join(' &middot; ');

  return (
    '<div class="hv-entry hv-entry--fetch">' +
      '<div class="hv-entry-left">' +
        '<span class="hv-icon hv-icon--fetch">' +
          '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' +
            '<path d="M1 8a7 7 0 1 0 14 0"/><path d="M8 1v6l3 3"/>' +
          '</svg>' +
        '</span>' +
      '</div>' +
      '<div class="hv-entry-body">' +
        '<div class="hv-entry-title">' +
          'Fetcher run &middot; <span class="hv-run-time">' + _hTime(e.created_at) + '</span>' +
        '</div>' +
        '<div class="hv-entry-meta">' + stats + '</div>' +
        (sources ? '<div class="hv-entry-meta hv-entry-sources">' + sources + '</div>' : '') +
      '</div>' +
      '<div class="hv-entry-right">' +
        (scored > 0
          ? '<span class="hv-fetch-badge">+' + scored + '</span>'
          : '<span class="hv-fetch-badge hv-fetch-badge--zero">0</span>') +
      '</div>' +
    '</div>'
  );
}

function _hTime(iso) {
  if (!iso) return '';
  var d = new Date(iso);
  if (isNaN(d)) return iso.slice(0, 16).replace('T', ' ');
  return d.toLocaleString(undefined, {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

function _hvRenderFetcher(entries) {
  var el = document.getElementById('hv-fetcher');
  if (!el) return;
  if (!entries.length) {
    el.innerHTML = '<p class="hv-empty">No fetcher runs yet. Go to Job Matches and click Run.</p>';
    return;
  }
  el.innerHTML = entries.map(_hvFetcherEntry).join('');
}

// ── Applications tab ──────────────────────────────────────

function _hvRenderApplications(entries) {
  var el = document.getElementById('hv-applications');
  if (!el) return;
  if (!entries.length) {
    el.innerHTML = '<p class="hv-empty">No applications tracked yet. Mark jobs as Applied in Job Matches.</p>';
    return;
  }
  el.innerHTML = entries.map(function(e) {
    var tier = e.score != null ? _hTierCls(e.score) : '';
    var link = e.url
      ? ' &middot; <a class="hv-entry-link" href="' + _hEsc(e.url) + '" target="_blank" rel="noopener">View posting</a>'
      : '';
    return (
      '<div class="hv-entry">' +
        '<div class="hv-entry-left">' +
          '<span class="hv-icon hv-icon--apply">' +
            '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' +
              '<path d="M13 2H3a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V3a1 1 0 0 0-1-1z"/>' +
              '<path d="M5 8l2 2 4-4"/>' +
            '</svg>' +
          '</span>' +
        '</div>' +
        '<div class="hv-entry-body">' +
          '<div class="hv-entry-title">' + _hEsc(e.title || 'Role') + '</div>' +
          '<div class="hv-entry-meta">' +
            _hEsc(e.company || '') +
            ' &middot; Applied ' + _hAgo(e.applied_at) +
            link +
          '</div>' +
        '</div>' +
        (e.score != null
          ? '<div class="hv-entry-right"><span class="hv-score ' + tier + '">' + Math.round(e.score) + '%</span></div>'
          : '') +
      '</div>'
    );
  }).join('');
}

// ── Badge ─────────────────────────────────────────────────

function _hvUpdateBadge(count) {
  var badge = document.getElementById('sb-badge-history');
  if (!badge) return;
  badge.textContent = count > 0 ? String(count) : '';
  badge.style.display = count > 0 ? '' : 'none';
}

// ── Init ──────────────────────────────────────────────────
(function() { hvLoad(); })();
