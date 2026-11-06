#!/usr/bin/env python3
"""Rain, subject pass 01: five rest-frame sketches from one script.

Each variant is its own pattern x drawing language (see pass.json). Every frame
is 480 x 220, keeps the stock header and draws the controls at their defaults:
rate 1.0 drops a beat, roof 12 st, gust 0, puddle 0.

    python3 screens/rain/passes/01-subject/sketch.py

Device rules kept even at sketch stage: one subpath per path, <= 64 points,
lines as closed filled ribbons, explicit paint on every leaf, grey only,
<= 3 fractional digits. Sketches have no bound nodes yet (that's phase 4).
"""
from __future__ import annotations

import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent

D = {"rate": 0.4, "roof": 1 / 3, "gust": 0.5, "puddle": 0.0}
RATE = 0.25 * 32 ** D["rate"]          # drops per beat: 1.0
SPAN = 36 * D["roof"]                  # semitones: 12
GUST = 2 * D["gust"] - 1               # -1..1: 0
PUDDLE = D["puddle"]                   # 0..1: 0
LABELS = ["rate", "roof", "gust", "puddle"]
VALUES = ["1.0", "12", "0", "0"]

G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
FONT = "UniversNextPro-Light"
SCALE = [0, 2, 4, 5, 7, 9, 11]         # major scale degrees, for the tile courses


def f(v: float) -> str:
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def courses(span: float) -> list[int]:
    """Semitone offsets of the tile courses a span covers (scale notes)."""
    out = []
    octv = 0
    while True:
        for d in SCALE:
            st = 12 * octv + d
            if st > span + 1e-6:
                return out
            out.append(st)
        octv += 1


# ---------------------------------------------------------------- primitives
class Frame:
    def __init__(self, title: str):
        self.title = title
        self.items: list[str] = []

    def add(self, s: str) -> None:
        self.items.append(s)

    def poly(self, pts, fill, stroke="none", sw=0.0):
        pts = dedupe(pts)
        assert 3 <= len(pts) <= 64, len(pts)
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
        sws = f' stroke-width="{f(sw)}"' if stroke != "none" else ' stroke-width="0"'
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def ribbon(self, pts, w, colour):
        """An open line of width w as closed filled ribbons, <= 30 segments a piece."""
        pts = dedupe(pts, close=False)
        n, i = 30, 0
        while i < len(pts) - 1:
            self._piece(pts[i:i + n + 1], w, colour)
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
            ln = math.hypot(dx, dy) or 1
            nx, ny = -dy / ln, dx / ln
            left.append((x + nx * h, y + ny * h))
            right.append((x - nx * h, y - ny * h))
        self.poly(left + right[::-1], colour)

    def line(self, a, b, w, colour):
        self._piece([a, b], w, colour)

    def ring(self, cx, cy, r, colour, sw, fill="none"):
        sws = f' stroke-width="{f(sw)}"' if colour != "none" else ' stroke-width="0"'
        self.add(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}" stroke="{colour}"{sws}/>')

    def disc(self, cx, cy, r, fill):
        self.ring(cx, cy, r, "none", 0, fill)

    def rect(self, x, y, w, h, fill):
        self.add(f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" fill="{fill}" stroke="none" stroke-width="0"/>')

    def text(self, x, y, s, colour=G4, size=10):
        self.add(f'<text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{colour}" stroke="none" '
                 f'stroke-width="0" font-family="{FONT}" font-size="{size}px">{s}</text>')

    def svg(self) -> str:
        head = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
            f"  <title>rain · subject pass 01 · {self.title}</title>",
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
            head.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{c}" stroke="none" '
                        f'font-family="{FONT}" font-size="20px">{VALUES[i]}</text>')
        head.append("  </g>")
        return "\n".join(head + ["  " + s for s in self.items] + ["</svg>", ""])


def dedupe(pts, close=True):
    out = []
    for p in pts:
        p = (round(p[0], 3), round(p[1], 3))
        if not out or math.dist(out[-1], p) >= 0.2:
            out.append(p)
    if close and len(out) > 2 and math.dist(out[0], out[-1]) < 0.3:
        out.pop()
    return out


