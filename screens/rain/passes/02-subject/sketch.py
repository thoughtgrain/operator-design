#!/usr/bin/env python3
"""Rain, subject pass 02: five rest-frame sketches from one script.

Five directions from pass.json (angle x way of drawing), none of them the
first pass's roof plans, pulse trains or labelled sections:

    v1  the verge's tile ends at large scale          edge-lit silhouette
    v2  raindrops themselves, size is pitch           detailed line art
    v3  a rainstick, pins are the courses             hidden-line 3D
    v4  pantiles seen close, water in the pans        bold closed outlines
    v5  flowerpots under a dripping eave              cutaway section

    python3 screens/rain/passes/02-subject/sketch.py

Every frame is 480 x 220 with the stock header and the controls at their
defaults (rate 1.0 drops a beat, roof 12 st, gust 0, puddle 0). No text below
the header. Every 3D thing is modelled in world units and projected through
one camera per frame (craft.md, Think in 3D). Lines are closed filled ribbons;
outlines are closed paths; hatching is 45 deg hairlines >= 4 px apart, clipped
to the region in the generator. Grey only, never red.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent

D = {"rate": 0.4, "roof": 1 / 3, "gust": 0.5, "puddle": 0.0}
RATE = 0.25 * 32 ** D["rate"]          # drops per beat: 1.0
SPAN = 36 * D["roof"]                  # semitones: 12
GUST = 2 * D["gust"] - 1               # -1..1: 0
PUDDLE = D["puddle"]                   # 0..1: 0
LABELS = ["rate", "roof", "gust", "puddle"]
VALUES = ["1.0", "12", "0", "0"]

G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
FONT = "UniversNextPro-Light"
SCALE = [0, 2, 4, 5, 7, 9, 11]
HAIR, LINE, SUBJ = 1.0, 1.5, 2.5      # the three weights (craft.md)
TOP = 21.0                             # body starts below the stock header


def f(v: float) -> str:
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def courses(span: float) -> list[int]:
    out, octv = [], 0
    while True:
        for d in SCALE:
            st = 12 * octv + d
            if st > span + 1e-6:
                return out
            out.append(st)
        octv += 1


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
    """A look-at pinhole camera; world y is up. fit() scales and centres it so
    the given key points land in a screen box."""

    def __init__(self, eye, target, focal=1.0, cx=240.0, cy=120.0):
        self.eye = eye
        self.fwd = norm(sub(target, eye))
        self.right = norm(cross(self.fwd, (0, 1, 0)))
        self.up = cross(self.right, self.fwd)
        self.focal, self.cx, self.cy = focal, cx, cy

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


# ---------------------------------------------------------------- 2D geometry
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
    """Sutherland-Hodgman against the body rectangle."""
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


def seg_in_poly(a, b, poly):
    """Pieces of segment ab inside a simple polygon (even-odd)."""
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


def point_in(p, poly):
    c = False
    for i in range(len(poly)):
        a, b = poly[i - 1], poly[i]
        if (a[1] > p[1]) != (b[1] > p[1]):
            x = a[0] + (p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if x > p[0]:
                c = not c
    return c


def ellipse_pts(cx, cy, rx, ry, a0=0.0, a1=2 * math.pi, n=40):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * k / n), cy + ry * math.sin(a0 + (a1 - a0) * k / n))
            for k in range(n + 1)]


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
    """Reduce a polyline to n points (keeps ends)."""
    if len(pts) <= n:
        return pts
    return [pts[round(k * (len(pts) - 1) / (n - 1))] for k in range(n)]


# ---------------------------------------------------------------- frame
class Frame:
    def __init__(self, title: str):
        self.title = title
        self.items: list[str] = []

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
        """A closed body: black (or given) fill, outline stroke >= 1.5 px."""
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

    def disc(self, cx, cy, r, fill):
        self.add(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}" stroke="none" stroke-width="0"/>')

    def hatch(self, region, colour=G3, gap=4.0, w=HAIR):
        """45 deg hairlines across a closed region, >= gap px apart, clipped to it."""
        xs, ys = [p[0] for p in region], [p[1] for p in region]
        lo, hi = min(xs) + min(ys), max(xs) + max(ys)   # lines x + y = c
        c = lo + gap / 2
        while c < hi:
            a = (c - max(ys) - 2, max(ys) + 2)
            b = (c - min(ys) + 2, min(ys) - 2)
            for p, q in seg_in_poly(a, b, region):
                if math.dist(p, q) >= 3:
                    self.line(p, q, w, colour)
            c += gap * math.sqrt(2)

    def svg(self) -> str:
        head = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
            f"  <title>rain · subject pass 02 · {self.title}</title>",
            '  <g id="preview_canvas">',
            '    <rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>',
            "  </g>",
            '  <g id="preview_header">',
        ]
        for i, c in enumerate([G0, G1, G2, G3, G4, G5, G6, G7]):
            head.append(f'    <rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
        for i, lab in enumerate(LABELS):
            c = "#CBCBCB" if i < 2 else "#000000"
            head.append(f'    <text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{c}" stroke="none" '
                        f'font-family="{FONT}" font-size="10px">{lab}</text>')
        for i, v in enumerate(VALUES):
            c = "#CBCBCB" if i < 2 else "#000000"
            head.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{c}" stroke="none" '
                        f'font-family="{FONT}" font-size="20px">{v}</text>')
        head.append("  </g>")
        return "\n".join(head + ["  " + s for s in self.items] + ["</svg>", ""])


# ================================================================ v1
def v1() -> Frame:
    """The verge at large scale: the gable end of the roof, its plain-tile courses
    as a sawtooth of noses, black against black and lit only along the edges that
    face the sky. The eave corner is in frame, the rest of the roof runs off the
    right edge. Drops fall onto the treads; the struck course's rim is the light."""
    fr = Frame("v1 · the verge, edge-lit")
    cs = courses(SPAN)
    n = len(cs)
    pitch = math.radians(30)
    u = (math.cos(pitch), math.sin(pitch), 0.0)          # up the slope
    v = (-math.sin(pitch), math.cos(pitch), 0.0)         # out of the slope
    run = 10.0                                           # slope length in frame (world)
    e = run / n                                          # exposure per course
    t = 0.32                                             # nose thickness
    depth = 3.2                                          # how far the courses run back (z)

    def P(s, h, z=0.0):
        return add(add(mul(u, s), mul(v, h)), (0.0, 0.0, z))

    cam = Camera((3.0, 6.5, 16.0), (4.6, 2.6, -1.0))
    key = [P(-0.6, -1.2), P(run, t), P(run, t, -depth), P(0, -1.4, 0)]
    cam.fit(key, (16, 34, 520, 222))

    # silhouette profile (slope coords): sawtooth of noses
    prof = []
    for k in range(n):
        s0, s1 = k * e, (k + 1) * e
        prof += [(s0, 0.0), (s0, t), (s0 + 0.1 * e, t + 0.02), (s1, 0.42 * t)]
    prof.append((n * e + 0.4, 0.42 * t))
    # receding course lines (the nose edges running back into the dark), drawn first
    for k in range(n):
        a = cam(P(k * e, t))
        b = cam(P(k * e, t, -depth))
        fr.ribbon([a, b], HAIR, G2)
        a2 = cam(P(k * e + 0.1 * e, t + 0.02, 0))
    # far verge (the other end of the courses) as a hairline sawtooth, dim
    far = [cam(P(s, h, -depth)) for s, h in prof]
    fr.ribbon(far, HAIR, G1)
    # the body: barge board and roof mass, black, hiding what's behind
    barge = 0.9
    body = [cam(P(s, h)) for s, h in prof] + [cam(P(n * e + 0.4, -barge)), cam(P(-0.35, -barge))]
    body = [cam(P(-0.35, 0.0))] + body
    fr.poly(body, G0)
    # barge board's lower edge and fascia: hairline, dim
    fr.ribbon([cam(P(-0.35, -barge)), cam(P(n * e + 0.4, -barge))], HAIR, G2)
    fr.ribbon([cam(P(-0.35, -0.12)), cam(P(n * e + 0.4, -0.12))], HAIR, G1)
    # the rim light: the sky-facing edge of each nose and tread
    struck = 5
    for k in range(n):
        s0, s1 = k * e, (k + 1) * e
        tread = [cam(P(s0, t)), cam(P(s0 + 0.1 * e, t + 0.02)), cam(P(s1, 0.42 * t))]
        if k == struck:
            fr.ribbon(tread, SUBJ, G7)
        else:
            fr.ribbon(tread, LINE, G4)
        # the nose face (riser) is turned from the light: hairline
        fr.ribbon([cam(P(s0, 0.0)), cam(P(s0, t))], HAIR, G3)
    # gutter at the eave: a half-round in profile, a dark body with a lit rim (empty: puddle 0)
    gc = P(-0.25, -0.35)
    g = cam(gc)
    rr = cam.focal * 0.42 / cam.depth(gc)
    gut = ellipse_pts(g[0], g[1], rr, rr, 0, math.pi, 16)
    inner = ellipse_pts(g[0], g[1], rr - 3, rr - 3, math.pi, 0, 16)
    fr.outline(gut + inner, G3, LINE)
    # drops: short falling streaks, vertical in still air, above the courses they'll hit
    rnd = random.Random(11)
    for k, frac in ((1, 0.55), (3, 0.3), (6, 0.6)):
        base = cam(P((k + frac) * e, 0.42 * t + 0.2))
        hgt = 26 + rnd.random() * 30
        fr.ribbon([(base[0], base[1] - hgt - 13), (base[0], base[1] - hgt)], LINE, G4)
    # the drop that just landed: a short broken crown off the struck tread
    sp = cam(P((struck + 0.45) * e, 0.42 * t + 0.55 * t))
    for dx, dy in ((-7, -4), (7, -4)):
        fr.ribbon([(sp[0] + dx * 0.35, sp[1] - 1), (sp[0] + dx, sp[1] + dy)], LINE, G5)
    return fr


