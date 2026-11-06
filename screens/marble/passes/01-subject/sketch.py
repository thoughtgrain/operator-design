#!/usr/bin/env python3
"""Marble, subject pass 01: five rest-frame sketches from one script.

Marble is a player (synth + trackControl, aux track 12): marbles drop from a
hopper through rows of pegs, each peg kicking them one scale degree left or
right, into bins pitched on the scale around the played root. The notes go to
the target track. Every variant is drawn from the same small model at the
defaults (pegs 6 rows, drop 1/8, bounce 0 %, scale major), so the five
drawings disagree only in how they show it, never in what the machine does.

    python3 screens/marble/passes/01-subject/sketch.py

Device rules kept at sketch stage: one subpath per path, <= 64 points, lines
as closed filled ribbons (no open strokes), explicit paint on every leaf,
grey only, <= 4 fractional digits.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------- the model
ROWS = 6                      # pegs: enum "1".."12", default index 5 -> 6 rows
DROPS = 8                     # drop: division, default 0.5 -> 1/8 (8 marbles a bar)
BOUNCE = 0.0                  # bounce: rebound retriggers, default 0
SCALE = [0, 2, 4, 5, 7, 9, 11]  # major
NOTE = ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b"]
HEADER_LABELS = ["pegs", "drop", "bounce", "scale"]
HEADER_VALUES = ["6", "1/8", "0", "major"]


def degree_to_semi(d: int) -> int:
    """Scale degree (0 = root) to semitones from the root, any sign."""
    n = len(SCALE)
    octave, i = divmod(d, n)
    return 12 * octave + SCALE[i]


def bins():
    """(degree, semitones, probability) for each bin, left to right."""
    out = []
    for k in range(ROWS + 1):
        d = k - ROWS // 2
        p = math.comb(ROWS, k) / 2 ** ROWS
        out.append((d, degree_to_semi(d), p))
    return out


def bars(n_bars=4, seed=7):
    """Hits per bin for the last n bars (oldest first), seeded so every sketch agrees."""
    rng = random.Random(seed)
    out = []
    for _ in range(n_bars):
        h = [0] * (ROWS + 1)
        for _ in range(DROPS):
            h[sum(rng.random() < 0.5 for _ in range(ROWS))] += 1
        out.append(h)
    return out


def path_of(seed=3):
    """One marble's choices, row by row: +1 right, -1 left."""
    rng = random.Random(seed)
    return [1 if rng.random() < 0.5 else -1 for _ in range(ROWS)]


G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
FONT = "UniversNextPro-Light"


