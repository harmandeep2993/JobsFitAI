// assets/js/resumes.js
// Manages the My Resumes view and the analyzer resume picker.

var _rvSlotTarget = 0; // slot being uploaded into

var RV_SLOT_META = [
  { label: 'Base Resume',      hint: 'Your complete resume with all experience and skills' },
  { label: 'Tailored Resume 1', hint: 'Customised for a specific role or industry' },
  { label: 'Tailored Resume 2', hint: 'A second tailored variant' },
];

// ── Load + render ─────────────────────────────────────────

function rvLoad() {
  fetch('/api/resumes')
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (!d.ok) return;
      _rvRenderSlots(d.resumes);
      _rvRenderPicker(d.resumes);
      _rvUpdateBadge(d.resumes.length);
    })
    .catch(function() {});
}

function _rvRenderSlots(resumes) {
  var el = document.getElementById('rv-slots');
  if (!el) return;

  // Index by slot for fast lookup
  var bySlot = {};
  resumes.forEach(function(r) { bySlot[r.slot] = r; });

  var html = '';
  for (var s = 0; s < 3; s++) {
    var meta = RV_SLOT_META[s];
    var r    = bySlot[s];
    html += r ? _rvFilledSlot(r, meta) : _rvEmptySlot(s, meta);
  }
  el.innerHTML = html;
}

function _rvEmptySlot(slot, meta) {
  return (
    '<div class="rv-slot rv-slot-empty" onclick="rvPickFile(' + slot + ')">' +
      '<div class="rv-slot-num">' + (slot + 1) + '</div>' +
      '<div class="rv-slot-body">' +
        '<div class="rv-slot-label">' + meta.label + '</div>' +
        '<div class="rv-slot-hint">' + meta.hint + '</div>' +
        '<div class="rv-slot-cta">' +
          '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">' +
            '<path d="M2 14h12M8 2v9M5 5l3-3 3 3"/>' +
          '</svg>' +
          'Upload PDF or DOCX' +
        '</div>' +
      '</div>' +
    '</div>'
  );
}

function _rvFilledSlot(r, meta) {
  var date = r.uploaded_at ? r.uploaded_at.slice(0, 10) : '';
  var ext  = r.original_name.split('.').pop().toUpperCase();
  return (
    '<div class="rv-slot rv-slot-filled">' +
      '<div class="rv-slot-num">' + (r.slot + 1) + '</div>' +
      '<div class="rv-slot-body">' +
        '<div class="rv-slot-label-row">' +
          '<span class="rv-slot-label" id="rv-lbl-' + r.id + '" title="Click to rename" onclick="rvEditLabel(\'' + r.id + '\')">' +
            _esc(r.label) +
          '</span>' +
          '<button class="rv-lbl-edit-btn" title="Rename" onclick="rvEditLabel(\'' + r.id + '\')">' +
            '<svg width="11" height="11" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' +
              '<path d="M9.5 2.5l2 2L4 12H2v-2L9.5 2.5z"/>' +
            '</svg>' +
          '</button>' +
        '</div>' +
        '<div class="rv-slot-name">' +
          '<span class="rv-ext-badge">' + ext + '</span>' +
          _esc(r.original_name) +
        '</div>' +
        '<div class="rv-slot-meta">' + r.file_size_kb + ' KB &middot; ' + date + '</div>' +
        '<div class="rv-slot-actions">' +
          '<button class="rv-btn rv-btn-preview" onclick="rvPreview(\'' + r.id + '\',\'' + _esc(r.original_name) + '\')">Preview</button>' +
          '<button class="rv-btn rv-btn-replace" onclick="rvPickFile(' + r.slot + ')">Replace</button>' +
          '<button class="rv-btn rv-btn-del" onclick="rvDelete(\'' + r.id + '\')">Delete</button>' +
        '</div>' +
      '</div>' +
    '</div>'
  );
}

// ── Analyzer picker ───────────────────────────────────────

