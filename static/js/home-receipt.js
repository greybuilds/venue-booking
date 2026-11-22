/* Landing hero: a sample booking receipt prints out of a slot, fills in row by row, gets stamped, then tears off and the next one prints. */
(function () {
  var root = document.querySelector('[data-receipt]');
  if (!root) return;
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var wrap = root.querySelector('[data-slip]'), stamp = root.querySelector('[data-stamp]'), qr = root.querySelector('[data-qr]');
  var lines = [].slice.call(root.querySelectorAll('[data-l]'));
  var ITEMS = [
    { ref: 'RML-2026-00042', society: 'Computing Society', by: 'A. Khan (President)', venue: 'Seminar Hall, Block B', date: 'Wed 25 Nov 2026', time: '2:00 pm - 5:00 pm (3 hrs)', purpose: 'Hackathon kick-off' },
    { ref: 'RML-2026-00057', society: 'Robotics Club', by: 'S. Malik (Vice President)', venue: 'CS Lab 2, Computing Block', date: 'Fri 27 Nov 2026', time: '10:00 am - 12:00 pm (2 hrs)', purpose: 'Line-follower workshop' },
    { ref: 'RML-2026-00063', society: 'Drama Society', by: 'H. Ali (President)', venue: 'Main Seminar Hall, Admin Block', date: 'Sat 28 Nov 2026', time: '9:00 am - 1:00 pm (4 hrs)', purpose: 'Spring play rehearsal' }
  ];

  // a QR-shaped code, seeded from the reference so each receipt has its own (decorative: it is sample data)
  function code(seed) {
    var N = 25, h = 2166136261;
    for (var i = 0; i < seed.length; i++) { h ^= seed.charCodeAt(i); h = Math.imul(h, 16777619); }
    function rnd() { h += 0x6D2B79F5; var t = Math.imul(h ^ (h >>> 15), 1 | h); t ^= t + Math.imul(t ^ (t >>> 7), 61 | t); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }
    var d = '';
    function cell(x, y) { d += 'M' + x + ' ' + y + 'h1v1h-1z'; }
    function finder(ox, oy) {
      for (var y = 0; y < 7; y++) for (var x = 0; x < 7; x++) {
        var edge = x === 0 || y === 0 || x === 6 || y === 6, core = x >= 2 && x <= 4 && y >= 2 && y <= 4;
        if (edge || core) cell(ox + x, oy + y);
      }
    }
    function inFinder(x, y) { return (x < 8 && y < 8) || (x > N - 9 && y < 8) || (x < 8 && y > N - 9); }
    for (var y = 0; y < N; y++) for (var x = 0; x < N; x++) {
      if (inFinder(x, y)) continue;
      var timing = (x === 6 || y === 6) ? ((x + y) % 2 === 0) : rnd() < 0.5;
      if (timing) cell(x, y);
    }
    finder(0, 0); finder(N - 7, 0); finder(0, N - 7);
    qr.innerHTML = '<path d="' + d + '"/>';
  }

  function fill(it) {
    Object.keys(it).forEach(function (k) { var e = root.querySelector('[data-r="' + k + '"]'); if (e) e.textContent = it[k]; });
    code(it.ref);
  }
  var timers = [], n = 0;
  function later(fn, ms) { timers.push(setTimeout(fn, ms)); }

  function cycle() {
    wrap.className = 'rcp__wrap';
    lines.forEach(function (l) { l.classList.remove('is-in'); });
    stamp.classList.remove('is-on');
    fill(ITEMS[n++ % ITEMS.length]);
    void wrap.offsetWidth;
    wrap.classList.add('is-in');
    lines.forEach(function (l, i) { later(function () { l.classList.add('is-in'); }, 350 + i * 290); });
    later(function () { stamp.classList.add('is-on'); }, 3100);
    later(function () { wrap.classList.remove('is-in'); wrap.classList.add('is-out'); }, 8200);
    later(cycle, 9000);
  }

  if (reduce) {
    fill(ITEMS[0]);
    wrap.style.transform = 'none';
    lines.forEach(function (l) { l.classList.add('is-in'); l.style.transition = 'none'; });
    stamp.classList.add('is-on'); stamp.style.transition = 'none';
    return;
  }
  // wait for the landing intro before the first print
  // the first slip starts printing as the curtain lifts; skipping the intro brings it forward
  var first = setTimeout(cycle, document.documentElement.classList.contains('has-intro') ? 1200 : 400);
  document.addEventListener('intro-skip', function () { clearTimeout(first); first = setTimeout(cycle, 300); }, { once: true });
})();
