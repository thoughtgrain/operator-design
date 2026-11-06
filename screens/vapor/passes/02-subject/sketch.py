#!/usr/bin/env python3
"""Vapor subject pass 02: five rest-frame sketches, one per direction.

v1 exploded view        the speaking machine: bellows, reed, throat tube and lip iris, pulled apart on one axis
v2 single-weight contour the head cut down the middle while it sings: tongue, palate, throat, larynx
v3 hatched mass         a sung breath fogged onto a cold window pane, drips running from it
v4 edge-lit silhouette  the lips at the frame's edge and the breath leaving them into cold air
v5 detailed line art    vapor itself: a breath ring of vapor rising off a round "oo" mouthpiece

All frames show vapor's defaults: vowel a, breath 25 %, throat 1.00, glide 60 ms (0.4147).
Static artwork only (sketches); bound nodes come in the frames pass. 3D parts are modelled
and projected through one camera per variant (craft.md, Think in 3D).

    python3 screens/vapor/passes/02-subject/sketch.py
"""
from __future__ import annotations

import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent

C1, C2, C3, C4, C5, C6, C7 = "#CDCDCD", "#AFAFAF", "#969696", "#7D7D7D", "#646464", "#4B4B4B", "#323232"
BLACK = "#000000"
HAIR, LINE, SUBJ = 1.0, 1.5, 2.0

# defaults (definition.json), as normalised knob positions
VOWEL = 0.5     # a
BREATH = 0.25
THROAT = 0.3333  # ratio 1.00
GLIDE = 0.4147   # 60 ms
RATIO = 0.75 + 0.75 * THROAT

# vowel targets along u-o-a-e-i, each as (openness, frontness, rounding)
VOWELS = [(0.15, 0.0, 1.0), (0.45, 0.2, 0.9), (1.0, 0.45, 0.0), (0.45, 0.8, 0.0), (0.12, 1.0, 0.0)]


def vowel_at(v):
    """Interpolate (open, front, round) at a knob position 0..1 along u-o-a-e-i."""
    x = v * 4
    i = min(int(x), 3)
    t = x - i
    a, b = VOWELS[i], VOWELS[i + 1]
    return tuple(a[k] + (b[k] - a[k]) * t for k in range(3))


def f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# ------------------------------------------------------------------ frame + drawing helpers
class Frame:
    def __init__(self) -> None:
        self.parts: list[str] = []

    def add(self, s):
        self.parts.append(s)

    def poly(self, pts, stroke="none", sw=0.0, fill="none"):
        pts = dedupe(pts, closed=True)
        if len(pts) < 3:
            return
        for chunk in [pts] if len(pts) <= 64 else [pts[::math.ceil(len(pts) / 64)]]:
            d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in chunk) + " Z"
            sw_s = f' stroke-width="{f(sw)}"' if stroke != "none" else ' stroke-width="0"'
            self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}"{sw_s}/>')

    def line(self, pts, w, col):
        """An open line, drawn as a thin closed ribbon."""
        pts = dedupe(pts, closed=False)
        if len(pts) < 2:
            return
        for chunk in chunks(pts, 31):
            self.poly(ribbon_pts(chunk, w), fill=col)

    def svg(self):
        return HEADER + "\n".join("  " + p for p in self.parts) + "\n</svg>\n"


def dedupe(pts, closed):
    out = []
    for p in pts:
        p = (round(p[0], 2), round(p[1], 2))
        if not out or math.dist(out[-1], p) >= 0.4:
            out.append(p)
    if closed and len(out) > 2 and math.dist(out[0], out[-1]) < 0.4:
        out.pop()
    # drop near-reversals
    clean = []
    for p in out:
        if len(clean) >= 2:
            a, b = clean[-2], clean[-1]
            v1 = (b[0] - a[0], b[1] - a[1]); v2 = (p[0] - b[0], p[1] - b[1])
            l1, l2 = math.hypot(*v1), math.hypot(*v2)
            if l1 and l2 and (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2) < -0.995:
                clean.pop()
        clean.append(p)
    return clean


def chunks(pts, n):
    i = 0
    while i < len(pts) - 1:
        yield pts[i:i + n]
        i += n - 1


def ribbon_pts(pts, w):
    h = w / 2
    left, right = [], []
    for i, p in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        if 0 < i < len(pts) - 1:
            d1 = (p[0] - a[0], p[1] - a[1]); l1 = math.hypot(*d1) or 1
            d2 = (b[0] - p[0], b[1] - p[1]); l2 = math.hypot(*d2) or 1
            n1 = (-d1[1] / l1, d1[0] / l1); n2 = (-d2[1] / l2, d2[0] / l2)
            mx, my = n1[0] + n2[0], n1[1] + n2[1]
            ml = math.hypot(mx, my) or 1
            mx, my = mx / ml, my / ml
            cos = mx * n1[0] + my * n1[1]
            k = 1 / max(cos, 0.5)
            nx, ny = mx * k, my * k
        else:
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy) or 1
            nx, ny = -dy / L, dx / L
        left.append((p[0] + nx * h, p[1] + ny * h))
        right.append((p[0] - nx * h, p[1] - ny * h))
    return left + right[::-1]


