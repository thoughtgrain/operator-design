#!/usr/bin/env python3
"""Bell, revision pass 02: five rest-frame refinements of pass 01's v1 bell.

    python3 screens/bell/passes/02-revision/sketch.py

Writes v1..v5/rest.svg (480 x 220, header and authoring rules from
opxy/templates/frame.svg) and v1..v5/candidate.json. Every control sits at its
default: depth 12 dB, air 0.2 s, knee 6 dB, gain x2.00.

The owner's note on pass 01: keep v1's bell, drop the signal visualization.
So there's no trace, curve or waveform anywhere: the bell's shape is the
subject, and each control changes the bell or how it's struck and rings.
Nothing in the drawing is text; the stock header is the only text.

One model for all five: the bell is a surface of revolution (crown, a filleted
shoulder whose radius is the knee, a straight flared wall, a sound-bow at the
lip), hung on its cable below the surface. Each variant puts one camera on it
and projects every line through that camera: hidden-line edges by facing test
(the outer shell is convex, so a facing test is exact for it), interior lines
only where a cut or the open mouth shows them, painter's order for the rest.
The camera is fitted on both ends of depth's travel, so nothing clips at
either end.

Grey only, never red. Lines are thin closed ribbons; every leaf has explicit
paint. Hatching is 45 degree hairlines >= 3 px apart, clipped to its region.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 480, 220
TOP = 20                     # stock header ends here

BRIGHT, G175, G150, G125, G100, G75, G50 = ("#CDCDCD", "#AFAFAF", "#969696", "#7D7D7D",
                                           "#646464", "#4B4B4B", "#323232")
BLACK = "#000000"
HAIR, LINE, SUBJ = 1.0, 1.5, 2.0   # craft.md line weights
FONT = "UniversNextPro-Light"

# Defaults (normalised) from definition.json.
P = {"depth": 0.25, "air": 0.5, "knee": 0.25, "gain": 0.25}
CAPTIONS = ["12", "0.2s", "6.0", "2.00"]


# ---------------------------------------------------------------- vector helpers
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def mul(a, k): return (a[0] * k, a[1] * k, a[2] * k)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def unit(a):
    l = math.sqrt(dot(a, a)) or 1.0
    return mul(a, 1 / l)


def n(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# ---------------------------------------------------------------- camera
class Cam:
    """One camera per variant: position, look-at, ortho or perspective, then a 2D fit
    (uniform scale + offset) so the key object lands where the composition needs it."""

    def __init__(self, pos, look, persp=False, up=(0, 0, 1)):
        self.pos, self.persp = pos, persp
        self.f = unit(sub(look, pos))
        self.r = unit(cross(self.f, up))
        self.u = cross(self.r, self.f)
        self.k, self.ox, self.oy = 1.0, 0.0, 0.0

    def raw(self, p):
        d = sub(p, self.pos)
        z = dot(d, self.f)
        x, y = dot(d, self.r), dot(d, self.u)
        if self.persp:
            x, y = x / z, y / z
        return x, -y, z

    def __call__(self, p):
        x, y, _ = self.raw(p)
        return (self.ox + self.k * x, self.oy + self.k * y)

    def depth(self, p):
        return self.raw(p)[2]

    def fit(self, pts, box):
        """Scale and place so the raw points fill box (x0, y0, x1, y1), keeping aspect."""
        xs, ys = zip(*[self.raw(p)[:2] for p in pts])
        bx0, by0, bx1, by1 = box
        self.k = min((bx1 - bx0) / (max(xs) - min(xs)), (by1 - by0) / (max(ys) - min(ys)))
        self.ox = (bx0 + bx1) / 2 - self.k * (max(xs) + min(xs)) / 2
        self.oy = (by0 + by1) / 2 - self.k * (max(ys) + min(ys)) / 2

    def facing(self, p, nrm):
        view = sub(self.pos, p) if self.persp else mul(self.f, -1)
        return dot(unit(view), nrm)

    def ppu(self, p):
        """Pixels per world unit at p (size from distance)."""
        return self.k / (self.depth(p) if self.persp else 1.0)


# ---------------------------------------------------------------- the bell model
class Bell:
    """A surface of revolution about the z axis; rim at z = z0. Units: rim radius 1.

    knee  -> shoulder fillet radius (hard corner to a full round crown)
    air   -> the air pocket's share of the inside; the waterline sits below it
    lip   -> sound-bow width at the rim
    scale -> uniform size
    """
    H, RT, RR, WALL = 1.22, 0.58, 1.0, 0.085

    def __init__(self, z0=0.0, knee=P["knee"], air=P["air"], lip=0.06, scale=1.0, x0=0.0, y0=0.0):
        self.z0, self.s, self.x0, self.y0 = z0, scale, x0, y0
        self.rk = 0.03 + 0.5 * knee                 # knee: fillet 0.03 -> 0.53 of rim radius
        self.lip = lip
        self.outer = self._profile(self.H, self.RT, self.RR, self.rk, lip)
        w = self.WALL
        self.inner = self._profile(self.H - w, self.RT - w, self.RR - w, max(0.01, self.rk - w), 0.0)
        frac = 0.32 + 0.56 * air                    # air: pocket 32 % -> 88 % of the inside
        self.zw = (self.H - w) * (1 - frac)         # waterline height above the rim
        self.rw = self.r_at(self.inner, self.zw)

    @staticmethod
    def _profile(Hb, Rt, Rr, rk, lip, n_arc=9):
        """(r, z, nr, nz) from the crown centre out over the shoulder and down to the rim."""
        V = (Rt, Hb)
        d1 = (-1.0, 0.0)
        L2 = math.hypot(Rr - Rt, Hb)
        d2 = ((Rr - Rt) / L2, -Hb / L2)
        phi = math.acos(d1[0] * d2[0] + d1[1] * d2[1])
        t = rk / math.tan(phi / 2)
        t = min(t, Rt * 0.92, L2 * 0.55)
        rk = t * math.tan(phi / 2)
        T1 = (V[0] + d1[0] * t, V[1] + d1[1] * t)
        T2 = (V[0] + d2[0] * t, V[1] + d2[1] * t)
        bis = (d1[0] + d2[0], d1[1] + d2[1])
        bl = math.hypot(*bis)
        C = (V[0] + bis[0] / bl * rk / math.sin(phi / 2), V[1] + bis[1] / bl * rk / math.sin(phi / 2))
        wn = (Hb / L2, (Rr - Rt) / L2)                       # outward wall normal
        pts = [(0.0, Hb, 0.0, 1.0), (T1[0] * 0.5, Hb, 0.0, 1.0)]
        a0, a1 = math.atan2(T1[1] - C[1], T1[0] - C[0]), math.atan2(T2[1] - C[1], T2[0] - C[0])
        for i in range(n_arc + 1):
            a = a0 + (a1 - a0) * i / n_arc
            pts.append((C[0] + rk * math.cos(a), C[1] + rk * math.sin(a), math.cos(a), math.sin(a)))
        for k in (0.33, 0.66):
            pts.append((T2[0] + (Rr - T2[0]) * k, T2[1] * (1 - k), wn[0], wn[1]))
        bow = 0.12 + lip
        rb = Rr - (Rr - Rt) * bow / Hb
        pts.append((rb, bow, wn[0], wn[1]))
        if lip > 0:
            pts.append((rb + lip, bow * 0.45, 1.0, 0.0))
            pts.append((rb + lip, 0.0, 1.0, 0.0))
        else:
            pts.append((Rr, 0.0, wn[0], wn[1]))
        return pts

    @staticmethod
    def r_at(prof, z):
        for a, b in zip(prof, prof[1:]):
            if (a[1] - z) * (b[1] - z) <= 0 and a[1] != b[1]:
                t = (z - a[1]) / (b[1] - a[1])
                return a[0] + (b[0] - a[0]) * t
        return prof[-1][0]

    def P(self, r, z, th):
        s = self.s
        return (self.x0 + s * r * math.cos(th), self.y0 + s * r * math.sin(th), self.z0 + s * z)

    @staticmethod
    def N(nr, nz, th):
        return (nr * math.cos(th), nr * math.sin(th), nz)

    def shell(self, k=48):
        """Sample points of the outer shell (for the outline hull and camera fits)."""
        return [self.P(r, z, 2 * math.pi * i / k) for r, z, _, _ in self.outer for i in range(k)]

    def ring(self, prof, idx_or_z, k=72, th0=0.0, th1=2 * math.pi):
        """(point, normal, theta) round a latitude: a profile index, or a height (interpolated)."""
        if isinstance(idx_or_z, int):
            r, z, nr, nz = prof[idx_or_z]
        else:
            z = idx_or_z
            r = self.r_at(prof, z)
            nr, nz = 1.0, 0.0
        out = []
        for i in range(k + 1):
            th = th0 + (th1 - th0) * i / k
            out.append((self.P(r, z, th), self.N(nr, nz, th), th))
        return out

    def meridian(self, prof, th, sub=3):
        out = []
        for a, b in zip(prof, prof[1:]):
            for j in range(sub):
                t = j / sub
                r, z = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                nr, nz = a[2] + (b[2] - a[2]) * t, a[3] + (b[3] - a[3]) * t
                out.append((self.P(r, z, th), self.N(nr, nz, th), th))
        r, z, nr, nz = prof[-1]
        out.append((self.P(r, z, th), self.N(nr, nz, th), th))
        return out

    def crown(self):
        return (self.x0, self.y0, self.z0 + self.s * self.H)

    def shoulder_idx(self):
        """Profile indices: shoulder start (after the flat top), shoulder end, wall bands, bow, rim."""
        return 2, 2 + 9, len(self.outer) - 1


# ---------------------------------------------------------------- 2D geometry
def hull(pts):
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in pts))
    if len(pts) < 3:
        return pts

    def half(seq):
        h = []
        for p in seq:
            while len(h) >= 2 and ((h[-1][0] - h[-2][0]) * (p[1] - h[-2][1]) - (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0])) <= 0:
                h.pop()
            h.append(p)
        return h
    lo, hi = half(pts), half(pts[::-1])
    return lo[:-1] + hi[:-1]


def thin(poly, step=2.0, maxn=60):
    """Drop points closer than step so an outline fits the device's 64 points."""
    out = [poly[0]]
    for p in poly[1:]:
        if math.dist(p, out[-1]) >= step:
            out.append(p)
    while len(out) > maxn:
        out = out[::2]
    return out


