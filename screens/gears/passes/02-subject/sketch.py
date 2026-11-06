#!/usr/bin/env python3
"""Subject pass 02 for gears: five rest frames, all of them meshing toothed wheels.

    python3 screens/gears/passes/02-subject/sketch.py

Writes v1..v5/rest.svg (480 x 220, stock header kept as preview scaffolding).
Every frame shows the defaults: ratio 3:2, teeth 8, mesh 100 %, scale maj, no
notes, not muted. Sketches for picking a subject, not device frames: every part
is static artwork (no bound nodes yet); each candidate's risks argue the budget.

The model (definition.json): driver A has `teeth` teeth (8); follower B has
teeth x ratio (12). Same module, so one tooth pair meshes per step; step k
meshes A's tooth k mod 8 with B's tooth k mod 12, repeating every 24 steps.
The meshing pair's degree is (i + j) mod 14, read in the scale.

3D scenes (v1, v2, v4, v5) are modelled in world units (module 1) and drawn
through one perspective camera per scene, fitted to the body. v3 is a flat
face-on drawing, so it needs no camera. No text below the header.
"""
from __future__ import annotations

import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 480, 220
G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
FONT = "UniversNextPro-Light"
HEADER = [("ratio", "3:2"), ("teeth", "8"), ("mesh", "100"), ("scale", "maj")]
HAIR, LINE, SUBJ = 1.0, 1.5, 2.0
BODY = (22, 216)          # usable body rows

# ------------------------------------------------------------------ model
TEETH_A, RATIO = 8, (3, 2)
TEETH_B = TEETH_A * RATIO[0] // RATIO[1]          # 12
SCALE = [0, 2, 4, 5, 7, 9, 11]                     # maj
PCS = set(SCALE)                                   # pitch classes in the scale
CYCLE = TEETH_A * TEETH_B // math.gcd(TEETH_A, TEETH_B)  # 24


def degree(k):
    return (k % TEETH_A + k % TEETH_B) % 14


def semis(deg):
    return SCALE[deg % 7] + 12 * (deg // 7)


# ---------------------------------------------------------------- svg out
def f(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def dedupe(pts, gap=0.3):
    out = []
    for p in pts:
        if not out or math.dist(out[-1], p) >= gap:
            out.append(p)
    return out


def poly(pts, fill, stroke="none", sw=None):
    pts = dedupe(pts)
    if len(pts) > 2 and math.dist(pts[0], pts[-1]) < 0.3:
        pts = pts[:-1]
    if len(pts) < 2:
        return ""
    d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
    s = f'<path d="{d}" fill="{fill}" stroke="{stroke}"'
    if stroke != "none":
        s += f' stroke-width="{sw}"'
    return s + "/>"


def big_poly(pts, fill, stroke="none", sw=None):
    """A closed outline over 64 points: black body in one piece of <= 64
    (decimated), outline as stroked ribbons."""
    pts = dedupe(pts)
    out = []
    if fill != "none":
        step = max(1, math.ceil(len(pts) / 64))
        out.append(poly(pts[::step], fill))
    if stroke != "none":
        out.append(ribbon(pts + [pts[0]], sw, stroke))
    return "\n".join(o for o in out if o)


def ribbon(pts, w, fill):
    """An open polyline as thin closed ribbons (filled, no stroke), <= 62 points each."""
    pts = dedupe(pts, 0.6)
    if len(pts) < 2:
        return ""
    out, i = [], 0
    while i < len(pts) - 1:
        out.append(_ribbon(pts[i:i + 31], w, fill))
        i += 30
    return "\n".join(out)


def _ribbon(pts, w, fill):
    h, n = w / 2, len(pts)
    left, right = [], []
    for k in range(n):
        if k == 0 or k == n - 1:
            a, b = (pts[0], pts[1]) if k == 0 else (pts[-2], pts[-1])
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy) or 1
            nx, ny, m = -dy / L, dx / L, h
        else:
            ax, ay = pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]
            bx, by = pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1]
            la, lb = math.hypot(ax, ay) or 1, math.hypot(bx, by) or 1
            n1, n2 = (-ay / la, ax / la), (-by / lb, bx / lb)
            nx, ny = n1[0] + n2[0], n1[1] + n2[1]
            ln = math.hypot(nx, ny) or 1
            nx, ny = nx / ln, ny / ln
            m = h / max(0.5, nx * n1[0] + ny * n1[1])
        x, y = pts[k]
        left.append((x + nx * m, y + ny * m))
        right.append((x - nx * m, y - ny * m))
    return poly(left + right[::-1], fill)


def seg(p, q, w, fill):
    return ribbon([p, q], w, fill)


def loop(pts, w, fill):
    """A closed hairline loop as ribbons."""
    return ribbon(list(pts) + [pts[0]], w, fill)


