#!/usr/bin/env python3
"""Beacon, subject pass 02: five lighthouses, one rest frame each, from one script.

The owner asked for a lighthouse (pass.json, focus). Each variant takes its own
angle and way of drawing (pass.json, directions). Every frame is 480 x 220,
keeps the stock header, draws the controls at their defaults (pulse 25 %,
lens 0.7, sweep 2.4 st, fog 0) and carries no text below the header.

    python3 screens/beacon/passes/02-subject/sketch.py

3D things are modelled in world units and projected through one camera per
frame (craft.md, Think in 3D). Device rules kept at sketch stage: one subpath
per path, <= 64 points, lines as filled closed ribbons, explicit paint on
every leaf, grey only, <= 4 fractional digits.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent

# defaults, as control positions 0..1 (definition.json)
D = {"pulse": 0.25, "lens": 0.7, "sweep": 0.2, "fog": 0.0}
HEADER_VALUES = ["25", "83", "2.4", "0"]
LABELS = ["pulse", "lens", "sweep", "fog"]

G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
HAIR, LINE, SUBJ = 1.0, 1.5, 2.0          # craft.md, Line weights
FONT = "UniversNextPro-Light"
BODY = (0.0, 22.0, 480.0, 219.0)          # artwork stays clear of the header (y 0-20)
HATCH = 4.0                               # hatch pitch, px at 1:1 (>= 3)


def f(v: float) -> str:
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def lerp(a, b, t):
    return a + (b - a) * t


# ---------------------------------------------------------------- clipping
def clip_poly(pts, box=BODY):
    """Sutherland-Hodgman against an axis-aligned box."""
    x0, y0, x1, y1 = box

    def cut(pts, inside, inter):
        out = []
        for i, p in enumerate(pts):
            q = pts[i - 1]
            if inside(p):
                if not inside(q):
                    out.append(inter(q, p))
                out.append(p)
            elif inside(q):
                out.append(inter(q, p))
        return out

    def ix(xc):
        return lambda a, b: (xc, a[1] + (b[1] - a[1]) * (xc - a[0]) / (b[0] - a[0]))

    def iy(yc):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (yc - a[1]) / (b[1] - a[1]), yc)

    for inside, inter in ((lambda p: p[0] >= x0, ix(x0)), (lambda p: p[0] <= x1, ix(x1)),
                          (lambda p: p[1] >= y0, iy(y0)), (lambda p: p[1] <= y1, iy(y1))):
        if not pts:
            return []
        pts = cut(pts, inside, inter)
    return pts


def clip_line(pts, box=BODY):
    """Split a polyline into the runs that lie inside the box."""
    x0, y0, x1, y1 = box
    runs, cur = [], []

    def seg(a, b):
        t0, t1 = 0.0, 1.0
        dx, dy = b[0] - a[0], b[1] - a[1]
        for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
            if p == 0:
                if q < 0:
                    return None
            else:
                t = q / p
                if p < 0:
                    t0 = max(t0, t)
                else:
                    t1 = min(t1, t)
        if t0 > t1:
            return None
        return (a[0] + dx * t0, a[1] + dy * t0), (a[0] + dx * t1, a[1] + dy * t1), t0 > 0, t1 < 1

    for a, b in zip(pts, pts[1:]):
        r = seg(a, b)
        if r is None:
            if cur:
                runs.append(cur)
                cur = []
            continue
        pa, pb, cut_a, cut_b = r
        if not cur or cut_a:
            if cur:
                runs.append(cur)
            cur = [pa]
        cur.append(pb)
        if cut_b:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return [r for r in runs if len(r) >= 2]


def poly_line_hits(poly, a, d):
    """Parameters t where the line a + t d crosses the polygon's edges."""
    ts = []
    for i in range(len(poly)):
        p, q = poly[i - 1], poly[i]
        ex, ey = q[0] - p[0], q[1] - p[1]
        den = d[0] * ey - d[1] * ex
        if abs(den) < 1e-12:
            continue
        wx, wy = p[0] - a[0], p[1] - a[1]
        t = (wx * ey - wy * ex) / den
        u = (wx * d[1] - wy * d[0]) / den
        if 0 <= u < 1:
            ts.append(t)
    return sorted(ts)


