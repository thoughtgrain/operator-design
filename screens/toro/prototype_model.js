// Toro revision 3, frame by frame: mirrors gen_frames.frame() with the motion in motion.md.
// MODEL and LAYERS are injected by build_prototype.py from gen_frames.py.
(() => {
"use strict";
const M = MODEL, G = M.G, NS = "http://www.w3.org/2000/svg";
const grey = l => G[Math.max(0, Math.min(7, Math.round(l * 7)))];
const CONTROLS = M.CONTROLS, DEFAULTS = M.DEFAULTS;
const WHAT = {
  spread: "the Moon slides along its dotted ephemeris track",
  fold: "the Milky Way's contours fold at the edges, 1× to 8×, and brighten as the band thickens",
  cutoff: "the magnifier moves in on Aldebaran: a point grows into the star's disk",
  res: "Airy rings round the magnified star, fading outward",
  shape: "the Moon's phase, crescent to full",
  noise: "faint stars come out, 40 to 165",
  drive: "more Taurid meteor trails are plotted",
  aphx: "stars drift off their places, gently then wildly",
};

// ---- geometry (same as gen_frames.py) ----
const f = v => (Math.round(v * 1000) / 1000).toString();
const poly = pts => "M " + pts.map(([x, y]) => f(x) + " " + f(y)).join(" L ") + " Z";
const dot = (r, n = 10) => Array.from({ length: n }, (_, k) => [Math.cos(k * 2 * Math.PI / n) * r, Math.sin(k * 2 * Math.PI / n) * r]);
function annulus(r, w, n = 31, gap = 1.5) {
  const a = Array.from({ length: n }, (_, k) => (gap / 2 + (360 - gap) * k / (n - 1)) * Math.PI / 180);
  return a.map(t => [Math.cos(t) * (r + w / 2), Math.sin(t) * (r + w / 2)]).concat(a.slice().reverse().map(t => [Math.cos(t) * (r - w / 2), Math.sin(t) * (r - w / 2)]));
}
function ribbon(pts, w) {
  const ns = pts.map((_, i) => { const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)]; const dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1; return [-dy / l * w / 2, dx / l * w / 2]; });
  return pts.map(([x, y], i) => [x + ns[i][0], y + ns[i][1]]).concat(pts.map(([x, y], i) => [x - ns[i][0], y - ns[i][1]]).reverse());
}
const taper = (len, w0, w1) => [[0, -w0 / 2], [len, -w1 / 2], [len, w1 / 2], [0, w0 / 2]];
const rot = (pts, deg) => { const c = Math.cos(deg * Math.PI / 180), s = Math.sin(deg * Math.PI / 180); return pts.map(([x, y]) => [x * c - y * s, x * s + y * c]); };
const spike = (r, inner = 0.05) => Array.from({ length: 8 }, (_, k) => { const a = -Math.PI / 2 + k * Math.PI / 4, rr = k % 2 ? r * inner : r; return [Math.cos(a) * rr, Math.sin(a) * rr]; });
function foldSignal(s) { while (s > 1 || s < -1) s = s > 1 ? 2 - s : -2 - s; return s; }
const hrand = (i, salt) => { const x = Math.sin(i * 12.9898 + salt * 78.233) * 43758.5453; return x - Math.floor(x); };
function moonPhase(lit, r = M.MOON.r) {
  const ts = Array.from({ length: 16 }, (_, i) => (-78 + 156 * i / 15) * Math.PI / 180);
  return ts.map(t => [r * Math.cos(t), r * Math.sin(t)]).concat(ts.slice().reverse().map(t => [(1 - 2 * lit) * r * Math.cos(t), r * Math.sin(t)]));
}
const inInset = (x, y, pad = 0) => Math.hypot(x - M.INSET[0], y - M.INSET[1]) < M.INSET_R + pad;
const onBody = (x, y) => x >= 2 && x <= 478 && y >= M.BODY_TOP + 2 && y <= 218;