function _rvRenderPicker(resumes) {
  var picker  = document.getElementById('az-resume-picker');
  var zone    = document.getElementById('up-zone');
  var manBtn  = document.getElementById('az-resume-manage');

  if (!picker) return;

  if (!resumes || resumes.length === 0) {
    picker.style.display = 'none';
    if (zone)   zone.style.display   = '';
    if (manBtn) manBtn.style.display = 'none';
    return;
  }

  picker.style.display = '';
  if (zone)   zone.style.display   = 'none';
  if (manBtn) manBtn.style.display = '';

  var html = '<div class="az-rv-picker"><div id="az-rv-reco-banner" style="display:none;"></div>';
  resumes.forEach(function(r) {
    var ext  = r.original_name.split('.').pop().toUpperCase();
    var sel  = (window._resumeId === r.id) ? ' selected' : '';
    var hist = '';
    if (r.last_score != null) {
      var tierCls = r.last_score >= 80 ? 'sc-exc' : r.last_score >= 60 ? 'sc-good' : r.last_score >= 40 ? 'sc-partial' : 'sc-poor';
      hist = '<div class="az-rv-card-hist">' +
             '<span class="az-rv-hist-score ' + tierCls + '">' + r.last_score + '%</span>' +
             '<span class="az-rv-hist-jd">' + _esc((r.last_jd || '').slice(0, 55)) + '…</span>' +
             '</div>';
    }
    html += (
      '<div class="az-rv-card' + sel + '" onclick="rvSelect(\'' + r.id + '\',\'' + _esc(r.original_name) + '\')">' +
        '<div class="az-rv-card-left">' +
          '<span class="az-rv-slot-num">' + (r.slot + 1) + '</span>' +
        '</div>' +
        '<div class="az-rv-card-body">' +
          '<div class="az-rv-card-label">' + _esc(r.label) + '</div>' +
          '<div class="az-rv-card-name">' +
            '<span class="rv-ext-badge">' + ext + '</span>' +
            _esc(r.original_name) +
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
  html += '<button class="az-rv-add" onclick="rvPickFile(-1)">+ Upload another resume</button>';
  html += '</div>';

  picker.innerHTML = html;

  // Auto-select first if nothing selected yet
  if (!window._resumeId && resumes.length > 0) {
    rvSelect(resumes[0].id, resumes[0].original_name);
  }
}

window.rvSelect = function(id, name) {
  window._resumeId          = id;
  window._resumeTmp         = null;
  window._resumeFingerprint = id;

  // Update visual selection
  document.querySelectorAll('.az-rv-card').forEach(function(c) {
    c.classList.toggle('selected', c.getAttribute('onclick').indexOf(id) !== -1);
  });

  // Show file name in upload zone label if it exists
  if (typeof updateUploadZone === 'function') updateUploadZone(name);
  setStep(2);
  toast('Resume selected: ' + name, 'ok', 2000);

  // Wire to Job Matches so it scores against the same resume (fire-and-forget).
  fetch('/api/resumes/' + id + '/use-for-matching', { method: 'POST' }).catch(function() {});
};

// ── Upload ────────────────────────────────────────────────

window.rvPickFile = function(slot) {
  _rvSlotTarget = (slot === -1) ? _rvNextFreeSlot() : slot;
  var inp = document.getElementById('rv-file-input');
  if (inp) inp.click();
};

function _rvNextFreeSlot() {
  var slots = Array.from(document.querySelectorAll('.rv-slot-filled')).length;
  return Math.min(slots, 2);
}

(function bindRvFileInput() {
  var inp = document.getElementById('rv-file-input');
  if (!inp) { setTimeout(bindRvFileInput, 80); return; }
  inp.addEventListener('change', function() {
    if (inp.files && inp.files[0]) rvUpload(inp.files[0], _rvSlotTarget);
    inp.value = '';
  });
})();

window.rvUpload = function(file, slot) {
  var suffix = file.name.split('.').pop().toLowerCase();
  if (!['pdf', 'docx'].includes(suffix)) {
    toast('Only PDF and DOCX files are supported.', 'warn'); return;
  }
  if (file.size > 5 * 1024 * 1024) {
    toast('File is too large (max 5 MB).', 'warn'); return;
  }

  var fd = new FormData();
  fd.append('file', file);
  fd.append('slot', String(slot));

  toast('Uploading…', 'info', 2000);

  fetch('/api/resumes/upload', { method: 'POST', body: fd })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (!d.ok) { toast('Upload failed: ' + (d.error || 'unknown'), 'err'); return; }
      toast(d.label + ' saved.', 'ok', 3000);
      rvLoad(); // refresh both slots view and picker
      // Auto-select the freshly uploaded resume in the analyser
      rvSelect(d.id, d.name);
    })
    .catch(function() { toast('Upload failed.', 'err'); });
};

// ── Rename label ─────────────────────────────────────────

window.rvEditLabel = function(id) {
  var span = document.getElementById('rv-lbl-' + id);
  if (!span || span.querySelector('input')) return; // already editing

  var current = span.textContent.trim();
  span.innerHTML =
    '<input class="rv-lbl-input" value="' + _esc(current) + '" maxlength="50" ' +
    'onclick="event.stopPropagation()" />';

  var inp = span.querySelector('input');
  inp.focus();
  inp.select();

  function save() {
    var val = inp.value.trim();
    if (!val || val === current) { rvLoad(); return; }
    fetch('/api/resumes/' + id + '/label', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ label: val }),
    })
      .then(function(r) { return r.json(); })
      .then(function(d) {
        if (!d.ok) toast('Could not rename.', 'err');
        rvLoad();
      })
      .catch(function() { rvLoad(); });
  }

  inp.addEventListener('keydown', function(e) {
    if (e.key === 'Enter')  { e.preventDefault(); save(); }
    if (e.key === 'Escape') { rvLoad(); }
  });
  inp.addEventListener('blur', save);
};

