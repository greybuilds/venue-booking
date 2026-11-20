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

// the demo: drag the request across the day; it snaps to the nearest free slot
(function () {
  var frame = document.querySelector('.app-frame');
  var track = frame && frame.querySelector('.track');
  var lane = track && track.querySelector('.track__lane');
  var req = track && track.querySelector('[data-drag]');
  var live = frame && frame.querySelector('[data-live]');
  if (!req || !live) return;
  frame.classList.add('is-js');
  req.tabIndex = 0;
  req.setAttribute('role', 'slider');
  req.setAttribute('aria-label', 'Requested start time');
  req.setAttribute('aria-valuemin', '8'); req.setAttribute('aria-valuemax', '18');

  var LEN = 2, SPAN = 12;                       // request is 2h on a 12h day (08:00 to 20:00)
  var BOOKED = [[0, 2, 'Chess Society'], [6, 8, 'Robotics']];
  var h = 1.5, dragging = false, startX = 0, startH = 0;

  function clash(x) {
    for (var i = 0; i < BOOKED.length; i++) if (x < BOOKED[i][1] && x + LEN > BOOKED[i][0]) return BOOKED[i];
    return null;
  }
  function nearestFree(x) {
    var best = null, d = 99;
    [2, 4, 8, 10].forEach(function (f) { if (Math.abs(f - x) < d) { d = Math.abs(f - x); best = f; } });
    return best;
  }
  function clock(x) { var m = Math.round((8 + x) * 2) * 30; return ('0' + Math.floor(m / 60)).slice(-2) + ':' + ('0' + (m % 60)).slice(-2); }
  function place(x) {
    req.style.transform = 'translateX(' + ((x - 1.5) * lane.clientWidth / SPAN) + 'px)';
  }
  function say(x, settled) {
    var c = clash(x);
    frame.dataset.state = c ? 'clash' : 'ok';
    var span = clock(x) + ' to ' + clock(x + LEN);
    live.innerHTML = c ? '<b>Clash</b> with ' + c[2] + ', ' + span
                       : '<b>' + (settled ? 'Confirmed' : 'Free') + '</b> Coding Club, ' + span;
    req.setAttribute('aria-valuenow', String(8 + x));
    req.setAttribute('aria-valuetext', span);
  }
  function enter() { if (!frame.classList.contains('is-live')) { frame.classList.add('is-live'); place(h); say(h, false); } }
  function snap() {
    h = Math.round(h * 2) / 2;
    if (clash(h)) h = nearestFree(h);
    place(h); say(h, true);
  }

  req.addEventListener('pointerdown', function (e) {
    enter();
    dragging = true; startX = e.clientX; startH = h;
    req.classList.add('is-dragging');
    req.setPointerCapture(e.pointerId);
    e.preventDefault();
  });
  req.addEventListener('pointermove', function (e) {
    if (!dragging) return;
    var perH = lane.clientWidth / SPAN;
    h = Math.min(SPAN - LEN, Math.max(0, startH + (e.clientX - startX) / perH));
    place(h); say(h, false);
  });
  function end() { if (!dragging) return; dragging = false; req.classList.remove('is-dragging'); snap(); }
  req.addEventListener('pointerup', end);
  req.addEventListener('pointercancel', end);
  req.addEventListener('keydown', function (e) {
    var step = e.key === 'ArrowRight' ? 0.5 : e.key === 'ArrowLeft' ? -0.5 : 0;
    if (!step) return;
    e.preventDefault(); enter();
    h = Math.min(SPAN - LEN, Math.max(0, h + step)); place(h); say(h, !clash(h));
  });
  window.addEventListener('resize', function () { if (frame.classList.contains('is-live')) place(h); });
})();
