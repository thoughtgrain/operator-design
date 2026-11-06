#!/usr/bin/env python3
"""Kiln subject pass 01: one rest-frame sketch per direction (v1..v5).

Each sketch is the rest frame of its subject at the definition's defaults
(strike 50, glaze 30, crack 0, fire 1.12), stock header kept, 480 x 220.
Sketches, not final frames: parts that a control would move carry kiln_node_i
ids so the budget can be estimated, the rest is static artwork.

    python3 screens/kiln/passes/01-subject/sketch.py
"""
from __future__ import annotations

import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 480, 220

# stock greys
G0, G1, G2, G3, G4, G5, G6, BK = ("#CDCDCD", "#AFAFAF", "#969696", "#7D7D7D",
                                  "#646464", "#4B4B4B", "#323232", "#000000")

TITLES = ["strike", "glaze", "crack", "fire"]
VALUES = ["50", "30", "0", "1.12"]          # defaults: 0.5, 0.3, 0.0, 1.00 + 0.5 * 0.24
FONT = 'font-family="UniversNextPro-Light"'


def f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


class Frame:
    def __init__(self) -> None:
        self.out: list[str] = []
        self.node = 0

    def nid(self) -> str:
        i = self.node
        self.node += 1
        return f' id="kiln_node_{i}"'

    def path(self, pts, fill=BK, stroke="none", sw=0.0, bound=False, origin=None):
        clean = []
        for x, y in pts:
            p = (round(x, 2), round(y, 2))
            if not clean or math.dist(p, clean[-1]) >= 0.2:
                clean.append(p)
        while len(clean) > 2 and math.dist(clean[0], clean[-1]) < 0.3:
            clean.pop()
        assert len(clean) <= 64, len(clean)
        tr = ""
        if origin is not None:
            ox, oy = origin
            clean = [(round(x - ox, 2), round(y - oy, 2)) for x, y in clean]
            tr = f' transform="matrix(1 0 0 1 {f(ox)} {f(oy)})"'
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in clean) + " Z"
        ident = self.nid() if bound else ""
        self.out.append(f'  <path{ident} d="{d}"{tr} fill="{fill}" stroke="{stroke}" stroke-width="{f(sw)}"/>')

    def circle(self, cx, cy, r, fill, stroke="none", sw=0.0, bound=False):
        ident = self.nid() if bound else ""
        self.out.append(f'  <circle{ident} cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}" stroke="{stroke}" stroke-width="{f(sw)}"/>')

    def ribbon(self, pts, w, fill, bound=False):
        """A line as a thin closed ribbon (filled), split into ≤ 30-point runs."""
        step = 29
        i = 0
        while i < len(pts) - 1:
            run = pts[i:i + step + 1]
            self.path(ribbon_outline(run, w), fill=fill, bound=bound)
            i += step

    def text(self, x, y, s, fill=G3, size=10):
        self.out.append(f'  <text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{fill}" stroke="none" {FONT} font-size="{size}px">{s}</text>')

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

    palette = [G0, G2, G4, G6]


def ribbon_outline(pts, w):
    """Offset a polyline both ways by w/2 (mitred, clamped) and close it."""
    h = w / 2
    left, right = [], []
    n = len(pts)
    for i in range(n):
        if i == 0:
            dx, dy = pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]
        elif i == n - 1:
            dx, dy = pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]
        else:
            ax, ay = pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]
            bx, by = pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]
            la, lb = math.hypot(ax, ay) or 1, math.hypot(bx, by) or 1
            dx, dy = ax / la + bx / lb, ay / la + by / lb
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        k = h
        if 0 < i < n - 1:  # mitre, clamped
            ax, ay = pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]
            la = math.hypot(ax, ay) or 1
            cos = abs((-ay / la) * nx + (ax / la) * ny)
            k = h / max(cos, 0.5)
        left.append((pts[i][0] + nx * k, pts[i][1] + ny * k))
        right.append((pts[i][0] - nx * k, pts[i][1] - ny * k))
    return left + right[::-1]


def arc(cx, cy, rx, ry, a0, a1, n):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * t / (n - 1)),
             cy + ry * math.sin(a0 + (a1 - a0) * t / (n - 1))) for t in range(n)]


