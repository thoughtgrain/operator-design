#!/usr/bin/env python3
"""Lathe subject pass 02: one rest-frame sketch per direction (v1..v5).

Each sketch is the rest frame of its subject at the definition's defaults
(cut 1.00, groove 0, wear 0, rumble 0), stock header kept, 480 x 220.
No text below the header. Parts a control would move carry lathe_node_i ids
so the budget can be estimated; everything else is static artwork. Every
line is a thin closed ribbon or a closed outline, never an open stroke.
3D subjects (v3, v4, v5) are modelled in world units and projected through
one camera each.

    python3 screens/lathe/passes/02-subject/sketch.py
"""
from __future__ import annotations

import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 480, 220

G0, G1, G2, G3, G4, G5, G6, BK = ("#CDCDCD", "#AFAFAF", "#969696", "#7D7D7D",
                                  "#646464", "#4B4B4B", "#323232", "#000000")
TITLES = ["cut", "groove", "wear", "rumble"]
VALUES = ["1.00", "0", "0", "0"]
FONT = 'font-family="UniversNextPro-Light"'

# line weights (craft.md): hairline, line, subject
HAIR, LINE, SUBJ = 1.0, 1.5, 2.0

# ---------------------------------------------------------------- the defaults
CUT = 1.0      # cutting level, x (0.5 .. 4.0)
GROOVE = 0.0   # 0 rim .. 1 label
WEAR = 0.0
RUMBLE = 0.0
DRIVE = 0.6 + 1.4 * math.log2(CUT / 0.5) / 3     # how hard the tanh bites


def f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def soft(x: float, drive: float = DRIVE) -> float:
    """The cutter's saturation: unity-ish tanh, crests flatten as drive rises."""
    return math.tanh(x * drive * 1.6) / math.tanh(drive * 1.6)


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
            if not clean or math.dist(p, clean[-1]) >= 0.3:
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

    def outline(self, pts, stroke, sw=LINE, fill=BK, node=None, origin=None):
        """A closed outline; long ones are drawn as a black fill plus ribbon runs."""
        if len(pts) <= 60:
            self.path(pts, fill=fill, stroke=stroke, sw=sw, node=node, origin=origin)
            return
        step = max(1, math.ceil(len(pts) / 60))
        if fill != "none":
            self.path(pts[::step], fill=fill)
        self.ribbon(pts + [pts[0]], sw, stroke)

    def ribbon(self, pts, w, fill, node=None, origin=None):
        """A line as a thin filled closed ribbon; long lines split into <= 31-point runs."""
        if len(pts) < 2:
            return
        if len(pts) <= 31:
            self.path(ribbon_outline(pts, w), fill=fill, node=node, origin=origin)
            return
        i = 0
        while i < len(pts) - 1:
            self.path(ribbon_outline(pts[i:i + 31], w), fill=fill)
            i += 30

    def seg(self, a, b, w, fill):
        self.ribbon([a, b], w, fill)

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


def clip_segment(p, q, poly):
    """Cyrus-Beck: clip segment p-q to a convex polygon (any winding)."""
    t0, t1 = 0.0, 1.0
    dx, dy = q[0] - p[0], q[1] - p[1]
    n = len(poly)
    area = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    sgn = 1 if area > 0 else -1
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        nx, ny = sgn * (b[1] - a[1]), -sgn * (b[0] - a[0])
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


def hatch(F, poly, fill=G5, spacing=4.5, w=HAIR, inset=1.6):
    """45-degree hairlines clipped to a convex region, >= 3 px clear between lines."""
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    # pull the region in a little so hatching never touches the outline
    shrunk = []
    for x, y in poly:
        d = math.hypot(x - cx, y - cy) or 1
        shrunk.append((x - (x - cx) / d * inset, y - (y - cy) / d * inset))
    xs = [p[0] for p in shrunk]
    ys = [p[1] for p in shrunk]
    R = math.hypot(max(xs) - min(xs), max(ys) - min(ys))
    s2 = math.sqrt(0.5)
    ux, uy = s2, -s2           # along the hatch (rising to the right)
    nx, ny = s2, s2
    k = -R - ((cx * nx + cy * ny) % spacing)
    while k <= R:
        p = (cx + nx * k - ux * R, cy + ny * k - uy * R)
        q = (cx + nx * k + ux * R, cy + ny * k + uy * R)
        s = clip_segment(p, q, shrunk)
        if s and math.dist(*s) > 2.5:
            F.seg(s[0], s[1], w, fill)
        k += spacing


