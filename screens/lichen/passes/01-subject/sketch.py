#!/usr/bin/env python3
"""Subject-pass sketches for lichen: five rest frames from one colony model.

    python3 screens/lichen/passes/01-subject/sketch.py

Writes v1..v5/rest.svg (480 x 220, stock header kept) and renders rest.png
beside each with rsvg-convert when it exists. All five draw the same colony
(model below) at the same tick, so they differ in pattern and drawing
language, not in what the machine is doing.

The model (the DSP sketch the brief describes):
  lattice   7 scale degrees (columns, wrapping round the octave) x 5 registers
            (rows). A cell's neighbours: one and two degrees either side (a step
            and a third) and the same degree one register up and down.
  grow      each tick, each living cell spreads into one free neighbour with
            chance grow x 0.6; at most 3 births a tick (they are the notes).
  decay     a living cell of age a dies with chance decay x a / 6; dead crust
            can't be regrown for 4 ticks.
  seed      spores per bar (16 ticks): each lands on a random empty cell.
  scale     which semitones the seven (or five) degrees sit on.

Rest settings come from definition.json defaults: grow 35 %, decay 20 %,
seed 1, scale maj.
"""
from __future__ import annotations

import math
import random
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 480, 220

SCALES = {"maj": [0, 2, 4, 5, 7, 9, 11], "min": [0, 2, 3, 5, 7, 8, 10], "dor": [0, 2, 3, 5, 7, 9, 10],
          "phr": [0, 1, 3, 5, 7, 8, 10], "lyd": [0, 2, 4, 6, 7, 9, 11], "mix": [0, 2, 4, 5, 7, 9, 10],
          "pent": [0, 2, 4, 7, 9], "pmin": [0, 3, 5, 7, 10]}
DEF = {"grow": 0.35, "decay": 0.2, "seed": 1, "scale": "maj"}
HEAD_L = ["grow", "decay", "seed", "scale"]
HEAD_V = ["35", "20", "1", "maj"]
R = 5            # registers
SNAP = 25        # tick shown
RNG_SEED = 7

G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")


# --- colony model -----------------------------------------------------------
def nbrs(c, r, n):
    out = [((c + d) % n, r) for d in (-2, -1, 1, 2)]
    out += [(c, r + d) for d in (-1, 1) if 0 <= r + d < R]
    return out


def run(grow=DEF["grow"], decay=DEF["decay"], seed=DEF["seed"], n=7, ticks=SNAP + 1, rs=RNG_SEED):
    rng = random.Random(rs)
    st = {(c, r): 0 for c in range(n) for r in range(R)}
    st[(2, 2)] = 1
    hist, births = [], []
    for t in range(ticks):
        new = dict(st)
        born = []
        for k, a in sorted(st.items()):
            if a > 0:
                free = [q for q in nbrs(*k, n) if st[q] == 0 and new[q] == 0]
                if free and len(born) < 3 and rng.random() < grow * 0.6:
                    q = rng.choice(free)
                    new[q] = 1
                    born.append((q, k))
                new[k] = -4 if rng.random() < min(1, decay * a / 6) else a + 1
            elif a < 0:
                new[k] = a + 1
        if seed and t % 16 == 15:
            empty = [k for k, a in new.items() if a == 0]
            k = rng.choice(empty)
            new[k] = 1
            born.append((k, None))
        st = new
        hist.append(dict(st))
        births.append(born)
    return hist, births


HIST, BIRTHS = run()
STATE = HIST[SNAP]
BORN = {q for q, _ in BIRTHS[SNAP]}
LINKS = [(q, p) for q, p in BIRTHS[SNAP] if p is not None]
LIVE = {k for k, a in STATE.items() if a > 0}
DEAD = {k for k, a in STATE.items() if a < 0}
SC = SCALES[DEF["scale"]]
N = len(SC)
# a spore waiting for the next bar: an empty cell far from the colony
SPORES = [k for k, a in STATE.items() if a == 0][-1:]


def pitch(c, r):
    return SC[c] + 12 * r


