#!/usr/bin/env python3
"""Rain, subject pass 03: the whole screen is a window pane in the rain.

Owner's direction: raindrops on the side of a window, the entire screen is the
window, you see the rain run down and collect into drops that then fall. Five
ways into that one window, one per direction in pass.json:

    v1  the trail a run leaves (mark or trace)     bold closed outlines
    v2  the pane's cut edge, a bead in profile     cutaway section
    v3  a heavy bead and the drops it gathered     exploded view
    v4  one heavy bead about to go, close          single-weight contour
    v5  the rain itself: drops on the glass        hatched mass

    python3 screens/rain/passes/03-subject/sketch.py            rest frames
    python3 screens/rain/passes/03-subject/sketch.py --motion   + vN/motion.gif

One model for all five (Pane, below): a drop lands at the height of its note
(higher on the glass = higher note) inside the band the roof span sets; beads
that touch merge; a bead heavier than the puddle's hold breaks away and runs
down, drifting with the gust, swallowing the beads in its path (each swallowed
bead is a note the puddle plays again) and leaving a wiped trail. Every bead is
a spherical cap on the glass (base radius a, height h, sagging downward),
modelled in world units and projected through one camera per variant (craft.md,
Think in 3D). No text below the header; grey only; lines are closed ribbons.
"""
from __future__ import annotations

import math
import random
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

DEFAULTS = {"rate": 0.4, "roof": 1 / 3, "gust": 0.5, "puddle": 0.0}
# motion clips: the defaults with a little gust and some puddle so a run forms
MOTION = {"rate": 0.4, "roof": 1 / 3, "gust": 0.6, "puddle": 0.35}

G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
GREYS = [G0, G1, G2, G3, G4, G5, G6, G7]
FONT = "UniversNextPro-Light"
SCALE = [0, 2, 4, 5, 7, 9, 11]
HAIR, LINE, SUBJ = 1.0, 1.5, 2.5
TOP = 21.0


def f(v: float) -> str:
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def settings(c):
    rate = 0.25 * 32 ** c["rate"]
    span = 36 * c["roof"]
    gust = 2 * c["gust"] - 1
    vals = [f"{rate:.1f}", f"{span:.0f}", "0" if abs(gust) < 0.005 else f"{gust * 100:+.0f}",
            f"{c['puddle'] * 100:.0f}"]
    return rate, span, gust, c["puddle"], vals


def courses(span):
    out, o = [], 0
    while True:
        for d in SCALE:
            st = 12 * o + d
            if st > span + 1e-6:
                return out
            out.append(st)
        o += 1


# ---------------------------------------------------------------- vectors / camera
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def mul(a, k): return (a[0] * k, a[1] * k, a[2] * k)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def norm(a):
    l = math.sqrt(dot(a, a)) or 1.0
    return (a[0] / l, a[1] / l, a[2] / l)


class Camera:
    """Look-at pinhole camera, world y up. The pane is the plane z = 0, the rain side
    faces +z. fit() scales and centres so key points land in a screen box."""

    def __init__(self, eye, target):
        self.eye = eye
        self.fwd = norm(sub(target, eye))
        self.right = norm(cross(self.fwd, (0, 1, 0)))
        self.up = cross(self.right, self.fwd)
        self.focal, self.cx, self.cy = 1.0, 0.0, 0.0

    def depth(self, p):
        return dot(sub(p, self.eye), self.fwd)

    def __call__(self, p):
        v = sub(p, self.eye)
        z = dot(v, self.fwd)
        return (self.cx + self.focal * dot(v, self.right) / z,
                self.cy - self.focal * dot(v, self.up) / z)

    def fit(self, pts, box):
        x0, y0, x1, y1 = box
        self.focal, self.cx, self.cy = 1.0, 0.0, 0.0
        sp = [self(p) for p in pts]
        sx0, sx1 = min(p[0] for p in sp), max(p[0] for p in sp)
        sy0, sy1 = min(p[1] for p in sp), max(p[1] for p in sp)
        k = min((x1 - x0) / (sx1 - sx0), (y1 - y0) / (sy1 - sy0))
        self.focal = k
        self.cx = (x0 + x1) / 2 - k * (sx0 + sx1) / 2
        self.cy = (y0 + y1) / 2 - k * (sy0 + sy1) / 2
        return self

    def pin(self, world, screen):
        """Shift the projection so a world point lands on a screen point."""
        p = self(world)
        self.cx += screen[0] - p[0]
        self.cy += screen[1] - p[1]
        return self


# ---------------------------------------------------------------- 2D helpers
def dedupe(pts, close=True):
    out = []
    for p in pts:
        p = (round(p[0], 3), round(p[1], 3))
        if not out or math.dist(out[-1], p) >= 0.2:
            out.append(p)
    if close and len(out) > 2 and math.dist(out[0], out[-1]) < 0.3:
        out.pop()
    return out


