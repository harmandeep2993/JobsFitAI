// assets/js/theme.js
// Theme toggle — light / dark
// Saves preference to localStorage key 'jf'

function toggleTheme() {
  const root = document.documentElement;
  const btn  = document.getElementById('themechange');

  if (root.classList.contains('dark')) {
    root.classList.remove('dark');
    localStorage.setItem('jf', 'light');
    if (btn) btn.textContent = '☀️';
  } else {
    root.classList.add('dark');
    localStorage.setItem('jf', 'dark');
    if (btn) btn.textContent = '🌙';
  }
}

// Restore saved theme and bind toggle button
// Uses retry IIFE — button may not exist at load time
(function bindTheme() {
  const btn = document.getElementById('themechange');

  if (btn) {
    btn.addEventListener('click', toggleTheme);

    // Restore saved preference
    const saved = localStorage.getItem('jf');
    if (saved === 'dark') {
      document.documentElement.classList.add('dark');
      btn.textContent = '🌙';
    }
  } else {
    setTimeout(bindTheme, 50);
  }
})();