# --- svg helpers ------------------------------------------------------------
def f(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def clean(pts, closed=True, gap=0.3):
    out = []
    for p in pts:
        if not out or math.dist(p, out[-1]) >= gap:
            out.append(p)
    if closed and len(out) > 2 and math.dist(out[0], out[-1]) < gap:
        out.pop()
    return out


class Svg:
    def __init__(self):
        self.o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
                  '  <g id="preview_canvas">',
                  f'    <rect x="0" y="0" width="{W}" height="{H}" fill="#000000" stroke="none"/>',
                  '  </g>']
        steps = [G0, G1, G2, G3, G4, G5, G6, G7]
        self.o.append('  <g id="preview_header">')
        for i, c in enumerate(steps):
            self.o.append(f'    <rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
        for i, (lab, val) in enumerate(zip(HEAD_L, HEAD_V)):
            col = "#CBCBCB" if i < 2 else "#000000"
            self.o.append(f'    <text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{col}" stroke="none" '
                          f'font-family="UniversNextPro-Light" font-size="10px">{lab}</text>')
            self.o.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{col}" stroke="none" '
                          f'font-family="UniversNextPro-Light" font-size="20px">{val}</text>')
        self.o.append('  </g>')

    def poly(self, pts, fill="none", stroke="none", sw=None):
        pts = clean(pts)
        if len(pts) < 3:
            return
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
        s = f' stroke-width="{sw}"' if stroke != "none" else ""
        self.o.append(f'  <path d="{d}" fill="{fill}" stroke="{stroke}"{s}/>')

    def ribbon(self, pts, w, col):
        """An open line drawn as a thin closed ribbon (constraints: no traced strokes)."""
        pts = clean(pts, closed=False, gap=0.6)
        if len(pts) < 2:
            return
        if len(pts) > 30:  # one subpath holds 64 points: split long lines into touching ribbons
            for i in range(0, len(pts) - 1, 29):
                self.ribbon(pts[i:i + 30], w, col)
            return
        h = w / 2
        left, right = [], []
        for i, p in enumerate(pts):
            a = pts[max(0, i - 1)]
            b = pts[min(len(pts) - 1, i + 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(dx, dy) or 1
            nx, ny = -dy / ln, dx / ln
            left.append((p[0] + nx * h, p[1] + ny * h))
            right.append((p[0] - nx * h, p[1] - ny * h))
        self.poly(left + right[::-1], fill=col)

    def seg(self, a, b, w, col):
        self.ribbon([a, b], w, col)

    def dashed(self, pts, w, col, dash=8, gap=4):
        """A dashed line as separate ribbons (no stroke-dasharray on the device)."""
        acc, run, on = 0.0, [pts[0]], True
        for a, b in zip(pts, pts[1:]):
            ln = math.dist(a, b)
            t = 0.0
            while t < ln:
                lim = (dash if on else gap) - acc
                step = min(lim, ln - t)
                t += step
                acc += step
                p = (a[0] + (b[0] - a[0]) * t / ln, a[1] + (b[1] - a[1]) * t / ln)
                if on:
                    run.append(p)
                if acc >= (dash if on else gap) - 1e-9:
                    if on and len(run) > 1:
                        self.ribbon(run, w, col)
                    on, acc, run = not on, 0.0, [p]
        if on and len(run) > 1:
            self.ribbon(run, w, col)

    def circle(self, cx, cy, r, fill="none", stroke="none", sw=None):
        s = f' stroke-width="{sw}"' if stroke != "none" else ""
        self.o.append(f'  <circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}" stroke="{stroke}"{s}/>')

    def text(self, x, y, s, col=G4, size=10):
        self.o.append(f'  <text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{col}" stroke="none" '
                      f'font-family="UniversNextPro-Light" font-size="{size}px">{s}</text>')

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(self.o + ["</svg>", ""]), encoding="utf-8")
        if shutil.which("rsvg-convert"):
            subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H), "-b", "black",
                            str(path), "-o", str(path.with_suffix(".png"))], check=True)


