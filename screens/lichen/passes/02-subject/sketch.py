#!/usr/bin/env python3
"""Subject pass 02 sketches for lichen: five rest frames from one colony model.

    python3 screens/lichen/passes/02-subject/sketch.py

Writes v1..v5/rest.svg (480 x 220, stock header kept) and renders rest.png
beside each with rsvg-convert. All five draw the same colony (the model from
pass 01, copied here so this file stands alone) at the same tick, at the
definition's defaults (grow 35, decay 20, seed 1, maj).

Every 3D thing is modelled in world units and projected through one camera
per variant (craft.md, Think in 3D). No text below the header: every state
is a line weight, a brightness, a movement or 45-degree hatching.

The model:
  lattice   12 columns x 6 rows, odd rows set half a cell right (a hex
            lattice). A cell's degree is col - floor(row / 2) + 2 row. In
            continuous hex coordinates (X = col + row % 2 / 2) that is
            X + 1.5 row, which the pitch-warped drawings use.
  grow      each living cell takes one free neighbour with chance grow;
            at most 2 births a tick (they are the notes).
  decay     a living cell of age a dies with chance decay * a / 8; dead
            crust can't regrow for 5 ticks.
  seed      spores per bar land on random empty cells.
  scale     which semitones the degrees sit on.
"""
from __future__ import annotations

import math
import random
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 480, 220
TOP, BOT = 23.0, 215.0          # body band the drawings stay inside

SCALES = {"maj": [0, 2, 4, 5, 7, 9, 11], "min": [0, 2, 3, 5, 7, 8, 10], "dor": [0, 2, 3, 5, 7, 9, 10],
          "phr": [0, 1, 3, 5, 7, 8, 10], "lyd": [0, 2, 4, 6, 7, 9, 11], "mix": [0, 2, 4, 5, 7, 9, 10],
          "pent": [0, 2, 4, 7, 9], "pmin": [0, 3, 5, 7, 10]}
DEF = {"grow": 0.35, "decay": 0.2, "seed": 1, "scale": "maj"}
HEAD_L = ["grow", "decay", "seed", "scale"]
HEAD_V = ["35", "20", "1", "maj"]
C, R = 12, 6
SNAP = 14
RNG_SEED = 282
START = (6, 2)
RH = math.sqrt(3) / 2           # row spacing for unit-wide hexes

G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
HAIR, LINE, SUBJ = 1.0, 1.5, 2.2


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
LIVE = {k for k, a in STATE.items() if a > 0}
DEAD = {k for k, a in STATE.items() if a < 0}
FREE = {k for k, a in STATE.items() if a == 0}
SC = SCALES[DEF["scale"]]
N = len(SC)
SPORES = [(10, 4), (9, 1), (1, 3), (11, 2), (2, 0), (10, 5), (0, 4), (8, 5)][:DEF["seed"]]


def degree(o, r):
    return o - r // 2 + 2 * r


def pitch_of_degree(d):
    return SC[d % N] + 12 * (d // N)


def pitch(o, r):
    return pitch_of_degree(degree(o, r))


def semitone_after(d):
    """True when the next degree up is a half step away."""
    return pitch_of_degree(d + 1) - pitch_of_degree(d) == 1


def pc(dc):
    """Continuous pitch for a fractional degree, normalised so the mean step is 1."""
    i = math.floor(dc)
    t = dc - i
    a, b = pitch_of_degree(i), pitch_of_degree(i + 1)
    return (a + (b - a) * t) * N / 12.0


def hexc(o, r):
    """Cell centre in plain hex world units (unit-wide cells)."""
    return (o + 0.5 * (r % 2), r * RH)


HEXV = [(0.5 * math.cos(math.radians(a)) / math.cos(math.radians(30)),
         0.5 * math.sin(math.radians(a)) / math.cos(math.radians(30))) for a in (-30, 30, 90, 150, 210, 270)]


def hexpoly(o, r, k=1.0):
    x, y = hexc(o, r)
    return [(x + vx * k, y + vy * k) for vx, vy in HEXV]


# --- vector helpers ---------------------------------------------------------
def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    ln = math.sqrt(dot(a, a)) or 1
    return tuple(x / ln for x in a)


class Cam:
    """One pinhole camera: eye, look-at, focal length in px, image centre."""

    def __init__(self, eye, at, f, cx, cy):
        self.e = eye
        self.fw = norm(sub(at, eye))
        self.rt = norm(cross(self.fw, (0, 0, 1)))
        self.up = cross(self.rt, self.fw)
        self.f, self.cx, self.cy = f, cx, cy

    def p(self, q):
        d = sub(q, self.e)
        z = dot(d, self.fw)
        k = self.f / z
        return (self.cx + dot(d, self.rt) * k, self.cy - dot(d, self.up) * k)

    def dist(self, q):
        return dot(sub(q, self.e), self.fw)


def clip_half(poly, inside, cut):
    """Sutherland-Hodgman against one half-plane: inside(p) bool, cut(a, b) -> point."""
    out = []
    for i, cur in enumerate(poly):
        prev = poly[i - 1]
        ci, pi = inside(cur), inside(prev)
        if ci:
            if not pi:
                out.append(cut(prev, cur))
            out.append(cur)
        elif pi:
            out.append(cut(prev, cur))
    return out


def clip_rect(poly, x0=0.0, y0=TOP, x1=W, y1=BOT):
    def lerp(a, b, t):
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    for ax, lim, keep_gt in ((0, x0, True), (0, x1, False), (1, y0, True), (1, y1, False)):
        if not poly:
            return []
        poly = clip_half(poly,
                         (lambda p, ax=ax, lim=lim, g=keep_gt: p[ax] >= lim if g else p[ax] <= lim),
                         (lambda a, b, ax=ax, lim=lim: lerp(a, b, (lim - a[ax]) / (b[ax] - a[ax]))))
    return poly


def clip_seg(a, b, x0=0.0, y0=TOP, x1=W, y1=BOT):
    """Liang-Barsky clip of a segment to the body box."""
    t0, t1 = 0.0, 1.0
    dx, dy = b[0] - a[0], b[1] - a[1]
    for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
        if p == 0:
            if q < 0:
                return None
            continue
        t = q / p
        if p < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
    if t0 >= t1:
        return None
    return (a[0] + dx * t0, a[1] + dy * t0), (a[0] + dx * t1, a[1] + dy * t1)


def inpoly(p, poly):
    x, y = p
    c = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i - 1], poly[i]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def area(poly):
    return 0.5 * sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))


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


