#!/usr/bin/env python3
"""Ants subject pass 03: one rest-frame sketch per direction (v1..v5).

No ant bodies anywhere: each variant draws what the colony does or leaves
(a route worn into a mechanism, scent beads on a surface, a worn crossing,
a rope laid up from strands, the trail band itself). Rest frames at the
definition's defaults (ants 4, scent 50, fade 30, scale pent), stock header
kept, 480 x 220, no text below the header. States are line weight,
brightness, movement or 45 degree hatching, never a lighter grey fill.
3D scenes (v2-v5) are modelled in world units and projected through one
camera each (class Cam).

    python3 screens/ants/passes/03-subject/sketch.py
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
                if len(seg) >= 2 and sum(math.dist(a, b) for a, b in zip(seg, seg[1:])) > 3.0:
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
                    if b - a > 3.0:
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



# ---- one camera per 3D scene ------------------------------------------------
class Cam:
    """Pinhole camera: position, look-at point, focal length in px, screen centre."""

    def __init__(self, pos, look, focal, cx, cy):
        self.p = pos
        fw = [look[i] - pos[i] for i in range(3)]
        n = math.sqrt(sum(v * v for v in fw))
        self.fw = [v / n for v in fw]
        up = (0.0, 1.0, 0.0)
        r = [up[1] * self.fw[2] - up[2] * self.fw[1],
             up[2] * self.fw[0] - up[0] * self.fw[2],
             up[0] * self.fw[1] - up[1] * self.fw[0]]
        n = math.sqrt(sum(v * v for v in r))
        self.r = [v / n for v in r]
        self.u = [self.fw[1] * self.r[2] - self.fw[2] * self.r[1],
                  self.fw[2] * self.r[0] - self.fw[0] * self.r[2],
                  self.fw[0] * self.r[1] - self.fw[1] * self.r[0]]
        self.f, self.cx, self.cy = focal, cx, cy

    def depth(self, P):
        return sum((P[i] - self.p[i]) * self.fw[i] for i in range(3))

    def ppu(self, P):
        """Pixels per world unit at P's depth."""
        return self.f / self.depth(P)

    def __call__(self, P):
        d = [P[i] - self.p[i] for i in range(3)]
        z = sum(d[i] * self.fw[i] for i in range(3))
        x = sum(d[i] * self.r[i] for i in range(3))
        y = sum(d[i] * self.u[i] for i in range(3))
        return (self.cx + self.f * x / z, self.cy - self.f * y / z)


def rng(seed):
    """Small deterministic noise source so every run draws the same frame."""
    s = [seed]

    def r():
        s[0] = (s[0] * 1103515245 + 12345) % 2147483648
        return s[0] / 2147483648
    return r


def disc(cx, cy, r, n=20):
    return ellipse(cx, cy, r, r, n)