def inside(pt, poly):
    x, y = pt
    c = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xi > x:
                c = not c
    return c


def seg_intervals(a, b, poly):
    """Parameter intervals of segment a->b inside poly."""
    ts = [0.0, 1.0]
    for p, q in zip(poly, poly[1:] + poly[:1]):
        d = (b[0] - a[0], b[1] - a[1])
        e = (q[0] - p[0], q[1] - p[1])
        den = d[0] * e[1] - d[1] * e[0]
        if abs(den) < 1e-9:
            continue
        t = ((p[0] - a[0]) * e[1] - (p[1] - a[1]) * e[0]) / den
        u = ((p[0] - a[0]) * d[1] - (p[1] - a[1]) * d[0]) / den
        if 0 < t < 1 and 0 <= u <= 1:
            ts.append(t)
    ts.sort()
    out = []
    for t0, t1 in zip(ts, ts[1:]):
        if t1 - t0 < 1e-6:
            continue
        m = (t0 + t1) / 2
        if inside((a[0] + (b[0] - a[0]) * m, a[1] + (b[1] - a[1]) * m), poly):
            out.append((t0, t1))
    return out


def subtract(ivs, cut):
    out = []
    for a0, a1 in ivs:
        pieces = [(a0, a1)]
        for c0, c1 in cut:
            nxt = []
            for p0, p1 in pieces:
                if c1 <= p0 or c0 >= p1:
                    nxt.append((p0, p1))
                else:
                    if c0 > p0:
                        nxt.append((p0, c0))
                    if c1 < p1:
                        nxt.append((c1, p1))
            pieces = nxt
        out += pieces
    return out


