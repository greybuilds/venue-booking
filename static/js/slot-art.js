/* Slot Drift: seeded timetable simulation. See docs/slot-drift.md */
(function () {
  const host = document.querySelector("[data-slot-art]");
  if (!host || typeof p5 === "undefined") return;
  const params = { seed: 8, rooms: 7, slots: 24, spawnEvery: 46, clashHold: 34, life: 520 };
  const INK = "#111111", ORANGE = "#FF6A00", HAIR = "#E4E4E0", SURFACE = "#F6F6F4";
  const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  new p5(function (p) {
    let blocks = [], occ, cw, ch, pad = 18;

    const free = (r, c, w, self) => {
      if (c < 0 || c + w > params.slots) return false;
      for (let i = c; i < c + w; i++) if (occ[r][i] && occ[r][i] !== self) return false;
      return true;
    };
    const mark = (b, v) => { for (let i = b.c; i < b.c + b.w; i++) occ[b.r][i] = v; };

    function spawn() {
      const w = p.floor(p.random(2, 6));
      const b = { r: p.floor(p.random(params.rooms)), c: p.floor(p.random(params.slots - w)), w, age: 0, state: "new" };
      b.x = b.c; b.y = b.r;
      if (free(b.r, b.c, w, null)) { b.state = "set"; mark(b, b); }
      else { b.state = "clash"; b.hold = params.clashHold; }
      blocks.push(b);
    }
    function resolve(b) {
      let best = null, bd = 1e9;
      for (let r = 0; r < params.rooms; r++) for (let c = 0; c <= params.slots - b.w; c++) {
        if (!free(r, c, b.w, null)) continue;
        const d = (r - b.r) * (r - b.r) * 3 + (c - b.c) * (c - b.c);
        if (d < bd) { bd = d; best = { r, c }; }
      }
      if (!best) { b.state = "gone"; return; }
      b.r = best.r; b.c = best.c; b.state = "set"; mark(b, b);
    }
    function reset() {
      p.randomSeed(params.seed); p.noiseSeed(params.seed);
      occ = Array.from({ length: params.rooms }, () => Array(params.slots).fill(null));
      blocks = [];
      for (let i = 0; i < 9; i++) spawn();
      blocks.forEach(b => { if (b.state === "clash") resolve(b); b.x = b.c; b.y = b.r; b.age = p.floor(p.random(params.life * 0.6)); });
    }
    function size() {
      const w = host.clientWidth, h = host.clientHeight || 420;
      p.resizeCanvas(w, h); cw = (w - pad * 2) / params.slots; ch = (h - pad * 2) / params.rooms;
    }
    function draw() {
      p.clear(); p.background(255);
      p.stroke(HAIR); p.strokeWeight(1);
      for (let r = 0; r <= params.rooms; r++) p.line(pad, pad + r * ch, p.width - pad, pad + r * ch);
      for (let c = 0; c <= params.slots; c += 4) p.line(pad + c * cw, pad, pad + c * cw, p.height - pad);
      for (const b of blocks) {
        b.x = p.lerp(b.x, b.c, 0.09); b.y = p.lerp(b.y, b.r, 0.09);
        const x = pad + b.x * cw + 2, y = pad + b.y * ch + 3, w = b.w * cw - 4, h = ch - 6;
        const fade = b.state === "set" ? p.constrain((params.life - b.age) / 60, 0, 1) : 1;
        if (b.state === "clash") {
          const j = p.sin(p.frameCount * 0.7) * 1.2;
          p.noStroke(); p.fill(ORANGE); p.rect(x + j, y, w, h, 6);
        } else {
          p.stroke(INK); p.strokeWeight(1.25); p.fill(p.lerpColor(p.color(255), p.color(SURFACE), 1));
          p.drawingContext.globalAlpha = fade; p.rect(x, y, w, h, 6); p.drawingContext.globalAlpha = 1;
        }
      }
    }
    function step() {
      if (p.frameCount % params.spawnEvery === 0) spawn();
      for (const b of blocks) {
        if (b.state === "clash" && --b.hold <= 0) resolve(b);
        else if (b.state === "set" && ++b.age > params.life) { mark(b, null); b.state = "gone"; }
      }
      blocks = blocks.filter(b => b.state !== "gone");
    }
    p.setup = function () {
      p.createCanvas(host.clientWidth, host.clientHeight || 420).parent(host);
      size(); reset();
      if (still) { for (let i = 0; i < 400; i++) step(); blocks.forEach(b => { b.x = b.c; b.y = b.r; }); draw(); p.noLoop(); }
    };
    p.draw = function () { step(); draw(); };
    p.windowResized = size;
  });
})();