def clip_poly(pts, x0=0.0, y0=TOP, x1=480.0, y1=220.0):
    def clip(poly, inside, cut):
        out = []
        for i in range(len(poly)):
            a, b = poly[i - 1], poly[i]
            ia, ib = inside(a), inside(b)
            if ib:
                if not ia:
                    out.append(cut(a, b))
                out.append(b)
            elif ia:
                out.append(cut(a, b))
        return out

    def cx(v):
        return lambda a, b: (v, a[1] + (b[1] - a[1]) * (v - a[0]) / (b[0] - a[0]))

    def cy(v):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (v - a[1]) / (b[1] - a[1]), v)

    for inside, cut in ((lambda p: p[0] >= x0, cx(x0)), (lambda p: p[0] <= x1, cx(x1)),
                        (lambda p: p[1] >= y0, cy(y0)), (lambda p: p[1] <= y1, cy(y1))):
        if not pts:
            return []
        pts = clip(pts, inside, cut)
    return pts


def point_in(p, poly):
    c = False
    for i in range(len(poly)):
        a, b = poly[i - 1], poly[i]
        if (a[1] > p[1]) != (b[1] > p[1]):
            x = a[0] + (p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if x > p[0]:
                c = not c
    return c


def seg_in_poly(a, b, poly):
    ts = [0.0, 1.0]
    for i in range(len(poly)):
        p, q = poly[i - 1], poly[i]
        d1 = (b[0] - a[0], b[1] - a[1])
        d2 = (q[0] - p[0], q[1] - p[1])
        den = d1[0] * d2[1] - d1[1] * d2[0]
        if abs(den) < 1e-9:
            continue
        t = ((p[0] - a[0]) * d2[1] - (p[1] - a[1]) * d2[0]) / den
        u = ((p[0] - a[0]) * d1[1] - (p[1] - a[1]) * d1[0]) / den
        if 0 <= t <= 1 and 0 <= u <= 1:
            ts.append(t)
    ts.sort()
    out = []
    for t0, t1 in zip(ts, ts[1:]):
        m = (t0 + t1) / 2
        pm = (a[0] + (b[0] - a[0]) * m, a[1] + (b[1] - a[1]) * m)
        if t1 - t0 > 1e-6 and point_in(pm, poly):
            out.append(((a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0),
                        (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)))
    return out


def hull(pts):
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in pts))
    if len(pts) < 3:
        return pts

    def half(ps):
        h = []
        for p in ps:
            while len(h) >= 2 and ((h[-1][0] - h[-2][0]) * (p[1] - h[-2][1]) -
                                   (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0])) <= 0:
                h.pop()
            h.append(p)
        return h
    lo, hi = half(pts), half(pts[::-1])
    return lo[:-1] + hi[:-1]


def resample(pts, n):
    if len(pts) <= n:
        return pts
    return [pts[round(k * (len(pts) - 1) / (n - 1))] for k in range(n)]


def even(pts, step):
    """Resample a polyline at an even arc-length step."""
    if len(pts) < 2:
        return list(pts)
    out, acc = [pts[0]], 0.0
    for a, b in zip(pts, pts[1:]):
        d = math.dist(a, b)
        while acc + d >= step and d > 0:
            t = (step - acc) / d
            a = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            out.append(a)
            d = math.dist(a, b)
            acc = 0.0
        acc += d
    if math.dist(out[-1], pts[-1]) > step * 0.3:
        out.append(pts[-1])
    return out


# ---------------------------------------------------------------- frame
class Frame:
    def __init__(self, title, values):
        self.title, self.values = title, values
        self.items = []

    def add(self, s):
        self.items.append(s)

    def poly(self, pts, fill, stroke="none", sw=0.0, clip=True):
        pts = dedupe(clip_poly(list(pts)) if clip else list(pts))
        if len(pts) < 3:
            return
        if len(pts) > 64:
            pts = resample(pts, 64)
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        if max(xs) - min(xs) < 3 and max(ys) - min(ys) < 3:
            return
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
        sws = f' stroke-width="{f(sw)}"' if stroke != "none" else ' stroke-width="0"'
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def outline(self, pts, colour, sw, fill=G0):
        self.poly(pts, fill, colour, sw)

    def ribbon(self, pts, w, colour):
        pts = dedupe(pts, close=False)
        n, i = 26, 0
        while i < len(pts) - 1:
            self._piece(pts[i:i + n + 1], w, colour)
            i += n

    def _piece(self, seg, w, colour):
        if len(seg) < 2:
            return
        h = w / 2
        left, right = [], []
        for k, (x, y) in enumerate(seg):
            if k == 0:
                dx, dy = seg[1][0] - x, seg[1][1] - y
            elif k == len(seg) - 1:
                dx, dy = x - seg[k - 1][0], y - seg[k - 1][1]
            else:
                ax, ay = x - seg[k - 1][0], y - seg[k - 1][1]
                bx, by = seg[k + 1][0] - x, seg[k + 1][1] - y
                la, lb = math.hypot(ax, ay) or 1, math.hypot(bx, by) or 1
                dx, dy = ax / la + bx / lb, ay / la + by / lb
            ln = math.hypot(dx, dy) or 1
            nx, ny = -dy / ln, dx / ln
            left.append((x + nx * h, y + ny * h))
            right.append((x - nx * h, y - ny * h))
        self.poly(left + right[::-1], colour)

    def line(self, a, b, w, colour):
        self._piece([a, b], w, colour)

    def hatch(self, region, colour=G3, gap=4.0, w=HAIR, minlen=3.0):
        """45 deg hairlines across a closed region, gap px apart, clipped to it."""
        region = clip_poly(region)
        if len(region) < 3:
            return
        xs, ys = [p[0] for p in region], [p[1] for p in region]
        lo, hi = min(xs) + min(ys), max(xs) + max(ys)
        c = lo + gap / 2
        while c < hi:
            a = (c - max(ys) - 2, max(ys) + 2)
            b = (c - min(ys) + 2, min(ys) - 2)
            for p, q in seg_in_poly(a, b, region):
                if math.dist(p, q) >= minlen:
                    self.line(p, q, w, colour)
            c += gap * math.sqrt(2)

    def svg(self):
        head = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
            f"  <title>rain · subject pass 03 · {self.title}</title>",
            '  <g id="preview_canvas">',
            '    <rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>',
            "  </g>",
            '  <g id="preview_header">',
        ]
        for i, c in enumerate(GREYS):
            head.append(f'    <rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
        for i, lab in enumerate(["rate", "roof", "gust", "puddle"]):
            c = "#CBCBCB" if i < 2 else "#000000"
            head.append(f'    <text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{c}" stroke="none" '
                        f'font-family="{FONT}" font-size="10px">{lab}</text>')
        for i, v in enumerate(self.values):
            c = "#CBCBCB" if i < 2 else "#000000"
            head.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{c}" stroke="none" '
                        f'font-family="{FONT}" font-size="20px">{v}</text>')
        head.append("  </g>")
        return "\n".join(head + ["  " + s for s in self.items] + ["</svg>", ""])


