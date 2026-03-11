// assets/js/analysis.js
// JD validation + analysis trigger
// Communicates with Python via NiceGUI emitEvent()

// Check JD textarea content
// Adds success styling when enough text is present
// Emits jd_added event once on first valid input
function checkJD() {
  const jd = document.getElementById('jd-input');
  if (!jd) return;

  const text = jd.value.trim();

  if (text.length > 30) {
    if (!jd.classList.contains('success')) {
      jd.classList.add('success');

      if (typeof emitEvent === 'function') {
        emitEvent('jd_added', {});
      }
    }
  } else {
    jd.classList.remove('success');
  }
}

// Trigger full analysis
// Validates inputs then emits run_analysis to Python
window.startAnalysis = function() {
  const jdEl = document.getElementById('jd-input');
  const jd   = jdEl ? jdEl.value.trim() : '';

  if (jd.length < 50) {
    alert('Please paste a job description.');
    return;
  }

  if (!window._resumeTmp) {
    alert('Please upload a resume file first.');
    return;
  }

  window._jdText = jd;

  if (typeof emitEvent === 'function') {
    emitEvent('run_analysis');
  }
};

// Bind JD textarea events
// Retry IIFE — element may not exist yet
(function bindJD() {
  const jd = document.getElementById('jd-input');

  if (jd) {
    jd.addEventListener('input', checkJD);
    jd.addEventListener('paste', () => setTimeout(checkJD, 10));
  } else {
    setTimeout(bindJD, 50);
  }
})();

// Bind analyse button
// Retry IIFE — button may not exist yet
(function bindAnalyse() {
  const btn = document.getElementById('analyse-btn');

  if (btn) {
    btn.addEventListener('click', startAnalysis);
  } else {
    setTimeout(bindAnalyse, 50);
  }
})();