// ── Delete ────────────────────────────────────────────────

window.rvDelete = function(id) {
  fetch('/api/resumes/' + id, { method: 'DELETE' })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (!d.ok) { toast('Delete failed.', 'err'); return; }
      if (window._resumeId === id) {
        window._resumeId  = null;
        window._resumeTmp = null;
      }
      toast('Resume removed.', 'ok', 2000);
      rvLoad();
    })
    .catch(function() { toast('Delete failed.', 'err'); });
};

// ── Preview ───────────────────────────────────────────────

window.rvPreview = function(id, filename) {
  var modal   = document.getElementById('resume-preview-modal');
  var content = document.getElementById('rp-content');
  var sub     = document.querySelector('#resume-preview-modal .dt-sub');
  if (!modal || !content) return;

  modal.style.display = 'flex';
  var ext = (filename || '').split('.').pop().toLowerCase();

  if (ext === 'pdf') {
    if (sub) sub.textContent = 'Original resume';
    content.classList.add('rp-content--frame');
    content.innerHTML = '<iframe class="rp-frame" src="/api/resumes/' + id + '/file#navpanes=0" title="Resume preview"></iframe>';
  } else {
    if (sub) sub.textContent = 'Extracted text from your uploaded file';
    content.classList.remove('rp-content--frame');
    content.innerHTML = '<div class="rp-loading"><div class="up-spinner" style="width:20px;height:20px;border-width:2px;"></div><span>Loading preview&hellip;</span></div>';
    fetch('/api/resume-preview', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ resume_id: id }),
    })
      .then(function(r) { return r.json(); })
      .then(function(d) {
        if (!d.ok) {
          content.innerHTML = '<p class="rp-err">Could not extract: ' + (d.error || 'unknown') + '</p>';
          return;
        }
        var total   = d.total_chars;
        var trunc   = total > d.text.length
          ? '<div class="rp-trunc">Showing first ' + d.text.length.toLocaleString() + ' of ' + total.toLocaleString() + ' characters</div>'
          : '';
        content.innerHTML =
          '<div class="rp-meta">' + _esc(filename) + ' &nbsp;&middot;&nbsp; ' + total.toLocaleString() + ' chars</div>' +
          trunc +
          '<pre class="rp-text">' + _esc(d.text) + '</pre>';
      })
      .catch(function(e) {
        content.innerHTML = '<p class="rp-err">Request failed: ' + e + '</p>';
      });
  }
};

