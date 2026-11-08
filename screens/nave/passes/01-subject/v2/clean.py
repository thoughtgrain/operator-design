#!/usr/bin/env python3
"""nave v2 cleanup: the owner's pick, fig. 1 alone, recomposed for the whole body.

    python3 screens/nave/passes/01-subject/v2/clean.py            # writes v2/clean.svg
    python3 screens/nave/passes/01-subject/v2/clean.py doors=1 OUT  # a probe at other settings

The model and svg helpers are copied from ../sketch.py (unchanged). The impulse
plot (fig. 2) is gone: stone and doors, which lived there, now show in the section.
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



# ------------------------------------------------------------ v2, cleaned
FLOOR = 192            # floor line (top of the slab)
VINT = 52              # intrados of the vault
SPRING = 124           # springing of the arcade and of the apse's half-dome
SHELL = 8              # thickness of the cut masonry
BAY = 34               # arcade bay


def geometry(c):
    L = 140 + 130 * c["nave"]                 # nave: the east end moves 130 px
    ra = SPRING - VINT                        # apse radius
    x0 = 250 - (L + ra) / 2                   # the church stays centred as it grows
    xe = x0 + L
    porch = 8 + 48 * c["doors"]               # doors: how far the door stands back, 8 .. 56 px
    return L, ra, x0, xe, porch


def inside(x, y, c):
    L, ra, x0, xe, _ = geometry(c)
    if y < VINT or y > FLOOR or x < x0:
        return False
    if x <= xe:
        return True
    if y >= SPRING:
        return x <= xe + ra
    return (x - xe) ** 2 + (y - SPRING) ** 2 <= ra ** 2


def normal(x, y, c):
    """Inward normal of the boundary the ray just crossed."""
    L, ra, x0, xe, _ = geometry(c)
    if x > xe and y < SPRING:
        d = math.hypot(x - xe, y - SPRING)
        return (-(x - xe) / d, -(y - SPRING) / d)
    if x > xe + ra - 1:
        return (-1.0, 0.0)
    return (0.0, 1.0)


def trace(p, ang, c, reach):
    """A sound ray from p at `ang` degrees until it meets the stone, then `reach` px of reflection."""
    x, y = p
    dx, dy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    pts = [(x, y)]
    step = 0.5
    while inside(x + dx * step, y + dy * step, c):
        x, y = x + dx * step, y + dy * step
    pts.append((x, y))
    nx, ny = normal(x, y, c)
    k = dx * nx + dy * ny
    rx, ry = dx - 2 * k * nx, dy - 2 * k * ny
    t = 0.0
    while t < reach and inside(x + rx * (t + step), y + ry * (t + step), c):
        t += step
    if t > 1.5:
        pts.append((x + rx * t, y + ry * t))
    return pts


def v2_clean(c):
    s = Svg()
    L, ra, x0, xe, porch = geometry(c)
    door_top = FLOOR - 36

    # arcade, seen beyond the cut: piers and pointed arches, quiet (Line, mid grey)
    nb = max(1, int((L - 8) // BAY))
    pitch = (L - 8) / nb
    for i in range(nb):
        a = x0 + 4 + i * pitch
        b = a + pitch
        s.rect(a, SPRING, 5, FLOOR - SPRING, fill=G0, stroke=G3, sw=1.2)
        w = b - (a + 5)
        left = arc(a + 5 + w, SPRING, w, 180, 240, 10)
        right = arc(a + 5, SPRING, w, 300, 360, 10)
        s.ribbon(left + right[1:], 1.5, G3)
    s.rect(xe - 1, SPRING, 5, FLOOR - SPRING, fill=G0, stroke=G3, sw=1.2)

    # the cut shell: west wall, vault, half-dome and east wall as one double outline,
    # black between (hidden-line), outer face at Line weight
    outer = ([(x0 - SHELL, door_top), (x0 - SHELL, VINT - SHELL)]
             + arc(xe, SPRING, ra + SHELL, -90, 0, 20) + [(xe + ra + SHELL, FLOOR)])
    inner = ([(xe + ra, FLOOR)] + arc(xe, SPRING, ra, 0, -90, 20) + [(x0, VINT), (x0, door_top)])
    s.poly(outer + inner, fill=G0, stroke="none")
    s.ribbon(outer, 1.5, G5)
    s.ribbon([(x0 - SHELL, door_top), (x0, door_top)], 1.5, G5)
    # the room's inner face: the subject, the one brightest line
    s.ribbon(inner, 2.0, G7)

    # porch: the doors stand back from the west wall by `porch`
    xd = x0 - SHELL - porch
    roof = door_top - 2
    s.poly([(xd - 3, roof - 6), (x0 - SHELL, roof - 6), (x0 - SHELL, roof), (xd - 3, roof)],
           fill=G0, stroke=G5, sw=1.5)
    s.ribbon([(xd, roof), (xd, FLOOR)], 1.5, G5)          # the door jamb, where the sound comes in

    # floor slab, porch to east wall
    s.ribbon([(xd - 3, FLOOR), (xe + ra + SHELL, FLOOR)], 1.5, G5)
    s.ribbon([(xd - 3, FLOOR + 6), (xe + ra + SHELL, FLOOR + 6)], 1.2, G3)

    # sound: one ray in through the doors (its length is the pre-delay), then the choir
    # fans it into rays; each ray reflects off the stone, harder stone carries further
    sy = FLOOR - 16
    fan = (x0 + 10, sy)
    s.ribbon([(xd + 4, sy), fan], 1.2, G5)
    s.circle(fan[0], fan[1], 2.5, G0, G5, 1.2)
    n = 1 + round(13 * c["choir"])
    reach = 6 + 60 * c["stone"]
    for k in range(n):
        ang = -38 if n == 1 else -16 - 56 * k / (n - 1)
        ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        start = (fan[0] + ux * 7, fan[1] + uy * 7)
        s.ribbon(trace(start, ang, c, reach), 1.0, G4)
    return s


def main():
    import sys
    c = dict(DEFAULTS)
    args = sys.argv[1:]
    out = HERE / "clean.svg"
    for arg in args:
        if "=" in arg:
            k, v = arg.split("=")
            c[k] = float(v)
        else:
            out = Path(arg)
    v2_clean(c).write(out, c)
    print(out)


if __name__ == "__main__":
    main()