# --- contours (marching squares) --------------------------------------------
def contours(fn, x0, y0, x1, y1, step=3.0, level=0.5):
    nx, ny = int((x1 - x0) / step) + 1, int((y1 - y0) / step) + 1
    v = [[fn(x0 + i * step, y0 + j * step) for i in range(nx)] for j in range(ny)]

    def interp(p, q, a, b):
        t = (level - a) / (b - a) if b != a else 0.5
        return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)

    segs = []
    for j in range(ny - 1):
        for i in range(nx - 1):
            corners = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            vals = [v[b][a] for a, b in corners]
            inside = [x > level for x in vals]
            edges = []
            for e in range(4):
                a, b = e, (e + 1) % 4
                if inside[a] != inside[b]:
                    edges.append(e)
            if len(edges) == 2:
                segs.append(((i, j, edges[0]), (i, j, edges[1])))
            elif len(edges) == 4:
                segs.append(((i, j, 0), (i, j, 1)))
                segs.append(((i, j, 2), (i, j, 3)))

    def key(i, j, e):  # shared edge id
        return {0: ("h", i, j), 1: ("v", i + 1, j), 2: ("h", i, j + 1), 3: ("v", i, j)}[e]

    def pos(k):
        kind, i, j = k
        p = (x0 + i * step, y0 + j * step)
        if kind == "h":
            q = (x0 + (i + 1) * step, y0 + j * step)
            return interp(p, q, v[j][i], v[j][i + 1])
        q = (x0 + i * step, y0 + (j + 1) * step)
        return interp(p, q, v[j][i], v[j + 1][i])

    adj = {}
    for a, b in segs:
        ka, kb = key(*a), key(*b)
        adj.setdefault(ka, []).append(kb)
        adj.setdefault(kb, []).append(ka)
    seen, loops = set(), []
    for start in adj:
        if start in seen:
            continue
        loop, prev, cur = [start], None, start
        seen.add(start)
        while True:
            nxt = [k for k in adj[cur] if k != prev and k not in seen]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            seen.add(cur)
            loop.append(cur)
        if len(loop) > 6:
            loops.append([pos(k) for k in loop])
    return loops


def resample(pts, n):
    ring = pts + [pts[0]]
    lens = [math.dist(a, b) for a, b in zip(ring, ring[1:])]
    total = sum(lens)
    out, acc, i = [], 0.0, 0
    for k in range(n):
        target = total * k / n
        while acc + lens[i] < target:
            acc += lens[i]
            i += 1
        t = (target - acc) / lens[i] if lens[i] else 0
        a, b = ring[i], ring[i + 1]
        out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def perimeter(pts):
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:] + pts[:1]))


def smooth_loop(pts, maxn=60, px=5.0):
    n = max(12, min(maxn, int(perimeter(pts) / px)))
    return resample(pts, n)


# =============================================================================
# v1 · P12 Orrery · engineering schematic
# =============================================================================
def v1():
    s = Svg()
    cx, cy, k, tilt = 240.0, 122.0, 42.0, 0.40
    radii = [1.25 + 0.8 * r for r in range(R)]

    def proj(rad, th):
        return (cx + rad * k * math.sin(th), cy + rad * k * tilt * math.cos(th))

    def ang(c):
        return 2 * math.pi * SC[c] / 12

    sun = 0.72 * k
    # centre lines (chain lines): horizontal and vertical through the sun
    s.dashed([(28, cy), (452, cy)], 1, G2, dash=14, gap=4)
    s.dashed([(cx, 30), (cx, 210)], 1, G2, dash=14, gap=4)
    # seed track (outer, dashed) back half then everything else
    seed_r = radii[-1] + 0.55
    arc = [proj(seed_r, math.pi / 2 + math.pi * i / 60) for i in range(61)]
    s.dashed(arc, 1, G3, dash=5, gap=5)
    # orbit back runs
    for rad in radii:
        s.ribbon([proj(rad, math.pi / 2 + math.pi * i / 72) for i in range(73)], 1.2, G2)

    def planet(c, r, front):
        th = ang(c)
        if (math.cos(th) >= 0) != front:
            return
        x, y = proj(radii[r], th)
        depth = 1 + 0.18 * math.cos(th) * radii[r] / radii[-1]
        key = (c, r)
        if key in BORN:
            s.circle(x, y, 5.2 * depth, fill=G7, stroke=G7, sw=1.5)
        elif key in LIVE:
            s.circle(x, y, 4.2 * depth, fill=G2, stroke=G6, sw=1.5)
        elif key in DEAD:
            s.circle(x, y, 3.2 * depth, fill=G0, stroke=G3, sw=1.2)
        else:
            dx, dy = math.sin(th), tilt * math.cos(th)
            ln = math.hypot(dx, dy)
            s.seg((x - dx / ln * 3, y - dy / ln * 3), (x + dx / ln * 3, y + dy / ln * 3), 1.2, G3)

    for r in range(R):
        for c in range(N):
            planet(c, r, front=False)
    # the sun: root of the lattice, a sphere, with its equator
    s.circle(cx, cy, sun, fill=G0, stroke=G4, sw=1.5)
    s.ribbon([(cx + sun * math.sin(math.pi / 2 + math.pi * i / 40), cy + sun * 0.3 * math.cos(math.pi / 2 + math.pi * i / 40)) for i in range(41)][::-1], 1, G2)
    s.ribbon([(cx + sun * math.sin(-math.pi / 2 + math.pi * i / 40), cy + sun * 0.3 * math.cos(-math.pi / 2 + math.pi * i / 40)) for i in range(41)], 1.2, G3)
    # orbit front runs
    for rad in radii:
        s.ribbon([proj(rad, -math.pi / 2 + math.pi * i / 72) for i in range(73)], 1.2, G3)
    s.dashed([proj(seed_r, -math.pi / 2 + math.pi * i / 60) for i in range(61)], 1, G3, dash=5, gap=5)
    # growth links: along the orbit for a step/third, radial for a register
    for (qc, qr), (pc, pr) in LINKS:
        if qr == pr:
            a0, a1 = ang(pc), ang(qc)
            if abs(a1 - a0) > math.pi:
                a1 += 2 * math.pi if a1 < a0 else -2 * math.pi
            s.ribbon([proj(radii[qr], a0 + (a1 - a0) * i / 16) for i in range(17)], 1.5, G5)
        else:
            th = ang(qc)
            s.ribbon([proj(radii[pr] + (radii[qr] - radii[pr]) * i / 6, th) for i in range(7)], 1.5, G5)
    for r in range(R):
        for c in range(N):
            planet(c, r, front=True)
    # spores waiting on the seed track
    for (c, r) in SPORES:
        x, y = proj(seed_r, ang(c) + 0.35)
        s.circle(x, y, 3.5, fill=G0, stroke=G5, sw=1.5)
    # schematic labels: degrees round the far side, registers on the axis
    for c in range(N):
        th = ang(c)
        if math.cos(th) < -0.05:
            x, y = proj(seed_r + 0.35, th)
            s.text(x - 3, y + 3, str(c + 1), G4)
    for r, rad in enumerate(radii):
        x, _ = proj(rad, math.pi / 2)
        if r % 2 == 0:
            s.seg((x, cy - 3), (x, cy - 9), 1, G3)
            s.text(x - 3, cy - 12, str(r + 1), G4)
    s.text(452, cy + 4, "oct", G4)
    s.save(HERE / "v1" / "rest.svg")