def f(v: float) -> str:
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# ---------------------------------------------------------------- primitives
class Frame:
    def __init__(self, title: str):
        self.title = title
        self.items: list[str] = []

    def add(self, s: str) -> None:
        self.items.append(s)

    def poly(self, pts, fill, stroke="none", sw=0.0):
        pts = dedupe(pts)
        assert 3 <= len(pts) <= 64, len(pts)
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
        sws = f' stroke-width="{f(sw)}"' if stroke != "none" else ""
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def ribbon(self, pts, w, colour):
        """An open line of width w as filled closed ribbons, <= 64 points a piece."""
        pts = dedupe(pts)
        n = 30
        i = 0
        while i < len(pts) - 1:
            self._ribbon_piece(pts[i:i + n + 1], w, colour)
            i += n

    def _ribbon_piece(self, seg, w, colour):
        h = w / 2
        left, right = [], []
        for k, (x, y) in enumerate(seg):
            if k == 0:
                dx, dy = seg[1][0] - x, seg[1][1] - y
                ln = math.hypot(dx, dy) or 1
                nx, ny, m = -dy / ln, dx / ln, 1.0
            elif k == len(seg) - 1:
                dx, dy = x - seg[k - 1][0], y - seg[k - 1][1]
                ln = math.hypot(dx, dy) or 1
                nx, ny, m = -dy / ln, dx / ln, 1.0
            else:
                ax, ay = x - seg[k - 1][0], y - seg[k - 1][1]
                bx, by = seg[k + 1][0] - x, seg[k + 1][1] - y
                la, lb = math.hypot(ax, ay) or 1, math.hypot(bx, by) or 1
                ax, ay, bx, by = ax / la, ay / la, bx / lb, by / lb
                tx, ty = ax + bx, ay + by
                lt = math.hypot(tx, ty) or 1
                tx, ty = tx / lt, ty / lt
                nx, ny = -ty, tx
                # miter length, capped
                cosv = nx * -ay + ny * ax
                m = min(2.0, 1 / max(0.5, abs(cosv)))
            left.append((x + nx * h * m, y + ny * h * m))
            right.append((x - nx * h * m, y - ny * h * m))
        self.poly(left + right[::-1], colour)

    def loop(self, pts, colour, sw, fill="none"):
        self.poly(pts, fill, colour, sw)

    def circle(self, cx, cy, r, fill, stroke="none", sw=0.0):
        sws = f' stroke-width="{f(sw)}"' if stroke != "none" else ""
        self.add(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def rect(self, x, y, w, h, fill):
        self.add(f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" fill="{fill}" stroke="none"/>')

    def line(self, a, b, w, colour):
        self._ribbon_piece([a, b], w, colour)

    def dashed(self, a, b, w, colour, dash=6, gap=4):
        L = math.dist(a, b)
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        t = 0.0
        while t < L - 1:
            e = min(L, t + dash)
            self.line((a[0] + ux * t, a[1] + uy * t), (a[0] + ux * e, a[1] + uy * e), w, colour)
            t = e + gap

    def text(self, x, y, s, colour=G4, size=10):
        self.add(f'<text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{colour}" stroke="none" '
                 f'font-family="{FONT}" font-size="{size}px">{s}</text>')

    def svg(self) -> str:
        head = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
            f"  <title>marble · subject pass 01 · {self.title}</title>",
            '  <g id="preview_canvas">',
            '    <rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>',
            "  </g>",
            '  <g id="preview_header">',
        ]
        steps = [G0, G1, G2, G3, G4, G5, G6, G7]
        for i, c in enumerate(steps):
            head.append(f'    <rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
        for i, lab in enumerate(HEADER_LABELS):
            c = "#CBCBCB" if i < 2 else "#000000"
            head.append(f'    <text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{c}" stroke="none" '
                        f'font-family="{FONT}" font-size="10px">{lab}</text>')
            head.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{c}" stroke="none" '
                        f'font-family="{FONT}" font-size="20px">{HEADER_VALUES[i]}</text>')
        head.append("  </g>")
        body = ["  " + s for s in self.items]
        return "\n".join(head + body + ["</svg>", ""])


def dedupe(pts):
    out = []
    for p in pts:
        p = (round(p[0], 3), round(p[1], 3))
        if not out or math.dist(out[-1], p) >= 0.2:
            out.append(p)
    if len(out) > 2 and math.dist(out[0], out[-1]) < 0.3:
        out.pop()
    return out


def ellipse_pts(cx, cy, rx, ry, a0, a1, n):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * k / n), cy + ry * math.sin(a0 + (a1 - a0) * k / n))
            for k in range(n + 1)]


