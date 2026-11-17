// The bench page. No framework, no build step: the server hands these files over as they are.
import { FrameView } from "./frames.js";
import { Midi, relativeStep } from "./midi.js";

const $ = (sel, el = document) => el.querySelector(sel);
const h = (tag, props = {}, ...kids) => {
  const el = Object.assign(document.createElement(tag), props);
  for (const k of kids.flat()) if (k != null) el.append(k);
  return el;
};
const store = {
  get(key, fallback) {
    try {
      const v = localStorage.getItem("opxy-bench:" + key);
      return v === null ? fallback : JSON.parse(v);
    } catch { return fallback; }
  },
  set(key, value) {
    try { localStorage.setItem("opxy-bench:" + key, JSON.stringify(value)); } catch { /* private window */ }
  },
};
const reduced = matchMedia("(prefers-reduced-motion: reduce)");

async function api(path, body) {
  const opts = { credentials: "same-origin" };
  if (body !== undefined) Object.assign(opts, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const res = await fetch(path, opts);
  const data = await res.json().catch(() => ({ error: res.statusText }));
  if (!res.ok) throw new Error(data.error || res.statusText);
  return data;
}
const fileUrl = (rel) => "/file/" + rel.split("/").map(encodeURIComponent).join("/");

let toastTimer;
function toast(text) {
  const t = $("#toast");
  t.textContent = text;
  t.dataset.on = "1";
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (t.dataset.on = "0"), 3200);
}

const S = {
  config: null,
  machines: [],
  machine: null,
  pass: null,
  view: "board",
  mode: store.get("mode", "vector"),
  valueMap: false,
  frames: [],          // every FrameView on the page, so a lens change reaches all of them
  cycle: { index: 0, previous: null, view: null },
  play: null,
  events: null,
};

// ── lens ─────────────────────────────────────────────────────────────────────
function track(fv) {
  S.frames.push(fv);
  fv.setLens(S.mode, S.valueMap);
  return fv;
}
function setLens(mode = S.mode, valueMap = S.valueMap) {
  S.mode = mode;
  S.valueMap = valueMap;
  store.set("mode", mode);
  for (const b of document.querySelectorAll("[data-mode]")) b.setAttribute("aria-checked", String(b.dataset.mode === mode));
  $("#valuemap").setAttribute("aria-pressed", String(valueMap));
  S.frames = S.frames.filter((f) => f.el.isConnected);
  for (const f of S.frames) f.setLens(mode, valueMap);
}
const headerBottom = () => (S.machine && S.machine.controls.length > 4 ? S.config.header.twoPage.bottom : S.config.header.stock.bottom);

// ── views ────────────────────────────────────────────────────────────────────
function setView(view) {
  S.view = view;
  store.set("view", view);
  for (const tab of document.querySelectorAll("[role=tab]")) {
    const on = tab.dataset.view === view;
    tab.setAttribute("aria-selected", String(on));
    tab.tabIndex = on ? 0 : -1;
    $("#" + tab.getAttribute("aria-controls")).hidden = !on;
  }
  if (view === "cycle") showCycle(S.cycle.index);
  if (view === "play") startPlay();
  else stopPlay();
  syncUrl();
}

function syncUrl() {
  const q = new URLSearchParams();
  if (S.machine) q.set("m", S.machine.id);
  if (S.pass) q.set("p", S.pass.pass);
  q.set("view", S.view);
  history.replaceState(null, "", "?" + q.toString());
}

// ── machine and pass ─────────────────────────────────────────────────────────
async function loadMachine(id, passName) {
  S.machine = await api(`/api/machine/${encodeURIComponent(id)}`);
  $("#machine").value = id;
  const sel = $("#pass");
  sel.replaceChildren();
  const list = [...S.machine.passes].reverse();
  for (const p of list) {
    const state = p.state === "selected" ? `picked ${p.selected}` : p.state.replaceAll("_", " ");
    sel.append(h("option", { value: p.name, textContent: `${p.name} · ${state}` }));
  }
  if (!list.length) sel.append(h("option", { value: "", textContent: "no passes yet" }));
  sel.disabled = !list.length;
  const open = list.find((p) => !["selected", "rejected"].includes(p.state));
  const chosen = list.find((p) => p.name === passName) || open || list[0];
  setupPlay();
  connectEvents(id);
  await loadPass(chosen ? chosen.name : null);
}

async function loadPass(name) {
  if (name) $("#pass").value = name;
  S.pass = name ? await api(`/api/pass/${encodeURIComponent(S.machine.id)}/${encodeURIComponent(name)}`) : null;
  S.cycle.index = Math.min(S.cycle.index, Math.max(0, (S.pass?.variants.length || 1) - 1));
  renderPassline();
  renderBoard();
  renderRail();
  if (S.view === "cycle") showCycle(S.cycle.index);
  syncUrl();
}

