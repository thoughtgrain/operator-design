#!/usr/bin/env python3
"""Ants subject pass 01: one rest-frame sketch per direction (v1..v5).

Each sketch is the rest frame of its subject at the definition's defaults
(ants 4, scent 50, fade 30, scale pent), stock header kept, 480 x 220.
Sketches, not final frames: parts a control would move carry ants_node_i ids
so the budget can be estimated; everything else is static artwork.

All five share one model of the machine, so they draw the same colony:
a pentatonic lattice over two octaves, one reinforced phrase (TRAIL), two
older trails that are fading (GHOSTS), and four ants on the live trail.

    python3 screens/ants/passes/01-subject/sketch.py
"""
from __future__ import annotations

import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 480, 220

G0, G1, G2, G3, G4, G5, G6, BK = ("#CDCDCD", "#AFAFAF", "#969696", "#7D7D7D",
                                  "#646464", "#4B4B4B", "#323232", "#000000")
TITLES = ["ants", "scent", "fade", "scale"]
VALUES = ["4", "50", "30", "pent"]      # defaults 0.4286 (4 of 1..8), 0.5, 0.3, 0 (pent)
FONT = 'font-family="UniversNextPro-Light"'

# ---- the shared colony model -------------------------------------------
PENT = [0, 2, 4, 7, 9]                  # semitones of the pentatonic degrees
DEG = [o * 12 + s for o in range(2) for s in PENT] + [24]   # 11 lattice nodes, two octaves
NAMES = ["1", "2", "3", "5", "6"] * 2 + ["1"]
TRAIL = [0, 2, 3, 5, 4, 2, 1, 0]        # the reinforced phrase, as indices into DEG (a loop)
GHOSTS = [[5, 7, 8, 10, 8, 6], [3, 4, 6, 7, 5]]   # older trails, fading
N_ANTS = 4
SCENT = 0.5
FADE = 0.3


def f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


class Frame:
    def __init__(self, palette) -> None:
        self.out: list[str] = []
        self.node = 0
        self.palette = palette

    def nid(self) -> str:
        i = self.node
        self.node += 1
        return f' id="ants_node_{i}"'

    def path(self, pts, fill=BK, stroke="none", sw=0.0, bound=False):
        clean = []
        for x, y in pts:
            p = (round(x, 2), round(y, 2))
            if not clean or math.dist(p, clean[-1]) >= 0.2:
                clean.append(p)
        while len(clean) > 2 and math.dist(clean[0], clean[-1]) < 0.3:
            clean.pop()
        assert len(clean) <= 64, len(clean)
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in clean) + " Z"
        ident = self.nid() if bound else ""
        self.out.append(f'  <path{ident} d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{f(sw)}"/>')

    def circle(self, cx, cy, r, fill, stroke="none", sw=0.0, bound=False):
        ident = self.nid() if bound else ""
        self.out.append(f'  <circle{ident} cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}" '
                        f'stroke="{stroke}" stroke-width="{f(sw)}"/>')

    def rect(self, x, y, w, h, fill, stroke="none", sw=0.0):
        self.out.append(f'  <rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" fill="{fill}" '
                        f'stroke="{stroke}" stroke-width="{f(sw)}"/>')

    def line(self, pts, w, fill, bound=False):
        """A line as a thin closed ribbon (filled), split into runs of ≤ 30 points."""
        step = 29
        i = 0
        while i < len(pts) - 1:
            run = pts[i:i + step + 1]
            self.path(ribbon(run, w), fill=fill, bound=bound)
            i += step

    def dashed(self, pts, w, fill, on=4.0, off=4.0):
        for run in dashes(pts, on, off):
            if len(run) >= 2 and math.dist(run[0], run[-1]) > 1:
                self.path(ribbon(run, w), fill=fill)

    def text(self, x, y, s, fill=G3, size=10):
        self.out.append(f'  <text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{fill}" stroke="none" '
                        f'{FONT} font-size="{size}px">{s}</text>')

    def svg(self) -> str:
        head = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
                '  <g id="preview_canvas">',
                f'    <rect x="0" y="0" width="{W}" height="{H}" fill="#000000" stroke="none"/>',
                '  </g>', '  <g id="preview_header">']
        for k, c in enumerate([BK, G6, G5, G4, G3, G2, G1, G0]):
            head.append(f'    <rect x="{60 * k}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
        for k in range(4):
            ink = "#CBCBCB" if k < 2 else "#000000"
            head.append(f'    <text transform="matrix(1 0 0 1 {5 + 120 * k} 10)" fill="{ink}" stroke="none" '
                        f'{FONT} font-size="10px">{TITLES[k]}</text>')
        for k in range(4):
            ink = "#CBCBCB" if k < 2 else "#000000"
            head.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * k} 17.44)" fill="{ink}" stroke="none" '
                        f'{FONT} font-size="20px">{VALUES[k]}</text>')
        head.append('  </g>')
        pal = [f'  <path id="ants_palette_{i}" d="M {700 + 10 * i} 300 L {704 + 10 * i} 300 L {704 + 10 * i} 304 Z" '
               f'fill="{c}" stroke="{c}" stroke-width="2"/>' for i, c in enumerate(self.palette)]
        return "\n".join(head + pal + self.out + ["</svg>", ""])


