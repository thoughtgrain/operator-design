#!/usr/bin/env python3
"""Kiln subject pass 02: one rest-frame sketch per direction (v1..v5).

Every sketch is the rest frame at the definition's defaults (strike 50,
glaze 30, crack 0, fire 1.12), stock header kept, 480 x 220, no text below
the header. 3D things (bowls, mallets, ring courses, cones) are modelled in
world units and projected through one camera per frame (craft.md, Think in
3D); flat sections (v2, the kiln walls in v3) are drawn in the screen plane.

Line weights: hairline 1.1, line 1.5, subject 2.2. One brightest element
(#CDCDCD) per frame. Semi-opaque glaze is 45-degree hatching, >= 4 px apart,
clipped to its region. Lines are closed ribbons; bodies are black fills
behind their outlines.

    python3 screens/kiln/passes/02-subject/sketch.py
"""
from __future__ import annotations

import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 480, 220

G0, G1, G2, G3, G4, G5, G6, BK = ("#CDCDCD", "#AFAFAF", "#969696", "#7D7D7D",
                                  "#646464", "#4B4B4B", "#323232", "#000000")
HAIR, LINE, SUBJ = 1.1, 1.5, 2.2
HATCH = 4.0

TITLES = ["strike", "glaze", "crack", "fire"]
VALUES = ["50", "30", "0", "1.12"]
FONT = 'font-family="UniversNextPro-Light"'

# defaults
STRIKE, GLAZE, CRACK, FIRE = 0.5, 0.3, 0.0, 0.5


def f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# ----------------------------------------------------------------- 2D helpers
def dedupe(pts, gap=0.6, closed=False):
    out = []
    for p in pts:
        p = (round(p[0], 2), round(p[1], 2))
        if not out or math.dist(p, out[-1]) >= gap:
            out.append(p)
    if closed:
        while len(out) > 3 and math.dist(out[0], out[-1]) < gap:
            out.pop()
    return out


def decimate(pts, n=60):
    if len(pts) <= n:
        return pts
    return [pts[round(i * (len(pts) - 1) / (n - 1))] for i in range(n)]


def offset_line(pts, d, closed=False):
    """Offset a polyline by d (left of travel), mitred and clamped."""
    n = len(pts)
    out = []
    for i in range(n):
        if closed:
            a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
        else:
            a = pts[i - 1] if i > 0 else None
            b = pts[i]
            c = pts[i + 1] if i < n - 1 else None
        dirs = []
        for p, q in ((a, b), (b, c)):
            if p is None or q is None:
                continue
            dx, dy = q[0] - p[0], q[1] - p[1]
            L = math.hypot(dx, dy) or 1
            dirs.append((dx / L, dy / L))
        tx = sum(v[0] for v in dirs)
        ty = sum(v[1] for v in dirs)
        L = math.hypot(tx, ty) or 1
        tx, ty = tx / L, ty / L
        nx, ny = ty, -tx
        k = d
        if len(dirs) == 2:
            cos = dirs[0][0] * tx + dirs[0][1] * ty
            k = d / max(cos, 0.5)
        out.append((b[0] + nx * k, b[1] + ny * k))
    return out


def ribbon_pts(pts, w):
    left = offset_line(pts, w / 2)
    right = offset_line(pts, -w / 2)
    return left + right[::-1]


def inside(pt, poly):
    x, y = pt
    c = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xi > x:
                c = not c
    return c


def hull(points):
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in points))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def resample_closed(poly, step=4.0):
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        L = math.dist(a, b)
        k = max(1, int(L / step))
        for j in range(k):
            t = j / k
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def ellipse(cx, cy, rx, ry, a0=0.0, a1=2 * math.pi, n=48):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / (n - 1)),
             cy + ry * math.sin(a0 + (a1 - a0) * i / (n - 1))) for i in range(n)]


def intervals(poly, c):
    """Where the line x + y = c crosses poly: sorted parameter x values, paired."""
    xs = []
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        u1, u2 = x1 + y1 - c, x2 + y2 - c
        if (u1 > 0) != (u2 > 0):
            t = u1 / (u1 - u2)
            xs.append(x1 + (x2 - x1) * t)
    xs.sort()
    return [(xs[i], xs[i + 1]) for i in range(0, len(xs) - 1, 2)]


def isect(a, b):
    out = []
    for p, q in a:
        for r, s in b:
            lo, hi = max(p, r), min(q, s)
            if hi > lo:
                out.append((lo, hi))
    return out


def minus(a, b):
    out = a
    for r, s in b:
        nxt = []
        for p, q in out:
            if s <= p or r >= q:
                nxt.append((p, q))
                continue
            if r > p:
                nxt.append((p, r))
            if s < q:
                nxt.append((s, q))
        out = nxt
    return out


