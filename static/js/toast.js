/* Toasts. Django messages arrive as <li data-toast> inside #toasts; HTMX responses send
   an HX-Trigger header {"toast": {"msg": "...", "type": "success"}}. */
(() => {
  const stack = document.getElementById('toasts');
  if (!stack) return;

  const close = (el) => {
    if (!el || el.dataset.leaving) return;
    el.dataset.leaving = '1';
    clearTimeout(el._t);
    el.classList.add('is-leaving');
    const done = () => el.remove();
    el.addEventListener('animationend', done, { once: true });
    setTimeout(done, 400);
  };

  const arm = (el) => {
    const ms = el.classList.contains('vb-toast--error') ? 8000 : 5000;
    let left = ms, started = performance.now();
    const run = () => { started = performance.now(); el._t = setTimeout(() => close(el), left); };
    el.addEventListener('pointerenter', () => { clearTimeout(el._t); left -= performance.now() - started; });
    el.addEventListener('pointerleave', run);
    el.querySelector('.vb-toast__x').addEventListener('click', () => close(el));
    run();
  };

  const make = (msg, type) => {
    const el = document.createElement('div');
    el.className = 'vb-toast vb-toast--' + (type === 'danger' ? 'error' : type || 'info');
    el.setAttribute('role', type === 'error' ? 'alert' : 'status');
    el.innerHTML = '<span class="vb-toast__dot" aria-hidden="true"></span><span class="vb-toast__msg"></span>' +
      '<button type="button" class="vb-toast__x roundbtn" aria-label="Dismiss"><svg viewBox="0 0 16 16" width="12" height="12"><path d="M4 4l8 8M12 4l-8 8" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg></button>';
    el.querySelector('.vb-toast__msg').textContent = msg;
    stack.append(el);
    arm(el);
    return el;
  };

  window.vbToast = make;
  stack.querySelectorAll('.vb-toast').forEach(arm);
  document.addEventListener('toast', (e) => { if (e.detail && e.detail.msg) make(e.detail.msg, e.detail.type); });
  document.addEventListener('htmx:responseError', () => make('Something went wrong. Try again.', 'error'));
  document.addEventListener('htmx:sendError', () => make('Could not reach the server.', 'error'));
})();
