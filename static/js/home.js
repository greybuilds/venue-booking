(function () {
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

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

// reveal on scroll: hidden until they enter the screen, then settle in, siblings one after another
(function () {
  if (!('IntersectionObserver' in window) || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var els = [].slice.call(document.querySelectorAll('.home-block h2, .steps li, .vrow, .home-block .link-draw, .home-close h2, .home-close .btn'));
  if (!els.length) return;
  var seen = new Map();
  els.forEach(function (el) {
    var p = el.parentElement;
    var i = seen.get(p) || 0; seen.set(p, i + 1);
    el.classList.add('rvl');
    el.style.setProperty('--i', Math.min(i, 5));
  });
  document.documentElement.classList.add('js-reveal');
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      e.target.classList.add('in');
      io.unobserve(e.target);
    });
  }, { threshold: 0.15, rootMargin: '0px 0px -8% 0px' });
  els.forEach(function (el) { io.observe(el); });
})();

// the landing intro: any click or key press skips it
(function () {
  var html = document.documentElement;
  if (!html.classList.contains('has-intro')) return;
  function skip() {
    html.classList.add('skip-intro');
    document.dispatchEvent(new Event('intro-skip'));
    off();
  }
  function off() { ['pointerdown', 'keydown'].forEach(function (t) { window.removeEventListener(t, skip); }); }
  ['pointerdown', 'keydown'].forEach(function (t) { window.addEventListener(t, skip); });
  setTimeout(off, 2200);
})();