def resample(pts, n, closed=True):
    ring = pts + [pts[0]] if closed else list(pts)
    lens = [math.dist(a, b) for a, b in zip(ring, ring[1:])]
    total = sum(lens)
    out, acc, i = [], 0.0, 0
    m = n if closed else n - 1
    for k in range(n):
        target = total * k / m
        while i < len(lens) - 1 and acc + lens[i] < target:
            acc += lens[i]
            i += 1
        t = (target - acc) / lens[i] if lens[i] else 0
        a, b = ring[i], ring[i + 1]
        out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
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

    def poly(self, pts, fill="none", stroke="none", sw=None, clip=True):
        pts = clean(pts)
        if clip:
            cp = clean(clip_rect(pts))
            if stroke != "none" and len(cp) >= 3 and (len(cp) != len(pts) or any(
                    math.dist(a, b) > 0.01 for a, b in zip(cp, pts))):
                # clipped by the frame: fill the clipped shape, stroke only the real edges
                self.poly(cp, fill=fill, clip=False)
                self.line(pts + pts[:1], sw, stroke)
                return
            pts = cp
        if len(pts) < 3 or abs(area(pts)) < 0.5:
            return
        if len(pts) > 64:
            pts = resample(pts, 64)
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
        s = f' stroke-width="{sw}"' if stroke != "none" else ""
        self.o.append(f'  <path d="{d}" fill="{fill}" stroke="{stroke}"{s}/>')

    def ribbon(self, pts, w, col):
        """An open line drawn as a thin closed ribbon (constraints: no traced strokes)."""
        pts = clean(pts, closed=False, gap=0.6)
        if len(pts) < 2:
            return
        if len(pts) > 30:
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
        c = clip_seg(a, b)
        if c and math.dist(*c) > 0.8:
            self.ribbon(list(c), w, col)

    def line(self, pts, w, col):
        """A polyline clipped to the body, as ribbons."""
        run = []
        for a, b in zip(pts, pts[1:]):
            c = clip_seg(a, b)
            if c is None:
                if len(run) > 1:
                    self.ribbon(run, w, col)
                run = []
                continue
            if run and math.dist(run[-1], c[0]) < 0.01:
                run.append(c[1])
            else:
                if len(run) > 1:
                    self.ribbon(run, w, col)
                run = [c[0], c[1]]
        if len(run) > 1:
            self.ribbon(run, w, col)

    def dashed(self, pts, w, col, dash=5, gap=4):
        acc, cur, on = 0.0, [pts[0]], True
        for a, b in zip(pts, pts[1:]):
            ln = math.dist(a, b)
            t = 0.0
            while t < ln - 1e-9:
                lim = (dash if on else gap) - acc
                step = min(lim, ln - t)
                t += step
                acc += step
                p = (a[0] + (b[0] - a[0]) * t / ln, a[1] + (b[1] - a[1]) * t / ln)
                if on:
                    cur.append(p)
                if acc >= (dash if on else gap) - 1e-9:
                    if on and len(cur) > 1:
                        self.line(cur, w, col)
                    on, acc, cur = not on, 0.0, [p]
        if on and len(cur) > 1:
            self.line(cur, w, col)

    def hatch(self, polys, col=G3, gap=4.0, w=HAIR, phase=0.0):
        """45-degree hairlines (rising to the right), gap px apart, clipped to the
        polygons (even-odd) and to the body."""
        pts = [p for q in polys for p in q]
        if not pts:
            return
        lo = min(x - y for x, y in pts)
        hi = max(x - y for x, y in pts)
        step = gap * math.sqrt(2)
        c = math.floor((lo - phase) / step) * step + phase
        while c <= hi:
            # line: x - y = c ... parametrise by x; y = x - c (screen: rises to the right
            # means y falls as x grows, so use x + y = c instead)
            xs = []
            for q in polys:
                for a, b in zip(q, q[1:] + q[:1]):
                    sa, sb = a[0] + a[1], b[0] + b[1]
                    if (sa - c) * (sb - c) < 0:
                        t = (c - sa) / (sb - sa)
                        xs.append(a[0] + (b[0] - a[0]) * t)
            xs.sort()
            for x1, x2 in zip(xs[0::2], xs[1::2]):
                self.seg((x1, c - x1), (x2, c - x2), w, col)
            c += step
        # (the loop runs over x - y bounds, which match x + y extents closely enough
        #  only for square-ish regions; widen to be safe)

    def disc(self, cx, cy, r, fill, stroke="none", sw=None, n=20):
        self.poly([(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n))
                   for k in range(n)], fill=fill, stroke=stroke, sw=sw)

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(self.o + ["</svg>", ""]), encoding="utf-8")
        if shutil.which("rsvg-convert"):
            subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H), "-b", "black",
                            str(path), "-o", str(path.with_suffix(".png"))], check=True)