def dashed(pts, w, fill, dash=6.0, gap=4.0):
    """Dashed polyline (screen units) as short ribbons."""
    out, acc, on, cur = [], 0.0, True, [pts[0]]
    for a, b in zip(pts, pts[1:]):
        L = math.dist(a, b)
        t = 0.0
        while t < L:
            left = (dash if on else gap) - acc
            if t + left <= L:
                t += left
                p = (a[0] + (b[0] - a[0]) * t / L, a[1] + (b[1] - a[1]) * t / L)
                if on:
                    cur.append(p)
                    out.append(ribbon(cur, w, fill))
                cur, acc, on = [p], 0.0, not on
            else:
                acc += L - t
                if on:
                    cur.append(b)
                t = L
    if on and len(cur) > 1 and math.dist(cur[0], cur[-1]) > 2:
        out.append(ribbon(cur, w, fill))
    return out


def hatch(polys, spacing=3.5, w=HAIR, fill=G3, slope=1):
    """45-degree hairlines clipped to the region (even-odd over polys):
    lines y = -slope * x + c on screen, spacing measured perpendicular."""
    edges = []
    xs, ys = [], []
    for P in polys:
        for a, b in zip(P, P[1:] + P[:1]):
            edges.append((a, b))
        xs += [p[0] for p in P]
        ys += [p[1] for p in P]
    if not edges:
        return []
    cs = [y + slope * x for x, y in zip(xs, ys)]
    c0, c1 = min(cs), max(cs)
    stepc = spacing * math.sqrt(2)
    out = []
    c = math.floor(c0 / stepc) * stepc + stepc / 2
    while c < c1:
        ts = []
        for (ax, ay), (bx, by) in edges:
            ga, gb = ay + slope * ax - c, by + slope * bx - c
            if (ga > 0) != (gb > 0):
                t = ga / (ga - gb)
                ts.append(ax + (bx - ax) * t)
        ts.sort()
        for x0, x1 in zip(ts[::2], ts[1::2]):
            if x1 - x0 > 1.2:
                out.append(seg((x0 + 0.3, c - slope * (x0 + 0.3)), (x1 - 0.3, c - slope * (x1 - 0.3)), w, fill))
        c += stepc
    return out


def clip_y(pts, ymin):
    """Split an open polyline into runs that stay at y >= ymin."""
    runs, cur = [], []
    for a, b in zip(pts, pts[1:]):
        ina, inb = a[1] >= ymin, b[1] >= ymin
        if ina and not cur:
            cur = [a]
        if ina and inb:
            cur.append(b)
        elif ina and not inb:
            t = (ymin - a[1]) / (b[1] - a[1])
            cur.append((a[0] + (b[0] - a[0]) * t, ymin))
            runs.append(cur)
            cur = []
        elif not ina and inb:
            t = (ymin - a[1]) / (b[1] - a[1])
            cur = [(a[0] + (b[0] - a[0]) * t, ymin), b]
    if len(cur) > 1:
        runs.append(cur)
    return runs


def frame(body):
    steps = [G0, G1, G2, G3, G4, G5, G6, G7]
    hdr = [f'<rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>'
           for i, c in enumerate(steps)]
    for i, (t, v) in enumerate(HEADER):
        ink = "#CBCBCB" if i < 2 else G0
        hdr.append(f'<text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{ink}" stroke="none" '
                   f'font-family="{FONT}" font-size="10px">{t}</text>')
        hdr.append(f'<text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{ink}" stroke="none" '
                   f'font-family="{FONT}" font-size="20px">{v}</text>')
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        '<g id="preview_canvas">', f'<rect x="0" y="0" width="{W}" height="{H}" fill="{G0}" stroke="none"/>', '</g>',
        '<g id="preview_header">', *hdr, '</g>',
        *[b for b in body if b],
        '</svg>', ""])


# ------------------------------------------------------------------- 3D
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def mul(a, k): return (a[0] * k, a[1] * k, a[2] * k)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def norm(a):
    L = math.sqrt(dot(a, a))
    return (a[0] / L, a[1] / L, a[2] / L)


class Cam:
    """One perspective camera; fit() scales and places the scene in a box."""

    def __init__(self, eye, target, up=(0, 1, 0)):
        self.eye, self.t = eye, target
        self.fw = norm(sub(target, eye))
        self.rt = norm(cross(self.fw, up))
        self.up = cross(self.rt, self.fw)
        self.d0 = math.sqrt(dot(sub(target, eye), sub(target, eye)))
        self.s, self.ox, self.oy = 1.0, 0.0, 0.0

    def raw(self, P):
        d = sub(P, self.eye)
        z = dot(d, self.fw)
        return (self.d0 * dot(d, self.rt) / z, -self.d0 * dot(d, self.up) / z)

    def fit(self, pts, box):
        x0, y0, x1, y1 = box
        r = [self.raw(p) for p in pts]
        rx0, rx1 = min(p[0] for p in r), max(p[0] for p in r)
        ry0, ry1 = min(p[1] for p in r), max(p[1] for p in r)
        self.s = min((x1 - x0) / (rx1 - rx0), (y1 - y0) / (ry1 - ry0))
        self.ox = (x0 + x1) / 2 - self.s * (rx0 + rx1) / 2
        self.oy = (y0 + y1) / 2 - self.s * (ry0 + ry1) / 2

    def p(self, P):
        x, y = self.raw(P)
        return (self.ox + self.s * x, self.oy + self.s * y)

    def ps(self, Ps):
        return [self.p(P) for P in Ps]

    def dist(self, P):
        d = sub(P, self.eye)
        return math.sqrt(dot(d, d))

    def facing(self, P, n):
        return dot(n, sub(self.eye, P)) > 0


