#!/usr/bin/env python3
"""Subject-pass sketches for tide: five rest frames, one per direction.

    python3 screens/tide/passes/01-subject/sketch.py

Writes v1..v5/rest.svg (480 x 220, stock header kept as preview scaffolding).
Every frame shows the defaults: swell 2.0 s, depth 0.5 s, salt 0 %, drift 0 %, no notes.
These are sketches for picking a subject, not device frames: parts are static
artwork (no bound nodes yet), so the budget is argued in each candidate's risks.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 480, 220

# stock greys (tokens.json)
G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
FONT = "UniversNextPro-Light"

# defaults (definition.json)
SWELL_S = 0.25 * 32 ** 0.6      # 2.0 s between waves
DEPTH_S = 0.05 * 100 ** 0.5     # 0.5 s ring time
SALT = 0.0
DRIFT = 0.0
HEADER = [("swell", "2.0s"), ("depth", "0.5s"), ("salt", "0"), ("drift", "0")]


# ----------------------------------------------------------------- helpers
def f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def dedupe(pts):
    out = []
    for p in pts:
        if not out or math.dist(out[-1], p) >= 0.25:
            out.append(p)
    return out


def poly(pts, fill, stroke="none", sw=None, closed=True):
    pts = dedupe(pts)
    if closed and len(pts) > 2 and math.dist(pts[0], pts[-1]) < 0.25:
        pts = pts[:-1]
    d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + (" Z" if closed else "")
    s = f'<path d="{d}" fill="{fill}" stroke="{stroke}"'
    if stroke != "none":
        s += f' stroke-width="{sw}"'
    return s + "/>"


def rect(x, y, w, h, fill, stroke="none", sw=None):
    s = f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" fill="{fill}" stroke="{stroke}"'
    if stroke != "none":
        s += f' stroke-width="{sw}"'
    return s + "/>"


def text(x, y, s, fill=G4, size=10):
    return (f'<text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{fill}" stroke="none" '
            f'font-family="{FONT}" font-size="{size}px">{s}</text>')


def ribbon(pts, w, fill):
    """An open polyline as thin closed ribbons (filled, no stroke), chunked to <= 62 points each."""
    pts = dedupe(pts)
    out = []
    i = 0
    while i < len(pts) - 1:
        chunk = pts[i:i + 31]
        out.append(_ribbon(chunk, w, fill))
        i += 30
    return "\n".join(out)


def _ribbon(pts, w, fill):
    h = w / 2
    n = len(pts)
    left, right = [], []
    for k in range(n):
        if k == 0:
            dx, dy = pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]
            L = math.hypot(dx, dy)
            nx, ny, m = -dy / L, dx / L, h
        elif k == n - 1:
            dx, dy = pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]
            L = math.hypot(dx, dy)
            nx, ny, m = -dy / L, dx / L, h
        else:
            ax, ay = pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]
            bx, by = pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1]
            la, lb = math.hypot(ax, ay), math.hypot(bx, by)
            n1 = (-ay / la, ax / la)
            n2 = (-by / lb, bx / lb)
            nx, ny = n1[0] + n2[0], n1[1] + n2[1]
            ln = math.hypot(nx, ny) or 1
            nx, ny = nx / ln, ny / ln
            cos = max(0.5, nx * n1[0] + ny * n1[1])
            m = h / cos
        x, y = pts[k]
        left.append((x + nx * m, y + ny * m))
        right.append((x - nx * m, y - ny * m))
    return poly(left + right[::-1], fill)


def clip_line_poly(p0, p1, polygon):
    """Segments of the line p0->p1 that lie inside polygon (even-odd)."""
    (x0, y0), (x1, y1) = p0, p1
    ts = []
    n = len(polygon)
    for i in range(n):
        ax, ay = polygon[i]
        bx, by = polygon[(i + 1) % n]
        dx, dy = x1 - x0, y1 - y0
        ex, ey = bx - ax, by - ay
        den = dx * ey - dy * ex
        if abs(den) < 1e-9:
            continue
        t = ((ax - x0) * ey - (ay - y0) * ex) / den
        u = ((ax - x0) * dy - (ay - y0) * dx) / den
        if 0 <= t <= 1 and 0 <= u < 1:
            ts.append(t)
    ts.sort()
    segs = []
    for a, b in zip(ts[0::2], ts[1::2]):
        segs.append(((x0 + (x1 - x0) * a, y0 + (y1 - y0) * a), (x0 + (x1 - x0) * b, y0 + (y1 - y0) * b)))
    return segs


def frame(body: list[str]) -> str:
    steps = [G0, G1, G2, G3, G4, G5, G6, G7]
    hdr = [rect(60 * i, 0, 60, 20, c) for i, c in enumerate(steps)]
    for i, (t, v) in enumerate(HEADER):
        ink = "#CBCBCB" if i < 2 else G0
        hdr.append(f'<text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{ink}" stroke="none" '
                   f'font-family="{FONT}" font-size="10px">{t}</text>')
        hdr.append(f'<text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{ink}" stroke="none" '
                   f'font-family="{FONT}" font-size="20px">{v}</text>')
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        '<g id="preview_canvas">', rect(0, 0, W, H, G0), '</g>',
        '<g id="preview_header">', *hdr, '</g>',
        *body,
        '</svg>', ""])


def ring_down(t, depth=DEPTH_S, salt=SALT):
    """The pool's response to one wave of noise, t in seconds after the wave's front."""
    if t < 0:
        return 0.0
    attack = 1 - math.exp(-t / 0.06)
    env = attack * math.exp(-t / (depth * 0.9))
    ratios = [1, 2.0 + salt, 3.0 + 2 * salt]
    s = sum(math.sin(2 * math.pi * (5.0 * r) * t) / (1 + 2.5 * k) for k, r in enumerate(ratios))
    return env * s / 1.3


# ------------------------------------------------- v1  P5 · oscilloscope
def v1():
    body = []
    # dim persistence traces of earlier swells, receding toward a horizon
    layers = [(104, 0.55, G3), (78, 0.38, G2), (61, 0.27, G2)]
    for base, k, ink in reversed(layers):
        cx = 240
        span = 380 * k
        pts = []
        for i in range(int(span / 1.6) + 1):
            x = cx - span / 2 + i * 1.6
            t = (x - (cx - span / 2)) / span * 1.6 - 0.12
            pts.append((x, base - 34 * k * ring_down(t)))
        body.append(ribbon(pts, 1.2, ink))
        # graticule baseline stubs at the trace's two ends
        body.append(rect(cx - span / 2 - 10, base - 0.5, 6, 1.2, G2))
        body.append(rect(cx + span / 2 + 4, base - 0.5, 6, 1.2, G2))
    # the figure: this swell's ring-down, bright
    base = 152
    x0, x1 = 44, 436
    pts = []
    for i in range(int((x1 - x0) / 1.4) + 1):
        x = x0 + i * 1.4
        t = (x - x0) / (x1 - x0) * 1.6 - 0.12
        pts.append((x, base - 36 * ring_down(t)))
    # graticule: centre line and minor ticks under the figure
    body.append(ribbon([(x0, base), (x1, base)], 1, G2))
    body.append(ribbon(pts, 2.2, G7))
    # activity strip: wave arrivals, one per swell period across 8 s
    for k in range(5):
        x = 44 + k * (392 * SWELL_S / 8)
        body.append(rect(x, 202, 5, 8, G5 if k == 0 else G3))
    return frame(body)


# --------------------------------------------- v2  P10 · typeset diagram
def v2():
    body = []
    rows, cols = 8, 16
    x0, dx = 92, 23.5
    y0, dy = 46, 19
    dt = 4.0 / cols
    waves = [0.0, SWELL_S]
    body.append(ribbon([(16, 30), (464, 30)], 1, G3))
    body.append(ribbon([(16, 200), (464, 200)], 1, G3))
    for r in range(rows):
        ratio = (r + 1) ** (1 + 0.3 * SALT)
        y = y0 + r * dy
        tau = DEPTH_S * 1.6 / (1 + 0.45 * r)
        body.append(text(26, y + 3.5, f"f{r + 1}", G4))
        for c in range(cols):
            t = c * dt + dt / 2
            a = 0.0
            for w0 in waves:
                if t >= w0:
                    a += math.exp(-(t - w0) / tau) * (1 - 0.06 * r)
            a = min(a, 1.0)
            side = 3 + 12 * math.sqrt(a)
            x = x0 + c * dx
            if side < 5.5:
                body.append(rect(x - 2, y - 2, 4, 4, G0, G2, 1.5))
                continue
            front = any(abs(t - w0) < dt / 1.5 for w0 in waves[-1:])
            if front:
                ink = G7
            else:
                ink = G5 if a > 0.45 else G3
            body.append(rect(x - side / 2, y - side / 2, side, side, ink))
    # time axis, typeset
    body.append(text(x0 - 6, 213, "0", G4))
    body.append(text(x0 + 8 * dx - 10, 213, "2 s", G4))
    body.append(text(x0 + 15 * dx - 10, 213, "4 s", G4))
    return frame(body)


# --------------------------------------- v3  P15 · orthographic elevation
def v3():
    body = []
    rnd = random.Random(7)
    cell, gap = 20, 2
    cols, rows = 24, 10                       # y 20..220
    top = 20
    # elevation of the shore: rock top per column (row index of the first rock cell)
    rock_top = [9, 9, 9, 8, 8, 7, 5, 3, 3, 4, 8, 9, 9, 9, 8, 8, 9, 9, 9, 8, 6, 4, 4, 4]
    water = 5                                   # still-water row inside the pool (depth)
    sea = 6
    crest = {2: 3, 3: 4, 4: 4}                  # the arriving swell: column -> top row
    for c in range(cols):
        for r in range(rows):
            x, y = c * cell + gap / 2, top + r * cell + gap / 2
            s = cell - gap
            if r >= rock_top[c]:
                body.append(rect(x + 0.75, y + 0.75, s - 1.5, s - 1.5, G0, G3, 1.5))
                continue
            in_pool = 10 <= c <= 20
            surface = (water if in_pool else crest.get(c, sea)) if c < 21 else 99
            if r < surface:
                continue
            if r == surface and (c in crest or (in_pool and c in (12, 13, 17))):
                body.append(rect(x, y, s, s, G7))         # foam run on the crest, glints in the pool
            elif in_pool and r == surface:
                body.append(rect(x, y, s, s, G4))
            else:
                body.append(rect(x, y, s, s, G2 if (r + c) % 3 else G1))
    # spray over the rim from the last wave
    for c, r in ((6, 2), (7, 2)):
        body.append(rect(c * cell + gap / 2, top + r * cell + gap / 2, cell - gap, cell - gap, G5))
    return frame(body)


# ----------------------------------------------- v4  P1 · survey plan
def blob(cx, cy, rx, ry, harm, n=56, k=1.0):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        r = 1 + k * sum(amp * math.cos(m * a + ph) for m, amp, ph in harm)
        pts.append((cx + rx * r * math.cos(a), cy + ry * r * math.sin(a)))
    return pts


def v4():
    body = []
    harm = [(2, 0.07, 0.4), (3, 0.06, 1.3), (5, 0.03, 2.0)]
    cx, cy, rx, ry = 270, 116, 136, 68
    # rim: the pool's edge, a bright ribbon open at the mouth (west)
    rim = []
    gap = math.radians(16)
    n = 60
    for i in range(n + 1):
        a = math.pi + gap + (2 * math.pi - 2 * gap) * i / n
        r = 1 + sum(amp * math.cos(m * a + ph) for m, amp, ph in harm)
        rim.append((cx + rx * r * math.cos(a), cy + ry * r * math.sin(a)))
    mouth = rim[0]
    # contours: two basins, each its own resonant hollow
    for (bx, by, brx, bry, steps, h) in ((312, 112, 74, 40, 4, [(2, 0.08, 0.9), (3, 0.05, 0.2)]),
                                         (196, 128, 36, 22, 3, [(2, 0.1, 2.1), (3, 0.06, 1.0)])):
        for s in range(steps):
            k = 1 - s / steps
            ink = G3 if s == 0 else G4 if s < steps - 1 else G5
            pts = blob(bx, by, brx * k, bry * k, h, n=40)
            body.append(poly(pts, "none", ink, 1.5))
    # shelf contour just inside the rim
    shelf = blob(cx + 6, cy, rx * 0.86, ry * 0.8, harm, n=56)
    body.append(poly(shelf, "none", G2, 1.5))
    # swell fronts arriving from the west, spaced by the swell period
    sp = 22 * SWELL_S / 2
    for k in range(3):
        R = 46 + k * sp
        pts = [(mouth[0] + 40 + R * math.cos(a), mouth[1] + R * math.sin(a))
               for a in [math.radians(150 + i * 3) for i in range(21)]]
        pts = [p for p in pts if p[0] > 6]
        body.append(ribbon(pts, 1.2, G4 if k == 0 else G3))
    # tide mark: dotted line, drift moves it
    for i in range(0, 56, 3):
        x, y = blob(cx + 6, cy, rx * 0.93, ry * 0.9, harm, n=56)[i]
        body.append(rect(x - 1.5, y - 1.5, 3, 3, G3))
    body.append(ribbon(rim, 2.4, G7))
    # soundings and scale bar
    body.append(text(306, 116, "1.4", G5))
    body.append(text(188, 132, "0.8", G4))
    body.append(text(210, 90, "0.3", G4))
    for i in range(4):
        body.append(rect(372 + i * 20, 200, 20, 4, G4 if i % 2 == 0 else G0, G4, 1.5))
    body.append(text(372, 214, "0", G4))
    body.append(text(444, 214, "2 m", G4))
    return frame(body)


# ------------------------------------------- v5  P13 · patent section
def v5():
    body = []
    rock = [(0, 180), (60, 176), (110, 168), (138, 146), (152, 112), (162, 88), (174, 80), (186, 84),
            (194, 104), (200, 142), (226, 142), (226, 196), (256, 196), (256, 142), (284, 142),
            (284, 184), (314, 184), (314, 142), (342, 142), (342, 172), (372, 172), (372, 142),
            (406, 142), (414, 114), (424, 94), (480, 92), (480, 214), (0, 214)]
    # hatching of the cut rock, 45 deg, 7 px apart
    for c in range(-240, 720, 7):
        p0, p1 = (c, 0), (c + 240, 240)
        for a, b in clip_line_poly(p0, p1, rock):
            if math.dist(a, b) > 3:
                body.append(ribbon([a, b], 1, G2))
    body.append(poly(rock, "none", G5, 1.5))
    # sea surface with the arriving swell (10), drawn up to the rock face
    def sea_y(x):
        crest_x, far_x = 112, 112 - 64 * SWELL_S / 2
        y = 124
        for cxp, amp, wdt in ((crest_x, 38, 20), (far_x, 18, 18)):
            d = (x - cxp) / wdt
            y -= amp * math.exp(-d * d * (1.6 if d > 0 else 0.7))
        return y
    sea = []
    x = 0.0
    while x <= 145:
        sea.append((x, sea_y(x)))
        x += 2
    body.append(ribbon(sea, 2.2, G7))
    # pool water surface (14) between the rims, with patent water marks below
    body.append(ribbon([(197, 110), (411, 110)], 2.2, G7))
    for (x, y, w) in ((232, 122, 22), (300, 128, 18), (360, 120, 24), (240, 162, 10), (294, 160, 12)):
        body.append(ribbon([(x, y), (x + w, y)], 1.2, G3))
    # reference numerals with leaders
    for (tx, ty, lab, lx0, ly0, lx1, ly1) in ((60, 56, "10", 76, 60, 104, 80),
                                               (166, 44, "12", 176, 48, 176, 76),
                                               (440, 64, "14", 438, 68, 404, 106),
                                               (234, 58, "16", 241, 64, 241, 186)):
        body.append(ribbon([(lx0, ly0), (lx1, ly1)], 1, G4))
        body.append(text(tx, ty, lab, G5))
    body.append(text(430, 40, "fig. 1", G4))
    return frame(body)


def main():
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        d = HERE / name
        d.mkdir(exist_ok=True)
        (d / "rest.svg").write_text(fn())
        print(d / "rest.svg")


if __name__ == "__main__":
    main()
