#!/usr/bin/env python3
"""Lathe subject pass 01: one rest-frame sketch per direction (v1..v5).

Each sketch is the rest frame of its subject at the definition's defaults
(cut 1.00, groove 0, wear 0, rumble 0), stock header kept, 480 x 220.
Sketches, not final frames: parts a control would move carry lathe_node_i ids
so the budget can be estimated; everything else is static artwork. Every line
is a thin closed ribbon or a closed outline, never an open stroke.

    python3 screens/lathe/passes/01-subject/sketch.py
"""
from __future__ import annotations

import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 480, 220

G0, G1, G2, G3, G4, G5, G6, BK = ("#CDCDCD", "#AFAFAF", "#969696", "#7D7D7D",
                                  "#646464", "#4B4B4B", "#323232", "#000000")
TITLES = ["cut", "groove", "wear", "rumble"]
VALUES = ["1.00", "0", "0", "0"]   # defaults: 0.5 * 8 ** (1/3) = 1.00, then 0, 0, 0
FONT = 'font-family="UniversNextPro-Light"'

# ---------------------------------------------------------------- the defaults
CUT = 1.0      # cutting level, x (0.5 .. 4.0)
GROOVE = 0.0   # 0 rim .. 1 label
WEAR = 0.0
RUMBLE = 0.0


def f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def soft(x: float, drive: float) -> float:
    """The cutter's saturation: unity-gain-ish tanh, harder as drive rises."""
    return math.tanh(x * drive) / math.tanh(drive) if drive > 0 else x


def signal(t: float) -> float:
    return (0.62 * math.sin(2 * math.pi * 3 * t) + 0.28 * math.sin(2 * math.pi * 7 * t + 1.1)
            + 0.12 * math.sin(2 * math.pi * 13 * t + 0.4))


class Frame:
    def __init__(self, palette) -> None:
        self.out: list[str] = []
        self.palette = palette

    def path(self, pts, fill=BK, stroke="none", sw=0.0, node=None, origin=None):
        clean = []
        for x, y in pts:
            p = (round(x, 2), round(y, 2))
            if not clean or math.dist(p, clean[-1]) >= 0.25:
                clean.append(p)
        while len(clean) > 2 and math.dist(clean[0], clean[-1]) < 0.4:
            clean.pop()
        assert 3 <= len(clean) <= 64, len(clean)
        tr = ""
        if origin is not None:
            ox, oy = origin
            clean = [(round(x - ox, 2), round(y - oy, 2)) for x, y in clean]
            assert all(abs(x) <= 64 and abs(y) <= 64 for x, y in clean), "mutable extent"
            tr = f' transform="matrix(1 0 0 1 {f(ox)} {f(oy)})"'
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in clean) + " Z"
        ident = f' id="lathe_node_{node}"' if node is not None else ""
        self.out.append(f'  <path{ident} d="{d}"{tr} fill="{fill}" stroke="{stroke}" stroke-width="{f(sw)}"/>')

    def ribbon(self, pts, w, fill, node=None, origin=None):
        """A line as a thin filled closed ribbon; long lines split into <= 31-point runs."""
        if len(pts) <= 31:
            self.path(ribbon_outline(pts, w), fill=fill, node=node, origin=origin)
            return
        i = 0
        while i < len(pts) - 1:
            self.path(ribbon_outline(pts[i:i + 31], w), fill=fill)
            i += 30

    def seg(self, a, b, w, fill):
        self.ribbon([a, b], w, fill)

    def dashed(self, a, b, w, fill, dash=8, gap=3, dot=3):
        """Chain line (centre line): long dash, gap, short dash, gap."""
        L = math.dist(a, b)
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        s = 0.0
        pattern = [(dash, True), (gap, False), (dot, True), (gap, False)]
        k = 0
        while s < L:
            ln, on = pattern[k % 4]
            e = min(L, s + ln)
            if on and e - s > 1:
                self.seg((a[0] + ux * s, a[1] + uy * s), (a[0] + ux * e, a[1] + uy * e), w, fill)
            s = e
            k += 1

    def rect(self, x, y, w, h, fill, stroke="none", sw=0.0):
        self.out.append(f'  <rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" fill="{fill}" '
                        f'stroke="{stroke}" stroke-width="{f(sw)}"/>')

    def text(self, x, y, s, fill=G3, size=10):
        assert len(s) <= 23
        self.out.append(f'  <text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{fill}" stroke="none" '
                        f'{FONT} font-size="{size}px">{s}</text>')

    def svg(self) -> str:
        head = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
            '  <g id="preview_canvas">',
            f'    <rect x="0" y="0" width="{W}" height="{H}" fill="#000000" stroke="none"/>',
            '  </g>',
            '  <g id="preview_header">',
        ]
        steps = [BK, G6, G5, G4, G3, G2, G1, G0]
        for k, c in enumerate(steps):
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
        pal = [f'  <path id="lathe_palette_{i}" d="M {700 + 10 * i} 300 L {704 + 10 * i} 300 L {704 + 10 * i} 304 Z" '
               f'fill="{c}" stroke="{c}" stroke-width="2"/>' for i, c in enumerate(self.palette)]
        return "\n".join(head + pal + self.out + ["</svg>", ""])


