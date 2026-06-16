// assets/js/ats.js
// ATS Score view - check a resume against ATS keyword, section, and formatting requirements.

var _atsInitDone = false;
var _atsResumeId = null;  // currently selected resume id

var ATS_SLOT_LABELS = ['Base', 'Tailored 1', 'Tailored 2'];

// === Escape helpers ===
function _atsEsc(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function _atsEscAttr(str) {
  return String(str).replace(/&/g, '&amp;').replace(/"/g, '&quot;');
}

// === Init ===
window.atInit = function() {
  var view = document.getElementById('view-ats');
  if (!view) return;

  if (!_atsInitDone) {
    _atsInitDone = true;
    view.innerHTML = _atsBuildShell();
    _atsBindJD();
  }

  _atsLoadResumes();
};

function _atsBuildShell() {
  return (
    '<div class="az-hero">' +
      '<div class="az-hero-icon" aria-hidden="true">' +
        '<svg width="20" height="20" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">' +
          '<path d="M8 1L2 4v4c0 3.3 2.5 5.8 6 7 3.5-1.2 6-3.7 6-7V4L8 1z"/>' +
          '<polyline points="5,8.5 7,10.5 11,5.5"/>' +
        '</svg>' +
      '</div>' +
      '<div>' +
        '<h1 class="az-hero-title">ATS <em>Score</em></h1>' +
        '<p class="az-hero-sub">Check whether your resume will pass ATS filters - exact keyword matches from the job description, required section headings, and formatting flags</p>' +
      '</div>' +
    '</div>' +

    '<div class="ats-workspace">' +

      '<div class="ats-panel ats-panel-resume">' +
        '<div class="az-panel-hd">' +
          '<span class="az-pnum">01</span>' +
          '<span class="az-plbl">Resume</span>' +
        '</div>' +
        '<div id="ats-resume-picker" class="ats-picker-body">' +
          '<div class="ats-picker-loading">Loading resumes&hellip;</div>' +
        '</div>' +
      '</div>' +

      '<div class="ats-panel ats-panel-jd">' +
        '<div class="az-panel-hd">' +
          '<span class="az-pnum">02</span>' +
          '<span class="az-plbl">Job Description</span>' +
          '<span class="jd-counter ats-jd-counter" id="ats-jd-counter">0 / 5000</span>' +
          '<button class="az-pact az-pact-jd" onclick="atsClearJD()">Clear</button>' +
        '</div>' +
        '<div class="jd-wrap ats-jd-wrap">' +
          '<div class="jd-empty-icon" aria-hidden="true">' +
            '<svg width="30" height="34" viewBox="0 0 30 34" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' +
              '<rect x="2" y="5" width="26" height="27" rx="3"/>' +
              '<rect x="9" y="1" width="12" height="7" rx="2"/>' +
              '<line x1="8" y1="15" x2="22" y2="15"/>' +
              '<line x1="8" y1="20" x2="22" y2="20"/>' +
              '<line x1="8" y1="25" x2="16" y2="25"/>' +
            '</svg>' +
          '</div>' +
          '<textarea id="ats-jd-input" class="jd-box ats-jd-box"' +
            ' placeholder="Paste the full job description here&hellip;">' +
          '</textarea>' +
        '</div>' +
        '<div class="ats-cta">' +
          '<button class="ats-run-btn" id="ats-scan-btn" onclick="atCheck()" disabled>' +
            'Analyse' +
            '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
              '<path d="M3 8h10M9 4l4 4-4 4"/>' +
            '</svg>' +
          '</button>' +
        '</div>' +
      '</div>' +

    '</div>' +

    '<div id="ats-results"></div>'
  );
}

// === Resume picker ===
function _atsLoadResumes() {
  fetch('/api/resumes')
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (!d.ok) return;
      _atsRenderPicker(d.resumes || []);
    })
    .catch(function() {
      var picker = document.getElementById('ats-resume-picker');
      if (picker) picker.innerHTML = '<div class="ats-picker-empty">Could not load resumes.</div>';
    });
}

