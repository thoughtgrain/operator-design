#!/usr/bin/env python3
"""Silt, subject pass 02: one rest-frame sketch per direction (v1..v5).

Run from anywhere:  python3 screens/silt/passes/02-subject/sketch.py
Writes vN/rest.svg beside this file, drawn at the definition's defaults
(settle 1.0 s, layers 16, stir 35 %, grain 0), no notes held.

Every 3D thing is modelled in world units and projected through one camera
per variant (craft.md, Think in 3D). No text below the header. Grey only.
Lines are closed ribbons; closed bodies are stroked closed outlines; every
path is one subpath of <= 64 points. Semi-opaque things are 45-degree
hatching, clipped by hand to their outline (the device has no clip-path).
"""
from __future__ import annotations

import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 480, 220
FONT = "UniversNextPro-Light"
G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
HAIR, LINE, SUBJ = 1.0, 1.5, 2.2

# ---------------------------------------------------------------- the model
DEFAULTS = {"settle": 0.5, "layers": 0.5, "stir": 0.35, "grain": 0.0}
LAYERS = [2, 4, 8, 12, 16, 24, 32, 48, 64]


def settle_s(v):
    return 0.1 * (100 ** v)


def n_partials(v):
    return LAYERS[round(v * (len(LAYERS) - 1))]


def lift(k, n):
    """How far a stir lifts partial k (high partials lift most), 0..1."""
    return ((k - 1) / max(1, n - 1)) ** 0.8


def jitter(k, seed=7):
    return random.Random(seed * 1000 + k).uniform(-1, 1)


# ------------------------------------------------------------------ camera
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    L = math.sqrt(dot(a, a))
    return (a[0] / L, a[1] / L, a[2] / L)


class Camera:
    """Pinhole camera: eye, look-at, then fitted so given key points land in a screen box."""

    def __init__(self, eye, target, up=(0, 0, 1)):
        self.eye = eye
        self.fw = norm(sub(target, eye))
        self.rt = norm(cross(self.fw, up))
        self.up = cross(self.rt, self.fw)
        self.f, self.cx, self.cy = 1.0, 0.0, 0.0

    def raw(self, p):
        d = sub(p, self.eye)
        z = dot(d, self.fw)
        return dot(d, self.rt) / z, -dot(d, self.up) / z, z

    def fit(self, pts, box):
        """Uniform scale + translate so the key points fill box (x0, y0, x1, y1), centred."""
        r = [self.raw(p) for p in pts]
        xs, ys = [q[0] for q in r], [q[1] for q in r]
        x0, y0, x1, y1 = box
        s = min((x1 - x0) / (max(xs) - min(xs)), (y1 - y0) / (max(ys) - min(ys)))
        self.f = s
        self.cx = (x0 + x1) / 2 - s * (max(xs) + min(xs)) / 2
        self.cy = (y0 + y1) / 2 - s * (max(ys) + min(ys)) / 2

    def __call__(self, p):
        x, y, _ = self.raw(p)
        return (self.cx + self.f * x, self.cy + self.f * y)

    def depth(self, p):
        return self.raw(p)[2]

    def ppu(self, p):
        """Pixels per world unit at p's depth."""
        return self.f / self.raw(p)[2]


# ------------------------------------------------------------- svg helpers
def fmt(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def dedupe(pts, closed=False):
    out = []
    for p in pts:
        p = (round(p[0], 2), round(p[1], 2))
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) >= 0.3:
            out.append(p)
    if closed and len(out) > 2 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) < 0.3:
        out.pop()
    return out


def resample(pts, maxn):
    """Thin a closed outline to at most maxn points."""
    if len(pts) <= maxn:
        return pts
    step = len(pts) / maxn
    return [pts[int(i * step)] for i in range(maxn)]