# ---------------------------------------------------------------- v1
def v1() -> Frame:
    """P14 Loom, engineering schematic: each bar weaves a row; bins are warp threads."""
    F = Frame("v1 · P14 loom · engineering schematic")
    B = bins()
    hist = bars(4)                       # oldest first; the front row is the latest bar
    semi_px = 21.0
    cx = 232.0
    xs = [cx + s * semi_px - (B[0][1] + B[-1][1]) / 2 * semi_px for _, s, _ in B]
    rdx, rdy = 26.0, -22.0               # one row back = one bar earlier (oblique, from a 3D model)
    base_y = 176.0
    w, dd = 12.0, 0.32                   # slab width, slab depth as a fraction of the row pitch
    unit = 7.0                           # one marble = 7 px of slab height
    nrows = len(hist)

    def P(x, row, h):                    # world (x on the front line, row back, height) -> screen
        return (x + rdx * row, base_y + rdy * row - h)

    # warp threads: one per bin, running back through all rows (centre-line style: long-short dash)
    for x in xs:
        a, b = P(x + w / 2, -0.4, 0), P(x + w / 2, nrows - 0.5, 0)
        F.dashed(a, b, 1.0, G2, dash=9, gap=3)
    # weft ground lines, one per row (the bar line), hairline
    for r in range(nrows):
        F.line(P(xs[0] - 10, r, 0), P(xs[-1] + w + 10, r, 0), 1.0, G1 if r else G2)

    greys = [G7, G5, G4, G3]             # front (latest) to back (oldest)
    for r in reversed(range(nrows)):     # back to front
        h = hist[nrows - 1 - r]
        col = greys[r]
        sw = 2.0 if r == 0 else 1.2
        for i, x in enumerate(xs):
            n = h[i]
            if n == 0:
                continue
            H = n * unit
            fl, fr = P(x, r, 0), P(x + w, r, 0)
            tl, tr = P(x, r, H), P(x + w, r, H)
            bl_, br_ = P(x, r + dd, H), P(x + w, r + dd, H)
            br0 = P(x + w, r + dd, 0)
            F.loop([tl, tr, br_, bl_], col, 1.0 if r else 1.5, fill=G0)          # top
            F.loop([fr, br0, br_, tr], col, 1.0 if r else 1.5, fill=G0)          # side
            F.loop([fl, fr, tr, tl], col, sw, fill=G0)                          # front
            # one hairline per marble in the stack, front row only (the count reads)
            if r == 0:
                for k in range(1, n):
                    yk = fl[1] - k * unit
                    F.line((x + 2.5, yk), (x + w - 2.5, yk), 1.0, G4)

    # schematic annotation: bin names under the front row, a dimension for one bar of depth,
    # and a leader naming the rows
    for (d, s, p), x in zip(B, xs):
        name = NOTE[s % 12]
        F.text(x + w / 2 - 3 * len(name), base_y + 16, name, G4)
    # dimension line: row pitch = 1 bar, at the right, with extension lines
    ex = xs[-1] + w + 22
    a, b = P(ex, 0, 0), P(ex, 1, 0)
    F.line((a[0] - 6, a[1]), (a[0] + 4, a[1]), 1.0, G3)
    F.line((b[0] - 6, b[1]), (b[0] + 4, b[1]), 1.0, G3)
    F.line((a[0], a[1]), (b[0], b[1]), 1.0, G3)
    F.text(a[0] + 22, (a[1] + b[1]) / 2 + 4, "1 bar", G4)
    # leader to the oldest row
    o = P(xs[0] - 10, nrows - 1, 0)
    F.line((o[0], o[1]), (o[0] - 26, o[1] - 14), 1.0, G3)
    F.text(o[0] - 62, o[1] - 16, "bar −3", G4)
    # hopper symbol in schematic form: a funnel feeding the cloth, centred over the root thread
    F.text(330, 44, "warp: 7 bins", G4)
    F.text(330, 58, "weft: 1 bar", G4)
    return F


# ---------------------------------------------------------------- v2
def v2() -> Frame:
    """P5 Field and figure, oscilloscope: a graticule field, the distribution as the bright trace."""
    F = Frame("v2 · P5 field and figure · oscilloscope trace")
    x0, x1, y0, y1 = 40, 440, 34, 178
    div = 40
    # graticule (the field): 10 x ~3.6 divisions, low grey, minor ticks on the centre axes only
    for k in range(11):
        x = x0 + k * div
        F.line((x, y0), (x, y1), 1.0, G1)
    for y in (y0, y0 + 36, y0 + 72, y0 + 108, y1):
        F.line((x0, y), (x1, y), 1.0, G1)
    xc = (x0 + x1) / 2
    yc = y0 + 72
    for k in range(1, 50):
        x = x0 + k * 8
        if x % div == 0:
            continue
        F.line((x, yc - 2), (x, yc + 2), 1.0, G2)
    # x axis = pitch: 1 semitone = 16 px, root at the centre; the scale's tones are the long
    # ticks on the baseline (scale moves these)
    semi = 16.0
    for s in range(-12, 13):
        x = xc + s * semi
        if x < x0 or x > x1:
            continue
        if s % 12 in SCALE:
            F.line((x, y1), (x, y1 + 6), 1.0, G4)
    # figure: probability per bin as a stepped trace across the screen (pulses at the bins)
    B = bins()
    base = y1 - 2
    H = 120 / max(p for *_, p in B)
    pw = 5.0
    pts = [(x0, base)]
    for d, s, p in B:
        x = xc + s * semi
        h = max(3.0, p * H)
        pts += [(x - pw, base), (x - pw + 1.2, base - h), (x + pw - 1.2, base - h), (x + pw, base)]
    pts.append((x1, base))
    F.ribbon(pts, 2.0, G7)
    # channel 2 (bounce): the rebound trace, flat at bounce 0, in a lower grey, under the pulses
    F.ribbon([(x0, y1 - 14), (x1, y1 - 14)], 1.0, G3) if BOUNCE > 0 else None
    # readouts in the scope's corners
    F.text(x0 + 4, y0 + 13, "ch1  p(note)", G4)
    F.text(x1 - 58, y0 + 13, "6 rows", G4)
    for d, s, p in B:
        x = xc + s * semi
        name = NOTE[s % 12]
        F.text(x - 3 * len(name), y1 + 17, name, G4)
    # activity strip: the drops in the bar, one mark each (count follows drop)
    sx0, sw_ = 40, 400
    for k in range(DROPS):
        x = sx0 + (k + 0.5) * sw_ / DROPS
        F.rect(x - 2, 200, 4, 8, G3)
    F.line((sx0, 211), (sx0 + sw_, 211), 1.0, G2)
    return F


