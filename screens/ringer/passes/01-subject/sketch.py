#!/usr/bin/env python3
"""Ringer, subject pass 01: five rest-frame sketches from one script.

Each variant is its own pattern x drawing language (see pass.json). Every
frame is 480 x 220, keeps the stock header, and draws the controls at their
defaults: bells 6 (minor), method plain bob, pace 2 blows a beat, stroke 0 %.
The rows come from real place notation, so every drawing shows plain bob minor.

    python3 screens/ringer/passes/01-subject/sketch.py

Device rules kept even at sketch stage: one subpath per path, <= 64 points,
lines as closed filled ribbons (no open strokes), explicit paint on every
leaf, grey only (never red), <= 4 fractional digits.
"""
from __future__ import annotations

import math
from pathlib import Path

HERE = Path(__file__).resolve().parent

N = 6                      # bells at default (0.25 of 4..12)
PACE = 2.0                 # blows per beat at default (0.5 of 0.5..8, exponential)
GAP = 0.0                  # handstroke gap, blows (stroke default 0)
LABELS = ["bells", "method", "pace", "stroke"]
VALUES = ["6", "bob", "2.0", "0"]

G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
FONT = "UniversNextPro-Light"


# ---------------------------------------------------------------- the method
def change(row, places):
    """Apply one change: every pair not held by a place swaps."""
    row = list(row)
    i = 0
    n = len(row)
    while i < n - 1:
        if (i + 1) in places:
            i += 1
            continue
        if (i + 2) in places:  # odd stretch; the place holds, move on
            i += 1
            continue
        row[i], row[i + 1] = row[i + 1], row[i]
        i += 2
    return row


def plain_bob(n, rows):
    """Plain bob on n bells (even n): x1n x1n ... x12, from rounds."""
    lead = []
    for k in range(n):
        lead.append(set())            # x: all swap
        lead.append({1, n})
    lead[-1] = {1, 2}
    out = [list(range(1, n + 1))]
    k = 0
    while len(out) < rows:
        out.append(change(out[-1], lead[k % len(lead)]))
        k += 1
    return out


ROWS = plain_bob(N, 40)


def place_of(row, bell):
    return row.index(bell) + 1


# ---------------------------------------------------------------- primitives
def f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def dedupe(pts):
    out = []
    for p in pts:
        p = (round(p[0], 2), round(p[1], 2))
        if not out or math.dist(out[-1], p) >= 0.2:
            out.append(p)
    if len(out) > 2 and math.dist(out[0], out[-1]) < 0.3:
        out.pop()
    return out


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
        """A line of width w as filled closed ribbons, <= 30 segments a piece."""
        pts = dedupe(pts)
        if len(pts) < 2:
            return
        i = 0
        while i < len(pts) - 1:
            self._piece(pts[i:i + 31], w, colour)
            i += 30

    def _piece(self, seg, w, colour):
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
                n1 = (-ay / la, ax / la)
                n2 = (-by / lb, bx / lb)
                sx, sy = n1[0] + n2[0], n1[1] + n2[1]
                ls = math.hypot(sx, sy)
                if ls < 1e-6:
                    sx, sy, ls = n1[0], n1[1], 1
                nx, ny = sx / ls, sy / ls
                cos = nx * n1[0] + ny * n1[1]
                m = min(1 / max(cos, 0.2), 2.5)
            left.append((x + nx * h * m, y + ny * h * m))
            right.append((x - nx * h * m, y - ny * h * m))
        self.poly(left + right[::-1], colour)

    def loop(self, pts, colour, sw, fill="none"):
        self.poly(pts, fill, colour, sw)

    def circle(self, cx, cy, r, fill, stroke="none", sw=0.0):
        sws = f' stroke-width="{f(sw)}"' if stroke != "none" else ""
        self.add(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def line(self, a, b, w, colour):
        self._piece([a, b], w, colour)

    def text(self, x, y, s, colour=G4, size=10):
        self.add(f'<text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{colour}" stroke="none" '
                 f'font-family="{FONT}" font-size="{size}px">{s}</text>')

    def svg(self) -> str:
        head = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
            f"  <title>ringer · subject pass 01 · {self.title}</title>",
            '  <g id="preview_canvas">',
            '    <rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>',
            "  </g>",
            '  <g id="preview_header">',
        ]
        for i, c in enumerate([G0, G1, G2, G3, G4, G5, G6, G7]):
            head.append(f'    <rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
        for i, lab in enumerate(LABELS):
            c = "#CBCBCB" if i < 2 else "#000000"
            head.append(f'    <text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{c}" stroke="none" '
                        f'font-family="{FONT}" font-size="10px">{lab}</text>')
        for i, val in enumerate(VALUES):
            c = "#CBCBCB" if i < 2 else "#000000"
            head.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{c}" stroke="none" '
                        f'font-family="{FONT}" font-size="20px">{val}</text>')
        head.append("  </g>")
        body = ["  " + s for s in self.items]
        return "\n".join(head + body + ["</svg>", ""])

    def write(self, variant: str) -> None:
        d = HERE / variant
        d.mkdir(exist_ok=True)
        (d / "rest.svg").write_text(self.svg())