def arc(cx, cy, r, a0, a1, n=24):
    return [(cx + r * math.cos(a0 + (a1 - a0) * k / n), cy + r * math.sin(a0 + (a1 - a0) * k / n))
            for k in range(n + 1)]


def recent_drops(n_bar: int, seed: int, n_courses: int):
    """The last bar's drops: (course index, angle/slot, age 0 newest .. 1 oldest)."""
    rnd = random.Random(seed)
    return [(rnd.randrange(n_courses), rnd.random(), k / max(1, n_bar - 1)) for k in range(n_bar)]


# ---------------------------------------------------------------- v1 · P12 orrery · survey plan
def v1() -> Frame:
    fr = Frame("v1 · P12 orrery · survey plan")
    cx, cy = 240, 119
    cs = courses(SPAN)                       # 8 courses for 12 st (incl. the octave)
    n = len(cs)
    r_in, r_out = 14, 84
    radii = [r_out - (r_out - r_in) * k / (n - 1) for k in range(n)]   # course 0 (lowest) at the eave
    r_gut = 93
    # hips: eight radial hairlines, ridge to eave (the roof's plan)
    for k in range(8):
        a = math.pi / 8 + k * math.pi / 4
        fr.line((cx + r_in * math.cos(a), cy + r_in * math.sin(a)),
                (cx + r_out * math.cos(a), cy + r_out * math.sin(a)), 1, G2)
    # tile courses: concentric orbits, evenly spaced (a plan is a projection straight down)
    for k, r in enumerate(radii):
        fr.ring(cx, cy, r, G3 if k % 7 else G4, 1)
    # gutter: the puddle's orbit, a double line
    fr.ring(cx, cy, r_gut, G4, 1.5)
    fr.ring(cx, cy, r_gut - 4, G2, 1)
    # finial at the ridge: the orrery's sun, a dark body with a bright-ish rim
    fr.ring(cx, cy, 7, G5, 1.5, G0)
    # drops landed this bar (rate 1/beat -> 4), each on the course of its note
    rnd = random.Random(7)
    drops = [(3, 0.12), (6, 0.37), (1, 0.61), (4, 0.83)]
    for i, (c, t) in enumerate(drops):
        a = -math.pi / 2 + t * 2 * math.pi
        x, y = cx + radii[c] * math.cos(a), cy + radii[c] * math.sin(a)
        if i == len(drops) - 1:
            fr.disc(x, y, 4.5, G7)                       # the drop that just sounded: brightest
        else:
            fr.disc(x, y, 3.5, G0)
            fr.ring(x, y, 3, [G4, G5, G5][i], 1.5)
    # survey furniture: north point, chainage along one hip, scale bar, station names
    nx, ny = 412, 58
    fr.line((nx, ny + 22), (nx, ny - 4), 1, G4)
    fr.poly([(nx, ny - 8), (nx + 4, ny + 2), (nx, ny), (nx - 4, ny + 2)], G4)
    fr.text(nx - 3, ny + 34, "n", G4)
    # course chainage along the east axis: semitones above the eave course
    for k in (0, 2, 4, 7):
        r = radii[k]
        fr.line((cx + r, cy - 1.5), (cx + r, cy + 3), 1, G4)
    fr.text(cx + 99, cy + 4, "eave", G4)
    fr.line((cx + 5, cy - 5), (cx + 60, cy - 72), 1, G3)       # leader from the ridge finial
    fr.text(cx + 63, cy - 74, "ridge +12", G4)
    # scale bar, bottom left: 0 . 6 . 12 st across the plan's radius
    bx, by = 34, 200
    fr.line((bx, by), (bx + 70, by), 1, G4)
    for k in range(3):
        fr.line((bx + 35 * k, by - 4), (bx + 35 * k, by + 0.5), 1, G4)
    fr.text(bx - 2, by - 8, "0", G4)
    fr.text(bx + 31, by - 8, "6", G4)
    fr.text(bx + 64, by - 8, "12 st", G4)
    fr.text(34, 40, "plan · roof", G4)
    fr.text(cx + 100, cy + 82, "gutter", G4)
    fr.line((cx + 66, cy + 66), (cx + 98, cy + 80), 1, G3)
    return fr