function _atsRenderPicker(resumes) {
  var picker = document.getElementById('ats-resume-picker');
  if (!picker) return;

  if (!resumes || resumes.length === 0) {
    picker.innerHTML =
      '<div class="ats-picker-empty">' +
        'No resumes stored. Upload one in <strong>My Resumes</strong> first.' +
      '</div>';
    return;
  }

  var html = '<div class="az-rv-picker">';
  var multiSlot = resumes.length > 1;
  resumes.forEach(function(r) {
    var ext = r.original_name.split('.').pop().toUpperCase();
    var slotLbl = ATS_SLOT_LABELS[r.slot] || ('Slot ' + (r.slot + 1));
    var sel = (_atsResumeId === r.id) ? ' selected' : '';
    var hist = '';
    if (r.last_score != null) {
      var tierCls = r.last_score >= 80 ? 'sc-exc' : r.last_score >= 60 ? 'sc-good' : r.last_score >= 40 ? 'sc-partial' : 'sc-poor';
      hist =
        '<div class="az-rv-card-hist">' +
          '<span class="az-rv-hist-score ' + tierCls + '">' + r.last_score + '%</span>' +
          '<span class="az-rv-hist-jd">' + _atsEsc((r.last_jd || '').slice(0, 55)) + '</span>' +
        '</div>';
    }
    html += (
      '<div class="az-rv-card' + sel + '" onclick="atsSelectResume(\'' + _atsEscAttr(r.id) + '\',\'' + _atsEscAttr(r.original_name) + '\')">' +
        '<div class="az-rv-card-body">' +
          '<div class="az-rv-card-label">' + _atsEsc(slotLbl) + ' &middot; ' + _atsEsc(r.label) + '</div>' +
          '<div class="az-rv-card-name">' +
            '<span class="rv-ext-badge">' + _atsEsc(ext) + '</span>' +
            _atsEsc(r.original_name) +
          '</div>' +
          hist +
        '</div>' +
        '<div class="az-rv-card-check">' +
          '<svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">' +
            '<path d="M3 8l4 4 6-7"/>' +
          '</svg>' +
        '</div>' +
      '</div>'
    );
  });
  html += '</div>';


  picker.innerHTML = html;

  // Auto-select first if nothing selected
  if (!_atsResumeId && resumes.length > 0) {
    atsSelectResume(resumes[0].id, resumes[0].original_name);
  }
}

window.atsSelectResume = function(id, name) {
  _atsResumeId = id;
  window._atsResumeId = id;

  document.querySelectorAll('#ats-resume-picker .az-rv-card').forEach(function(c) {
    c.classList.toggle('selected', c.getAttribute('onclick').indexOf(id) !== -1);
  });

  _atsUpdateButtons();
  if (typeof toast === 'function') toast('Resume selected: ' + name, 'ok', 2000);
};

// === JD binding ===
function _atsBindJD() {
  var view = document.getElementById('view-ats');
  if (!view) return;

  view.addEventListener('input', function(e) {
    if (e.target && e.target.id === 'ats-jd-input') {
      _atsOnJDInput(e.target);
    }
  });
  view.addEventListener('paste', function(e) {
    if (e.target && e.target.id === 'ats-jd-input') {
      setTimeout(function() { _atsOnJDInput(e.target); }, 10);
    }
  });
}

function _atsOnJDInput(ta) {
  var val = ta ? ta.value : '';
  var len = val.length;
  var counter = document.getElementById('ats-jd-counter');
  if (counter) {
    counter.textContent = len + ' / 5000';
    counter.className = 'jd-counter ats-jd-counter' + (len > 4500 ? ' limit' : len > 4000 ? ' warn' : '');
  }
  _atsUpdateButtons();
}

function _atsUpdateButtons() {
  var hasRes = !!_atsResumeId;
  var scanBtn = document.getElementById('ats-scan-btn');
  if (scanBtn) scanBtn.disabled = !hasRes;
}

