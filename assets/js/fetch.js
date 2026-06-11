// assets/js/fetch.js
// Sidebar navigation — switches between the views and refreshes data-backed
// tabs when opened.

window.showView = function(name) {
  document.querySelectorAll('.view').forEach(v => { v.style.display = 'none'; });
  const view = document.getElementById('view-' + name);
  if (view) view.style.display = 'block';

  document.querySelectorAll('.jfai-sidebar .sb-item')
    .forEach(el => el.classList.remove('active'));
  const nav = document.getElementById('nav-' + name);
  if (nav) nav.classList.add('active');

  if (name === 'matches' && typeof window.loadMatchState === 'function') {
    window.loadMatchState();
  }
  if (name === 'history' && typeof window.loadHistory === 'function') {
    window.loadHistory();
  }
};