# ---------------------------------------------------------------- v2 · P13 capture · patent section
def v2() -> Frame:
    fr = Frame("v2 · P13 capture · patent section")
    angle = math.radians(6 + 40 * D["roof"] * 1.0)       # roof 12 st -> ~19.3 deg
    ex, ey = 82, 176                                        # eave point on the rafter line
    length = 320
    u = (math.cos(angle), -math.sin(angle))                 # up the slope
    nrm = (-math.sin(angle), -math.cos(angle))              # normal, pointing up and out

    def P(s, h):
        return (ex + u[0] * s + nrm[0] * h, ey + u[1] * s + nrm[1] * h)

    # rafter in section: a band under the tiles, cut face hatched at 5 px
    rt = 9
    band = [P(-6, -2), P(length + 4, -2), P(length + 4, -2 - rt), P(-6, -2 - rt)]
    fr.poly(band, G0, G4, 1.5)
    s = 2
    while s < length:
        a, b = P(s + rt * 0.8, -3.2), P(s, -2 - rt + 1.2)
        fr.line(a, b, 1, G2)
        s += 6
    # wall posts under eave and ridge, hatched sections
    for s0 in (10, length - 16):
        p = P(s0, -2 - rt)
        x0 = p[0]
        y0 = p[1]
        fr.poly([(x0, y0), (x0 + 12, y0 - 12 * math.tan(angle)), (x0 + 12, 208), (x0, 208)], G0, G4, 1.5)
        yy = y0 + 4
        while yy < 204:
            fr.line((x0 + 1.5, yy + 4), (x0 + 10.5, yy - 5), 1, G2)
            yy += 6
    # tile courses: overlapping plates, lowest first so each upper tile laps the one below
    cs = courses(SPAN)
    n = len(cs)
    L = length / n
    struck = 5
    for i in range(n):
        s0, s1 = i * L - 6, (i + 1) * L
        pts = [P(s0, 5.5), P(s1, 0.5), P(s1, 3.5), P(s0 + 1.5, 8.5)]
        if i == struck:
            fr.poly(pts, G7, G7, 1)
        else:
            fr.poly(pts, G0, G5, 1.5)
    # gutter at the eave: a half-round in section, its water level is puddle
    gx, gy = P(-10, 2)
    gx -= 4
    gy += 6
    g = arc(gx, gy, 10, 0, math.pi, 20)
    fr.ribbon(g, 2, G5)
    fr.line((gx - 10, gy), (gx - 13, gy - 3), 1.5, G5)
    fr.line((gx - 7, gy + 8), (gx + 7, gy + 8), 1, G3)       # water line: low at puddle 0
    # drops falling: short streaks, vertical at gust 0, one per beat of the bar
    lean = GUST * 0.6
    for k, (s_hit, top) in enumerate([(0.16, 44), (0.38, 30), (0.83, 38), ((struck + 0.5) / n, 0)]):
        hx, hy = P(s_hit * length, 9)
        if top == 0:
            # the drop just captured by the struck course: a tiny splash above it, two plates
            fr.line((hx - 7, hy - 5), (hx - 3, hy - 1.5), 1.5, G6)
            fr.line((hx + 7, hy - 5), (hx + 3, hy - 1.5), 1.5, G6)
            continue
        y1 = hy - top
        fr.line((hx + lean * top, y1 - 16), (hx + lean * top, y1), 1.5, G5)
    # patent callouts: numbers with leader lines
    def call(num, at, tx, ty):
        fr.line(at, (tx + 6, ty - 4), 1, G3)
        fr.text(tx - 10 if tx < at[0] else tx + 8, ty, num, G4)
    tp = P((struck + 0.5) * L, 9)
    call("10", tp, tp[0] - 28, tp[1] - 26)
    rp = P(length * 0.4, -8)
    call("12", rp, rp[0] + 10, rp[1] + 26)
    call("14", (gx - 6, gy + 9), gx - 4, gy + 30)
    rid = P(length - 2, 6)
    call("16", rid, rid[0] + 18, rid[1] - 10)
    fr.text(420, 205, "fig. 1", G4)
    return fr


