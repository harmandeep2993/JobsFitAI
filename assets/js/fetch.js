// Topbar navigation - switches views using .active class for CSS transitions

window.toggleSettings = function() {
  var drawer = document.getElementById('settings-drawer');
  var backdrop = document.getElementById('settings-backdrop');
  if (!drawer) return;
  var isOpen = drawer.classList.contains('open');
  drawer.classList.toggle('open', !isOpen);
  if (backdrop) backdrop.classList.toggle('open', !isOpen);
};

window.closeSettings = function() {
  var drawer = document.getElementById('settings-drawer');
  var backdrop = document.getElementById('settings-backdrop');
  if (drawer) drawer.classList.remove('open');
  if (backdrop) backdrop.classList.remove('open');
};

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
