// assets/js/fetch.js
// Job fetching — query Adzuna via /api/fetch-jobs, render results,
// and load a chosen posting's description into the JD textarea.

function escapeHtml(s) {
  return (s || '').replace(/&/g, '&amp;')
                  .replace(/</g, '&lt;')
                  .replace(/>/g, '&gt;');
}

// ── Fetch jobs ────────────────────────────────────────────
window.fetchJobs = function() {
  const queryEl = document.getElementById('fetch-query');
  const locEl   = document.getElementById('fetch-loc');
  const btn     = document.getElementById('fetch-btn');
  const box     = document.getElementById('fetch-results');

  const query = queryEl ? queryEl.value.trim() : '';
  const loc   = locEl   ? locEl.value.trim()   : '';

  if (!query) {
    alert('Enter a role to search for.');
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Fetching…';

  const url = '/api/fetch-jobs'
    + '?query='    + encodeURIComponent(query)
    + '&location=' + encodeURIComponent(loc)
    + '&results=8';

  fetch(url)
    .then(r => r.json())
    .then(d => {
      btn.disabled = false;
      btn.textContent = '⤓ Fetch';

      if (!d.ok) {
        alert('Fetch failed: ' + (d.error || 'unknown'));
        return;
      }

      window._fetchedJobs = d.jobs || [];
      box.style.display = 'block';

      if (!window._fetchedJobs.length) {
        box.innerHTML = '<div class="fetch-empty">No jobs found. Try a different role or location.</div>';
        return;
      }

      box.innerHTML = window._fetchedJobs.map((j, i) =>
        '<div class="fetch-item" onclick="selectJob(' + i + ')">' +
          '<div class="fetch-item-title">' + escapeHtml(j.title) + '</div>' +
          '<div class="fetch-item-meta">' +
            escapeHtml(j.company || 'Unknown') +
            (j.location ? ' · ' + escapeHtml(j.location) : '') +
            (j.language ? ' · ' + escapeHtml(j.language) : '') +
          '</div>' +
        '</div>'
      ).join('');
    })
    .catch(e => {
      btn.disabled = false;
      btn.textContent = '⤓ Fetch';
      alert('Fetch error: ' + e);
    });
};

// ── Select a fetched job ──────────────────────────────────
// Loads the posting's description into the JD textarea and fires an
// input event so the counter + analysis-readiness checks update.
window.selectJob = function(i) {
  const job = (window._fetchedJobs || [])[i];
  if (!job) return;

  const jd = document.getElementById('jd-input');
  if (jd) {
    jd.value = job.description || '';
    jd.dispatchEvent(new Event('input'));
  }

  document.querySelectorAll('#fetch-results .fetch-item')
    .forEach((el, idx) => el.classList.toggle('selected', idx === i));
};