# ============================================================ v1 · gate cascade
def v1() -> Frame:
    """A hand-held marble board: rocker gates in a cascade, five outlets (pent).

    Every marble that passes a gate pushes it further toward the side it took
    (deposit); a spring pulls each gate back to centre (fade). The route the
    gates have been thrown onto is the worn groove, the brightest line.
    """
    F = Frame([G0, G2, G4])
    cy, x0, dx, dy, w = 121.0, 84.0, 90.0, 44.0, 13.0

    def node(k, j):
        return (x0 + k * dx, cy + (j - k / 2) * dy)

    # board: a rounded slab entering from the left, running off the right edge
    bx0, by0, by1, rad = 14.0, 25.0, 216.0, 12.0
    board = (ellipse(bx0 + rad, by0 + rad, rad, rad, 10, a0=math.pi, a1=1.5 * math.pi, closed=False)
             + [(530, by0), (530, by1)]
             + ellipse(bx0 + rad, by1 - rad, rad, rad, 10, a0=0.5 * math.pi, a1=math.pi, closed=False))
    F.shape(board, G3, LINE)
    F.hatch(board, fill=G5, gap=5.0)

    edges = [((-20.0, cy), node(0, 0))]
    for k in range(4):
        for j in range(k + 1):
            edges += [(node(k, j), node(k + 1, j)), (node(k, j), node(k + 1, j + 1))]
    outlets = [(node(4, j), (520.0, node(4, j)[1])) for j in range(5)]
    edges += outlets
    nodes = [node(k, j) for k in range(5) for j in range(k + 1)]

    # carve: a grey band one Line wider than the channel, then the black channel
    for a, b in edges:
        F.line([a, b], w + 2 * LINE, G3)
    for p in nodes:
        F.path(disc(p[0], p[1], w / 2 + LINE, 16), fill=G3)
    for a, b in edges:
        F.line([a, b], w, BK)
    for p in nodes:
        F.path(disc(p[0], p[1], w / 2, 16), fill=BK)

    # the reinforced route and two older ones (decisions: 0 up, 1 down)
    def route(dec):
        j, pts = 0, [(-20.0, cy), node(0, 0)]
        for k, d in enumerate(dec):
            j += d
            pts.append(node(k + 1, j))
        pts.append((520.0, pts[-1][1]))
        return pts

    main_dec = [1, 0, 1, 0]
    old = [[0, 0, 0, 1], [1, 1, 1, 0]]
    main = route(main_dec)
    # old routes: residue hatched inside the channel where it leaves the main route
    for dec in old[:2]:
        pts = route(dec)
        for a, b in zip(pts[1:-1], pts[2:]):
            if (a, b) in list(zip(main, main[1:])):
                continue
            ang = math.atan2(b[1] - a[1], b[0] - a[0])
            ca, sa = math.cos(ang), math.sin(ang)
            a2, b2 = (a[0] + ca * 9, a[1] + sa * 9), (b[0] - ca * 9, b[1] - sa * 9)
            F.hatch(ribbon([a2, b2], w - 3), fill=G4, gap=3.2)

    # gates: a rocker blade hinged at the tip of the mass after each split
    th = math.atan2(dy / 2, dx)
    tip = (w / 2 + LINE) / math.sin(th) + 2
    r = rng(7)
    on_route = {}
    j = 0
    for k, d in enumerate(main_dec):
        on_route[(k, j)] = d
        j += d
    for k in range(4):
        for j in range(k + 1):
            hx, hy = node(k, j)[0] + tip, node(k, j)[1]
            if (k, j) in on_route:
                # thrown toward the branch not taken: blade swings across it
                ang = (1 if on_route[(k, j)] == 1 else -1) * math.radians(22) * (0.5 + SCENT)
                edge, sw = G1, LINE
            else:
                ang = math.radians(5) * (r() * 2 - 1)
                edge, sw = G3, HAIR
            L, t = 30.0, 6.0
            ca, sa = math.cos(math.pi - ang), math.sin(math.pi - ang)
            nx, ny = -sa, ca
            tipx, tipy = hx + ca * L, hy + sa * L
            blade = [(hx + nx * t / 2, hy + ny * t / 2), (tipx + nx * t / 2, tipy + ny * t / 2),
                     (tipx - nx * t / 2, tipy - ny * t / 2), (hx - nx * t / 2, hy - ny * t / 2)]
            F.shape(blade, edge, sw, bound=True)
            F.shape(disc(hx, hy, 3.2, 12), G2, HAIR)

    # the worn groove: the brightest line, down the middle of the route
    F.line(simplify(densify(main, 3)), SUBJ, G0, bound=True)

    # marbles on the route, one per ant
    for fr in (0.08, 0.33, 0.57, 0.83)[:N_ANTS]:
        (mx, my), _ = point_along(main, fr)
        F.shape(disc(mx, my, 4.6, 16), G2, LINE, bound=True)
    return F


