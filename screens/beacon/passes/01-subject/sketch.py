#!/usr/bin/env python3
"""Beacon, subject pass 01: five rest-frame sketches from one script.

Each variant is a different pattern x drawing language (see pass.json). Every
frame is 480 x 220, keeps the stock header, and draws the controls at their
defaults (pulse 25 %, lens 0.7 -> feedback 83 %, sweep 2.4 st, fog 0).

    python3 screens/beacon/passes/01-subject/sketch.py

Device rules kept even at sketch stage: one subpath per path, <= 64 points,
lines as closed filled ribbons (no open strokes), explicit paint on every
leaf, grey only, <= 4 fractional digits.
"""
from __future__ import annotations

import math
from pathlib import Path

HERE = Path(__file__).resolve().parent

# defaults, as control positions 0..1
D = {"pulse": 0.25, "lens": 0.7, "sweep": 0.2, "fog": 0.0}
FEEDBACK = 0.995 * math.sqrt(D["lens"])            # lens mapping: power 0.5, max 0.995
HEADER_VALUES = ["25", "83", "2.4", "0"]
LABELS = ["pulse", "lens", "sweep", "fog"]

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
        """Closed polygon (one subpath, <= 64 points)."""
        pts = dedupe(pts)
        assert 3 <= len(pts) <= 64, len(pts)
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
        sws = f' stroke-width="{f(sw)}"' if stroke != "none" else ""
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def ribbon(self, pts, w, colour, closed=False):
        """A line of width w as filled closed ribbons, split so no piece passes 64 points."""
        pts = dedupe(pts)
        if closed:
            # a closed loop: draw as outline polygon with a stroke, fill black stays separate
            raise ValueError("use loop()")
        n = 30
        i = 0
        while i < len(pts) - 1:
            seg = pts[i:i + n + 1]
            self._ribbon_piece(seg, w, colour)
            i += n

    def _ribbon_piece(self, seg, w, colour):
        h = w / 2
        left, right = [], []
        for k, (x, y) in enumerate(seg):
            if k == 0:
                dx, dy = seg[1][0] - x, seg[1][1] - y
            elif k == len(seg) - 1:
                dx, dy = x - seg[k - 1][0], y - seg[k - 1][1]
            else:
                ax, ay = x - seg[k - 1][0], y - seg[k - 1][1]
                bx, by = seg[k + 1][0] - x, seg[k + 1][1] - y
                la, lb = math.hypot(ax, ay) or 1, math.hypot(bx, by) or 1
                dx, dy = ax / la + bx / lb, ay / la + by / lb
                if math.hypot(dx, dy) < 1e-6:
                    dx, dy = ax, ay
            ln = math.hypot(dx, dy) or 1
            nx, ny = -dy / ln, dx / ln
            # limit miter
            left.append((x + nx * h, y + ny * h))
            right.append((x - nx * h, y - ny * h))
        self.poly(left + right[::-1], colour)

    def loop(self, pts, colour, sw, fill="none"):
        """A closed outline (stroked closed path). Splits are not allowed, so <= 64 points."""
        self.poly(pts, fill, colour, sw)

    def circle(self, cx, cy, r, fill, stroke="none", sw=0.0):
        sws = f' stroke-width="{f(sw)}"' if stroke != "none" else ""
        self.add(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def rect(self, x, y, w, h, fill):
        self.add(f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" fill="{fill}" stroke="none"/>')

    def line(self, a, b, w, colour):
        self._ribbon_piece([a, b], w, colour)

    def text(self, x, y, s, colour=G4, size=10):
        self.add(f'<text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{colour}" stroke="none" '
                 f'font-family="{FONT}" font-size="{size}px">{s}</text>')

    def svg(self) -> str:
        head = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
            f"  <title>beacon · subject pass 01 · {self.title}</title>",
            '  <g id="preview_canvas">',
            '    <rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>',
            "  </g>",
            '  <g id="preview_header">',
        ]
        steps = [G0, G1, G2, G3, G4, G5, G6, G7]
        for i, c in enumerate(steps):
            head.append(f'    <rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
        for i, lab in enumerate(LABELS):
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


def arc(cx, cy, rx, ry, a0, a1, n):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * k / n), cy + ry * math.sin(a0 + (a1 - a0) * k / n))
            for k in range(n + 1)]