# ---------------------------------------------------------------- v3 · P14 loom · hidden-line isometric
def v3() -> Frame:
    fr = Frame("v3 · P14 loom · hidden-line isometric")
    cols = len(courses(SPAN))        # 8 warp threads at 12 st
    rows = 4                         # this bar + three behind
    k = 22                           # world unit along a thread (column)
    kr = 30                          # world unit along the weft (row, back up the roof)
    ox, oy = 128, 150
    c30, s30 = 0.866, 0.5
    slope = 0.42                     # roof rise per unit of depth

    def S(x, y, z=0.0):
        # x: column (pitch), y: row back up the roof (older), z: up
        X = ox + x * c30 * k + y * c30 * kr * 0.55
        Y = oy + x * s30 * k * 0.55 - y * s30 * kr * 0.9 - (z + y * kr * slope)
        return (X, Y)

    # hits per row (4 per bar at rate 1/beat), gust 0 so no drift, puddle 0 so no repeats
    hits = {0: [1, 3, 4, 6], 1: [0, 3, 5, 7], 2: [2, 4, 5, 7], 3: [1, 2, 4, 6]}
    # warp threads: hairlines running up the roof (drawn first, behind everything)
    for c in range(cols + 1):
        fr.line(S(c, -0.2), S(c, rows + 0.25), 1, G2)
    # cells back to front
    order = sorted(((c, r) for r in range(rows) for c in range(cols)), key=lambda t: (-t[1], t[0]))
    h = 6
    pad = 0.12
    for c, r in order:
        x0, x1, y0, y1 = c + pad, c + 1 - pad, r + pad, r + 1 - pad
        if c in hits[r]:
            newest = r == 0 and c == 6
            top = [S(x0, y0, h), S(x1, y0, h), S(x1, y1, h), S(x0, y1, h)]
            front = [S(x0, y0, 0), S(x1, y0, 0), S(x1, y0, h), S(x0, y0, h)]
            side = [S(x1, y0, 0), S(x1, y1, 0), S(x1, y1, h), S(x1, y0, h)]
            if r == 0:
                # this bar: solid slabs (they sounded); the newest is the brightest thing
                fr.poly(front, G2, G4, 1)
                fr.poly(side, G1, G4, 1)
                fr.poly(top, G7 if newest else G5, G7 if newest else G5, 1)
            else:
                # earlier bars: hidden-line wire slabs, black fill, grey edge
                edge = [G4, G3, G3][r - 1]
                fr.poly(front, G0, edge, 1)
                fr.poly(side, G0, edge, 1)
                fr.poly(top, G0, edge, 1)
        else:
            fr.poly([S(x0, y0), S(x1, y0), S(x1, y1), S(x0, y1)], G0, G2, 1)
    # eave fascia along the front edge, ridge along the back
    fr.ribbon([S(-0.1, -0.15), S(cols + 0.1, -0.15)], 1.5, G4)
    fr.ribbon([S(-0.1, rows + 0.25), S(cols + 0.1, rows + 0.25)], 1.5, G3)
    # labels: rows by age, threads by pitch
    for r, lab in enumerate(["now", "-1", "-2", "-3"]):
        x, y = S(cols + 0.35, r + 0.5)
        fr.text(x + 2, y + 4, lab, G4 if r else G5)
    x, y = S(0, -0.15)
    fr.text(x - 26, y + 4, "0 st", G4)
    x, y = S(cols, -0.15)
    fr.text(x - 40, y + 4, "+12", G4)
    x, y = S(-0.4, rows + 0.4)
    fr.text(x - 30, y - 2, "ridge", G4)
    return fr