class Svg:
    def __init__(self):
        self.items: list[str] = []

    def add(self, s):
        self.items.append("  " + s)

    def ribbon(self, pts, w, fill):
        """Open polyline -> thin closed filled ribbon of width w, split every 30 segments."""
        pts = dedupe(pts)
        if len(pts) < 2:
            return
        i = 0
        while i < len(pts) - 1:
            self._ribbon(pts[i:i + 31], w, fill)
            i += 30

    def _ribbon(self, pts, w, fill):
        h = w / 2
        left, right = [], []
        n = len(pts)
        for i, (x, y) in enumerate(pts):
            if i == 0:
                dx, dy = pts[1][0] - x, pts[1][1] - y
            elif i == n - 1:
                dx, dy = x - pts[i - 1][0], y - pts[i - 1][1]
            else:
                ax, ay = x - pts[i - 1][0], y - pts[i - 1][1]
                bx, by = pts[i + 1][0] - x, pts[i + 1][1] - y
                la, lb = math.hypot(ax, ay) or 1, math.hypot(bx, by) or 1
                dx, dy = ax / la + bx / lb, ay / la + by / lb
            L = math.hypot(dx, dy) or 1
            nx, ny = -dy / L, dx / L
            m = 1.0
            if 0 < i < n - 1:
                ax, ay = x - pts[i - 1][0], y - pts[i - 1][1]
                la = math.hypot(ax, ay) or 1
                cos = abs(nx * (-ay / la) + ny * (ax / la))
                m = min(2.0, 1 / max(cos, 0.5))
            left.append((x + nx * h * m, y + ny * h * m))
            right.append((x - nx * h * m, y - ny * h * m))
        self.poly(left + right[::-1], fill=fill)

    def loop(self, pts, w, fill):
        """Closed hairline loop as a ribbon (start point repeated, so it closes visually)."""
        pts = dedupe(pts, closed=True)
        self.ribbon(pts + [pts[0]], w, fill)

    def poly(self, pts, fill="none", stroke="none", sw=LINE):
        pts = dedupe(pts, closed=True)
        seen, uniq = set(), []
        for q in pts:
            if q not in seen:
                seen.add(q)
                uniq.append(q)
        pts = uniq
        if len(pts) < 3:
            return
        pts = resample(pts, 64)
        d = "M " + " L ".join(f"{fmt(x)} {fmt(y)}" for x, y in pts) + " Z"
        sw_attr = f' stroke-width="{fmt(sw)}"' if stroke != "none" else ""
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}"{sw_attr}/>')

    def dashed(self, pts, w, fill, dash=4, gap=3):
        """Dashed polyline: each dash a short ribbon."""
        acc, on, cur = 0.0, True, [pts[0]]
        for a, b in zip(pts, pts[1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            t = 0.0
            while t < L:
                lim = dash if on else gap
                step = min(lim - acc, L - t)
                t += step
                acc += step
                p = (a[0] + (b[0] - a[0]) * t / L, a[1] + (b[1] - a[1]) * t / L)
                if on:
                    cur.append(p)
                if acc >= lim - 1e-9:
                    if on and len(cur) > 1:
                        self.ribbon(cur, w, fill)
                    on, acc, cur = not on, 0.0, [p]
        if on and len(cur) > 1:
            self.ribbon(cur, w, fill)

    def hatch(self, poly, spacing, fill, w=HAIR, minlen=2.0):
        """45-degree hairlines (rising to the right), clipped to a polygon, spacing px apart."""
        hatch_lines(self, poly, spacing, fill, w, minlen)

    def write(self, path, values):
        head = HEADER.format(*values)
        path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n'
                        f'{head}\n' + "\n".join(self.items) + "\n</svg>\n")


def hatch_lines(svg, poly, spacing, fill, w, minlen, offset=0.0):
    # lines x + y = c; perpendicular spacing s -> c step s * sqrt 2
    cs = [x + y for x, y in poly]
    step = spacing * math.sqrt(2)
    c = math.floor(min(cs) / step) * step + offset
    n = len(poly)
    while c < max(cs):
        hits = []
        for i in range(n):
            (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
            a, b = x1 + y1 - c, x2 + y2 - c
            if (a < 0) != (b < 0):
                t = a / (a - b)
                hits.append((x1 + (x2 - x1) * t, y1 + (y2 - y1) * t))
        hits.sort()
        for p, q in zip(hits[0::2], hits[1::2]):
            if math.hypot(q[0] - p[0], q[1] - p[1]) >= max(minlen, 3.0):
                svg.ribbon([p, q], w, fill)
        c += step


def hull(pts):
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in pts))
    if len(pts) < 3:
        return pts

    def half(ps):
        out = []
        for p in ps:
            while len(out) >= 2 and ((out[-1][0] - out[-2][0]) * (p[1] - out[-2][1])
                                     - (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0])) <= 0:
                out.pop()
            out.append(p)
        return out
    lo, up = half(pts), half(pts[::-1])
    return lo[:-1] + up[:-1]