function renderPassline() {
  const line = $("#passline");
  line.replaceChildren();
  const m = S.machine;
  const p = S.pass;
  line.append(h("h1", {}, m.name + " ", h("small", { textContent: p ? p.pass : "" })));
  if (!p) {
    line.append(h("p", { className: "focus" }, h("span", { textContent: "No design passes yet. The knobs in Play still work on any drawn frames." })));
    return;
  }
  const state = h("span", { className: "state", textContent: p.state.replaceAll("_", " ") });
  state.dataset.state = p.state;
  const actions = h("div", { className: "actions" });
  actions.append(h("button", { className: "quiet", textContent: "Note to the agent…", onclick: () => openNote() }));
  if (p.rejectable) actions.append(h("button", { textContent: "None of these…", onclick: () => openDecide("reject") }));
  line.append(state, actions);
  const said = p.selection
    ? `Picked ${p.selection.variant} by ${p.selection.chosenBy}: ${p.selection.reason}`
    : p.rejection ? `Turned down by ${p.rejection.chosenBy}: ${p.rejection.reason}` : p.focus ? `Focus: ${p.focus}` : null;
  if (said) line.append(h("p", { className: "focus" }, h("span", { textContent: said })));
  if (p.notes.length) line.append(h("ul", { className: "problems" }, p.notes.map((n) => h("li", { textContent: n }))));
}

function altFor(v) {
  return `${v.variant}: ${v.subject || v.direction.join(", ") || "variant"}`;
}

function pairText(v, pair) {
  const other = pair.pair.split("–").find((x) => x !== v.variant);
  if ("bodyDiffPct" in pair) return { text: `${other} Δ ${pair.bodyDiffPct}%`, ok: pair.ok };
  return { text: `${other} ${pair.ok ? "distinct" : "too alike"}`, ok: pair.ok };
}

function renderBoard() {
  const board = $("#board");
  board.replaceChildren();
  if (!S.pass) return;
  const top = headerBottom();
  S.pass.variants.forEach((v, i) => {
    const fv = track(new FrameView({ alt: altFor(v), headerBottom: top }));
    if (v.frame) fv.setSource(fileUrl(v.frame));
    else fv.missing("not drawn yet");
    const well = h("div", { className: "frame-well" }, fv.el);
    const head = h("div", { className: "card-head" },
      h("span", { className: "vid", textContent: v.variant }),
      h("span", { className: "dir" }, v.direction.map((d) => h("span", { textContent: d }))));
    const picked = S.pass.selection?.variant === v.variant;
    if (picked) head.append(h("span", { className: "picked-tag", textContent: "picked" }));
    const checks = h("p", { className: "checks" });
    for (const pair of v.pairs) {
      const { text, ok } = pairText(v, pair);
      checks.append(h("span", { textContent: text, className: ok ? "" : "bad" }));
    }
    if (v.frame) lintInto(checks, v.frame);
    const card = h("li", { className: "card" }, well, fv.meter, head);
    card.dataset.picked = picked ? "1" : "0";
    if (v.subject) card.append(h("p", { className: "subject", textContent: v.subject }));
    if (v.controls.length) {
      card.append(h("details", {}, h("summary", { textContent: "What each control does" }),
        h("ul", {}, v.controls.map((c) => h("li", { textContent: c })))));
    }
    if (v.risks.length) {
      card.append(h("details", {}, h("summary", { textContent: "Risks the designer named" }),
        h("ul", {}, v.risks.map((c) => h("li", { textContent: c })))));
    }
    card.append(checks);
    const pick = h("button", { textContent: `Pick ${v.variant}…`, onclick: () => openDecide("pick", v.variant) });
    pick.disabled = !S.pass.pickable;
    if (!S.pass.pickable) pick.title = `This pass is ${S.pass.state.replaceAll("_", " ")}; a pick needs five unique variants submitted.`;
    card.append(h("div", { className: "card-actions" },
      h("button", { className: "quiet", textContent: "Cycle from here", onclick: () => { S.cycle.index = i; setView("cycle"); } }),
      pick));
    board.append(card);
  });
}

async function lintInto(el, frame) {
  try {
    const r = await api(`/api/lint/${encodeURIComponent(S.machine.id)}?path=${encodeURIComponent(frame)}`);
    const span = h("span", { textContent: `lint ${r.errors} err · ${r.warnings} warn` });
    if (r.errors) span.className = "bad";
    span.title = r.byRule.map((g) => `${g.rule} ×${g.count}: ${g.example}`).join("\n") || "clean";
    el.append(span);
  } catch (e) {
    el.append(h("span", { textContent: "lint unavailable", title: e.message }));
  }
}

