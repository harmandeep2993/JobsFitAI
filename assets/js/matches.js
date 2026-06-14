// assets/js/matches.js
// Job Matches dashboard - load a resume once, fetch German jobs from
// Arbeitnow, score each against the resume, and show a ranked list.
// Supports auto-refresh that scores only newly-seen jobs.


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

// Human-friendly "time since fetched" from an ISO timestamp string (scored_at).
function fetchedAgo(scored_at) {
  if (!scored_at) return '';
  const d = new Date(scored_at);
  if (isNaN(d.getTime())) return '';
  const mins = Math.floor((Date.now() - d.getTime()) / 60000);
  if (mins < 1)   return 'just now';
  if (mins < 60)  return mins + 'm ago';
  const hrs = Math.floor(mins / 60);
  if (hrs < 24)   return hrs + 'h ago';
  const days = Math.floor(hrs / 24);
  if (days < 7)   return days + 'd ago';
  return Math.floor(days / 7) + 'w ago';
}

// === Load current state (resume + stored results) ===
window.loadMatchState = function() {
  fetch('/api/match/state')
    .then(r => r.json())
    .then(d => {
      if (!d.ok) return;
      setResumeStatus(d.has_resume, d.resume_name);
      renderStats(d.stats);
      renderResume(d.resume);
      renderScheduler(d.scheduler);
      renderFilters(d.filters);
      // Restore "New" highlights from the last fetch run (survives page reload).
      var threshold = localStorage.getItem('jfa_run_threshold') || '';
      var newIds = threshold
        ? new Set((d.results || []).filter(function(r) {
            return r.scored_at && r.scored_at > threshold;
          }).map(function(r) { return r.id; }))
        : new Set();
      renderMatches(d.results || [], newIds);
    })
    .catch(() => {});
};

// Uploaded resume + the info extracted from it.
// Store the resume and just show/hide the "View Resume Details" button.
window.renderResume = function renderResume(r) {
  const btn = document.getElementById('mt-resume-btn');
  window._resumeInfo = (r && r.name) ? r : null;
  if (btn) btn.style.display = window._resumeInfo ? 'inline-flex' : 'none';
};

function resumeHTML(r) {
  const skills = (r.skills || []).slice(0, 30).map(s =>
    '<span class="rz-chip">' + mtEsc(s) + '</span>').join('');
  const exp = (r.experience || []).map(e =>
    '<div class="rz-row"><span class="rz-role">' + mtEsc(e.title || '') + '</span>' +
    '<span class="rz-co">' + mtEsc(e.company || '') + '</span>' +
    '<span class="rz-dt">' + mtEsc(e.start || '') + '-' + mtEsc(e.end || '') +
    ' (' + (e.years || 0) + 'y)</span></div>').join('');
  const edu = (r.education || []).map(e =>
    '<div class="rz-row">' + mtEsc((e.degree || '') + ' ' + (e.field || '')) +
    ' · ' + mtEsc(e.institution || '') + '</div>').join('');
  const langs = (r.languages || []).map(mtEsc).join(', ');
  const certs = (r.certifications || []).map(mtEsc).join(', ');

  return '' +
    '<div class="dt-head">' +
      '<div><div class="dt-title">📄 ' + mtEsc(r.name) + '</div>' +
        '<div class="dt-sub">' + mtEsc(r.title || '') +
          (r.total_years ? ' · ' + r.total_years + 'y experience' : '') + '</div></div>' +
      '<button class="dt-close" id="detail-close" onclick="closeDetail(event)">✕</button>' +
    '</div>' +
    (skills ? '<div class="rz-sec"><div class="rz-label">Skills</div><div class="rz-chips">' + skills + '</div></div>' : '') +
    (exp   ? '<div class="rz-sec"><div class="rz-label">Experience</div>' + exp + '</div>' : '') +
    (edu   ? '<div class="rz-sec"><div class="rz-label">Education</div>' + edu + '</div>' : '') +
    (langs ? '<div class="rz-sec"><div class="rz-label">Languages</div><div class="rz-row">' + langs + '</div></div>' : '') +
    (certs ? '<div class="rz-sec"><div class="rz-label">Certifications</div><div class="rz-row">' + certs + '</div></div>' : '');
}

window.openResume = function() {
  const r = window._resumeInfo;
  const modal = document.getElementById('detail-modal');
  const box = document.getElementById('detail-box');
  if (!r || !modal || !box) return;
  box.innerHTML = resumeHTML(r);
  modal.style.display = 'flex';
};

// Background scheduler control.
function schedLabel(m) {
  return '● ON · every ' + (m >= 60 ? (m / 60) + 'h' : m + 'm');
}