def ribbon(pts, w):
    """Offset a polyline both ways by w/2 (mitred, clamped); flat ends, closed."""
    h = w / 2
    left, right = [], []
    n = len(pts)
    for i in range(n):
        if i == 0:
            dx, dy = pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]
        elif i == n - 1:
            dx, dy = pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]
        else:
            ax, ay = pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]
            bx, by = pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]
            la, lb = math.hypot(ax, ay) or 1, math.hypot(bx, by) or 1
            dx, dy = ax / la + bx / lb, ay / la + by / lb
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        k = h
        if 0 < i < n - 1:
            ax, ay = pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]
            la = math.hypot(ax, ay) or 1
            cos = abs((-ay / la) * nx + (ax / la) * ny)
            k = h / max(cos, 0.5)
        left.append((pts[i][0] + nx * k, pts[i][1] + ny * k))
        right.append((pts[i][0] - nx * k, pts[i][1] - ny * k))
    return left + right[::-1]


def dashes(pts, on, off):
    """Split a polyline into dash runs by arc length."""
    out, cur, s, drawing = [], [pts[0]], 0.0, True
    lim = on
    for a, b in zip(pts, pts[1:]):
        seg = math.dist(a, b)
        t0 = 0.0
        while s + (seg - t0) >= lim:
            t = t0 + (lim - s)
            p = (a[0] + (b[0] - a[0]) * t / seg, a[1] + (b[1] - a[1]) * t / seg)
            if drawing:
                cur.append(p)
                out.append(cur)
            cur = [p]
            drawing = not drawing
            t0, s = t, 0.0
            lim = on if drawing else off
        s += seg - t0
        if drawing:
            cur.append(b)
    if drawing and len(cur) > 1:
        out.append(cur)
    return out


def ellipse(cx, cy, rx, ry, n=24, rot=0.0):
    c, s = math.cos(rot), math.sin(rot)
    return [(cx + rx * math.cos(2 * math.pi * k / n) * c - ry * math.sin(2 * math.pi * k / n) * s,
             cy + rx * math.cos(2 * math.pi * k / n) * s + ry * math.sin(2 * math.pi * k / n) * c)
            for k in range(n)]


def body(F, x, y, ang, fill, bound=True, L=8.0, Wd=3.8):
    """An ant, drawn as the language's plain mark: a short solid capsule along its heading."""
    c, s = math.cos(ang), math.sin(ang)
    pts = []
    for k in range(16):
        t = 2 * math.pi * k / 16
        ex, ey = (L / 2) * math.cos(t), (Wd / 2) * math.sin(t)
        pts.append((x + ex * c - ey * s, y + ex * s + ey * c))
    F.path(pts, fill=fill, bound=bound)




def catmull(ctrl, per=8, closed=True):
    out = []
    m = len(ctrl)
    rng = range(m) if closed else range(m - 1)
    for i in rng:
        p0 = ctrl[i - 1] if (closed or i > 0) else ctrl[0]
        p1, p2 = ctrl[i], ctrl[(i + 1) % m]
        p3 = ctrl[(i + 2) % m] if (closed or i + 2 < m) else ctrl[-1]
        for k in range(per):
            t = k / per
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(2)))
    out.append(out[0] if closed else ctrl[-1])
    return out


def heading(pts, j):
    a, b = pts[max(0, j - 1)], pts[min(len(pts) - 1, j + 1)]
    return math.atan2(b[1] - a[1], b[0] - a[0])