# ================================================================ the pane model
class Bead:
    __slots__ = ("x", "y", "r", "t", "lit", "res", "id", "tail")

    def __init__(self, x, y, r, t, res=False, tail=None):
        self.x, self.y, self.r, self.t = x, y, r, t
        self.lit, self.res, self.tail = False, res, tail
        self.id = None


class Run:
    def __init__(self, b, t):
        self.x, self.y, self.r, self.t0 = b.x, b.y, b.r, t
        self.trail = [(b.x, b.y)]
        self.widths = [b.r]
        self.lit, self.flash, self.acc = b.lit, t, 0.0
        self.done = False
        self.phase = (b.x * 0.37) % 6.28


class Pane:
    """World units: x right, y up, the glass is z = 0. A drop's height is its note."""

    def __init__(self, W, H, c, seed, r_land, yc=0.6, band=0.3, speed=110.0, residue=None,
                 hold=(1.9, 3.2)):
        self.W, self.H = W, H
        self.rate, self.span, self.gust, self.puddle, _ = settings(c)
        self.rng = random.Random(seed)
        self.r_land = r_land
        self.yc, self.band = yc * H, band * H
        # puddle is how much the glass holds before a bead lets go
        self.r_break = r_land[1] * (hold[0] + (hold[1] - hold[0]) * self.puddle)
        self.speed = speed
        self.residue = residue if residue is not None else r_land[0] * 0.62
        self.beads: list[Bead] = []
        self.runs: list[Run] = []
        self.trails: list[Run] = []
        self.events: list[tuple] = []
        self.serial = 0

    def pitch_y(self, st):
        if self.span < 1e-6:
            return self.yc
        half = self.band * self.span / 36
        return self.yc + (st / self.span - 0.5) * 2 * half

    def _new(self, b):
        self.serial += 1
        b.id = self.serial
        self.beads.append(b)
        return b

    def land(self, t, st=None, x=None, r=None):
        cs = courses(self.span) or [0]
        st = self.rng.choice(cs) if st is None else st
        y = self.pitch_y(st) + self.rng.uniform(-1, 1) * self.r_land[0] * 0.5
        if x is None:
            x = self.rng.uniform(0.03, 0.97) * self.W
        r = self.rng.uniform(*self.r_land) if r is None else r
        for b in self.beads:
            b.lit = False
        for run in self.runs:
            run.lit = False
        b = self._new(Bead(x, y, r, t, tail=(self.gust, 1.0)))
        b.lit = True
        self.events.append(("land", t, b.x, b.y))
        self._merge(b, t)
        return b

    def _merge(self, b, t):
        while True:
            hit = [o for o in self.beads if o is not b and math.dist((o.x, o.y), (b.x, b.y)) < (o.r + b.r) * 0.9]
            if not hit:
                break
            for o in hit:
                v0, v1 = b.r ** 3, o.r ** 3
                b.x = (b.x * v0 + o.x * v1) / (v0 + v1)
                b.y = (b.y * v0 + o.y * v1) / (v0 + v1)
                b.r = (v0 + v1) ** (1 / 3)
                b.lit = b.lit or o.lit
                b.res = False
                self.beads.remove(o)
        if b.r > self.r_break:
            self.beads.remove(b)
            run = Run(b, t)
            self.runs.append(run)
            self.events.append(("break", t, b.x, b.y))

    def step(self, t, dt):
        for run in list(self.runs):
            age = t - run.t0
            v = self.speed * min(1.0, 0.35 + age * 3.0)
            dy = v * dt
            run.y -= dy
            run.x += (self.gust * 0.55 + 0.25 * math.sin(run.y * 0.045 + run.phase)) * dy
            run.acc += dy
            if math.dist(run.trail[-1], (run.x, run.y)) >= 1.5:
                run.trail.append((run.x, run.y))
                run.widths.append(run.r)
            if run.acc > run.r * 3.2:   # leave a bead behind in the trail
                run.acc = 0.0
                rr = self.residue
                if run.r > rr * 1.6:
                    self._new(Bead(run.x + self.rng.uniform(-0.3, 0.3) * run.r, run.y + run.r * 1.6, rr, t, res=True))
                    run.r = max(rr, (run.r ** 3 - rr ** 3 * 0.5) ** (1 / 3))
            for o in list(self.beads):
                if o.res and o.t >= run.t0:
                    continue
                if math.dist((o.x, o.y), (run.x, run.y)) < run.r + o.r * 0.9:
                    run.r = (run.r ** 3 + o.r ** 3 * 0.85) ** (1 / 3)
                    run.lit = run.lit or o.lit
                    self.beads.remove(o)
                    run.flash = t
                    self.events.append(("echo", t, run.x, run.y))
            if run.y < run.r * 1.25 + 1:
                run.y = run.r * 1.25 + 1
                run.done = True
                self.runs.remove(run)
                self.trails.append(run)
                self.trails = self.trails[-4:]
                b = self._new(Bead(run.x, run.y, run.r, t))
                b.lit = run.lit

    def settle(self, t):
        while self.runs:
            self.step(t, 1 / 60)
            t += 1 / 60
        return t

    def history(self, n):
        t = 0.0
        for _ in range(n):
            t += self.rng.expovariate(self.rate * 2)
            self.land(t)
            t = self.settle(t)
        return t


