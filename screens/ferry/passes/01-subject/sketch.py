#!/usr/bin/env python3
"""Ferry, subject pass 01: one rest-frame sketch per direction (v1..v5).

Run from anywhere:  python3 screens/ferry/passes/01-subject/sketch.py
Writes vN/rest.svg beside this file. Every frame is drawn at the definition's
defaults (route up, 4 ports, swell 0 %, dwell 1/8), no notes held.

One timetable model feeds all five drawings, so they disagree only in how
they draw it. Lines are closed ribbons, closed contours are stroked closed
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
ROUTES = ["up", "down", "shtl", "cross", "tramp"]
PORTS = [2, 3, 4, 5, 6, 7, 8]
DIVS = ["1/32", "1/16", "1/8", "1/4", "1/2"]          # dwell, short -> long (assumed host table order)
DEFAULTS = {"route": 0.0, "ports": 2 / 6, "swell": 0.0, "dwell": 0.5}
CHORD = [0, 4, 7]                                       # the held chord, C E G from C4
NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def route(c):
    return ROUTES[round(c["route"] * (len(ROUTES) - 1))]


def n_ports(c):
    return PORTS[round(c["ports"] * (len(PORTS) - 1))]


def dwell_div(c):
    return DIVS[round(c["dwell"] * (len(DIVS) - 1))]


def slots_per_bar(c):
    return int(dwell_div(c).split("/")[1])


def pitches(n):
    """Port i's pitch in semitones over C4: the chord's tones, then octaves up."""
    return [CHORD[i % 3] + 12 * (i // 3) for i in range(n)]


def name(p):
    return f"{NAMES[p % 12]}{4 + p // 12}"


def order(rt, n, length):
    """Port indices the ferry visits, in route order, for `length` stops."""
    if rt == "up":
        cyc = list(range(n))
    elif rt == "down":
        cyc = list(range(n - 1, -1, -1))
    elif rt == "shtl":
        cyc = list(range(n)) + list(range(n - 2, 0, -1))
    elif rt == "cross":
        cyc, lo, hi = [], 0, n - 1
        while lo <= hi:
            cyc.append(lo)
            if hi != lo:
                cyc.append(hi)
            lo, hi = lo + 1, hi - 1
    else:
        r = random.Random(7)
        return [r.randrange(n) for _ in range(length)]
    return [cyc[i % len(cyc)] for i in range(length)]


def late(k, swell, seed=11):
    """How late swell holds stop k, 0..1 of a slot (seeded, frozen)."""
    r = random.Random(seed * 131 + k)
    return swell * r.random() * 0.6


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
        sw_attr = f' stroke-width="{f(sw)}"' if stroke != "none" else ' stroke-width="0"'
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}"{sw_attr}/>')

    def line(self, x1, y1, x2, y2, w, fill):
        self._ribbon([(x1, y1), (x2, y2)], w, fill)

    def rect(self, x, y, w, h, fill="none", stroke="none", sw=1.0):
        self.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], fill, stroke, sw)

    def circle(self, cx, cy, r, fill, stroke="none", sw=1.0):
        sw_attr = f' stroke-width="{f(sw)}"' if stroke != "none" else ' stroke-width="0"'
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
    <text transform="matrix(1 0 0 1 5 10)" fill="#CBCBCB" stroke="none" font-family="UniversNextPro-Light" font-size="10px">route</text>
    <text transform="matrix(1 0 0 1 125 10)" fill="#CBCBCB" stroke="none" font-family="UniversNextPro-Light" font-size="10px">ports</text>
    <text transform="matrix(1 0 0 1 245 10)" fill="#000000" stroke="none" font-family="UniversNextPro-Light" font-size="10px">swell</text>
    <text transform="matrix(1 0 0 1 365 10)" fill="#000000" stroke="none" font-family="UniversNextPro-Light" font-size="10px">dwell</text>
    <text transform="matrix(1 0 0 1 65 17.44)" fill="#CBCBCB" stroke="none" font-family="UniversNextPro-Light" font-size="20px">{0}</text>
    <text transform="matrix(1 0 0 1 185 17.44)" fill="#CBCBCB" stroke="none" font-family="UniversNextPro-Light" font-size="20px">{1}</text>
    <text transform="matrix(1 0 0 1 305 17.44)" fill="#000000" stroke="none" font-family="UniversNextPro-Light" font-size="20px">{2}</text>
    <text transform="matrix(1 0 0 1 425 17.44)" fill="#000000" stroke="none" font-family="UniversNextPro-Light" font-size="20px">{3}</text>
  </g>"""