# ----------------------------------------------------------------- frame
class Frame:
    def __init__(self) -> None:
        self.out: list[str] = []
        self.node = 0
        self.palette = [G0, G2, G4, G6]

    def nid(self, bound):
        if not bound:
            return ""
        i = self.node
        self.node += 1
        return f' id="kiln_node_{i}"'

    def poly(self, pts, fill=BK, stroke="none", sw=0.0, bound=False):
        """A closed shape: black (or other) body, optional outline."""
        pts = dedupe(pts, closed=True)
        pts = decimate(pts, 62)
        if len(pts) < 3:
            return
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
        sws = f' stroke-width="{f(sw)}"' if stroke != "none" else ' stroke-width="0"'
        self.out.append(f'  <path{self.nid(bound)} d="{d}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def line(self, pts, w, colour, bound=False, closed=False):
        """An open (or closed) line drawn as thin closed ribbons of <= 28 points."""
        pts = dedupe(pts)
        if closed and pts:
            pts = pts + [pts[0]]
        if len(pts) < 2:
            return
        segs = len(pts) - 1
        chunks = max(1, math.ceil(segs / 27))
        step = math.ceil(segs / chunks)
        i = 0
        while i < len(pts) - 1:
            run = pts[i:i + step + 1]
            if len(run) >= 2:
                outline = dedupe(ribbon_pts(run, w), gap=0.15, closed=True)
                if len(outline) >= 3:
                    d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in outline) + " Z"
                    self.out.append(f'  <path{self.nid(bound)} d="{d}" fill="{colour}" stroke="none" stroke-width="0"/>')
            i += step

    def circle(self, cx, cy, r, fill=BK, stroke="none", sw=0.0, bound=False):
        sws = f' stroke-width="{f(sw)}"' if stroke != "none" else ' stroke-width="0"'
        self.out.append(f'  <circle{self.nid(bound)} cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def runs(self, pts, mask, w, colour, minlen=3):
        """Draw the runs of a sampled curve where mask is true."""
        def emit(run):
            if len(run) >= minlen:
                xs, ys = [p[0] for p in run], [p[1] for p in run]
                if max(max(xs) - min(xs), max(ys) - min(ys)) >= 5:
                    self.line(run, w, colour)
        run = []
        for p, m in zip(pts, mask):
            if m:
                run.append(p)
            else:
                emit(run)
                run = []
        emit(run)

    def hatch(self, inc, exc=(), colour=G4, w=HAIR, spacing=HATCH, phase=0.0):
        """45-degree hairlines inside every polygon of inc and outside every one of exc."""
        allp = [p for poly in inc for p in poly]
        lo = min(x + y for x, y in allp)
        hi = max(x + y for x, y in allp)
        c = math.floor((lo - phase) / spacing) * spacing + phase
        while c <= hi:
            iv = intervals(inc[0], c)
            for poly in inc[1:]:
                iv = isect(iv, intervals(poly, c))
            for poly in exc:
                iv = minus(iv, intervals(poly, c))
            for x0, x1 in iv:
                if x1 - x0 > 3.2:
                    a = (x0 + 0.5, c - x0 - 0.5)
                    b = (x1 - 0.5, c - x1 + 0.5)
                    self.line([a, b], w, colour)
            c += spacing

    def svg(self) -> str:
        head = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
            '  <g id="preview_canvas">',
            f'    <rect x="0" y="0" width="{W}" height="{H}" fill="#000000" stroke="none"/>',
            '  </g>',
            '  <g id="preview_header">',
        ]
        steps = [BK, G6, G5, G4, G3, G2, G1, G0]
        for k, c in enumerate(steps):
            head.append(f'    <rect x="{60 * k}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
        for k in range(4):
            ink = "#CBCBCB" if k < 2 else "#000000"
            head.append(f'    <text transform="matrix(1 0 0 1 {5 + 120 * k} 10)" fill="{ink}" stroke="none" {FONT} font-size="10px">{TITLES[k]}</text>')
        for k in range(4):
            ink = "#CBCBCB" if k < 2 else "#000000"
            head.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * k} 17.44)" fill="{ink}" stroke="none" {FONT} font-size="20px">{VALUES[k]}</text>')
        head.append('  </g>')
        pal = [f'  <path id="kiln_palette_{i}" d="M {700 + 10 * i} 300 L {704 + 10 * i} 300 L {704 + 10 * i} 304 Z" '
               f'fill="{c}" stroke="{c}" stroke-width="2"/>' for i, c in enumerate(self.palette)]
        return "\n".join(head + pal + self.out + ["</svg>", ""])


