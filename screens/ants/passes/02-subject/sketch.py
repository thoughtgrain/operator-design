#!/usr/bin/env python3
"""Ants subject pass 02: one rest-frame sketch per direction (v1..v5).

Each sketch is the rest frame of its subject at the definition's defaults
(ants 4, scent 50, fade 30, scale pent), stock header kept, 480 x 220.
No text below the header; states are line weight, brightness, movement or
hatching, never a lighter grey fill. 3D subjects (v5) are modelled and
projected through one camera.

All five draw the same colony state: a pentatonic lattice over two octaves
(11 degrees), one reinforced phrase (TRAIL), two fading older trails
(GHOSTS) and four ants.

    python3 screens/ants/passes/02-subject/sketch.py
"""
from __future__ import annotations

import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 480, 220
TOP = 22.0                      # artwork stays below the stock header

G0, G1, G2, G3, G4, G5, G6, BK = ("#CDCDCD", "#AFAFAF", "#969696", "#7D7D7D",
                                  "#646464", "#4B4B4B", "#323232", "#000000")
HAIR, LINE, SUBJ = 1.0, 1.5, 2.25
TITLES = ["ants", "scent", "fade", "scale"]
VALUES = ["4", "50", "30", "pent"]
FONT = 'font-family="UniversNextPro-Light"'

# ---- the shared colony model -------------------------------------------
PENT = [0, 2, 4, 7, 9]
N_DEG = 11                                  # two pentatonic octaves + the top root
TRAIL = [0, 2, 3, 5, 4, 2, 1, 0]           # the reinforced phrase (a loop)
GHOSTS = [[5, 7, 8, 10, 8, 6], [3, 4, 6, 7, 5]]
N_ANTS, SCENT, FADE = 4, 0.5, 0.3


def f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# ---- geometry helpers ----------------------------------------------------
def clip_poly(poly, x0=-40.0, y0=TOP, x1=520.0, y1=219.5):
    """Sutherland-Hodgman against a rectangle."""
    def clip(pts, inside, inter):
        out = []
        for i in range(len(pts)):
            a, b = pts[i - 1], pts[i]
            ia, ib = inside(a), inside(b)
            if ib:
                if not ia:
                    out.append(inter(a, b))
                out.append(b)
            elif ia:
                out.append(inter(a, b))
        return out

    def ix(xv):
        return lambda a, b: (xv, a[1] + (b[1] - a[1]) * (xv - a[0]) / (b[0] - a[0]))

    def iy(yv):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (yv - a[1]) / (b[1] - a[1]), yv)

    p = list(poly)
    for inside, inter in ((lambda q: q[0] >= x0, ix(x0)), (lambda q: q[0] <= x1, ix(x1)),
                          (lambda q: q[1] >= y0, iy(y0)), (lambda q: q[1] <= y1, iy(y1))):
        if not p:
            return p
        p = clip(p, inside, inter)
    return p


def densify(pts, step=2.0):
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        n = max(1, int(math.dist(a, b) / step))
        out += [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(1, n + 1)]
    return out


def clip_line(pts, x0=-40.0, y0=TOP + 1, x1=520.0, y1=219.0):
    runs, cur = [], []
    for p in densify(pts, 1.5):
        if x0 <= p[0] <= x1 and y0 <= p[1] <= y1:
            cur.append(p)
        else:
            if len(cur) > 1:
                runs.append(cur)
            cur = []
    if len(cur) > 1:
        runs.append(cur)
    return [simplify(r) for r in runs]


def simplify(pts, tol=0.25):
    """Drop nearly collinear points (keeps ribbons under 64 points)."""
    if len(pts) < 3:
        return pts
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, b, c = out[-1], pts[i], pts[i + 1]
        cross = abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
        if cross / (math.dist(a, c) or 1) > tol or math.dist(a, b) > 14:
            out.append(b)
    out.append(pts[-1])
    return out


def ribbon(pts, w):
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
    pts = densify(pts, 1.0)
    out, cur, s, drawing = [], [pts[0]], 0.0, True
    for a, b in zip(pts, pts[1:]):
        s += math.dist(a, b)
        if drawing:
            cur.append(b)
        if s >= (on if drawing else off):
            if drawing and len(cur) > 1:
                out.append(cur)
            drawing, s, cur = not drawing, 0.0, [b]
    if drawing and len(cur) > 1:
        out.append(cur)
    return out