# ======================================================= v2 · scent beads, close
def v2() -> Frame:
    """The ground the colony works, seen close: sand grains, edge-lit.

    The trail is a channel swept clear through the grains, bending past the
    pebbles that are this scale's degrees; scent lies on its floor as beads,
    the newest at the front. An older branch is filling back in (hatched).
    """
    F = Frame([G0, G1, G3, G5])
    cam = Cam((-0.45, 0.95, -0.95), (0.2, 0.0, 1.9), 250.0, 250.0, 112.0)
    r = rng(23)
    half = 0.12 + 0.16 * SCENT

    # the degrees as pebbles, the phrase bending round them in turn
    peb = [(0.7, 0.45), (-0.75, 1.6), (0.75, 2.8), (-0.7, 4.1), (0.7, 5.5)]
    ctrl = [(0.1, -0.55)]
    for i, (px, pz) in enumerate(peb):
        ctrl.append((px - (1 if px > 0 else -1) * 0.42, pz))
    ctrl.append((0.2, 6.6))
    ctrl.append((0.0, 9.0))
    line = catmull(ctrl, per=12, closed=False)
    # an older branch leaving at the third pebble, refilling
    old = catmull([(0.33, 2.8), (0.9, 3.6), (1.6, 4.3), (2.5, 4.8)], per=10, closed=False)

    def near(p, path, d):
        return any(math.hypot(p[0] - q[0], p[1] - q[1]) < d for q in path)

    def grain(x, z, rr, rim, sw, flat=0.55, body=None):
        pts = []
        wob = [0.8 + 0.4 * r() for _ in range(7)]
        for i in range(21):
            t = 2 * math.pi * i / 21
            k = wob[i % 7]
            pts.append(cam((x + rr * k * math.cos(t), 0.0, z + rr * k * math.sin(t))))
            pts.append(cam((x + rr * k * 0.6 * math.cos(t), rr * flat * 0.8, z + rr * k * 0.6 * math.sin(t))))
        pts.append(cam((x, rr * flat, z)))
        sil = hull(pts)
        cx = sum(p[0] for p in sil) / len(sil)
        cy = sum(p[1] for p in sil) / len(sil)
        F.path(sil, fill=BK, stroke=body or G6, sw=HAIR)
        angs = [math.degrees(math.atan2(p[1] - cy, p[0] - cx)) for p in sil]
        run = sorted([i for i in range(len(sil)) if -170 <= angs[i] <= -60], key=lambda i: angs[i])
        if len(run) >= 2:
            F.line([sil[i] for i in run], sw, rim)
        return cx, cy, (max(p[0] for p in sil) - min(p[0] for p in sil)) / 2

    items = []
    # grains everywhere the trail isn't
    tries = 0
    while len(items) < 330 and tries < 9000:
        tries += 1
        x, z = -2.6 + 5.6 * r(), -0.9 + 9.5 * r()
        rr = 0.04 + 0.075 * r() * r()
        if near((x, z), line, half + rr + 0.05) or any(math.hypot(x - a, z - b) < 0.3 + rr for a, b in peb):
            continue
        if near((x, z), old, half * 0.8 + rr) and r() > FADE * 1.6:
            continue
        if any(math.hypot(x - it[1], z - it[2]) < it[3] + rr + 0.02 for it in items):
            continue
        if cam.ppu((x, 0, z)) * rr < 2.0 or not (0 < cam((x, 0, z))[0] < W and TOP + 2 < cam((x, 0, z))[1] < H + 6):
            continue
        items.append(("grain", x, z, rr))
    for px, pz in peb:
        items.append(("pebble", px, pz, 0.24))

    # the old branch's floor: hatched, it is there but going
    lft, rgt = [], []
    for i, p in enumerate(old):
        a, b = old[max(i - 1, 0)], old[min(i + 1, len(old) - 1)]
        tx, tz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, tz) or 1
        k = half * 0.8 * (1 - 0.5 * i / (len(old) - 1))
        lft.append(cam((p[0] + tz / L * k, 0, p[1] - tx / L * k)))
        rgt.append(cam((p[0] - tz / L * k, 0, p[1] + tx / L * k)))
    F.hatch(lft + rgt[::-1], fill=G5, gap=3.4)

    # the channel's swept edges
    for s in (-1, 1):
        edge = []
        for i, p in enumerate(line):
            if p[1] > 6.4:
                break
            if cam.depth((p[0], 0, p[1])) < 0.3:
                continue
            a, b = line[max(i - 1, 0)], line[min(i + 1, len(line) - 1)]
            tx, tz = b[0] - a[0], b[1] - a[1]
            L = math.hypot(tx, tz) or 1
            edge.append(cam((p[0] + s * tz / L * half, 0, p[1] - s * tx / L * half)))
        F.line(edge, HAIR, G5)

    # scent beads on the channel floor, newest at the front
    nb = 11
    for k in range(nb):
        p, _ = point_along(line, 0.075 + k * 0.058)
        rr = 0.11 * (1 - 0.3 * FADE) ** k
        items.append(("bead", p[0], p[1], rr, k))

    for it in sorted(items, key=lambda it: -cam.depth((it[1], 0, it[2]))):
        kind, x, z, rr = it[:4]
        if kind == "grain":
            grain(x, z, rr, G4, HAIR, flat=0.5)
        elif kind == "pebble":
            grain(x, z, rr, G2, LINE, flat=0.6, body=G5)
        else:
            k = it[4]
            if cam.ppu((x, 0, z)) * rr < 1.6:
                p = cam((x, 0, z))
                F.line([(p[0] - 2, p[1]), (p[0] + 2, p[1])], HAIR, G5)      # dried to a mark
                continue
            rim, sw = (G0, SUBJ) if k == 0 else (G1, LINE) if k < N_ANTS else (G3, HAIR)
            cx, cy, rx = grain(x, z, rr, rim, sw, flat=0.75, body=G5)
            if rx > 7:
                F.line([(cx - rx * 0.5, cy - rx * 0.02), (cx - rx * 0.18, cy - rx * 0.32)], HAIR, G2)
    return F


