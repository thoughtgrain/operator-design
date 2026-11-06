#!/usr/bin/env python3
"""Pylon subject pass 01: one rest.svg sketch per direction (v1..v5), all from one model.

    python3 screens/pylon/passes/01-subject/sketch.py

Sketches follow opxy/craft.md (one drawing language, three line weights, one bright subject)
and the authoring rules in opxy/constraints.md, but haven't been through phases 4-5 yet.
Every line is a closed filled ribbon; every leaf has explicit paint; grey only.
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


# ---- v1 · P10 voice field, patent section ---------------------------------------------------------------------------
def v1(p):
    fr = Frame()
    NI, NJ = 10 + round(8 * p["span"]), 5      # span: slabs along the line
    u, v = (13.0, 4.0), (-8.0, 6.0)
    O = (150.0, 92.0)
    T = 6.0
    w = mode_weights(p)

    def P(i, j, h=0.0):
        return (O[0] + i * u[0] + j * v[0], O[1] + i * u[1] + j * v[1] - h)

    heights = {}
    for j in range(NJ):
        for i in range(NI):
            x = (i + 0.5) / NI
            s = sum(a * math.sin(n * math.pi * x) * math.cos(0.42 * n * j) for n, a in w.items())
            heights[(i, j)] = abs(s)
    top = max(heights.values()) or 1
    for k in heights:
        heights[k] = round(34 * heights[k] / top)

    # pylon cross-arms, cut in section at both ends of the span (static)
    for i_end, side in ((0, -1), (NI, 1)):
        a = P(i_end, 0, 0)
        q = ((a[0] + (2 if side < 0 else 0), a[1] + 12), (v[0] * NJ, v[1] * NJ), (0.0, -50.0))
        o, ea, eb = q
        corners = [o, (o[0] + ea[0], o[1] + ea[1]), (o[0] + ea[0] + eb[0], o[1] + ea[1] + eb[1]), (o[0] + eb[0], o[1] + eb[1])]
        fr.poly(corners, G0, G4, HAIR)
        hatch_quad(fr, q, 5.0, 1.0, G3)

    cells = sorted(heights, key=lambda k: (k[0] * u[1] + k[1] * v[1], k[0]))
    for (i, j) in cells:
        h = heights[(i, j)]
        a, b, c, d = P(i, j, h + T), P(i + 1, j, h + T), P(i + 1, j + 1, h + T), P(i, j + 1, h + T)
        hollow = h < 12
        crest = h >= 30
        edge = G4 if hollow else G5
        # front face (edge d-c), right face (edge b-c), then top
        fr.poly([d, c, (c[0], c[1] + T), (d[0], d[1] + T)], G0 if hollow else G1, edge, HAIR, bind=True)
        fr.poly([b, c, (c[0], c[1] + T), (b[0], b[1] + T)], G0 if hollow else G2, edge, HAIR, bind=True)
        fr.poly([a, b, c, d], G0 if hollow else (G7 if crest else G4), edge, HAIR, bind=True)

    # patent callouts: numerals with plain leaders, at fixed places
    fr.text(36, 52, "10")
    fr.seg((50, 56), (112, 76), HAIR, G4)          # pylon section
    fr.text(408, 80, "12")
    fr.seg((404, 82), (330, 120), HAIR, G4)       # field
    fr.text(66, 190, "14")
    fr.seg((82, 186), (128, 140), HAIR, G4)       # a conductor row
    fr.text(420, 200, "fig. 1", G4)
    return fr.svg(p, [G7, G5, G4, G0])


# ---- v2 · P15 cell field, hidden-line isometric ----------------------------------------------------------------------
def v2(p):
    fr = Frame()
    NI, NJ = 13, 8                    # i downwind, j along the wire
    s = 16.0
    u, v = (s * 0.866, s * 0.5), (-s * 0.866, s * 0.5)
    O = (214.0, 46.0)
    RAISE = 6.0

    def P(i, j, h=0.0):
        return (O[0] + i * u[0] + j * v[0], O[1] + i * u[1] + j * v[1] - h)

    rng = random.Random(7)
    rolls = 2 + round(5 * p["wind"])                      # vortex rolls still standing downwind
    run = 2 + round(6 * p["span"])                        # spanwise correlation: cells per run along the wire
    lit = set()
    for k in range(rolls):
        i = 1 + 2 * k
        if i >= NI:
            break
        j0 = (k * 3) % max(1, NJ - run + 1) if run < NJ else 0
        for j in range(j0, min(NJ, j0 + run)):
            di = 0
            if p["gust"] > 0 and rng.random() < p["gust"]:
                di = rng.choice((-1, 1)) * (1 + int(rng.random() * 2 * p["gust"]))
            if 0 <= i + di < NI:
                lit.add((i + di, j))
    grey = set()
    hum_n = round(p["hum"] * 40)
    lattice = [(i, j) for i in range(NI) for j in range(NJ) if (i + 2 * j) % 3 == 0 and (i, j) not in lit]
    grey.update(lattice[:hum_n])

    order = sorted(((i, j) for i in range(NI) for j in range(NJ)), key=lambda k: (k[0] + k[1], k[0]))
    for (i, j) in order:
        if (i, j) in lit:
            a, b, c, d = P(i, j, RAISE), P(i + 1, j, RAISE), P(i + 1, j + 1, RAISE), P(i, j + 1, RAISE)
            fr.poly([d, c, (c[0], c[1] + RAISE), (d[0], d[1] + RAISE)], G2, G4, HAIR, bind=True)
            fr.poly([b, c, (c[0], c[1] + RAISE), (b[0], b[1] + RAISE)], G1, G4, HAIR, bind=True)
            fr.poly([a, b, c, d], G5, G6, HAIR, bind=True)
        else:
            fill = G3 if (i, j) in grey else G0
            fr.poly([P(i, j), P(i + 1, j), P(i + 1, j + 1), P(i, j + 1)], fill, G1, 1.0, bind=True)

    # the conductor: a bright ribbon over the upwind edge, on two short masts at the field's corners
    H = 22.0
    a, b = P(0.45, -0.2, H), P(0.45, NJ + 0.2, H)
    fr.seg((a[0], a[1]), (a[0], a[1] + H + 4), LINE, G4)
    fr.seg((b[0], b[1]), (b[0], b[1] + H + 4), LINE, G4)
    fr.seg(a, b, 2.5, G7)
    return fr.svg(p, [G7, G5, G3, G1])


# ---- v3 · P1 section drawing, star atlas -----------------------------------------------------------------------------
def v3(p):
    fr = Frame()
    C = (240.0, 760.0)                           # pole of the chart, far below the screen
    # graticule: altitude arcs and azimuth lines, hairline ground
    for r in (560, 600, 640, 680):
        pts = []
        for k in range(61):
            ang = math.radians(-112 + 44 * k / 60)
            x, y = C[0] + r * math.cos(ang - math.pi / 2 + math.pi / 2 - math.pi / 2), 0
            ang2 = -math.pi / 2 + math.radians(-22 + 44 * k / 60)
            x, y = C[0] + r * math.cos(ang2), C[1] + r * math.sin(ang2)
            if 24 <= y <= 216 and 0 <= x <= 480:
                pts.append((x, y))
        if len(pts) > 2:
            fr.ribbon(pts, HAIR, G1 if r != 560 else G3)
    for deg in range(-20, 21, 5):
        ang = -math.pi / 2 + math.radians(deg)
        A = (C[0] + 560 * math.cos(ang), C[1] + 560 * math.sin(ang))
        B = (C[0] + 740 * math.cos(ang), C[1] + 740 * math.sin(ang))
        t0 = max(0.0, (A[1] - 216) / (A[1] - B[1])) if A[1] > 216 else 0.0
        t1 = (A[1] - 26) / (A[1] - B[1])
        fr.seg(lerp(A, B, t0), lerp(A, B, min(1, t1)), HAIR, G1)
    fr.text(8, 196, "0°", G4)
    fr.text(8, 158, "5°", G4)
    fr.text(8, 120, "10°", G4)
    fr.text(452, 196, "az", G4)

    # background field stars (static, magnitudes by size)
    rng = random.Random(11)
    for _ in range(14):
        x, y = rng.uniform(30, 450), rng.uniform(30, 120)
        fr.circle((x, y), rng.choice((1.6, 2.0, 2.4)), G3)

    # the span: two pylon heads and the wire between them, a chain of standing-wave loops on its catenary
    half = 70 + 110 * p["span"]
    sag = 18 + 46 * p["span"]
    A, B = (240 - half, 92.0), (240 + half, 92.0)
    n = max(1, round(lock_mode(p)))
    amp = 9.0
    N = 31

    def cat(t):
        x = A[0] + (B[0] - A[0]) * t
        return x, A[1] + sag * (1 - (2 * t - 1) ** 2)

    upper, lower = [], []
    for k in range(N):
        t = k / (N - 1)
        x, y = cat(t)
        dis = max(1.0, amp * abs(math.sin(n * math.pi * t)))
        upper.append((x, y - dis))
        lower.append((x, y + dis))
    fr.poly(upper + lower[::-1][1:-1], G0, G7, SUBJ, bind=True)
    # antinodes: stars on the wire, plotted at the loop crests
    for k in range(n):
        t = (k + 0.5) / n
        fr.circle(cat(t), 2.4, G6, bind=True)
    # pylon heads as double stars with plumb lines to the horizon
    for P_ in (A, B):
        fr.circle(P_, 4.0, G6, bind=True)
        fr.seg((P_[0], P_[1] + 7), (P_[0], 200), HAIR, G3)
    fr.text(36, 52, "radiant", G4)
    fr.circle((50, 62), 2.4, G0, G4, HAIR)
    # gust: meteor trails pointing back to the radiant (count; none at 0)
    k_tr = round(12 * p["gust"])
    for k in range(k_tr):
        ang = math.radians(10 + 7 * k)
        r0 = 50 + 13 * (k % 4)
        a = (50 + r0 * math.cos(ang), 62 + r0 * math.sin(ang))
        b = (50 + (r0 + 26) * math.cos(ang), 62 + (r0 + 26) * math.sin(ang))
        fr.seg(a, b, HAIR, G5)
    # hum: an ephemeris band under the wire, its width the hum level (collapsed at 0)
    if p["hum"] > 0:
        off = 6 + 24 * p["hum"]
        fr.ribbon([(x, y + off) for x, y in (cat(k / 30) for k in range(31))], HAIR, G4)
    return fr.svg(p, [G7, G6, G4, G1])


# ---- v4 · P2 diagram + trace, engineering schematic --------------------------------------------------------------------
def v4(p):
    fr = Frame()
    nrungs = 4 + round(8 * p["span"])            # wire modes in band: long spans pack them closer
    lock = lock_mode(p)
    y0, y1 = 44.0, 204.0
    busL, busR = 112.0, 214.0
    ys = [y0 + (y1 - y0) * (k + 0.5) / nrungs for k in range(nrungs)]
    # mode index of each rung, low at the bottom; the rung closest to the lock is lit
    sel = min(range(nrungs), key=lambda k: abs((nrungs - k) - lock * nrungs / 7.0))
    fr.seg((busL, y0), (busL, y1), LINE, G4)
    fr.seg((busR, y0), (busR, y1), LINE, G4)
    for k, y in enumerate(ys):
        lit = k == sel
        c = G6 if lit else G3
        wgt = LINE if lit else HAIR
        fr.seg((busL, y), (138, y), wgt, c)
        # inductor: three humps, as a closed ribbon
        coil = []
        for m in range(25):
            t = m / 24
            coil.append((138 + 30 * t, y - 4.5 * abs(math.sin(3 * math.pi * t))))
        fr.ribbon(coil, wgt, c)
        fr.seg((168, y), (186, y), wgt, c)
        # capacitor: two plates
        fr.poly([(186, y - 5), (188.5, y - 5), (188.5, y + 5), (186, y + 5)], c)
        fr.poly([(192, y - 5), (194.5, y - 5), (194.5, y + 5), (192, y + 5)], c)
        fr.seg((194.5, y), (busR, y), wgt, c)
    # shedding source: a box feeding a tap that slides along the bank (wind)
    fr.poly([(18, 104), (78, 104), (78, 130), (18, 130)], G0, G5, LINE)
    fr.text(26, 121, "st·v/d", G5)
    ty = ys[sel]
    fr.ribbon([(78, 117), (94, 117), (94, ty), (busL - 7, ty)], LINE, G6, bind=True)
    fr.poly([(busL - 8, ty - 4), (busL - 1, ty), (busL - 8, ty + 4)], G6, bind=True)
    fr.text(118, 38, "modes", G4)
    # sum node and output
    fr.seg((busR, 120), (250, 120), LINE, G4)
    fr.circle((258, 120), 8, G0, G5, LINE)
    fr.seg((254, 120), (262, 120), HAIR, G5)
    fr.seg((258, 116), (258, 124), HAIR, G5)
    # mains: a second input under the sum, its trace's amplitude the hum level (flat at 0)
    fr.seg((258, 128), (258, 186), LINE, G4)
    hum = []
    for m in range(61):
        t = m / 60
        hum.append((270 + 196 * t, 186 - 14 * p["hum"] * math.sin(2 * math.pi * 4 * t)))
    fr.seg((258, 186), (270, 186), LINE, G4)
    fr.ribbon(hum, LINE, G4, bind=True)
    fr.text(420, 206, "50 hz", G4)
    # output trace: the locked mode with its neighbours; gust shapes the envelope
    rng = random.Random(3)
    env_pts = [1.0 + p["gust"] * (rng.random() * 1.6 - 0.8) for _ in range(6)]
    tr = []
    for m in range(62):
        t = m / 61
        e = env_pts[int(t * 5)] * (1 - (t * 5 % 1)) + env_pts[min(5, int(t * 5) + 1)] * (t * 5 % 1)
        x = 270 + 196 * t
        tr.append((x, 120 - 30 * e * math.sin(2 * math.pi * (2.5 + 0.5 * lock) * t)
                   * (0.75 + 0.25 * math.sin(2 * math.pi * 1.3 * t))))
    fr.ribbon(tr, SUBJ, G7, bind=True)
    fr.seg((270, 120), (466, 120), HAIR, G1)
    fr.text(444, 80, "out", G4)
    return fr.svg(p, [G7, G6, G4, G3])


# ---- v5 · P14 loom, oscilloscope trace -----------------------------------------------------------------------------------
def v5(p):
    fr = Frame()
    gx0, gx1, gy0, gy1 = 40.0, 440.0, 30.0, 210.0
    # graticule: hairline divisions with minor ticks on the centre axes
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
    step = 6 + 16 * p["span"]                   # depth of the history: long spans ring longer
    n = max(1, round(lock_mode(p)))
    rng = random.Random(5)
    base = (60.0, 150.0)
    L = 300.0
    greys = [G7, G5, G4, G3]
    # warp threads: where the wire's nodes hold row after row
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
    # ch2: the mains, a small trace on the bottom division
    hum = []
    for m in range(61):
        t = m / 60
        hum.append((gx0 + 10 + (gx1 - gx0 - 20) * t, 196 - 10 * p["hum"] * math.sin(2 * math.pi * 8 * t)))
    fr.ribbon(hum, HAIR, G4, bind=True)
    fr.text(gx0 + 4, 192, "ch2", G4)
    fr.text(gx1 - 30, 42, "ch1", G4)
    return fr.svg(p, [G7, G5, G4, G1])


VARIANTS = {"v1": v1, "v2": v2, "v3": v3, "v4": v4, "v5": v5}

if __name__ == "__main__":
    for name, fn in VARIANTS.items():
        d = HERE / name
        d.mkdir(exist_ok=True)
        (d / "rest.svg").write_text(fn(dict(DEFAULTS)))
        print(d / "rest.svg")