def hatch_fixed(s, polys, col=G3, gap=4.0, w=HAIR):
    """Hatch with the sweep running over x + y (the actual line family)."""
    pts = [p for q in polys for p in q]
    if not pts:
        return
    lo = min(x + y for x, y in pts)
    hi = max(x + y for x, y in pts)
    step = gap * math.sqrt(2)
    c = math.floor(lo / step) * step
    while c <= hi:
        xs = []
        for q in polys:
            for a, b in zip(q, q[1:] + q[:1]):
                sa, sb = a[0] + a[1], b[0] + b[1]
                if (sa - c) * (sb - c) < 0:
                    t = (c - sa) / (sb - sa)
                    xs.append(a[0] + (b[0] - a[0]) * t)
        xs.sort()
        for x1, x2 in zip(xs[0::2], xs[1::2]):
            s.seg((x1, c - x1), (x2, c - x2), w, col)
        c += step


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
            edges = [e for e in range(4) if inside[e] != inside[(e + 1) % 4]]
            if len(edges) == 2:
                segs.append(((i, j, edges[0]), (i, j, edges[1])))
            elif len(edges) == 4:
                segs.append(((i, j, 0), (i, j, 1)))
                segs.append(((i, j, 2), (i, j, 3)))

    def key(i, j, e):
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


def chamfer(poly, k):
    """Cut each corner back by k of its edges: a rounded areola."""
    out = []
    n = len(poly)
    for i in range(n):
        a, b, c = poly[i - 1], poly[i], poly[(i + 1) % n]
        out.append((b[0] + (a[0] - b[0]) * k, b[1] + (a[1] - b[1]) * k))
        out.append((b[0] + (c[0] - b[0]) * k, b[1] + (c[1] - b[1]) * k))
    return out


def thick(age):
    return 0.07 + 0.03 * min(abs(age), 8)


