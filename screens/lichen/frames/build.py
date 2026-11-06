#!/usr/bin/env python3
"""Lichen · refined v1 (stone block cut open under a lichen crust): frames.

    python3 screens/lichen/frames/build.py

Writes, next to this file:
  rest.svg/png                      defaults (grow 35, decay 20, seed 1, maj)
  <control>-0/-50/-100.svg/png      grow, decay, seed, scale, others at default
  before-after.png                  pass-02 v1 rest beside the refined rest, 1:1
  contact.png                       rest + every control's 0/50/100, 1:1
  motion.gif                        a few ticks of growth and decay, then still

and runs lint_frame.py and perceptibility.py on them (from a scratch folder
under frames/ that is deleted again at the end).

What changed from pass 02's sketch: the stone and the crust are solid bodies
lit from the upper left (tops lighter, walls darker, every face well below
the one bright element), the plates are rounded lobed areolae instead of
chamfered hexes, cracks are real black splits with a lit lip, spores are
solid grains with a shadow on the stone, and dead crust is hatched (black
body, mid-grey 45-degree hairlines) because it is there but inactive.

Everything 3D is modelled in world units (unit-wide hex cells, z up) and
projected through one camera (craft.md, Think in 3D). No text below the
header.
"""
from __future__ import annotations

import math
import random
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LICHEN = HERE.parent
REPO = LICHEN.parent.parent
W, H = 480, 220
TOP, BOT = 21.0, 216.0           # body band the drawing stays inside

SCALES = {"maj": [0, 2, 4, 5, 7, 9, 11], "min": [0, 2, 3, 5, 7, 8, 10], "dor": [0, 2, 3, 5, 7, 9, 10],
          "phr": [0, 1, 3, 5, 7, 8, 10], "lyd": [0, 2, 4, 6, 7, 9, 11], "mix": [0, 2, 4, 5, 7, 9, 10],
          "pent": [0, 2, 4, 7, 9], "pmin": [0, 3, 5, 7, 10]}
SCALE_NAMES = ["maj", "min", "dor", "phr", "lyd", "mix", "pent", "pmin"]
SEEDS = [0, 1, 2, 3, 4, 6, 8]
DEF = {"grow": 0.35, "decay": 0.2, "seed": 1, "scale": "maj"}
C, R = 12, 6
SNAP = 14
RNG_SEED = 282
START = (6, 2)
RH = math.sqrt(3) / 2

# palette (grey only; header steps plus one darker face)
G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
GE = "#1E1E1E"                   # the stone's end face, in shadow
HAIR, LINE, SUBJ = 1.0, 1.5, 2.2

STONE_TOP, STONE_CUT, STONE_END = G2, G1, GE
CRUST_TOP, CRUST_WALL = G5, G3
BORN_TOP, BORN_WALL = G7, G5
DEAD_EDGE, DEAD_HATCH, FLAKE_EDGE = G3, G3, G4
SPORE = G5


# --- colony model (same rule and seed as passes/01 and 02) -------------------
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


HIST, BIRTHS = run(ticks=SNAP + 3)


def degree(o, r):
    return o - r // 2 + 2 * r


def semitone_after(d, sc):
    n = len(sc)
    p = lambda k: sc[k % n] + 12 * (k // n)
    return p(d + 1) - p(d) == 1


def hexc(o, r):
    return (o + 0.5 * (r % 2), r * RH)


# --- geometry helpers --------------------------------------------------------
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
    def __init__(self, eye, at, f, cx, cy):
        self.e = eye
        self.fw = norm(sub(at, eye))
        self.rt = norm(cross(self.fw, (0, 0, 1)))
        self.up = cross(self.rt, self.fw)
        self.f, self.cx, self.cy = f, cx, cy

    def p(self, q):
        d = sub(q, self.e)
        k = self.f / dot(d, self.fw)
        return (self.cx + dot(d, self.rt) * k, self.cy - dot(d, self.up) * k)

    def dist(self, q):
        return dot(sub(q, self.e), self.fw)


def clip_half(poly, inside, cut):
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


def area(poly):
    return 0.5 * sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))


