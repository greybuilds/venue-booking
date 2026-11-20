/* Landing page generative pieces: Gates and Dial. See docs/slot-drift.md */
(function () {
  if (typeof p5 === "undefined") return;
  const INK = "#111111", ORANGE = "#FF6A00", HAIR = "#E4E4E0";
  const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function pauseOffscreen(host, p) {
    if (still || !("IntersectionObserver" in window)) return;
    new IntersectionObserver(es => es[0].isIntersecting ? p.loop() : p.noLoop()).observe(host);
  }

  function gates(host) {
    const params = { seed: 21, gates: 4, spawnEvery: 9, speed: 1.9 };
    new p5(function (p) {
      let dots = [], G = [];
      const layout = () => {
        G = [];
        for (let i = 0; i < params.gates; i++) G.push({ x: p.width * (0.3 + i * 0.17), gy: p.random(0.2, 0.8) * p.height, gap: p.height * 0.2 });
      };
      p.setup = function () {
        p.createCanvas(host.clientWidth, host.clientHeight).parent(host);
        p.randomSeed(params.seed); layout();
        if (still) { for (let i = 0; i < 260; i++) tick(); draw(); p.noLoop(); }
        pauseOffscreen(host, p);
      };
      function tick() {
        if (p.frameCount % params.spawnEvery === 0) dots.push({ x: -6, y: p.random(p.height), s: params.speed * p.random(0.8, 1.2), hot: false });
        for (const d of dots) {
          d.x += d.s;
          d.hot = false;
          for (const g of G) {
            const dist = g.x - d.x;
            if (dist > 0 && dist < 110 && Math.abs(d.y - g.gy) > g.gap / 2 - 6) { d.y = p.lerp(d.y, g.gy + p.random(-4, 4), 0.05); d.hot = true; }
          }
        }
        dots = dots.filter(d => d.x < p.width + 8);
      }
      function draw() {
        p.background(255);
        p.stroke(INK); p.strokeWeight(1.5);
        for (const g of G) { p.line(g.x, 0, g.x, g.gy - g.gap / 2); p.line(g.x, g.gy + g.gap / 2, g.x, p.height); }
        p.noStroke();
        for (const d of dots) { p.fill(d.hot ? ORANGE : INK); p.circle(d.x, d.y, d.hot ? 9 : 6); }
      }
      p.draw = function () { tick(); draw(); };
      p.windowResized = function () { p.resizeCanvas(host.clientWidth, host.clientHeight); p.randomSeed(params.seed); layout(); dots = []; };
    });
  }

  function dial(host) {
    const params = { seed: 5, rings: 6, step: 0.0045, life: 900, spawnEvery: 38 };
    new p5(function (p) {
      let arcs = [], hand = 0;
      const spawn = (age) => {
        const r = p.floor(p.random(params.rings)), a = p.random(p.TWO_PI), span = p.random(0.25, 0.9);
        arcs.push({ r, a, span, age: age || 0, flare: 0 });
      };
      p.setup = function () {
        p.createCanvas(host.clientWidth, host.clientHeight).parent(host);
        p.randomSeed(params.seed);
        for (let i = 0; i < 14; i++) spawn(p.floor(p.random(params.life * 0.7)));
        if (still) { draw(); p.noLoop(); }
        pauseOffscreen(host, p);
      };
      function draw() {
        p.background(255);
        const cx = p.width * 0.5, cy = p.height * 0.5, R = Math.min(p.width, p.height) * 0.46, gap = R / (params.rings + 1.2);
        p.noFill();
        for (let i = 0; i < params.rings; i++) { p.stroke(HAIR); p.strokeWeight(1); p.circle(cx, cy, 2 * (gap * (i + 1.2))); }
        p.stroke(HAIR);
        for (let h = 0; h < 24; h++) { const a = h / 24 * p.TWO_PI - p.HALF_PI; p.line(cx + p.cos(a) * gap * 0.9, cy + p.sin(a) * gap * 0.9, cx + p.cos(a) * R, cy + p.sin(a) * R); }
        for (const b of arcs) {
          const rad = gap * (b.r + 1.2), f = p.constrain((params.life - b.age) / 60, 0, 1);
          p.strokeCap(p.SQUARE); p.strokeWeight(10);
          p.drawingContext.globalAlpha = f;
          p.stroke(p.lerpColor(p.color(INK), p.color(ORANGE), b.flare));
          p.arc(cx, cy, 2 * rad, 2 * rad, b.a - p.HALF_PI, b.a + b.span - p.HALF_PI);
          p.drawingContext.globalAlpha = 1;
        }
        const ha = hand - p.HALF_PI;
        p.stroke(ORANGE); p.strokeWeight(2); p.line(cx, cy, cx + p.cos(ha) * R, cy + p.sin(ha) * R);
        p.noStroke(); p.fill(ORANGE); p.circle(cx, cy, 10);
      }
      p.draw = function () {
        hand = (hand + params.step * 2) % p.TWO_PI;
        if (p.frameCount % params.spawnEvery === 0) spawn();
        for (const b of arcs) {
          b.age++;
          const d = ((hand - b.a) % p.TWO_PI + p.TWO_PI) % p.TWO_PI;
          b.flare = d < b.span ? 1 : Math.max(0, b.flare - 0.03);
        }
        arcs = arcs.filter(b => b.age < params.life);
        draw();
      };
      p.windowResized = function () { p.resizeCanvas(host.clientWidth, host.clientHeight); };
    });
  }

  function field(host) {
    const params = { seed: 11, cell: 34, speed: 0.00035, scale: 0.0016 };
    new p5(function (p) {
      let t = 0;
      p.setup = function () {
        p.createCanvas(host.clientWidth, host.clientHeight).parent(host);
        p.noiseSeed(params.seed); p.pixelDensity(1);
        if (still) { draw(); p.noLoop(); }
        pauseOffscreen(host, p);
      };
      function draw() {
        p.clear();
        p.strokeCap(p.SQUARE);
        const c = params.cell, L = c * 0.62;
        for (let y = c / 2; y < p.height; y += c) {
          for (let x = c / 2; x < p.width; x += c) {
            const n = p.noise(x * params.scale, y * params.scale, t);
            const a = n * p.TWO_PI * 2;
            const hot = n > 0.6, dark = n < 0.42;
            if (hot) { p.stroke(255, 106, 0, 200); p.strokeWeight(2.5); }
            else if (dark) { p.stroke(17, 17, 17, 95); p.strokeWeight(1.8); }
            else { p.stroke(17, 17, 17, 44); p.strokeWeight(1.2); }
            const dx = p.cos(a) * L / 2, dy = p.sin(a) * L / 2;
            p.line(x - dx, y - dy, x + dx, y + dy);
          }
        }
      }
      p.draw = function () { t += params.speed * p.deltaTime; draw(); };
      p.windowResized = function () { p.resizeCanvas(host.clientWidth, host.clientHeight); if (still) draw(); };
    });
  }

  const g = document.querySelector('[data-art="gates"]'), d = document.querySelector('[data-art="dial"]');
  if (g) gates(g);
  if (d) dial(d);
  const f = document.querySelector('[data-art="field"]');
  if (f) field(f);
})();