HEADER = """  <g id="preview_canvas">
    <rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>
  </g>
  <g id="preview_header">
    <rect x="0" y="0" width="60" height="20" fill="#000000" stroke="none"/>
    <rect x="60" y="0" width="60" height="20" fill="#323232" stroke="none"/>
    <rect x="120" y="0" width="60" height="20" fill="#4B4B4B" stroke="none"/>
    <rect x="180" y="0" width="60" height="20" fill="#646464" stroke="none"/>
    <rect x="240" y="0" width="60" height="20" fill="#7D7D7D" stroke="none"/>
    <rect x="300" y="0" width="60" height="20" fill="#969696" stroke="none"/>
    <rect x="360" y="0" width="60" height="20" fill="#AFAFAF" stroke="none"/>
    <rect x="420" y="0" width="60" height="20" fill="#CDCDCD" stroke="none"/>
    <text transform="matrix(1 0 0 1 5 10)" fill="#CBCBCB" stroke="none" font-family="UniversNextPro-Light" font-size="10px">settle</text>
    <text transform="matrix(1 0 0 1 125 10)" fill="#CBCBCB" stroke="none" font-family="UniversNextPro-Light" font-size="10px">layers</text>
    <text transform="matrix(1 0 0 1 245 10)" fill="#000000" stroke="none" font-family="UniversNextPro-Light" font-size="10px">stir</text>
    <text transform="matrix(1 0 0 1 365 10)" fill="#000000" stroke="none" font-family="UniversNextPro-Light" font-size="10px">grain</text>
    <text transform="matrix(1 0 0 1 65 17.44)" fill="#CBCBCB" stroke="none" font-family="UniversNextPro-Light" font-size="20px">{0}</text>
    <text transform="matrix(1 0 0 1 185 17.44)" fill="#CBCBCB" stroke="none" font-family="UniversNextPro-Light" font-size="20px">{1}</text>
    <text transform="matrix(1 0 0 1 305 17.44)" fill="#000000" stroke="none" font-family="UniversNextPro-Light" font-size="20px">{2}</text>
    <text transform="matrix(1 0 0 1 425 17.44)" fill="#000000" stroke="none" font-family="UniversNextPro-Light" font-size="20px">{3}</text>
  </g>"""


def captions(c):
    s = settle_s(c["settle"])
    st = f"{s:.1f}s" if s < 10 else f"{s:.0f}s"
    return st, str(n_partials(c["layers"])), str(round(c["stir"] * 100)), str(round(c["grain"] * 100))


# ===================================================================== v1
def v1(c):
    """Exploded view of the material: one mica-like platelet per partial, flat hexagonal plates
    exploded up a slanted leader line. Stir sets the explosion gaps (high partials furthest),
    settle tilts the lifted plates (a slow settle glides, a fast one drops flat), layers is
    the plate count, grain breaks the hexagons into coarse chipped grains off the line."""
    s = Svg()
    n, stir, grain, sn = n_partials(c["layers"]), c["stir"], c["grain"], c["settle"]
    rad = [1.0 * k ** -0.32 for k in range(1, n + 1)]
    thick = [0.07 * r + 0.035 for r in rad]
    z, zs = 0.0, []
    for k in range(1, n + 1):
        zs.append(z)
        gap = (0.02 + stir * 1.25 * lift(k + 1, n)) * 16 / max(n, 8)
        z += thick[k - 1] + gap
    slope = 1.25  # leader line runs up and downstream
    plates = []
    for k in range(1, n + 1):
        r, t, z0 = rad[k - 1], thick[k - 1], zs[k - 1]
        rng = random.Random(31 * k)
        phi = rng.uniform(0, math.pi / 3)
        off = grain * 0.45 * r * jitter(k, 3)
        ctr = (slope * z0 + off, grain * 0.3 * r * jitter(k, 5), z0)
        tilt = math.radians(26) * sn * lift(k, n) * (1 if k % 2 else -0.7)
        ax = rng.uniform(0, math.pi)
        verts = []
        m = 6 + (int(grain * 4 + 0.5) if grain > 0 else 0)
        for i in range(m):
            a = phi + i * 2 * math.pi / m
            rr = r * (1 + grain * 0.35 * random.Random(97 * k + i).uniform(-1, 1))
            verts.append((rr * math.cos(a), rr * math.sin(a)))
        def place(px, py, pz):
            # tilt about a horizontal axis through the centre
            ca, sa = math.cos(ax), math.sin(ax)
            u, v = px * ca + py * sa, -px * sa + py * ca
            v, pz = v * math.cos(tilt) - pz * math.sin(tilt), v * math.sin(tilt) + pz * math.cos(tilt)
            px, py = u * ca - v * sa, u * sa + v * ca
            return (ctr[0] + px, ctr[1] + py, ctr[2] + pz)
        top = [place(x, y, t) for x, y in verts]
        bot = [place(x, y, 0) for x, y in verts]
        plates.append((k, r, top, bot, place(0, 0, t)))
    cam = Camera(eye=(slope * z * 0.35, -9.0, z * 0.5 + 6.5), target=(slope * z * 0.5, 0, z * 0.5))
    key = [p for (_, _, top, bot, _) in plates for p in top + bot]
    cam.fit(key, (56, 34, 424, 200))
    # leader line through the centres, behind every plate (exploded-view convention)
    a = cam((plates[0][4][0] - 0.0, 0, -0.35))
    b = cam((slope * (zs[-1] + 0.5), 0, zs[-1] + 0.5))
    s.dashed([a, b], HAIR, G3, dash=5, gap=4)
    for idx, (k, r, top, bot, ctop) in enumerate(plates):
        T = [cam(p) for p in top]
        B = [cam(p) for p in bot]
        outline = hull(T + B)
        bright = idx == len(plates) - 1
        s.poly(outline, fill=G0, stroke=G7 if bright else G5, sw=SUBJ if bright else LINE)
        rs = r * cam.ppu(ctop)
        if rs >= 6:
            s.loop(T, HAIR, G6 if bright else G4)
            # vertical edges on the front: top vertex below the face centre
            cy = sum(p[1] for p in T) / len(T)
            for p, q in zip(T, B):
                if p[1] > cy and math.hypot(q[0] - p[0], q[1] - p[1]) >= 3:
                    s.ribbon([p, q], HAIR, G4)
        # growth steps on the face: inner structure, kept >= 3 px from the edge
        for f in (0.55, 0.28):
            if rs * (1 - f) * 0.45 >= 3.5 and rs * f >= 5:
                ctr = cam(ctop)
                inner = [(ctr[0] + (p[0] - ctr[0]) * f, ctr[1] + (p[1] - ctr[1]) * f) for p in T]
                s.loop(inner, HAIR, G3)
    return s