// ---- screen: static layers and nodes in artwork order ----
const svg = document.getElementById("screen");
const el = (tag, attrs, parent = svg) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); parent.appendChild(e); return e; };
const layer = html => { const gEl = el("g", {}); gEl.innerHTML = html; return gEl; };
el("rect", { x: 0, y: 0, width: 480, height: 220, fill: "#000000" });
layer(LAYERS.back);
const nodes = [];
const node = (pts, fill) => { const e = el("path", { d: poly(pts), fill: fill || G[5] }); const n = { e, key: "" }; nodes.push(n); return n; };
const mw = [0, 1, 2].map(() => { const e = el("path", { d: "", fill: "none", stroke: G[2], "stroke-width": 1.5, transform: `translate(${M.MW.origin[0]} ${M.MW.origin[1]})` }); const n = { e, key: "" }; nodes.push(n); return n; });
const trails = M.TRAIL.map(([, , , len]) => node(taper(len, 1.6, 0.5)));
const field = M.FIELD.map(([, , r]) => node(dot(r)));
const joinNodes = M.JOINS.map(([a, b]) => { const [xa, ya] = M.POS[a], [xb, yb] = M.POS[b]; const d = Math.hypot(xb - xa, yb - ya); return node(rot(ribbon([[0, 0], [d, 0]], M.LINE_W), Math.atan2(yb - ya, xb - xa) * 180 / Math.PI), G[3]); });
layer(LAYERS.halos);
const starNames = Object.keys(M.STARS);
const stars = starNames.map(n => node(dot(M.STARS[n]), G[6]));
layer(LAYERS.labels);
const moonBody = node(dot(M.MOON.r, 32), G[1]);
const phases = Array.from({ length: M.MOON.phases }, (_, k) => node(moonPhase(0.1 + 0.9 * k / (M.MOON.phases - 1)), G[3]));
const moonLimb = node(annulus(M.MOON.r, M.LINE_W, 31), G[6]);
layer(LAYERS.inset);
const insetSpike = node(spike(30));
const insetStar = node(dot(30, 32), G[5]);
const insetCore = node(dot(30, 32), G[7]);
const rings = [0, 1, 2, 3].map(() => node(annulus(30, 1.3, 31)));
const neigh = [[13, -9], [-11, 12]].map(() => node(dot(1.7), G[5]));

// header preview (two pages, page 1 edited)
const hdr = el("g", {});
el("rect", { x: 0, y: 0, width: 480, height: 38, fill: "#000000" }, hdr);
G.forEach((c, i) => el("rect", { x: 60 * i, y: 0, width: 60, height: 20, fill: c }, hdr));
const font = "UniversNextPro-Light, Helvetica Neue, Helvetica, Arial, sans-serif";
const hv = [], hv2 = [];
for (let col = 0; col < 4; col++) {
  const light = col < 2 ? "#CBCBCB" : "#000000";
  const mk = (x, y, size, fill, txt) => { const e = el("text", { x, y, "font-size": size, fill, "font-family": font, "font-weight": 300 }, hdr); e.textContent = txt; return e; };
  mk(5 + 120 * col, 10, 10, light, CONTROLS[col]); hv.push(mk(65 + 120 * col, 17.4, 20, light, ""));
  mk(5 + 120 * col, 33, 10, "#5A5A5A", CONTROLS[col + 4]); hv2.push(mk(65 + 120 * col, 33, 13, "#707070", ""));
}

// ---- state ----
const target = Object.assign({}, DEFAULTS), eased = Object.assign({}, DEFAULTS);
const S = { notes: false, interval: 0.125, reduced: false, sweeping: true, manualNotes: false, t: 0, serial: 0, noteAge: 9, held: false,
  lit: new Array(M.FIELD.length).fill(false), litAt: new Array(M.FIELD.length).fill(-9), clock: 0, nextNote: 0, trailHit: 3 };
const q = v => Math.round(v * 1024) / 1024;
function place(n, x, y, a, s, fill, visible = true) {
  const key = visible ? `${q(x)},${q(y)},${Math.round(a * 10)},${q(s)},${fill}` : "hidden";
  if (key === n.key) return 0;
  n.key = key;
  if (!visible) { n.e.setAttribute("visibility", "hidden"); return 1; }
  n.e.setAttribute("visibility", "visible");
  n.e.setAttribute("transform", `translate(${f(x)} ${f(y)}) rotate(${f(a)}) scale(${f(s)})`);
  n.e.setAttribute("fill", fill);
  return 1;
}

// ---- sweep timeline ----
const PHASE_LIST = [{ name: "rest", dur: 2.5, notes: false }, { name: "playing", dur: 3, notes: true }]
  .concat(CONTROLS.map(c => ({ name: c, control: c, dur: 4.8, notes: true })));
const TOTAL = PHASE_LIST.reduce((a, p) => a + p.dur, 0);
function sweepAt(t) { let tt = t % TOTAL; for (const p of PHASE_LIST) { if (tt < p.dur) return [p, tt]; tt -= p.dur; } return [PHASE_LIST[0], 0]; }
function keyframe(def, u) {
  const k = [[0, def], [0.8, 0], [1.2, 0], [3.0, 1], [3.6, 1], [4.8, def]];
  for (let i = 1; i < k.length; i++) if (u <= k[i][0]) { const [t0, v0] = k[i - 1], [t1, v1] = k[i]; return v0 + (v1 - v0) * (u - t0) / (t1 - t0); }
  return def;
}