# =============================================================================
# v2 · P13 Capture · oscilloscope trace
# =============================================================================
def v2():
    s = Svg()
    gx0, gx1, gy0, gy1 = 48.0, 432.0, 32.0, 200.0
    unit = (gx1 - gx0) / 12

    def at(c, r):
        return (gx0 + (SC[c] + 0.5) * unit, gy1 - 18 - r * 33)

    # graticule: frame, register lines, degree lines, centre axis ticks
    s.poly([(gx0, gy0), (gx1, gy0), (gx1, gy1), (gx0, gy1)], stroke=G2, sw=1)
    for r in range(R):
        y = at(0, r)[1]
        s.seg((gx0, y), (gx1, y), 1, G1)
    for c in range(N):
        x = at(c, 0)[0]
        s.seg((x, gy0), (x, gy1), 1, G1)
    midy = (gy0 + gy1) / 2
    for i in range(1, 60):
        x = gx0 + i * (gx1 - gx0) / 60
        if i % 5:
            s.seg((x, midy - 2), (x, midy + 2), 1, G2)
    # every lattice point as a faint graticule dot
    for r in range(R):
        for c in range(N):
            if (c, r) not in LIVE and (c, r) not in DEAD:
                x, y = at(c, r)
                s.circle(x, y, 1.6, fill=G2, stroke="none")

    def field(cells, sx, sy):
        pts = [at(*k) for k in cells]

        def fn(x, y):
            return sum(math.exp(-(((x - px) / sx) ** 2 + ((y - py) / sy) ** 2)) for px, py in pts)
        return fn

    # the capture front: everything the colony holds, inflated by grow's reach
    front = contours(field(LIVE | DEAD, 22, 18), gx0 - 30, gy0 - 20, gx1 + 30, gy1 + 20, 3, 0.5)
    for lp in front:
        s.poly(smooth_loop(lp, 60, 5), fill="none", stroke=G6, sw=2)
    # the dead centre: afterglow trace round the crust that can't regrow
    dead = contours(field(DEAD, 14, 11), gx0 - 30, gy0 - 20, gx1 + 30, gy1 + 20, 3, 0.55)
    for lp in dead:
        s.poly(smooth_loop(lp, 40, 5), fill="none", stroke=G3, sw=1.5)
    for k in LIVE - BORN:
        x, y = at(*k)
        s.circle(x, y, 2.6, fill=G4, stroke="none")
    for k in BORN:
        x, y = at(*k)
        s.circle(x, y, 4, fill=G7, stroke="none")
    for k in SPORES:
        x, y = at(*k)
        s.circle(x, y, 3.5, fill=G0, stroke=G5, sw=1.5)
    # scope labels: degrees under the screen, channel note at the corner
    for c in range(N):
        x = at(c, 0)[0]
        s.text(x - 3, 213, str(c + 1), G4)
    s.text(gx1 + 6, gy0 + 9, "oct", G4)
    for r in range(R):
        s.text(gx1 + 6, at(0, r)[1] + 4, str(r + 1), G4)
    s.save(HERE / "v2" / "rest.svg")


