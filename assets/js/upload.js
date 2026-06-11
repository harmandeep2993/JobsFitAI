// assets/js/upload.js
// File upload — drag and drop + browse
// POSTs to /api/upload, stores tmp path in window._resumeTmp

const JD_MAX_CHARS = 5000;

// ── Clear resume ──────────────────────────────────────────
window.clearResume = function() {
  window._resumeTmp  = null;
  window._resumeName = null;

  // Sync the Matches tab resume status so it doesn't show stale data.
  if (typeof window.renderResume === 'function') window.renderResume(null);

  const zone = document.getElementById('up-zone');
  if (zone) {
    zone.outerHTML =
      '<div class="up-zone" id="up-zone"' +
        ' ondragover="event.preventDefault();this.classList.add(\'drag\')"' +
        ' ondragleave="this.classList.remove(\'drag\')"' +
        ' ondrop="event.preventDefault();this.classList.remove(\'drag\');handleFileSelect(event.dataTransfer.files[0])">' +
        '<svg width="30" height="36" viewBox="0 0 36 44" fill="none" style="opacity:0.3;">' +
          '<rect x="1" y="1" width="26" height="34" rx="3" stroke="currentColor" stroke-width="2" fill="none"/>' +
          '<path d="M27 1l8 8h-8V1z" stroke="currentColor" stroke-width="2" fill="none"/>' +
          '<line x1="6" y1="13" x2="22" y2="13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>' +
          '<line x1="6" y1="19" x2="22" y2="19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>' +
          '<line x1="6" y1="25" x2="15" y2="25" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>' +
        '</svg>' +
        '<div class="up-text">Drop file or <strong>browse</strong></div>' +
        '<div class="up-hint">PDF &nbsp;&middot;&nbsp; DOCX &nbsp;&middot;&nbsp; DOC</div>' +
      '</div>';

    // Rebind after DOM replacement
    setTimeout(bindUpload, 50);
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
  if (!['pdf', 'docx', 'doc'].includes(ext)) {
    alert('Please upload PDF, DOCX or DOC.');
    return;
  }

  if (file.size > FILE_MAX_MB * 1024 * 1024) {
    alert('File is too large (' + (file.size / 1024 / 1024).toFixed(1) + ' MB). Maximum size is ' + FILE_MAX_MB + ' MB.');
    return;
  }

  const fd = new FormData();
  fd.append('file', file);

  fetch('/api/upload', { method: 'POST', body: fd })
    .then(r => r.json())
    .then(d => {
      if (!d.ok) {
        alert('Upload failed: ' + (d.error || 'unknown'));
        return;
      }

      window._resumeTmp  = d.tmp;
      window._resumeName = d.name;

      const zone = document.getElementById('up-zone');
      if (zone) {
        zone.outerHTML =
          '<div class="file-chip" id="up-zone">' +
            '<span style="font-size:28px;">&#128196;</span>' +
            '<div style="text-align:center;">' +
              '<div class="fc-name" title="' + d.name + '">' + d.name + '</div>' +
              '<div class="fc-meta">' + d.kb + ' KB &middot; ' + d.ext + '</div>' +
            '</div>' +
            '<span style="color:var(--green);font-size:18px;font-weight:700;">&#10003;</span>' +
          '</div>';
      }

      if (typeof emitEvent === 'function') {
        emitEvent('file_uploaded', {});
      }
    })
    .catch(e => alert('Upload error: ' + e));
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
    jd.addEventListener('input', () => {
      clearTimeout(_debounce);
      _debounce = setTimeout(() => updateCounter(jd.value.length), 50);
    });
    jd.addEventListener('paste', () => setTimeout(() => updateCounter(jd.value.length), 10));
    updateCounter(0);
  } else {
    setTimeout(bindCounter, 50);
  }
}

bindUpload();
bindCounter();