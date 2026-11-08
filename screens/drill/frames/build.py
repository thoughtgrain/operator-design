#!/usr/bin/env python3
"""drill · refined subject (pass 02, v3): a carpenter's brace boring a board.

The owner picked v3 and asked for it "more refined, and readable visually".
This builder models the brace in 3D (world units are millimetres) and projects
every point through one orthographic camera, yawed 18 deg and raised 8 deg so the
turned parts show their ends and the bow's sweep reads as a sweep:

  head pad + knob neck · swept bow (two bends each side) · turned grip on the throw
  · ratchet collar with its cam ring · chuck shell and jaws · auger bit (shank,
  core, twist lands, spurs, cutting lips, lead screw) · board in section

Drawing language: detailed line art (craft.md, Think in 3D): black-filled solids,
outer edges at Line weight in a mid grey, inner detail (turned grooves, knurl,
cam ribs) at Hairline, a highlight streak on every turned part from the same
light (upper left, towards the camera). One brightest element: the auger's
twist and cutting head (#CDCDCD), the part the sound comes from.

Controls (others at default):
  ratio  the bow's throw (sweep), 32 -> 118 mm, so the grip and its ferrules drop
         ~58 px; on a note the crank also turns faster at higher ratio
  teeth  turns of the auger's twist, 3 -> 24 lands over its length (count)
  wear   the cutting head blunts (spurs and lead screw pull back), the lands thin
         and their lower corners wear back
  bite   the whole brace slides along its axis into the board, the bit sinking
         from just the screw (bite 0) to 74 mm deep (bite 100); the bore follows

Device plan (paths = mutable outlines, 64 points each, within +-64 px of origin):
  path 0 bow rod · path 1 twist lands, left half · path 2 twist lands, right half
  + cutting head · path 3 the bore (black fill erases the grain it cuts)
Everything else is a static node that only translates (bite, and the grip on a
note).

Run: python3 screens/drill/frames/build.py [--style line|edgelit] [--gif] [--trial]
"""
from __future__ import annotations

import argparse
import math
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

G = {0: "#000000", 1: "#323232", 2: "#4B4B4B", 3: "#646464", 4: "#7D7D7D",
     5: "#969696", 6: "#AFAFAF", 7: "#CDCDCD"}
BLACK, BRIGHT = G[0], G[7]
HAIR, LINE, SUBJ = 1.0, 1.5, 2.2
BODY_TOP = 22

DEFAULTS = {"ratio": 0.5, "teeth": 0.15, "wear": 0.0, "bite": 0.35}
TEETH_LABELS = [str(n) for n in range(3, 25)]


def ratio_value(v): return 0.5 * 16 ** v
def teeth_value(v): return int(TEETH_LABELS[min(len(TEETH_LABELS) - 1, int(v * len(TEETH_LABELS)))])


def header_values(c):
    return [f"{ratio_value(c['ratio']):.2f}", TEETH_LABELS[min(21, int(c['teeth'] * 22))],
            f"{round(c['wear'] * 100)}", f"{round(c['bite'] * 100)}"]   # ux.md: amounts without %


# ------------------------------------------------------------- vectors ----
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def mul(a, k): return (a[0] * k, a[1] * k, a[2] * k)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def norm(a):
    ln = math.sqrt(dot(a, a)) or 1.0
    return mul(a, 1 / ln)


class Ortho:
    """One orthographic camera: world z up, x along the brace; screen y grows down."""

    def __init__(self, yaw_deg, elev_deg, scale, cx, cy):
        s, c = math.sin(math.radians(yaw_deg)), math.cos(math.radians(yaw_deg))
        se, ce = math.sin(math.radians(elev_deg)), math.cos(math.radians(elev_deg))
        self.right = (c, -s, 0.0)
        self.fwd = (s * ce, c * ce, -se)
        self.up = (s * se, c * se, ce)
        # roll the camera so the brace's axis (world x) lies level on screen
        rho = math.atan2(dot((1, 0, 0), self.up), dot((1, 0, 0), self.right))
        cr, sr = math.cos(rho), math.sin(rho)
        r0, u0 = self.right, self.up
        self.right = add(mul(r0, cr), mul(u0, sr))
        self.up = add(mul(r0, -sr), mul(u0, cr))
        self.k, self.cx, self.cy = scale, cx, cy

    def __call__(self, p):
        return (self.cx + self.k * dot(p, self.right), self.cy - self.k * dot(p, self.up))

    def proj(self, pts):
        return [self(p) for p in pts]

    def facing(self, n):
        return dot(n, self.fwd) < 0


# ------------------------------------------------------------- svg --------
def f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def dedupe(pts, closed=True, gap=0.4):
    o = [pts[0]]
    for p in pts[1:]:
        if math.dist(p, o[-1]) > gap:
            o.append(p)
    while closed and len(o) > 3 and math.dist(o[-1], o[0]) < 0.6:
        o.pop()
    return o


def normal2(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy) or 1
    return (-dy / ln, dx / ln)