# ---------------------------------------------------------------- drawing kit
class Frame:
    def __init__(self) -> None:
        self.parts: list[str] = []

    def poly(self, pts, fill="none", stroke=BRIGHT, sw=SUBJ) -> None:
        pts = dedupe(pts)
        assert 3 <= len(pts) <= 64, len(pts)
        d = "M " + " L ".join(f"{n(x)} {n(y)}" for x, y in pts) + " Z"
        st = f'stroke="{stroke}" stroke-width="{n(sw)}"' if stroke != "none" else 'stroke="none"'
        self.parts.append(f'<path d="{d}" fill="{fill}" {st}/>')

    def line(self, pts, w=HAIR, colour=G100) -> None:
        """A polyline as a thin filled closed ribbon (never a stroke traced back)."""
        pts = dedupe(pts)
        if len(pts) < 2 or sum(math.dist(a, b) for a, b in zip(pts, pts[1:])) < 3:
            return
        for chunk in chunks(pts, 31):
            if len(chunk) >= 2:
                self.poly(ribbon(chunk, w), fill=colour, stroke="none")

    def circle(self, cx, cy, r, fill=BLACK, stroke=G100, sw=HAIR) -> None:
        st = f'stroke="{stroke}" stroke-width="{n(sw)}"' if stroke != "none" else 'stroke="none"'
        self.parts.append(f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n(r)}" fill="{fill}" {st}/>')

    def body(self, outline, fill=BLACK, stroke=G150, sw=LINE):
        """A closed black body with its silhouette edge."""
        self.poly(thin(outline), fill=fill, stroke=stroke, sw=sw)

    def hatch(self, region, spacing=4.0, colour=G75, flip=False, holes=(), box=(0, TOP + 1, W, H - 1)):
        """45 degree hairlines, spacing px apart (perpendicular), clipped to region minus holes."""
        assert spacing >= 3.0
        xs = [p[0] for p in region]
        ys = [p[1] for p in region]
        step = spacing * math.sqrt(2)
        sgn = -1 if flip else 1
        cs = [x + sgn * y for x, y in region]
        c = math.floor(min(cs) / step) * step
        while c <= max(cs):
            # line x + sgn*y = c, from y=min-2 to y=max+2
            y0, y1 = min(ys) - 2, max(ys) + 2
            a = (c - sgn * y0, y0)
            b = (c - sgn * y1, y1)
            ivs = seg_intervals(a, b, region)
            for hole in holes:
                ivs = subtract(ivs, seg_intervals(a, b, hole))
            for t0, t1 in ivs:
                p = (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0)
                q = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
                p, q = clip_box(p, q, box)
                if p and math.dist(p, q) >= 4:
                    self.line([p, q], w=HAIR, colour=colour)
            c += step

    def dashed(self, pts, dash=4.0, gap=3.0, w=HAIR, colour=G100):
        """A polyline drawn as dashes (the hidden-line convention)."""
        acc, on, cur = 0.0, True, [pts[0]]
        for a, b in zip(pts, pts[1:]):
            L = math.dist(a, b)
            pos = 0.0
            while pos < L:
                lim = (dash if on else gap) - acc
                if L - pos >= lim:
                    pos += lim
                    p = (a[0] + (b[0] - a[0]) * pos / L, a[1] + (b[1] - a[1]) * pos / L)
                    if on:
                        cur.append(p)
                        if sum(math.dist(u, v) for u, v in zip(cur, cur[1:])) >= 3:
                            self.line(cur, w=w, colour=colour)
                    cur = [p]
                    on, acc = not on, 0.0
                else:
                    acc += L - pos
                    if on:
                        cur.append(b)
                    pos = L

    def svg(self, title: str) -> str:
        palette = "\n  ".join(
            f'<path id="bell_palette_{i}" d="M {700 + 10 * i} 300 L {704 + 10 * i} 300 L {704 + 10 * i} 304 Z" '
            f'fill="{c}" stroke="{c}" stroke-width="2"/>'
            for i, c in enumerate([BRIGHT, G150, G100, G75, G50, BLACK]))
        body = "\n  ".join(self.parts)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n'
                f'  <!-- bell · revision pass 02 · {title} · rest (defaults). Generated by sketch.py -->\n'
                f'  <g id="preview_canvas">\n    <rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>\n  </g>\n'
                f'{header()}\n  {palette}\n  {body}\n</svg>\n')


def clip_box(p, q, box):
    x0, y0, x1, y1 = box
    t0, t1 = 0.0, 1.0
    dx, dy = q[0] - p[0], q[1] - p[1]
    for pp, qq in ((-dx, p[0] - x0), (dx, x1 - p[0]), (-dy, p[1] - y0), (dy, y1 - p[1])):
        if pp == 0:
            if qq < 0:
                return None, None
            continue
        t = qq / pp
        if pp < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
    if t0 >= t1:
        return None, None
    return (p[0] + dx * t0, p[1] + dy * t0), (p[0] + dx * t1, p[1] + dy * t1)


def dedupe(pts):
    out = []
    for p in pts:
        p = (round(p[0], 2), round(p[1], 2))
        if not out or math.dist(out[-1], p) >= 0.6:
            out.append(p)
    if len(out) > 2 and math.dist(out[0], out[-1]) < 0.6:
        out.pop()
    return out


def chunks(pts, size):
    if len(pts) <= size:
        yield pts
        return
    i = 0
    while i < len(pts) - 1:
        yield pts[i:i + size]
        i += size - 1


def norm2(v):
    l = math.hypot(*v) or 1.0
    return (v[0] / l, v[1] / l)