def hull(pts):
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in pts))
    if len(pts) < 3:
        return pts

    def half(seq):
        h = []
        for p in seq:
            while len(h) >= 2 and ((h[-1][0] - h[-2][0]) * (p[1] - h[-2][1])
                                   - (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0])) <= 0:
                h.pop()
            h.append(p)
        return h
    lo, up = half(pts), half(pts[::-1])
    return lo[:-1] + up[:-1]


def fmt(v):
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
    def __init__(self, values):
        self.o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
                  '  <g id="preview_canvas">',
                  f'    <rect x="0" y="0" width="{W}" height="{H}" fill="#000000" stroke="none"/>',
                  '  </g>',
                  '  <g id="preview_header">']
        for i, c in enumerate([G0, G1, G2, G3, G4, G5, G6, G7]):
            self.o.append(f'    <rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
        for i, (lab, val) in enumerate(zip(["grow", "decay", "seed", "scale"], values)):
            col = "#CBCBCB" if i < 2 else "#000000"
            self.o.append(f'    <text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{col}" stroke="none" '
                          f'font-family="UniversNextPro-Light" font-size="10px">{lab}</text>')
            self.o.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{col}" stroke="none" '
                          f'font-family="UniversNextPro-Light" font-size="20px">{val}</text>')
        self.o.append('  </g>')

    def poly(self, pts, fill="none", stroke="none", sw=None, clip=True, min_area=2.5):
        pts = clean(pts)
        if clip:
            cp = clean(clip_rect(pts))
            if stroke != "none" and len(cp) >= 3 and (len(cp) != len(pts) or any(
                    math.dist(a, b) > 0.01 for a, b in zip(cp, pts))):
                self.poly(cp, fill=fill, clip=False)
                self.line(pts + pts[:1], sw, stroke)
                return
            pts = cp
        if len(pts) < 3 or abs(area(pts)) < min_area:
            return
        if len(pts) > 64:
            pts = resample(pts, 64)
        d = "M " + " L ".join(f"{fmt(x)} {fmt(y)}" for x, y in pts) + " Z"
        s = f' stroke-width="{sw}"' if stroke != "none" else ""
        self.o.append(f'  <path d="{d}" fill="{fill}" stroke="{stroke}"{s}/>')

    def ribbon(self, pts, w, col, taper=None):
        """An open line as a thin closed ribbon (no traced strokes). taper=(w0, w1)."""
        pts = clean(pts, closed=False, gap=0.6)
        if len(pts) < 2:
            return
        if len(pts) > 30:
            for i in range(0, len(pts) - 1, 29):
                self.ribbon(pts[i:i + 30], w, col)
            return
        left, right = [], []
        n = len(pts)
        for i, p in enumerate(pts):
            a = pts[max(0, i - 1)]
            b = pts[min(n - 1, i + 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(dx, dy) or 1
            nx, ny = -dy / ln, dx / ln
            h = (taper[0] + (taper[1] - taper[0]) * i / (n - 1)) / 2 if taper else w / 2
            left.append((p[0] + nx * h, p[1] + ny * h))
            right.append((p[0] - nx * h, p[1] - ny * h))
        self.poly(left + right[::-1], fill=col, min_area=1.0)

    def seg(self, a, b, w, col):
        c = clip_seg(a, b)
        if c and math.dist(*c) > 3.0:
            self.ribbon(list(c), w, col)

    def line(self, pts, w, col):
        run_ = []
        for a, b in zip(pts, pts[1:]):
            c = clip_seg(a, b)
            if c is None:
                if len(run_) > 1:
                    self.ribbon(run_, w, col)
                run_ = []
                continue
            if run_ and math.dist(run_[-1], c[0]) < 0.01:
                run_.append(c[1])
            else:
                if len(run_) > 1:
                    self.ribbon(run_, w, col)
                run_ = [c[0], c[1]]
        if len(run_) > 1:
            self.ribbon(run_, w, col)

    def disc(self, cx, cy, rx, fill, ry=None, n=20):
        ry = rx if ry is None else ry
        self.poly([(cx + rx * math.cos(2 * math.pi * k / n), cy + ry * math.sin(2 * math.pi * k / n))
                   for k in range(n)], fill=fill)

    def text(self):
        return "\n".join(self.o + ["</svg>", ""])

    def save(self, path: Path):
        path.write_text(self.text(), encoding="utf-8")
        render(path, path.with_suffix(".png"))


def render(svg: Path, png: Path):
    subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H), "-b", "black", str(svg), "-o", str(png)],
                   check=True)


