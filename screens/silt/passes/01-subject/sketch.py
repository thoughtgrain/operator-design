#!/usr/bin/env python3
"""Silt, subject pass 01: one rest-frame sketch per direction (v1..v5).

Run from anywhere:  python3 screens/silt/passes/01-subject/sketch.py
Writes vN/rest.svg beside this file. Every frame is drawn at the definition's
defaults (settle 1.0 s, layers 16, stir 35 %, grain 0), no notes held.

All lines are closed ribbons (filled outlines), closed contours are stroked
closed outlines, and every path is one subpath of <= 64 points. Grey only.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 480, 220
FONT = "UniversNextPro-Light"

# Palette (stock greys)
G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")

# ---------------------------------------------------------------- the model
DEFAULTS = {"settle": 0.5, "layers": 0.5, "stir": 0.35, "grain": 0.0}
LAYERS = [2, 4, 8, 12, 16, 24, 32, 48, 64]


def settle_s(v):            # exponential 0.1 .. 10 s
    return 0.1 * (100 ** v)


def n_partials(v):
    return LAYERS[round(v * (len(LAYERS) - 1))]


def bed(k):
    """How much of partial k's level survives once it has settled."""
    return math.exp(-(k - 1) * 0.22)


def lift(k, n):
    """How strongly a stir lifts partial k (high partials lift most)."""
    return ((k - 1) / max(1, n - 1)) ** 0.8


def amp(k, n, stir):
    return (1.0 / k) * (bed(k) + stir * lift(k, n) * (1 - bed(k)))


def jitter(k, seed=7):
    r = random.Random(seed * 1000 + k)
    return r.uniform(-1, 1)


def freq(k, grain):
    return k * (1 + grain * 0.04 * jitter(k))


# ------------------------------------------------------------- svg helpers
def f(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


class Svg:
    def __init__(self):
        self.items: list[str] = []

    def add(self, s):
        self.items.append("  " + s)

    def ribbon(self, pts, w, fill):
        """Open polyline -> closed filled ribbon of width w. Splits at 31 points."""
        pts = dedupe(pts)
        if len(pts) < 2:
            return
        step = 30
        i = 0
        while i < len(pts) - 1:
            chunk = pts[i:i + step + 1]
            self._ribbon(chunk, w, fill)
            i += step

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
            # miter scale, capped
            m = 1.0
            if 0 < i < n - 1:
                ax, ay = x - pts[i - 1][0], y - pts[i - 1][1]
                la = math.hypot(ax, ay) or 1
                cos = abs(nx * (-ay / la) + ny * (ax / la))
                m = min(2.0, 1 / max(cos, 0.5))
            left.append((x + nx * h * m, y + ny * h * m))
            right.append((x - nx * h * m, y - ny * h * m))
        outline = left + right[::-1]
        self.poly(outline, fill=fill, stroke="none", sw=None)

    def poly(self, pts, fill="none", stroke="none", sw=1.0, ident=None):
        pts = dedupe(pts, closed=True)
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
        sw_attr = f' stroke-width="{f(sw)}"' if stroke != "none" else ""
        idattr = f' id="{ident}"' if ident else ""
        self.add(f'<path{idattr} d="{d}" fill="{fill}" stroke="{stroke}"{sw_attr}/>')

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

    def dashed(self, x1, y1, x2, y2, w, fill, dash=4, gap=3):
        L = math.hypot(x2 - x1, y2 - y1)
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        t = 0.0
        while t < L:
            e = min(L, t + dash)
            if e - t > 0.6:
                self.line(x1 + ux * t, y1 + uy * t, x1 + ux * e, y1 + uy * e, w, fill)
            t += dash + gap

    def write(self, path, values):
        head = HEADER.format(*values)
        body = "\n".join(self.items)
        path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n'
                        f'{head}\n{body}\n</svg>\n')


def dedupe(pts, closed=False):
    out = []
    for p in pts:
        p = (round(p[0], 2), round(p[1], 2))
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) >= 0.3:
            out.append(p)
    if closed and len(out) > 2 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) < 0.3:
        out.pop()
    return out


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


def norm_settle(c):
    return c["settle"]