# ---------------------------------------------------------------- v3
def v3() -> Frame:
    """P12 Orrery, typeset diagram: a radial Galton board on the pitch-class circle."""
    F = Frame("v3 · P12 orrery · typeset diagram")
    cx, cy = 236.0, 112.0
    tilt = math.radians(24)              # camera elevation over the orbit plane
    ky = math.sin(tilt)
    R_out = 200.0
    R0 = 34.0
    rings = [R0 + (R_out - R0) * (k + 1) / (ROWS + 1) for k in range(ROWS)]
    sun_r = 16.0

    def proj(r, ang):                    # ang 0 = front (towards camera), clockwise seen from above
        return (cx + r * math.sin(ang), cy + r * math.cos(ang) * ky)

    def ring(r, a0, a1, w, col, n=48):
        pts = [proj(r, a0 + (a1 - a0) * k / n) for k in range(n + 1)]
        F.ribbon(pts, w, col)

    # back halves of every orbit first (they pass behind the sun), then the sun, then front halves
    def halves(r, w, col):
        ring(r, math.pi / 2, 3 * math.pi / 2, w, col)
    for r in rings:
        halves(r, 1.0, G2)
    halves(R_out, 1.5, G4)
    # drop clock on the innermost path: one tick per drop in the bar
    ring(R0 - 2, math.pi / 2, 3 * math.pi / 2, 1.0, G2)
    for k in range(DROPS):
        a = 2 * math.pi * (k + 0.5) / DROPS
        if math.cos(a) < 0:
            x, y = proj(R0 - 2, a)
            F.circle(x, y, 2.5, G0, G4, 1.0)
    # the hopper as the sun: an outlined sphere with a hairline equator
    F.circle(cx, cy - sun_r * 0.55, sun_r, G0, G5, 1.5)
    F.ribbon(ellipse_pts(cx, cy - sun_r * 0.55, sun_r, sun_r * ky, 0.05, math.pi - 0.05, 20), 1.0, G3)
    for r in rings:
        ring(r, -math.pi / 2, math.pi / 2, 1.0, G2)
    ring(R_out, -math.pi / 2, math.pi / 2, 1.5, G4)
    ring(R0 - 2, -math.pi / 2, math.pi / 2, 1.0, G2)
    for k in range(DROPS):
        a = 2 * math.pi * (k + 0.5) / DROPS
        if math.cos(a) >= 0:
            x, y = proj(R0 - 2, a)
            F.circle(x, y, 2.5, G0, G4, 1.0)

    # bins as planets on the outer orbit: angle = pitch class (30 deg a semitone), root in front;
    # size from probability. Typeset labels beside each.
    B = bins()
    items = []
    for d, s, p in B:
        ang = math.radians(30 * s)
        x, y = proj(R_out, ang)
        depth = math.cos(ang)
        rr = 3.0 + 9.0 * math.sqrt(p / 0.3125)
        rr *= 0.85 + 0.15 * depth       # size from distance, mild
        items.append((depth, x, y, rr, s, p))
    for depth, x, y, rr, s, p in sorted(items):
        root = s == 0
        F.circle(x, y - rr, rr, G0, G7 if root else G5, 2.0 if root else 1.5)
        # a terminator line (half-lit) to keep them out of icon territory
        F.ribbon(ellipse_pts(x, y - rr, rr * 0.45, rr - 0.8, -math.pi / 2, math.pi / 2, 10), 1.0, G3)
        name = NOTE[s % 12]
        lx = x + rr + 4 if x >= cx else x - rr - 4 - 6 * len(name)
        F.text(lx, y - rr + 4, name, G4)
    # one marble's path from the sun out through the rings: each ring steps a degree.
    choices = path_of()
    def semi_of(dg):                     # fractional degree -> semitones, linear between tones
        lo = math.floor(dg)
        t = dg - lo
        return degree_to_semi(lo) * (1 - t) + degree_to_semi(lo + 1) * t
    # model: between rings the marble falls outward and slides one half-degree sideways,
    # sampled finely so the projected path is a smooth spiral, not straight chords
    radii = [R0 - 2] + rings + [R_out]
    degs = [0.0]
    for c in choices:
        degs.append(degs[-1] + c / 2)
    degs.append(degs[-1])
    pts = []
    for k in range(len(radii) - 1):
        for t in range(6):
            u = t / 6
            r = radii[k] + (radii[k + 1] - radii[k]) * u
            dg = degs[k] + (degs[k + 1] - degs[k]) * (u * u * (3 - 2 * u))
            pts.append(proj(r, math.radians(30 * semi_of(dg))))
    pts.append(proj(R_out, math.radians(30 * semi_of(degs[-1]))))
    F.ribbon(pts, 1.0, G4)
    # caption, set like a figure in a book
    F.text(20, 206, "fig. 1  6 rows · major", G4)
    return F