def ellipse(cx, cy, rx, ry, n=48, a0=0.0):
    return [(cx + rx * math.cos(a0 + 2 * math.pi * t / n), cy + ry * math.sin(a0 + 2 * math.pi * t / n))
            for t in range(n)]


class Camera:
    """One pinhole camera: position, look-at point, focal length, screen centre. World z is up."""

    def __init__(self, pos, look, focal, centre):
        self.p = pos
        fx, fy, fz = (look[i] - pos[i] for i in range(3))
        L = math.sqrt(fx * fx + fy * fy + fz * fz)
        self.fw = (fx / L, fy / L, fz / L)
        rx, ry, rz = self.fw[1] * 1 - self.fw[2] * 0, self.fw[2] * 0 - self.fw[0] * 1, 0.0  # fw x up(0,0,1)
        L = math.hypot(rx, ry)
        self.rt = (rx / L, ry / L, 0.0)
        a, b = self.rt, self.fw                                  # up = right x forward
        self.up = (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
        self.F = focal
        self.c = centre

    def depth(self, q):
        d = [q[i] - self.p[i] for i in range(3)]
        return sum(d[i] * self.fw[i] for i in range(3))

    def __call__(self, q):
        d = [q[i] - self.p[i] for i in range(3)]
        x = sum(d[i] * self.rt[i] for i in range(3))
        y = sum(d[i] * self.up[i] for i in range(3))
        z = sum(d[i] * self.fw[i] for i in range(3))
        return (self.c[0] + self.F * x / z, self.c[1] - self.F * y / z)


# ================================================================ v1
def v1() -> Frame:
    """The lathe itself, in profile: the workpiece turning between centres, its profile cut by the tool.

    Single-weight contour: every part of the machine is one Line-weight contour; the only
    heavier line is the turned profile (the subject), the only lighter ones the centre line,
    the chip and (with wear) chatter marks.
    """
    F = Frame([G0, G2, G3, G5])
    ax = 116                                      # spindle axis
    raw = 34                                      # radius of the stock still to be turned
    x_chuck, x_tool, x_end = 136, 236, 366        # chuck face, cutting point, work end face
    base = 22 - GROOVE * 12                       # groove: the cross-slide feeds in, the turned radius shrinks
    amp = 8.5 * min(1.6, CUT ** 0.35)             # cut: depth of the profile; crests flatten (soft)

    def r(x):
        t = (x - x_tool) / (x_end - x_tool)
        u = 0.08 + 0.84 * t
        return base + amp * soft(0.72 * math.sin(2 * math.pi * 3 * u) + 0.3 * math.sin(2 * math.pi * 7 * u + 1.1))

    # bed and ways
    F.outline([(20, 178), (460, 178), (460, 186), (20, 186)], G4)
    F.outline([(30, 186), (450, 186), (446, 206), (34, 206)], G5)
    # headstock and its spindle nose
    F.outline([(22, 56), (114, 56), (114, 178), (22, 178)], G4)
    F.outline([(36, 70), (100, 70), (100, 104), (36, 104)], G5, sw=HAIR)
    for y in (82, 92):
        F.seg((44, y), (92, y), HAIR, G5)
    F.outline([(114, ax - 22), (120, ax - 22), (120, ax + 22), (114, ax + 22)], G4)
    # chuck body and jaws gripping the raw stock
    F.outline([(120, ax - 46), (130, ax - 46), (130, ax + 46), (120, ax + 46)], G3)
    for s in (-1, 1):
        y0 = ax + s * raw
        F.outline([(130, y0 + s * 2), (x_chuck + 8, y0 + s * 2), (x_chuck + 8, y0 + s * 12),
                   (130, y0 + s * 14)], G3)
    # raw stock, not yet turned
    F.outline([(x_chuck, ax - raw), (x_tool, ax - raw), (x_tool, ax + raw), (x_chuck, ax + raw)], G4)
    # the turned profile: the subject (node 0 would carry it, re-keyed by cut and groove)
    xs = [x_tool + (x_end - x_tool) * i / 29 for i in range(30)]
    top = [(x, ax - r(x)) for x in xs]
    bot = [(x, ax + r(x)) for x in reversed(xs)]
    prof = [(x_tool - 1.2, ax - raw)] + top + bot + [(x_tool - 1.2, ax + raw)]
    F.path(prof, fill=BK, stroke=G0, sw=SUBJ, node=0)
    # tailstock: dead centre in the end of the work, quill, body, handwheel boss
    F.outline([(x_end, ax - 3), (x_end + 18, ax - 9), (x_end + 18, ax + 9), (x_end, ax + 3)], G3)
    F.outline([(x_end + 18, ax - 13), (x_end + 52, ax - 13), (x_end + 52, ax + 13), (x_end + 18, ax + 13)], G4)
    F.outline([(x_end + 52, ax - 30), (x_end + 92, ax - 30), (x_end + 92, 178), (x_end + 46, 178),
               (x_end + 46, ax + 22), (x_end + 52, ax + 22)], G4)
    F.outline([(x_end + 92, ax - 6), (x_end + 102, ax - 6), (x_end + 102, ax + 6), (x_end + 92, ax + 6)], G5)
    # carriage, cross-slide and tool post below the work (node 1: moves with groove)
    tip_y = ax + r(x_tool)
    F.outline([(x_tool - 34, 168), (x_tool + 58, 168), (x_tool + 58, 178), (x_tool - 34, 178)], G4)
    F.outline([(x_tool + 2, tip_y + 22), (x_tool + 44, tip_y + 22), (x_tool + 44, 168),
               (x_tool + 2, 168)], G4)
    tool = [(x_tool + 0.6, tip_y + 0.6), (x_tool + 3, tip_y + 0.6), (x_tool + 30, tip_y + 10),
            (x_tool + 30, tip_y + 20), (x_tool + 6, tip_y + 20)]
    F.outline(tool, G2, node=1)
    # the chip curling off the cutting point, one hairline helix
    chip = []
    for i in range(30):
        t = i / 29
        a = t * 4.4 * math.pi
        chip.append((x_tool - 4 - 30 * t + 4.5 * math.sin(a), tip_y + 10 + 18 * t + 4.5 * math.cos(a) - 4.5))
    F.ribbon(chip, HAIR, G3)
    # centre line, chain, over everything
    x = 104
    pat = [(12, True), (3, False), (3, True), (3, False)]
    k = 0
    while x < 470:
        ln, on = pat[k % 4]
        e = min(470, x + ln)
        if on:
            F.seg((x, ax), (e, ax), HAIR, G5)
        x, k = e, k + 1
    return F


# ================================================================ v2
def v2() -> Frame:
    """The cutter head on its lead screw, side-on, drawn as hatched masses; the stylus the one bright body."""
    F = Frame([G0, G3, G5])
    c = 150 + GROOVE * 190          # groove: the carriage runs along the screw, rim (left) to label (right)
    surf = 170                      # top of the lacquer coat
    # the lead screw, with its thread drawn as ribs, and bearings at both ends
    F.outline([(28, 41), (452, 41), (452, 53), (28, 53)], G4)
    x = 34
    while x < 446:
        F.seg((x, 51.5), (x + 6, 42.5), HAIR, G5)
        x += 5
    for bx in (16, 452):
        F.outline([(bx, 32), (bx + 12, 32), (bx + 12, 62), (bx, 62)], G3)
        hatch(F, [(bx, 32), (bx + 12, 32), (bx + 12, 62), (bx, 62)], G5)
    # platter slab: lacquer coat over the aluminium core, in section, with the label step at the right
    coat = [(24, surf), (380, surf), (380, surf + 7), (24, surf + 7)]
    core = [(24, surf + 7), (456, surf + 7), (456, surf + 24), (24, surf + 24)]
    F.outline(core, G4)
    hatch(F, core, G6, spacing=4.5)
    lab = [(380, surf - 4), (456, surf - 4), (456, surf + 7), (380, surf + 7)]
    F.outline(lab, G4)
    F.outline([(412, surf - 16), (420, surf - 16), (420, surf - 4), (412, surf - 4)], G4)  # spindle
    # the coat, with the turns already cut (rim side, behind the stylus) as small notches
    top = [(24, surf)]
    gx = 34
    while gx < c - 8:
        top += [(gx - 2.5, surf), (gx - 0.4, surf + 3.5), (gx + 0.4, surf + 3.5), (gx + 2.5, surf)]
        gx += 9
    top += [(c - 4, surf), (c - 0.6, surf + 5.5), (c + 0.6, surf + 5.5), (c + 4, surf), (380, surf),
            (380, surf + 7), (24, surf + 7)]
    F.path(top, fill=BK, stroke=G3, sw=LINE)
    # carriage riding the screw (a hatched mass)
    car = [(c - 32, 34), (c + 32, 34), (c + 32, 62), (c - 32, 62)]
    F.outline(car, G3)
    hatch(F, car, G5)
    # column down to the head
    col = [(c - 9, 62), (c + 9, 62), (c + 9, 90), (c - 9, 90)]
    F.outline(col, G4)
    # the head: hatched mass with a window onto the armature
    head = [(c - 38, 90), (c + 38, 90), (c + 38, 138), (c - 38, 138)]
    F.outline(head, G3)
    hatch(F, head, G5)
    win = [(c - 15, 98), (c + 15, 98), (c + 15, 132), (c - 15, 132)]
    F.outline(win, G4)
    for s in (-1, 1):                                         # the stop pads the armature swings against
        pad = [(c + s * 13, 110), (c + s * 9, 110), (c + s * 9, 118), (c + s * 13, 118)]
        F.outline(pad, G4, sw=HAIR)
    # holder below the head
    hold = [(c - 12, 138), (c + 12, 138), (c + 6, 152), (c - 6, 152)]
    F.outline(hold, G4)
    hatch(F, hold, G5, spacing=4.5, inset=2.2)
    # suction nozzle beside the stylus
    noz = [(c + 30, 138), (c + 38, 138), (c + 16, surf - 7), (c + 9, surf - 7)]
    F.outline(noz, G4)
    # the stylus: armature from its pivot in the window to the cutting tip (node 0: cut turns it)
    piv = (c, 112)
    ang = 0.0
    sty = [(-2.5, -4), (2.5, -4), (3.5, 24), (1.6, 58), (0.6, 63), (-0.6, 63), (-1.6, 58), (-3.5, 24)]
    pts = [(piv[0] + x * math.cos(ang) - y * math.sin(ang), piv[1] + x * math.sin(ang) + y * math.cos(ang))
           for x, y in sty]
    F.path(pts, fill=G0, stroke=G0, sw=1.0, node=0, origin=piv)
    F.outline(ellipse(piv[0], piv[1], 3.2, 3.2, 12), G0, sw=HAIR)
    # the drive coil around the armature: hairline turns across the window
    for y in (114, 119, 124):
        F.seg((c - 8, y), (c - 4.5, y), HAIR, G4)
        F.seg((c + 4.5, y), (c + 8, y), HAIR, G4)
    return F


# ================================================================ v3
def v3() -> Frame:
    """The lacquer surface, very close, at grazing light: grooves running away from the eye.

    Edge-lit silhouette: the coat is a black mass; only the lips of the grooves catch the light.
    The near edge of the field is the cut face of the coat, a silhouette with its V notches,
    its top edge lit. The camera looks down at the surface, so there's no horizon: the field
    simply runs out of light at the top of the frame.
    """
    F = Frame([G0, G2, G3, G5])
    cam = Camera((0, 0, 1.0), (0, 4.2, -0.35), 330, (240, 112))
    pitch, half, depth = 0.5, 0.15, 0.13
    shift = -GROOVE * pitch * 4          # groove: the field slides left; the rim leaves, more turns come in
    y0, y1 = 1.75, 9.0

    def wig(k, y):
        t = (y - y0) / (y1 - y0)
        return 0.055 * soft(signal(0.13 * k + 0.55 * t), DRIVE if k == 0 else 1.0)

    rim_x = pitch * 3.5 + shift          # rim bevel: the field ends here at groove 0
    ks = [k for k in range(-12, 8) if k * pitch + half < rim_x]

    def lip(k, side, y):
        return (k * pitch + wig(k, y) + side * half, y, 0.0)

    # receding lips: lit lip a Line, shaded lip a hairline; each stops before it would come
    # within 3 px of its neighbour, and the brighter near part fades to a dimmer far part
    for k in ks:
        for side in (-1, 1):
            if k == 0:
                w, near_c, far_c = (SUBJ, G0, G0) if side < 0 else (LINE, G2, G2)
            else:
                w, near_c, far_c = (LINE, G3, G4) if side < 0 else (HAIR, G4, G5)
            pts, cols = [], []
            for i in range(44):
                y = y0 + (y1 - y0) * (i / 43) ** 1.5
                p = cam(lip(k, side, y))
                gap = abs(cam((pitch - 2 * half, y, 0))[0] - cam((0, y, 0))[0])
                if gap < 3.6 or p[1] < 24:
                    break
                if -1 <= p[0] <= 481:
                    pts.append(p)
                    cols.append(near_c if i < 26 else far_c)
            if len(pts) < 2:
                continue
            cut = cols.index(far_c) if far_c in cols and far_c != near_c else len(pts)
            node = 0 if (k == 0 and side < 0) else None
            if cut >= 2:
                F.ribbon(pts[:cut], w, near_c, node=node if cut <= 31 else None)
            if len(pts) - cut >= 2:
                F.ribbon(pts[cut - 1:], w, far_c)
    # the rim bevel: the field's right edge, a lit lip falling away
    rim = []
    for i in range(20):
        y = y0 + (y1 - y0) * (i / 19) ** 1.5
        p = cam((rim_x, y, 0))
        if p[1] < 24:
            break
        rim.append(p)
    if len(rim) >= 2 and rim[0][0] < 480:
        F.ribbon([p for p in rim if p[0] <= 480], LINE, G3)
    # near cut face, a silhouette: black mass below its lit, notched top edge
    edge = []
    for k in ks:
        gx = k * pitch + wig(k, y0)
        for px, pz in ((-half, 0), (-0.025, -depth), (0.025, -depth), (half, 0)):
            p = cam((gx + px, y0, pz))
            if -6 < p[0] < 486:
                edge.append(p)
    rb = cam((rim_x + 0.14, y0, -0.2))
    edge += [cam((rim_x, y0, 0)), rb]
    body = [(-2, edge[0][1])] + edge + [(rb[0], 214), (-2, 214)]
    F.path(body, fill=BK)
    F.ribbon([(-1, edge[0][1])] + edge, LINE, G3)
    F.seg(rb, (rb[0], 212), HAIR, G5)
    return F


# ================================================================ v4
def v4() -> Frame:
    """The cut playing back: the disc on the platter, close and low, the tonearm reading it."""
    F = Frame([G0, G2, G3, G5])
    cam = Camera((-0.2, -2.55, 1.05), (0.18, 0.1, -0.1), 430, (214, 122))
    R, Rl = 1.0, 0.31
    rp = 0.93 - GROOVE * 0.56            # groove: where the stylus reads, rim to label
    zt, zb, zd = 0.0, -0.13, 0.012

    def ring(rad, z, n=56, a0=0.0, a1=2 * math.pi):
        m = n if abs(a1 - a0 - 2 * math.pi) < 1e-9 else n - 1
        return [cam((rad * math.cos(a0 + (a1 - a0) * i / m), rad * math.sin(a0 + (a1 - a0) * i / m), z))
                for i in range(n)]

    # platter: a cylinder, its front half side as a band with strobe marks
    side = ring(1.04, zt, 28, math.pi, 2 * math.pi) + ring(1.04, zb, 28, 2 * math.pi, math.pi)
    F.outline(side, G4)
    for i in range(1, 24):
        a = math.pi + math.pi * i / 24
        p = cam((1.04 * math.cos(a), 1.04 * math.sin(a), zt - 0.03))
        q = cam((1.04 * math.cos(a), 1.04 * math.sin(a), zb + 0.03))
        if math.dist(p, q) > 3:
            F.seg(p, q, HAIR, G5)
    F.outline(ring(1.04, zt), G4)
    # the disc, its grooves as hairline rings spaced >= 3 px at the narrowest
    F.outline(ring(R, zd), G3)
    rad = 0.93
    while rad > Rl + 0.08:
        F.outline(ring(rad, zd, 60), G5, sw=HAIR, fill="none")
        rad -= 0.09
    F.outline(ring(Rl, zd + 0.002, 44), G4)
    F.outline(ring(0.07, zd + 0.002, 20), G5, sw=HAIR, fill="none")
    sp = ring(0.022, zd, 7, 0, math.pi) + ring(0.022, zd + 0.1, 7, math.pi, 0)
    F.outline(sp, G3)
    # tonearm geometry: pivot back right, the stylus on radius rp
    P = (1.3, 0.5)
    L = 1.36
    d = math.hypot(*P)
    a = (rp * rp - L * L + d * d) / (2 * d)
    hh = math.sqrt(max(0.0, rp * rp - a * a))
    bx, by = a * P[0] / d, a * P[1] / d
    S = (bx + hh * P[1] / d, by - hh * P[0] / d)
    # the groove being read: the bright arc running into the stylus
    th = math.atan2(S[1], S[0])
    arc = [cam((rp * math.cos(th - 0.9 + 0.03 * i), rp * math.sin(th - 0.9 + 0.03 * i), zd)) for i in range(31)]
    F.ribbon(arc, SUBJ, G0, node=0)
    u = ((S[0] - P[0]) / L, (S[1] - P[1]) / L)
    v = (-u[1], u[0])
    zarm = 0.2
    # base: a short cylinder on the plinth
    base = ring(0.16, zb, 1)  # placeholder to keep the signature simple
    bpts = [cam((P[0] + 0.15 * math.cos(t), P[1] + 0.15 * math.sin(t), zb - 0.05)) for t in
            [math.pi + math.pi * i / 14 for i in range(15)]]
    bpts += [cam((P[0] + 0.15 * math.cos(t), P[1] + 0.15 * math.sin(t), zarm - 0.06)) for t in
             [2 * math.pi - math.pi * i / 14 for i in range(15)]]
    F.outline(bpts, G4)
    F.outline([cam((P[0] + 0.15 * math.cos(t), P[1] + 0.15 * math.sin(t), zarm - 0.06)) for t in
               [2 * math.pi * i / 32 for i in range(32)]], G4)
    # counterweight: a short cylinder on the arm's tail
    cwc = (P[0] - u[0] * 0.3, P[1] - u[1] * 0.3)
    cwp = []
    for s, z in ((-1, 1), (1, 1), (1, -1), (-1, -1)):
        cwp.append(cam((cwc[0] + u[0] * 0.09 * s, cwc[1] + u[1] * 0.09 * s, zarm + 0.075 * z)))
    F.outline([cwp[0], cwp[1], cwp[2], cwp[3]], G3)
    # arm tube: a hollow ribbon from pivot to headshell
    tube = []
    for i in range(26):
        t = i / 25
        tube.append(cam((P[0] - u[0] * 0.2 + u[0] * (L * 0.88 + 0.2) * t,
                         P[1] - u[1] * 0.2 + u[1] * (L * 0.88 + 0.2) * t, zarm)))
    F.ribbon(tube, 4.0, G2)
    F.ribbon(tube[1:-1], 1.2, BK)
    # headshell plate and cartridge down to the stylus
    hs = []
    for du, dv in ((L * 0.86, -0.05), (L * 0.86, 0.06), (L + 0.05, 0.06), (L + 0.05, -0.05)):
        hs.append(cam((P[0] + u[0] * du + v[0] * dv, P[1] + u[1] * du + v[1] * dv, zarm - 0.02)))
    cart = []
    for du, dv, z in ((L * 0.93, -0.035, zarm - 0.03), (L * 0.93, 0.045, zarm - 0.03),
                      (L + 0.01, 0.045, zd + 0.035), (L - 0.0, -0.035, zd + 0.035)):
        cart.append(cam((P[0] + u[0] * du + v[0] * dv, P[1] + u[1] * du + v[1] * dv, z)))
    F.outline(cart, G3)
    F.outline(hs, G2)
    # cueing post at the rest
    rest = [cam(p) for p in ((1.5, -0.55, zb - 0.05), (1.56, -0.55, zb - 0.05), (1.56, -0.55, zarm), (1.5, -0.55, zarm))]
    F.outline(rest, G5)
    return F


# ================================================================ v5
def v5() -> Frame:
    """A specimen of the cut: one length of groove in a block of lacquer on aluminium, hidden-line 3D.

    Every knob does to it what it would do to the real thing: cut sinks and widens the groove and
    flattens its swings, groove packs the same swings shorter (inner turns move slower under the
    stylus), wear knocks chips out of the lips, rumble heaves the block on its bed.
    """
    F = Frame([G0, G2, G3, G5])
    cam = Camera((-1.6, -5.6, 3.9), (3.1, 1.0, 0.2), 470, (236, 118))
    Lx, Wy = 6.4, 2.2
    zc, zt = 0.55, 0.95
    gy = Wy / 2
    half = 0.25 * min(1.5, CUT ** 0.3)      # cut: the groove gets wider and deeper
    deep = 0.26 * min(1.5, CUT ** 0.3)
    lam = 1.0 - GROOVE * 0.45               # groove: wavelength shortens toward the label
    amp = 0.2
    pitch = 0.78

    def gyx(x, k=0):
        if k:
            return gy + k * pitch + 0.05 * signal(x / Lx * 0.7 + 0.3 * k)
        return gy + amp * soft(signal((x / Lx) / lam * 0.9 + 0.05))

    p = cam
    sil = [p((0, 0, 0)), p((Lx, 0, 0)), p((Lx, 0, zt)), p((Lx, Wy, zt)), p((0, Wy, zt)), p((0, Wy, 0))]
    F.path(sil, fill=BK)
    # left end face, in section: outline with the V notches, coat line, core hatched
    end = [(0, 0, 0), (0, Wy, 0), (0, Wy, zt)]
    for k in (1, 0, -1):
        c0 = gyx(0, k)
        h0, d0 = (half, deep) if k == 0 else (0.11, 0.12)
        end += [(0, c0 + h0, zt), (0, c0 + 0.02, zt - d0), (0, c0 - 0.02, zt - d0), (0, c0 - h0, zt)]
    end += [(0, 0, zt)]
    F.path([p(q) for q in end], fill=BK, stroke=G3, sw=LINE)
    core_end = [p((0, 0.08, 0.08)), p((0, Wy - 0.08, 0.08)), p((0, Wy - 0.08, zc - 0.06)), p((0, 0.08, zc - 0.06))]
    hatch(F, core_end, G5, spacing=4.5, inset=0.5)
    F.seg(p((0, 0, zc)), p((0, Wy, zc)), HAIR, G4)
    # front face, its coat line
    F.path([p((0, 0, 0)), p((Lx, 0, 0)), p((Lx, 0, zt)), p((0, 0, zt))], fill=BK, stroke=G3, sw=LINE)
    F.seg(p((0.02, 0, zc)), p((Lx - 0.02, 0, zc)), HAIR, G4)
    # top face
    F.path([p((0, 0, zt)), p((Lx, 0, zt)), p((Lx, Wy, zt)), p((0, Wy, zt))], fill=BK, stroke=G3, sw=LINE)
    # the right end breaks off: the far end face isn't seen, a break mark on the near corner
    xs = [Lx * i / 30 for i in range(31)]
    # neighbouring turns, quieter: their two lips as hairlines
    for k in (-1, 1):
        for s in (-1, 1):
            F.ribbon([p((x, gyx(x, k) + s * 0.11, zt)) for x in xs], HAIR, G4)
    # the groove: floor hairline, near lip a Line, far lip (the lit one) the subject
    F.ribbon([p((x, gyx(x), zt - deep)) for x in xs], HAIR, G5)
    F.ribbon([p((x, gyx(x) - half, zt)) for x in xs], LINE, G2)
    F.ribbon([p((x, gyx(x) + half, zt)) for x in xs], SUBJ, G0, node=0)
    return F


def main() -> None:
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        d = HERE / name
        d.mkdir(exist_ok=True)
        (d / "rest.svg").write_text(fn().svg())
        print(d / "rest.svg")


if __name__ == "__main__":
    main()