def ellipse_pts(cx, cy, rx, ry, n=48, a0=0.0, a1=2 * math.pi):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * k / n), cy + ry * math.sin(a0 + (a1 - a0) * k / n))
            for k in range(n + (0 if a1 - a0 >= 2 * math.pi - 1e-9 else 1))]


# A bell profile, half-section: (r, z) from crown (z=0) down to the lip (z=1),
# radius as a fraction of the lip radius. Real bells: flat crown, long waist,
# sound bow flaring to the lip.
BELL = [(0.42, 0.0), (0.52, 0.04), (0.56, 0.14), (0.58, 0.32), (0.62, 0.5),
        (0.70, 0.66), (0.84, 0.82), (0.96, 0.93), (1.0, 1.0)]
BELL_IN = [(0.36, 0.08), (0.46, 0.14), (0.5, 0.32), (0.55, 0.5), (0.62, 0.66),
           (0.75, 0.82), (0.86, 0.92)]


# ======================================================================
# v1 · P12 Orrery · patent section
# Each bell has its own orbit (treble innermost, tenor outermost) on a tilted
# plate; its angle on the orbit is its place in the current row, so the change
# reads round the plate and a bell hunting is a planet travelling its orbit.
# ======================================================================
def v1():
    fr = Frame("v1 · P12 orrery · patent section")
    cx, cy = 236, 132
    tilt = 0.4                         # sin(elevation): orthographic camera
    row = ROWS[4]
    R = [44 + 19 * b for b in range(N)]  # world radius of bell b+1's orbit
    rim = R[-1] + 20

    def P(rr, ang, z=0.0):
        return (cx + rr * math.cos(ang), cy + rr * math.sin(ang) * tilt - z)

    # places round the plate; place 1 at the front-left, travelling clockwise
    # seen from above (left to right across the front). A handstroke gap would
    # open a sector before place 1 (GAP = 0 at default: no sector).
    span = 2 * math.pi
    a_start = math.radians(150)

    def place_angle(p):
        return a_start - span * ((p - 1) + GAP) / (N + GAP)

    # the plate rim: graduated, one tick per blow in two bars at the pace
    fr.loop(ellipse_pts(cx, cy, rim, rim * tilt, 60), G3, 1.2)
    ticks = int(PACE * 8)
    for k in range(ticks):
        a = 2 * math.pi * k / ticks
        fr.line(P(rim, a), P(rim - 7, a), 1.2, G3)

    # orbits, back halves first
    for b in range(N):
        col = G3 if b == 0 else G2
        fr.ribbon(ellipse_pts(cx, cy, R[b], R[b] * tilt, 40, math.pi, 2 * math.pi), 1.2, col)

    # the hub: a vertical arbor drawn in section, hatched at 45 degrees
    hx, top, base, hw = cx, cy - 58, cy, 9
    bore = 2.5
    for side in (-1, 1):
        x0, x1 = (hx - hw, hx - bore) if side < 0 else (hx + bore, hx + hw)
        fr.loop([(x0, top), (x1, top), (x1, base), (x0, base)], G4, 1.5, G0)
        y = top + 4
        while y < base + (x1 - x0):
            a = (x0, y)
            b = (x1, y - (x1 - x0))
            # clip to the section box
            pa = (x0, min(max(a[1], top), base))
            pb_y = y - (x1 - x0)
            if pb_y < top:
                pb = (x0 + (y - top), top)
            else:
                pb = (x1, pb_y)
            if a[1] > base:
                pa = (x0 + (a[1] - base), base)
            if math.dist(pa, pb) > 2:
                fr.line(pa, pb, 1.0, G3)
            y += 4
    fr.loop([(hx - hw - 4, top - 4), (hx + hw + 4, top - 4), (hx + hw + 4, top), (hx - hw - 4, top)], G4, 1.5, G0)
    fr.loop(ellipse_pts(hx, base, hw + 6, (hw + 6) * tilt, 32), G4, 1.5, G0)

    # bells: one per orbit, at the angle of its place; drawn back to front
    bodies = []
    for b in range(N):
        p = place_of(row, b + 1)
        a = place_angle(p)
        x, y = P(R[b], a)
        bodies.append((y, b, x))
    # front halves of orbits drawn before the near bells but after far ones
    far = [t for t in bodies if t[0] < cy]
    near = [t for t in bodies if t[0] >= cy]

    def bell(x, y, b):
        lip = 5.5 + 0.9 * b
        h = lip * 1.5
        col, sw = (G7, 2.0) if b == 0 else (G5, 1.5)
        outer = [(x - r * lip, y - h + z * h) for r, z in BELL] + \
                [(x + r * lip, y - h + z * h) for r, z in reversed(BELL)]
        fr.poly(outer, G0, col, sw)
        # the cut: inner wall of the section, one side only (a half section)
        if b >= 2:
            inner = [(x + r * lip, y - h + z * h) for r, z in BELL_IN]
            fr.ribbon(inner, 1.0, G3)
        fr.line((x, y - h), (x, y - h - 3), 1.5, col)
        fr.line((x - 3, y - h - 3), (x + 3, y - h - 3), 1.5, col)

    for y, b, x in sorted(far):
        bell(x, y, b)
    for b in range(N):
        col = G3 if b == 0 else G2
        fr.ribbon(ellipse_pts(cx, cy, R[b], R[b] * tilt, 40, 0, math.pi), 1.2, col)
    for y, b, x in sorted(near):
        bell(x, y, b)

    # reference numerals with leaders, patent style
    def numeral(txt, at, tx, ty):
        fr.line(at, (tx + (12 if tx < at[0] else -2), ty - 4), 1.0, G3)
        fr.text(tx, ty, txt, G4)

    numeral("10", (hx - hw, top + 10), 150, 46)
    tb = [t for t in bodies if t[1] == 0][0]
    numeral("12", (tb[2] + 6, tb[0] - 6), 330, 64)
    numeral("14", P(R[-1], math.radians(20)), 420, 160)
    numeral("16", P(rim, math.radians(200)), 52, 120)
    fr.text(20, 208, "fig. 1", G4)
    fr.write("v1")


