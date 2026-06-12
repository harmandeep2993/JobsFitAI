// assets/js/analysis.js

// ── Step indicator (top progress bar) ────────────────────
function setStep(n) {
  var labels = ['Upload', 'Job Description', 'Analysing', 'Results'];
  var parts = labels.map(function(lbl, i) {
    var num = i + 1;
    var done = num < n, act = num === n;
    var nc = done ? 's-done' : (act ? 's-act' : 's-todo');
    var lc = done ? 'sl-done' : (act ? 'sl-act' : 'sl-todo');
    var txt = done ? '&#10003;' : String(num);
    return '<div class="step-pill"><div class="step-num ' + nc + '">' + txt + '</div>' +
           '<span class="step-lbl ' + lc + '">' + lbl + '</span></div>' +
           (num < 4 ? '<div class="step-sep"></div>' : '');
  }).join('');
  var el = document.querySelector('.steps');
  if (el) el.outerHTML = '<div class="steps">' + parts + '</div>';
}

// ── Analysis progress stepper ─────────────────────────────
var _azTimers = [];

var AZ_STEPS = [
  { label: 'Reading resume',           sub: 'Extracting text and skills from your file'      },
  { label: 'Parsing job description',  sub: 'Identifying requirements and keywords'           },
  { label: 'Computing semantic match', sub: 'Comparing your profile against the role'         },
  { label: 'Generating report',        sub: 'Building skill gaps and recommendations'         },
];

// Approximate real timing (ms from request start) for each step becoming active.
// Steps auto-advance so something is always moving while the LLM works.
var AZ_TIMINGS = [0, 1800, 3600, 5800];

function renderProgress() {
  var box = document.getElementById('spinner');
  if (!box) return;
  var dots = AZ_STEPS.map(function(_, i) {
    return '<span class="az-dot' + (i === 0 ? ' active' : '') + '" id="az-dot-' + i + '"></span>';
  }).join('');
  box.innerHTML =
    '<div class="az-progress-inner">' +
      '<div class="az-spin-ring" id="az-spin-ring"></div>' +
      '<div class="az-status-label" id="az-status-label">' + AZ_STEPS[0].label + '&hellip;</div>' +
      '<div class="az-status-sub"   id="az-status-sub">'   + AZ_STEPS[0].sub   + '</div>' +
      '<div class="az-stage-dots">' + dots + '</div>' +
    '</div>';
  box.style.display = 'flex';
}

function _fadeText(el, text) {
  if (!el) return;
  el.style.opacity = '0';
  setTimeout(function() {
    el.textContent = text;
    el.style.opacity = '1';
  }, 150);
}

function setAzStep(i, state) {
  if (state !== 'active') return;
  var labelEl = document.getElementById('az-status-label');
  var subEl   = document.getElementById('az-status-sub');
  var countEl = document.getElementById('az-step-count');
  _fadeText(labelEl, AZ_STEPS[i].label + '…');
  _fadeText(subEl,   AZ_STEPS[i].sub);
  if (countEl) countEl.textContent = (i + 1) + ' / ' + AZ_STEPS.length;
  for (var j = 0; j < AZ_STEPS.length; j++) {
    var dot = document.getElementById('az-dot-' + j);
    if (dot) dot.className = 'az-dot' + (j === i ? ' active' : (j < i ? ' done' : ''));
  }
}

function startProgress() {
  _azTimers.forEach(clearTimeout);
  _azTimers = [];
  renderProgress();
  for (var i = 1; i < AZ_STEPS.length; i++) {
    (function(idx) {
      _azTimers.push(setTimeout(function() {
        setAzStep(idx, 'active');
      }, AZ_TIMINGS[idx]));
    })(i);
  }
}

function completeProgress(cb) {
  _azTimers.forEach(clearTimeout);
  _azTimers = [];
  var labelEl = document.getElementById('az-status-label');
  var subEl   = document.getElementById('az-status-sub');
  var ring    = document.getElementById('az-spin-ring');
  for (var i = 0; i < AZ_STEPS.length; i++) {
    var dot = document.getElementById('az-dot-' + i);
    if (dot) dot.className = 'az-dot done';
  }
  _fadeText(labelEl, 'Analysis complete');
  _fadeText(subEl,   'Building your results…');
  if (ring) ring.classList.add('az-spin-done');
  setTimeout(function() {
    var box = document.getElementById('spinner');
    if (box) { box.style.opacity = '0'; box.style.transition = 'opacity .2s ease'; }
    setTimeout(function() {
      if (box) box.style.display = 'none';
      if (cb) cb();
    }, 220);
  }, 650);
}

