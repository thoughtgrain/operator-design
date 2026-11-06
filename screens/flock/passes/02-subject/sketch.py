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
    cam = Camera((0.0, 7.6, -10.5), (0.35, 1.25, 0.0), 470, (240, 122))
    rnd = random.Random(4)
    n = N_DEG
    R = 0.3
    reeds = []
    for i in range(n):
        x = -5.0 + 10.0 * i / (n - 1)
        z = 0.35 * math.sin(i * 1.7) + rnd.uniform(-0.15, 0.15)
        top = 2.55 + 0.22 * math.sin(i * 2.3 + 0.4) + rnd.uniform(-0.08, 0.08)
        col = 2.0 * 2 ** (-DEG[i] / 12)          # air column, 2.0 .. 0.5
        reeds.append((x, z, top, top - col))
    birds = []
    for k, (u, h, d) in enumerate(BIRDS):
        x = -5.0 + 10.0 * u
        birds.append((x, 3.75 + 0.9 * h, 0.5 * d))
    # the bird that plays now: skimming the mouth of the reed under it
    lo = min(range(N_BIRDS), key=lambda k: birds[k][1])
    ri = cell((birds[lo][0] + 5) / 10)
    birds[lo] = (reeds[ri][0] - 0.25, reeds[ri][2] + 0.55, reeds[ri][1])

    def ring(x, z, y, r, a0=0.0, a1=2 * math.pi, n_=40):
        return [cam((x + r * math.cos(a0 + (a1 - a0) * t / n_), y, z + r * math.sin(a0 + (a1 - a0) * t / n_)))
                for t in range(n_ + 1)]

    order = sorted(range(n), key=lambda i: -cam.depth((reeds[i][0], 0, reeds[i][1])))
    for i in order:
        x, z, top, node = reeds[i]
        playing = i == ri
        cut = node - 0.28
        bottom = -3.2
        sil = hull(ring(x, z, top, R) + ring(x, z, bottom, R))
        F.outline(sil, G5 if playing else G4, LINE)
        # back wall inside: three vertical hairlines from the rim down to the node
        for a in (math.radians(60), math.radians(90), math.radians(120)):
            p0 = cam((x + 0.8 * R * math.cos(a), top, z + 0.8 * R * math.sin(a)))
            p1 = cam((x + 0.8 * R * math.cos(a), node, z + 0.8 * R * math.sin(a)))
            F.line(p0, p1, HAIR, G4 if playing else G2)
        # rim: the inner back arc shows the wall's thickness
        F.ribbon(ring(x, z, top, 0.78 * R, 0, math.pi, 20), HAIR, G3)
        # the node that stops the column, seen from above
        F.outline(ring(x, z, node, 0.8 * R, n_=36)[:-1], G6 if playing else G4, LINE)
        # the front wall, cut: its top edge is the front half of a ring at the cut height
        front = ring(x, z, cut, R, math.pi, 2 * math.pi, 20)
        lower = ring(x, z, bottom, R, math.pi, 2 * math.pi, 20)
        F.outline(front + lower[::-1], G4, LINE)
        F.ribbon(ring(x, z, cut, 0.78 * R, math.pi, 2 * math.pi, 20), HAIR, G2)
        # joints further down the stalk
        for j in (1.25, 2.6):
            yj = cut - j
            if yj > bottom + 0.3:
                F.ribbon(ring(x, z, yj, R, math.pi * 1.04, math.pi * 1.96, 16), HAIR, G3)
    # birds over the mouths, flying right; the one at the mouth is the brightest thing
    for k in sorted(range(N_BIRDS), key=lambda k: -cam.depth(birds[k])):
        x, y, z = birds[k]
        pts = [cam(p) for p in bird_world((x, y, z), heading=math.radians(-8 + 10 * BIRDS[k][2]),
                                          dihedral=0.18 + 0.12 * ((k * 5) % 3), size=0.62)]
        if k == lo:
            F.outline(pts, G7, SUBJ)
        else:
            F.outline(pts, G5, LINE)
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
    # top surface, outlined; drawn first so the section sits over its front edge
    back = [cam((x, snow(x), Z1)) for x in xs]
    front = [cam((x, snow(x), Z0)) for x in xs]
    F.outline(thin(front[::2] + back[::-2], 62), G3, LINE)
    # ridge lines receding along each furrow crest (hairlines)
    for i in range(n):
        xc = X0 + pitch * (i + 0.5)
        F.line(cam((xc, snow(xc), Z0)), cam((xc, snow(xc), Z1)), HAIR, G2)
    # the section face at z = Z0: snow layer over hatched soil
    base = -1.25
    soil = [cam((x, ground(x), Z0)) for x in xs[::2]]
    soil_poly = soil + [cam((X1, base, Z0)), cam((X0, base, Z0))]
    F.poly(soil_poly, G0)
    F.hatch(soil_poly, G3, 4.0)
    F.ribbon(soil, HAIR, G4)
    # right end face of the block (in shadow): hatched too
    side = [cam((X1, snow(X1), Z0)), cam((X1, snow(X1), Z1)), cam((X1, base, Z1)), cam((X1, base, Z0))]
    F.outline(side, G3, LINE)
    F.hatch(side, G2, 4.0)
    sec = [cam((x, snow(x), Z0)) for x in xs[::2]] + [cam((X1, base, Z0)), cam((X0, base, Z0))]
    F.outline(sec, G4, LINE, fill="none")

    # wing prints: each landing pressed a bird's spread wings into the snow
    def print_pts(x, z, yaw, size, open_=1.0):
        out = []
        for (px, py, pz) in bird_local(0.0, -0.2 * open_, size):
            p = rot_y((px, 0, pz), yaw)
            out.append(cam((x + p[0], snow(x + p[0]) - 0.02, z + p[2])))
        return out

    def feathers(x, z, yaw, size, colour):
        for side_ in (1, -1):
            root = (0.2 * size, 0.15 * size * side_)
            for f_ in range(4):
                t = 0.5 + 0.16 * f_
                tip = (-0.05 - 0.2 * f_ * 0.4, side_ * (0.55 + 0.12 * f_))
                p0 = rot_y((root[0] - 0.25 * size, 0, root[1]), yaw)
                p1 = rot_y((tip[0] * size, 0, tip[1] * size), yaw)
                F.line(cam((x + p0[0], snow(x + p0[0]), z + p0[2])),
                       cam((x + p1[0], snow(x + p1[0]), z + p1[2])), HAIR, colour)
                del t

    rnd = random.Random(9)
    prints = []
    for k, (u, h, d) in enumerate(BIRDS):
        # each bird's track runs back into the field; speed sets how far apart its touch-downs are
        x = X0 + (X1 - X0) * u
        z = 3.9 + 0.6 * d
        prints.append((x, z, rnd.uniform(-0.3, 0.3), 0)) if k % 2 else None
    tracks = []
    for k, (u, h, d) in enumerate(BIRDS[:5]):
        x = X0 + (X1 - X0) * u + 0.1 * k
        z = 4.3 - 0.85 * k + 0.25 * d
        tracks.append((x, z, math.radians(-90 + 25 * d), k))
    tracks.sort(key=lambda t: -t[1])
    for j, (x, z, yaw, k) in enumerate(tracks):
        newest = j == len(tracks) - 1
        pts = print_pts(x, z, yaw, 0.95)
        F.outline(pts, G7 if newest else G4, SUBJ if newest else LINE)
        feathers(x, z, yaw, 0.95, G5 if newest else G2)
    return F


