// assets/js/ats.js
// ATS Maker view - generate a complete ATS-optimised resume from a stored
// resume and a pasted job description.

var _atsInitDone  = false;
var _atsResumeId  = null;  // currently selected resume id

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
        '<h1 class="az-hero-title">ATS <em>Maker</em></h1>' +
        '<p class="az-hero-sub">Generate a complete ATS-optimised resume tailored to the job description</p>' +
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
          '<button class="ats-scan-btn" id="ats-scan-btn" onclick="atCheck()" disabled>' +
            'Quick Scan' +
          '</button>' +
          '<button class="ats-run-btn" id="ats-run-btn" onclick="atGenerate()" disabled>' +
            'Generate ATS Resume' +
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
  resumes.forEach(function(r) {
    var ext     = r.original_name.split('.').pop().toUpperCase();
    var slotLbl = ATS_SLOT_LABELS[r.slot] || ('Slot ' + (r.slot + 1));
    var sel     = (_atsResumeId === r.id) ? ' selected' : '';
    var hist    = '';
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
        '<div class="az-rv-card-left">' +
          '<span class="az-rv-slot-num">' + (r.slot + 1) + '</span>' +
        '</div>' +
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
  var val   = ta ? ta.value : '';
  var len   = val.length;
  var counter = document.getElementById('ats-jd-counter');
  if (counter) {
    counter.textContent = len + ' / 5000';
    counter.className = 'jd-counter ats-jd-counter' + (len > 4500 ? ' limit' : len > 4000 ? ' warn' : '');
  }
  _atsUpdateButtons();
}

function _atsUpdateButtons() {
  var jdEl   = document.getElementById('ats-jd-input');
  var jdLen  = jdEl ? jdEl.value.trim().length : 0;
  var hasRes = !!_atsResumeId;

  var runBtn  = document.getElementById('ats-run-btn');
  var scanBtn = document.getElementById('ats-scan-btn');

  if (runBtn)  runBtn.disabled  = !(hasRes && jdLen >= 50);
  if (scanBtn) scanBtn.disabled = !hasRes;
}

window.atsClearJD = function() {
  var ta = document.getElementById('ats-jd-input');
  if (ta) { ta.value = ''; _atsOnJDInput(ta); }
};

// === API calls ===
window.atGenerate = function() {
  var ta = document.getElementById('ats-jd-input');
  var jd = ta ? ta.value.trim() : '';

  if (!_atsResumeId) { if (typeof toast === 'function') toast('Select a resume first.', 'warn'); return; }
  if (jd.length < 50) { if (typeof toast === 'function') toast('Paste a job description (at least 50 characters).', 'warn'); return; }

  var results = document.getElementById('ats-results');
  if (results) results.innerHTML = '<div class="ats-loading">Generating ATS-optimised resume&hellip; this may take a moment.</div>';

  var runBtn = document.getElementById('ats-run-btn');
  if (runBtn) { runBtn.disabled = true; runBtn.textContent = 'Generating…'; }

  fetch('/api/ats/optimise', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ resume_id: _atsResumeId, jd: jd }),
  })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (!d.ok) {
        if (results) results.innerHTML =
          '<div class="ats-error">' + _atsEsc(d.error || 'Generation failed. Please try again.') + '</div>';
        return;
      }
      atRenderResults(d);
    })
    .catch(function(e) {
      if (results) results.innerHTML =
        '<div class="ats-error">Request failed: ' + _atsEsc(String(e)) + '</div>';
    })
    .finally(function() {
      var runBtn = document.getElementById('ats-run-btn');
      if (runBtn) {
        runBtn.disabled = false;
        runBtn.innerHTML =
          'Generate ATS Resume' +
          '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
            '<path d="M3 8h10M9 4l4 4-4 4"/>' +
          '</svg>';
      }
      _atsUpdateButtons();
    });
};