def offset(pts, h):
    """Offset an open polyline by h px (mitred, flat ends)."""
    n = len(pts)
    out = []
    for j in range(n):
        ns = []
        if j > 0:
            ns.append(normal2(pts[j - 1], pts[j]))
        if j < n - 1:
            ns.append(normal2(pts[j], pts[j + 1]))
        nx = sum(a for a, _ in ns); ny = sum(b for _, b in ns)
        ln = math.hypot(nx, ny) or 1
        nx, ny = nx / ln, ny / ln
        m = 1.0
        if len(ns) == 2:
            c = ns[0][0] * nx + ns[0][1] * ny
            m = min(1 / max(c, 0.35), 2.5)
        out.append((pts[j][0] + nx * h * m, pts[j][1] + ny * h * m))
    return out


class Svg:
    """Named elements, so frames can be diffed node by node (redraw estimate)."""

    def __init__(self):
        self.parts: list[tuple[str, str]] = []
        self.npts: dict[str, int] = {}

    def path(self, name, pts, fill, stroke, sw, limit=64):
        pts = dedupe(pts)
        if len(pts) < 3:
            return
        if len(pts) > limit:
            raise ValueError(f"{name}: outline with {len(pts)} points")
        self.npts[name] = len(pts)
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
        self.parts.append((name, f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'))

    def ribbon(self, name, pts, width, col):
        """An open polyline as a thin closed ribbon (never a stroke traced back)."""
        pts = dedupe(pts, closed=False)
        if len(pts) < 2:
            return
        step, i, k = 28, 0, 0
        while i < len(pts) - 1:
            chunk = pts[i:i + step + 1]
            h = max(width - 0.3, 0.4) / 2
            self.path(f"{name}.{k}", offset(chunk, h) + offset(chunk, -h)[::-1], col, col, 0.3)
            i += step; k += 1

    def write(self, path: Path, title: str, values):
        tmpl = (ROOT / "opxy" / "templates" / "frame.svg").read_text()
        head = tmpl.split("  <!-- Palette entries")[0]
        head = head.split("<!--", 1)[0] + head.split("-->", 1)[1].lstrip("\n")
        titles = iter(["ratio", "teeth", "wear", "bite"])
        for p in ("p1", "p2", "p3", "p4"):
            head = head.replace(f">{p}</text>", f">{next(titles)}</text>", 1)
        parts = head.split('font-size="20px">0</text>')
        head = parts[0] + "".join(f'font-size="20px">{v}</text>' + rest for v, rest in zip(values, parts[1:]))
        pal = ('  <path id="drill_palette_0" d="M 700 300 L 704 300 L 704 304 Z" fill="#CDCDCD" stroke="#CDCDCD" stroke-width="2"/>\n'
               '  <path id="drill_palette_1" d="M 710 300 L 714 300 L 714 304 Z" fill="#646464" stroke="#646464" stroke-width="2"/>\n')
        body = "\n".join("  " + p for _, p in self.parts)
        path.write_text(head.rstrip() + f"\n  <title>{title}</title>\n" + pal + body + "\n</svg>\n")


# ------------------------------------------------------------- geometry ---
def ring(c, r, n=24):
    return [add(c, (0, r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n))) for i in range(n)]


def clip_x(poly, x0, keep_greater=True):
    """Sutherland-Hodgman on a 2D (x, *) polygon against the line x = x0."""
    out = []
    n = len(poly)
    inside = (lambda p: p[0] >= x0) if keep_greater else (lambda p: p[0] <= x0)
    for i in range(n):
        a, b = poly[i - 1], poly[i]
        ia, ib = inside(a), inside(b)
        if ib:
            if not ia:
                t = (x0 - a[0]) / (b[0] - a[0]); out.append((x0, a[1] + (b[1] - a[1]) * t))
            out.append(b)
        elif ia:
            t = (x0 - a[0]) / (b[0] - a[0]); out.append((x0, a[1] + (b[1] - a[1]) * t))
    return out


class Scene:
    YAW, ELEV = 18.0, 8.0
    LIGHT = norm((0, -0.42, 0.91))          # streaks sit on the upper, camera-side face

    # brace and bit, along x (mm), before the bite offset
    NECK_END, RATCHET_START = 55.0, 250.0
    GRIP0, GRIP1 = 102.0, 204.0
    X_TWIST0, X_E = 386.0, 610.0             # twist from the shank's throat to the cutting head
    R_TWIST, R_CORE, R_SHANK = 15.0, 5.2, 5.6
    BOARD_W, BOARD_H, BOARD_D = 100.0, 108.0, 44.0
    R_BORE = 17.0                            # a little over the spurs, so the bore wall clears the bit by ~1 px

    def __init__(self, c, theta=0.0, style="line"):
        self.c, self.theta, self.style = c, theta, style
        self.ratio_n = c["ratio"]
        self.teeth = teeth_value(c["teeth"])
        self.wear = c["wear"]
        self.bite = c["bite"]
        self.T = 32 + 86 * self.ratio_n                       # the bow's throw (mm)
        self.depth = -6 + 80 * self.bite                      # cutting head past the board's face
        self.F = self.X_E + 6                                 # board face, world x
        self.dx = self.F - self.X_E + self.depth - 6 + 6      # brace offset so x_e lands at F + depth
        self.dx = (self.F + self.depth) - self.X_E
        self.cam = Ortho(self.YAW, self.ELEV, 0.67, 0, 117)
        # place the scene: head pad's left edge at bite 0 sits ~9 px in from the left
        x_left = min(self.cam((0 + (self.F - 6) - self.X_E, 0, z))[0] for z in (-35, 35))
        self.cam.cx = 9 - x_left + 2
        self.s = Svg()

    # -- projections ------------------------------------------------------
    def P(self, p):
        return self.cam(p)

    def B(self, x, y=0.0, z=0.0):
        """A point on the brace (moves with bite)."""
        return self.cam((x + self.dx, y, z))

    def axis_perp(self):
        a, b = self.cam((0, 0, 0)), self.cam((1, 0, 0))
        d = (b[0] - a[0], b[1] - a[1]); ln = math.hypot(*d)
        d = (d[0] / ln, d[1] / ln)
        n = (d[1], -d[0])
        if n[1] > 0:
            n = (-n[0], -n[1])
        return d, n

    # -- solids of revolution ------------------------------------------------
    def revolve(self, profile, yc=0.0, zc=0.0, n=24, move=True):
        """Outline of a turned part about the line (y=yc, z=zc) along x: top and bottom
        extremes along the profile, plus the outer halves of the two end discs."""
        d, up = self.axis_perp()
        ox = self.dx if move else 0.0
        tops, bots, rings = [], [], []
        for x, r in profile:
            c3 = (x + ox, yc, zc)
            cs = self.cam(c3)
            pts = self.cam.proj(ring(c3, r, n))
            ds = [(p[0] - cs[0]) * up[0] + (p[1] - cs[1]) * up[1] for p in pts]
            it, ib = ds.index(max(ds)), ds.index(min(ds))
            tops.append(pts[it]); bots.append(pts[ib]); rings.append((pts, it, ib, cs))

        def half(entry, outer_sign):
            pts, it, ib, cs = entry
            arcs = []
            for step in (1, -1):
                arc, i = [pts[ib]], ib
                while i != it:
                    i = (i + step) % n; arc.append(pts[i])
                mid = arc[len(arc) // 2]
                side = (mid[0] - cs[0]) * d[0] + (mid[1] - cs[1]) * d[1]
                arcs.append((side * outer_sign, arc))
            return max(arcs)[1]          # bottom -> top, on the outer side

        left = half(rings[0], -1)
        right = half(rings[-1], +1)
        return tops + right[::-1][1:-1] + bots[::-1] + left[1:-1]

    def ring_arc(self, x, r, yc=0.0, zc=0.0, n=32, move=True):
        """The camera-facing half of a ring on a turned part (a groove, a step)."""
        c3 = ((x + (self.dx if move else 0)), yc, zc)
        pts, out = ring(c3, r, n), []
        k0 = None
        flags = [self.cam.facing(sub(p, c3)) for p in pts]
        start = flags.index(False) if False in flags else 0
        for k in range(n + 1):
            i = (start + k) % n
            if flags[i]:
                out.append(self.cam(pts[i]))
        return out

    def streak(self, profile, yc=0.0, zc=0.0, inset=1, k=0.97, move=True):
        ox = self.dx if move else 0.0
        pts = [self.cam(add((x + ox, yc, zc), mul(self.LIGHT, r * k))) for x, r in profile[inset:len(profile) - inset]]
        return pts

    # -- drawing helpers ----------------------------------------------------
    def solid(self, name, pts, edge=G[5], w=LINE):
        if self.style == "edgelit":
            self.s.path(name, pts, BLACK, G[2], HAIR)
            lit_edges(self.s, name + ".lit", pts, BRIGHT, SUBJ)
        else:
            self.s.path(name, pts, BLACK, edge, w)

    def detail(self, name, pts, col=G[3], w=HAIR):
        if self.style == "edgelit":
            return
        self.s.ribbon(name, pts, w, col)

    # ======================================================================
    def board(self):
        F, W, H, D = self.F, self.BOARD_W, self.BOARD_H, self.BOARD_D
        edge = G[4]
        top = [(F, 0, H), (F + W, 0, H), (F + W, D, H), (F, D, H)]
        # the face the bit enters (far half; the near half is cut away): its half hole
        hole = [(F, self.R_BORE * math.sin(math.pi * i / 12), -self.R_BORE * math.cos(math.pi * i / 12)) for i in range(13)]
        entry = [(F, 0, H), (F, D, H), (F, D, -H), (F, 0, -H)] + hole
        self.s.path("board.top", self.cam.proj(top), BLACK, G[3], LINE)
        self.s.path("board.entry", self.cam.proj(entry), BLACK, G[3], LINE)
        # the bore's far wall, seen through the mouth: one ring edge a little way in
        sect = [(F, 0, H), (F + W, 0, H), (F + W, 0, -H), (F, 0, -H)]
        self.s.path("board.section", self.cam.proj(sect), BLACK, edge, LINE)
        # grain in the cut face: the plank's length runs up and down, so the bore cuts across it
        xs = [F + 9 + i * (W - 18) / 9 for i in range(10)]
        for i, x in enumerate(xs):
            pts = []
            for j in range(13):
                z = -H + 6 + (2 * H - 12) * j / 12
                pts.append((x + 1.6 * math.sin(j * 0.8 + i * 1.7) + 0.9 * math.sin(j * 2.1 + i), 0, z))
            self.s.ribbon(f"board.grain{i}", self.cam.proj(pts), HAIR, G[2])

    def bore(self):
        """Path 3: the bore cut so far, black (it erases the grain it crosses), edged like the cut."""
        F = self.F
        xe = self.X_E + self.dx
        Rb = self.R_BORE
        ls, lsc, blunt, _ = self.tip_dims()
        # the floor follows the cutting head: spur grooves at the rim, the lips' cone, the screw's hole
        half = [(xe + ls + 1.2, Rb - 0.6), (xe + ls + 1.2, Rb - 3.6), (xe + 4.5, 6.2)]
        for i, (x, r) in enumerate(self.screw_profile()):
            half.append((x + 1.0, r + 0.9))
        poly2 = [(F - 3, Rb)] + half + [(x, -z) for x, z in half[::-1]] + [(F - 3, -Rb)]
        poly2 = clip_x(poly2, F, True)
        if len(poly2) < 3:
            return
        # subdivide the walls so the path carries the frame's one point count on device (64)
        self.s.path("bore", self.cam.proj([(x, 0, z) for x, z in poly2]), BLACK, G[4], LINE)

    # -- the auger -----------------------------------------------------------
    def tip_dims(self):
        w = self.wear
        spur = 10.0 * (1 - w) + 1.0          # spur length past the lips
        screw = 18.0 * (1 - 0.62 * w) + 1.0  # lead screw length
        blunt = 0.5 + 2.6 * w               # flat at the screw's point
        thread = 1.4 * (1 - 0.8 * w)        # thread depth
        return spur, screw, blunt, thread

    def screw_profile(self):
        """The lead screw's upper edge, from base to point (x, r)."""
        _, ls, blunt, th = self.tip_dims()
        xe = self.X_E + self.dx
        x0, r0 = xe + 4.5, 4.6
        # one and a half threads, then the point (kept short: the head shares path 2 with the lands)
        t1, t2, t3 = 0.2, 0.5, 0.72
        return [(x0 + ls * t1, r0 * (1 - t1) + blunt / 2 * t1 + th),
                (x0 + ls * t2, r0 * (1 - t2) + blunt / 2 * t2 - 0.1),
                (x0 + ls * t3, r0 * (1 - t3) + blunt / 2 * t3 + th * 0.6),
                (x0 + ls, blunt / 2)]

    def cutting_head(self):
        """Upper half of the head, from the twist's end round to the screw's point (x, z)."""
        xe = self.X_E + self.dx
        R = self.R_TWIST
        ls, _, _, _ = self.tip_dims()
        rw = 1.6 * self.wear
        pts = [(xe, R), (xe + ls, R - 1.0 - rw), (xe + 1.8, R - 4.2), (xe + 4.5, 5.6)]
        return pts + self.screw_profile()

    def twist(self):
        """Paths 1 and 2: the lands, hanging from a lit top edge, crawling as the bit turns."""
        cam = self.cam
        R = self.R_TWIST
        x0, xe = self.X_TWIST0 + self.dx, self.X_E + self.dx
        L = xe - x0 - 2.0
        n = self.teeth
        p = L / n
        land = p * (0.48 - 0.2 * self.wear)    # wear: the lands thin as they're worn back
        phase = (-self.theta / (2 * math.pi)) % 1.0       # lands crawl back towards the chuck as it bores
        d, up = self.axis_perp()
        k = cam.k
        under = R * k - 1.7                                # the top edge's underside, px from the axis

        def axis_pt(x):
            return cam((x, 0, 0))

        def perp_of(pt, x):
            a = axis_pt(x)
            return (pt[0] - a[0]) * up[0] + (pt[1] - a[1]) * up[1]

        def to_screen(x, t):
            ph = math.pi / 2 + math.pi * t
            pt = cam((x, R * math.cos(ph), R * math.sin(ph)))
            # clamp under the top edge
            o = perp_of(pt, x)
            if o > under - 1.2:          # near the top edge: treat as attached
                return (pt[0] - up[0] * (o - under), pt[1] - up[1] * (o - under)), True
            return pt, False

        def top_pt(x, o):
            a = axis_pt(x)
            return (a[0] + up[0] * o, a[1] + up[1] * o)

        # each land in (x, t) space: t = 0 at the top edge, 1 at the bottom silhouette
        lands = []
        for i in range(-1, n + 1):
            xl = x0 + 1.0 + (i + phase) * p
            poly = [(xl, 0.0), (xl + land, 0.0), (xl + land + p / 2, 1.0), (xl + p / 2, 1.0)]
            poly = clip_x(poly, x0 + 1.0, True)
            if len(poly) >= 3 and not any(q[1] <= 1e-6 for q in poly):
                # the land's top is behind the throat: hang what's left from the throat's corner
                on = [j for j, q in enumerate(poly) if abs(q[0] - (x0 + 1.0)) < 1e-6]
                if on:
                    j = min(on, key=lambda j: poly[j][1])
                    poly[j] = (x0 + 1.0, 0.0)
            if len(poly) >= 3:
                poly = clip_x(poly, xe - 1.6, False)
            if len(poly) >= 3 and max(q[0] for q in poly) - min(q[0] for q in poly) > 0.8:
                lands.append(poly)
        head = [cam((x, 0, z)) for x, z in self.cutting_head()]
        head = head + [cam((x, 0, -z)) for x, z in self.cutting_head()[::-1]][1:]
        budget = 64
        mins = [len(self.land_outline(poly, to_screen, 0)) for poly in lands]
        fixed = [4, 4 + len(head)]
        half = None
        for h in range(len(lands), -1, -1):
            if fixed[0] + sum(mins[:h]) <= budget and fixed[1] + sum(mins[h:]) <= budget:
                half = h
                break
        if half is None:
            raise ValueError(f"twist: {len(lands)} lands don't fit two 64-point outlines")
        # balance: move lands to B while both still fit and A is the fuller one
        while half > 1 and fixed[0] + sum(mins[:half]) - mins[half - 1] >= fixed[1] + sum(mins[half - 1:]) - 4 \
                and fixed[1] + sum(mins[half - 1:]) <= budget:
            half -= 1
        groups = [lands[:half], lands[half:]]

        def top_x(poly, fn):
            xs = [q[0] for q in poly if q[1] <= 1e-6] or [q[0] for q in poly]
            return fn(xs)
        x_mid = top_x(lands[half - 1], max) + 0.5 * (p - land) if half > 0 else x0
        if half < len(lands):
            x_mid = min(x_mid, (top_x(lands[half - 1], max) + top_x(lands[half], min)) / 2)

        for gi, grp in enumerate(groups):
            xa = x0 if gi == 0 else x_mid
            xb = x_mid if gi == 0 else xe
            spare = budget - fixed[gi] - sum(mins[:half] if gi == 0 else mins[half:])
            extra = spare // max(1, len(grp))
            # edge samples per land: corners + curved edges
            pts = [top_pt(xa, R * k)]
            if gi == 0:
                pts = [top_pt(xa, under), top_pt(xa, R * k)]
            pts.append(top_pt(xb, R * k))
            if gi == 1:
                pts += head
                pts.append(top_pt(xb, -R * k + 0.0))        # the head's back face, up to the top edge
                pts[-1] = cam((xe, 0, -R))
            pts.append(top_pt(xb, under))
            for poly in grp[::-1]:
                pts += self.land_outline(poly, to_screen, extra)
            pts.append(top_pt(xa, under) if gi == 1 else top_pt(xa + 0.01, under))
            pts = tidy(pts)
            name = f"twist{'AB'[gi]}"
            col = BRIGHT
            if self.style == "edgelit":
                self.s.path(name, pts, BLACK, G[3], HAIR)
            else:
                self.s.path(name, pts, BLACK, col, LINE)

    def land_outline(self, poly, to_screen, budget):
        """A land, traversed from its top-right corner (under the top edge) down, across
        the bottom and back up: right edge, bottom, left edge. Wear rounds the bottom corners."""
        # poly in (x, t); find its corners in order: top edge (t=0) from right to left is the
        # attachment to the spine, so walk the rest of the outline from top-right to top-left.
        n = len(poly)
        # rotate so we start just after the top edge's right end
        tops = [i for i, q in enumerate(poly) if q[1] <= 1e-6]
        if len(tops) >= 2:
            # top edge between two t=0 vertices; start at the right one
            ir = max(tops, key=lambda i: poly[i][0])
            seq = [poly[(ir + j) % n] for j in range(n)]
            # direction: next vertex should go downwards (t increasing)
            if seq[1][1] <= 1e-6:
                seq = [seq[0]] + seq[1:][::-1]
            seq = seq[:]  # ends at the top-left vertex
        elif len(tops) == 1:
            i0 = tops[0]
            seq = [poly[(i0 + j) % n] for j in range(n)]
            if seq[1][0] < seq[-1][0]:
                seq = [seq[0]] + seq[1:][::-1]
            # ends on the throat line; the comb closes up it to the top edge
        else:
            seq = poly[:]
        # sample the edges
        E = len(seq) - 1
        curved = sum(1 for j in range(E) if abs(seq[j + 1][1] - seq[j][1]) > 0.05)
        per_edge = 1 + max(0, budget) // max(1, curved)
        out = []
        wr = 0.75 * self.wear
        for j in range(len(seq) - 1):
            a, b = seq[j], seq[j + 1]
            m = per_edge if abs(b[1] - a[1]) > 0.05 else 1
            for i in range(m):
                t = i / m
                x = a[0] + (b[0] - a[0]) * t
                tt = a[1] + (b[1] - a[1]) * t
                out.append((x, tt))
        out.append(seq[-1])
        # wear: pull the bottom corners up and in (a rounded, worn land)
        if wr > 0:
            res = []
            for x, t in out:
                if t > 1 - wr * 0.6:
                    t = 1 - wr * 0.6 + (t - (1 - wr * 0.6)) * 0.35
                res.append((x, t))
            out = res
        scr = [to_screen(x, t) for x, t in out]
        # where the edges run up under the top edge, keep one attachment point per edge
        # (a run of clamped points would fold back along the underside)
        i0 = 0
        while i0 + 1 < len(scr) and scr[i0][1] and scr[i0 + 1][1]:
            i0 += 1
        i1 = len(scr) - 1
        while i1 - 1 > i0 and scr[i1][1] and scr[i1 - 1][1]:
            i1 -= 1
        return [q for q, _ in scr[i0:i1 + 1]]

    def bit_static(self):
        R = self.R_TWIST
        # shank, from the jaws to the throat of the twist
        prof = [(350, self.R_SHANK), (self.X_TWIST0 - 9, self.R_SHANK), (self.X_TWIST0 - 4, self.R_SHANK + 0.6), (self.X_TWIST0 + 1, self.R_CORE + 2.2)]
        self.solid("shank", self.revolve(prof, n=16), edge=G[5])
        self.detail("shank.streak", self.streak(prof, inset=0, k=0.6), G[4])
        # the core, seen between the lands
        core = [(self.X_TWIST0, self.R_CORE), (self.X_E, self.R_CORE)]
        if self.style == "line":
            self.s.path("core", self.revolve(core, n=16), BLACK, G[3], HAIR)

    # -- the brace -------------------------------------------------------------
    def head(self):
        pad = [(0, 17), (1.2, 25), (3.5, 30.5), (8, 34), (15, 35.5), (23, 35), (29, 32), (33, 27), (35.5, 20), (37, 13)]
        neck = [(36, 9.5), (38, 9.5), (39.5, 11.5), (45, 11.5), (46.5, 9.5), (self.NECK_END, 8.6)]
        self.solid("head.pad", self.revolve(pad, n=28))
        self.detail("head.dome", self.ring_arc(1.2, 25), G[3])
        self.detail("head.streak", self.streak(pad, inset=2, k=0.95), G[4])
        self.solid("head.neck", self.revolve(neck, n=20))
        self.detail("head.bead", self.ring_arc(39.5, 11.5, n=24), G[3])

    def bow_centerline(self):
        """The bow's centreline in its own plane: (x, u), u the distance from the axis."""
        T = self.T
        corners = [(self.NECK_END - 1, 0), (74, 0), (96, T), (210, T), (232, 0), (self.RATCHET_START + 1, 0)]
        rad = [0, 15, 15, 15, 15, 0]
        out = [corners[0]]
        for i in range(1, len(corners) - 1):
            a, b, c = corners[i - 1], corners[i], corners[i + 1]
            r = rad[i]
            u1 = norm((a[0] - b[0], a[1] - b[1], 0)); u2 = norm((c[0] - b[0], c[1] - b[1], 0))
            ang = math.acos(max(-1, min(1, u1[0] * u2[0] + u1[1] * u2[1])))
            tlen = r / math.tan(ang / 2)
            p = (b[0] + u1[0] * tlen, b[1] + u1[1] * tlen)
            q = (b[0] + u2[0] * tlen, b[1] + u2[1] * tlen)
            for j in range(6):
                t = j / 5
                x = (1 - t) ** 2 * p[0] + 2 * (1 - t) * t * b[0] + t * t * q[0]
                y = (1 - t) ** 2 * p[1] + 2 * (1 - t) * t * b[1] + t * t * q[1]
                out.append((x, y))
        out.append(corners[-1])
        return out

    def bow_dir(self):
        th = self.theta
        return (0.0, math.sin(th), -math.cos(th))

    def bow(self):
        """Path 0: the bow rod, a tube 15 mm across, projected from its centreline."""
        dvec = self.bow_dir()
        cl = [self.B(x, *mul(dvec, u)[1:]) for x, u in self.bow_centerline()]
        h = 8.0 * self.cam.k      # a 16 mm rod: ~11 px at 1:1
        pts = offset(cl, h) + offset(cl, -h)[::-1]
        self.solid("bow", pts)

    def grip(self):
        dvec = self.bow_dir()
        yc, zc = dvec[1] * self.T, dvec[2] * self.T
        g0, g1 = self.GRIP0, self.GRIP1
        prof = [(g0, 9), (g0 + 1.5, 14), (g0 + 5, 17), (g0 + 10, 18.2), (g0 + 20, 19), ((g0 + g1) / 2, 19.5),
                (g1 - 20, 19), (g1 - 10, 18.2), (g1 - 5, 17), (g1 - 1.5, 14), (g1, 9)]
        # the grip's two ferrules, metal collars it turns between
        for i, (xa, sg) in enumerate(((g0, -1), (g1, 1))):
            fer = sorted([(xa + sg * 0.5, 10.4), (xa + sg * 1.2, 12.2), (xa + sg * 5.2, 12.2), (xa + sg * 6.0, 10.4)])
            self.solid(f"grip.ferrule{i}", self.revolve(fer, yc, zc, n=20))
        self.solid("grip", self.revolve(prof, yc, zc, n=24))
        self.detail("grip.ring0", self.ring_arc(g0 + 9, 18.1, yc, zc), G[3])
        self.detail("grip.ring1", self.ring_arc(g1 - 9, 18.1, yc, zc), G[3])
        self.detail("grip.ring2", self.ring_arc(g0 + 15, 18.7, yc, zc), G[3])
        self.detail("grip.ring3", self.ring_arc(g1 - 15, 18.7, yc, zc), G[3])
        self.detail("grip.streak", self.streak(prof, yc, zc, inset=3, k=0.93), G[4])

    def ratchet_and_chuck(self):
        x0 = self.RATCHET_START
        collar = [(x0, 12), (x0 + 2, 14.5), (x0 + 9, 14.5), (x0 + 10, 18), (x0 + 24, 18), (x0 + 25, 15), (x0 + 33, 15),
                  (x0 + 35, 13.5)]
        self.solid("ratchet", self.revolve(collar, n=28))
        # the cam ring's ribs, hairlines across its front, >= 3 px apart
        if self.style == "line":
            d, up = self.axis_perp()
            for i, a in enumerate((-60, -30, 0, 30, 60)):
                ph = math.radians(180 + a)          # front of the ring faces -y
                r = 18
                yy, zz = r * math.cos(ph) * -1 * -1, r * math.sin(ph)
                yy = -r * math.cos(math.radians(a)); zz = r * math.sin(math.radians(a))
                self.s.ribbon(f"ratchet.rib{i}", [self.B(x0 + 11.5, yy, zz), self.B(x0 + 22.5, yy, zz)], HAIR, G[3])
            self.detail("ratchet.step", self.ring_arc(x0 + 2, 14.5), G[3])
        self.detail("ratchet.streak", self.streak(collar, inset=1, k=0.95), G[4])
        cx0 = x0 + 35
        shell = [(cx0, 13.5), (cx0 + 3, 17.5), (cx0 + 8, 19), (cx0 + 30, 18.6), (cx0 + 44, 15.5), (cx0 + 54, 11.8), (cx0 + 58, 10.6)]
        self.solid("chuck", self.revolve(shell, n=28))
        self.detail("chuck.bead0", self.ring_arc(cx0 + 8, 19), G[3])
        self.detail("chuck.bead1", self.ring_arc(cx0 + 44, 15.5), G[3])
        self.detail("chuck.streak", self.streak(shell, inset=1, k=0.95), G[4])
        # jaws: two wedges closing on the shank at the chuck's nose
        nx = cx0 + 58
        for i, sgn in enumerate((1, -1)):
            jaw = [(nx - 1, sgn * 10.2), (nx + 5, sgn * 8.6), (nx + 7.5, sgn * (self.R_SHANK + 0.6)),
                   (nx - 1, sgn * (self.R_SHANK + 0.6))]
            self.solid(f"jaw{i}", [self.B(x, 0, z) for x, z in jaw])

    # ======================================================================
    def draw(self):
        self.board()
        self.bore()
        self.bit_static()
        self.twist()
        toward = math.sin(self.theta) < -1e-6           # bow on the camera's side of the axis
        if not toward:
            self.bow(); self.grip()
        self.head()
        self.ratchet_and_chuck()
        if toward:
            self.bow(); self.grip()
        return self.s


def tidy(pts):
    """Device hygiene for the lands' outlines while they crawl: no repeated points and no
    hairpin turns (a sliver land clipped at the throat or the head can make either)."""
    out = []
    for q in pts:
        if all(math.dist(q, o) > 0.13 for o in out):
            out.append(q)
    changed = True
    while changed and len(out) > 4:
        changed = False
        for i in range(len(out)):
            a, b, c = out[i - 1], out[i], out[(i + 1) % len(out)]
            v1 = (b[0] - a[0], b[1] - a[1]); v2 = (c[0] - b[0], c[1] - b[1])
            l1, l2 = math.hypot(*v1), math.hypot(*v2)
            if l1 < 1e-9 or l2 < 1e-9:
                continue
            cosang = (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)
            if cosang < -0.996:          # within ~5 deg of straight back
                del out[i]; changed = True
                break
    return out


def lit_edges(svg, name, poly, col, width, light=(-0.45, -0.89), thresh=0.3):
    """Edge-lit trial only: the runs of a closed outline whose outward normal faces the light."""
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))
    sgn = 1 if area > 0 else -1
    n = len(poly)
    flags = []
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        nx, ny = (dy / ln) * sgn, (-dx / ln) * sgn
        flags.append(nx * light[0] + ny * light[1] > thresh)
    start = flags.index(False) if False in flags else 0
    run, k = [], 0
    for j in range(n):
        i = (start + j) % n
        if flags[i]:
            if not run:
                run = [poly[i]]
            run.append(poly[(i + 1) % n])
        elif run:
            svg.ribbon(f"{name}{k}", run, width, col); run = []; k += 1
    if run:
        svg.ribbon(f"{name}{k}", run, width, col)