def score(c, t0, t1, seed):
    """Note times for a clip: Poisson at rate drops a beat, 120 bpm."""
    rng = random.Random(seed)
    rate, *_ = settings(c)
    out, t = [], t0
    while True:
        t += max(0.22, rng.expovariate(rate * 2))
        if t > t1:
            return out
        out.append(t)


# ================================================================ cap geometry
def cap_point(b, rho, th, h_k=0.55, sag=None, lean=None):
    """A bead as a sagging spherical cap: base radius a = r, height h, the lower half of
    the footprint stretched by sag, the apex leaning down by lean (gravity)."""
    a = b.r
    sag = (0.12 + 0.3 * min(1.0, a / 12)) if sag is None else sag
    lean = a * 0.18 if lean is None else lean
    s = math.sin(th)
    y = b.y + a * rho * s * (1 + sag * max(0.0, -s)) - lean * (1 - rho * rho)
    x = b.x + a * rho * math.cos(th)
    return (x, y, a * h_k * (1 - rho * rho))


def cap_outline(cam, b, n=40, **kw):
    pts = [cam(cap_point(b, rho, 2 * math.pi * k / n, **kw)) for rho in (1.0, 0.8, 0.55, 0.3) for k in range(n)]
    return resample(hull(pts), 60)


def footprint(cam, b, rho=1.0, n=44, **kw):
    return [cam(cap_point(b, rho, 2 * math.pi * k / n, **kw)) for k in range(n)]