# =============================================================================
# v3 · P14 Loom · typeset diagram
# =============================================================================
def v3():
    s = Svg()
    rows = 4
    x0, base = 46.0, 186.0
    thread = []      # (c, r, x) in pitch order
    for r in range(R):
        for c in range(N):
            thread.append((c, r))

    def tx(c, r):
        return x0 + (pitch(c, r) - r * 0.0) * 6.55

    def row_geom(kk):  # kk 0 = this tick (front), 3 = oldest (back)
        sk = 1 - 0.1 * kk
        return base - kk * 30, 10 * kk, sk

    # warp threads: hairlines from the back row to the front
    for (c, r) in thread:
        yb, ob, sb = row_geom(rows - 1)
        yf, of, sf = row_geom(0)
        xb = 240 + (tx(c, r) - 240) * sb + ob
        xf = tx(c, r) + of
        s.seg((xb, yb - 4), (xf, yf + 4), 1, G1)
    # rows, back to front
    for kk in range(rows - 1, -1, -1):
        st = HIST[SNAP - kk]
        born = {q for q, _ in BIRTHS[SNAP - kk]}
        y, off, sk = row_geom(kk)
        for (c, r) in thread:
            a = st[(c, r)]
            if a <= 0:
                continue
            x = 240 + (tx(c, r) - 240) * sk + off
            w, dp = 5.4 * sk, 5 * sk
            if kk == 0:
                hgt = 9
                front = [(x - w / 2, y), (x + w / 2, y), (x + w / 2, y - hgt), (x - w / 2, y - hgt)]
                top = [(x - w / 2, y - hgt), (x + w / 2, y - hgt), (x + w / 2 + 3, y - hgt - dp), (x - w / 2 + 3, y - hgt - dp)]
                b = (c, r) in born
                s.poly(front, fill=G1, stroke=G5, sw=1)
                s.poly(top, fill=G7 if b else G3, stroke=G7 if b else G4, sw=1)
            else:
                top = [(x - w / 2, y), (x + w / 2, y), (x + w / 2 + 3, y - dp), (x - w / 2 + 3, y - dp)]
                shade = {1: G3, 2: G2, 3: G1}[kk]
                edge = {1: G4, 2: G3, 3: G2}[kk]
                if (c, r) in born:
                    edge = G5
                s.poly(top, fill=shade, stroke=edge, sw=1)
    # spore pin at the front edge, where the next bar's spore lands
    for (c, r) in SPORES:
        x = tx(c, r)
        s.seg((x, base + 3), (x, base + 13), 1.2, G5)
        s.circle(x, base + 16, 2.6, fill=G0, stroke=G5, sw=1.2)
    # typeset furniture: row labels, octave rules, figure caption
    for kk, lab in enumerate(["t", "t-1", "t-2", "t-3"]):
        y, _, _ = row_geom(kk)
        s.text(8, y - 2, lab, G4 if kk else G5)
    for r in range(R):
        xa, xb = tx(0, r) - 3, tx(N - 1, r) + 3
        s.seg((xa, 206), (xb, 206), 1, G3)
        s.seg((xa, 203), (xa, 206.5), 1, G3)
        s.text((xa + xb) / 2 - 3, 216, str(r + 1), G4)
    s.text(8, 36, "fig. 1  growth by tick", G4)
    s.save(HERE / "v3" / "rest.svg")