def gear2d(N, rp, m=1.0, rot=0.0, tips=None):
    """Spur outline, 4 points a tooth (root, tip, tip, root), flat lands;
    tooth t centred on angle rot + t * pitch. tips[t] scales tooth height."""
    ra, rr = rp + m, rp - 1.25 * m
    pitch = 2 * math.pi / N
    pts = []
    for t in range(N):
        a = rot + t * pitch
        rt = rr + (ra - rr) * (1 if tips is None else tips[t])
        for da, r in ((-0.31, rr), (-0.17, rt), (0.17, rt), (0.31, rr)):
            ang = a + da * pitch
            pts.append((r * math.cos(ang), r * math.sin(ang)))
    return pts


def ring(r, n=48, a0=0.0):
    return [(r * math.cos(a0 + 2 * math.pi * k / n), r * math.sin(a0 + 2 * math.pi * k / n)) for k in range(n)]


class Disc:
    """A prism: a 2D outline in the plane (c; u, v), extruded `thick` along n."""

    def __init__(self, c, u, v, outline, thick):
        self.c, self.u, self.v = c, u, v
        self.n = cross(u, v)
        self.o, self.t = outline, thick

    def w(self, x, y, z=0.0):
        return add(self.c, add(mul(self.u, x), add(mul(self.v, y), mul(self.n, z))))

    def front_z(self, cam):
        return self.t if cam.facing(self.w(0, 0, self.t), self.n) else 0.0

    def sides(self, cam):
        """Visible side quads: (depth, world corners, outward normal)."""
        out = []
        o = self.o
        for a, b in zip(o, o[1:] + o[:1]):
            ex, ey = b[0] - a[0], b[1] - a[1]
            L = math.hypot(ex, ey)
            if L < 1e-6:
                continue
            nx, ny = ey / L, -ex / L               # outline is CCW: right of edge is outside
            nw = add(mul(self.u, nx), mul(self.v, ny))
            mid = self.w((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, self.t / 2)
            if not cam.facing(mid, nw):
                continue
            q = [self.w(*a, 0), self.w(*b, 0), self.w(*b, self.t), self.w(*a, self.t)]
            out.append((cam.dist(mid), q, nw))
        out.sort(key=lambda r: -r[0])
        return out

    def cap(self, cam, pts2d, dz=0.0):
        z = self.front_z(cam)
        z = z + dz if z > 0 else z - dz
        return cam.ps([self.w(x, y, z) for x, y in pts2d])


def draw_disc(cam, d, edge=G4, cap_edge=G5, side_w=LINE, cap_w=LINE, side_fill=G0):
    out = []
    for _, q, _ in d.sides(cam):
        out.append(poly(cam.ps(q), side_fill, edge, side_w))
    cap = d.cap(cam, d.o)
    out.append(poly(cap, G0, cap_edge, cap_w) if len(cap) <= 64 else big_poly(cap, G0, cap_edge, cap_w))
    return out


def cylinder(cam, c, axis, r, length, edge=G4, cap_edge=G5, n=32):
    """A cylinder from c along axis: silhouette hull, then the visible end."""
    a = norm(axis)
    tmp = (0, 1, 0) if abs(a[1]) < 0.9 else (1, 0, 0)
    u = norm(cross(a, tmp))
    v = cross(a, u)
    d = Disc(c, u, v, ring(r, n), length)
    pts = [d.w(x, y, 0) for x, y in d.o] + [d.w(x, y, length) for x, y in d.o]
    hull = convex_hull(cam.ps(pts))
    return [poly(hull, G0, edge, LINE), poly(d.cap(cam, d.o), G0, cap_edge, LINE)], d


def convex_hull(pts):
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


def box_faces(cam, x0, x1, y0, y1, z0, z1):
    """Visible faces of an axis box: list of (name, screen polygon)."""
    P = lambda x, y, z: (x, y, z)
    faces = {
        "front": ([P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1)], (0, 0, 1)),
        "back": ([P(x0, y0, z0), P(x0, y1, z0), P(x1, y1, z0), P(x1, y0, z0)], (0, 0, -1)),
        "top": ([P(x0, y1, z0), P(x0, y1, z1), P(x1, y1, z1), P(x1, y1, z0)], (0, 1, 0)),
        "bottom": ([P(x0, y0, z0), P(x1, y0, z0), P(x1, y0, z1), P(x0, y0, z1)], (0, -1, 0)),
        "left": ([P(x0, y0, z0), P(x0, y0, z1), P(x0, y1, z1), P(x0, y1, z0)], (-1, 0, 0)),
        "right": ([P(x1, y0, z0), P(x1, y1, z0), P(x1, y1, z1), P(x1, y0, z1)], (1, 0, 0)),
    }
    out = []
    for name, (q, n) in faces.items():
        cen = mul(add(add(q[0], q[1]), add(q[2], q[3])), 0.25)
        if cam.facing(cen, n):
            out.append((name, cam.ps(q)))
    return out


