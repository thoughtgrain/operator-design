#!/usr/bin/env python3
"""Subject-pass 02 sketches for tide: five rest frames, one per direction.

    python3 screens/tide/passes/02-subject/sketch.py

Writes v1..v5/rest.svg (480 x 220, stock header kept as preview scaffolding).
Every frame shows the defaults: swell 2.0 s, depth 0.5 s, salt 0 %, drift 0 %, no notes.
Each variant models its scene in 3D (x right, y away from the viewer, z up) and
projects it through one camera. No text below the header; states are line,
position or hatching, never a lighter grey fill. These are subject sketches,
not device frames: parts are static artwork (no bound nodes yet).
"""
from __future__ import annotations

import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 480, 220
TOP = 21            # first body row: artwork stays below the stock header

G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
FONT = "UniversNextPro-Light"
HAIR, LINE, SUBJ = 1.1, 1.5, 2.2      # the three weights (craft.md)

# defaults (definition.json), as positions 0..1 and as the DSP's units
P_SWELL, P_DEPTH, SALT, DRIFT = 0.6, 0.5, 0.0, 0.0
SWELL_S = 0.25 * 32 ** P_SWELL        # 2.0 s between waves
DEPTH_S = 0.05 * 100 ** P_DEPTH       # 0.5 s ring time
HEADER = [("swell", "2.0s"), ("depth", "0.5s"), ("salt", "0"), ("drift", "0")]


def ratio(k: int, salt: float = SALT) -> float:
    """Partial k's ratio to the note (brief: r^(1 + 0.3 salt))."""
    return k ** (1 + 0.3 * salt)


# ================================================================ geometry
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def mul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    L = math.sqrt(dot(a, a))
    return (a[0] / L, a[1] / L, a[2] / L)


class Camera:
    """One pinhole camera: eye, look-at point, focal length in px, and where the look-at point lands."""

    def __init__(self, eye, target, f, at):
        self.eye = eye
        self.fw = norm(sub(target, eye))
        self.rt = norm(cross(self.fw, (0, 0, 1)))
        self.up = cross(self.rt, self.fw)
        self.f = f
        self.cx, self.cy = at

    def depth(self, p):
        return dot(sub(p, self.eye), self.fw)

    def p(self, P):
        d = sub(P, self.eye)
        z = dot(d, self.fw)
        return (self.cx + self.f * dot(d, self.rt) / z, self.cy - self.f * dot(d, self.up) / z)

    def ps(self, pts):
        return [self.p(q) for q in pts]

    def facing(self, normal, point):
        """True when a face with this outward normal faces the camera."""
        return dot(normal, sub(self.eye, point)) > 0


def circle3(c, r, n=48, a0=0.0, a1=2 * math.pi, z=None):
    out = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        out.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a), c[2] if z is None else z))
    return out


# ================================================================ 2D drawing
def f2(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def dedupe(pts, gap=0.3):
    out = []
    for p in pts:
        if not out or math.dist(out[-1], p) >= gap:
            out.append(p)
    return out


def clip_poly_rect(pts, x0=0, y0=TOP, x1=W, y1=H):
    """Sutherland-Hodgman: a filled polygon clipped to the body."""
    def clip(pts, inside, inter):
        out = []
        for i in range(len(pts)):
            a, b = pts[i - 1], pts[i]
            ia, ib = inside(a), inside(b)
            if ib:
                if not ia:
                    out.append(inter(a, b))
                out.append(b)
            elif ia:
                out.append(inter(a, b))
        return out

    def ix(xc):
        return lambda a, b: (xc, a[1] + (b[1] - a[1]) * (xc - a[0]) / (b[0] - a[0]))

    def iy(yc):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (yc - a[1]) / (b[1] - a[1]), yc)

    for inside, inter in ((lambda p: p[0] >= x0, ix(x0)), (lambda p: p[0] <= x1, ix(x1)),
                          (lambda p: p[1] >= y0, iy(y0)), (lambda p: p[1] <= y1, iy(y1))):
        if not pts:
            return []
        pts = clip(pts, inside, inter)
    return pts