function renderScheduler(s) {
  s = s || {};
  const cb = document.getElementById('mt-sched');
  const iv = document.getElementById('mt-sched-interval');
  const st = document.getElementById('mt-sched-status');
  if (cb) cb.checked = !!s.enabled;
  if (iv && s.interval) iv.value = String(s.interval);
  if (st) {
    st.textContent = s.enabled ? schedLabel(s.interval) : '○ off';
    st.className = 'mt-status ' + (s.enabled ? 'ok' : '');
  }
}

window.toggleScheduler = function() {
  const on = document.getElementById('mt-sched').checked;
  const interval = parseInt(document.getElementById('mt-sched-interval').value, 10) || 60;
  const st = document.getElementById('mt-sched-status');
  st.textContent = '…';
  fetch('/api/match/scheduler', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ enabled: on, interval: interval }),
  })
    .then(r => r.json())
    .then(d => {
      if (!d.ok) { st.textContent = '✕'; return; }
      st.textContent = d.enabled ? schedLabel(d.interval) : '○ off';
      st.className = 'mt-status ' + (d.enabled ? 'ok' : '');
    })
    .catch(() => { st.textContent = '✕'; });
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

// Editable filter panel - built once so polling doesn't clobber edits.
function renderFilters(f) {
  if (!f) return;
  window._filtersData = f;
  const box = document.getElementById('mt-filters');
  if (!box || window._filtersRendered) return;
  window._filtersRendered = true;

  window._titles = (f.target_titles || []).slice();
  box.innerHTML =
    '<div class="set-row"><label class="set-lbl">Countries</label>' +
      '<input id="flt-countries" class="fetch-inp" value="' +
        mtEsc((f.countries || []).join(', ')) +
        '" placeholder="germany, netherlands, belgium"/></div>' +
    '<div class="set-row"><label class="set-lbl">Location</label>' +
      '<input id="flt-location" class="fetch-inp" value="' + mtEsc(f.location || '') +
        '" placeholder="city (optional) - blank = whole country"/></div>' +
    '<div class="set-row" style="align-items:flex-start;">' +
      '<label class="set-lbl">Target titles</label>' +
      '<div class="kw-wrap" id="kw-wrap"></div></div>' +
    '<div class="set-row"><label class="set-lbl"></label>' +
      '<input id="flt-newtitle" class="fetch-inp" placeholder="add a role keyword"/>' +
      '<button class="btn-ghost" onclick="addTitle()">Add</button></div>' +
    '<div class="set-actions"><button class="btn-primary" onclick="saveFilters()">Save</button>' +
      '<span class="mt-status" id="flt-status">≤ ' + f.max_age_days +
        ' days old · LLM relevance + entry-level gate</span></div>';
  rerenderChips();
}

function rerenderChips() {
  const w = document.getElementById('kw-wrap');
  if (!w) return;
  w.innerHTML = (window._titles || []).map((t, i) =>
    '<span class="kw-chip">' + mtEsc(t) +
    '<button class="kw-x" onclick="removeTitle(' + i + ')" title="remove">✕</button></span>'
  ).join('');
}

window.removeTitle = function(i) { window._titles.splice(i, 1); rerenderChips(); };

window.addTitle = function() {
  const el = document.getElementById('flt-newtitle');
  const v = (el.value || '').trim().toLowerCase();
  if (v && !window._titles.includes(v)) { window._titles.push(v); el.value = ''; rerenderChips(); }
};

window.saveFilters = function() {
  const st = document.getElementById('flt-status');
  st.textContent = 'Saving…';
  fetch('/api/match/filters', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      target_titles: window._titles,
      countries:     document.getElementById('flt-countries').value,
      location:      document.getElementById('flt-location').value,
    }),
  })
    .then(r => r.json())
    .then(d => {
      if (!d.ok) { st.textContent = '✕ save failed'; return; }
      window._titles = d.target_titles;
      rerenderChips();
      st.textContent = '✓ Saved · ' + d.target_titles.length + ' titles · ' +
        ((d.countries || []).join(', ') || 'germany') +
        (d.location ? ' · ' + d.location : '');
    })
    .catch(() => { st.textContent = '✕ save error'; });
};

window.toggleFilters = function() {
  const p = document.getElementById('mt-filters');
  const t = document.getElementById('mt-filters-toggle');
  const show = p.style.display === 'none';
  p.style.display = show ? 'block' : 'none';
  if (t) {
    t.innerHTML = '⚙ Filters &amp; keywords ' + (show ? '▾' : '▸');
    t.setAttribute('aria-expanded', show ? 'true' : 'false');
  }
};

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

