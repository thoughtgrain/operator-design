#!/usr/bin/env python3
"""Subject-pass sketches for lattice: five rest frames from one plate model.

    python3 screens/lattice/passes/01-subject/sketch.py

Writes v1..v5/rest.svg (480 x 220, stock header kept) and renders rest.png
beside each with rsvg-convert when it exists. Every variant draws from the
same small modal model of the plate (model below), so the five differ in
pattern and language, not in what the sound is.

Rest settings come from definition.json defaults: size 8, tension 40,
damp 30, pickup 60.
"""
from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 480, 220

# --- defaults (definition.json) ------------------------------------------
SIZE_LABELS = [4, 6, 8, 10, 12]
DEF = {"size": 0.5, "tension": 0.4, "damp": 0.3, "pickup": 0.6}
STRIKE = (0.3, 0.35)          # fixed excitation point, plate coordinates 0..1
ASPECT = 1.3                  # plate is a little wider than tall: splits degenerate modes
T0 = 0.37                     # snapshot time for the rest picture (in fundamental periods)


def size_n(v: float) -> int:
    return SIZE_LABELS[round(v * (len(SIZE_LABELS) - 1))]


def pickup_xy(p: float) -> tuple[float, float]:
    """Pickup slides from the strike point (0) to the far corner region (1)."""
    return (STRIKE[0] + p * (0.88 - STRIKE[0]), STRIKE[1] + p * (0.82 - STRIKE[1]))