# =================================================================== v1
def v1():
    """Cutaway section: a gearbox with its front wall and lid cut away. The two
    wheels stand on their shafts inside; the cut faces of the casing are hatched.
    B carries a twelve-hole index plate pinned at the scale's degrees."""
    rpA, rpB = TEETH_A / 2, TEETH_B / 2
    A_c, B_c = (0, 0, 0), (rpA + rpB, 0, 0)
    X, Y = (1, 0, 0), (0, 1, 0)
    gA = Disc(A_c, X, Y, gear2d(TEETH_A, rpA, rot=0.0), 2.0)
    gB = Disc(B_c, X, Y, gear2d(TEETH_B, rpB, rot=math.pi + math.pi / TEETH_B), 2.0)
    # casing (world): back wall, floor, two end walls, cut at z = ZC
    x0, x1, y0, y1, ZB, ZC, T = -6.6, 17.6, -8.4, 8.4, -2.6, 3.4, 0.9
    cam = Cam(eye=(-7.0, 11.0, 34.0), target=(5.5, -0.5, 0.0))
    cam.fit([(x0, y0, ZB - T), (x1, y1, ZC), (x0, y1, ZB - T), (x1, y0, ZC), (x0, y0, ZC), (x1, y1, ZB - T)],
            (34, BODY[0] + 2, 446, BODY[1] - 2))
    out = []
    slabs = [
        (x0, x1, y0, y1, ZB - T, ZB),           # back wall
        (x0, x1, y0, y0 + T, ZB, ZC),           # floor
        (x0, x0 + T, y0 + T, y1, ZB, ZC),       # left end wall
        (x1 - T, x1, y0 + T, y1, ZB, ZC),       # right end wall
    ]
    cut_faces = []
    for i, s in enumerate(slabs):
        for name, q in box_faces(cam, *s):
            out.append(poly(q, G0, G4, LINE))
            if name == "front" and i > 0:
                cut_faces.append(q)
    for q in cut_faces:                          # section hatching on the cut
        out += hatch([q], spacing=3.5, fill=G3)
    # back wall inner face: hairline panel inset
    inset = 0.9
    out.append(loop(cam.ps([(x0 + T + inset, y0 + T + inset, ZB), (x1 - T - inset, y0 + T + inset, ZB),
                            (x1 - T - inset, y1 - inset, ZB), (x0 + T + inset, y1 - inset, ZB)]), HAIR, G2))
    # bearing bosses on the back wall and shafts
    for c, rb in ((A_c, 1.7), (B_c, 1.9)):
        boss, _ = cylinder(cam, (c[0], c[1], ZB), (0, 0, 1), rb, 0.7, edge=G3, cap_edge=G4)
        out += boss
    shaftA, _ = cylinder(cam, (0, 0, ZB + 0.7), (0, 0, 1), 0.7, 4.6 - ZB, edge=G4, cap_edge=G5)
    shaftB, _ = cylinder(cam, (B_c[0], 0, ZB + 0.7), (0, 0, 1), 0.85, 3.4 - ZB, edge=G4, cap_edge=G5)
    out += shaftB
    # wheel B, then its index plate
    out += draw_disc(cam, gB)
    out.append(loop(gB.cap(cam, ring(rpB - 1.25 - 0.55, 60)), HAIR, G3))
    plate = Disc(add(B_c, (0, 0, 2.0)), X, Y, ring(3.6, 48), 0.45)
    out += draw_disc(cam, plate, edge=G3, cap_edge=G4)
    hr = 2.75
    for k in range(12):
        a = math.pi / 2 - 2 * math.pi * k / 12                       # degree 0 at the top, clockwise
        hx, hy = hr * math.cos(a), hr * math.sin(a)
        hole = [(hx + 0.36 * math.cos(t), hy + 0.36 * math.sin(t)) for t in [2 * math.pi * i / 16 for i in range(16)]]
        out.append(loop(plate.cap(cam, hole), HAIR, G3))
        if k in PCS:                                                 # a pin stands in the hole
            pin, _ = cylinder(cam, plate.w(hx, hy, plate.t), (0, 0, 1), 0.36, 0.55, edge=G4, cap_edge=G5, n=14)
            out += pin
    out += shaftB[1:]  # shaft end over the plate
    # wheel A on its shaft
    out += shaftA[:1]
    out += draw_disc(cam, gA)
    out.append(loop(gA.cap(cam, ring(rpA - 1.25 - 0.5, 40)), HAIR, G3))
    out.append(loop(gA.cap(cam, ring(1.5, 32)), HAIR, G3))
    for k in range(4):                                               # web ribs
        a = math.pi / 4 + k * math.pi / 2
        out.append(ribbon(gA.cap(cam, [(1.5 * math.cos(a), 1.5 * math.sin(a)),
                                        (1.9 * math.cos(a), 1.9 * math.sin(a))]), HAIR, G3))
    sA, _ = cylinder(cam, (0, 0, 2.0), (0, 0, 1), 0.7, 0.9, edge=G4, cap_edge=G5)
    out += sA
    # the meshing tooth: A's tooth 0, its front face edge, brightest
    t0 = gear2d(TEETH_A, rpA)[0:4]
    out.append(ribbon(gA.cap(cam, t0), SUBJ, G7))
    return frame(out)