# ======================================================= v3 · stepping-stone ford
def v3() -> Frame:
    """A ford of stepping stones: one row per step, one stone per degree.

    The worn route across is the trail: polished tops, a dished tread; stones
    off it are mossed over (hatched). The colony's crossing is the phrase.
    """
    F = Frame([G0, G1, G3, G5])
    cam = Cam((0.5, 3.4, -2.3), (0.2, 0.0, 2.6), 300.0, 240.0, 122.0)
    r = rng(11)
    rows, per = 6, 5
    route = [2, 1, 1, 3, 4, 3]
    old_route = [2, 2, 0, 1, 3, 4]
    zb0, zb1 = -0.75, 6.25           # near and far banks

    # far bank: a ragged edge, the trail carrying on as a worn path
    bank = [(-6.0 + 0.4 * i, 0.12, zb1 + 0.12 * math.sin(i * 1.7) + 0.05 * r()) for i in range(31)]
    bpts = [cam(p) for p in bank]
    F.line(bpts, LINE, G3)
    for i in range(0, 30, 3):
        x0, _, z0 = bank[i]
        a = cam((x0 + 0.1, 0.12, z0 + 0.35))
        F.line([a, (a[0] + 2, a[1] - 5)], HAIR, G5)
    # near bank, cut by the frame
    nb = [cam((-6.0 + 0.4 * i, 0.12, zb0 + 0.1 * math.sin(i * 2.3))) for i in range(31)]
    F.line(nb, LINE, G3)

    # water: sparse flow lines across the stream
    for i in range(26):
        x = -4.5 + r() * 9.0
        z = zb0 + 0.35 + r() * (zb1 - zb0 - 0.7)
        L = 0.35 + r() * 0.4
        a, b = cam((x, 0, z)), cam((x + L, 0, z))
        if 23 < a[1] < 218:
            F.line([a, b], HAIR, G6)

    stones = []
    for ri in range(rows):
        for si in range(per):
            x = (si - 2) * 1.2 + (r() - 0.5) * 0.3
            z = 0.25 + ri * 1.0 + (r() - 0.5) * 0.18
            rad = 0.36 + r() * 0.08
            stones.append((ri, si, x, z, rad, [0.78 + 0.36 * r() for _ in range(9)]))

    def top_pts(x, z, rad, wob, h, n=27):
        out = []
        for i in range(n):
            t = 2 * math.pi * i / n
            k = wob[i % 9] * 0.6 + wob[(i + 1) % 9] * 0.4
            out.append((x + rad * k * math.cos(t) * 1.15, h, z + rad * k * math.sin(t) * 0.85))
        return out

    lead = (len(route) - 3, route[-3])           # the stone the front ant stands on
    for ri, si, x, z, rad, wob in sorted(stones, key=lambda s: -cam.depth((s[2], 0, s[3]))):
        h = 0.2
        top3 = top_pts(x, z, rad, wob, h)
        base3 = top_pts(x, z, rad * 1.06, wob, 0.0)
        top = [cam(p) for p in top3]
        sil = hull(top + [cam(p) for p in base3])
        # ripples on the upstream (left) side, a wake to the right
        for k, off in enumerate((0.13, 0.27)):
            arc = [cam((x + (rad + off) * 1.15 * math.cos(t), 0, z + (rad + off) * 0.85 * math.sin(t)))
                   for t in [math.pi * (0.62 + 0.76 * i / 10) for i in range(11)]]
            F.line(arc, HAIR, G5 if k == 0 else G6)
        wk = [cam((x + rad * 1.1 + 0.05 + 0.3 * i / 4, 0, z + s * (0.12 + 0.12 * i / 4)))
              for s in (-1,) for i in range(5)]
        F.line(wk, HAIR, G6)
        on = route[ri] == si
        was = old_route[ri] == si and not on
        F.path(sil, fill=BK, stroke=G3, sw=LINE)
        # the stone's flank: short hairlines down the near side
        last = None
        for i in range(13, 27):
            a, b = top[i], cam(base3[i])
            if b[1] - a[1] > 3.5 and (last is None or abs(a[0] - last) >= 4.5):
                F.line([(a[0], a[1] + 1.6), (b[0], b[1] - 1.2)], HAIR, G5)
                last = a[0]
        if on:
            stroke = G0 if (ri, si) == lead else G1
            F.path(top, fill=BK, stroke=stroke, sw=SUBJ if (ri, si) == lead else LINE, bound=True)
            # the dished, polished tread worn into the top
            dish = [cam((x + rad * 0.55 * math.cos(t), h, z + rad * 0.45 * math.sin(t)))
                    for t in [math.pi * (0.05 + 0.9 * i / 10) for i in range(11)]]
            F.line(dish, HAIR, G2)
            if ri < N_ANTS + 1 and (ri, si) != lead and ri != 0:
                # wet from a crossing just now: a short sheen on the near lip
                sheen = [cam((x + rad * 0.72 * math.cos(t), h, z + rad * 0.62 * math.sin(t)))
                         for t in [math.pi * (1.25 + 0.3 * i / 5) for i in range(6)]]
                F.line(sheen, LINE, G2)
        else:
            F.path(top, fill=BK, stroke=G4, sw=HAIR)
            # moss over the top: hatched; a stone that was on the old route keeps a bare patch
            if was:
                bare = [cam((x + 0.42 * (px - x) + 0.08, h, z + 0.42 * (pz - z))) for px, _, pz in top3]
                F.hatch(top, fill=G5, gap=3.4, holes=(bare,))
                F.line(bare + [bare[0]], HAIR, G4)
            else:
                F.hatch(top, fill=G5, gap=3.4)
            # a crack across the top
            F.line([cam((x - rad * 0.5, h, z + rad * 0.1)), cam((x + rad * 0.1, h, z - rad * 0.15))], HAIR, G5)
    return F