# ================================================================== v3 · one detail · exploded view
def v3() -> Frame:
    """One bird at large scale, exploded like a model kit; its neighbours cut by the frame's edge."""
    F = Frame("v3 · one bird, exploded · exploded view")
    cam = Camera((2.2, 4.4, -7.5), (0.1, 0.2, 0.0), 300, (240, 124))
    E = 0.55 + 0.75 * (1 - COHERE)               # explosion distance: cohere pulls the parts together
    yaw = math.radians(-14)

    def W(p, off=(0, 0, 0)):
        return cam(add(rot_y(p, yaw), off))

    # neighbours, assembled and cut by the frame's edge (the rest of the flock)
    for (pos, hd, sz) in (((-6.4, 2.6, 3.4), -0.2, 1.6), ((6.1, -1.3, 1.0), 0.15, 1.5),
                          ((-5.0, -2.9, -1.4), -0.05, 1.3), ((3.6, 3.55, 4.2), 0.1, 1.5)):
        pts = [cam(p) for p in bird_world(pos, heading=hd, dihedral=0.25, size=sz)]
        F.outline(pts, G3, LINE)

    # body: an ellipsoid (silhouette from its projected hull) with section rings inside
    a, b, c = 0.95, 0.36, 0.34
    body = []
    for i in range(24):
        th = math.pi * i / 23
        for j in range(24):
            ph = 2 * math.pi * j / 24
            body.append(W((a * math.cos(th), b * math.sin(th) * math.cos(ph), c * math.sin(th) * math.sin(ph))))
    # exploded parts' offsets (world, before yaw): wings out sideways and up, tail back, head forward
    off_r = scl((0.0, 0.55, 1.0), E)
    off_l = scl((0.0, 0.55, -1.0), E)
    off_t = scl((-1.0, 0.1, 0.0), E)
    wing_l, wing_r = [], []
    for x, z in _HALF[3:13]:
        span = max(0.0, (abs(z) - 0.14) / 0.86)
        p = (x * 1.9, 0.12 + 0.32 * span * span, z * 1.9)
        wing_r.append(p)
    wing_r = [(0.4, 0.12, 0.2), (0.62, 0.13, 0.42)] + [(x * 1.9 + 0.3, 0.12 + 0.3 * ((z - 0.14) / 0.86) ** 2, z * 1.9 + 0.1)
                                                       for x, z in _HALF[4:12]] + [(-0.12, 0.12, 0.32)]
    wing_l = [(x, y, -z) for x, y, z in wing_r]
    tail = [(-0.75, 0.05, 0.12), (-1.5, 0.08, 0.3), (-1.62, 0.08, 0.1), (-1.6, 0.08, -0.1), (-1.5, 0.08, -0.3),
            (-0.75, 0.05, -0.12)]
    # assembly lines: dashed hairlines from each part back to its seat on the body
    for seat, off in (((0.18, 0.1, 0.3), off_r), ((0.18, 0.1, -0.3), off_l), ((-0.7, 0.05, 0.0), off_t)):
        p0 = rot_y(seat, yaw)
        p1 = add(p0, off)
        L = math.dist(p0, p1)
        nseg = int(L / 0.16)
        for s in range(0, nseg, 2):
            q0 = add(p0, scl(sub(p1, p0), s / nseg))
            q1 = add(p0, scl(sub(p1, p0), (s + 1) / nseg))
            F.line(cam(q0), cam(q1), HAIR, G3)

    def part(pts, off):
        return [cam(add(rot_y(p, yaw), off)) for p in pts]

    def feather_lines(wing, off, side, bright):
        # primaries: one per scale degree, five on the left wing (low octave), six on the right
        root = (0.25, 0.14, 0.32 * side)
        k = 5 if side < 0 else 6
        for f in range(k):
            t = (f + 0.5) / k
            tip = ((0.55 - 1.2 * t) * 1.0 + 0.0, 0.12 + 0.3 * (0.35 + 0.65 * t) ** 2,
                   side * (0.9 + 0.95 * (1 - abs(t - 0.55))))
            colour = G7 if (bright is not None and f == bright) else G2
            w = SUBJ if colour == G7 else HAIR
            F.line(cam(add(rot_y(root, yaw), off)), cam(add(rot_y(tip, yaw), off)), w, colour)

    parts = [("tail", tail, off_t), ("wl", wing_l, off_l), ("body", None, (0, 0, 0)), ("wr", wing_r, off_r)]
    parts.sort(key=lambda p: -cam.depth(p[2]))
    for name, pts, off in parts:
        if name == "body":
            sil = hull(body)
            F.outline(sil, G5, LINE)
            for t in (-0.45, 0.0, 0.45):          # section rings: front halves only
                ring = [W((a * t, b * math.sqrt(1 - t * t) * math.cos(ph), c * math.sqrt(1 - t * t) * math.sin(ph)))
                        for ph in [math.pi * (0.5 + s / 20) for s in range(21)]]
                F.ribbon(ring, HAIR, G3)
            spine = [W((a * math.cos(th), b * math.sin(th), 0)) for th in [math.pi * s / 20 for s in range(21)]]
            F.ribbon(spine, HAIR, G3)
            # beak, a closed cone outline at the front
            bk = [W((0.92, 0.06, 0.07)), W((1.3, 0.0, 0.0)), W((0.92, -0.06, -0.07)), W((0.9, 0.08, -0.05))]
            F.outline(hull(bk), G5, LINE)
            ex = W((0.62, 0.17, 0.2))
            F.outline(ell(ex[0], ex[1], 3.2, 3.2, 16), G5, HAIR)
        elif name == "tail":
            F.outline(part(pts, off), G4, LINE)
            for zz in (-0.2, 0.0, 0.2):
                F.line(cam(add(rot_y((-0.8, 0.05, zz * 0.5), yaw), off)), cam(add(rot_y((-1.55, 0.08, zz), yaw), off)),
                       HAIR, G2)
        else:
            side = 1 if name == "wr" else -1
            F.outline(part(pts, off), G4, LINE)
            feather_lines(pts, off, side, 3 if side > 0 else None)
    return F