window.atCheck = function() {
  if (!_atsResumeId) { if (typeof toast === 'function') toast('Select a resume first.', 'warn'); return; }

  var results = document.getElementById('ats-results');
  if (results) results.innerHTML = '<div class="ats-loading">Scanning resume structure&hellip;</div>';

  var scanBtn = document.getElementById('ats-scan-btn');
  if (scanBtn) { scanBtn.disabled = true; scanBtn.textContent = 'Scanning…'; }

  fetch('/api/ats/check', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ resume_id: _atsResumeId }),
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
      var scanBtn = document.getElementById('ats-scan-btn');
      if (scanBtn) { scanBtn.disabled = false; scanBtn.textContent = 'Quick Scan'; }
      _atsUpdateButtons();
    });
};

// === Generate results rendering ===
window.atRenderResults = function(d) {
  var results = document.getElementById('ats-results');
  if (!results) return;

  var html = '<div class="ats-results-inner">';

  // Compact coverage stat at the top
  if (d.coverage_before && d.coverage_after) {
    html += _atsCoverageStatHTML(d.coverage_before, d.coverage_after);
  }

  // Full generated resume card (main output)
  if (d.resume) {
    html += _atsResumeHTML(d.resume, d.plain_text || '');
  }

  // Collapsible warnings - only if there are actual issues
  var missingSections = (d.section_flags || []).filter(function(f) { return !f.found; });
  var fmtFlags = d.formatting_flags || [];
  if (missingSections.length || fmtFlags.length) {
    html += _atsWarningsHTML(missingSections, fmtFlags);
  }

  html += '</div>';
  results.innerHTML = html;
};

// === Quick Scan results rendering ===
window.atRenderCheckResults = function(d) {
  var results = document.getElementById('ats-results');
  if (!results) return;

  var html = '<div class="ats-results-inner">';

  if (d.section_flags && d.section_flags.length) {
    html += _atsSectionFlagsHTML(d.section_flags);
  }

  if (d.formatting_flags && d.formatting_flags.length) {
    html += _atsFormattingFlagsHTML(d.formatting_flags);
  }

  if ((!d.section_flags || !d.section_flags.length) && (!d.formatting_flags || !d.formatting_flags.length)) {
    html += '<div class="ats-all-ok">No structural or formatting issues found.</div>';
  }

  html += '</div>';
  results.innerHTML = html;
};

// === Coverage stat (compact) ===
function _atsCoverageStatHTML(before, after) {
  var bPct = before.pct || 0;
  var aPct = after.pct  || 0;
  var gain = aPct - bPct;
  var tierCls = aPct >= 80 ? 'sc-exc' : aPct >= 60 ? 'sc-good' : aPct >= 40 ? 'sc-partial' : 'sc-poor';
  var gainHtml = gain > 0
    ? '<span class="ats-cov-gain">+' + gain + '%</span>'
    : '';

  return (
    '<div class="ats-cov-stat">' +
      '<span class="ats-cov-stat-lbl">JD keyword coverage</span>' +
      '<span class="ats-cov-before-val">' + bPct + '%</span>' +
      '<svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
        '<path d="M3 8h10M9 4l4 4-4 4"/>' +
      '</svg>' +
      '<span class="ats-cov-after-val ' + tierCls + '">' + aPct + '%</span>' +
      gainHtml +
      '<span class="ats-cov-detail">' + after.matched.length + ' / ' + after.total + ' keywords matched</span>' +
    '</div>'
  );
}