def clip_line_rect(pts, x0=0.5, y0=TOP + 0.5, x1=W - 0.5, y1=H - 0.5):
    """An open polyline clipped to the body: a list of runs."""
    runs, cur = [], []

    def inside(p):
        return x0 <= p[0] <= x1 and y0 <= p[1] <= y1

    def seg_clip(a, b):
        t0, t1 = 0.0, 1.0
        dx, dy = b[0] - a[0], b[1] - a[1]
        for pp, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
            if pp == 0:
                if q < 0:
                    return None
                continue
            r = q / pp
            if pp < 0:
                t0 = max(t0, r)
            else:
                t1 = min(t1, r)
            if t0 > t1:
                return None
        return (a[0] + dx * t0, a[1] + dy * t0), (a[0] + dx * t1, a[1] + dy * t1)

    for a, b in zip(pts, pts[1:]):
        s = seg_clip(a, b)
        if s is None:
            if cur:
                runs.append(cur)
                cur = []
            continue
        p, q = s
        if not cur:
            cur = [p]
        elif math.dist(cur[-1], p) > 0.01:
            runs.append(cur)
            cur = [p]
        cur.append(q)
        if not inside(b):
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return [r for r in runs if len(r) >= 2]


def poly(pts, fill, stroke="none", sw=None):
    pts = dedupe(clip_poly_rect(dedupe(pts)))
    if len(pts) > 2 and math.dist(pts[0], pts[-1]) < 0.3:
        pts = pts[:-1]
    if len(pts) < 3:
        return ""
    out = []
    # the device takes <= 64 points per path; a long fill is split into fans of the same polygon
    if len(pts) > 62:
        step = max(1, math.ceil(len(pts) / 60))
        pts = pts[::step]
    d = "M " + " L ".join(f"{f2(x)} {f2(y)}" for x, y in pts) + " Z"
    s = f'<path d="{d}" fill="{fill}" stroke="{stroke}"'
    if stroke != "none":
        s += f' stroke-width="{sw}"'
    out.append(s + "/>")
    return "\n".join(out)


def line(pts, w, ink):
    """An open polyline drawn as thin closed ribbons (filled, no stroke), clipped to the body."""
    out = []
    for run in clip_line_rect(dedupe(pts)):
        run = dedupe(run)
        i = 0
        while i < len(run) - 1:
            chunk = run[i:i + 31]
            if len(chunk) >= 2 and sum(math.dist(a, b) for a, b in zip(chunk, chunk[1:])) > 1.5:
                out.append(_ribbon(chunk, w, ink))
            i += 30
    return "\n".join(o for o in out if o)


def loop(pts, w, ink):
    """A closed outline as a ribbon (start point repeated at the end)."""
    pts = dedupe(pts)
    if math.dist(pts[0], pts[-1]) > 0.3:
        pts = pts + [pts[0]]
    return line(pts, w, ink)


def _ribbon(pts, w, fill):
    h = w / 2
    n = len(pts)
    left, right = [], []
    for k in range(n):
        if k in (0, n - 1):
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
    pts2 = dedupe(left + right[::-1], 0.2)
    if len(pts2) < 3:
        return ""
    d = "M " + " L ".join(f"{f2(x)} {f2(y)}" for x, y in pts2) + " Z"
    return f'<path d="{d}" fill="{fill}" stroke="none"/>'


def clip_line_poly(p0, p1, polygon):
    """Segments of the line p0->p1 inside polygon (even-odd)."""
    (x0, y0), (x1, y1) = p0, p1
    ts = []
    n = len(polygon)
    for i in range(n):
        ax, ay = polygon[i]
        bx, by = polygon[(i + 1) % n]
        dx, dy = x1 - x0, y1 - y0
        ex, ey = bx - ax, by - ay
        den = dx * ey - dy * ex
        if abs(den) < 1e-9:
            continue
        t = ((ax - x0) * ey - (ay - y0) * ex) / den
        u = ((ax - x0) * dy - (ay - y0) * dx) / den
        if 0 <= t <= 1 and 0 <= u < 1:
            ts.append(t)
    ts.sort()
    return [((x0 + (x1 - x0) * a, y0 + (y1 - y0) * a), (x0 + (x1 - x0) * b, y0 + (y1 - y0) * b))
            for a, b in zip(ts[0::2], ts[1::2])]


def hatch(polygon, ink, gap=4.0, phase=0.0):
    """45-degree hairlines >= 3 px apart, clipped to the region (craft.md: semi-opaque / shaded areas)."""
    out = []
    step = gap * math.sqrt(2)
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    lo, hi = min(xs) + min(ys), max(xs) + max(ys)       # lines x + y = c
    c = math.floor((lo - phase) / step) * step + phase
    while c <= hi:
        p0, p1 = (c - min(ys) + 400, min(ys) - 400), (c - max(ys) - 400, max(ys) + 400)
        for a, b in clip_line_poly(p0, p1, polygon):
            if math.dist(a, b) > 3:
                out.append(line([a, b], HAIR, ink))
        c += step
    return out


