#!/usr/bin/env python3
"""Subject-pass sketches for ebb: five rest frames, one per direction.

    python3 screens/ebb/passes/01-subject/sketch.py

Writes v1..v5/rest.svg (480 x 220, stock header kept as preview scaffolding).
Every frame shows the defaults: tide 12 st, period 8.0 s, foam 0 %, scale maj,
not muted, no notes sounding. These are sketches for picking a subject, not
device frames: parts are static artwork (no bound nodes yet), so each
candidate argues its budget in its risks.

The rule all five draw (definition.json, brief.md):
    pitch(t) = mean + tide/2 * sin(2 pi t / period), quantised to the scale;
    near each turn (high and low water) foam scatters grace notes.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 480, 220

G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
FONT = "UniversNextPro-Light"

# defaults (definition.json)
TIDE = 12.0                       # semitones, 0.3333 of 0..36
PERIOD = 32 ** 0.6                # 8.0 s, exponential 1..32
FOAM = 0.0
SCALES = {
    "maj": [0, 2, 4, 5, 7, 9, 11],
    "min": [0, 2, 3, 5, 7, 8, 10],
    "dor": [0, 2, 3, 5, 7, 9, 10],
    "lyd": [0, 2, 4, 6, 7, 9, 11],
    "phr": [0, 1, 3, 5, 7, 8, 10],
    "pent": [0, 2, 4, 7, 9],
    "hira": [0, 2, 3, 7, 8],
}
SCALE = SCALES["maj"]
MEAN = 18.0                       # mid register, semitones above the bottom of the 3-octave span
HEADER = [("tide", "12"), ("period", "8.0s"), ("foam", "0"), ("scale", "maj")]


# ----------------------------------------------------------------- the rule
def degrees(scale=SCALE, top=36):
    out = []
    octave = 0
    while True:
        for s in scale:
            p = octave * 12 + s
            if p > top:
                return out
            out.append(p)
        octave += 1


def tide_pitch(t, tide=TIDE, period=PERIOD, phase=0.0):
    return MEAN + tide / 2 * math.sin(2 * math.pi * t / period + phase)


def quantise(p, scale=SCALE):
    ds = degrees(scale)
    return min(ds, key=lambda d: abs(d - p))


# ----------------------------------------------------------------- svg helpers
def f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def dedupe(pts):
    out = []
    for p in pts:
        if not out or math.dist(out[-1], p) >= 0.3:
            out.append(p)
    return out


def poly(pts, fill, stroke="none", sw=None):
    pts = dedupe(pts)
    if len(pts) > 2 and math.dist(pts[0], pts[-1]) < 0.3:
        pts = pts[:-1]
    d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
    s = f'<path d="{d}" fill="{fill}" stroke="{stroke}"'
    if stroke != "none":
        s += f' stroke-width="{sw}"'
    return s + "/>"


def rect(x, y, w, h, fill, stroke="none", sw=None):
    s = f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" fill="{fill}" stroke="{stroke}"'
    if stroke != "none":
        s += f' stroke-width="{sw}"'
    return s + "/>"


def circle(cx, cy, r, fill, stroke="none", sw=None):
    s = f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}" stroke="{stroke}"'
    if stroke != "none":
        s += f' stroke-width="{sw}"'
    return s + "/>"


def text(x, y, s, fill=G4, size=10):
    return (f'<text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{fill}" stroke="none" '
            f'font-family="{FONT}" font-size="{size}px">{s}</text>')


def _ribbon(pts, w):
    """Offset an open polyline both ways and close it: a filled ribbon of width w."""
    n = len(pts)
    left, right = [], []
    for i in range(n):
        if i == 0:
            dx, dy = pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]
            L = math.hypot(dx, dy)
            nx, ny, m = -dy / L, dx / L, 1.0
        elif i == n - 1:
            dx, dy = pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]
            L = math.hypot(dx, dy)
            nx, ny, m = -dy / L, dx / L, 1.0
        else:
            ax, ay = pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]
            bx, by = pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]
            la, lb = math.hypot(ax, ay), math.hypot(bx, by)
            n1 = (-ay / la, ax / la)
            n2 = (-by / lb, bx / lb)
            sx, sy = n1[0] + n2[0], n1[1] + n2[1]
            ls = math.hypot(sx, sy) or 1.0
            nx, ny = sx / ls, sy / ls
            cos = nx * n1[0] + ny * n1[1]
            m = min(1 / max(cos, 0.35), 2.5)
        h = w / 2 * m
        left.append((pts[i][0] + nx * h, pts[i][1] + ny * h))
        right.append((pts[i][0] - nx * h, pts[i][1] - ny * h))
    return left + right[::-1]


def line(pts, w, fill):
    """Open polyline as closed ribbons, chunked so each outline stays <= 62 points."""
    pts = dedupe(pts)
    out = []
    i = 0
    while i < len(pts) - 1:
        chunk = pts[i:i + 30]
        out.append(poly(_ribbon(chunk, w), fill))
        i += 29
    return "\n".join(out)


def seg(x0, y0, x1, y1, w, fill):
    return line([(x0, y0), (x1, y1)], w, fill)


def dashed(pts, w, fill, dash=4.0, gap=4.0):
    """Dashes along a polyline, each its own short ribbon."""
    out, cur, acc, on = [], [pts[0]], 0.0, True
    for a, b in zip(pts, pts[1:]):
        L = math.dist(a, b)
        t = 0.0
        while t < L:
            room = (dash if on else gap) - acc
            step = min(room, L - t)
            t += step
            acc += step
            p = (a[0] + (b[0] - a[0]) * t / L, a[1] + (b[1] - a[1]) * t / L)
            if on:
                cur.append(p)
            if acc >= (dash if on else gap) - 1e-9:
                if on and len(cur) > 1:
                    out.append(line(cur, w, fill))
                on, acc, cur = not on, 0.0, [p]
    if on and len(cur) > 1:
        out.append(line(cur, w, fill))
    return "\n".join(out)


def ellipse_pts(cx, cy, rx, ry, n=48, a0=0.0, a1=2 * math.pi):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / (n - 1 if a1 - a0 < 2 * math.pi else n)),
             cy + ry * math.sin(a0 + (a1 - a0) * i / (n - 1 if a1 - a0 < 2 * math.pi else n))) for i in range(n)]


def convex_hull(pts):
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in pts))

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


def header():
    steps = [G0, G1, G2, G3, G4, G5, G6, G7]
    out = ['<g id="preview_header">']
    for i, c in enumerate(steps):
        out.append(rect(i * 60, 0, 60, 20, c))
    for i, (label, value) in enumerate(HEADER):
        ink = "#CBCBCB" if i < 2 else G0
        out.append(text(5 + 120 * i, 10, label, ink, 10))
        out.append(text(65 + 120 * i, 17.44, value, ink, 20))
    out.append("</g>")
    return "\n".join(out)


def frame(body: list[str], note: str) -> str:
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        f"<!-- ebb, subject pass 01, {note}. Generated by sketch.py; defaults, rest, not muted. -->",
        '<g id="preview_canvas">', rect(0, 0, W, H, G0), "</g>",
        header(),
        *body,
        "</svg>",
    ])


# ======================================================== v1 · P13 capture · orthographic elevation
def v1():
    """A stepped sea wall in elevation. Each tread is one scale degree, its height the pitch.
    The water is the capture line: the highest tread it covers is the note that plays."""
    b = []
    ds = degrees()                      # 22 degrees over 3 octaves (maj)
    u = 4.0                             # px per semitone
    base = 184.0                        # tread of degree 0
    datum = 192.0
    x0, w = 54.0, 17.0
    ty = [base - p * u for p in ds]
    xr = x0 + len(ds) * w
    yw = base - MEAN * u                # still water at mean level
    yhw = base - (MEAN + TIDE / 2) * u
    ylw = base - (MEAN - TIDE / 2) * u

    # wall: one profile, solid black body
    prof = [(x0, datum)]
    for k, y in enumerate(ty):
        prof += [(x0 + k * w, y), (x0 + (k + 1) * w, y)]
    prof += [(xr, datum)]
    b.append(poly(prof, G0, G3, 1.5))
    # coursing: a joint under every riser, hairline
    for k in range(1, len(ds)):
        b.append(seg(x0 + k * w, ty[k - 1] + 3, x0 + k * w, datum - 1, 1, G1))

    # water: the region under the still level that the wall doesn't fill
    kc = next(k for k, y in enumerate(ty) if y < yw)      # first tread above water
    xc = x0 + kc * w
    water = [(24, yw), (xc, yw)]
    for k in range(kc - 1, -1, -1):
        water += [(x0 + (k + 1) * w, ty[k]), (x0 + k * w, ty[k])]
    water += [(x0, datum), (24, datum)]
    b.append(poly(water, G1))

    # tide marks painted on the wall face, and their range dimension
    for y, lab in ((yhw, "hw"), (ylw, "lw")):
        kx = next(k for k, ty_ in enumerate(ty) if ty_ < y)
        b.append(seg(24, y, x0 + kx * w, y, 1, G4))
        b.append(text(26, y - 3, lab, G4))
    xd = xr + 18
    b.append(seg(xd, yhw, xd, ylw, 1, G4))
    b.append(seg(xd - 4, yhw, xd + 4, yhw, 1, G4))
    b.append(seg(xd - 4, ylw, xd + 4, ylw, 1, G4))
    b.append(text(xd - 12, ylw + 14, "range", G4))

    # datum
    b.append(seg(20, datum, 460, datum, 1, G2))
    b.append(text(24, datum + 13, "datum", G3 if False else G4))

    # surface: swell ripple, wavelength from period
    lam = PERIOD * 7.5
    surf = [(x, yw + 1.2 * math.sin(2 * math.pi * (x - 24) / lam)) for x in [24 + i * 2 for i in range(int((xc - 24) / 2) + 1)]]
    surf[-1] = (xc, surf[-1][1])
    b.append(line(surf, 1.5, G5))

    # captured tread: the highest one under water, the brightest thing on screen
    k = kc - 1
    b.append(poly([(x0 + k * w + 1, ty[k]), (x0 + (k + 1) * w - 1, ty[k]),
                   (x0 + (k + 1) * w - 1, datum - 1), (x0 + k * w + 1, datum - 1)], "none", G7, 2))
    return frame(b, "v1 P13 capture, orthographic elevation")


# ======================================================== v2 · P14 loom · survey plan
def v2():
    """Four bars of the tide woven as rows of a surveyed sheet, newest at the front (bottom).
    Threads are the 16 steps of a bar; each note is a slab on its thread at its sounding."""
    b = []
    steps, bars = 16, 4
    dt = 4.0 / steps                    # 120 bpm: a row is two bars (4 s), a step an eighth
    xt = [126 + i * 21 for i in range(steps)]
    tops = [28 + r * 42 for r in range(bars)]
    rh = 40
    k = 1.0                             # px per semitone inside a row

    # neat line of the sheet
    nl = (112, 24, 454, 198)
    for a, c in (((nl[0], nl[1]), (nl[2], nl[1])), ((nl[2], nl[1]), (nl[2], nl[3])),
                 ((nl[2], nl[3]), (nl[0], nl[3])), ((nl[0], nl[3]), (nl[0], nl[1]))):
        b.append(seg(*a, *c, 1, G2))
    # warp threads (chainage lines)
    for x in xt:
        b.append(seg(x, 26, x, 196, 1, G1))

    ages = [(G3, 8, 3), (G4, 9, 3), (G5, 10, 3.5), (G7, 12, 4)]   # oldest to newest
    for r in range(bars):
        top = tops[r]
        bot = top + rh
        # row baseline and the mean-water contour, dashed
        b.append(seg(114, bot, 452, bot, 1, G2))
        ym = bot - 3 - MEAN * k
        b.append(dashed([(114, ym), (452, ym)], 1, G1, 3, 4))
        ink, sw, sh = ages[r]
        weft = []
        for i, x in enumerate(xt):
            t = (r * steps + i) * dt
            p = quantise(tide_pitch(t))
            weft.append((x, bot - 3 - p * k))
        # the weft: one hairline thread through the row's soundings, then the slabs on it
        b.append(line([(114, weft[0][1])] + weft + [(452, weft[-1][1])], 1, G2 if r < 3 else G3))
        for x, y in weft:
            b.append(rect(x - sw / 2, y - sh / 2, sw, sh, ink))
    b.append(text(118, tops[3] + 12, "now", G4))
    b.append(text(118, tops[0] + 12, "-12s", G4))
    b.append(text(xt[0] - 3, 210, "1", G4))
    b.append(text(xt[-1] - 6, 210, "16", G4))

    # scale bar: one octave, alternating blocks between the scale's degrees (6 px per semitone)
    sx, sy, u = 22, 186, 6
    edges = SCALE + [12]
    for j, (a, c) in enumerate(zip(edges, edges[1:])):
        if j % 2 == 0:
            b.append(rect(sx + a * u, sy, (c - a) * u, 5, G5))
        else:
            b.append(rect(sx + a * u + 0.5, sy + 0.5, (c - a) * u - 1, 4, G0, G5, 1))
    b.append(text(sx - 2, sy + 18, "0", G4))
    b.append(text(sx + 12 * u - 8, sy + 18, "12", G4))
    return frame(b, "v2 P14 loom, survey plan")


# ======================================================== v3 · P5 field and figure · patent section
def v3():
    """FIG. 1: a float in section riding the sea, its graduated spar passing a fixed index.
    The sea is the field, the float the figure, the notes it has read a strip along the bottom."""
    b = []
    hz = 60.0
    b.append(seg(20, hz, 460, hz, 1, G2))
    # field: receding swell lines, spacing and wavelength grow toward the viewer
    lam_front = PERIOD * 9.0
    ys = [66, 71, 77, 84, 93, 104, 118, 135, 156, 180]
    for y in ys:
        depth = (y - hz) / (ys[-1] - hz)
        lam = max(lam_front * depth, 8)
        amp = 0.5 + 2.0 * depth
        pts = [(x, y + amp * math.sin(2 * math.pi * (x - 240) / lam)) for x in range(20, 461, 2)]
        b.append(line(pts, 1, G2))

    # fixed pile with the index arm and the two stops (the tide's range)
    px = 334
    b.append(poly([(px, 30), (px + 10, 30), (px + 10, 190), (px, 190)], G0, G4, 1.5))
    u = 3.0
    deck = 116.0
    for dy in (-TIDE / 2 * u, TIDE / 2 * u):
        b.append(rect(px - 7, deck + dy - 2, 7, 4, G5))
    yi = 70.0
    b.append(seg(250, yi, px, yi, 1, G5))

    # spar with graduations at the scale's degrees (3 px per semitone)
    sx = 240
    b.append(poly([(sx - 3, 34), (sx + 3, 34), (sx + 3, deck), (sx - 3, deck)], G0, G5, 1.5))
    top_p = MEAN + (deck - 34) / u
    for p in degrees():
        y = deck - (p - (MEAN - 0)) * u - (deck - yi) + (deck - yi)  # spar reads MEAN at the index when still
        y = yi - (p - MEAN) * u
        if 38 < y < deck - 2:
            ln = 8 if p % 12 == 0 else 4
            b.append(seg(sx - 3 - ln, y, sx - 3, y, 1, G5))

    # float in section: hull outline, right half cut and hatched
    hull = []
    for i in range(25):
        a = math.pi * i / 24
        hull.append((sx + 30 * math.cos(a), deck + 4 + 26 * math.sin(a) ** 1.4))
    hull = [(sx - 30, deck), (sx + 30, deck)] + hull[1:-1][::-1][::-1]
    hull = [(sx + 30, deck)] + [(sx + 30 * math.cos(math.pi * i / 24), deck + 4 + 26 * math.sin(math.pi * i / 24) ** 1.4)
                                for i in range(1, 24)] + [(sx - 30, deck)]
    b.append(poly(hull, G0, G7, 2.5))
    # hatch the cut half at 45 degrees, 4 px apart, clipped to the hull
    def inside(x, y):
        if x < sx + 2 or y < deck + 2:
            return False
        dx = (x - sx) / 30
        if abs(dx) >= 1:
            return False
        a = math.acos(dx)
        return y < deck + 4 + 26 * math.sin(a) ** 1.4 - 2
    for c in range(-40, 80, 5):
        pts = []
        for s in range(0, 200):
            x = sx + c + s * 0.3
            y = deck + s * 0.3
            if inside(x, y):
                pts.append((x, y))
        if len(pts) > 6:
            b.append(seg(pts[0][0], pts[0][1], pts[-1][0], pts[-1][1], 1, G3))
    # waterline across the hull
    b.append(seg(sx - 34, deck + 10, sx + 34, deck + 10, 1, G4))

    # reference numerals and leaders
    for (lx, ly, tx, ty, n) in ((sx - 30, deck + 16, 168, 150, "10"),
                                (sx - 4, 50, 196, 46, "12"),
                                (300, yi, 300, 52, "14"),
                                (px - 6, deck - TIDE / 2 * u, 372, 92, "16")):
        b.append(seg(lx, ly, tx + (10 if tx < lx else -2), ty - 3, 1, G4))
        b.append(text(tx - (6 if tx < lx else -2), ty, n, G4))
    b.append(text(24, 214, "fig. 1", G4))

    # strip: the last notes read off the spar, oldest dim
    b.append(seg(120, 210, 400, 210, 1, G1))
    for i in range(28):
        t = (i - 27) * 0.25
        p = quantise(tide_pitch(t))
        hgt = 3 + (p - (MEAN - 6)) * 0.7
        b.append(rect(122 + i * 10, 209 - hgt, 2, hgt, G3))
    return frame(b, "v3 P5 field and figure, patent section")


# ======================================================== v4 · P12 orrery · hidden-line isometric
def v4():
    """The moon drawn round the earth, raising the water into a bulge that points at it.
    Bulge length is the tide, the moon's distance the period (Kepler), a pitch-class ring the scale."""
    b = []
    el = math.radians(35.26)
    sy = math.sin(el)
    cx, cy = 240.0, 116.0
    re = 26.0

    def P(X, Y):
        return (cx + X, cy + Y * sy)

    R = 80 + 44 * math.log(PERIOD) / math.log(32)
    ring = 66.0
    theta = math.radians(38)               # moon's place: the tide's phase
    a = re + 3 + TIDE * 0.9
    bb = re + 2

    def bulge(i, n=96):
        ph = 2 * math.pi * i / n
        X0, Y0 = a * math.cos(ph), bb * math.sin(ph)
        X = X0 * math.cos(theta) - Y0 * math.sin(theta)
        Y = X0 * math.sin(theta) + Y0 * math.cos(theta)
        return X, Y

    def runs(world, near):
        """Split a closed world polyline into runs on the near (Y > 0) or far side."""
        out, cur = [], []
        n = len(world)
        start = next(i for i in range(n) if (world[i][1] > 0) != near)
        for j in range(n + 1):
            X, Y = world[(start + j) % n]
            if (Y > 0) == near:
                cur.append(P(X, Y))
            elif cur:
                out.append(cur)
                cur = []
        if cur:
            out.append(cur)
        return out

    orbit = [(R * math.cos(2 * math.pi * i / 120), R * math.sin(2 * math.pi * i / 120)) for i in range(120)]
    ringw = [(ring * math.cos(2 * math.pi * i / 96), ring * math.sin(2 * math.pi * i / 96)) for i in range(96)]
    bul = [bulge(i) for i in range(96)]
    beads = []
    for pc in range(12):
        ph = -math.pi / 2 + 2 * math.pi * pc / 12
        beads.append((ring * math.cos(ph), ring * math.sin(ph), pc in SCALE))

    def bead(X, Y, on):
        x, y = P(X, Y)
        return circle(x, y, 3, G5 if on else G0, G5 if not on else "none", 1.5 if not on else None)

    # far side, back to front
    for r_ in runs(orbit, False):
        b.append(line(r_, 1, G3))
    for r_ in runs(ringw, False):
        b.append(line(r_, 1, G2))
    for X, Y, on in beads:
        if Y <= 0:
            b.append(bead(X, Y, on))
    # water: the prolate spheroid the moon pulls the sea into, as its hidden-line silhouette
    ce = math.cos(el)
    cloud = []
    for i in range(24):
        for j in range(1, 12):
            ph, th = 2 * math.pi * i / 24, math.pi * j / 12
            u, v, w_ = a * math.cos(th), bb * math.sin(th) * math.cos(ph), bb * math.sin(th) * math.sin(ph)
            X = u * math.cos(theta) - v * math.sin(theta)
            Y = u * math.sin(theta) + v * math.cos(theta)
            cloud.append((cx + X, cy + Y * sy - w_ * ce))
    for sgn in (1, -1):
        X, Y = sgn * a * math.cos(theta), sgn * a * math.sin(theta)
        cloud.append((cx + X, cy + Y * sy))
    hull = convex_hull(cloud)
    b.append(poly(hull, G0, G7, 2.5))
    # earth inside it, hidden: dashed, as a hidden-line drawing shows what's behind a surface
    b.append(dashed(ellipse_pts(cx, cy, re, re, 72) + [(cx + re, cy)], 1, G3, 3, 3))
    top = min(y for x, y in hull if abs(x - cx) < 4)
    b.append(seg(cx, top - 1.5, cx, top - 10, 1, G4))
    for r_ in runs(ringw, True):
        b.append(line(r_, 1, G2))
    for X, Y, on in beads:
        if Y > 0:
            b.append(bead(X, Y, on))
    for r_ in runs(orbit, True):
        b.append(line(r_, 1, G3))
    # moon: hidden-line sphere on its orbit, its equator as a hairline
    mx, my = P(R * math.cos(theta), R * math.sin(theta))
    mr = 9.0
    b.append(circle(mx, my, mr, G0, G5, 1.5))
    b.append(line(ellipse_pts(mx, my, mr - 1, (mr - 1) * sy, 24, 0, math.pi), 1, G3))
    # tie line from earth to moon: the axis the bulge follows, dashed
    tip = P(a * math.cos(theta), a * math.sin(theta))
    b.append(dashed([(tip[0] + 3, tip[1] + 2), (mx - mr * 0.8, my - mr * 0.5)], 1, G3, 3, 3))
    return frame(b, "v4 P12 orrery, hidden-line isometric")