# ================================================================== v4 · the flock itself · single-weight contour
def v4() -> Frame:
    """Eight starlings in flight over a ploughed field, drawn in one contour weight."""
    F = Frame("v4 · starlings over the field · single-weight contour")
    cam = Camera((0.0, 1.4, -8.0), (0.0, 2.6, 6.0), 330, (240, 112))
    n = N_DEG
    # field: one drill row per cell, running away from us to the horizon
    X0, X1 = -6.5, 6.5
    zf = 30.0
    rows = []
    for i in range(n + 1):
        x = X0 + (X1 - X0) * i / n
        rows.append(x)
    horizon = cam((0, 0, 400))[1]
    birds = []
    for k, (u, h, d) in enumerate(BIRDS):
        x = X0 + (X1 - X0) * u
        birds.append((x * 0.9, 3.0 + 1.2 * h, 5.5 + 2.2 * d))
    lo = min(range(N_BIRDS), key=lambda k: cam.depth(birds[k]))  # nearest bird plays now
    ci = cell((birds[lo][0] / 0.9 - X0) / (X1 - X0))
    for i, x in enumerate(rows[:-1]):
        xc = (x + rows[i + 1]) / 2
        p0, p1 = cam((xc, 0, -1.0)), cam((xc, 0, zf))
        playing = i == ci
        F.line(p0, p1, LINE if playing else HAIR, G4 if playing else G2)
    F.line((0, horizon), (480, horizon), HAIR, G3)
    for k in sorted(range(N_BIRDS), key=lambda k: -cam.depth(birds[k])):
        x, y, z = birds[k]
        phase = (k * 3) % 4
        pts = [cam(p) for p in bird_world((x, y, z), heading=math.radians(-10 + 12 * BIRDS[k][2]),
                                          pitch=math.radians(4), bank=math.radians(8 * (phase - 1.5)),
                                          dihedral=(-0.15, 0.1, 0.35, 0.55)[phase], sweep=0.15, size=0.85)]
        if k == lo:
            F.outline(pts, G7, SUBJ)
        else:
            F.outline(pts, G5, LINE)
    return F


