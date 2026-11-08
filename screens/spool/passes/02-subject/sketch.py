#!/usr/bin/env python3
"""Spool, subject pass 02: five rest-frame sketches of a spool of thread.

    python3 screens/spool/passes/02-subject/sketch.py

Writes v1..v5/rest.svg (480 x 220) beside this file, at the definition's
defaults (wear 0, wow 0, length 0.5 = 0.32 s, bias 0.5 = 0).

Every spool here is modelled in 3D (cylinders, boxes, helices, a laid thread)
and projected through one perspective camera per frame (craft.md, Think in 3D).
Hidden lines are handled by painter's order with black fills behind outlines.
Open lines are closed ribbons; closed outlines are stroked closed paths. No
text below the header. Grey only.

These are subject sketches, not device frames: nothing is bound yet, and the
part counts are far over a device budget in places (each candidate's risks say
where). Binding and the budget belong to phase 4/5.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent

# Stock greys (constraints.md, header steps).
B, S2, S, M, G, D, F, K = ("#CDCDCD", "#AFAFAF", "#969696", "#7D7D7D",
                           "#646464", "#4B4B4B", "#323232", "#000000")
FONT = "UniversNextPro-Light"
HAIR, LINE, SUBJ = 1.0, 1.5, 2.2          # craft.md line weights

BODY = (0.0, 21.0, 480.0, 220.0)          # artwork stays below the stock header

# ---------------------------------------------------------------- the machine

DEFAULTS = {"wear": 0.0, "wow": 0.0, "length": 0.5, "bias": 0.5}


class Spool:
    """Control positions (0..1) -> what happens to the thread."""

    # The cycle as written: a ramp, a step down to a shelf, a drop, a floor.
    WRITTEN = [(0.0, -0.9), (0.55, 0.9), (0.6, -0.1), (0.85, 0.15), (0.9, -0.9), (1.0, -0.9)]

    def __init__(self, **kv: float) -> None:
        v = {**DEFAULTS, **kv}
        self.pos = v
        self.wear = v["wear"] ** 2                          # power 2
        self.wow = v["wow"]
        self.length = 0.05 * (2.0 / 0.05) ** v["length"]    # s, exponential
        self.bias = v["bias"] * 2 - 1                       # -1 under .. +1 over

    def header(self) -> list[str]:
        b = round(self.bias * 100)
        return [str(round(self.wear * 100)), str(round(self.wow * 100)),
                f"{self.length:.2f}s", ("+" if b > 0 else "") + str(b)]

    def fullness(self) -> float:
        """How much thread is wound, 0..1, from length (a longer loop is more thread)."""
        return self.pos["length"]


# ---------------------------------------------------------------- 3D

def v3(x, y, z):
    return np.array([x, y, z], dtype=float)


def unit(v):
    return v / np.linalg.norm(v)


class Camera:
    """One perspective camera: position, look-at, then a 2D fit."""

    def __init__(self, pos, target, up=(0, 0, 1)):
        self.pos = np.asarray(pos, float)
        fwd = unit(np.asarray(target, float) - self.pos)
        right = unit(np.cross(fwd, up))
        self.fwd, self.right, self.up = fwd, right, np.cross(right, fwd)
        self.f, self.cx, self.cy = 1.0, 0.0, 0.0

    def raw(self, p):
        d = np.asarray(p, float) - self.pos
        z = d @ self.fwd
        return (d @ self.right) / z, (d @ self.up) / z, z

    def fit(self, pts, box):
        """Scale and centre so the bbox of pts fills box (x0, y0, x1, y1), aspect kept."""
        r = np.array([self.raw(p)[:2] for p in pts])
        (x0, y0), (x1, y1) = r.min(0), r.max(0)
        bx0, by0, bx1, by1 = box
        self.f = min((bx1 - bx0) / (x1 - x0), (by1 - by0) / (y1 - y0))
        self.cx = (bx0 + bx1) / 2 - self.f * (x0 + x1) / 2
        self.cy = (by0 + by1) / 2 + self.f * (y0 + y1) / 2
        return self

    def __call__(self, p):
        x, y, _ = self.raw(p)
        return (self.cx + self.f * x, self.cy - self.f * y)

    def dist(self, p):
        return float(np.linalg.norm(np.asarray(p, float) - self.pos))

    def faces(self, p, normal):
        return float(np.dot(normal, self.pos - np.asarray(p, float))) > 0


def basis(axis):
    a = unit(np.asarray(axis, float))
    t = v3(1, 0, 0) if abs(a[0]) < 0.9 else v3(0, 1, 0)
    u = unit(np.cross(a, t))
    return a, u, np.cross(a, u)


def ring(c, axis, r, n=72, a0=0.0, a1=2 * math.pi):
    _, u, w = basis(axis)
    c = np.asarray(c, float)
    ts = np.linspace(a0, a1, n, endpoint=(a1 - a0) < 2 * math.pi - 1e-9)
    return [c + r * (math.cos(t) * u + math.sin(t) * w) for t in ts], ts


def hull(pts):
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in pts))
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


# ---------------------------------------------------------------- 2D kit

def n(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def dedupe(pts, gap=0.3, closed=False):
    out = []
    for p in pts:
        if not out or math.dist(out[-1], p) >= gap:
            out.append(tuple(p))
    if closed and len(out) > 2 and math.dist(out[0], out[-1]) < max(gap, 0.5):
        out.pop()
    return out


def decimate(pts, cap=60):
    if len(pts) <= cap:
        return pts
    k = len(pts) / cap
    return [pts[int(i * k)] for i in range(cap)]


def clip_poly(pts, box=BODY):
    """Sutherland-Hodgman against the body rectangle."""
    x0, y0, x1, y1 = box
    edges = [(lambda p: p[0] >= x0, lambda a, b: _ix(a, b, 0, x0)),
             (lambda p: p[0] <= x1, lambda a, b: _ix(a, b, 0, x1)),
             (lambda p: p[1] >= y0, lambda a, b: _ix(a, b, 1, y0)),
             (lambda p: p[1] <= y1, lambda a, b: _ix(a, b, 1, y1))]
    out = list(pts)
    for inside, cut in edges:
        if not out:
            break
        src, out = out, []
        for i, cur in enumerate(src):
            prev = src[i - 1]
            if inside(cur):
                if not inside(prev):
                    out.append(cut(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(cut(prev, cur))
    return out


def _ix(a, b, k, v):
    t = (v - a[k]) / (b[k] - a[k])
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def clip_line(pts, box=BODY):
    """Split an open polyline into runs inside the body rectangle."""
    x0, y0, x1, y1 = box
    ins = lambda p: x0 <= p[0] <= x1 and y0 <= p[1] <= y1
    runs, cur = [], []
    for i, p in enumerate(pts):
        if ins(p):
            if not cur and i > 0:
                cur.append(_enter(pts[i - 1], p, box))
            cur.append(p)
        else:
            if cur:
                cur.append(_enter(p, pts[i - 1], box))
                runs.append(cur)
                cur = []
    if cur:
        runs.append(cur)
    return [r for r in runs if len(r) >= 2]


def _enter(out_p, in_p, box):
    """Point where the segment out_p -> in_p crosses into box."""
    lo, hi = 0.0, 1.0
    for _ in range(30):
        m = (lo + hi) / 2
        q = (out_p[0] + (in_p[0] - out_p[0]) * m, out_p[1] + (in_p[1] - out_p[1]) * m)
        if box[0] <= q[0] <= box[2] and box[1] <= q[1] <= box[3]:
            hi = m
        else:
            lo = m
    return (out_p[0] + (in_p[0] - out_p[0]) * hi, out_p[1] + (in_p[1] - out_p[1]) * hi)


def offset(pts, w):
    """Closed ribbon polygon of width w around an open polyline (mitred, clamped)."""
    h = w / 2
    left, right = [], []
    for i, p in enumerate(pts):
        a = pts[i - 1] if i > 0 else None
        b = pts[i + 1] if i < len(pts) - 1 else None
        normals = []
        for q0, q1 in ((a, p), (p, b)):
            if q0 is None or q1 is None:
                continue
            dx, dy = q1[0] - q0[0], q1[1] - q0[1]
            ln = math.hypot(dx, dy)
            normals.append((-dy / ln, dx / ln))
        nx = sum(v[0] for v in normals)
        ny = sum(v[1] for v in normals)
        ln = math.hypot(nx, ny) or 1
        nx, ny = nx / ln, ny / ln
        cos = max(0.5, nx * normals[0][0] + ny * normals[0][1])
        m = h / cos
        left.append((p[0] + nx * m, p[1] + ny * m))
        right.append((p[0] - nx * m, p[1] - ny * m))
    return left + right[::-1]


class Frame:
    def __init__(self, title: str, values: list[str]) -> None:
        self.title, self.values, self.body = title, values, []

    def poly(self, pts, fill=K, stroke="none", sw=0.0, clip=True):
        pts = [tuple(map(float, p)) for p in pts]
        if clip:
            pts = clip_poly(pts)
        pts = decimate(dedupe(pts, 0.4, closed=True), 62)
        if len(pts) < 3:
            return
        d = "M " + " L ".join(f"{n(x)} {n(y)}" for x, y in pts) + " Z"
        sw_attr = f' stroke-width="{n(sw)}"' if stroke != "none" else ""
        self.body.append(f'<path d="{d}" fill="{fill}" stroke="{stroke}"{sw_attr}/>')

    def outline(self, pts, col, w, fill=K):
        """A closed outline (stroked closed path) with a black body behind it."""
        pts = [tuple(map(float, p)) for p in pts]
        if all(BODY[0] <= x <= BODY[2] and BODY[1] + w <= y <= BODY[3] for x, y in pts):
            self.poly(pts, fill=fill, stroke=col, sw=w, clip=False)
        else:  # crosses the frame edge: fill the clipped body, draw the outline as a ribbon
            if fill != "none":
                self.poly(pts, fill=fill)
            self.line(list(pts) + [pts[0]], w, col)

    def line(self, pts, w, col):
        """An open line as filled closed ribbons, clipped, <= 62 points per path."""
        pts = [tuple(map(float, p)) for p in pts]
        for run in clip_line(pts, (BODY[0], BODY[1] + w, BODY[2], BODY[3])):
            run = dedupe(run, 0.8)
            i = 0
            while i < len(run) - 1:
                chunk = run[i:i + 31]
                if len(chunk) >= 2:
                    self.poly(offset(chunk, w), fill=col, clip=False)
                i += 30

    def svg(self) -> str:
        steps = [K, F, D, G, M, S, S2, B]
        head = ['<g id="preview_canvas">', '  <rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>', '</g>',
                '<g id="preview_header">']
        for i, c in enumerate(steps):
            head.append(f'  <rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
        for i, t in enumerate(["wear", "wow", "length", "bias"]):
            col = "#CBCBCB" if i < 2 else "#000000"
            head.append(f'  <text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{col}" stroke="none" '
                        f'font-family="{FONT}" font-size="10px">{t}</text>')
            head.append(f'  <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{col}" stroke="none" '
                        f'font-family="{FONT}" font-size="20px">{self.values[i]}</text>')
        head.append('</g>')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">\n'
                f'  <!-- spool · subject pass 02 · {self.title} -->\n  ' + "\n  ".join(head) + "\n  "
                + "\n  ".join(self.body) + "\n</svg>\n")


# ---------------------------------------------------------------- solids (hull-based hidden line)

def cyl_hull(cam, c0, c1, r, n=72):
    a = np.asarray(c1, float) - np.asarray(c0, float)
    r0, _ = ring(c0, a, r, n)
    r1, _ = ring(c1, a, r, n)
    return hull([cam(p) for p in r0 + r1])


def visible_runs(cam, pts3, normals):
    runs, cur = [], []
    for p, nr in zip(pts3, normals):
        if cam.faces(p, nr):
            cur.append(cam(p))
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return runs


def ring_arcs(cam, c, axis, r, n=120):
    """Visible (front-facing) arcs of a circle drawn on a cylinder's side."""
    pts, ts = ring(c, axis, r, n)
    _, u, w = basis(axis)
    nrm = [math.cos(t) * u + math.sin(t) * w for t in ts]
    # rotate so a run doesn't wrap across the array's start
    k = next((i for i, (p, q) in enumerate(zip(pts, nrm)) if not cam.faces(p, q)), 0)
    pts, nrm = pts[k:] + pts[:k], nrm[k:] + nrm[:k]
    return visible_runs(cam, pts, nrm)