# ------------------------------------------------------------- frames -----
def frame(c, theta=0.0, style="line"):
    return Scene(c, theta, style).draw()


def render_png(svg_path: Path, png_path: Path):
    subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", "-o", str(png_path), str(svg_path)], check=True)


def crank_motion(fps=25):
    """theta(t) for the preview: rest, a note held ~2.4 s, release coasting to the next
    bottom-dead-centre, rest. Speed follows ratio (more turns of the wheel, a faster crank)."""
    c = DEFAULTS
    w_play = 2 * math.pi * (0.55 + 0.6 * c["ratio"])      # rad/s at default: ~0.85 rev/s
    t_on, t_off, t_end = 0.4, 2.8, 4.6
    th, w, out = 0.0, 0.0, []
    dt = 1 / fps
    t = 0.0
    target = None
    while t < t_end:
        if t_on <= t < t_off:
            w += (w_play - w) * (1 - math.exp(-dt / 0.06))  # spins up in ~0.18 s
            th += w * dt
        elif t >= t_off:
            if target is None:
                # coast on, then settle at the next crank-down (gravity holds the bow below)
                target = (math.floor((th + w * 0.35) / (2 * math.pi)) + 1) * 2 * math.pi
            # critically damped approach to the target
            k = 9.0
            acc = k * k * (target - th) - 2 * k * w
            w += acc * dt
            th += w * dt
            if abs(target - th) < 0.004 and abs(w) < 0.02:
                th, w = target, 0.0
        out.append((t, th % (2 * math.pi) if t >= t_off and th == target else th, t_on <= t < t_off))
        t += dt
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", default="line", choices=["line", "edgelit"])
    ap.add_argument("--gif", action="store_true")
    ap.add_argument("--trial", action="store_true", help="also write the edge-lit rest to trial-edgelit.svg/png")
    args = ap.parse_args()

    out = HERE
    sets = [("rest", DEFAULTS)]
    for ctl in ("ratio", "teeth", "wear", "bite"):
        for v in (0, 50, 100):
            c = dict(DEFAULTS); c[ctl] = v / 100
            sets.append((f"{ctl}-{v}", c))
    for name, c in sets:
        svg = frame(c, 0.0, args.style)
        p = out / f"{name}.svg"
        svg.write(p, f"drill · the brace boring a board · {name}", header_values(c))
        render_png(p, out / f"{name}.png")
        print(p, sum(1 for _ in svg.parts), "elements")
    if args.trial:
        svg = frame(DEFAULTS, 0.0, "edgelit")
        svg.write(out / "trial-edgelit.svg", "drill · edge-lit trial", header_values(DEFAULTS))
        render_png(out / "trial-edgelit.svg", out / "trial-edgelit.png")
    make_sheets(out)
    if args.gif:
        make_gif(out)


