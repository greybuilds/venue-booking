(function () {
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // pause button on the demo loop
  var frame = document.querySelector('.app-frame');
  var pause = document.querySelector('[data-pause]');
  if (frame && pause) {
    pause.tabIndex = 0;
    pause.addEventListener('click', function () {
      var p = frame.classList.toggle('is-paused');
      pause.textContent = p ? 'Play' : 'Pause';
      pause.setAttribute('aria-label', p ? 'Play the demo' : 'Pause the demo');
    });
    frame.removeAttribute('aria-hidden');
  }

  // the one dealt moment: words light up as the section scrolls
  var sec = document.querySelector('[data-moment]');
  var h = sec && sec.querySelector('[data-words]');
  if (!h || reduce) return;
  var keys = ['opening hours,', 'clashes,', 'length', 'weekly', 'limit'];
  var words = h.textContent.trim().split(/\s+/);
  h.setAttribute('aria-label', h.textContent.trim());
  h.textContent = '';
  var spans = words.map(function (w, i) {
    var s = document.createElement('span');
    s.className = 'w';
    s.setAttribute('aria-hidden', 'true');
    s.textContent = w;
    h.appendChild(s);
    if (i < words.length - 1) h.appendChild(document.createTextNode(' '));
    return s;
  });
  ['hours,', 'clashes,', 'length', 'weekly'].forEach(function (k) {
    spans.forEach(function (s) { if (s.textContent === k) s.classList.add('key'); });
  });
  document.documentElement.classList.add('js-moment');
  var ticking = false;
  function update() {
    ticking = false;
    var r = sec.getBoundingClientRect();
    var total = r.height - window.innerHeight;
    var p = total > 0 ? Math.min(1, Math.max(0, -r.top / total)) : 1;
    var n = Math.round(p * 1.15 * spans.length);
    spans.forEach(function (s, i) { s.classList.toggle('lit', i < n); });
  }
  window.addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
  window.addEventListener('resize', update);
  update();
})();