def hatch(s, poly, col=DEAD_HATCH, gap=4.0, w=HAIR, inset=0.8):
    """45-degree hairlines >= 4 px apart, clipped to a (screen) polygon."""
    if len(poly) < 3:
        return
    lo = min(x + y for x, y in poly)
    hi = max(x + y for x, y in poly)
    step = gap * math.sqrt(2)
    c = math.floor(lo / step) * step + step / 2
    while c <= hi:
        xs = []
        for a, b in zip(poly, poly[1:] + poly[:1]):
            sa, sb = a[0] + a[1], b[0] + b[1]
            if (sa - c) * (sb - c) < 0:
                t = (c - sa) / (sb - sa)
                xs.append(a[0] + (b[0] - a[0]) * t)
        xs.sort()
        for x1, x2 in zip(xs[0::2], xs[1::2]):
            # pull the ends in a touch so the hatch sits inside the edge line
            if x2 - x1 > 3 * inset:
                s.seg((x1 + inset, c - x1 - inset), (x2 - inset, c - x2 + inset), w, col)
        c += step


# --- the scene ---------------------------------------------------------------
CUT = 2 * RH                     # the section plane: through the start row
X0, X1 = 2.2, 9.8                # block ends (world x)
YB = 5 * RH + 0.5                # block back face
ZB = -0.78                       # block bottom
CAM = Cam((4.75, -9.0, 5.2), (5.95, 3.0, -0.25), 700, 236, 108)
P = CAM.p
LIGHT = (0.55, 0.45)             # shadow throw on the stone per unit of height (world x, y)


def plate_outline(o, r, live=frozenset(), n=48):
    """An areola on hex cell (o, r), world XY, CCW: a rounded, uneven plate.
    Sides that meet a living neighbour stay straight and close (a packed crust
    split by narrow cracks); sides at the margin bulge into rounded lobes,
    two to a side, the way a crustose lichen's edge does."""
    cx, cy = hexc(o, r)
    rng = random.Random(o * 31 + r * 7)
    ph = rng.random() * 6.28
    k = 0.9 + 0.05 * rng.random()
    cx += (rng.random() - 0.5) * 0.04
    cy += (rng.random() - 0.5) * 0.04
    dirs = {}
    for q in nbrs(o, r):
        qx, qy = hexc(*q)
        dirs[round(math.degrees(math.atan2(qy - hexc(o, r)[1], qx - hexc(o, r)[0])) / 60) % 6] = q in live
    pts = []
    for i in range(n):
        th = 2 * math.pi * i / n
        deg = math.degrees(th)
        side = round(deg / 60) % 6
        phi = (deg + 30) % 60 - 30
        if dirs.get(side, False):
            rr = 0.5 / math.cos(math.radians(phi)) ** 0.55
            rr *= 0.99 + 0.012 * math.sin(4 * th + ph)
        else:
            rr = 0.5 / math.cos(math.radians(phi)) ** 0.2
            rr *= 0.95 + 0.075 * math.cos(math.radians(phi) * 6) + 0.015 * math.sin(7 * th + ph)
        pts.append((cx + rr * k * math.cos(th), cy + rr * k * math.sin(th)))
    return pts


def thickness(age):
    """Crust thickness by age, in three steps (the device draws three wall variants)."""
    a = abs(age)
    return 0.13 if a <= 2 else (0.21 if a <= 5 else 0.29)