# ================================================================== v5 · mechanism · hatched mass
def v5() -> Frame:
    """A crank automaton: eight carved birds on rods over a comb; each rod plucks the tine under it."""
    F = Frame("v5 · crank automaton · hatched mass")
    cam = Camera((-3.2, 5.6, -9.5), (0.2, 1.3, 0.0), 360, (232, 126))
    n = N_DEG
    BX0, BX1, BY0, BY1, BZ0, BZ1 = -4.6, 4.6, -1.6, 0.0, -1.0, 1.0

    def box_face(pts):
        return [cam(p) for p in pts]

    top = box_face([(BX0, BY1, BZ0), (BX1, BY1, BZ0), (BX1, BY1, BZ1), (BX0, BY1, BZ1)])
    front = box_face([(BX0, BY1, BZ0), (BX1, BY1, BZ0), (BX1, BY0, BZ0), (BX0, BY0, BZ0)])
    left = box_face([(BX0, BY1, BZ0), (BX0, BY1, BZ1), (BX0, BY0, BZ1), (BX0, BY0, BZ0)])
    # the mass: the box's front face hatched (in shadow), lid and end plain
    F.outline(left, G4, LINE)
    F.outline(front, G4, LINE)
    F.hatch(front, G2, 4.0)
    F.outline(top, G4, LINE)
    # slot along the lid the rods ride in
    slot = box_face([(BX0 + 0.4, BY1, 0.08), (BX1 - 0.4, BY1, 0.08), (BX1 - 0.4, BY1, 0.28), (BX0 + 0.4, BY1, 0.28)])
    F.outline(slot, G3, HAIR)
    # the comb: one tine per scale degree along the lid's front edge, long (low) to short (high)
    tines = []
    for i in range(n):
        x = BX0 + 0.55 + (BX1 - BX0 - 1.1) * i / (n - 1)
        L = 0.95 * 2 ** (-DEG[i] / 24) + 0.25
        tines.append((x, L))
    rods = []
    for k, (u, h, d) in enumerate(BIRDS):
        x = BX0 + 0.55 + (BX1 - BX0 - 1.1) * u
        rods.append((x, 1.9 + 0.55 * h))
    lo = min(range(N_BIRDS), key=lambda k: rods[k][1])
    ci = cell((rods[lo][0] - BX0 - 0.55) / (BX1 - BX0 - 1.1))
    for i, (x, L) in enumerate(tines):
        p = [cam((x - 0.09, BY1 + 0.02, -0.15)), cam((x + 0.09, BY1 + 0.02, -0.15)),
             cam((x + 0.09, BY1 + 0.02, -0.15 - L)), cam((x - 0.09, BY1 + 0.02, -0.15 - L))]
        F.outline(p, G5 if i == ci else G3, LINE if i == ci else HAIR)
    # comb bar holding the tines
    bar = box_face([(BX0 + 0.3, BY1 + 0.02, -0.1), (BX1 - 0.3, BY1 + 0.02, -0.1),
                    (BX1 - 0.3, BY1 + 0.02, 0.0), (BX0 + 0.3, BY1 + 0.02, 0.0)])
    F.outline(bar, G4, HAIR)
    # crank on the right end: axle boss, arm, handle (the thing in the hand)
    ax = (BX1, -0.8, 0.0)
    ang = math.radians(-40)
    arm_end = (BX1 + 0.35, -0.8 + 1.1 * math.sin(ang), 1.1 * math.cos(ang))
    a0, a1 = cam(add(ax, (0.35, 0, 0))), cam(arm_end)
    boss = [cam((BX1 + 0.05, -0.8 + 0.28 * math.sin(t), 0.28 * math.cos(t))) for t in [2 * math.pi * s / 28 for s in range(28)]]
    F.outline(boss, G4, LINE)
    F.hatch(boss, G2, 4.0, phase=1)
    dx, dy = a1[0] - a0[0], a1[1] - a0[1]
    L = math.hypot(dx, dy)
    nx, ny = -dy / L * 3.2, dx / L * 3.2
    F.outline([(a0[0] + nx, a0[1] + ny), (a1[0] + nx, a1[1] + ny), (a1[0] - nx, a1[1] - ny), (a0[0] - nx, a0[1] - ny)],
              G4, LINE)
    h0, h1 = cam(add(arm_end, (0.0, 0, 0))), cam(add(arm_end, (0.95, 0, 0)))
    hx, hy = h1[0] - h0[0], h1[1] - h0[1]
    hl = math.hypot(hx, hy)
    mx, my = -hy / hl * 4.2, hx / hl * 4.2
    handle = [(h0[0] + mx, h0[1] + my), (h1[0] + mx, h1[1] + my), (h1[0] - mx, h1[1] - my), (h0[0] - mx, h0[1] - my)]
    F.outline(handle, G5, LINE)
    F.hatch(handle, G3, 3.2)
    # rods and their birds, back to front; the rod over the playing tine carries the bright bird
    order = sorted(range(N_BIRDS), key=lambda k: -cam.depth((rods[k][0], rods[k][1], 0.18)))
    for k in order:
        x, ht = rods[k]
        r0, r1 = cam((x, BY1, 0.18)), cam((x, ht, 0.18))
        F.outline([(r0[0] - 1.4, r0[1]), (r1[0] - 1.4, r1[1]), (r1[0] + 1.4, r1[1]), (r0[0] + 1.4, r0[1])],
                  G4, HAIR)
        # pick at the rod's foot, leaning over the comb
        pk0, pk1 = cam((x, BY1 + 0.08, 0.1)), cam((x, BY1 + 0.08, -0.35))
        F.line(pk0, pk1, LINE, G7 if k == lo else G4)
        pts = [cam(p) for p in bird_world((x, ht + 0.12, 0.18), heading=math.radians(-15),
                                          dihedral=0.3, size=0.55)]
        F.outline(pts, G6 if k == lo else G4, LINE)
        if k == lo:
            pass
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
