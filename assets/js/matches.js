// assets/js/matches.js
// Job Matches dashboard — load a resume once, fetch German jobs from
// Arbeitnow, score each against the resume, and show a ranked list.
// Supports auto-refresh that scores only newly-seen jobs.

window._matchPoll = null;

function mtEsc(s) {
  return (s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;')
                  .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// Badge color follows the match label (falls back to score thresholds).
function labelClass(label, score) {
  const l = (label || '').toLowerCase();
  if (l.includes('excellent')) return 'sc-exc';
  if (l.includes('good'))      return 'sc-good';
  if (l.includes('partial'))   return 'sc-partial';
  if (l.includes('poor'))      return 'sc-poor';
  if (score >= 80) return 'sc-exc';
  if (score >= 60) return 'sc-good';
  if (score >= 40) return 'sc-partial';
  return 'sc-poor';
}

// Human-friendly "time since published" from a unix-epoch string.
function relTime(posted) {
  const ts = parseInt(posted, 10);
  if (!ts) return '';
  const days = Math.floor((Date.now() / 1000 - ts) / 86400);
  if (days <= 0)  return 'today';
  if (days === 1) return '1 day ago';
  if (days < 7)   return days + ' days ago';
  const weeks = Math.floor(days / 7);
  if (weeks < 5)  return weeks + (weeks === 1 ? ' week ago' : ' weeks ago');
  const months = Math.floor(days / 30);
  return months + (months === 1 ? ' month ago' : ' months ago');
}

// ── Load current state (resume + stored results) ──────────
window.loadMatchState = function() {
  fetch('/api/match/state')
    .then(r => r.json())
    .then(d => {
      if (!d.ok) return;
      setResumeStatus(d.has_resume, d.resume_name);
      renderStats(d.stats);
      renderFilters(d.filters);
      renderMatches(d.results || [], new Set());
    })
    .catch(() => {});
};

// Live metrics bar.
function renderStats(s) {
  const box = document.getElementById('mt-stats');
  if (!box || !s) return;
  const cards = [
    ['Seen', s.seen], ['Scored', s.scored], ['Good 60+', s.good], ['Applied', s.applied],
  ];
  box.innerHTML = cards.map(([k, v]) =>
    '<div class="stat"><div class="stat-n">' + (v || 0) + '</div>' +
    '<div class="stat-l">' + k + '</div></div>'
  ).join('');
}

// Show which keywords/rules drive the job extraction.
function renderFilters(f) {
  const box = document.getElementById('mt-filters');
  if (!box || !f) return;

  function group(label, arr, cls) {
    if (!arr || !arr.length) return '';
    return '<div class="mt-fgroup"><span class="mt-flabel">' + label + '</span>' +
      arr.map(x => '<span class="mt-chip ' + cls + '">' + mtEsc(x) + '</span>').join('') +
      '</div>';
  }

  box.innerHTML =
    group('Target titles', f.target_titles, 'tc') +
    group('Entry-level keywords', f.entry_keywords, 'ec') +
    group('Excluded (seniority)', f.exclude_keywords, 'xc') +
    '<div class="mt-fgroup"><span class="mt-flabel">Limits</span>' +
      '<span class="mt-chip">≤ ' + f.max_age_days + ' days old</span>' +
      '<span class="mt-chip">≤ ' + f.max_experience_years + ' yrs exp</span>' +
    '</div>';
}

function setResumeStatus(has, name) {
  const el = document.getElementById('mt-resume-status');
  if (!el) return;
  if (has) {
    el.textContent = '✓ ' + (name || 'resume loaded');
    el.className = 'mt-status ok';
  } else {
    el.textContent = 'No resume loaded';
    el.className = 'mt-status';
  }
}

// ── Resume upload ─────────────────────────────────────────
function uploadMatchResume(file) {
  if (!file) return;
  const status = document.getElementById('mt-resume-status');
  status.textContent = 'Uploading…';
  status.className = 'mt-status';

  const fd = new FormData();
  fd.append('file', file);

  fetch('/api/upload', { method: 'POST', body: fd })
    .then(r => r.json())
    .then(d => {
      if (!d.ok) throw new Error(d.error || 'upload failed');
      status.textContent = 'Extracting resume…';
      return fetch('/api/match/resume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tmp: d.tmp, name: d.name }),
      });
    })
    .then(r => r.json())
    .then(d => {
      if (!d.ok) throw new Error(d.error || 'extraction failed');
      setResumeStatus(true, d.name + ' · ' + d.experience_years + 'y exp');
      // New resume re-scores existing jobs — refresh the list to show it.
      if (typeof loadMatchState === 'function') loadMatchState();
      const poll = document.getElementById('mt-poll-status');
      if (poll && d.rescored) {
        poll.textContent = '✓ re-scored ' + d.rescored + ' jobs against the new resume';
        poll.className = 'mt-status ok';
      }
    })
    .catch(e => {
      status.textContent = '✕ ' + e.message;
      status.className = 'mt-status err';
    });
}

// ── Fetch & score (streams results as the funnel runs) ────
window.runMatch = function() {
  const status = document.getElementById('mt-poll-status');
  const btn    = document.getElementById('mt-run-btn');
  const query  = document.getElementById('mt-query').value.trim();
  const loc    = document.getElementById('mt-loc').value.trim();
  const entry  = document.getElementById('mt-entry');
  const entryOnly = entry ? entry.checked : true;

  if (btn) btn.disabled = true;
  status.textContent = 'Starting…';
  status.className = 'mt-status';

  // Snapshot current ids so everything scored this run is flagged NEW.
  fetch('/api/match/state')
    .then(r => r.json())
    .then(prev => {
      window._preRunIds = new Set((prev.results || []).map(x => x.id));
      const url = '/api/match/run'
        + '?query='      + encodeURIComponent(query)
        + '&location='   + encodeURIComponent(loc)
        + '&entry_only=' + (entryOnly ? 'true' : 'false');
      return fetch(url);
    })
    .then(r => r.json())
    .then(d => {
      if (!d.ok) {
        if (btn) btn.disabled = false;
        status.textContent = d.error === 'no_resume'
          ? '✕ Load a resume first' : '✕ ' + (d.error || 'failed');
        status.className = 'mt-status err';
        return;
      }
      pollRun();   // results stream in as the funnel scores them
    })
    .catch(e => {
      if (btn) btn.disabled = false;
      status.textContent = '✕ ' + e;
      status.className = 'mt-status err';
    });
};

// Poll run progress and re-render; new jobs appear (highlighted) as scored.
function pollRun() {
  const status = document.getElementById('mt-poll-status');
  const btn    = document.getElementById('mt-run-btn');

  fetch('/api/match/state')
    .then(r => r.json())
    .then(d => {
      if (!d.ok) return;
      renderStats(d.stats);

      const pre = window._preRunIds || new Set();
      const newIds = new Set((d.results || []).filter(r => !pre.has(r.id)).map(r => r.id));
      renderMatches(d.results || [], newIds);

      const rs = d.run_status || {};
      if (rs.running) {
        status.className = 'mt-status';
        status.textContent = rs.phase === 'fetching'
          ? 'Fetching jobs…'
          : 'Scoring… ' + (rs.scored || 0) + ' found · ' +
            (rs.checked || 0) + '/' + (rs.total || 0) + ' checked';
        setTimeout(pollRun, 2000);
      } else {
        if (btn) btn.disabled = false;
        status.textContent = '✓ ' + newIds.size + ' new · ' +
                             (d.results || []).length + ' total · ' +
                             new Date().toLocaleTimeString();
        status.className = 'mt-status ok';
      }
    })
    .catch(() => { if (btn) btn.disabled = false; });
}

// ── Render ranked matches ─────────────────────────────────
// Shared match-card builder, reused by the Matches and History views.
window.matchCardHTML = function(r, isNew) {
  const matched = (r.matched_required || []).slice(0, 5).map(mtEsc).join(', ');
  const missing = (r.missing_required || []).slice(0, 5).map(mtEsc).join(', ');
  const posted  = relTime(r.posted_at);
  const applied = !!r.applied;
  return '' +
    '<div class="match-card' + (isNew ? ' is-new' : '') + (applied ? ' is-applied' : '') + '">' +
      '<div class="match-top">' +
        '<div class="match-score ' + labelClass(r.label, r.score) + '">' +
          Math.round(r.score) + '<span class="match-score-pct">%</span>' +
        '</div>' +
        (isNew ? '<span class="match-new">✨ NEW</span>' : '') +
        (applied ? '<span class="match-applied-tag">✓ Applied</span>' : '') +
      '</div>' +
      '<div class="match-title">' + mtEsc(r.title) + '</div>' +
      '<div class="match-meta">' +
        mtEsc(r.company || 'Unknown') +
        (r.location ? ' · ' + mtEsc(r.location) : '') +
      '</div>' +
      '<div class="match-sub">' +
        (posted ? '🕒 ' + posted : '') +
        (posted && r.language ? ' · ' : '') +
        (r.language ? mtEsc(r.language) : '') +
      '</div>' +
      (matched ? '<div class="match-skills"><span class="ok">✓</span> ' + matched + '</div>' : '') +
      (missing ? '<div class="match-skills"><span class="miss">✗</span> ' + missing + '</div>' : '') +
      '<div class="match-actions">' +
        (r.url ? '<a class="job-card-link" href="' + mtEsc(r.url) +
                 '" target="_blank" rel="noopener">Open ↗</a>' : '') +
        '<button class="apply-toggle' + (applied ? ' on' : '') +
          '" onclick="toggleApplied(\'' + mtEsc(r.id) + '\',' + (applied ? 1 : 0) + ')">' +
          (applied ? 'Applied ✓' : 'Mark applied') +
        '</button>' +
      '</div>' +
    '</div>';
};

// Toggle a job's applied state, then refresh whichever views are open.
window.toggleApplied = function(id, applied) {
  fetch('/api/match/applied', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ id: id, applied: !applied }),
  })
    .then(r => r.json())
    .then(d => {
      if (!d.ok) return;
      if (typeof loadMatchState === 'function') loadMatchState();
      if (typeof loadHistory === 'function') loadHistory();
    })
    .catch(() => {});
};