# =================================================================== v2
def v2():
    """Exploded view: B lifted straight up its axis off its arbor, A seated on
    its own, so both faces show what the run has left on them: every mesh
    scores a short groove across the web behind the tooth that played, at a
    radius set by the note it played (low near the hub, high near the rim)."""
    rpA, rpB = TEETH_A / 2, TEETH_B / 2
    dAB = rpA + rpB
    X, Z = (1, 0, 0), (0, 0, -1)          # wheels flat, axis +Y (u x v = Y)
    lift, T = 5.4, 1.0
    rotB = math.pi + math.pi / TEETH_B
    gA = Disc((0, 0, 0), X, Z, gear2d(TEETH_A, rpA), T)
    gB = Disc((dAB, lift, 0), X, Z, gear2d(TEETH_B, rpB, rot=rotB), T)
    cam = Cam(eye=(1.0, 15.0, 23.0), target=(5.5, 1.5, 0.0))
    pts = [gA.w(x, y, z) for x, y in ring(rpA + 1, 16) for z in (0, T)] + \
          [gB.w(x, y, z) for x, y in ring(rpB + 1, 16) for z in (0, T)] + [(0, -2.6, 0)]
    cam.fit(pts, (60, BODY[0] + 3, 420, BODY[1] - 3))
    out = []
    # A's arbor below it, then A
    arbA, _ = cylinder(cam, (0, -2.4, 0), (0, 1, 0), 0.55, 2.4, edge=G3, cap_edge=G4)
    out += arbA[:1]
    out += draw_disc(cam, gA)
    out.append(loop(gA.cap(cam, ring(rpA - 1.25 - 0.4, 40)), HAIR, G3))
    out.append(loop(gA.cap(cam, ring(0.55, 18)), LINE, G4))
    # B's arbor and washer stand where B came off, beside A's tooth 0
    arbB, _ = cylinder(cam, (dAB, -2.4, 0), (0, 1, 0), 0.55, 2.9, edge=G3, cap_edge=G4)
    out += arbB
    washer = Disc((dAB, 0.5, 0), X, Z, ring(1.5, 32), 0.3)
    out += cylinder(cam, (dAB, 0.5, 0), (0, 1, 0), 1.5, 0.3, edge=G3, cap_edge=G4)[0]
    out.append(loop(washer.cap(cam, ring(0.55, 18)), HAIR, G3))
    # assembly lines: B's axis, and B's meshing gap down to its place
    out += dashed(cam.ps([(dAB, 0.8, 0), (dAB, lift, 0)]), HAIR, G4, 4, 3)
    gap = rpB - 0.3
    out += dashed(cam.ps([(dAB - gap, lift, 0), (dAB - gap, T, 0)]), HAIR, G4, 4, 3)
    out += draw_disc(cam, gB)
    out.append(loop(gB.cap(cam, ring(rpB - 1.25 - 0.4, 60)), HAIR, G3))
    out.append(loop(gB.cap(cam, ring(0.55, 18)), LINE, G4))

    def grooves(g, N, rot, rp, owner, bright_k=None):
        o = []
        r0, r1 = 1.05, rp - 1.25 - 0.75
        pitch = 2 * math.pi / N
        for t in range(N):
            ks = [k for k in range(CYCLE) if owner(k) == t]
            for idx, k in enumerate(ks):
                lane = (idx - (len(ks) - 1) / 2) * 0.3 * pitch
                a = rot + t * pitch + lane
                r = r0 + (r1 - r0) * semis(degree(k)) / 23
                span = 0.11 * pitch * (rp / r) ** 0.5
                arc_ = [(r * math.cos(a + span * s), r * math.sin(a + span * s)) for s in (-1, -0.5, 0, 0.5, 1)]
                br = k == bright_k
                o.append(ribbon(g.cap(cam, arc_), SUBJ if br else LINE, G7 if br else G5))
        return o
    out += grooves(gB, TEETH_B, rotB, rpB, lambda k: k % TEETH_B)
    out += grooves(gA, TEETH_A, 0.0, rpA, lambda k: k % TEETH_A, bright_k=CYCLE - 1)
    return frame(out)


