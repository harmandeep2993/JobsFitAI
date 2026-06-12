// assets/js/toast.js
// Slide-in toast notifications — replaces all alert() calls

(function () {
  function container() {
    var c = document.getElementById('toast-root');
    if (!c) {
      c = document.createElement('div');
      c.id = 'toast-root';
      c.className = 'toast-root';
      document.body.appendChild(c);
    }
    return c;
  }

  // type: 'ok' | 'err' | 'info' | 'warn'
  window.toast = function (msg, type, duration) {
    type     = type     || 'info';
    duration = duration || 3500;

    var icons = { ok: '✓', err: '✕', info: 'i', warn: '!' };
    var c = container();
    var t = document.createElement('div');
    t.className = 'toast toast-' + type;
    t.innerHTML =
      '<span class="ti">' + (icons[type] || 'i') + '</span>' +
      '<span class="tm">' + msg + '</span>' +
      '<button class="tx" onclick="this.parentElement.remove()" aria-label="Dismiss">✕</button>';

    c.appendChild(t);
    requestAnimationFrame(function () {
      requestAnimationFrame(function () { t.classList.add('show'); });
    });

    setTimeout(function () {
      t.classList.remove('show');
      setTimeout(function () { if (t.parentElement) t.remove(); }, 320);
    }, duration);
  };
})();