// === Resume upload ===
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
      if (typeof loadMatchState === 'function') loadMatchState();
      const poll = document.getElementById('mt-poll-status');
      if (poll && d.rescored) {
        poll.textContent = '✓ re-scored ' + d.rescored + ' jobs against the new resume';
        poll.className = 'mt-status ok';
      }
      if (d.diff) renderResumeDiff(d.diff);
    })
    .catch(e => {
      status.textContent = '✕ ' + e.message;
      status.className = 'mt-status err';
    });
}

// === Fetch & score (streams results as the funnel runs) ===
window.runMatch = function() {
  const status = document.getElementById('mt-poll-status');
  const btn    = document.getElementById('mt-run-btn');
  const query  = document.getElementById('mt-query').value.trim();
  const entry  = document.getElementById('mt-entry');
  const entryOnly = entry ? entry.checked : true;

  if (btn) btn.disabled = true;
  status.textContent = 'Starting…';
  status.className = 'mt-status';
  renderSkeletons(6);
  setTopbarRunning(true, 'Starting…');

  // Record run start - scored_at values after this are flagged "New" even after reload.
  localStorage.setItem('jfa_run_threshold', new Date(Date.now() - 3000).toISOString().slice(0, 19));

  // Snapshot current ids so everything scored this run is flagged NEW.
  fetch('/api/match/state')
    .then(r => r.json())
    .then(prev => {
      window._preRunIds = new Set((prev.results || []).map(x => x.id));
      const url = '/api/match/run'
        + '?query='      + encodeURIComponent(query)
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
      _pollAttempts = 0;
      pollRun();   // results stream in as the funnel scores them
    })
    .catch(e => {
      if (btn) btn.disabled = false;
      status.textContent = '✕ ' + e;
      status.className = 'mt-status err';
    });
};

// Poll run progress and re-render; new jobs appear (highlighted) as scored.
// Stops after MAX_POLL_ATTEMPTS to prevent infinite loops if backend stalls.
var _pollAttempts = 0;
var MAX_POLL_ATTEMPTS = 150; // 150 × 2 s = 5 minutes max

function setTopbarRunning(running, label) {
  var dot = document.getElementById('tb-run-dot');
  var lbl = document.getElementById('tb-run-label');
  if (dot) dot.style.display = running ? 'flex' : 'none';
  if (lbl && label) lbl.textContent = label;
}

function setTopbarFetchTime() {
  var el = document.getElementById('tb-fetch-time');
  if (el) el.textContent = 'Last fetch ' + new Date().toLocaleTimeString();
}

function pollRun() {
  const status = document.getElementById('mt-poll-status');
  const btn    = document.getElementById('mt-run-btn');

  _pollAttempts++;
  if (_pollAttempts > MAX_POLL_ATTEMPTS) {
    if (btn) btn.disabled = false;
    status.textContent = '✕ Timed out - run took too long. Try again.';
    status.className = 'mt-status err';
    setTopbarRunning(false);
    return;
  }

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
        var phaseText =
          rs.phase === 'fetching'    ? 'Fetching jobs…' :
          rs.phase === 'classifying' ? 'Filtering ' + (rs.total || 0) + ' jobs…' :
          'Scoring ' + (rs.scored || 0) + '/' + (rs.total || 0) + '…';
        status.className  = 'mt-status';
        status.textContent = phaseText;
        setTopbarRunning(true, phaseText);
        setTimeout(pollRun, 2000);
      } else {
        _pollAttempts = 0;
        if (btn) btn.disabled = false;
        status.textContent = '✓ ' + newIds.size + ' new · ' +
                             (d.results || []).length + ' total · ' +
                             new Date().toLocaleTimeString();
        status.className = 'mt-status ok';
        setTopbarRunning(false);
        setTopbarFetchTime();
        if (newIds.size > 0) toast(newIds.size + ' new job' + (newIds.size === 1 ? '' : 's') + ' scored', 'ok', 3000);
      }
    })
    .catch(() => {
      _pollAttempts = 0;
      if (btn) btn.disabled = false;
      status.textContent = '✕ Connection lost. Check server and try again.';
      status.className = 'mt-status err';
      setTopbarRunning(false);
    });
}

// === SVG gauge ring builder ===
var GAUGE_R    = 17;
var GAUGE_CIRC = +(2 * Math.PI * GAUGE_R).toFixed(2); // 106.81