// === Full resume card ===
function _atsResumeHTML(resume, plainText) {
  var copyBtn =
    '<button class="ats-copy-resume-btn" onclick="atCopyResume(this)" data-text="' + _atsEscAttr(plainText) + '">' +
      '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
        '<rect x="5" y="5" width="9" height="10" rx="1.5"/>' +
        '<path d="M11 5V3.5A1.5 1.5 0 0 0 9.5 2h-6A1.5 1.5 0 0 0 2 3.5v8A1.5 1.5 0 0 0 3.5 13H5"/>' +
      '</svg>' +
      'Copy full resume' +
    '</button>';

  var toolbar =
    '<div class="ats-resume-toolbar">' +
      '<span class="ats-resume-label">ATS-Optimised Resume</span>' +
      copyBtn +
    '</div>';

  var body = '<div class="ats-resume-body">';

  // Professional Summary
  if (resume.summary) {
    body +=
      '<div class="ats-resume-section">' +
        '<div class="ats-resume-sh">Professional Summary</div>' +
        '<p class="ats-resume-summary">' + _atsEsc(resume.summary) + '</p>' +
      '</div>';
  }

  // Work Experience
  if (resume.experience && resume.experience.length) {
    body += '<div class="ats-resume-section"><div class="ats-resume-sh">Work Experience</div>';
    (resume.experience || []).forEach(function(role) {
      var headerParts = [role.title, role.company, role.dates].filter(Boolean).map(_atsEsc);
      var header = headerParts.join(' <span class="ats-role-sep">|</span> ');
      var bullets = (role.bullets || []).map(function(b) {
        return '<li>' + _atsEsc(b) + '</li>';
      }).join('');
      body +=
        '<div class="ats-resume-role">' +
          (header ? '<div class="ats-role-hd">' + header + '</div>' : '') +
          (bullets ? '<ul class="ats-role-bullets">' + bullets + '</ul>' : '') +
        '</div>';
    });
    body += '</div>';
  }

  // Skills
  if (resume.skills && resume.skills.length) {
    body +=
      '<div class="ats-resume-section">' +
        '<div class="ats-resume-sh">Skills</div>' +
        '<p class="ats-skills-text">' + resume.skills.map(_atsEsc).join(', ') + '</p>' +
      '</div>';
  }

  // Education
  if (resume.education && resume.education.length) {
    body += '<div class="ats-resume-section"><div class="ats-resume-sh">Education</div>';
    (resume.education || []).forEach(function(edu) {
      var parts = [edu.degree, edu.institution, edu.year].filter(Boolean).map(_atsEsc);
      if (parts.length) {
        body += '<div class="ats-edu-entry">' + parts.join(' <span class="ats-role-sep">|</span> ') + '</div>';
      }
    });
    body += '</div>';
  }

  body += '</div>'; // .ats-resume-body

  return (
    '<div class="ats-resume-card">' +
      toolbar +
      body +
    '</div>'
  );
}

// === Collapsible warnings ===
function _atsWarningsHTML(missingSections, formattingFlags) {
  var count = missingSections.length + formattingFlags.length;
  var warnIcon =
    '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
      '<path d="M8 1L1 14h14L8 1z"/>' +
      '<line x1="8" y1="6" x2="8" y2="10"/>' +
      '<circle cx="8" cy="12.5" r=".5" fill="currentColor"/>' +
    '</svg>';

  var rows = '';
  missingSections.forEach(function(f) {
    rows +=
      '<div class="ats-flag-item ats-flag-warn">' +
        warnIcon +
        '<div class="ats-flag-body">' +
          '<span class="ats-flag-name">Missing section: ' + _atsEsc(f.name) + '</span>' +
          (f.suggestion ? '<span class="ats-flag-suggestion">' + _atsEsc(f.suggestion) + '</span>' : '') +
        '</div>' +
      '</div>';
  });
  formattingFlags.forEach(function(f) {
    rows +=
      '<div class="ats-flag-item ats-flag-warn">' +
        warnIcon +
        '<div class="ats-flag-body"><span class="ats-flag-name">' + _atsEsc(f) + '</span></div>' +
      '</div>';
  });

  var chevron =
    '<svg class="ats-warn-chevron" width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
      '<path d="M4 6l4 4 4-4"/>' +
    '</svg>';

  return (
    '<div class="ats-section ats-warnings-section">' +
      '<div class="ats-section-hd ats-warn-toggle" onclick="atsToggleWarnings(this)">' +
        warnIcon +
        '<span>' + count + ' formatting warning' + (count !== 1 ? 's' : '') + ' detected in original resume</span>' +
        chevron +
      '</div>' +
      '<div class="ats-warn-list">' + rows + '</div>' +
    '</div>'
  );
}

