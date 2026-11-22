/* Inner-page motion: elements rise in as they enter the viewport, staggered when several arrive together. The landing page has its own scroll-linked reveals, so it is skipped here. */
(() => {
  if (document.querySelector('.home-hero') || !('IntersectionObserver' in window)) return;
  const main = document.getElementById('main-content');
  if (!main) return;
  const sel = '.page-head, h1:not(.dhead h1), .nav-pills, .legend, .vb-card:not(.facts), .table tbody tr, form .mb-3, .alert, .receipt, .detail-list';
  const els = [...main.querySelectorAll(sel)].filter((e) => !e.closest('.auth-card') && !e.parentElement.closest('.rv'));
  if (!els.length) return;
  document.documentElement.classList.add('js-rv');
  els.forEach((e) => e.classList.add('rv'));
  const io = new IntersectionObserver((entries) => {
    let i = 0;
    entries.filter((en) => en.isIntersecting).forEach((en) => {
      en.target.style.setProperty('--i', Math.min(i++, 8));
      en.target.classList.add('rv-in');
      io.unobserve(en.target);
      setTimeout(() => en.target.classList.remove('rv', 'rv-in'), 1400);
    });
  }, { rootMargin: '0px 0px -6% 0px', threshold: 0.05 });
  els.forEach((e) => io.observe(e));
})();