# ================================================================ v2
def drop_profile(r, flat, n=40):
    """Side profile of a falling raindrop: round on top, flattened underneath."""
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        x, y = math.cos(a), math.sin(a)
        y = y * (0.96 if y > 0 else (1 - flat))
        pts.append((r * x, r * y))
    return pts


def v2() -> Frame:
    """Rain itself: the drops of the last bar falling through still air, drawn as
    real drops (round on top, flattened underneath the bigger they are). A drop's
    size is its note: big drops are the low courses, small the high ones. The one
    that just played is the bright one."""
    fr = Frame("v2 · the drops")
    cs = courses(SPAN)
    n = len(cs)
    cam = Camera((0.0, 40.0, 900.0), (0.0, 0.0, 0.0))
    cam.fit([(-235, -95, 0), (235, 95, 0)], (14, 30, 466, 214))
    rnd = random.Random(5)
    placed = []
    want = 7
    tries = 0
    while len(placed) < want and tries < 4000:
        tries += 1
        c = rnd.randrange(n)
        r = 7.0 + 11.0 * (1 - c / (n - 1))
        x, y, z = rnd.uniform(-210, 210), rnd.uniform(-70, 72), rnd.uniform(-60, 60)
        if all(math.hypot(x - q[0], y - q[1]) > r + q[3] + 34 for q in placed):
            placed.append((x, y, z, r, c))
    placed.sort(key=lambda q: -cam.depth((q[0], q[1], q[2])))   # far first
    newest = min(range(len(placed)), key=lambda i: abs(placed[i][0] - 40) + abs(placed[i][1] + 10))
    for i, (x, y, z, r, c) in enumerate(placed):
        p = (x, y, z)
        o = cam(p)
        k = cam.focal / cam.depth(p)
        rp = r * k
        flat = 0.08 + 0.38 * (r - 7) / 11
        prof = [(o[0] + px * k, o[1] - py * k) for px, py in drop_profile(r, flat)]
        bright = i == newest
        # fall trail: hairlines above the drop, the length it fell this frame
        for j, dx in enumerate((-0.42, 0.0, 0.42)):
            if rp < 9 and j != 1:
                continue
            L = (1.4 + 0.6 * (j == 1)) * rp + 8
            top = (o[0] + dx * rp, o[1] - 0.96 * rp - 4 - L)
            bot = (o[0] + dx * rp, o[1] - 0.96 * rp - 4)
            fr.ribbon([top, bot], HAIR, G4 if bright else G2)
        fr.outline(prof, G7 if bright else G4, SUBJ if bright else LINE)
        # inner structure: the near half of the equator (seen from a little above)
        if rp >= 9:
            ry = rp * 0.3
            eq = ellipse_pts(o[0], o[1] + rp * 0.06, rp * 0.93 - 1, ry, 0.15, math.pi - 0.15, 18)
            fr.ribbon(eq, HAIR, G4 if bright else G3)
            # the refraction crescent, up and left
            hl = ellipse_pts(o[0] - rp * 0.1, o[1] - rp * 0.08, rp * 0.6, rp * 0.62,
                             math.pi * 1.08, math.pi * 1.45, 10)
            fr.ribbon(hl, HAIR, G5 if bright else G3)
    return fr