def smoothstep(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- the model
# One small model of the voice, used by every variant so the drawings agree:
# a pulse of width w (in comb periods) every P periods excites a comb of delay
# 1 period with feedback g; fog is a one-pole smoothing of the result.
def pulse_halfwidth_px(period_px):
    return max(1.2, D["pulse"] * 0.5 * period_px)


def echo_amps(g=FEEDBACK, floor=0.06, cap=40):
    out, a = [], 1.0
    while a > floor and len(out) < cap:
        out.append(a)
        a *= g
    return out


# ---------------------------------------------------------------- v1
def v1() -> Frame:
    """P3 Trace as subject, survey plan: the output traced along a chained baseline."""
    F = Frame("v1 · P3 trace as subject · survey plan")
    base_y, x0, x1 = 156, 36, 452
    # chained baseline with chainage ticks and a few figures
    F.line((x0, base_y), (x1, base_y), 1.2, G3)
    for k, x in enumerate(range(x0, x1 + 1, 26)):
        major = k % 4 == 0
        F.line((x, base_y - (5 if major else 3)), (x, base_y + (5 if major else 3)), 1.0, G3)
        if major:
            F.text(x - 3, base_y + 18, str(k // 4 * 10), G4)
    F.text(x1 - 26, base_y + 31, "ch. ms", G4)
    # station: survey triangle at chainage 0, with label
    sx, sy = x0, base_y
    F.loop([(sx - 6, sy + 5), (sx + 6, sy + 5), (sx, sy - 6)], G5, 1.5, fill=G0)
    F.text(sx - 30, sy - 8, "stn a", G4)
    # bearing ray from the station: the rotating light (sweep); kept under the trace
    ang = math.radians(-(8 + 40 * D["sweep"]))
    L = 92
    F.line((sx + 9 * math.cos(ang), sy + 9 * math.sin(ang)),
           (sx + L * math.cos(ang), sy + L * math.sin(ang)), 1.0, G5)
    F.ribbon(arc(sx, sy, 34, 34, 0, ang, 8), 1.0, G3)
    # input pulse train under the baseline (pulse width)
    period = 18.0
    pulses = [64, 204, 344]
    hw = max(1.5, D["pulse"] * 0.5 * period)
    y_lo, y_hi = 200, 186
    pts = [(x0, y_lo)]
    for px in pulses:
        pts += [(px - hw, y_lo), (px - hw, y_hi), (px + hw, y_hi), (px + hw, y_lo)]
    pts.append((x1, y_lo))
    F.ribbon(pts, 1.5, G4)
    # output trace: each pulse rings through the comb (lens), the bright subject.
    # Echoes one comb period apart, falling by the feedback; teeth as wide as the pulse.
    amps = echo_amps(floor=0.1)
    rest_y, H = 128, 84
    shw = min(period / 2 - 1.2, max(2.2, hw + 1.2))
    out = [(x0, rest_y)]
    for px in pulses:
        for k, a in enumerate(amps):
            c = px + k * period
            if c + shw > pulses[-1] + 140 or (px != pulses[-1] and c + shw > px + 136) or c + shw > x1:
                break
            out += [(c - shw, rest_y), (c - 0.7, rest_y - H * a), (c + 0.7, rest_y - H * a), (c + shw, rest_y)]
    out.append((x1, rest_y))
    # survey offsets: perpendiculars from the chain line where each pulse fires, tying input to output
    for px in pulses:
        F.line((px - shw - 3, base_y - 2), (px - shw - 3, rest_y + 4), 1.0, G3)
    F.ribbon(out, 2.0, G7)
    return F


# ---------------------------------------------------------------- v2
def v2() -> Frame:
    """P4 Stack in depth, patent section: the comb lens as stacked Fresnel plates in section."""
    F = Frame("v2 · P4 stack in depth · patent section")
    amps = echo_amps(floor=0.3, cap=6)          # plates that survive the lens (count)
    n = len(amps)
    spread = 1.0 + 0.8 * D["fog"]               # fog pushes the plates apart (position)
    dx, dy = 24 * spread, -17 * spread          # recession per plate
    fx, fy = 176, 190                           # front plate's lower-left corner
    w, h = 176, 24                              # plate section
    teeth = 8
    tw = w / teeth
    blunt = 0.12 + 0.6 * D["pulse"]             # pulse width blunts the tooth faces
    greys = [G7, G5, G4, G3, G3, G2]
    for i in reversed(range(n)):
        ox, oy = fx + dx * i, fy + dy * i
        top = []
        for t in range(teeth):
            x = ox + t * tw
            top += [(x + 0.6, oy - h + 10), (x + tw * (1 - blunt), oy - h), (x + tw - 0.6, oy - h)]
        top.append((ox + w, oy - h + 10))
        outline = [(ox, oy)] + top + [(ox + w, oy)]
        F.loop(outline, greys[i], 2.0 if i == 0 else 1.2, fill=G0)
        if i == 0:
            # section hatching on the cut face of the front plate: 45 deg, 6 px pitch
            for k in range(0, int(w / 6)):
                xa = ox + 6 + k * 6
                if xa + 10 > ox + w - 3:
                    break
                F.line((xa, oy - 2), (xa + 10, oy - 12), 1.0, G3)
    # lamp housing in section at the left: a reflector cup (hatched wall) with a coiled filament
    lx, ly = 82, 140
    cup_o = arc(lx, ly, 30, 30, math.radians(100), math.radians(260), 18)
    cup_i = arc(lx, ly, 25, 25, math.radians(260), math.radians(100), 18)
    F.loop(cup_o + cup_i, G5, 1.5, fill=G0)
    for k in range(1, 8):
        a = math.radians(100 + 20 * k)
        F.line((lx + 25.5 * math.cos(a), ly + 25.5 * math.sin(a)), (lx + 29.5 * math.cos(a + 0.12), ly + 29.5 * math.sin(a + 0.12)), 1.0, G3)
    coil = []
    for k in range(9):
        coil.append((lx - 8 + 2 * k, ly + (-4 if k % 2 else 4)))
    F.ribbon(coil, 1.2, G5)
    # rotating shutter (sweep): a blade on the lamp's axis, at its angle, with the swing drawn as an arc
    ang = math.radians(-60 + 240 * D["sweep"])
    a2 = ang + math.radians(22)
    blade = arc(lx, ly, 42, 42, ang, a2, 6) + arc(lx, ly, 37, 37, a2, ang, 6)
    F.loop(blade, G6, 1.5, fill=G1)
    F.ribbon(arc(lx, ly, 48, 48, math.radians(-60), ang, 10), 1.0, G3)
    # optical axis (hairline) from the lamp into the stack
    F.line((lx + 34, ly), (fx - 8, ly), 1.0, G3)
    F.line((fx - 8, ly - 4), (fx - 8, ly + 4), 1.0, G3)
    # patent reference numerals with leader lines
    F.line((lx - 24, ly + 22), (lx - 34, ly + 40), 1.0, G4)
    F.text(lx - 46, ly + 52, "10", G4)
    F.line((fx + 30, fy - 4), (fx + 18, fy + 12), 1.0, G4) if False else None
    F.line((fx - 2, fy - 8), (fx - 18, fy + 2), 1.0, G4)
    F.text(fx - 34, fy + 12, "12", G4)
    bx, by = fx + dx * (n - 1) + w, fy + dy * (n - 1) - h
    F.line((bx + 2, by + 4), (bx + 16, by - 6), 1.0, G4)
    F.text(bx + 18, by - 6, "14", G4)
    ma = ang + math.radians(11)
    F.line((lx + 44 * math.cos(ma), ly + 44 * math.sin(ma)), (lx + 58 * math.cos(ma), ly + 58 * math.sin(ma) - 8), 1.0, G4)
    F.text(lx + 60 * math.cos(ma) - 2, ly + 60 * math.sin(ma) - 12, "16", G4)
    F.text(420, 210, "fig. 1", G4)
    return F


# ---------------------------------------------------------------- v3
def iso(x, y, z, ox=240, oy=150, s=1.0):
    return (ox + (x - y) * 0.866 * s, oy + (x + y) * 0.5 * s - z * s)


def clip_seg(a, b, ymin, ymax, xmin=0, xmax=480):
    """Liang-Barsky clip of segment ab to a box."""
    t0, t1 = 0.0, 1.0
    dx, dy = b[0] - a[0], b[1] - a[1]
    for p, q in ((-dx, a[0] - xmin), (dx, xmax - a[0]), (-dy, a[1] - ymin), (dy, ymax - a[1])):
        if p == 0:
            if q < 0:
                return None
            continue
        t = q / p
        if p < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
    if t0 >= t1:
        return None
    return (a[0] + dx * t0, a[1] + dy * t0), (a[0] + dx * t1, a[1] + dy * t1)


def v3() -> Frame:
    """P5 Field and figure, hidden-line isometric: the lens barrel standing on the sea."""
    F = Frame("v3 · P5 field and figure · hidden-line isometric")
    ox, oy = 232, 132
    sp = 20
    N = 8
    # field: an isometric sea grid; lines further back drop a grey step, all clipped to the body
    for i in range(-N, N + 1):
        for a, b in ((iso(i * sp, -N * sp, 0, ox, oy), iso(i * sp, N * sp, 0, ox, oy)),
                     (iso(-N * sp, i * sp, 0, ox, oy), iso(N * sp, i * sp, 0, ox, oy))):
            c = clip_seg(a, b, 42, 186, 8, 472)
            if c:
                F.line(c[0], c[1], 1.0, G2 if abs(i) <= 4 else G1)
    # sweep: the beam's lit patch on the water, a hidden-line sector along its bearing
    R, Hh = 30, 84
    ang = math.radians(-40 + 140 * D["sweep"])
    half = math.radians(8)
    sector = [iso((R + 8) * math.cos(ang - half), (R + 8) * math.sin(ang - half), 0, ox, oy)]
    sector += [iso(96 * math.cos(ang + half * t / 6), 96 * math.sin(ang + half * t / 6), 0, ox, oy) for t in range(-6, 7)]
    sector += [iso((R + 8) * math.cos(ang + half), (R + 8) * math.sin(ang + half), 0, ox, oy)]
    F.loop(sector, G4, 1.2, fill=G0)
    # figure: the comb lens as a barrel of evenly spaced rings (count = lens focus), hidden-line
    rings = 3 + int(round(9 * D["lens"]))
    def ring(z, a0=0.0, a1=2 * math.pi, n=40):
        return [iso(R * math.cos(a0 + (a1 - a0) * k / n), R * math.sin(a0 + (a1 - a0) * k / n), z, ox, oy)
                for k in range(n + 1)]
    lo, hi = math.radians(-45), math.radians(135)
    F.poly(ring(0, lo, hi, 30) + ring(Hh, hi, lo + 2 * math.pi, 30), G0)
    # lit window: where the light faces now (sweep), a band on the barrel's near face
    wa = max(lo + math.radians(16), min(hi - math.radians(16), ang))
    w0, w1 = wa - math.radians(14), wa + math.radians(14)
    win = ring(Hh * 0.18, w0, w1, 8) + ring(Hh * 0.82, w1, w0, 8)
    F.poly(win, G2)
    for k in range(1, rings):
        z = Hh * k / rings
        F.ribbon(ring(z, lo, hi, 24), 1.0, G4)
    for a in (lo, hi):
        F.line(iso(R * math.cos(a), R * math.sin(a), 0, ox, oy), iso(R * math.cos(a), R * math.sin(a), Hh, ox, oy), 2.0, G7)
    F.ribbon(ring(0, lo, hi, 30), 2.0, G7)
    F.loop(ring(Hh, 0, 2 * math.pi, 48)[:-1], G7, 2.0, fill=G0)
    cx, cy = iso(0, 0, Hh, ox, oy)
    F.loop([(cx - 6, cy), (cx, cy - 3.5), (cx + 6, cy), (cx, cy + 3.5)], G5, 1.2, fill=G0)
    # strip: the pulse train as marks along the bottom, width = pulse width
    w = 4 + 18 * D["pulse"]
    for k in range(12):
        x = 24 + k * 37
        F.rect(x, 198, w, 8, G5 if k % 4 == 0 else G3)
    return F


# ---------------------------------------------------------------- v4
def v4() -> Frame:
    """P10 Voice field, star atlas: the comb's spectrum plotted as a star field on a conic chart."""
    F = Frame("v4 · P10 voice field · star atlas")
    px, py = 240, 560
    cols, rows = 12, 4               # harmonics 1..12, four trips round the comb
    th0, th1 = math.radians(-114), math.radians(-66)
    r0, r1 = 400, 512
    def at(c, r):
        th = th0 + (th1 - th0) * (c + 0.5) / cols
        rr = r1 - (r1 - r0) * (r + 0.5) / rows
        return (px + rr * math.cos(th), py + rr * math.sin(th))
    for r in range(rows + 1):
        rr = r1 - (r1 - r0) * r / rows
        F.ribbon(arc(px, py, rr, rr, th0, th1, 48), 1.0, G2)
    for c in range(0, cols + 1, 3):
        th = th0 + (th1 - th0) * c / cols
        F.line((px + r0 * math.cos(th), py + r0 * math.sin(th)), (px + r1 * math.cos(th), py + r1 * math.sin(th)), 1.0, G2)
    # magnitudes from the model: pulse width shapes the spectrum (a sinc with a dark lane at 1/width),
    # lens keeps energy through later trips (rows); fog would dim the high harmonics.
    g = FEEDBACK
    width = 0.04 + 0.5 * D["pulse"]
    stars = []
    for r in range(rows):
        for c in range(cols):
            k = c + 1
            x = math.pi * k * width
            spec = abs(math.sin(x) / x)
            fogcut = 1.0 / (1.0 + (k * D["fog"] * 0.6) ** 2)
            stars.append((c, r, spec * fogcut * g ** (r * 2.0)))
    mmax = max(m for *_, m in stars)
    # sweep: the beam's track, a hairline great circle from the fundamental, clipped to the chart
    ang = math.radians(-10 - 40 * D["sweep"])
    sx, sy = at(0, 0)
    c = clip_seg((sx + 12 * math.cos(ang), sy + 12 * math.sin(ang)), (sx + 400 * math.cos(ang), sy + 400 * math.sin(ang)), 40, 200, 0, 470)
    if c:
        F.line(c[0], c[1], 1.0, G4)
    col0 = [at(0, r) for r in range(rows)]
    for a, b in zip(col0, col0[1:]):
        d = math.dist(a, b)
        ux, uy = (b[0] - a[0]) / d, (b[1] - a[1]) / d
        F.line((a[0] + ux * 9, a[1] + uy * 9), (b[0] - ux * 9, b[1] - uy * 9), 1.0, G4)
    for c_, r, m in stars:
        m /= mmax
        x, y = at(c_, r)
        if m < 0.07:
            F.circle(x, y, 2.2, G0, G3, 1.0)          # past the limiting magnitude: hollow
            continue
        rad = 2.0 + 5.0 * math.sqrt(m)
        col = G7 if (c_ == 0 and r == 0) else (G5 if m > 0.3 else G4)
        F.circle(x, y, rad, col)
    for c_ in (0, 3, 6, 9):
        th = th0 + (th1 - th0) * (c_ + 0.5) / cols
        x, y = px + (r0 - 14) * math.cos(th), py + (r0 - 14) * math.sin(th)
        F.text(x - 4, y + 4, str(c_ + 1) if c_ else "f0", G4)
    F.text(352, 212, "harmonic chart", G4)
    return F


# ---------------------------------------------------------------- v5
def v5() -> Frame:
    """P14 Loom (stretch), engineering schematic: the comb's feedback loop weaving its delay line."""
    F = Frame("v5 · P14 loom · engineering schematic")
    y = 58
    F.text(16, y - 8, "in", G4)
    F.line((16, y), (46, y), 1.5, G4)
    F.circle(56, y, 9, G0, G5, 1.5)
    F.line((51, y), (61, y), 1.0, G5)
    F.line((56, y - 5), (56, y + 5), 1.0, G5)
    F.line((65, y), (88, y), 1.5, G4)
    F.loop([(88, y - 12), (150, y - 12), (150, y + 12), (88, y + 12)], G5, 1.5, fill=G0)
    F.text(108, y + 4, "z-T", G5)
    F.line((150, y), (460, y), 1.5, G4)
    F.text(444, y - 8, "out", G4)
    F.line((172, y), (172, y + 26), 1.5, G4)
    F.loop([(172, y + 40), (162, y + 26), (182, y + 26)], G5, 1.5, fill=G0)
    F.text(186, y + 38, "g", G5)
    F.line((172, y + 40), (172, y + 62), 1.5, G4)
    F.line((172, y + 62), (140, y + 62), 1.5, G4)
    F.loop([(100, y + 52), (140, y + 52), (140, y + 72), (100, y + 72)], G4, 1.2, fill=G0)
    F.text(110, y + 66, "fog", G4)
    F.line((100, y + 62), (56, y + 62), 1.5, G4)
    F.line((56, y + 62), (56, y + 9), 1.5, G4)
    # the cloth: warp threads are the delay line's taps; each trip round the loop weaves a row,
    # newest at the front. Oblique projection; slabs raised where the energy is.
    amps = echo_amps(floor=0.0, cap=4)
    warp = 12
    tx, ty = 214, 204
    ddx, ddy = 10, -17
    sp = 19
    pw = 1 + round(D["pulse"] * 8)
    start = 2
    shear = D["sweep"] * 4.0
    greys = [G7, G5, G4, G3]
    nrows = len(amps)
    for t in range(warp):
        a = (tx + t * sp + 6, ty - 2)
        b = (tx + t * sp + 6 + ddx * (nrows - 0.3), ty - 2 + ddy * (nrows - 0.3))
        F.line(a, b, 1.0, G1)
    for r in reversed(range(nrows)):
        ox = tx + ddx * r + shear * r
        oy = ty + ddy * r
        for t in range(warp):
            x = ox + t * sp
            lit = start <= t < start + pw
            if not lit:
                F.loop([(x, oy - 2), (x + 10, oy - 2), (x + 14, oy - 7), (x + 4, oy - 7)], G2, 1.0, fill=G0)
                continue
            hgt = 6 + 38 * amps[r]
            col = greys[r]
            F.loop([(x, oy), (x + 10, oy), (x + 10, oy - hgt), (x, oy - hgt)], col, 2.0 if r == 0 else 1.2, fill=G0)
            F.loop([(x + 10, oy), (x + 14, oy - 5), (x + 14, oy - hgt - 5), (x + 10, oy - hgt)], col, 1.0, fill=G0)
            F.loop([(x, oy - hgt), (x + 10, oy - hgt), (x + 14, oy - hgt - 5), (x + 4, oy - hgt - 5)], col, 1.0, fill=G0)
    # leader from the delay block to the cloth it describes
    F.line((119, y + 12), (119, y + 46), 1.0, G3) if False else None
    F.line((150, y + 4), (196, y + 4), 1.0, G0) if False else None
    F.line((200, 150), (226, 168), 1.0, G3)
    F.text(16, 172, "taps of z-T, last 4 trips", G4) if False else None
    F.text(70, 150, "delay line, 4 trips", G4)
    return F


def main():
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        out = HERE / name / "rest.svg"
        out.parent.mkdir(exist_ok=True)
        out.write_text(fn().svg(), encoding="utf-8")
        print(out)


if __name__ == "__main__":
    main()
