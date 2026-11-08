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
    """A speaking machine pulled apart along its air axis (world x), seen from front-right above.
    Left to right: wedge bellows (breath opens its boards), reed block (the glottal pulse),
    telescoping throat tube (throat draws it out), flared mouth and the lip iris in front of it
    (vowel shapes the aperture), with the spring that closes it back to "oo" (glide = coils)."""
    fr = Frame()
    cam = Cam(eye=(330, 150, 470), target=(0, -4, 0), focal=560, cx=232, cy=122)
    op, fw, rd = vowel_at(VOWEL)
    P = cam.p

    # dash-dot axis (exploded-view convention)
    x0, x1 = -260, 262
    x, n = x0, 0
    while x < x1:
        L = 10 if n % 2 == 0 else 2
        fr.line([P((x, 0, 0)), P((min(x + L, x1), 0, 0))], HAIR, C6)
        x += L + 4
        n += 1

    def cyl(xa, xb, r_, edge=C4, bore=True, seams=()):
        pa = cam.ps(circle3((xa, 0, 0), (0, 1, 0), (0, 0, 1), r_, 36))
        pb = cam.ps(circle3((xb, 0, 0), (0, 1, 0), (0, 0, 1), r_, 36))
        fr.poly(convex_hull(pa + pb), stroke=edge, sw=LINE, fill=BLACK)
        for s_ in seams:
            xs_ = xa + (xb - xa) * s_
            fr.line(cam.ps(circle3((xs_, 0, 0), (0, 1, 0), (0, 0, 1), r_, 20, 0.0, math.pi)), HAIR, C6)
        fr.poly(pb, stroke=edge, sw=HAIR, fill=BLACK)
        if bore:
            fr.poly(cam.ps(circle3((xb, 0, 0), (0, 1, 0), (0, 0, 1), r_ - 4, 30)), stroke=C6, sw=HAIR, fill=BLACK)

    # ---- wedge bellows: two pear-shaped boards hinged at the nozzle, leather folds between.
    hx = -168                       # hinge line (x), boards run back to -x
    half = math.radians(3 + 17 * BREATH)   # half the opening angle: 3..20 degrees

    def board_outline(ang, inset=0.0):
        pts = []
        for i in range(29):
            t = i / 28
            a = math.pi * (t - 0.5)
            # pear: narrow at the hinge, wide at the back
            u = 34 + 46 * math.cos(a) - inset        # length back from the hinge
            w = (30 - inset) * math.sin(a)
            pts.append((u, w))
        pts = [(4, -12 + inset * 0.3)] + pts + [(4, 12 - inset * 0.3)]
        return [(hx - u * math.cos(ang), w, 4 * math.copysign(1, ang) + u * math.sin(ang)) for u, w in pts]

    fr.poly(cam.ps(board_outline(-half)), stroke=C5, sw=LINE, fill=BLACK)
    folds = 4
    for k in range(1, folds * 2):
        a = -half + 2 * half * k / (folds * 2)
        inset = 5 if k % 2 else 0
        fr.poly(cam.ps(board_outline(a, inset)), stroke=C6, sw=HAIR, fill=BLACK)
    top = board_outline(half)
    fr.poly(cam.ps(top), stroke=C4, sw=LINE, fill=BLACK)
    # the board's handle and its grain line
    fr.line(cam.ps([(hx - u * math.cos(half), 0, 4 + u * math.sin(half) + 0.5) for u in (30, 70)]), HAIR, C6)
    # nozzle cone from the hinge forward
    cyl(hx, hx + 26, 6, edge=C4, bore=False)

    # ---- reed block (the glottis): a small housing with the reed tongue lifted out of its slot
    rx0, rx1, s = -112, -80, 13
    V = {(i, j, k): (rx0 if i == 0 else rx1, -s if j == 0 else s, -s if k == 0 else s)
         for i in (0, 1) for j in (0, 1) for k in (0, 1)}
    for fc in ([(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)], [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)],
               [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]):
        fr.poly([P(V[k]) for k in fc], stroke=C4, sw=LINE, fill=BLACK)
    fr.poly([P((rx0 + 6, s, -3)), P((rx1 - 6, s, -3)), P((rx1 - 6, s, 3)), P((rx0 + 6, s, 3))], stroke=C5, sw=HAIR, fill=BLACK)
    fr.line([P((rx0 + 8, s, 0)), P((rx1 - 7, s + 7, 0))], LINE, C3)
    fr.poly(cam.ps(circle3((rx1, 0, 0), (0, 1, 0), (0, 0, 1), 5, 20)), stroke=C5, sw=HAIR, fill=BLACK)

    # ---- throat tube: three telescoping sections; throat draws the set out
    tx = -54
    seg = 26 + 22 * RATIO
    for i, r_ in enumerate((11, 14, 17)):
        xa = tx + i * (seg + 12)
        cyl(xa, xa + seg, r_, seams=(0.5,))
    tend = tx + 3 * seg + 24

    # ---- mouth: a flared horn
    mx0, mx1 = tend + 6, tend + 52
    rings = [(mx0 + (mx1 - mx0) * i / 6, 15 + 23 * (i / 6) ** 1.8) for i in range(7)]
    pts = []
    for xr, rr in rings:
        pts += cam.ps(circle3((xr, 0, 0), (0, 1, 0), (0, 0, 1), rr, 36))
    fr.poly(convex_hull(pts), stroke=C4, sw=LINE, fill=BLACK)
    for xr, rr in rings[2:-1:2]:
        fr.line(cam.ps(circle3((xr, 0, 0), (0, 1, 0), (0, 0, 1), rr, 20, 0.0, math.pi)), HAIR, C6)
    fr.poly(cam.ps(circle3((mx1, 0, 0), (0, 1, 0), (0, 0, 1), 38, 44)), stroke=C4, sw=HAIR, fill=BLACK)
    fr.poly(cam.ps(circle3((mx1, 0, 0), (0, 1, 0), (0, 0, 1), 32, 40)), stroke=C6, sw=HAIR, fill=BLACK)

    # ---- lip iris: a flat ring of leaves, its aperture shaped by the vowel
    ix = mx1 + 36
    fr.poly(convex_hull(cam.ps(circle3((ix - 5, 0, 0), (0, 1, 0), (0, 0, 1), 40, 48))
                        + cam.ps(circle3((ix, 0, 0), (0, 1, 0), (0, 0, 1), 40, 48))), stroke=C4, sw=LINE, fill=BLACK)
    fr.poly(cam.ps(circle3((ix, 0, 0), (0, 1, 0), (0, 0, 1), 40, 48)), stroke=C4, sw=HAIR, fill=BLACK)
    ay = 6 + 22 * op * (1 - 0.6 * fw) + 2 * rd   # aperture half-height
    az = 6 + 20 * op + 12 * fw - 2 * rd          # half-width
    for k in range(9):
        a = 2 * math.pi * k / 9 + 0.3
        fr.line([P((ix, ay * math.sin(a), az * math.cos(a))), P((ix, 37 * math.sin(a + 0.55), 37 * math.cos(a + 0.55)))],
                HAIR, C6)
    ap = [(ix, ay * math.sin(a), az * math.cos(a)) for a in [2 * math.pi * k / 40 for k in range(40)]]
    fr.poly(cam.ps(ap), stroke=C1, sw=SUBJ, fill=BLACK)
    # glide: the spring that pulls the iris back to "oo"; more coils, softer, slower
    coils = 3 + round(12 * GLIDE)
    sy = -52
    sx0, sx1 = ix - 44, ix - 8
    fr.line([P((sx0 - 6, sy, 0)), P((sx0, sy, 0))], LINE, C4)
    N = coils * 12
    fr.line([P((sx0 + (sx1 - sx0) * i / N, sy + 4 * math.sin(2 * math.pi * coils * i / N),
                4 * math.cos(2 * math.pi * coils * i / N))) for i in range(N + 1)], HAIR, C3)
    fr.line([P((sx1, sy, 0)), P((ix, -39, 0))], LINE, C4)
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
    ox, oy = 150, 22
    op, fw, rd = vowel_at(VOWEL)
    lar = 150 + 30 * THROAT            # vocal folds, local y: 150 .. 180

    def T(pts):
        return [(ox + x, oy + y) for x, y in pts]

    j = 3 + 9 * op                     # jaw drop at the chin
    lipf = 5 * rd - 2 * fw             # lip protrusion
    upper = [(40, 196), (42, 170), (34, 142), (16, 116), (8, 84), (14, 48), (40, 18), (80, 6), (122, 8),
             (150, 22), (164, 44), (166, 58), (163, 66), (170, 80), (180, 94), (172, 99), (164, 100),
             (165, 106), (169 + lipf, 110), (164 + lipf, 113)]
    lower = [(164 + lipf, 115 + j * 0.6), (169 + lipf, 120 + j * 0.7), (160, 130 + j * 0.8),
             (164, 144 + j), (158, 154 + j), (138, 158 + j * 0.6), (118, 160), (110, 168), (110, 182), (106, 198)]
    fr.line(T(smooth(upper, 6)), W, C3)
    fr.line(T(smooth(lower, 6)), W, C3)
    # the cut through the cranium: an inner contour following the skull, a calm second line
    skull = [(30, 120), (20, 86), (26, 52), (48, 28), (84, 18), (118, 20), (142, 34), (152, 52), (148, 64)]
    fr.line(T(smooth(skull, 6)), W, C7)
    # nasal cavity above the palate
    nasal = [(160, 96), (140, 84), (112, 78), (96, 84), (94, 94), (124, 94), (156, 100)]
    fr.poly(T(smooth(nasal, 5, closed=True)), stroke=C6, sw=W, fill=BLACK)
    # hard palate arching back, soft palate hanging to the uvula
    palate = [(158, 104), (146, 98), (128, 96), (110, 99), (100, 104), (94, 112), (93, 118)]
    fr.line(T(smooth(palate, 6)), W, C4)
    # incisors
    fr.poly(T([(158, 103), (162, 104), (161, 112), (158, 111)]), stroke=C5, sw=W, fill=BLACK)
    fr.poly(T([(156, 120 + j * 0.6), (159, 119 + j * 0.6), (160, 127 + j * 0.6), (156, 127 + j * 0.6)]),
            stroke=C5, sw=W, fill=BLACK)
    # pharynx back wall down into the oesophagus
    wall = [(92, 96), (86, 112), (84, 132), (84, 156), (86, 180), (86, 198)]
    fr.line(T(smooth(wall, 6)), W, C5)

    def tongue(o, f_):
        hx = 110 + 30 * f_ - 2 * o
        hy = 104 + 14 * o
        root = 98 + 6 * f_ - 6 * o
        ty = 121 + j * 0.6
        return [(154, ty), ((154 + hx) / 2 + 2, (ty + hy) / 2 - 2), (hx, hy),
                ((hx + root) / 2 - 2, hy + 0.3 * (136 - hy)), (root + 1, hy + 0.72 * (140 - hy)), (root + 1, 148)]
    cur = smooth(tongue(op, fw), 6)
    # glide: hatched sweep between the tongue and its "oo" onset, as far back as glide reaches
    u = VOWELS[0]
    go = op + (u[0] - op) * GLIDE
    gf = fw + (u[1] - fw) * GLIDE
    gh = smooth(tongue(go, gf), 6)
    hatch(fr, [T(cur + gh[::-1])], spacing=3.5, col=C6)
    fr.line(T(gh), HAIR, C5)
    # underside of the tongue, floor of the mouth, down to the hyoid
    floor_ = [(154, 124 + j * 0.6), (146, 134 + j * 0.6), (128, 142 + j * 0.4), (112, 150), (106, lar - 10)]
    fr.line(T(smooth(floor_, 6)), W, C6)
    # epiglottis, a small flap leaning back over the airway
    fr.line(T(smooth([(cur[-1][0], cur[-1][1]), (97, lar - 14), (92, lar - 22)], 4)), W, C4)
    # larynx: thyroid cartilage in front, the folds across the airway
    fr.poly(T([(98, lar - 6), (112, lar - 8), (116, lar + 2), (112, lar + 14), (98, lar + 12)]),
            stroke=C5, sw=W, fill=BLACK)
    fr.line(T([(86, lar + 3), (93, lar + 2)]), W, C2)
    fr.line(T([(95, lar + 2), (98, lar + 3)]), W, C2)
    # trachea: front wall below the larynx, rings as short marks
    fr.line(T([(102, lar + 14), (104, 198)]), W, C6)
    for yy in range(int(lar + 22), 196, 7):
        fr.line(T([(88, yy), (101, yy)]), HAIR, C7)
    fr.line(T(cur), SUBJ, C1)

    # breath: dashes of air rising through the folds, over the tongue and out between the lips
    path = smooth([(94, 198), (92, lar + 4), (90, lar - 30), (91, 112), (108, 108 + 8 * op), (140, 110 + 6 * op),
                   (172 + lipf, 113 + j * 0.3), (204, 112), (232, 108)], 8)
    lens = [0]
    for a, b in zip(path, path[1:]):
        lens.append(lens[-1] + math.dist(a, b))
    count = 4 + round(20 * BREATH)
    for k in range(count):
        t0 = (k + 0.5) / count * lens[-1]
        seg_ = [p for p, l in zip(path, lens) if t0 <= l <= t0 + 5 and p[0] < 166]
        if len(seg_) >= 2:
            fr.line(T(seg_), W, C4)
    return fr


