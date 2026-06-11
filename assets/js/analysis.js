// assets/js/analysis.js
// JD validation + analysis trigger
// Calls POST /api/analyze; no NiceGUI dependency.

// ── Step indicator ────────────────────────────────────────
function setStep(n) {
  const labels = ['Upload', 'Job Description', 'Analysing', 'Results'];
  const parts  = labels.map(function(lbl, i) {
    const num  = i + 1;
    const done = num < n;
    const act  = num === n;
    const nc   = done ? 's-done' : (act ? 's-act'  : 's-todo');
    const lc   = done ? 'sl-done': (act ? 'sl-act' : 'sl-todo');
    const txt  = done ? '&#10003;' : String(num);
    return '<div class="step-pill"><div class="step-num ' + nc + '">' + txt + '</div>' +
           '<span class="step-lbl ' + lc + '">' + lbl + '</span></div>' +
           (num < 4 ? '<div class="step-sep"></div>' : '');
  }).join('');
  const el = document.querySelector('.steps');
  if (el) el.outerHTML = '<div class="steps">' + parts + '</div>';
}

// ── JD validation ─────────────────────────────────────────
function checkJD() {
  const jd = document.getElementById('jd-input');
  if (!jd) return;
  const text = jd.value.trim();
  if (text.length > 30) {
    if (!jd.classList.contains('success')) {
      jd.classList.add('success');
      setStep(2);
    }
  } else {
    jd.classList.remove('success');
  }
}

// ── Analysis trigger ──────────────────────────────────────
window.startAnalysis = function() {
  const jdEl = document.getElementById('jd-input');
  const jd   = jdEl ? jdEl.value.trim() : '';

  if (jd.length < 50) {
    alert('Please paste a job description (at least 50 characters).');
    return;
  }
  if (!window._resumeTmp) {
    alert('Please upload a resume file first.');
    return;
  }

  const btn     = document.getElementById('analyse-btn');
  const spinner = document.getElementById('spinner');
  const spinTxt = document.getElementById('spin-text');

  setStep(3);
  if (spinner) spinner.style.display = 'flex';
  if (btn) { btn.disabled = true; btn.style.opacity = '.45'; }
  if (spinTxt) spinTxt.textContent = 'Analysing…';

  const payload = { tmp: window._resumeTmp, jd: jd };

  fetch('/api/analyze', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(payload),
  })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (!d.ok) {
        var msg = {
          'resume_extraction_failed': 'Could not extract resume — check the file or try a different one.',
          'jd_extraction_failed':     'Could not extract job description — make sure it contains enough text.',
          'could not parse resume':   'Could not parse resume — check the file format.',
          'llm_unavailable':          'LLM provider is not available. Check your API key in Settings.',
        }[d.error] || ('Analysis failed: ' + (d.error || 'unknown error'));
        alert(msg);
        return;
      }

      setStep(4);

      var r = document.getElementById('jf-results');
      if (r) {
        r.innerHTML = d.html;
        r.style.display = 'block';
      }

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
    })
    .catch(function(e) {
      alert('Request failed: ' + e);
    })
    .finally(function() {
      if (spinner) spinner.style.display = 'none';
      if (btn) { btn.disabled = false; btn.style.opacity = '1'; }
      window._resumeTmp  = null;
      window._resumeName = null;
    });
};

// ── Bind JD textarea ──────────────────────────────────────
(function bindJD() {
  var jd = document.getElementById('jd-input');
  if (jd) {
    jd.addEventListener('input', checkJD);
    jd.addEventListener('paste', function() { setTimeout(checkJD, 10); });
  } else {
    setTimeout(bindJD, 50);
  }
})();

// ── Bind analyse button ───────────────────────────────────
(function bindAnalyse() {
  var btn = document.getElementById('analyse-btn');
  if (btn) {
    btn.addEventListener('click', startAnalysis);
  } else {
    setTimeout(bindAnalyse, 50);
  }
})();