# ================================================================ v3
def v3() -> Frame:
    """A rainstick: a long hollow stick with pins driven through it in a spiral,
    pebbles falling inside strike the pins. Each ring of pins is a course; a pin
    just struck carries a ring of light at its head. Turning the stick (gust)
    tilts it; level, a shake scatters the pebbles at random."""
    fr = Frame("v3 · the rainstick")
    cs = courses(SPAN)
    n = len(cs)
    R, L = 15.0, 400.0
    yaw = math.radians(16)
    ax = (math.cos(yaw), 0.0, math.sin(yaw))          # +x end comes toward the camera
    e1 = (0.0, 1.0, 0.0)
    e2 = norm(cross(ax, e1))

    def S(s, phi, r=R):
        return add(mul(ax, s), add(mul(e1, r * math.cos(phi)), mul(e2, r * math.sin(phi))))

    cam = Camera((40.0, 150.0, 620.0), (0.0, 0.0, 0.0))
    ring_l = [S(-L / 2, a) for a in [k * math.pi / 18 for k in range(36)]]
    ring_r = [S(L / 2, a) for a in [k * math.pi / 18 for k in range(36)]]
    cam.fit(ring_l + ring_r, (26, 44, 456, 200))

    def facing(s, phi):
        nrm = add(mul(e1, math.cos(phi)), mul(e2, math.sin(phi)))
        return dot(nrm, norm(sub(cam.eye, S(s, phi))))

    # body: hull of both end rings = the tube's silhouette, black, Line weight
    body = hull([cam(p) for p in ring_l + ring_r])
    fr.outline(body, G4, LINE)
    # inner structure: a few growth nodes (visible half rings), hairline
    for s in (-110.0, 20.0, 140.0):
        pts = [cam(S(s, a)) for a in [k * math.pi / 40 for k in range(81)] if facing(s, a) > 0.05]
        fr.ribbon(pts, HAIR, G2)
    # the grip: a cord wound round the left end, hairlines >= 3 px apart
    for j in range(7):
        s = -L / 2 + 14 + j * 6.0
        pts = [cam(S(s + 3.0 * math.sin(a), a)) for a in [k * math.pi / 30 for k in range(61)]
               if facing(s, a) > 0.05]
        fr.ribbon(pts, HAIR, G3)
    # near end: open, a rim with wall thickness and the inside dark (no pebbles: puddle 0)
    rim = [cam(S(L / 2, a)) for a in [k * math.pi / 24 for k in range(48)]]
    inner = [cam(S(L / 2, a, R - 3.0)) for a in [k * math.pi / 24 for k in range(48)]]
    fr.outline(rim, G4, LINE)
    fr.outline(inner, G3, LINE)
    # far wall seen inside the mouth: the inner bottom, hairline
    deep = [cam(S(L / 2 - 26, a, R - 3.0)) for a in [math.pi * (0.62 + 0.76 * k / 20) for k in range(21)]]
    deep = [p for p in deep if point_in(p, inner)]
    fr.ribbon(deep, HAIR, G2)
    # pins: n rings along the stick, six per ring, turning in a spiral; visible heads only
    s0, s1 = -L / 2 + 70, L / 2 - 26
    struck = {(2, 1): 2, (4, 3): 1, (5, 0): 1, (6, 2): 3}  # (ring, pin): age 3 newest
    for k in range(n):
        s = s0 + (s1 - s0) * k / (n - 1)
        for j in range(6):
            phi = j * math.pi / 3 + k * 0.42
            fc = facing(s, phi)
            if fc < 0.3:
                continue
            p = cam(S(s, phi))
            age = struck.get((k, j))
            if age == 3:
                fr.disc(p[0], p[1], 2.6, G7)
                fr.ribbon(ellipse_pts(p[0], p[1], 5.2, 5.2, 0, 2 * math.pi, 20), LINE, G5)
            elif age:
                fr.disc(p[0], p[1], 2.0, G4)
                fr.ribbon(ellipse_pts(p[0], p[1], 5.0, 5.0, 0, 2 * math.pi, 20), HAIR, G4)
            else:
                fr.disc(p[0], p[1], 1.8, G3)
    return fr