function hideProgress() {
  _azTimers.forEach(clearTimeout);
  _azTimers = [];
  var box = document.getElementById('spinner');
  if (box) { box.style.opacity = ''; box.style.transition = ''; box.style.display = 'none'; }
}

// ── JD validation ─────────────────────────────────────────
function checkJD() {
  var jd = document.getElementById('jd-input');
  if (!jd) return;
  if (jd.value.trim().length > 30) {
    if (!jd.classList.contains('success')) { jd.classList.add('success'); setStep(2); }
  } else {
    jd.classList.remove('success');
  }
}

// ── Persistent result cache (localStorage, survives refresh) ─
var _CACHE_LS_KEY = 'jfai_cache';
var _CACHE_MAX    = 5;

function _cacheGet(key) {
  try {
    var store = JSON.parse(localStorage.getItem(_CACHE_LS_KEY) || 'null');
    return (store && store[key]) ? store[key] : null;
  } catch(e) { return null; }
}

function _cacheSet(key, html) {
  try {
    var store = JSON.parse(localStorage.getItem(_CACHE_LS_KEY) || 'null') || {};
    var keys  = Object.keys(store);
    while (keys.length >= _CACHE_MAX) { delete store[keys.shift()]; }
    store[key] = html;
    localStorage.setItem(_CACHE_LS_KEY, JSON.stringify(store));
  } catch(e) {}
}

// ── Results placeholder HTML (restored by runAgain) ──────
var RES_PLACEHOLDER =
  '<div class="res-placeholder">' +
  '<div class="res-empty-body">' +
  '<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">' +
  '<rect x="3" y="12" width="4" height="9" rx="1"/>' +
  '<rect x="10" y="5" width="4" height="16" rx="1"/>' +
  '<rect x="17" y="8" width="4" height="13" rx="1"/>' +
  '</svg>' +
  '<p>Upload your resume and paste a job description,<br>then click <strong>Analyse Match</strong> to see your results</p>' +
  '</div>' +
  '</div>';

// ── Analysis trigger ──────────────────────────────────────
window.startAnalysis = function() {
  var jdEl = document.getElementById('jd-input');
  var jd   = jdEl ? jdEl.value.trim() : '';

  if (jd.length < 50)                             { toast('Paste a job description (at least 50 characters).', 'warn'); return; }
  if (!window._resumeId && !window._resumeTmp)    { toast('Select or upload a resume first.', 'warn'); return; }

  // Cache hit — keyed on stable file fingerprint so it survives page refresh
  var fingerprint = window._resumeFingerprint || window._resumeId || window._resumeTmp || '';
  var cacheKey    = fingerprint + '::' + jd;
  var cached      = _cacheGet(cacheKey);
  if (cached) {
    var resultsEl = document.getElementById('jf-results');
    if (resultsEl) {
      resultsEl.innerHTML = cached;
      animateResRing();
      animateBdRings();
    }
    toast('Showing cached result — inputs unchanged', 'info', 3000);
    return;
  }

  var btn = document.getElementById('analyse-btn');
  if (btn) { btn.disabled = true; btn.style.opacity = '.45'; }

  var resultsEl = document.getElementById('jf-results');

  setStep(3);
  startProgress();

  // Send resume_id (persistent store) or fall back to tmp (legacy temp path)
  var resumePayload = window._resumeId
    ? { resume_id: window._resumeId }
    : { tmp: window._resumeTmp };

  fetch('/api/analyze', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(Object.assign({ jd: jd }, resumePayload)),
  })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (!d.ok) {
        var msgs = {
          'resume_extraction_failed': 'Could not extract resume — check the file or try a different one.',
          'jd_extraction_failed':     'Could not extract the job description — add more text.',
          'could not parse resume':   'Could not parse resume — check the file format.',
          'llm_unavailable':          'LLM provider is unavailable. Check your API key in Settings.',
        };
        hideProgress();
        toast(msgs[d.error] || 'Analysis failed: ' + (d.error || 'unknown error'), 'err', 5000);
        return;
      }

      completeProgress(function() {
        setStep(4);
        if (resultsEl) {
          resultsEl.innerHTML = d.html;
          animateResRing();
          animateBdRings();
          _cacheSet(cacheKey, d.html);
        }
        toast('Analysis complete — ' + Math.round(d.score) + '% match (' + d.label + ')', 'ok', 4000);
      });
    })
    .catch(function(e) {
      hideProgress();
      toast('Request failed: ' + e, 'err');
    })
    .finally(function() {
      if (btn) { btn.disabled = false; btn.style.opacity = '1'; }
    });
};