# ======================================================== v5 · P10 voice field · star atlas
def v5():
    """A star chart of the rule: every (time, scale degree) cell is a star whose magnitude is
    how close the tide passes it, so the played notes form a sinuous ecliptic band."""
    b = []
    X0, X1, Y0, Y1 = 46.0, 452.0, 32.0, 190.0
    span = 16.0                            # seconds shown, now at the right
    py = (Y1 - Y0 - 8) / 36

    def sx(t):
        return X0 + (t + span) / span * (X1 - X0 - 10)

    def syp(p):
        return Y1 - 4 - p * py

    # neat line and graticule
    for a, c in (((X0, Y0), (X1, Y0)), ((X1, Y0), (X1, Y1)), ((X1, Y1), (X0, Y1)), ((X0, Y1), (X0, Y0))):
        b.append(seg(*a, *c, 1, G2))
    for s in range(-14, 1, 2):
        b.append(seg(sx(s), Y0 + 1, sx(s), Y1 - 1, 1, G1))
    for p in (12, 24):
        b.append(seg(X0 + 1, syp(p), X1 - 1, syp(p), 1, G1))
    for p, lab in ((0, "+0"), (12, "+12"), (24, "+24"), (36, "+36")):
        b.append(text(16, syp(p) + 4, lab, G4))
    b.append(text(sx(-16) - 4, 204, "-16s", G4))
    b.append(text(sx(-8) - 8, 204, "-8s", G4))
    b.append(text(sx(0) - 16, 204, "now", G4))

    # ecliptic: the tide's own path, dashed
    path = [(sx(t / 10), syp(tide_pitch(t / 10))) for t in range(-160, 1)]
    b.append(dashed(path, 1, G3, 3, 4))

    # the field: one star per (column, degree), magnitude from distance to the tide
    cols = 40
    ds = degrees()
    for i in range(cols):
        t = -span + (i + 0.5) * span / cols
        p = tide_pitch(t)
        for d in ds:
            r = 2.8 - abs(p - d) * 0.75
            if r >= 1.5:
                b.append(circle(sx(t), syp(d), r, G5))
    # the present: brightest star
    t = 0.0
    q = quantise(tide_pitch(t))
    b.append(circle(sx(t), syp(q), 3.5, G7))
    return frame(b, "v5 P10 voice field, star atlas")


def main():
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        out = HERE / name / "rest.svg"
        out.parent.mkdir(exist_ok=True)
        out.write_text(fn() + "\n", encoding="utf-8")
        print(out)


if __name__ == "__main__":
    main()