// ── cycle ────────────────────────────────────────────────────────────────────
function renderRail() {
  const rail = $("#rail");
  rail.replaceChildren();
  if (!S.pass) return;
  S.pass.variants.forEach((v, i) => {
    const b = h("button", { onclick: () => showCycle(i) },
      h("span", { className: "vid", textContent: v.variant + (S.pass.selection?.variant === v.variant ? " · picked" : "") }),
      h("span", { className: "dir", textContent: v.direction.join(" × ") }));
    rail.append(h("li", {}, b));
  });
  const well = $("#cycle-well");
  well.replaceChildren();
  S.cycle.view = track(new FrameView({ headerBottom: headerBottom() }));
  well.append(S.cycle.view.el);
  well.after(S.cycle.view.meter);
  document.querySelectorAll(".stage > .meter").forEach((m) => { if (m !== S.cycle.view.meter) m.remove(); });
}

function showCycle(i, remember = true) {
  if (!S.pass || !S.pass.variants.length) return;
  const n = S.pass.variants.length;
  i = ((i % n) + n) % n;
  if (remember && i !== S.cycle.index) S.cycle.previous = S.cycle.index;
  S.cycle.index = i;
  const v = S.pass.variants[i];
  const fv = S.cycle.view;
  fv.setAlt(altFor(v));
  if (v.frame) fv.setSource(fileUrl(v.frame));
  else fv.missing("not drawn yet");
  document.querySelectorAll("#rail button").forEach((b, k) => b.setAttribute("aria-current", String(k === i)));
  const out = $("#cycle-readout");
  out.replaceChildren(h("p", { className: "dir", textContent: `${v.variant} · ${v.direction.join(" × ")}` }));
  if (v.subject) out.append(h("p", { className: "subject", textContent: v.subject }));
  if (v.controls.length) out.append(h("ul", {}, v.controls.map((c) => h("li", { textContent: c }))));
  const pick = h("button", { textContent: `Pick ${v.variant}…`, onclick: () => openDecide("pick", v.variant) });
  pick.disabled = !S.pass.pickable;
  out.append(h("div", { className: "card-actions" }, pick));
}

// ── play: knobs, MIDI, notes ─────────────────────────────────────────────────
const midi = new Midi();

function setupPlay() {
  const m = S.machine;
  const sets = [];
  if (m.generator) sets.push({ id: "live", label: "live · " + m.generator.split("/").pop() });
  for (const s of m.frameSets) sets.push(s);
  const sel = $("#frameset");
  sel.replaceChildren(...sets.map((s) => h("option", { value: s.id, textContent: s.label })));
  sel.disabled = !sets.length;
  const keep = S.play?.machine === m.id ? S.play.setId : null;
  S.play = {
    machine: m.id,
    sets,
    setId: sets.some((s) => s.id === keep) ? keep : sets[0]?.id ?? null,
    targets: m.controls.map((c) => c.default),
    shown: m.controls.map((c) => c.default),
    last: null,
    held: new Set(),
    env: 0,
    learning: null,
    bindings: store.get("midi:" + m.id, {}),
    view: null,
    raf: 0,
    stamp: 0,
    url: null,
    inflight: false,
    nonce: 0,
    knobs: [],
  };
  if (S.play.setId) sel.value = S.play.setId;
  const well = $("#play-well");
  well.replaceChildren();
  S.play.view = track(new FrameView({ headerBottom: headerBottom() }));
  well.append(S.play.view.el);
  document.querySelectorAll(".play > .meter").forEach((x) => x.remove());
  well.after(S.play.view.meter);
  buildDeck();
  describeSource();
  if (S.view === "play") startPlay();
}

function currentSet() {
  return S.play.sets.find((s) => s.id === S.play.setId) || null;
}

function describeSource() {
  const p = $("#play-source");
  const set = currentSet();
  if (!set) {
    p.innerHTML = "Nothing to play yet: this machine has no drawn frames and no <code>bench.py</code>.";
    return;
  }
  if (set.id === "live") {
    p.innerHTML = "<b>Live.</b> Every knob position is drawn by the machine's own generator, the same code as the stills. Moves settle the way the device eases them.";
  } else {
    const n = Object.keys(set.keyframes.controls).length;
    p.innerHTML = `<b>Drawn frames only.</b> ${n} control${n === 1 ? "" : "s"} drawn at 0, 50 and 100: a knob snaps to the nearest drawn frame and nothing is blended. Add <code>screens/${S.machine.id}/bench.py</code> for every position.`;
  }
}