# --- plate model ----------------------------------------------------------
def modes(n: int, tension: float):
    """Modes (m, k) a mesh of n junctions per side can carry, with frequency
    relative to (1,1). Tension blends a membrane (f ~ |k|) into a stiff plate
    (f ~ |k|^2), which stretches the upper modes apart."""
    out = []
    lim = max(2, n // 2)
    for m in range(1, lim + 1):
        for k in range(1, lim + 1):
            q = (m / ASPECT) ** 2 + k ** 2
            q1 = (1 / ASPECT) ** 2 + 1
            memb = math.sqrt(q / q1)
            plate = q / q1
            f = (1 - tension) * memb + tension * plate
            out.append((m, k, f))
    out.sort(key=lambda t: t[2])
    return out


def phi(m, k, x, y):
    return math.sin(m * math.pi * x) * math.sin(k * math.pi * y)


def tau(f, damp):
    """Ring time in fundamental periods; higher modes die faster."""
    return (0.4 + 9.0 * (1 - damp) ** 2) / (1 + 0.6 * (f - 1))


def field(x, y, s=DEF):
    n, t, d = size_n(s["size"]), s["tension"], s["damp"]
    v = 0.0
    for m, k, f in modes(n, t):
        a = phi(m, k, *STRIKE) / math.sqrt(m * m + k * k)
        v += a * phi(m, k, x, y) * math.cos(2 * math.pi * f * T0) * math.exp(-T0 / tau(f, d))
    return v


def response(t, s=DEF):
    """Output at the pickup after a strike, t in fundamental periods."""
    n, tn, d = size_n(s["size"]), s["tension"], s["damp"]
    px, py = pickup_xy(s["pickup"])
    v = 0.0
    for m, k, f in modes(n, tn)[:6]:
        a = phi(m, k, *STRIKE) * phi(m, k, px, py) / math.sqrt(m * m + k * k)
        v += a * math.cos(2 * math.pi * f * t) * math.exp(-t / tau(f, d) * 1.6)
    return v


# --- svg helpers ----------------------------------------------------------
def fmt(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


class Svg:
    def __init__(self, labels, values):
        self.out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
                    '  <g id="preview_canvas">',
                    f'    <rect x="0" y="0" width="{W}" height="{H}" fill="#000000" stroke="none"/>',
                    '  </g>']
        self.header(labels, values)

    def header(self, labels, values):
        steps = ["#000000", "#323232", "#4B4B4B", "#646464", "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD"]
        o = ['  <g id="preview_header">']
        for i, c in enumerate(steps):
            o.append(f'    <rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
        for i, (lab, val) in enumerate(zip(labels, values)):
            col = "#CBCBCB" if i < 2 else "#000000"
            o.append(f'    <text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{col}" stroke="none" '
                     f'font-family="UniversNextPro-Light" font-size="10px">{lab}</text>')
            o.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{col}" stroke="none" '
                     f'font-family="UniversNextPro-Light" font-size="20px">{val}</text>')
        o.append('  </g>')
        self.out += o

    def path(self, pts, fill="none", stroke="none", sw=None, closed=True):
        clean = []
        for p in pts:
            if not clean or math.dist(p, clean[-1]) >= 0.2:
                clean.append(p)
        if closed and len(clean) > 2 and math.dist(clean[0], clean[-1]) < 0.3:
            clean.pop()
        d = "M " + " L ".join(f"{fmt(x)} {fmt(y)}" for x, y in clean) + (" Z" if closed else "")
        sws = f' stroke-width="{sw}"' if stroke != "none" else ""
        self.out.append(f'  <path d="{d}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def circle(self, cx, cy, r, fill="none", stroke="none", sw=None):
        sws = f' stroke-width="{sw}"' if stroke != "none" else ""
        self.out.append(f'  <circle cx="{fmt(cx)}" cy="{fmt(cy)}" r="{fmt(r)}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def rect(self, x, y, w, h, fill, stroke="none", sw=None):
        self.path([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], fill, stroke, sw)

    def text(self, x, y, s, fill="#7D7D7D", size=10):
        self.out.append(f'  <text transform="matrix(1 0 0 1 {fmt(x)} {fmt(y)})" fill="{fill}" stroke="none" '
                        f'font-family="UniversNextPro-Light" font-size="{size}px">{s}</text>')

    def line(self, pts, w, fill):
        """An open line as closed ribbons of at most 64 points each."""
        pts = dedupe(pts)
        if len(pts) < 2:
            return
        chunk = 30
        i = 0
        while i < len(pts) - 1:
            seg = pts[i:i + chunk + 1]
            self.path(ribbon(seg, w), fill)
            i += chunk

    def save(self, path: Path):
        path.write_text("\n".join(self.out + ["</svg>", ""]))


def dedupe(pts, gap=1.0):
    out = []
    for p in pts:
        if not out or math.dist(p, out[-1]) >= gap:
            out.append(p)
    if len(out) >= 2 and math.dist(pts[-1], out[-1]) > 0.01 and math.dist(pts[-1], out[-1]) < gap:
        out[-1] = pts[-1]
    return out


def ribbon(pts, w):
    left, right = [], []
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L * w / 2, dx / L * w / 2
        left.append((x + nx, y + ny))
        right.append((x - nx, y - ny))
    return left + right[::-1]


def seg(a, b, w, fill, s: Svg):
    s.path(ribbon([a, b], w), fill)


def dashed(s: Svg, pts, w, fill, on=4.0, off=3.0):
    """Dash a polyline into short closed ribbons."""
    pts = dedupe(pts, 0.5)
    acc, cur, drawing = 0.0, [pts[0]], True
    for a, b in zip(pts, pts[1:]):
        L = math.dist(a, b)
        t = 0.0
        while t < L:
            room = (on if drawing else off) - acc
            step = min(room, L - t)
            t += step
            acc += step
            p = (a[0] + (b[0] - a[0]) * t / L, a[1] + (b[1] - a[1]) * t / L)
            if drawing:
                cur.append(p)
            if acc >= (on if drawing else off) - 1e-9:
                if drawing and len(cur) >= 2:
                    s.line(cur, w, fill)
                drawing, acc, cur = not drawing, 0.0, [p]
    if drawing and len(cur) >= 2 and math.dist(cur[0], cur[-1]) > 1:
        s.line(cur, w, fill)


def clip(p, q, x0, y0, x1, y1):
    """Liang-Barsky clip of segment pq to a rectangle."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    t0, t1 = 0.0, 1.0
    for pp, qq in ((-dx, p[0] - x0), (dx, x1 - p[0]), (-dy, p[1] - y0), (dy, y1 - p[1])):
        if pp == 0:
            if qq < 0:
                return None
        else:
            r = qq / pp
            if pp < 0:
                t0 = max(t0, r)
            else:
                t1 = min(t1, r)
    if t0 >= t1:
        return None
    return (p[0] + t0 * dx, p[1] + t0 * dy), (p[0] + t1 * dx, p[1] + t1 * dy)


def hatch(s: Svg, x0, y0, x1, y1, gap, fill, w=1.0):
    """45-degree section hatching inside a rectangle."""
    c = x0 - (y1 - y0)
    while c < x1:
        r = clip((c, y1), (c + 400, y1 - 400), x0, y0, x1, y1)
        if r and math.dist(*r) > 2:
            seg(r[0], r[1], w, fill, s)
        c += gap * math.sqrt(2)


HEADER = (["size", "tension", "damp", "pickup"],
          [str(size_n(DEF["size"])), str(round(DEF["tension"] * 100)),
           str(round(DEF["damp"] * 100)), str(round(DEF["pickup"] * 100))])


# --- v1 · P15 cell field, patent section ----------------------------------
def v1():
    s = Svg(*HEADER)
    n = size_n(DEF["size"])
    pitch = 14
    side = n * pitch
    x0, y0 = 196 - side / 2, 119 - side / 2
    vals = [[abs(field((i + 0.5) / n, (j + 0.5) / n)) for i in range(n)] for j in range(n)]
    top = max(max(r) for r in vals) or 1
    felt = DEF["damp"] * (n / 2 - 1)          # felt band depth, in cells
    # clamp frame: a hatched section band all round (held at the edges)
    fw = 10
    fx0, fy0, fx1, fy1 = x0 - fw - 2, y0 - fw - 2, x0 + side + fw + 2, y0 + side + fw + 2
    for bx0, by0, bx1, by1 in ((fx0, fy0, fx1, y0 - 2), (fx0, y0 + side + 2, fx1, fy1),
                               (fx0, y0 - 2, x0 - 2, y0 + side + 2), (x0 + side + 2, y0 - 2, fx1, y0 + side + 2)):
        hatch(s, bx0, by0, bx1, by1, 4, "#4B4B4B", 1.0)
    s.rect(fx0, fy0, fx1 - fx0, fy1 - fy0, "none", "#7D7D7D", 1.5)
    s.rect(x0 - 2, y0 - 2, side + 4, side + 4, "none", "#7D7D7D", 1.5)
    # cells: one per mesh junction, value = displacement snapshot
    for j in range(n):
        for i in range(n):
            edge = min(i, j, n - 1 - i, n - 1 - j)
            cx, cy = x0 + i * pitch + 0.5, y0 + j * pitch + 0.5
            if edge < felt:
                s.rect(cx + 2, cy + 2, pitch - 5, pitch - 5, "#000000", "#4B4B4B", 1.0)
                continue
            v = vals[j][i] / top
            g = "#AFAFAF" if v > 0.62 else "#7D7D7D" if v > 0.36 else "#4B4B4B" if v > 0.16 else None
            if g:
                s.rect(cx, cy, pitch - 1, pitch - 1, g)
    # felt line: the inner edge of the damping band
    fd = math.ceil(felt) * pitch
    if fd > 0:
        s.rect(x0 + fd - 1, y0 + fd - 1, side - 2 * fd + 2, side - 2 * fd + 2, "none", "#969696", 1.0)
    # strike and pickup
    sx, sy = x0 + STRIKE[0] * side, y0 + STRIKE[1] * side
    s.circle(sx, sy, 4, "#000000", "#CBCBCB", 1.5)
    px, py = pickup_xy(DEF["pickup"])
    pi_, pj = min(n - 1, int(px * n)), min(n - 1, int(py * n))
    s.rect(x0 + pi_ * pitch - 1, y0 + pj * pitch - 1, pitch + 1, pitch + 1, "none", "#CDCDCD", 2.25)
    # patent numerals with leader lines
    lx = 336
    leaders = [("10", 52, (x0 + side - 2, y0 + 12)),
               ("12", 82, (sx + 4, sy - 2)),
               ("14", 118, (x0 + (pi_ + 1) * pitch, y0 + pj * pitch + 4)),
               ("16", 158, (x0 + side + fw, y0 + side + 4))]
    for num, ty, (ax, ay) in leaders:
        mx = (lx - 6 + ax) / 2
        s.line([(lx - 4, ty - 3), (mx + 10, ty - 3 + (ay - ty + 3) * 0.3), (ax, ay)], 1.0, "#646464")
        s.text(lx, ty, num, "#969696")
    s.text(20, 208, "fig. 1", "#7D7D7D")
    s.text(372, 82, "strike", "#7D7D7D")
    s.text(372, 118, "pickup", "#7D7D7D")
    return s


# --- v2 · P1 section drawing, hidden-line isometric ------------------------
def v2():
    s = Svg(*HEADER)
    n = size_n(DEF["size"])
    k = 105 + (n - 4) * 6.5
    cx, cy = 222, 128
    vals = {}
    zs = 18.0

    def P(u, v, z=0.0):
        return (cx + (u - v) * k * 0.866, cy + (u + v - 1) * k * 0.5 - z)

    top = max(abs(field(u / 20, v / 20)) for u in range(21) for v in range(21)) or 1

    def Z(u, v):
        key = (round(u, 4), round(v, 4))
        if key not in vals:
            vals[key] = field(u, v) / top * zs
        return vals[key]

    e = 0.07
    # clamp frame: top surface ring and its near faces, drawn behind the plate
    outer = [P(-e, -e), P(1 + e, -e), P(1 + e, 1 + e), P(-e, 1 + e)]
    th = 8
    # near faces (u = 1+e side and v = 1+e side face the viewer)
    s.path([P(1 + e, -e), P(1 + e, 1 + e), (P(1 + e, 1 + e)[0], P(1 + e, 1 + e)[1] + th),
            (P(1 + e, -e)[0], P(1 + e, -e)[1] + th)], "#323232", "#646464", 1.0)
    s.path([P(1 + e, 1 + e), P(-e, 1 + e), (P(-e, 1 + e)[0], P(-e, 1 + e)[1] + th),
            (P(1 + e, 1 + e)[0], P(1 + e, 1 + e)[1] + th)], "#323232", "#646464", 1.0)
    s.path(outer, "#000000", "#7D7D7D", 1.5)
    for (u, v) in ((-e / 2, -e / 2), (1 + e / 2, -e / 2), (1 + e / 2, 1 + e / 2), (-e / 2, 1 + e / 2),
                   (0.5, -e / 2), (0.5, 1 + e / 2), (-e / 2, 0.5), (1 + e / 2, 0.5)):
        x, y = P(u, v)
        s.circle(x, y, 2, "#000000", "#7D7D7D", 1.0)
    # plate: black body hides the frame's inner edge, then mesh lines, then outline
    edge = ([P(t / 16, 0, Z(t / 16, 0)) for t in range(16)] + [P(1, t / 16, Z(1, t / 16)) for t in range(16)] +
            [P(1 - t / 16, 1, Z(1 - t / 16, 1)) for t in range(16)] + [P(0, 1 - t / 16, Z(0, 1 - t / 16)) for t in range(16)])
    s.path(edge, "#000000", "none")
    for i in range(1, n - 1):
        a = i / (n - 1)
        s.line([P(a, t / 24, Z(a, t / 24)) for t in range(25)], 1.0, "#646464")
        s.line([P(t / 24, a, Z(t / 24, a)) for t in range(25)], 1.0, "#646464")
    s.path(edge, "none", "#CDCDCD", 2.25)
    # striker: rod and head above the strike point
    sx, sy = P(*STRIKE, Z(*STRIKE))
    s.line([(sx, sy - 3), (sx, sy - 44)], 1.5, "#969696")
    s.path([(sx - 5, sy - 44), (sx + 5, sy - 44), (sx + 5, sy - 54), (sx - 5, sy - 54)], "#323232", "#AFAFAF", 1.5)
    s.circle(sx, sy, 2.5, "#000000", "#AFAFAF", 1.5)
    # pickup: a stylus pin at its point, lead to the right
    pu, pv = pickup_xy(DEF["pickup"])
    qx, qy = P(pu, pv, Z(pu, pv))
    s.line([(qx, qy - 3), (qx, qy - 26)], 1.5, "#969696")
    s.circle(qx, qy, 2.5, "#000000", "#AFAFAF", 1.5)
    s.line([(qx, qy - 26), (qx + 40, qy - 26), (404, 96)], 1.0, "#646464")
    s.text(408, 99, "pickup")
    # damper: a felt block hanging over the far edge, its height set by damp
    du, dv = 0.78, 0.12
    lift = (1 - DEF["damp"]) * 40
    bw, bd, bh = 0.16, 0.08, 7
    base = [P(du - bw / 2, dv - bd / 2), P(du + bw / 2, dv - bd / 2), P(du + bw / 2, dv + bd / 2), P(du - bw / 2, dv + bd / 2)]
    dashed(s, base + [base[0]], 1.0, "#4B4B4B", 3, 3)
    up = lambda p, h: (p[0], p[1] - h)
    b = [up(p, lift) for p in base]
    t = [up(p, lift + bh) for p in base]
    s.path([b[1], b[2], b[3], t[3], t[2], t[1]], "#323232", "#7D7D7D", 1.0)
    s.path(t, "#4B4B4B", "#7D7D7D", 1.0)
    s.line([((t[0][0] + t[2][0]) / 2, (t[0][1] + t[2][1]) / 2), ((t[0][0] + t[2][0]) / 2, 30)], 1.0, "#646464")
    s.text(sx - 40, sy - 48, "strike")
    s.text(((t[0][0] + t[2][0]) / 2) + 6, 40, "damper")
    return s


# --- v3 · P2 diagram + trace, star atlas ----------------------------------
def v3():
    s = Svg(*HEADER)
    n = size_n(DEF["size"])
    X0, Y0, X1, Y1 = 22, 34, 214, 206

    def chart(u, v):
        # a gentle conic projection: rows bow, columns converge toward the top
        w = (X1 - X0 - 28)
        h = (Y1 - Y0 - 28)
        sx = 1 - 0.12 * (1 - v)
        x = (X0 + X1) / 2 + (u - 0.5) * w * sx
        y = Y0 + 14 + v * h + 10 * ((u - 0.5) ** 2) * 2
        return x, y

    # neat line (double) with ticks at the mesh pitch
    s.rect(X0, Y0, X1 - X0, Y1 - Y0, "none", "#7D7D7D", 1.0)
    s.rect(X0 - 4, Y0 - 4, X1 - X0 + 8, Y1 - Y0 + 8, "none", "#7D7D7D", 1.5)
    for i in range(n):
        x = chart((i + 0.5) / n, 1)[0]
        seg((x, Y1), (x, Y1 - 4), 1.0, "#7D7D7D", s)
        x2 = chart((i + 0.5) / n, 0)[0]
        seg((x2, Y0), (x2, Y0 + 4), 1.0, "#7D7D7D", s)
    # graticule
    for g in range(1, 4):
        a = g / 4
        s.line([chart(a, t / 20) for t in range(21)], 1.0, "#4B4B4B")
        s.line([chart(t / 20, a) for t in range(21)], 1.0, "#4B4B4B")
    # stars at the mesh junctions, magnitude from the displacement snapshot
    vals = [[abs(field((i + 0.5) / n, (j + 0.5) / n)) for i in range(n)] for j in range(n)]
    top = max(max(r) for r in vals) or 1
    for j in range(n):
        for i in range(n):
            v = vals[j][i] / top
            x, y = chart((i + 0.5) / n, (j + 0.5) / n)
            if v > 0.12:
                s.circle(x, y, 1.5 + 2.2 * v, "#969696")
            else:
                s.circle(x, y, 1.5, "#000000", "#646464", 1.0)
    # strike and pickup, joined by a constellation line that sags without tension
    a = chart(*STRIKE)
    b = chart(*pickup_xy(DEF["pickup"]))
    sag = (1 - DEF["tension"]) * 34
    pts = []
    for t in range(25):
        f = t / 24
        x = a[0] + (b[0] - a[0]) * f
        y = a[1] + (b[1] - a[1]) * f + sag * 4 * f * (1 - f)
        pts.append((x, y))
    trimmed = [p for p in pts if math.dist(p, a) > 7 and math.dist(p, b) > 8]
    s.line(trimmed, 1.5, "#AFAFAF")
    s.circle(*a, 5, "#000000", "#AFAFAF", 1.5)
    s.circle(*a, 2, "#AFAFAF")
    s.circle(*b, 6, "#000000", "#AFAFAF", 1.5)
    s.circle(*b, 2.5, "#AFAFAF")
    s.text(a[0] - 40, a[1] + 3, "strike")
    s.text(b[0] - 14, b[1] + 18, "pickup")
    # light curve: what the pickup hears after a strike
    ax, ay, ax1 = 262, 120, 462
    s.line([(ax, 40), (ax, 200)], 1.0, "#646464")
    s.line([(ax, ay), (ax1, ay)], 1.0, "#4B4B4B")
    for i in range(1, 11):
        x = ax + i * (ax1 - ax) / 10
        seg((x, ay - 2.5), (x, ay + 2.5), 1.0, "#646464", s)
    span = 6.0
    N = 180
    samples = [response(span * i / N) for i in range(N + 1)]
    top = max(abs(v) for v in samples) or 1
    curve = [(ax + 2 + (ax1 - ax - 4) * i / N, ay - 62 * samples[i] / top) for i in range(N + 1)]
    s.line(curve, 2.0, "#CDCDCD")
    s.text(ax1 - 6, ay + 16, "t")
    s.text(ax + 6, 44, "out")
    return s


# --- v4 · P3 trace as subject, engineering schematic ------------------------
def v4():
    s = Svg(*HEADER)
    n = size_n(DEF["size"])
    span = 120 + (n - 4) / 8 * 260
    xa, xb = 240 - span / 2, 240 + span / 2
    yc = 104
    amp = 44 * (1 - 0.65 * DEF["damp"])
    px, py = pickup_xy(DEF["pickup"])
    # the section line runs through strike and pickup: x across the span
    lim = max(2, n // 2)
    ms = [(m, (1 - DEF["tension"]) * m + DEF["tension"] * m * m) for m in range(1, lim + 1)]

    def g(x):
        return sum(math.sin(m * math.pi * STRIKE[0]) / m * math.sin(m * math.pi * x) *
                   math.cos(2 * math.pi * f * T0) * math.exp(-T0 / tau(f, DEF["damp"])) for m, f in ms)

    def env(x):
        return sum(abs(math.sin(m * math.pi * STRIKE[0]) / m * math.sin(m * math.pi * x)) for m, f in ms)

    top = max(env(i / 100) for i in range(101)) or 1
    # fixed supports: wall line, section hatch on the outside
    for x, side in ((xa, -1), (xb, 1)):
        s.line([(x, yc - 34), (x, yc + 34)], 2.0, "#969696")
        for i in range(8):
            y = yc - 30 + i * 9
            s.line([(x, y + 4), (x + side * 7, y - 3)], 1.0, "#646464")
    # envelope of the swing, dashed
    dashed(s, [(xa + (xb - xa) * i / 60, yc - amp * env(i / 60) / top) for i in range(61)], 1.0, "#646464")
    dashed(s, [(xa + (xb - xa) * i / 60, yc + amp * env(i / 60) / top) for i in range(61)], 1.0, "#646464")
    # centre line (chain line)
    dashed(s, [(xa - 14, yc), (xb + 14, yc)], 1.0, "#4B4B4B", 10, 3)
    # the trace: the plate's cut through strike and pickup
    s.line([(xa + (xb - xa) * i / 120, yc - amp * g(i / 120) / top) for i in range(121)], 2.25, "#CDCDCD")
    # strike: a force arrow onto the plate
    sx = xa + (xb - xa) * STRIKE[0]
    sy = yc - amp * g(STRIKE[0]) / top
    s.line([(sx, 34), (sx, sy - 10)], 1.5, "#969696")
    s.path([(sx - 4, sy - 11), (sx + 4, sy - 11), (sx, sy - 3)], "#969696")
    s.text(sx + 6, 44, "strike")
    # pickup probe on the trace, lead down to the output terminal
    qf = STRIKE[0] + DEF["pickup"] * (0.92 - STRIKE[0])
    qx = xa + (xb - xa) * qf
    qy = yc - amp * g(qf) / top
    s.circle(qx, qy, 3.5, "#000000", "#AFAFAF", 1.5)
    s.line([(qx, qy + 4), (qx, 166)], 1.0, "#7D7D7D")
    s.circle(qx, 170, 4, "#000000", "#969696", 1.5)
    s.text(qx + 8, 174, "out")
    # dimension line for the span
    yd = 192
    for x in (xa, xb):
        s.line([(x, yc + 40), (x, yd + 5)], 1.0, "#646464")
    s.line([(xa + 6, yd), (xb - 6, yd)], 1.0, "#7D7D7D")
    s.path([(xa, yd), (xa + 7, yd - 3), (xa + 7, yd + 3)], "#7D7D7D")
    s.path([(xb, yd), (xb - 7, yd + 3), (xb - 7, yd - 3)], "#7D7D7D")
    s.rect(240 - 18, yd - 7, 36, 14, "#000000")
    s.text(240 - 11, yd + 4, "span")
    # title block
    s.rect(392, 196, 82, 18, "none", "#646464", 1.0)
    s.text(397, 209, "plate sect.", "#7D7D7D")
    return s


# --- v5 · P12 orrery, oscilloscope trace (stretch) ------------------------
def v5():
    s = Svg(*HEADER)
    n = size_n(DEF["size"])
    cx, cy = 240, 120
    tilt = 0.36
    # graticule: 10 x 8 divisions, centre axes with minor ticks
    gx0, gx1, gy0, gy1 = 40, 440, 32, 208
    for i in range(11):
        x = gx0 + i * 40
        dashed(s, [(x, gy0), (x, gy1)], 1.0, "#323232", 2, 4)
    for j in range(9):
        y = gy0 + j * 22
        dashed(s, [(gx0, y), (gx1, y)], 1.0, "#323232", 2, 4)
    for i in range(51):
        x = gx0 + i * 8
        seg((x, cy - 2), (x, cy + 2), 1.0, "#4B4B4B", s)
    # modes as orbits: radius from frequency, count from size
    ms = modes(n, DEF["tension"])[:n]
    f1, fK = ms[0][2], ms[-1][2]
    px, py = pickup_xy(DEF["pickup"])
    amps = [abs(phi(m, k, *STRIKE) * phi(m, k, px, py)) for m, k, f in ms]
    amax = max(amps) or 1
    loud = amps.index(max(amps))

    def E(a, th):
        return cx + a * math.cos(th), cy + a * tilt * math.sin(th)

    rings = []
    for idx, (m, k, f) in enumerate(ms):
        a = 26 + 172 * (f - f1) / ((fK - f1) or 1)
        th = 2 * math.pi * (f * T0 % 1)
        trail = min(0.92, 0.18 + 0.9 * tau(f, DEF["damp"]) / 10) * 2 * math.pi
        rings.append((a, th, trail, amps[idx] / amax, idx == loud))

    def orbit(a, lo, hi, fill, w):
        steps = max(8, int(abs(hi - lo) * a / 4))
        s.line([E(a, lo + (hi - lo) * i / steps) for i in range(steps + 1)], w, fill)

    def trail_arc(a, th, trail, far):
        # phosphor trail behind the planet (orbit runs with increasing angle); split at the sun's depth
        lo, hi = th - trail, th
        pieces = []
        for base in range(-2, 3):
            for (s0, s1, isfar) in ((base * 2 * math.pi + math.pi, base * 2 * math.pi + 2 * math.pi, True),
                                    (base * 2 * math.pi, base * 2 * math.pi + math.pi, False)):
                a0, a1 = max(lo, s0), min(hi, s1)
                if a1 - a0 > 0.02 and isfar == far:
                    pieces.append((a0, a1))
        for a0, a1 in pieces:
            orbit(a, a0, a1, "#969696", 1.5)

    for far in (True, False):
        for a, th, trail, amp, is_loud in rings:
            lo, hi = (math.pi, 2 * math.pi) if far else (0, math.pi)
            orbit(a, lo + 0.01, hi - 0.01, "#4B4B4B", 1.0)
        for a, th, trail, amp, is_loud in rings:
            trail_arc(a, th, trail, far)
        if far:
            s.circle(cx, cy, 6, "#000000", "#969696", 1.5)
        for a, th, trail, amp, is_loud in rings:
            if (math.sin(th) < 0) == far:
                x, y = E(a, th)
                r = 2 + 4.5 * amp
                if is_loud:
                    s.circle(x, y, r, "#CDCDCD")
                else:
                    s.circle(x, y, r, "#000000", "#AFAFAF", 1.5)
    s.text(gx0 + 4, gy1 - 6, "x-y", "#7D7D7D")
    return s


def main():
    rsvg = shutil.which("rsvg-convert")
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        d = HERE / name
        d.mkdir(exist_ok=True)
        svg = d / "rest.svg"
        fn().save(svg)
        if rsvg:
            subprocess.run([rsvg, "-w", str(W), "-h", str(H), "-b", "black", str(svg), "-o", str(d / "rest.png")], check=True)
        print("wrote", svg)


if __name__ == "__main__":
    main()