# ---------------------------------------------------------------- v4
def v4() -> Frame:
    """P13 Capture, orthographic elevation: the board itself, bins as pipes cut to pitch."""
    F = Frame("v4 · P13 capture · orthographic elevation")
    cx = 240.0
    B = bins()
    nb = len(B)
    bw = 22.0                            # bin pitch (centre to centre)
    peg_dx = bw                          # peg lattice matches the bins
    top = 54.0                           # first peg row
    row_dy = 14.0
    bins_top = top + ROWS * row_dy + 4
    floor0 = 198.0                       # deepest floor (lowest note)
    semi_px = 4.0                        # 1 semitone = 4 px of pipe length
    left = cx - nb * bw / 2
    right = cx + nb * bw / 2
    # cabinet: side walls in section (hatched), drawn as double lines, a base plate
    for wx, sgn in ((left - 10, 1), (right + 2, -1)):
        F.loop([(wx, 30), (wx + 8, 30), (wx + 8, floor0 + 4), (wx, floor0 + 4)], G4, 1.2, fill=G0)
        for k in range(0, 34):
            ya = 36 + k * 5
            if ya + 7 > floor0 + 2:
                break
            F.line((wx + 1.5, ya + 6), (wx + 6.5, ya + 1), 1.0, G2)
    F.line((left - 10, floor0 + 6), (right + 10, floor0 + 6), 1.5, G4)
    # hopper funnel and gate (drop sets the gate's aperture)
    F.loop([(cx - 46, 26), (cx + 46, 26), (cx + 8, 42), (cx + 8, 46), (cx - 8, 46), (cx - 8, 42)], G5, 1.5, fill=G0)
    gap = 2.0 + 4.0 * 0.5                # aperture at drop 1/8
    F.rect(cx - 16, 46, 16 - gap, 3, G4)
    F.rect(cx + gap, 46, 16 - gap, 3, G4)
    # pegs: triangular lattice, row k has k+1 pegs
    for k in range(ROWS):
        y = top + k * row_dy
        for j in range(k + 1):
            x = cx + (j - k / 2) * peg_dx
            F.circle(x, y, 2.5, G3, G5, 1.0)
    # bins: dividers from bins_top down to each bin's floor; floor height set by pitch
    # (lower note = longer pipe = deeper floor). Scale moves the floors.
    lowest = B[0][1]
    for i in range(nb + 1):
        x = left + i * bw
        F.rect(x - 1, bins_top, 2, floor0 - bins_top, G4)
    for i, (d, s, p) in enumerate(B):
        x = left + i * bw
        fy = floor0 - (s - lowest) * semi_px
        F.rect(x + 1, fy, bw - 2, 2, G5)
        # below the floor: the pipe's dead length, hatched lightly so the floor reads as a level
        name = NOTE[s % 12]
        F.text(x + bw / 2 - 3 * len(name), floor0 + 18, name, G4)
    # the pile: marbles captured in the last bar, stacked on each floor (what's in a bin plays)
    hist = [round(p * 2 * DROPS) for _, _, p in B]   # two bars' worth, at the expected counts
    r = 4.5
    for i, (d, s, p) in enumerate(B):
        x = left + i * bw + bw / 2
        fy = floor0 - (s - lowest) * semi_px
        for k in range(hist[i]):
            ox = -5 if k % 2 == 0 else 5
            if hist[i] == 1:
                ox = 0
            yk = fy - r - 1 - (k // 2) * (2 * r) - (r * 0.0)
            F.circle(x + ox, yk, r, G0, G7, 1.5)
    # dimension: one semitone of pipe, at the right, elevation-drawing style
    dx = right + 26
    yA, yB = floor0, floor0 - 12 * semi_px
    F.line((dx - 5, yA), (dx + 5, yA), 1.0, G3)
    F.line((dx - 5, yB), (dx + 5, yB), 1.0, G3)
    F.line((dx, yA), (dx, yB), 1.0, G3)
    F.text(dx + 9, (yA + yB) / 2 + 4, "1 oct", G4)
    F.text(left - 92, 36, "elev. a–a", G4)
    return F


# ---------------------------------------------------------------- v5
def v5() -> Frame:
    """P3 Trace as subject (stretch), survey plan: one marble's fall as a traverse."""
    F = Frame("v5 · P3 trace as subject · survey plan")
    B = bins()
    x_st, cy = 46.0, 112.0
    leg = 50.0                           # chainage per peg row
    dy = 13.0                            # half the lattice step
    xs = [x_st + leg * (k + 1) for k in range(ROWS)]
    x_lot = x_st + leg * (ROWS + 1) + 10
    # lot line on the right: the property line divided into parcels, one per bin, placed by pitch
    semi_px = 10.0
    mid_s = (B[0][1] + B[-1][1]) / 2
    lot_y = [cy + (s - mid_s) * -semi_px for _, s, _ in B]     # higher note = further north (up)
    F.line((x_lot, lot_y[-1] - 14), (x_lot, lot_y[0] + 14), 1.5, G4)
    for i, (y, (d, s, p)) in enumerate(zip(lot_y, B)):
        ext = 10 if i % 2 == 0 else 22
        F.line((x_lot, y), (x_lot + ext, y), 1.0, G4)
        F.text(x_lot + ext + 4, y + 4, NOTE[s % 12], G4)
    # stations: a peg row is a column of survey stations; open triangles, hairline
    for k, x in enumerate(xs):
        for j in range(k + 2):
            y = cy + (j - (k + 1) / 2) * 2 * dy
            F.loop([(x - 4, y + 3.5), (x + 4, y + 3.5), (x, y - 3.5)], G3, 1.0, fill=G0)
    # the hopper as the origin station, labelled
    F.loop([(x_st - 6, cy + 5), (x_st + 6, cy + 5), (x_st, cy - 6)], G5, 1.5, fill=G0)
    F.text(x_st - 18, cy - 12, "stn 0", G4)
    # the traverse: one marble, leg by leg, bearing up or down a station per row, into its lot
    choices = path_of()
    pts = [(x_st, cy)]
    off = 0.0
    for k, c in enumerate(choices):
        off += c * dy * -1
        pts.append((xs[k], cy + off))
    k_bin = sum(1 for c in choices if c > 0)
    pts.append((x_lot, lot_y[k_bin]))
    F.ribbon(pts, 2.0, G7)
    # leg bearings, typeset small on the first and last legs only
    # chain line at the bottom: the bar, with a peg per drop (drop sets the count)
    y_ch = 196.0
    F.line((x_st, y_ch), (x_lot, y_ch), 1.2, G3)
    for k in range(DROPS + 1):
        x = x_st + (x_lot - x_st) * k / DROPS
        hgt = 5 if k in (0, DROPS) else 3
        F.line((x, y_ch - hgt), (x, y_ch + hgt), 1.0, G3)
    F.text(x_st, y_ch + 16, "0", G4)
    F.text(x_lot - 18, y_ch + 16, "1 bar", G4)
    # scale bar, survey style: one semitone of northing on the lot line
    F.text(14, 36, "plan · 6 rows · major", G4)
    return F


def main():
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        out = HERE / name / "rest.svg"
        out.parent.mkdir(exist_ok=True)
        out.write_text(fn().svg(), encoding="utf-8")
        print(out)


if __name__ == "__main__":
    main()