def ribbon(pts, w):
    h = w / 2
    left, right = [], []
    for i, p in enumerate(pts):
        if i == 0:
            d = (pts[1][0] - p[0], pts[1][1] - p[1])
            nx, ny = norm2((-d[1], d[0]))
            m = 1.0
        elif i == len(pts) - 1:
            d = (p[0] - pts[i - 1][0], p[1] - pts[i - 1][1])
            nx, ny = norm2((-d[1], d[0]))
            m = 1.0
        else:
            a = norm2((p[0] - pts[i - 1][0], p[1] - pts[i - 1][1]))
            b = norm2((pts[i + 1][0] - p[0], pts[i + 1][1] - p[1]))
            n1, n2 = (-a[1], a[0]), (-b[1], b[0])
            nx, ny = norm2((n1[0] + n2[0], n1[1] + n2[1]))
            cos = nx * n1[0] + ny * n1[1]
            m = min(1 / max(cos, 1e-3), 2.5)
        left.append((p[0] + nx * h * m, p[1] + ny * h * m))
        right.append((p[0] - nx * h * m, p[1] - ny * h * m))
    return left + right[::-1]


def header() -> str:
    steps = [BLACK, G50, G75, G100, G125, G150, G175, BRIGHT]
    rows = [f'    <rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>' for i, c in enumerate(steps)]
    for i, label in enumerate(["depth", "air", "knee", "gain"]):
        ink = "#CBCBCB" if i < 2 else BLACK
        rows.append(f'    <text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{ink}" stroke="none" '
                    f'font-family="{FONT}" font-size="10px">{label}</text>')
        rows.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{ink}" stroke="none" '
                    f'font-family="{FONT}" font-size="20px">{CAPTIONS[i]}</text>')
    return '  <g id="preview_header">\n' + "\n".join(rows) + "\n  </g>"


# ---------------------------------------------------------------- projected line drawing
def runs(cam, samples, keep):
    """Split projected samples into runs where keep(point, normal, theta) holds."""
    out, cur = [], []
    for p, nrm, th in samples:
        if keep(p, nrm, th):
            cur.append(cam(p))
        else:
            if len(cur) >= 2:
                out.append(cur)
            cur = []
    if len(cur) >= 2:
        out.append(cur)
    return out


def draw_runs(f, rr, w=HAIR, colour=G100, dashed=False):
    for r in rr:
        (f.dashed(r, w=w, colour=colour) if dashed else f.line(r, w=w, colour=colour))


def outline_of(cam, bell, k=60):
    return hull([cam(p) for p in bell.shell(k)])


def exterior_detail(f, cam, bell, keep_theta=lambda th: True, ribs=12, rib_colour=G75,
                    hoop_colour=G100, min_face=0.3):
    """Hidden-line exterior: hoop bands and meridian ribs where they face the camera."""
    s0, s1, rim = bell.shoulder_idx()
    def vis(lim):
        return lambda p, nrm, th: cam.facing(p, nrm) > lim and keep_theta(th)
    for idx in (s0, s1, s1 + 1, s1 + 2, s1 + 3):
        if idx < len(bell.outer):
            draw_runs(f, runs(cam, bell.ring(bell.outer, idx, 96), vis(0.04)), colour=hoop_colour)
    if bell.lip > 0:
        draw_runs(f, runs(cam, bell.ring(bell.outer, len(bell.outer) - 2, 96), vis(0.04)), colour=hoop_colour)
    for i in range(ribs):
        th = 2 * math.pi * (i + 0.5) / ribs
        draw_runs(f, runs(cam, bell.meridian(bell.outer[1:s1 + 4], th), vis(min_face)), colour=rib_colour)


def cable(f, cam, top_pt, bell, colour=G125):
    a, b = cam(top_pt), cam(bell.crown())
    eye = (b[0], b[1] - 4)
    f.line([a, (eye[0], eye[1] - 3.2)], w=HAIR, colour=colour)
    f.circle(eye[0], eye[1], 3.2, fill=BLACK, stroke=colour, sw=HAIR)


# ---------------------------------------------------------------- control mappings
def gain_amt(g=P["gain"]):
    """Makeup x1..x16 (exponential), as 0..1 of its log range: the normalised value itself."""
    return g