def inside(pt, polygon):
    x, y = pt
    c = False
    n = len(polygon)
    for i in range(n):
        ax, ay = polygon[i]
        bx, by = polygon[(i + 1) % n]
        if (ay > y) != (by > y) and x < ax + (bx - ax) * (y - ay) / (by - ay):
            c = not c
    return c


def runs_where(pts, keep):
    """Split a polyline into runs of consecutive points for which keep(pt) holds."""
    runs, cur = [], []
    for p in pts:
        if keep(p):
            cur.append(p)
        else:
            if len(cur) >= 2:
                runs.append(cur)
            cur = []
    if len(cur) >= 2:
        runs.append(cur)
    return runs


def hull(pts):
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in pts))

    def half(seq):
        h = []
        for p in seq:
            while len(h) >= 2 and ((h[-1][0] - h[-2][0]) * (p[1] - h[-2][1]) - (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0])) <= 0:
                h.pop()
            h.append(p)
        return h
    lower, upper = half(pts), half(pts[::-1])
    return lower[:-1] + upper[:-1]


def frame(body: list[str]) -> str:
    steps = [G0, G1, G2, G3, G4, G5, G6, G7]
    hdr = [f'<rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>' for i, c in enumerate(steps)]
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


# ======================================================= v1 · exploded view
def v1():
    """One tuned hollow at large scale, exploded: the cup in the shelf (running off the frame),
    the body of water lifted out of it on its axis, the inlet stone drawn out along the line the
    swell comes in on, and the swell's tongue entering at the left edge."""
    cam = Camera(eye=(0.35, -5.0, 3.1), target=(-0.35, 0, 0.35), f=300, at=(262, 124))
    body = []
    D = 0.3 + 0.55 * P_DEPTH                     # depth: how deep the cup is
    notch = math.radians(16)

    # the shelf: its front drop runs off both edges of the frame
    for yy, zz, ink, w in ((-1.55, 0.0, G4, LINE), (-1.75, -0.32, G3, HAIR)):
        body.append(line(cam.ps([(x / 10, yy if zz == 0 else yy, zz) for x in range(-60, 61)]), w, ink))
    for x in (-3.9, -3.1, -2.2, 1.5, 2.6, 3.4):
        body.append(line(cam.ps([(x, -1.55, 0), (x + 0.06, -1.75, -0.32)]), HAIR, G2))
    # a few joints in the shelf, out from the lip
    for a, r0, r1 in ((math.radians(-40), 1.18, 1.5), (math.radians(30), 1.2, 2.3), (math.radians(140), 1.2, 2.0),
                      (math.radians(-140), 1.18, 1.5), (math.radians(75), 1.2, 2.6)):
        body.append(line(cam.ps([(r * math.cos(a + 0.12 * (r - r0)), r * math.sin(a + 0.12 * (r - r0)), 0)
                                 for r in (r0, (r0 + r1) / 2, r1)]), HAIR, G2))

    # the cup: lip (open at the inlet notch), a second edge for its thickness, far-wall meridians
    lip = circle3((0, 0, 0), 1.0, 80, math.pi + notch, 3 * math.pi - notch)
    outer = circle3((0, 0, 0), 1.12, 80, math.pi + notch * 0.9, 3 * math.pi - notch * 0.9)
    for th in [math.radians(a) for a in range(25, 160, 18)]:
        mer = []
        for i in range(0, 15):
            t = i / 18
            r = math.cos(t * math.pi / 2)
            mer.append((r * math.cos(th), r * math.sin(th), -D * math.sin(t * math.pi / 2)))
        body.append(line(cam.ps(mer), HAIR, G3))
    body.append(line(cam.ps(outer), HAIR, G3))
    body.append(line(cam.ps(lip), LINE, G5))
    # the notch's two cheeks
    for s in (-1, 1):
        a = math.pi + s * notch
        body.append(line(cam.ps([(1.0 * math.cos(a), 1.0 * math.sin(a), 0), (1.12 * math.cos(a), 1.12 * math.sin(a), 0)]),
                         LINE, G5))

    # assembly axis of the cup and the lens: hairline, in two runs (the lens hides the middle)
    LZ = 1.3                                    # how far the water is lifted out
    body.append(line(cam.ps([(0, 0, 0.12), (0, 0, LZ - 0.2)]), HAIR, G2))
    body.append(line(cam.ps([(0, 0, LZ + 0.05), (0, 0, LZ + 0.42)]), HAIR, G2))

    # the inlet stone, drawn out along the swell's line (wedge block, hidden-line)
    off = (-1.3, 0.0, 0.62)
    a0, a1 = math.pi - notch * 0.85, math.pi + notch * 0.85
    ring = []
    for (r, z) in ((0.98, 0.0), (1.16, 0.0), (1.16, -0.2), (0.98, -0.2)):
        ring.append([(r * math.cos(a), r * math.sin(a), z) for a in (a0, a1)])
    # corners: inner/outer x near/far x top/bottom
    def C(r_i, a_i, z_i):
        r = (0.98, 1.16)[r_i]
        a = (a0, a1)[a_i]
        z = (0.0, -0.2)[z_i]
        return add((r * math.cos(a), r * math.sin(a), z), off)
    faces = [  # (corner list, outward normal)
        ([C(0, 0, 0), C(1, 0, 0), C(1, 1, 0), C(0, 1, 0)], (0, 0, 1)),
        ([C(1, 0, 0), C(1, 0, 1), C(1, 1, 1), C(1, 1, 0)], (-1, 0, 0)),
        ([C(0, 0, 0), C(0, 0, 1), C(1, 0, 1), C(1, 0, 0)], (0, 1, 0)),
        ([C(0, 1, 0), C(1, 1, 0), C(1, 1, 1), C(0, 1, 1)], (0, -1, 0)),
        ([C(0, 0, 0), C(0, 1, 0), C(0, 1, 1), C(0, 0, 1)], (1, 0, 0)),
    ]
    vis = [fc for fc in faces if cam.facing(fc[1], fc[0][0])]
    vis.sort(key=lambda fc: -cam.depth(mul(add(fc[0][0], fc[0][2]), 0.5)))
    for pts, n in vis:
        sp = cam.ps(pts)
        body.append(poly(sp, G0))
        body.append(loop(sp, LINE, G4))
    top = cam.ps(faces[0][0])
    # a weathering line across the stone's top (inner structure, hairline)
    body.append(line([((top[0][0] + top[1][0]) / 2 * 0.6 + (top[3][0] + top[2][0]) / 2 * 0.4,
                        (top[0][1] + top[1][1]) / 2 * 0.6 + (top[3][1] + top[2][1]) / 2 * 0.4),
                       ((top[0][0] + top[3][0]) / 2, (top[0][1] + top[3][1]) / 2)], HAIR, G3))
    # its assembly line back into the notch
    home = (-1.07, 0, -0.1)
    body.append(line(cam.ps([add(home, (-0.05, 0, 0.12)), add(home, (off[0] * 0.62, 0, off[2] * 0.62))]), HAIR, G2))

    # the swell's tongue, entering from the left edge along the same line, crests across it
    tip_x = -3.0
    tongue = []
    for i in range(0, 25):
        a = math.pi / 2 - math.pi * i / 24
        tongue.append((tip_x - 0.35 + 0.35 * math.cos(a) * 1.0, 0.5 * math.sin(a), 0.35))
    tongue = [(-6.0, 0.62, 0.35)] + tongue + [(-6.0, -0.62, 0.35)]
    ts = cam.ps(tongue)
    body.append(poly(ts, G0))
    body.append(line(ts, LINE, G4))
    lam = 0.16 + 0.22 * SWELL_S / 2              # swell: crest spacing on the tongue
    x = tip_x - 0.42
    while x > -6:
        half = 0.5 if x < tip_x - 0.35 else 0.5
        body.append(line(cam.ps([(x, -half * 0.96, 0.35), (x - 0.06, 0, 0.35), (x, half * 0.96, 0.35)]), HAIR, G3))
        x -= lam

    # the water, lifted out on the axis: a lens with a side, standing crests on top, its rim brightest
    R = 0.8
    topc = circle3((0, 0, LZ), R, 72)
    bot_front = circle3((0, 0, LZ - 0.13), R, 36, math.pi, 2 * math.pi)
    sil = cam.ps(circle3((0, 0, LZ), R, 36, 0, math.pi)) + cam.ps(bot_front)
    body.append(poly(sil, G0))
    body.append(line(cam.ps(bot_front), LINE, G4))
    for s in (0, math.pi):
        body.append(line(cam.ps([(R * math.cos(s), 0, LZ), (R * math.cos(s), 0, LZ - 0.13)]), LINE, G4))
    # standing-wave crests across the surface: evenly spaced at salt 0, stretched with salt
    for k in range(-4, 5):
        if k == 0:
            continue
        u = abs(k) / 5
        x = math.copysign(R * u ** (1 + 0.6 * SALT), k)
        hw = math.sqrt(max(R * R - x * x, 0)) * 0.94
        body.append(line(cam.ps([(x, -hw, LZ), (x, hw, LZ)]), HAIR, G4))
    body.append(loop(cam.ps(topc), SUBJ, G7))
    return frame(body)


