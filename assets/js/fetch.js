// Sidebar navigation - switches views using .active class for CSS transitions

const VIEW_TITLES = { analyzer: 'Analyzer', ats: 'ATS Maker', matches: 'Job Matches', history: 'History', settings: 'Settings' };

window.showView = function(name) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  const view = document.getElementById('view-' + name);
  if (view) view.classList.add('active');

  document.querySelectorAll('.jfai-sidebar .sb-item')
    .forEach(el => el.classList.remove('active'));
  const nav = document.getElementById('nav-' + name);
  if (nav) nav.classList.add('active');

  const titleEl = document.getElementById('tb-page-title');
  if (titleEl) titleEl.textContent = VIEW_TITLES[name] || name;

  if (name === 'ats' && typeof window.atInit === 'function') {
    window.atInit();
  }
  if (name === 'matches' && typeof window.loadMatchState === 'function') {
    window.loadMatchState();
  }
  if (name === 'history' && typeof window.loadHistory === 'function') {
    window.loadHistory();
  }
};