# ---------------------------------------------------------------- frame
class Frame:
    def __init__(self, title: str):
        self.title = title
        self.items: list[str] = []

    def add(self, s: str) -> None:
        self.items.append(s)

    def poly(self, pts, fill, stroke="none", sw=0.0, clip=True):
        if clip:
            pts = clip_poly(list(pts))
        pts = dedupe(pts)
        if len(pts) < 3:
            return
        assert len(pts) <= 64, len(pts)
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
        sws = f' stroke-width="{f(sw)}"' if stroke != "none" else ""
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def body(self, pts, edge, sw, fill=G0):
        """A solid body: black fill that hides what's behind, outlined."""
        self.poly(pts, fill, edge, sw)

    def ribbon(self, pts, w, colour, min_len=0.0):
        """A line of width w as filled closed ribbons, clipped to the body."""
        for run in clip_line(list(pts)):
            run = dedupe(run, closed=False)
            if len(run) < 2:
                continue
            if sum(math.dist(a, b) for a, b in zip(run, run[1:])) < max(min_len, 0.6):
                continue
            i, n = 0, 28
            while i < len(run) - 1:
                self._piece(run[i:i + n + 1], w, colour)
                i += n

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
        self.poly(left + right[::-1], colour, clip=False)

    def line(self, a, b, w, colour):
        self.ribbon([a, b], w, colour)

    def circle(self, cx, cy, r, fill, stroke="none", sw=0.0):
        sws = f' stroke-width="{f(sw)}"' if stroke != "none" else ""
        self.add(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def hatch(self, poly, colour=G3, pitch=HATCH, slope=1, w=HAIR):
        """45-degree hairlines clipped to a polygon (craft.md, semi-opaque areas)."""
        poly = clip_poly(list(poly))
        if len(poly) < 3:
            return
        d = (1.0, -1.0) if slope > 0 else (1.0, 1.0)
        # family of parallel lines: x + y = c (slope +1 on screen means rising right)
        key = (lambda p: p[0] + p[1]) if slope > 0 else (lambda p: p[0] - p[1])
        cs = [key(p) for p in poly]
        step = pitch * math.sqrt(2)
        c = math.floor(min(cs) / step) * step + step
        while c < max(cs):
            a = (c, 0.0) if slope > 0 else (c, 0.0)
            ts = poly_line_hits(poly, a, d)
            for t0, t1 in zip(ts[0::2], ts[1::2]):
                p0 = (a[0] + d[0] * t0, a[1] + d[1] * t0)
                p1 = (a[0] + d[0] * t1, a[1] + d[1] * t1)
                if math.dist(p0, p1) >= 4.0:
                    self.ribbon([p0, p1], w, colour)
            c += step

    def svg(self) -> str:
        head = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
            f"  <title>beacon · subject pass 02 · {self.title}</title>",
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
        for i, val in enumerate(HEADER_VALUES):
            c = "#CBCBCB" if i < 2 else "#000000"
            head.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{c}" stroke="none" '
                        f'font-family="{FONT}" font-size="20px">{val}</text>')
        head.append("  </g>")
        return "\n".join(head + ["  " + s for s in self.items] + ["</svg>", ""])


def dedupe(pts, closed=True):
    out = []
    for p in pts:
        p = (round(p[0], 3), round(p[1], 3))
        if not out or math.dist(out[-1], p) >= 0.25:
            out.append(p)
    if closed and len(out) > 2 and math.dist(out[0], out[-1]) < 0.3:
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


def vesica(cx, cy, w, h, n=10):
    """A flame / lamp image: a pointed lens shape, w wide, h tall."""
    right = [(cx + w / 2 * math.sin(math.pi * k / n), cy - h / 2 + h * k / n) for k in range(n + 1)]
    left = [(cx - w / 2 * math.sin(math.pi * k / n), cy - h / 2 + h * k / n) for k in range(n - 1, 0, -1)]
    return right + left


