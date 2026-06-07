// assets/js/fetch.js
// Job Search tab — switch sidebar views, query Adzuna via /api/fetch-jobs,
// and display the fetched postings. Standalone: does not touch the
// resume-vs-JD analyzer flow.

function escapeHtml(s) {
  return (s || '').replace(/&/g, '&amp;')
                  .replace(/</g, '&lt;')
                  .replace(/>/g, '&gt;')
                  .replace(/"/g, '&quot;');
}

// ── Sidebar view switching ────────────────────────────────
// Shows the requested view ("analyzer" | "jobsearch") and marks the
// matching sidebar item active. The other views stay in the DOM hidden.
window.showView = function(name) {
  document.querySelectorAll('.view').forEach(v => { v.style.display = 'none'; });
  const view = document.getElementById('view-' + name);
  if (view) view.style.display = 'block';

  document.querySelectorAll('.jfai-sidebar .sb-item')
    .forEach(el => el.classList.remove('active'));
  const nav = document.getElementById('nav-' + name);
  if (nav) nav.classList.add('active');

  // Refresh the matches dashboard when its tab is opened.
  if (name === 'matches' && typeof window.loadMatchState === 'function') {
    window.loadMatchState();
  }
};

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
  box.style.display = 'block';
  box.innerHTML = '<div class="fetch-empty">Searching…</div>';

  const url = '/api/fetch-jobs'
    + '?query='    + encodeURIComponent(query)
    + '&location=' + encodeURIComponent(loc)
    + '&results=10';

  fetch(url)
    .then(r => r.json())
    .then(d => {
      btn.disabled = false;
      btn.textContent = '→ Fetch Jobs';

      if (!d.ok) {
        box.innerHTML = '<div class="fetch-empty">Fetch failed: '
          + escapeHtml(d.error || 'unknown') + '</div>';
        return;
      }

      const jobs = d.jobs || [];
      if (!jobs.length) {
        box.innerHTML = '<div class="fetch-empty">No jobs found. Try a different role or location.</div>';
        return;
      }

      box.innerHTML = jobs.map(j =>
        '<div class="job-card">' +
          '<div class="job-card-head">' +
            '<div class="job-card-title">' + escapeHtml(j.title) + '</div>' +
            (j.language ? '<span class="job-card-lang">' + escapeHtml(j.language) + '</span>' : '') +
          '</div>' +
          '<div class="job-card-meta">' +
            escapeHtml(j.company || 'Unknown company') +
            (j.location ? ' · ' + escapeHtml(j.location) : '') +
          '</div>' +
          (j.description ? '<div class="job-card-desc">' + escapeHtml(j.description) + '</div>' : '') +
          (j.url ? '<a class="job-card-link" href="' + escapeHtml(j.url) +
                   '" target="_blank" rel="noopener">Open posting ↗</a>' : '') +
        '</div>'
      ).join('');
    })
    .catch(e => {
      btn.disabled = false;
      btn.textContent = '→ Fetch Jobs';
      box.innerHTML = '<div class="fetch-empty">Fetch error: ' + escapeHtml(String(e)) + '</div>';
    });
};