def captions(c):
    return route(c), str(n_ports(c)), str(round(c["swell"] * 100)), dwell_div(c)


def ellipse_pts(cx, cy, rx, ry, n=60, a0=0.0, a1=2 * math.pi, wob=0.0, k=7):
    out = []
    closed = abs((a1 - a0) - 2 * math.pi) < 1e-6
    steps = n if closed else n - 1
    for i in range(n):
        a = a0 + (a1 - a0) * i / steps
        r = 1 + wob * math.sin(k * a)
        out.append((cx + rx * r * math.cos(a), cy + ry * r * math.sin(a)))
    return out


def hull_plan(x, y, ang, L=16, B=6):
    """A hull seen from above, pointed bow, square transom: 6 points."""
    ca, sa = math.cos(ang), math.sin(ang)
    local = [(L / 2, 0), (L * 0.15, -B / 2), (-L / 2, -B / 2 * 0.85), (-L / 2, B / 2 * 0.85), (L * 0.15, B / 2)]
    return [(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in local]


# ------------------------------------------------- v1 · P5 · engineering schematic
def v1(c):
    """A ferry in side elevation on a receding sea; a timing diagram of the timetable underneath."""
    s = Svg()
    sw = c["swell"]
    vx, vy = 240, 96                            # vanishing point
    rows = [121, 125, 130, 136, 143, 151, 160, 170]
    for j, y in enumerate(rows):
        near = (y - vy) / (rows[-1] - vy)
        amp = sw * 6 * near
        pts = [(x, y + amp * math.sin(x / (14 + 20 * near) + j)) for x in range(36, 446, 6)]
        s.ribbon(pts, 1.0, G1 if j < 3 else G2)
    for k in range(-5, 6):
        xb = vx + k * 46
        y0 = rows[0]
        x0 = vx + (xb - vx) * (y0 - vy) / (rows[-1] - vy)
        s.line(x0, y0, xb, rows[-1], 1.0, G1)

    # centreline and waterline, schematic
    s.dashed([(240, 44), (240, 176)], 1.0, G2, dash=9, gap=3)
    s.text(244, 52, "CL", G4)
    wl = 130
    s.dashed([(326, wl), (360, wl)], 1.0, G3, dash=5, gap=3)
    s.text(364, wl + 3.5, "WL", G4)

    heel = math.radians(sw * 9)
    ox, oy = 240, wl

    def P(pts):
        ca, sa = math.cos(heel), math.sin(heel)
        return [(ox + x * ca - y * sa, oy + x * sa + y * ca) for x, y in pts]

    # hidden line: the hull under the waterline
    s.dashed(P([(-62, 0), (-56, 9), (50, 9), (61, 0)]), 1.0, G3, dash=4, gap=3)
    # superstructure first, hull over it
    s.poly(P([(-20, -24), (-11, -24), (-11, -42), (-20, -42)]), G0, G5, 1.5)        # funnel
    s.poly(P([(-50, -12), (44, -12), (44, -25), (-50, -25)]), G0, G5, 1.5)          # car-deck house
    s.poly(P([(6, -25), (38, -25), (38, -36), (6, -36)]), G0, G5, 1.5)              # bridge
    s.ribbon(P([(-44, -19), (38, -19)]), 1.0, G3)                                    # window band
    s.ribbon(P([(10, -31.5), (34, -31.5)]), 1.0, G3)
    s.ribbon(P([(26, -36), (26, -47)]), 1.0, G5)                                    # mast
    s.poly(P([(-63, 0), (-70, -12), (70, -12), (82, -17), (63, 0)]), G0, G7, 2.0)    # hull

    # timing diagram: one bar of the timetable, pulse height = the port's pitch
    n, slots = n_ports(c), slots_per_bar(c)
    ps = pitches(n)
    seq = order(route(c), n, slots)
    x0, x1, base = 36, 444, 208
    cell = (x1 - x0) / slots
    top = max(ps) or 1
    pts = [(x0, base)]
    for k, port in enumerate(seq):
        a = x0 + cell * (0.3 + late(k, sw))
        b = a + cell * 0.55
        a += cell * k
        b += cell * k
        h = 6 + 18 * ps[port] / top
        pts += [(a, base), (a, base - h), (b, base - h), (b, base)]
    pts.append((x1, base))
    s.ribbon(pts, 1.5, G5)
    for k in range(slots + 1):
        s.line(x0 + cell * k, base + 2, x0 + cell * k, base + 6, 1.0, G3)
    s.text(8, base + 1, "t", G4)
    return s


# ------------------------------------------------- v2 · P12 · oscilloscope trace
def v2(c):
    """An X-Y scope: octaves as orbits, ports as pitch-class points on them, the beam is the ferry."""
    s = Svg()
    sw = c["swell"]
    gx0, gx1, gy0, gy1, div = 140, 340, 38, 198, 20
    cx, cy = 240, 118
    for i in range(11):
        x = gx0 + i * div
        s.line(x, gy0, x, gy1, 1.0, G1 if i not in (0, 10) else G2)
    for j in range(9):
        y = gy0 + j * div
        s.line(gx0, y, gx1, y, 1.0, G1 if j not in (0, 8) else G2)
    for t in range(1, 50):                        # minor ticks on the centre axes
        x = gx0 + t * 4
        if t % 5:
            s.line(x, cy - 2, x, cy + 2, 1.0, G2)
    for t in range(1, 40):
        y = gy0 + t * 4
        if t % 5:
            s.line(cx - 2, y, cx + 2, y, 1.0, G2)
    s.text(gx0 + 4, gy1 - 5, "X-Y", G4)
    s.text(gx1 - 30, gy1 - 5, "oct", G4)

    n = n_ports(c)
    ps = pitches(n)
    R = [40, 70, 98]
    sq = 0.42
    orbits = sorted({p // 12 for p in ps})
    for o in range(3):
        col = G3 if o in orbits else G2
        pts = ellipse_pts(cx, cy, R[o], R[o] * sq, n=60, wob=sw * 0.06, k=9)
        s.ribbon(pts + pts[:1], 1.0, col)

    def at(p):
        o, pc = p // 12, p % 12
        a = math.pi / 2 + pc / 12 * 2 * math.pi
        return (cx + R[o] * math.cos(a), cy + R[o] * sq * math.sin(a)), a, o

    # the route as trace links along each orbit, in travel direction
    seq = order(route(c), n, n + 1)
    for a_i, b_i in zip(seq, seq[1:]):
        (pa, aa, oa), (pb, ab, ob) = at(ps[a_i]), at(ps[b_i])
        if oa != ob:
            continue
        if ab < aa:
            ab += 2 * math.pi
        arc = ellipse_pts(cx, cy, R[oa], R[oa] * sq, n=24, a0=aa, a1=ab, wob=sw * 0.06, k=9)
        s.ribbon(arc, 1.5, G5)
    s.circle(cx, cy, 5, G0, G4, 1.5)             # the sun: the chord's root
    for i, p in enumerate(ps):
        (x, y), _, _ = at(p)
        if i == seq[0]:
            continue
        s.circle(x, y, 3.5, G0, G5, 1.5)
    (x, y), _, _ = at(ps[seq[0]])
    r = 3 + 6 * c["dwell"]                        # the beam dwells: a longer dwell burns a bigger spot
    s.circle(x, y, r, G7, G7, 2.0)
    return s


# ------------------------------------------------- v3 · P13 · typeset diagram
def v3(c):
    """A bay in plan: piers by pitch along the shore, each with a capture ring of dwell; legs of the route across the water."""
    s = Svg()
    sw = c["swell"]
    n = n_ports(c)
    ps = pitches(n)
    top = max(ps) or 1

    def shore(x):
        return 50 + 6 * math.sin((x - 20) / 440 * math.pi)

    coast = [(x, shore(x)) for x in range(16, 466, 10)]
    s.ribbon(coast, 1.5, G5)
    s.ribbon([(x, y + 5) for x, y in coast], 1.0, G2)

    xs = [72 + 336 * p / top for p in ps]
    heads = []
    r = 9 + 22 * c["dwell"]
    for x, p in zip(xs, ps):
        y0 = shore(x)
        s.line(x, y0, x, y0 + 14, 1.5, G5)
        hy = y0 + 14 + r * 0.6
        heads.append((x, hy))
        s.dashed(ellipse_pts(x, hy, r, r * 0.6, n=48, a0=0, a1=2 * math.pi * 47 / 48), 1.0, G3, dash=4, gap=3)
        s.text(x - 8, y0 - 8, name(p), G5)

    seq = order(route(c), n, n + 1)
    for leg, (a_i, b_i) in enumerate(zip(seq, seq[1:])):
        (xa, ya), (xb, yb) = heads[a_i], heads[b_i]
        depth = 28 + 0.32 * abs(xb - xa)
        mx, my = (xa + xb) / 2, max(ya, yb) + depth
        pts = []
        for i in range(41):
            t = i / 40
            x = (1 - t) ** 2 * xa + 2 * (1 - t) * t * mx + t * t * xb
            y = (1 - t) ** 2 * ya + 2 * (1 - t) * t * my + t * t * yb
            y += sw * 6 * math.sin(t * math.pi * 9) * math.sin(t * math.pi)
            pts.append((x, y))
        # the leg starts and ends at the capture ring, not the pier
        pts = [p for p in pts if math.hypot((p[0] - xa) / r, (p[1] - ya) / (r * 0.6)) > 1
               and math.hypot((p[0] - xb) / r, (p[1] - yb) / (r * 0.6)) > 1]
        s.ribbon(pts, 1.0, G4)
        lx, ly = (xa + xb) / 2, (ya + yb) / 2 * 0.5 + my * 0.5 + 0.5 * depth * 0 + 14
        s.text(lx - 3, min(ly, 206), str(leg + 1), G5)
    hx, hy = heads[seq[0]]
    s.poly(hull_plan(hx, hy, -0.35, L=16, B=6), G7, G7, 1.0)
    s.text(12, 210, "fig. 1", G4)
    return s


# ------------------------------------------------- v4 · P14 · orthographic elevation
def v4(c):
    """The timetable woven as cloth in elevation: one band per voyage, newest at the front (bottom), slabs raised by pitch."""
    s = Svg()
    sw = c["swell"]
    n, slots = n_ports(c), slots_per_bar(c)
    ps = pitches(n)
    top = max(ps) or 1
    x0, x1 = 48, 452
    cell = (x1 - x0) / slots
    bases = [74, 118, 162, 206]                 # oldest .. newest
    shades = [G2, G3, G4, G5]
    for k in range(slots):
        x = x0 + cell * (k + 0.5)
        s.line(x, 32, x, 206, 1.0, G1)          # warp threads
    labels = ["-3", "-2", "-1", "now"]
    woven_now = 3                               # the front row is part-woven
    cur = woven_now - 1
    for row, base in enumerate(bases):
        s.line(x0 - 4, base, x1 + 4, base, 1.0, G2)       # weft datum
        s.text(8, base - 1, labels[row], G4)
        seq = order(route(c), n, slots)
        count = slots if row < 3 else woven_now
        for k in range(count):
            lift = 3 + 26 * ps[seq[k]] / top
            dx = cell * late(k + 17 * row, sw)
            x = x0 + cell * k + cell * 0.2 + dx
            w = cell * 0.6
            y = base - lift - 7
            bright = row == 3 and k == cur
            s.rect(x, y, w, 7, G7 if bright else G0, G7 if bright else shades[row], 1.5)
    return s


# ------------------------------------------------- v5 · P4 · survey plan (stretch)
def v5(c):
    """Survey sheets of each port stacked in route order; the front sheet is the port the ferry lies at."""
    s = Svg()
    sw = c["swell"]
    n = n_ports(c)
    ps = pitches(n)
    seq = order(route(c), n, n)
    vis = min(n, 6)
    W0, H0 = 214, 110
    fx, fy = 36, 98
    ddx, ddy = 34, -12
    for layer in range(vis - 1, -1, -1):
        x, y = fx + ddx * layer, fy + ddy * layer
        front = layer == 0
        s.rect(x, y, W0, H0, G0, G5 if front else (G4 if layer == 1 else G3), 1.5)
        if not front:
            s.text(x + 4, y + 9.5, name(ps[seq[layer]]), G4)
    # front sheet: a harbour in plan
    x, y = fx, fy
    for i in range(1, W0 // 10):                  # border ticks, survey grid
        s.line(x + i * 10, y, x + i * 10, y + 3, 1.0, G2)
        s.line(x + i * 10, y + H0, x + i * 10, y + H0 - 3, 1.0, G2)
    for i in range(1, H0 // 10 + 1):
        if y + i * 10 < y + H0:
            s.line(x, y + i * 10, x + 3, y + i * 10, 1.0, G2)
            s.line(x + W0, y + i * 10, x + W0 - 3, y + i * 10, 1.0, G2)

    def coast(t, off):
        """Coast from the sheet's left edge round to its top edge; off pushes it seaward."""
        cxx, cyy = x + 6, y + 6
        a = t * math.pi / 2
        rr = 58 + off + sw * 4 * math.sin(t * 17 + off)
        return (cxx + rr * math.sin(a) * 1.9, cyy + rr * math.cos(a) * 0.95)

    for j, off in enumerate([0, 9, 18, 27]):
        pts = [coast(t / 30, off) for t in range(31)]
        pts = [(px, py) for px, py in pts if x + 4 < px < x + W0 - 4 and y + 4 < py < y + H0 - 4]
        s.ribbon(pts, 1.5 if j == 0 else 1.0, G5 if j == 0 else G2)
    # pier and berth
    px0, py0 = coast(0.42, 0)
    ang = math.atan2(py0 - (y + 6), (px0 - (x + 6)) / 1.9 * 0.95)
    ux, uy = math.cos(ang), math.sin(ang)
    s.line(px0, py0, px0 + ux * 34, py0 + uy * 34, 1.5, G5)
    blen = 16 + 26 * c["dwell"]
    bx, by = px0 + ux * 34 + uy * 6, py0 + uy * 34 - ux * 6
    nx, ny = -uy, ux
    corners = [(bx - nx * 5 - ux * blen, by - ny * 5 - uy * blen), (bx - nx * 5, by - ny * 5),
               (bx + nx * 5, by + ny * 5), (bx + nx * 5 - ux * blen, by + ny * 5 - uy * blen)]
    s.dashed(corners + [corners[0]], 1.0, G4, dash=4, gap=3)
    cxh, cyh = bx - ux * blen / 2, by - uy * blen / 2
    s.poly(hull_plan(cxh, cyh, ang + math.pi, L=min(blen - 4, 18), B=6), G7, G7, 1.0)
    s.text(x + W0 - 56, y + H0 - 7, name(ps[seq[0]]), G5)
    s.text(x + W0 - 30, y + H0 - 7, f"1/{n}", G4)
    return s


def main():
    c = DEFAULTS
    for nm, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        fn(c).write(HERE / nm / "rest.svg", captions(c))
        print(f"wrote {nm}/rest.svg")


if __name__ == "__main__":
    main()