function buildDeck() {
  const deck = $("#deck");
  deck.replaceChildren();
  S.play.knobs = [];
  const ctrls = S.machine.controls;
  ctrls.forEach((c, i) => {
    if (ctrls.length > 4 && i % 4 === 0) deck.append(h("p", { className: "page", textContent: `page ${i / 4 + 1}` }));
    deck.append(buildKnob(c, i));
  });
  paintKnobs();
}

const ARC_R = 25, CX = 32, CY = 32, SWEEP = 270, START = 135;
const polar = (deg, r = ARC_R) => [CX + r * Math.cos((deg * Math.PI) / 180), CY + r * Math.sin((deg * Math.PI) / 180)];
function arcPath(a0, a1) {
  const [x0, y0] = polar(a0), [x1, y1] = polar(a1);
  return `M ${x0} ${y0} A ${ARC_R} ${ARC_R} 0 ${a1 - a0 > 180 ? 1 : 0} 1 ${x1} ${y1}`;
}

function buildKnob(c, i) {
  const id = `knob-${i}`;
  const NS = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(NS, "svg");
  svg.setAttribute("viewBox", "0 0 64 64");
  svg.setAttribute("aria-hidden", "true");
  svg.innerHTML = `<path class="track" fill="none" stroke-width="3" d="${arcPath(START, START + SWEEP)}"/>
    <path class="arc" fill="none" stroke-width="3" d=""/>
    <line class="default" stroke-width="1.5"/>
    <line class="ghost" stroke-width="1.5"/>
    <circle class="cap" cx="32" cy="32" r="17" stroke-width="1"/>
    <line class="pointer" stroke-width="2" stroke-linecap="round"/>`;
  const dial = h("button", { className: "dial", id });
  dial.setAttribute("role", "slider");
  dial.setAttribute("aria-valuemin", "0");
  dial.setAttribute("aria-valuemax", "100");
  dial.setAttribute("aria-label", c.label);
  dial.append(svg);
  const out = h("output", { htmlFor: id, title: "Knob position, 0 to 100. The header shows the value in its own unit." });
  const learn = h("button", { textContent: "learn", title: "Turn a knob on your controller to bind it here" });
  learn.setAttribute("aria-pressed", "false");
  const bound = h("button", { hidden: true, title: "Unbind" });
  const rel = h("button", { textContent: "rel", hidden: true, title: "Relative encoder: steps instead of positions" });
  rel.setAttribute("aria-pressed", "false");
  const knob = h("div", { className: "knob" }, dial, h("label", { htmlFor: id, textContent: c.label }), out,
    h("div", { className: "bind" }, learn, bound, rel));
  S.play.knobs.push({ knob, dial, svg, out, learn, bound, rel });

  const set = (v) => setControl(i, v);
  let drag = null;
  dial.addEventListener("pointerdown", (e) => {
    dial.setPointerCapture(e.pointerId);
    drag = { y: e.clientY, v: S.play.targets[i] };
  });
  dial.addEventListener("pointermove", (e) => {
    if (!drag) return;
    const scale = e.shiftKey ? 800 : 200;
    set(drag.v + (drag.y - e.clientY) / scale);
  });
  const end = () => (drag = null);
  dial.addEventListener("pointerup", end);
  dial.addEventListener("pointercancel", end);
  dial.addEventListener("dblclick", () => set(c.default));
  dial.addEventListener("wheel", (e) => {
    e.preventDefault();
    set(S.play.targets[i] - Math.sign(e.deltaY) * (e.shiftKey ? 0.002 : 0.01));
  }, { passive: false });
  dial.addEventListener("keydown", (e) => {
    const v = S.play.targets[i];
    const step = { ArrowUp: 0.01, ArrowRight: 0.01, ArrowDown: -0.01, ArrowLeft: -0.01, PageUp: 0.1, PageDown: -0.1 }[e.key];
    if (step !== undefined) { set(v + step * (e.shiftKey ? 10 : 1)); e.preventDefault(); }
    else if (e.key === "Home") { set(0); e.preventDefault(); }
    else if (e.key === "End") { set(1); e.preventDefault(); }
    else if (e.key === "Delete" || e.key === "Backspace") { set(c.default); e.preventDefault(); }
  });
  learn.addEventListener("click", () => {
    S.play.learning = S.play.learning === i ? null : i;
    if (S.play.learning !== null && !midi.access) connectMidi();
    paintKnobs();
  });
  bound.addEventListener("click", () => {
    for (const [k, b] of Object.entries(S.play.bindings)) if (b.index === i) delete S.play.bindings[k];
    saveBindings();
  });
  rel.addEventListener("click", () => {
    for (const b of Object.values(S.play.bindings)) if (b.index === i) b.rel = !b.rel;
    saveBindings();
  });
  return knob;
}

