// assets/js/upload.js
// File upload — drag and drop + browse
// POSTs to /api/upload, stores tmp path in window._resumeTmp

window.handleFileSelect = function(file) {
  if (!file) return;

  const ext = file.name.split('.').pop().toLowerCase();
  if (!['pdf', 'docx', 'doc'].includes(ext)) {
    alert('Please upload PDF, DOCX or DOC.');
    return;
  }

  const fd = new FormData();
  fd.append('file', file);

  fetch('/api/upload', { method: 'POST', body: fd })
    .then(r  => r.json())
    .then(d  => {
      if (!d.ok) {
        alert('Upload failed: ' + (d.error || 'unknown'));
        return;
      }

      // Store for analysis
      window._resumeTmp  = d.tmp;
      window._resumeName = d.name;

      // Replace upload zone with file chip
      const zone = document.getElementById('up-zone');
      if (zone) {
        zone.outerHTML =
          '<div class="file-chip" id="up-zone">' +
            '<span style="font-size:36px;">&#128196;</span>' +
            '<div style="text-align:center;">' +
              '<div class="fc-name" title="' + d.name + '">' + d.name + '</div>' +
              '<div class="fc-meta">' + d.kb + ' KB &middot; ' + d.ext + '</div>' +
            '</div>' +
            '<span style="color:var(--green);font-size:20px;font-weight:700;">&#10003;</span>' +
          '</div>';
      }

      if (typeof emitEvent === 'function') {
        emitEvent('file_uploaded', {});
      }
    })
    .catch(e => alert('Upload error: ' + e));
};

// Bind upload zone click and drag-drop
// Retry IIFE — elements may not exist yet when script runs
(function bindUpload() {
  const zone  = document.getElementById('up-zone');
  const input = document.getElementById('file-input');

  if (zone && input) {
    zone.addEventListener('click', () => input.click());
    input.addEventListener('change', () => handleFileSelect(input.files[0]));
  } else {
    setTimeout(bindUpload, 50);
  }
})();