#!/usr/bin/env python3
"""Flock, subject pass 02: five rest-frame sketches from one script.

    python3 screens/flock/passes/02-subject/sketch.py

Pass 01 (pitch plans, labelled elevations, bar histories) was turned down.
These five start from what flock is and does: eight birds crossing a
two-octave pitch field, each bird sounding the scale degree under it as it
crosses into a new cell. Every frame is the rest state at the defaults
(cohere 50 %, speed 1.00, scatter 0, scale pent: 11 degrees over two octaves),
built from one flock model and drawn through a perspective camera.

Rules kept in every frame: the stock header exactly as opxy/templates/frame.svg
has it and no other text; grey only, never red; one brightest element
(#CDCDCD); three weights (hairline 1.1, line 1.5, subject 2.25); states as
line, movement or 45-degree hatching (>= 3 px apart, clipped), never a lighter
grey fill; solid bodies filled black behind their outlines; one subpath and
<= 64 points per path; lines as closed filled ribbons.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parents[3] / "opxy" / "templates" / "frame.svg"

# ------------------------------------------------------------------ state at the defaults
COHERE, SPEED, SCATTER = 0.5, 1.0, 0.0
SCALE = [0, 2, 4, 7, 9]                     # pent
DEG = [12 * o + s for o in range(2) for s in SCALE] + [24]   # 11 cells, low to high
N_DEG = len(DEG)
N_BIRDS = 8

G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
HAIR, LINE, SUBJ = 1.1, 1.5, 2.25


def flock(seed: int = 11):
    """Eight birds in the flock's own frame: (u across the pitch field 0..1, h height -1..1, d depth -1..1).

    Cohesion sets the spread round the centre; scatter (0 here) would push some birds far out.
    """
    rnd = random.Random(seed)
    spread = 0.07 + 0.26 * (1 - COHERE)
    cu = 0.55
    out = []
    for i in range(N_BIRDS):
        a = 2 * math.pi * (i / N_BIRDS) + rnd.uniform(-0.35, 0.35)
        r = 0.45 + 0.55 * rnd.random()
        out.append((cu + spread * r * math.cos(a) * 1.25, 0.9 * r * math.sin(a) * 0.8, rnd.uniform(-1, 1)))
    return out


BIRDS = flock()


def cell(u: float) -> int:
    return min(N_DEG - 1, max(0, round(u * (N_DEG - 1))))


# ------------------------------------------------------------------ geometry helpers
def fmt(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def dedupe(pts):
    out = []
    for p in pts:
        if not out or math.dist(p, out[-1]) >= 0.25:
            out.append(p)
    while len(out) > 2 and math.dist(out[0], out[-1]) < 0.3:
        out.pop()
    return out


def hull(pts):
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in pts))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]


def thin(pts, n=60):
    """Keep at most n points of a closed outline, evenly by index."""
    if len(pts) <= n:
        return pts
    return [pts[int(i * len(pts) / n)] for i in range(n)]


def ell(cx, cy, rx, ry, n=40, a0=0.0, a1=2 * math.pi):
    full = abs(a1 - a0 - 2 * math.pi) < 1e-9
    k = n if full else n + 1
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(k)]


def seg_poly(a, b, poly):
    """Parts of segment a-b inside polygon poly (even-odd), as (p, q) pairs."""
    ts = []
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        ex, ey = x1 - x0, y1 - y0
        den = dx * ey - dy * ex
        if abs(den) < 1e-12:
            continue
        t = ((x0 - a[0]) * ey - (y0 - a[1]) * ex) / den
        s = ((x0 - a[0]) * dy - (y0 - a[1]) * dx) / den
        if 0 <= t <= 1 and 0 <= s < 1:
            ts.append(t)
    ts.sort()
    out = []
    for i in range(0, len(ts) - 1, 2):
        t0, t1 = ts[i], ts[i + 1]
        out.append(((a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0),
                    (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)))
    return out


# ------------------------------------------------------------------ camera
def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross3(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    L = math.sqrt(dot(a, a))
    return (a[0] / L, a[1] / L, a[2] / L)


class Camera:
    """Perspective camera, world y up. Screen x right, screen y down."""

    def __init__(self, eye, target, f, centre):
        self.e = eye
        self.fw = norm(sub(target, eye))
        self.rt = norm(cross3((0, 1, 0), self.fw))
        self.up = cross3(self.fw, self.rt)
        self.f, self.c = f, centre

    def depth(self, p):
        return dot(sub(p, self.e), self.fw)

    def __call__(self, p):
        d = sub(p, self.e)
        z = dot(d, self.fw)
        return (self.c[0] + self.f * dot(d, self.rt) / z, self.c[1] - self.f * dot(d, self.up) / z)


def rot_y(p, a):
    c, s = math.cos(a), math.sin(a)
    return (p[0] * c + p[2] * s, p[1], -p[0] * s + p[2] * c)


def rot_x(p, a):
    c, s = math.cos(a), math.sin(a)
    return (p[0], p[1] * c - p[2] * s, p[1] * s + p[2] * c)


def rot_z(p, a):
    c, s = math.cos(a), math.sin(a)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def scl(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


# ------------------------------------------------------------------ the bird, modelled once
# Local frame: x forward (beak), y up, z to the bird's right. A starling seen in plan: short
# triangular swept wings, a pointed head, a short square tail. Wing points carry their span
# fraction so dihedral (wing up or down) and sweep can bend them.
_HALF = [  # (x, z) from the beak back along the right side, then the tail
    (0.55, 0.00), (0.47, 0.06), (0.34, 0.09), (0.20, 0.11),            # beak, head, neck
    (0.24, 0.30), (0.22, 0.55), (0.12, 0.85), (-0.05, 1.12),           # wing leading edge
    (-0.14, 1.18), (-0.16, 1.02), (-0.10, 0.78), (-0.12, 0.50),        # tip, trailing edge
    (-0.14, 0.26), (-0.12, 0.10),                                      # wing root
    (-0.30, 0.08), (-0.52, 0.15), (-0.58, 0.00),                       # rump, tail
]


def bird_local(dihedral=0.25, sweep=0.0, size=1.0):
    pts = []
    side = _HALF + [(x, -z) for x, z in reversed(_HALF[1:-1])]
    for x, z in side:
        span = max(0.0, (abs(z) - 0.1) / 1.08)
        # sweep: wing points rotate back about the root (0.2, 0.15)
        if span > 0:
            ang = sweep * span
            rx, rz = x - 0.05, abs(z) - 0.11
            x = 0.05 + rx * math.cos(ang) - rz * math.sin(ang)
            az = 0.11 + rx * math.sin(ang) + rz * math.cos(ang)
            z = math.copysign(az, z)
        y = dihedral * span * span * 1.0 + 0.02 * (1 - span)
        pts.append((x * size, y * size, z * size))
    return pts


def bird_world(pos, heading=0.0, pitch=0.0, bank=0.0, dihedral=0.25, sweep=0.0, size=1.0):
    out = []
    for p in bird_local(dihedral, sweep, size):
        p = rot_x(p, bank)
        p = rot_z(p, pitch)
        p = rot_y(p, heading)
        out.append(add(p, pos))
    return out


# ------------------------------------------------------------------ frame writer
class Frame:
    def __init__(self, title: str):
        self.title = title
        self.items: list[str] = []

    def add(self, s: str) -> None:
        self.items.append(s)

    def poly(self, pts, fill, stroke="none", sw=0.0):
        pts = dedupe(pts)
        if len(pts) < 3:
            return
        assert len(pts) <= 64, len(pts)
        d = "M " + " L ".join(f"{fmt(x)} {fmt(y)}" for x, y in pts) + " Z"
        sws = f' stroke-width="{fmt(sw)}"' if stroke != "none" else ' stroke-width="0"'
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def outline(self, pts, stroke, sw, fill=G0):
        self.poly(thin(dedupe(pts)), fill, stroke, sw)

    def ribbon(self, pts, w, colour):
        """An open polyline of width w as closed filled ribbons, <= 30 points a side each."""
        pts = dedupe(pts)
        if len(pts) < 2:
            return
        i = 0
        while i < len(pts) - 1:
            self._piece(pts[i:i + 31], w, colour)
            i += 30

    def _piece(self, seg, w, colour):
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
                if math.hypot(dx, dy) < 1e-6:
                    dx, dy = ax, ay
            ln = math.hypot(dx, dy) or 1
            nx, ny = -dy / ln, dx / ln
            left.append((x + nx * h, y + ny * h))
            right.append((x - nx * h, y - ny * h))
        self.poly(left + right[::-1], colour)

    def line(self, a, b, w, colour):
        if math.dist(a, b) >= 1.0:
            self._piece([a, b], w, colour)

    def hatch(self, region, colour=G2, gap=4.0, w=HAIR, phase=0.0):
        """45-degree hairlines (rising to the right), gap px apart, clipped to region."""
        region = dedupe(region)
        xs = [p[0] for p in region]
        ys = [p[1] for p in region]
        step = gap * math.sqrt(2)
        c0 = min(x + y for x, y in region)
        c1 = max(x + y for x, y in region)
        c = c0 + ((phase - c0) % step)
        x0, x1 = min(xs) - 2, max(xs) + 2
        while c < c1:
            a, b = (x0, c - x0), (x1, c - x1)
            for p, q in seg_poly(a, b, region):
                if math.dist(p, q) > 2.5:
                    self.line(p, q, w, colour)
            c += step

    def svg(self) -> str:
        head = TEMPLATE.read_text(encoding="utf-8")
        s0 = head.index('  <g id="preview_canvas">')
        s1 = head.index("  <!-- Palette entries")
        out = ['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
               f"  <title>flock · subject pass 02 · {self.title}</title>",
               head[s0:s1].rstrip()]
        out += ["  " + s for s in self.items]
        out.append("</svg>")
        return "\n".join(out) + "\n"


# ================================================================== v1 · cutaway · bold closed outlines
def v1() -> Frame:
    """A reed bed that is a pan pipe: each reed cut open to show the node that stops it.

    The air column above a reed's node sets its pitch (two octaves: 4:1 in length), so the
    cutaway explains the field: a bird skimming a reed's mouth blows it.
    """
    F = Frame("v1 · reed bed cut open · bold closed outlines")
    cam = Camera((0.0, 6.6, -11.5), (0.2, 0.9, 0.0), 500, (240, 146))
    rnd = random.Random(4)
    n = N_DEG
    R = 0.27
    reeds = []
    for i in range(n):
        x = -4.9 + 9.8 * i / (n - 1)
        z = 0.3 * math.sin(i * 1.7) + rnd.uniform(-0.12, 0.12)
        top = 1.75 + 0.2 * math.sin(i * 2.3 + 0.4) + rnd.uniform(-0.08, 0.08)
        col = 1.6 * 2 ** (-DEG[i] / 12)          # air column, 1.6 .. 0.4: two octaves
        reeds.append((x, z, top, top - col))
    birds = []
    for k, (u, h, d) in enumerate(BIRDS):
        birds.append((-4.9 + 9.8 * u, 2.75 + 0.45 * h, 0.4 * d))
    # the bird that plays now: skimming the mouth of the reed under it
    lo = min(range(N_BIRDS), key=lambda k: birds[k][1])
    ri = cell((birds[lo][0] + 4.9) / 9.8)
    birds[lo] = (reeds[ri][0] - 0.2, reeds[ri][2] + 0.42, reeds[ri][1])

    def ring(x, z, y, r, a0=0.0, a1=2 * math.pi, n_=40):
        return [cam((x + r * math.cos(a0 + (a1 - a0) * t / n_), y, z + r * math.sin(a0 + (a1 - a0) * t / n_)))
                for t in range(n_ + 1)]

    order = sorted(range(n), key=lambda i: -cam.depth((reeds[i][0], 0, reeds[i][1])))
    for i in order:
        x, z, top, node = reeds[i]
        playing = i == ri
        cut = node - 0.3
        bottom = -4.0
        edge = G5 if playing else G4
        sil = hull(ring(x, z, top, R) + ring(x, z, bottom, R))
        F.outline(sil, edge, LINE)
        # back wall inside: two hairlines from the rim down to the node
        for a in (math.radians(65), math.radians(115)):
            p0 = cam((x + 0.82 * R * math.cos(a), top, z + 0.82 * R * math.sin(a)))
            p1 = cam((x + 0.82 * R * math.cos(a), node, z + 0.82 * R * math.sin(a)))
            F.line(p0, p1, HAIR, G4 if playing else G2)
        # rim: the inner back arc shows the wall's thickness
        F.ribbon(ring(x, z, top, 0.8 * R, 0, math.pi, 20), HAIR, G3)
        # the node that stops the column
        F.outline(ring(x, z, node, 0.82 * R, n_=36)[:-1], G6 if playing else G4, LINE)
        # the front wall, cut away above the node: its cut edge is the front half of a ring
        front = ring(x, z, cut, R, math.pi, 2 * math.pi, 20)
        lower = ring(x, z, bottom, R, math.pi, 2 * math.pi, 20)
        F.outline(front + lower[::-1], edge, LINE)
        # joints further down the stalk
        for j in (1.1, 2.3):
            yj = cut - j
            F.ribbon(ring(x, z, yj, R, math.pi * 1.06, math.pi * 1.94, 14), HAIR, G2)
    # birds over the mouths, flying right and banking towards us; the one at a mouth is brightest
    for k in sorted(range(N_BIRDS), key=lambda k: -cam.depth(birds[k])):
        x, y, z = birds[k]
        pts = [cam(p) for p in bird_world((x, y, z), heading=math.radians(-62 + 12 * BIRDS[k][2]),
                                          bank=math.radians(0), dihedral=(0.05, 0.25, 0.4)[(k * 5) % 3],
                                          size=0.62)]
        F.outline(pts, G7 if k == lo else G5, SUBJ if k == lo else LINE)
    return F


# ================================================================== v2 · trace · cutaway section
def v2() -> Frame:
    """Wing prints left in snow where the flock touched down, the field cut open in section."""
    F = Frame("v2 · wing prints in snow · cutaway section")
    cam = Camera((0.0, 6.4, -9.0), (0.0, -0.2, 2.2), 430, (240, 104))
    n = N_DEG
    X0, X1 = -5.4, 5.4
    Z0, Z1 = 0.0, 5.0
    pitch = (X1 - X0) / n
    SNOW = 0.32

    def ground(x):
        """Furrow profile: one ridge per cell, centred on the cell."""
        t = (x - X0) / pitch
        return 0.18 * math.cos(2 * math.pi * (t - 0.5))

    def snow(x):
        return ground(x) * 0.45 + SNOW

    xs = [X0 + (X1 - X0) * k / 60 for k in range(61)]
    back = [cam((x, snow(x), Z1)) for x in xs]
    front = [cam((x, snow(x), Z0)) for x in xs]
    F.outline(thin(front[::2] + back[::-2], 62), G3, LINE)
    # ridge lines receding along each furrow crest
    for i in range(n):
        xc = X0 + pitch * (i + 0.5)
        F.line(cam((xc, snow(xc), Z0)), cam((xc, snow(xc), Z1)), HAIR, G2)
    # the section face at z = Z0: snow layer (black) over cut soil (hatched)
    base = -1.25
    soil = [cam((x, ground(x), Z0)) for x in xs[::2]]
    soil_poly = soil + [cam((X1, base, Z0)), cam((X0, base, Z0))]
    F.poly(soil_poly, G0)
    F.hatch(soil_poly, G3, 4.0)
    F.ribbon(soil, HAIR, G4)
    side = [cam((X1, snow(X1), Z0)), cam((X1, snow(X1), Z1)), cam((X1, base, Z1)), cam((X1, base, Z0))]
    F.outline(side, G3, LINE)
    F.hatch(side, G2, 4.0)
    sec = [cam((x, snow(x), Z0)) for x in xs[::2]] + [cam((X1, base, Z0)), cam((X0, base, Z0))]
    F.outline(sec, G4, LINE, fill="none")

    def on_snow(x, z):
        return cam((x, snow(x) - 0.02, z))

    def print_at(x, z, yaw, size, newest):
        """A bird's spread wings pressed into the snow, with the primaries' marks."""
        pts = []
        for (px, _, pz) in bird_local(0.0, 0.0, size):
            p = rot_y((px, 0, pz), yaw)
            pts.append(on_snow(x + p[0], z + p[2]))
        F.outline(pts, G7 if newest else G4, SUBJ if newest else LINE)
        for side_ in (1, -1):
            wrist = (0.1 * size, side_ * 0.62 * size)
            for f_ in range(3):
                tip = ((-0.06 - 0.03 * f_) * size, side_ * (0.82 + 0.13 * f_) * size)
                p0 = rot_y((wrist[0], 0, wrist[1]), yaw)
                p1 = rot_y((tip[0], 0, tip[1]), yaw)
                F.line(on_snow(x + p0[0], z + p0[2]), on_snow(x + p1[0], z + p1[2]), HAIR, G5 if newest else G2)

    # each touch-down left one print; the flock landed across a few furrows (cohere), in a line
    # running back into the field (speed spaces them); the nearest is the newest, the note now
    marks = []
    for k, (u, h, d) in enumerate(BIRDS):
        x = X0 + (X1 - X0) * u
        z = 0.9 + 0.5 * k + 0.2 * d
        marks.append((x, z, math.radians(-90 + 22 * d + (8 if k % 2 else -8)), k))
    marks.sort(key=lambda t: -t[1])
    for j, (x, z, yaw, k) in enumerate(marks):
        print_at(x, z, yaw, 0.82, j == len(marks) - 1)
    return F


# ================================================================== v3 · one detail · exploded view
def v3() -> Frame:
    """One bird at large scale, exploded like a model kit; its neighbours cut by the frame's edge."""
    F = Frame("v3 · one bird, exploded · exploded view")
    cam = Camera((-2.6, 8.4, -7.0), (0.3, 0.0, 0.25), 300, (236, 124))
    E = 3.3 * (0.18 + 0.36 * (1 - COHERE))               # explosion: cohere pulls the parts together
    yaw = math.radians(8)
    S_ = 3.3

    def P(p, off=(0, 0, 0)):
        return cam(add(rot_y(scl(p, S_), yaw), off))

    # neighbours, assembled, cut by the frame's edge: the rest of the flock
    for (pos, hd, sz) in (((-8.6, 0.0, 1.4), 0.1, 2.2), ((8.4, 0.0, -2.6), -0.1, 2.2),
                          ((5.8, 0.0, 6.2), -0.2, 2.0)):
        pts = [cam(p) for p in bird_world(pos, heading=hd, dihedral=0.15, size=sz)]
        F.outline(pts, G3, LINE)

    # body: an ellipsoid; silhouette from its projected hull, section rings and spine inside
    a, b, c = 0.62, 0.2, 0.19
    body_pts = []
    for i in range(20):
        th = math.pi * i / 19
        for j in range(20):
            ph = 2 * math.pi * j / 20
            body_pts.append(P((a * math.cos(th), b * math.sin(th) * math.cos(ph), c * math.sin(th) * math.sin(ph))))

    off_r = scl((0.0, 0.25, 1.0), E)            # right wing: out and up
    off_l = scl((0.0, 0.25, -1.0), E)           # left wing
    off_t = scl((-1.0, 0.05, 0.0), E * 0.8)     # tail back

    # wing: the arm (coverts) plus the primaries fanned from the wrist, each pulled out a little
    def wing(side):
        arm = [(0.18, 0.04, 0.12), (0.24, 0.06, 0.32), (0.22, 0.08, 0.56), (0.06, 0.09, 0.66),
               (-0.12, 0.09, 0.6), (-0.14, 0.06, 0.32), (-0.12, 0.04, 0.12)]
        arm = [(x, y, side * z) for x, y, z in arm]
        k = 5 if side < 0 else 6                  # degrees: low octave on the left, high on the right
        feathers = []
        wrist = (0.04, 0.09, side * 0.62)
        for f in range(k):
            t = f / (k - 1)
            ang = math.radians(8 + 72 * t)       # fanned from forward-out to back-out
            L = 0.62 - 0.22 * t
            d = (-math.sin(ang), 0.05, side * math.cos(ang))
            gap = 0.06 + 0.22 * E / S_
            base = add(wrist, scl(d, gap))
            pts = []
            for s in range(13):
                u = s / 12
                w = 0.055 * math.sin(math.pi * min(1, u * 1.05)) ** 0.7 + 0.012
                q = add(base, scl(d, L * u))
                nrm = (math.cos(ang), 0, side * math.sin(ang))
                pts.append(add(q, scl(nrm, w)))
            for s in range(12, -1, -1):
                u = s / 12
                w = 0.055 * math.sin(math.pi * min(1, u * 1.05)) ** 0.7 + 0.012
                q = add(base, scl(d, L * u))
                nrm = (math.cos(ang), 0, side * math.sin(ang))
                pts.append(sub(q, scl(nrm, w)))
            feathers.append((pts, base, add(base, scl(d, L))))
        return arm, feathers

    tail = [(-0.5, 0.0, 0.06), (-0.95, 0.0, 0.17), (-1.0, 0.0, 0.06), (-1.0, 0.0, -0.06), (-0.95, 0.0, -0.17),
            (-0.5, 0.0, -0.06)]

    def assembly(p0, off):
        q0 = rot_y(scl(p0, S_), yaw)
        q1 = add(q0, off)
        L = math.dist(q0, q1)
        nseg = max(2, int(L / 0.07))
        for s in range(0, nseg, 2):
            F.line(cam(add(q0, scl(sub(q1, q0), s / nseg))), cam(add(q0, scl(sub(q1, q0), (s + 1) / nseg))),
                   HAIR, G3)

    assembly((0.05, 0.05, 0.2), off_r)
    assembly((0.05, 0.05, -0.2), off_l)
    assembly((-0.5, 0.0, 0.0), off_t)

    parts = [("tail", off_t), ("wl", off_l), ("body", (0, 0, 0)), ("wr", off_r)]
    parts.sort(key=lambda p: -cam.depth(add(p[1], (0, 0, 0.6 if p[0] == "wr" else (-0.6 if p[0] == "wl" else 0)))))
    for name, off in parts:
        if name == "body":
            F.outline(hull(body_pts), G5, LINE)
            for t in (-0.5, 0.0, 0.5):
                r = math.sqrt(1 - t * t)
                ring = [P((a * t, b * r * math.cos(ph), c * r * math.sin(ph)))
                        for ph in [math.pi * (-0.5 + s / 20) for s in range(21)]]
                F.ribbon(ring, HAIR, G3)
            spine = [P((a * math.cos(th), b * math.sin(th), 0)) for th in [math.pi * s / 20 for s in range(21)]]
            F.ribbon(spine, HAIR, G3)
            bk = [P((0.58, 0.04, 0.05)), P((0.86, 0.0, 0.0)), P((0.58, -0.04, -0.05)), P((0.57, 0.05, -0.04))]
            F.outline(hull(bk), G5, LINE)
            e = P((0.45, 0.1, 0.09))
            F.outline(ell(e[0], e[1], 2.6, 2.6, 14), G5, HAIR)
        elif name == "tail":
            F.outline([P(p, off) for p in tail], G4, LINE)
            for zz in (-0.08, 0.0, 0.08):
                F.line(P((-0.55, 0.0, zz * 0.4), off), P((-0.97, 0.0, zz * 1.4), off), HAIR, G2)
        else:
            side = 1 if name == "wr" else -1
            arm, feathers = wing(side)
            fs = sorted(enumerate(feathers), key=lambda kv: -cam.depth(add(rot_y(kv[1][1], yaw), off)))
            for f, (pts, b0, b1) in fs:
                lit = side > 0 and f == 2         # the degree this bird sounds now
                F.outline([P(p, off) for p in pts], G7 if lit else G4, SUBJ if lit else LINE)
                F.line(P(b0, off), P(add(b0, scl(sub(b1, b0), 0.85)), off), HAIR, G5 if lit else G2)
            F.outline([P(p, off) for p in arm], G4, LINE)
            for t in (0.33, 0.66):
                F.line(P((0.2 - 0.3 * t * 0, 0.05, side * (0.14 + 0.45 * t)), off),
                       P((-0.12, 0.06, side * (0.14 + 0.45 * t)), off), HAIR, G2)
    return F