# =================================================== v2 · single-weight contour
def v2():
    """The tide, literally: the swash running up a shore, its lace edge the one bright line,
    the strand marks of earlier waves above it, the swell lines out on the sea, and a ledge of
    eight hollows the water has just filled. Every line one weight."""
    cam = Camera(eye=(0.0, -7.0, 2.6), target=(0.4, 1.6, 0), f=330, at=(232, 112))
    body = []
    th = math.radians(-24)                       # the shore runs diagonally across the view

    def S(u, v, z=0.0):                          # shore coordinates: u along the shore, v up the beach (toward viewer)
        return (u * math.cos(th) + v * math.sin(th), -u * math.sin(th) + v * math.cos(th) * -1, z)

    # horizon
    hz = cam.p((0, 4000, 0))[1]
    body.append(line([(0, hz), (480, hz)], LINE, G2))
    # swell lines on the sea, parallel to the shore, spaced by the period
    lam = 0.55 * SWELL_S / 2 + 0.25
    v = -1.2
    k = 0
    while k < 12:
        pts = cam.ps([S(u / 4, v - 0.05 * math.sin(u * 0.7 + k)) for u in range(-60, 61)])
        ys = [p[1] for p in pts]
        if min(ys) - hz < 4:
            break
        body.append(line(pts, LINE, G3 if k < 2 else G2))
        v -= lam * (1 + 0.25 * k)
        k += 1

    # wet edge where the sea meets the beach
    body.append(line(cam.ps([S(u / 4, -0.55 + 0.04 * math.sin(u * 0.9)) for u in range(-60, 61)]), LINE, G3))
    # strand marks of earlier swashes: depth decides how many stay
    n_marks = 1 + round(4 * P_DEPTH)
    rnd = random.Random(4)
    for m in range(n_marks):
        vv = 0.75 + 0.42 * (m + 1)
        pts = []
        for u in range(-60, 61):
            uu = u / 4
            pts.append(S(uu, vv + 0.12 * math.sin(uu * 1.3 + m * 2) + 0.06 * math.sin(uu * 3.1 + m)))
        sp = cam.ps(pts)
        # broken lines: strand marks are scattered wrack, not continuous
        seg, cur = [], []
        for i, p in enumerate(sp):
            if (i // 7 + m) % 3 != 2:
                cur.append(p)
            elif cur:
                seg.append(cur)
                cur = []
        if cur:
            seg.append(cur)
        for s in seg:
            body.append(line(s, LINE, G3 if m == 0 else G2))

    # the ledge with eight hollows, upper right, partly in the swash
    ledge_c = (1.7, -1.2)
    ledge = []
    for i in range(14):
        a = 2 * math.pi * i / 14
        r = 1.0 + 0.12 * math.sin(3 * a + 0.5) + 0.07 * math.cos(5 * a)
        ledge.append((ledge_c[0] + 2.0 * r * math.cos(a), ledge_c[1] + 0.95 * r * math.sin(a), 0.0))
    ledge_s = cam.ps(ledge)
    body.append(poly(ledge_s, G0))
    body.append(loop(ledge_s, LINE, G4))

    # the swash: the lacy edge of the latest wave, brightest; it stops at the ledge
    sw = []
    for u in range(-80, 81):
        uu = u / 5
        vv = 0.65 + 0.16 * math.sin(uu * 1.7) + 0.07 * math.sin(uu * 4.3 + 1) + 0.03 * math.sin(uu * 9.1)
        sw.append(S(uu, vv))
    sws = cam.ps(sw)
    for run in runs_where(sws, lambda p: not inside(p, ledge_s)):
        body.append(line(run, LINE, G7))
    # the thin sheet behind the swash: one backwash line
    bw = cam.ps([S(u / 5, 0.15 + 0.1 * math.sin(u / 5 * 1.3 + 2)) for u in range(-80, 81)])
    for run in runs_where(bw, lambda p: not inside(p, ledge_s)):
        body.append(line(run, LINE, G3))

    # eight hollows in the ledge: size by partial (bigger hollow, lower partial)
    spots = [(0.35, -1.15), (1.15, -0.75), (1.95, -1.35), (2.65, -0.85), (3.2, -1.45), (0.95, -1.75),
             (2.35, -1.9), (3.25, -1.05)]
    for k, (x, y) in enumerate(spots, start=1):
        r = 0.5 / ratio(k) ** 0.75
        rim = cam.ps(circle3((x, y, 0), r, 40))
        body.append(loop(rim, LINE, G5 if k == 1 else G4))
        if r > 0.12:
            water = cam.ps(circle3((x + 0.02, y + 0.06 * r, 0), r * 0.62, 32, math.pi * 1.1, math.pi * 1.9))
            body.append(line(water, LINE, G3))
    return frame(body)


# ======================================================= v3 · hatched mass
def v3():
    """The mechanism: eight stone pipes standing in the surge, their mouths cut to the
    partial ratios, so each wave blowing across them rings its own pitch. The stone's
    turned-away side is hatched; the fundamental's mouth is the brightest edge."""
    cam = Camera(eye=(-2.2, -9.0, 4.4), target=(0.0, 0.0, 1.35), f=440, at=(250, 118))
    body = []
    water_z = 0.25 + 0.5 * P_DEPTH                 # depth: the pool stands higher round the pipes
    R = 0.3
    xs = [-2.55 + i * 0.73 for i in range(8)]
    pipes = []
    for k, x in enumerate(xs, start=1):
        h = water_z + 3.0 / ratio(k) ** 0.9
        y = 0.18 * (x / 2.5) ** 2 * 2.5
        pipes.append((k, (x, y), h))
    light = norm((-1, -0.6, 0.4))                  # light from the left, in front

    # surge crests on the water in front of the pipes, spaced by the swell period
    lam = 0.35 + 0.45 * SWELL_S / 2
    yy = -0.8
    for i in range(4):
        pts = cam.ps([(x / 6, yy + 0.06 * math.sin(x / 6 * 1.4 + i), water_z) for x in range(-36, 37)])
        body.append(line(pts, HAIR if i else LINE, G3 if i else G4))
        yy -= lam
    # far waterline behind the pipes
    body.append(line(cam.ps([(x / 6, 1.6, water_z) for x in range(-36, 37)]), HAIR, G2))

    for k, (x, y), h in sorted(pipes, key=lambda p: -cam.depth((p[1][0], p[1][1], 0))):
        c = (x, y, 0)
        # silhouette of the cylinder above the water: top ellipse back half + sides + waterline front half
        to_eye = norm(sub(cam.eye, (x, y, h / 2)))
        side = norm(cross((0, 0, 1), to_eye))     # unit vector to the silhouette edge, horizontally
        ang_r = math.atan2(side[1], side[0])
        top_back = circle3((x, y, h), R, 24, ang_r, ang_r + math.pi)
        wl_front = circle3((x, y, water_z), R, 24, ang_r + math.pi, ang_r + 2 * math.pi)
        sil = cam.ps(top_back) + cam.ps(wl_front)
        body.append(poly(sil, G0))
        # hatched mass: the half turned from the light, between the centre line and the dark silhouette edge
        dark = -1 if dot(side, light) > 0 else 1
        a_dark = ang_r if dark < 0 else ang_r + math.pi
        mid = math.atan2(-to_eye[1], -to_eye[0]) + math.pi   # the angle facing the eye
        shade3 = circle3((x, y, h), R, 12, mid + 0.15 * dark * -1, a_dark) if False else None
        # region: from the angle facing the eye (offset toward dark) to the dark edge, top to waterline
        a_from = mid + (0.25 if a_dark > mid else -0.25)
        a_to = a_dark
        top_arc = [(x + R * math.cos(a), y + R * math.sin(a), h) for a in [a_from + (a_to - a_from) * i / 10 for i in range(11)]]
        bot_arc = [(x + R * math.cos(a), y + R * math.sin(a), water_z) for a in [a_to + (a_from - a_to) * i / 10 for i in range(11)]]
        region = cam.ps(top_arc) + cam.ps(bot_arc)
        body.extend(hatch(region, G3, gap=3.6, phase=k * 1.3))
        # outline: two side edges and the waterline (Line), and the mouth (rim of the top)
        for a in (ang_r, ang_r + math.pi):
            body.append(line(cam.ps([(x + R * math.cos(a), y + R * math.sin(a), h),
                                     (x + R * math.cos(a), y + R * math.sin(a), water_z)]), LINE, G4))
        body.append(line(cam.ps(wl_front), LINE, G4))
        mouth = cam.ps(circle3((x, y, h), R, 40))
        body.append(poly(mouth, G0))
        body.append(loop(mouth, SUBJ if k == 1 else LINE, G7 if k == 1 else G5))
        # the bore: the inner wall's far lip, a hairline inside the mouth
        inner = cam.ps(circle3((x, y, h), R * 0.7, 30))
        body.append(loop(inner, HAIR, G3))
        # a coursing joint on the stone, partway down (inner structure)
        if h - water_z > 0.9:
            body.append(line(cam.ps(circle3((x, y, water_z + (h - water_z) * 0.45), R, 16, ang_r + math.pi, ang_r + 2 * math.pi)),
                             HAIR, G2))
    return frame(body)


# =================================================== v4 · edge-lit silhouette
def v4():
    """The material, close: foam on the pool's surface. Each bubble rings at a pitch set by
    its size (a bubble's own resonance), so the raft is sorted into eight sizes, the
    partials. Black domes, lit only along their back edges; the largest is the brightest."""
    cam = Camera(eye=(0.0, -7.5, 1.15), target=(0.0, 0.6, 0.15), f=520, at=(240, 140))
    body = []
    rnd = random.Random(11)

    # ripple lines on the surface beneath the raft: spacing follows the swell period
    lam = 0.25 + 0.35 * SWELL_S / 2
    y = -1.6
    last = None
    while y < 30:
        sy = cam.p((0, y, 0))[1]
        if last is not None and last - sy < 4:
            break
        if sy < H:
            body.append(line(cam.ps([(x / 3, y + 0.05 * math.sin(x / 3 + y), 0) for x in range(-45, 46)]), HAIR, G2))
        last = sy
        y += lam * (1 + 0.15 * (y + 1.6))

    # the raft: depth decides how many bubbles survive; sizes are the partials
    n = 6 + round(12 * P_DEPTH)                     # 12 at the default
    classes = [1, 2, 3, 2, 4, 5, 3, 6, 4, 7, 8, 5, 6, 7, 8, 3, 4, 5]
    placed = []
    for k in classes[:n]:
        r = 0.62 / ratio(k) ** 0.8
        for _ in range(4000):
            x = rnd.uniform(-2.6, 2.6)
            yy = rnd.uniform(-0.6, 1.9)
            if k == 1:
                x, yy = 0.25, 0.55
            if all(math.hypot(x - px, yy - py) > (r + pr) * 1.02 for px, py, pr, _ in placed):
                break
        placed.append((x, yy, r, k))
    for x, yy, r, k in sorted(placed, key=lambda b: -cam.depth((b[0], b[1], 0))):
        c = (x, yy, 0)
        cs = cam.p(c)
        # projected radius of the sphere at its depth
        rp = cam.f * r / cam.depth(c)
        top = cam.p((x, yy, r))
        # the dome: upper half of the sphere's outline + front half of its waterline
        upper = [(cs[0] + rp * math.cos(a), cs[1] - (cs[1] - top[1]) * 0 - rp * math.sin(a))
                 for a in [math.pi * i / 32 for i in range(33)]]
        wl = cam.ps(circle3(c, r, 32, math.pi, 2 * math.pi))
        dome = upper + wl[1:-1]
        body.append(poly(dome, G0))
        # the waterline's front edge, hairline
        body.append(line(wl, HAIR, G3))
        # rim light along the back edge (light from behind, upper left)
        arc = [(cs[0] + rp * math.cos(a), cs[1] - rp * math.sin(a))
               for a in [math.radians(170 - 115 * i / 20) for i in range(21)]]
        if k == 1:
            body.append(line(arc, SUBJ, G7))
            body.append(line([(cs[0] + rp * math.cos(a), cs[1] - rp * math.sin(a))
                              for a in [math.radians(55 - 40 * i / 8) for i in range(9)]], HAIR, G4))
        else:
            body.append(line(arc, LINE, G5 if k <= 3 else G4))
        # the film's inner reflection: a hairline inside the dome, opposite side (larger bubbles only)
        if rp > 14:
            body.append(line([(cs[0] + rp * 0.66 * math.cos(a), cs[1] - rp * 0.66 * math.sin(a))
                              for a in [math.radians(40 - 25 * i / 8) for i in range(9)]], HAIR, G3))
    return frame(body)


# =================================================== v5 · detailed line art
def v5():
    """One scene, one subject: a boulder at the sea's edge with the pool in its top,
    drawn as detailed line art (hidden-line facets, strata, the pool's inner wall),
    the swell running in across the sea behind and around it."""
    cam = Camera(eye=(-3.4, -9.5, 3.9), target=(0.2, 0.0, 0.85), f=430, at=(272, 128))
    body = []
    rnd = random.Random(23)

    # sea: horizon and wave fronts on the plane z=0, spaced by the swell period
    hz = cam.p((0, 4000, 0))[1]
    body.append(line([(0, hz), (480, hz)], HAIR, G2))
    lam = 0.7 + 0.9 * SWELL_S / 2
    fronts = [-2.6 + i * lam * (1 + 0.35 * i) for i in range(12)]
    prev = None
    for i, yf in enumerate(fronts):
        pts = cam.ps([(x / 3, yf + 0.12 * math.sin(x / 3 * 0.8 + i), 0) for x in range(-40, 41)])
        sy = min(p[1] for p in pts)
        if prev is not None and abs(prev - sy) < 4.5:
            break
        prev = sy
        near = i == 0
        body.append(line(pts, LINE if near else HAIR, G4 if near else G3 if i < 3 else G2))

    # the boulder: rings of a faceted body (bottom at the water, a bulge, the top)
    N = 9
    rings = []
    for z, rx, ry, jit in ((0.0, 1.85, 1.35, 0.12), (0.75, 2.0, 1.45, 0.1), (1.45, 1.55, 1.1, 0.08)):
        ring = []
        for i in range(N):
            a = 2 * math.pi * (i + 0.3 * rnd.random()) / N
            j = 1 + jit * (rnd.random() - 0.5) * 2
            ring.append((rx * j * math.cos(a), ry * j * math.sin(a), z + 0.08 * (rnd.random() - 0.5)))
        rings.append(ring)
    faces = []
    for r0, r1 in ((rings[0], rings[1]), (rings[1], rings[2])):
        for i in range(N):
            q = [r0[i], r0[(i + 1) % N], r1[(i + 1) % N], r1[i]]
            n = cross(sub(q[1], q[0]), sub(q[3], q[0]))
            cen = mul(add(add(q[0], q[1]), add(q[2], q[3])), 0.25)
            if dot(n, (cen[0], cen[1], 0)) < 0:
                n = mul(n, -1)
            faces.append((q, n, cen))
    vis = [fc for fc in faces if cam.facing(fc[1], fc[2])]
    allpts = cam.ps(rings[0] + rings[1] + rings[2])
    sil = hull(allpts)
    body.append(poly(sil, G0))
    for q, n, cen in vis:
        sq = cam.ps(q)
        body.append(loop(sq, HAIR, G3))
        # strata: lines across the face at fixed fractions, kept >= 3 px apart
        for t in (0.33, 0.66):
            a = cam.p(add(mul(q[0], 1 - t), mul(q[3], t)))
            b = cam.p(add(mul(q[1], 1 - t), mul(q[2], t)))
            h = abs(cam.p(q[3])[1] - cam.p(q[0])[1])
            if h * 0.33 >= 4 and math.dist(a, b) > 6:
                body.append(line([a, b], HAIR, G2))
    # the top face (seen from above), and the pool in it
    topq = cam.ps(rings[2])
    body.append(loop(topq, HAIR, G3))
    body.append(loop(sil, LINE, G4))

    # pool: the rim, the far inner wall, the water surface (the brightest), sunk by depth
    pc = (0.15, 0.05, 1.45)
    pr = 0.82
    d = 0.08 + 0.3 * P_DEPTH
    rim = cam.ps(circle3(pc, pr, 64))
    body.append(poly(rim, G0))
    body.append(loop(rim, LINE, G5))
    # the far inner wall: a few vertical hairlines from the rim down to the water
    for a in [math.radians(v) for v in (35, 60, 90, 120, 145)]:
        p0 = (pc[0] + pr * math.cos(a), pc[1] + pr * math.sin(a), pc[2])
        p1 = (pc[0] + pr * 0.94 * math.cos(a), pc[1] + pr * 0.94 * math.sin(a), pc[2] - d)
        body.append(line(cam.ps([p0, p1]), HAIR, G3))
    water = cam.ps(circle3((pc[0], pc[1], pc[2] - d), pr * 0.94, 72))
    for run in runs_where(water, lambda p: inside(p, rim)):
        body.append(line(run, SUBJ, G7))
    # wet foot: the wash line hugging the boulder's front at the water
    foot = cam.ps(rings[0][:])
    body.append(line([foot[i] for i in (5, 6, 7, 8, 0, 1)] if False else [], LINE, G4))
    return frame(body)


def main():
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        d = HERE / name
        d.mkdir(exist_ok=True)
        (d / "rest.svg").write_text(fn())
        print(d / "rest.svg")


if __name__ == "__main__":
    main()