# =========================================================== v4 · ring and ropes
def v4() -> Frame:
    """One mooring ring at large scale, ropes run off to the rest of the lattice.

    Each rope is a way to another degree. The one the colony keeps using is
    laid up from many strands and pulled taut; the rest hang slack, and the
    ones left longest have frayed through (hatched past the break).
    """
    F = Frame([G0, G2, G4])
    cam = Cam((-1.6, 1.3, -7.0), (-0.45, -0.05, 0.0), 540.0, 240.0, 120.0)
    C = (-1.55, 0.05, 0.0)
    R, rt = 0.62, 0.11
    tilt = math.radians(28)                       # ring plane turned toward the right
    e1 = (math.cos(tilt), 0.0, math.sin(tilt))
    e2 = (0.0, 1.0, 0.0)
    nrm = (-math.sin(tilt), 0.0, math.cos(tilt))

    def ring_pt(u, v=0.0, rr=None):
        rr = rt if rr is None else rr
        k = R + rr * math.cos(v)
        return tuple(C[i] + k * (math.cos(u) * e1[i] + math.sin(u) * e2[i]) + rr * math.sin(v) * nrm[i]
                     for i in range(3))

    # ropes: (angle on the ring, far end, radius, sag, break fraction or None)
    ropes = [(math.radians(-8), (9.0, -0.5, 3.0), 0.07, 0.0, None),        # the trail: taut, thick
             (math.radians(48), (3.6, 3.4, 2.5), 0.034, 0.55, None),
             (math.radians(150), (-6.5, 1.6, 1.5), 0.032, 0.6, 0.62),
             (math.radians(222), (-4.6, -3.6, 0.6), 0.03, 0.5, 0.55),
             (math.radians(300), (1.9, -4.2, 1.2), 0.034, 0.45, 0.7)]

    def rope_curve(a, b, sag, n=40):
        pts = []
        for i in range(n + 1):
            t = i / n
            p = [a[k] + (b[k] - a[k]) * t for k in range(3)]
            p[1] -= sag * 4 * t * (1 - t) * math.dist(a, b) * 0.18
            pts.append(tuple(p))
        return pts

    def rope_outline(c3, rad):
        sc = [cam(p) for p in c3]
        left, right = [], []
        for i, p in enumerate(sc):
            q0, q1 = sc[max(i - 1, 0)], sc[min(i + 1, len(sc) - 1)]
            dx, dy = q1[0] - q0[0], q1[1] - q0[1]
            L = math.hypot(dx, dy) or 1
            nx, ny = -dy / L, dx / L
            wpx = cam.ppu(c3[i]) * rad
            left.append((p[0] + nx * wpx, p[1] + ny * wpx))
            right.append((p[0] - nx * wpx, p[1] - ny * wpx))
        return sc, left, right

    def draw_rope(c3, rad, edge, sw, lay, lay_w, strands, ghost=False):
        sc, left, right = rope_outline(c3, rad)
        poly = left + right[::-1]
        if ghost:
            F.path(clip_poly(poly), fill=BK)
            F.hatch(poly, fill=G5, gap=3.2)
            F.dashed(left, HAIR, G5, 3, 3)
            F.dashed(right, HAIR, G5, 3, 3)
            return sc, left, right
        F.path(clip_poly(poly), fill=BK)
        F.line(left, sw, edge)
        F.line(right, sw, edge)
        # lay lines: the strands' twist, slanting across the visible face
        s = 0.0
        pitch = 9.0 if strands > 2 else 12.0
        for i in range(1, len(sc)):
            s += math.dist(sc[i], sc[i - 1])
            if s >= pitch:
                s = 0.0
                j = max(i - 2, 0)
                a = (left[i][0] * 0.9 + right[i][0] * 0.1, left[i][1] * 0.9 + right[i][1] * 0.1)
                b = (right[j][0] * 0.9 + left[j][0] * 0.1, right[j][1] * 0.9 + left[j][1] * 0.1)
                if math.dist(a, b) > 3:
                    F.line([a, b], lay_w, lay)
        return sc, left, right

    # ropes that leave behind the ring first, then the ring, then the near ones
    order = sorted(range(len(ropes)), key=lambda i: -cam.depth(ropes[i][1]))
    ring_done = False

    def draw_ring():
        outer = hull([cam(ring_pt(2 * math.pi * i / 48, 2 * math.pi * j / 12)) for i in range(48) for j in range(12)])
        F.path(outer, fill=BK, stroke=G2, sw=LINE, bound=True)
        hole = [cam(ring_pt(2 * math.pi * i / 40, math.pi, rt)) for i in range(40)]
        F.path(hole, fill=BK, stroke=G3, sw=LINE)
        crest = [cam(ring_pt(2 * math.pi * i / 40, -math.pi / 2, rt)) for i in range(41)]
        F.line(crest[2:20], HAIR, G3)
        F.line(crest[22:39], HAIR, G4)

    for i in order:
        u, far, rad, sag, brk = ropes[i]
        if not ring_done and cam.depth(far) < cam.depth(C) + 1.0:
            draw_ring()
            ring_done = True
        a = ring_pt(u, 0.0, rt + rad * 0.6)
        c3 = rope_curve(a, far, sag)
        if i == 0:
            draw_rope(c3, rad, G0, SUBJ, G2, HAIR, N_ANTS)
        elif brk is None:
            draw_rope(c3, rad, G3, LINE, G4, HAIR, 1)
        else:
            vis = [j for j, q in enumerate(c3) if 0 <= cam(q)[0] <= W and TOP <= cam(q)[1] <= H]
            k = max(6, int((max(vis) if vis else len(c3)) * brk * (1 - 0.6 * FADE)))
            draw_rope(c3[k:], rad, G5, HAIR, G5, HAIR, 1, ghost=True)
            sc, left, right = draw_rope(c3[:k + 1], rad, G3, LINE, G4, HAIR, 1)
            # the frayed end: loose fibres splaying from the break
            ex, ey = sc[-1]
            dx, dy = sc[-1][0] - sc[-3][0], sc[-1][1] - sc[-3][1]
            L = math.hypot(dx, dy) or 1
            dx, dy = dx / L, dy / L
            for k2, spread in enumerate((-0.5, -0.15, 0.2, 0.55)):
                ca, sa = math.cos(spread), math.sin(spread)
                fx, fy = dx * ca - dy * sa, dx * sa + dy * ca
                Lf = 8 + 3 * (k2 % 2)
                F.line([(ex - dy * (k2 - 1.5) * 1.2, ey + dx * (k2 - 1.5) * 1.2),
                        (ex + fx * Lf, ey + fy * Lf)], HAIR, G4)
        # the hitch round the ring: two turns of the rope's own line
        for v0 in (-0.17, 0.17):
            ring3 = [ring_pt(u + v0, 2 * math.pi * j / 24, rt + rad * 0.35) for j in range(25)]
            mid = cam.depth(ring_pt(u + v0, 0.0, 0.0))
            ring3 = ring3[:-1]
            fl = [cam.depth(q) <= mid for q in ring3]
            start = next((j for j in range(len(fl)) if fl[j] and not fl[j - 1]), 0)
            front = []
            for j in range(len(fl)):
                q = ring3[(start + j) % len(fl)]
                if not fl[(start + j) % len(fl)]:
                    break
                front.append(cam(q))
            if len(front) > 2:
                F.line(front, LINE if i == 0 else HAIR, G1 if i == 0 else G3)
    if not ring_done:
        draw_ring()
    return F