# =============================================================================
# v1 · cutaway section: the colony as crust on a block of stone, cut open
# =============================================================================
def v1():
    """A block of stone carrying the colony, cut open along row 2 (the start
    row). The cut face is a section: stone with its bedding, the crust's
    thickness (its age) on top, the cortex inside it, rhizines into the stone.
    Behind the cut, the rest of the colony stands as crust plates. Every knob
    is something physical: grow pushes tongues of crust over bare stone, decay
    lifts dead crust off in flakes, seed drops spores, scale opens the cracks
    between stones a half step apart."""
    s = Svg()
    cut = 2 * RH
    yb = 5 * RH + 0.55
    x0w, x1w, zb = 2.15, 9.75, -1.0
    TK = 0.85
    cam = Cam((5.95, -9.6, 5.0), (5.95, 2.9, -0.3), 690, 240, 112)
    P = cam.p

    def keep(pt):
        return pt[1] >= cut - 1e-9

    def ycut(a, b):
        t = (cut - a[1]) / (b[1] - a[1])
        return (a[0] + (b[0] - a[0]) * t, cut)

    def xclip(poly):
        poly = clip_half(poly, lambda p: p[0] >= x0w, lambda a, b: (x0w, a[1] + (b[1] - a[1]) * (x0w - a[0]) / (b[0] - a[0])))
        if poly:
            poly = clip_half(poly, lambda p: p[0] <= x1w, lambda a, b: (x1w, a[1] + (b[1] - a[1]) * (x1w - a[0]) / (b[0] - a[0])))
        return poly

    def half(poly):
        return clip_half(poly, keep, ycut)

    top = [(x0w, cut, 0), (x1w, cut, 0), (x1w, yb, 0), (x0w, yb, 0)]
    front = [(x0w, cut, zb), (x1w, cut, zb), (x1w, cut, 0), (x0w, cut, 0)]
    side = [(x1w, cut, zb), (x1w, yb, zb), (x1w, yb, 0), (x1w, cut, 0)]
    s.poly([P(q) for q in side], fill=G0, stroke=G3, sw=LINE)
    s.poly([P(q) for q in top], fill=G0, stroke=G3, sw=LINE)
    s.poly([P(q) for q in front], fill=G0, stroke=G4, sw=LINE)

    # half-step joints: open cracks down the cut face and back across the top (scale)
    joints = [hexc(o, 2)[0] + 0.5 for o in range(C - 1) if semitone_after(degree(o, 2))]
    joints = [x for x in joints if x0w + 0.2 < x < x1w - 0.2]
    # bedding planes in the cut face: hairlines >= 6 px apart, broken at the cracks
    rng = random.Random(7)
    for k, z in enumerate((-0.34, -0.6, -0.86)):
        xs = [x0w + 0.1 + rng.random() * 0.3]
        while xs[-1] < x1w - 0.3:
            xs.append(min(x1w - 0.1, xs[-1] + 0.35 + rng.random() * 0.3))
        pts = [(x, z + 0.025 * math.sin(x * 2.1 + k * 1.3)) for x in xs]
        runs, cur = [], []
        for x, zz in pts:
            if any(abs(x - j) < 0.12 for j in joints):
                if len(cur) > 1:
                    runs.append(cur)
                cur = []
            else:
                cur.append(P((x, cut, zz)))
        if len(cur) > 1:
            runs.append(cur)
        for rr in runs:
            s.line(rr, HAIR, G2)
    for jx in joints:
        a, b = P((jx - 0.06, cut, 0)), P((jx + 0.06, cut, 0))
        m = P((jx + 0.02, cut, -0.45))
        e = P((jx - 0.04, cut, -0.82))
        s.poly([a, m, b], fill=G0, stroke="none")
        s.line([a, m, e], HAIR, G4)
        s.line([b, m], HAIR, G4)
    for r in range(2, R):
        for o in range(C - 1):
            if semitone_after(degree(o, r)):
                x, y = hexc(o, r)
                if not (x0w + 0.2 < x + 0.5 < x1w - 0.2):
                    continue
                ya, yb2 = max(cut, y - 0.289), min(yb, y + 0.289)
                if yb2 <= ya:
                    continue
                s.seg(P((x + 0.47, ya, 0)), P((x + 0.47, yb2, 0)), HAIR, G3)
                s.seg(P((x + 0.54, ya, 0)), P((x + 0.54, yb2, 0)), HAIR, G3)

    # crust: plates (live), hatched remnants with lifted flakes (dead), tongues (grow)
    items = []
    for (o, r), a in STATE.items():
        if r < 2 or a == 0:
            continue
        hp = chamfer(hexpoly(o, r, 0.94), 0.24)
        if r == 2:
            hp = half(hp)
        hp = xclip(hp)
        cx, cy = hexc(o, r)
        items.append((cam.dist((cx, cy, 0)), "cell", (o, r), hp, a))
    g = DEF["grow"]
    for (o, r) in LIVE:
        if r < 2:
            continue
        for q in nbrs(o, r):
            if q not in FREE:
                continue
            ax, ay = hexc(o, r)
            bx, by = hexc(*q)
            dx, dy = bx - ax, by - ay
            ln = math.hypot(dx, dy)
            ux, uy, nx, ny = dx / ln, dy / ln, -dy / ln, dx / ln
            L = 0.42 + 0.7 * g
            pts = []
            for k in range(11):
                tt = k / 10
                along = 0.4 + (L - 0.4) * math.sin(tt * math.pi) ** 0.5
                sd = 0.2 * math.cos(tt * math.pi)
                pts.append((ax + ux * along + nx * sd, ay + uy * along + ny * sd))
            poly = xclip(half(pts))
            if len(poly) >= 3:
                mx = sum(p[0] for p in poly) / len(poly)
                my = sum(p[1] for p in poly) / len(poly)
                items.append((cam.dist((mx, my, 0)) + 0.01, "tongue", (o, r), poly, 1))
    items.sort(key=lambda t: -t[0])

    for _, kind, (o, r), hp, a in items:
        if len(hp) < 3:
            continue
        if area(hp) < 0:
            hp = hp[::-1]
        if kind == "tongue":
            # a thin lobe of crust over bare stone: drawn as a flat sheet, edge only
            s.poly([P((x, y, 0.03)) for x, y in hp], fill=G0, stroke=G4, sw=HAIR)
            continue
        if a > 0:
            h = thick(a) * TK
            born = (o, r) in BORN
            prism(s, cam, hp, 0, h, side=G4, topc=G7 if born else G5,
                  topw=SUBJ if born else LINE, sidew=HAIR)
            if r == 2:          # section: cortex line inside the crust, rhizines into the stone
                x, _ = hexc(o, r)
                pts = [P((x - 0.44 + 0.88 * k / 8, cut, h * 0.55)) for k in range(9)]
                s.line(pts, HAIR, G3)
                for k in (-0.28, 0.0, 0.26):
                    s.line([P((x + k, cut, 0)), P((x + k + 0.03, cut, -0.1)),
                            P((x + k - 0.02, cut, -0.19))], HAIR, G3)
        else:
            # dead crust: a thin hatched remnant, one flake hinged at its back edge
            h = 0.05
            prism(s, cam, hp, 0, h, side=G3, topc=G3, topw=HAIR, sidew=HAIR)
            hatch_fixed(s, [[P((x, y, h)) for x, y in hp]], G3, 4.0)
            cx, cy = hexc(o, r)
            ang = math.radians(12 + 75 * DEF["decay"])
            hy = max(cut, cy + 0.06) if r == 2 else cy + 0.06
            hx0, hx1 = cx - 0.36, cx + 0.36
            reach = 0.36
            fl = [(hx0, hy, h), (hx1, hy, h),
                  (hx1 - 0.08, hy - reach * math.cos(ang), h + reach * math.sin(ang)),
                  (hx0 + 0.1, hy - reach * 0.9 * math.cos(ang), h + reach * 0.9 * math.sin(ang))]
            if r == 2:
                fl = [(x, max(y, cut), z) for x, y, z in fl]
            fp = [P(q) for q in fl]
            s.poly(fp, fill=G0, stroke=G4, sw=HAIR)
            hatch_fixed(s, [fp], G3, 4.0)

    # spores: falling onto bare stone, a dashed hairline to where each lands (seed)
    for (o, r) in SPORES:
        x, y = hexc(o, max(r, 3))
        x = min(max(x, x0w + 0.3), x1w - 0.3)
        a = P((x, y, 0.75))
        b = P((x, y, 0.0))
        s.dashed([(a[0], a[1] + 4), (b[0], b[1] - 2)], HAIR, G3, 3, 3)
        s.disc(a[0], a[1], 2.3, fill=G5)
        s.line([(b[0] - 3, b[1]), (b[0] + 3, b[1])], HAIR, G3)
    s.save(HERE / "v1" / "rest.svg")