# ================================================================== v3 hatched mass: a breath fogged on a cold pane
def v3():
    """A window pane, face on. The sung breath has fogged it: a dense hatched core in the vowel's
    shape, a sparser halo out to where breath carries, the patch higher on the glass for a longer
    throat (a bigger singer), and drops running down from the fog to the glazing bar (glide)."""
    fr = Frame()
    rnd = random.Random(7)
    op, fw, rd = vowel_at(VOWEL)
    # glazing bars: vertical at x 330, horizontal at y 176. Each drawn as two edges + putty line.
    for x in (326, 334):
        fr.line([(x, 21), (x, 186)], LINE if x == 326 else HAIR, C6)
        fr.line([(x, 194), (x, 220)], LINE if x == 326 else HAIR, C6)
    for y in (186, 194):
        fr.line([(0, y), (326, y)], LINE if y == 186 else HAIR, C6)
        fr.line([(334, y), (480, y)], LINE if y == 186 else HAIR, C6)
    # putty bevel, inside the pane corner
    fr.line([(0, 182), (322, 182), (322, 21)], HAIR, C7)
    fr.line([(338, 21), (338, 182), (480, 182)], HAIR, C7)
    fr.line([(0, 198), (322, 198), (322, 220)], HAIR, C7)
    fr.line([(338, 220), (338, 198), (480, 198)], HAIR, C7)

    cx = 166
    cy = 108 - 44 * THROAT            # throat: a longer throat, a bigger singer, a mouth higher on the glass
    sc = 0.7 + 0.45 * THROAT * 1.0 + 0.0     # throat scales the whole patch
    sc = 0.76
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

    # drops: glide sets how many have gathered and run (count): a trail and a solid bead at its foot
    drops = 2 + round(12 * GLIDE)
    xs = [cx - rx * 0.75 + rx * 1.5 * (i + 0.5) / drops + rnd.uniform(-4, 4) for i in range(drops)]
    for x in xs:
        ys = [p[1] for p in core if abs(p[0] - x) < 8 and p[1] > cy]
        y0 = (max(ys) if ys else cy + ry) - 6
        y1 = min(y0 + rnd.uniform(10, 46), 174)
        wob = [(x + 0.9 * math.sin(i * 1.1 + x), y0 + (y1 - y0) * i / 10) for i in range(11)]
        fr.line(wob, HAIR, C3)
        drop = [(x - 2.4, y1 + 1), (x, y1 - 1.5), (x + 2.4, y1 + 1), (x + 2.2, y1 + 3.6), (x, y1 + 5), (x - 2.2, y1 + 3.6)]
        fr.poly(drop, fill=C3)
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
    lar = 184 + 26 * THROAT        # larynx bump on the neck: 184 .. 210
    D = 14
    upper = [(D + 30, 21), (D + 33, 34), (D + 31, 44), (D + 40, 58), (D + 54, 72), (D + 56, 77), (D + 50, 80),
             (D + 42, 80), (D + 42, 88), (D + 49 + lipf, 97), (D + 52 + lipf, 103), (D + 47 + lipf, 107)]
    mouth_in = (D + 38, 109 + gap * 0.5)
    lower = [(D + 47 + lipf, 110 + gap), (D + 51 + lipf, 116 + gap), (D + 46 + lipf * 0.6, 123 + gap * 1.1),
             (D + 42, 130 + jaw * 0.6), (D + 51, 144 + jaw * 0.8), (D + 47, 157 + jaw), (D + 30, 163 + jaw * 0.8),
             (D + 8, 165 + jaw * 0.5), (D, 169 + jaw * 0.3)]
    neck = [(D - 1, 175 + jaw * 0.2), (D, lar - 12), (D + 7, lar), (D + 2, lar + 12), (D - 4, 230)]
    prof = smooth(upper, 6) + [mouth_in] + smooth(lower, 6) + smooth(neck, 6)
    body = [(-10, 21)] + prof + [(-10, 230)]
    fr.poly(body, fill=BLACK)
    # rim light: the one bright line
    rim = [p for p in prof if 21 <= p[1] <= 219]
    fr.line(rim, SUBJ, C1)
    # a quieter inner rim along the jaw, as a silhouette lit from behind shows
    jaw_in = smooth([(D + 40, 136 + jaw * 0.6), (D + 44, 149 + jaw * 0.8), (D + 39, 157 + jaw * 0.9), (D + 22, 160 + jaw * 0.7)], 5)
    fr.line(jaw_in, HAIR, C6)

    # plume: centre line rising a little to the right, narrow "oo" neck for the glide length, then opening
    x_start = D + 55 + lipf
    y_start = 108.5 + gap * 0.5
    neck_len = 12 + 150 * GLIDE

    def centre(t):  # t in px along x from the lips
        return (x_start + t, y_start - 0.07 * t - 6 * math.sin(t / 120) ** 2)

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
            k_ = int(ph)
            amp = 0.10 + 0.14 * ((k_ * 7919) % 5) / 4
            bump = amp * w * abs(math.sin(math.pi * ph))
            ph2 = ph + 0.45
            amp2 = 0.08 + 0.12 * ((int(ph2) * 104729) % 4) / 3
            bump2 = amp2 * w * abs(math.sin(math.pi * ph2))
        else:
            bump = bump2 = 0
        up_pts.append((cxp, cyp - w / 2 - bump))
        lo_pts.append((cxp, cyp + w / 2 + bump2))
    plume = up_pts + lo_pts[::-1]
    # cold air: hatched faintly inside the plume, the vapour there but not solid
    hatch(fr, [[(x, max(y, 21)) for x, y in plume]], spacing=6, col=C7)
    fr.line([p for p in up_pts if p[1] > 21 and p[0] < 482], LINE, C4)
    fr.line([p for p in lo_pts if p[0] < 482], LINE, C4)
    # folds inside the open plume: a short arc under each billow, in the plume's own line
    for k in range(billows):
        t = neck_len + (k + 0.55) / billows * (span - neck_len)
        if t > 474 - x_start:
            continue
        cxp, cyp = centre(t)
        w = width(t)
        rr = 0.3 * w
        if rr < 4:
            continue
        side = -1 if k % 2 == 0 else 1
        arc = [(cxp + rr * math.cos(a), cyp + side * (0.18 * w) + side * 0.5 * rr * math.sin(a) * -1)
               for a in [math.pi * (0.15 + 0.7 * i / 12) for i in range(13)]]
        fr.line(arc, HAIR, C5)
    return fr