window.atsClearJD = function() {
  var ta = document.getElementById('ats-jd-input');
  if (ta) { ta.value = ''; _atsOnJDInput(ta); }
};

// === API calls ===
window.atCheck = function() {
  if (!_atsResumeId) { if (typeof toast === 'function') toast('Select a resume first.', 'warn'); return; }

  var results = document.getElementById('ats-results');
  if (results) results.innerHTML = '<div class="ats-loading">Analysing resume&hellip;</div>';

  var scanBtn = document.getElementById('ats-scan-btn');
  if (scanBtn) { scanBtn.disabled = true; scanBtn.textContent = 'Analysing…'; }

  var jd = (document.getElementById('ats-jd-input') || {}).value || '';

  fetch('/api/ats/check', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ resume_id: _atsResumeId, jd: jd }),
  })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (!d.ok) {
        if (results) results.innerHTML =
          '<div class="ats-error">' + _atsEsc(d.error || 'Scan failed. Please try again.') + '</div>';
        return;
      }
      atRenderCheckResults(d);
    })
    .catch(function(e) {
      if (results) results.innerHTML =
        '<div class="ats-error">Request failed: ' + _atsEsc(String(e)) + '</div>';
    })
    .finally(function() {
      _atsUpdateButtons();
      var scanBtn = document.getElementById('ats-scan-btn');
      if (scanBtn) {
        scanBtn.innerHTML =
          'Analyse' +
          '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
            '<path d="M3 8h10M9 4l4 4-4 4"/>' +
          '</svg>';
      }
    });
};

// === ATS Score card (keyword coverage only) ===
function _atsScoreCardHTML(atsScore) {
  var hasJD = atsScore && atsScore.has_jd;
  var s = (atsScore && atsScore.score != null) ? atsScore.score : null;

  if (!hasJD || s === null) {
    return (
      '<div class="ats-score-card ats-score-no-jd">' +
        '<div class="ats-score-no-jd-icon">&#128269;</div>' +
        '<div>' +
          '<div class="ats-score-no-jd-title">Paste a JD to see your ATS keyword score</div>' +
          '<div class="ats-score-no-jd-sub">ATS systems score by exact keyword matches - paste the job description above and re-run to see your score.</div>' +
        '</div>' +
      '</div>'
    );
  }

  var tierCls   = s >= 80 ? 'sc-exc' : s >= 60 ? 'sc-good' : s >= 40 ? 'sc-partial' : 'sc-poor';
  var tierColor = s >= 80 ? 'var(--green)' : s >= 60 ? 'var(--blue)' : s >= 40 ? 'var(--amber)' : 'var(--red)';
  var r = 28, circ = +(2 * Math.PI * r).toFixed(2);
  var offset = +(circ * (1 - s / 100)).toFixed(2);
  var tierLbl = s >= 80 ? 'Excellent' : s >= 60 ? 'Good' : s >= 40 ? 'Needs work' : 'Poor';

  var ring =
    '<svg class="ats-score-ring" width="76" height="76" viewBox="0 0 76 76">' +
      '<circle cx="38" cy="38" r="' + r + '" fill="none" stroke="var(--bd)" stroke-width="5"/>' +
      '<circle cx="38" cy="38" r="' + r + '" fill="none" stroke="' + tierColor + '" stroke-width="5"' +
        ' stroke-dasharray="' + circ + '" stroke-dashoffset="' + offset + '"' +
        ' stroke-linecap="round" transform="rotate(-90 38 38)"/>' +
    '</svg>' +
    '<div class="ats-score-num ' + tierCls + '">' + s + '%</div>';

  return (
    '<div class="ats-score-card">' +
      '<div class="ats-score-left">' +
        '<div class="ats-score-ring-wrap">' + ring + '</div>' +
        '<div class="ats-score-lbl">ATS Score</div>' +
      '</div>' +
      '<div class="ats-score-right">' +
        '<div class="ats-score-title ' + tierCls + '">' + tierLbl + '</div>' +
        '<div class="ats-score-desc">Your resume contains <strong>' + s + '%</strong> of the required keywords verbatim. ATS systems scan for exact strings - this is your actual keyword match rate.</div>' +
      '</div>' +
    '</div>'
  );
}