// ---- the frame ----
function frame(dt) {
  S.clock += dt;
  for (const c of CONTROLS) {
    if (S.reduced) eased[c] = target[c];
    else { eased[c] += (target[c] - eased[c]) * (1 - Math.exp(-dt / 0.035)); if (Math.abs(target[c] - eased[c]) < 0.0015) eased[c] = target[c]; }
  }
  let noteOn = false;
  if (S.notes) {
    S.nextNote -= dt;
    if (S.nextNote <= 0) { S.nextNote += S.interval; S.serial++; noteOn = true; S.noteAge = 0; S.trailHit = (S.trailHit + 5) % M.TRAIL.length; }
    S.held = (S.interval - S.nextNote) < S.interval * 0.55;
  } else { S.held = false; S.nextNote = 0; }
  if (!noteOn) S.noteAge += dt;
  const v = eased, motion = !S.reduced;
  const flash = motion ? Math.exp(-S.noteAge / 0.06) : 0;
  let changed = 0;

  // fold: Milky Way contours (re-key per fold detent; a note brightens the core contour)
  const foldQ = Math.round(v.fold * 100) / 100, gain = 1 + 7 * foldQ, amp = 0.6 + 17 * foldQ ** 1.4;
  const [ox, oy] = M.MW.origin, [ax, ay] = M.MW.a, [bx, by] = M.MW.b;
  const dx = bx - ax, dy = by - ay, ln = Math.hypot(dx, dy), nx = -dy / ln, ny = dx / ln;
  const shades = [G[1], grey((2 + 1.5 * foldQ) / 7), grey((3 + 2 * foldQ + flash) / 7)];
  [26, 17, 8].forEach((half, c) => {
    const n = mw[c], key = `${foldQ}|${shades[c]}`;
    if (n.key === key) return;
    const reshape = !n.key.startsWith(`${foldQ}|`);
    n.key = key; changed++;
    n.e.setAttribute("stroke", shades[c]);
    if (!reshape) return;
    const A = [], B = [];
    for (let k = 0; k < 32; k++) {
      const u = k / 31, cx = ax + dx * u, cy = ay + dy * u;
      const tk = 0.35 + 0.65 * Math.sin(Math.PI * Math.min(1, 0.1 + 0.9 * u));
      const la = 0.24 * Math.sin((2.3 + 0.7 * c) * Math.PI * u + 1.9 * c) + 0.12 * Math.sin((5.1 - 0.9 * c) * Math.PI * u + 1.3 + c);
      const lb = 0.22 * Math.sin((1.7 + 0.5 * c) * Math.PI * u + 2.1 + 1.1 * c) + 0.10 * Math.sin((4.3 + 1.3 * c) * Math.PI * u + 0.4);
      const fa = foldSignal(gain * Math.sin((3.7 + 0.6 * c) * Math.PI * u + 2 * c)) * amp * (c + 1) / 3;
      const fb = foldSignal(gain * Math.sin((3.1 - 0.4 * c) * Math.PI * u + c + 1.7)) * amp * (c + 1) / 3;
      const wa = Math.max(1, (half * (1 + la) + fa) * tk), wb = Math.max(1, (half * (1 + lb) + fb) * tk);
      A.push([cx + nx * wa - ox, cy + ny * wa - oy]); B.push([cx - nx * wb - ox, cy - ny * wb - oy]);
    }
    let pts = A.concat(B.reverse());
    const far = Math.max(...pts.map(([x, y]) => Math.max(Math.abs(x), Math.abs(y))));
    if (far > 63.5) pts = pts.map(([x, y]) => [x * 63.5 / far, y * 63.5 / far]);
    n.e.setAttribute("d", poly(pts));
  });

  // drive: plotted meteor trails; a note lights one
  const shownTrails = 2 + Math.round((M.TRAIL.length - 2) * v.drive);
  M.TRAIL.forEach(([x, y, ang], k) => {
    const hit = motion && k === S.trailHit && flash > 0.25;
    changed += place(trails[k], x, y, ang, hit ? 1.4 : 1, hit ? G[7] : grey((3 + 2 * v.drive) / 7), k < shownTrails || hit);
  });

  // noise + aphx: faint stars
  const kink = 0.4 * v.aphx + 0.6 * v.aphx ** 3, shown = M.FIELD_BASE + Math.round((M.FIELD.length - M.FIELD_BASE) * v.noise);
  let budget = 3;
  M.FIELD.forEach(([x, y, , sh], k) => {
    const reach = kink * (6 + 20 * hrand(k, 1)), a = 2 * Math.PI * hrand(k, 2);
    const px = x + Math.cos(a) * reach, py = y + Math.sin(a) * reach;
    if (k >= shown) { S.lit[k] = false; changed += place(field[k], px, py, 0, 1, G[sh], false); return; }
    if (motion && S.held && budget > 0 && S.clock - S.litAt[k] > 0.35 && hrand(k * 31, Math.floor(S.clock * 6)) < 0.05) { S.lit[k] = !S.lit[k]; S.litAt[k] = S.clock; budget--; }
    if (!S.held && S.lit[k]) S.lit[k] = false;
    changed += place(field[k], px, py, 0, S.lit[k] ? 1.25 : 1, S.lit[k] ? G[7] : G[sh], onBody(px, py));
  });

  // the figure: static geometry, brightening on a note
  joinNodes.forEach((n, k) => { const [x, y] = M.POS[M.JOINS[k][0]]; changed += place(n, x, y, 0, 1, grey((3 + 3 * flash) / 7)); });
  starNames.forEach((name, k) => { const [x, y] = M.POS[name]; changed += place(stars[k], x, y, 0, name === "ald" ? 1 + 0.3 * flash : 1, name === "ald" ? G[7] : G[6]); });

  // spread + shape: the Moon
  const mx = M.MOON.x0 + (M.MOON.x1 - M.MOON.x0) * v.spread, phase = Math.round(v.shape * (M.MOON.phases - 1));
  changed += place(moonBody, mx, M.MOON.y, 0, 1, G[1]);
  phases.forEach((n, k) => { changed += place(n, mx, M.MOON.y, 0, 1, G[3], k === phase); });
  changed += place(moonLimb, mx, M.MOON.y, 0, 1, G[6]);

  // cutoff + res: the magnifier
  const [ix, iy0] = M.INSET, iy = iy0 + 4, starR = 1.8 + 25 * v.cutoff;
  changed += place(insetSpike, ix, iy, 0, Math.min(38, starR + 9 + 7 * flash) / 30, grey((4 + 2 * flash) / 7));
  changed += place(insetStar, ix, iy, 0, starR * (1 + 0.12 * flash) / 30, G[5]);
  changed += place(insetCore, ix, iy, 0, Math.max(1.6, starR * 0.78) / 30, G[7]);
  rings.forEach((n, i) => {
    const b = Math.max(0, Math.min(1, v.res * 4 - i + 0.25)), radius = starR + 5 + 5.5 * i;
    changed += place(n, ix, iy, 0, Math.max(radius, 4) / 30, grey((1 + 3.5 * b * (1 - 0.12 * i) + (b > 0 ? 2 * flash : 0)) / 7), b > 0.05 && radius < M.INSET_R - 3);
  });
  const m = 1 + 3.5 * v.cutoff ** 2;
  [[13, -9], [-11, 12]].forEach(([nx2, ny2], k) => { const x = ix + nx2 * m, y = iy + ny2 * m; changed += place(neigh[k], x, y, 0, 1, G[5], inInset(x, y, -4)); });

  // header text slots
  let texts = 0;
  const caps = {}; CONTROLS.forEach(k => caps[k] = String(Math.round(target[k] * 100))); caps.spread = (1 + 0.5 * target.spread).toFixed(2);
  for (let col = 0; col < 4; col++) for (const [arr, name] of [[hv, CONTROLS[col]], [hv2, CONTROLS[col + 4]]]) if (arr[col].textContent !== caps[name]) { arr[col].textContent = caps[name]; texts++; }
  return [changed, texts];
}