# ======================================================================== v1
def v1() -> Frame:
    """P12 Orrery, typeset diagram: degrees as planets on octave orbits round the nest."""
    F = Frame([G0, G1, G2, G3, G4, G5, BK])
    cx, cy, s = 240, 118, 54.0
    e = math.radians(26)
    radii = [1.5, 2.55]
    Rs = 0.7

    def P(r, th):
        return (cx + s * r * math.cos(th), cy + s * r * math.sin(th) * math.sin(e))

    def ang(semi):
        return math.pi / 2 - 2 * math.pi * (semi % 12) / 12

    nodes = [(DEG[i] // 12, ang(DEG[i])) for i in range(10)]   # two octaves, one orbit each

    def link(i, j):
        (oi, ai), (oj, aj) = nodes[i], nodes[j]
        d = (aj - ai + math.pi) % (2 * math.pi) - math.pi
        n = max(4, int(abs(d) * 12) + 2)
        pts = [(radii[oi] + (radii[oj] - radii[oi]) * k / (n - 1), ai + d * k / (n - 1)) for k in range(n)]
        return pts

    def near(th):
        return math.sin(th) >= 0

    layers = {False: [], True: []}
    for r in radii:
        layers[False].append(("line", [P(r, math.pi + math.pi * k / 40) for k in range(41)], 1.0, G5, False))
        layers[True].append(("line", [P(r, math.pi * k / 40) for k in range(41)], 1.0, G4, False))
    for semi in PENT:                                  # spokes: the lattice's pitch classes
        a = ang(semi)
        layers[near(a)].append(("line", [P(1.05, a), P(2.85, a)], 1.0, G4 if near(a) else G5, False))
    for g, shade in zip(GHOSTS, (G3, G4)):             # older trails, fading
        for a, b in zip(g, g[1:]):
            if a < 10 and b < 10:
                pr = link(a, b)
                mid = pr[len(pr) // 2][1]
                layers[near(mid)].append(("line", [P(r, t) for r, t in pr], 1.5, shade, False))
    trail = []
    for a, b in zip(TRAIL, TRAIL[1:]):                 # the reinforced trail
        pr = link(a, b)
        pts = [P(r, t) for r, t in pr]
        trail.append(pts)
        layers[near(pr[len(pr) // 2][1])].append(("line", pts, 2.4, G0, True))
    on = set(TRAIL)
    for i, (o, a) in enumerate(nodes):
        x, y = P(radii[o], a)
        layers[near(a)].append(("planet", x, y, i in on))

    def draw(item):
        if item[0] == "line":
            F.line(item[1], item[2], item[3], bound=item[4])
        else:
            _, x, y, lit = item
            if lit:
                F.circle(x, y, 4.2, G2, BK, 1.2, bound=True)
            else:
                F.circle(x, y, 3.8, BK, G3, 1.5, bound=True)

    for it in layers[False]:
        draw(it)
    # the nest: a dark sphere seated in the plane, a line rim, its entrance on top
    F.path(ellipse(cx, cy, s * Rs, s * Rs, 48), fill=BK, stroke=G3, sw=1.5, bound=True)
    F.line([(cx + s * Rs * math.cos(math.pi * k / 24), cy + s * Rs * math.sin(math.pi * k / 24) * math.sin(e))
            for k in range(25)], 1.0, G4)
    F.path(ellipse(cx, cy - s * Rs * 0.7, 6, 2.4, 16), fill=BK, stroke=G3, sw=1.5)
    for it in layers[True]:
        draw(it)
    for k in range(N_ANTS):
        seg = trail[2 * k]
        m = len(seg) // 2
        body(F, seg[m][0], seg[m][1], heading(seg, m), G1)
    for semi, nm in zip(PENT, ["1", "2", "3", "5", "6"]):
        x, y = P(2.98, ang(semi))
        F.text(x - 3, y + 4, nm, G3)
    F.text(cx - 11, cy - s * Rs - 6, "nest", G3)
    F.text(8, 208, "fig. 1  two octaves", G3)
    return F


# ======================================================================== v2
def v2() -> Frame:
    """P13 Capture, orthographic elevation: trails build mounds; fade is the waterline."""
    F = Frame([G0, G1, G3, G4, G5, G6, BK])
    x0, x1 = 40, 440
    ground = 184
    n = len(DEG)
    xs = [x0 + (x1 - x0) * i / (n - 1) for i in range(n)]
    use = [0.0] * n
    for i in TRAIL[:-1]:
        use[i] += 1.0
    for g, wgt in zip(GHOSTS, (0.45, 0.25)):
        for i in g:
            use[i] += wgt
    hmax = 104 * (0.5 + SCENT)
    top = max(use)
    heights = [hmax * u / top for u in use]

    def bump(u):
        u = abs(u)
        if u < 0.3:
            return 1.0
        if u > 1:
            return 0.0
        return 0.5 + 0.5 * math.cos(math.pi * (u - 0.3) / 0.7)

    def prof(x):
        return max(h * bump((x - xi) / 17.0) for xi, h in zip(xs, heights))

    N = 116
    pts = [(x0 - 20 + (x1 - x0 + 40) * k / (N - 1),) for k in range(N)]
    pts = [(x, ground - prof(x)) for (x,) in pts]
    water = ground - 0.30 * 104 - 4
    F.rect(x0 - 24, water, x1 - x0 + 48, ground - water, G6)
    runs, cur, dry = [], [pts[0]], pts[0][1] < water
    for p in pts[1:]:
        d = p[1] < water
        if d != dry:
            runs.append((dry, cur + [p]))
            cur, dry = [p], d
        else:
            cur.append(p)
    runs.append((dry, cur))
    for dry_, run in runs:
        if len(run) >= 2:
            F.line(run, 2.2 if dry_ else 1.5, G0 if dry_ else G4, bound=dry_)
    F.dashed([(x0 - 24, water), (x1 + 24, water)], 1.2, G3, 6, 4)
    # ground line and earth below it, elevation convention: 45° ticks, 6 px apart
    F.line([(x0 - 24, ground), (x1 + 24, ground)], 1.2, G3)
    x = x0 - 20
    while x < x1 + 20:
        F.line([(x, ground + 8), (x + 6, ground + 2)], 1.0, G5)
        x += 7
    for i, xx in enumerate(xs):
        F.text(xx - 3, ground + 22, NAMES[i], G3)
    order = sorted(range(n), key=lambda i: -heights[i])[:N_ANTS]
    for k, i in enumerate(sorted(order)):
        y = ground - heights[i] - 3.2
        body(F, xs[i] + (-3 if k % 2 else 3), y, 0.0, G1)
    yt = ground - max(heights)
    F.line([(18, yt), (18, ground)], 1.2, G4)
    F.line([(14, yt), (22, yt)], 1.2, G4)
    F.line([(14, ground), (22, ground)], 1.2, G4)
    F.text(x1 + 6, water - 4, "fade", G3)
    F.text(x1 - 36, 42, "elev. a", G3)
    return F


# ======================================================================== v3
def v3() -> Frame:
    """P14 Loom, survey plan: each pass a contour across eight step threads."""
    F = Frame([G0, G1, G2, G3, G4, G5, BK])
    xl, xr = 92, 436
    steps = 8
    xs = [xl + (xr - xl) * k / (steps - 1) for k in range(steps)]
    rows, yfront, pitch, band = 5, 186, 30, 22
    lev = band / (len(DEG) - 1)
    ytop = yfront - pitch * (rows - 1) - band - 6
    for k, x in enumerate(xs):                                 # step threads (warp)
        F.line([(x, ytop), (x, yfront + 6)], 1.0, G5)
        F.text(x - 3, ytop - 6, str(k + 1), G3)
    # degree ruler at the left margin: one tick per lattice degree (scale sets the count)
    for i in range(len(DEG)):
        y = yfront - i * lev
        w = 6 if NAMES[i] == "1" else 3
        F.line([(64 - w, y), (64, y)], 1.0, G4)
    F.line([(64, yfront + 1), (64, yfront - band - 1)], 1.0, G4)
    rnd = random.Random(11)
    phrase0 = TRAIL[:steps]
    for r in range(rows - 1, -1, -1):                          # oldest first
        y = yfront - pitch * r
        ph = list(phrase0)
        for k in range(len(ph)):
            if rnd.random() < (1 - SCENT) * 0.22 * r:
                ph[k] = max(0, min(len(DEG) - 1, ph[k] + rnd.choice((-2, -1, 1, 2))))
        st = [(xs[k], y - lev * d) for k, d in enumerate(ph)]
        shade = [G0, G2, G3, G4, G5][r]
        wgt = 2.2 if r == 0 else (1.5 if r == 1 else 1.2)
        F.line(st, wgt, shade, bound=True)
        if r == 0:
            for sx, sy in st:
                F.rect(sx - 2.5, sy - 2.5, 5, 5, BK, G2, 1.5)
        F.text(14, y + 4 - band / 2, "now" if r == 0 else f"−{r}", G3)
    st0 = [(xs[k], yfront - lev * d) for k, d in enumerate(phrase0)]
    for k in range(N_ANTS):
        a, b = st0[2 * k], st0[2 * k + 1]
        body(F, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, math.atan2(b[1] - a[1], b[0] - a[0]), G1)
    F.text(xr - 52, 212, "plan, 5 passes", G3)
    return F


# ======================================================================== v4
def v4() -> Frame:
    """P5 Field and figure, patent section: the trail loop over a lattice of degrees, the field cut at the front."""
    F = Frame([G0, G1, G2, G3, G4, G5, G6, BK])
    cols, rws = 10, 5

    def P(i, j):                       # i: step neighbours, j: third neighbours (skewed, Tonnetz-like)
        X = (i - (cols - 1) / 2) + 0.5 * j - 1.0
        zz = 1 + 0.42 * j
        return (240 + 42 * X / zz, 52 + 128 / zz)

    for j in range(rws):
        F.line([P(0, j), P(cols - 1, j)], 1.0, G5 if j else G4)
    for i in range(cols):
        F.line([P(i, 0), P(i, rws - 1)], 1.0, G5)
    for i in range(1, cols):
        jj = min(rws - 1, i)
        F.line([P(i, 0), P(i - jj, jj)], 1.0, G6 if False else G5)
    # section: the field cut along its front edge, soil hatched at 45°, 6 px apart
    (xa, yf), (xb, _) = P(0, 0), P(cols - 1, 0)
    dpt = 11
    F.line([(xa, yf + dpt), (xb, yf + dpt)], 1.2, G4)
    F.line([(xa, yf), (xa, yf + dpt)], 1.2, G4)
    F.line([(xb, yf), (xb, yf + dpt)], 1.2, G4)
    x = xa + 4
    while x < xb + dpt - 2:
        a = (max(xa + 2, x - dpt + 2), 0)
        a = (a[0], yf + dpt - 1 - (a[0] - (x - dpt + 2)))
        b = (min(x, xb - 2), 0)
        b = (b[0], yf + 1 + (x - b[0]))
        if b[0] - a[0] > 2:
            F.line([a, b], 1.0, G5)
        x += 6
    ghosts = [([(6, 1), (7, 2), (6, 3), (5, 2)], G3), ([(1, 3), (2, 4), (0, 4)], G4)]
    for ctrl, shade in ghosts:
        F.dashed(catmull([P(i, j) for i, j in ctrl]), 1.5, shade, 5, 4)
    loop = [(2, 0), (4, 0), (5, 1), (4, 3), (2, 3), (1, 2), (1, 1)]
    curve = catmull([P(i, j) for i, j in loop], per=8)
    F.line(curve[:29], 2.4, G0, bound=True)
    F.line(curve[28:], 2.4, G0, bound=True)
    for i, j in loop:
        x_, y_ = P(i, j)
        F.circle(x_, y_, 3.2, BK, G2, 1.5)
    for k in range(N_ANTS):
        jx = 4 + k * (len(curve) // N_ANTS)
        body(F, curve[jx][0], curve[jx][1], heading(curve, jx), G1)

    def label(num, px, py, tx, ty):
        F.line([(px, py), (tx, ty)], 1.0, G4)
        F.text(tx + (3 if tx >= px else -14), ty + 4, num, G3)

    p = curve[30]
    label("10", p[0], p[1], p[0] - 30, 44)
    p = P(8, 3)
    label("12", p[0], p[1], p[0] + 26, 52)
    jx = 4 + 1 * (len(curve) // N_ANTS)
    label("14", curve[jx][0], curve[jx][1], curve[jx][0] + 40, curve[jx][1] - 30)
    label("16", xb - 6, yf + 6, xb + 16, yf + 6)
    F.text(8, 44, "FIG. 2", G3)
    for k in range(8):
        sx = 172 + 18 * k
        lit = k < 5
        F.rect(sx, 200 if lit else 201, 10, 6 if lit else 4, G2 if lit else BK, G4, 1.5)
    return F


# ======================================================================== v5
def v5() -> Frame:
    """P11 Instrument stack (stretch), hidden-line isometric: a formicarium, one chamber per degree."""
    F = Frame([G0, G1, G2, G3, G4, BK])
    c30, s30 = math.cos(math.radians(30)), math.sin(math.radians(30))
    ox, oy = 168, 120

    def P(x, y, z):
        return (ox + (x - y) * c30, oy + (x + y) * s30 - z)

    L, D, Hh = 184, 14, 88
    # stand: a low plinth under the slab, hidden-line
    pl = 6
    F.path([P(-6, 6, 0), P(L + 6, 6, 0), P(L + 6, -D - 6, 0), P(-6, -D - 6, 0)], fill=BK, stroke=G4, sw=1.5)
    F.path([P(-6, 6, 0), P(L + 6, 6, 0), P(L + 6, 6, -pl), P(-6, 6, -pl)], fill=BK, stroke=G4, sw=1.5)
    F.path([P(L + 6, 6, 0), P(L + 6, -D - 6, 0), P(L + 6, -D - 6, -pl), P(L + 6, 6, -pl)], fill=BK, stroke=G4, sw=1.5)
    F.path([P(L, 0, 0), P(L, -D, 0), P(L, -D, Hh), P(L, 0, Hh)], fill=BK, stroke=G4, sw=1.5)
    F.path([P(0, 0, Hh), P(L, 0, Hh), P(L, -D, Hh), P(0, -D, Hh)], fill=BK, stroke=G4, sw=1.5)
    F.path([P(0, 0, 0), P(L, 0, 0), P(L, 0, Hh), P(0, 0, Hh)], fill=BK, stroke=G3, sw=1.5)
    soil = Hh - 12
    F.line([P(2 + (L - 4) * k / 30, 0, soil + 1.8 * math.sin(k * 1.1)) for k in range(31)], 1.2, G4)
    tiers = [14, 40]
    chambers = []
    for semi in DEG:
        o = semi // 12
        if o < 2:
            k = PENT.index(semi % 12)
            chambers.append((22 + k * 35, tiers[o] + 4 * (k % 2)))
        else:
            chambers.append((22 + 2 * 35, 62))

    def tunnel(i, j, w, shade, bound=False, dash=False):
        (xa, za), (xb, zb) = chambers[i], chambers[j]
        mx, mz = (xa + xb) / 2, (za + zb) / 2 + (5 if za == zb else 0)
        pts = []
        for k in range(12):
            t = k / 11
            pts.append(P((1 - t) ** 2 * xa + 2 * (1 - t) * t * mx + t * t * xb, 0,
                         (1 - t) ** 2 * za + 2 * (1 - t) * t * mz + t * t * zb))
        if dash:
            F.dashed(pts, w, shade, 4, 4)
        else:
            F.line(pts, w, shade, bound=bound)
        return pts

    top = chambers[10]
    F.line([P(top[0] + 3, 0, soil), P(top[0] + 1, 0, top[1] + 5)], 1.5, G3)
    for g, shade in zip(GHOSTS, (G3, G4)):
        for a, b in zip(g, g[1:]):
            tunnel(a, b, 1.5, shade, dash=True)
    tp = [tunnel(a, b, 2.4, G0, bound=True) for a, b in zip(TRAIL, TRAIL[1:])]
    on = set(TRAIL)
    for i, (x, z) in enumerate(chambers):
        ring = [P(x + 10 * math.cos(2 * math.pi * t / 20), 0, z + 5.5 * math.sin(2 * math.pi * t / 20)) for t in range(20)]
        F.path(ring, fill=BK, stroke=G2 if i in on else G4, sw=1.5, bound=True)
    for k in range(N_ANTS):
        seg = tp[(2 * k + 1) % len(tp)]
        m = len(seg) // 2
        body(F, seg[m][0], seg[m][1], heading(seg, m), G1)
    for name, z in (("oct 1", tiers[0]), ("oct 2", tiers[1]), ("oct 3", 62)):
        x, y = P(0, 0, z)
        F.text(x - 34, y + 4, name, G3)
    return F


def main() -> None:
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        d = HERE / name
        d.mkdir(exist_ok=True)
        fr = fn()
        (d / "rest.svg").write_text(fr.svg())
        print(name, "bound nodes", fr.node)


if __name__ == "__main__":
    main()