# ===================================================================== v2
def v2(c):
    """A pebble has just dropped into a still, shallow stream; a plume of silt curls up off
    the bed where it landed and leans away downstream. Single-weight contour."""
    s = Svg()
    n, stir, grain, sn = n_partials(c["layers"]), c["stir"], c["grain"], c["settle"]
    WS = 1.55                      # water surface height
    cam = Camera(eye=(0.6, -7.0, 2.5), target=(0.6, 0, 0.8))
    cam.fit([(-2.4, 0, 0), (3.6, 0, 0), (0.6, 0, WS + 0.05), (0.6, 0, -0.2)], (0, 34, 480, 206))
    rng = random.Random(4)

    def bed_z(x, y=0.0):
        return 0.07 * math.sin(1.3 * x + 0.4) + 0.04 * math.sin(3.1 * x + 1.2 * y) - 0.02 * y

    # far bank (back of the stream bed), then the near bed profile
    far = [cam((x / 10, 3.2, bed_z(x / 10, 3.2) + 0.55 + 0.12 * math.sin(x / 10 * 0.9))) for x in range(-60, 75)]
    s.ribbon(far, LINE, G2)
    # water surface: a straight line broken where the rings sit, rings centred above the pebble
    sx = 0.0
    lo, hi = cam((sx - 1.05, 0, WS)), cam((sx + 1.05, 0, WS))
    s.ribbon([cam((-6, 0, WS)), (lo[0] - 4, lo[1])], LINE, G4)
    s.ribbon([(hi[0] + 4, hi[1]), cam((8, 0, WS))], LINE, G4)
    for rr in (0.35, 0.68, 1.0):
        ring = [cam((sx + rr * math.cos(a / 40 * 2 * math.pi), rr * math.sin(a / 40 * 2 * math.pi), WS)) for a in range(40)]
        s.poly(ring, fill="none", stroke=G4, sw=LINE)
    # plume: one curl per partial, in the vertical plane through the pebble
    lean = math.radians(4 + 36 * sn)
    circles = []
    for k in range(1, n + 1):
        L = lift(k, n)
        h = 0.28 + stir * 2.1 * L + 0.05 * L
        h = min(h, WS - 0.18)
        x = sx + (h - 0.25) * math.tan(lean) + grain * 0.35 * jitter(k, 11)
        zc = h + grain * 0.12 * jitter(k, 13)
        rho = 0.14 + 0.2 * L ** 0.7
        circles.append((x, zc, rho))
    ctr = (sum(c_[0] for c_ in circles) / n, sum(c_[1] for c_ in circles) / n)
    outline = []
    for i in range(60):
        th = i / 60 * 2 * math.pi
        u = (math.cos(th), math.sin(th))
        best = 0.05
        for (x, zc, rho) in circles:
            dx, dz = x - ctr[0], zc - ctr[1]
            proj = dx * u[0] + dz * u[1]
            perp2 = dx * dx + dz * dz - proj * proj
            if perp2 <= rho * rho:
                best = max(best, proj + math.sqrt(rho * rho - perp2))
        outline.append(cam((ctr[0] + best * u[0], 0, ctr[1] + best * u[1])))
    # near bed profile, the pebble on it
    bed = [cam((x / 10, 0, bed_z(x / 10))) for x in range(-60, 80)]
    s.ribbon(bed, LINE, G5)
    s.poly(outline, fill=G0, stroke=G7, sw=LINE)
    # the curls inside: a three-quarter turn each, one per partial
    for (x, zc, rho) in circles:
        rs = rho * cam.ppu((x, 0, zc)) * 0.5
        if rs < 2.6:
            continue
        p0 = cam((x, 0, zc))
        a0 = rng.uniform(0, 2 * math.pi)
        pts = []
        for j in range(18):
            t = j / 17
            a = a0 + t * 1.5 * math.pi
            rr = rs * (0.45 + 0.55 * t)
            pts.append((p0[0] + rr * math.cos(a), p0[1] + rr * math.sin(a)))
        s.ribbon(pts, LINE, G5)
    peb = []
    for i in range(36):
        a = i / 36 * 2 * math.pi
        rr = 1 + 0.06 * math.sin(3 * a + 1) + 0.04 * math.sin(5 * a)
        peb.append(cam((sx + 0.42 * rr * math.cos(a), 0, bed_z(sx) + 0.13 + 0.17 * rr * math.sin(a))))
    s.poly(peb, fill=G0, stroke=G5, sw=LINE)
    return s