function renderMatches(results, newIds) {
  const box = document.getElementById('mt-results');
  if (!box) return;
  newIds = newIds || new Set();

  if (!results.length) {
    box.innerHTML = '<div class="fetch-empty">No matches yet. Load a resume and click Fetch &amp; Score.</div>';
    return;
  }

  // New jobs first, then by score within each group.
  const ordered = results.slice().sort((a, b) => {
    const an = newIds.has(a.id) ? 1 : 0;
    const bn = newIds.has(b.id) ? 1 : 0;
    if (an !== bn) return bn - an;
    return (b.score || 0) - (a.score || 0);
  });

  box.innerHTML = ordered.map(r => window.matchCardHTML(r, newIds.has(r.id))).join('');
}

// ── Auto-refresh ──────────────────────────────────────────
window.toggleAutoMatch = function() {
  const on = document.getElementById('mt-auto').checked;
  const status = document.getElementById('mt-poll-status');

  if (window._matchPoll) {
    clearInterval(window._matchPoll);
    window._matchPoll = null;
  }

  if (on) {
    const secs = parseInt(document.getElementById('mt-interval').value, 10) || 300;
    runMatch();
    window._matchPoll = setInterval(runMatch, secs * 1000);
    status.textContent = 'Auto-refresh on (every ' + (secs / 60) + ' min)';
    status.className = 'mt-status ok';
  } else {
    status.textContent = 'Auto-refresh off';
    status.className = 'mt-status';
  }
};

// ── Bind ──────────────────────────────────────────────────
(function bindMatches() {
  const file = document.getElementById('mt-file');
  if (file) {
    file.addEventListener('change', () => uploadMatchResume(file.files[0]));
    loadMatchState();
  } else {
    setTimeout(bindMatches, 80);
  }
})();