def prism(s, cam, base, z0, h, side=G4, topc=G5, topw=LINE, sidew=HAIR):
    """A convex prism on base (CCW, world XY), drawn hidden-line: visible side
    faces back to front with black fill, then the top."""
    P = cam.p
    n = len(base)
    faces = []
    for i in range(n):
        a, b = base[i], base[(i + 1) % n]
        nx, ny = b[1] - a[1], -(b[0] - a[0])
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, z0 + h / 2)
        toeye = sub(cam.e, mid)
        if nx * toeye[0] + ny * toeye[1] > 0:
            faces.append((cam.dist(mid), [P((a[0], a[1], z0)), P((b[0], b[1], z0)),
                                          P((b[0], b[1], z0 + h)), P((a[0], a[1], z0 + h))]))
    for _, q in sorted(faces, key=lambda t: -t[0]):
        s.poly(q, fill=G0, stroke=side, sw=sidew)
    s.poly([P((x, y, z0 + h)) for x, y in base], fill=G0, stroke=topc, sw=topw)


# =============================================================================
# v2 · exploded view: the colony taken apart into what it's made of
# =============================================================================
def v2():
    s = Svg()
    cam = Cam((5.6, -13.0, 6.6), (5.6, 2.6, 1.9), 470, 240, 112)
    P = cam.p
    zs = {"plate": 0.0, "dead": 1.3, "live": 2.6, "spore": 4.4}
    # 1 · the stone lattice plate: every cell a tile; half-step seams raised
    pl = [(-0.6, -0.65), (12.15, -0.65), (12.15, 5 * RH + 0.65), (-0.6, 5 * RH + 0.65)]
    prism(s, cam, pl, -0.22, 0.22, side=G3, topc=G3, topw=LINE, sidew=HAIR)
    for r in range(R):
        for o in range(C):
            hp = [P((x, y, 0)) for x, y in hexpoly(o, r)]
            for i, (a, b) in enumerate(zip(hp, hp[1:] + hp[:1])):
                if i == 0 and o < C - 1 and semitone_after(degree(o, r)):
                    continue
                s.seg(a, b, HAIR, G1 if (o, r) not in LIVE | DEAD else G2)
            if o < C - 1 and semitone_after(degree(o, r)):
                # the edge between this cell and the next one up a half step: a ridge
                x, y = hexc(o, r)
                a, b = (x + 0.5, y - 0.289), (x + 0.5, y + 0.289)
                prism(s, cam, [(a[0] - 0.04, a[1]), (a[0] + 0.04, a[1]), (b[0] + 0.04, b[1]), (b[0] - 0.04, b[1])],
                      0, 0.09, side=G3, topc=G4, topw=HAIR, sidew=HAIR)
    # assembly axes: dashed hairlines through the layers, at the start cell and at each birth
    axes = [START] + sorted(BORN)
    def axis(c, za, zb):
        x, y = hexc(*c)
        s.dashed([P((x, y, za)), P((x, y, zb))], HAIR, G2, 4, 3)
    for c in axes:
        axis(c, 0.02, zs["dead"] - 0.02)
    # 2 · the dead crust layer: hatched plates where the centre died
    for c in sorted(DEAD, key=lambda c: -cam.dist((*hexc(*c), 0))):
        hp = [P((x, y, zs["dead"])) for x, y in chamfer(hexpoly(*c, k=0.92), 0.24)]
        s.poly(hp, fill=G0, stroke=G3, sw=HAIR)
        hatch_fixed(s, [hp], G3, 4.0)
    for c in axes:
        axis(c, zs["dead"] + 0.02, zs["live"] - 0.02)
    # 3 · the living crust: prisms whose height is age; births lifted out of it
    g = DEF["grow"]
    cells = sorted(LIVE, key=lambda c: -cam.dist((*hexc(*c), zs["live"])))
    lifted = []
    for c in cells:
        a = STATE[c]
        if c in BORN:
            lifted.append(c)
            continue
        hp = chamfer(hexpoly(*c, k=0.92), 0.24)
        prism(s, cam, hp, zs["live"], thick(a) * 1.6, side=G3, topc=G5, topw=LINE, sidew=HAIR)
    for c in axes:
        axis(c, zs["live"] + 0.3, zs["live"] + 0.55 + 1.6 * g)
    for c in lifted:
        hp = chamfer(hexpoly(*c, k=0.92), 0.24)
        prism(s, cam, hp, zs["live"] + 0.55 + 1.6 * g, thick(1) * 1.6, side=G4, topc=G7, topw=SUBJ, sidew=HAIR)
    # 4 · spores waiting above, one per spore due this bar
    for c in SPORES:
        x, y = hexc(*c)
        a = P((x, y, zs["spore"]))
        b = P((x, y, zs["live"] + 0.1))
        s.dashed([(a[0], a[1] + 4), b], HAIR, G2, 3, 3)
        s.disc(a[0], a[1], 2.4, fill=G5)
    s.save(HERE / "v2" / "rest.svg")