def make_sheets(out: Path):
    """contact.png (rest, then each control at 0 / 50 / 100) and before-after.png, all at 1:1."""
    from PIL import Image, ImageDraw
    W, H, G, L = 480, 220, 8, 14
    im = Image.new("RGB", (3 * W + 4 * G, 5 * (L + H + G) + G), (38, 38, 38))
    d = ImageDraw.Draw(im)

    def put(name, x, y):
        d.text((x, y), name.replace("-", " "), fill=(200, 200, 200))
        im.paste(Image.open(out / f"{name}.png").convert("RGB"), (x, y + L))
    put("rest", G, G)
    for r, ctl in enumerate(("ratio", "teeth", "wear", "bite")):
        for k, v in enumerate((0, 50, 100)):
            put(f"{ctl}-{v}", G + k * (W + G), G + (r + 1) * (L + H + G))
    im.save(out / "contact.png")
    before = out.parent / "passes" / "02-subject" / "v3" / "rest.png"
    ba = Image.new("RGB", (2 * W + 3 * G, H + L + 2 * G), (38, 38, 38))
    d = ImageDraw.Draw(ba)
    d.text((G, G - 2), "before: pass 02 v3", fill=(200, 200, 200))
    d.text((2 * G + W, G - 2), "after: refined rest", fill=(200, 200, 200))
    ba.paste(Image.open(before).convert("RGB"), (G, G + L))
    ba.paste(Image.open(out / "rest.png").convert("RGB"), (2 * G + W, G + L))
    ba.save(out / "before-after.png")


