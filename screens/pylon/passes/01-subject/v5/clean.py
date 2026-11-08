#!/usr/bin/env python3
"""Pylon v5, cleaned rest frame (owner pick). Helpers copied from ../sketch.py; writes clean.svg beside this file.

    python3 screens/pylon/passes/01-subject/v5/clean.py
"""
from __future__ import annotations

import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONT = "UniversNextPro-Light"
HAIR, LINE, SUBJ = 1.1, 1.5, 2.0
G0, G1, G2, G3, G4, G5, G6, G7 = "#000000", "#323232", "#4B4B4B", "#646464", "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD"

# ---- the machine model (shared by every variant) -----------------------------------------------------------------
DEFAULTS = {"wind": 0.5637, "span": 0.5981, "gust": 0.0, "hum": 0.0}


def wind_ms(x):
    return 0.5 * 40 ** x


def span_m(x):
    return 20 * 20 ** x


def lock_mode(p):
    """mode number the shed vortices lock onto: Strouhal frequency over the span's mode spacing (3 at defaults)"""
    return max(1.0, wind_ms(p["wind"]) * span_m(p["span"]) / 160.0)


def mode_weights(p, nmax=12):
    nstar = lock_mode(p)
    sigma = 0.55 + 1.6 * p["gust"]
    return {n: math.exp(-((n - nstar) ** 2) / (2 * sigma * sigma)) for n in range(1, nmax + 1)}


def captions(p):
    return [f"{wind_ms(p['wind']):.1f}", f"{span_m(p['span']):.0f}", f"{round(p['gust'] * 100)}", f"{round(p['hum'] * 100)}"]


# ---- svg helpers ---------------------------------------------------------------------------------------------------
def f(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


class Frame:
    def __init__(self, prefix="pylon"):
        self.out = []
        self.prefix = prefix
        self.nodes = 0

    def _id(self, bind):
        if not bind:
            return ""
        i = self.nodes
        self.nodes += 1
        return f' id="{self.prefix}_node_{i}"'

    def poly(self, pts, fill, stroke="none", sw=None, bind=False):
        pts = dedupe(pts)
        if len(pts) < 3:
            return
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
        swa = f' stroke-width="{f(sw)}"' if stroke != "none" else ""
        self.out.append(f'<path{self._id(bind)} d="{d}" fill="{fill}" stroke="{stroke}"{swa}/>')

    def ribbon(self, pts, w, fill, bind=False):
        """a line as a thin closed ribbon, split into pieces of <= 62 points"""
        pts = dedupe(pts)
        step = 30
        i = 0
        while i < len(pts) - 1:
            chunk = pts[i:i + step + 1]
            self.poly(offset_ribbon(chunk, w), fill, bind=bind)
            i += step

    def seg(self, a, b, w, fill):
        self.ribbon([a, b], w, fill)

    def circle(self, c, r, fill, stroke="none", sw=None, bind=False):
        swa = f' stroke-width="{f(sw)}"' if stroke != "none" else ""
        self.out.append(f'<circle{self._id(bind)} cx="{f(c[0])}" cy="{f(c[1])}" r="{f(r)}" fill="{fill}" stroke="{stroke}"{swa}/>')

    def text(self, x, y, s, fill=G4, size=10):
        self.out.append(f'<text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{fill}" stroke="none" '
                        f'font-family="{FONT}" font-size="{size}px">{s}</text>')

    def svg(self, p, palette):
        head = header(p)
        pal = "".join(f'<path id="{self.prefix}_palette_{i}" d="M {700 + 10 * i} 300 L {704 + 10 * i} 300 L {704 + 10 * i} 304 Z" '
                      f'fill="{c}" stroke="{c}" stroke-width="2"/>\n' for i, c in enumerate(palette))
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">\n'
                '<g id="preview_canvas"><rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/></g>\n'
                + head + pal + "\n".join(self.out) + "\n</svg>\n")


def dedupe(pts):
    out = []
    for p in pts:
        p = (round(p[0], 2), round(p[1], 2))
        if not out or math.dist(out[-1], p) >= 0.3:
            out.append(p)
    if len(out) > 2 and math.dist(out[0], out[-1]) < 0.3:
        out.pop()
    return out


def offset_ribbon(pts, w):
    h = w / 2
    left, right = [], []
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L * h, dx / L * h
        left.append((x + nx, y + ny))
        right.append((x - nx, y - ny))
    return left + right[::-1]