# =============================================================================
# v4 · P5 Field and figure · orthographic elevation
# =============================================================================
def v4():
    s = Svg()
    wx0, unit, ch = 60.0, 30.0, 28.0
    ground = 190.0
    steps = [(SC[(i + 1) % N] - SC[i]) % 12 or 12 for i in range(N)]

    def stone(c, r):
        off = 0.5 * unit if r % 2 else 0.0
        xa = wx0 + SC[c] * unit + off
        xb = xa + steps[c] * unit
        yb = ground - r * ch
        return xa, yb - ch, xb, yb

    def centre(c, r):
        xa, ya, xb, yb = stone(c, r)
        return ((xa + xb) / 2, (ya + yb) / 2)

    wx1 = wx0 + 12 * unit
    # the wall (field): mortar joints at a low grey, coping and ground lines
    for r in range(R):
        yb = ground - r * ch
        s.seg((wx0, yb - ch), (wx1, yb - ch), 1, G1)
        for c in range(N):
            xa, ya, xb, _ = stone(c, r)
            if wx0 < xa < wx1:
                s.seg((xa, ya + 1), (xa, yb - 1), 1, G1)
    s.seg((wx0, 50), (wx0, ground), 1, G2)
    s.seg((wx1, 50), (wx1, ground), 1, G2)
    s.seg((wx0 - 20, ground + 1), (wx1 + 20, ground + 1), 2, G4)

    # the figure: the thallus, a lobed patch over the stones it lives on
    live = list(LIVE)

    def fn(x, y):
        v = 0.0
        for k in live:
            px, py = centre(*k)
            sx = 20 if k not in BORN else 26
            v += math.exp(-(((x - px) / sx) ** 2 + ((y - py) / 13) ** 2))
        return v

    for lp in contours(fn, wx0 - 40, 30, wx1 + 40, ground + 10, 3, 0.55):
        pts = smooth_loop(lp, 64, 5)
        mx = sum(p[0] for p in pts) / len(pts)
        my = sum(p[1] for p in pts) / len(pts)
        lob = []
        for i, (x, y) in enumerate(pts):
            th = math.atan2(y - my, x - mx)
            bump = 2.2 * math.cos(9 * th)
            dx, dy = x - mx, y - my
            ln = math.hypot(dx, dy) or 1
            lob.append((x + dx / ln * bump, min(ground - 1, y + dy / ln * bump)))
        s.poly(lob, fill=G1, stroke=G7, sw=2.5)
    # dead areolae: crust cracked open at the old centre
    for k in DEAD:
        x, y = centre(*k)
        if fn(x, y) > 0.55:
            pts = [(x + 7 * math.cos(a) * (1 + 0.2 * math.sin(3 * a)), y + 5 * math.sin(a)) for a in
                   [2 * math.pi * i / 7 for i in range(7)]]
            s.poly(pts, fill=G0, stroke=G3, sw=1.5)
    # spores on bare stone
    for k in SPORES:
        x, y = centre(*k)
        s.circle(x, y, 3, fill=G0, stroke=G5, sw=1.5)
    # elevation furniture: course levels at the right
    for r in range(R):
        yb = ground - r * ch
        s.seg((wx1 + 4, yb), (wx1 + 12, yb), 1, G3)
        s.text(wx1 + 15, yb - ch / 2 + 4, str(r + 1), G4)
    s.text(wx1 + 15, 46, "oct", G4)
    # activity strip: the last 16 ticks of new growth, this tick brightest
    for i in range(16):
        t = SNAP - 15 + i
        nb = len(BIRTHS[t])
        x = wx0 + 10 + i * (wx1 - wx0 - 20) / 15
        hgt = 4 + 3 * nb
        col = G7 if i == 15 else (G4 if nb else G2)
        s.poly([(x - 2.5, 214), (x + 2.5, 214), (x + 2.5, 214 - hgt), (x - 2.5, 214 - hgt)], fill=col)
    s.save(HERE / "v4" / "rest.svg")