window.atsToggleWarnings = function(hd) {
  var list = hd.parentElement && hd.parentElement.querySelector('.ats-warn-list');
  if (!list) return;
  var open = list.classList.toggle('ats-warn-list--open');
  var chevron = hd.querySelector('.ats-warn-chevron');
  if (chevron) chevron.style.transform = open ? 'rotate(180deg)' : '';
};

// === Section flags (used by Quick Scan) ===
function _atsSectionFlagsHTML(flags) {
  var rows = flags.map(function(f) {
    if (f.found) {
      return (
        '<div class="ats-flag-item ats-flag-ok">' +
          '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
            '<path d="M2 8l4 4 8-8"/>' +
          '</svg>' +
          '<span class="ats-flag-name">' + _atsEsc(f.name) + '</span>' +
        '</div>'
      );
    }
    var suggestion = f.suggestion
      ? '<span class="ats-flag-suggestion">' + _atsEsc(f.suggestion) + '</span>'
      : '';
    return (
      '<div class="ats-flag-item ats-flag-warn">' +
        '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
          '<path d="M8 1L1 14h14L8 1z"/>' +
          '<line x1="8" y1="6" x2="8" y2="10"/>' +
          '<circle cx="8" cy="12.5" r=".5" fill="currentColor"/>' +
        '</svg>' +
        '<div class="ats-flag-body">' +
          '<span class="ats-flag-name">' + _atsEsc(f.name) + '</span>' +
          suggestion +
        '</div>' +
      '</div>'
    );
  }).join('');

  return (
    '<div class="ats-section">' +
      '<div class="ats-section-hd">' +
        '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
          '<rect x="2" y="2" width="12" height="12" rx="2"/>' +
          '<line x1="5" y1="8" x2="11" y2="8"/>' +
          '<line x1="8" y1="5" x2="8" y2="11"/>' +
        '</svg>' +
        '<span>Resume Sections</span>' +
      '</div>' +
      '<div class="ats-flag-list">' + rows + '</div>' +
    '</div>'
  );
}

// === Formatting flags (used by Quick Scan) ===
function _atsFormattingFlagsHTML(flags) {
  var rows = flags.map(function(f) {
    return (
      '<div class="ats-flag-item ats-flag-warn">' +
        '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
          '<path d="M8 1L1 14h14L8 1z"/>' +
          '<line x1="8" y1="6" x2="8" y2="10"/>' +
          '<circle cx="8" cy="12.5" r=".5" fill="currentColor"/>' +
        '</svg>' +
        '<div class="ats-flag-body">' +
          '<span class="ats-flag-name">' + _atsEsc(f) + '</span>' +
        '</div>' +
      '</div>'
    );
  }).join('');

  return (
    '<div class="ats-section">' +
      '<div class="ats-section-hd">' +
        '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
          '<line x1="3" y1="5" x2="13" y2="5"/>' +
          '<line x1="3" y1="8" x2="13" y2="8"/>' +
          '<line x1="3" y1="11" x2="9" y2="11"/>' +
        '</svg>' +
        '<span>Formatting Issues</span>' +
      '</div>' +
      '<div class="ats-flag-list">' + rows + '</div>' +
    '</div>'
  );
}

// === Copy ===
window.atCopyResume = function(btn) {
  var text = btn.getAttribute('data-text') || '';
  if (!text) {
    if (typeof toast === 'function') toast('No resume content to copy.', 'warn');
    return;
  }
  var origHtml = btn.innerHTML;
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).then(function() {
      btn.textContent = 'Copied!';
      setTimeout(function() { btn.innerHTML = origHtml; }, 1400);
    }).catch(function() {
      if (typeof toast === 'function') toast('Could not copy - please copy manually.', 'warn');
    });
  } else {
    var ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    btn.textContent = 'Copied!';
    setTimeout(function() { btn.innerHTML = origHtml; }, 1400);
  }
};