// ---- UI ----
const $ = id => document.getElementById(id);
const encWrap = $("encoders"), encs = {};
[["page 1", 0], ["page 2", 4]].forEach(([label, off]) => {
  const pl = document.createElement("div"); pl.className = "pagelabel"; pl.textContent = label; encWrap.appendChild(pl);
  for (let i = 0; i < 4; i++) {
    const name = CONTROLS[off + i], box = document.createElement("label");
    box.className = "enc" + (off ? " p2" : "");
    box.style.setProperty("--step", G[Math.min(7, i * 2 + 1)]);
    box.innerHTML = `<div class="top"><b>${name}</b><span id="v-${name}"></span></div><input type="range" id="r-${name}" min="0" max="100" step="1" aria-label="${name}">`;
    encWrap.appendChild(box);
    const r = box.querySelector("input");
    r.value = Math.round(DEFAULTS[name] * 100);
    r.addEventListener("input", () => { stopSweep(); target[name] = r.value / 100; });
    encs[name] = { box, r, out: box.querySelector("span") };
  }
});
const setPressed = (btn, on) => btn.setAttribute("aria-pressed", on ? "true" : "false");
function manualCaption() { $("phase").textContent = "manual"; $("what").textContent = "turn any control; notes stay as set"; }
function stopSweep() { if (S.sweeping) { S.sweeping = false; setPressed($("play"), false); manualCaption(); } }
$("play").addEventListener("click", () => { S.sweeping = !S.sweeping; setPressed($("play"), S.sweeping); if (S.sweeping) S.t = 0; else manualCaption(); });
$("notes").addEventListener("click", () => { S.notes = !S.notes; S.manualNotes = true; setPressed($("notes"), S.notes); });
$("rm").addEventListener("click", () => { S.reduced = !S.reduced; setPressed($("rm"), S.reduced); });
document.querySelectorAll('input[name="tempo"]').forEach(r => r.addEventListener("change", () => { S.interval = parseFloat(r.value); }));
document.querySelectorAll('input[name="zoom"]').forEach(r => r.addEventListener("change", () => { const z = parseFloat(r.value); svg.setAttribute("width", 480 * z); svg.setAttribute("height", 220 * z); }));
if (window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches) { S.reduced = true; setPressed($("rm"), true); }