# ---------------------------------------------------------------- v4 · P5 field and figure · star atlas
def v4() -> Frame:
    fr = Frame("v4 · P5 field and figure · star atlas")
    # field: a conic graticule, parallels as arcs about a pole above the screen, meridians as rays
    px, py = 240, -300
    for rr in (360, 405, 450, 495):
        lim = math.acos((28 - py) / rr)        # stop each parallel where it would climb past y 28
        a0 = max(math.pi / 2 - 0.62, math.pi / 2 - lim)
        fr.ribbon(arc(px, py, rr, a0, math.pi - a0, 40), 1, G1)
    for m in range(-3, 4):
        a = math.pi / 2 + m * 0.17
        r0 = max(352, (30 - py) / math.sin(a))
        fr.line((px + r0 * math.cos(a), py + r0 * math.sin(a)), (px + 500 * math.cos(a), py + 500 * math.sin(a)), 1, G1)
    fr.text(420, 140, "+20°", G4)
    # figure: the roof as a constellation, eaves to ridge; tile stars are the courses
    rise = 34 + 48 * D["roof"]                 # ridge height above the eaves: 50 px at 12 st
    eL, eR, ridge = (138, 168), (342, 168), (240, 168 - rise)
    cs = courses(SPAN)
    n = len(cs)
    stars = []
    for i in range(n):
        t = i / (n - 1)
        stars.append((eL[0] + (ridge[0] - eL[0]) * t, eL[1] + (ridge[1] - eL[1]) * t))
    for i in range(1, n):
        t = i / (n - 1)
        stars.append((eR[0] + (ridge[0] - eR[0]) * t, eR[1] + (ridge[1] - eR[1]) * t))
    # constellation lines, broken short of each star the way an atlas draws them
    def figline(a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy)
        g = 5 / ln
        fr.line((a[0] + dx * g, a[1] + dy * g), (b[0] - dx * g, b[1] - dy * g), 1, G4)
    for i in range(n - 1):
        figline(stars[i], stars[i + 1])
    figline(stars[n - 1], stars[n])
    for i in range(n, 2 * n - 2):
        figline(stars[i], stars[i + 1])
    figline(eL, eR)
    # stars: magnitude by course (lower courses brighter in the atlas sense = bigger)
    hit = 4                                     # the course that just sounded
    for i, (x, y) in enumerate(stars):
        course = i if i < n else (2 * n - 2 - i)
        r = 3.2 - 1.2 * course / (n - 1)
        if i == hit:
            fr.disc(x, y, 4.5, G7)
        else:
            fr.disc(x, y, r, G5)
    # meteor trails: drops plotted back toward the radiant (gust moves it along the ecliptic)
    rad = (240 + 150 * GUST, 40)
    fr.ring(rad[0], rad[1], 4, G4, 1)
    fr.line((rad[0] - 9, rad[1]), (rad[0] - 6, rad[1]), 1, G4)
    fr.line((rad[0] + 6, rad[1]), (rad[0] + 9, rad[1]), 1, G4)
    fr.text(rad[0] + 12, rad[1] + 4, "radiant", G4)
    for target, frac in ((stars[hit], 1.0), (stars[n + 2], 0.0), (stars[1], 0.0), (stars[2 * n - 3], 0.0)):
        dx, dy = target[0] - rad[0], target[1] - rad[1]
        ln = math.hypot(dx, dy)
        ux, uy = dx / ln, dy / ln
        end = (target[0] - ux * 8, target[1] - uy * 8)
        start = (end[0] - ux * 26, end[1] - uy * 26)
        if frac:
            fr.ribbon([start, end], 1.5, G6)
        else:
            fr.ribbon([start, end], 1, G4)
    # puddle: an open cluster below the left eave, drawn as an atlas draws one (a dotted ring)
    pc = (98, 188)
    for k in range(14):
        a = k * 2 * math.pi / 14
        fr.disc(pc[0] + 13 * math.cos(a), pc[1] + 13 * math.sin(a), 0.9, G3)
    fr.text(pc[0] - 52, pc[1] + 4, "puddle", G4)
    fr.text(eR[0] + 14, eR[1] + 4, "tegula", G4)
    # activity strip: the last 16 beats, a tick per beat, taller where a drop fell
    sx = 172
    for k in range(16):
        x = sx + k * 9
        dropped = k in (0, 4, 8, 12)
        fr.rect(x, 206 - (6 if dropped else 2), 4, 6 if dropped else 2, G4 if dropped else G2)
    return fr


# ---------------------------------------------------------------- v5 · P9 one-bit ink · engineering schematic
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def inside(poly, x, y):
    c = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