def keep_cut(poly):
    poly = clip_half(poly, lambda p: p[1] >= CUT - 1e-9,
                     lambda a, b: (a[0] + (b[0] - a[0]) * (CUT - a[1]) / (b[1] - a[1]), CUT))
    if poly:
        poly = clip_half(poly, lambda p: p[0] >= X0 + 0.04,
                         lambda a, b: (X0 + 0.04, a[1] + (b[1] - a[1]) * (X0 + 0.04 - a[0]) / (b[0] - a[0])))
    if poly:
        poly = clip_half(poly, lambda p: p[0] <= X1 - 0.04,
                         lambda a, b: (X1 - 0.04, a[1] + (b[1] - a[1]) * (X1 - 0.04 - a[0]) / (b[0] - a[0])))
    if poly:
        poly = clip_half(poly, lambda p: p[1] <= YB - 0.04,
                         lambda a, b: (a[0] + (b[0] - a[0]) * (YB - 0.04 - a[1]) / (b[1] - a[1]), YB - 0.04))
    return poly


def in_block(o, r):
    x, y = hexc(o, r)
    return r >= 2 and X0 - 0.3 < x < X1 + 0.3


def ys_at(poly, x):
    out = []
    for a, b in zip(poly, poly[1:] + poly[:1]):
        if (a[0] - x) * (b[0] - x) < 0 or (a[0] == x and b[0] != x):
            t = (x - a[0]) / (b[0] - a[0])
            out.append(a[1] + (b[1] - a[1]) * t)
    return out


def extrude(bp, tp):
    """Screen outline of a vertical extrusion: the top's upper edge and the
    base's lower edge, sampled across x (exact for these near-convex plates)."""
    x0 = min(p[0] for p in bp + tp) + 0.05
    x1 = max(p[0] for p in bp + tp) - 0.05
    n = max(4, int((x1 - x0) / 1.2))
    up, lo = [], []
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        yt, yb = ys_at(tp, x), ys_at(bp, x)
        if not yt and not yb:
            continue
        up.append((x, min(yt + yb)))
        lo.append((x, max(yt + yb)))
    return up + lo[::-1]


def solid(s, base, h, top, wall, z0=0.0):
    """A flat-topped body standing on the stone: walls, then top."""
    if len(base) < 3:
        return
    bp = [P((x, y, z0)) for x, y in base]
    tp = [P((x, y, z0 + h)) for x, y in base]
    s.poly(extrude(bp, tp), fill=wall, stroke=G0, sw=HAIR)
    s.poly(tp, fill=top, stroke=G0, sw=HAIR)


def scale_about(poly, k):
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    return [(cx + (x - cx) * k, cy + (y - cy) * k) for x, y in poly]


def tongue_outline(a, b, length):
    """A crust lobe from cell a towards free cell b: narrow at the root,
    widening to a blunt tip split into two rounded lobes, reaching `length`
    world units past a's plate edge. Thinner than the plates: the growing margin."""
    ax, ay = hexc(*a)
    bx, by = hexc(*b)
    dx, dy = bx - ax, by - ay
    ln = math.hypot(dx, dy)
    ux, uy, nx, ny = dx / ln, dy / ln, -dy / ln, dx / ln
    root, tip = 0.25, 0.44 + length
    w0, w1 = 0.12, 0.13 + 0.09 * min(1.0, length / 0.6)
    tipc = tip - w1 * 0.8
    side = []
    for i in range(7):
        t = i / 6
        side.append((root + (tipc - root) * t, w0 + (w1 - w0) * t ** 0.7))
    pts = [(u, v) for u, v in side]
    for i in range(1, 16):
        aa = math.radians(90 - 180 * i / 16)
        rad = w1 * (1 - 0.22 * math.exp(-(math.degrees(aa) / 18) ** 2))
        pts.append((tipc + 0.8 * rad * math.cos(aa), rad * math.sin(aa)))
    pts += [(u, -v) for u, v in side[::-1]]
    return [(ax + ux * u + nx * v, ay + uy * u + ny * v) for u, v in pts][::-1]