# ---------------------------------------------------------------- v1
def v1() -> Frame:
    """P15 cell field, hidden-line isometric: the glaze surface as a tiled slab field."""
    F = Frame()
    F.palette = [G0, G2, G5, G4, BK, G6]
    rnd = random.Random(7)
    a, b = 12, 7                 # iso half-width / half-height of one cell
    NI, NJ = 14, 8
    ox, oy = 210, 46
    t = 5                        # slab thickness (fire)
    strike_at = (3.0, 6.5)       # where the mallet lands, front left
    # glaze: ~30 % of cells in the grey layer, in runs of 2-4 along i
    state = {}
    for j in range(NJ):
        i = 0
        while i < NI:
            run = rnd.randint(2, 4)
            kind = "glaze" if rnd.random() < 0.3 else "wire"
            for k in range(run):
                if i + k < NI:
                    state[(i + k, j)] = kind
            i += run
    # strike 50: a lit patch (runs) round the strike point
    for (i, j) in list(state):
        d = math.hypot(i - strike_at[0], (j - strike_at[1]) * 1.3)
        if d < 1.2:
            state[(i, j)] = "hit"
        elif d < 3.4 and rnd.random() < 0.75 - d * 0.12:
            state[(i, j)] = "lit"
    cells = sorted(state, key=lambda c: (c[0] + c[1], c[0]))
    for (i, j) in cells:
        cx = ox + (i - j) * a
        cy = oy + (i + j) * b
        top = [(cx, cy), (cx + a, cy + b), (cx, cy + 2 * b), (cx - a, cy + b)]
        side = [(cx - a, cy + b), (cx, cy + 2 * b), (cx + a, cy + b),
                (cx + a, cy + b + t), (cx, cy + 2 * b + t), (cx - a, cy + b + t)]
        kind = state[(i, j)]
        face, edge, sface = {
            "wire": (BK, G4, BK),
            "glaze": (G5, G4, G6),
            "lit": (G2, G3, G5),
            "hit": (G0, G1, G4),
        }[kind]
        F.path(side, fill=sface, stroke=edge, sw=1, bound=True, origin=(cx, cy + b))
        F.path(top, fill=face, stroke=edge, sw=1, bound=True, origin=(cx, cy + b))
    return F