def draw_cyl(fr, cam, c0, c1, r, col, w, cap_col=None, cap_w=None, n=72):
    """Black body, silhouette outline, the end cap that faces the camera."""
    h = cyl_hull(cam, c0, c1, r, n)
    fr.outline(h, col, w)
    a = unit(np.asarray(c1, float) - np.asarray(c0, float))
    for c, nn in ((c0, -a), (c1, a)):
        if cam.faces(c, nn):
            pts, _ = ring(c, a, r, n)
            fr.outline([cam(p) for p in pts], cap_col or col, cap_w or w)
    return h


def box_faces(c, ax, half):
    """Six faces of an oriented box: (corners, normal)."""
    c = np.asarray(c, float)
    ax = [unit(np.asarray(v, float)) for v in ax]
    out = []
    for i in range(3):
        j, k = (i + 1) % 3, (i + 2) % 3
        for s in (-1, 1):
            fc = c + s * half[i] * ax[i]
            quad = [fc + sj * half[j] * ax[j] + sk * half[k] * ax[k]
                    for sj, sk in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            out.append((quad, s * ax[i]))
    return out


def draw_box(fr, cam, c, ax, half, col, w, inner=None):
    for quad, nn in box_faces(c, ax, half):
        ctr = sum(quad) / 4
        if cam.faces(ctr, nn):
            fr.outline([cam(p) for p in quad], col, w)
            if inner:
                inner(quad, nn)


def thread3(fr, cam, pts3, w, col):
    fr.line([cam(p) for p in pts3], w, col)


def bez3(p0, p1, p2, p3, k=40):
    p0, p1, p2, p3 = (np.asarray(p, float) for p in (p0, p1, p2, p3))
    return [(1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3
            for t in np.linspace(0, 1, k)]


class DepthBuffer:
    """A small z-buffer (3x supersampled) for exact hidden-line removal of faceted models."""

    SS = 3

    def __init__(self, cam, w=480, h=220):
        self.cam = cam
        self.W, self.H = w * self.SS, h * self.SS
        self.buf = np.zeros((self.H, self.W))          # 1/z of the nearest surface; 0 = nothing

    def _s(self, p):
        x, y = self.cam(p)
        return x * self.SS, y * self.SS, 1.0 / self.cam.raw(p)[2]

    def face(self, poly3):
        v = [self._s(p) for p in poly3]
        for i in range(1, len(v) - 1):
            self._tri(v[0], v[i], v[i + 1])

    def _tri(self, a, b, c):
        xs, ys = (a[0], b[0], c[0]), (a[1], b[1], c[1])
        x0, x1 = max(int(min(xs)) - 1, 0), min(int(max(xs)) + 2, self.W)
        y0, y1 = max(int(min(ys)) - 1, 0), min(int(max(ys)) + 2, self.H)
        if x0 >= x1 or y0 >= y1:
            return
        X, Y = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-9:
            return
        l1 = ((b[1] - c[1]) * (X - c[0]) + (c[0] - b[0]) * (Y - c[1])) / den
        l2 = ((c[1] - a[1]) * (X - c[0]) + (a[0] - c[0]) * (Y - c[1])) / den
        l3 = 1 - l1 - l2
        e = -0.02
        m = (l1 >= e) & (l2 >= e) & (l3 >= e)
        z = l1 * a[2] + l2 * b[2] + l3 * c[2]
        sub = self.buf[y0:y1, x0:x1]
        np.maximum(sub, np.where(m, z, 0), out=sub)

    def visible(self, p, eps=0.004):
        x, y, iz = self._s(p)
        xi, yi = int(x), int(y)
        if not (0 <= xi < self.W and 0 <= yi < self.H):
            return False
        return iz >= self.buf[yi, xi] * (1 - eps)

    def runs(self, pts3, step=0.5):
        """Visible screen-space runs of a 3D polyline."""
        out, cur = [], []
        for a, b in zip(pts3, pts3[1:]):
            la = math.dist(self.cam(a), self.cam(b))
            k = max(2, int(la / step))
            for t in np.linspace(0, 1, k, endpoint=False):
                p = a + (b - a) * t
                if self.visible(p):
                    cur.append(self.cam(p))
                elif cur:
                    out.append(cur); cur = []
        if self.visible(pts3[-1]):
            cur.append(self.cam(pts3[-1]))
        if cur:
            out.append(cur)
        return [r for r in out if len(r) >= 2 and math.dist(r[0], r[-1]) > 1.0]


# ---------------------------------------------------------------- v1 · trace · single-weight contour

def v1(s: Spool) -> Frame:
    """A spool lying on a table, seen from high above, and the trail of thread it has
    paid out behind it: the written cycle laid in thread, repeat after repeat."""
    fr = Frame("v1 · the trace left behind · single-weight contour", s.header())
    cam = Camera((6.4, -4.6, 3.4), (1.0, 0.4, 0.2))
    # world: table z=0; trail runs along +x at y=0, cycle amplitude along y.
    amp = 0.55 * (1 - 0.35 * max(s.bias, 0))
    period = 1.25 + 0.9 * (s.pos["length"] - 0.5)      # length: wavelength of one repeat on the table
    x_end = 2.4                                         # where the newest repeat ends
    reps = 5.4
    pts = []
    x_start = x_end - reps * period
    k = math.floor(x_start / period) - 1
    while True:
        for u, yv in Spool.WRITTEN:
            x = (k + u) * period + (x_end % period)
            if x_start - 0.6 <= x <= x_end + 1e-6:
                pts.append(v3(x, amp * yv, 0))
        k += 1
        if (k + 0) * period + (x_end % period) > x_end + 1e-6:
            break
    pts = [p for p in pts if p[0] <= x_end + 1e-6]
    # spool: lying on its side, axis along y (across the trail), ahead of the trail end
    sx, sy = x_end + 1.5, 0.15
    Rf, Rw, Lh, tf = 0.42, 0.24 + 0.1 * s.fullness(), 0.55, 0.07
    axis = v3(0, 1, 0)
    zc = Rf
    c = v3(sx, sy, zc)
    # the free run: from the trail's end, lifting to the winding's underside
    land = v3(sx - 0.12, sy + 0.12, zc + Rw)             # comes off the top of the winding
    free = bez3(pts[-1], pts[-1] + v3(0.55, 0, 0), land + v3(-0.55, -0.05, 0.05), land, 28)
    cam.fit([v3(-1.6, 0.6, 0), v3(sx + Rf, sy - Lh - tf, 0), v3(sx - Rf, sy + Lh, 2 * Rf), v3(1.0, -0.6, 0)],
            (8, 40, 446, 208))
    col, w = M, LINE                                   # one weight for the drawing
    # spool, far flange first (camera is at -y, so +y is far)
    far0, far1 = c + v3(0, Lh, 0), c + v3(0, Lh + tf, 0)
    near0, near1 = c - v3(0, Lh + tf, 0), c - v3(0, Lh, 0)
    draw_cyl(fr, cam, far0, far1, Rf, col, w)
    fr.outline(cyl_hull(cam, near1, far0, Rw), col, w)
    # a few turns of the winding, contour weight, >= 4 px apart
    for t in np.linspace(-Lh + 0.08, Lh - 0.08, 7):
        for run in ring_arcs(cam, c + v3(0, t, 0), axis, Rw):
            fr.line(run, w, D)
    fr.line([cam(p) for p in free], w, B)               # behind the near flange
    draw_cyl(fr, cam, near0, near1, Rf, col, w)
    # the bore in the near flange's face
    bore, _ = ring(near0, axis, 0.09, 36)
    fr.outline([cam(p) for p in bore], col, w)
    # the trail and the free run: the one bright thing, same single weight
    fr.line([cam(p) for p in pts], w, B)
    return fr


# ---------------------------------------------------------------- v2 · one detail large · hatched mass

def v2(s: Spool) -> Frame:
    """The lip of a big spool, so close the frame cuts it off: the top flange's rim and
    the wound mass under it, the turns drawn as a hatched mass, one thread peeling away."""
    fr = Frame("v2 · one detail at large scale · hatched mass", s.header())
    Rf, tf = 1.0, 0.1
    Rw = 0.80 + 0.12 * s.fullness()
    z_top = 1.4
    cam = Camera((-1.1, -5.2, 2.15), (0.2, 0, 1.0))
    cam.fit([v3(-Rf, 0, z_top + tf), v3(-Rf, 0, 0.35), v3(Rf * 0.5, -Rf * 0.85, z_top + tf)],
            (176, 38, 560, 260))
    axis = v3(0, 0, 1)
    # the wound mass: black body, silhouette
    wall = cyl_hull(cam, v3(0, 0, -0.6), v3(0, 0, z_top), Rw)
    fr.outline(wall, M, LINE)
    # the turns: a cross-wound helix seen as hatching, 1 px hairlines, >= 4.5 px apart
    pitch = 0.075 * (1 + 0.25 * s.bias)                 # bias: how tightly the turns lie
    ang = math.radians(38)
    for z0 in np.arange(-1.6, z_top + 0.9, pitch):
        pts3, nrm = [], []
        for th in np.linspace(math.radians(110), math.radians(330), 140):
            z = z0 + Rw * math.tan(ang) * (th - math.pi)
            if -0.6 <= z <= z_top - 0.005:
                pts3.append(v3(Rw * math.cos(th), Rw * math.sin(th), z))
                nrm.append(v3(math.cos(th), math.sin(th), 0))
        for run in visible_runs(cam, pts3, nrm):
            fr.line(run, HAIR, G)
    # the flange above it: side band, top face, bevel, bore
    draw_cyl(fr, cam, v3(0, 0, z_top), v3(0, 0, z_top + tf), Rf, M, LINE)
    for r in (0.93,):
        pts, _ = ring(v3(0, 0, z_top + tf), axis, r, 90)
        fr.line([cam(p) for p in pts] + [cam(pts[0])], HAIR, D)
    pts, _ = ring(v3(0, 0, z_top + tf), axis, 0.16, 48)
    fr.outline([cam(p) for p in pts], D, HAIR)
    # the thread: leaves the wound mass just under the rim on the left, runs out of frame
    th0 = math.radians(205)
    z0 = z_top - 0.18
    p0 = v3(Rw * math.cos(th0), Rw * math.sin(th0), z0)
    tang = v3(-math.sin(th0), math.cos(th0), 0) * -1
    sag = 0.25 * (1 + s.bias)                           # bias: tension, taut .. slack
    run = bez3(p0, p0 + tang * 0.5, p0 + v3(-1.2, -0.9, -0.15 - sag), v3(-2.6, -1.2, 0.95), 40)
    fr.line([cam(p) for p in run], SUBJ, B)
    return fr


# ---------------------------------------------------------------- v3 · the spool, literally · edge-lit silhouette

def v3_(s: Spool) -> Frame:
    """A wooden spool of thread standing on end, black against black, its right-hand
    edges caught by a light from behind; the loose end hangs and curls on the ground."""
    fr = Frame("v3 · the object, literally · edge-lit silhouette", s.header())
    Rf, tf, Rw = 1.0, 0.13, 0.66 + 0.22 * s.fullness()
    zb0, zb1, zt0, zt1 = 0.0, tf, 1.5 - tf, 1.5
    cam = Camera((1.3, -5.6, 2.25), (0.15, 0, 0.72))
    cam.fit([v3(x, y, z) for x in (-Rf, Rf) for y in (-Rf, Rf) for z in (0, 1.5)] + [v3(2.2, -0.6, 0)],
            (140, 30, 396, 206))
    axis = v3(0, 0, 1)
    light = np.array([0.94, -0.34])                      # screen direction the light comes from

    def lit_runs(pts, thresh, closed=True):
        """Split a convex outline into runs lit by the light (outward normal toward it) and dark ones."""
        cx_ = sum(p[0] for p in pts) / len(pts)
        cy_ = sum(p[1] for p in pts) / len(pts)
        ring2 = pts + [pts[0]] if closed else pts
        lit, dark, cur, state = [], [], [], None
        for a, b in zip(ring2, ring2[1:]):
            mx, my = (a[0] + b[0]) / 2 - cx_, (a[1] + b[1]) / 2 - cy_
            dx, dy = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(dx, dy) or 1
            nx, ny = dy / ln, -dx / ln
            if nx * mx + ny * my < 0:
                nx, ny = -nx, -ny
            on = nx * light[0] + ny * light[1] > thresh
            if state is not None and on != state:
                (lit if state else dark).append(cur)
                cur = [a]
            if not cur:
                cur = [a]
            cur.append(b)
            state = on
        if cur:
            (lit if state else dark).append(cur)
        return lit, dark

    def lit_outline(h, w_lit, col_lit, col_dark=F, thresh=0.35, fill=True):
        if fill:
            fr.poly(h)
        lit, dark = lit_runs(h, thresh)
        for r in dark:
            fr.line(r, HAIR, col_dark)
        for r in lit:
            fr.line(r, w_lit, col_lit)

    def flange(z0, z1):
        h = cyl_hull(cam, v3(0, 0, z0), v3(0, 0, z1), Rf)
        lit_outline(h, LINE, S)
        top, _ = ring(v3(0, 0, z1), axis, Rf, 96)
        tp = [cam(p) for p in top]
        fr.poly(tp)
        lit, dark = lit_runs(tp, 0.55)
        for r in dark:
            fr.line(r, HAIR, D)
        for r in lit:
            fr.line(r, LINE, S)

    flange(zb0, zb1)
    # the winding: black body, the brightest rim on its lit edge, a few turns near that edge
    h = cyl_hull(cam, v3(0, 0, zb1), v3(0, 0, zt0), Rw)
    fr.poly(h)
    cx = cam(v3(0, 0, (zb1 + zt0) / 2))[0]
    xmax = max(p[0] for p in h)
    for z in np.arange(zb1 + 0.05, zt0 - 0.02, 0.05):
        pts, ts = ring(v3(0, 0, z), axis, Rw, 200)
        nrm = [v3(math.cos(t), math.sin(t), 0) for t in ts]
        for run in visible_runs(cam, pts, nrm):
            seg = [p for p in run if p[0] > cx + 0.55 * (xmax - cx)]
            if len(seg) >= 2:
                fr.line(seg, HAIR, D)
    lit_outline(h, SUBJ, B, thresh=0.7, fill=False)
    flange(zt0, zt1)
    # the bore in the top face
    bore, _ = ring(v3(0, 0, zt1), axis, 0.13, 40)
    fr.outline([cam(p) for p in bore], D, HAIR)
    # the loose end: off the winding's lit side, over the bottom flange's rim, onto the ground, a curl
    th = math.radians(-24)
    out = v3(math.cos(th), math.sin(th), 0)
    side = v3(-math.sin(th), math.cos(th), 0)
    p0 = Rw * out + v3(0, 0, 0.98)
    ctrl = [p0, p0 + 0.1 * out - 0.04 * side + v3(0, 0, -0.18),
            1.06 * Rf * out - 0.08 * side + v3(0, 0, tf + 0.1),
            1.18 * Rf * out - 0.12 * side + v3(0, 0, 0.0)]
    gc = 1.18 * Rf * out + v3(0.42, -0.42, 0)
    a0 = math.atan2(ctrl[-1][1] - gc[1], ctrl[-1][0] - gc[0])
    r0 = math.dist(ctrl[-1][:2], gc[:2])
    for t in np.linspace(0.35, 1.6 * math.pi, 9):
        rr = r0 * (1 - 0.22 * t / math.pi)
        ctrl.append(gc + v3(rr * math.cos(a0 - t), rr * math.sin(a0 - t), 0))
    fr.line([cam(p) for p in catmull(ctrl, 10)], SUBJ, B)
    return fr


def catmull(ctrl, k=10):
    """Smooth 3D curve through control points (Catmull-Rom)."""
    c = [ctrl[0]] + list(ctrl) + [ctrl[-1]]
    out = []
    for i in range(1, len(c) - 2):
        p0, p1, p2, p3 = c[i - 1], c[i], c[i + 1], c[i + 2]
        for t in np.linspace(0, 1, k, endpoint=False):
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(ctrl[-1])
    return out


def _arc_split(pts, keep):
    runs, cur = [], []
    for p in pts + [pts[0]]:
        if keep(p):
            cur.append(p)
        elif cur:
            runs.append(cur); cur = []
    if cur:
        runs.append(cur)
    return [r for r in runs if len(r) >= 2]


# ---------------------------------------------------------------- v4 · the mechanism · detailed line art

def v4(s: Spool) -> Frame:
    """A hand bobbin winder: base, two bearing posts, spindle, crank, a tension post with
    two discs, spring and nut; the thread comes through the discs onto the bobbin."""
    fr = Frame("v4 · the mechanism, the thing in the hand · detailed line art", s.header())
    cam = Camera((4.4, -7.6, 4.6), (0.15, 0, 0.95))
    zs = 1.2
    Rf, Rh = 0.72, 0.17
    Rw = 0.3 + 0.32 * s.fullness()
    cam.fit([v3(x, y, z) for x in (-2.3, 2.6) for y in (-1.1, 0.95) for z in (-0.22, 0)]
            + [v3(0, 1.0, 2.45), v3(-2.3, 0.6, 2.3)], (16, 30, 464, 214))
    X, Y, Z = v3(1, 0, 0), v3(0, 1, 0), v3(0, 0, 1)
    OL, IN = M, G                                        # outer edges, inner detail

    def hair_inset(quad, nn, d=0.07):
        c = sum(quad) / 4
        q2 = [c + (p - c) * (1 - d / max(np.linalg.norm(p - c), 1e-6) * 1.4) for p in quad]
        fr.outline([cam(p) for p in q2], IN, HAIR, fill="none")

    # base plate (camera at -y, +z: the back is +y)
    draw_box(fr, cam, v3(0.15, 0, -0.11), (X, Y, Z), (2.45, 1.05, 0.11), OL, LINE,
             inner=lambda q, nn: hair_inset(q, nn, 0.12) if nn[2] > 0.5 else None)
    # tension post at the back, stud along -y toward the camera, discs, spring, nut
    draw_box(fr, cam, v3(-0.2, 0.9, 1.15), (X, Y, Z), (0.11, 0.09, 1.15), OL, LINE)
    zt = 2.02
    draw_cyl(fr, cam, v3(-0.2, 0.81, zt), v3(-0.2, 0.18, zt), 0.035, OL, HAIR)
    draw_cyl(fr, cam, v3(-0.2, 0.68, zt), v3(-0.2, 0.64, zt), 0.24, OL, LINE, IN, HAIR)
    gap_y = 0.61
    thr_in = [v3(-2.5, gap_y, 2.32), v3(-1.2, gap_y, 2.12), v3(-0.2, gap_y, zt - 0.17)]
    thread3(fr, cam, thr_in, SUBJ, B)
    draw_cyl(fr, cam, v3(-0.2, 0.58, zt), v3(-0.2, 0.54, zt), 0.24, OL, LINE, IN, HAIR)
    # spring: a helix round the stud, hairline, turns >= 3 px apart
    sp = []
    for t in np.linspace(0, 1, 90):
        a = t * 2 * math.pi * 5
        sp.append(v3(-0.2 + 0.07 * math.cos(a), 0.52 - 0.2 * t, zt + 0.07 * math.sin(a)))
    nr = [v3(math.cos(t * 2 * math.pi * 5), 0, math.sin(t * 2 * math.pi * 5)) for t in np.linspace(0, 1, 90)]
    for run in visible_runs(cam, sp, nr):
        fr.line(run, HAIR, IN)
    draw_cyl(fr, cam, v3(-0.2, 0.32, zt), v3(-0.2, 0.22, zt), 0.1, OL, LINE, IN, HAIR, n=6)
    # bearing posts and spindle, far (left) to near (right)
    def post(x):
        draw_box(fr, cam, v3(x, 0, 0.7), (X, Y, Z), (0.11, 0.3, 0.7), OL, LINE)
        for hole_x in (x - 0.11, x + 0.11):
            if cam.faces(v3(hole_x, 0, zs), X * (1 if hole_x > x else -1)):
                pts, _ = ring(v3(hole_x, 0, zs), X, 0.1, 30)
                fr.outline([cam(p) for p in pts], IN, HAIR, fill="none")
                pts, _ = ring(v3(hole_x, 0, 0.32), X, 0.05, 20)
                fr.outline([cam(p) for p in pts], IN, HAIR, fill="none")
    draw_cyl(fr, cam, v3(-1.95, 0, zs), v3(-1.75, 0, zs), 0.06, OL, HAIR)
    post(-1.62)
    draw_cyl(fr, cam, v3(-1.5, 0, zs), v3(-0.62, 0, zs), 0.06, OL, HAIR)
    # bobbin: far flange, hub, winding, thread onto it, near flange
    xa, xb, tf = -0.62, 0.62, 0.07
    draw_cyl(fr, cam, v3(xa - tf, 0, zs), v3(xa, 0, zs), Rf, OL, LINE)
    draw_cyl(fr, cam, v3(xa, 0, zs), v3(xb, 0, zs), Rw, OL, LINE)
    for x in np.arange(xa + 0.045, xb, 0.06):
        for run in ring_arcs(cam, v3(x, 0, zs), X, Rw, 120):
            fr.line(run, HAIR, IN)
    # thread from the discs down onto the winding (tangent, then wraps over the front)
    P = np.array([gap_y, zt - 0.17])
    C = np.array([0.0, zs])
    d = P - C
    al, be = math.atan2(d[1], d[0]), math.acos(Rw / np.linalg.norm(d))
    tp = al - be
    xt = 0.05
    land = v3(xt, Rw * math.cos(tp), zs + Rw * math.sin(tp))
    out = bez3(thr_in[-1], thr_in[-1] + v3(0.05, -0.02, -0.08), land + (thr_in[-1] - land) * 0.3, land, 30)
    wrap = [v3(xt + 0.02 * k / 30, Rw * math.cos(tp - k / 30 * (tp + 1.35)), zs + Rw * math.sin(tp - k / 30 * (tp + 1.35)))
            for k in range(31)]
    thread3(fr, cam, out + wrap[1:], SUBJ, B)
    draw_cyl(fr, cam, v3(xb, 0, zs), v3(xb + tf, 0, zs), Rf, OL, LINE)
    # the near flange's face: five holes round the hub, hub bore
    for k in range(5):
        a = k * 2 * math.pi / 5 + 0.3
        pts, _ = ring(v3(xb + tf, 0.44 * math.cos(a), zs + 0.44 * math.sin(a)), X, 0.12, 30)
        fr.outline([cam(p) for p in pts], IN, HAIR, fill="none")
    pts, _ = ring(v3(xb + tf, 0, zs), X, Rh, 36)
    fr.outline([cam(p) for p in pts], IN, HAIR, fill="none")
    draw_cyl(fr, cam, v3(xb + tf, 0, zs), v3(1.31, 0, zs), 0.06, OL, HAIR)
    post(1.42)
    draw_cyl(fr, cam, v3(1.53, 0, zs), v3(2.02, 0, zs), 0.06, OL, HAIR)
    # crank: arm turned about the spindle (wow sets its rocking), handle parallel to it
    phi = math.radians(-115 + 40 * s.wow)
    radial = v3(0, math.cos(phi), math.sin(phi))
    tang = np.cross(X, radial)
    L = 0.62
    draw_box(fr, cam, v3(2.07, 0, zs) + radial * (L / 2), (X, radial, tang), (0.05, L / 2 + 0.09, 0.09), OL, LINE)
    hc = v3(2.12, 0, zs) + radial * L
    draw_cyl(fr, cam, hc, hc + v3(0.42, 0, 0), 0.075, OL, LINE)
    return fr


# ---------------------------------------------------------------- v5 · the winding seen close · hidden-line 3D

def v5(s: Spool) -> Frame:
    """A spool on its side with a quarter of the winding cut away toward the camera,
    so the thread shows in section: every turn a small round cut, layer on layer
    on the barrel, between two whole flanges."""
    fr = Frame("v5 · the material, seen close · hidden-line 3D", s.header())
    Rf, Rbo, Rb = 1.0, 0.13, 0.34
    Rw = 0.62 + 0.3 * s.fullness()                       # length: how many layers are wound
    x0, xa, xb, x1 = -1.22, -1.08, 1.08, 1.22
    e = math.radians(31)
    cam = Camera((-2.3, -5.6, 5.6 * math.tan(e)), (0.0, 0, 0.1))
    # theta: point = (x, -r cos th, r sin th): th=0 faces the camera (-y), th=90 is up
    tha, thb = math.radians(-18), math.radians(82)       # the quarter of the winding that's cut away

    def P(x, r, th):
        return v3(x, -r * math.cos(th), r * math.sin(th))

    def radial(th):
        return v3(0, -math.cos(th), math.sin(th))

    cam.fit([P(x, Rf, t) for x in (x0, x1) for t in np.linspace(0, 2 * math.pi, 24)],
            (-10, 26, 470, 262))                        # close: the frame trims the flanges' rims
    faces = []
    full = np.linspace(0, 2 * math.pi, 73)
    mat = np.linspace(thb, tha + 2 * math.pi, 56)       # where the winding still is
    cut = np.linspace(tha, thb, 14)                     # the notch

    def add(fill3, edges, extra=None):
        ctr = sum(fill3) / len(fill3)
        faces.append((cam.dist(ctr), fill3, edges, extra))

    def cylinder(r, xl, xr, ths, open_ends, turns=0.0, col=M):
        for i, (t0, t1) in enumerate(zip(ths, ths[1:])):
            tm = (t0 + t1) / 2
            if not cam.faces(P((xl + xr) / 2, r, tm), radial(tm)):
                continue
            quad = [P(xl, r, t0), P(xr, r, t0), P(xr, r, t1), P(xl, r, t1)]
            edges = [([P(xl, r, t0), P(xl, r, t1)], LINE, col), ([P(xr, r, t0), P(xr, r, t1)], LINE, col)]
            for tt, nb in ((t0, t0 - (t1 - t0)), (t1, t1 + (t1 - t0))):
                end = open_ends and ((i == 0 and tt == t0) or (i == len(ths) - 2 and tt == t1))
                if end or not cam.faces(P((xl + xr) / 2, r, nb), radial(nb)):
                    edges.append(([P(xl, r, tt), P(xr, r, tt)], LINE, col))
            if turns:                                     # the outermost turns, hairline
                x = xl + turns / 2 + 0.006
                while x < xr - turns / 2:
                    edges.append(([P(x, r, t0), P(x, r, t1)], HAIR, G))
                    x += turns + 0.004
            add(quad, edges)

    def annulus(x, rin, rout, nx, ths, draw_in=True):
        if not cam.faces(v3(x, 0, 0), v3(nx, 0, 0)):
            return
        for t0, t1 in zip(ths, ths[1:]):
            quad = [P(x, rin, t0), P(x, rout, t0), P(x, rout, t1), P(x, rin, t1)]
            edges = [([P(x, rout, t0), P(x, rout, t1)], LINE, M)]
            if draw_in:
                edges.append(([P(x, rin, t0), P(x, rin, t1)], LINE, M))
            add(quad, edges)

    d = 0.07                                             # thread diameter
    cylinder(Rf, x0, xa, full, False)
    cylinder(Rf, xb, x1, full, False)
    cylinder(Rw, xa, xb, mat, True, turns=d)
    cylinder(Rb, xa, xb, cut, False)
    annulus(x0, Rbo, Rf, -1, full)
    annulus(x1, Rbo, Rf, 1, full)
    annulus(xa, Rw, Rf, 1, mat)
    annulus(xa, Rb, Rf, 1, cut)
    annulus(xb, Rw, Rf, -1, mat)
    annulus(xb, Rb, Rf, -1, cut)

    # the two cut faces of the winding, split along x for depth order, thread sections on them
    for th, side in ((tha, 1), (thb, -1)):
        nn = v3(0, math.sin(th), math.cos(th)) * side
        if not cam.faces(P(0, (Rb + Rw) / 2, th), nn):
            continue
        xs = np.linspace(xa, xb, 9)
        for l, r in zip(xs, xs[1:]):
            quad = [P(l, Rb, th), P(r, Rb, th), P(r, Rw, th), P(l, Rw, th)]
            edges = [([P(l, Rw, th), P(r, Rw, th)], LINE, M), ([P(l, Rb, th), P(r, Rb, th)], LINE, M)]
            circles = []
            layer, rr = 0, Rb + d / 2 + 0.004
            while rr + d / 2 <= Rw + 1e-6:
                x = xa + d / 2 + 0.006 + (d / 2) * (layer % 2)
                while x + d / 2 <= xb - 0.004:
                    if l - 1e-9 <= x < r:
                        circles.append((x, rr))
                    x += d + 0.004
                rr += d * 0.9
                layer += 1
            add(quad, edges, (th, circles, d))

    # Hidden lines by a depth buffer: rasterise every face, keep the parts of each
    # edge (and each thread section) that are at the front. Faces are black on black,
    # so only the visible lines need drawing.
    zb = DepthBuffer(cam)
    for _, fill3, _, _ in faces:
        zb.face(fill3)
    for _, fill3, edges, extra in sorted(faces, key=lambda f: -f[0]):
        if extra:
            th, circles, dd = extra
            for x, rr in circles:
                if not zb.visible(P(x, rr, th)):
                    continue
                pts = [cam(P(x + dd * 0.39 * math.cos(a), rr + dd * 0.39 * math.sin(a), th))
                       for a in np.linspace(0, 2 * math.pi, 14, endpoint=False)]
                fr.outline(pts, B, HAIR)
        for pts, w, col in edges:
            for run in zb.runs(pts):
                fr.line(run, w, col)
    # the bore through the near flange
    bore, _ = ring(v3(x0, 0, 0), v3(1, 0, 0), Rbo, 36)
    fr.outline([cam(p) for p in bore], M, LINE)
    return fr


VARIANTS = {"v1": v1, "v2": v2, "v3": v3_, "v4": v4, "v5": v5}

if __name__ == "__main__":
    s = Spool()
    for name, fn in VARIANTS.items():
        (HERE / name).mkdir(exist_ok=True)
        (HERE / name / "rest.svg").write_text(fn(s).svg())
        print("wrote", name)