# =================================================================== v3
def involute_tooth(rp, m, centre_a, alpha=math.radians(20), n=7, height=1.0):
    rb = rp * math.cos(alpha)
    ra, rr = rp + m * height, rp - 1.25 * m
    inv = lambda a: math.tan(a) - a
    half = math.pi / (2 * rp / m) / 1 + 0  # half tooth thickness angle at pitch: (pi m / 2) / rp / 2
    half = (math.pi * m / 2) / rp / 2
    phi_p = inv(math.acos(rb / rp))

    def flank(sign):
        pts = []
        r0 = max(rb, rr)
        for i in range(n):
            r = r0 + (ra - r0) * i / (n - 1)
            phi = inv(math.acos(min(1.0, rb / r)))
            a = centre_a + sign * (half + phi_p - phi)
            pts.append((r * math.cos(a), r * math.sin(a)))
        if rr < rb:
            a = centre_a + sign * (half + phi_p)
            pts.insert(0, (rr * math.cos(a), rr * math.sin(a)))
        return pts
    left = flank(-1)
    right = flank(1)
    return left + right[::-1]


def gear_involute(N, rp, m, rot):
    pts = []
    for t in range(N):
        pts += involute_tooth(rp, m, rot + 2 * math.pi * t / N)
    return pts


def v3():
    """Single-weight contour: the mesh itself at large scale. A rises from the
    bottom edge, B comes down from beyond the top; one tooth of B sits in A's
    gap at the pitch point. The rest of both wheels is left to the frame."""
    m = 19.0
    rpA, rpB = m * TEETH_A / 2, m * TEETH_B / 2
    P = (240.0, 110.0)                                   # pitch point
    cA = (P[0], P[1] + rpA)
    cB = (P[0], P[1] - rpB)
    w = LINE
    out = []
    ymin = BODY[0] + 1

    def put(c, pts):
        return [(c[0] + x, c[1] + y) for x, y in pts]

    def draw(pts, ink, close=True, wd=w):
        pts = list(pts) + ([pts[0]] if close else [])
        o = []
        for run in clip_y(pts, ymin):
            run = [p for p in run if -4 <= p[0] <= W + 4] if False else run
            o.append(ribbon(run, wd, ink))
        return o
    # A: tooth 0 points up at the pitch point (angle -90 deg on screen)
    rotA = -math.pi / 2 + math.pi / TEETH_A                 # gap at the top, B's tooth sits in it
    rotB = math.pi / 2                                      # B tooth pointing down
    A = put(cA, gear_involute(TEETH_A, rpA, m, rotA))
    B = put(cB, gear_involute(TEETH_B, rpB, m, rotB))
    # black bodies so outlines hide what's behind (B is behind nothing; keep clean)
    out += draw(B, G5)
    out += draw(A, G5)
    # B's rim, inner edge of the rim
    out += draw(put(cB, ring(rpB - 1.25 * m - 0.75 * m, 180)), G3)
    # A: the rim's inner edge is an index ring of twelve positions; at the
    # scale's seven it is cut with a notch (degree 0 straight up, clockwise)
    rim_in = rpA - 2.0 * m
    ring_pts = []
    for k in range(12):
        a0 = -math.pi / 2 + 2 * math.pi * k / 12
        if k in PCS:
            for da, r in ((-0.11, rim_in), (-0.07, rim_in - 0.38 * m), (0.07, rim_in - 0.38 * m), (0.11, rim_in)):
                ring_pts.append((r * math.cos(a0 + da), r * math.sin(a0 + da)))
        for i in range(5):
            a = a0 + 0.11 + (2 * math.pi / 12 - 0.22) * i / 4
            ring_pts.append((rim_in * math.cos(a), rim_in * math.sin(a)))
    out += draw(put(cA, ring_pts), G4)
    hub_r, bore_r = 0.95 * m, 0.42 * m
    out += draw(put(cA, ring(hub_r, 60)), G3)
    out += draw(put(cA, ring(bore_r, 40)), G3)
    # the pair in contact: B's tooth in A's gap, brightest
    tB = put(cB, involute_tooth(rpB, m, rotB))
    out += draw(tB, G7, close=False)
    return frame(out)