function gaugeHTML(cls, pct, label) {
  var offset = +(GAUGE_CIRC * (1 - Math.max(0, Math.min(100, pct)) / 100)).toFixed(2);
  return '<div class="jt-score">' +
    '<svg class="jt-gauge" viewBox="0 0 44 44" aria-hidden="true">' +
      '<circle class="jt-gauge-bg" cx="22" cy="22" r="' + GAUGE_R + '"/>' +
      '<circle class="jt-gauge-arc ' + cls + '" cx="22" cy="22" r="' + GAUGE_R + '" ' +
        'stroke-dasharray="' + GAUGE_CIRC + '" ' +
        'stroke-dashoffset="' + GAUGE_CIRC + '" ' +
        'data-offset="' + offset + '"/>' +
    '</svg>' +
    '<span class="jt-score-val ' + cls + '">' + label + '</span>' +
  '</div>';
}

// === Render ranked matches ===
// Shared thumbnail card builder, reused by Matches and History views.
window.matchCardHTML = function(r, isNew) {
  const posted  = relTime(r.posted_at);
  const fetched = fetchedAgo(r.scored_at);
  const applied = !!r.applied;
  const pending = r.status === 'pending';
  const noJd    = r.status === 'jd_unavailable';

  const lc = labelClass(r.label, r.score);

  // SVG gauge ring - arc length reflects actual score
  const scoreVal = Math.round(r.score || 0);
  const badge = pending
    ? gaugeHTML('sc-na', 0, '…')
    : noJd
      ? gaugeHTML('sc-na', 0, 'JD?')
      : gaugeHTML(lc, scoreVal, scoreVal + '%');

  // Inline chips next to company name
  const chips =
    (isNew   ? '<span class="match-new">NEW</span>' : '') +
    (noJd    ? '<span class="match-na-tag">manual</span>' : '') +
    (applied ? '<span class="match-applied-tag">Applied</span>' : '');

  // Skill tags - 4 matched (green) + 4 missing (red)
  let skillsHTML = '';
  if (!noJd && !pending) {
    const mTags = (r.matched_required || []).slice(0, 4)
      .map(s => '<span class="tag tg">' + mtEsc(s) + '</span>').join('');
    const xTags = (r.missing_required || []).slice(0, 4)
      .map(s => '<span class="tag tr">' + mtEsc(s) + '</span>').join('');
    skillsHTML = mTags + xTags;
  } else if (noJd) {
    skillsHTML = '<span class="jt-na-hint">Paste JD to score</span>';
  } else {
    skillsHTML = '<span class="jt-na-hint">Scoring…</span>';
  }

  // Single meta line: date . lang . source
  const metaParts = [
    posted     ? posted        : null,
    r.language || null,
    r.source   || null,
  ].filter(Boolean);

  // Footer actions
  const detailBtn = noJd
    ? '<button class="jt-btn jt-btn-primary" onclick="openJdModal(\'' + mtEsc(r.id) + '\')">Paste JD</button>'
    : '<button class="jt-btn jt-btn-primary" onclick="openDetail(\'' + mtEsc(r.id) + '\')">Analyze</button>';

  const openBtn = r.url
    ? '<a class="jt-btn" href="' + mtEsc(r.url) + '" target="_blank" rel="noopener">Open ↗</a>'
    : '';

  const applyBtn =
    '<button class="jt-btn jt-apply' + (applied ? ' on' : '') +
    '" onclick="toggleApplied(\'' + mtEsc(r.id) + '\',' + (applied ? 1 : 0) + ')">' +
    (applied ? '✓ Applied' : 'Applied?') + '</button>';

  const delBtn =
    '<button class="jt-del" onclick="deleteMatch(\'' + mtEsc(r.id) + '\')" title="Remove">' +
      '<svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' +
        '<path d="M2 4h12"/><path d="M5 4V2h6v2"/><path d="M3 4l1 10h8l1-10"/><path d="M6.5 7v4M9.5 7v4"/>' +
      '</svg>' +
    '</button>';

  return '' +
    '<div class="job-thumb' +
        (isNew    ? ' is-new'    : '') +
        (applied  ? ' is-applied': '') +
        (noJd     ? ' is-na'     : '') + '">' +

      '<div class="jt-body">' +
        '<div class="jt-title-row">' +
          '<div class="jt-title">' + mtEsc(r.title || '') + '</div>' +
          badge +
        '</div>' +
        (r.location ? '<div class="jt-loc">&#128205; ' + mtEsc(r.location) + '</div>' : '') +
        '<div class="jt-company-row">' +
          '<span class="jt-company">' + mtEsc(r.company || 'Unknown') + '</span>' +
          (chips ? '<span class="jt-chips">' + chips + '</span>' : '') +
        '</div>' +
        (metaParts.length
          ? '<div class="jt-meta">' + metaParts.join(' &middot; ') + '</div>'
          : '') +
        '<div class="jt-skills">' + skillsHTML + '</div>' +
      '</div>' +

      '<div class="jt-foot">' +
        detailBtn + openBtn + applyBtn +
        '<div class="jt-foot-r">' + delBtn + '</div>' +
      '</div>' +

    '</div>';
};