# ================================================================ v1 · centred hero, front elevation
def v1() -> Frame:
    """Front elevation (ortho, 10 degrees down), the bell centred, its front-right quarter cut away
    so the air pocket, the water and the clapper show. Brightest: the clapper (the sound source)."""
    f = Frame()
    cam = Cam((0, -10, 10 * math.tan(math.radians(10))), (0, 0, 0))
    surface = 0.0
    zrim = lambda d: -(Bell.H + 0.2 + 0.85 * d)              # depth: crown 0.2 -> 1.05 below the surface
    ends = Bell(zrim(0)).shell() + Bell(zrim(1)).shell() + [(0, 0, surface)]
    cam.fit(ends, (150, 31, 330, 207))
    b = Bell(zrim(P["depth"]), lip=0.06)
    # the surface: one hairline, full width
    y_s = cam((0, 0, surface))[1]
    f.line([(14, y_s), (466, y_s)], w=HAIR, colour=G100)
    cable(f, cam, (0, 0, surface), b)

    cutaway = lambda th: not (-math.pi / 2 < ((th + math.pi) % (2 * math.pi)) - math.pi < 0)
    out = outline_of(cam, b)
    f.body(out, stroke=G50, sw=HAIR)                          # dark body behind everything bell
    # interior, rear-right quarter (seen through the cut): hoops on the inner surface
    for z in (b.zw + 0.18, b.zw + 0.42, b.zw + 0.66):
        if z < b.inner[0][1] - 0.15:
            rr = runs(cam, b.ring(b.inner, z, 40, 0.0, math.pi / 2), lambda *a: True)
            draw_runs(f, rr, colour=G50)
    # water inside: its cut face on the section plane (x >= 0, y = 0), hatched
    zs = [z for _, z, _, _ in b.inner]
    water = [cam(b.P(0, 0, 0)), cam(b.P(b.inner[-1][0], 0, 0)), cam(b.P(b.r_at(b.inner, b.zw), b.zw, 0)),
             cam(b.P(0, b.zw, 0))]
    f.hatch(water, spacing=4, colour=G75, flip=True)
    # waterline: the visible quarter of the surface inside (rear-right arc + its cut edge)
    arc = [cam(b.P(b.rw, b.zw, th)) for th in [math.pi / 2 * i / 24 for i in range(25)]]
    f.line(arc[::-1] + [cam(b.P(0, b.zw, 0))], w=LINE, colour=G125)
    # the cut wall on the section plane: outer and inner profile, hatched the other way
    sec = [cam(b.P(r, z, 0)) for r, z, _, _ in b.outer] + [cam(b.P(r, z, 0)) for r, z, _, _ in b.inner[::-1]]
    f.hatch(sec, spacing=3.2, colour=G100)
    f.line([cam(b.P(r, z, 0)) for r, z, _, _ in b.outer], w=LINE, colour=G150)
    f.line([cam(b.P(r, z, 0)) for r, z, _, _ in b.inner], w=HAIR, colour=G100)
    f.line([cam(b.P(b.outer[-1][0], 0, 0)), cam(b.P(b.inner[-1][0], 0, 0))], w=HAIR, colour=G100)
    # the front cut plane (x = 0, y < 0) is edge-on from the front: its crown edge closes the cut
    f.line([cam(b.P(0, b.H, -math.pi / 2)), cam(b.P(0, b.H - b.WALL, -math.pi / 2))], w=HAIR, colour=G100)
    # exterior, everything but the removed quarter
    exterior_detail(f, cam, b, keep_theta=cutaway, ribs=14)
    # silhouette: left profile edge + rim arc of the kept part
    left = [cam(b.P(r, z, math.pi)) for r, z, _, _ in b.outer]
    f.line(left, w=LINE, colour=G150)
    rim = runs(cam, b.ring(b.outer, len(b.outer) - 1, 96), lambda p, nrm, th: cutaway(th))
    draw_runs(f, rim, w=LINE, colour=G150)
    # the clapper: hung from the crown, swung out by gain toward the cut (rotation 4 -> 34 degrees)
    ang = math.radians(4 + 30 * gain_amt())
    piv = b.P(0, b.H - b.WALL - 0.02, 0)
    L = (b.H - b.WALL) * 0.78
    ball = add(piv, mul((math.sin(ang), 0, -math.cos(ang)), L * b.s))
    # swing range: a dashed hairline arc from hanging to the swing's end
    sw = [cam(add(piv, mul((math.sin(a), 0, -math.cos(a)), L * b.s)))
          for a in [ang * i / 12 for i in range(13)]]
    f.dashed(sw, dash=3, gap=3, colour=G75)
    f.line([cam(piv), cam(ball)], w=LINE, colour=G125)
    bp = cam(ball)
    f.circle(bp[0], bp[1], 0.1 * cam.ppu(ball), fill=BRIGHT, stroke=BRIGHT, sw=HAIR)
    return f


# ================================================================ v2 · low horizon, top-down plan
def v2() -> Frame:
    """Looking down through the water from above, steeply: the bell is a black cut-out in a hatched
    field (negative space), its rim's ring mode drawn bright. Depth is size from distance."""
    f = Frame()
    cam = Cam((0.9, -2.6, 4.2), (0, 0, -1.6), persp=True)
    zrim = lambda d: -(Bell.H + 0.25 + 2.3 * d)
    ends = Bell(zrim(0)).shell() + Bell(zrim(1)).shell()
    cam.fit(ends, (170, 70, 310, 206))
    b = Bell(zrim(P["depth"]), lip=0.05)
    out = outline_of(cam, b)
    # the field: the water's surface, hatched; the bell cut out of it
    field = [(14, 34), (466, 34), (466, 210), (14, 210)]
    hole = thin(out)
    f.hatch(field, spacing=6, colour=G50, holes=[hole])
    # a low horizon: the field's far edge as a single hairline, with the cable dropping through it
    f.line([(14, 34), (466, 34)], w=HAIR, colour=G75)
    top = cam((0, 0, 0.0))
    f.body(out, stroke=G100, sw=HAIR)
    cable(f, cam, (0, 0, 0.0), b, colour=G100)
    exterior_detail(f, cam, b, ribs=10, rib_colour=G50, hoop_colour=G75, min_face=0.4)
    # air: the waterline inside, seen through the shell as a hidden (dashed) ring
    ring = [cam(p) for p, _, _ in b.ring(b.inner, b.zw, 72)]
    f.dashed(ring, dash=4, gap=3, colour=G100)
    # gain: the rim rings in its (2,0) mode, an oval about the round rim; deflection 0.02 -> 0.24
    amp = 0.02 + 0.22 * gain_amt()
    r0 = b.outer[-1][0]
    rim_rest = [cam(b.P(r0, 0, 2 * math.pi * i / 72)) for i in range(73)]
    f.line(rim_rest, w=HAIR, colour=G75)
    rim_mode = [cam(b.P(r0 * (1 + amp * math.cos(2 * (2 * math.pi * i / 56))), 0, 2 * math.pi * i / 56))
                for i in range(56)]
    f.poly(rim_mode, fill="none", stroke=BRIGHT, sw=SUBJ)
    return f