# ===================================================================== v3
def v3(c):
    """A snow globe of silt, the rule as a toy: shake it and the flakes lift, then sink.
    Masses drawn as hatching: the drift on the floor dense, the suspended cloud sparse with
    one hatch line per partial; the cloud's lifted top edge is the bright line."""
    s = Svg()
    n, stir, grain, sn = n_partials(c["layers"]), c["stir"], c["grain"], c["settle"]
    R, rb = 1.0, 0.78
    zc = math.sqrt(R * R - rb * rb)
    cam = Camera(eye=(0, -7.5, 2.4), target=(0, 0, 0.55))
    cam.fit([(-R, 0, zc), (R, 0, zc), (0, 0, zc + R), (0, -1.0, -0.62), (-1.02, 0, -0.62), (1.02, 0, -0.62)],
            (150, 32, 330, 208))
    C = cam((0, 0, zc))
    rpx = R * cam.ppu((0, 0, zc)) * 1.003
    sphere = [(C[0] + rpx * math.cos(a / 64 * 2 * math.pi), C[1] + rpx * math.sin(a / 64 * 2 * math.pi)) for a in range(64)]
    s.poly(sphere, fill=G0, stroke=G5, sw=LINE)
    # interior is drawn in the y=0 plane, inside an inner radius (the glass has thickness)
    Ri = 0.9
    floor = 0.08

    def inside_x(zz):
        d = Ri * Ri - (zz - zc) ** 2
        return math.sqrt(max(d, 0))

    def drift(x):
        w = inside_x(floor) * 0.98
        return floor + 0.2 * max(0.0, 1 - (x / w) ** 2) ** 0.8
    w0 = inside_x(floor) * 0.98
    xs = [-w0 + 2 * w0 * i / 40 for i in range(41)]
    drift_top = [cam((x, 0, drift(x))) for x in xs]
    drift_poly = drift_top + [cam((w0, 0, floor)), cam((0, 0, floor - 0.04)), cam((-w0, 0, floor))]
    # suspended cloud: bottom hangs above the drift by the settle time, top lifted by stir
    hang = 0.06 + 0.42 * sn
    rng = random.Random(9)
    top_pts, bot_pts = [], []
    xs2 = [-0.82 + 1.64 * i / 44 for i in range(45)]
    for i, x in enumerate(xs2):
        zb = drift(max(min(x, w0), -w0)) + hang
        u = (x + 0.82) / 1.64
        bulge = math.sin(math.pi * u) ** 0.7
        zt = zb + 0.02 + 0.12 * bulge + stir * 1.05 * bulge * (0.75 + 0.25 * math.sin(7 * u + 1))
        zt += grain * 0.12 * random.Random(50 + i).uniform(-1, 1)
        lim_t = zc + math.sqrt(max(Ri * Ri - x * x, 0)) - 0.04
        lim_b = zc - math.sqrt(max(Ri * Ri - x * x, 0)) + 0.04
        zt, zb = min(zt, lim_t), max(zb, lim_b)
        if zt - zb > 0.03:
            top_pts.append((x, zt))
            bot_pts.append((x, zb))
    cloud = [cam((x, 0, z)) for x, z in top_pts] + [cam((x, 0, z)) for x, z in bot_pts[::-1]]
    # hatch the cloud with exactly n lines across its extent (count = layers), >= 3.2 px apart
    cs = [x + y for x, y in cloud]
    span = (max(cs) - min(cs)) / math.sqrt(2)
    sp = max(3.2, span / (n + 1))
    hatch_lines(s, cloud, sp, G4, HAIR, 2.0, offset=(span - sp * min(n, int(span / sp))) / 2 * 0)
    # drift: dense hatching, a solid mass
    s.poly(drift_poly, fill=G0, stroke=G4, sw=LINE)
    hatch_lines(s, drift_poly, 3.2, G3, HAIR, 2.0)
    # the lifted top edge is the subject
    s.ribbon([cam((x, 0, z)) for x, z in top_pts], SUBJ, G7)
    # coarse flakes falling out under the cloud (grain), none at 0
    if grain > 0:
        for k in range(1, 7):
            x = -0.6 + 1.2 * random.Random(70 + k).random()
            zz = drift(x) + hang * random.Random(80 + k).random()
            p = cam((x, 0, zz))
            r = 1.5 + 3.5 * grain
            s.poly([(p[0], p[1] - r), (p[0] + r, p[1]), (p[0], p[1] + r), (p[0] - r, p[1])], fill=G0, stroke=G5, sw=LINE)
    # glass highlight: a hairline arc upper left, inner structure of the sphere
    arc = [(C[0] + rpx * 0.82 * math.cos(math.radians(a)), C[1] + rpx * 0.82 * math.sin(math.radians(a))) for a in range(200, 246, 3)]
    s.ribbon(arc, HAIR, G4)
    # base: a frustum, solid, hatched mass with its top rim
    zt_, zb_ = 0.0, -0.62
    r_t, r_b = 0.86, 1.02
    ring_t = [cam((r_t * math.cos(a / 48 * 2 * math.pi), r_t * math.sin(a / 48 * 2 * math.pi), zt_)) for a in range(48)]
    ring_b = [cam((r_b * math.cos(a / 48 * 2 * math.pi), r_b * math.sin(a / 48 * 2 * math.pi), zb_)) for a in range(48)]
    front_t = [p for i, p in enumerate(ring_t) if math.sin(i / 48 * 2 * math.pi) <= 0.02]
    body = hull([p for i, p in enumerate(ring_b) if math.sin(i / 48 * 2 * math.pi) <= 0]
                + [cam((-r_t, 0, zt_)), cam((r_t, 0, zt_))])
    # base outline: front half of the bottom ring + the top ring's front half
    lower = sorted([p for i, p in enumerate(ring_b) if math.sin(i / 48 * 2 * math.pi) <= 0], key=lambda p: p[0])
    upper = sorted(front_t, key=lambda p: p[0])
    base_poly = [cam((-r_b, 0, zb_))] + lower + [cam((r_b, 0, zb_)), cam((r_t, 0, zt_))] + upper[::-1] + [cam((-r_t, 0, zt_))]
    base_poly = [cam((-r_t, 0, zt_)), cam((-r_b, 0, zb_))] + lower + [cam((r_b, 0, zb_)), cam((r_t, 0, zt_))] + upper[::-1]
    s.poly(base_poly, fill=G0, stroke=G5, sw=LINE)
    hatch_lines(s, base_poly, 4.0, G3, HAIR, 2.0)
    # a band groove round the base (inner structure)
    band = sorted([cam((0.93 * math.cos(a / 48 * 2 * math.pi), 0.93 * math.sin(a / 48 * 2 * math.pi), -0.3))
                   for a in range(48) if math.sin(a / 48 * 2 * math.pi) <= 0], key=lambda p: p[0])
    s.ribbon(band, LINE, G4)
    return s


