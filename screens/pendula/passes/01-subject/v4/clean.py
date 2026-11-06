#!/usr/bin/env python3
"""Pendula v4 (P12 orrery, patent section): cleanup of the rest sketch.

    python3 screens/pendula/passes/01-subject/v4/clean.py

Writes clean.svg next to this file (render: rsvg-convert -w 480 -h 220 -b black
clean.svg -o clean.png). Same idea and composition as sketch.py's v4: conical
pendulums on one spindle, their orbits stacked into a cone over a base dial, the
section plane through the spindle as the gate, every bob held on one radius
before release. Cleanup only: no numerals, figure label or section letters; the
bobs are spaced and sized so they no longer touch; the hub's section hatching is
true 45 degree hairlines 3.5 px apart; the cutting-plane line takes the Line
weight. Model and primitives copied from ../sketch.py.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ---- the machine's defaults (definition.json) ------------------------------
LENGTH_T = 0.4771          # 1.2 s, exponential 0.4..4 s
COUNT = 8                  # linear 3..16
SWING = 0.6                # 0..1
SCALE = "pent"
K = 16                     # longest pendulum makes K swings per realign cycle
SCALES = {
    "pent": [0, 2, 4, 7, 9],
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "dor": [0, 2, 3, 5, 7, 9, 10],
    "hira": [0, 2, 3, 7, 8],
    "chrom": list(range(12)),
}
HEADER_VALUES = ["1.2s", "8", "60", "pent"]
HEADER_TITLES = ["length", "count", "swing", "scale"]

G = {"ground": "#323232", "ground2": "#4B4B4B", "dim": "#646464", "mid": "#7D7D7D",
     "sec": "#969696", "sec2": "#AFAFAF", "hi": "#CDCDCD", "black": "#000000"}

W_HAIR, W_LINE, W_SUBJ = 1.0, 1.5, 2.0


def f(v: float) -> str:
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def swing_deg(t: float = SWING) -> float:
    return 10 + 35 * t


def scale_notes(n: int, scale: str = SCALE) -> list[int]:
    """Semitone of each pendulum, longest (lowest) first."""
    deg = SCALES[scale]
    return [deg[i % len(deg)] + 12 * (i // len(deg)) for i in range(n)]


# ---- drawing primitives: everything is a closed path, circle or text --------
class Svg:
    def __init__(self) -> None:
        self.items: list[str] = []

    def add(self, s: str) -> None:
        self.items.append(s)

    def ribbon(self, pts, w: float, col: str) -> None:
        """An open polyline as thin closed ribbons (filled, no stroke), ≤ 32 centre points each."""
        pts = dedupe(pts)
        if len(pts) < 2:
            return
        start = 0
        while start < len(pts) - 1:
            chunk = pts[start:start + 31]
            self._ribbon(chunk, w, col)
            start += 30

    def _ribbon(self, pts, w, col):
        h = w / 2
        left, right = [], []
        for i, p in enumerate(pts):
            a = pts[max(i - 1, 0)]
            b = pts[min(i + 1, len(pts) - 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(dx, dy) or 1
            nx, ny = -dy / ln, dx / ln
            left.append((p[0] + nx * h, p[1] + ny * h))
            right.append((p[0] - nx * h, p[1] - ny * h))
        ring = dedupe(left + right[::-1])
        self.add(f'<path d="{d_of(ring)}" fill="{col}" stroke="none" stroke-width="0"/>')

    def seg(self, a, b, w, col):
        self.ribbon([a, b], w, col)

    def poly(self, pts, stroke: str, w: float, fill: str = "none") -> None:
        """Closed outline (≤ 64 points)."""
        pts = dedupe(pts)
        self.add(f'<path d="{d_of(pts)}" fill="{fill}" stroke="{stroke}" stroke-width="{f(w)}"/>')

    def circle(self, c, r, stroke, w, fill="#000000"):
        self.add(f'<circle cx="{f(c[0])}" cy="{f(c[1])}" r="{f(r)}" fill="{fill}" stroke="{stroke}" stroke-width="{f(w)}"/>')

    def rect(self, x, y, w, h, fill, stroke="none", sw=0):
        self.add(f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" fill="{fill}" stroke="{stroke}" stroke-width="{f(sw)}"/>')

    def text(self, x, y, s, col=G["mid"], size=10):
        self.add(f'<text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{col}" stroke="none" '
                 f'font-family="UniversNextPro-Light" font-size="{size}px">{s}</text>')

    def write(self, path: Path, title: str) -> None:
        head = header()
        body = "\n  ".join(self.items)
        path.write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">\n'
            f'  <title>{title}</title>\n{head}\n  {body}\n</svg>\n')


def dedupe(pts):
    out = []
    for p in pts:
        p = (round(p[0], 3), round(p[1], 3))
        if not out or math.dist(out[-1], p) >= 0.2:
            out.append(p)
    if len(out) > 2 and math.dist(out[0], out[-1]) < 0.3:
        out.pop()
    return out


def d_of(pts) -> str:
    return "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"


def arc_pts(c, r, a0, a1, n=24):
    """Angles in degrees, 0 = straight down, positive = to the right."""
    out = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        out.append((c[0] + r * math.sin(a), c[1] + r * math.cos(a)))
    return out


def header() -> str:
    steps = ["#000000", "#323232", "#4B4B4B", "#646464", "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD"]
    rows = ['  <g id="preview_canvas">', '    <rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>',
            '  </g>', '  <g id="preview_header">']
    for i, c in enumerate(steps):
        rows.append(f'    <rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
    for i, t in enumerate(HEADER_TITLES):
        col = "#CBCBCB" if i < 2 else "#000000"
        rows.append(f'    <text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{col}" stroke="none" '
                    f'font-family="UniversNextPro-Light" font-size="10px">{t}</text>')
    for i, v in enumerate(HEADER_VALUES):
        col = "#CBCBCB" if i < 2 else "#000000"
        rows.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{col}" stroke="none" '
                    f'font-family="UniversNextPro-Light" font-size="20px">{v}</text>')
    rows.append("  </g>")
    return "\n".join(rows)


def inside(pt, poly):
    x, y = pt
    c = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def hatch(s: Svg, poly, spacing=3.5, inset=1.5, col=G["dim"]):
    """Section hatching: 45 degree hairlines (x + y = c) clipped to poly, `spacing` px apart square
    to the lines, ends pulled `inset` px back from the outline."""
    step = spacing * math.sqrt(2)
    sums = [x + y for x, y in poly]
    c = math.ceil(min(sums) / step) * step
    edges = list(zip(poly, poly[1:] + poly[:1]))
    while c < max(sums):
        xs = []
        for (x1, y1), (x2, y2) in edges:
            s1, s2 = x1 + y1 - c, x2 + y2 - c
            if (s1 > 0) != (s2 > 0):
                xs.append(x1 + (x2 - x1) * s1 / (s1 - s2))
        xs.sort()
        for a, b in zip(xs[0::2], xs[1::2]):
            a, b = a + inset / math.sqrt(2), b - inset / math.sqrt(2)
            if (b - a) * math.sqrt(2) >= 3.0:
                s.seg((a, c - a), (b, c - b), W_HAIR, col)
        c += step


# ---- v4 · P12 Orrery · patent section ---------------------------------------
SPREAD = 0.64          # shortest rod as a share of the longest: 1 - SPREAD (sketch: 0.55)


def v4() -> Svg:
    s = Svg()
    n = COUNT
    th = math.radians(swing_deg())
    L0 = 70 + 70 * LENGTH_T
    lens = [L0 * (1 - SPREAD * i / (n - 1)) for i in range(n)]
    e = math.radians(22)
    cam = math.radians(28)
    cx, piv_y = 240.0, 43.0

    def P(x, y, z):  # world: x right, y away, z up; pivot at origin
        xr = x * math.cos(cam) - y * math.sin(cam)
        yr = x * math.sin(cam) + y * math.cos(cam)
        return (cx + xr, piv_y - (z * math.cos(e)) - yr * math.sin(e))

    def circ(r, z, a0, a1, m=30):
        return [P(r * math.cos(a0 + (a1 - a0) * k / m), r * math.sin(a0 + (a1 - a0) * k / m), z) for k in range(m + 1)]

    base_z = -140.0
    br = 84
    # Base plate and its dial: scale degrees long (Line), the rest short (Hairline), both >= 4 px on screen.
    s.poly(circ(br, base_z, 0, 2 * math.pi, 60)[:-1], G["dim"], W_LINE, G["black"])
    deg = set(SCALES[SCALE])
    for k in range(12):
        a = math.pi / 2 + 2 * math.pi * k / 12
        r0 = br - (18 if k in deg else 11)
        s.ribbon([P(r0 * math.cos(a), r0 * math.sin(a), base_z), P((br - 3) * math.cos(a), (br - 3) * math.sin(a), base_z)],
                 W_LINE if k in deg else W_HAIR, G["mid"] if k in deg else G["dim"])
    # The gate: the section plane x = 0. Its trace on the plate is a cutting-plane line: Line-weight
    # ends past the rim, long hairline dashes across the plate (each dash >= 6 px).
    for y0, y1 in ((-br - 15, -br - 4), (br + 4, br + 15)):
        s.ribbon([P(0, y0, base_z), P(0, y1, base_z)], W_LINE, G["sec"])
    yy = -br + 6
    while yy + 8 <= br - 6:
        s.ribbon([P(0, yy, base_z), P(0, yy + 8, base_z)], W_HAIR, G["mid"])
        yy += 14
    orbits = [(L * math.sin(th), -L * math.cos(th)) for L in lens]
    lo, hi = -cam, math.pi - cam
    # Back halves of the orbits (behind the spindle).
    for r, z in orbits:
        s.ribbon(circ(r, z, lo, hi), W_HAIR, G["ground2"])
    # Spindle and hub; the hub is cut by the section plane, so it carries section hatching.
    for dx in (-3.5, 3.5):
        s.ribbon([P(dx, 0, -5), P(dx, 0, base_z)], W_LINE, G["mid"])
    hub = [P(-10, 0, 10), P(10, 0, 10), P(10, 0, -6), P(-10, 0, -6)]
    s.poly(hub, G["sec"], W_LINE, G["black"])
    hatch(s, hub)
    # Front halves of the orbits.
    for r, z in orbits:
        s.ribbon(circ(r, z, hi, lo + 2 * math.pi), W_HAIR, G["dim"])
    # Held at release: every bob on one radius, front left, on one rod from the hub.
    az = math.radians(200)
    tip = lens[0]
    bobs = [P(r * math.cos(az), r * math.sin(az), z) for r, z in orbits]
    s.ribbon([P(0, 0, -6), P(tip * math.sin(th) * math.cos(az), tip * math.sin(th) * math.sin(az), -tip * math.cos(th))],
             W_LINE, G["sec"])
    gap = min(math.dist(a, b) for a, b in zip(bobs, bobs[1:]))
    # Bobs are solid bodies: one bright mass each, no ring (a 2 px ring this small left a pinhole).
    rb = min(3.6, (gap - 3) / 2)                    # >= 3 px of black between neighbouring bobs
    for c in bobs:
        s.circle(c, rb, "none", 0, G["hi"])
    return s


def main() -> None:
    v4().write(HERE / "clean.svg", "pendula v4 rest · clean")
    print("wrote clean.svg")


if __name__ == "__main__":
    main()
