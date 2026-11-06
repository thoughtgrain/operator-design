#!/usr/bin/env python3
"""Nave, subject pass 01: one rest-frame sketch per direction (v1..v5).

Run from anywhere:  python3 screens/nave/passes/01-subject/sketch.py
Writes vN/rest.svg beside this file, every frame at the definition's defaults
(nave 2.2 s, stone 50 %, choir 60 %, doors 20 ms), no notes held.

Lines are closed filled ribbons, closed contours are stroked closed outlines,
every path is one subpath of <= 64 points. Grey only, never red.
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

# ---------------------------------------------------------------- the model
DEFAULTS = {"nave": 0.5, "stone": 0.5, "choir": 0.6, "doors": 0.2828}


def rt60(v):            # exponential 0.4 .. 12 s
    return 0.4 * (30 ** v)


def predelay(v):        # power, exponent 2, 0 .. 250 ms
    return 0.25 * v * v


def hf_ratio(stone):    # how long the highs last against the broadband tail
    return 0.2 + 0.75 * stone


def captions(c):
    r = rt60(c["nave"])
    nave = f"{r:.1f}s" if r < 10 else f"{r:.0f}s"
    return nave, str(round(c["stone"] * 100)), str(round(c["choir"] * 100)), f"{round(predelay(c['doors']) * 1000)}ms"


# ------------------------------------------------------------- svg helpers
def f(v):
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


class Svg:
    def __init__(self):
        self.items: list[str] = []

    def add(self, s):
        self.items.append("  " + s)

    def poly(self, pts, fill="none", stroke="none", sw=1.0):
        pts = dedupe(pts, closed=True)
        if len(pts) < 3:
            return
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
        sw_attr = f' stroke-width="{f(sw)}"' if stroke != "none" else ""
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}"{sw_attr}/>')

    def ribbon(self, pts, w, fill):
        """Open polyline -> closed filled ribbon of width w, split into <= 31-point runs."""
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

    def line(self, x1, y1, x2, y2, w, fill):
        self._ribbon([(x1, y1), (x2, y2)], w, fill)

    def dashed(self, x1, y1, x2, y2, w, fill, dash=4, gap=3):
        L = math.hypot(x2 - x1, y2 - y1)
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        t = 0.0
        while t < L:
            e = min(L, t + dash)
            if e - t > 0.8:
                self.line(x1 + ux * t, y1 + uy * t, x1 + ux * e, y1 + uy * e, w, fill)
            t += dash + gap

    def rect(self, x, y, w, h, fill="none", stroke="none", sw=1.0):
        sw_attr = f' stroke-width="{f(sw)}"' if stroke != "none" else ""
        self.add(f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" fill="{fill}" stroke="{stroke}"{sw_attr}/>')

    def circle(self, cx, cy, r, fill, stroke="none", sw=1.0):
        sw_attr = f' stroke-width="{f(sw)}"' if stroke != "none" else ""
        self.add(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}" stroke="{stroke}"{sw_attr}/>')

    def text(self, x, y, s, fill=G4, size=10):
        self.add(f'<text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{fill}" stroke="none" '
                 f'font-family="{FONT}" font-size="{size}px">{s}</text>')

    def write(self, path, c):
        head = HEADER.format(*captions(c))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n'
                        f'{head}\n' + "\n".join(self.items) + "\n</svg>\n")


def arc(cx, cy, r, a0, a1, n=16):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / (n - 1))),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / (n - 1)))) for i in range(n)]


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
    <text transform="matrix(1 0 0 1 5 10)" fill="#CBCBCB" stroke="none" font-family="UniversNextPro-Light" font-size="10px">nave</text>
    <text transform="matrix(1 0 0 1 125 10)" fill="#CBCBCB" stroke="none" font-family="UniversNextPro-Light" font-size="10px">stone</text>
    <text transform="matrix(1 0 0 1 245 10)" fill="#000000" stroke="none" font-family="UniversNextPro-Light" font-size="10px">choir</text>
    <text transform="matrix(1 0 0 1 365 10)" fill="#000000" stroke="none" font-family="UniversNextPro-Light" font-size="10px">doors</text>
    <text transform="matrix(1 0 0 1 65 17.44)" fill="#CBCBCB" stroke="none" font-family="UniversNextPro-Light" font-size="20px">{0}</text>
    <text transform="matrix(1 0 0 1 185 17.44)" fill="#CBCBCB" stroke="none" font-family="UniversNextPro-Light" font-size="20px">{1}</text>
    <text transform="matrix(1 0 0 1 305 17.44)" fill="#000000" stroke="none" font-family="UniversNextPro-Light" font-size="20px">{2}</text>
    <text transform="matrix(1 0 0 1 425 17.44)" fill="#000000" stroke="none" font-family="UniversNextPro-Light" font-size="20px">{3}</text>
  </g>"""