# =============================================================================
# v3 · single-weight contour: the trail the colony has left on the stone
# =============================================================================
def v3():
    s = Svg()
    pmax = pitch_of_degree(19)

    def pos(c):
        o, r = c
        return (44 + pitch(o, r) * 392 / pmax, 196 - r * 30)

    # every birth since the start, parent to child, as one bent contour
    links = []
    for t in range(SNAP + 1):
        for q, p in BIRTHS[t]:
            links.append((t, q, p))
    g = DEF["grow"]

    def curve(a, b, bend=0.18, n=14):
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        dx, dy = b[0] - a[0], b[1] - a[1]
        cx, cy = mx - dy * bend, my + dx * bend
        return [((1 - u) ** 2 * a[0] + 2 * (1 - u) * u * cx + u * u * b[0],
                 (1 - u) ** 2 * a[1] + 2 * (1 - u) * u * cy + u * u * b[1]) for u in (k / n for k in range(n + 1))]

    # the origin: where the first spore landed, a small closed ring
    o0 = pos(START)
    ring = [(o0[0] + 4 * math.cos(2 * math.pi * k / 18), o0[1] + 4 * math.sin(2 * math.pi * k / 18)) for k in range(19)]
    s.line(ring, LINE, G4)

    for t, q, p in links:
        if p is None:
            continue
        a, b = pos(p), pos(q)
        pts = curve(a, b)
        if q in BORN and t == SNAP:
            continue
        if STATE[q] < 0:
            # dead: the trail has worn through in places, the gaps opening with decay
            s.dashed(pts, LINE, G3, 6 - 4 * DEF["decay"], 2 + 6 * DEF["decay"])
        else:
            s.line(pts, LINE, G5)
    # growing tips: from each live margin cell, short probes towards free neighbours (grow)
    for c in LIVE:
        for q in nbrs(*c):
            if q in FREE:
                a, b = pos(c), pos(q)
                L = 0.12 + 0.5 * g
                e = (a[0] + (b[0] - a[0]) * L, a[1] + (b[1] - a[1]) * L)
                s.line(curve(a, e, 0.1, 6), LINE, G3)
    # this tick's births: the one bright line
    for t, q, p in links:
        if t == SNAP and p is not None:
            s.line(curve(pos(p), pos(q)), LINE, G7)
    # spores: a closed contour where each will land, with its fall drawn in from above
    for c in SPORES:
        x, y = pos(c)
        ring = [(x + 3 * math.cos(2 * math.pi * k / 14), y + 3 * math.sin(2 * math.pi * k / 14)) for k in range(15)]
        s.line(ring, LINE, G4)
        s.dashed([(x, y - 24), (x, y - 6)], LINE, G3, 3, 3)
    s.save(HERE / "v3" / "rest.svg")