def ellipse(cx, cy, rx, ry, n=28, rot=0.0, a0=0.0, a1=2 * math.pi, closed=True):
    c, s = math.cos(rot), math.sin(rot)
    m = n if closed else n + 1
    pts = []
    for k in range(m):
        t = a0 + (a1 - a0) * k / n
        ex, ey = rx * math.cos(t), ry * math.sin(t)
        pts.append((cx + ex * c - ey * s, cy + ex * s + ey * c))
    return pts


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


def hull(pts):
    pts = sorted(set((round(x, 2), round(y, 2)) for x, y in pts))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]


def point_along(pts, frac):
    seg = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
    tot = sum(seg)
    s = frac * tot
    for (a, b), L in zip(zip(pts, pts[1:]), seg):
        if s <= L:
            t = s / (L or 1)
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), math.atan2(b[1] - a[1], b[0] - a[0])
        s -= L
    return pts[-1], math.atan2(pts[-1][1] - pts[-2][1], pts[-1][0] - pts[-2][0])


# ---- frame writer ----------------------------------------------------------
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
        if len(clean) < 3:
            return
        while len(clean) > 64:
            clean = clean[::2]
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in clean) + " Z"
        ident = self.nid() if bound else ""
        self.out.append(f'  <path{ident} d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{f(sw)}"/>')

    def shape(self, pts, stroke, sw, fill=BK, bound=False):
        """A closed outline: black body, edge in one of the three weights."""
        p = clip_poly(pts)
        if len(p) >= 3:
            self.path(p, fill=fill, stroke=stroke, sw=sw, bound=bound)

    def line(self, pts, w, fill, bound=False):
        for run in clip_line(pts):
            i = 0
            while i < len(run) - 1:
                seg = run[i:i + 30]
                if len(seg) >= 2 and sum(math.dist(a, b) for a, b in zip(seg, seg[1:])) > 0.8:
                    self.path(ribbon(seg, w), fill=fill, bound=bound)
                i += 29

    def dashed(self, pts, w, fill, on=4.0, off=4.0):
        for run in dashes(pts, on, off):
            if math.dist(run[0], run[-1]) > 2:
                self.line(simplify(run), w, fill)

    def hatch(self, poly, fill=G4, gap=4.0, w=HAIR, inset=0.8, holes=()):
        """45° hairlines (up to the right), gap px apart, clipped to poly minus holes."""
        poly = clip_poly(poly)
        if len(poly) < 3:
            return
        step = gap * math.sqrt(2)
        cs = [x + y for x, y in poly]
        c = min(cs) + step / 2
        while c < max(cs):
            segs = self._cuts(poly, c)
            for x1, x2 in segs:
                for hole in holes:
                    pass
                cut = [(x1, x2)]
                for hole in holes:
                    nxt = []
                    hs = self._cuts(hole, c)
                    for a, b in cut:
                        pieces = [(a, b)]
                        for h1, h2 in hs:
                            new = []
                            for p, q in pieces:
                                if h2 <= p or h1 >= q:
                                    new.append((p, q))
                                else:
                                    if h1 > p:
                                        new.append((p, h1 - 1))
                                    if h2 < q:
                                        new.append((h2 + 1, q))
                            pieces = new
                        nxt += pieces
                    cut = nxt
                for a, b in cut:
                    a, b = a + inset * 0.7, b - inset * 0.7
                    if b - a > 1.6:
                        self.path(ribbon([(a, c - a), (b, c - b)], w), fill=fill)
            c += step

    @staticmethod
    def _cuts(poly, c):
        xs = []
        n = len(poly)
        for i in range(n):
            (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
            sa, sb = ax + ay - c, bx + by - c
            if (sa < 0) != (sb < 0):
                t = sa / (sa - sb)
                xs.append(ax + (bx - ax) * t)
        xs.sort()
        return [(xs[i], xs[i + 1]) for i in range(0, len(xs) - 1, 2)]

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


# ---- a plan-view ant in line (v1, v3, v4) ----------------------------------
def ant_plan(F, x, y, ang, L, edge, sw=HAIR, legs=None, bound=True, legw=HAIR):
    """Seen from above: gaster, petiole, mesosoma, head, six legs, two antennae."""
    c, s = math.cos(ang), math.sin(ang)

    def P(u, v):
        return (x + u * L * c - v * L * s, y + u * L * s + v * L * c)

    legs = legs or edge
    for side in (-1, 1):                       # legs and antennae under the body
        for root, knee, foot in (((0.10, 0.04), (0.22, 0.20), (0.40, 0.30)),
                                 ((0.04, 0.05), (0.06, 0.24), (0.02, 0.40)),
                                 ((-0.02, 0.05), (-0.12, 0.22), (-0.34, 0.34))):
            F.line([P(root[0], side * root[1]), P(knee[0], side * knee[1]), P(foot[0], side * foot[1])],
                   legw, legs)
        F.line([P(0.42, side * 0.03), P(0.50, side * 0.12), P(0.66, side * 0.16)], legw, legs)
    parts = [(-0.26, 0, 0.21, 0.135), (-0.05, 0, 0.035, 0.035), (0.08, 0, 0.12, 0.06), (0.33, 0, 0.1, 0.085)]
    for u, v, ru, rv in parts:
        pts = [P(u + ru * math.cos(t), v + rv * math.sin(t)) for t in [2 * math.pi * k / 20 for k in range(20)]]
        F.shape(pts, edge, sw, bound=bound)


def ant_side(F, x, y, L, edge, sw=HAIR, legs=None, facing=1):
    """A small ant seen from the side, feet on y, walking towards +x (facing)."""
    def P(u, v):
        return (x + facing * u * L, y - v * L)
    legs = legs or edge
    for root, knee, foot in (((0.12, 0.2), (0.24, 0.3), (0.34, 0.0)), ((0.06, 0.2), (0.06, 0.32), (0.02, 0.0)),
                             ((0.0, 0.2), (-0.14, 0.3), (-0.3, 0.0))):
        F.line([P(*root), P(*knee), P(*foot)], HAIR, legs)
    for u, v, ru, rv in [(-0.25, 0.3, 0.2, 0.14), (-0.04, 0.27, 0.035, 0.06), (0.09, 0.27, 0.12, 0.07),
                         (0.32, 0.32, 0.09, 0.09)]:
        F.shape([P(u + ru * math.cos(t), v + rv * math.sin(t)) for t in [2 * math.pi * k / 18 for k in range(18)]],
                edge, sw, bound=True)
    F.line([P(0.38, 0.38), P(0.44, 0.56), P(0.58, 0.5)], HAIR, legs)


# ======================================================================== v1
def v1() -> Frame:
    """Pegs and thread, single-weight contour: every crossing winds a strand between two pegs;
    strands that aren't walked again slip off and hang."""
    F = Frame([G0, G2, G3, G4, BK])
    WT = LINE                                   # the one weight
    n = N_DEG
    x0, dx = 62.0, 35.6
    px = [x0 + i * dx for i in range(n)]
    top, plank = 88.0, 168.0
    # plank: a long board in elevation, its front edge and top face
    F.shape([(30, plank), (450, plank), (450, plank + 12), (30, plank + 12)], G4, WT)
    F.line([(34, plank + 4), (446, plank + 4)], WT, G4)
    # pegs: shafts and turned heads
    for x in px:
        F.shape([(x - 3.2, top + 4), (x + 3.2, top + 4), (x + 3.2, plank), (x - 3.2, plank)], G4, WT)
        F.shape(ellipse(x, top, 6.5, 5.5, 20), G3, WT)

    def drape(a, b, sag_k=0.30, lift=0.0):
        xa, xb = px[a], px[b]
        L = abs(xb - xa)
        sag = sag_k * L ** 0.92
        pts = []
        for k in range(25):
            t = k / 24
            xx = xa + (xb - xa) * t
            yy = top + 3 + lift + sag * (4 * t * (1 - t)) ** 0.95
            pts.append((xx, yy))
        return pts

    # fallen strands (fade): old threads slipped off one peg and hanging past the board
    hang = [(7, 1.0, 46.0), (9, -1.0, 58.0)]
    for peg, side, depth in hang[: 2 if FADE < 0.5 else 1]:
        x = px[peg]
        pts = [(x + side * 3, top + 4)]
        for k in range(1, 22):
            t = k / 21
            pts.append((x + side * (3 + 14 * math.sin(t * 1.6)), top + 4 + t * (plank + 30 - top)))
        F.line(pts, WT, G4)
    # live strands: each walked edge carries a bundle (scent: strands per edge)
    edges = {}
    for a, b in zip(TRAIL, TRAIL[1:]):
        key = (min(a, b), max(a, b))
        edges[key] = edges.get(key, 0) + 1
    order = sorted(edges, key=lambda e: e[1] - e[0], reverse=True)
    for (a, b) in order:
        strands = 1 + int(SCENT * 2.0 + 0.2 * edges[(a, b)])
        for k in range(strands):
            F.line(drape(a, b, lift=k * 3.2), WT, G0, bound=(k == 0))
    # one stray single strand from the wandering part of the walk
    F.line(drape(5, 6, sag_k=0.42), WT, G3)
    # ants: contour ants walking the strands
    spots = [((0, 2), 0.42), ((3, 5), 0.6), ((2, 3), 0.5), ((1, 2), 0.35)]
    for (a, b), t in spots[:N_ANTS]:
        pts = drape(a, b, lift=0)
        (x, y), ang = point_along(pts, t)
        nx, ny = math.sin(ang), -math.cos(ang)
        ant_plan(F, x + nx * 0.5, y - 6, ang, 18, G2, WT, legs=G3)
    return F


# ======================================================================== v2
def v2() -> Frame:
    """Cutaway of one ant at work, hatched mass: the gaster cut open shows the gland
    and its duct laying the trail; the antennae read it."""
    F = Frame([G0, G2, G3, G4, G5, BK])
    gy = 176.0                                     # ground
    # ground and the degree slabs under it (scale: slab count)
    F.line([(8, gy), (472, gy)], HAIR, G4)
    n = N_DEG
    sw_ = (472 - 8) / n
    for i in range(n):
        x = 8 + i * sw_
        F.shape([(x + 2, gy + 4), (x + sw_ - 2, gy + 4), (x + sw_ - 2, gy + 16), (x + 2, gy + 16)], G5, HAIR)
    # body parts, side view, walking right
    gx, gyc, grx, gry, grot = 196.0, 124.0, 58.0, 38.0, -0.22
    gaster = ellipse(gx, gyc, grx, gry, 48, grot)
    inner = ellipse(gx, gyc, grx - 9, gry - 9, 40, grot)
    meso = [(262, 112), (276, 98), (300, 92), (326, 94), (342, 100), (346, 112), (334, 124),
            (306, 128), (280, 128), (266, 122)]
    meso = catmull(meso, 3)[:-1]
    head = ellipse(378, 100, 30, 25, 32, 0.25)
    petiole = [(248, 126), (252, 108), (258, 104), (264, 110), (262, 128), (254, 132)]
    # far legs first (hairline, dim)
    far = [[(300, 124), (318, 146), (348, gy)], [(292, 126), (286, 150), (276, gy)],
           [(282, 126), (256, 146), (238, gy)]]
    for leg in far:
        F.line(leg, HAIR, G5)
    # trail: from the sting tip down to the ground and back along it; fade sets where it dies
    tipa = grot + math.pi
    tip = (gx + (grx + 2) * math.cos(tipa), gyc + (grx + 2) * math.sin(tipa))
    fresh_end = 92.0
    dead_end = 8 + FADE * 60
    trail = [tip, (tip[0] - 4, gy - 4), (tip[0] - 12, gy - 1.2)] + [(x, gy - 1.2) for x in range(int(tip[0]) - 20, int(fresh_end), -10)] + [(fresh_end, gy - 1.2)]
    F.line(trail, SUBJ, G0, bound=True)
    # evaporating stretch: hatched band, there but fading
    F.hatch([(dead_end, gy - 7), (fresh_end, gy - 7), (fresh_end, gy - 0.5), (dead_end, gy - 0.5)], G4, gap=4)
    # followers: small ants walking the trail (ants: count)
    for k in range(N_ANTS - 1):
        ant_side(F, 116 - k * 26 + 46, gy - 1.5, 20, G3, HAIR, legs=G4)
    # hatched masses: head and mesosoma
    for part in (head, meso, petiole):
        F.shape(part, G3, LINE)
        F.hatch(part, G5, gap=4.5, inset=1.5)
    # gaster cut open: wall hatched (cut material), interior black with the gland
    F.shape(gaster, G3, LINE)
    F.hatch(gaster, G4, gap=3.2, holes=[inner], inset=1.2)
    F.shape(inner, G4, HAIR)
    for k in (1, 2, 3):                                     # segment plates on the cut wall
        a = grot + math.pi / 2 - 0.15 + 0.0
        u = -0.55 + 0.42 * k
        px_, py_ = gx + grx * u * math.cos(grot), gyc + grx * u * math.sin(grot)
    gland = ellipse(gx - 6, gyc + 4, 26, 15, 30, grot + 0.1)
    F.shape(gland, G2, LINE)
    F.hatch(ellipse(gx - 6, gyc + 4, 22, 11, 30, grot + 0.1), G3, gap=3.2, inset=1)
    duct = [(gx - 30, gyc + 10), (gx - 42, gyc + 18), (tip[0] + 6, tip[1] - 2)]
    F.line(duct, LINE, G2)
    # near legs (Line weight)
    near = [[(318, 122), (346, 140), (360, gy)], [(300, 126), (300, 150), (292, gy)],
            [(284, 126), (262, 148), (232, gy)]]
    for leg in near:
        F.line(leg, LINE, G3)
    # eye, mandible
    F.shape(ellipse(386, 94, 8, 6.5, 20, 0.2), G3, HAIR)
    F.shape([(402, 112), (414, 116), (420, 124), (410, 122), (400, 118)], G3, HAIR)
    # antennae (scent: rotation of the flagellum, raised & searching at 0, down on the trail at 100)
    elbow = (408, 52)
    F.line([(392, 78), elbow], LINE, G3)
    a = math.radians(-35 + 105 * SCENT)
    tipA = (elbow[0] + 64 * math.cos(a), elbow[1] + 64 * math.sin(a))
    F.line(catmull([elbow, ((elbow[0] + tipA[0]) / 2 + 3, (elbow[1] + tipA[1]) / 2 - 4), tipA], 6, False), LINE, G3)
    F.line([(384, 80), (398, 56)], HAIR, G5)
    b = a - 0.25
    F.line([(398, 56), (398 + 56 * math.cos(b), 56 + 56 * math.sin(b))], HAIR, G5)
    return F


# ======================================================================== v3
def v3() -> Frame:
    """The trace the colony leaves: a leaf held against low light, black, its margin and
    veins edge-lit, and the trail the ants keep walking glistening across it."""
    F = Frame([G0, G2, G3, G4, G5, BK])
    rot = math.radians(-5)
    cx, cy = 248.0, 122.0
    Lh = 206.0                                  # half length

    def P(t, v):
        """t: 0 stem .. 1 tip; v: -1 lower margin .. 1 upper margin."""
        x = -Lh + 2 * Lh * t
        half = 82 * (math.sin(math.pi * min(max(t, 0.0), 0.999)) ** 0.75) * (1 - 0.3 * t)
        y = -(v * half) + 14 * math.sin(math.pi * t) - 6
        c, s = math.cos(rot), math.sin(rot)
        return (cx + x * c - y * s, cy + x * s + y * c)

    up = [P(k / 30, 1) for k in range(31)]
    lo = [P(k / 30, -1) for k in range(31)]
    leaf = up + lo[::-1][1:-1]
    # stem
    F.line([P(0, 0), P(-0.03, 0.15), P(-0.07, 0.5)], LINE, G4)
    F.shape(leaf, G5, HAIR)
    F.line(up[1:], LINE, G2)                     # the lit margin
    # midrib: edge-lit on its upper side
    F.line([P(k / 24, 0.03) for k in range(1, 24)], HAIR, G3)
    F.line([P(k / 24, -0.03) for k in range(1, 22)], HAIR, G5)
    # side veins: one per degree (scale: veins per side), lower side octave one, upper octave two
    nodes = []
    lower = [0.14, 0.30, 0.46, 0.62, 0.78]
    upper = [0.20, 0.36, 0.52, 0.68, 0.84]
    for side, ts in ((-1, lower), (1, upper)):
        for t0 in ts:
            vein = [P(t0 + 0.13 * (k / 12) ** 1.4, side * (0.04 + 0.86 * k / 12)) for k in range(13)]
            F.line(vein, HAIR, G4 if side > 0 else G5)
            nodes.append(vein[7])
    nodes.append(P(0.93, 0.0))
    # ghost trails (fade): old trails, dashed and dull
    for g in GHOSTS[: 2 if FADE < 0.5 else 1]:
        F.dashed(catmull([nodes[i] for i in g], 6, False), HAIR, G3, on=3, off=4)
    # the live trail: one glistening loop through the phrase (scent: strands merge into one)
    loop = catmull([nodes[i] for i in TRAIL[:-1]], 6, True)
    F.line(loop, SUBJ, G0, bound=True)
    stray = catmull([nodes[0], nodes[6], nodes[2]], 6, False)
    F.line([(x, y + 3.5) for x, y in stray], HAIR, G3)
    # ants: silhouettes on the trail, rim-lit
    for t in (0.06, 0.31, 0.55, 0.8)[:N_ANTS]:
        (x, y), ang = point_along(loop, t)
        ant_plan(F, x, y, ang, 17, G2, HAIR, legs=G3)
    return F


# ======================================================================== v4
def v4() -> Frame:
    """One fork of the lattice at large scale: a twig junction where a step can go to any
    degree of the octave, one branch per degree, the rest of the lattice past the frame."""
    F = Frame([G0, G2, G3, G4, G5, BK])
    kx, ky = 132.0, 196.0
    n = 5                                        # scale: branches (degrees per octave)
    angs = [math.radians(-168 + 150 * k / (n - 1)) for k in range(n)]
    chosen = 3                                   # the branch the trail takes
    branches = []
    for k, a in enumerate(angs):
        bend = 0.12 * (1 if k % 2 else -1)
        cl = []
        for j in range(16):
            r = 26 + j * 30
            aa = a + bend * math.sin(j / 15 * math.pi * 0.8)
            cl.append((kx + r * math.cos(aa), ky + r * math.sin(aa)))
        wid = [13 - 4.5 * j / 15 for j in range(16)]
        branches.append((cl, wid))
    order = sorted(range(n), key=lambda k: k == chosen)
    for k in order:
        cl, wid = branches[k]
        left, right = [], []
        for j, (x, y) in enumerate(cl):
            a, b = cl[max(0, j - 1)], cl[min(15, j + 1)]
            d = math.atan2(b[1] - a[1], b[0] - a[0])
            nx, ny = -math.sin(d), math.cos(d)
            left.append((x + nx * wid[j], y + ny * wid[j]))
            right.append((x - nx * wid[j], y - ny * wid[j]))
        body = left + right[::-1]
        F.shape(body, G3, LINE)
        # bark: two grain lines inside, ring scars across
        for fr in (-0.42, 0.42):
            F.line([(x + (-math.sin(math.atan2(cl[min(15, j + 1)][1] - cl[max(0, j - 1)][1], cl[min(15, j + 1)][0] - cl[max(0, j - 1)][0]))) * wid[j] * fr,
                     y + math.cos(math.atan2(cl[min(15, j + 1)][1] - cl[max(0, j - 1)][1], cl[min(15, j + 1)][0] - cl[max(0, j - 1)][0])) * wid[j] * fr)
                    for j, (x, y) in enumerate(cl) if j >= 1], HAIR, G5)
        for j in (3, 7, 11):
            F.line([left[j], ((left[j][0] + right[j][0]) / 2 + 2, (left[j][1] + right[j][1]) / 2 + 2), right[j]], HAIR, G4)
        if k == chosen:
            F.line([(x, y) for x, y in cl[1:]], SUBJ, G0, bound=True)
        elif k in (1, 4)[: 2 if FADE < 0.5 else 1]:
            # old scent left on an unused branch: deposits that haven't evaporated yet
            for j in range(2, 2 + int(9 * (1 - FADE))):
                x, y = cl[j]
                a2 = math.atan2(cl[j + 1][1] - y, cl[j + 1][0] - x)
                F.line([(x - 4 * math.cos(a2), y - 4 * math.sin(a2)), (x + 4 * math.cos(a2), y + 4 * math.sin(a2))], LINE, G3)
    # the knot where the branches meet
    knot = [(kx + (34 + 4 * math.sin(3 * t)) * math.cos(t), ky + (30 + 3 * math.cos(5 * t)) * math.sin(t))
            for t in [2 * math.pi * k / 40 for k in range(40)]]
    F.shape(knot, G3, LINE)
    for r in (22, 13):
        F.line(ellipse(kx + 2, ky - 2, r * 1.1, r * 0.9, 28, 0.2, closed=False), HAIR, G4)
    # the scout at the fork: its heading swings onto the scented branch with scent
    target = math.atan2(branches[chosen][0][2][1] - ky, branches[chosen][0][2][0] - kx)
    wander = angs[1]
    head = wander + (target - wander) * (0.3 + 0.7 * SCENT)
    ant_plan(F, kx + 18 * math.cos(head), ky - 8 + 18 * math.sin(head), head, 40, G2, LINE, legs=G3, legw=LINE)
    # ants already on the scented branch (ants: count)
    cl = branches[chosen][0]
    for k, j in enumerate((4, 7, 10)[: N_ANTS - 1]):
        x, y = cl[j]
        a2 = math.atan2(cl[j + 1][1] - y, cl[j + 1][0] - x)
        ant_plan(F, x, y, a2, 32 - 3 * k, G2, HAIR, legs=G3)
    return F


# ======================================================================== v5 (3D)
class Camera:
    def __init__(self, pos, look, f, cx, cy):
        self.p = pos
        fw = [look[i] - pos[i] for i in range(3)]
        n = math.sqrt(sum(v * v for v in fw))
        self.fw = [v / n for v in fw]
        r = [self.fw[2], 0.0, -self.fw[0]]              # right = fw x up(0,1,0)
        n = math.sqrt(sum(v * v for v in r))
        self.r = [-v / n for v in r]
        self.u = [self.r[1] * self.fw[2] - self.r[2] * self.fw[1],
                  self.r[2] * self.fw[0] - self.r[0] * self.fw[2],
                  self.r[0] * self.fw[1] - self.r[1] * self.fw[0]]
        if self.u[1] < 0:
            self.u = [-v for v in self.u]
        self.f, self.cx, self.cy = f, cx, cy

    def depth(self, P):
        d = [P[i] - self.p[i] for i in range(3)]
        return sum(d[i] * self.fw[i] for i in range(3))

    def __call__(self, P):
        d = [P[i] - self.p[i] for i in range(3)]
        z = sum(d[i] * self.fw[i] for i in range(3))
        x = sum(d[i] * self.r[i] for i in range(3))
        y = sum(d[i] * self.u[i] for i in range(3))
        return (self.cx + self.f * x / z, self.cy - self.f * y / z)


def ant3d(F, cam, pos, heading, size, edge=G3, inner=G4, legc=G3):
    """One ant modelled from ellipsoids and jointed legs, hidden-line by painter's order."""
    ch, sh = math.cos(heading), math.sin(heading)

    def W(p):
        x, y, z = p[0] * size, p[1] * size, p[2] * size
        return (pos[0] + x * ch - z * sh, pos[1] + y, pos[2] + x * sh + z * ch)

    parts = {"gaster": ((-0.36, 0.26, 0), (0.25, 0.16, 0.17)),
             "petiole": ((-0.08, 0.24, 0), (0.045, 0.075, 0.045)),
             "meso": ((0.09, 0.25, 0), (0.16, 0.075, 0.075)),
             "head": ((0.34, 0.27, 0), (0.105, 0.095, 0.1))}
    legs = []
    for side in (-1, 1):
        for rx, kx, fx in ((0.16, 0.30, 0.46), (0.08, 0.10, 0.10), (0.0, -0.16, -0.36)):
            legs.append((side, [W((rx, 0.21, side * 0.05)), W((kx, 0.36, side * 0.24)),
                                W((fx, 0.0, side * 0.40))]))
        legs.append((side, [W((0.42, 0.31, side * 0.04)), W((0.47, 0.46, side * 0.13)),
                            W((0.66, 0.34, side * 0.22))]))
    cpos = cam.p
    # which side is far from the camera
    side_far = 1 if cam.depth(W((0, 0.2, 1))) > cam.depth(W((0, 0.2, -1))) else -1
    for side, pts in legs:
        if side == side_far:
            F.line([cam(p) for p in pts], HAIR, G4)
    items = sorted(parts.items(), key=lambda kv: -cam.depth(W(kv[1][0])))
    for name, (c, r) in items:
        samples = []
        for i in range(18):
            th = math.pi * (i + 0.5) / 18
            for j in range(24):
                ph = 2 * math.pi * j / 24
                samples.append(cam(W((c[0] + r[0] * math.cos(th), c[1] + r[1] * math.sin(th) * math.cos(ph),
                                      c[2] + r[2] * math.sin(th) * math.sin(ph)))))
        for e in ((1, 0, 0), (-1, 0, 0)):
            samples.append(cam(W((c[0] + e[0] * r[0], c[1], c[2]))))
        out = hull(samples)
        F.shape(out, edge, LINE, bound=True)
        # inner structure: rings round the long axis, front-facing runs only
        rings = {"gaster": (-0.55, -0.15, 0.25), "meso": (-0.3, 0.4), "head": (0.2,)}.get(name, ())
        for u in rings:
            ring_run = []
            runs = []
            for j in range(41):
                ph = 2 * math.pi * j / 40
                sx = math.sqrt(max(0.0, 1 - u * u))
                lp = (c[0] + r[0] * u, c[1] + r[1] * sx * math.cos(ph), c[2] + r[2] * sx * math.sin(ph))
                nrm = (u / r[0], sx * math.cos(ph) / r[1], sx * math.sin(ph) / r[2])
                wp = W(lp)
                wn = (nrm[0] * ch - nrm[2] * sh, nrm[1], nrm[0] * sh + nrm[2] * ch)
                vis = sum(wn[i] * (cpos[i] - wp[i]) for i in range(3)) > 0
                if vis:
                    ring_run.append(cam(wp))
                elif len(ring_run) > 1:
                    runs.append(ring_run)
                    ring_run = []
                else:
                    ring_run = []
            if len(ring_run) > 1:
                runs.append(ring_run)
            for rr in runs:
                # trim the ends a little so the ring doesn't touch the silhouette
                if len(rr) > 6:
                    F.line(rr[2:-2], HAIR, inner)
        if name == "head":
            for side in (-1, 1):                         # compound eye
                ec = (c[0] + 0.02, c[1] + 0.02, c[2] + side * r[2] * 0.82)
                if cam.depth(W(ec)) < cam.depth(W(c)):
                    pts = [cam(W((ec[0] + 0.035 * math.cos(t), ec[1] + 0.03 * math.sin(t), ec[2])))
                           for t in [2 * math.pi * k / 14 for k in range(14)]]
                    F.shape(pts, inner, HAIR)
    for side, pts in legs:
        if side != side_far:
            F.line([cam(p) for p in pts], LINE if size > 0.8 else HAIR, legc)


def v5() -> Frame:
    """Ants, drawn literally in hidden-line 3D: a file of modelled ants walking the
    reinforced path across the degree stones, one camera over the whole scene."""
    F = Frame([G0, G2, G3, G4, G5, BK])
    cam = Camera((3.2, 3.6, 7.4), (0.6, 0.1, -0.6), 300.0, 232.0, 116.0)
    # degree stones: two rows, octave one near, octave two far; one more for the top root
    sp = 1.9
    stones = [(-3.8 + i * sp, 0.0, 0.6) for i in range(5)] + [(-2.9 + i * sp, 0.0, -2.0) for i in range(5)] + [(6.6, 0.0, -2.0)]

    def disc(c, r, y):
        return [(c[0] + r * math.cos(t), y, c[2] + r * math.sin(t)) for t in [2 * math.pi * k / 32 for k in range(32)]]
    # ground marks: a few hairline contours of the ground, far ones only
    # ghost paths (fade): old routes, thin and dashed on the ground
    for g in GHOSTS[: 2 if FADE < 0.5 else 1]:
        pts = [cam(stones[i]) for i in g]
        F.dashed(pts, HAIR, G4, on=4, off=4)
    # live path: the bright trail on the ground
    route = [cam(stones[i]) for i in TRAIL]
    F.line(catmull(route[:-1], 6, True), SUBJ, G0, bound=True)
    # stones, far to near: hidden-line low cylinders
    for c in sorted(stones, key=lambda s: -cam.depth(s)):
        top = [cam(p) for p in disc(c, 0.5, 0.16)]
        bot = [cam(p) for p in disc(c, 0.5, 0.0)]
        F.shape(hull(top + bot), G4, LINE)
        F.shape(top, G5, HAIR)
    # ants along the route, far to near
    walk = [stones[i] for i in TRAIL]
    spots = []
    for (a, b), t in zip(zip(walk, walk[1:]), (0.55, 0.0, 0.5, 0.0, 0.0, 0.45, 0.5)):
        if t:
            spots.append(((a[0] + (b[0] - a[0]) * t, 0.0, a[2] + (b[2] - a[2]) * t),
                          math.atan2(b[2] - a[2], b[0] - a[0])))
    for p, h in sorted(spots[:N_ANTS], key=lambda s: -cam.depth(s[0])):
        ant3d(F, cam, p, h, 1.15)
    return F


def main() -> None:
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        F = fn()
        (HERE / name).mkdir(exist_ok=True)
        (HERE / name / "rest.svg").write_text(F.svg())
        print(name, "bound nodes", F.node)


if __name__ == "__main__":
    main()