def flake_points(base, ang, h):
    """Dead crust: the whole areola, shrunk a little as it dries, lifted on a
    hinge along its back edge (front edge up, towards the viewer)."""
    cx = sum(p[0] for p in base) / len(base)
    cy = sum(p[1] for p in base) / len(base)
    pts = [(cx + (x - cx) * 0.86, cy + (y - cy) * 0.86) for x, y in base]
    hy = max(p[1] for p in pts)
    return [(x, hy + (y - hy) * math.cos(ang), h - (y - hy) * math.sin(ang)) for x, y in pts]


def scene(grow=DEF["grow"], decay=DEF["decay"], seed=DEF["seed"], scale="maj", tick=SNAP, phase=None):
    """One frame. phase=None is settled; 0..1 is the time since this tick's
    births, for the motion preview."""
    values = [str(round(grow * 100)), str(round(decay * 100)), str(seed), scale]
    s = Svg(values)
    st = HIST[tick]
    born = {q for q, _ in BIRTHS[tick]}
    prev_born = {q for q, _ in BIRTHS[tick - 1]} if tick > 0 else set()
    newly_dead = {k for k, a in st.items() if a == -5}
    live = {k for k, a in st.items() if a > 0}
    free = {k for k, a in st.items() if a == 0}
    sc = SCALES[scale]
    ease = (lambda t: 1 - math.exp(-t / 0.22)) if phase is not None else (lambda t: 1.0)
    e = ease(phase or 0)

    # --- the stone block: solid faces by their light ---
    end = [(X1, CUT, ZB), (X1, YB, ZB), (X1, YB, 0), (X1, CUT, 0)]
    top = [(X0, CUT, 0), (X1, CUT, 0), (X1, YB, 0), (X0, YB, 0)]
    front = [(X0, CUT, ZB), (X1, CUT, ZB), (X1, CUT, 0), (X0, CUT, 0)]
    s.poly([P(q) for q in end], fill=STONE_END)
    s.poly([P(q) for q in top], fill=STONE_TOP)
    s.poly([P(q) for q in front], fill=STONE_CUT)

    # half-step joints along the cut row: the stone is split there (scale)
    joints = [hexc(o, 2)[0] + 0.5 for o in range(C - 1) if semitone_after(degree(o, 2), sc)]
    joints = [x for x in joints if X0 + 0.25 < x < X1 - 0.25]

    # bedding in the cut face: two calm hairlines, broken at the cracks
    for k, z in enumerate((-0.36, -0.6)):
        xs = [X0 + 0.12 + 0.05 * k + 0.02 * i for i in range(int((X1 - X0 - 0.3) / 0.02))]
        run_ = []
        for x in xs:
            if any(abs(x - j) < 0.1 for j in joints):
                if len(run_) > 1:
                    s.line(run_, HAIR, G2)
                run_ = []
                continue
            run_.append(P((x, CUT, z + 0.03 * math.sin(x * 1.7 + k * 2.1))))
        if len(run_) > 1:
            s.line(run_, HAIR, G2)

    cracks = {}
    for jx in joints:
        rng = random.Random(int(jx * 100))
        # down the cut face, the full height: an open wedge, wide at the top
        zs = [0, -0.2, -0.4, -0.6, ZB]
        xs = [jx] + [jx + (rng.random() - 0.5) * 0.1 for _ in zs[1:]]
        wd = [0.11, 0.085, 0.065, 0.045, 0.03]
        left = [P((x - w, CUT, z)) for x, z, w in zip(xs, zs, wd)]
        right = [P((x + w, CUT, z)) for x, z, w in zip(xs, zs, wd)]
        s.poly(left + right[::-1], fill=G0)
        s.line(right, HAIR, G4)               # the lit lip of the break
        # back across the top: the same split, narrowing to the back face
        ys = [CUT + (YB - CUT) * i / 6 for i in range(7)]
        xt = [jx] + [jx + (rng.random() - 0.5) * 0.14 for _ in ys[1:]]
        wt = [0.11 - 0.06 * i / 6 for i in range(7)]
        left = [P((x - w, y, 0)) for x, y, w in zip(xt, ys, wt)]
        right = [P((x + w, y, 0)) for x, y, w in zip(xt, ys, wt)]
        s.poly(left + right[::-1], fill=G0)
        s.line(right, HAIR, G4)
        cracks[jx] = list(zip(xt, ys, wt))

    # the block's lit arris and silhouette: crisp edges where faces meet black
    s.line([P((X0, CUT, 0)), P((X1, CUT, 0))], LINE, G4)
    s.line([P((X0, CUT, ZB)), P((X0, CUT, 0)), P((X0, YB, 0)), P((X1, YB, 0))], HAIR, G3)
    s.line([P((X1, CUT, ZB)), P((X1, YB, ZB)), P((X1, YB, 0))], HAIR, G3)
    s.line([P((X0, CUT, ZB)), P((X1, CUT, ZB))], HAIR, G3)
    s.line([P((X1, CUT, ZB)), P((X1, CUT, 0))], HAIR, G3)

    # --- the crust ---
    items = []
    for (o, r), a in st.items():
        if a == 0 or not in_block(o, r):
            continue
        base = keep_cut(plate_outline(o, r, frozenset(live)))
        if len(base) < 3:
            continue
        cx, cy = hexc(o, r)
        items.append((CAM.dist((cx, max(cy, CUT), 0)), "cell", (o, r), base, a))
    # tongues: one per free cell at the margin, from one living neighbour
    L = 0.85 * grow ** 0.7
    used = {}
    if L > 0.04:
        for q in sorted(free):
            if not in_block(*q):
                continue
            src = [k for k in nbrs(*q) if k in live and in_block(*k)]
            src = [k for k in src if used.get(k, 0) < 2]
            if not src:
                continue
            k = min(src, key=lambda c: (abs(hexc(*c)[1] - hexc(*q)[1]), c))
            used[k] = used.get(k, 0) + 1
            Lk = L * (e if k in born else 1)
            poly = keep_cut(tongue_outline(k, q, Lk))
            if len(poly) >= 3:
                mx = sum(p[0] for p in poly) / len(poly)
                my = sum(p[1] for p in poly) / len(poly)
                items.append((CAM.dist((mx, my, 0)) + 100, "tongue", k, poly, 1))
    items.sort(key=lambda t: -t[0])

    # shadows first: they lie on the stone, under everything standing on it
    for _, kind, c, base, a in items:
        if a > 0:
            h = thickness(a) if kind == "cell" else 0.07
            if kind == "cell" and c in born:
                h *= e
                base = scale_about(base, 0.55 + 0.45 * e)
            sh = [(x + LIGHT[0] * h, y + LIGHT[1] * h) for x, y in base]
            s.poly(hull([P((x, y, 0)) for x, y in base + sh]), fill=G0)

    for _, kind, (o, r), base, a in items:
        if area(base) < 0:
            base = base[::-1]
        cx, cy = hexc(o, r)
        if kind == "tongue":
            hb = (o, r) in born
            solid(s, base, 0.06, BORN_TOP if hb and phase is not None and e < 0.6 else CRUST_TOP,
                  CRUST_WALL)
            continue
        if a > 0:
            b = (o, r) in born
            h = thickness(a)
            topc, wallc = CRUST_TOP, CRUST_WALL
            if b:
                topc, wallc = BORN_TOP, BORN_WALL
                h *= e
                base = scale_about(base, 0.55 + 0.45 * e)
            elif phase is not None and (o, r) in prev_born and e < 0.5:
                topc, wallc = G6, G4          # last tick's growth, dimming
            solid(s, base, max(h, 0.02), topc, wallc)
            # the crust splits where the stone under it is split (scale)
            for jx, path in cracks.items():
                xs_ = [p[0] for p in base]
                if not (min(xs_) + 0.05 < jx < max(xs_) - 0.05):
                    continue
                ys_ = sorted(ys_at(base, jx))
                if len(ys_) < 2:
                    continue
                ya, yb = ys_[0] + 0.01, ys_[-1] - 0.01
                pts = [(x, y, w) for x, y, w in path if ya <= y <= yb]
                pts = [(jx, ya, 0.1)] + pts + [(pts[-1][0] if pts else jx, yb, 0.07)]
                left = [P((x - w * 0.7, y, h)) for x, y, w in pts]
                right = [P((x + w * 0.7, y, h)) for x, y, w in pts]
                s.poly(left + right[::-1], fill=G0)
                if ya <= CUT + 1e-6:          # and down the crust's own cut face
                    x = jx
                    s.poly([P((x - 0.07, CUT, h)), P((x + 0.07, CUT, h)), P((x + 0.05, CUT, 0)),
                            P((x - 0.05, CUT, 0))], fill=G0)
            if r == 2:                       # the section: crust layers and rhizines
                xs = [x for x, y in base if abs(y - CUT) < 1e-6]
                if len(xs) >= 2:
                    xa, xb = min(xs) + 0.02, max(xs) - 0.02
                    cort = min(0.06, h * 0.4)
                    s.poly([P((xa, CUT, 0)), P((xb, CUT, 0)), P((xb, CUT, h - cort)), P((xa, CUT, h - cort))],
                           fill=BORN_WALL if b else CRUST_WALL)
                    s.poly([P((xa, CUT, h - cort)), P((xb, CUT, h - cort)), P((xb, CUT, h)), P((xa, CUT, h))],
                           fill=BORN_TOP if b else CRUST_TOP)
                    nrh = int((xb - xa) / 0.13)
                    for i in range(nrh):
                        x = xa + (xb - xa) * (i + 0.5) / nrh
                        dz = 0.14 + 0.05 * ((i * 7) % 3) / 2
                        s.line([P((x, CUT, -0.005)), P((x + 0.02, CUT, -dz * 0.5)), P((x - 0.01, CUT, -dz))],
                               HAIR, G3)
        else:
            # dead crust: the areola dries and lifts off as a hatched flake, hinged at
            # its back; the stone it sat on is left as a dark scar
            s.poly([P((x, y, 0)) for x, y in base], fill=G0, stroke=DEAD_EDGE, sw=HAIR)
            ang_full = math.radians(12 + 66 * decay ** 0.8)
            ang = ang_full * (e if (o, r) in newly_dead else 1)
            fp = [P(q) for q in flake_points(base, ang, 0.03)]
            s.poly(fp, fill=G0, stroke=FLAKE_EDGE, sw=LINE)
            hatch(s, clean(fp), inset=1.6)

    # spores (seed): solid grains hanging over bare stone, each over its shadow
    for c in spore_cells()[:seed]:
        x, y = hexc(*c)
        sh = [P((x + 0.15 * math.cos(t), y + 0.15 * math.sin(t), 0))
              for t in [2 * math.pi * k / 18 for k in range(18)]]
        s.poly(sh, fill=G0)
        g = P((x, y, 0.36))
        rr = 0.105 * CAM.f / CAM.dist((x, y, 0.36))
        s.disc(g[0], g[1], rr, fill=SPORE)
    return s