# ----------------------------------------------------------------- 3D
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def mul(a, k): return (a[0] * k, a[1] * k, a[2] * k)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross3(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def norm(a):
    L = math.sqrt(dot(a, a)) or 1
    return (a[0] / L, a[1] / L, a[2] / L)


class Cam:
    """One perspective camera: eye, look-at, focal length, screen centre."""

    def __init__(self, elev_deg, dist, target=(0, 0, 0), azim_deg=0.0, focal=1.0, cx=240.0, cy=120.0):
        e, a = math.radians(elev_deg), math.radians(azim_deg)
        self.target = target
        self.eye = add(target, (dist * math.cos(e) * math.sin(a), -dist * math.cos(e) * math.cos(a), dist * math.sin(e)))
        self.fwd = norm(sub(target, self.eye))
        self.right = norm(cross3(self.fwd, (0, 0, 1)))
        self.up = cross3(self.right, self.fwd)
        self.f, self.cx, self.cy = focal, cx, cy

    def raw(self, P):
        d = sub(P, self.eye)
        z = dot(d, self.fwd)
        return dot(d, self.right) / z, dot(d, self.up) / z, z

    def p(self, P):
        x, y, _ = self.raw(P)
        return (self.cx + self.f * x, self.cy - self.f * y)

    def depth(self, P):
        return dot(sub(P, self.eye), self.fwd)

    def fit(self, pts3, box):
        """Scale and centre so the projected pts3 fill box (x0, y0, x1, y1), aspect kept."""
        r = [self.raw(P)[:2] for P in pts3]
        xs, ys = [q[0] for q in r], [q[1] for q in r]
        x0, y0, x1, y1 = box
        self.f = min((x1 - x0) / (max(xs) - min(xs)), (y1 - y0) / (max(ys) - min(ys)))
        self.cx = (x0 + x1) / 2 - self.f * (max(xs) + min(xs)) / 2
        self.cy = (y0 + y1) / 2 + self.f * (max(ys) + min(ys)) / 2

    def ppr(self, P):
        """Pixels per world unit at P's depth."""
        return self.f / self.depth(P)


class Bowl:
    """A thrown bowl as a surface of revolution about z, foot at z = 0."""

    def __init__(self, R=1.0, Hh=0.62, foot_r=0.42, foot_h=0.08, wall=0.06, lip=0.0, origin=(0, 0, 0)):
        self.R, self.H, self.fr, self.fh, self.w, self.o = R, Hh, foot_r, foot_h, wall, origin
        self.lip = lip

    def outer(self, t):
        """Outer wall profile, t 0 (foot junction) .. 1 (rim): (r, z, nr, nz) with outward normal."""
        a = t * math.pi / 2
        r0 = self.fr - 0.02
        r = r0 + (self.R - r0) * math.sin(a) + self.lip * t ** 6
        z = self.fh + (self.H - self.fh) * (1 - math.cos(a))
        dr = (self.R - r0) * math.cos(a) + 6 * self.lip * t ** 5 * 2 / math.pi
        dz = (self.H - self.fh) * math.sin(a)
        L = math.hypot(dr, dz) or 1
        return r, z, dz / L, -dr / L

    def inner(self, t):
        """Inner wall profile: offset of the outer by the wall; cavity-side normal."""
        r, z, nr, nz = self.outer(t)
        ri, zi = r - self.w * nr, z - self.w * nz
        return max(ri, 0.0), zi, -nr, -nz

    def P(self, r, z, th):
        return add(self.o, (r * math.cos(th), r * math.sin(th), z))

    def ring(self, r, z, n=96):
        return [self.P(r, z, 2 * math.pi * i / n) for i in range(n)]

    def all_outer(self):
        pts = []
        for k in range(13):
            r, z, _, _ = self.outer(k / 12)
            pts += self.ring(r, z, 64)
        pts += self.ring(self.fr, 0, 64)
        return pts


def ring_vis(cam, bowl, r, z, nr, nz, n=180, cavity=False, opening=None):
    pts3 = [bowl.P(r, z, 2 * math.pi * i / n) for i in range(n)]
    out, mask = [], []
    for i, P in enumerate(pts3):
        th = 2 * math.pi * i / n
        nvec = (nr * math.cos(th), nr * math.sin(th), nz)
        q = cam.p(P)
        v = dot(nvec, sub(cam.eye, P)) > 0
        if v and opening is not None:
            v = inside(q, opening)
        out.append(q)
        mask.append(v)
    # rotate so the sequence starts at a hidden sample (runs don't wrap)
    if not all(mask) and any(mask):
        k = mask.index(False)
        out, mask = out[k:] + out[:k], mask[k:] + mask[:k]
    return out, mask


def draw_bowl(F, cam, b, edge=G2, inner_rings=(), outer_rings=(), glaze=None, rim=G2, rim_w=LINE,
              hatch_colour=G4):
    """Hidden-line bowl: black body, silhouette, lip, inner and outer throwing rings, glaze hatching."""
    sil = hull([cam.p(P) for P in b.all_outer()])
    F.poly(resample_closed(sil, 6), fill=BK, stroke=edge, sw=LINE)
    ro, zo, _, _ = b.outer(1)
    ri, zi, _, _ = b.inner(1)
    rim_o = [cam.p(P) for P in b.ring(ro, zo, 96)]
    rim_i = [cam.p(P) for P in b.ring(ri, zi, 96)]
    # interior: black (the cavity's walls hide the front of the body behind them)
    F.poly(rim_i, fill=BK)
    if glaze is not None:
        rg, zg, _, _ = b.inner(glaze)
        g_ring = [cam.p(P) for P in b.ring(rg, zg, 96)]
        F.hatch([g_ring, rim_i], colour=hatch_colour)
        pts, mask = ring_vis(cam, b, rg, zg, *b.inner(glaze)[2:], cavity=True, opening=rim_i)
        F.runs(pts, mask, HAIR, G3)
    for t in inner_rings:
        r, z, nr, nz = b.inner(t)
        pts, mask = ring_vis(cam, b, r, z, nr, nz, opening=rim_i)
        F.runs(pts, mask, HAIR, G4)
    for t in outer_rings:
        r, z, nr, nz = b.outer(t)
        pts, mask = ring_vis(cam, b, r, z, nr, nz)
        F.runs(pts, mask, HAIR, G4)
    # foot junction
    pts, mask = ring_vis(cam, b, b.fr, b.fh, 0.0, -1.0)
    pts, mask = ring_vis(cam, b, b.fr, b.fh, 1.0, -0.15)
    F.runs(pts, mask, HAIR, G4)
    F.line(rim_i, rim_w, rim, closed=True)
    F.line(rim_o, rim_w, rim, closed=True)
    return sil, rim_o, rim_i


def draw_mallet(F, cam, A, B, rh, rs, head=G0, head_w=SUBJ, shaft=G3, wraps=4, wrap_colour=G4):
    """A yarn-wound mallet: handle cylinder A->B, sphere head at B with wraps about the shaft axis."""
    a, b = cam.p(A), cam.p(B)
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    wa, wb = rh * cam.ppr(A), rh * cam.ppr(B)
    shaft_poly = [(a[0] + nx * wa, a[1] + ny * wa), (b[0] + nx * wb, b[1] + ny * wb),
                  (b[0] - nx * wb, b[1] - ny * wb), (a[0] - nx * wa, a[1] - ny * wa)]
    F.poly(shaft_poly, fill=BK, stroke=shaft, sw=LINE)
    # butt end ellipse
    axis = norm(sub(B, A))
    u = norm(cross3(axis, (0, 0, 1)))
    v = cross3(axis, u)
    butt = [cam.p(add(A, add(mul(u, rh * math.cos(t)), mul(v, rh * math.sin(t))))) for t in
            [2 * math.pi * i / 32 for i in range(32)]]
    F.poly(butt, fill=BK, stroke=shaft, sw=HAIR)
    # head
    c = cam.p(B)
    R = rs * cam.ppr(B)
    F.circle(c[0], c[1], R, fill=BK, stroke=head, sw=head_w)
    # wraps: circles on the sphere about the shaft axis, front half only
    for k in range(1, wraps + 1):
        phi = -0.75 + 1.5 * k / (wraps + 1)          # latitude along the axis
        cr = rs * math.cos(phi)
        cc = add(B, mul(axis, rs * math.sin(phi)))
        pts, mask = [], []
        for i in range(120):
            t = 2 * math.pi * i / 120
            P = add(cc, add(mul(u, cr * math.cos(t)), mul(v, cr * math.sin(t))))
            nvec = norm(sub(P, B))
            pts.append(cam.p(P))
            mask.append(dot(nvec, sub(cam.eye, P)) > 0.05 * rs)
        if not all(mask) and any(mask):
            j = mask.index(False)
            pts, mask = pts[j:] + pts[:j], mask[j:] + mask[:j]
        pts = [(c[0] + (x - c[0]) * 0.94, c[1] + (y - c[1]) * 0.94) for x, y in pts]
        F.runs(pts, mask, HAIR, wrap_colour)
    return c, R


# ================================================================= v1
def v1() -> Frame:
    """The mallet in the hand over a hidden-line bowl."""
    F = Frame()
    F.palette = [G0, G2, G3, G4]
    b = Bowl(Hh=0.74, lip=0.0)
    cam = Cam(elev_deg=30, dist=7.0, azim_deg=-14)
    # mallet: pivot (wrist) up and right; backswing angle from strike
    swing = math.radians(10 + 40 * STRIKE)               # 10 .. 50 deg above the strike line
    contact = b.P(1.0 + 0.26, 0.78, math.radians(-8))   # head centre where it meets the rim
    wrist = add(contact, (1.25, -0.35, 0.2))
    arm = sub(contact, wrist)
    Lm = math.sqrt(dot(arm, arm))
    # rotate the arm about the wrist in the vertical plane through it
    hd = norm((arm[0], arm[1], 0))
    ang0 = math.atan2(arm[2], math.hypot(arm[0], arm[1]))
    ang = ang0 + swing
    head = add(wrist, (hd[0] * Lm * math.cos(ang), hd[1] * Lm * math.cos(ang), Lm * math.sin(ang)))
    scene = b.all_outer() + [wrist, head, add(head, (0, 0, 0.3)), add(head, (0, 0, -0.3))]
    cam.fit(scene, (70, 28, 430, 208))
    sil, rim_o, rim_i = draw_bowl(F, cam, b, edge=G2, inner_rings=(0.3, 0.55, 0.78),
                                  outer_rings=(0.25, 0.5, 0.75), glaze=GLAZE * 0.9 + 0.05, rim=G2)
    # the rim point the mallet aims at: a short travel arc from head back to contact (dashed, hairline)
    arc_pts = []
    for i in range(14):
        a2 = ang0 + swing * i / 13
        P = add(wrist, (hd[0] * Lm * math.cos(a2), hd[1] * Lm * math.cos(a2), Lm * math.sin(a2)))
        arc_pts.append(cam.p(P))
    draw_mallet(F, cam, wrist, head, rh=0.045, rs=0.24, wraps=4)
    return F


# ================================================================= v2
def v2() -> Frame:
    """The fired body seen close: a rim fragment in section, glaze skin, pores, a felt tip."""
    F = Frame()
    F.palette = [G0, G2, G3, G6]
    rnd = random.Random(5)
    # the wall: a curved slab, concave side up, rising to a rounded lip at the right
    def mid(t):  # centreline, t 0..1
        return 44 + 282 * t, 186 - 86 * t ** 2.4
    thick = 42
    N = 36
    cl = [mid(i / N) for i in range(N + 1)]
    up = offset_line(cl, thick / 2)        # inner (glazed) face
    dn = offset_line(cl, -thick / 2)       # outer face
    ex, ey = cl[-1]
    tx, ty = cl[-1][0] - cl[-2][0], cl[-1][1] - cl[-2][1]
    L = math.hypot(tx, ty)
    tx, ty = tx / L, ty / L
    nx, ny = ty, -tx
    lip = [(ex + tx * thick / 2 * math.sin(math.pi * i / 10) + nx * thick / 2 * math.cos(math.pi * i / 10),
            ey + ty * thick / 2 * math.sin(math.pi * i / 10) + ny * thick / 2 * math.cos(math.pi * i / 10))
           for i in range(1, 10)]
    # broken edge at the left: a stepped fracture across the wall
    a0, b0 = up[0], dn[0]
    frac = [(b0[0] + 6, b0[1] - 8), (b0[0] - 3, b0[1] - 17), (a0[0] + 8, a0[1] + 14), (a0[0] + 1, a0[1] + 6)]
    body = up + lip + dn[::-1] + frac
    # glaze skin on the concave face: thickness from glaze
    gt = 5 + 16 * GLAZE
    gl = offset_line(cl, thick / 2 + gt)
    skin = gl[1:-2] + up[1:-2][::-1]
    F.poly(body, fill=BK, stroke=G0, sw=SUBJ)
    # double outline: a keyline inside the body, parallel to the outer face
    F.line(offset_line(cl[2:-1], -thick / 2 + 5), HAIR, G5)
    # glaze skin: glassy, so hatched; its free surface a line
    F.poly(skin, fill=BK, stroke=G2, sw=LINE)
    F.hatch([skin], colour=G4, spacing=4)
    # pores: closed ovals in the body, fewer as the body vitrifies (fire)
    npores = int(round(17 - 12 * FIRE))
    placed = []
    tries = 0
    while len(placed) < npores and tries < 2000:
        tries += 1
        t = rnd.uniform(0.07, 0.93)
        s = rnd.uniform(-0.22, 0.22)
        i = min(N - 1, int(t * N))
        k = (cl[i + 1][0] - cl[i][0], cl[i + 1][1] - cl[i][1])
        Lk = math.hypot(*k) or 1
        x, y = mid(t)
        px, py = x + (k[1] / Lk) * s * thick, y - (k[0] / Lk) * s * thick
        if any(math.dist((px, py), q) < 17 for q in placed):
            continue
        placed.append((px, py))
        rx, ry = rnd.uniform(4.5, 7), rnd.uniform(2.8, 3.8)
        rot = math.atan2(k[1], k[0]) + rnd.uniform(-0.3, 0.3)
        ov = [(px + rx * math.cos(a) * math.cos(rot) - ry * math.sin(a) * math.sin(rot),
               py + rx * math.cos(a) * math.sin(rot) + ry * math.sin(a) * math.cos(rot))
              for a in [2 * math.pi * i / 20 for i in range(20)]]
        F.poly(ov, fill=BK, stroke=G3, sw=LINE)
    # felt mallet tip resting on the lip (strike: soft and broad .. hard and small)
    tip_r = 26 - 12 * STRIKE
    top = (ex + nx * thick / 2 * 0.15, ey - thick / 2 * 0.95)
    d = (0.62, -0.78)
    cx, cy = top[0] + d[0] * (tip_r + 1), top[1] + d[1] * (tip_r + 1)
    sx, sy = cx + 64, cy - 22
    dx, dy = sx - cx, sy - cy
    L = math.hypot(dx, dy)
    qx, qy = -dy / L * 5, dx / L * 5
    F.poly([(cx + qx, cy + qy), (sx + qx, sy + qy), (sx - qx, sy - qy), (cx - qx, cy - qy)],
           fill=BK, stroke=G3, sw=LINE)
    F.poly([(sx + qx * 1.4, sy + qy * 1.4), (sx + 8 * dx / L + qx * 1.4, sy + 8 * dy / L + qy * 1.4),
            (sx + 8 * dx / L - qx * 1.4, sy + 8 * dy / L - qy * 1.4), (sx - qx * 1.4, sy - qy * 1.4)],
           fill=BK, stroke=G3, sw=LINE)
    F.circle(cx, cy, tip_r, fill=BK, stroke=G2, sw=SUBJ)
    F.circle(cx, cy, tip_r - 5, fill=BK, stroke=G4, sw=HAIR)
    return F


# ================================================================= v3
def v3() -> Frame:
    """The kiln opened: brick chamber in section, one bowl on the shelf, cone bent, a tapping rod."""
    F = Frame()
    F.palette = [G0, G2, G3, G4]
    x0, x1 = 92, 388          # chamber inside
    yfloor = 196
    yspring = 112            # arch springs here
    wall = 26
    bh, bw = 12, 26           # brick course height, brick length
    # walls: brick courses, outlined, staggered
    for side in (0, 1):
        xa = x0 - wall if side == 0 else x1
        xb = x0 if side == 0 else x1 + wall
        y = yfloor + 14
        row = 0
        while y - bh >= yspring - 2:
            off = (row % 2) * bw / 2
            xs = [xa] + [x for x in [xa - off + bw * k for k in range(1, 4)] if xa < x < xb] + [xb]
            for p, q in zip(xs, xs[1:]):
                if q - p > 4:
                    F.poly([(p + 1, y - bh + 1), (q - 1, y - bh + 1), (q - 1, y - 1), (p + 1, y - 1)],
                           fill=BK, stroke=G5, sw=HAIR)
            y -= bh
            row += 1
    # sprung arch: voussoirs between two circles
    cxa, R1 = (x0 + x1) / 2, (x1 - x0) / 2 / math.sin(math.radians(38))
    cya = yspring + R1 * math.cos(math.radians(38))
    R2 = R1 + wall
    a0, a1 = math.radians(-90 - 38), math.radians(-90 + 38)
    nvs = 17
    for k in range(nvs):
        aa = a0 + (a1 - a0) * k / nvs + 0.004
        ab = a0 + (a1 - a0) * (k + 1) / nvs - 0.004
        pts = ellipse(cxa, cya, R1 + 1, R1 + 1, aa, ab, 5) + ellipse(cxa, cya, R2 - 1, R2 - 1, ab, aa, 5)
        F.poly(pts, fill=BK, stroke=G5, sw=HAIR)
    # floor slab line and chamber outline (cut face edge), one line weight
    F.line([(x0 - wall - 6, yfloor + 15), (x1 + wall + 6, yfloor + 15)], LINE, G4)
    F.line([(x0, yfloor + 2), (x0, yspring)], LINE, G3)
    F.line([(x1, yfloor + 2), (x1, yspring)], LINE, G3)
    F.line(ellipse(cxa, cya, R1, R1, a0, a1, 40), LINE, G3)
    # spy hole through the right wall: gap where the rod enters
    # shelf on posts
    sy = 168
    F.poly([(120, sy), (330, sy), (330, sy + 6), (120, sy + 6)], fill=BK, stroke=G3, sw=HAIR)
    for px in (132, 306):
        F.poly([(px, sy + 7), (px + 10, sy + 7), (px + 10, yfloor + 1), (px, yfloor + 1)], fill=BK, stroke=G4, sw=HAIR)
    # bowl on the shelf, one camera (low and almost level, as through the open front)
    b = Bowl()
    cam = Cam(elev_deg=14, dist=8.0)
    cam.fit(b.all_outer(), (166, 104, 290, sy))
    draw_bowl(F, cam, b, edge=G0, outer_rings=(0.35, 0.65), inner_rings=(0.6,), rim=G0, rim_w=SUBJ)
    # glaze on the outside from the rim down: hatched band between the rim's front and the glaze line
    g = 1 - (0.15 + 0.6 * GLAZE)
    sil = hull([cam.p(P) for P in b.all_outer()])
    r, z, nr, nz = b.outer(g)
    gl, gm = ring_vis(cam, b, r, z, nr, nz)
    front = sorted([p for p, m in zip(gl, gm) if m])
    ro_, zo_ = b.outer(1)[0], b.outer(1)[1]
    rim_front = sorted([cam.p(b.P(ro_, zo_, -math.pi * i / 63)) for i in range(64)])
    region = front + rim_front[::-1]
    F.hatch([region, sil], colour=G4)
    F.runs(gl, gm, HAIR, G2)
    # pyrometric cone in its pad, bent by fire, left of the bowl on the shelf
    padx, pady = 140, sy
    F.poly([(padx - 9, pady), (padx + 9, pady), (padx + 7, pady - 6), (padx - 7, pady - 6)], fill=BK, stroke=G3, sw=HAIR)
    bend = math.radians(10 + 80 * FIRE)
    base = (padx, pady - 6)
    Lc = 34
    spine = []
    for i in range(13):
        s = i / 12
        a = bend * s ** 1.6
        # integrate a curve leaning right
        if i == 0:
            spine.append(base)
        else:
            px, py = spine[-1]
            spine.append((px + math.sin(a) * Lc / 12, py - math.cos(a) * Lc / 12))
    wv = [4.0 * (1 - i / 12) + 0.7 for i in range(13)]
    left, right = [], []
    for i in range(13):
        if i < 12:
            dx, dy = spine[i + 1][0] - spine[i][0], spine[i + 1][1] - spine[i][1]
        L = math.hypot(dx, dy)
        nx, ny = -dy / L, dx / L
        left.append((spine[i][0] + nx * wv[i], spine[i][1] + ny * wv[i]))
        right.append((spine[i][0] - nx * wv[i], spine[i][1] - ny * wv[i]))
    F.poly(left + right[::-1], fill=BK, stroke=G2, sw=LINE)
    # tapping rod through the spy hole in the right wall, its tip off the rim by strike
    ro = cam.p(b.P(b.outer(1)[0], b.outer(1)[1] - 0.04, 0))
    gap = 6 + 30 * (1 - STRIKE)
    tip = (ro[0] + gap, ro[1] + 2)
    end = (x1 + wall + 30, tip[1] - 8)
    dx, dy = end[0] - tip[0], end[1] - tip[1]
    L = math.hypot(dx, dy)
    qx, qy = -dy / L * 2.2, dx / L * 2.2
    F.poly([(tip[0] + qx, tip[1] + qy), (end[0] + qx, end[1] + qy), (end[0] - qx, end[1] - qy),
            (tip[0] - qx, tip[1] - qy)], fill=BK, stroke=G2, sw=LINE)
    F.circle(tip[0], tip[1], 4.5, fill=BK, stroke=G2, sw=LINE)
    return F


# ================================================================= v4
def v4() -> Frame:
    """The bowl exploded along its axis into ring courses, spaced like its modes."""
    F = Frame()
    F.palette = [G0, G2, G3, G4]
    b = Bowl()
    cam = Cam(elev_deg=26, dist=9.0)
    ncourse = 4
    ts = [math.acos(1 - i / ncourse) * 2 / math.pi for i in range(ncourse + 1)]   # equal heights
    stretch = 1.0 + 0.24 * FIRE
    # exploded offsets: gap grows up the stack like the stretched upper modes
    gaps = [0.0]
    for k in range(1, ncourse + 1):
        gaps.append(gaps[-1] + 0.2 * (1 + 2.0 * (stretch - 1) * k))
    # foot ring is course 0 (below everything)
    courses = []
    for k in range(ncourse):
        ta, tb = ts[k], ts[k + 1]
        ra, za, _, _ = b.outer(ta)
        rb, zb, _, _ = b.outer(tb)
        ia, iza, _, _ = b.inner(ta)
        ib, izb, _, _ = b.inner(tb)
        dz = gaps[k + 1]
        courses.append(((ra, za + dz), (rb, zb + dz), (max(ia, 0.04), iza + dz), (ib, izb + dz)))
    foot = ((b.fr, -0.06), (b.fr - 0.02, b.fh - 0.06))
    allp = []
    for (oa, ob, ia, ib) in courses:
        allp += b.ring(ob[0], ob[1], 32) + b.ring(oa[0], oa[1], 32)
    allp += b.ring(b.fr, -0.2, 32)
    allp += [(0, 0, gaps[-1] + 1.15), (0.0, 0, -0.4)]
    mallet_head = (1.55, -0.2, gaps[-1] + 0.95)
    mallet_wrist = (2.6, 0.4, gaps[-1] + 1.6)
    allp += [mallet_head, mallet_wrist]
    cam.fit(allp, (110, 30, 380, 208))
    # axis: dashed hairline from below the foot to above the top course
    top = cam.p((0, 0, gaps[-1] + 0.95))
    bot = cam.p((0, 0, -0.4))
    nd = 22
    axis = [(bot[0] + (top[0] - bot[0]) * i / nd, bot[1] + (top[1] - bot[1]) * i / nd) for i in range(nd + 1)]
    axis_segments = [axis[i:i + 2] for i in range(0, nd, 2)]
    # foot ring (a short cylinder)
    fa = [cam.p(P) for P in b.ring(b.fr, -0.2, 64)]
    fb = [cam.p(P) for P in b.ring(b.fr, b.fh - 0.2, 64)]
    fi = [cam.p(P) for P in b.ring(b.fr - 0.06, b.fh - 0.2, 64)]
    for seg in axis_segments:
        if seg[0][1] > fb[0][1] + 30:
            F.line(seg, HAIR, G5)
    F.poly(hull(fa + fb), fill=BK, stroke=G3, sw=LINE)
    F.line(fb, HAIR, G3, closed=True)
    F.line(fi, HAIR, G4, closed=True)
    # courses bottom to top
    for k, (oa, ob, ia, ib) in enumerate(courses):
        OA = [cam.p(P) for P in b.ring(oa[0], oa[1], 72)]
        OB = [cam.p(P) for P in b.ring(ob[0], ob[1], 72)]
        IB = [cam.p(P) for P in b.ring(ib[0], ib[1], 72)]
        IA = [cam.p(P) for P in b.ring(ia[0], ia[1], 72)]
        shell = hull(OA + OB)
        # axis dashes seen through the hole of this course get drawn before it
        F.poly(resample_closed(shell, 6), fill=BK, stroke=G2 if k < ncourse - 1 else G0,
               sw=LINE if k < ncourse - 1 else SUBJ)
        # glazed inner wall: hatched where glaze reaches (from the bottom courses up)
        reach = GLAZE * ncourse + 0.6
        if k < reach:
            F.hatch([IB], exc=[IA], colour=G4, spacing=4)
        # inner bottom edge, back arc visible inside the top hole
        mask = [inside(q, IB) or True for q in IA]
        vis = [inside(q, IB) and q[1] < cam.p((0, 0, ia[1]))[1] for q in IA]
        F.runs(IA, vis, HAIR, G3)
        # top face: outer front arc (inner edge of the side band) and the inner lip
        front = [q[1] > cam.p((0, 0, ob[1]))[1] for q in OB]
        F.runs(OB, front, HAIR if k < ncourse - 1 else LINE, G2 if k < ncourse - 1 else G0)
        F.line(IB, HAIR if k < ncourse - 1 else LINE, G2 if k < ncourse - 1 else G0, closed=True)
    # axis above the stack
    for seg in axis_segments:
        if seg[0][1] < cam.p((0, 0, courses[-1][1][1]))[1] - 18:
            F.line(seg, HAIR, G5)
    # mallet, exploded off to the upper right along its own line of strike
    draw_mallet(F, cam, mallet_wrist, mallet_head, rh=0.04, rs=0.2, head=G2, head_w=LINE, wraps=3)
    return F


# ================================================================= v5
def v5() -> Frame:
    """The ringing bowl cut through its axis: cut face, interior contours, one weight throughout."""
    F = Frame()
    F.palette = [G0, G2, G3, G4]
    b = Bowl(wall=0.075 - 0.03 * FIRE, R=1.0, Hh=0.64)
    cam = Cam(elev_deg=22, dist=7.5, azim_deg=0)
    # back half: theta in [0, pi] (y > 0, away from camera)
    def half(r, z, n=64):
        return [b.P(r, z, math.pi * i / (n - 1)) for i in range(n)]
    pts = []
    for k in range(13):
        r, z, _, _ = b.outer(k / 12)
        pts += half(r, z, 24)
    pts += half(b.fr, 0, 24)
    cam.fit(pts, (52, 34, 372, 206))
    # silhouette of the back half: hull of its outer rings + cut profile
    profL = [cam.p((-b.outer(k / 24)[0], 0, b.outer(k / 24)[1])) for k in range(25)]
    profR = [cam.p((b.outer(k / 24)[0], 0, b.outer(k / 24)[1])) for k in range(25)]
    body = hull([cam.p(P) for P in pts])
    F.poly(resample_closed(body, 6), fill=BK, stroke=G3, sw=LINE)
    # interior contours: rings on the inner surface at equal height steps, back half
    ri1, zi1, _, _ = b.inner(1)
    floor_z = b.inner(0)[1]
    n_c = 7
    for k in range(1, n_c):
        zt = floor_z + (zi1 - floor_z) * k / n_c
        # find t with inner z = zt
        lo, hi = 0.0, 1.0
        for _ in range(30):
            m = (lo + hi) / 2
            if b.inner(m)[1] < zt:
                lo = m
            else:
                hi = m
        r, z, _, _ = b.inner(lo)
        ring = [cam.p(P) for P in half(r, z, 64)]
        g_lvl = b.inner(GLAZE * 0.9 + 0.05)[1]
        F.line(ring, LINE, G4 if z > g_lvl else G3)
    # glaze: hatched floor pool region below the glaze contour, back half
    rg, zg, _, _ = b.inner(GLAZE * 0.9 + 0.05)
    g_ring = [cam.p(P) for P in half(rg, zg, 48)]
    F.hatch([g_ring], colour=G4, w=LINE, spacing=5)
    F.line(g_ring, LINE, G2)
    # inner rim back half
    F.line([cam.p(P) for P in half(ri1, zi1, 64)], LINE, G2)
    # cut face: the wall section, one closed outline through both walls, the brightest thing
    n = 13
    fr2 = b.fr - 0.08
    sect = [cam.p((-b.fr, 0, 0))]
    sect += [cam.p((-b.outer(k / n)[0], 0, b.outer(k / n)[1])) for k in range(n + 1)]
    sect += [cam.p((-(b.outer(1)[0] - b.w / 2), 0, b.outer(1)[1] + b.w * 0.45))]
    sect += [cam.p((-b.inner(k / n)[0], 0, b.inner(k / n)[1])) for k in range(n, -1, -1)]
    sect += [cam.p((b.inner(k / n)[0], 0, b.inner(k / n)[1])) for k in range(1, n + 1)]
    sect += [cam.p((b.outer(1)[0] - b.w / 2, 0, b.outer(1)[1] + b.w * 0.45))]
    sect += [cam.p((b.outer(k / n)[0], 0, b.outer(k / n)[1])) for k in range(n, -1, -1)]
    sect += [cam.p((b.fr, 0, 0)), cam.p((fr2, 0, 0)), cam.p((fr2, 0, b.fh)),
             cam.p((-fr2, 0, b.fh)), cam.p((-fr2, 0, 0))]
    F.poly(sect, fill=BK, stroke=G0, sw=LINE)
    # mallet head (felt ball) poised off the right lip, one weight
    lipR = cam.p((b.outer(1)[0], 0, b.outer(1)[1]))
    rs = 14
    gap = 4 + 24 * (1 - STRIKE)
    cx, cy = lipR[0] + rs + gap, lipR[1] - rs * 0.4
    sx, sy = cx + 46, cy - 30
    dx, dy = sx - cx, sy - cy
    L = math.hypot(dx, dy)
    qx, qy = -dy / L * 3, dx / L * 3
    F.poly([(cx + qx, cy + qy), (sx + qx, sy + qy), (sx - qx, sy - qy), (cx - qx, cy - qy)], fill=BK, stroke=G3, sw=LINE)
    F.circle(cx, cy, rs, fill=BK, stroke=G2, sw=LINE)
    return F


def main() -> None:
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        d = HERE / name
        d.mkdir(exist_ok=True)
        (d / "rest.svg").write_text(fn().svg())
        print("wrote", d / "rest.svg")


if __name__ == "__main__":
    main()