function saveBindings() {
  store.set("midi:" + S.machine.id, S.play.bindings);
  paintKnobs();
}

function setControl(i, v) {
  const p = S.play;
  p.targets[i] = Math.min(1, Math.max(0, v));
  p.last = i;
  if (reduced.matches) p.shown[i] = p.targets[i];
  paintKnobs();
}

function snapFor(i) {
  const set = currentSet();
  if (!set || set.id === "live") return null;
  const drawn = set.keyframes.controls[String(i + 1)];
  if (!drawn) return null;
  const vals = Object.keys(drawn).map(Number);
  const target = S.play.targets[i] * 100;
  return vals.reduce((a, b) => (Math.abs(b - target) < Math.abs(a - target) ? b : a));
}

function paintKnobs() {
  const p = S.play;
  const ctrls = S.machine.controls;
  const live = currentSet()?.id === "live";
  p.knobs.forEach((k, i) => {
    const v = p.targets[i];
    const ang = START + SWEEP * v;
    k.svg.querySelector(".arc").setAttribute("d", v > 0.001 ? arcPath(START, ang) : "");
    const [px, py] = polar(ang, 14), [qx, qy] = polar(ang, 4);
    const ptr = k.svg.querySelector(".pointer");
    ptr.setAttribute("x1", qx); ptr.setAttribute("y1", qy); ptr.setAttribute("x2", px); ptr.setAttribute("y2", py);
    const dAng = START + SWEEP * ctrls[i].default;
    const [d0x, d0y] = polar(dAng, ARC_R + 3), [d1x, d1y] = polar(dAng, ARC_R + 7);
    const def = k.svg.querySelector(".default");
    def.setAttribute("x1", d0x); def.setAttribute("y1", d0y); def.setAttribute("x2", d1x); def.setAttribute("y2", d1y);
    const ghost = k.svg.querySelector(".ghost");
    const snap = !live && p.last === i ? snapFor(i) : null;
    if (snap !== null && Math.abs(snap - v * 100) > 0.5) {
      const gAng = START + SWEEP * (snap / 100);
      const [g0x, g0y] = polar(gAng, 6), [g1x, g1y] = polar(gAng, ARC_R + 6);
      ghost.setAttribute("x1", g0x); ghost.setAttribute("y1", g0y); ghost.setAttribute("x2", g1x); ghost.setAttribute("y2", g1y);
      k.knob.dataset.snapped = "1";
    } else {
      ghost.removeAttribute("x1");
      k.knob.dataset.snapped = "0";
    }
    const pct = Math.round(v * 100);
    k.out.textContent = String(pct);
    k.dial.setAttribute("aria-valuenow", String(pct));
    k.dial.setAttribute("aria-valuetext", snap !== null && snap !== pct ? `${pct}, showing the drawn ${snap}` : String(pct));
    k.knob.dataset.moved = Math.abs(v - ctrls[i].default) > 0.004 ? "1" : "0";
    k.knob.dataset.learning = p.learning === i ? "1" : "0";
    k.learn.setAttribute("aria-pressed", String(p.learning === i));
    const binding = Object.entries(p.bindings).find(([, b]) => b.index === i);
    k.bound.hidden = !binding;
    k.rel.hidden = !binding;
    k.learn.hidden = !!binding && p.learning !== i;
    if (binding) {
      const [key, b] = binding;
      const [ch, cc] = key.split(":");
      k.bound.textContent = `CC${cc}${ch !== "1" ? "·" + ch : ""} ×`;
      k.bound.setAttribute("aria-label", `Unbind CC ${cc} from ${ctrls[i].label}`);
      k.rel.setAttribute("aria-pressed", String(!!b.rel));
    }
  });
  const held = p.held.size;
  $("#note-state").textContent = held ? `${held} note${held === 1 ? "" : "s"} held` : "no notes";
  $("#hold").setAttribute("aria-pressed", String(p.held.has("key") || p.held.has("button")));
}

function holdNote(id, on) {
  const p = S.play;
  if (!p) return;
  if (on) p.held.add(id);
  else p.held.delete(id);
  paintKnobs();
}