# ------------------------------------------------------------------ v1
def v1(c):
    """P2 Diagram + trace, oscilloscope: spectrum + dB decay (left), output trace (right)."""
    s = Svg()
    n, stir, grain = n_partials(c["layers"]), c["stir"], c["grain"]
    # graticules: left upper (spectrum), left lower (ch2 decay), right (output)
    for (x0, y0, x1, y1, nx, ny) in ((14, 32, 226, 136, 8, 4), (14, 150, 226, 206, 8, 2), (254, 32, 466, 206, 8, 6)):
        s.rect(x0, y0, x1 - x0, y1 - y0, fill="none", stroke=G2, sw=1)
        for i in range(1, nx):
            x = x0 + (x1 - x0) * i / nx
            for j in range(1, ny):
                y = y0 + (y1 - y0) * j / ny
                s.line(x - 2, y, x + 2, y, 1, G2)
                s.line(x, y - 2, x, y + 2, 1, G2)
        # centre-axis minor ticks
        cy = y0 + (y1 - y0) / 2 if ny % 2 == 0 else None
        if cy is not None and ny > 2:
            for i in range(1, nx * 5):
                x = x0 + (x1 - x0) * i / (nx * 5)
                s.line(x, cy - 1.5, x, cy + 1.5, 1, G2)
    # ch1: spectrum, one line per partial, height in dB
    base = 134
    span = 196
    for k in range(1, n + 1):
        x = 40 + (span - 20) * (math.log(freq(k, grain)) / math.log(n + 0.5)) if n > 1 else 20
        db = 20 * math.log10(max(amp(k, n, stir), 1e-4))
        h = max(2.0, (db + 48) / 48 * 96)
        s.line(x, base, x, base - h, 1.5, G5)
    # ch2: decay in dB vs time is a straight line; settle sets its angle
    ang = math.radians(4 + 56 * (1 - c["settle"]))
    px, py, L = 44, 154, 72
    s.line(px, py, px + L * math.cos(ang), py + L * math.sin(ang), 1.5, G5)
    # output trace: one period of the stirred sum
    pts = []
    vals = []
    for i in range(0, 105):
        t = i / 104
        vals.append(sum(amp(k, n, stir) * math.sin(2 * math.pi * freq(k, grain) * t) for k in range(1, n + 1)))
    m = max(abs(v) for v in vals)
    for i, v in enumerate(vals):
        pts.append((258 + i * 2, 119 - v / m * 70))
    s.ribbon(pts, 2, G7)
    s.text(18, 46, "ch1", G4)
    s.text(18, 164, "ch2", G4)
    s.text(258, 46, "out", G4)
    return s


# ------------------------------------------------------------------ v2
def v2(c):
    """P3 Trace as subject, typeset diagram: the wave, its component partials sinking, a stipple bed."""
    s = Svg()
    n, stir, grain = n_partials(c["layers"]), c["stir"], c["grain"]
    x0, x1, cy, A = 44, 436, 76, 34
    # axes, hairline, with drawn arrowheads
    s.line(36, cy, 446, cy, 1, G3)
    s.poly([(452, cy), (444, cy - 3), (444, cy + 3)], fill=G3)
    s.line(40, cy + 38, 40, cy - 40, 1, G3)
    s.poly([(40, cy - 46), (37, cy - 38), (43, cy - 38)], fill=G3)
    s.text(456, cy + 4, "t", G4)
    s.text(48, cy - 38, "a", G4)
    # the wave
    vals = []
    for i in range(0, 197):
        t = i / 196
        vals.append(sum(amp(k, n, stir) * math.sin(2 * math.pi * freq(k, grain) * t) for k in range(1, n + 1)))
    m = max(abs(v) for v in vals)
    s.ribbon([(x0 + i * 2, cy - v / m * A) for i, v in enumerate(vals)], 2.25, G7)
    # component partials, printed small beneath, sinking toward the bed
    shown = list(range(2, min(n, 9) + 1))
    top = 122 + 26 * (1 - c["settle"])
    for j, k in enumerate(shown):
        yk = top + j * 7
        a = 2.0
        pts = []
        steps = 98
        for i in range(steps + 1):
            t = i / steps
            pts.append((x0 + t * (x1 - x0), yk - a * math.sin(2 * math.pi * freq(k, grain) * t)))
        s.ribbon(pts, 1.1, G3)
    s.text(16, top + 4, "k2", G4)
    s.text(16, top + (len(shown) - 1) * 7 + 4, f"k{shown[-1]}", G4)
    # stipple bed: geology convention for silt; grain scales the dots
    r = 1.5 * (1 + grain)
    for row, y in enumerate((196, 203)):
        x = x0 + (3 if row else 0)
        while x <= x1:
            s.circle(x, y, r, G4)
            x += 6
    s.line(x0, 208, x1, 208, 1, G3)
    s.text(x1 - 26, 218, "fig. 1", G4)
    return s