# ======================================================================
# v2 · P13 Capture · hidden-line isometric
# The machine's rule is the bells' own: a bell sounds where it is in its
# swing. So the frame hangs the ring, each bell turned on its axle to how far
# it has come round, and the change reads as a staircase of mouths.
# ======================================================================
def v2():
    fr = Frame("v2 · P13 capture · hidden-line isometric")
    s = 1.0
    ox, oy = 118, 70
    c30, s30 = math.cos(math.radians(30)), 0.5

    def iso(X, Y, Z):
        return (ox + (X - Y) * c30 * s, oy + (X + Y) * s30 * s - Z * s)

    pit = 34
    L = pit * N
    row = ROWS[4]
    W = 16                                  # half width of the frame
    zb = -34                                # frame sill height below the axles
    # frame: sills and posts, hidden-line (black-filled faces, grey edges)
    # back rail
    def beam(X0, X1, Y, Z, col=G3, th=5):
        pts = [iso(X0, Y, Z), iso(X1, Y, Z), iso(X1, Y, Z - th), iso(X0, Y, Z - th)]
        fr.poly(pts, G0, col, 1.2)

    beam(-6, L + 6, -W, 2)
    beam(-6, L + 6, -W, zb)
    for k in range(N + 1):
        X = k * pit - pit / 2 + pit / 2
        a, b = iso(X, -W, zb), iso(X, -W, 2)
        fr.line(a, b, 1.2, G2)

    # floor of the ringing chamber below: ropes drop through it
    zf = -78
    fl = [iso(-10, -W - 10, zf), iso(L + 10, -W - 10, zf), iso(L + 10, W + 10, zf), iso(-10, W + 10, zf)]
    fr.loop(fl, G2, 1.2)

    # bells: place p has swung furthest for p = 1 (about to strike), least for p = n
    order = []
    for b in range(N):
        p = place_of(row, b + 1)
        ang = math.radians(165 - (p - 1) * 140 / (N - 1))   # from mouth-up, handstroke side
        order.append((b, ang))

    for b, ang in order:
        X = pit / 2 + b * pit
        lip = 9 + 1.0 * b
        h = lip * 1.45
        ca, sa = math.cos(ang), math.sin(ang)

        def rot(u, z):
            # (u along the row, z up) in the wheel plane, turned by ang about the axle
            return (X + u * ca - z * sa, u * sa + z * ca)

        # wheel: a hairline circle in the X-Z plane, behind the bell
        wr = h + 6
        wheel = []
        for k in range(48):
            t = 2 * math.pi * k / 48
            wheel.append(iso(X + wr * math.cos(t), W - 4, wr * math.sin(t)))
        fr.loop(wheel, G2, 1.2)
        # rope from the wheel's rim down through the floor to its sally
        rx = X + wr
        sally_z = zf + 12 + 10 * (1 - math.log(PACE / 0.5) / math.log(16))
        fr.line(iso(rx, W - 4, 0), iso(rx, W - 4, sally_z + 8), 1.2, G3)
        fr.loop([iso(rx - 1.8, W - 4, sally_z + 8), iso(rx + 1.8, W - 4, sally_z + 8),
                 iso(rx + 1.8, W - 4, sally_z), iso(rx - 1.8, W - 4, sally_z)], G4, 1.2, G1)
        fr.line(iso(rx, W - 4, sally_z), iso(rx, W - 4, zf), 1.2, G3)

        # the bell: a solid of revolution about its own axis, hung from the axle
        # axis direction in the wheel plane
        rings = []
        for r, z in BELL:
            ring = []
            for k in range(24):
                t = 2 * math.pi * k / 24
                u = r * lip * math.cos(t)
                yy = r * lip * math.sin(t)
                zz = h * 0.15 + z * h        # crown just under the axle... mouth outward
                Xr, Zr = rot(u, -zz)
                ring.append(iso(Xr, yy, Zr))
            rings.append(ring)
        a0 = iso(*(lambda q: (q[0], 0, q[1]))(rot(0, 0)))
        a1 = iso(*(lambda q: (q[0], 0, q[1]))(rot(0, -h)))
        ax, ay = a1[0] - a0[0], a1[1] - a0[1]
        la = math.hypot(ax, ay) or 1
        nx, ny = -ay / la, ax / la
        left = [max(r, key=lambda q: q[0] * nx + q[1] * ny) for r in rings]
        right = [min(r, key=lambda q: q[0] * nx + q[1] * ny) for r in rings]
        col, sw = (G7, 2.0) if b == 0 else (G5, 1.5)
        lipring = rings[-1]
        # silhouette: crown, one side, lip, other side
        fr.poly(left + right[::-1], G0, col, sw)
        mouth_up = math.cos(ang) < 0      # mouth faces up/out: show the lip ellipse
        fr.loop(lipring, col if mouth_up else G4, 1.5 if mouth_up else 1.2, G0 if mouth_up else "none")
        # headstock and gudgeon on the axle
        fr.loop([iso(X - 6, -W, 2), iso(X + 6, -W, 2), iso(X + 6, W, 2), iso(X - 6, W, 2)], G3, 1.2, G0)
        # stay: a short bar standing off the headstock, opposite the mouth
        st0 = rot(0, 2)
        st1 = rot(0, 16)
        fr.line(iso(st0[0], 0, st0[1]), iso(st1[0], 0, st1[1]), 1.5, G4)

    # front rail drawn last so it hides what is behind it
    beam(-6, L + 6, W, 2, G4)
    beam(-6, L + 6, W, zb, G3)
    for k in range(N + 1):
        X = k * pit
        fr.line(iso(X, W, zb - 5), iso(X, W, 2), 1.2, G3)

    fr.text(20, 208, "hand", G4)
    fr.text(392, 46, "frame, 6 pits", G4)
    fr.write("v2")