// device easing: each move settles within the motion tokens' window; notes rise and fall like the stock envelope
function startPlay() {
  if (!S.play || S.play.raf) return;
  S.play.stamp = performance.now();
  const tick = (now) => {
    const p = S.play;
    if (!p) return;
    const dt = Math.min(0.1, (now - p.stamp) / 1000);
    p.stamp = now;
    const settle = S.config.motion.easeSecondsMax;
    const k = reduced.matches ? 1 : 1 - Math.exp((-dt * 4) / settle);
    p.shown = p.shown.map((s, i) => (Math.abs(p.targets[i] - s) < 0.002 ? p.targets[i] : s + (p.targets[i] - s) * k));
    const want = p.held.size ? 1 : 0;
    const rate = reduced.matches ? 1 : dt / (want ? S.config.motion.easeSecondsMin : settle);
    p.env = want > p.env ? Math.min(1, p.env + rate) : Math.max(0, p.env - rate);
    showPlayFrame();
    p.raf = requestAnimationFrame(tick);
  };
  S.play.raf = requestAnimationFrame(tick);
}
function stopPlay() {
  if (S.play?.raf) cancelAnimationFrame(S.play.raf);
  if (S.play) S.play.raf = 0;
}

function showPlayFrame() {
  const p = S.play;
  const set = currentSet();
  if (!set) {
    if (p.url !== "none") { p.view.missing("nothing to play"); p.url = "none"; }
    return;
  }
  let url;
  if (set.id === "live") {
    const q = (x) => (Math.round(x * 200) / 200).toFixed(3);
    url = `/gen/${encodeURIComponent(S.machine.id)}.svg?v=${p.shown.map(q).join(",")}&n=${q(p.env)}&r=${p.nonce}`;
  } else {
    const kf = set.keyframes;
    let rel = kf.rest;
    if (p.held.size && kf.playing) rel = kf.playing;
    else if (p.last !== null) {
      const off = Math.abs(p.targets[p.last] - S.machine.controls[p.last].default) > 0.004;
      const snap = snapFor(p.last);
      if (off && snap !== null) rel = kf.controls[String(p.last + 1)][String(snap)];
    }
    url = fileUrl(rel);
  }
  if (url === p.url || p.inflight) return;
  p.inflight = true;
  p.url = url;
  p.view.setSource(url).finally(() => { p.inflight = false; });
}

// ── MIDI ─────────────────────────────────────────────────────────────────────
let hinted = false;
async function connectMidi() {
  const btn = $("#midi");
  try {
    const names = await midi.connect();
    btn.dataset.state = "on";
    $("#midi-status").textContent = names.length ? `MIDI · ${names.length} in` : "MIDI · no inputs";
    toast(names.length ? `Listening to ${names.join(", ")}` : "MIDI is on; plug in a controller and it'll appear.");
  } catch (e) {
    btn.dataset.state = "off";
    $("#midi-status").textContent = "MIDI off";
    toast(e.message || "MIDI permission was refused");
  }
}
midi.addEventListener("ports", (e) => {
  $("#midi-status").textContent = e.detail.names.length ? `MIDI · ${e.detail.names.length} in` : "MIDI · no inputs";
});
let blink;
function activity() {
  const b = $("#midi");
  b.dataset.activity = "1";
  clearTimeout(blink);
  blink = setTimeout(() => (b.dataset.activity = "0"), 90);
}
midi.addEventListener("cc", ({ detail: { channel, cc, value } }) => {
  activity();
  const p = S.play;
  if (!p || !S.machine.controls.length) return;
  const key = `${channel}:${cc}`;
  if (p.learning !== null) {
    for (const [k, b] of Object.entries(p.bindings)) if (b.index === p.learning || k === key) delete p.bindings[k];
    p.bindings[key] = { index: p.learning, rel: false };
    toast(`CC ${cc} → ${S.machine.controls[p.learning].label}`);
    p.learning = null;
    saveBindings();
  } else if (!p.bindings[key]) {
    const taken = new Set(Object.values(p.bindings).map((b) => b.index));
    const free = S.machine.controls.findIndex((_, i) => !taken.has(i));
    if (free < 0) return;
    p.bindings[key] = { index: free, rel: false };
    toast(`CC ${cc} → ${S.machine.controls[free].label} (press learn to change)`);
    saveBindings();
  }
  const b = p.bindings[key];
  setControl(b.index, b.rel ? p.targets[b.index] + relativeStep(value) / 127 : value / 127);
  if (S.view !== "play" && !hinted) {
    hinted = true;
    toast("Knobs move the screen in Play (K)");
  }
});
midi.addEventListener("noteon", ({ detail }) => { activity(); holdNote(`n${detail.channel}:${detail.note}`, true); });
midi.addEventListener("noteoff", ({ detail }) => { activity(); holdNote(`n${detail.channel}:${detail.note}`, false); });
midi.addEventListener("panic", () => { if (S.play) { S.play.held.clear(); paintKnobs(); } });