def make_gif(out: Path):
    from PIL import Image
    tmp = out / "_gif"
    tmp.mkdir(exist_ok=True)
    frames, prev, changes = [], None, []
    for i, (t, th, held) in enumerate(crank_motion()):
        svg = frame(DEFAULTS, th)
        cur = dict(svg.parts)
        if prev is not None:
            changes.append((t, held, sum(1 for k in set(cur) | set(prev) if cur.get(k) != prev.get(k))))
        prev = cur
        p = tmp / f"f{i:03d}.svg"
        svg.write(p, "drill · motion", header_values(DEFAULTS))
        render_png(p, tmp / f"f{i:03d}.png")
        frames.append(Image.open(tmp / f"f{i:03d}.png").convert("L").convert("P"))
    frames[0].save(out / "motion.gif", save_all=True, append_images=frames[1:], duration=40, loop=0)
    shutil.rmtree(tmp)
    # redraw estimate from the sketch: elements that changed between consecutive frames
    playing = [n for t, h, n in changes if h or (t >= 2.8 and n > 0)]
    print("changed elements/frame while moving: avg %.1f peak %d over %d frames" %
          (sum(playing) / max(1, len(playing)), max(playing or [0]), len(playing)))
    print("tail:", [n for _, _, n in changes[-12:]])


if __name__ == "__main__":
    main()