# =============================================================================
# v4 · hatched mass: one stretch of the margin at large scale
# =============================================================================
def v4():
    s = Svg()
    u = 66.0
    focus = (6, 3)

    def wx(X, Y):
        r = Y / RH
        return pc(X + 1.5 * r) - pc(1.5 * r)

    fx = wx(*hexc(*focus))
    fy = hexc(*focus)[1]

    def S(pt):
        X, Y = pt
        return (262 + (wx(X, Y) - fx) * u, 118 - (Y - fy) * u)

    def cellpoly(c, k=1.0):
        x, y = hexc(*c)
        return [S((x + (vx * k), y + (vy * k))) for vx, vy in HEXV]

    rng = random.Random(11)
    g = DEF["grow"]
    # bare stone: joints only
    for c in FREE:
        cp = cellpoly(c)
        for a, b in zip(cp, cp[1:] + cp[:1]):
            s.seg(a, b, HAIR, G2)
    # dead crust: the hatched mass the colony leaves at its centre
    for c in DEAD:
        cp = cellpoly(c, 0.97)
        s.poly(cp, fill=G0, stroke=G3, sw=HAIR)
        hatch_fixed(s, [clip_rect(cp)], G3, 4.0)
    # tongues: the margin pushing into free neighbours (grow)
    for c in LIVE:
        for q in nbrs(*c):
            if q not in FREE:
                continue
            ax, ay = hexc(*c)
            bx, by = hexc(*q)
            dx, dy = bx - ax, by - ay
            ln = math.hypot(dx, dy)
            ux, uy = dx / ln, dy / ln
            nx, ny = -uy, ux
            L = 0.42 + 0.62 * g
            wv = 0.2
            pts = []
            for k in range(13):
                tt = k / 12
                along = 0.36 + (L - 0.36) * math.sin(tt * math.pi) ** 0.6
                side = wv * math.cos(tt * math.pi)
                pts.append((ax + ux * along + nx * side, ay + uy * along + ny * side))
            sp = [S(p) for p in pts]
            s.poly(sp, fill=G0, stroke=G4, sw=LINE)
    # living crust: black bodies, cracked into areolae that multiply with age
    for c in sorted(LIVE):
        cp = cellpoly(c, 0.97)
        born = c in BORN
        s.poly(cp, fill=G0, stroke=G7 if born else G4, sw=SUBJ if born else LINE)
        a = STATE[c]
        cx = sum(p[0] for p in cp) / 6
        cy = sum(p[1] for p in cp) / 6
        ncr = min(5, 1 + a // 2)
        for k in range(ncr):
            i = (k * 2 + rng.randint(0, 1)) % 6
            m = ((cp[i][0] + cp[(i + 1) % 6][0]) / 2, (cp[i][1] + cp[(i + 1) % 6][1]) / 2)
            j = (cx + (rng.random() - 0.5) * 10, cy + (rng.random() - 0.5) * 10)
            mid = ((m[0] + j[0]) / 2 + rng.uniform(-3, 3), (m[1] + j[1]) / 2 + rng.uniform(-3, 3))
            p0 = (m[0] + (j[0] - m[0]) * 0.12, m[1] + (j[1] - m[1]) * 0.12)
            s.line([p0, mid, j], HAIR, G3)
    # spores on bare stone near the margin (seed)
    spots = [(8, 3), (8, 1), (7, 5), (9, 2), (8, 4), (3, 3), (9, 4), (7, 0)]
    for c in spots[:DEF["seed"]]:
        x, y = S(hexc(*c))
        s.disc(x + 9, y - 6, 2.6, fill=G5)
    s.save(HERE / "v4" / "rest.svg")


# =============================================================================
# v5 · edge-lit silhouette: the lichen itself, a foliose rosette on stone
# =============================================================================
def v5():
    s = Svg()
    cam = Cam((5.6, -6.2, 8.4), (5.6, 2.3, 0), 285, 240, 120)
    P = cam.p
    g = DEF["grow"]
    cen = (sum(hexc(*c)[0] for c in LIVE) / len(LIVE), sum(hexc(*c)[1] for c in LIVE) / len(LIVE))
    blobs = []
    for c in LIVE:
        x, y = hexc(*c)
        blobs.append((x, y, 0.5, 1.0))
        frees = [q for q in nbrs(*c) if q in FREE]
        for q in frees:
            bx, by = hexc(*q)
            dx, dy = bx - x, by - y
            for k, (t, sg) in enumerate(((0.32, 0.27), (0.5 + 0.2 * g, 0.2), (0.62 + 0.45 * g, 0.14))):
                blobs.append((x + dx * t, y + dy * t, sg, 0.75))
    holes = [hexc(*c) for c in DEAD]

    def field(x, y):
        v = 0.0
        for bx, by, sg, w in blobs:
            d2 = (x - bx) ** 2 + (y - by) ** 2
            if d2 < 9 * sg * sg:
                v += w * math.exp(-d2 / (sg * sg))
        for hx, hy in holes:
            d2 = (x - hx) ** 2 + (y - hy) ** 2
            if d2 < 1.2:
                v -= 0.95 * math.exp(-d2 / 0.13)
        return v

    loops = contours(field, -0.5, -0.8, 12.5, 5.6, step=0.05, level=0.55)
    # outward normal from the field gradient, light from the upper left of the screen
    L = (-0.55, -0.83)

    def outward(x, y):
        e = 0.02
        gx = field(x + e, y) - field(x - e, y)
        gy = field(x, y + e) - field(x, y - e)
        return (-gx, -gy)

    born_pts = [hexc(*c) for c in BORN]
    sl = []
    for lp in loops:
        lp = resample(lp, max(24, min(400, int(len(lp)))))
        scr = [P((x, y, 0.0)) for x, y in lp]
        mx, my = sum(p[0] for p in lp) / len(lp), sum(p[1] for p in lp) / len(lp)
        sl.append((lp, scr, abs(area(scr))))
    sl.sort(key=lambda t: -t[2])
    outer = [t for t in sl if not any(inpoly(t[1][0], o[1]) for o in sl if o is not t and o[2] > t[2])]
    inner = [t for t in sl if t not in outer]
    # thickness: the shadow edge under the lit edge, 3 px down
    for lp, scr, _ in outer:
        s.poly([(x, y + 3) for x, y in scr], fill=G0, stroke=G2, sw=HAIR)
        s.poly(scr, fill=G0, stroke=G2, sw=HAIR)
    # the dead centre: hatched, the old crust that's there but no longer living
    for lp, scr, _ in inner:
        s.poly(scr, fill=G0, stroke="none")
        hatch_fixed(s, [scr], G2, 4.0)
    # lobe ridges: one hairline down each lobe, tip to base
    for c in LIVE:
        x, y = hexc(*c)
        for q in nbrs(*c):
            if q in FREE:
                bx, by = hexc(*q)
                dx, dy = bx - x, by - y
                pts = [P((x + dx * t, y + dy * t, 0)) for t in (0.08, 0.3, 0.42 + 0.35 * g)]
                s.line(pts, HAIR, G3)
    # apothecia: fruiting cups on cells a half step below their neighbour (scale)
    for c in sorted(LIVE):
        if semitone_after(degree(*c)) and c not in BORN:
            x, y = hexc(*c)
            cup = [P((x + 0.17 * math.cos(2 * math.pi * k / 20), y + 0.17 * math.sin(2 * math.pi * k / 20), 0))
                   for k in range(20)]
            s.poly(cup, fill=G0, stroke=G4, sw=LINE)
            lit = [P((x + 0.11 * math.cos(math.radians(a)), y + 0.11 * math.sin(math.radians(a)), 0))
                   for a in range(200, 341, 20)]
            s.line(lit, HAIR, G5)
    # rims: lit where the edge faces the light, bright where a lobe was just born
    for group in (outer, inner):
        for lp, scr, _ in group:
            n = len(lp)
            cls = []
            for i in range(n):
                ox, oy = outward(*lp[i])
                a, b = scr[i - 1], scr[(i + 1) % n]
                tx, ty = b[0] - a[0], b[1] - a[1]
                # screen normal: pick the side the world outward normal projects to
                w0 = P((lp[i][0], lp[i][1], 0))
                w1 = P((lp[i][0] + ox * 0.05 / (math.hypot(ox, oy) or 1), lp[i][1] + oy * 0.05 / (math.hypot(ox, oy) or 1), 0))
                nx, ny = w1[0] - w0[0], w1[1] - w0[1]
                ln = math.hypot(nx, ny) or 1
                lit = (nx * L[0] + ny * L[1]) / ln
                near_born = any(math.dist(lp[i], bp) < 0.62 for bp in born_pts) and group is outer
                cls.append(3 if near_born else (2 if lit > 0.35 else (1 if lit > -0.2 else 0)))
            style = {3: (SUBJ, G7), 2: (LINE, G5), 1: (HAIR, G4), 0: None}
            i0 = next((i for i in range(n) if cls[i] != cls[i - 1]), 0)
            runs, cur = [], [i0]
            for k in range(1, n + 1):
                i = (i0 + k) % n
                if cls[i] == cls[cur[0]] and k < n:
                    cur.append(i)
                else:
                    cur.append(i)
                    runs.append((cls[cur[0]], cur))
                    cur = [i]
            for cl, idx in runs:
                st = style[cl]
                if st:
                    s.line([scr[i] for i in idx], st[0], st[1])
    # spores: released downwind of the rosette (seed)
    for k, c in enumerate(SPORES):
        x, y = hexc(*c)
        p = P((x, y, 0.0))
        s.disc(p[0], p[1], 1.8, fill=G4)
    s.save(HERE / "v5" / "rest.svg")


if __name__ == "__main__":
    for fn in (v1, v2, v3, v4, v5):
        fn()
    print("snapshot tick", SNAP, "live", len(LIVE), "dead", len(DEAD), "born", sorted(BORN), "spores", SPORES)
