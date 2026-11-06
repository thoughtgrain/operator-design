#!/usr/bin/env python3
"""Canyon, subject pass 01: one rest-frame sketch per direction (v1..v5).

Run from anywhere:  python3 screens/canyon/passes/01-subject/sketch.py
Writes vN/rest.svg beside this file. Every frame is drawn at the definition's
defaults (distance 253 ms, walls 4, absorb 35 %, wind 0), no audio passing.

One echo model feeds all five drawings, so they disagree only in how they
draw it. Lines are closed ribbons, closed contours are stroked closed
outlines, every path is one subpath of <= 64 points. Grey only, no red.
These are subject sketches: unbound artwork, no node ids yet.
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
DEFAULTS = {"distance": 0.5, "walls": 3 / 7, "absorb": 0.35, "wind": 0.0}
WALLS = [1, 2, 3, 4, 5, 6, 8, 12]
SOUND = 343.0  # m/s


def delay_s(v):                       # exponential 0.04 .. 1.6 s
    return 0.04 * 40 ** v


def metres(v):                        # one way to the first wall
    return delay_s(v) * SOUND / 2


def n_taps(v):
    return WALLS[round(v * (len(WALLS) - 1))]


def level(k, absorb):
    """Tap k (1-based) level: each wall returns 0.8 of what reached it,
    and the rock takes a further share that grows with absorb."""
    return (0.8 * (1 - 0.45 * absorb)) ** (k - 1)


def brightness(k, absorb):
    """How much of the highs survive k reflections."""
    return (1 - absorb) ** k


def wobble(k, wind, seed=3):
    """Wind's slow modulation, frozen at one instant: a seeded offset per tap in -1..1, times wind."""
    r = random.Random(seed * 101 + k)
    return wind * r.uniform(-1, 1)


# ------------------------------------------------------------- svg helpers
def f(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def dedupe(pts, closed=False):
    out = []
    for p in pts:
        p = (round(p[0], 2), round(p[1], 2))
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) >= 0.4:
            out.append(p)
    if closed and len(out) > 2 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) < 0.4:
        out.pop()
    return out


