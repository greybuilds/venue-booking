/* Rolling numbers. <number-flow data-n="3">3</number-flow> counts up on load; the plain text
   stays in place if the library does not load. After an HTMX action the server sends
   HX-Trigger {"pending": n} and the chip rolls to the new value. */
import 'https://cdn.jsdelivr.net/npm/number-flow@0.6.2/+esm';

const els = [...document.querySelectorAll('number-flow[data-n]')];
await customElements.whenDefined('number-flow');
els.forEach((el) => {
  const n = Number(el.dataset.n);
  el.update(0);
  setTimeout(() => el.update(n), 120);
});

document.addEventListener('pending', (e) => {
  const n = Number(e.detail && e.detail.value);
  const counts = (e.detail && e.detail.counts) || {};
  Object.entries(counts).forEach(([k, v]) => document.querySelectorAll('[data-tabcount="' + k + '"]').forEach((el) => { el.textContent = v; }));
  const chip = document.querySelector('[data-pending]');
  if (!chip || Number.isNaN(n)) return;
  chip.classList.toggle('is-empty', n === 0);
  const el = chip.querySelector('number-flow');
  if (el) el.update(n);
});