# ================================================================ v4
def v4() -> Frame:
    """Pantiles seen close: the S-shaped clay the rain lands on, a few courses
    rising away, each tile a bold closed outline over black. The tile just struck
    is the bright one; puddle fills the pans with water (hatched, there but not
    solid); here at 0 they're dry."""
    fr = Frame("v4 · pantiles, close")
    cs = courses(SPAN)
    n = len(cs)
    pitch = math.radians(32)
    up = (0.0, math.sin(pitch), -math.cos(pitch))   # up the slope, away from us
    nrm = (0.0, math.cos(pitch), math.sin(pitch))
    W = 1.0           # tile width
    e = 0.62          # exposure
    A = 0.13          # wave height

    def wave(x):      # pantile: a broad pan and a rolled roll
        ph = (x / W) % 1.0
        return A * math.sin(2 * math.pi * ph - math.pi / 2) if ph < 1 else 0

    def P(x, s, h=0.0):
        return add(add((x, 0.0, 0.0), mul(up, s)), mul(nrm, h + wave(x)))

    cam = Camera((0.35, 2.2, 3.2), (0.35, 1.1, -1.6))
    cam.fit([P(-2.2, 0, -0.2), P(2.9, 0, -0.2), P(-2.2, n * e, 0.3), P(2.9, n * e, 0.3)],
            (-30, 40, 510, 214))
    struck = (5, 1)       # course, tile
    pans = []
    for k in reversed(range(n)):          # far courses first; near ones overlap them
        s = k * e
        for j in range(-4, 6):
            x0, x1 = j * W, (j + 1) * W
            xs = [x0 + (x1 - x0) * q / 16 for q in range(17)]
            lower = [cam(P(x, s, A)) for x in xs]
            upper = [cam(P(x, s + e * 1.15, A)) for x in reversed(xs)]
            shape = lower + upper
            if max(p[0] for p in shape) < 0 or min(p[0] for p in shape) > 480:
                continue
            hit = (k, j) == struck
            depth_w = SUBJ if k < 3 else LINE
            fr.outline(shape, G7 if hit else (G4 if k < 4 else G3), SUBJ if hit else depth_w)
            if k < 3:
                pans.append((k, j, xs, s))
    # drops falling toward the roof: small bold teardrops, closed outlines
    drops = [(-0.9, 5.2, 0.55), (1.55, 3.4, 0.7), (0.4, 7.4, 0.5)]
    for x, s, hgt in drops:
        base = P(x, s, A + hgt)
        o = cam(base)
        k = cam.focal / cam.depth(base) * 0.085
        tear = []
        for q in range(24):
            a = 2 * math.pi * q / 24
            r = 1.0 if math.sin(a) > 0 else 1.0 - 0.75 * (-math.sin(a)) ** 1.4
            tear.append((o[0] + k * r * math.cos(a) * 0.9, o[1] + k * math.sin(a) * (1.0 if math.sin(a) > 0 else 1.9)))
        fr.outline(tear, G5, LINE)
    # the splash off the struck tile: a broken crown, two short bold strokes
    k, j = struck
    c = cam(P((j + 0.5) * W, k * e + 0.28, A + 0.04))
    for dx in (-1, 1):
        fr.ribbon([(c[0] + dx * 3, c[1] - 2), (c[0] + dx * 9, c[1] - 9)], LINE, G5)
    return fr


