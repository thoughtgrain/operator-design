#!/usr/bin/env python3
"""Canyon v4, cleaned rest frame (owner pick). Helpers copied from ../sketch.py; writes clean.svg beside this file.

    python3 screens/canyon/passes/01-subject/v4/clean.py
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



FLOOR_Y = 200.0


def v4_clean(c):
    """P1 Section drawing, star atlas: the canyon cut across, its echoes plotted as stars between the walls.
    No lettering: the order of the echoes is the chain itself (it climbs from the shout, wall to wall)."""
    s = Svg()
    n, a = n_taps(c["walls"]), c["absorb"]
    half = 50 + 100 * c["distance"]
    for y in (48, 84, 120, 156, 192):
        pts = [(x, y + 0.0009 * (x - 240) ** 2 - 10) for x in range(4, 477, 12)]
        s.ribbon(pts, 1, G1)
    for m in (-3, -2, -1, 0, 1, 2, 3):
        pts = [(240 + m * 52 * (0.55 + 0.45 * (y - 24) / 190), y) for y in range(24, 197, 8)]
        s.ribbon(pts, 1, G1)
    left, right = wall_profile(-1, half), wall_profile(1, half)
    # one rock body in section: left rim, down the left wall, across the floor, up the right wall, right rim,
    # closed off screen so its outline never runs along (or clips at) the frame edges
    rim_l, rim_r = left[-1][1], right[-1][1]
    body = ([(-4, rim_l)] + left[::-1] + right + [(484, rim_r), (484, 226), (-4, 226)])
    s.poly(body, fill=G0, stroke=G4, sw=1.5)
    for prof, side in ((left, -1), (right, 1)):
        inset = [(x - side * 10, y) for x, y in prof[1:-1]]
        s.dashed(inset[::-1], 1, G2, dash=5, gap=4)

    def wall_x(prof, y):
        for (x1, y1), (x2, y2) in zip(prof, prof[1:]):
            if y2 <= y <= y1:
                return x1 + (x2 - x1) * (y1 - y) / (y1 - y2)
        return prof[-1][0]

    src = (240, 190)
    stars = []
    for k in range(1, n + 1):
        y = 190 - 146 * k / (n + 0.6)
        prof = right if k % 2 else left
        side = 1 if k % 2 else -1
        x = wall_x(prof, y) - side * 11
        wx, wy = wobble(k, c["wind"]) * 16, wobble(k + 50, c["wind"]) * 8
        stars.append((x + wx, y + wy, 1.8 + 4.2 * level(k, a), k))
    chain = [(src[0], src[1], 3.5)] + [(x, y, r) for x, y, r, _ in stars]
    for (x1, y1, r1), (x2, y2, r2) in zip(chain, chain[1:]):
        L = math.hypot(x2 - x1, y2 - y1)
        g1, g2 = (r1 + 4) / L, (r2 + 4) / L
        s.line(x1 + (x2 - x1) * g1, y1 + (y2 - y1) * g1, x2 - (x2 - x1) * g2, y2 - (y2 - y1) * g2, 1, G3)
    s.circle(src[0], src[1], 3.5, G0, G5, 1.2)
    # stars: size is the magnitude (absorb); the first echo is the one bright body, the rest one mid grey
    for x, y, r, k in stars:
        s.circle(x, y, r + 1.5, G0)
        s.circle(x, y, r, G7 if k == 1 else G5)
    return s


if __name__ == "__main__":
    v4_clean(DEFAULTS).write(HERE / "clean.svg", captions(DEFAULTS))
    print(HERE / "clean.svg")