window.deleteMatch = function(id) {
  fetch('/api/match/delete', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ id: id }),
  })
    .then(r => r.json())
    .then(d => { if (d.ok) loadMatchState(); })
    .catch(() => {});
};

window.clearAllMatches = function() {
  // Two-click confirmation: first click arms, second fires
  var btn = document.querySelector('.mt-clear');
  if (!btn) return;
  if (btn.dataset.armed !== 'yes') {
    btn.dataset.armed = 'yes';
    btn.textContent = '⚠ Confirm clear?';
    btn.style.color = 'var(--red)';
    setTimeout(function() {
      btn.dataset.armed = '';
      btn.textContent = '🗑 Clear all';
      btn.style.color = '';
    }, 3000);
    return;
  }
  btn.dataset.armed = '';
  btn.textContent = '🗑 Clear all';
  btn.style.color = '';
  fetch('/api/match/clear', { method: 'POST' })
    .then(r => r.json())
    .then(d => {
      if (d.ok) { loadMatchState(); toast('All matches cleared.', 'ok'); }
    })
    .catch(function() { toast('Clear failed - check server.', 'err'); });
};

// === Detail / "more analysis" modal ===
window.openDetail = function(id) {
  const modal = document.getElementById('detail-modal');
  const box   = document.getElementById('detail-box');
  if (!modal || !box) return;
  box.innerHTML = '<div class="fetch-empty">Loading analysis…</div>';
  modal.style.display = 'flex';

  fetch('/api/match/detail?id=' + encodeURIComponent(id))
    .then(r => r.json())
    .then(d => {
      if (!d.ok) { box.innerHTML = '<div class="fetch-empty">Not found.</div>'; return; }
      box.innerHTML = renderDetail(d);
    })
    .catch(() => { box.innerHTML = '<div class="fetch-empty">Error loading analysis.</div>'; });
};

window.closeDetail = function(ev) {
  // Close only when clicking the overlay or the close button.
  if (ev && ev.target && ev.target.id !== 'detail-modal' && ev.target.id !== 'detail-close') return;
  const modal = document.getElementById('detail-modal');
  if (modal) modal.style.display = 'none';
};

function bar(label, val) {
  const v = Math.round(val || 0);
  return '<div class="dt-bar-row"><span class="dt-bar-l">' + label + '</span>' +
    '<span class="dt-bar"><span class="dt-bar-fill ' + scoreBarClass(v) +
    '" style="width:' + v + '%"></span></span><span class="dt-bar-v">' + v + '%</span></div>';
}
function scoreBarClass(v) {
  return v >= 80 ? 'sc-exc' : v >= 60 ? 'sc-good' : v >= 40 ? 'sc-partial' : 'sc-poor';
}

function renderDetail(d) {
  const j  = d.job || {};
  const ss = d.section_scores || {};
  const jd = d.jd || {};
  const rz = d.resume || {};

  const order = [
    ['Required skills', 'required_skills'], ['Responsibilities', 'responsibilities'],
    ['Experience', 'experience'], ['Education', 'education'],
    ['Preferred skills', 'preferred_skills'], ['Languages', 'languages'],
    ['Certifications', 'certifications'],
  ];
  const bars = order.filter(([_, k]) => k in ss).map(([l, k]) => bar(l, ss[k])).join('');

  const matched = (d.matched_required || []).map(mtEsc).join(', ') || '-';
  const missing = (d.missing_required || []).map(mtEsc).join(', ') || '-';
  const jdReq   = (jd.required_skills || []).map(mtEsc).join(', ') || '-';
  const jdResp  = (jd.responsibilities || []).slice(0, 8).map(x => '<li>' + mtEsc(x) + '</li>').join('');

  return '' +
    '<div class="dt-head">' +
      '<div><div class="dt-title">' + mtEsc(j.title || '') + '</div>' +
        '<div class="dt-sub">' + mtEsc(j.company || '') +
        (j.location ? ' · ' + mtEsc(j.location) : '') + '</div></div>' +
      '<div class="match-score ' + labelClass(j.label, j.score) + '">' +
        Math.round(j.score || 0) + '<span class="match-score-pct">%</span></div>' +
      '<button class="dt-close" id="detail-close" onclick="closeDetail(event)">✕</button>' +
    '</div>' +
    (d.summary ? '<div class="dt-summary">' + mtEsc(d.summary) + '</div>' : '') +
    '<div class="dt-grid">' +
      '<div class="dt-col">' +
        '<div class="dt-h">Match breakdown</div>' + bars +
        '<div class="dt-h">Skills</div>' +
        '<div class="dt-skill"><span class="ok">✓ have:</span> ' + matched + '</div>' +
        '<div class="dt-skill"><span class="miss">✗ missing:</span> ' + missing + '</div>' +
      '</div>' +
      '<div class="dt-col">' +
        '<div class="dt-h">Job requirements</div>' +
        '<div class="dt-skill"><b>Required:</b> ' + jdReq + '</div>' +
        (jdResp ? '<div class="dt-h">Responsibilities</div><ul class="dt-ul">' + jdResp + '</ul>' : '') +
        '<div class="dt-h">Your resume</div>' +
        '<div class="dt-skill">' + mtEsc(rz.title || '') +
          (rz.total_years ? ' · ' + rz.total_years + 'y' : '') + '</div>' +
        '<div class="dt-skill">' + (rz.skills || []).slice(0, 18).map(mtEsc).join(', ') + '</div>' +
      '</div>' +
    '</div>' +
    (j.url ? '<a class="btn-primary" href="' + mtEsc(j.url) + '" target="_blank" rel="noopener" style="margin-top:14px;">Open posting ↗</a>' : '');
}

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

