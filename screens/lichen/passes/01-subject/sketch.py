#!/usr/bin/env python3
"""Subject-pass sketches for lichen: five rest frames from one colony model.

    python3 screens/lichen/passes/01-subject/sketch.py

Writes v1..v5/rest.svg (480 x 220, stock header kept) and renders rest.png
beside each with rsvg-convert when it exists. All five draw the same colony
(model below) at the same tick, so they differ in pattern and drawing
language, not in what the machine is doing.

The model (the DSP sketch the brief describes):
  lattice   an isomorphic scale lattice, 12 columns x 6 rows, odd rows set half
            a cell right (a hex lattice drawn as running bond). Right is the next
            scale degree, up-left one degree, up-right two (a third), so a cell's
            degree is col - floor(row / 2) + 2 row: degrees 0..19, about three
            octaves. Six neighbours per cell.
  grow      each tick, each living cell spreads into one free neighbour with
            chance grow; at most 2 births a tick (they are the notes).
  decay     a living cell of age a dies with chance decay x a / 8; dead crust
            can't be regrown for 5 ticks, so the colony's old centre dies back
            while its margin grows, as a lichen does.
  seed      spores per bar (16 ticks): each lands on a random empty cell.
  scale     which semitones the degrees sit on (7 or 5 per octave).

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
C, R = 12, 6     # columns, rows
SNAP = 14        # tick shown
RNG_SEED = 282
START = (6, 2)

G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")


# --- colony model -----------------------------------------------------------
def nbrs(o, r):
    out = [(o - 1, r), (o + 1, r)]
    sh = r % 2
    for d in (-1, 1):
        out += [(o - 1 + sh, r + d), (o + sh, r + d)]
    return [(a, b) for a, b in out if 0 <= a < C and 0 <= b < R]


def run(grow=DEF["grow"], decay=DEF["decay"], seed=DEF["seed"], ticks=SNAP + 1, rs=RNG_SEED):
    rng = random.Random(rs)
    st = {(o, r): 0 for o in range(C) for r in range(R)}
    st[START] = 1
    hist, births = [], []
    for t in range(ticks):
        new = dict(st)
        born = []
        order = sorted(st.items())
        rng.shuffle(order)
        for k, a in order:
            if a > 0:
                free = [q for q in nbrs(*k) if st[q] == 0 and new[q] == 0]
                if free and len(born) < 2 and rng.random() < grow:
                    q = rng.choice(free)
                    new[q] = 1
                    born.append((q, k))
                new[k] = -5 if rng.random() < min(1, decay * a / 8) else a + 1
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
# the spore due at the next bar, on bare lattice away from the colony
SPORES = [(10, 4)]


def degree(o, r):
    return o - r // 2 + 2 * r


def pitch(o, r):
    d = degree(o, r)
    return SC[d % N] + 12 * (d // N)


def half_step_after(d):
    """True when the degree after d is a semitone above it (scale's half-step seams)."""
    a = SC[d % N] + 12 * (d // N)
    e = d + 1
    return SC[e % N] + 12 * (e // N) - a == 1


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
    cx, cy, k, tilt = 240.0, 120.0, 42.0, 0.40
    radii = [1.15 + 0.68 * r for r in range(R)]

    def proj(rad, th):
        return (cx + rad * k * math.sin(th), cy + rad * k * tilt * math.cos(th))

    def ang(o, r):  # one slot per column, odd rows half a slot on; the colony's side faces the camera
        return 2 * math.pi * (o + 0.5 * (r % 2) - 5.5) / C

    sun = 0.7 * k
    s.dashed([(26, cy), (454, cy)], 1, G2, dash=14, gap=4)
    s.dashed([(cx, 28), (cx, 212)], 1, G2, dash=14, gap=4)
    seed_r = radii[-1] + 0.5
    s.dashed([proj(seed_r, math.pi / 2 + math.pi * i / 60) for i in range(61)], 1, G3, dash=5, gap=5)
    for rad in radii:
        s.ribbon([proj(rad, math.pi / 2 + math.pi * i / 72) for i in range(73)], 1.2, G2)

    def planet(o, r, front):
        th = ang(o, r)
        if (math.cos(th) >= 0) != front:
            return
        x, y = proj(radii[r], th)
        depth = 1 + 0.18 * math.cos(th) * radii[r] / radii[-1]
        key = (o, r)
        dx, dy = math.sin(th), tilt * math.cos(th)
        ln = math.hypot(dx, dy)
        if degree(o, r) % N == 0:  # root slots carry a longer radial mark: the scale's octave
            s.seg((x - dx / ln * 7, y - dy / ln * 7), (x + dx / ln * 7, y + dy / ln * 7), 1.2, G4)
        if key in BORN:
            s.circle(x, y, 5.4 * depth, fill=G7, stroke=G7, sw=1.5)
        elif key in LIVE:
            s.circle(x, y, 4.2 * depth, fill=G2, stroke=G6, sw=1.5)
        elif key in DEAD:
            s.circle(x, y, 3.2 * depth, fill=G0, stroke=G3, sw=1.2)
        elif degree(o, r) % N:
            s.seg((x - dx / ln * 3, y - dy / ln * 3), (x + dx / ln * 3, y + dy / ln * 3), 1.2, G3)

    for r in range(R):
        for o in range(C):
            planet(o, r, front=False)
    s.circle(cx, cy, sun, fill=G0, stroke=G4, sw=1.5)
    s.ribbon([(cx + sun * math.sin(-math.pi / 2 + math.pi * i / 40),
               cy + sun * 0.3 * math.cos(-math.pi / 2 + math.pi * i / 40)) for i in range(41)], 1.2, G3)
    for rad in radii:
        s.ribbon([proj(rad, -math.pi / 2 + math.pi * i / 72) for i in range(73)], 1.2, G3)
    s.dashed([proj(seed_r, -math.pi / 2 + math.pi * i / 60) for i in range(61)], 1, G3, dash=5, gap=5)
    # growth links: along the orbit for a step, across orbits for a third
    for (q, p) in LINKS:
        a0, a1 = ang(*p), ang(*q)
        r0, r1 = radii[p[1]], radii[q[1]]
        s.ribbon([proj(r0 + (r1 - r0) * i / 12, a0 + (a1 - a0) * i / 12) for i in range(13)], 1.5, G5)
    for r in range(R):
        for o in range(C):
            planet(o, r, front=True)
    for (o, r) in SPORES:
        x, y = proj(seed_r, ang(o, r))
        s.circle(x, y, 3.5, fill=G0, stroke=G5, sw=1.5)
    for r, rad in enumerate(radii):
        x, _ = proj(rad, math.pi / 2)
        s.seg((x, cy - 3), (x, cy - 8), 1, G3)
        s.text(x - 3, cy - 11, str(r + 1), G4)
    s.text(cx + 196, cy - 11, "row", G4)
    s.save(HERE / "v1" / "rest.svg")


# =============================================================================
# v2 · P13 Capture · oscilloscope trace
# =============================================================================
def v2():
    s = Svg()
    gx0, gx1, gy0, gy1 = 40.0, 424.0, 30.0, 200.0
    unit = (gx1 - gx0) / 12.5
    rowh = (gy1 - gy0) / 6

    def at(o, r):
        return (gx0 + (o + 0.5 * (r % 2) + 0.5) * unit, gy1 - (r + 0.5) * rowh)

    # graticule: a 12 x 6 scope screen with a ticked centre axis
    s.poly([(gx0, gy0), (gx1, gy0), (gx1, gy1), (gx0, gy1)], stroke=G2, sw=1)
    for r in range(1, R):
        y = gy1 - r * rowh
        s.seg((gx0 + 1, y), (gx1 - 1, y), 1, G1)
    for i in range(1, 12):
        x = gx0 + i * (gx1 - gx0) / 12
        s.seg((x, gy0 + 1), (x, gy1 - 1), 1, G1)
    midy = gy1 - 3 * rowh
    for i in range(1, 60):
        x = gx0 + i * (gx1 - gx0) / 60
        if i % 5:
            s.seg((x, midy - 2.5), (x, midy + 2.5), 1, G2)
    for r in range(R):
        for o in range(C):
            if (o, r) not in LIVE and (o, r) not in DEAD:
                x, y = at(o, r)
                s.circle(x, y, 1.7, fill=G2, stroke="none")

    def field(cells, sx, sy):
        pts = [at(*k) for k in cells]

        def fn(x, y):
            return sum(math.exp(-(((x - px) / sx) ** 2 + ((y - py) / sy) ** 2)) for px, py in pts)
        return fn

    box = (gx0 - 30, gy0 - 20, gx1 + 30, gy1 + 20)
    # the capture front: the line new growth crosses; what it holds is alive
    for lp in contours(field(LIVE | DEAD, 21, 17), *box, 3, 0.5):
        s.poly(smooth_loop(lp, 60, 5), fill="none", stroke=G6, sw=2)
    # the dead centre: afterglow round the crust that can't regrow yet
    for lp in contours(field(DEAD, 20, 15), *box, 3, 0.7):
        s.poly(smooth_loop(lp, 40, 5), fill="none", stroke=G3, sw=1.5)
    for k in LIVE - BORN:
        x, y = at(*k)
        s.circle(x, y, 2.6, fill=G4, stroke="none")
    for k in BORN:
        x, y = at(*k)
        s.circle(x, y, 4.2, fill=G7, stroke="none")
    for k in SPORES:
        x, y = at(*k)
        s.circle(x, y, 3.5, fill=G0, stroke=G5, sw=1.5)
    # scale: the root of each octave is labelled on the screen
    for r in range(R):
        for o in range(C):
            if degree(o, r) % N == 0:
                x, y = at(o, r)
                s.text(x + 5, y - 4, "1", G4)
    s.text(gx1 + 7, gy0 + 9, "ch1", G4)
    s.text(gx1 + 7, gy1, "lat", G4)
    s.save(HERE / "v2" / "rest.svg")


# =============================================================================
# v3 · P14 Loom · typeset diagram
# =============================================================================
def v3():
    s = Svg()
    rows = 4
    vp = (250.0, -260.0)
    base = [186.0, 154.0, 126.0, 102.0]
    degs = sorted({degree(o, r) for o in range(C) for r in range(R)})

    def dpitch(d):
        return SC[d % N] + 12 * (d // N)

    def tx(d):
        return 34 + dpitch(d) * 12.4

    def place(d, kk):
        y = base[kk]
        sk = (y - vp[1]) / (base[0] - vp[1])
        return vp[0] + (tx(d) - vp[0]) * sk, y, sk

    for d in degs:  # warp threads
        xb, yb, _ = place(d, rows - 1)
        xf, yf, _ = place(d, 0)
        s.seg((xb, yb - 6), (xf, yf + 3), 1, G2 if d % N == 0 else G1)
    for kk in range(rows - 1, -1, -1):
        st = HIST[SNAP - kk]
        born = {degree(*q) for q, _ in BIRTHS[SNAP - kk]}
        alive = {degree(*c) for c, a in st.items() if a > 0}
        for d in degs:
            if d not in alive:
                continue
            x, y, sk = place(d, kk)
            w, dp = 9 * sk, 6 * sk
            b = d in born
            if kk == 0:
                hgt = 12
                front = [(x - w / 2, y), (x + w / 2, y), (x + w / 2, y - hgt), (x - w / 2, y - hgt)]
                top = [(x - w / 2, y - hgt), (x + w / 2, y - hgt), (x + w / 2 + 3, y - hgt - dp), (x - w / 2 + 3, y - hgt - dp)]
                s.poly(front, fill=G1, stroke=G5, sw=1)
                s.poly(top, fill=G7 if b else G3, stroke=G7 if b else G5, sw=1)
            else:
                top = [(x - w / 2, y), (x + w / 2, y), (x + w / 2 + 3 * sk, y - dp), (x - w / 2 + 3 * sk, y - dp)]
                shade = {1: G3, 2: G2, 3: G1}[kk]
                edge = {1: G4, 2: G3, 3: G3}[kk]
                s.poly(top, fill=shade, stroke=G5 if b else edge, sw=1)
    for (o, r) in SPORES:
        x = tx(degree(o, r))
        s.seg((x, base[0] + 3), (x, base[0] + 11), 1.2, G5)
        s.circle(x, base[0] + 14, 2.6, fill=G0, stroke=G5, sw=1.2)
    for kk, lab in enumerate(["t", "t-1", "t-2", "t-3"]):
        s.text(8, base[kk] - 2, lab, G5 if kk == 0 else G4)
    octs = sorted({d // N for d in degs})
    for oc in octs:
        ds = [d for d in degs if d // N == oc]
        xa, xb = tx(ds[0]) - 4, tx(ds[-1]) + 4
        s.seg((xa, 206), (xb, 206), 1, G3)
        s.seg((xa, 201), (xa, 206.5), 1, G3)
        s.text((xa + xb) / 2 - 3, 216, str(oc + 1), G4)
    s.text(8, 36, "fig. 1  growth by tick", G4)
    s.save(HERE / "v3" / "rest.svg")


# =============================================================================
# v4 · P5 Field and figure · orthographic elevation
# =============================================================================
def v4():
    s = Svg()
    wx0, sw_, ch = 58.0, 30.0, 24.0
    ground = 192.0
    wx1 = wx0 + C * sw_ + sw_ / 2

    def stone(o, r):
        xa = wx0 + (o + 0.5 * (r % 2)) * sw_
        yb = ground - r * ch
        return xa, yb - ch, xa + sw_, yb

    def centre(o, r):
        xa, ya, xb, yb = stone(o, r)
        return ((xa + xb) / 2, (ya + yb) / 2)

    # the wall (field): bed joints, perpends, half-step perpends doubled
    for r in range(R + 1):
        y = ground - r * ch
        s.seg((wx0, y), (wx1, y), 1, G1)
    for r in range(R):
        for o in range(C + 1):
            xa, ya, _, yb = stone(o, r)
            if xa > wx1 - 1:
                continue
            s.seg((xa, ya + 1), (xa, yb - 1), 1, G1)
            if 0 < o and half_step_after(degree(o - 1, r)):
                s.seg((xa + 3.5, ya + 4), (xa + 3.5, yb - 4), 1, G2)
    s.seg((wx0 - 22, ground + 1.5), (wx1 + 22, ground + 1.5), 2, G4)

    # the figure: the thallus, one lobed patch over the stones it holds
    patch = list(LIVE | DEAD)

    def fn(x, y):
        return sum(math.exp(-(((x - px) / 19) ** 2 + ((y - py) / 15) ** 2)) for px, py in (centre(*k) for k in patch))

    for lp in contours(fn, wx0 - 40, 26, wx1 + 40, ground + 12, 3, 0.55):
        if perimeter(lp) < 60:
            continue
        pts = smooth_loop(lp, 64, 4.5)
        for _ in range(2):  # relax the grid's stair-steps before lobing
            pts = [((a[0] + 2 * b[0] + c[0]) / 4, (a[1] + 2 * b[1] + c[1]) / 4)
                   for a, b, c in zip(pts[-1:] + pts[:-1], pts, pts[1:] + pts[:1])]
        mx = sum(p[0] for p in pts) / len(pts)
        my = sum(p[1] for p in pts) / len(pts)
        acc, lob = 0.0, []
        for i, (x, y) in enumerate(pts):
            acc += math.dist(pts[i - 1], (x, y)) if i else 0
            bump = 3.0 * math.cos(2 * math.pi * acc / 24)
            dx, dy = x - mx, y - my
            ln = math.hypot(dx, dy) or 1
            lob.append((x + dx / ln * bump, min(ground - 0.5, y + dy / ln * bump)))
        s.poly(lob, fill=G1, stroke=G7, sw=2.5)
    for k in DEAD:  # old crust cracked open: areolae at the dead centre
        x, y = centre(*k)
        pts = [(x + 8 * math.cos(a), y + 6 * math.sin(a) * (1 + 0.15 * math.cos(2 * a)))
               for a in [2 * math.pi * (i + 0.3) / 6 for i in range(6)]]
        s.poly(pts, fill=G0, stroke=G3, sw=1.5)
    for k in BORN:  # this tick's growth: a fresh lobe brightening at the margin
        x, y = centre(*k)
        s.circle(x, y, 3.6, fill=G7, stroke="none")
    for k in SPORES:
        x, y = centre(*k)
        s.circle(x, y, 3, fill=G0, stroke=G5, sw=1.5)
    for r in range(R):
        yb = ground - r * ch
        s.seg((wx1 + 6, yb - ch), (wx1 + 12, yb - ch), 1, G3)
    s.text(wx1 + 8, ground - R * ch - 6, "+3rd", G4)
    s.text(wx0 - 2, ground - R * ch - 6, "elev.", G4)
    # activity strip: the last 16 ticks of new growth, this tick brightest
    for i in range(16):
        t = SNAP - 15 + i
        nb = len(BIRTHS[t]) if t >= 0 else 0
        x = wx0 + 12 + i * (wx1 - wx0 - 24) / 15
        hgt = 4 + 3 * nb
        col = G7 if i == 15 else (G4 if nb else G2)
        s.poly([(x - 2.5, 214), (x + 2.5, 214), (x + 2.5, 214 - hgt), (x - 2.5, 214 - hgt)], fill=col)
    s.save(HERE / "v4" / "rest.svg")


# =============================================================================
# v5 · P2 Diagram + trace · survey plan (stretch)
# =============================================================================
def v5():
    s = Svg()
    px0, py1, cw, rh = 14.0, 200.0, 16.8, 26.0
    ptop = py1 - R * rh

    def lot(o, r):
        xa = px0 + (o + 0.5 * (r % 2)) * cw
        return xa, py1 - (r + 1) * rh, xa + cw, py1 - r * rh

    for r in range(R + 1):  # plan: lots in running bond, like a surveyed terrace
        y = py1 - r * rh
        s.seg((px0, y), (px0 + (C + 0.5) * cw, y), 1, G1)
    for r in range(R):
        for o in range(C + 1):
            xa, ya, _, yb = lot(o, r)
            s.seg((xa, ya + 1), (xa, yb - 1), 1, G1)

    def cell_at(x, y):
        r = int((py1 - y) // rh)
        if not 0 <= r < R:
            return None
        o = math.floor((x - px0) / cw - 0.5 * (r % 2))
        return (o, r)

    def traverse(cells):
        fn = lambda x, y: 1.0 if cell_at(x, y) in cells else 0.0
        out = []
        for lp in contours(fn, px0 - 4, ptop - 4, px0 + (C + 1) * cw, py1 + 4, 1.0, 0.5):
            pts = clean([(round(x * 2) / 2, round(y * 2) / 2) for x, y in lp], gap=0.4)
            corners = []
            for i, p in enumerate(pts):
                a, b = pts[i - 1], pts[(i + 1) % len(pts)]
                if abs((p[0] - a[0]) * (b[1] - p[1]) - (p[1] - a[1]) * (b[0] - p[0])) > 0.3:
                    corners.append(p)
            corners = clean(corners, gap=2.0)
            if len(corners) >= 4:
                out.append(corners)
        return out

    for lp in traverse(LIVE | DEAD):
        s.poly(lp, fill="none", stroke=G6, sw=2)
        for x, y in lp:
            s.circle(x, y, 2.2, fill=G0, stroke=G6, sw=1.2)
    for k in DEAD:
        xa, ya, xb, yb = lot(*k)
        s.poly([(xa + 4, ya + 6), (xb - 4, ya + 6), (xb - 4, yb - 6), (xa + 4, yb - 6)], fill="none", stroke=G3, sw=1.2)
    for k in BORN:
        xa, ya, xb, yb = lot(*k)
        mx, my = (xa + xb) / 2, (ya + yb) / 2
        s.poly([(mx - 4, my - 4), (mx + 4, my - 4), (mx + 4, my + 4), (mx - 4, my + 4)], fill=G7)
    for k in SPORES:
        xa, ya, xb, yb = lot(*k)
        mx, my = (xa + xb) / 2, (ya + yb) / 2
        s.poly([(mx, my - 5), (mx + 5, my + 4), (mx - 5, my + 4)], fill=G0, stroke=G5, sw=1.2)
    for r in range(R):
        for o in range(C):
            if degree(o, r) % N == 0:
                xa, ya, xb, yb = lot(o, r)
                s.text(xa + 2, yb - 3, "1", G4)
    s.text(px0, 36, "plan", G4)
    s.seg((240, 28), (240, 214), 1, G2)

    # profile: the notes the colony has played; chainage = ticks, level = pitch
    qx0, qx1, qy0, qy1 = 262.0, 466.0, 46.0, 200.0
    span, pmax = 16, 36

    def lv(p):
        return qy1 - (p / pmax) * (qy1 - qy0)

    for oc in range(4):
        y = lv(12 * oc)
        s.seg((qx0, y), (qx1, y), 1, G2 if oc == 0 else G1)
    for i in range(0, span + 1, 4):
        x = qx0 + i * (qx1 - qx0) / span
        s.seg((x, qy1), (x, qy1 + 5), 1, G3)
    stations = []
    for i in range(span):
        t = SNAP - span + 1 + i
        if t < 0:
            continue
        x = qx0 + (i + 0.5) * (qx1 - qx0) / span
        bs = sorted(BIRTHS[t], key=lambda b: pitch(*b[0]))
        for j, (q, _) in enumerate(bs):
            stations.append((x + (j - (len(bs) - 1) / 2) * 4, lv(pitch(*q)), t == SNAP))
    for a, b in zip(stations, stations[1:]):  # a levelled profile: hold, then step
        s.seg((a[0], a[1]), (b[0], a[1]), 1.5, G4)
        s.seg((b[0], a[1]), (b[0], b[1]), 1.5, G4)
    for x, y, now in stations:
        if now:
            s.circle(x, y, 3.8, fill=G7, stroke="none")
        else:
            s.circle(x, y, 2.4, fill=G0, stroke=G5, sw=1.2)
    s.text(qx0, 36, "profile", G4)
    s.text(qx1 - 22, 213, "now", G4)
    s.save(HERE / "v5" / "rest.svg")


if __name__ == "__main__":
    for fn in (v1, v2, v3, v4, v5):
        fn()
    print("snapshot tick", SNAP, "live", len(LIVE), "dead", len(DEAD), "born", sorted(BORN), "spores", SPORES)