def header(p):
    steps = [G0, G1, G2, G3, G4, G5, G6, G7]
    s = '<g id="preview_header">\n'
    for i, c in enumerate(steps):
        s += f'<rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>\n'
    for i, (lab, val) in enumerate(zip(["wind", "span", "gust", "hum"], captions(p))):
        c = "#CBCBCB" if i < 2 else "#000000"
        s += (f'<text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{c}" stroke="none" font-family="{FONT}" '
              f'font-size="10px">{lab}</text>\n')
        s += (f'<text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{c}" stroke="none" font-family="{FONT}" '
              f'font-size="20px">{val}</text>\n')
    return s + "</g>\n"


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def hatch_quad(fr, q, spacing, w, fill):
    """45-degree section hatching inside a parallelogram q = (origin, edge a, edge b), clipped in its own coordinates"""
    o, ea, eb = q
    la, lb = math.hypot(*ea), math.hypot(*eb)
    n = int((la + lb) / spacing)
    for k in range(1, n):
        c = k * spacing
        # line s*la - t*lb = c - lb  in (s, t) in [0,1]^2 (screen-ish distance along each edge)
        pts = []
        for s in (0.0, 1.0):
            t = (s * la + lb - c) / lb
            if 0 <= t <= 1:
                pts.append((s, t))
        for t in (0.0, 1.0):
            s = (c - lb + t * lb) / la
            if 0 <= s <= 1:
                pts.append((s, t))
        pts = sorted(set((round(a, 4), round(b, 4)) for a, b in pts))
        if len(pts) < 2:
            continue
        (s0, t0), (s1, t1) = pts[0], pts[-1]
        A = (o[0] + ea[0] * s0 + eb[0] * t0, o[1] + ea[1] * s0 + eb[1] * t0)
        B = (o[0] + ea[0] * s1 + eb[0] * t1, o[1] + ea[1] * s1 + eb[1] * t1)
        if math.dist(A, B) > 3:
            fr.seg(A, B, w, fill)




# ---- v5 cleaned · P14 loom, oscilloscope trace --------------------------------------------------------------------------
def channel_mark(fr, y, strokes, x0=31.0, length=6.0, gap=4.0):
    """A scope's channel ground marker in the graticule's own hairlines, just outside the left edge at the trace's zero:
    one stroke for the wire (ch1), two for the mains (ch2). Drawn, not lettered."""
    offs = [0.0] if strokes == 1 else [-gap / 2, gap / 2]
    for o in offs:
        fr.seg((x0, y + o), (x0 + length, y + o), HAIR, G4)


def v5_clean(p):
    fr = Frame()
    gx0, gx1, gy0, gy1 = 40.0, 440.0, 30.0, 210.0
    for k in range(11):
        x = gx0 + (gx1 - gx0) * k / 10
        fr.seg((x, gy0), (x, gy1), HAIR, G1)
    for k in range(7):
        y = gy0 + (gy1 - gy0) * k / 6
        fr.seg((gx0, y), (gx1, y), HAIR, G1)
    cy = gy0 + (gy1 - gy0) * 3 / 6
    for k in range(51):
        x = gx0 + (gx1 - gx0) * k / 50
        if k % 5:
            fr.seg((x, cy - 3), (x, cy + 3), HAIR, G2)
    rows = 4
    step = 6 + 16 * p["span"]
    n = max(1, round(lock_mode(p)))
    rng = random.Random(5)
    base = (60.0, 150.0)
    L = 300.0
    greys = [G7, G5, G4, G3]
    for k in range(n + 1):
        x = base[0] + L * k / n
        fr.seg((x, base[1]), (x + step * (rows - 1), base[1] - step * (rows - 1)), HAIR, G2)
    for r in reversed(range(rows)):
        dn = 0.0
        if p["gust"] > 0:
            dn = p["gust"] * (rng.random() * 2 - 1) * 1.5
        ph = (1.0, 0.8, 0.62, 0.48)[r]
        pts = []
        for m in range(31):
            t = m / 30
            pts.append((base[0] + L * t + step * r,
                        base[1] - step * r - 26 * ph * math.sin((n + dn) * math.pi * t)))
        fr.ribbon(pts, SUBJ if r == 0 else LINE, greys[r], bind=True)
    hum_y = 196.0
    hum = []
    for m in range(61):
        t = m / 60
        hum.append((gx0 + 10 + (gx1 - gx0 - 20) * t, hum_y - 10 * p["hum"] * math.sin(2 * math.pi * 8 * t)))
    fr.ribbon(hum, HAIR, G4, bind=True)
    # channel marks replace the 'ch1' / 'ch2' text: one stroke at the wire's zero, two at the mains' zero
    channel_mark(fr, base[1], 1)
    channel_mark(fr, hum_y, 2)
    return fr.svg(p, [G7, G5, G4, G1])


if __name__ == "__main__":
    (HERE / "clean.svg").write_text(v5_clean(dict(DEFAULTS)))
    print(HERE / "clean.svg")