def lane(cam, run, wk=0.8, step=3.0):
    """The wiped trail as a closed outline: the run's path, each side offset by its width."""
    pts = [(x, y) for x, y in run.trail]
    if len(pts) < 2:
        return []
    c = even([cam((x, y, 0)) for x, y in pts], step)
    ws = []
    for p in c:
        # nearest recorded width
        j = min(range(len(pts)), key=lambda i: math.dist(cam((pts[i][0], pts[i][1], 0)), p))
        r = run.widths[j]
        ws.append(r)
    k = abs(cam((1, 0, 0))[0] - cam((0, 0, 0))[0])
    left, right = [], []
    for i, (x, y) in enumerate(c):
        a = c[max(0, i - 1)]
        b = c[min(len(c) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        taper = min(1.0, 0.35 + i / max(1, len(c) - 1) * 0.9)
        w = max(1.6, ws[i] * k * wk * taper)
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    poly = left + right[::-1]
    return resample(dedupe(poly), 62)


# ================================================================ variants
class Variant:
    title = ""
    seed = 1

    def __init__(self, c):
        self.c = c
        self.vals = settings(c)[4]

    def frame(self, pane, t, motion=False):
        fr = Frame(self.title, self.vals)
        self.draw(fr, pane, t, motion)
        return fr

    @staticmethod
    def flare(b, t):
        """Landing: the bead lands 1.5x and settles in ~0.18 s; 1 once settled."""
        if b.res:
            return 1.0
        d = t - b.t
        if d < 0:
            return 1.0
        s = 1 + 0.5 * math.exp(-d / 0.055)
        return 1.0 if s < 1.03 else s

    @staticmethod
    def arriving(pane, t):
        """Drops in their last 0.1 s before the glass: (x, y, gust) of each."""
        return getattr(pane, "incoming", [])


def scaled(b, s):
    o = Bead(b.x, b.y, b.r * s, b.t, b.res, b.tail)
    o.lit, o.id = b.lit, b.id
    return o


# ---------------------------------------------------------------- v1
class V1(Variant):
    """The trace: the pane face on, wide. The subject is the trails the runs wipe through
    the beaded glass, each a closed lane drawn in bold outline with the beads it left
    strung inside; the beads themselves are bold closed outlines, double-lined when big."""
    title = "v1 · the trails, bold outline"
    seed = 31

    def pane(self):
        p = Pane(480, 199, self.c, self.seed, r_land=(2.4, 3.6), yc=0.62, band=0.33, speed=120)
        return p

    def camera(self, pane):
        cam = Camera((240, 100, 4000), (240, 100, 0))
        return cam.fit([(0, 0, 0), (480, 199, 0)], (0, 21, 480, 220))

    def draw(self, fr, pane, t, motion):
        cam = self.camera(pane)
        trails = pane.trails + pane.runs
        for i, run in enumerate(trails):
            newest = run is trails[-1]
            col = G5 if newest else (G4 if i >= len(trails) - 3 else G3)
            fr.outline(lane(cam, run), col, LINE if not newest else 2.0)
        for b in sorted(pane.beads, key=lambda b: b.lit):
            s = self.flare(b, t)
            bb = scaled(b, s)
            ol = cap_outline(cam, bb)
            if b.lit:
                fr.outline(ol, G7, SUBJ)
            elif b.res:
                fr.outline(ol, G3, LINE)
            else:
                fr.outline(ol, G4, 2.0)
            if b.r > 4.2 and not b.res:   # double outline: the meniscus inside the rim
                fr.ribbon(footprint(cam, bb, rho=0.55) + footprint(cam, bb, rho=0.55)[:1], HAIR,
                          G5 if b.lit else G3)
        for run in pane.runs:
            hb = Bead(run.x, run.y, run.r, run.t0)
            lit = run.lit or t - run.flash < 0.12
            fr.outline(cap_outline(cam, hb, lean=run.r * 0.5, sag=0.6), G7 if lit else G5, SUBJ)
        for x, y in self.arriving(pane, t):
            a = cam((x - pane.gust * 14, y + 16, 0))
            b = cam((x - pane.gust * 5, y + 5, 0))
            fr.line(a, b, HAIR, G5)


# ---------------------------------------------------------------- v2
class V2(Variant):
    """The rule as a real pane: the glass seen from the side and cut through at its right
    edge, so its thickness shows as a hatched section and the bead sitting on the cut shows
    its meniscus in profile. Every knob does what it would do to a real wet window."""
    title = "v2 · the cut edge, section"
    seed = 47
    T = 9.0          # glass thickness
    XC = 300.0       # the cut

    def pane(self):
        return Pane(self.XC, 200, self.c, self.seed, r_land=(3.2, 5.2), yc=0.6, band=0.34, speed=120)

    def camera(self, pane):
        cam = Camera((self.XC + 170, 150, 330), (self.XC - 110, 92, -10))
        cam.fit([(0, 0, 0), (self.XC, 0, 0), (self.XC, 200, 0), (0, 200, 0), (self.XC, 0, -self.T)],
                (-60, 24, 470, 226))
        return cam

    def heavy(self, pane):
        """The bead on the cut: puddle sets how much it holds before it lets go."""
        r = pane.r_land[1] * (1.5 + 1.6 * pane.puddle) * 1.6
        return Bead(self.XC, pane.yc - 18, r, -9)

    def draw(self, fr, pane, t, motion):
        cam = self.camera(pane)
        XC, T = self.XC, self.T
        # the pane's inner face and its bottom edge: hairlines, the glass ends past the frame
        fr.ribbon([cam((XC, 0, -T)), cam((-200, 0, -T))], HAIR, G2)
        fr.ribbon([cam((XC, 0, 0)), cam((-200, 0, 0))], LINE, G3)
        # trails then beads, far ones first
        for run in pane.trails + pane.runs:
            pts = [cam((x, y, 0)) for x, y in run.trail]
            if len(pts) > 1:
                fr.ribbon(even(pts, 2.0), HAIR, G3)
        items = sorted(pane.beads, key=lambda b: -cam.depth((b.x, b.y, 0)))
        for b in items:
            if b.x > XC - b.r * 0.4:
                continue
            bb = scaled(b, self.flare(b, t))
            fr.outline(cap_outline(cam, bb, h_k=0.75), G7 if b.lit else (G3 if b.res else G4),
                       SUBJ if b.lit else LINE)
            if b.r > 4.5:   # one contour at half height
                ring = footprint(cam, bb, rho=0.6, h_k=0.75)
                fr.ribbon(ring + ring[:1], HAIR, G3)
        for run in pane.runs:
            hb = Bead(run.x, run.y, run.r, run.t0)
            lit = run.lit or t - run.flash < 0.12
            fr.outline(cap_outline(cam, hb, h_k=0.75, lean=run.r * 0.5, sag=0.6), G7 if lit else G5, SUBJ)
        # the section: the cut face of the glass, hatched at 45 deg, outlined
        face = [cam((XC, -40, 0)), cam((XC, 260, 0)), cam((XC, 260, -T)), cam((XC, -40, -T))]
        fr.outline(face, G4, LINE)
        hv = self.heavy(pane)
        # the heavy bead's far half behind the cut (a cap) then its profile on the cut face
        half = [cam(cap_point(hv, rho, math.pi / 2 + math.pi * k / 30, h_k=0.8, sag=0.55, lean=hv.r * 0.32))
                for rho in (1.0, 0.75, 0.5, 0.25, 0.0) for k in range(31)]
        fr.outline(resample(hull(half), 60), G4, LINE)
        cut_floor = []
        for k in range(25):
            u = -1 + 2 * k / 24
            # profile: height of the cap along the cut line x = XC, y through the footprint
            yy = hv.y + hv.r * u * (1 + 0.55 * max(0.0, -u)) - hv.r * 0.32 * (1 - u * u)
            cut_floor.append((yy, hv.r * 0.8 * (1 - u * u)))
        prof = [cam((XC, yy, z)) for yy, z in cut_floor]
        sect = prof + [cam((XC, cut_floor[-1][0], 0)), cam((XC, cut_floor[0][0], 0))][::-1][:0]
        glassface = [cam((XC, cut_floor[0][0], 0)), cam((XC, cut_floor[-1][0], 0))]
        region = prof[::-1] + glassface[::1][:0]
        fr.outline(prof[::-1] + [cam((XC, cut_floor[0][0], -0.01))], G0, 0.0) if False else None
        # cut glass hatched above and below the bead's foot
        fr.hatch(face, G3, gap=4.0)
        fr.ribbon(face + face[:1], LINE, G4)
        fr.poly(prof, G0, "none")
        fr.ribbon(prof, SUBJ, G7)
        # its meniscus: a hairline a little inside the profile, the water's skin
        inner = [cam((XC, yy, z * 0.55)) for yy, z in cut_floor[3:-3]]
        fr.ribbon(inner, HAIR, G5)
        for x, y in self.arriving(pane, t):
            a = cam((x - pane.gust * 12, y + 14, 30))
            b = cam((x - pane.gust * 2, y + 2, 4))
            fr.line(a, b, HAIR, G5)


# ---------------------------------------------------------------- v3
class V3(Variant):
    """Exploded view: the heaviest bead on the glass, with the drops it gathered pulled back
    off the pane along the line the rain came in on. Each part hangs over the spot where it
    landed (its height on the glass is its note), a hairline back to that spot."""
    title = "v3 · the gathered drops, exploded"
    seed = 5

    def pane(self):
        return Pane(420, 200, self.c, self.seed, r_land=(3.4, 5.0), yc=0.62, band=0.4, speed=110)

    def camera(self, pane):
        cam = Camera((-170, 330, 470), (215, 85, 0))
        cam.fit([(0, 0, 0), (420, 0, 0), (420, 200, 0), (0, 200, 0)], (-30, 6, 520, 236))
        return cam

    def parts(self, pane):
        n = 2 + round(10 * pane.puddle)
        rng = random.Random(self.seed + 3)
        cs = courses(pane.span) or [0]
        hx, hy = 250.0, pane.yc - 34
        out = []
        for i in range(n):
            st = cs[(i * 3 + 1) % len(cs)]
            y = pane.pitch_y(st)
            x = hx + (i - (n - 1) / 2) * 36 + rng.uniform(-6, 6)
            out.append(Bead(x, y, rng.uniform(4.4, 6.2), -5))
        vol = sum(p.r ** 3 for p in out) * 1.1
        return Bead(hx, hy, vol ** (1 / 3), -1), out

    def axis(self, pane):
        return norm((-pane.gust * 0.6, 0.42, 1.0))

    def draw(self, fr, pane, t, motion):
        cam = self.camera(pane)
        # the glazing bar at the foot of the pane: a bar seen from above, its top edge lit
        fr.outline([cam((-60, 0, 0)), cam((480, 0, 0)), cam((480, 0, 16)), cam((-60, 0, 16))], G3, LINE)
        fr.outline([cam((-60, 0, 16)), cam((480, 0, 16)), cam((480, -14, 16)), cam((-60, -14, 16))], G3, LINE)
        for run in pane.trails + pane.runs:
            pts = [cam((x, y, 0)) for x, y in run.trail]
            if len(pts) > 1:
                fr.ribbon(even(pts, 2.0), HAIR, G3)
        hv, parts = self.parts(pane)
        beads = [b for b in pane.beads if math.dist((b.x, b.y), (hv.x, hv.y)) > hv.r + b.r + 8]
        for b in sorted(beads, key=lambda b: -cam.depth((b.x, b.y, 0))):
            bb = scaled(b, self.flare(b, t))
            fr.outline(cap_outline(cam, bb, h_k=0.7), G7 if b.lit else (G3 if b.res else G4), LINE)
        for run in pane.runs:
            hb = Bead(run.x, run.y, run.r, run.t0)
            lit = run.lit or t - run.flash < 0.12
            fr.outline(cap_outline(cam, hb, h_k=0.7, lean=run.r * 0.5, sag=0.6), G7 if lit else G5, SUBJ)
        ax = self.axis(pane)
        # the assembly: the heavy bead on the glass, its contact ring, the parts above
        for p in parts:   # landing spots and the slide each drop made to the heavy bead
            ring = footprint(cam, p, rho=1.0, h_k=0.7)
            fr.ribbon(ring + ring[:1], HAIR, G3)
        hvo = cap_outline(cam, hv, h_k=0.7, sag=0.45, lean=hv.r * 0.3)
        fr.outline(hvo, G5, LINE)
        for rho in (0.7, 0.4):
            ring = footprint(cam, hv, rho=rho, h_k=0.7, sag=0.45, lean=hv.r * 0.3)
            fr.ribbon(ring + ring[:1], HAIR, G4)
        lift = 70.0
        order = sorted(parts, key=lambda p: -cam.depth(add((p.x, p.y, 0), mul(ax, lift))))
        for p in order:
            base = (p.x, p.y, 0)
            top = add(base, mul(ax, lift))
            fr.ribbon([cam(add(base, mul(ax, p.r * 0.5))), cam(add(base, mul(ax, lift - 1)))], HAIR, G3)
            # the part: a drop as it arrived, a cap with its flat underside showing
            q = Bead(top[0], top[1], p.r, p.t)
            def P(rho, th, _q=q, _z=top[2]):
                x, y, z = cap_point(_q, rho, th, h_k=0.7)
                return (x, y, z + _z)
            under = [cam(P(1.0, 2 * math.pi * k / 30)) for k in range(30)]
            dome = [cam(P(rho, 2 * math.pi * k / 30)) for rho in (1.0, 0.6, 0.3, 0.0) for k in range(30)]
            fr.outline(resample(hull(dome + under), 56), G4, LINE)
            fr.ribbon(under + under[:1], HAIR, G3)
        # the drop that just landed joins it: the brightest part is the heavy bead's skin
        fr.ribbon(hvo + hvo[:1], SUBJ, G7)
        for x, y in self.arriving(pane, t):
            a = cam(add((x, y, 0), mul(ax, 40)))
            b = cam(add((x, y, 0), mul(ax, 8)))
            fr.line(a, b, HAIR, G5)


# ---------------------------------------------------------------- v4
class V4(Variant):
    """One heavy bead, close, about to let go: its surface drawn as level contours, one
    weight throughout. Neighbours are cut by the frame's edges; the pane is only implied."""
    title = "v4 · one heavy bead, contour"
    seed = 12

    def pane(self):
        p = Pane(480, 200, self.c, self.seed, r_land=(7.0, 10.0), yc=0.55, band=0.6, speed=150,
                 hold=(5.5, 7.0))
        return p

    def camera(self, pane):
        cam = Camera((150, 230, 700), (250, 100, 0))
        cam.fit([(0, 0, 0), (480, 0, 0), (480, 200, 0), (0, 200, 0)], (-40, 4, 520, 236))
        return cam

    def heavy(self, pane):
        r = 36 + 22 * pane.puddle
        return Bead(300, 104, r, -3)

    def draw(self, fr, pane, t, motion):
        cam = self.camera(pane)
        W = LINE
        for run in pane.trails + pane.runs:
            fr.outline(lane(cam, run, wk=0.7, step=4.0), G3, W)
        hv = self.heavy(pane)
        others = [b for b in pane.beads if math.dist((b.x, b.y), (hv.x, hv.y)) > hv.r * 1.25 + b.r]
        for b in sorted(others, key=lambda b: -cam.depth((b.x, b.y, 0))):
            bb = scaled(b, self.flare(b, t))
            fr.outline(cap_outline(cam, bb, h_k=0.6), G7 if b.lit else G4, W)
            if b.r > 8:
                ring = footprint(cam, bb, rho=0.5, h_k=0.6)
                fr.ribbon(ring + ring[:1], W, G3)
        for run in pane.runs:
            hb = Bead(run.x, run.y, run.r, run.t0)
            lit = run.lit or t - run.flash < 0.12
            fr.outline(cap_outline(cam, hb, h_k=0.6, lean=run.r * 0.5, sag=0.6), G7 if lit else G5, W)
        # the heavy bead: silhouette, then its contours, each split into visible runs
        kw = dict(h_k=0.62, sag=0.7, lean=hv.r * 0.42)
        sil = cap_outline(cam, hv, n=56, **kw)
        fr.outline(sil, G7, W)
        n = 7
        for k in range(1, n):
            rho = 1 - k / n
            pts, vis = [], []
            for j in range(73):
                th = 2 * math.pi * j / 72
                p = cap_point(hv, rho, th, **kw)
                e = 0.002
                pr = cap_point(hv, rho + e, th, **kw)
                pt = cap_point(hv, rho, th + e, **kw)
                nrm = cross(sub(pr, p), sub(pt, p))
                if nrm[2] < 0:
                    nrm = mul(nrm, -1)
                v = dot(nrm, sub(cam.eye, p)) > 0
                pts.append(cam(p))
                vis.append(v)
            runp = []
            for p, v in zip(pts, vis):
                if v:
                    runp.append(p)
                elif runp:
                    if len(runp) > 2:
                        fr.ribbon(runp, W, G5)
                    runp = []
            if len(runp) > 2:
                fr.ribbon(runp, W, G5)
        for x, y in self.arriving(pane, t):
            a = cam((x - pane.gust * 30, y + 40, 0))
            b = cam((x - pane.gust * 10, y + 12, 0))
            fr.line(a, b, W, G5)


# ---------------------------------------------------------------- v5
class V5(Variant):
    """The rain, literally: water on black glass, every bead and run a hatched mass (water
    is see-through, so it's hatched, not tinted), its lower rim lit where the meniscus
    catches the light. Closer than v1: fewer, bigger drops."""
    title = "v5 · rain on the glass, hatched"
    seed = 23

    def pane(self):
        return Pane(240, 100, self.c, self.seed, r_land=(2.6, 3.6), yc=0.6, band=0.36, speed=60)

    def camera(self, pane):
        cam = Camera((120, 50, 3000), (120, 50, 0))
        return cam.fit([(0, 0, 0), (240, 100, 0)], (0, 21, 480, 220))

    def draw(self, fr, pane, t, motion):
        cam = self.camera(pane)
        for run in pane.trails + pane.runs:
            ln = lane(cam, run, wk=0.42, step=3.0)
            if len(ln) > 3:
                fr.hatch(ln, G2, gap=4.0)
        for b in pane.beads:
            bb = scaled(b, self.flare(b, t))
            ol = cap_outline(cam, bb)
            fr.poly(ol, G0)
            fr.hatch(ol, G3, gap=3.2)
            self.rim(fr, cam, bb, G7 if b.lit else G5, SUBJ if b.lit else LINE)
        for run in pane.runs:
            hb = Bead(run.x, run.y, run.r, run.t0)
            lit = run.lit or t - run.flash < 0.12
            ol = cap_outline(cam, hb, lean=run.r * 0.5, sag=0.6)
            fr.poly(ol, G0)
            fr.hatch(ol, G3, gap=3.2)
            self.rim(fr, cam, hb, G7 if lit else G5, SUBJ, sag=0.6, lean=run.r * 0.5)
        for x, y in self.arriving(pane, t):
            a = cam((x - pane.gust * 8, y + 9, 0))
            b = cam((x - pane.gust * 3, y + 3, 0))
            fr.line(a, b, HAIR, G5)

    @staticmethod
    def rim(fr, cam, b, col, w, **kw):
        pts = [cam(cap_point(b, 1.0, math.pi * (1.08 + 0.84 * k / 20), **kw)) for k in range(21)]
        fr.ribbon(pts, w, col)


VARIANTS = {"v1": V1, "v2": V2, "v3": V3, "v4": V4, "v5": V5}


# ================================================================ rest + motion
def rest_pane(V, c, n_hist):
    v = V(c)
    p = v.pane()
    p.history(n_hist)
    return v, p


HIST = {"v1": 70, "v2": 34, "v3": 28, "v4": 14, "v5": 30}


def write_rest():
    for name, V in VARIANTS.items():
        v, p = rest_pane(V, DEFAULTS, HIST[name])
        d = HERE / name
        d.mkdir(exist_ok=True)
        (d / "rest.svg").write_text(v.frame(p, 1e9).svg())
        print("wrote", d / "rest.svg")


def write_motion(fps=15, dur=4.6, play=(0.15, 3.0)):
    tmp = HERE / "_frames"
    for name, V in VARIANTS.items():
        v, p = rest_pane(V, MOTION, HIST[name])
        t0 = p.events[-1][1] + 10 if p.events else 0.0
        notes = score(MOTION, 0, play[1] - play[0], V.seed)
        rng = random.Random(V.seed + 99)
        times = [t0 + play[0] + n for n in notes]
        q = list(times)
        plan = {}
        out = tmp / name
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True)
        nframes = round(dur * fps)
        prev, changes = None, []
        cs = courses(p.span) or [0]

        def planned(tn):
            if tn not in plan:
                st = rng.choice(cs)
                y = p.pitch_y(st)
                x = rng.uniform(0.05, 0.95) * p.W
                near = [b for b in p.beads if abs(b.y - y) < b.r * 1.5 and not b.res]
                if near and rng.random() < 0.6:   # some land on a bead at their height, so beads gather
                    big = max(near, key=lambda b: b.r)
                    x = big.x + rng.uniform(-0.4, 0.4) * big.r
                plan[tn] = (st, x)
            return plan[tn]

        for i in range(nframes):
            t = t0 + i / fps
            while q and q[0] <= t:
                tn = q.pop(0)
                st, x = planned(tn)
                p.land(tn, st=st, x=x)
            p.step(t, 1 / fps)
            p.incoming = [(planned(tn)[1], p.pitch_y(planned(tn)[0])) for tn in q if 0 < tn - t <= 0.1]
            fr = v.frame(p, t, motion=True)
            svg = fr.svg()
            items = set(fr.items)
            if prev is not None:
                changes.append(max(len(items - prev), len(prev - items)))
            prev = items
            sp = out / f"{i:03d}.svg"
            sp.write_text(svg)
            subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", "-b", "black", str(sp), "-o",
                            str(out / f"{i:03d}.png")], check=True)
        gif = HERE / name / "motion.gif"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", str(out / "%03d.png"),
                        "-vf", "split[a][b];[a]palettegen=max_colors=32:reserve_transparent=0[p];[b][p]paletteuse=dither=none",
                        "-loop", "0", str(gif)], check=True)
        sounding = [c for c in changes[: round((play[1] + 0.9) * fps)]]
        tail = changes[-round(0.5 * fps):]
        print(f"{name}: motion.gif {nframes} frames @ {fps} fps; changed elements/frame while sounding "
              f"avg {sum(sounding) / max(1, len(sounding)):.1f}, peak {max(sounding)}; last 0.5 s {sum(tail)}")
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    write_rest()
    if "--motion" in sys.argv:
        write_motion()