# ================================================================ v5
def v5() -> Frame:
    """Under the eave, a shelf of clay flowerpots, cut through to show their
    hollows: the drip line above lets the rain fall into them, and each pot rings
    its own note (the big ones low, the small ones high). The pot that just rang is
    bright; puddle is the water standing in them (hatched; dry at 0)."""
    fr = Frame("v5 · pots under the eave, cut away")
    cs = courses(SPAN)
    n = len(cs)
    cam = Camera((0.0, 120.0, 900.0), (0.0, 0.0, 0.0))
    # pot sizes: low course = big pot
    radii = [26.0 - 14.0 * k / (n - 1) for k in range(n)]
    gap = 12.0
    total = sum(2 * r for r in radii) + gap * (n - 1)
    xs, x = [], -total / 2
    for r in radii:
        xs.append(x + r)
        x += 2 * r + gap
    shelf_y = -60.0
    cam.fit([(-total / 2 - 30, shelf_y - 14, 0), (total / 2 + 30, 100, 0)], (12, 26, 468, 212))

    def ring(cx_, y, r, a0, a1, m=24):
        return [cam((cx_ + r * math.cos(a0 + (a1 - a0) * q / m), y, r * math.sin(a0 + (a1 - a0) * q / m)))
                for q in range(m + 1)]

    # eave above: the drip edge of the roof, a dark slab with a lit lower edge
    ey = 92.0
    edge = [cam((-total / 2 - 60, ey, 0)), cam((total / 2 + 60, ey, 0)),
            cam((total / 2 + 60, ey + 30, 0)), cam((-total / 2 - 60, ey + 30, 0))]
    fr.poly(edge, G0)
    fr.ribbon([cam((-total / 2 - 60, ey, 0)), cam((total / 2 + 60, ey, 0))], LINE, G4)
    fr.ribbon([cam((-total / 2 - 60, ey + 7, 0)), cam((total / 2 + 60, ey + 7, 0))], HAIR, G2)
    # the shelf: a plank under the pots, front edge Line, top face hairline
    sh = [cam((-total / 2 - 30, shelf_y, 30)), cam((total / 2 + 30, shelf_y, 30)),
          cam((total / 2 + 30, shelf_y - 9, 30)), cam((-total / 2 - 30, shelf_y - 9, 30))]
    fr.outline(sh, G3, LINE)
    fr.ribbon([cam((-total / 2 - 30, shelf_y, -30)), cam((total / 2 + 30, shelf_y, -30))], HAIR, G2)
    struck = 3
    for i, (cxp, r) in enumerate(zip(xs, radii)):
        H = r * 1.05
        rb = r * 0.68
        t = max(2.6, r * 0.12)
        bright = i == struck
        col = G7 if bright else G4
        # back half of the inside: the far rim and the far floor, seen through the cut
        fr.ribbon(ring(cxp, shelf_y + H, r - t, math.pi, 2 * math.pi), HAIR, G5 if bright else G3)
        fr.ribbon(ring(cxp, shelf_y + t, rb - t, math.pi, 2 * math.pi, 16), HAIR, G2)
        # the cut walls: left and right sections through the clay, closed outlines
        for side in (-1, 1):
            prof = [(rb, 0.0), (r, H), (r + t * 0.5, H), (r + t * 0.5, H - t * 1.4),
                    (r - t * 0.3, H - t * 1.4), (rb - t, t), (0.0, t), (0.0, 0.0)]
            if side == 1:
                pts = [cam((cxp + px, shelf_y + py, 0)) for px, py in prof]
            else:
                pts = [cam((cxp - px, shelf_y + py, 0)) for px, py in prof]
            fr.outline(pts, col, SUBJ if bright else LINE)
    # drops falling from the drip edge, straight down in still air
    for i, frac in ((1, 0.45), (5, 0.62), (6, 0.25)):
        cxp, r = xs[i], radii[i]
        yb = shelf_y + r * 1.05 + 20 + 30 * frac
        a, b = cam((cxp - r * 0.25, yb + 14, 0)), cam((cxp - r * 0.25, yb, 0))
        fr.ribbon([a, b], LINE, G4)
    # the one that just rang: its drop meeting the floor, a short crown
    c = cam((xs[struck], shelf_y + 2.6 + 2, 0))
    for dx in (-1, 1):
        fr.ribbon([(c[0] + dx * 2, c[1] - 1), (c[0] + dx * 7, c[1] - 7)], LINE, G5)
    return fr


def main():
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        d = HERE / name
        d.mkdir(exist_ok=True)
        (d / "rest.svg").write_text(fn().svg())
        print(f"wrote {d / 'rest.svg'}")


if __name__ == "__main__":
    main()