# ================================================================== v5 detailed line art: a breath ring of vapour
def v5():
    """Vapour, literally: a ring of breath rising through cold air, modelled as a torus and projected,
    its rolling flow drawn as hidden-line hairlines round the core. Vowel shapes the ring's plan
    (small and round for u, wide for a, flattened for i, like the lips it left), throat thickens its
    core, breath sheds wisps off it, glide is the small hatched "oo" ring it opened from, still rising
    behind it."""
    fr = Frame()
    op, fw, rd = vowel_at(VOWEL)
    cam = Cam(eye=(0, 150, 400), target=(0, -4, 0), focal=430, cx=240, cy=92)
    R = 36 + 26 * op + 12 * fw            # plan radius across
    kz = 1.0 - 0.4 * fw                   # plan squash in depth for spread vowels
    r = 14 + 20 * THROAT                  # core thickness follows throat
    ring_y = 0

    tilt = math.radians(-9)               # rings lean as they travel

    def tl(q):
        x_, y_, z_ = q
        return (x_ * math.cos(tilt) - y_ * math.sin(tilt), x_ * math.sin(tilt) + y_ * math.cos(tilt), z_)

    def tor(phi, th, Rr=R, rr=r, yc=ring_y, k=kz):
        rad = norm((math.cos(phi), 0, math.sin(phi) * k))
        return tl((Rr * math.cos(phi) + rr * math.cos(th) * rad[0], yc + rr * math.sin(th),
                   Rr * math.sin(phi) * k + rr * math.cos(th) * rad[2]))

    # wake: a few broken streamlines rising from below the frame toward the ring's underside
    for k in range(5):
        a0 = 2 * math.pi * k / 5 + 0.5
        pts = []
        for i in range(30):
            t = i / 29
            y = -150 + (ring_y - r - 12 + 150) * t
            rr = 8 + (R - r - 8) * t ** 2.5
            a = a0 + 1.1 * t
            pts.append((rr * math.cos(a), y, rr * math.sin(a)))
        pp = cam.ps(pts)
        # broken into dashes: vapour thins as it rises
        for i in range(0, len(pp) - 3, 5):
            fr.line(pp[i:i + 3], HAIR, C7)

    # glide: the onset "oo" ring, small and round, still rising (hatched: there, not solid)
    gy = -128 + 70 * GLIDE
    gR, gr = 12, 5
    gt = math.radians(7)
    outer = cam.ps(circle3((0, gy, 0), (math.cos(gt), math.sin(gt), 0), (0, 0, 1), gR + gr, 40))
    inner = cam.ps(circle3((0, gy, 0), (math.cos(gt), math.sin(gt), 0), (0, 0, 1), gR - gr, 32))
    fr.poly(outer, fill=BLACK)
    hatch(fr, [outer, inner], spacing=3, col=C5)
    fr.poly(outer, stroke=C4, sw=HAIR)
    fr.poly(inner, stroke=C4, sw=HAIR)

    # the ring: sections back to front; each section disc filled black hides what's behind it,
    # and only the arc of it facing the camera is drawn
    N = 32
    secs = sorted(((cam.depth(tor(2 * math.pi * i / N + 0.05, 0, rr=0)), 2 * math.pi * i / N + 0.05) for i in range(N)),
                  reverse=True)
    for _, phi in secs:
        fr.poly(cam.ps([tor(phi, 2 * math.pi * jj / 36) for jj in range(36)]), fill=BLACK)
        c = tor(phi, 0, rr=0)
        runs, vis = [], []
        for jj in range(37):
            q = tor(phi, 2 * math.pi * jj / 36)
            if dot(sub(q, c), sub(cam.eye, q)) > 0:
                vis.append(cam.p(q))
            elif vis:
                runs.append(vis); vis = []
        if vis:
            runs.append(vis)
        for run in runs:
            if len(run) >= 2:
                fr.line(run, HAIR, C4)

    # outer silhouette: the one bright line
    ctr = cam.p((0, ring_y, 0))
    sil = []
    for i in range(120):
        phi = 2 * math.pi * i / 120
        best, bd = None, -1
        for jj in range(60):
            q = cam.p(tor(phi, 2 * math.pi * jj / 60))
            d = math.dist(q, ctr)
            if d > bd:
                bd, best = d, q
        sil.append(best)
    fr.poly(sil, stroke=C1, sw=SUBJ)

    # breath: wisps peeling off the ring's top and trailing up and back
    wisps = 2 + round(12 * BREATH)
    for k in range(wisps):
        phi = 2 * math.pi * (k + 0.3) / wisps + 0.9
        pts = []
        for i in range(16):
            t = i / 15
            a = phi + 0.7 * t
            rr_ = R + r * 0.6 + 16 * t
            pts.append(tl((rr_ * math.cos(a), ring_y + r * 0.8 + 26 * t - 10 * t * t, rr_ * math.sin(a) * kz)))
        if cam.depth(pts[0]) > cam.depth((0, 0, 0)) + R * 0.4:
            continue  # behind the ring
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