# ---------------------------------------------------------------- v2
def v2() -> Frame:
    """P1 section drawing, star atlas: the bowl cut a-a, its modes charted as stars."""
    F = Frame()
    F.palette = [G0, G1, G3, G6]
    cx, cy, R, wall = 240, 104, 88, 5
    # graticule: two declination arcs from a pole far above the chart
    pole, rs = (240, -840), 905
    for r in (886, 938):
        dx = 196
        a0 = math.acos(dx / r)
        F.ribbon(arc(pole[0], pole[1], r, r, a0, math.pi - a0, 40), 1, G6)
    # stars: modes n = 2..7, x by log frequency ratio along the ecliptic
    ratios = [1.0, 2.71, 5.15, 8.43, 12.1, 16.5]
    stretch = 1.12
    mags = [5.0, 4.0, 3.3, 2.7, 2.3, 2.0]       # strike 50: upper modes fainter
    stars = []
    for k, (rt, m) in enumerate(zip(ratios, mags)):
        rr = rt * (stretch ** (k * 0.5))
        u = math.log(rr) / math.log(ratios[-1] * stretch ** 2.5)
        x = 70 + u * 360
        y = pole[1] + math.sqrt(rs ** 2 - (x - pole[0]) ** 2)
        stars.append((x, y, m))
    # constellation lines between neighbouring stars, broken short of each disc
    for (x0, y0, m0), (x1, y1, m1) in zip(stars, stars[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        p0 = (x0 + ux * (m0 + 4), y0 + uy * (m0 + 4))
        p1 = (x1 - ux * (m1 + 4), y1 - uy * (m1 + 4))
        F.ribbon([p0, p1], 1, G4)
    for k, (x, y, m) in enumerate(stars):
        F.circle(x, y, m, G1, bound=True)
        F.text(x - 6, y + m + 12, f"n{k + 2}", G3)
    # meteor trail: the strike, plotted from its radiant down to the rim
    hit = (cx - R + 2, cy + 2)
    ang = math.radians(-38)                         # strike 50 sets this angle
    tail = (hit[0] + 92 * math.cos(math.pi + ang), hit[1] + 92 * math.sin(math.pi + ang))
    F.circle(tail[0], tail[1], 3.5, BK, G3, 1)       # radiant
    seg = [(tail[0] + (hit[0] - tail[0]) * s, tail[1] + (hit[1] - tail[1]) * s) for s in (0.12, 0.88)]
    # taper: thin at the radiant, 2 px at the rim
    mx, my = (seg[1][0] - seg[0][0]), (seg[1][1] - seg[0][1])
    L = math.hypot(mx, my)
    nx, ny = -my / L, mx / L
    F.path([(seg[0][0] + nx * 0.5, seg[0][1] + ny * 0.5), (seg[1][0] + nx * 1.2, seg[1][1] + ny * 1.2),
            (seg[1][0] - nx * 1.2, seg[1][1] - ny * 1.2), (seg[0][0] - nx * 0.5, seg[0][1] - ny * 0.5)],
           fill=G2, bound=True, origin=hit)
    # the bowl in section: the cut wall as one bright U band, foot ring below
    outer = [(cx - R * math.cos(math.radians(6 * k)), cy + R * math.sin(math.radians(6 * k))) for k in range(31)]
    inner = [(cx - (R - wall) * math.cos(math.radians(6 * (30 - k))), cy + (R - wall) * math.sin(math.radians(6 * (30 - k))))
             for k in range(31)]
    F.path(outer + inner, fill=G0, stroke="none", sw=0, bound=True)
    # foot ring in section: two small blocks under the bowl
    for s in (-1, 1):
        x0 = cx + s * 22
        F.path([(x0 - 4, cy + R - 3), (x0 + 4, cy + R - 3), (x0 + 4, cy + R + 7), (x0 - 4, cy + R + 7)],
               fill=G0, bound=False)
    F.ribbon([(cx - 60, cy + R + 8), (cx + 60, cy + R + 8)], 1, G4)
    # glaze pooled in the well: a level line (meniscus) inside the section
    gy = cy + 66                                    # glaze 30
    half = math.sqrt((R - wall) ** 2 - (gy - cy) ** 2) - 1.5
    F.path([(cx - half, gy), (cx + half, gy), (cx + half - 0.6, gy + 1.5), (cx - half + 0.6, gy + 1.5)],
           fill=G2, bound=True, origin=(cx, gy))
    # section mark and plate label
    F.text(cx - R - 4, cy - 6, "a", G3)
    F.text(cx + R - 2, cy - 6, "a", G3)
    F.text(8, 208, "section a–a", G3)
    return F


# ---------------------------------------------------------------- v3
def ring(t, f0=1.0, decay=3.2, beat=0.0, stretch=1.12):
    ratios = [1.0, 2.71, 5.15]
    amps = [1.0, 0.42, 0.18]
    v = 0.0
    for k, (r, a) in enumerate(zip(ratios, amps)):
        rr = r * stretch ** (k * 0.5)
        v += a * math.exp(-t * decay * (1 + k * 0.9)) * math.sin(2 * math.pi * f0 * rr * t)
    if beat:
        v *= 1 - beat * 0.5 * (1 - math.cos(2 * math.pi * 1.4 * t))
    return v


def v3() -> Frame:
    """P2 diagram + trace, engineering schematic: mallet -> mode bank + damper -> sum | ring trace."""
    F = Frame()
    F.palette = [G0, G2, G3, G6]
    wire = G3
    # source: mallet impulse box
    F.path([(14, 96), (58, 96), (58, 136), (14, 136)], fill=BK, stroke=G2, sw=1.5)
    # impulse inside: a pulse whose width is the mallet's contact (strike)
    pw = 7                                            # strike 50
    F.path([(22, 128), (36 - pw / 2, 128), (36 - pw / 2, 104), (36 + pw / 2, 104), (36 + pw / 2, 128), (50, 128),
            (50, 129.5), (36 + pw / 2 - 1.5, 129.5), (36 + pw / 2 - 1.5, 105.5), (36 - pw / 2 + 1.5, 105.5),
            (36 - pw / 2 + 1.5, 129.5), (22, 129.5)], fill=G1, bound=True, origin=(36, 116))
    F.text(14, 150, "mallet", G3)
    # bus to the mode bank
    F.ribbon([(58, 116), (74, 116)], 1, wire)
    F.ribbon([(74, 54), (74, 178)], 1, wire)
    ys = [54, 95, 137, 178]
    labels = ["1.00", "2.79", "5.45", "9.23"]
    for y, lab in zip(ys, labels):
        F.ribbon([(74, y), (86, y)], 1, wire)
        F.path([(86, y - 13), (140, y - 13), (140, y + 13), (86, y + 13)], fill=BK, stroke=G2, sw=1.5)
        F.text(93, y + 4, lab, G3)
        F.ribbon([(140, y), (196, y)], 1, wire)
    # damper (glaze): a dashpot across the bank, piston on a rod
    F.ribbon([(166, 54), (166, 178)], 1, G4)
    F.path([(156, 92), (176, 92), (176, 140), (156, 140)], fill=BK, stroke=G2, sw=1.5)
    piston_y = 104                                    # glaze 30: shallow
    F.path([(158, piston_y), (174, piston_y), (174, piston_y + 4), (158, piston_y + 4)], fill=G2, bound=True,
           origin=(166, piston_y + 2))
    F.text(150, 156, "glaze", G3)
    # summing junction
    F.ribbon([(196, 54), (196, 178)], 1, wire)
    F.circle(214, 116, 9, BK, G2, 1.5)
    F.ribbon([(196, 116), (205, 116)], 1, wire)
    F.ribbon([(209, 116), (219, 116)], 1, G2)
    F.ribbon([(214, 111), (214, 121)], 1, G2)
    F.ribbon([(223, 116), (244, 116)], 1, wire)
    # right zone: the ring trace (output), brightest
    x0, x1, yc, amp = 248, 468, 112, 50
    n = 300
    pts = [(x0 + (x1 - x0) * k / (n - 1), yc - amp * ring(k / (n - 1) * 1.0, f0=7.0) / 1.2) for k in range(n)]
    F.ribbon(pts, 2, G0, bound=True)
    # time axis
    F.ribbon([(248, 172), (468, 172)], 1, G4)
    # mode ruler (fire): ticks at the stretched mode ratios, log scale
    for k, r in enumerate([1.0, 2.71, 5.15, 8.43]):
        rr = r * 1.12 ** (k * 0.5)
        x = 252 + 200 * math.log(rr) / math.log(14)
        F.path([(x - 0.75, 186), (x + 0.75, 186), (x + 0.75, 198), (x - 0.75, 198)], fill=G2, bound=True,
               origin=(x, 192))
    F.ribbon([(248, 198), (468, 198)], 1, G4)
    F.text(422, 212, "modes", G3)
    F.text(422, 168, "t", G3)
    return F


# ---------------------------------------------------------------- v4
def v4() -> Frame:
    """P3 trace as subject, oscilloscope: the bowl's ring, big, on a graticule."""
    F = Frame()
    F.palette = [G0, G4, G6]
    X0, X1, Y0, Y1 = 16, 464, 30, 206
    # graticule: 10 x 8 divisions, hairline, minor ticks on the centre axes
    dx, dy = (X1 - X0) / 10, (Y1 - Y0) / 8
    for k in range(11):
        x = X0 + k * dx
        F.path([(x - 0.5, Y0), (x + 0.5, Y0), (x + 0.5, Y1), (x - 0.5, Y1)], fill=G6)
    for k in range(9):
        y = Y0 + k * dy
        F.path([(X0, y - 0.5), (X1, y - 0.5), (X1, y + 0.5), (X0, y + 0.5)], fill=G6)
    yc = Y0 + 3 * dy                                   # channel 1 axis
    for k in range(50):
        x = X0 + k * dx / 5
        if k % 5:
            F.path([(x - 0.5, yc - 3), (x + 0.5, yc - 3), (x + 0.5, yc + 3), (x - 0.5, yc + 3)], fill=G5)
    # channel 1: the ring (sum of modes), bright, starts at the trigger
    amp = 2.6 * dy                                     # strike 50
    n = 230
    t0 = X0 + dx * 0.5
    pts = []
    for k in range(n):
        u = k / (n - 1)
        x = t0 + (X1 - 4 - t0) * u
        pts.append((x, yc - amp * ring(u, f0=11.0, decay=2.4) / 1.25))
    pre = [(X0 + 2, yc), (t0, yc)]
    F.ribbon(pre, 2, G0)
    F.ribbon(pts, 2, G0, bound=True)
    # channel 2: the highest mode alone, small, grey
    y2 = Y0 + 7 * dy
    pts2 = []
    for k in range(200):
        u = k / 199
        x = t0 + (X1 - 4 - t0) * u
        pts2.append((x, y2 - 0.55 * dy * math.exp(-u * 5.0) * math.sin(2 * math.pi * 11 * 5.45 * 1.0 * u * 0.42)))
    F.ribbon(pts2, 1.5, G4, bound=True)
    # glaze: the decay cursor, where the ring falls below -40 dB
    cur = t0 + (X1 - t0) * 0.62
    F.path([(cur - 0.75, Y0 + 2), (cur + 0.75, Y0 + 2), (cur + 0.75, Y1 - 2), (cur - 0.75, Y1 - 2)], fill=G3,
           bound=True, origin=(cur, (Y0 + Y1) / 2))
    # trigger mark on the left edge
    F.path([(X0 + 1, yc - 4), (X0 + 7, yc), (X0 + 1, yc + 4)], fill=G3)
    F.text(X0 + 4, Y1 + 11, "1  20 ms", G3)
    F.text(cur + 4, Y0 + 12, "-40 dB", G3)
    return F


# ---------------------------------------------------------------- v5
def v5() -> Frame:
    """P12 orrery (stretch), typeset diagram: the bowl as the sun, its modes as orbits."""
    F = Frame()
    F.palette = [G0, G1, G2, G4, G6]
    cx, cy = 240, 112
    elev = math.radians(22)
    k = 70                                            # px per world unit
    radii = [1.0, 1.55, 2.1, 2.65]                    # modes n = 2..5 (fire 1.12 spacing)
    sq = math.sin(elev)

    def proj(r, th):
        return cx + k * r * math.cos(th), cy + k * r * math.sin(th) * sq

    # bowl: rim radius and depth in world units
    rim_r = 0.6
    # orbits, back halves first
    for r in radii:
        back = [proj(r, math.radians(180 + 180 * s / 40)) for s in range(41)]
        F.ribbon(back, 1, G4)
    # the bowl: hemisphere body below its rim (dark body, bright outline)
    rx, ry = k * rim_r, k * rim_r * sq
    body = arc(cx, cy, rx, rx * 0.95, math.radians(0), math.radians(180), 30)
    rimfront = arc(cx, cy, rx, ry, math.radians(180), math.radians(360), 30)
    F.path(body + rimfront[1:-1], fill=G6, stroke="none", sw=0)
    # outline of the body, subject weight, brightest
    F.ribbon(body, 2, G0)
    rim = arc(cx, cy, rx, ry, 0, 2 * math.pi, 31)[:-1]
    F.path(rim, fill=BK, stroke=G0, sw=2, bound=True)
    # orbits, front halves after the bowl
    for r in radii:
        front = [proj(r, math.radians(180 * s / 40)) for s in range(41)]
        F.ribbon(front, 1, G4)
    # planets: 2n antinodes per mode, strike 50 populates n = 2..4
    for idx, (r, n) in enumerate(zip(radii, (2, 3, 4, 5))):
        if n == 5:
            continue
        for p in range(2 * n):
            th = 2 * math.pi * p / (2 * n) + 0.35 * idx + 0.4
            x, y = proj(r, th)
            depth = math.sin(th)                       # nearer when sin > 0
            size = (3.6 - idx * 0.45) * (1 + 0.12 * depth)
            near = depth > -0.2 or abs(x - cx) > rx + size
            if not near and abs(x - cx) < rx and y > cy - ry - 2:
                continue                                # hidden behind the bowl
            F.circle(x, y, size, G2 if idx else G1, BK, 1, bound=True)
    # typeset labels at each orbit's right end
    for r, n in zip(radii, (2, 3, 4, 5)):
        x, y = proj(r, 0)
        F.text(x + 4, y + 4, f"n = {n}", G3)
    F.text(8, 208, "fig. 1  bowl modes", G3)
    return F


def main() -> None:
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        d = HERE / name
        d.mkdir(exist_ok=True)
        fr = fn()
        (d / "rest.svg").write_text(fr.svg())
        print(name, "nodes", fr.node)


if __name__ == "__main__":
    main()