# ======================================================================
# v3 · P14 Loom · star atlas
# The method as a chart of the sky: rows are parallels of a conic projection,
# places its meridians, every blow a star sized by its bell, and the treble's
# path drawn through them as the constellation line. New rows weave in at the
# bottom, the chart slides back.
# ======================================================================
def v3():
    fr = Frame("v3 · P14 loom · star atlas")
    ax, ay = 236, -420                    # apex of the cone, off screen
    R0 = 612                              # radius of the newest row (front)
    dr = 15                               # radius step per row (pace: rows per window)
    shown = 9
    rows = ROWS[6:6 + shown]
    span = math.radians(17)

    def P(rr, p):
        # place p (1..N) on parallel of radius rr
        t = -span + 2 * span * (p - 1) / (N - 1)
        return (ax + rr * math.sin(t), ay + rr * math.cos(t))

    # neatline: double border, atlas style
    x0, y0, x1, y1 = 44, 30, 430, 210
    fr.loop([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], G3, 1.2)
    fr.loop([(x0 + 4, y0 + 4), (x1 - 4, y0 + 4), (x1 - 4, y1 - 4), (x0 + 4, y1 - 4)], G2, 1.2)
    # graduation ticks along the inner border, one per 3 px of meridian
    for k in range(0, 37):
        x = x0 + 4 + k * (x1 - x0 - 8) / 36
        ln = 4 if k % 6 == 0 else 2.5
        fr.line((x, y1 - 4), (x, y1 - 4 - ln), 1.0, G3)

    # parallels (rows) and meridians (places)
    Rs = [R0 - dr * k for k in range(shown)]
    for k, rr in enumerate(Rs):
        arc = [(ax + rr * math.sin(t), ay + rr * math.cos(t))
               for t in [-span - 0.05 + (2 * span + 0.1) * i / 40 for i in range(41)]]
        fr.ribbon(arc, 1.0, G1 if k else G2)
    for p in range(1, N + 1):
        fr.ribbon([P(Rs[-1] - 10, p), P(R0 + 10, p)], 1.0, G1)

    # secondary figure: bell 2's path, hairline
    line2 = [P(Rs[k], place_of(rows[shown - 1 - k], 2)) for k in range(shown)]
    fr.ribbon(line2, 1.2, G4)

    # stars: every blow, magnitude by bell (tenor brightest-largest disc but
    # mid grey; the treble's stars bright on its line)
    for k in range(shown):
        r = rows[shown - 1 - k]
        for i, bell in enumerate(r):
            x, y = P(Rs[k], i + 1)
            if bell == 1:
                continue
            rad = 1.5 + 0.42 * bell
            fr.circle(x, y, rad, G5 if k == 0 else G3, G0, 1.0)

    # the constellation: the treble's path through the rows
    tl = [P(Rs[k], place_of(rows[shown - 1 - k], 1)) for k in range(shown)]
    fr.ribbon(tl, 2.0, G7)
    for k, (x, y) in enumerate(tl):
        fr.circle(x, y, 3.0 if k == 0 else 2.2, G7, G0, 1.0)

    # labels: bell numbers on the newest row, row numbers like declinations
    for i, bell in enumerate(rows[-1]):
        x, y = P(R0, i + 1)
        fr.text(x - 3, y + 2 + 12 if y + 14 < 205 else y - 8, str(bell), G4)
    for k in (0, 4, 8):
        x, y = P(Rs[k], N)
        fr.text(x + 12, y + 3, str(6 + shown - 1 - k), G4)
    fr.text(52, 46, "plain bob minor", G4)
    fr.write("v3")