def ribbon_outline(pts, w):
    """Offset a polyline both ways by w/2 (mitred, clamped) and close it with flat ends."""
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


def ellipse(cx, cy, rx, ry, n=48, a0=0.0, a1=2 * math.pi, closed=True):
    m = n if closed else n - 1
    return [(cx + rx * math.cos(a0 + (a1 - a0) * t / m), cy + ry * math.sin(a0 + (a1 - a0) * t / m))
            for t in range(n)]


def clip_segment(p, q, poly):
    """Cyrus-Beck: clip segment p-q to a convex polygon (any winding)."""
    t0, t1 = 0.0, 1.0
    dx, dy = q[0] - p[0], q[1] - p[1]
    n = len(poly)
    area = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    sgn = 1 if area > 0 else -1
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        nx, ny = sgn * (b[1] - a[1]), -sgn * (b[0] - a[0])   # outward normal
        num = nx * (p[0] - a[0]) + ny * (p[1] - a[1])
        den = nx * dx + ny * dy
        if den == 0:
            if num > 0:
                return None
            continue
        t = -num / den
        if den > 0:
            t1 = min(t1, t)
        else:
            t0 = max(t0, t)
    if t0 >= t1:
        return None
    return (p[0] + dx * t0, p[1] + dy * t0), (p[0] + dx * t1, p[1] + dy * t1)


def hatch(F, poly, spacing, fill, w=1.0, angle=45):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    a = math.radians(angle)
    ux, uy = math.cos(a), -math.sin(a)
    nx, ny = -uy, ux
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    R = math.hypot(max(xs) - min(xs), max(ys) - min(ys))
    k = -R
    while k <= R:
        p = (cx + nx * k - ux * R, cy + ny * k - uy * R)
        q = (cx + nx * k + ux * R, cy + ny * k + uy * R)
        s = clip_segment(p, q, poly)
        if s and math.dist(*s) > 2.5:
            F.seg(s[0], s[1], w, fill)
        k += spacing