# ================================================================ v3 · column-affine section
def v3() -> Frame:
    """The bell in section, straight on (8 degrees down), its parts under their own columns:
    depth's sounding line in column 1, the air pocket in column 2, the knee's shoulder in 3,
    gain's hammer in 4. Brightest: where the hammer's note lands on the sound-bow."""
    f = Frame()
    cam = Cam((0, -10, 10 * math.tan(math.radians(8))), (0, 0, 0))
    zrim = lambda d: -(Bell.H + 0.12 + 0.55 * d)
    ends = Bell(zrim(0)).shell() + Bell(zrim(1)).shell() + [(0, 0, 0)]
    cam.fit(ends, (138, 32, 342, 208))
    cam.ox += 0
    b = Bell(zrim(P["depth"]), lip=0.07)
    y_s = cam((0, 0, 0))[1]
    f.line([(14, y_s), (466, y_s)], w=HAIR, colour=G100)
    cable(f, cam, (0, 0, 0), b)
    # column 1, depth: a sounding line from the surface down to the bell's rim level, its lead at the end
    x1 = 60
    y_rim = cam(b.P(0, 0, 0))[1]
    f.line([(x1, y_s), (x1, y_rim - 7)], w=HAIR, colour=G100)
    lead = [(x1 - 3, y_rim - 7), (x1 + 3, y_rim - 7), (x1 + 2, y_rim), (x1 - 2, y_rim)]
    f.poly(lead, fill=BLACK, stroke=G125, sw=HAIR)
    for y in range(int(y_s) + 12, int(y_rim) - 9, 12):         # the line's fathom marks: ticks, no figures
        f.line([(x1 - 3, y), (x1 + 3, y)], w=HAIR, colour=G75)
    f.line([(x1 + 6, y_rim), (cam(b.P(b.outer[-1][0], 0, math.pi))[0] - 6, y_rim)], w=HAIR, colour=G50)
    # the bell: section on the plane y = 0, both halves; inner rear surface seen through the cut
    out = outline_of(cam, b)
    f.body(out, stroke=G50, sw=HAIR)
    for z in (b.zw + 0.2, b.zw + 0.45, b.zw + 0.7):
        if z < b.inner[0][1] - 0.12:
            draw_runs(f, runs(cam, b.ring(b.inner, z, 60, 0, math.pi), lambda *a: True), colour=G50)
    rin0 = b.inner[-1][0]
    water = ([cam(b.P(rin0, 0, math.pi)), cam(b.P(rin0, 0, 0))] +
             [cam(b.P(b.rw, b.zw, 0)), cam(b.P(b.rw, b.zw, math.pi))])
    f.hatch(water, spacing=4, colour=G75, flip=True)
    f.line([cam(b.P(b.rw, b.zw, math.pi)), cam(b.P(b.rw, b.zw, 0))], w=LINE, colour=G125)
    rear = [cam(b.P(b.rw, b.zw, th)) for th in [math.pi * i / 36 for i in range(37)]]
    f.line(rear, w=HAIR, colour=G75)
    for side in (0, math.pi):
        sec = [cam(b.P(r, z, side)) for r, z, _, _ in b.outer] + [cam(b.P(r, z, side)) for r, z, _, _ in b.inner[::-1]]
        f.hatch(sec, spacing=3.2, colour=G100)
        f.line([cam(b.P(r, z, side)) for r, z, _, _ in b.outer], w=LINE, colour=G150)
        f.line([cam(b.P(r, z, side)) for r, z, _, _ in b.inner], w=HAIR, colour=G100)
        f.line([cam(b.P(b.outer[-1][0], 0, side)), cam(b.P(b.inner[-1][0], 0, side))], w=HAIR, colour=G100)
    # column 3, knee: the shoulder fillet's construction (centre mark and the arc continued, hairline)
    s0, s1, _ = b.shoulder_idx()
    a, c_ = b.outer[s0], b.outer[s1]
    # centre of the fillet from the profile's normals
    cr = (a[0] - a[2] * b.rk, a[1] - a[3] * b.rk)
    cpt = cam(b.P(cr[0], cr[1], 0))
    f.line([(cpt[0] - 3, cpt[1]), (cpt[0] + 3, cpt[1])], w=HAIR, colour=G75)
    f.line([(cpt[0], cpt[1] - 3), (cpt[0], cpt[1] + 3)], w=HAIR, colour=G75)
    for p in (a, c_):
        f.dashed([cpt, cam(b.P(p[0], p[1], 0))], dash=3, gap=3, colour=G75)
    # column 4, gain: a hammer on a pivot outside the bell, drawn back from the sound-bow (rotation 6 -> 46 deg)
    bow = b.outer[-2]
    hit = cam(b.P(bow[0] + 0.02, bow[1], 0))
    pv = (hit[0] + 78, hit[1] - 34)
    arm = math.hypot(hit[0] - pv[0], hit[1] - pv[1])
    rest = math.atan2(hit[1] - pv[1], hit[0] - pv[0])
    back = math.radians(6 + 40 * gain_amt())
    ang = rest + back
    head = (pv[0] + arm * math.cos(ang), pv[1] + arm * math.sin(ang))
    sweep = [(pv[0] + arm * math.cos(rest + back * i / 10), pv[1] + arm * math.sin(rest + back * i / 10))
             for i in range(11)]
    f.dashed(sweep, dash=3, gap=3, colour=G75)
    f.line([pv, head], w=LINE, colour=G125)
    f.circle(pv[0], pv[1], 3.5, fill=BLACK, stroke=G125, sw=HAIR)
    ux, uy = math.cos(ang), math.sin(ang)
    px, py = -uy, ux
    hh = [(head[0] + px * 6 - ux * 1, head[1] + py * 6 - uy * 1), (head[0] + px * 6 + ux * 7, head[1] + py * 6 + uy * 7),
          (head[0] - px * 6 + ux * 7, head[1] - py * 6 + uy * 7), (head[0] - px * 6 - ux * 1, head[1] - py * 6 - uy * 1)]
    f.poly(hh, fill=BLACK, stroke=G125, sw=LINE)
    # where the note lands: the struck face of the sound-bow, bright
    lip_pts = [cam(b.P(r, z, 0)) for r, z, _, _ in b.outer[-3:]]
    f.line(lip_pts, w=SUBJ + 0.5, colour=BRIGHT)
    return f