// ── decide: pick or reject, and notes to the agent ───────────────────────────
let deciding = null;
function openDecide(kind, variant) {
  if (!S.pass) return;
  deciding = { kind, variant };
  const v = S.pass.variants.find((x) => x.variant === variant);
  $("#decide-title").textContent = kind === "pick" ? `Pick ${variant}` : `None of these five`;
  $("#decide-what").textContent = kind === "pick"
    ? `${S.machine.name} · ${S.pass.pass} · ${v?.direction.join(" × ") || ""}`
    : `Closes ${S.pass.pass} without a pick. The next pass starts from your reason.`;
  $("#decide-reason-label").textContent = kind === "pick" ? "Why this one" : "Why none of them";
  $("#decide-name").value = store.get("name", "");
  $("#decide-reason").value = "";
  $("#decide-error").textContent = "";
  $("#decide").showModal();
  ($("#decide-name").value ? $("#decide-reason") : $("#decide-name")).focus();
}
$("#decide-form").addEventListener("submit", async (e) => {
  if (e.submitter?.value !== "ok") return;
  e.preventDefault();
  const name = $("#decide-name").value.trim();
  const reason = $("#decide-reason").value.trim();
  if (!name || !reason) {
    $("#decide-error").textContent = "Both your name and a reason are needed; the pick is recorded as yours.";
    return;
  }
  store.set("name", name);
  const body = { machine: S.machine.id, pass: S.pass.pass, reason, chosenBy: name };
  try {
    if (deciding.kind === "pick") await api("/api/pick", { ...body, variant: deciding.variant });
    else await api("/api/reject", body);
    $("#decide").close();
    toast(deciding.kind === "pick" ? `Recorded: ${deciding.variant}. The agent sees it at its next poll.` : "Recorded: none of these.");
    await loadMachine(S.machine.id, S.pass.pass);
  } catch (err) {
    $("#decide-error").textContent = err.message;
  }
});

function openNote() {
  const verbs = $("#verbs");
  verbs.replaceChildren(...["none", ...S.config.verbs].map((v, i) => {
    const input = h("input", { type: "radio", name: "verb", value: v === "none" ? "" : v, checked: i === 0 });
    return h("label", {}, input, v);
  }));
  $("#note-text").value = "";
  $("#note-error").textContent = "";
  $("#note").showModal();
  $("#note-text").focus();
}
$("#note-form").addEventListener("submit", async (e) => {
  if (e.submitter?.value !== "ok") return;
  e.preventDefault();
  const text = $("#note-text").value.trim();
  if (!text) { $("#note-error").textContent = "Write the note first."; return; }
  const verb = new FormData($("#note-form")).get("verb") || null;
  try {
    await api("/api/message", { machine: S.machine.id, pass: S.pass?.pass, variant: S.view === "cycle" ? S.pass?.variants[S.cycle.index]?.variant : null, verb, text, chosenBy: store.get("name", "") || null });
    $("#note").close();
    toast("Sent. The agent reads it at its next poll.");
  } catch (err) {
    $("#note-error").textContent = err.message;
  }
});

// ── live updates ─────────────────────────────────────────────────────────────
let reloadTimer;
function connectEvents(machineId) {
  S.events?.close();
  S.events = new EventSource(`/events?machine=${encodeURIComponent(machineId)}`);
  S.events.onmessage = (e) => {
    let ev;
    try { ev = JSON.parse(e.data); } catch { return; }
    if (ev.type === "generator" && S.play) {
      S.play.nonce++;
      toast("Generator changed; redrawing.");
    } else if (["changed", "pick", "reject"].includes(ev.type)) {
      clearTimeout(reloadTimer);
      reloadTimer = setTimeout(() => loadMachine(S.machine.id, S.pass?.pass).catch((err) => toast(err.message)), 300);
    }
  };
}