// Active client-side filters (updated by onScoreFilter / onLangFilter).
window._mtMinScore   = 0;
window._mtLang       = '';
window._mtAllData    = [];
window._mtShowNew     = false;   // show only "New" jobs
window._mtHideApplied = false;   // hide applied jobs
window._mtMaxAge      = 'all';   // published within N days ('all' = no limit)
window._mtSource      = 'all';   // job source ('all', 'adzuna', 'arbeitnow')

// === Sort ===
window._mtSort = 'score';

window.setSort = function(s) {
  window._mtSort = s;
  document.querySelectorAll('.sort-btn[data-sort]').forEach(function(btn) {
    btn.classList.toggle('active', btn.dataset.sort === s);
  });
  renderMatches(window._mtAllData, window._mtLastNewIds || new Set());
};

window.setMtAge = function(days) {
  window._mtMaxAge = days;
  document.querySelectorAll('.sort-btn[data-age]').forEach(function(btn) {
    btn.classList.toggle('active', btn.dataset.age === String(days));
  });
  renderMatches(window._mtAllData, window._mtLastNewIds || new Set());
};

window.setMtScore = function(min) {
  window._mtMinScore = min;
  document.querySelectorAll('.sort-btn[data-score]').forEach(function(btn) {
    btn.classList.toggle('active', btn.dataset.score === String(min));
  });
  renderMatches(window._mtAllData, window._mtLastNewIds || new Set());
};

window.setMtSource = function(src) {
  window._mtSource = src;
  document.querySelectorAll('.sort-btn[data-src]').forEach(function(btn) {
    btn.classList.toggle('active', btn.dataset.src === src);
  });
  renderMatches(window._mtAllData, window._mtLastNewIds || new Set());
};

window.toggleMtNew = function() {
  window._mtShowNew = !window._mtShowNew;
  var btn = document.getElementById('mt-fn-btn');
  if (btn) btn.classList.toggle('active', window._mtShowNew);
  renderMatches(window._mtAllData, window._mtLastNewIds || new Set());
};

window.toggleMtApplied = function() {
  window._mtHideApplied = !window._mtHideApplied;
  var btn = document.getElementById('mt-fa-btn');
  if (btn) btn.classList.toggle('active', window._mtHideApplied);
  renderMatches(window._mtAllData, window._mtLastNewIds || new Set());
};

// === Skeleton loading ===
function renderSkeletons(n) {
  const box = document.getElementById('mt-results');
  if (!box) return;
  var html = '';
  for (var i = 0; i < (n || 6); i++) {
    html +=
      '<div class="sk-card">' +
        '<div class="sk-line sk-score"></div>' +
        '<div class="sk-line sk-title"></div>' +
        '<div class="sk-line sk-sub"></div>' +
        '<div class="sk-line sk-meta"></div>' +
        '<div class="sk-line sk-tags"></div>' +
        '<div class="sk-line sk-foot"></div>' +
      '</div>';
  }
  box.innerHTML = html;
}

// === Gauge arc fill animation ===
function animateScores() {
  document.querySelectorAll('.jt-gauge-arc[data-offset]').forEach(function(arc) {
    var circ   = parseFloat(arc.getAttribute('stroke-dasharray'));
    var target = parseFloat(arc.dataset.offset);
    var duration = 700;
    var startTime = null;
    function step(ts) {
      if (!startTime) startTime = ts;
      var progress = Math.min((ts - startTime) / duration, 1);
      var eased    = 1 - Math.pow(1 - progress, 3);
      arc.setAttribute('stroke-dashoffset', circ - eased * (circ - target));
      if (progress < 1) requestAnimationFrame(step);
      else arc.removeAttribute('data-offset');
    }
    requestAnimationFrame(step);
  });
}