# ================================================================ v4 · off-axis diagonal, three-quarter iso
def v4() -> Frame:
    """Three-quarter isometric, the bell off to the right on a diagonal surface edge, the water's
    hatching closing up with depth (a density gradient). Hidden-line ribs; the waterline dashed."""
    f = Frame()
    az, el = math.radians(-50), math.radians(26)
    cam = Cam((10 * math.cos(az) * math.cos(el), 10 * math.sin(az) * math.cos(el), 10 * math.sin(el)), (0, 0, 0))
    zrim = lambda d: -(Bell.H + 0.3 + 1.2 * d)
    gscale = lambda g: 0.8 * 1.65 ** g                          # gain: x0.80 -> x1.32 (1.65x)
    ends = (Bell(zrim(0), scale=gscale(1)).shell() + Bell(zrim(1) * 1.0, scale=gscale(1)).shell())
    cam.fit(ends, (262, 50, 452, 206))
    b = Bell(zrim(P["depth"]), scale=gscale(P["gain"]), lip=0.05)
    # the surface plane's near edge runs diagonally across: a world line along -x..x at y = 1.6
    e0, e1 = cam((-14, 1.4, 0)), cam((6, 1.4, 0))
    # density gradient: hatch bands under the edge, spacing closing from 11 px to 4 px with depth
    out = thin(outline_of(cam, b))
    bands = [(0.0, 0.6, 11), (0.6, 1.5, 8), (1.5, 2.5, 6), (2.5, 4.5, 4.5)]
    for z0, z1, sp in bands:
        reg = [cam((-14, 1.4, -z0)), cam((6, 1.4, -z0)), cam((6, 1.4, -z1)), cam((-14, 1.4, -z1))]
        f.hatch(reg, spacing=sp, colour=G50, holes=[out])
    f.line([e0, e1], w=HAIR, colour=G100)
    f.body(out, stroke=G100, sw=HAIR)
    cable(f, cam, (0, 0, 0.0), b, colour=G100)
    exterior_detail(f, cam, b, ribs=16, rib_colour=G75, hoop_colour=G100, min_face=0.28)
    # silhouette edge
    f.poly(out, fill="none", stroke=G175, sw=SUBJ)
    # air: the waterline as a hidden ring, dashed
    ring = [cam(p) for p, _, _ in b.ring(b.inner, b.zw, 72)]
    f.dashed(ring, dash=4, gap=3, colour=G125)
    # brightest: the shoulder hoop, where the knee shapes the bell
    s0, s1, _ = b.shoulder_idx()
    mid = (s0 + s1) // 2
    draw_runs(f, runs(cam, b.ring(b.outer, mid, 96), lambda p, nrm, th: cam.facing(p, nrm) > 0.05),
              w=SUBJ, colour=BRIGHT)
    return f


# ================================================================ v5 · full-bleed field, low angle
def v5() -> Frame:
    """From below and in front, looking up into the mouth: the bell large in a full-bleed hatched
    field, the air pocket's waterline and the clapper seen inside. Brightest: the rim (depth's part:
    the whole bell is what depth lowers, and the lip is its leading edge)."""
    f = Frame()
    cam = Cam((0, -4.6, -4.4), (0, 0, -2.0), persp=True)
    zrim = lambda d: -(Bell.H + 0.15 + 0.9 * d)
    ends = Bell(zrim(0)).shell() + Bell(zrim(1)).shell() + [(0, 0, 0)]
    cam.fit(ends, (130, 30, 350, 210))
    b = Bell(zrim(P["depth"]), lip=0.06)
    out = thin(outline_of(cam, b))
    f.hatch([(0, 21), (480, 21), (480, 220), (0, 220)], spacing=7, colour=G50, holes=[out])
    y_s = cam((0, 0, 0))[1]
    cable(f, cam, (0, 0, 0.0), b, colour=G100)
    f.body(out, stroke=G100, sw=HAIR)
    rim_poly = [cam(b.P(b.outer[-1][0], 0, 2 * math.pi * i / 60)) for i in range(60)]
    mouth = [cam(b.P(b.inner[-1][0], 0, 2 * math.pi * i / 60)) for i in range(60)]
    outside = lambda p, nrm, th: cam.facing(p, nrm) > 0.05 and not inside(cam(p), mouth)
    s0, s1, _ = b.shoulder_idx()
    for idx in (s0, s1, s1 + 1, s1 + 2, s1 + 3):
        draw_runs(f, runs(cam, b.ring(b.outer, idx, 96), outside), colour=G100)
    for i in range(16):
        th = 2 * math.pi * (i + 0.5) / 16
        draw_runs(f, runs(cam, b.meridian(b.outer[1:s1 + 4], th),
                           lambda p, nrm, th: cam.facing(p, nrm) > 0.3 and not inside(cam(p), mouth)), colour=G75)
    # inside the mouth: inner hoops above the water, the waterline, the clapper
    inn = lambda p, nrm, th: inside(cam(p), mouth)
    for z in (b.zw + 0.25, b.zw + 0.55):
        if z < b.inner[0][1] - 0.1:
            draw_runs(f, runs(cam, b.ring(b.inner, z, 96), inn), colour=G50)
    wl = [cam(p) for p, _, _ in b.ring(b.inner, b.zw, 72)]
    f.hatch(thin(wl, 1.5), spacing=4, colour=G75, flip=True)
    f.line(wl, w=LINE, colour=G125)
    # gain: the clapper's ball, scale x0.7 -> x1.3 of its radius (1.85x)
    piv = b.P(0, b.H - b.WALL, 0)
    ball = b.P(0, b.zw * 0.35 + 0.05, 0)
    f.line([cam(piv), cam(ball)], w=HAIR, colour=G125)
    rball = 0.11 * (0.7 + 0.6 * gain_amt())
    bp = cam(ball)
    f.circle(bp[0], bp[1], rball * cam.ppu(ball), fill=BLACK, stroke=G150, sw=LINE)
    # the rim, depth's leading edge, brightest
    f.poly(rim_poly, fill="none", stroke=BRIGHT, sw=SUBJ)
    return f