def spore_cells():
    """Where the bar's spores will land: bare cells on the stone, spread out,
    fixed order so seed adds grains rather than moving them."""
    st = HIST[SNAP]
    return [c for c in [(9, 4), (3, 5), (8, 2), (4, 3), (9, 5), (2, 4), (5, 5), (7, 4)]
            if st[c] == 0]


# --- outputs ---------------------------------------------------------------
CONTROLS = ["grow", "decay", "seed", "scale"]
SCORES = [5, 4, 2, 3]


def control_value(name, v):
    if name in ("grow", "decay"):
        return v / 100
    if name == "seed":
        return SEEDS[round(v / 100 * (len(SEEDS) - 1))]
    return SCALE_NAMES[round(v / 100 * (len(SCALE_NAMES) - 1) + 1e-9)] if v != 50 else "lyd"


def frame_for(name=None, v=None, **kw):
    args = dict(DEF)
    if name:
        args[name] = control_value(name, v)
    args.update(kw)
    return scene(args["grow"], args["decay"], args["seed"], args["scale"],
                 kw.get("tick", SNAP), kw.get("phase"))


def black_share(png: Path):
    from PIL import Image
    im = Image.open(png).convert("L")
    px = im.load()
    n = blk = 0
    for y in range(21, H):
        for x in range(W):
            n += 1
            blk += px[x, y] < 12
    return blk / n