# ======================================================================
# v4 · P5 Field and figure · engineering schematic
# One bell in elevation, set on its headstock and wheel, swung to the angle
# the pace lets it rise to; a ringing-chamber floor recedes behind it; the
# whole pull (handstroke and backstroke rows) runs along the strip below.
# ======================================================================
def v4():
    fr = Frame("v4 · P5 field and figure · engineering schematic")
    # field: the chamber floor as a receding grid, stopped before it packs
    hz, fy, vx = 92, 190, 240
    for k in range(-8, 9):
        top = (vx + k * 14, hz + 34)
        bot = (vx + k * 44, fy)
        fr.line(top, bot, 1.0, G1)
    y = fy
    step = 15
    while y > hz + 36:
        fr.line((20, y), (460, y), 1.0, G1)
        step *= 0.78
        y -= max(step, 6)

    # figure: the bell, in elevation, turned to its set angle about the gudgeon
    gx, gy = 196, 104
    frac = math.log(PACE / 0.5) / math.log(16)      # 0 slow .. 1 fast
    ang = math.radians(178 - 70 * frac)             # slow: up at balance; fast: rung low
    lip = 34
    h = 50

    def rot(u, z):
        ca, sa = math.cos(ang), math.sin(ang)
        return (gx + u * ca - z * sa, gy - (u * sa + z * ca))

    # centre lines (dash-dot) through the gudgeon
    def dashdot(a, b, col=G3):
        L = math.dist(a, b)
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        t = 0
        pat = [10, 3, 3, 3]
        k = 0
        while t < L:
            seg = min(pat[k % 4], L - t)
            if k % 2 == 0 and seg > 1.5:
                fr.line((a[0] + ux * t, a[1] + uy * t), (a[0] + ux * (t + seg), a[1] + uy * (t + seg)), 1.0, col)
            t += seg
            k += 1

    dashdot((gx - 100, gy), (gx + 100, gy))
    dashdot((gx, gy - 70), (gx, gy + 70))

    # wheel: rim, spokes; drawn behind the bell
    wr = 66
    fr.loop(ellipse_pts(gx, gy, wr, wr, 60), G4, 1.5)
    fr.loop(ellipse_pts(gx, gy, wr - 5, wr - 5, 60), G2, 1.2)
    for k in range(4):
        t = ang + math.pi / 4 + k * math.pi / 2
        fr.line((gx + 10 * math.cos(t), gy - 10 * math.sin(t)),
                (gx + (wr - 5) * math.cos(t), gy - (wr - 5) * math.sin(t)), 1.2, G2)

    # the bell: section profile turned about the gudgeon (crown at the headstock)
    outer = [rot(-r * lip, -(8 + z * h)) for r, z in BELL] + [rot(r * lip, -(8 + z * h)) for r, z in reversed(BELL)]
    fr.poly(outer, G0, G7, 2.5)
    inner = [rot(-r * lip, -(8 + z * h)) for r, z in BELL_IN] + [rot(r * lip, -(8 + z * h)) for r, z in reversed(BELL_IN)]
    fr.poly(inner, G0, G4, 1.2)
    # clapper: hidden line inside (dashes), hung from the crown staple
    c0, c1 = rot(0, -12), rot(0, -(8 + 0.92 * h))
    L = math.dist(c0, c1)
    for t in range(0, int(L) - 3, 7):
        a = (c0[0] + (c1[0] - c0[0]) * t / L, c0[1] + (c1[1] - c0[1]) * t / L)
        b = (c0[0] + (c1[0] - c0[0]) * (t + 4) / L, c0[1] + (c1[1] - c0[1]) * (t + 4) / L)
        fr.line(a, b, 1.2, G4)
    # headstock and stay
    hs = [rot(-22, 0), rot(22, 0), rot(22, -8), rot(-22, -8)]
    fr.poly(hs, G0, G5, 1.5)
    st = [rot(-2, 0), rot(2, 0), rot(2, 40), rot(-2, 40)]
    fr.poly(st, G0, G5, 1.5)
    fr.circle(gx, gy, 3.5, G0, G5, 1.5)

    # angle dimension: arc from mouth-down to the set angle, with its figure
    arc_r = 84
    a_from = -math.pi / 2
    a_to = a_from + ang
    pts = [(gx + arc_r * math.cos(a_from + (a_to - a_from) * k / 40),
            gy - arc_r * math.sin(a_from + (a_to - a_from) * k / 40)) for k in range(41)]
    fr.ribbon(pts, 1.0, G3)
    for a in (a_from, a_to):
        fr.line((gx + (arc_r - 4) * math.cos(a), gy - (arc_r - 4) * math.sin(a)),
                (gx + (arc_r + 4) * math.cos(a), gy - (arc_r + 4) * math.sin(a)), 1.2, G4)
    fr.text(gx + 92, gy - 46, f"{int(math.degrees(ang))}°", G4)
    # part labels with leaders
    fr.line((gx + 40, gy - 50), (330, 58), 1.0, G3)
    fr.text(334, 61, "wheel", G4)
    fr.line(rot(0, 40), (330, 82), 1.0, G3)
    fr.text(334, 85, "stay", G4)

    # strip: the whole pull, handstroke then backstroke, one tick per blow,
    # tick height by bell (treble tallest); the gap before handstroke is stroke
    sx, sy = 120, 212
    row_h, row_b = ROWS[4], ROWS[5]
    pitch = 10
    xk = sx + GAP * pitch
    fr.text(sx - 36, sy - 2, "h b", G4)
    for r_i, r in enumerate((row_h, row_b)):
        for i, bell in enumerate(r):
            hgt = 4 + (N - bell) * 2.2
            col = G7 if bell == 1 else G4
            fr.poly([(xk, sy), (xk + 4, sy), (xk + 4, sy - hgt), (xk, sy - hgt)], col)
            xk += pitch
        xk += 6
    fr.write("v4")