# ---------------------------------------------------------------- candidates
CANDIDATES = {
    "v1": {
        "subject": "The bell centred in front elevation with its front-right quarter cut away, so the air pocket, the hatched water below it and the clapper hanging inside show, on its cable under one surface line.",
        "controls": [
            "depth: the bell is lowered on its cable, crown from just under the surface line to about 70 px below it (position).",
            "air: the waterline inside drops as the air pocket grows from a third to nine tenths of the bell, and the hatched water in the cut shrinks with it (position + hatched area).",
            "knee: the shoulder between crown and wall goes from a hard corner to a full round crown, fillet radius about 2 to 40 px, in the silhouette, the cut wall and every hoop (shape).",
            "gain: the clapper swings out toward the cut, from hanging (4 degrees) to 34 degrees, its travel a dashed hairline arc (rotation); the bright ball is the sound source.",
        ],
        "risks": "The cutaway adds three hatch fields (wall cut, water cut, and the rear interior seen through) inside a 150 px bell: at 1:1 the wall hatching is only 2-3 lines and could read as a grey band. Gain as a clapper's swing angle is a metaphor for loudness, not makeup gain; a resting drawing that shows a swung clapper must stay still at rest. The quarter cut is a fixed drawing; on device every visible run is redrawn when knee or depth change.",
    },
    "v2": {
        "subject": "Looking steeply down through the water at the bell below: a black cut-out in a hatched field, its hidden waterline dashed through the shell and its rim drawn in the ring mode it sounds with.",
        "controls": [
            "depth: the bell sinks away from the camera, so it shrinks and drops toward the bottom of the field (size from distance, about 1.7x, plus position).",
            "air: the dashed waterline ring, seen through the shell, slides up or down the bell and widens or narrows with it (position + shape).",
            "knee: the crown's flat top shrinks into a rounded shoulder, so the top hoops close in and the outline rounds (shape).",
            "gain: the rim's oval ring mode about the round rim grows from barely off-round to a strong four-node flex (shape, about 20 px at the extremes); it's the brightest line.",
        ],
        "risks": "Seen from above, the air pocket is inside an opaque shell, so the waterline is a hidden-line convention the player must learn. The hatched field is all water texture; with the bell small at full depth, the subject could become a dark hole in a grey pattern. Ring-mode oval is a physical picture of ringing but static at rest; it must not move while idle.",
    },
    "v3": {
        "subject": "The bell cut in section on its cable, its parts under their own columns: a sounding line for depth, the air pocket over hatched water, the shoulder's fillet construction, and a hammer drawn back from the sound-bow.",
        "controls": [
            "depth: the bell is lowered, and the sounding line in column 1 pays out with it, its lead weight dropping level with the rim (position).",
            "air: the waterline across the section drops as the pocket grows, the hatched water cut below it shrinking (position + hatched area).",
            "knee: the shoulder fillet in column 3 grows from a hard corner to a full round crown; its centre mark and radius lines move with it (shape).",
            "gain: the hammer in column 4 is drawn back from the sound-bow, from 6 to 46 degrees, its swing a dashed arc (rotation); the struck face of the bow is the brightest line.",
        ],
        "risks": "Column-affine puts four parts in four columns, which edges toward a panel; the sounding line and hammer are additions beside the bell, not the bell itself. The fillet construction lines are drafting marks that could read as decoration. A pure section is the closest to v1 of the five and the least 3D.",
    },
    "v4": {
        "subject": "The bell in three-quarter isometric, off to the right below a diagonal surface edge, in water whose hatching closes up with depth, its waterline a dashed hidden ring and its shoulder the bright hoop.",
        "controls": [
            "depth: the bell sinks into denser hatching, from the open top bands to the close bottom ones (position + the gradient it sits in).",
            "air: the dashed hidden waterline ring slides along the bell (position + shape).",
            "knee: the bright shoulder hoop moves inward and down as the crown rounds, and the outline softens (shape).",
            "gain: the whole bell grows, x0.80 to x1.32 about its crown (scale).",
        ],
        "risks": "Four hatch densities are four nested bands of grey value; spaced 11 to 4.5 px they stay line, not tint, but the 4.5 px band is near the limit. Gain as scale reads as 'bigger', not 'louder', and fights the gradient for what depth means. The surface edge diagonal is a projected world line, so it can't move with depth.",
    },
    "v5": {
        "subject": "Looking up into the bell's mouth from below, the bell large in a full-bleed hatched field: inside, the water's surface and the clapper hanging over it; the rim bright.",
        "controls": [
            "depth: the bell comes down toward the camera, so it grows and lowers in the frame (size from distance, about 1.3x, plus position); the bright rim leads.",
            "air: the waterline ellipse inside the mouth moves up into the bell or down toward the rim as the pocket grows and shrinks, its hatched water with it (position + area).",
            "knee: the crown's shoulder rounds in the silhouette above the rim (shape).",
            "gain: the clapper's ball grows, x0.7 to x1.3 (scale).",
        ],
        "risks": "Seen from below, the inside reads only if the mouth is open enough; at full depth the bell fills much of the field. Full-bleed hatching lowers the black share. The clapper hangs on the axis, so gain's change is concentrated in a small spot near the centre; it may miss the 40 px spread floor.",
    },
}


def main() -> None:
    frames = {"v1": v1, "v2": v2, "v3": v3, "v4": v4, "v5": v5}
    titles = {"v1": "v1 centred hero, front elevation cutaway", "v2": "v2 low horizon, top-down plan",
              "v3": "v3 column-affine section", "v4": "v4 off-axis diagonal, three-quarter iso",
              "v5": "v5 full-bleed field, low angle"}
    for vid, fn in frames.items():
        d = HERE / vid
        d.mkdir(exist_ok=True)
        (d / "rest.svg").write_text(fn().svg(titles[vid]))
        c = {"variant": vid, **CANDIDATES[vid]}
        (d / "candidate.json").write_text(json.dumps(c, indent=2, ensure_ascii=False) + "\n")
    print("wrote", ", ".join(frames))


if __name__ == "__main__":
    main()