# ================================================================ v1
def v1() -> Frame:
    """P1 section drawing, typeset diagram: the stylus mid-cut, the lacquer blank in section."""
    F = Frame([G0, G1, G2, G4])
    S = 232                    # stylus centre line (fixed; the blank moves under it with groove)
    top, coat, sub = 104, 126, 142
    pitch, half = 22, 8.5
    depth = 12 + 5 * math.log2(CUT)                    # cut: groove depth (12 px at 1.00)
    flat = max(0.0, (CUT - 1.0) / 3.0) * 8 + 1.4        # cut: the V bottoms out (flat) as it saturates
    rim = S - 3 * pitch - 8 - GROOVE * 160  # groove: the rim slides out left as the cut moves in
    lead = 452 - GROOVE * 170               # groove: the smooth inner lacquer runs out toward the label
    cut_x = []
    x = S - pitch
    while x - half > rim + 4:
        cut_x.insert(0, x)
        x -= pitch

    # platter (rumble: shape of this line, flat at 0)
    F.ribbon([(28 + 8 * i, 150 + RUMBLE * 10 * math.sin(i / 52 * 2 * math.pi)) for i in range(53)], 1.2, G5)
    F.text(30, 164, "platter", G4)

    # aluminium core, in section
    core = [(rim + 4, coat), (lead, coat), (lead, sub), (rim + 4, sub), (rim, sub - 4), (rim, coat + 4)]
    F.path(core, fill=G6, stroke=G4, sw=1.2)

    def vee(x, inset=0.0):
        return [(x - half + inset * 1.5, top - inset), (x - flat / 2 + inset, top + depth - inset * 2),
                (x + flat / 2 - inset, top + depth - inset * 2), (x + half - inset * 1.5, top - inset)]

    # lacquer coat with the cut grooves, outlined as one closed section
    surf = [(rim, coat), (rim, top + 4), (rim + 4, top)]
    for x in cut_x:
        surf += vee(x)
    surf += vee(S) + [(lead, top), (lead, coat)]
    F.path(surf, fill=BK, stroke=G3, sw=1.5)
    hatch(F, [(rim + 6, top + 2), (lead - 2, top + 2), (lead - 2, coat - 1.5), (rim + 6, coat - 1.5)], 5, G6, 1.0)
    for x in cut_x + [S]:      # keep hatching out of the grooves
        F.path(vee(x, 0.8), fill=BK)

    # the groove being cut now (node 0: cut reshapes it)
    g = [(S - 16, top)] + vee(S) + [(S + 16, top)]
    F.ribbon(g, 2.0, G1, node=0, origin=(S, top))

    # the stylus, in section: shank, taper, flat tip (node 1, rides with cut depth)
    tip = top + depth - 1.5
    st = [(S - 8, 28), (S + 8, 28), (S + 8, 70), (S + 1.4, tip), (S - 1.4, tip), (S - 8, 70)]
    F.path(st, fill=BK, stroke=G0, sw=2.0, node=1)
    F.seg((S, 36), (S, 66), 1.0, G4)          # the stylus' heater wire, a hairline inside

    # swarf thread coiling off the cut (static in this sketch)
    sw = []
    for i in range(31):
        t = i / 30
        a = t * 5.5 * math.pi
        sw.append((S + 12 + 44 * t + 5 * math.cos(a), top - 10 - 36 * t + 4 * math.sin(a)))
    F.ribbon(sw, 1.5, G3)

    # break line where the section is cut off (typeset convention)
    zz = [(lead + 3, top - 6), (lead + 3, top + 8), (lead + 8, top + 12), (lead - 2, top + 18), (lead + 3, top + 22),
          (lead + 3, sub + 6)]
    if lead < 470:
        F.ribbon(zz, 1.0, G4)

    # typeset labels and leaders
    F.seg((S + 11, 44), (S + 44, 44), 1.0, G4)
    F.text(S + 48, 47, "stylus", G2)
    F.seg((S + 62, top - 44), (S + 80, top - 44), 1.0, G4)
    F.text(S + 84, top - 41, "swarf", G3)
    F.seg((340, coat - 6), (340, 180), 1.0, G4)
    F.text(323, 192, "lacquer", G3)
    F.seg((410, sub - 5), (410, 180), 1.0, G4)
    F.text(386, 192, "aluminium", G3)
    F.seg((rim + 1, top + 10), (rim - 10, 180), 1.0, G4)
    F.text(rim - 22, 192, "rim", G3)
    F.text(30, 210, "fig. 1  cut, in section", G3)
    return F