# ======================================================== v5 · the trail itself
def v5() -> Frame:
    """The trail, drawn as the thing it is: a cleared band worn into the ground.

    One closed loop (the phrase that has set) past the stones it plays,
    spurs of old trail fading into the litter, seeds carried round the loop.
    """
    F = Frame([G0, G1, G2, G4])
    cam = Cam((0.0, 5.0, -4.4), (0.0, 0.0, 0.75), 290.0, 240.0, 116.0)
    r = rng(5)
    # the phrase's stations on the ground, in the order the loop visits them
    stations = [(-3.5, 0.7), (-2.3, 2.5), (-0.3, 2.7), (1.3, 1.5), (3.1, 2.4),
                (3.8, 0.3), (2.0, -0.9), (-1.4, -0.8)]
    half = 0.16 + 0.22 * SCENT

    centre = catmull(stations, per=10, closed=True)[:-1]
    n = len(centre)
    outer, inner = [], []
    for i in range(n):
        a, b = centre[i - 1], centre[(i + 1) % n]
        tx, tz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, tz) or 1
        nx, nz = tz / L, -tx / L
        outer.append((centre[i][0] + nx * half, centre[i][1] + nz * half))
        inner.append((centre[i][0] - nx * half, centre[i][1] - nz * half))
    # which side is outside the loop
    def area(poly):
        return abs(sum(poly[i - 1][0] * poly[i][1] - poly[i][0] * poly[i - 1][1] for i in range(len(poly))))
    if area(inner) > area(outer):
        outer, inner = inner, outer

    def G(p, y=0.0):
        return cam((p[0], y, p[1]))

    # spurs: old trails that leave the loop and fade out (hatched)
    spurs = [(1, (-2.6, 4.6)), (4, (5.2, 1.4)), (7, (-2.4, -3.0))]
    for si, far in spurs:
        s = stations[si]
        mid = ((s[0] + far[0]) / 2 + 0.4, (s[1] + far[1]) / 2)
        reach = 1.0 - 0.75 * FADE
        tip = (s[0] + (far[0] - s[0]) * reach, s[1] + (far[1] - s[1]) * reach)
        line = catmull([s, (s[0] + (mid[0] - s[0]) * reach, s[1] + (mid[1] - s[1]) * reach), tip], per=8, closed=False)
        hw = half * 0.8
        lft, rgt = [], []
        for i, p in enumerate(line):
            a, b = line[max(i - 1, 0)], line[min(i + 1, len(line) - 1)]
            tx, tz = b[0] - a[0], b[1] - a[1]
            L = math.hypot(tx, tz) or 1
            k = hw * (1 - 0.85 * i / (len(line) - 1))
            lft.append((p[0] + tz / L * k, p[1] - tx / L * k))
            rgt.append((p[0] - tz / L * k, p[1] + tx / L * k))
        poly = [G(p) for p in lft + rgt[::-1]]
        F.shape(poly, G4, LINE)
        F.hatch(poly, fill=G5, gap=3.4)

    # litter the colony has cleared off the band: twigs, bold closed capsules
    litter = [(-4.4, 3.4, 0.55), (4.3, 3.6, 0.6), (-0.4, 4.4, 0.45), (5.0, -1.4, 0.5), (-4.9, -1.3, 0.5),
              (0.5, 1.15, 0.4), (-0.6, -2.3, 0.5), (3.3, -2.5, 0.4), (-2.6, 1.0, 0.3), (1.9, 4.6, 0.4)]
    for x, z, s in litter:
        rot = r() * math.pi
        ux, uz = math.cos(rot), math.sin(rot)
        tw = 0.07
        cap = ([(x + ux * s + tw * math.cos(t) * ux - tw * math.sin(t) * uz, z + uz * s + tw * math.cos(t) * uz + tw * math.sin(t) * ux)
                for t in [-math.pi / 2 + math.pi * i / 6 for i in range(7)]]
               + [(x - ux * s + tw * math.cos(t) * ux - tw * math.sin(t) * uz, z - uz * s + tw * math.cos(t) * uz + tw * math.sin(t) * ux)
                  for t in [math.pi / 2 + math.pi * i / 6 for i in range(7)]])
        F.shape([G(p) for p in cap], G4, LINE)

    # the band: outer edge brightest, inner edge one step down
    F.shape([G(p) for p in outer], G0, 2.5, bound=True)
    F.shape([G(p) for p in inner], G2, 2.0, bound=True)

    # stones of the lattice: those the phrase plays sit at the loop's outer edge
    def stone(x, z, s, edge, sw, ring2):
        pts = [(x + s * math.cos(t) * 1.15, z + s * math.sin(t) * 0.9) for t in [2 * math.pi * i / 16 for i in range(16)]]
        top = [G(p, 0.2) for p in pts]
        base = [G(p, 0.0) for p in pts]
        F.shape(hull(top + base), edge, sw)
        F.shape(top, G4 if ring2 else G5, LINE if ring2 else HAIR)

    cx = sum(p[0] for p in stations) / len(stations)
    cz = sum(p[1] for p in stations) / len(stations)
    placed = []
    for sx, sz in stations:
        dx, dz = sx - cx, sz - cz
        L = math.hypot(dx, dz) or 1
        placed.append((sx + dx / L * (half + 0.32), sz + dz / L * (half + 0.32)))
    spare = [(-4.7, 1.9), (-0.9, 1.3), (1.2, 0.4), (4.9, 1.7), (0.6, -2.0), (-1.2, 3.9)]
    for x, z in sorted(placed + spare, key=lambda p: -p[1]):
        on = (x, z) in placed
        stone(x, z, 0.3 if on else 0.24, G2 if on else G4, 2.0 if on else LINE, on)

    # seeds carried round the loop, one per ant
    for k in range(N_ANTS):
        p, ang = point_along(centre + [centre[0]], 0.06 + k / N_ANTS)
        seed = [(p[0] + 0.17 * math.cos(t) * math.cos(ang) - 0.09 * math.sin(t) * math.sin(ang),
                 p[1] + 0.17 * math.cos(t) * math.sin(ang) + 0.09 * math.sin(t) * math.cos(ang))
                for t in [2 * math.pi * i / 14 for i in range(14)]]
        F.shape([G(q, 0.05) for q in seed], G1, LINE, bound=True)
    return F


def main() -> None:
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        F = fn()
        (HERE / name).mkdir(exist_ok=True)
        (HERE / name / "rest.svg").write_text(F.svg())
        print(name, "bound nodes", F.node, "elements", len(F.out))


if __name__ == "__main__":
    main()