// === Keyword capsules ===
function _atsKeywordCapsulesHTML(coverage) {
  if (!coverage || !coverage.total) return '';
  var matched = coverage.matched || [];
  var missing = coverage.missing || [];
  var caps =
    matched.map(function(s) { return '<span class="kw-cap kw-cap--hit">' + _atsEsc(s) + '</span>'; }).join('') +
    missing.map(function(s) { return '<span class="kw-cap kw-cap--miss tr">' + _atsEsc(s) + '</span>'; }).join('');
  return (
    '<div class="ats-kw-block">' +
      '<div class="ats-block-hd">Required Keywords &mdash; ' + matched.length + ' of ' + coverage.total + ' found verbatim</div>' +
      '<div class="ats-kw-caps">' + caps + '</div>' +
    '</div>'
  );
}

// === Section checklist ===
function _atsSectionChecklistHTML(secFlags) {
  if (!secFlags || !secFlags.length) return '';
  var found = secFlags.filter(function(f) { return f.found; }).length;
  var rows = secFlags.map(function(f) {
    return (
      '<div class="ats-check-row' + (f.found ? '' : ' ats-check-fail') + '">' +
        '<span class="ats-check-icon">' + (f.found ? '&#10003;' : '&#10007;') + '</span>' +
        '<span class="ats-check-lbl">' + _atsEsc(f.name) + '</span>' +
        (!f.found && f.suggestion ? '<span class="ats-check-hint">' + _atsEsc(f.suggestion) + '</span>' : '') +
      '</div>'
    );
  }).join('');
  return (
    '<div class="ats-kw-block">' +
      '<div class="ats-block-hd">Section Headings &mdash; ' + found + ' of ' + secFlags.length + ' detected</div>' +
      '<div class="ats-check-list">' + rows + '</div>' +
    '</div>'
  );
}

// === Formatting checklist ===
function _atsFormattingChecklistHTML(fmtFlags) {
  if (!fmtFlags) return '';
  if (!fmtFlags.length) {
    return (
      '<div class="ats-kw-block">' +
        '<div class="ats-block-hd">Formatting</div>' +
        '<div class="ats-check-list">' +
          '<div class="ats-check-row">' +
            '<span class="ats-check-icon">&#10003;</span>' +
            '<span class="ats-check-lbl">No formatting issues detected</span>' +
          '</div>' +
        '</div>' +
      '</div>'
    );
  }
  var rows = fmtFlags.map(function(f) {
    return (
      '<div class="ats-check-row ats-check-fail">' +
        '<span class="ats-check-icon">&#9888;</span>' +
        '<span class="ats-check-lbl">' + _atsEsc(f) + '</span>' +
      '</div>'
    );
  }).join('');
  return (
    '<div class="ats-kw-block">' +
      '<div class="ats-block-hd">Formatting &mdash; ' + fmtFlags.length + ' issue' + (fmtFlags.length > 1 ? 's' : '') + '</div>' +
      '<div class="ats-check-list">' + rows + '</div>' +
    '</div>'
  );
}

// === Results rendering ===
window.atRenderCheckResults = function(d) {
  var results = document.getElementById('ats-results');
  if (!results) return;

  var html = '<div class="ats-results-inner">';

  // ATS score (keyword coverage only)
  html += _atsScoreCardHTML(d.ats_score || null);

  // Keyword capsules when JD was provided
  if (d.coverage && d.coverage.total) {
    html += _atsKeywordCapsulesHTML(d.coverage);
  }

  // Section headings checklist
  if (d.section_flags && d.section_flags.length) {
    html += _atsSectionChecklistHTML(d.section_flags);
  }

  // Formatting checklist
  html += _atsFormattingChecklistHTML(d.formatting_flags || []);

  html += '</div>';
  results.innerHTML = html;
};
