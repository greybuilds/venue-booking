/* Detail-page art. Two seeded fields, both reading real data.
   occupancy: strokes lie flat where the room is free and stand up (ink = confirmed, orange = waiting) inside booked hours.
   radial:    strokes swirl round the society's initial; verified societies pulse orange outward, others stay grey and slow. */
(function () {
  if (typeof p5 === "undefined") return;
  const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const clamp01 = (x) => Math.min(1, Math.max(0, x));
  const smooth = (a, b, x) => { const t = clamp01((x - a) / (b - a)); return t * t * (3 - 2 * t); };

  function watch(host, p) {
    if ("ResizeObserver" in window) new ResizeObserver(() => { if (host.clientWidth && host.clientHeight) p.resizeCanvas(host.clientWidth, host.clientHeight); }).observe(host);
    if (!still && "IntersectionObserver" in window) new IntersectionObserver((es) => (es[0].isIntersecting ? p.loop() : p.noLoop())).observe(host);
  }
  function pointer(host, p, state) {
    host.addEventListener("pointermove", (e) => { const r = host.getBoundingClientRect(); state.x = e.clientX - r.left; state.y = e.clientY - r.top; });
    host.addEventListener("pointerleave", () => { state.x = state.y = -999; });
  }
  function stroke(p, x, y, a, len, rgb, alpha, w) {
    const dx = Math.cos(a) * len / 2, dy = Math.sin(a) * len / 2;
    p.stroke(rgb[0], rgb[1], rgb[2], alpha); p.strokeWeight(w);
    p.line(x - dx, y - dy, x + dx, y + dy);
  }

  function occupancy(host) {
    const seed = +host.dataset.seed || 1;
    const bars = [...document.querySelectorAll(".timeline .slot")].map((s) => ({ a: +s.dataset.l, b: +s.dataset.l + +s.dataset.w, wait: s.classList.contains("pending") }));
    const m = { x: -999, y: -999 };
    new p5((p) => {
      const cell = 24 + (seed % 3) * 3;
      p.setup = () => {
        p.createCanvas(host.clientWidth, host.clientHeight).parent(host);
        p.noiseSeed(seed); p.frameRate(30); pointer(host, p, m); watch(host, p);
        if (still) { p.noLoop(); p.redraw(); }
      };
      p.draw = () => {
        p.clear();
        const cols = Math.max(4, Math.round(p.width / cell)), rows = Math.max(3, Math.round(p.height / cell));
        const sx = p.width / cols, sy = p.height / rows, tm = still ? 0 : p.frameCount * 0.004;
        for (let j = 0; j < rows; j++) for (let i = 0; i < cols; i++) {
          const x = (i + 0.5) * sx, y = (j + 0.5) * sy, pct = (x / p.width) * 100;
          let occ = 0, wait = false;
          for (const b of bars) {
            const w = smooth(b.a - 2.5, b.a + 0.5, pct) * (1 - smooth(b.b - 0.5, b.b + 2.5, pct));
            if (w > occ) { occ = w; wait = b.wait; }
          }
          const n = p.noise(x * 0.004, y * 0.006, tm + seed);
          let a = p.lerp((n - 0.5) * 0.8, -Math.PI / 2 + (n - 0.5) * 0.35, occ);
          const d = Math.hypot(x - m.x, y - m.y), near = 1 - smooth(0, 110, d);
          if (near > 0) a = p.lerp(a, Math.atan2(m.y - y, m.x - x), near * 0.7);
          const len = p.lerp(sx * 0.5, sy * 0.86, occ);
          if (occ > 0.5) stroke(p, x, y, a, len, wait ? [255, 106, 0] : [17, 17, 17], 235, 2.4);
          else stroke(p, x, y, a, len, near > 0.3 ? [255, 106, 0] : [17, 17, 17], near > 0.3 ? 200 : 55 + n * 50, 1.4);
        }
      };
    });
  }

  function radial(host) {
    const seed = +host.dataset.seed || 1, ok = host.dataset.verified === "1";
    const m = { x: -999, y: -999 };
    new p5((p) => {
      const cell = 22 + (seed % 4) * 2, hole = 64;
      p.setup = () => {
        p.createCanvas(host.clientWidth, host.clientHeight).parent(host);
        p.noiseSeed(seed); p.frameRate(30); pointer(host, p, m); watch(host, p);
        if (still) { p.noLoop(); p.redraw(); }
      };
      p.draw = () => {
        p.clear();
        const cx = p.width / 2, cy = p.height / 2, R = Math.min(p.width, p.height * 1.6) / 2;
        const cols = Math.round(p.width / cell), rows = Math.round(p.height / cell);
        const sx = p.width / cols, sy = p.height / rows, tm = still ? 0 : p.frameCount;
        for (let j = 0; j < rows; j++) for (let i = 0; i < cols; i++) {
          const x = (i + 0.5) * sx, y = (j + 0.5) * sy, dx = x - cx, dy = y - cy, r = Math.hypot(dx, dy);
          if (r < hole) continue;
          const n = p.noise(x * 0.006, y * 0.006, seed), far = smooth(hole, R, r);
          let a = Math.atan2(dy, dx) + Math.PI / 2 + (n - 0.5) * 2.2 * far;
          const d = Math.hypot(x - m.x, y - m.y), near = 1 - smooth(0, 100, d);
          if (near > 0) a = p.lerp(a, Math.atan2(dy, dx), near * 0.6);
          const wave = Math.sin(r * 0.07 - tm * (ok ? 0.07 : 0.025) + seed) * 0.5 + 0.5;
          const fade = 1 - smooth(R * 0.55, R, r), len = p.lerp(sx * 0.9, sx * 0.45, far);
          if (ok && wave > 0.72) stroke(p, x, y, a, len, [255, 106, 0], 230 * fade + 25, 2.4);
          else stroke(p, x, y, a, len, [17, 17, 17], (ok ? 40 : 70) * fade + 12 + (ok ? 0 : wave * 30), 1.5);
        }
      };
    });
  }

  document.querySelectorAll("[data-art]").forEach((host) => {
    if (host.dataset.art === "occupancy") occupancy(host);
    else if (host.dataset.art === "radial") radial(host);
  });

  /* a marker for "now", only when the day shown is today */
  const tl = document.querySelector(".tl[data-day]");
  if (tl) {
    const now = new Date(), pad = (n) => String(n).padStart(2, "0");
    if (tl.dataset.day === now.getFullYear() + "-" + pad(now.getMonth() + 1) + "-" + pad(now.getDate())) {
      const mins = (s) => { const [h, m] = s.split(":").map(Number); return h * 60 + m; };
      const o = mins(tl.dataset.open), c = mins(tl.dataset.close), t = now.getHours() * 60 + now.getMinutes();
      const el = tl.querySelector(".tl__now");
      if (el && t > o && t < c) { el.style.setProperty("--l", ((t - o) / (c - o)) * 100); el.hidden = false; }
    }
  }
})();