# ===================================================================== v4
def v4(c):
    """A prospector's pan cut in half at work: the swirl tips the water up one wall, the
    fines ride up in it, the heavy grains stay in the crease. Edge-lit silhouette: dark
    bodies, a light rim on their upper edge; the water is hatched; the tilted waterline is
    the bright line."""
    s = Svg()
    n, stir, grain, sn = n_partials(c["layers"]), c["stir"], c["grain"], c["settle"]
    rb, rt, dep, wall = 0.8, 1.7, 0.85, 0.07
    cam = Camera(eye=(0, -7.5, 2.2), target=(0, 0.3, 0.3))
    cam.fit([(-rt - 0.1, 0, dep), (rt + 0.1, 0, dep), (0, rt, dep + 0.02), (0, 0, -wall - 0.02),
             (-rt - 0.1, 0, -0.05), (rt + 0.1, 0, -0.05)], (50, 44, 430, 204))

    def ring(r, z, a0, a1, m=40):
        return [cam((r * math.cos(a), r * math.sin(a), z)) for a in
                [a0 + (a1 - a0) * i / (m - 1) for i in range(m)]]
    # back half of the pan, inside: rim, bottom, and the riffles on the back wall
    back_rim = ring(rt, dep, 0, math.pi)
    back_bot = ring(rb, 0, 0, math.pi)
    inner = back_rim + back_bot[::-1]
    s.poly(inner, fill=G0, stroke="none")
    # outer back rim lip (a thin solid body lit on top)
    s.ribbon(ring(rt + wall, dep, 0, math.pi, 48), LINE, G5)
    for f in (0.62, 0.74, 0.86):
        rr, zz = rb + (rt - rb) * f, dep * f
        s.ribbon(ring(rr, zz, 0.12, math.pi - 0.12), HAIR, G3)
    s.ribbon(back_bot, HAIR, G3)
    # water: tilted plane through the axis; stir sets its angle
    ang = math.radians(4 + 34 * stir)
    zw = 0.4

    def water_z(x):
        return zw + math.tan(ang) * x

    def wall_x(z, side):
        return side * (rb + (rt - rb) * z / dep)
    # section of the interior in y=0, below the waterline
    prof = []
    xl = None
    for i in range(41):  # left wall, bottom, right wall
        pass
    zl = zw - math.tan(ang) * rb
    # left intersection: water_z(x) = z on left wall x = -(rb + (rt-rb) z/dep)
    k = (rt - rb) / dep
    zl = (zw - math.tan(ang) * rb) / (1 + math.tan(ang) * k)
    zr = min(dep - 0.02, (zw + math.tan(ang) * rb) / (1 - math.tan(ang) * k))
    xl, xr = wall_x(zl, -1), wall_x(zr, 1)
    sec = [(xl, zl), (-rb, 0.0), (rb, 0.0), (xr, zr)]
    water = [cam((x, 0, z)) for x, z in sec]
    # waterline on the back wall: where the tilted plane meets the cone, back half
    back_wl = []
    for i in range(41):
        a = i / 40 * math.pi
        # solve r(z) = rb + k z, z = zw + tan(ang) * r cos a
        cosa = math.cos(a)
        z = (zw + math.tan(ang) * rb * cosa) / (1 - math.tan(ang) * k * cosa)
        z = min(max(z, 0.0), dep)
        r = rb + k * z
        back_wl.append(cam((r * cosa, r * math.sin(a), z)))
    surf = [cam((x, 0, z)) for x, z in sec[:1]] + back_wl[::-1][1:-1] + [cam((xr, 0, zr))]
    # water region seen: section polygon plus the visible surface sheet behind it, hatched
    sheet = [cam((xl, 0, zl))] + back_wl[::-1] + [cam((xr, 0, zr))]
    s.ribbon(back_wl, HAIR, G4)
    hatch_lines(s, water, 4.0, G3, HAIR, 2.0)
    # particles in the section plane: heavy (low partials) in the crease, fines lifted up
    # the high side of the swirl; settle sets how high the fines still hang
    for kk in range(1, n + 1):
        L = lift(kk, n)
        u = (kk - 1) / max(1, n - 1)
        x = -0.5 + 1.3 * u + 0.08 * jitter(kk, 2)
        x = min(x, xr - 0.25)
        ztop = water_z(x) - 0.06
        z = 0.04 + (ztop - 0.04) * L * (0.25 + 0.75 * sn) * (0.85 + 0.15 * jitter(kk, 4))
        z = max(0.045, min(z, ztop))
        size = (0.1 * (1 - L) + 0.045) * (1 + 1.4 * grain)
        p = cam((x, 0, z + size * 0.6))
        rpx = max(3.0, size * cam.ppu((x, 0, z)))
        rng = random.Random(400 + kk)
        pts = [(p[0] + rpx * (1 + 0.25 * rng.uniform(-1, 1)) * math.cos(a / 7 * 2 * math.pi),
                p[1] + rpx * 0.75 * (1 + 0.25 * rng.uniform(-1, 1)) * math.sin(a / 7 * 2 * math.pi)) for a in range(7)]
        s.poly(pts, fill=G0, stroke="none")
        # rim light: the upper-left edge only
        rim = [(p[0] + rpx * math.cos(math.radians(a)), p[1] + rpx * 0.75 * math.sin(math.radians(a))) for a in range(170, 300, 20)]
        s.ribbon(rim, LINE, G5)
    # the cut wall: a solid section, dark body with a lit inner edge
    for side in (-1, 1):
        out_pts = [(side * (rb + wall), -wall), (side * (rt + wall), dep), (side * rt, dep), (side * rb, 0.0)]
        s.poly([cam((x, 0, z)) for x, z in out_pts], fill=G1, stroke="none")
        s.ribbon([cam((side * rt, 0, dep)), cam((side * rb, 0, 0))], LINE, G5)
    s.poly([cam((x, 0, z)) for x, z in [(-rb - wall, -wall), (rb + wall, -wall), (rb, 0), (-rb, 0)]], fill=G1, stroke="none")
    s.ribbon([cam((-rb, 0, 0)), cam((rb, 0, 0))], LINE, G5)
    # outer underside of the front rim: hairline to close the section
    s.ribbon([cam((-rt - wall, 0, dep)), cam((-rb - wall, 0, -wall)), cam((rb + wall, 0, -wall)), cam((rt + wall, 0, dep))], HAIR, G3)
    # the waterline in the cut: the subject
    s.ribbon([cam((xl, 0, zl)), cam((xr, 0, zr))], SUBJ, G7)
    return s