// ── Results tab switching ─────────────────────────────────
window.jfTab = function(el, panelId) {
  document.querySelectorAll('#jf-tab-row .tab-item').forEach(function(t) {
    t.classList.remove('active');
  });
  document.querySelectorAll('.jf-panel').forEach(function(p) {
    p.style.display = 'none';
  });
  el.classList.add('active');
  var panel = document.getElementById(panelId);
  if (panel) panel.style.display = 'block';
};

// ── Ring animations (sidebar score + breakdown rings) ─────
function animateResRing() { animateBdRings(); }

function animateBdRings() {
  var circ = 106.81;
  function ease(t) { return t < 0.5 ? 4*t*t*t : 1 - Math.pow(-2*t+2, 3)/2; }
  document.querySelectorAll('#jf-summary .jt-gauge-arc[data-offset], #jf-breakdown .jt-gauge-arc[data-offset]').forEach(function(arc) {
    var target = parseFloat(arc.getAttribute('data-offset'));
    var start  = null, dur = 750;
    (function animate(ts) {
      if (!start) start = ts;
      var p = Math.min((ts - start) / dur, 1);
      arc.style.strokeDashoffset = circ - (circ - target) * ease(p);
      if (p < 1) requestAnimationFrame(animate);
    })(performance.now());
  });
}

// ── Breakdown accordion toggles ───────────────────────────
window.bdToggle = function(item) {
  if (!item) return;
  var open = item.getAttribute('data-open') === 'true';
  item.setAttribute('data-open', open ? 'false' : 'true');
  // sync expand-all button label
  var panel = item.closest('#jf-breakdown');
  if (panel) {
    var btn   = panel.querySelector('.bd-expand-all');
    var items = panel.querySelectorAll('.bd-item');
    var anyOpen = Array.from(items).some(function(i) {
      return i.getAttribute('data-open') === 'true';
    });
    if (btn) btn.textContent = anyOpen ? 'Collapse all' : 'Expand all';
  }
};

window.bdToggleAll = function(btn) {
  var list    = btn.closest('#jf-breakdown');
  if (!list) return;
  var items   = list.querySelectorAll('.bd-item');
  var anyOpen = Array.from(items).some(function(i) {
    return i.getAttribute('data-open') === 'true';
  });
  items.forEach(function(item) {
    item.setAttribute('data-open', anyOpen ? 'false' : 'true');
  });
  btn.textContent = anyOpen ? 'Expand all' : 'Collapse all';
};

// ── Run Again (keep resume, clear JD + results) ──────────
window.runAgain = function() {
  _azTimers.forEach(clearTimeout);
  _azTimers = [];
  var jdEl    = document.getElementById('jd-input');
  var results = document.getElementById('jf-results');
  var spinner = document.getElementById('spinner');
  var btn     = document.getElementById('analyse-btn');

  if (jdEl)    { jdEl.value = ''; jdEl.classList.remove('success'); }
  if (results) { results.innerHTML = RES_PLACEHOLDER; }
  if (spinner) { spinner.style.display = 'none'; }
  if (btn)     { btn.disabled = false; btn.style.opacity = '1'; }
  if (typeof updateCounter === 'function') updateCounter(0);

  var card = document.querySelector('.az-workspace, .card');
  if (card) card.scrollIntoView({ behavior: 'smooth', block: 'start' });
  if (jdEl) setTimeout(function() { jdEl.focus(); }, 350);
};

// ── Bindings ──────────────────────────────────────────────
(function bindJD() {
  var jd = document.getElementById('jd-input');
  if (jd) {
    jd.addEventListener('input', checkJD);
    jd.addEventListener('paste', function() { setTimeout(checkJD, 10); });
  } else { setTimeout(bindJD, 50); }
})();

(function bindAnalyse() {
  var btn = document.getElementById('analyse-btn');
  if (btn) { btn.addEventListener('click', startAnalysis); }
  else { setTimeout(bindAnalyse, 50); }
})();

document.addEventListener('keydown', function(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    var v = document.getElementById('view-analyzer');
    if (v && v.classList.contains('active')) startAnalysis();
  }
});