def main():
    for p in HERE.glob("*.svg"):
        p.unlink()
    for p in HERE.glob("*.png"):
        p.unlink()
    frames = {"rest": frame_for()}
    for name in CONTROLS:
        for v in (0, 50, 100):
            frames[f"{name}-{v}"] = frame_for(name, v)
    for stem, svg in frames.items():
        svg.save(HERE / f"{stem}.svg")

    # lint every frame
    lint = subprocess.run([sys.executable, str(REPO / "opxy/tools/lint_frame.py"),
                           *[str(HERE / f"{k}.svg") for k in frames],
                           "--definition", str(LICHEN / "definition.json")],
                          capture_output=True, text=True)
    print(lint.stdout.strip().splitlines()[-1] if lint.stdout.strip() else lint.stderr)
    (HERE / "_lint.txt").write_text(lint.stdout + lint.stderr)

    # scratch copies under the device naming, for perceptibility and the contact sheet
    scratch = HERE / "_scratch"
    if scratch.exists():
        shutil.rmtree(scratch)
    scratch.mkdir()
    (scratch / "rest.svg").write_text(frames["rest"].text())
    (scratch / "playing.svg").write_text(frame_for(tick=SNAP + 1, phase=0.08).text())
    for i, name in enumerate(CONTROLS, 1):
        for v in (0, 50, 100):
            (scratch / f"c{i}-{v:03d}.svg").write_text(frames[f"{name}-{v}"].text())
    per = subprocess.run([sys.executable, str(REPO / "opxy/tools/perceptibility.py"), str(scratch),
                          "--scores", ",".join(map(str, SCORES)), "--names", ",".join(CONTROLS)],
                         capture_output=True, text=True)
    print(per.stdout + per.stderr)
    (HERE / "_perceptibility.txt").write_text(per.stdout + per.stderr)

    # contact sheet: rest, then one row per control (playing left out: not a deliverable)
    (scratch / "playing.svg").unlink()
    subprocess.run([sys.executable, str(REPO / "opxy/tools/contact_sheet.py"), str(scratch),
                    "--out", str(scratch / "contact.svg"), "--png"], check=True, capture_output=True)
    shutil.copy(scratch / "contact.png", HERE / "contact.png")

    # before / after at 1:1
    from PIL import Image
    before = Image.open(LICHEN / "passes/02-subject/v1/rest.png").convert("RGB")
    after = Image.open(HERE / "rest.png").convert("RGB")
    ba = Image.new("RGB", (W * 2 + 16, H), (22, 22, 22))
    ba.paste(before, (0, 0))
    ba.paste(after, (W + 16, 0))
    ba.save(HERE / "before-after.png")

    # motion preview: a few ticks of growth and decay, then still on the rest frame
    imgs, delays = [], []
    tick_ms, step_ms = 400, 40
    for t in range(SNAP - 4, SNAP + 1):
        for k in range(tick_ms // step_ms):
            ph = k * step_ms / 1000
            svg = scratch / "m.svg"
            svg.write_text(frame_for(tick=t, phase=ph).text())
            render(svg, scratch / "m.png")
            imgs.append(Image.open(scratch / "m.png").convert("RGB"))
            delays.append(step_ms)
    imgs.append(Image.open(HERE / "rest.png").convert("RGB"))
    delays.append(2000)
    pal = [im.convert("P", palette=Image.ADAPTIVE, colors=32) for im in imgs]
    pal[0].save(HERE / "motion.gif", save_all=True, append_images=pal[1:], duration=delays, loop=0,
                optimize=False, disposal=1)

    # node-change estimate from the motion: count changed cells per tick is in refine.md
    print("black share rest:", round(black_share(HERE / "rest.png"), 3))
    for k in frames:
        print(k, "black", round(black_share(HERE / f"{k}.png"), 3))
    shutil.rmtree(scratch)


if __name__ == "__main__":
    main()