window.onLangFilter = function() {
  const el = document.getElementById('flt-lang');
  window._mtLang = el ? el.value : '';
  renderMatches(window._mtAllData, window._mtLastNewIds || new Set());
};

function renderMatches(results, newIds) {
  window._mtAllData    = results;
  window._mtLastNewIds = newIds;
  const box = document.getElementById('mt-results');
  if (!box) return;
  newIds = newIds || new Set();

  // Apply all client-side filters.
  const minScore    = window._mtMinScore   || 0;
  const lang        = window._mtLang       || '';
  const showNew     = window._mtShowNew;
  const hideApplied = window._mtHideApplied;
  const maxAge      = window._mtMaxAge;
  const source      = window._mtSource     || 'all';
  const nowSec      = Date.now() / 1000;

  const filtered = results.filter(function(r) {
    if (r.status === 'jd_unavailable') return true;
    if ((r.score || 0) < minScore) return false;
    if (lang && (r.language || '') !== lang) return false;
    if (showNew && !newIds.has(r.id)) return false;
    if (hideApplied && r.applied) return false;
    if (source !== 'all' && (r.source || '') !== source) return false;
    if (maxAge !== 'all') {
      var ts = parseInt(r.posted_at, 10) || 0;
      if (ts && (nowSec - ts) > maxAge * 86400) return false;
    }
    return true;
  });

  // Update sidebar badge - unreviewed (unapplied, scored) jobs
  var unreviewed = results.filter(function(r) { return !r.applied && r.status !== 'pending'; }).length;
  var badge = document.getElementById('sb-badge-matches');
  if (badge) {
    badge.textContent = unreviewed > 0 ? String(unreviewed) : '';
    badge.style.display = unreviewed > 0 ? '' : 'none';
  }

  // Show sort row when there are any results
  var sortRow = document.getElementById('sort-row');
  if (sortRow) sortRow.style.display = results.length ? 'flex' : 'none';

  // Update result count
  var countEl = document.getElementById('mt-result-count');
  if (countEl) {
    countEl.textContent = filtered.length < results.length
      ? filtered.length + ' of ' + results.length
      : results.length + ' jobs';
  }

  if (!filtered.length) {
    const msg = results.length
      ? 'No jobs match the current filters.'
      : 'No matches yet. Load a resume and click Fetch &amp; Score.';
    box.innerHTML = '<div class="fetch-empty">' + msg + '</div>';
    return;
  }

  // Sort - new jobs always float to top in score mode
  const sort = window._mtSort || 'score';
  const ordered = filtered.slice().sort(function(a, b) {
    const an = newIds.has(a.id) ? 1 : 0;
    const bn = newIds.has(b.id) ? 1 : 0;
    if (sort === 'score' && an !== bn) return bn - an;
    if (sort === 'score')   return (b.score || 0) - (a.score || 0);
    if (sort === 'fetched') return (b.scored_at || '').localeCompare(a.scored_at || '');
    return 0;
  });

  box.innerHTML = ordered.map(function(r) {
    return window.matchCardHTML(r, newIds.has(r.id));
  }).join('');

  requestAnimationFrame(animateScores);
}

// === Resume diff banner ===
function renderResumeDiff(diff) {
  if (!diff) return;

  const added   = diff.skills_added   || [];
  const removed = diff.skills_removed || [];
  const expAdd  = diff.exp_added      || [];
  const expRem  = diff.exp_removed    || [];
  const yrBefore = diff.years_before  || 0;
  const yrAfter  = diff.years_after   || 0;

  if (!added.length && !removed.length && !expAdd.length && !expRem.length && yrBefore === yrAfter) return;

  const chip = function(text, cls) {
    return '<span class="tag ' + cls + '" style="font-size:11px;">' + mtEsc(text) + '</span>';
  };

  var rows = [];

  if (added.length)
    rows.push('<div><strong>Skills added:</strong> ' + added.map(s => chip(s, 'tg')).join(' ') + '</div>');
  if (removed.length)
    rows.push('<div><strong>Skills removed:</strong> ' + removed.map(s => chip(s, 'tr')).join(' ') + '</div>');
  if (expAdd.length)
    rows.push('<div><strong>Experience added:</strong> ' + expAdd.map(function(e) {
      return chip(e.replace('|', ' @ '), 'tg'); }).join(' ') + '</div>');
  if (expRem.length)
    rows.push('<div><strong>Experience removed:</strong> ' + expRem.map(function(e) {
      return chip(e.replace('|', ' @ '), 'tr'); }).join(' ') + '</div>');
  if (yrBefore !== yrAfter)
    rows.push('<div><strong>Experience years:</strong> ' + yrBefore + 'y &rarr; ' + yrAfter + 'y</div>');

  const banner = document.createElement('div');
  banner.className = 'content-card';
  banner.style.cssText = 'margin-bottom:12px;border-left:3px solid var(--blue);padding:12px 16px;font-size:13px;';
  banner.innerHTML =
    '<div style="font-weight:600;margin-bottom:8px;">Resume updated - what changed</div>' +
    rows.join('') +
    '<button onclick="this.parentElement.remove()" style="margin-top:8px;font-size:11px;background:none;border:none;cursor:pointer;opacity:.6;">dismiss</button>';

  const results = document.getElementById('mt-results');
  if (results) results.before(banner);
}