# ===================================================================== v5
def v5(c):
    """A slab of rippled silt, lifted out after the water has gone: the ripples are what each
    stir-and-settle left behind. Detailed line art: crests and troughs on the top, the
    cross-laminae of migrating ripples in the cut face, mud drapes hatched in the troughs."""
    s = Svg()
    n, stir, grain, sn = n_partials(c["layers"]), c["stir"], c["grain"], c["settle"]
    Lx, Ly, T = 4.2, 1.5, 0.42
    m = max(2, n // 2)
    lam = Lx / m
    A = 0.05 + stir * 0.24
    asym = 0.72

    def phase_u(u, v):
        d = grain * 0.32 * lam * (math.sin(2 * math.pi * v / Ly * 1.3 + u * 2.1) + 0.5 * math.sin(5.1 * v + 3 * u))
        return ((u + d) / lam) % 1.0

    def prof(p):
        # stoss rises gently to the crest at asym, lee drops steeply
        if p < asym:
            return 0.5 - 0.5 * math.cos(math.pi * p / asym)
        return 0.5 + 0.5 * math.cos(math.pi * (p - asym) / (1 - asym))

    def top(u, v):
        return T + A * prof(phase_u(u, v))
    cam = Camera(eye=(-1.6, -6.2, 4.4), target=(Lx * 0.5, Ly * 0.5, 0.2))
    cam.fit([(0, 0, 0), (Lx, 0, 0), (Lx, Ly, 0), (0, Ly, T + A), (Lx, Ly, T + A), (0, 0, T + A)], (40, 40, 440, 206))
    us = [Lx * i / 160 for i in range(161)]
    vs = [Ly * i / 30 for i in range(31)]
    front_top = [cam((u, 0, top(u, 0))) for u in us]
    back_top = [cam((u, Ly, top(u, Ly))) for u in us]
    right_top = [cam((Lx, v, top(Lx, v))) for v in vs]
    left_top = [cam((0, v, top(0, v))) for v in vs]
    # top surface (black body), outline at Line weight
    surf = front_top + right_top + back_top[::-1] + left_top[::-1]
    s.poly(surf, fill=G0, stroke="none")
    for edge in (back_top, left_top):
        s.ribbon(edge, LINE, G5)
    # mud drapes in the troughs: hatched strips, wider for a quick settle
    dw = lam * (0.06 + 0.22 * (1 - sn))
    for j in range(m + 1):
        ut = j * lam
        strip_a, strip_b = [], []
        for v in vs:
            d = grain * 0.32 * lam * (math.sin(2 * math.pi * v / Ly * 1.3 + ut * 2.1) + 0.5 * math.sin(5.1 * v + 3 * ut))
            u0, u1 = ut - d - dw / 2, ut - d + dw / 2
            if u1 <= 0.02 or u0 >= Lx - 0.02:
                continue
            u0, u1 = max(u0, 0.02), min(u1, Lx - 0.02)
            strip_a.append(cam((u0, v, T + 0.004)))
            strip_b.append(cam((u1, v, T + 0.004)))
        if len(strip_a) > 3:
            hatch_lines(s, strip_a + strip_b[::-1], 3.2, G3, HAIR, 1.5)
    # crest lines: one hairline per ripple
    for j in range(m):
        uc = (j + asym) * lam
        pts = []
        for v in vs:
            d = grain * 0.32 * lam * (math.sin(2 * math.pi * v / Ly * 1.3 + uc * 2.1) + 0.5 * math.sin(5.1 * v + 3 * uc))
            u = uc - d
            if 0.01 < u < Lx - 0.01:
                pts.append(cam((u, v, T + A)))
        if len(pts) > 1:
            s.ribbon(pts, HAIR, G5)
    # front face: the cut, with cross-laminae (foresets parallel to each lee)
    face = [cam((0, 0, 0)), cam((Lx, 0, 0))] + [p for p in front_top[::-1]]
    s.poly(face, fill=G0, stroke=G5, sw=LINE)
    lee = (1 - asym) * lam
    ppu = cam.ppu((Lx / 2, 0, T))
    for j in range(m):
        uc = (j + asym) * lam
        for q in (0.35, 0.75):
            # a foreset: from crest-ish down the lee slope, tucked into the ripple below
            x0 = uc - q * lam * 0.9
            zt = T + A * prof(phase_u(x0, 0)) - 0.03
            x1 = x0 + lee * 1.3
            zb = T - A * 0.9 - 0.05
            if x0 < 0.03 or x1 > Lx - 0.03 or (zt - zb) * ppu < 4:
                continue
            seg = [cam((x0 + (x1 - x0) * t / 6, 0, zt + (zb - zt) * (t / 6) ** 0.8)) for t in range(7)]
            s.ribbon(seg, HAIR, G3)
    # bounding set (the base of the ripple set) and the slab's right end face
    s.ribbon([cam((0.03, 0, T - A * 0.9 - 0.08)), cam((Lx - 0.03, 0, T - A * 0.9 - 0.08))], HAIR, G2)
    endf = [cam((Lx, 0, 0)), cam((Lx, Ly, 0))] + right_top[::-1]
    s.poly(endf, fill=G0, stroke=G5, sw=LINE)
    # the front ripple profile: the trace itself, brightest
    s.ribbon(front_top, SUBJ, G7)
    return s


def main():
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        d = HERE / name
        d.mkdir(exist_ok=True)
        fn(DEFAULTS).write(d / "rest.svg", captions(DEFAULTS))


if __name__ == "__main__":
    main()