def dither(fr: Frame, poly, level: float, cell=2, colour=G7):
    """Ordered dither inside poly, as run-length rects (static artwork only)."""
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    x0, x1 = int(min(xs)) // cell * cell, int(max(xs)) + cell
    y0, y1 = int(min(ys)) // cell * cell, int(max(ys)) + cell
    thr = level * 16
    for y in range(y0, y1, cell):
        run = None
        for x in range(x0, x1 + cell, cell):
            on = (x < x1 and inside(poly, x + cell / 2, y + cell / 2)
                  and BAYER[(y // cell) % 4][(x // cell) % 4] < thr)
            if on and run is None:
                run = x
            elif not on and run is not None:
                fr.rect(run, y, x - run, cell, colour)
                run = None


def inset(poly, d):
    """Shrink a convex polygon by d (for the 1 px black gutter inside every outline)."""
    n = len(poly)
    cx = sum(p[0] for p in poly) / n
    cy = sum(p[1] for p in poly) / n
    out = []
    for x, y in poly:
        dx, dy = x - cx, y - cy
        ln = math.hypot(dx, dy) or 1
        out.append((x - dx / ln * d, y - dy / ln * d))
    return out


def v5() -> Frame:
    fr = Frame("v5 · P9 one-bit ink · engineering schematic")
    # hero: the roof in elevation, a gable of tile courses, each course a dither band
    ridge = (196, 52)
    eL, eR = (84, 132), (308, 132)
    cs = courses(SPAN)
    n = len(cs)
    def lerp(a, b, t):
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        band = [lerp(eL, ridge, t0), lerp(eR, ridge, t0), lerp(eR, ridge, t1), lerp(eL, ridge, t1)]
        if i == n - 1:
            band = [lerp(eL, ridge, t0), lerp(eR, ridge, t0), ridge]
        level = 0.25 if i % 2 == 0 else 0.5
        dither(fr, inset(band, 2.5), level, 2, G6)
    # course lines: hard 2 px outlines between bands
    for i in range(1, n):
        t = i / n
        fr.line(lerp(eL, ridge, t), lerp(eR, ridge, t), 2, G6)
    # the gable outline: the one bright mass, 2.5 px
    fr.ribbon([(eL[0] - 10, eL[1] + 6), ridge, (eR[0] + 10, eR[1] + 6)], 2.5, G7)
    # fascia and gutter: a flat-grey channel under the eaves, then the wall in solid black
    fr.poly([(eL[0] - 6, 140), (eR[0] + 6, 140), (eR[0] + 6, 147), (eL[0] - 6, 147)], G3, G6, 2)
    fr.poly([(104, 147), (288, 147), (288, 196), (104, 196)], G0, G5, 2)
    dither(fr, inset([(104, 147), (288, 147), (288, 196), (104, 196)], 3.5), 0.125, 2, G4)
    # puddle: a flat plane at the downpipe foot (moves, so flat grey, no dither)
    fr.poly([(300, 202), (344, 202), (336, 208), (306, 208)], G3, G6, 2)
    fr.line((296, 147), (296, 198), 2, G5)
    # rain: four flat streak glyphs above the roof, vertical at gust 0
    for x, y in ((120, 40), (176, 30), (236, 36), (282, 58)):
        fr.poly([(x, y), (x + 3, y), (x + 3, y + 14), (x, y + 14)], G5, G5, 0.5)
    # schematic layer: leader wires from each glyph to a terminal, labelled like a drawing's parts
    def term(at, to, lab):
        fr.ribbon([at, (to[0], at[1]), to], 1, G4)
        fr.ring(to[0], to[1], 3, G4, 1, G0)
        fr.text(to[0] + 8, to[1] + 4, lab, G4)
    term((124, 40), (372, 44), "r1  rate")
    term((300, 104), (372, 84), "f1  roof")
    term((340, 205), (372, 164), "p1  puddle")
    # gust: a flat wind glyph at the left, three short horizontal strokes (centred: calm)
    for k, w in enumerate((22, 30, 16)):
        fr.line((28, 70 + 9 * k), (28 + w, 70 + 9 * k), 2, G5)
    fr.text(24, 108, "g1  gust", G4)
    return fr


def main() -> None:
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        out = HERE / name / "rest.svg"
        out.parent.mkdir(exist_ok=True)
        out.write_text(fn().svg(), encoding="utf-8")
        print(out)


if __name__ == "__main__":
    main()