def hatch(fr, loops, spacing=4.0, col=C5, w=HAIR, clip_y=(21, 220), phase=0.0):
    """45-degree hairlines, `spacing` px apart (perpendicular), clipped to the loops (even-odd)."""
    allp = [p for lp in loops for p in lp]
    lo = min(x + y for x, y in allp); hi = max(x + y for x, y in allp)
    step = spacing * math.sqrt(2)
    c = math.floor((lo - phase) / step) * step + phase + step
    while c < hi:
        xs = []
        for lp in loops:
            n = len(lp)
            for i in range(n):
                (x0, y0), (x1, y1) = lp[i], lp[(i + 1) % n]
                s0, s1 = x0 + y0 - c, x1 + y1 - c
                if (s0 < 0) != (s1 < 0):
                    t = s0 / (s0 - s1)
                    xs.append(x0 + (x1 - x0) * t)
        xs.sort()
        for a, b in zip(xs[0::2], xs[1::2]):
            p, q = (a, c - a), (b, c - b)
            # clip to the body
            if p[1] > q[1]:
                p, q = q, p
            # p is upper (smaller y); along the line y decreases as x increases
            y0, y1 = clip_y
            if q[1] < y0 or p[1] > y1:
                continue
            if p[1] < y0:
                p = (c - y0, y0)
            if q[1] > y1:
                q = (c - y1, y1)
            if math.dist(p, q) >= 1.5:
                fr.line([p, q], w, col)
        c += step


def ellipse(cx, cy, rx, ry, n=48, a0=0.0, a1=2 * math.pi, rot=0.0):
    pts = []
    cr, sr = math.cos(rot), math.sin(rot)
    for i in range(n + 1 if a1 - a0 < 2 * math.pi - 1e-6 else n):
        a = a0 + (a1 - a0) * i / (n if a1 - a0 < 2 * math.pi - 1e-6 else n)
        x, y = rx * math.cos(a), ry * math.sin(a)
        pts.append((cx + x * cr - y * sr, cy + x * sr + y * cr))
    return pts


def smooth(pts, n=6, closed=False):
    """Catmull-Rom through the points."""
    out = []
    m = len(pts)
    rng = range(m) if closed else range(m - 1)
    for i in rng:
        p0 = pts[(i - 1) % m] if closed else pts[max(i - 1, 0)]
        p1 = pts[i]
        p2 = pts[(i + 1) % m] if closed else pts[i + 1]
        p3 = pts[(i + 2) % m] if closed else pts[min(i + 2, m - 1)]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(2)))
    if not closed:
        out.append(pts[-1])
    return out


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))


# ------------------------------------------------------------------ 3D
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def mul(a, k): return (a[0] * k, a[1] * k, a[2] * k)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def norm(a):
    l = math.sqrt(dot(a, a)) or 1
    return (a[0] / l, a[1] / l, a[2] / l)


class Cam:
    """One camera per scene: eye, look-at, focal length in px, screen point the look-at lands on. World y is up."""

    def __init__(self, eye, target, focal, cx, cy):
        self.eye = eye
        self.fw = norm(sub(target, eye))
        self.rt = norm(cross(self.fw, (0, 1, 0)))
        self.up = cross(self.rt, self.fw)
        self.f, self.cx, self.cy = focal, cx, cy

    def p(self, q):
        d = sub(q, self.eye)
        z = dot(d, self.fw)
        return (self.cx + self.f * dot(d, self.rt) / z, self.cy - self.f * dot(d, self.up) / z)

    def depth(self, q):
        return dot(sub(q, self.eye), self.fw)

    def ps(self, qs):
        return [self.p(q) for q in qs]


def circle3(c, u, v, r, n=40, a0=0.0, a1=2 * math.pi):
    full = a1 - a0 >= 2 * math.pi - 1e-6
    cnt = n if full else n + 1
    return [add(c, add(mul(u, r * math.cos(a0 + (a1 - a0) * i / n)), mul(v, r * math.sin(a0 + (a1 - a0) * i / n))))
            for i in range(cnt)]


# ------------------------------------------------------------------ header
LABELS = ["vowel", "breath", "throat", "glide"]
VALUES = ["a", "25", "1.00", "60ms"]


def header_svg():
    steps = ["#000000", "#323232", "#4B4B4B", "#646464", "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD"]
    out = ['  <g id="preview_canvas">', '    <rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>', "  </g>",
           '  <g id="preview_header">']
    for i, c in enumerate(steps):
        out.append(f'    <rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
    for i, lab in enumerate(LABELS):
        tcol = "#CBCBCB" if i < 2 else "#000000"
        out.append(f'    <text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{tcol}" stroke="none" '
                   f'font-family="UniversNextPro-Light" font-size="10px">{lab}</text>')
    for i, val in enumerate(VALUES):
        tcol = "#CBCBCB" if i < 2 else "#000000"
        out.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{tcol}" stroke="none" '
                   f'font-family="UniversNextPro-Light" font-size="20px">{val}</text>')
    out.append("  </g>")
    return "\n".join(out) + "\n"