// ---- meter ----
const spark = $("spark"), ctx = spark.getContext("2d"), hist = [], times = [];
function drawSpark() {
  const w = spark.width, h = spark.height, max = 40, bw = w / 240;
  ctx.fillStyle = "#141517"; ctx.fillRect(0, 0, w, h);
  hist.forEach((n, i) => { ctx.fillStyle = n > 20 ? "#d3a24f" : "#7d8a93"; const bh = Math.min(h, n / max * h); ctx.fillRect(i * bw, h - bh, Math.max(1, bw - 0.5), bh); });
  const y20 = h - 20 / max * h;
  ctx.strokeStyle = "#a9bcc8"; ctx.setLineDash([6, 6]); ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(0, y20); ctx.lineTo(w, y20); ctx.stroke(); ctx.setLineDash([]);
  ctx.fillStyle = "#8c9095"; ctx.font = "20px IBM Plex Mono, monospace"; ctx.fillText("20", 6, y20 - 6);
}

// ---- loop ----
let last = performance.now();
function tick(now) {
  const dt = Math.min(0.1, (now - last) / 1000); last = now;
  if (S.sweeping) {
    S.t += dt;
    const [p, u] = sweepAt(S.t);
    if (!S.manualNotes) { S.notes = p.notes; setPressed($("notes"), S.notes); }
    for (const c of CONTROLS) target[c] = DEFAULTS[c];
    if (p.control) target[p.control] = keyframe(DEFAULTS[p.control], u);
    $("phase").textContent = p.control ? `${p.name} · ${Math.round(target[p.control] * 100)}` : p.name;
    $("what").textContent = p.control ? WHAT[p.control] : (p.notes ? "defaults, notes playing: the figure brightens, Aldebaran flares, a meteor trail lights, stars twinkle" : "defaults, no notes: nothing should move");
    for (const c of CONTROLS) { encs[c].r.value = Math.round(target[c] * 100); encs[c].box.classList.toggle("live", p.control === c); }
  } else for (const c of CONTROLS) encs[c].box.classList.remove("live");
  for (const c of CONTROLS) encs[c].out.textContent = c === "spread" ? (1 + 0.5 * target[c]).toFixed(2) : Math.round(target[c] * 100);
  const [changed, texts] = frame(dt);
  hist.push(changed); if (hist.length > 240) hist.shift();
  times.push([now, changed]); while (times.length && now - times[0][0] > 4000) times.shift();
  const last1 = times.filter(([t]) => now - t <= 1000);
  $("now").textContent = changed; $("now").classList.toggle("over", changed > 20);
  $("avg").textContent = (last1.reduce((a, [, n]) => a + n, 0) / Math.max(1, last1.length)).toFixed(1);
  $("peak").textContent = times.reduce((mx, [, n]) => Math.max(mx, n), 0);
  $("texts").textContent = texts;
  drawSpark();
  requestAnimationFrame(tick);
}
requestAnimationFrame(tick);
})();