# =============================================================================
# v5 · P2 Diagram + trace · survey plan (stretch)
# =============================================================================
def v5():
    s = Svg()
    px0, py1, cw, rh = 26.0, 200.0, 29.0, 31.0

    def plot(c, r):
        return px0 + c * cw, py1 - (r + 1) * rh, px0 + (c + 1) * cw, py1 - r * rh

    # plan: parcel grid
    for r in range(R + 1):
        y = py1 - r * rh
        s.seg((px0, y), (px0 + N * cw, y), 1, G1)
    for c in range(N + 1):
        x = px0 + c * cw
        s.seg((x, py1 - R * rh), (x, py1), 1, G1)
    # colony traverse: union of live parcels, inset, with stations at the corners
    def union_loops(cells, inset):
        def fn(x, y):
            c = int((x - px0) // cw)
            r = int((py1 - y) // rh)
            return 1.0 if (c, r) in cells else 0.0
        loops = contours(fn, px0 - 6, py1 - R * rh - 6, px0 + N * cw + 6, py1 + 6, 1.0, 0.5)
        out = []
        for lp in loops:
            # snap to a rectilinear traverse: keep the corners
            pts = clean([(round(x), round(y)) for x, y in lp], gap=0.5)
            corners = []
            for i, p in enumerate(pts):
                a, b = pts[i - 1], pts[(i + 1) % len(pts)]
                if abs((p[0] - a[0]) * (b[1] - p[1]) - (p[1] - a[1]) * (b[0] - p[0])) > 0.5:
                    corners.append(p)
            cx = sum(p[0] for p in corners) / max(1, len(corners))
            cy = sum(p[1] for p in corners) / max(1, len(corners))
            out.append([(x + (inset if x < cx else -inset), y + (inset if y < cy else -inset)) for x, y in corners])
        return out

    for lp in union_loops(LIVE, 3):
        s.poly(lp, fill="none", stroke=G6, sw=2)
        for x, y in lp:
            s.circle(x, y, 2.2, fill=G0, stroke=G6, sw=1.2)
    for (c, r) in DEAD:
        xa, ya, xb, yb = plot(c, r)
        s.poly([(xa + 8, ya + 8), (xb - 8, ya + 8), (xb - 8, yb - 8), (xa + 8, yb - 8)], fill="none", stroke=G3, sw=1.2)
    for (c, r) in BORN:
        xa, ya, xb, yb = plot(c, r)
        mx, my = (xa + xb) / 2, (ya + yb) / 2
        s.poly([(mx - 4, my - 4), (mx + 4, my - 4), (mx + 4, my + 4), (mx - 4, my + 4)], fill=G7, stroke="none")
    for (c, r) in SPORES:
        xa, ya, xb, yb = plot(c, r)
        mx, my = (xa + xb) / 2, (ya + yb) / 2
        s.poly([(mx, my - 5), (mx + 5, my + 4), (mx - 5, my + 4)], fill=G0, stroke=G5, sw=1.2)
    for c in range(N):
        s.text(px0 + c * cw + cw / 2 - 3, 213, str(c + 1), G4)
    for r in range(R):
        s.text(10, py1 - r * rh - rh / 2 + 4, str(r + 1), G4)
    s.text(px0, 36, "plan", G4)
    s.seg((240, 28), (240, 214), 1, G2)

    # profile: the notes the colony has played, chainage = ticks, level = pitch
    qx0, qx1, qy0, qy1 = 262.0, 466.0, 46.0, 200.0
    span = 24
    pmax = 12 * R

    def lv(p):
        return qy1 - (p / pmax) * (qy1 - qy0)

    for r in range(R + 1):
        y = lv(12 * r)
        s.seg((qx0, y), (qx1, y), 1, G1 if r % R else G2)
    for i in range(0, span + 1, 4):
        x = qx0 + i * (qx1 - qx0) / span
        s.seg((x, qy1), (x, qy1 + 4), 1, G3)
    stations = []
    for i in range(span):
        t = SNAP - span + 1 + i
        x = qx0 + (i + 0.5) * (qx1 - qx0) / span
        for (q, _) in sorted(BIRTHS[t], key=lambda b: pitch(*b[0])):
            stations.append((x, lv(pitch(*q)), t == SNAP))
    for a, b in zip(stations, stations[1:]):
        s.seg(a[:2], b[:2], 1.5, G4)
    for x, y, now in stations:
        if now:
            s.circle(x, y, 3.6, fill=G7, stroke="none")
        else:
            s.circle(x, y, 2.4, fill=G0, stroke=G5, sw=1.2)
    s.text(qx0, 36, "profile", G4)
    s.text(qx1 - 22, 213, "now", G4)
    s.save(HERE / "v5" / "rest.svg")


if __name__ == "__main__":
    for fn in (v1, v2, v3, v4, v5):
        fn()
    print("snapshot tick", SNAP, "live", len(LIVE), "dead", len(DEAD), "born", sorted(BORN), "spores", SPORES)
