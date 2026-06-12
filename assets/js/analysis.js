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
  box.innerHTML =
    '<div class="az-progress">' +
    AZ_STEPS.map(function(s, i) {
      return '<div class="az-step pending" id="az-step-' + i + '">' +
        '<div class="az-step-icon"><span class="az-step-num">' + (i + 1) + '</span></div>' +
        '<div class="az-step-body">' +
          '<div class="az-step-label">' + s.label + '</div>' +
          '<div class="az-step-sub">' + s.sub + '</div>' +
        '</div>' +
      '</div>';
    }).join('') +
    '</div>';
  box.style.display = 'block';
}

function setAzStep(i, state) {
  var el = document.getElementById('az-step-' + i);
  if (!el) return;
  el.className = 'az-step ' + state;
  var icon = el.querySelector('.az-step-icon');
  var sub  = el.querySelector('.az-step-sub');
  if (state === 'active') {
    if (icon) icon.innerHTML = '<span class="az-step-num">' + (i + 1) + '</span>';
    if (sub)  sub.textContent = AZ_STEPS[i].sub;
  } else if (state === 'done') {
    if (icon) icon.innerHTML = '<span class="az-step-check">&#10003;</span>';
    if (sub)  sub.textContent = 'Done';
  }
}

function startProgress() {
  _azTimers.forEach(clearTimeout);
  _azTimers = [];
  renderProgress();
  setAzStep(0, 'active');
  for (var i = 1; i < AZ_STEPS.length; i++) {
    (function(idx) {
      _azTimers.push(setTimeout(function() {
        setAzStep(idx - 1, 'done');
        setAzStep(idx, 'active');
      }, AZ_TIMINGS[idx]));
    })(i);
  }
}

function completeProgress(cb) {
  _azTimers.forEach(clearTimeout);
  _azTimers = [];
  // Snap all remaining steps to done in quick succession for visual satisfaction
  var delay = 0;
  for (var i = 0; i < AZ_STEPS.length; i++) {
    (function(idx, d) {
      setTimeout(function() { setAzStep(idx, 'done'); }, d);
    })(i, delay);
    delay += 120;
  }
  setTimeout(function() {
    var box = document.getElementById('spinner');
    if (box) box.style.display = 'none';
    if (cb) cb();
  }, delay + 300);
}

function hideProgress() {
  _azTimers.forEach(clearTimeout);
  _azTimers = [];
  var box = document.getElementById('spinner');
  if (box) box.style.display = 'none';
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

// ── Analysis trigger ──────────────────────────────────────
window.startAnalysis = function() {
  var jdEl = document.getElementById('jd-input');
  var jd   = jdEl ? jdEl.value.trim() : '';

  if (jd.length < 50)        { toast('Paste a job description (at least 50 characters).', 'warn'); return; }
  if (!window._resumeTmp)    { toast('Upload a resume file first.', 'warn'); return; }

  var btn = document.getElementById('analyse-btn');
  if (btn) { btn.disabled = true; btn.style.opacity = '.45'; }

  var resultsEl = document.getElementById('jf-results');
  if (resultsEl) { resultsEl.style.display = 'none'; }

  setStep(3);
  startProgress();

  fetch('/api/analyze', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ tmp: window._resumeTmp, jd: jd }),
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
        if (resultsEl) { resultsEl.innerHTML = d.html; resultsEl.style.display = 'block'; }
        toast('Analysis complete — ' + Math.round(d.score) + '% match (' + d.label + ')', 'ok', 4000);
      });
    })
    .catch(function(e) {
      hideProgress();
      toast('Request failed: ' + e, 'err');
    })
    .finally(function() {
      if (btn) { btn.disabled = false; btn.style.opacity = '1'; }
      window._resumeTmp  = null;
      window._resumeName = null;
    });
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