// === JD paste modal (for jd_unavailable cards) ===
window.openJdModal = function(id) {
  var job    = (window._mtAllData || []).find(function(r) { return r.id === id; }) || {};
  var modal  = document.getElementById('jd-modal');
  var title  = document.getElementById('jd-modal-title');
  var sub    = document.getElementById('jd-modal-sub');
  var input  = document.getElementById('jd-modal-input');
  var status = document.getElementById('jd-modal-status');
  var btn    = document.getElementById('jd-modal-btn');
  if (!modal) return;
  window._jdModalId = id;
  if (title)  title.textContent  = job.title   || 'Paste Job Description';
  if (sub)    sub.textContent    = job.company  || '';
  if (input)  input.value        = '';
  if (status) { status.textContent = ''; status.className = 'mt-status'; }
  if (btn)    { btn.disabled = false; btn.textContent = 'Score this job'; }
  modal.style.display = 'flex';
  setTimeout(function() { if (input) input.focus(); }, 60);
};

window.closeJdModal = function(ev) {
  if (ev && ev.target && ev.target.id !== 'jd-modal') return;
  document.getElementById('jd-modal').style.display = 'none';
};

window.confirmJdModal = function() {
  document.getElementById('jd-modal').style.display = 'none';
};

window.submitJd = function() {
  var id     = window._jdModalId;
  var input  = document.getElementById('jd-modal-input');
  var btn    = document.getElementById('jd-modal-btn');
  var status = document.getElementById('jd-modal-status');
  var text   = (input ? input.value : '').trim();

  if (text.length < 50) {
    if (status) { status.textContent = 'Too short - paste the full job description.'; status.className = 'mt-status err'; }
    return;
  }

  if (btn)    { btn.disabled = true; btn.textContent = 'Scoring…'; }
  if (status) { status.textContent = ''; status.className = 'mt-status'; }

  fetch('/api/match/score-jd', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ id: id, jd_text: text }),
  })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (!d.ok) {
        if (btn) { btn.disabled = false; btn.textContent = 'Score this job'; }
        var msg = d.error === 'no_resume' ? 'Load a resume first.' : (d.error || 'Scoring failed.');
        if (status) { status.textContent = '✕ ' + msg; status.className = 'mt-status err'; }
        return;
      }
      // Show result panel; OK button will close the modal
      var score = Math.round(d.score || 0);
      var badge = document.getElementById('jd-res-badge');
      var lbl   = document.getElementById('jd-res-label');
      var res   = document.getElementById('jd-modal-result');
      var hint  = document.getElementById('jd-modal-hint');
      if (badge) badge.textContent = score + '%';
      if (lbl)   lbl.textContent   = d.label || '';
      // colour-code the badge using existing label classes
      if (badge) badge.className = 'jd-res-badge ' + labelClass(d.label, d.score);
      // hide the form, show the result
      if (document.getElementById('jd-modal-input')) document.getElementById('jd-modal-input').style.display = 'none';
      if (document.getElementById('jd-modal-foot'))  document.getElementById('jd-modal-foot').style.display  = 'none';
      if (hint) hint.style.display = 'none';
      if (res)  res.style.display  = 'flex';
      loadMatchState();
    })
    .catch(function(e) {
      if (btn) { btn.disabled = false; btn.textContent = 'Score this job'; }
      if (status) { status.textContent = '✕ ' + e; status.className = 'mt-status err'; }
    });
};

// === Bind ===
(function bindMatches() {
  const file = document.getElementById('mt-file');
  if (file) {
    file.addEventListener('change', () => uploadMatchResume(file.files[0]));
    loadMatchState();
  } else {
    setTimeout(bindMatches, 80);
  }
})();