# ------------------------------------------------------------------ v3
def v3(c):
    """P4 Stack in depth, orthographic elevation: octave bands as plates stepping back."""
    s = Svg()
    n, stir, grain = n_partials(c["layers"]), c["stir"], c["grain"]
    bands = int(math.log2(n)) + 1                  # 1, 2, 3-4, 5-8, 9-16 ...
    names = ["k1"] + [f"k{2 ** (b - 1) + 1}-{2 ** b}" if b > 1 else "k2" for b in range(1, bands)]
    dx, dy, pw, th = 22, 16, 230, 8
    gx, gy = 48, 194
    current = round(c["settle"] * (bands - 1))
    # ground line with hatching (elevation convention)
    s.line(30, gy, 260, gy, 1.2, G4)
    for x in range(34, 258, 7):
        s.line(x, gy + 1, x - 5, gy + 7, 1, G2)
    # plates, back to front so the front hides the back
    for b in reversed(range(bands)):
        rest_y = gy - 2 - b * dy
        lifted = stir * 46 * (b / max(1, bands - 1)) ** 1.4
        x = gx + b * dx
        y = rest_y - lifted
        if lifted > 3:
            # settled position, hidden line
            s.dashed(x, rest_y, x + pw, rest_y, 1, G2)
            # fall line: dimension from settled to lifted
            s.line(x + pw + 6, rest_y, x + pw + 6, y, 1, G3)
            s.line(x + pw + 3, rest_y, x + pw + 9, rest_y, 1, G3)
            s.line(x + pw + 3, y, x + pw + 9, y, 1, G3)
        if b == current:
            top = []
            teeth = 23
            for i in range(teeth + 1):
                tx = x + pw * i / teeth
                tz = (1.5 + 3.5 * grain) * (1 if i % 2 else 0) if 0 < i < teeth else 0
                top.append((tx, y - th - tz))
            outline = [(x, y)] + top + [(x + pw, y)]
            s.poly(outline, fill=G0, stroke=G7, sw=2)
        else:
            s.poly([(x, y), (x, y - th), (x + pw, y - th), (x + pw, y)], fill=G0,
                   stroke=G5 if b < current else G3, sw=1.5)
        s.text(x - 4 - 6.4 * len(names[b]), y - 1, names[b], G4)
    s.text(300, 212, "elevation", G4)
    return s


# ------------------------------------------------------------------ v4
def v4(c):
    """P5 Field and figure, survey plan: a silt plume over a contoured basin, partials as chainage."""
    s = Svg()
    n, stir, grain = n_partials(c["layers"]), c["stir"], c["grain"]
    rnd = random.Random(3)
    # field: contoured basin bed, static, low grey
    ccx, ccy = 290, 112
    phase = [rnd.uniform(0, 6.28) for _ in range(3)]
    for i, (rx, ry) in enumerate([(40, 16), (72, 30), (106, 44), (142, 58), (180, 72), (222, 84)]):
        pts = []
        for j in range(60):
            a = 2 * math.pi * j / 60
            wob = 1 + 0.06 * math.sin(3 * a + phase[0] + i * 0.4) + 0.04 * math.sin(5 * a + phase[1])
            y = ccy + ry * wob * math.sin(a)
            pts.append((ccx + rx * wob * math.cos(a), min(max(y, 26), 190)))
        s.poly(pts, fill="none", stroke=G1 if i % 2 else G2, sw=1)
    # inlet channel banks
    s.line(8, 98, 52, 100, 1.5, G5)
    s.line(8, 122, 52, 120, 1.5, G5)
    # flow centreline, dash-dot, with arrowhead at the far end
    x = 54
    while x < 444:
        s.line(x, 110, min(x + 10, 444), 110, 1, G3)
        if x + 14 < 444:
            s.line(x + 13, 110, x + 15, 110, 1, G3)
        x += 18
    s.poly([(452, 110), (444, 107), (444, 113)], fill=G3)
    s.text(416, 102, "flow", G4)
    # figure: the plume in plan; settle scales it, stir lobes its edge
    sc = 0.7 + 0.6 * c["settle"]
    Lx, Wd = 190 * sc, 34 * sc
    top, bot = [], []
    m = 30
    for i in range(m + 1):
        t = i / m
        w = Wd * (0.3 + 0.7 * t ** 0.7) * math.sqrt(max(0.0, 1 - t ** 2.2))
        lobe = 1 + stir * 0.7 * math.sin(5 * math.pi * t + 0.6) * t
        w = max(0.0, w * lobe)
        xx = 52 + t * Lx
        top.append((xx, 110 - w))
        bot.append((xx + 0.01, 110 + w * (1 - 0.12 * math.sin(4 * math.pi * t))))
    outline = top + bot[::-1][1:]
    s.poly(outline, fill=G0, stroke=G7, sw=2)
    # deposit lens: coarse grain drops near the inlet, fine travels downstream
    dxc = 52 + Lx * (0.78 - 0.5 * grain)
    lens = [(dxc + 22 * math.cos(2 * math.pi * j / 40), 110 + 7 * math.sin(2 * math.pi * j / 40)) for j in range(40)]
    s.poly(lens, fill=G0, stroke=G5, sw=1.5)
    # spot heights on the bed
    for (sx, sy, lab) in ((372, 62, "2.4"), (404, 164, "3.1"), (126, 168, "1.2")):
        s.line(sx - 3, sy, sx + 3, sy, 1, G3)
        s.line(sx, sy - 3, sx, sy + 3, 1, G3)
        s.text(sx + 5, sy + 4, lab, G4)
    # chainage strip: one station per partial
    s.line(40, 204, 440, 204, 1, G3)
    for k in range(1, n + 1):
        xk = 40 + 400 * (k - 1) / max(1, n - 1)
        tall = (k % 4 == 0) or k == 1
        s.line(xk, 204, xk, 196 if tall else 199, 1.2, G5)
        if tall:
            s.text(xk + 2, 216, str(k), G4)
    s.text(12, 36, "plan", G4)
    return s