# ================================================================ v2
def v2() -> Frame:
    """P2 diagram + trace, orthographic elevation: the lathe side-on, the played groove beside it."""
    F = Frame([G0, G1, G3, G5])
    # ---- left: side elevation (structure) -------------------------------
    ground = 186
    F.seg((14, ground), (232, ground), 1.0, G5)
    F.rect(26, 150, 196, 34, BK, G4, 1.5)                 # plinth
    F.seg((34, 167), (214, 167), 1.0, G6)
    F.rect(40, 139, 168, 11, BK, G3, 1.5)                  # platter
    F.rect(44, 134.5, 160, 4.5, BK, G2, 1.5)               # lacquer blank
    F.rect(122, 126, 4, 8.5, BK, G3, 1.2)                  # spindle
    F.dashed((124, 40), (124, 196), 1.0, G5)               # centre line
    F.rect(34, 48, 196, 6, BK, G3, 1.5)                    # carriage rail, cantilevered over the disc
    F.rect(212, 54, 12, 96, BK, G4, 1.5)                   # its column on the plinth

    c = 56 + GROOVE * 56                                   # groove: carriage from the rim toward the spindle
    head = [(c - 13, 54), (c + 13, 54), (c + 13, 96), (c + 6, 102), (c + 6, 118), (c + 1, 131), (c - 1, 131),
            (c - 6, 118), (c - 6, 102), (c - 13, 96)]
    F.path(head, fill=BK, stroke=G0, sw=2.0, node=0)       # cutter head, the brightest thing
    F.seg((c - 13, 76), (c + 13, 76), 1.0, G4)
    # suction nozzle beside the stylus
    F.path([(c + 9, 122), (c + 22, 116), (c + 34, 116), (c + 34, 121), (c + 23, 121), (c + 11, 127)],
           fill=BK, stroke=G3, sw=1.2)
    # dimension: radius of the cut, rim to stylus (typeset ticks, no arrows)
    F.seg((44, 200), (c, 200), 1.0, G4)
    F.seg((44, 196), (44, 204), 1.0, G4)
    F.seg((c, 196), (c, 204), 1.0, G4)
    F.text(14, 44, "elevation", G3)
    F.text(130, 210, "spindle", G4)

    # ---- right: the groove as played (trace) --------------------------------
    x0, x1, yc, amp = 262, 462, 116, 34
    # rumble: the groove's centre line wanders (node 1; flat at 0)
    cl = [(x0 + (x1 - x0) * i / 30, yc + RUMBLE * 12 * math.sin(i / 30 * 2 * math.pi * 1.2)) for i in range(31)]
    F.ribbon(cl[:16], 1.0, G5, node=1, origin=(x0 + 50, yc))
    F.ribbon(cl[15:], 1.0, G5, node=2, origin=(x0 + 150, yc))
    # cut: the trace's amplitude and how flat its peaks are (nodes 3, 4)
    drive = 0.6 + 1.4 * math.log2(CUT / 0.5) / 3
    pts = [(x0 + (x1 - x0) * i / 60, yc - amp * soft(signal(i / 60), drive) * min(1.6, CUT ** 0.35)) for i in range(61)]
    F.ribbon(pts[:31], 2.0, G1, node=3, origin=(x0 + 50, yc))
    F.ribbon(pts[30:], 2.0, G1, node=4, origin=(x0 + 150, yc))
    # wear: crackle ticks along the trace (count; none at 0)
    for k in range(int(round(WEAR * 16))):
        xx = x0 + 8 + 12 * k
        F.seg((xx, yc - 50), (xx, yc - 42), 1.2, G2)
    # amplitude scale, elevation style: ticks at +-1 and 0
    for yy, lab in ((yc - amp, "+1"), (yc, "0"), (yc + amp, "-1")):
        F.seg((x0 - 10, yy), (x0 - 4, yy), 1.0, G4)
    F.text(262, 44, "groove wall, played", G3)
    F.text(262, 186, "one turn", G4)
    F.seg((x0, 176), (x1, 176), 1.0, G5)
    F.seg((x0, 172), (x0, 180), 1.0, G5)
    F.seg((x1, 172), (x1, 180), 1.0, G5)
    return F


# ================================================================ v3
def v3() -> Frame:
    """P3 trace as subject, survey plan: the groove from above, a sector of the side as a site plan."""
    F = Frame([G0, G2, G4, G5])
    C = (240, 650)                     # disc centre, far below the frame
    Rg = 516                           # the groove being cut
    pitch = 11

    def arcpts(R, x_from, x_to, n, wob=0.0, phase=0.0, dx=0.0):
        out = []
        for i in range(n):
            x = x_from + (x_to - x_from) * i / (n - 1)
            u = (x - C[0] - dx) / R
            if abs(u) >= 1:
                continue
            y = C[1] - R * math.sqrt(1 - u * u)
            y -= wob * signal(i / (n - 1) * 1.6 + phase)
            out.append((x, y))
        return out

    # survey grid crosses (sparse, hairline)
    for gx in range(60, 461, 100):
        for gy in (60, 180):
            F.seg((gx - 3, gy), (gx + 3, gy), 1.0, G5)
            F.seg((gx, gy - 3), (gx, gy + 3), 1.0, G5)

    # outer turns, already cut (rumble: the set shifts off-centre, node 5; concentric at 0)
    for k in range(1, 6):
        R = Rg + pitch * k
        pts = arcpts(R, 24, 456, 60, wob=1.6, phase=0.37 * k, dx=RUMBLE * 24)
        F.ribbon(pts, 1.2, G4 if k < 3 else G5)
    # the label edge (groove: rises toward the cut as it moves inward)
    Rl = 430 + GROOVE * 64
    lab = arcpts(Rl, 120, 360, 40)
    if lab and min(p[1] for p in lab) < 220:
        F.ribbon([p for p in lab if p[1] < 226], 1.5, G3, node=4)

    # the groove being cut, bright, modulated by the signal (cut: shape), three nodes of <= 128 px
    drive = 0.6 + 1.4 * math.log2(CUT / 0.5) / 3
    pts = []
    for i in range(91):
        x = 55 + 370 * i / 90
        u = (x - C[0]) / Rg
        y = C[1] - Rg * math.sqrt(1 - u * u) - 5.5 * soft(signal(i / 90 * 1.6), drive)
        pts.append((x, y))
    for j in range(3):
        run = pts[j * 30:j * 30 + 31]
        mid = run[15]
        F.ribbon(run, 2.5, G0, node=j, origin=(round(mid[0]), round(mid[1])))

    # chainage along the groove: ticks and station labels
    for i, s in ((0, "0+00"), (30, "0+40"), (60, "0+80"), (90, "1+20")):
        x, y = pts[i]
        F.seg((x, y + 8), (x, y + 13), 1.0, G3)
        F.text(x - 9, y + 25, s, G3)
    # labels and the title block
    F.text(28, 66, "rim", G3)
    F.text(372, 210, "scale", G4)
    F.rect(404, 202, 12, 4, G3)
    F.rect(416, 202, 12, 4, BK, G3, 1.0)
    F.rect(428, 202, 12, 4, G3)
    F.text(444, 210, "1 mm", G4)
    F.text(28, 210, "plan, side a", G3)
    return F