// ── keys ─────────────────────────────────────────────────────────────────────
function typing(e) {
  const t = e.target;
  return t.closest("dialog[open]") || ["INPUT", "TEXTAREA", "SELECT"].includes(t.tagName) || (t.getAttribute?.("role") === "slider" && e.key.startsWith("Arrow"));
}
document.addEventListener("keydown", (e) => {
  if (e.metaKey || e.ctrlKey || e.altKey || typing(e)) return;
  const k = e.key.toLowerCase();
  if (k === "b") setView("board");
  else if (k === "c") setView("cycle");
  else if (k === "k") setView("play");
  else if (k === "d") setLens(S.mode === "device" ? "vector" : "device");
  else if (k === "a") setLens(S.mode === "arm" ? "vector" : "arm");
  else if (k === "v") setLens(S.mode, !S.valueMap);
  else if (S.view === "cycle" && /^[1-9]$/.test(k)) showCycle(Number(k) - 1);
  else if (S.view === "cycle" && e.key === "ArrowRight") showCycle(S.cycle.index + 1);
  else if (S.view === "cycle" && e.key === "ArrowLeft") showCycle(S.cycle.index - 1);
  else if (S.view === "cycle" && e.key === " " && !e.repeat && S.cycle.previous !== null) {
    S.cycle.flick = S.cycle.index;
    showCycle(S.cycle.previous, false);
  } else if (S.view === "play" && e.key === " " && !e.repeat) holdNote("key", true);
  else if (S.view === "play" && k === "0") S.machine.controls.forEach((c, i) => setControl(i, c.default));
  else return;
  e.preventDefault();
});
document.addEventListener("keyup", (e) => {
  if (e.key !== " ") return;
  if (S.view === "cycle" && S.cycle.flick !== undefined) {
    showCycle(S.cycle.flick, false);
    S.cycle.flick = undefined;
  } else if (S.view === "play") holdNote("key", false);
});
window.addEventListener("blur", () => { if (S.play) { S.play.held.delete("key"); S.play.held.delete("button"); paintKnobs(); } });

// ── boot ─────────────────────────────────────────────────────────────────────
async function boot() {
  const q = new URLSearchParams(location.search);
  S.config = await api("/api/config");
  $("#renderer").textContent = `Renderer for checks: ${S.config.renderer}. ${S.config.colour.allowed ? "Colour allowed by this harness, never red." : "Grey only."}`;
  S.machines = await api("/api/machines");
  const sel = $("#machine");
  sel.replaceChildren(...S.machines.map((m) => h("option", { value: m.id, textContent: `${m.id}${m.passes ? ` · ${m.passes} pass${m.passes === 1 ? "" : "es"}` : ""}${m.live ? " · live" : ""}` })));
  for (const tab of document.querySelectorAll("[role=tab]")) tab.addEventListener("click", () => setView(tab.dataset.view));
  $(".views").addEventListener("keydown", (e) => {
    if (!["ArrowLeft", "ArrowRight"].includes(e.key)) return;
    const tabs = [...document.querySelectorAll("[role=tab]")];
    const i = tabs.findIndex((t) => t.dataset.view === S.view);
    const next = tabs[(i + (e.key === "ArrowRight" ? 1 : tabs.length - 1)) % tabs.length];
    setView(next.dataset.view);
    next.focus();
  });
  for (const b of document.querySelectorAll("[data-mode]")) b.addEventListener("click", () => setLens(b.dataset.mode));
  $("#valuemap").addEventListener("click", () => setLens(S.mode, !S.valueMap));
  $("#midi").addEventListener("click", connectMidi);
  sel.addEventListener("change", () => loadMachine(sel.value).catch((e) => toast(e.message)));
  $("#pass").addEventListener("change", (e) => loadPass(e.target.value).catch((err) => toast(err.message)));
  $("#frameset").addEventListener("change", (e) => {
    S.play.setId = e.target.value;
    S.play.url = null;
    describeSource();
    paintKnobs();
  });
  const hold = $("#hold");
  hold.addEventListener("pointerdown", (e) => { hold.setPointerCapture(e.pointerId); holdNote("button", true); });
  for (const t of ["pointerup", "pointercancel"]) hold.addEventListener(t, () => holdNote("button", false));
  hold.addEventListener("keydown", (e) => { if ((e.key === "Enter" || e.key === " ") && !e.repeat) { e.preventDefault(); e.stopPropagation(); holdNote("button", true); } });
  hold.addEventListener("keyup", (e) => { if (e.key === "Enter" || e.key === " ") { e.stopPropagation(); holdNote("button", false); } });
  $("#defaults").addEventListener("click", () => S.machine.controls.forEach((c, i) => setControl(i, c.default)));
  setLens();

  const wanted = q.get("m");
  const first = S.machines.find((m) => m.id === wanted) || S.machines.find((m) => m.passes) || S.machines[0];
  if (!first) {
    $("#passline").textContent = "No screens yet. Start one with screen_init.";
    return;
  }
  await loadMachine(first.id, q.get("p"));
  setView(["board", "cycle", "play"].includes(q.get("view")) ? q.get("view") : store.get("view", "board"));
}

boot().catch((e) => {
  $("#passline").textContent = `The bench couldn't start: ${e.message}`;
});