# ------------------------------------------------------------------ v5
def v5(c):
    """P11 Instrument stack (stretch), patent section: a settling column cut open."""
    s = Svg()
    n, stir, grain = n_partials(c["layers"]), c["stir"], c["grain"]
    cx, top, base, half, wall = 240, 40, 196, 52, 7
    # base plate, sectioned
    s.rect(cx - 82, base, 164, 8, fill=G0, stroke=G5, sw=1.5)
    for x in range(int(cx - 80), int(cx + 80), 5):
        s.line(x, base + 7, x + 5, base + 1, 1, G3)
    # walls in section with 45 degree hatching
    for side in (-1, 1):
        x0 = cx + side * half - (wall if side < 0 else 0)
        s.rect(x0, top, wall, base - top, fill=G0, stroke=G5, sw=1.5)
        y = top + 4
        while y < base - 2:
            s.line(x0 + 1.2, y + wall - 2.4, x0 + wall - 1.2, y, 1, G3)
            y += 5
    # cap with pivot
    s.rect(cx - half - wall - 4, top - 6, 2 * (half + wall) + 8, 6, fill=G0, stroke=G5, sw=1.5)
    # strata: one line per partial from the bed up; the interface is where settled meets suspended
    inner0, inner1 = cx - half + 2, cx + half - 2
    shown = min(n, 24)
    sp = (base - top - 30) / (shown + 1)
    iface = base - 18 - 100 * c["settle"]
    for k in range(1, shown + 1):
        y = base - 2 - k * sp * 0.9
        if y < iface:
            break
        s.line(inner0, y, inner1, y, 1, G3)
    s.line(inner0, iface, inner1, iface, 2.25, G7)
    # suspended particles above the interface; grain scales them
    rnd = random.Random(11)
    r = 1.5 * (1 + grain)
    for _ in range(22):
        px, py = rnd.uniform(inner0 + 4, inner1 - 4), rnd.uniform(top + 30, iface - 6)
        s.circle(px, py, r, G4)
    # stirring arm, hinged at the cap; stir swings it
    ang = math.radians(stir * 40)
    L = 64
    tx, ty = cx + L * math.sin(ang), top + L * math.cos(ang)
    s.ribbon([(cx, top), (tx, ty)], 2, G6)
    s.circle(cx, top, 3, G0, G6, 1.5)
    s.poly([(tx - 9 * math.cos(ang), ty + 9 * math.sin(ang)), (tx + 9 * math.cos(ang), ty - 9 * math.sin(ang)),
            (tx + 9 * math.cos(ang) + 3 * math.sin(ang), ty - 9 * math.sin(ang) + 3 * math.cos(ang)),
            (tx - 9 * math.cos(ang) + 3 * math.sin(ang), ty + 9 * math.sin(ang) + 3 * math.cos(ang))],
           fill=G0, stroke=G6, sw=1.5)
    # reference numerals with leaders
    for (lx, ly, ex, ey, lab) in ((340, 60, cx + half + wall, 70, "10"),
                                  (130, 52, cx - 4, top + 2, "12"),
                                  (340, iface + 4, inner1 - 6, iface, "14"),
                                  (130, 188, cx - 60, base + 4, "16")):
        s.line(lx - (0 if lx > cx else -14), ly - 3, ex, ey, 1, G3)
        s.text(lx + (2 if lx > cx else -2), ly + 1, lab, G4)
    s.text(16, 212, "fig. 1", G4)
    return s


def main():
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        svg = fn(DEFAULTS)
        d = HERE / name
        d.mkdir(exist_ok=True)
        svg.write(d / "rest.svg", captions(DEFAULTS))
        print(d / "rest.svg")


if __name__ == "__main__":
    main()