# ======================================================================
# v5 · P4 Stack in depth · oscilloscope trace (stretch)
# Each row as the pitch staircase it sends to the target track, the newest
# row bright on the graticule, the rows before it stacked back up and right.
# ======================================================================
def v5():
    fr = Frame("v5 · P4 stack in depth · oscilloscope trace")
    gx0, gy0, gw, gh = 40, 100, 300, 104      # front graticule
    rows = ROWS[2:7]                            # five rows, the newest last
    frac = math.log(PACE / 0.5) / math.log(16)
    off = (18 - 8 * frac, -(15 - 6 * frac))   # depth step per row: time between rows

    # graticule: 10 x 4 divisions, hairline, centre axis ticked
    for k in range(11):
        x = gx0 + k * gw / 10
        fr.line((x, gy0), (x, gy0 + gh), 1.0, G1)
    for k in range(5):
        y = gy0 + k * gh / 4
        fr.line((gx0, y), (gx0 + gw, y), 1.0, G1 if k not in (0, 4) else G2)
    for k in range(51):
        x = gx0 + k * gw / 50
        fr.line((x, gy0 + gh / 2 - 2), (x, gy0 + gh / 2 + 2), 1.0, G2) if k % 5 else None

    def trace(row, dx, dy):
        lead = GAP * gw / (N + 1)
        step = (gw - lead) / N
        pts = [(gx0 + dx, gy0 + gh - 8 + dy)]
        x = gx0 + dx + lead + 6
        pts.append((x, gy0 + gh - 8 + dy))
        for i, bell in enumerate(row):
            lev = gy0 + 10 + (bell - 1) * (gh - 20) / (N - 1) + dy
            pts.append((x, lev))
            x2 = x + step - 6 if i < N - 1 else gx0 + gw + dx
            pts.append((x2 - 3, lev))
            pts.append((x2, gy0 + gh - 8 + dy) if i < N - 1 else (x2, lev))
            x = x2 + 6 if i < N - 1 else x2
            if i < N - 1:
                pts.append((x, gy0 + gh - 8 + dy))
        return pts

    greys = [G1, G2, G2, G3]
    for k in range(4, 0, -1):            # back to front
        dx, dy = off[0] * k, off[1] * k
        # the frame of each earlier sweep, hairline
        fr.loop([(gx0 + dx, gy0 + dy), (gx0 + gw + dx, gy0 + dy),
                 (gx0 + gw + dx, gy0 + gh + dy), (gx0 + dx, gy0 + gh + dy)], G1, 1.0, G0)
        fr.ribbon(trace(rows[4 - k], dx, dy), 1.2, greys[4 - k])
    fr.loop([(gx0, gy0), (gx0 + gw, gy0), (gx0 + gw, gy0 + gh), (gx0, gy0 + gh)], G3, 1.2)
    # redraw the graticule over the front black box
    for k in range(1, 10):
        x = gx0 + k * gw / 10
        fr.line((x, gy0 + 1), (x, gy0 + gh - 1), 1.0, G1)
    for k in range(1, 4):
        y = gy0 + k * gh / 4
        fr.line((gx0 + 1, y), (gx0 + gw - 1, y), 1.0, G1)
    fr.ribbon(trace(rows[4], 0, 0), 2.0, G7)

    # trigger marker and readouts, scope style
    fr.poly([(gx0 - 9, gy0 + gh - 12), (gx0 - 3, gy0 + gh - 8), (gx0 - 9, gy0 + gh - 4)], G4)
    fr.text(gx0, gy0 + gh + 13 if gy0 + gh + 13 < 216 else 214, "ch 1", G4)
    fr.text(gx0 + 160, 214, "1 row / sweep", G4)
    fr.text(gx0 + gw + 8, gy0 + gh / 2 + 3, "1/2 st", G4)
    fr.write("v5")


if __name__ == "__main__":
    for fn in (v1, v2, v3, v4, v5):
        fn()
    print("rows:", ["".join(map(str, r)) for r in ROWS[:12]])