# ------------------------------------------------------------------ v1
def v1(c):
    """P1 Section drawing, survey plan: the church cut at sill height, seen from above.

    nave  -> the east end (apse) moves east, bays are added behind it (position + count)
    stone -> a sound ray from the west door bounces between the walls; harder stone,
             more bounces survive (count of ray segments)
    choir -> the choir screen moves west, lengthening the stalls (position)
    doors -> the west porch lengthens, pushing the doors away from the nave (position)
    """
    s = Svg()
    yn, ys = 78, 170                     # inner faces of the north and south walls
    yc = (yn + ys) / 2
    xw = 112                              # west wall of the nave (inner face)
    xe = xw + 120 + 170 * c["nave"]       # chord of the apse
    porch = 12 + 70 * c["doors"]          # porch length
    wall = 6
    # --- walls (poché, the brightest mass: the cut)
    s.rect(xw, yn - wall, xe - xw, wall, fill=G7)
    s.rect(xw, ys, xe - xw, wall, fill=G7)
    # west wall with the door opening
    door = 22
    s.rect(xw - wall, yn - wall, wall, (yc - door / 2) - (yn - wall), fill=G7)
    s.rect(xw - wall, yc + door / 2, wall, (ys + wall) - (yc + door / 2), fill=G7)
    # apse: half ring of radius (ys-yn)/2
    r = (ys - yn) / 2
    outer = arc(xe, yc, r + wall, -90, 90, 30)
    inner = arc(xe, yc, r, 90, -90, 30)
    s.poly(outer + inner, fill=G7)
    # porch (narthex), thinner walls, open to the west
    py0, py1 = yc - 24, yc + 24
    s.rect(xw - wall - porch, py0 - 3, porch, 3, fill=G6)
    s.rect(xw - wall - porch, py1, porch, 3, fill=G6)
    # porch doors: two leaves with their swing arcs (survey convention)
    xd = xw - wall - porch
    s.rect(xd - 3, py0 - 3, 3, 12, fill=G6)
    s.rect(xd - 3, py1 - 9, 3, 12, fill=G6)
    for sign in (-1, 1):
        hinge_y = yc + sign * 15
        s.line(xd, hinge_y, xd + 15, hinge_y, 1.2, G5)
        s.ribbon(arc(xd, hinge_y, 15, 0 if sign > 0 else 0, -90 * sign, 10), 1, G3)
    # --- piers: two arcade rows, one per bay
    bay = 28
    nb = int((xe - xw - 10) // bay)
    for i in range(1, nb + 1):
        x = xw + i * bay - bay / 2 + 4
        if x > xe - 8:
            break
        for y in (yn + 20, ys - 20):
            s.rect(x - 3, y - 3, 6, 6, fill=G5)
    # bay numbers along the top, survey style
    for i in range(1, nb + 1):
        x = xw + i * bay - bay / 2 + 4
        if x > xe - 8:
            break
        s.text(x - 3, yn - 14, str(i), fill=G4, size=10)
    # centre line (dashed axis)
    s.dashed(xd - 18, yc, xe + r + wall + 14, yc, 1, G2, dash=8, gap=4)
    # --- choir: screen and stalls
    xs = xe - 24 - 90 * c["choir"]
    s.rect(xs - 2, yn + 26, 4, 14, fill=G5)
    s.rect(xs - 2, ys - 40, 4, 14, fill=G5)
    for k in range(3):
        y1 = yn + 4 + k * 5
        y2 = ys - 4 - k * 5
        s.line(xs + 4, y1, xe - 4, y1, 1, G3)
        s.line(xs + 4, y2, xe - 4, y2, 1, G3)
    # --- stone: a sound ray from the door, bouncing between the walls
    bounces = 2 + round(12 * c["stone"])
    x, y = xw + 2, yc
    dx, dy = 23.0, -46.0                     # first leg to the north wall
    pts = [(x, y)]
    left, right = xw + 4, xe - 4
    for b in range(bounces):
        ty = (yn + 3) if dy < 0 else (ys - 3)
        t = (ty - y) / dy
        nx = x + dx * t
        if nx > right:
            nx = right - (nx - right)
            dx = -dx
        x, y = nx, ty
        pts.append((x, y))
        dy = -dy
        dy = dy / abs(dy) * (ys - yn - 6)
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        shade = G5 if i < bounces * 0.5 else G4
        s.line(a[0], a[1], b[0], b[1], 1.2, shade)
    # --- labels
    s.text(xw + 6, ys + 22, "nave", fill=G4)
    s.text(xs + 6, ys + 22, "choir", fill=G4)
    s.text(xd - 4, py1 + 18, "porch", fill=G4)
    # scale bar
    x0, y0 = 20, 204
    for k in range(4):
        s.rect(x0 + k * 12, y0, 12, 3, fill=G5 if k % 2 == 0 else G2)
    s.text(x0 + 52, y0 + 5, "10 m", fill=G4)
    return s


# ------------------------------------------------------------------ v2
def v2(c):
    """P2 Diagram + trace, patent section.

    Left, fig. 1: the nave cut lengthwise. nave -> east end and bays (position + count);
    choir -> the sound arrow from the door fans into more scattered arrows (count).
    Right, fig. 2: the impulse response. doors -> the gap between the direct
    impulse and the first reflection (position); stone -> the treble envelope line
    over the reflections (shape).
    """
    s = Svg()
    # ---------------- fig. 1: longitudinal section
    floor = 176
    x0 = 26
    length = 110 + 90 * c["nave"]
    xe = x0 + length
    spring, apex, vault = 118, 98, 62
    # hatched section cut: floor slab
    s.rect(x0 - 8, floor, length + 30, 3, fill=G6)
    for k in range(int((length + 30) // 6)):
        xx = x0 - 6 + k * 6
        s.line(xx, floor + 4, xx - 5, floor + 10, 1, G3)
    # west wall in section, with the door opening at the bottom
    s.rect(x0 - 8, vault, 8, (floor - 30) - vault, fill=G6)
    # vault: a pointed barrel seen cut, drawn as its intrados line + extrados
    s.ribbon([(x0, vault + 4), (xe, vault + 4)], 2, G7)
    s.ribbon([(x0 - 8, vault - 4), (xe + 6, vault - 4)], 1.2, G5)
    for k in range(int(length // 8)):
        xx = x0 + 2 + k * 8
        s.line(xx, vault - 3, xx + 4, vault + 2, 1, G3)
    # arcade: piers and pointed arches, one per bay
    bay = 26
    nb = max(1, int((length - 6) // bay))
    for i in range(nb):
        a = x0 + 4 + i * bay
        b = a + bay
        s.rect(a, spring, 4, floor - spring, fill=G1, stroke=G5, sw=1)
        # pointed arch: two arcs meeting at the apex
        m = (a + 4 + b) / 2
        left = [(a + 4 + (m - a - 4) * math.sin(math.radians(t)), spring - (spring - apex) * (1 - math.cos(math.radians(t))) ** 0.8)
                for t in range(0, 91, 10)]
        right = [(2 * m - x, y) for x, y in left[::-1]][1:]
        s.ribbon(left + right, 1.5, G5)
    # east end: apse in section (a quarter dome)
    s.ribbon(arc(xe, floor, floor - vault - 4, -90, 0, 18), 2, G7)
    s.ribbon(arc(xe, floor, floor - vault + 4, -90, 0, 18), 1.2, G5)
    # choir: arrows from the door, scattering under the vault
    n = 1 + round(13 * c["choir"])
    src = (x0 + 4, floor - 14)
    for k in range(n):
        ang = -18 - (55 * k / max(1, n - 1) if n > 1 else 0)
        L = 34 + (k % 3) * 8
        ex = src[0] + L * math.cos(math.radians(ang)) + k * 3
        ey = src[1] + L * math.sin(math.radians(ang))
        sx, sy = src[0] + k * 3, src[1]
        s.line(sx, sy, ex, ey, 1, G4)
        # arrowhead: small closed triangle
        ux, uy = (ex - sx) / math.hypot(ex - sx, ey - sy), (ey - sy) / math.hypot(ex - sx, ey - sy)
        s.poly([(ex + ux * 3, ey + uy * 3), (ex - uy * 2.2, ey + ux * 2.2), (ex + uy * 2.2, ey - ux * 2.2)], fill=G4)
    # reference numerals with leader lines, patent style
    s.text(x0 + 30, vault - 10, "10", fill=G4)
    s.line(x0 + 36, vault - 7, x0 + 42, vault - 3, 1, G3)
    s.text(xe - 4, floor - 70, "12", fill=G4)
    s.text(x0 - 14, floor + 26, "fig. 1", fill=G4)
    # ---------------- fig. 2: impulse response
    bx, by = 262, 168                 # time origin, baseline
    s.rect(bx - 4, by + 2, 214, 1.2, fill=G4)
    for k in range(8):
        s.rect(bx + k * 26, by + 3, 1.2, 4, fill=G3)
    # direct sound: a single bright impulse at 0
    s.rect(bx - 1, by - 92, 3, 92, fill=G7)
    gap = 6 + 90 * c["doors"]
    t0 = bx + gap
    tail = 40 + 150 * c["nave"]
    rng = random.Random(3)
    teeth, xs = [], t0
    pts = [(t0 - 1, by)]
    nteeth = 15
    for k in range(nteeth):
        x = t0 + (tail * k / nteeth)
        e = math.exp(-3.2 * k / nteeth) * (0.6 + 0.4 * rng.random())
        h = 70 * e + 2
        pts += [(x, by - h), (x + 2.2, by - h), (x + 3.4, by)]
    pts += [(t0 + tail + 4, by)]
    pts += [(t0 + tail + 4, by + 1), (t0 - 1, by + 1)]
    s.poly(pts, fill="none", stroke=G7, sw=1.5)
    # treble envelope (stone): its own decay over the reflections
    hf = hf_ratio(c["stone"])
    env = []
    for k in range(25):
        x = t0 + tail * k / 24
        env.append((x, by - 72 * math.exp(-3.2 * (k / 24) / hf) - 2))
    s.ribbon(env, 1.2, G5)
    s.text(t0 + 26, by - 72 * math.exp(-3.2 * 0.2 / hf) - 10, "treble", fill=G4)
    # gap dimension (doors)
    s.line(bx + 2, by - 104, t0, by - 104, 1, G4)
    s.rect(t0 - 0.6, by - 109, 1.2, 10, fill=G4)
    s.text(bx + 4, by - 110, "door", fill=G4)
    s.text(bx - 6, by + 26, "fig. 2", fill=G4)
    return s


# ------------------------------------------------------------------ v3
def v3(c):
    """P3 Trace as subject, hidden-line isometric: the reverb's decay as a waterfall.

    Twelve band slices, low at the front, high at the back, each a hidden-line wedge
    (black fill) whose level falls along time.
    nave  -> how far every slice's tail runs (shape, length)
    stone -> how much shorter the high slices are than the low (shape across depth)
    choir -> discrete echo teeth at 0, a smooth wedge at 100 (shape along the top)
    doors -> the whole surface slides away from the time origin (position)
    """
    s = Svg()
    ox, oy = 34, 186                         # time origin, front slice baseline
    tdir = (0.985, 0.16)                     # time axis on screen
    fdir = (0.62, -0.52)                     # one band step into depth (x 8 px)
    step = 8.0
    nslice = 12
    gap = 8 + 90 * c["doors"]
    length = 60 + 170 * c["nave"]
    hf = hf_ratio(c["stone"])
    diff = c["choir"]
    rng = random.Random(11)
    echo_pos = sorted(rng.random() for _ in range(9))

    def P(t, k, z):
        return (ox + tdir[0] * t + fdir[0] * step * k, oy + tdir[1] * t + fdir[1] * step * k - z)

    # axes (behind): time axis on the floor, level axis at the origin
    s.ribbon([P(-6, 0, 0), P(gap + length + 30, 0, 0)], 1, G3)
    s.ribbon([P(0, 0, 0), P(0, nslice - 1, 0)], 1, G3)
    s.ribbon([P(0, nslice - 1, 0), P(0, nslice - 1, 70)], 1, G3)
    for k in range(int((gap + length + 20) // 30) + 1):
        a = P(k * 30, 0, 0)
        s.line(a[0], a[1], a[0] - 3, a[1] + 4, 1, G3)
    for k in range(nslice - 1, -1, -1):
        frac = k / (nslice - 1)
        Lk = length * (1 - (1 - hf) * frac)
        h0 = 64 * (1 - 0.35 * frac)
        top = []
        n = 26
        for i in range(n):
            t = Lk * i / (n - 1)
            lvl = h0 * (1 - t / Lk)
            # discrete echoes where diffusion is low: notch between echo peaks
            u = i / (n - 1)
            near = min(abs(u - e) for e in echo_pos)
            comb = max(0.0, 1 - near * 14)
            lvl *= diff + (1 - diff) * comb
            top.append(P(gap + t, k, max(0.0, lvl)))
        outline = [P(gap, k, 0)] + top + [P(gap + Lk, k, 0)]
        if k == 0:
            s.poly(outline, fill=G0, stroke=G7, sw=2)
        else:
            shade = G5 if k < 4 else (G4 if k < 8 else G3)
            s.poly(outline, fill=G0, stroke=shade, sw=1.2)
    # direct sound: one bright bar at t = 0 on the front slice
    a, b = P(0, 0, 0), P(0, 0, 80)
    s.line(a[0], a[1], b[0], b[1], 2.5, G7)
    # labels on the axes
    s.text(*P(gap + length + 18, 0, -14), "time", fill=G4)
    s.text(*[v + w for v, w in zip(P(0, nslice - 1, 0), (6, 0))], "treble", fill=G4)
    s.text(P(0, 0, 0)[0] - 4, P(0, 0, 0)[1] + 16, "0", fill=G4)
    return s


# ------------------------------------------------------------------ v4
def v4(c):
    """P4 Stack in depth, star atlas: the reverb as plates of reflections, early to late.

    Each plate is one atlas chart of echoes (stars sized by magnitude); the front
    plate is the first reflections, the back ones the late tail.
    nave  -> how far the plates recede (spacing; the last plate travels ~60 px)
    stone -> how fast magnitude falls from plate to plate (star scale)
    choir -> few bright stars (discrete echoes) to many faint ones (count)
    doors -> the gap between the source star and the first plate (position)
    """
    s = Svg()
    src = (34, 150)
    gap = 18 + 80 * c["doors"]
    pw, ph = 168, 104
    x0 = src[0] + gap
    y0 = 186 - ph
    spacing = 8 + 18 * c["nave"]
    nplates = 5
    hf = hf_ratio(c["stone"])
    nstars = 4 + round(22 * c["choir"])
    rng = random.Random(5)
    stars = [(rng.random(), rng.random(), rng.random()) for _ in range(40)]
    plates = []
    for k in range(nplates):
        px, py = x0 + k * spacing * 1.6, y0 - k * spacing
        plates.append((px, py))
    # back to front; each plate a black card that hides the ones behind
    for k in range(nplates - 1, -1, -1):
        px, py = plates[k]
        edge = G7 if k == 0 else (G5 if k == 1 else (G4 if k < 4 else G3))
        s.rect(px, py, pw, ph, fill=G0, stroke=edge, sw=1.5 if k == 0 else 1.2)
        # graduation ticks along the top edge, atlas style
        for t in range(1, 12):
            tx = px + t * pw / 12
            s.rect(tx - 0.5, py, 1.2, 4 if t % 3 else 6, fill=G3 if k else G4)
        # stars in the strip of this plate that the next plate doesn't cover
        mag_scale = (0.45 + 0.55 * hf) ** k
        visible = 0
        for (u, v, m) in stars:
            if visible >= nstars:
                break
            visible += 1
            sx, sy = px + 6 + u * (pw - 12), py + 8 + v * (ph - 14)
            if k > 0:
                fx, fy = plates[k - 1]
                if fx - 3 <= sx <= fx + pw + 3 and fy - 3 <= sy <= fy + ph + 3:
                    continue
            base = 1.2 + 2.6 * m * (1 - 0.55 * c["choir"])
            rad = base * mag_scale
            if rad < 1.2:
                continue
            shade = G7 if k == 0 else (G6 if k == 1 else G5)
            s.circle(sx, sy, rad, fill=shade)
    # front plate: faint declination lines
    px, py = plates[0]
    for t in range(1, 4):
        yy = py + t * ph / 4
        s.dashed(px + 3, yy, px + pw - 3, yy, 1, G2, dash=3, gap=4)
    # plate numerals
    for k, (px, py) in enumerate(plates):
        if k == 0:
            s.text(px + 4, py + ph + 13, "I  first", fill=G4)
        elif k == nplates - 1:
            s.text(px + pw + 4, py + 10, "V", fill=G4)
    # the source star (the west door) with its trail to the first plate
    s.circle(src[0], src[1], 4, fill=G7)
    s.ribbon(arc(src[0], src[1], 8, 0, 359, 30)[:-1], 1, G4)
    s.dashed(src[0] + 10, src[1], x0 - 2, src[1], 1, G4, dash=3, gap=3)
    s.text(src[0] - 14, src[1] + 22, "door", fill=G4)
    return s


# ------------------------------------------------------------------ v5
BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def dither_rect(s, x, y, w, h, level, cell=2):
    """Ordered dither in white 2 px cells, run-length merged per row."""
    rows = int(h // cell)
    cols = int(w // cell)
    for r in range(rows):
        run = None
        for q in range(cols + 1):
            on = q < cols and BAYER4[r % 4][q % 4] < level * 16
            if on and run is None:
                run = q
            if not on and run is not None:
                s.rect(x + run * cell, y + r * cell, (q - run) * cell, cell, fill="#FFFFFF" if False else G6)
                run = None


def v5(c):
    """P9 One-bit ink (stretch), engineering schematic: the church in side elevation.

    The figure is a chunky one-bit church (west tower, nave, apse) with schematic
    callouts as its glyphs.
    nave  -> the nave lengthens east, windows (bays) added (figure shape + count)
    stone -> dither tone of the walls (static, swapped for flat greys on device)
             plus the decay glyph's fine teeth persisting (shape)
    choir -> a scatter of ink squares around the choir window (count)
    doors -> a dimension line from the door to the first reflection mark (position)
    """
    s = Svg()
    ground = 182
    xt0, xt1 = 70, 112                   # west tower
    xe = xt1 + 120 + 150 * c["nave"]     # east end of the nave
    eave, ridge = 112, 84
    lvl = 0.25 + 0.5 * c["stone"]
    # ground line with schematic hatch
    s.rect(30, ground, 420, 2, fill=G7)
    for k in range(34):
        s.line(34 + k * 12, ground + 3, 28 + k * 12, ground + 9, 1, G3)
    # nave wall: dithered plane in a 2 px outline, 1 px black gutter inside
    s.rect(xt1, eave, xe - xt1, ground - eave, fill=G0, stroke=G7, sw=2)
    dither_rect(s, xt1 + 3, eave + 3, xe - xt1 - 6, ground - eave - 6, lvl)
    # nave roof: a long gable seen side-on (a parallelogram band)
    s.poly([(xt1, eave), (xt1 + 10, ridge), (xe - 4, ridge), (xe + 6, eave)], fill=G0, stroke=G7, sw=2)
    # apse: a half-round end, flat grey with outline
    s.poly([(xe + 1, eave + 4)] + arc(xe + 1, ground - 1, ground - eave - 5, -90, 0, 14)[1:] + [(xe + 1, ground - 1)],
           fill=G2, stroke=G7, sw=2)
    # windows, one per bay: tall lancets, black with an outline
    bay = 30
    nb = int((xe - xt1 - 20) // bay)
    for i in range(nb):
        wx = xt1 + 18 + i * bay
        top = [(wx + 5 + 5 * math.cos(math.radians(a)), eave + 16 - 7 * math.sin(math.radians(a))) for a in range(0, 181, 30)]
        s.poly([(wx + 10, eave + 46)] + top + [(wx, eave + 46)], fill=G0, stroke=G7, sw=2)
    # west tower
    s.rect(xt0, 56, xt1 - xt0, ground - 56, fill=G0, stroke=G7, sw=2)
    dither_rect(s, xt0 + 3, 59, xt1 - xt0 - 6, ground - 59 - 6, min(0.9, lvl + 0.25))
    s.poly([(xt0 - 3, 56), (xt1 + 3, 56), ((xt0 + xt1) / 2, 30)], fill=G0, stroke=G7, sw=2)
    # door: black arch in the tower foot
    dx = (xt0 + xt1) / 2
    s.poly([(dx + 9, ground)] + arc(dx, ground - 22, 9, 0, -180, 10)[1:] + [(dx - 9, ground)], fill=G0, stroke=G7, sw=2)
    # --- glyphs, one per control, schematic language
    # doors: dimension line from the door to the first-reflection mark
    pre = 14 + 70 * c["doors"]
    yd = 200
    s.rect(dx - 0.75, ground + 10, 1.5, 14, fill=G5)
    s.rect(dx + pre - 0.75, ground + 10, 1.5, 14, fill=G5)
    s.line(dx + 2, yd, dx + pre - 2, yd, 1.2, G5)
    s.poly([(dx + 1, yd), (dx + 6, yd - 3), (dx + 6, yd + 3)], fill=G5)
    s.poly([(dx + pre - 1, yd), (dx + pre - 6, yd - 3), (dx + pre - 6, yd + 3)], fill=G5)
    s.text(dx + pre + 6, yd + 4, "pre", fill=G4)
    # choir: ink squares scattered around the east end
    n = 2 + round(14 * c["choir"])
    rng = random.Random(9)
    for k in range(n):
        a = rng.uniform(-170, -10)
        rr = rng.uniform(80, 104)
        sx = xe + 1 + rr * math.cos(math.radians(a)) * 0.7
        sy = ground - 10 + rr * math.sin(math.radians(a)) * 0.9
        if sy < 26:
            continue
        s.rect(sx - 2, sy - 2, 4, 4, fill=G6)
    # stone: decay glyph over the roof, fine teeth survive with harder stone
    gx, gy = xt1 + 34, 52
    pts = []
    hf = hf_ratio(c["stone"])
    for i in range(30):
        x = gx + i * 4
        env = math.exp(-3 * i / 30)
        fine = math.exp(-3 * i / (30 * hf))
        y = gy - (9 * env + 6 * fine) * (1 if i % 2 == 0 else -0.35)
        pts.append((x, y))
    s.ribbon(pts, 1.5, G6)
    s.text(gx + 124, gy + 4, "ring", fill=G4)
    return s


VARIANTS = {"v1": v1, "v2": v2, "v3": v3, "v4": v4, "v5": v5}


def main():
    import sys
    c = dict(DEFAULTS)
    for arg in sys.argv[1:]:            # optional overrides, e.g. nave=1 choir=0
        k, v = arg.split("=")
        c[k] = float(v)
    out = HERE if len(sys.argv) == 1 else HERE / "_probe"
    for name, fn in VARIANTS.items():
        fn(c).write(out / name / "rest.svg", c)
        print(out / name / "rest.svg")


if __name__ == "__main__":
    main()