# ================================================================== v4 · the flock itself · single-weight contour
def v4() -> Frame:
    """Eight starlings in flight over a ploughed field, drawn in one contour weight; shadows hatched."""
    F = Frame("v4 · starlings over the field · single-weight contour")
    cam = Camera((0.0, 26.0, -10.0), (0.0, 0.0, 7.0), 640, (240, 116))
    n = N_DEG
    X0, X1 = -6.0, 6.0
    zf = 60.0
    rows = [X0 + (X1 - X0) * i / n for i in range(n + 1)]
    birds = []
    for k, (u, h, d) in enumerate(BIRDS):
        birds.append((X0 + (X1 - X0) * u, 4.2 + 1.0 * d, 7.0 + 4.4 * h))
    lo = min(range(N_BIRDS), key=lambda k: cam.depth(birds[k]))   # nearest bird plays now
    ci = cell((birds[lo][0] - X0) / (X1 - X0))
    # drill rows, one per cell, to the horizon; the row under the playing bird is drawn heavier
    for i in range(n):
        xc = (rows[i] + rows[i + 1]) / 2
        p0, p1 = cam((xc, 0, -2.0)), cam((xc, 0, 16.0))
        F.line(p0, p1, LINE if i == ci else HAIR, G4 if i == ci else G2)
    poses = []
    for k in range(N_BIRDS):
        phase = (k * 3) % 4
        poses.append(dict(heading=math.radians(-12 + 16 * BIRDS[k][1]), bank=math.radians(6 * (phase - 1.5)),
                          dihedral=(-0.2, 0.05, 0.3, 0.5)[phase], sweep=(0.0, 0.15, 0.3, 0.1)[phase], size=1.0))
    # shadows on the field straight below, hatched (there but not a body)
    for k in range(N_BIRDS):
        x, y, z = birds[k]
        # sun from the front left: each shadow falls behind and to the right of its bird
        sh = [cam((p[0] + 0.28 * y, 0.0, p[2] + 0.5 * y)) for p in bird_world((x, 0.0, z), **poses[k])]
        F.hatch(sh, G3, 3.0)
    for k in sorted(range(N_BIRDS), key=lambda k: -cam.depth(birds[k])):
        pts = [cam(p) for p in bird_world(birds[k], **poses[k])]
        F.outline(pts, G7 if k == lo else G5, LINE)
    return F