# ---------------------------------------------------------------- camera
def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def crs(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def unit(a):
    n = math.sqrt(dot(a, a))
    return (a[0] / n, a[1] / n, a[2] / n)


class Cam:
    """One pinhole camera: world z is up; f in px; target lands on (cx, cy)."""

    def __init__(self, eye, target, f, cx, cy):
        self.eye, self.f, self.cx, self.cy = eye, f, cx, cy
        self.fw = unit(sub(target, eye))
        self.rt = unit(crs(self.fw, (0, 0, 1)))
        self.up = crs(self.rt, self.fw)

    def depth(self, p):
        return dot(sub(p, self.eye), self.fw)

    def P(self, p):
        d = sub(p, self.eye)
        z = max(dot(d, self.fw), 1e-3)
        return (self.cx + self.f * dot(d, self.rt) / z, self.cy - self.f * dot(d, self.up) / z)

    def faces(self, p, n):
        return dot(sub(self.eye, p), n) > 0


def ring_pts(r, z, n=48, a0=0.0, a1=2 * math.pi, ox=0.0, oy=0.0):
    return [(ox + r * math.cos(a0 + (a1 - a0) * k / n), oy + r * math.sin(a0 + (a1 - a0) * k / n), z)
            for k in range(n + 1)]


def front_runs(cam, r, z, n=72, ox=0.0, oy=0.0, slope=0.0):
    """The visible runs of a horizontal ring on a surface of revolution (hidden-line).
    slope: outward normal's z component for a cone (positive leans the face upward)."""
    runs, cur = [], []
    for k in range(n + 1):
        a = 2 * math.pi * k / n
        p = (ox + r * math.cos(a), oy + r * math.sin(a), z)
        nrm = (math.cos(a), math.sin(a), slope)
        if cam.faces(p, nrm):
            cur.append(cam.P(p))
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    # stitch a run that wraps through angle 0
    if len(runs) > 1 and cam.faces((ox + r, oy, z), (1, 0, slope)):
        runs[0] = runs[-1] + runs[0][1:]
        runs.pop()
    return runs


def revolve_outline(cam, profile, ox=0.0, oy=0.0, n=96):
    """Left and right silhouettes of a surface of revolution, from its (z, r) profile."""
    left, right = [], []
    for z, r in profile:
        pts = [cam.P((ox + r * math.cos(2 * math.pi * k / n), oy + r * math.sin(2 * math.pi * k / n), z))
               for k in range(n)]
        left.append(min(pts))
        right.append(max(pts))
    return left, right


def cylinder(F, cam, r, z0, z1, edge, sw, top=True, top_colour=None, top_w=None, ox=0.0, oy=0.0):
    """Hidden-line cylinder: black body (hull of both rims), outline, visible top rim."""
    pts = [cam.P(p) for p in ring_pts(r, z0, 30, ox=ox, oy=oy)[:-1] + ring_pts(r, z1, 30, ox=ox, oy=oy)[:-1]]
    F.body(hull(pts), edge, sw)
    if top:
        rim = [cam.P(p) for p in ring_pts(r, z1, 48, ox=ox, oy=oy)[:-1]]
        F.poly(rim, G0, top_colour or edge, top_w or HAIR)


# ================================================================ v1
def v1() -> Frame:
    """The lens drum at large scale, its dome and pedestal past the frame's edges. Edge-lit silhouette."""
    F = Frame("v1 · the lens drum, close · edge-lit silhouette")
    Dd = 7.0
    cam = Cam((0, -Dd, 0.0), (0, 0, 0.0), 128 * Dd, 240, 122)
    belt = 0.2
    zmax = 0.95
    n = round(3 + 8 * D["lens"])             # lens: prism rings per zone
    dz = (zmax - belt) / n
    tooth = 0.075

    def rbase(z):
        a = abs(z)
        return 1.0 if a <= belt else 1.0 - 0.34 * (a - belt)

    # profile with saw-tooth prisms (catadioptric rings) above and below the belt
    prof_up, apex_up = [(0.0, 1.0), (belt, 1.0)], []
    for k in range(n):
        z0 = belt + k * dz
        za = z0 + 0.72 * dz
        prof_up += [(za, rbase(za) + tooth), (z0 + dz, rbase(z0 + dz))]
        apex_up.append((za, rbase(za) + tooth))
    prof = [(-z, r) for z, r in reversed(prof_up[1:])] + prof_up
    apexes = apex_up + [(-z, r) for z, r in apex_up]

    th_c = math.radians(-90 + 80 * D["sweep"])  # sweep: the lit panel turns off the axis
    half = math.radians(22.5)

    # silhouette, edge-lit: the side the lit panel has turned toward catches more light
    left, right = revolve_outline(cam, prof)
    F.ribbon(left, LINE, G4)
    F.ribbon(right, LINE, G5)

    # prism rings, edge-lit from the lamp inside: each prism's edge catches light only
    # near the lit panel (bright), fading to a hairline across the next panels, and as
    # a short rim where the drum turns away at either silhouette; the rest stays black.
    reach = math.radians(48)

    def arc3(r, z, a0, a1, n=24):
        return [(r * math.cos(lerp(a0, a1, k / n)), r * math.sin(lerp(a0, a1, k / n)), z) for k in range(n + 1)]

    def visible(pts3):
        return [cam.P(p) for p in pts3 if cam.faces(p, (p[0], p[1], 0))]

    for z, r in apexes:
        F.ribbon(visible(arc3(r, z, th_c - reach, th_c - half)), HAIR, G3)
        F.ribbon(visible(arc3(r, z, th_c + half, th_c + reach)), HAIR, G3)
        for a_edge in (math.radians(-180), math.radians(0)):
            s = 1 if a_edge == 0 else -1
            F.ribbon(visible(arc3(r, z, a_edge + s * math.radians(-14), a_edge + s * math.radians(4), 8)), HAIR, G4)
        F.ribbon([cam.P(p) for p in arc3(r, z, th_c - half, th_c + half, 16)], LINE, G5)

    # panel bars: eight brass frames round the drum, turning with the lens
    for i in range(8):
        a = th_c + half + 2 * half * i
        p_mid = (math.cos(a), math.sin(a), 0)
        if not cam.faces(p_mid, (math.cos(a), math.sin(a), 0)):
            continue
        if abs(math.cos(a)) > 0.93:
            continue
        pts = [cam.P(((rbase(z) + tooth * 0.5) * math.cos(a), (rbase(z) + tooth * 0.5) * math.sin(a), z))
               for z in [lerp(-zmax, zmax, k / 40) for k in range(41)]]
        F.ribbon(pts, HAIR, G3)

    # the belt: the refracting band where the lamp's image sits
    for zb, w, c in ((belt, LINE, G4), (-belt, LINE, G4), (0.1, HAIR, G2), (-0.1, HAIR, G2)):
        for run in front_runs(cam, 1.0, zb):
            F.ribbon(run, w, c)

    # the lamp seen through the lit panel: the one bright mass. pulse: its width
    lx, ly = cam.P((math.cos(th_c), math.sin(th_c), 0))
    w = 3 + 15 * D["pulse"]
    F.poly(vesica(lx, ly, w * abs(math.sin(th_c)) + 1.5, 40), G7)

    # fog: hatched from the bottom edge up (none at the default)
    if D["fog"] > 0:
        yt = 219 - 170 * D["fog"]
        F.hatch([(0, yt), (480, yt - 8), (480, 219), (0, 219)], G3, slope=-1)
    return F


# ================================================================ v2
def v2() -> Frame:
    """The lighthouse itself, standing on its stepped base: detailed line art from one camera."""
    F = Frame("v2 · the lighthouse · detailed line art")
    eye = (0.0, -17.0, 0.4)
    cam = Cam(eye, (0, 0, 2.7), 420, 128, 118)

    H = 4.6                                   # tower height
    r0, r1 = 1.15, 0.78                       # base and top radius

    def rt(z):
        return lerp(r0, r1, z / H)
    slope = (r0 - r1) / H

    # horizon, at eye height, behind everything
    yh = cam.P((40, 400, eye[2]))[1]
    F.line((0, yh), (480, yh), HAIR, G2)

    # the beam: a cone of light leaving the lantern, hatched because it's see-through
    lamp = (0, 0, H + 0.55)
    psi = math.radians(55 * D["sweep"])       # sweep: the beam turns toward the viewer
    halfa = math.radians(2 + 16 * (1 - D["lens"]))  # lens: the beam narrows
    edges = []
    for s in (-1, 1):
        a = psi + s * halfa
        d = (math.cos(a), -math.sin(a), 0.0)
        Lmax = 60.0
        if d[1] < 0:
            Lmax = min(Lmax, (abs(eye[1]) - 3.0) / -d[1])
        edges.append((cam.P((lamp[0] + 0.7 * d[0], lamp[1] + 0.7 * d[1], lamp[2])),
                      cam.P((lamp[0] + Lmax * d[0], lamp[1] + Lmax * d[1], lamp[2]))))
    beam = [edges[0][0], edges[0][1], edges[1][1], edges[1][0]]
    F.hatch(beam, G3)
    for a, b in edges:
        F.line(a, b, HAIR, G4)

    # stepped masonry base
    cylinder(F, cam, 1.75, -0.9, -0.4, G4, LINE, top_colour=G4, top_w=HAIR)
    cylinder(F, cam, 1.4, -0.4, 0.0, G4, LINE, top_colour=G4, top_w=HAIR)

    # tower: tapered, solid, outlined at subject weight
    prof = [(lerp(0, H, k / 4), rt(lerp(0, H, k / 4))) for k in range(5)]
    left, right = revolve_outline(cam, prof)
    bot = [cam.P(p) for p in ring_pts(r0, 0, 30, math.pi, 2 * math.pi)]
    F.body(left[::-1] + bot[1:-1] + right, G5, SUBJ)
    # courses of stone
    for k in range(1, 12):
        z = k * 0.38
        for run in front_runs(cam, rt(z), z, slope=slope):
            F.ribbon(run, HAIR, G3)
    # door with an arched head, and staggered windows
    def on_tower(a, z):
        r = rt(z) + 0.01
        return cam.P((r * math.cos(a), r * math.sin(a), z))
    a0 = math.radians(-90)
    door = [on_tower(a0 - 0.13, 0.02)] + [on_tower(a0 + 0.13 * math.cos(math.pi * k / 8), 0.62 + 0.18 * math.sin(math.pi * k / 8)) for k in range(9)][::-1]
    door = [on_tower(a0 - 0.13, 0.02), on_tower(a0 - 0.13, 0.62)] + \
           [on_tower(a0 - 0.13 * math.cos(math.pi * k / 8), 0.62 + 0.18 * math.sin(math.pi * k / 8)) for k in range(1, 8)] + \
           [on_tower(a0 + 0.13, 0.62), on_tower(a0 + 0.13, 0.02)]
    F.body(door, G4, LINE)
    for a, z in ((-70, 1.55), (-108, 2.65), (-80, 3.7)):
        a = math.radians(a)
        w = [on_tower(a - 0.09, z - 0.22), on_tower(a - 0.09, z + 0.22),
             on_tower(a + 0.09, z + 0.22), on_tower(a + 0.09, z - 0.22)]
        F.body(w, G4, HAIR)

    # corbels under the gallery
    for k in range(24):
        a = 2 * math.pi * k / 24
        p = (math.cos(a), math.sin(a), 0)
        if not cam.faces((rt(H) * p[0], rt(H) * p[1], H), (p[0], p[1], 0)):
            continue
        F.line(cam.P((rt(H - 0.35) * p[0], rt(H - 0.35) * p[1], H - 0.35)),
               cam.P((1.08 * p[0], 1.08 * p[1], H)), HAIR, G3)

    # gallery: back rail behind the lantern, deck, lantern, front rail
    rail_r, z_deck, z_rail = 1.1, H + 0.1, H + 0.45
    back = [cam.P(p) for p in ring_pts(rail_r, z_rail, 40, 0, math.pi)]
    F.ribbon(back, HAIR, G3)
    cylinder(F, cam, 1.12, H, z_deck, G4, LINE, top_colour=G4, top_w=HAIR)

    lr, lz0, lz1 = 0.62, z_deck, z_deck + 0.85
    cylinder(F, cam, lr, lz0, lz1, G4, LINE, top=False)
    # the lamp inside: the one bright mass. pulse: its width
    lx, ly = cam.P((0, 0, lamp[2]))
    F.poly(vesica(lx, ly, 3 + 10 * D["pulse"], 15), G7)
    # glazing bars over the lamp (helical astragals, as on a real lantern)
    for k in range(12):
        a0 = 2 * math.pi * k / 12
        pts3 = [(lr * math.cos(a0 + 0.5 * t), lr * math.sin(a0 + 0.5 * t), lerp(lz0, lz1, t))
                for t in [j / 10 for j in range(11)]]
        vis = [cam.P(p) for p in pts3 if cam.faces(p, (p[0], p[1], 0))]
        if len(vis) >= 2:
            F.ribbon(vis, HAIR, G4)
    for run in front_runs(cam, lr, lerp(lz0, lz1, 0.5)):
        F.ribbon(run, HAIR, G3)
    # dome, ventilator ball, rod
    dome = [(lz1 + 0.5 * math.sin(math.pi / 2 * k / 10), 0.7 * math.cos(math.pi / 2 * k / 10)) for k in range(11)]
    dl, dr = revolve_outline(cam, dome)
    eave = [cam.P(p) for p in ring_pts(0.7, lz1, 40, math.pi, 2 * math.pi)]
    F.body(dl[::-1] + eave[1:-1] + dr, G4, LINE)
    for k in (-1, 1):
        a = math.radians(-90 + 40 * k)
        F.ribbon([cam.P((r * math.cos(a), r * math.sin(a), z)) for z, r in dome[:9]], HAIR, G3)
    bx, by = cam.P((0, 0, lz1 + 0.62))
    F.circle(bx, by, 3.2, G0, G4, LINE)
    F.line(cam.P((0, 0, lz1 + 0.75)), cam.P((0, 0, lz1 + 1.1)), HAIR, G4)
    # front rail and its posts, over the lantern's foot
    front = [cam.P(p) for p in ring_pts(rail_r, z_rail, 40, math.pi, 2 * math.pi)]
    F.ribbon(front, LINE, G4)
    for k in range(16):
        a = math.pi + math.pi * (k + 0.5) / 16
        F.line(cam.P((rail_r * math.cos(a), rail_r * math.sin(a), z_deck)),
               cam.P((rail_r * math.cos(a), rail_r * math.sin(a), z_rail)), HAIR, G3)

    # fog: a hatched bank rising off the sea (none at the default)
    if D["fog"] > 0:
        yt = yh - 120 * D["fog"]
        F.hatch([(0, yt), (480, yt), (480, 219), (0, 219)], G3, slope=-1)
    return F


# ================================================================ v3
def v3() -> Frame:
    """The turning gear: four-panel lens on its mercury float, driven by a weight clock. Hidden-line 3D."""
    F = Frame("v3 · the clockwork and the turning lens · hidden-line 3D")
    eye = (-7.0, -11.0, 6.2)
    cam = Cam(eye, (0.75, 0, 1.75), 610, 218, 122)
    alpha = math.radians(18 + 72 * D["sweep"])  # sweep: how far the carriage has turned

    # --- the clock, behind and to the right
    bx0, bx1, by0, by1, bz0, bz1 = 1.75, 2.85, -0.45, 0.35, 0.1, 1.2
    V = lambda x, y, z: cam.P((x, y, z))
    front = [V(bx0, by0, bz0), V(bx1, by0, bz0), V(bx1, by0, bz1), V(bx0, by0, bz1)]
    top = [V(bx0, by0, bz1), V(bx1, by0, bz1), V(bx1, by1, bz1), V(bx0, by1, bz1)]
    F.body(top, G4, LINE)
    F.body(front, G4, LINE)
    # the weight cable drops through the floor, past the frame's edge
    cx_, cy_ = 2.55, -0.05
    F.line(V(cx_, cy_, bz0), V(cx_, cy_, -3.0), HAIR, G4)
    # wheels on the front plate: great wheel turns with the carriage (sweep), pinion, fly
    def plate(u, v):
        return V(u, by0, v)
    def wheel(u, v, r, spokes, phase, w, c):
        rim = [plate(u + r * math.cos(2 * math.pi * k / 28), v + r * math.sin(2 * math.pi * k / 28)) for k in range(28)]
        F.poly(rim, G0, c, w)
        for s in range(spokes):
            a = phase + 2 * math.pi * s / spokes
            F.line(plate(u + 0.05 * math.cos(a), v + 0.05 * math.sin(a)),
                   plate(u + r * math.cos(a), v + r * math.sin(a)), HAIR, c)
    wheel(2.12, 0.62, 0.36, 4, alpha * 3, LINE, G4)
    wheel(2.6, 0.92, 0.13, 3, -alpha * 9, HAIR, G4)
    # the fly (air brake) on top: shaft and two vanes
    fx, fy = 2.6, -0.05
    F.line(V(fx, fy, bz1), V(fx, fy, bz1 + 0.5), HAIR, G4)
    for s in (-1, 1):
        F.body([V(fx, fy, bz1 + 0.25), V(fx + 0.28 * s, fy, bz1 + 0.25), V(fx + 0.28 * s, fy, bz1 + 0.47),
                V(fx, fy, bz1 + 0.47)], G4, HAIR)
    # drive shaft to the carriage
    F.ribbon([V(bx0, -0.05, 1.0), V(1.15, -0.05, 1.0)], LINE, G4)

    # --- pedestal, mercury trough, float
    cylinder(F, cam, 0.75, 0.0, 0.14, G4, LINE, top_colour=G3)
    cylinder(F, cam, 0.42, 0.14, 1.1, G4, LINE, top=False)
    cylinder(F, cam, 1.18, 1.1, 1.42, G4, LINE, top_colour=G4, top_w=HAIR)
    # rack teeth round the trough's foot: they travel as the carriage turns
    for k in range(60):
        a = 2 * math.pi * k / 60 + alpha
        p = (1.18 * math.cos(a), 1.18 * math.sin(a), 1.1)
        if cam.faces(p, (math.cos(a), math.sin(a), 0)):
            F.line(V(p[0], p[1], 1.12), V(p[0], p[1], 1.22), HAIR, G3)
    cylinder(F, cam, 1.04, 1.42, 1.52, G4, LINE, top_colour=G3)

    # --- the four-panel lens, turned by alpha
    hw, z0, z1 = 0.82, 1.52, 3.3
    zc = (z0 + z1) / 2
    n_rings = round(2 + 6 * D["lens"])        # lens: prism rings per panel
    faces = []
    for i in range(4):
        a = alpha + math.pi / 2 * i
        nrm = (math.cos(a), math.sin(a), 0)
        tan = (-math.sin(a), math.cos(a), 0)
        c = (hw * nrm[0], hw * nrm[1], zc)
        if cam.faces(c, nrm):
            faces.append((cam.depth(c), c, nrm, tan))
    faces.sort(key=lambda t: -t[0])
    frontmost = min(faces, key=lambda t: dot(t[2], unit(sub(cam.eye, t[1]))) * -1)
    hz = (z1 - z0) / 2
    for _, c, nrm, tan in faces:
        def at(u, v):
            return cam.P((c[0] + u * tan[0], c[1] + u * tan[1], c[2] + v))
        F.body([at(-hw, -hz), at(hw, -hz), at(hw, hz), at(-hw, hz)], G5, SUBJ)
        # a flashing panel: a refracting belt of bullseye rings, cut off top and bottom
        # by the reflecting prisms above and below it (straight bars)
        vb = 0.42
        for s in (-1, 1):
            F.ribbon([at(-hw, s * vb), at(hw, s * vb)], HAIR, G4)
            n_pr = round(1 + 3 * D["lens"])
            for k in range(1, n_pr + 1):
                v = s * lerp(vb, hz, k / (n_pr + 1))
                F.ribbon([at(-hw + 0.06, v), at(hw - 0.06, v)], HAIR, G3)
        for k in range(1, n_rings + 1):
            r = lerp(0.12, 1.1, k / n_rings)
            run = []
            for j in range(97):
                t = 2 * math.pi * j / 96
                u, v = r * math.cos(t), r * math.sin(t) * 1.0
                if abs(u) < hw - 0.05 and abs(v) < vb - 0.04:
                    run.append(at(u, v))
                elif run:
                    F.ribbon(run, HAIR, G3)
                    run = []
            if run:
                F.ribbon(run, HAIR, G3)
        if c is frontmost[1]:
            # the flash: the lamp seen through the bullseye facing us. pulse: its size
            px, py = at(0, 0)
            F.poly(vesica(px, py, 2.5 + 8 * D["pulse"], 12), G7)
        else:
            px, py = at(0, 0)
            F.poly(vesica(px, py, 2.5, 8), G0, G4, HAIR)
        if D["fog"] > 0:  # fog: mist creeping up the glass, hatched
            zf = -hz + 2 * hz * D["fog"]
            F.hatch([at(-hw, -hz), at(hw, -hz), at(hw, zf), at(-hw, zf)], G3, slope=-1)
    # lid and the lamp's chimney through it
    lid = [cam.P((hw * math.cos(alpha + math.pi / 4 + math.pi / 2 * i) * math.sqrt(2),
                  hw * math.sin(alpha + math.pi / 4 + math.pi / 2 * i) * math.sqrt(2), z1)) for i in range(4)]
    F.body(lid, G5, LINE)
    cylinder(F, cam, 0.12, z1, z1 + 0.62, G4, LINE, top_colour=G4, top_w=HAIR)
    return F


# ================================================================ v4
def v4() -> Frame:
    """The sea close up, in bold closed outlines, the light on the horizon. Camera at the waterline."""
    F = Frame("v4 · the sea it lights · bold closed outlines")
    h, f, y0, cx = 1.4, 300.0, 76.0, 240.0      # eye height, focal, horizon, centre

    def P(X, Dp, Z):
        return (cx + f * X / Dp, y0 + f * (h - Z) / Dp)

    LX, LD = 5.5, 30.0                          # the lighthouse, out on its rock
    # horizon
    F.line((0, y0), (480, y0), HAIR, G3)

    # the beam, a closed outline, hatched
    O = (LX, LD, 3.1)
    psi = math.radians(14 + 50 * D["sweep"])    # sweep: the beam swings toward you
    halfa = math.radians(2 + 14 * (1 - D["lens"]))  # lens: the beam tightens
    # a cone: modelled as its upper and lower generators along the beam's bearing, so it
    # opens vertically as it comes toward you (the horizontal spread folds into the same band)
    d = (-math.cos(psi), -math.sin(psi))
    L = (LD - 2.6) / -d[1]
    edge = []
    for s in (1, -1):
        st = P(O[0] + 0.35 * d[0], O[1] + 0.35 * d[1], O[2] + s * 0.05)
        far = P(O[0] + L * d[0], O[1] + L * d[1], O[2] + s * L * math.tan(halfa) * 0.5)
        edge.append([st, far])
    beam = [edge[0][0], edge[0][1], edge[1][1], edge[1][0]]
    F.hatch(beam, G3)
    F.poly(beam, "none", G4, LINE)

    # the rock and the tower
    rock = [P(LX + 2.4 * math.cos(math.pi * k / 10), LD, 0.75 * math.sin(math.pi * k / 10) ** 0.6) for k in range(11)]
    F.body(rock, G4, LINE)
    tw = [P(LX - 0.42, LD, 0.4), P(LX - 0.28, LD, 2.7), P(LX + 0.28, LD, 2.7), P(LX + 0.42, LD, 0.4)]
    F.body(tw, G5, LINE)
    lan = [P(LX - 0.36, LD, 2.7), P(LX - 0.36, LD, 3.45), P(LX, LD, 3.75), P(LX + 0.36, LD, 3.45), P(LX + 0.36, LD, 2.7)]
    F.body(lan, G5, LINE)
    lx, ly = P(LX, LD, 3.1)
    F.circle(lx, ly, 2.4, G7)                  # the light: the one brightest point

    # swell, far to near: each crest a closed shape that hides what's behind
    rng = random.Random(7)
    rows = [3.4 * 1.3 ** k for k in range(6, -1, -1)]     # far to near, evenly spaced in log depth
    reach = lerp(LD, 3.0, 0.35 + 0.65 * D["lens"])  # lens: how far toward you the glitter reaches
    col_X = lambda Dp: (lx - cx) * Dp / f          # world X under the light at depth Dp

    def crest(s, k):
        # a wave's back rises slowly, its face falls steeply past a sharp crest at s = k
        return (s / k) ** 1.6 if s <= k else (1 - (s - k) / (1 - k)) ** 0.8
    for ri, Dp in enumerate(rows):
        W = 1.5
        off = rng.random() * W
        sw = SUBJ if Dp < 5.5 else LINE if Dp < 10 else HAIR
        hgt = 0.26
        X = -Dp * cx / f - off - W
        while P(X, Dp, 0)[0] < 480:
            w = W * (0.75 + 0.5 * rng.random())
            k = rng.uniform(0.55, 0.68)
            top, bot = [], []
            for j in range(17):
                s = j / 16
                top.append(P(X + w * s, Dp, hgt * crest(s, k)))
                bot.append(P(X + w * s, Dp, -0.05 * math.sin(math.pi * s)))
            shape = top + bot[-2:0:-1]
            F.body(shape, G4, sw)
            # glitter: crests under the light catch it, as far as the lens throws it
            xc = col_X(Dp)
            if Dp >= reach and X < xc < X + w:
                gl = (0.4 + 2.0 * D["pulse"]) / 2   # pulse: how long each glint is
                seg = []
                for j in range(41):
                    s = j / 40
                    xx = X + w * s
                    if abs(xx - xc) <= gl:
                        seg.append(P(xx, Dp, hgt * crest(s, k)))
                if len(seg) >= 2:
                    F.ribbon(seg, sw + 0.5, G6)
            X += w * (0.8 + 0.35 * rng.random())
    # glints on the far water, between the rock and the first row
    for Dp in (24.0, 20.0):
        if Dp >= reach:
            a, b = P(col_X(Dp) - 0.4 - 1.2 * D["pulse"], Dp, 0), P(col_X(Dp) + 0.4 + 1.2 * D["pulse"], Dp, 0)
            F.line(a, b, HAIR, G6)

    if D["fog"] > 0:  # fog: a hatched bank that rises over the horizon and the light
        yt = y0 + 10 - 70 * D["fog"]
        F.hatch([(0, yt), (480, yt), (480, y0 + 14), (0, y0 + 14)], G3, slope=-1)
    return F


# ================================================================ v5
def v5() -> Frame:
    """A headland at night, the lighthouse cut open: stair, weight shaft, lens and lamp, and the beam over the sea."""
    F = Frame("v5 · the headland, the tower cut open · cutaway section")
    tx = 104.0                                 # tower axis
    yb, yg = 154.0, 70.0                       # tower base, gallery
    sea = 190.0

    def ro(y):  # outer half-width
        return lerp(30, 19, (yb - y) / (yb - yg))

    # sea and swell first (behind the headland)
    F.line((150, sea), (480, sea), HAIR, G3)
    rng = random.Random(3)
    for yy, x0 in ((200, 220), (210, 168), (200, 360), (210, 300), (210, 420)):
        x = x0 + rng.uniform(-6, 6)
        F.ribbon([(x + k * 2.5, yy + 1.2 * math.sin(k * 0.9)) for k in range(12)], HAIR, G2)

    # the beam: it leaves the lantern over the sea; light pulses go out along it as hatched bands
    lamp = (tx, 59.0)
    half = math.radians(1.2 + 7 * (1 - D["lens"]))      # lens: the beam focuses
    L = 360 * math.cos(math.radians(72 * D["sweep"]))   # sweep: turning away shortens it (foreshortened)
    x_start = tx + 14
    def edge_y(x, s):
        return lamp[1] + s * (2.0 + (x - lamp[0]) * math.tan(half))
    x_end = min(x_start + L, 480)
    up = [(x, edge_y(x, -1)) for x in (x_start, x_end)]
    dn = [(x, edge_y(x, 1)) for x in (x_start, x_end)]
    F.line(up[0], up[1], HAIR, G4)
    F.line(dn[0], dn[1], HAIR, G4)
    period = 30.0
    band = 3 + 24 * D["pulse"]                          # pulse: each band's width, as a share of the period
    xb = x_start + 6
    while xb < x_end - 2:
        xe = min(xb + band, x_end)
        quad = [(xb, edge_y(xb, -1)), (xe, edge_y(xe, -1)), (xe, edge_y(xe, 1)), (xb, edge_y(xb, 1))]
        F.hatch(quad, G3)
        F.line(quad[0], quad[3], HAIR, G4)
        xb += period

    # the headland: rock in section, black, its skin a line
    land = [(0, 150), (48, 152), (tx - ro(yb) - 4, yb), (tx + ro(yb) + 6, yb), (150, 156), (166, 160),
            (178, 171), (186, 182), (194, sea), (200, 219), (0, 219)]
    F.poly(land, G0)
    F.ribbon(land[:-2], LINE, G4)

    # the weight shaft, sunk into the rock below the tower
    for s in (-1, 1):
        F.line((tx + 4 * s, yb), (tx + 4 * s, 206), HAIR, G3)
    F.poly([(tx - 2.5, 178), (tx + 2.5, 178), (tx + 2.5, 192), (tx - 2.5, 192)], G0, G4, HAIR)
    F.line((tx, yg + 2), (tx, 178), HAIR, G3)            # the cable, up to the clock

    # tower walls cut: outer at subject weight, inner a line, black between
    wall = 6.0
    for s in (-1, 1):
        outer = [(tx + s * ro(y), y) for y in (yb, yg)]
        inner = [(tx + s * (ro(y) - wall), y) for y in (yb, yg + 4)]
        F.body([outer[0], outer[1], (tx + s * (ro(yg) - wall), yg + 4), inner[0]], G5, LINE)
        F.ribbon(outer, SUBJ, G5)
    # floors and the spiral stair's cut treads, alternating sides
    for yf in (yb - 28, yb - 56):
        F.line((tx - ro(yf) + wall, yf), (tx - 6, yf), HAIR, G4)
        F.line((tx + 6, yf), (tx + ro(yf) - wall, yf), HAIR, G4)
    for k in range(13):
        y = yb - 5 - k * 6.2
        s = -1 if (k // 2) % 2 == 0 else 1
        xi = tx + s * (ro(y) - wall)
        F.line((xi, y), (xi - s * 9, y), HAIR, G3)
    # the clock at the lantern floor
    F.poly([(tx - 8, yg - 2), (tx + 8, yg - 2), (tx + 8, yg + 6), (tx - 8, yg + 6)], G0, G4, HAIR)

    # gallery deck and rail
    F.body([(tx - 30, yg), (tx + 30, yg), (tx + 30, yg + 3), (tx - 30, yg + 3)], G4, LINE)
    F.line((tx - 29, yg - 9), (tx + 29, yg - 9), HAIR, G4)
    for k in range(7):
        x = tx - 29 + k * 58 / 6
        F.line((x, yg - 9), (x, yg), HAIR, G3)

    # lantern: glazing cut, lens in section (stepped prisms each side), lamp
    lw, lt = 15.0, 46.0
    for s in (-1, 1):
        F.line((tx + s * lw, yg), (tx + s * lw, lt), LINE, G4)
        prof = []
        for k in range(6):
            y = yg - 2 - k * 4
            prof += [(tx + s * 7.5, y), (tx + s * 10, y - 2)]
        F.ribbon(prof, HAIR, G4)
    F.poly(vesica(lamp[0], lamp[1], 4.5, 11), G7)
    # dome and ventilator
    dome = [(tx + 17 * math.cos(math.pi * k / 16), lt - 13 * math.sin(math.pi * k / 16)) for k in range(17)]
    F.ribbon(dome, LINE, G4)
    F.circle(tx, lt - 16.5, 2.6, G0, G4, LINE)

    if D["fog"] > 0:  # fog: a hatched bank rising from the sea
        yt = sea - 130 * D["fog"]
        F.hatch([(150, yt), (480, yt), (480, sea), (150, sea)], G3, slope=-1)
    return F


def main():
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        out = HERE / name / "rest.svg"
        out.parent.mkdir(exist_ok=True)
        out.write_text(fn().svg())
        print(out.relative_to(HERE))


if __name__ == "__main__":
    main()