# ================================================================ v4
def v4() -> Frame:
    """P4 stack in depth, patent section: five slices of the side, rim to label, the one you hear lit."""
    F = Frame([G0, G1, G3, G5, G6])
    n = 5
    dx, dy = 36, -21
    w, h = 214, 15
    x0, y0 = 40, 160                # front slice, lower left
    current = round(GROOVE * (n - 1))
    drive = 0.6 + 1.4 * math.log2(CUT / 0.5) / 3

    def edge(i, xs, amp):
        """Top edge of slice i: the groove's modulation, shorter waves toward the label."""
        cyc = 3 + 1.6 * i
        pts = []
        for k in range(61):
            t = k / 60
            v = soft(signal(t * cyc / 3), drive) if i == current else signal(t * cyc / 3)
            pts.append((xs + w * t, amp * v))
        return pts

    for i in reversed(range(n)):
        xs = x0 + dx * i
        ys = y0 + dy * i + RUMBLE * 10 * math.sin(i * 1.4)     # rumble: slices ride a slow wave (position)
        lit = i == current
        amp = 4.5 * (min(1.6, CUT ** 0.35) if lit else 1.0)
        top = [(x, ys - 4 + y) for x, y in edge(i, xs, amp)]
        depth = (10, -6)
        # the slice's receding top face, then its front face in section
        back = [(x + depth[0], y + depth[1]) for x, y in top[::6]]
        F.path([top[0]] + back + [top[-1]], fill=BK, stroke=G5, sw=1.0)
        face = top[::2] + [(xs + w, ys + h), (xs, ys + h)]
        F.path(face, fill=BK, stroke=G0 if lit else G3, sw=2.0 if lit else 1.2, node=10 + i)
        poly = [(xs + 2, ys + 3), (xs + w - 2, ys + 3), (xs + w - 2, ys + h - 2), (xs + 2, ys + h - 2)]
        hatch(F, poly, 4.0, G2 if lit else G5, 1.0)
        if lit:   # node 0/1: the lit slice's groove edge, which cut reshapes (two <= 128 px runs)
            F.ribbon(top[:31], 2.0, G0, node=0, origin=(round(top[15][0]), round(ys)))
            F.ribbon(top[30:], 2.0, G0, node=1, origin=(round(top[45][0]), round(ys)))
        # reference numeral with its leader, at the slice's right end
        F.seg((xs + w + 3, ys + 8), (xs + w + 16, ys + 2), 1.0, G4)
        F.text(xs + w + 18, ys + 4, str(10 + 2 * i), G2 if lit else G3)

    F.text(40, 206, "fig. 2", G2)
    F.text(18, 168, "rim", G4)
    F.text(146, 80, "label", G4)
    return F