HEADER = ('<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">\n' + header_svg())


# ================================================================== v1 exploded view: the speaking machine
def v1():
    """Kempelen-style speaking machine pulled apart along its air axis (world x), seen from front-right
    above. Left to right: bellows (breath opens it), reed block (the glottal pulse), telescoping throat
    tube (throat draws it out), lip iris (vowel shapes its aperture) with its closing spring (glide = coils)."""
    fr = Frame()
    cam = Cam(eye=(60, 150, 560), target=(10, -8, 0), focal=560, cx=246, cy=118)
    op, fw, rd = vowel_at(VOWEL)

    def P(q):
        return cam.p(q)

    # dash-dot axis through the parts (exploded-view convention)
    x0, x1 = -235, 250
    n = 0
    x = x0
    while x < x1:
        L = 9 if n % 2 == 0 else 2
        fr.line([P((x, 0, 0)), P((min(x + L, x1), 0, 0))], HAIR, C6)
        x += L + 4
        n += 1

    def box(xa, xb, hy, hz, edge=C4, inner=None, bright=False):
        """Hidden-line box from xa..xb, half-sizes hy (up), hz (toward camera)."""
        V = {(i, j, k): (xa if i == 0 else xb, (-hy if j == 0 else hy), (-hz if k == 0 else hz))
             for i in (0, 1) for j in (0, 1) for k in (0, 1)}
        faces = [  # visible faces from front-right-above: +z, +y, +x
            [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)],
            [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)],
            [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)],
        ]
        for fc in faces:
            fr.poly([P(V[k]) for k in fc], stroke=edge, sw=LINE, fill=BLACK)
        return V

    # ---- bellows: back board, pleated leather, front board. breath opens it.
    depth = 26 + 64 * BREATH          # world length of the pleated part
    bx1 = -150                         # front board (fixed, nozzle side)
    bx0 = bx1 - depth
    hy, hz = 40, 30
    pleats = 7
    # back board
    box(bx0 - 6, bx0, hy + 4, hz + 4, edge=C4)
    # pleats: alternating in/out frames, drawn back to front, as hidden-line ribbons of leather
    for i in range(pleats):
        xa = bx0 + depth * i / pleats
        xb = bx0 + depth * (i + 1) / pleats
        inset = 6 if i % 2 == 0 else 0
        inset_b = 0 if i % 2 == 0 else 6
        ya, za, yb, zb = hy - inset, hz - inset, hy - inset_b, hz - inset_b
        top = [P((xa, ya, -za)), P((xb, yb, -zb)), P((xb, yb, zb)), P((xa, ya, za))]
        front = [P((xa, -ya, za)), P((xb, -yb, zb)), P((xb, yb, zb)), P((xa, ya, za))]
        fr.poly(top, stroke=C5, sw=HAIR, fill=BLACK)
        fr.poly(front, stroke=C5, sw=HAIR, fill=BLACK)
    box(bx1, bx1 + 6, hy + 4, hz + 4, edge=C4)
    # nozzle
    noz = [(bx1 + 6, 0, 0), (bx1 + 26, 0, 0)]
    for r_ in (7,):
        c0 = circle3((bx1 + 26, 0, 0), (0, 1, 0), (0, 0, 1), r_, 24)
        fr.poly(cam.ps(c0), stroke=C4, sw=HAIR, fill=BLACK)

    # ---- reed block (glottis): a small housing with the reed tongue showing through a slot
    rx0, rx1 = -96, -62
    V = box(rx0, rx1, 14, 14, edge=C4)
    # reed slot on the top face and the reed tongue (pulse) lifted a little
    slot = [P((rx0 + 6, 14, -3)), P((rx1 - 6, 14, -3)), P((rx1 - 6, 14, 3)), P((rx0 + 6, 14, 3))]
    fr.poly(slot, stroke=C5, sw=HAIR, fill=BLACK)
    fr.line([P((rx0 + 8, 14, 0)), P((rx1 - 8, 19, 0))], LINE, C3)

    # ---- throat tube: three telescoping sections, total length follows throat
    tx0 = -36
    tlen = 120 * RATIO / 1.0 * 0.75 + 20     # world length at this ratio
    radii = [12, 15, 18]
    seg = tlen / 3
    for i, r_ in enumerate(radii):
        xa = tx0 + i * (seg + 10)
        xb = xa + seg
        # cylinder: silhouette lines + near end ellipse, far end hidden-line
        c_a = circle3((xa, 0, 0), (0, 1, 0), (0, 0, 1), r_, 36)
        c_b = circle3((xb, 0, 0), (0, 1, 0), (0, 0, 1), r_, 36)
        pa, pb = cam.ps(c_a), cam.ps(c_b)
        # body as the hull of both ends
        hull = convex_hull(pa + pb)
        fr.poly(hull, stroke=C4, sw=LINE, fill=BLACK)
        fr.poly(pb, stroke=C4, sw=HAIR, fill=BLACK)
        # inner bore ring on the open end
        fr.poly(cam.ps(circle3((xb, 0, 0), (0, 1, 0), (0, 0, 1), r_ - 4, 30)), stroke=C6, sw=HAIR)
        # seam rings along the section
        for s in (0.33, 0.66):
            xs_ = xa + seg * s
            ring = cam.ps(circle3((xs_, 0, 0), (0, 1, 0), (0, 0, 1), r_, 36, -math.pi / 2, math.pi / 2))
            # only the half facing the camera (z > 0)
            fr.line(cam.ps(circle3((xs_, 0, 0), (0, 1, 0), (0, 0, 1), r_, 24, 0.0, math.pi)), HAIR, C6)
    tend = tx0 + 3 * seg + 20

    # ---- mouth bell: a flaring cone, then the lip iris plate in front
    mx0 = tend + 14
    mx1 = mx0 + 46
    rings = []
    for i in range(6):
        t = i / 5
        xr = mx0 + (mx1 - mx0) * t
        rr = 16 + 22 * t ** 1.6
        rings.append((xr, rr))
    outline_pts = []
    for xr, rr in rings:
        outline_pts += cam.ps(circle3((xr, 0, 0), (0, 1, 0), (0, 0, 1), rr, 36))
    fr.poly(convex_hull(outline_pts), stroke=C4, sw=LINE, fill=BLACK)
    for xr, rr in rings[1:-1]:
        fr.line(cam.ps(circle3((xr, 0, 0), (0, 1, 0), (0, 0, 1), rr, 24, 0.0, math.pi)), HAIR, C6)
    fr.poly(cam.ps(circle3((mx1, 0, 0), (0, 1, 0), (0, 0, 1), 38, 40)), stroke=C4, sw=HAIR, fill=BLACK)

    # lip iris: a flat plate, its aperture shaped by the vowel (round small u, open a, wide slit i)
    ix = mx1 + 34
    plate = circle3((ix, 0, 0), (0, 1, 0), (0, 0, 1), 40, 48)
    fr.poly(cam.ps(plate), stroke=C4, sw=LINE, fill=BLACK)
    # plate thickness edge
    fr.line(cam.ps(circle3((ix + 4, 0, 0), (0, 1, 0), (0, 0, 1), 40, 24, -0.2, math.pi * 0.62)), HAIR, C5)
    # iris leaves: radial hairlines from aperture to rim
    ay = 6 + 22 * op * (1 - 0.5 * fw)          # aperture half-height (up)
    az = 6 + 22 * op + 10 * fw - 4 * rd        # aperture half-width (across)
    ap = [(ix, ay * math.sin(a), az * math.cos(a)) for a in [2 * math.pi * k / 40 for k in range(40)]]
    for k in range(10):
        a = 2 * math.pi * k / 10 + 0.3
        p_in = (ix, ay * math.sin(a), az * math.cos(a))
        p_out = (ix, 36 * math.sin(a + 0.5), 36 * math.cos(a + 0.5))
        fr.line([P(p_in), P(p_out)], HAIR, C6)
    fr.poly(cam.ps(ap), stroke=C1, sw=SUBJ, fill=BLACK)
    # glide: a coil spring that closes the iris back to "oo"; more coils = softer = slower
    coils = 3 + round(12 * GLIDE)
    sx0, sx1 = ix - 30, ix - 4
    sy = -50
    spts = []
    N = coils * 12
    for i in range(N + 1):
        t = i / N
        a = 2 * math.pi * coils * t
        spts.append(P((sx0 + (sx1 - sx0) * t, sy + 5 * math.sin(a), 5 * math.cos(a))))
    fr.line([P((sx0 - 6, sy, 0)), P((sx0, sy, 0))], LINE, C4)
    fr.line(spts, HAIR, C3)
    fr.line([P((sx1, sy, 0)), P((ix, -38, 0))], LINE, C4)
    return fr


