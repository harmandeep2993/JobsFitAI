// assets/js/rewrite.js
// Handles the Improve tab - calls /api/improve-resume and renders before/after bullets.

var _rwLoaded = false;

// Called by the tab onclick - ensures this file is loaded before doing anything.
window.rwEnsureLoaded = function() {
  // Script is already loaded (this file), nothing extra needed.
};

// Badge colour class
function _rwBadgeCls(badge) {
  if (badge === 'Improved')          return 'rw-badge rw-badge--green';
  if (badge === 'Unchanged')         return 'rw-badge rw-badge--muted';
  return                                    'rw-badge rw-badge--blue';
}

function _rwItemHTML(item) {
  var badgeCls = _rwBadgeCls(item.badge);
  var after = item.after  || '';
  var before = item.before || '';
  var source = item.source || '';

  var beforeRow = before
    ? '<div class="rw-before"><span class="rw-label">Before</span><span class="rw-text">' + _rwEsc(before) + '</span></div>'
    : '';

  var copyBtn = after
    ? '<button class="rw-copy-btn" onclick="rwCopyBullet(this)" data-text="' + _rwEscAttr(after) + '" title="Copy bullet">Copy</button>'
    : '';

  return (
    '<div class="rw-item' + (item.changed ? ' rw-item--changed' : '') + '">' +
      '<div class="rw-item-hd">' +
        '<span class="rw-source">' + _rwEsc(source) + '</span>' +
        '<span class="' + badgeCls + '">' + _rwEsc(item.badge) + '</span>' +
      '</div>' +
      beforeRow +
      '<div class="rw-after">' +
        '<span class="rw-label">Improved</span>' +
        '<span class="rw-text">' + _rwEsc(after) + '</span>' +
        copyBtn +
      '</div>' +
    '</div>'
  );
}

function _rwSectionHTML(section) {
  var items = (section.items || []).filter(function(i) { return i.after; });
  if (!items.length) return '';

  var rows = items.map(_rwItemHTML).join('');
  return (
    '<div class="rw-group">' +
      '<div class="rw-group-hd">' + _rwEsc(section.group) + '</div>' +
      '<div class="rw-group-items">' + rows + '</div>' +
    '</div>'
  );
}

window.rwGenerate = function() {
  var jd = window._rwJd        || (document.getElementById('jd-input') || {}).value || '';
  var gaps = window._rwGaps      || [];
  var strengths = window._rwStrengths || [];

  if (!jd || jd.trim().length < 30) {
    toast('Run an analysis first so the Improve tab knows which role to target.', 'warn');
    return;
  }

  var btn = document.getElementById('rw-run-btn');
  var output = document.getElementById('rw-output');
  if (btn)    { btn.disabled = true; btn.textContent = 'Generating…'; }
  if (output) output.innerHTML = '<div class="rw-loading">Analysing your resumes and rewriting bullets…</div>';

  fetch('/api/improve-resume', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ jd: jd, gaps: gaps, strengths: strengths }),
  })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (!d.ok) {
        var msgs = {
          no_data:      'No resume data found. Upload at least one resume in My Resumes first.',
          llm_failed:   'LLM provider is unavailable. Check your API key in Settings.',
          parse_failed: 'Could not parse the LLM response. Try again.',
          jd_required:  'Job description is missing.',
        };
        if (output) output.innerHTML = '<div class="rw-error">' + _rwEsc(msgs[d.reason] || msgs[d.error] || 'Something went wrong. Try again.') + '</div>';
        return;
      }

      var sections = (d.sections || []).map(_rwSectionHTML).filter(Boolean);
      if (!sections.length) {
        if (output) output.innerHTML = '<div class="rw-empty">No bullets could be generated. Try adding more detail to your stored resumes.</div>';
        return;
      }

      var changed = d.sections.reduce(function(n, s) {
        return n + (s.items || []).filter(function(i) { return i.changed; }).length;
      }, 0);

      var total = d.sections.reduce(function(n, s) {
        return n + (s.items || []).filter(function(i) { return i.after; }).length;
      }, 0);

      var toggleBtn = changed && changed < total
        ? '<button class="rw-toggle-btn" id="rw-changed-toggle" onclick="rwToggleChanged(this)">' +
            'Show changed only (' + changed + ')' +
          '</button>'
        : '';

      var summary = '<div class="rw-summary">' + total + ' bullet' + (total !== 1 ? 's' : '') + ' generated' +
        (changed ? ', <span class="rw-summary--green">' + changed + ' improved</span>' : '') +
        toggleBtn +
        '</div>';

      if (output) output.innerHTML = summary + sections.join('');
    })
    .catch(function(e) {
      if (output) output.innerHTML = '<div class="rw-error">Request failed: ' + _rwEsc(String(e)) + '</div>';
    })
    .finally(function() {
      if (btn) { btn.disabled = false; btn.innerHTML =
        '<svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="margin-right:6px;"><polygon points="3,2 13,8 3,14"/></svg>Generate Improved Bullets'; }
    });
};

window.rwCopyBullet = function(btn) {
  var text = btn.getAttribute('data-text') || '';
  if (!text) return;
  navigator.clipboard.writeText(text).then(function() {
    var orig = btn.textContent;
    btn.textContent = 'Copied!';
    setTimeout(function() { btn.textContent = orig; }, 1400);
  }).catch(function() {
    toast('Could not copy - please copy manually.', 'warn');
  });
};

window.rwToggleChanged = function(btn) {
  var output = document.getElementById('rw-output');
  if (!output) return;
  var active = btn.getAttribute('data-active') === '1';
  if (active) {
    output.querySelectorAll('.rw-item').forEach(function(el) {
      el.style.display = '';
    });
    btn.setAttribute('data-active', '0');
    btn.textContent = btn.getAttribute('data-label-off');
  } else {
    var label = btn.textContent;
    btn.setAttribute('data-label-off', label);
    output.querySelectorAll('.rw-item').forEach(function(el) {
      el.style.display = el.classList.contains('rw-item--changed') ? '' : 'none';
    });
    btn.setAttribute('data-active', '1');
    btn.textContent = 'Show all bullets';
  }
};

// Minimal HTML escaping for injected text
function _rwEsc(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function _rwEscAttr(str) {
  return String(str).replace(/&/g, '&amp;').replace(/"/g, '&quot;');
}
