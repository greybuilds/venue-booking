/* Nav: the dashed "request" block follows the hovered or focused link, like the demo's slot. Desktop only; mobile gets plain rows. */
document.querySelectorAll('[data-navtrack]').forEach((track) => {
  const links = [...track.querySelectorAll('.nav-link')];
  const point = (el) => {
    const first = !track.classList.contains('is-on');
    if (first) track.classList.add('snap');
    const t = track.getBoundingClientRect(), r = el.getBoundingClientRect();
    track.style.setProperty('--x', (r.left - t.left - 1) + 'px');
    track.style.setProperty('--w', r.width + 'px');
    track.classList.add('is-on');
    if (first) { track.getBoundingClientRect(); track.classList.remove('snap'); }
  };
  const off = () => track.classList.remove('is-on');
  links.forEach((l) => {
    l.addEventListener('pointerenter', () => { if (matchMedia('(min-width: 992px)').matches) point(l); });
    l.addEventListener('focus', () => { if (matchMedia('(min-width: 992px)').matches && l.matches(':focus-visible')) point(l); });
  });
  track.addEventListener('pointerleave', off);
  track.addEventListener('focusout', (e) => { if (!track.contains(e.relatedTarget)) off(); });
});

/* Condense the pill after the first screen of scrolling (desktop). */
(() => {
  const nav = document.querySelector('.vb-nav');
  if (!nav) return;
  const set = () => nav.classList.toggle('is-floating', scrollY > 80 && matchMedia('(min-width: 992px)').matches);
  addEventListener('scroll', set, { passive: true });
  addEventListener('resize', set);
  set();
})();
