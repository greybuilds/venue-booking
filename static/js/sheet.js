/* Bottom sheet (Vaul style) on a native <dialog>: focus trap, Esc and inert page for free.
   Opens when HTMX swaps content into #sheet-body. Drag the handle or the sheet down to dismiss. */
(() => {
  const dlg = document.getElementById('sheet');
  const body = document.getElementById('sheet-body');
  if (!dlg || !body || !dlg.showModal) return;
  const calm = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let opener = null;

  const open = () => {
    if (!dlg.open) dlg.showModal();
    dlg.style.removeProperty('--drag');
    dlg.getBoundingClientRect(); /* commit the off-screen start so the slide-up transitions */
    dlg.classList.add('is-open');
  };
  const close = () => {
    if (!dlg.open || dlg.classList.contains('is-closing')) return;
    dlg.classList.remove('is-open');
    dlg.classList.add('is-closing');
    const done = () => { dlg.classList.remove('is-closing'); dlg.close(); };
    if (calm) return done();
    dlg.addEventListener('transitionend', done, { once: true });
    setTimeout(() => dlg.classList.contains('is-closing') && done(), 500);
  };

  document.addEventListener('htmx:beforeRequest', (e) => { if (e.detail.target === body) opener = e.detail.elt; });
  document.addEventListener('htmx:afterSwap', (e) => { if (e.detail.target === body) open(); });
  /* a change made inside the sheet: refresh the page behind it */
  document.addEventListener('bookings-changed', () => {
    if (window.htmx) htmx.ajax('GET', location.href, { target: '#main-content', select: '#main-content', swap: 'outerHTML' });
  });
  dlg.addEventListener('cancel', (e) => { e.preventDefault(); close(); });
  dlg.addEventListener('close', () => { body.innerHTML = ''; if (opener && opener.isConnected) opener.focus({ preventScroll: true }); });
  dlg.addEventListener('click', (e) => { if (e.target === dlg || e.target.closest('[data-sheet-close]')) close(); });

  /* drag to dismiss: follow the finger, then either fling away or spring back */
  let y0 = 0, t0 = 0, dy = 0, drag = false;
  dlg.addEventListener('pointerdown', (e) => {
    if (e.button || !e.target.closest('.vb-sheet__grab, .vb-sheet__panel') || e.target.closest('a, button, input, textarea, select, form')) return;
    if (!e.target.closest('.vb-sheet__grab') && body.scrollTop > 0) return;
    drag = true; y0 = e.clientY; t0 = performance.now(); dy = 0;
    dlg.setPointerCapture(e.pointerId);
    dlg.classList.add('is-drag');
  });
  dlg.addEventListener('pointermove', (e) => {
    if (!drag) return;
    dy = Math.max(0, e.clientY - y0);
    dlg.style.setProperty('--drag', dy + 'px');
  });
  const end = () => {
    if (!drag) return;
    drag = false;
    dlg.classList.remove('is-drag');
    const v = dy / Math.max(1, performance.now() - t0);
    if (dy > 110 || v > 0.6) { dlg.style.setProperty('--drag', '0px'); close(); }
    else dlg.style.setProperty('--drag', '0px');
  };
  dlg.addEventListener('pointerup', end);
  dlg.addEventListener('pointercancel', end);
})();

// A request made after the session ended gets the login page back. Send the whole window there
// instead of filling the sheet (or the page) with a second site.
document.addEventListener('htmx:beforeSwap', (e) => {
  const url = e.detail.xhr && e.detail.xhr.responseURL;
  if (!url) return;
  const u = new URL(url, location.href);
  if (u.pathname.startsWith('/login/') && !location.pathname.startsWith('/login/')) {
    e.detail.shouldSwap = false;
    location.assign(u.href);
  }
});