# ================================================================== v5 · mechanism · hatched mass
def v5() -> Frame:
    """A crank automaton: eight carved birds on rods over a comb; each rod's pick plucks the tine under it."""
    F = Frame("v5 · crank automaton · hatched mass")
    cam = Camera((4.6, 4.0, -7.6), (0.3, 1.0, 0.0), 400, (222, 132))
    n = N_DEG
    BX0, BX1, BY0, BY1, BZ0, BZ1 = -4.2, 4.2, -1.0, 0.0, -0.8, 0.8

    def C(pts):
        return [cam(p) for p in pts]

    top = C([(BX0, BY1, BZ0), (BX1, BY1, BZ0), (BX1, BY1, BZ1), (BX0, BY1, BZ1)])
    front = C([(BX0, BY1, BZ0), (BX1, BY1, BZ0), (BX1, BY0, BZ0), (BX0, BY0, BZ0)])
    end = C([(BX1, BY1, BZ0), (BX1, BY1, BZ1), (BX1, BY0, BZ1), (BX1, BY0, BZ0)])
    # the box is a solid mass: front face hatched (away from the light), end and lid plain
    F.outline(end, G4, LINE)
    F.outline(front, G4, LINE)
    F.hatch(front, G2, 4.0)
    F.outline(top, G4, LINE)
    # plinth line under the lid's lip
    F.line(cam((BX0, BY1 - 0.18, BZ0)), cam((BX1, BY1 - 0.18, BZ0)), HAIR, G3)
    # slot the rods ride in
    F.outline(C([(BX0 + 0.35, BY1, 0.22), (BX1 - 0.35, BY1, 0.22), (BX1 - 0.35, BY1, 0.42),
                 (BX0 + 0.35, BY1, 0.42)]), G3, HAIR)
    # the comb: one tine per scale degree, long (low) to short (high), on a bar along the front
    xs = [BX0 + 0.5 + (BX1 - BX0 - 1.0) * i / (n - 1) for i in range(n)]
    rods = []
    for k, (u, h, d) in enumerate(BIRDS):
        rods.append((BX0 + 0.5 + (BX1 - BX0 - 1.0) * u, 1.7 + 0.7 * h))
    lo = min(range(N_BIRDS), key=lambda k: rods[k][1])
    ci = cell((rods[lo][0] - BX0 - 0.5) / (BX1 - BX0 - 1.0))
    rods[lo] = (xs[ci], rods[lo][1])
    F.outline(C([(BX0 + 0.25, BY1, 0.0), (BX1 - 0.25, BY1, 0.0), (BX1 - 0.25, BY1 + 0.12, 0.0),
                 (BX0 + 0.25, BY1 + 0.12, 0.0)]), G4, LINE)
    for i, x in enumerate(xs):
        L = 0.85 * 2 ** (-DEG[i] / 24) + 0.12
        tine = C([(x - 0.08, BY1 + 0.03, 0.0), (x + 0.08, BY1 + 0.03, 0.0), (x + 0.08, BY1 + 0.03, -L),
                  (x - 0.08, BY1 + 0.03, -L)])
        F.outline(tine, G5 if i == ci else G3, LINE if i == ci else HAIR)
    # crank on the right end: boss, arm, handle (the thing in the hand)
    axle = (BX1, -0.5, 0.0)
    ang = math.radians(55)
    arm_end = (BX1 + 0.35, -0.5 + 0.95 * math.sin(ang), 0.95 * math.cos(ang))
    boss = C([(BX1 + 0.02, -0.5 + 0.26 * math.sin(t), 0.26 * math.cos(t)) for t in
              [2 * math.pi * s / 28 for s in range(28)]])
    F.outline(boss, G4, LINE)
    F.hatch(boss, G2, 3.5)

    def bar(p, q, half, colour, weight, hatch_=None):
        a0, a1 = cam(p), cam(q)
        dx, dy = a1[0] - a0[0], a1[1] - a0[1]
        L = math.hypot(dx, dy)
        nx, ny = -dy / L * half, dx / L * half
        poly = [(a0[0] + nx, a0[1] + ny), (a1[0] + nx, a1[1] + ny), (a1[0] - nx, a1[1] - ny), (a0[0] - nx, a0[1] - ny)]
        F.outline(poly, colour, weight)
        if hatch_:
            F.hatch(poly, hatch_, 3.2)

    bar(add(axle, (0.35, 0, 0)), arm_end, 3.0, G4, LINE)
    bar(arm_end, add(arm_end, (0.9, 0.0, 0.0)), 4.5, G5, LINE, G3)

    # a carved bird in profile (x forward, y up), wing raised, mounted on its rod
    body = [(0.55, 0.12), (0.42, 0.26), (0.26, 0.3), (0.08, 0.2), (-0.3, 0.2), (-0.62, 0.34), (-0.66, 0.27),
            (-0.4, 0.06), (-0.05, -0.12), (0.25, -0.08), (0.42, 0.04)]
    wingp = [(0.12, 0.2), (-0.02, 0.62), (-0.3, 0.56), (-0.24, 0.2)]
    order = sorted(range(N_BIRDS), key=lambda k: -cam.depth((rods[k][0], 0, 0.32)))
    for k in order:
        x, ht = rods[k]
        lit = k == lo
        bar((x, BY1, 0.32), (x, ht, 0.32), 1.6, G4, HAIR)
        # pick at the rod's foot, reaching over the comb
        F.line(cam((x, BY1 + 0.16, 0.3)), cam((x, BY1 + 0.16, -0.25)), LINE, G6 if lit else G3)
        s = 0.85
        yaw = math.radians(-35)
        bp = [cam(add(rot_y((px * s, py * s, 0.0), yaw), (x, ht + 0.1, 0.32))) for px, py in body]
        wp = [cam(add(rot_y((px * s, py * s, -0.02), yaw), (x, ht + 0.1, 0.32))) for px, py in wingp]
        F.outline(bp, G7 if lit else G5, SUBJ if lit else LINE)
        F.outline(wp, G5 if lit else G4, LINE)
        e = cam(add(rot_y((0.36 * s, 0.2 * s, 0.0), yaw), (x, ht + 0.1, 0.32)))
        F.outline(ell(e[0], e[1], 1.6, 1.6, 10), G5, HAIR)
    return F


VARIANTS = (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5))


def main() -> None:
    for name, fn in VARIANTS:
        d = HERE / name
        d.mkdir(exist_ok=True)
        (d / "rest.svg").write_text(fn().svg(), encoding="utf-8")
        print(f"wrote {d / 'rest.svg'}")


if __name__ == "__main__":
    main()