class Svg:
    def __init__(self):
        self.items: list[str] = []

    def add(self, s):
        self.items.append("  " + s)

    def ribbon(self, pts, w, fill):
        """Open polyline -> closed filled ribbon of width w, split every 30 points."""
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

    def poly(self, pts, fill="none", stroke="none", sw=1.0):
        pts = dedupe(pts, closed=True)
        if len(pts) < 3:
            return
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
        sw_attr = f' stroke-width="{f(sw)}"' if stroke != "none" else ""
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}"{sw_attr}/>')

    def line(self, x1, y1, x2, y2, w, fill):
        self._ribbon([(x1, y1), (x2, y2)], w, fill)

    def rect(self, x, y, w, h, fill="none", stroke="none", sw=1.0):
        self.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], fill, stroke, sw)

    def circle(self, cx, cy, r, fill, stroke="none", sw=1.0):
        sw_attr = f' stroke-width="{f(sw)}"' if stroke != "none" else ""
        self.add(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}" stroke="{stroke}"{sw_attr}/>')

    def text(self, x, y, s, fill=G4, size=10):
        self.add(f'<text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{fill}" stroke="none" '
                 f'font-family="{FONT}" font-size="{size}px">{s}</text>')

    def dashed(self, pts, w, fill, dash=4.0, gap=3.0):
        """Dash an open polyline."""
        segs = list(zip(pts, pts[1:]))
        on, run, cur = True, 0.0, [pts[0]]
        for (x1, y1), (x2, y2) in segs:
            L = math.hypot(x2 - x1, y2 - y1)
            t = 0.0
            while t < L:
                need = (dash if on else gap) - run
                step = min(need, L - t)
                t += step
                run += step
                p = (x1 + (x2 - x1) * t / L, y1 + (y2 - y1) * t / L)
                if on:
                    cur.append(p)
                if run >= (dash if on else gap) - 1e-9:
                    if on and len(cur) > 1:
                        self.ribbon(cur, w, fill)
                    on, run, cur = not on, 0.0, [p]
        if on and len(cur) > 1 and run > 2.5:
            self.ribbon(cur, w, fill)

    def write(self, path, values):
        head = HEADER.format(*values)
        body = "\n".join(self.items)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n'
                        f'{head}\n{body}\n</svg>\n')


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
    <text transform="matrix(1 0 0 1 5 10)" fill="#CBCBCB" stroke="none" font-family="UniversNextPro-Light" font-size="10px">distance</text>
    <text transform="matrix(1 0 0 1 125 10)" fill="#CBCBCB" stroke="none" font-family="UniversNextPro-Light" font-size="10px">walls</text>
    <text transform="matrix(1 0 0 1 245 10)" fill="#000000" stroke="none" font-family="UniversNextPro-Light" font-size="10px">absorb</text>
    <text transform="matrix(1 0 0 1 365 10)" fill="#000000" stroke="none" font-family="UniversNextPro-Light" font-size="10px">wind</text>
    <text transform="matrix(1 0 0 1 65 17.44)" fill="#CBCBCB" stroke="none" font-family="UniversNextPro-Light" font-size="20px">{0}</text>
    <text transform="matrix(1 0 0 1 185 17.44)" fill="#CBCBCB" stroke="none" font-family="UniversNextPro-Light" font-size="20px">{1}</text>
    <text transform="matrix(1 0 0 1 305 17.44)" fill="#000000" stroke="none" font-family="UniversNextPro-Light" font-size="20px">{2}</text>
    <text transform="matrix(1 0 0 1 425 17.44)" fill="#000000" stroke="none" font-family="UniversNextPro-Light" font-size="20px">{3}</text>
  </g>"""


def captions(c):
    t = delay_s(c["distance"])
    d = f"{t * 1000:.0f}ms" if t < 1 else f"{t:.2f}s"
    return d, str(n_taps(c["walls"])), str(round(c["absorb"] * 100)), str(round(c["wind"] * 100))


# ------------------------------------------------------------------ v1
def rock_rim(cx, cy, rx, ry, jag, seed, n=60):
    """A bench outline in plan: a squared ellipse with a fixed low-frequency
    irregularity (the rock's form) plus fine serration of size `jag` (its hardness)."""
    r = random.Random(seed)
    ph = [r.uniform(0, 6.283) for _ in range(6)]
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        c, s = math.cos(a), math.sin(a)
        e = 2.6
        k = (abs(c) ** e + abs(s) ** e) ** (-1 / e)
        form = 1 + 0.05 * math.sin(2 * a + ph[0]) + 0.04 * math.sin(3 * a + ph[1])
        ser = jag * (0.6 * math.sin(11 * a + ph[2]) + 0.4 * math.sin(17 * a + ph[3]))
        rr = k * form
        pts.append((cx + c * (rx * rr + ser), cy + s * (ry * rr + ser * 0.6)))
    return pts


def v1(c):
    """P4 Stack in depth, survey plan: the walls as rock benches stacked back up the canyon."""
    s = Svg()
    n, a = n_taps(c["walls"]), c["absorb"]
    step = 14 + 40 * c["distance"]                       # px between benches along the chainage
    ux, uy = 0.87, -0.49                                  # chainage bearing on the plan
    fx, fy = 178, 156                                     # first bench
    shown = min(n, 6)
    benches = [(fx + ux * step * i, fy + uy * step * i) for i in range(shown)]
    greys = [G7, G5, G4, G3, G3, G2]
    # back to front, each bench hides what's behind it (black fill)
    for i in reversed(range(shown)):
        cx, cy = benches[i]
        rot = math.radians(18 * wobble(i + 1, c["wind"]))
        jag = 3.4 * brightness(i + 1, a) / brightness(1, 0.35)
        rim = rock_rim(cx, cy, 82, 21, jag, seed=40 + i)
        if rot:
            rim = [(cx + (x - cx) * math.cos(rot) - (y - cy) * math.sin(rot),
                    cy + (x - cx) * math.sin(rot) + (y - cy) * math.cos(rot)) for x, y in rim]
        s.poly(rim, fill=G0, stroke=greys[i], sw=2 if i == 0 else 1.5)
        inner = rock_rim(cx + 6, cy + 1, 52, 10, jag * 0.5, seed=40 + i)
        s.poly(inner, fill=G0, stroke=G2 if i else G3, sw=1)
    # chainage traverse: dashed centreline from the mouth station up through the benches
    sx, sy = fx - ux * 62, fy - uy * 62
    ex, ey = benches[-1][0] + ux * 104, benches[-1][1] + uy * 104
    s.dashed([(sx, sy), (ex, ey)], 1, G3, dash=6, gap=3)
    # station at the canyon mouth: a survey control triangle
    s.poly([(sx, sy - 5), (sx + 5, sy + 4), (sx - 5, sy + 4)], fill=G0, stroke=G5, sw=1.2)
    s.text(sx - 30, sy + 14, "0+00", G4)
    m = metres(c["distance"])
    s.text(fx - 132, fy + 4, f"{m:.0f} m", G5)
    s.line(fx - 108, fy + 1, fx - 88, fy + 1, 1, G3)
    s.text(benches[-1][0] + 92, benches[-1][1] - 2, f"{m * shown:.0f} m", G4)
    s.text(392, 206, "plan · 1:2500", G3)
    return s


# ------------------------------------------------------------------ v2
def v2(c):
    """P10 Voice field, patent section: the echo's impulse response as a row of hatched rock columns."""
    s = Svg()
    n, a = n_taps(c["walls"]), c["absorb"]
    d = delay_s(c["distance"])
    cols, pitch, cw = 26, 15, 10
    x0, ground = 46, 182
    span = 1.3                                            # seconds across the row
    taps = [(k * d * (1 + 0.06 * wobble(k, c["wind"])), level(k, a), 0.018 + 0.05 * a * k) for k in range(1, n + 1)]
    heights = []
    for j in range(cols):
        t = (j + 0.5) * span / cols
        e = 0.0
        for tk, lv, sg in taps:
            e += lv * math.sqrt(0.018 / sg) * math.exp(-((t - tk) ** 2) / (2 * sg * sg))
        heights.append(max(4, round(118 * min(1.0, e))))
    peak = max(range(cols), key=lambda j: heights[j])
    # earth below the section line (patent ground symbol)
    for x in range(40, 446, 8):
        s.line(x, ground + 4, x - 6, ground + 10, 1, G2)
    s.line(36, ground + 1, 446, ground + 1, 1.5, G4)
    # columns: outlined, hatched at 45 degrees inside
    for j, hgt in enumerate(heights):
        x = x0 + j * pitch
        y = ground - hgt
        s.rect(x, y, cw, hgt, fill=G0, stroke=G7 if j == peak else G5, sw=2 if j == peak else 1.5)
        if hgt > 8:
            for cc in range(-hgt, cw, 5):                 # lines x - (y - top) = cc inside the rect
                p1 = (x + max(0, cc), y + max(0, -cc))
                p2 = (x + min(cw, cc + hgt), y + min(hgt, cw - cc))
                if math.hypot(p2[0] - p1[0], p2[1] - p1[1]) > 6:
                    q1 = (p1[0] + 1.2, p1[1] + 1.2)
                    q2 = (p2[0] - 1.2, p2[1] - 1.2)
                    if q2[0] - q1[0] > 1:
                        s.line(q1[0], q1[1], q2[0], q2[1], 1, G2)
    # reference numerals with leaders
    px = x0 + peak * pitch + cw
    py = ground - heights[peak]
    s.line(px + 2, py + 6, px + 22, py - 10, 1, G4)
    s.text(px + 24, py - 8, "10", G5)
    s.line(410, ground + 8, 424, ground + 22, 1, G4)
    s.text(428, ground + 32 - 4, "12", G5)
    last = x0 + min(cols - 1, round(taps[-1][0] / span * cols - 0.5)) * pitch
    s.line(last + 5, ground - heights[min(cols - 1, round(taps[-1][0] / span * cols - 0.5))] - 4, last + 14, 86, 1, G4)
    s.text(last + 10, 82, "14", G5)
    s.text(46, 60, "fig. 1", G4)
    return s


# ------------------------------------------------------------------ v3
def v3(c):
    """P15 Cell field, hidden-line isometric: the canyon floor as cells, lit where each echo's front passes."""
    s = Svg()
    n, a = n_taps(c["walls"]), c["absorb"]
    I, J, A = 14, 9, 15
    X0, Y0 = 204, 40
    src = (0, 4)
    D = 1.2 + 3.6 * c["distance"]                          # cells between echo fronts
    rnd = random.Random(11)
    state = {}
    for i in range(I):
        for j in range(J):
            r = math.hypot(i - src[0], (j - src[1]) * 1.0)
            st = ("floor", 0)
            for k in range(1, n + 1):
                rk = k * D + 1.6 * wobble(k * 7 + j, c["wind"])
                if abs(r - rk) < 0.62:
                    keep = rnd.random() < (1 - a) ** (k - 1) * (1.0 if k == 1 else 0.95)
                    st = ("lit", k) if keep else ("grey", k)
            state[(i, j)] = st
    state[src] = ("source", 0)

    def P(i, j, z=0.0):
        return X0 + (i - j) * A, Y0 + (i + j) * A / 2 - z

    edge = {1: G7, 2: G5, 3: G4, 4: G3}
    for ssum in range(I + J - 1):
        for i in range(I):
            j = ssum - i
            if not 0 <= j < J:
                continue
            kind, k = state[(i, j)]
            t0, t1, t2, t3 = P(i, j), P(i + 1, j), P(i + 1, j + 1), P(i, j + 1)
            if kind == "floor":
                s.poly([t0, t1, t2, t3], fill=G0, stroke=G1, sw=1)
            elif kind == "grey":
                s.poly([t0, t1, t2, t3], fill=G2, stroke=G3, sw=1)
            else:
                hz = 14 if kind == "source" else 8
                col = G5 if kind == "source" else edge.get(k, G3)
                u0, u1, u2, u3 = P(i, j, hz), P(i + 1, j, hz), P(i + 1, j + 1, hz), P(i, j + 1, hz)
                sw = 1.5 if k == 1 else 1.2
                s.poly([u3, u2, t2, t3], fill=G0, stroke=col, sw=sw)   # left face
                s.poly([u2, u1, t1, t2], fill=G0, stroke=col, sw=sw)   # right face
                s.poly([u0, u1, u2, u3], fill=G0, stroke=col, sw=sw)   # top
    return s


# ------------------------------------------------------------------ v4
def wall_profile(side, half, n=14):
    """One canyon wall in section, floor to rim, as a list of points (side -1 left, +1 right)."""
    r = random.Random(5 if side < 0 else 9)
    pts = []
    for i in range(n + 1):
        t = i / n
        y = 200 - 168 * t
        flare = 18 * t + 44 * t * t                       # walls open towards the rim
        jit = r.uniform(-3, 3) if 0 < i < n else 0
        pts.append((240 + side * (half + flare + jit), y))
    return pts


def v4(c):
    """P1 Section drawing, star atlas: the canyon cut across, its echoes plotted as stars between the walls."""
    s = Svg()
    n, a = n_taps(c["walls"]), c["absorb"]
    half = 50 + 100 * c["distance"]                       # half the floor width
    # graticule: hairline parallels and meridians, the walls cover them
    for y in (48, 84, 120, 156, 192):
        pts = [(x, y + 0.0009 * (x - 240) ** 2 - 10) for x in range(4, 477, 12)]
        s.ribbon(pts, 1, G1)
    for m in (-3, -2, -1, 0, 1, 2, 3):
        pts = [(240 + m * 52 * (0.55 + 0.45 * (y - 24) / 190), y) for y in range(24, 211, 8)]
        s.ribbon(pts, 1, G1)
    left, right = wall_profile(-1, half), wall_profile(1, half)
    for prof, side in ((left, -1), (right, 1)):
        edge_x = 0 if side < 0 else 480
        outline = prof + [(edge_x, prof[-1][1]), (edge_x, 212), (prof[0][0], 212)]
        s.poly(outline, fill=G0, stroke=G4, sw=1.5)
        inset = [(x - side * 10, y) for x, y in prof[1:-1]]
        s.dashed(inset[::-1], 1, G2, dash=5, gap=4)

    def wall_x(prof, y):
        for (x1, y1), (x2, y2) in zip(prof, prof[1:]):
            if y2 <= y <= y1:
                return x1 + (x2 - x1) * (y1 - y) / (y1 - y2)
        return prof[-1][0]

    src = (240, 194)
    stars = []
    for k in range(1, n + 1):
        y = 194 - 150 * k / (n + 0.6)
        prof = right if k % 2 else left
        side = 1 if k % 2 else -1
        x = wall_x(prof, y) - side * 9
        wx, wy = wobble(k, c["wind"]) * 16, wobble(k + 50, c["wind"]) * 8
        stars.append((x + wx, y + wy, 1.8 + 4.2 * level(k, a), k))
    # constellation line: source to each reflection, broken short of each star
    chain = [(src[0], src[1], 3.5)] + [(x, y, r) for x, y, r, _ in stars]
    for (x1, y1, r1), (x2, y2, r2) in zip(chain, chain[1:]):
        L = math.hypot(x2 - x1, y2 - y1)
        g1, g2 = (r1 + 4) / L, (r2 + 4) / L
        s.line(x1 + (x2 - x1) * g1, y1 + (y2 - y1) * g1, x2 - (x2 - x1) * g2, y2 - (y2 - y1) * g2, 1, G3)
    s.circle(src[0], src[1], 3.5, G0, G5, 1.2)
    names = "abcdefghijkl"
    for x, y, r, k in stars:
        s.circle(x, y, r + 1.5, G0)
        s.circle(x, y, r, G7 if k == 1 else (G5 if k < 3 else G4))
        side = 1 if k % 2 else -1
        s.text(x - side * (r + 8) - (6 if side > 0 else 0), y - r - 3, names[k - 1], G4)
    s.text(8, 212 - 4, f"sect. a–a  {metres(c['distance']):.0f} m", G4)
    return s


# ------------------------------------------------------------------ v5
def v5(c):
    """P5 Field and figure, engineering schematic: the wall pair dimensioned over the canyon floor, taps on the strip."""
    s = Svg()
    n, a, wind = n_taps(c["walls"]), c["absorb"], c["wind"]
    # field: floor grid in perspective, stopped before it packs under 3 px
    vp = (240 + 30 * wind, 104)
    rows = [186, 164, 149, 139, 132]
    for y in rows:
        s.line(28, y, 452, y, 1, G1)
    for m in range(-7, 8):
        bx = 240 + m * 44 + 24 * wind
        tx = vp[0] + (bx - vp[0]) * (rows[-1] - vp[1]) / (rows[0] - vp[1])
        s.line(tx, rows[-1], bx, rows[0], 1, G1)
    # figure: two wall blocks in elevation, scaled about the floor centre by distance
    sc = 0.7 + 0.6 * c["distance"]
    base = (240, 176)

    def T(p):
        return base[0] + p[0] * sc, base[1] + p[1] * sc

    gap = 64
    lw = [(-gap, 0), (-gap - 8, -40), (-gap - 4, -62), (-gap - 14, -104), (-gap - 74, -104),
          (-gap - 82, -60), (-gap - 92, 0)]
    rw = [(-x, y) for x, y in lw]
    s.poly([T(p) for p in lw], fill=G0, stroke=G7, sw=2)
    s.poly([T(p) for p in rw[::-1]], fill=G0, stroke=G7, sw=2)
    # centre line (dash-dot) and the dimension across the gap at the rim
    s.dashed([T((0, 6)), T((0, -118))], 1, G3, dash=9, gap=3)
    yd = T((0, -116))[1]
    xl, xr = T(lw[3])[0], T(rw[3])[0]
    s.line(xl, T(lw[3])[1] - 3, xl, yd - 5, 1, G4)
    s.line(xr, T(rw[3])[1] - 3, xr, yd - 5, 1, G4)
    s.line(xl, yd, xr, yd, 1, G5)
    for x in (xl, xr):
        s.line(x - 3, yd + 3, x + 3, yd - 3, 1.5, G5)
    label = f"{metres(c['distance']):.0f} m"
    s.rect(240 - 16, yd - 6, 32, 12, fill=G0)
    s.text(240 - 13, yd + 4, label, G5)
    # strip: the tap train in time, one bar per wall
    d = delay_s(c["distance"])
    s.line(40, 211, 440, 211, 1, G2)
    s.text(8, 211, "0", G3)
    s.text(446, 211, "1.3s", G3)
    for k in range(1, n + 1):
        t = k * d * (1 + 0.06 * wobble(k, wind))
        if t > 1.3:
            break
        x = 40 + t / 1.3 * 400
        h = max(4, 14 * level(k, a))
        s.rect(x - 2, 210 - h, 4, h, fill=G6 if k == 1 else G4)
    return s


def main():
    c = DEFAULTS
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        fn(c).write(HERE / name / "rest.svg", captions(c))
        print(f"wrote {name}/rest.svg")


if __name__ == "__main__":
    main()