# =================================================================== v4
def v4():
    """Hatched mass: two thick spur wheels on a low camera, lit from the upper
    left. Flanks turned from the light are hatched; faces toward it stay black.
    B's web is drilled at the scale's degrees (seven of twelve positions)."""
    rpA, rpB = TEETH_A / 2, TEETH_B / 2
    dAB = rpA + rpB
    X, Z = (1, 0, 0), (0, 0, -1)
    T = 3.0
    rotB = math.pi + math.pi / TEETH_B
    # angle the pair so B sits behind and right of A
    yaw = math.radians(-24)
    u = (math.cos(yaw), 0, -math.sin(yaw))
    v = cross(u, (0, 1, 0))
    v = (-v[0], -v[1], -v[2]) if dot(cross(u, v), (0, 1, 0)) < 0 else v
    gA = Disc((0, 0, 0), u, v, gear2d(TEETH_A, rpA), T)
    cB = add((0, 0, 0), mul(u, dAB))
    gB = Disc(cB, u, v, gear2d(TEETH_B, rpB, rot=rotB), T)
    cam = Cam(eye=(-3.0, 13.0, 26.0), target=(5.0, 1.0, -3.0))
    pts = [gA.w(x, y, z) for x, y in ring(rpA + 1, 16) for z in (0, T)] + \
          [gB.w(x, y, z) for x, y in ring(rpB + 1, 16) for z in (0, T)]
    cam.fit(pts, (60, BODY[0] + 6, 420, BODY[1] - 6))
    light = norm((-1.0, 0.6, 0.9))
    out = []

    def mass(g, holes=None):
        o = []
        for _, q, nw in g.sides(cam):
            sq = cam.ps(q)
            o.append(poly(sq, G0, G4, LINE))
            if dot(nw, light) < 0.15:
                o += hatch([sq], spacing=3.2, fill=G3)
        cap = g.cap(cam, g.o)
        o.append(poly(cap, G0, G5, LINE))
        return o
    # B is further from the camera: draw it first
    out += mass(gB)
    out.append(loop(gB.cap(cam, ring(rpB - 1.25 - 0.5, 60)), HAIR, G3))
    out.append(loop(gB.cap(cam, ring(1.7, 32)), HAIR, G3))
    out.append(loop(gB.cap(cam, ring(0.75, 20)), LINE, G4))
    for k in range(12):
        a = rotB - 2 * math.pi * k / 12 + math.pi / 2
        hx, hy = 3.35 * math.cos(a), 3.35 * math.sin(a)
        if k in PCS:
            hole = [(hx + 0.62 * math.cos(t), hy + 0.62 * math.sin(t)) for t in [2 * math.pi * i / 24 for i in range(24)]]
            hs = gB.cap(cam, hole)
            out.append(poly(hs, G0, G4, LINE))
            out += hatch([hs], spacing=3.2, fill=G3)              # the bore's wall in shade
        else:
            mark = [(hx + 0.3 * math.cos(t), hy + 0.2 * math.sin(t)) for t in [2 * math.pi * i / 10 for i in range(10)]]
            out.append(loop(gB.cap(cam, mark), HAIR, G3))
    out += mass(gA)
    out.append(loop(gA.cap(cam, ring(rpA - 1.25 - 0.5, 40)), HAIR, G3))
    out.append(loop(gA.cap(cam, ring(1.3, 28)), HAIR, G3))
    out.append(loop(gA.cap(cam, ring(0.6, 20)), LINE, G4))
    # brightest: the edge of B's tooth that sits in A's gap, top face
    tB = gear2d(TEETH_B, rpB, rot=rotB)[0:4]
    out.append(ribbon(gB.cap(cam, tB), SUBJ, G7))
    return frame(out)