// ── Recommendation ───────────────────────────────────────

var _rvRecoTimer  = null;
var _rvRecoActive = false; // true while a request is in flight
var _rvLastJD     = '';

function _rvRenderBanner(scores, recommendedId) {
  var banner = document.getElementById('az-rv-reco-banner');
  if (!banner) return;

  // Dismiss if recommended is already selected or only 1 score
  if (!scores || scores.length < 2 || recommendedId === window._resumeId) {
    banner.style.display = 'none';
    return;
  }

  var best   = scores[0];
  var others = scores.slice(1).map(function(s) {
    return _esc(s.label) + ': ' + s.score + '%';
  }).join(' &nbsp;&middot;&nbsp; ');

  banner.style.display = '';
  banner.innerHTML =
    '<div class="az-rv-reco-inner">' +
      '<div class="az-rv-reco-body">' +
        '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0">' +
          '<circle cx="8" cy="8" r="6"/><path d="M8 5v3l2 2"/>' +
        '</svg>' +
        '<div>' +
          '<div class="az-rv-reco-title">' +
            '<strong>' + _esc(best.label) + '</strong> looks like the best match for this role &mdash; ' + best.score + '%' +
          '</div>' +
          '<div class="az-rv-reco-sub">' + others + '</div>' +
        '</div>' +
      '</div>' +
      '<div class="az-rv-reco-actions">' +
        '<button class="az-rv-reco-use" onclick="rvSelect(\'' + best.id + '\',\'' + _esc(best.name) + '\');document.getElementById(\'az-rv-reco-banner\').style.display=\'none\'">Use this</button>' +
        '<button class="az-rv-reco-dismiss" onclick="document.getElementById(\'az-rv-reco-banner\').style.display=\'none\'">Dismiss</button>' +
      '</div>' +
    '</div>';
}

function _rvRequestReco(jd) {
  if (_rvRecoActive) return;
  _rvLastJD     = jd;
  _rvRecoActive = true;

  fetch('/api/resumes/recommend', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ jd: jd }),
  })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      _rvRecoActive = false;
      if (d.ok && d.scores && d.scores.length >= 2) {
        _rvRenderBanner(d.scores, d.recommended_id);
      }
    })
    .catch(function() { _rvRecoActive = false; });
}

// Called by analysis.js checkJD — fires when JD changes and 2+ resumes exist.
window.rvCheckReco = function(jd) {
  var picker = document.getElementById('az-resume-picker');
  if (!picker || picker.style.display === 'none') return;
  var cards = picker.querySelectorAll('.az-rv-card');
  if (cards.length < 2) return;
  if (jd.length < 150) return;
  if (jd === _rvLastJD) return;

  clearTimeout(_rvRecoTimer);
  _rvRecoTimer = setTimeout(function() { _rvRequestReco(jd); }, 1500);
};

// ── Badge ─────────────────────────────────────────────────

function _rvUpdateBadge(count) {
  var badge = document.getElementById('sb-badge-resumes');
  if (!badge) return;
  badge.textContent = count > 0 ? String(count) : '';
  badge.style.display = count > 0 ? '' : 'none';
}

// ── Util ──────────────────────────────────────────────────

function _esc(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Init ──────────────────────────────────────────────────

// Load on page start so picker is ready when user opens analyser.
(function() { rvLoad(); })();