def convex_hull(pts):
    pts = sorted(set((round(x, 2), round(y, 2)) for x, y in pts))
    if len(pts) < 3:
        return pts

    def cr(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


# ================================================================== v2 cutaway: the head singing, cut down the middle
def v2():
    """Mid-sagittal cutaway of a singer's head, single 1.5 px contour throughout. The tongue (the
    vowel) is the bright line; the larynx rides down the throat as the tract lengthens; breath is
    dashes of air rising through the airway; glide is the hatched sweep back to the "oo" tongue."""
    fr = Frame()
    W = LINE
    ox, oy, s = 150, 22, 1.0
    op, fw, rd = vowel_at(VOWEL)
    lar = 166 + 30 * THROAT            # larynx (vocal folds) height on screen: 166 .. 196

    def T(pts):
        return [(ox + x * s, oy + y * s) for x, y in pts]

    jaw = 4 + 10 * op                  # jaw drop in px at the chin
    lipf = 6 * rd - 2 * fw             # lip protrusion
    # outer profile: back of neck, skull, face; lower face drops with the jaw
    upper = [(40, 196), (42, 170), (34, 142), (16, 116), (8, 84), (14, 48), (40, 18), (80, 6), (122, 8),
             (150, 22), (164, 44), (166, 58), (163, 66), (170, 80), (180, 94), (172, 99), (164, 100),
             (166, 108), (170 + lipf, 113), (166 + lipf, 117)]
    lower = [(166 + lipf, 119 + jaw * 0.6), (170 + lipf, 124 + jaw * 0.7), (160, 132 + jaw * 0.8),
             (164, 146 + jaw), (158, 156 + jaw), (138, 160 + jaw * 0.6), (118, 162), (106, 172), (108, 186), (104, 198)]
    fr.line(T(smooth(upper, 6)), W, C3)
    fr.line(T(smooth(lower, 6)), W, C3)
    # the cut face of the skull: an inner contour that follows the cranium, a calm second line
    skull = [(30, 120), (20, 86), (26, 52), (48, 28), (84, 18), (118, 20), (142, 34), (152, 52), (148, 64)]
    fr.line(T(smooth(skull, 6)), W, C6)
    # spine column behind the airway: vertebra bodies as stacked outlines
    for i in range(5):
        y0 = 118 + i * 16
        fr.poly(T([(52, y0), (70, y0 + 1), (70, y0 + 12), (52, y0 + 13)]), stroke=C7, sw=W, fill=BLACK)
    # nasal cavity
    nasal = [(160, 96), (140, 84), (112, 76), (94, 82), (92, 94), (124, 94), (156, 100)]
    fr.poly(T(smooth(nasal, 5, closed=True)), stroke=C5, sw=W, fill=BLACK)
    # hard palate (roof of the mouth) and soft palate hanging back to the uvula
    palate = [(160, 104), (146, 100), (124, 99), (104, 102), (94, 110), (90, 118)]
    fr.line(T(smooth(palate, 6)), W, C4)
    # pharynx back wall down to the oesophagus
    wall = [(88, 92), (80, 108), (78, 130), (80, 152), (82, 176), (82, 198)]
    fr.line(T(smooth(wall, 6)), W, C5)

    # tongue: dorsum shape from the vowel. high back (u), low and retracted (a), high front (i)
    def tongue(o, fr_):
        hy = 104 + 26 * o - 2 * fr_          # height of the dorsum's crest
        hx = 104 + 40 * fr_                  # crest position (front/back)
        root = 96 + 10 * fr_ - 6 * o         # tongue root x (retracted for open vowels)
        tip = (156, 122 + jaw * 0.6)
        return [tip, (148, 116 + 8 * o), (hx + 14, hy + 2), (hx, hy), (hx - 16, hy + 6 + 4 * o),
                (root + 2, 136), (root, 150), (root + 4, lar - 12 - 30 * THROAT * 0)]
    cur = smooth(tongue(op, fw), 6)
    # glide: hatched sweep between the onset tongue (u) and where it's heading, as far back as glide reaches
    u = VOWELS[0]
    g = GLIDE
    ghost_o = op + (u[0] - op) * g
    ghost_f = fw + (u[1] - fw) * g
    gh = smooth(tongue(ghost_o, ghost_f), 6)
    region = cur + gh[::-1]
    hatch(fr, [T(region)], spacing=3.5, col=C6)
    fr.line(T(gh), HAIR, C5)
    # floor of the mouth and the jaw
    floor_ = [(156, 128 + jaw * 0.6), (140, 142 + jaw * 0.6), (118, 152), (104, lar - 18)]
    fr.line(T(smooth(floor_, 6)), W, C6)
    # epiglottis
    fr.line(T(smooth([(cur[-1][0], cur[-1][1] - 6), (96, lar - 22), (92, lar - 30)], 4)), W, C4)
    # larynx: thyroid outline at the throat front, vocal folds across the airway
    fr.poly(T([(92, lar - 8), (110, lar - 10), (114, lar + 4), (110, lar + 16), (92, lar + 14)]),
            stroke=C5, sw=W, fill=BLACK)
    fr.line(T([(84, lar + 2), (92, lar + 1)]), W, C3)
    fr.line(T([(94, lar + 1), (106, lar + 2)]), W, C3)
    # trachea rings below
    for yy in range(int(lar + 22), 198, 7):
        fr.line(T([(90, yy), (106, yy)]), W, C7)
    fr.line(T(smooth(cur, 1)), SUBJ, C1)

    # breath: dashes of air rising from the trachea, through the folds, over the tongue and out the lips
    path = smooth([(97, 198), (96, lar + 6), (92, lar - 30), (90, 120), (110, 116 + 10 * op), (150, 114 + 4 * op),
                   (176 + lipf, 116), (212, 112), (236, 106)], 8)
    lens = [0]
    for a, b in zip(path, path[1:]):
        lens.append(lens[-1] + math.dist(a, b))
    count = 4 + round(20 * BREATH)
    total = lens[-1]
    for k in range(count):
        t0 = (k + 0.5) / count * total
        seg_ = [p for p, l in zip(path, lens) if t0 <= l <= t0 + 5]
        if len(seg_) >= 2:
            fr.line(T(seg_), W, C4)
    return fr


# ================================================================== v3 hatched mass: a breath fogged on a cold pane
def v3():
    """A window pane, face on. The sung breath has fogged it: a dense hatched core in the vowel's
    shape, a sparser halo out to where breath carries, and drops running down from the fog
    to the glazing bar (glide)."""
    fr = Frame()
    rnd = random.Random(7)
    op, fw, rd = vowel_at(VOWEL)
    # glazing bars: vertical at x 330, horizontal at y 176. Each drawn as two edges + putty line.
    for x in (326, 334):
        fr.line([(x, 21), (x, 172)], LINE if x == 326 else HAIR, C6)
        fr.line([(x, 180), (x, 220)], LINE if x == 326 else HAIR, C6)
    for y in (172, 180):
        fr.line([(0, y), (326, y)], LINE if y == 172 else HAIR, C6)
        fr.line([(334, y), (480, y)], LINE if y == 172 else HAIR, C6)
    # putty bevel, inside the pane corner
    fr.line([(0, 168), (322, 168), (322, 21)], HAIR, C7)
    fr.line([(338, 21), (338, 168), (480, 168)], HAIR, C7)
    fr.line([(0, 184), (322, 184), (322, 220)], HAIR, C7)
    fr.line([(338, 220), (338, 184), (480, 184)], HAIR, C7)

    cx, cy = 168, 96
    sc = 0.7 + 0.45 * THROAT * 1.0 + 0.0     # throat scales the whole patch
    sc = 0.62 + 0.6 * THROAT
    rx = (26 + 40 * op + 34 * fw - 10 * rd) * sc * 1.25
    ry = (24 + 34 * op - 12 * fw) * sc * 1.25

    def blob(rx_, ry_, jitter, seed, n=48):
        r = random.Random(seed)
        ph = [r.uniform(0, 6.28) for _ in range(4)]
        pts = []
        for i in range(n):
            a = 2 * math.pi * i / n
            k = 1 + jitter * (0.5 * math.sin(3 * a + ph[0]) + 0.3 * math.sin(5 * a + ph[1]) + 0.2 * math.sin(8 * a + ph[2]))
            pts.append((cx + rx_ * k * math.cos(a), cy + ry_ * k * math.sin(a) + 0.06 * ry_ * math.sin(a) ** 2 * 4))
        return pts

    halo_k = 1.18 + 0.9 * BREATH
    halo = blob(rx * halo_k, ry * halo_k, 0.07, 3)
    core = blob(rx, ry, 0.05, 5)
    inner = blob(rx * 0.55, ry * 0.55, 0.06, 9)
    # halo: sparse, low grey, only between the core and its edge
    hatch(fr, [halo, core], spacing=7, col=C6)
    # core: denser hatched mass
    hatch(fr, [core, inner], spacing=4, col=C3)
    # the wettest centre: densest, brightest (the one brightest element)
    hatch(fr, [inner], spacing=3, col=C1)

    # drops: glide sets how many have gathered and run (count), each a trail ending in a bead
    drops = 2 + round(12 * GLIDE)
    bottom = max(p[1] for p in core)
    xs = sorted(rnd.uniform(cx - rx * 0.8, cx + rx * 0.8) for _ in range(drops))
    for x in xs:
        # where the core's lower edge sits at this x
        ys = [p[1] for p in core if abs(p[0] - x) < 6 and p[1] > cy]
        y0 = (max(ys) if ys else bottom) - 2
        L = rnd.uniform(18, 1) + (168 - 6 - y0) * rnd.uniform(0.3, 1.0)
        y1 = min(y0 + L, 160)
        wob = [(x + 0.8 * math.sin(i * 1.3), y0 + (y1 - y0) * i / 8) for i in range(9)]
        fr.line(wob, HAIR, C4)
        fr.poly(ellipse(x + 0.6, y1 + 2.4, 1.9, 2.6, 14), stroke=C3, sw=HAIR, fill=BLACK)
    return fr


# ================================================================== v4 edge-lit silhouette: lips at the edge, breath on cold air
def v4():
    """A singer's lower face at the left edge, a black silhouette lit along its rim, and the breath
    leaving the lips into cold air. Vowel shapes the lips and jaw, throat drops the larynx down the
    neck, breath adds billows to the plume, glide holds the plume in a narrow round "oo" stream
    before it opens."""
    fr = Frame()
    op, fw, rd = vowel_at(VOWEL)
    jaw = 6 + 16 * op
    lipf = 8 * rd - 3 * fw
    gap = 2 + 9 * op - 2 * fw + 1.5 * rd
    lar = 186 + 26 * (THROAT)      # larynx bump on the neck: 186 .. 212
    upper = [(-4, 40), (30, 44), (58, 52), (82, 62), (92, 74), (86, 80), (72, 82), (70, 90),
             (76 + lipf, 100), (80 + lipf, 106), (74 + lipf, 110)]
    mouth_in = (62, 112 + gap * 0.5)
    lower = [(74 + lipf, 112 + gap), (79 + lipf, 118 + gap), (72 + lipf * 0.6, 126 + gap * 1.1),
             (64, 132 + jaw * 0.6), (72, 146 + jaw * 0.8), (68, 160 + jaw), (50, 166 + jaw * 0.8),
             (24, 168 + jaw * 0.5), (16, 172 + jaw * 0.3)]
    neck = [(16, 176 + jaw * 0.2), (18, lar - 12), (26, lar), (20, lar + 12), (14, 230)]
    prof = smooth(upper, 6) + [mouth_in] + smooth(lower, 6) + smooth(neck, 6)
    body = [(-10, 30)] + prof + [(-10, 230)]
    fr.poly(body, fill=BLACK)
    # rim light: the one bright line
    rim = [p for p in prof if 21 <= p[1] <= 219]
    fr.line(rim, SUBJ, C1)
    # a quieter inner rim along the jaw, as a silhouette lit from behind shows
    jaw_in = smooth([(60, 136 + jaw * 0.6), (64, 150 + jaw * 0.8), (58, 160 + jaw * 0.9), (40, 164 + jaw * 0.7)], 5)
    fr.line(jaw_in, HAIR, C6)

    # plume: centre line rising a little to the right, narrow "oo" neck for the glide length, then opening
    x_start = 82 + lipf
    y_start = 111 + gap * 0.5
    neck_len = 12 + 150 * GLIDE

    def centre(t):  # t in px along x from the lips
        return (x_start + t, y_start - 0.10 * t - 10 * math.sin(t / 120) ** 2)

    def width(t):
        if t < neck_len:
            return 2.5 + gap * 0.25
        u_ = (t - neck_len) / 240
        return 2.5 + gap * 0.25 + 70 * (1 - math.exp(-2.4 * u_))

    span = 480 - x_start + 30
    billows = 2 + round(14 * BREATH)
    up_pts, lo_pts = [], []
    N = 120
    for i in range(N + 1):
        t = span * i / N
        cxp, cyp = centre(t)
        w = width(t)
        # scallops past the neck: billows evenly along the open part
        if t > neck_len:
            ph = (t - neck_len) / max(span - neck_len, 1) * billows
            sc_ = abs(math.sin(math.pi * ph))
            bump = 0.18 * w * sc_
        else:
            bump = 0
        up_pts.append((cxp, cyp - w / 2 - bump))
        lo_pts.append((cxp, cyp + w / 2 + bump * 0.7))
    plume = up_pts + lo_pts[::-1]
    # cold air: hatched faintly inside the plume, the vapour there but not solid
    hatch(fr, [[(x, max(y, 21)) for x, y in plume]], spacing=6, col=C7)
    fr.line([p for p in up_pts if p[1] > 21 and p[0] < 482], LINE, C4)
    fr.line([p for p in lo_pts if p[0] < 482], LINE, C4)
    # curls inside the open plume, one per billow, in the plume's own line
    for k in range(billows):
        t = neck_len + (k + 0.5) / billows * (span - neck_len)
        if t > 470 - x_start:
            continue
        cxp, cyp = centre(t)
        w = width(t)
        r0 = 0.22 * w
        if r0 < 3:
            continue
        sp = [(cxp + r0 * (1 - 0.6 * a / 7) * math.cos(a + k), cyp + 0.6 * r0 * (1 - 0.6 * a / 7) * math.sin(a + k))
              for a in [i * 0.25 for i in range(26)]]
        fr.line(sp, HAIR, C5)
    return fr


# ================================================================== v5 detailed line art: a breath ring of vapour
def v5():
    """Vapour, literally: a ring of breath rising off a round "oo" mouthpiece, modelled as a torus
    and projected, with its poloidal flow drawn as hidden-line hairlines. Vowel shapes the ring's
    plan (small round u, wide round a, flattened i), throat thickens its core, breath sheds wisps,
    glide is the small hatched "oo" ring still rising behind it."""
    fr = Frame()
    op, fw, rd = vowel_at(VOWEL)
    cam = Cam(eye=(0, 190, 430), target=(0, 10, 0), focal=430, cx=240, cy=104)
    R = 30 + 40 * op + 10 * fw            # plan radius across
    kz = 1.0 - 0.45 * fw                  # plan squash in depth for spread vowels
    r = 9 + 10 * THROAT                   # core thickness follows throat
    ring_y = 30

    def tor(phi, th, Rr=R, rr=r, yc=ring_y, k=kz):
        cx_, cz_ = Rr * math.cos(phi), Rr * math.sin(phi) * k
        rad = norm((math.cos(phi), 0, math.sin(phi) * k))
        return (cx_ + rr * math.cos(th) * rad[0], yc + rr * math.sin(th), cz_ + rr * math.cos(th) * rad[2])

    # mouthpiece: a short round tube at the bottom, its rim an ellipse
    ap_y, ap_r = -120, 12
    rim_top = circle3((0, ap_y, 0), (1, 0, 0), (0, 0, 1), ap_r, 40)
    rim_bot = circle3((0, ap_y - 40, 0), (1, 0, 0), (0, 0, 1), ap_r + 2, 40)
    fr.poly(convex_hull(cam.ps(rim_top) + cam.ps(rim_bot)), stroke=C5, sw=LINE, fill=BLACK)
    fr.poly(cam.ps(rim_top), stroke=C4, sw=LINE, fill=BLACK)
    fr.poly(cam.ps(circle3((0, ap_y, 0), (1, 0, 0), (0, 0, 1), ap_r - 4, 32)), stroke=C6, sw=HAIR, fill=BLACK)

    # wake: streamlines from the rim up into the ring's underside, twisting a little
    for k in range(8):
        a0 = 2 * math.pi * k / 8 + 0.2
        pts = []
        for i in range(25):
            t = i / 24
            y = ap_y + (ring_y - r * 0.6 - ap_y) * t
            rr = ap_r + (R - r * 0.9 - ap_r) * t ** 2.2
            a = a0 + 0.9 * t
            pts.append((rr * math.cos(a), y, rr * math.sin(a) * (1 + (kz - 1) * t ** 2)))
        # only the near streamlines (z > 0 at the top) draw fully; far ones are hidden behind the ring later
        fr.line(cam.ps(pts), HAIR, C6 if math.sin(a0 + 0.9) < 0 else C5)

    # glide: the onset "oo" ring, small and round, still rising up the wake (hatched: there, not solid)
    gy = ap_y + 16 + (ring_y - ap_y - 60) * GLIDE
    gR, gr = 13, 4
    outer = cam.ps(circle3((0, gy, 0), (1, 0, 0), (0, 0, 1), gR + gr, 40))
    inner = cam.ps(circle3((0, gy, 0), (1, 0, 0), (0, 0, 1), gR - gr, 32))
    fr.poly(outer, fill=BLACK)
    hatch(fr, [outer, inner], spacing=3, col=C5)
    fr.poly(outer, stroke=C4, sw=HAIR)
    fr.poly(inner, stroke=C4, sw=HAIR)

    # the ring: poloidal sections back to front; each disc filled black hides what's behind it,
    # and only its arc facing the camera is drawn
    N = 30
    secs = []
    for i in range(N):
        phi = 2 * math.pi * i / N + 0.05
        c = tor(phi, 0, rr=0)
        secs.append((cam.depth(c), phi))
    secs.sort(reverse=True)
    for _, phi in secs:
        pts3 = [tor(phi, 2 * math.pi * j / 32) for j in range(32)]
        fr.poly(cam.ps(pts3), fill=BLACK)
        c = tor(phi, 0, rr=0)
        vis = []
        runs = []
        for j in range(33):
            th = 2 * math.pi * j / 32
            q = tor(phi, th)
            nrm = sub(q, c)
            facing = dot(nrm, sub(cam.eye, q)) > 0
            if facing:
                vis.append(cam.p(q))
            elif vis:
                runs.append(vis); vis = []
        if vis:
            runs.append(vis)
        # merge wraparound
        for run in runs:
            if len(run) >= 2:
                fr.line(run, HAIR, C4)

    # outer silhouette: for each phi, the point of the section furthest from the ring's projected centre
    ctr = cam.p((0, ring_y, 0))
    sil = []
    for i in range(96):
        phi = 2 * math.pi * i / 96
        best, bd = None, -1
        for j in range(48):
            q = cam.p(tor(phi, 2 * math.pi * j / 48))
            d = math.dist(q, ctr)
            if d > bd:
                bd, best = d, q
        sil.append(best)
    fr.poly(sil, stroke=C1, sw=SUBJ)

    # breath: wisps shed off the ring's rim, small curls in the same projection
    rnd = random.Random(4)
    wisps = 2 + round(12 * BREATH)
    for k in range(wisps):
        phi = 2 * math.pi * (k + 0.3) / wisps + 0.4
        base = tor(phi, 0.6, rr=r + 4)
        pts = []
        for i in range(14):
            t = i / 13
            a = phi + 0.5 * t
            rr_ = (R + r + 6 + 14 * t)
            pts.append((rr_ * math.cos(a), ring_y + 6 + 22 * t - 8 * t * t, rr_ * math.sin(a) * kz))
        fr.line(cam.ps(pts), HAIR, C5)
    return fr


def main():
    for name, fn in [("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)]:
        out = HERE / name / "rest.svg"
        out.parent.mkdir(exist_ok=True)
        out.write_text(fn().svg())
        print("wrote", out.relative_to(HERE.parents[3]))


if __name__ == "__main__":
    main()