# ================================================================ v5
def v5() -> Frame:
    """P11 instrument stack (stretch), hidden-line isometric: the lathe itself, assembled."""
    F = Frame([G0, G2, G3, G4, G6])
    k = 1.12
    X0, Y0 = 248, 138
    c30, s30 = math.cos(math.radians(30)), 0.5

    def P(x, y, z):
        return (X0 + (x - y) * c30 * k, Y0 + (x + y) * s30 * k - z * k)

    def box(x0, x1, y0, y1, z0, z1, edge=G4, sw=1.5, node=None, top_edge=None):
        """Hidden-line box: the three faces the camera sees, black, grey edges."""
        right = [P(x1, y0, z0), P(x1, y1, z0), P(x1, y1, z1), P(x1, y0, z1)]   # +x face
        front = [P(x0, y1, z0), P(x1, y1, z0), P(x1, y1, z1), P(x0, y1, z1)]   # +y face
        topf = [P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1)]
        F.path(right, fill=BK, stroke=edge, sw=sw)
        F.path(front, fill=BK, stroke=edge, sw=sw)
        F.path(topf, fill=BK, stroke=top_edge or edge, sw=sw, node=node)

    def circle3(cx, cy, z, r, a0=0.0, a1=2 * math.pi, n=48, closed=True):
        m = n if closed else n - 1
        return [P(cx + r * math.cos(a0 + (a1 - a0) * i / m), cy + r * math.sin(a0 + (a1 - a0) * i / m), z)
                for i in range(n)]

    def cylinder(r, z0, z1, edge, sw=1.5, top_fill=BK):
        a0, a1 = math.radians(-45), math.radians(135)       # the half that faces the camera
        band = circle3(0, 0, z1, r, a0, a1, 25, False) + circle3(0, 0, z0, r, a1, a0, 25, False)
        F.path(band, fill=BK, stroke=edge, sw=sw)
        F.path(circle3(0, 0, z1, r), fill=top_fill, stroke=edge, sw=sw)

    # plinth, the far rail, the platter and the lacquer
    box(-62, 62, -72, 60, 0, 16, edge=G4)
    xc = -36 + GROOVE * 28                                  # groove: carriage from the rim toward the spindle
    box(-74, 44, -70, -62, 16, 28, edge=G4)                 # rail along the back
    box(xc - 9, xc + 9, -72, -60, 28, 44, edge=G3)          # carriage on the rail
    cylinder(46, 16, 24, G4)
    F.path(circle3(0, 0, 25.5, 43), fill=BK, stroke=G2, sw=1.5, node=6)   # lacquer top (rumble: turns in plane)
    # the cut band: turns from the rim in to the stylus (hairlines, >= 3 px apart)
    for r in (39, 33):
        if r > abs(xc) + 1:
            F.path(circle3(0, 0, 25.5, r, n=40), fill="none", stroke=G5, sw=1.5)
    F.path(circle3(0, 0, 25.5, 9, n=24), fill=BK, stroke=G4, sw=1.2)      # centre, uncut
    sp = circle3(0, 0, 25.5, 1.8, n=12)
    F.path(sp + [P(0, 0, 32)], fill=BK, stroke=G3, sw=1.2)                # spindle stub
    # wear: specks of dust on the lacquer (count; none at 0)
    for i in range(int(round(WEAR * 14))):
        a = i * 2.4
        F.rect(*P(28 * math.cos(a), 28 * math.sin(a), 25.5), 3, 3, G3)
    # the arm over the disc and the cutter head (node 0: the brightest part)
    box(xc - 3, xc + 3, -62, -4, 40, 44, edge=G3)
    box(xc - 7, xc + 7, -7, 7, 31, 52, edge=G0, sw=2.0, node=0)
    st = [P(xc - 1.5, 6, 31), P(xc + 1.5, 6, 31), P(xc + 0.3, 3, 25.8), P(xc - 0.3, 3, 25.8)]
    F.path(st, fill=BK, stroke=G0, sw=1.5, node=1)
    # cut: the swarf thread coiling from the stylus to the suction tube (scale, node 2)
    hx, hy = P(xc + 9, 8, 30)
    coil = []
    for i in range(30):
        t = i / 29
        a = t * 5 * math.pi
        coil.append((hx + 16 * t + 4 * math.cos(a), hy - 3 - 12 * t + 2.2 * math.sin(a)))
    F.ribbon(coil, 1.2, G3, node=2, origin=(round(hx), round(hy)))
    tube = [P(xc + 10, 0, 44), P(xc + 26, 0, 58), P(xc + 26, 0, 61), P(xc + 10, 0, 47)]
    F.path(tube, fill=BK, stroke=G4, sw=1.2)
    # labels, as on an assembly drawing
    F.text(332, 196, "lathe, assembled", G3)
    lx, ly = P(xc - 7, 7, 46)
    F.seg((lx - 3, ly), (lx - 40, ly), 1.0, G4)
    F.text(lx - 94, ly + 3, "cutter head", G2)
    return F


def main() -> None:
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        d = HERE / name
        d.mkdir(exist_ok=True)
        (d / "rest.svg").write_text(fn().svg())
        print(d / "rest.svg")


if __name__ == "__main__":
    main()
