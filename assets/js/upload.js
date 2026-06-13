// assets/js/upload.js
// File upload - drag and drop + browse
// POSTs to /api/upload, stores tmp path in window._resumeTmp

const JD_MAX_CHARS = 5000;

// ── Clear resume ──────────────────────────────────────────
window.clearResume = function() {
  window._resumeTmp         = null;
  window._resumeName        = null;
  window._resumeFingerprint = null;

  if (typeof window.renderResume === 'function') window.renderResume(null);

  const zone = document.getElementById('up-zone');
  if (zone) {
    zone.classList.remove('has-file');
    zone.innerHTML =
      '<svg width="28" height="34" viewBox="0 0 36 44" fill="none" style="opacity:0.3;">' +
        '<rect x="1" y="1" width="26" height="34" rx="3" stroke="currentColor" stroke-width="2" fill="none"/>' +
        '<path d="M27 1l8 8h-8V1z" stroke="currentColor" stroke-width="2" fill="none"/>' +
        '<line x1="6" y1="13" x2="22" y2="13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>' +
        '<line x1="6" y1="19" x2="22" y2="19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>' +
        '<line x1="6" y1="25" x2="15" y2="25" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>' +
      '</svg>' +
      '<div class="up-text">Drop or <strong>browse</strong></div>' +
      '<div class="up-hint">PDF &nbsp;&middot;&nbsp; DOCX</div>';
  }
};

// ── Clear JD ─────────────────────────────────────────────
window.clearJD = function() {
  const jd = document.getElementById('jd-input');
  if (jd) {
    jd.value = '';
    jd.classList.remove('success');
    updateCounter(0);
  }
};

// ── Char counter ─────────────────────────────────────────
function updateCounter(len) {
  const el = document.getElementById('jd-counter');
  if (!el) return;
  el.textContent = len + ' / ' + JD_MAX_CHARS;
  el.className   = 'jd-counter';
  if (len > JD_MAX_CHARS * 0.9) el.classList.add('warn');
  if (len >= JD_MAX_CHARS)      el.classList.add('limit');
}

// ── File upload ───────────────────────────────────────────
var FILE_MAX_MB = 5;

window.handleFileSelect = function(file) {
  if (!file) return;

  const ext = file.name.split('.').pop().toLowerCase();
  if (ext === 'doc') {
    toast('.doc not supported - convert to .docx or .pdf first.', 'warn', 5000);
    return;
  }
  if (!['pdf', 'docx'].includes(ext)) {
    toast('Please upload a PDF or DOCX file.', 'warn');
    return;
  }

  if (file.size > FILE_MAX_MB * 1024 * 1024) {
    toast('File too large (' + (file.size / 1024 / 1024).toFixed(1) + ' MB). Max is ' + FILE_MAX_MB + ' MB.', 'warn');
    return;
  }

  // Stable fingerprint - survives page refresh for the same physical file
  window._resumeFingerprint = file.name + '|' + file.size + '|' + (file.lastModified || 0);

  // Upload directly to the persistent store (slot 0 = base, or next free slot).
  const fd   = new FormData();
  fd.append('file', file);
  fd.append('slot', '0');

  const zone = document.getElementById('up-zone');
  if (zone) {
    zone.classList.add('uploading');
    zone.innerHTML =
      '<div class="up-spinner"></div>' +
      '<div class="up-text">Uploading&hellip;</div>';
  }

  fetch('/api/resumes/upload', { method: 'POST', body: fd })
    .then(r => r.json())
    .then(d => {
      if (!d.ok) {
        if (zone) zone.classList.remove('uploading');
        toast('Upload failed: ' + (d.error || 'unknown'), 'err');
        return;
      }
      // Refresh picker then auto-select the new resume
      if (typeof rvLoad === 'function') rvLoad();
      if (typeof rvSelect === 'function') rvSelect(d.id, d.name);
      if (typeof setStep === 'function') setStep(2);
    })
    .catch(e => {
      if (zone) zone.classList.remove('uploading');
      toast('Upload error: ' + e, 'err');
    });
};

// ── Resume preview modal ──────────────────────────────────
window.previewResume = function() {
  if (!window._resumeTmp) return;

  var modal   = document.getElementById('resume-preview-modal');
  var content = document.getElementById('rp-content');
  var sub     = document.querySelector('#resume-preview-modal .dt-sub');
  if (!modal || !content) return;

  var ext = (window._resumeName || '').split('.').pop().toLowerCase();
  modal.style.display = 'flex';

  if (ext === 'pdf') {
    if (sub) sub.textContent = 'Original resume';
    content.classList.add('rp-content--frame');
    var url = '/api/resume-file?tmp=' + encodeURIComponent(window._resumeTmp) + '#navpanes=0';
    content.innerHTML = '<iframe class="rp-frame" src="' + url + '" title="Resume preview"></iframe>';
  } else {
    if (sub) sub.textContent = 'Extracted text from your uploaded file';
    content.classList.remove('rp-content--frame');
    content.innerHTML = '<div class="rp-loading"><div class="up-spinner" style="width:20px;height:20px;border-width:2px;"></div><span>Loading preview&hellip;</span></div>';
    fetch('/api/resume-preview', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ tmp: window._resumeTmp }),
    })
      .then(function(r) { return r.json(); })
      .then(function(d) {
        if (!d.ok) { content.innerHTML = '<p class="rp-err">Could not extract: ' + (d.error || 'unknown') + '</p>'; return; }
        var total   = d.total_chars;
        var truncated = total > d.text.length ? '<div class="rp-trunc">Showing first ' + d.text.length.toLocaleString() + ' of ' + total.toLocaleString() + ' characters</div>' : '';
        content.innerHTML =
          '<div class="rp-meta">' + window._resumeName + ' &nbsp;&middot;&nbsp; ' + total.toLocaleString() + ' chars</div>' +
          truncated +
          '<pre class="rp-text">' + d.text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;') + '</pre>';
      })
      .catch(function(e) { content.innerHTML = '<p class="rp-err">Request failed: ' + e + '</p>'; });
  }
};

window.closeResumePreview = function() {
  var modal   = document.getElementById('resume-preview-modal');
  var content = document.getElementById('rp-content');
  if (modal)   modal.style.display = 'none';
  if (content) { content.classList.remove('rp-content--frame'); content.innerHTML = ''; }
};

// ── Bind upload zone ──────────────────────────────────────
function bindUpload() {
  const zone  = document.getElementById('up-zone');
  const input = document.getElementById('file-input');

  if (zone && input) {
    zone.addEventListener('click', () => input.click());
    input.addEventListener('change', () => handleFileSelect(input.files[0]));
  } else {
    setTimeout(bindUpload, 50);
  }
}

// ── Bind JD counter ───────────────────────────────────────
function bindCounter() {
  const jd = document.getElementById('jd-input');
  if (jd) {
    var _debounce;

    function enforceMax(showToast) {
      if (jd.value.length > JD_MAX_CHARS) {
        jd.value = jd.value.slice(0, JD_MAX_CHARS);
        if (showToast && typeof toast === 'function') {
          toast('Job description trimmed to 5,000 characters', 'warn', 3000);
        }
      }
    }

    jd.addEventListener('input', () => {
      enforceMax(false);
      clearTimeout(_debounce);
      _debounce = setTimeout(() => updateCounter(jd.value.length), 50);
    });
    jd.addEventListener('paste', () => setTimeout(() => {
      enforceMax(true);
      updateCounter(jd.value.length);
    }, 10));
    updateCounter(0);
  } else {
    setTimeout(bindCounter, 50);
  }
}

bindUpload();
bindCounter();
