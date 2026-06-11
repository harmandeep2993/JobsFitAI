// Sidebar navigation - switches views using .active class for CSS transitions

window.showView = function(name) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  const view = document.getElementById('view-' + name);
  if (view) view.classList.add('active');

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