# =================================================================== v5
def v5():
    """Edge-lit silhouette: the hand-cranked pair, close up. Every part is a
    black mass; only edges turned to the light (upper left) catch a rim, the
    rest is a ground line. The crank handle, the thing in the hand, carries the
    brightest edge. B is spoked, one spoke a semitone: the scale's seven are
    polished and catch the light, the other five stay dark."""
    rpA, rpB = TEETH_A / 2, TEETH_B / 2
    dAB = rpA + rpB
    X, Y = (1, 0, 0), (0, 1, 0)
    rotB = math.pi + math.pi / TEETH_B
    T = 1.4
    gA = Disc((0, 0, 0), X, Y, gear2d(TEETH_A, rpA), T)
    gB = Disc((dAB, 0, 0), X, Y, gear2d(TEETH_B, rpB, rot=rotB), T)
    crank_a = math.radians(128)
    arm_len = 7.4
    hc = (arm_len * math.cos(crank_a), arm_len * math.sin(crank_a))
    cam = Cam(eye=(-14.0, 6.0, 30.0), target=(3.0, 0.0, 0.0))
    cam.fit([gA.w(x, y, 0) for x, y in ring(rpA + 1, 12)] +
            [(hc[0] - 1, hc[1] + 1, 6.0), (hc[0] - 1, hc[1] - 1, 2.0),
             (dAB, -rpB - 1, 0), (dAB, rpB + 1, 0), (dAB - 3, -rpB - 1, 0)],
            (36, BODY[0] + 4, 330, BODY[1] - 2))
    light = norm2((-0.62, -0.78))

    def lit(pts, closed=True, hi=G5, lo=G1, wd=LINE, thresh=0.15, lo_w=HAIR):
        """Rim-light a screen outline (CCW or CW): runs facing the light in
        `hi`, the rest in a ground line."""
        ring_ = list(pts) + ([pts[0]] if closed else [])
        area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(ring_, ring_[1:]))
        sgn = 1 if area > 0 else -1
        o, run, state = [], [ring_[0]], None
        for a, b in zip(ring_, ring_[1:]):
            ex, ey = b[0] - a[0], b[1] - a[1]
            L = math.hypot(ex, ey) or 1
            nx, ny = -sgn * ey / L, sgn * ex / L
            nx, ny = -nx, -ny
            s = (nx * light[0] + ny * light[1]) > thresh
            if state is None:
                state = s
            if s != state:
                if lo is not None or state:
                    o.append(ribbon(run, wd if state else lo_w, hi if state else lo))
                run, state = [a], s
            run.append(b)
        if lo is not None or state:
            o.append(ribbon(run, wd if state else lo_w, hi if state else lo))
        return o

    def mass(g):
        o = [poly(cam.ps(q), G0) for _, q, _ in g.sides(cam)]
        sil = cam.ps([g.w(x, y, 0) for x, y in g.o])
        o.append(poly(sil, G0) if len(sil) <= 64 else big_poly(sil, G0))
        cap = g.cap(cam, g.o)
        o.append(poly(cap, G0))
        o += lit(cap)
        return o
    out = []
    out += mass(gB)
    rin, hub = rpB - 1.25 - 0.8, 1.5
    out += lit(gB.cap(cam, ring(rin, 72)[::-1]), hi=G4, lo=G1, wd=HAIR)
    out += lit(gB.cap(cam, ring(hub, 32)), hi=G4, lo=G1, wd=HAIR)
    out += lit(gB.cap(cam, ring(0.55, 16)), hi=G1, lo=G4, wd=HAIR, lo_w=LINE)
    for k in range(12):
        a = math.pi / 2 - 2 * math.pi * k / 12
        on = k in PCS
        ca, sa = math.cos(a), math.sin(a)
        for s in (-1, 1):
            off = 0.3 * s
            p0 = (hub * ca - off * sa, hub * sa + off * ca)
            p1 = (rin * ca - off * sa, rin * sa + off * ca)
            sp = gB.cap(cam, [p0, p1])
            # the screen normal of this edge, pointing out of the spoke
            mx, my = gB.cap(cam, [(0.5 * (hub + rin) * ca, 0.5 * (hub + rin) * sa)])[0]
            ex, ey = sp[1][0] - sp[0][0], sp[1][1] - sp[0][1]
            nx, ny = -ey, ex
            if nx * (sp[0][0] - mx) + ny * (sp[0][1] - my) < 0:
                nx, ny = -nx, -ny
            facing = nx * light[0] + ny * light[1] > 0
            if on and facing:
                out.append(ribbon(sp, LINE, G5))
            elif on:
                out.append(ribbon(sp, HAIR, G2))
            else:
                out.append(ribbon(sp, HAIR, G1))
    out += mass(gA)
    out += lit(gA.cap(cam, ring(rpA - 1.25 - 0.45, 40)[::-1]), hi=G3, lo=None, wd=HAIR)
    # crank arm on A's face
    ux, uy = math.cos(crank_a), math.sin(crank_a)
    arm_o = []
    for t in range(9):
        a = crank_a + math.pi / 2 + math.pi * t / 8           # round boss at the hub
        arm_o.append((1.15 * math.cos(a), 1.15 * math.sin(a)))
    for t in range(9):
        a = crank_a - math.pi / 2 + math.pi * t / 8           # round end at the handle
        arm_o.append((hc[0] + 0.8 * math.cos(a), hc[1] + 0.8 * math.sin(a)))
    arm = Disc((0, 0, T), X, Y, arm_o, 0.5)
    out += mass(arm)
    out += lit(arm.cap(cam, ring(0.45, 14)), hi=G1, lo=G4, wd=HAIR, lo_w=LINE)
    # the handle stands out of the arm toward the viewer
    hd = Disc((hc[0], hc[1], T + 0.5), X, Y, ring(0.7, 24), 4.2)
    body = cam.ps([hd.w(x, y, z) for x, y in hd.o for z in (0, 4.2)])
    sil = convex_hull(body)
    out.append(poly(sil, G0))
    out += lit(sil, hi=G7, lo=G1, wd=SUBJ, thresh=0.25)
    out += lit(hd.cap(cam, hd.o), hi=G1, lo=G4, wd=HAIR, thresh=0.25)
    return frame(out)


def norm2(v):
    L = math.hypot(*v)
    return (v[0] / L, v[1] / L)


def main():
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        d = HERE / name
        d.mkdir(exist_ok=True)
        (d / "rest.svg").write_text(fn())
        print(d / "rest.svg")


if __name__ == "__main__":
    main()
