#!/usr/bin/env python3
"""Kiln · frames and motion study for the picked subject (pass 02, v1).

A yarn-wound mallet poised over the rim of a thrown bowl, hidden-line 3D.
This builds, at 1:1 (480 x 220):

  rest.svg/png                     defaults (strike 50, glaze 30, crack 0, fire 1.12), no notes
  playing.svg/png                  defaults, 0.09 s after a strike (the note response)
  <control>-0|50|100.svg/png       strike, glaze, crack, fire, others at default
  motion.gif                       a note, a rolled chord, release, rest (16 fps)
  motion-glaze.gif                 the same strike on bare bisque, then under thick glaze
  motion-crack.gif                 the same strike uncracked, then cracked through
  motion-sheet.png                 eight key frames of motion.gif, timestamps outside the frames
  contact.png                      rest + 0/50/100 per control, labels outside the frames

    python3 screens/kiln/frames/build.py            # everything
    python3 screens/kiln/frames/build.py --stills   # svg/png stills + contact only

How the drawing maps onto the device (motion.md has the full node plan):

- The bowl is modelled in 3D and projected through one fixed camera. Everything in
  the bowl is authored once at fire 0 and fire shrinks it with one uniform scale
  about the foot (firing shrinkage), so every bowl part is a node that only scales.
- The rim's two edges are the machine's four mutable outlines (64 points each):
  outer and inner lip, each split into a left and a right half so every outline
  stays within +-64 px of its node origin. The ring is drawn by moving their
  points: the bowl's rim modes n = 2..5 (whose ring frequencies go 1 : 2.8 : 5.4 : 8.8,
  the brief's 1 : 2.7 : 5.2 : 8.4) bend the lip in plane by a few pixels.
- The glazed interior is a hatched disc scaled about its own centre (<= 1.96x),
  occluded by a black front-wall mask, so rising glaze is a scale + translate.
- The mallet is 2D in the screen plane: it turns about the wrist on a note, and
  the yarn ball scales down onto its bare core as strike (hardness) rises.
- The crack and its crazing are short segments revealed in order (a count).
"""
from __future__ import annotations

import math
import random
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 480, 220

G0, G1, G2, G3, G4, G5, G6, BK = ("#CDCDCD", "#AFAFAF", "#969696", "#7D7D7D",
                                  "#646464", "#4B4B4B", "#323232", "#000000")
# Bowl weights are authored at fire 0 (scale 1); fire shrinks them to 0.86x,
# so hairline 1.2 -> 1.03 and line 1.6 -> 1.38 stay inside craft.md's table.
B_HAIR, B_LINE = 1.2, 1.6
M_HAIR, M_LINE, SUBJ = 1.1, 1.5, 2.2
FONT = 'font-family="UniversNextPro-Light"'
TITLES = ["strike", "glaze", "crack", "fire"]
DEFAULTS = {"strike": 0.5, "glaze": 0.3, "crack": 0.0, "fire": 0.5}

# ---------------------------------------------------------------- sound model (visual)
RATIO = [1.0, 2.7, 5.2, 8.4]          # the brief's modal ratios, rim modes n = 2..5
F_BASE = 2.0                          # visual Hz of the fundamental's shiver
STATIONS = [-14.0, -58.0, -92.0, -162.0]   # rim stations (deg); 0 is the mallet's
THETA_CRACK = -124.0                  # where the crack runs down the front wall
A_WORLD = 0.024                       # peak radial bend of the lip, world units (~3 px at the sides)
SETTLE = 0.0025                       # below this (~0.3 px) a voice snaps to rest


def f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def header_values(p):
    crack = p["crack"] ** 1.6
    return [f"{round(100 * p['strike'])}", f"{round(100 * p['glaze'])}",
            f"{round(100 * crack)}", f"{1 + 0.24 * p['fire']:.2f}"]


# ---------------------------------------------------------------- 2D helpers
def dedupe(pts, gap=0.6, closed=False):
    out = []
    for p in pts:
        p = (round(p[0], 2), round(p[1], 2))
        if not out or math.dist(p, out[-1]) >= gap:
            out.append(p)
    if closed:
        while len(out) > 3 and math.dist(out[0], out[-1]) < gap:
            out.pop()
    return out


def decimate(pts, n=60):
    if len(pts) <= n:
        return pts
    return [pts[round(i * (len(pts) - 1) / (n - 1))] for i in range(n)]


def offset_line(pts, d):
    n = len(pts)
    out = []
    for i in range(n):
        a = pts[i - 1] if i > 0 else None
        b = pts[i]
        c = pts[i + 1] if i < n - 1 else None
        dirs = []
        for p, q in ((a, b), (b, c)):
            if p is None or q is None:
                continue
            dx, dy = q[0] - p[0], q[1] - p[1]
            L = math.hypot(dx, dy) or 1
            dirs.append((dx / L, dy / L))
        tx = sum(v[0] for v in dirs)
        ty = sum(v[1] for v in dirs)
        L = math.hypot(tx, ty) or 1
        tx, ty = tx / L, ty / L
        nx, ny = ty, -tx
        k = d
        if len(dirs) == 2:
            cos = dirs[0][0] * tx + dirs[0][1] * ty
            k = d / max(cos, 0.5)
        out.append((b[0] + nx * k, b[1] + ny * k))
    return out


def ribbon_pts(pts, w):
    return offset_line(pts, w / 2) + offset_line(pts, -w / 2)[::-1]


def taper_pts(pts, w0, w1):
    """A ribbon whose width runs from w0 at the start to w1 at the end."""
    n = len(pts)
    left, right = [], []
    for i in range(n):
        w = w0 + (w1 - w0) * i / max(1, n - 1)
        a = pts[max(0, i - 1)]
        c = pts[min(n - 1, i + 1)]
        dx, dy = c[0] - a[0], c[1] - a[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = dy / L, -dx / L
        left.append((pts[i][0] + nx * w / 2, pts[i][1] + ny * w / 2))
        right.append((pts[i][0] - nx * w / 2, pts[i][1] - ny * w / 2))
    return left + right[::-1]


def inside(pt, poly):
    x, y = pt
    c = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xi > x:
                c = not c
    return c


def hull(points):
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in points))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def resample_closed(poly, step=4.0):
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        L = math.dist(a, b)
        k = max(1, int(L / step))
        for j in range(k):
            t = j / k
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def intervals(poly, c):
    xs = []
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        u1, u2 = x1 + y1 - c, x2 + y2 - c
        if (u1 > 0) != (u2 > 0):
            t = u1 / (u1 - u2)
            xs.append(x1 + (x2 - x1) * t)
    xs.sort()
    return [(xs[i], xs[i + 1]) for i in range(0, len(xs) - 1, 2)]


class Tf:
    """Uniform scale s about pivot c (a node's own transform, composed)."""

    def __init__(self, c=(0.0, 0.0), s=1.0):
        self.c, self.s = c, s

    def __call__(self, p):
        return (self.c[0] + self.s * (p[0] - self.c[0]), self.c[1] + self.s * (p[1] - self.c[1]))

    def pts(self, pts):
        return [self(p) for p in pts]


def rot(p, c, a):
    ca, sa = math.cos(a), math.sin(a)
    dx, dy = p[0] - c[0], p[1] - c[1]
    return (c[0] + ca * dx - sa * dy, c[1] + sa * dx + ca * dy)


# ---------------------------------------------------------------- frame
class Frame:
    def __init__(self, values):
        self.out: list[str] = []
        self.values = values
        self.palette = [G0, G1, G2, G3, G4, G5]

    def poly(self, pts, fill=BK):
        pts = decimate(dedupe(pts, closed=True), 62)
        if len(pts) < 3:
            return
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
        self.out.append(f'  <path d="{d}" fill="{fill}" stroke="none" stroke-width="0"/>')

    def outline(self, pts, colour):
        """A filled closed ribbon (already an outline)."""
        pts = dedupe(pts, gap=0.15, closed=True)
        if len(pts) >= 3:
            d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
            self.out.append(f'  <path d="{d}" fill="{colour}" stroke="none" stroke-width="0"/>')

    def line(self, pts, w, colour, closed=False):
        """An open (or closed) line drawn as thin closed ribbons of <= 28 points per side."""
        pts = dedupe(pts)
        if closed and pts:
            pts = pts + [pts[0]]
        if len(pts) < 2:
            return
        segs = len(pts) - 1
        chunks = max(1, math.ceil(segs / 27))
        step = math.ceil(segs / chunks)
        i = 0
        while i < len(pts) - 1:
            run = pts[i:i + step + 1]
            if len(run) >= 2:
                self.outline(ribbon_pts(run, w), colour)
            i += step

    def circle(self, cx, cy, r, fill=BK, stroke="none", sw=0.0):
        sws = f' stroke-width="{f(sw)}"' if stroke != "none" else ' stroke-width="0"'
        self.out.append(f'  <circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def mutable(self, idx, origin, pts, colour):
        """A bound mutable outline: exactly 64 points, relative to its node origin."""
        assert len(pts) == 64, len(pts)
        rel = [(round(x - origin[0], 2), round(y - origin[1], 2)) for x, y in pts]
        far = max(max(abs(x), abs(y)) for x, y in rel)
        assert far <= 64, f"mutable outline {idx} reaches {far:.1f} px"
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in rel) + " Z"
        self.out.append(f'  <path id="kiln_node_{idx}" transform="matrix(1 0 0 1 {f(origin[0])} {f(origin[1])})" '
                        f'd="{d}" fill="{colour}" stroke="none" stroke-width="0"/>')

    def runs(self, pts, mask, w, colour, minlen=3):
        def emit(run):
            if len(run) >= minlen:
                xs, ys = [p[0] for p in run], [p[1] for p in run]
                if max(max(xs) - min(xs), max(ys) - min(ys)) >= 5:
                    self.line(run, w, colour)
        run = []
        for p, m in zip(pts, mask):
            if m:
                run.append(p)
            else:
                emit(run)
                run = []
        emit(run)

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
            head.append(f'    <text transform="matrix(1 0 0 1 {5 + 120 * k} 10)" fill="{ink}" stroke="none" {FONT} font-size="10px">{TITLES[k]}</text>')
        for k in range(4):
            ink = "#CBCBCB" if k < 2 else "#000000"
            head.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * k} 17.44)" fill="{ink}" stroke="none" {FONT} font-size="20px">{self.values[k]}</text>')
        head.append('  </g>')
        pal = [f'  <path id="kiln_palette_{i}" d="M {700 + 10 * i} 300 L {704 + 10 * i} 300 L {704 + 10 * i} 304 Z" '
               f'fill="{c}" stroke="{c}" stroke-width="2"/>' for i, c in enumerate(self.palette)]
        return "\n".join(head + pal + self.out + ["</svg>", ""])


# ---------------------------------------------------------------- 3D
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross3(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    L = math.sqrt(dot(a, a)) or 1
    return (a[0] / L, a[1] / L, a[2] / L)


class Cam:
    def __init__(self, elev_deg, dist, azim_deg=0.0):
        e, a = math.radians(elev_deg), math.radians(azim_deg)
        self.eye = (dist * math.cos(e) * math.sin(a), -dist * math.cos(e) * math.cos(a), dist * math.sin(e))
        self.fwd = norm(sub((0, 0, 0.3), self.eye))
        self.right = norm(cross3(self.fwd, (0, 0, 1)))
        self.up = cross3(self.right, self.fwd)
        self.f, self.cx, self.cy = 1.0, 240.0, 120.0

    def raw(self, P):
        d = sub(P, self.eye)
        z = dot(d, self.fwd)
        return dot(d, self.right) / z, dot(d, self.up) / z

    def p(self, P):
        x, y = self.raw(P)
        return (self.cx + self.f * x, self.cy - self.f * y)

    def fit(self, pts3, box):
        r = [self.raw(P) for P in pts3]
        xs, ys = [q[0] for q in r], [q[1] for q in r]
        x0, y0, x1, y1 = box
        self.f = min((x1 - x0) / (max(xs) - min(xs)), (y1 - y0) / (max(ys) - min(ys)))
        self.cx = (x0 + x1) / 2 - self.f * (max(xs) + min(xs)) / 2
        self.cy = (y0 + y1) / 2 + self.f * (max(ys) + min(ys)) / 2


class Bowl:
    """A thrown bowl, a surface of revolution about z, foot at z = 0. Authored at fire 0."""

    def __init__(self, R=1.0, Hh=0.72, foot_r=0.42, foot_h=0.08, wall=0.10):
        self.R, self.H, self.fr, self.fh, self.w = R, Hh, foot_r, foot_h, wall

    def outer(self, t):
        a = t * math.pi / 2
        r0 = self.fr - 0.02
        r = r0 + (self.R - r0) * math.sin(a)
        z = self.fh + (self.H - self.fh) * (1 - math.cos(a))
        dr = (self.R - r0) * math.cos(a)
        dz = (self.H - self.fh) * math.sin(a)
        L = math.hypot(dr, dz) or 1
        return r, z, dz / L, -dr / L

    def inner(self, t, w=None):
        w = self.w if w is None else w
        r, z, nr, nz = self.outer(t)
        return max(r - w * nr, 0.0), z - w * nz, -nr, -nz

    @staticmethod
    def P(r, z, th):
        return (r * math.cos(th), r * math.sin(th), z)

    def ring(self, r, z, n=96):
        return [self.P(r, z, 2 * math.pi * i / n) for i in range(n)]

    def all_outer(self):
        pts = []
        for k in range(13):
            r, z, _, _ = self.outer(k / 12)
            pts += self.ring(r, z, 64)
        pts += self.ring(self.fr, 0, 64)
        return pts


def ring_vis(cam, r, z, nr, nz, n=180, opening=None):
    out, mask = [], []
    for i in range(n):
        th = 2 * math.pi * i / n
        P = Bowl.P(r, z, th)
        nvec = (nr * math.cos(th), nr * math.sin(th), nz)
        q = cam.p(P)
        v = dot(nvec, sub(cam.eye, P)) > 0
        if v and opening is not None:
            v = inside(q, opening)
        out.append(q)
        mask.append(v)
    if not all(mask) and any(mask):
        k = mask.index(False)
        out, mask = out[k:] + out[:k], mask[k:] + mask[:k]
    return out, mask


# ---------------------------------------------------------------- the fixed scene
BOWL = Bowl()
CAM = Cam(elev_deg=29, dist=7.0, azim_deg=-14)
CAM.fit(BOWL.all_outer(), (36, 66, 272, 212))
FOOT = CAM.p((0, 0, 0))                       # fire's pivot: the foot's centre
AZ_SPLIT = (76.0, 256.0)                      # rim halves split front/back (camera azimuth -14)


def fire_scale(fire):
    return 1.0 - 0.14 * fire                  # firing shrinkage, 1.00 .. 0.86


def lip_wall(fire):
    return 0.10 - 0.035 * fire                # the lip thins as the body vitrifies


GLAZE_T = (0.13, 0.6)                        # inner-profile t of the glaze line, glaze 0 .. 100


def glaze_ring(g):
    t = GLAZE_T[0] + (GLAZE_T[1] - GLAZE_T[0]) * g
    r, z, _, _ = BOWL.inner(t)
    return r, z


def _sil_low():
    sil = hull([CAM.p(P) for P in BOWL.all_outer()])
    ring = resample_closed(sil, 4)
    left = CAM.p(Bowl.P(BOWL.R, BOWL.H, math.radians(166)))
    right = CAM.p(Bowl.P(BOWL.R, BOWL.H, math.radians(-14)))
    i0 = min(range(len(ring)), key=lambda i: math.dist(ring[i], left))
    i1 = min(range(len(ring)), key=lambda i: math.dist(ring[i], right))
    seq = ring[i0:] + ring[:i0]
    j = (i1 - i0) % len(ring)
    a = seq[:j + 1]
    b = seq[j:] + [seq[0]]
    low = a if sum(p[1] for p in a) / len(a) > sum(p[1] for p in b) / len(b) else b
    return [left] + low[1:-1] + [right] if low[0] == seq[0] else [right] + low[1:-1] + [left]


SIL_LOW = _sil_low()


def ellipse_of_ring(r, z, n=64):
    return [CAM.p(Bowl.P(r, z, 2 * math.pi * i / n)) for i in range(n)]


def bbox(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


GLAZE_AUTH = ellipse_of_ring(*glaze_ring(0.0))   # authored at its smallest; scaled up as glaze rises


def glaze_tf(g):
    """The glaze disc's own transform for glaze g: uniform scale + translate of the authored disc."""
    a = bbox(GLAZE_AUTH)
    b = bbox(ellipse_of_ring(*glaze_ring(g)))
    # the smaller of the width and height ratios, pinned at the back (top) of the ring, so the
    # scaled disc never rises above the true glaze line or over the lip
    s = min((b[2] - b[0]) / (a[2] - a[0]), (b[3] - b[1]) / (a[3] - a[1]))
    ca = ((a[0] + a[2]) / 2, a[1])
    cb = ((b[0] + b[2]) / 2, b[1])
    return s, ca, cb


assert glaze_tf(1.0)[0] <= 2.0, glaze_tf(1.0)[0]


# ---------------------------------------------------------------- crack and crazing (authored once)
def crack_geometry(seed=26):
    """A dunting crack as a tree grown down the front wall from the lip.

    Each step is a short segment with its path length from the crack's mouth;
    the knob reveals every segment nearer the mouth than its reach, so the crack
    runs down, forks, and its forks fork (a count of segments, eased by length).
    Returns [(dist, depth, (th, t), (th, t), branch)] sorted by dist.
    """
    rnd = random.Random(seed)
    th0 = math.radians(THETA_CRACK)
    segs = []
    ds = 0.034
    ids = [0]

    def grow(th, t, heading, budget, depth, dist):
        ids[0] += 1
        bid = ids[0]
        steps = int(budget / ds)
        for i in range(steps):
            heading += rnd.uniform(-0.3, 0.3)
            if depth == 0:
                heading *= 0.8                    # the main crack keeps running down the wall
            heading = max(-1.2, min(1.2, heading))
            r = BOWL.outer(t)[0]
            nth = th + math.sin(heading) * ds / r
            nt = t - math.cos(heading) * ds * 0.9
            if nt < (0.13 if depth == 0 else 0.2) or abs(nth - th0) > math.radians(50):
                return
            segs.append((dist, depth, (th, t), (nth, nt), bid))
            th, t, dist = nth, nt, dist + ds
            p_fork = (0.26, 0.2, 0.0)[depth] if depth < 3 else 0
            if i > 1 and rnd.random() < p_fork:
                side = rnd.choice((-1, 1))
                grow(th, t, side * rnd.uniform(1.05, 1.35), (0.62 if depth == 0 else 0.3) * rnd.uniform(0.6, 1.0),
                     depth + 1, dist)
    grow(th0, 0.99, 0.0, 0.92, 0, 0.0)
    segs.sort(key=lambda q: q[0])
    return segs


CRACK = crack_geometry()
CRACK_MAX = max(q[0] for q in CRACK) + 0.034



def wall_pt(th, t, out=0.0):
    r, z, nr, nz = BOWL.outer(t)
    return CAM.p(Bowl.P(r + out * nr, z + out * nz, th))


# ---------------------------------------------------------------- mallet (2D in the screen plane)
WRIST = (418.0, 118.0)
SHAFT_L = 152.0
REST_ANGLE = math.radians(205.0)               # head down-left of the wrist, poised over the rim
CORE_R = 11.5
YARN_R = 30.0


def head_radius(strike):
    """The yarn ball shrinks onto the bare core as hardness rises (scale 1.0 .. 0.52)."""
    return max(CORE_R, YARN_R * (1 - (1 - CORE_R / YARN_R) * strike / 0.96))


def head_scale(strike):
    return head_radius(strike) / YARN_R


def rim_point(theta_deg, fire, deform=None, extra=0.0):
    th = math.radians(theta_deg)
    d = deform(th) if deform else 0.0
    tf = Tf(FOOT, fire_scale(fire))
    return tf(CAM.p(Bowl.P(BOWL.R + d + extra, BOWL.H, th)))


def contact_angle(strike, fire):
    """Turn the mallet about the wrist until its head meets the rim."""
    r = head_radius(strike) + 1.0
    rim = [rim_point(a, fire) for a in range(-80, 60, 2)]
    ang = REST_ANGLE
    for _ in range(700):
        c = (WRIST[0] + SHAFT_L * math.cos(ang), WRIST[1] + SHAFT_L * math.sin(ang))
        if min(math.dist(c, q) for q in rim) <= r:
            return ang
        ang -= math.radians(0.1)               # downward swing (counter-clockwise on screen)
    return ang


def draw_mallet(F, strike, ang, head_colour=G0):
    c = (WRIST[0] + SHAFT_L * math.cos(ang), WRIST[1] + SHAFT_L * math.sin(ang))
    ax = (math.cos(ang), math.sin(ang))               # wrist -> head
    nx, ny = -ax[1], ax[0]
    R = head_radius(strike)
    # shaft: a slim tapered rod from the wrist into the head, black body, line edge
    wa, wb = 3.4, 2.6
    a, b = WRIST, (c[0] - ax[0] * R * 0.6, c[1] - ax[1] * R * 0.6)
    F.poly([(a[0] + nx * wa, a[1] + ny * wa), (b[0] + nx * wb, b[1] + ny * wb),
            (b[0] - nx * wb, b[1] - ny * wb), (a[0] - nx * wa, a[1] - ny * wa)])
    F.line([(a[0] + nx * wa, a[1] + ny * wa), (b[0] + nx * wb, b[1] + ny * wb)], M_LINE, G3)
    F.line([(a[0] - nx * wa, a[1] - ny * wa), (b[0] - nx * wb, b[1] - ny * wb)], M_LINE, G3)
    # butt end: a small closed cap across the rod
    cap = [(a[0] + nx * wa + ax[0] * 0.2, a[1] + ny * wa + ax[1] * 0.2),
           (a[0] - nx * wa + ax[0] * 0.2, a[1] - ny * wa + ax[1] * 0.2),
           (a[0] - nx * wa - ax[0] * 2.4, a[1] - ny * wa - ax[1] * 2.4),
           (a[0] + nx * wa - ax[0] * 2.4, a[1] + ny * wa - ax[1] * 2.4)]
    F.poly(cap, fill=BK)
    F.line([cap[2], cap[3]], M_LINE, G3)
    # bare core underneath (shows when the yarn is gone): bright, subject weight, with its collar
    yarn_on = R > CORE_R + 0.4
    if not yarn_on:
        F.circle(c[0], c[1], CORE_R, fill=BK, stroke=head_colour, sw=SUBJ)
        # collar where the rod enters the core, and one turned groove: a hard, bare bead
        col = (c[0] - ax[0] * (CORE_R - 0.5), c[1] - ax[1] * (CORE_R - 0.5))
        F.line([(col[0] + nx * 4.6, col[1] + ny * 4.6), (col[0] - nx * 4.6, col[1] - ny * 4.6)], M_HAIR, G3)
        g = [rot((c[0] + CORE_R * 0.55 * math.cos(t), c[1] + CORE_R * 0.98 * math.sin(t)), c, ang)
             for t in [math.pi * (0.62 + 0.76 * i / 15) for i in range(16)]]
        F.line(g, M_HAIR, G4)
        return c, CORE_R
    # yarn ball: one node scaled about its centre; stroke authored 2.4 at scale 1 -> 1.25 at 0.52
    s = R / YARN_R
    F.circle(c[0], c[1], R, fill=BK, stroke=head_colour, sw=2.4 * s)
    # wraps: latitude bands about the rod's axis, front half only, unwound as hardness rises
    nwrap = 10
    shown = max(0, round(nwrap * (1 - strike) + 0.49)) if strike < 0.96 else 0
    order = [4, 5, 3, 6, 2, 7, 1, 8, 0, 9]
    vis = set(order[:shown])
    for k in range(nwrap):
        if k not in vis:
            continue
        phi = -0.95 + 1.9 * (k + 0.5) / nwrap        # latitude along the axis, rod side positive
        cr = R * math.cos(phi) * 0.94
        cc = (c[0] - ax[0] * R * math.sin(phi) * 0.94, c[1] - ax[1] * R * math.sin(phi) * 0.94)
        arc = []
        for i in range(25):
            t = math.pi * i / 24
            # ellipse in the head's frame: major across the rod, minor along it (foreshortened)
            u = cr * math.cos(t)
            v = cr * 0.34 * math.sin(t)
            arc.append((cc[0] + nx * u + ax[0] * v, cc[1] + ny * u + ax[1] * v))
        F.line(arc, M_HAIR * max(1.0, s), G3 if 2 <= k <= 7 else G4)
    return c, R


# ---------------------------------------------------------------- the ring (modal model)
class Voice:
    def __init__(self, t0, station, strike, t_off=None):
        self.t0, self.station, self.strike, self.t_off = t0, station, strike, t_off


def mode_freqs(p):
    S = 1 + 0.24 * p["fire"]
    c = p["crack"] ** 1.6
    detune = [0.0, 0.05, -0.06, 0.07]
    out = []
    for k, r in enumerate(RATIO):
        rr = r * (S if k else 1.0)
        fk = F_BASE * rr ** 0.6 * (1 + c * detune[k])
        split = 0.11 * c if k else 0.0            # doublets on modes >= 2
        out.append((fk * (1 - split / 2), fk * (1 + split / 2)))
    return out


def mode_t60(p):
    g = p["glaze"]
    base = 6.0 * 0.05 ** g                         # ~6 s bare .. 0.3 s thick
    return [base / (1 + 1.4 * g * k) * (1 + 0.45 * p["fire"] * k / 3) for k in range(4)]


def mode_amps(h):
    """Excitation by hardness: a soft mallet rings the fundamental, a hard one all four."""
    w = [1.0] + [(0.12 + 0.72 * h) ** k * 0.92 ** k for k in (1, 2, 3)]
    tot = sum(w)
    return [A_WORLD * x / tot * (1.6 + 0.6 * h) for x in w]


def release_gate(v, t, release):
    if v.t_off is None or t < v.t_off:
        return 1.0
    return math.exp(-(t - v.t_off) / (release / 3))


def deformation(p, voices, t, frame_index=0, release=1.2):
    """Radial bend of the lip at world angle th: the sum of each voice's rim modes."""
    fr = mode_freqs(p)
    T = mode_t60(p)
    thc = math.radians(THETA_CRACK)
    terms = []
    for v in voices:
        tau = t - v.t0
        if tau < 0:
            continue
        G = release_gate(v, t, release)
        A = mode_amps(v.strike)
        ths = math.radians(STATIONS[v.station])
        for k in range(4):
            n = k + 2
            env = A[k] * math.exp(-3.45 * tau / T[k]) * G
            if env < SETTLE * 0.25:
                continue
            ac, as_ = math.cos(n * (ths - thc)), math.sin(n * (ths - thc))
            w1, w2 = 2 * math.pi * fr[k][0], 2 * math.pi * fr[k][1]
            terms.append((n, env * ac * math.sin(w1 * tau), env * as_ * math.sin(w2 * tau), env))
    total = sum(abs(x[1]) + abs(x[2]) for x in terms)
    if total < SETTLE:
        terms = []
    live = sum(x[3] for x in terms)
    c = p["crack"] ** 1.6
    buzz = 0.0
    if terms and c > 0.15:
        buzz = (1 if frame_index % 2 else -1) * min(0.012, live * 0.5) * c

    def d(th):
        s = 0.0
        for n, a1, a2, _ in terms:
            s += a1 * math.cos(n * (th - thc)) + a2 * math.sin(n * (th - thc))
        if buzz:
            dt = math.atan2(math.sin(th - thc), math.cos(th - thc))
            s += buzz * (1 if dt > 0 else -1) * math.exp(-abs(dt) / 0.18)
        return s
    return d, bool(terms), live


# ---------------------------------------------------------------- scene
def rim_half(fire, r, deform, lo_deg, hi_deg, w, extra_fn):
    tf = Tf(FOOT, fire_scale(fire))
    cl = []
    for i in range(32):
        th = math.radians(lo_deg + (hi_deg - lo_deg) * i / 31)
        rr = r + deform(th) + extra_fn(th)
        cl.append(tf(CAM.p(Bowl.P(rr, BOWL.H, th))))
    return ribbon_pts(cl, w * fire_scale(fire))


def crack_step(p):
    """A dunting crack springs the lip: the far side stands proud, the near side sinks a little,
    so the rim's round is broken at the crack (the static half of the doublet idea)."""
    u = p["crack"]
    thc = math.radians(THETA_CRACK)

    def e(th):
        if u <= 0:
            return 0.0
        dt = math.atan2(math.sin(th - thc), math.cos(th - thc))
        if dt > 0:
            return 0.02 * u * math.exp(-dt / 0.55)
        return -0.012 * u * math.exp(dt / 0.4)
    return e


def rim_origins(fire):
    """Node origins of the four rim outlines (moved with fire's scale, so points stay within +-64)."""
    tf = Tf(FOOT, fire_scale(fire))
    out = []
    for r in (BOWL.R, BOWL.R - lip_wall(0)):
        for lo, hi in ((AZ_SPLIT[0], AZ_SPLIT[1]), (AZ_SPLIT[1] - 360, AZ_SPLIT[0])):
            pts = [CAM.p(Bowl.P(r, BOWL.H, math.radians(lo + (hi - lo) * i / 31))) for i in range(32)]
            x0, y0, x1, y1 = bbox(pts)
            out.append(tf(((x0 + x1) / 2, (y0 + y1) / 2)))
    return out


def draw_scene(p, voices=(), t=0.0, frame_index=0, release=1.2):
    F = Frame(header_values(p))
    s = fire_scale(p["fire"])
    tf = Tf(FOOT, s)
    hair, line = B_HAIR * s, B_LINE * s
    deform, ringing, live = deformation(p, voices, t, frame_index, release)

    # --- body: black silhouette (authored at fire 0, scaled about the foot)
    sil = hull([CAM.p(P) for P in BOWL.all_outer()])
    F.poly(tf.pts(resample_closed(sil, 6)))

    # --- cavity: inner throwing rings (back runs inside the opening)
    rim_i_thick = [CAM.p(P) for P in BOWL.ring(BOWL.R - lip_wall(0), BOWL.H, 120)]
    for tt in (0.42, 0.66, 0.86):
        r, z, nr, nz = BOWL.inner(tt)
        pts, mask = ring_vis(CAM, r, z, nr, nz, opening=rim_i_thick)
        F.runs(tf.pts(pts), mask, hair, G5 if tt < 0.6 else G4)

    # --- glaze: hatched disc below the glaze line, scaled about its own centre
    if p["glaze"] > 0.005:
        gs, ca, cb = glaze_tf(p["glaze"])
        gtf = lambda q: tf((cb[0] + gs * (q[0] - ca[0]), cb[1] + gs * (q[1] - ca[1])))
        poly = GLAZE_AUTH
        x0, y0, x1, y1 = bbox(poly)
        step = 5.0
        c = math.floor((x0 + y0) / step) * step
        while c <= x1 + y1:
            for xa, xb in intervals(poly, c):
                if xb - xa > 3.0:
                    a = (xa + 0.4, c - xa - 0.4)
                    b = (xb - 0.4, c - xb + 0.4)
                    F.line([gtf(a), gtf(b)], 1.2 * gs * s, G3)
            c += step
        F.line([gtf(q) for q in poly], 1.2 * gs * s, G2, closed=True)

    # --- front wall: a black mask from the inner lip's front arc down, hiding what's behind
    front = []
    for i in range(61):
        th = math.radians(166 + 180 * i / 60)                # front arc, left extreme -> right extreme
        front.append(CAM.p(Bowl.P(BOWL.R - lip_wall(0), BOWL.H, th)))
    xl, xr = front[0][0], front[-1][0]
    if xl > xr:
        front = front[::-1]
    low = [q for q in sil if q[1] > CAM.p((0, 0, BOWL.H))[1]]
    low = sorted(low, key=lambda q: -q[0])
    mask = front + [(front[-1][0] + 0.5, front[-1][1] + 1.5)] + low
    F.poly(tf.pts(mask))

    # --- outer throwing rings (front runs) and the foot
    for tt in (0.3, 0.55, 0.8):
        r, z, nr, nz = BOWL.outer(tt)
        pts, msk = ring_vis(CAM, r, z, nr, nz)
        F.runs(tf.pts(pts), msk, hair, G4)
    pts, msk = ring_vis(CAM, BOWL.fr, BOWL.fh, 1.0, -0.15)
    F.runs(tf.pts(pts), msk, hair, G4)

    # --- the crack (count channel on the knob position u): a tree revealed by path length
    u = p["crack"]
    if u > 0:
        reach = CRACK_MAX * u
        branches = {}
        for q in CRACK:
            if q[0] < reach:
                branches.setdefault(q[4], []).append(q)
        for bid, segs in sorted(branches.items(), key=lambda kv: kv[1][0][1]):
            depth = segs[0][1]
            pts = [segs[0][2]] + [q[3] for q in segs]
            # the tip grows smoothly (on the device a chunk node scales up about its root)
            last = segs[-1]
            k = min(1.0, (reach - last[0]) / 0.034)
            a, b = last[2], last[3]
            pts[-1] = (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)
            scr = tf.pts([wall_pt(th, tt, 0.004) for th, tt in pts])
            if len(scr) < 2 or math.dist(scr[0], scr[-1]) < 3:
                continue
            if depth == 0:
                F.outline(taper_pts(dedupe(scr, 0.8), (1.4 + 2.8 * u) * s, 1.1 * s), G2)
            else:
                F.line(scr, (1.5 if depth == 1 else 1.2) * s, G2 if depth == 1 else G3)

    # --- silhouette outline (hidden-line edge): the wall and belly only, from one end of the
    # lip round under the foot to the other. The lip itself is the rim outlines, so nothing
    # static doubles the rim when it rings.
    F.line(tf.pts(SIL_LOW), line, G2)

    # --- the lip: four mutable outlines (outer L/R, inner L/R)
    origins = rim_origins(p["fire"])
    step = crack_step(p)
    k = 0
    for r in (BOWL.R, BOWL.R - lip_wall(p["fire"])):
        for lo, hi in ((AZ_SPLIT[0], AZ_SPLIT[1]), (AZ_SPLIT[1] - 360, AZ_SPLIT[0])):
            pts = rim_half(p["fire"], r, deform, lo, hi, B_LINE, step)
            F.mutable(k, origins[k], pts, G2)
            k += 1

    # head dims for the beat its contact flash is the brightest thing on screen
    head_colour = G0
    for v in voices:
        if v.station == 0 and 0 <= t - v.t0 < 0.07 + 0.09 * (1 - v.strike):
            head_colour = G2
    # --- the mallet
    latest = None
    for v in voices:
        if v.t0 <= t and (latest is None or v.t0 > latest.t0):
            latest = v
    ang = REST_ANGLE
    if latest is not None:
        tau = t - latest.t0
        c_ang = contact_angle(p["strike"], p["fire"])
        dwell = 0.03 + 0.07 * (1 - p["strike"])       # soft yarn stays on the rim a beat longer
        if tau < dwell:
            ang = c_ang
        else:
            e = math.exp(-(tau - dwell) / 0.042)       # ease-out, settled in ~0.2 s
            ang = REST_ANGLE + (c_ang - REST_ANGLE) * e
            if abs(ang - REST_ANGLE) < math.radians(0.15):
                ang = REST_ANGLE
    draw_mallet(F, p["strike"], ang, head_colour)
    # --- contact marks at struck stations: a flash, then a faint scuff while the key is held
    for v in voices:
        tau = t - v.t0
        if tau < 0:
            continue
        held = v.t_off is None or t < v.t_off
        flash = 0.07 + 0.09 * (1 - v.strike)          # soft: longer, broader contact
        if tau < flash:
            col, wid = G0, SUBJ
        elif tau < flash + 0.16:
            col, wid = G2, M_LINE
        elif held:
            col, wid = G4, M_LINE
        else:
            continue
        span_px = 28 - 20 * v.strike                       # broad soft contact .. crisp hard one
        ths = STATIONS[v.station]
        # the flash sits on the lip itself; the afterglow and the held mark sit just outside it
        out = 0.012 if col == G0 else 0.05
        a0 = rim_point(ths - 5, p["fire"], extra=out)
        a1 = rim_point(ths + 5, p["fire"], extra=out)
        deg_per_px = 10 / max(1e-3, math.dist(a0, a1))
        half = span_px * deg_per_px / 2
        arc = [rim_point(ths - half + 2 * half * i / 10, p["fire"], extra=out) for i in range(11)]
        F.line(arc, wid, col)

    return F, ringing


# ---------------------------------------------------------------- output
def render_png(svg_path: Path, png_path: Path):
    subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H), "-b", "black", "-o", str(png_path), str(svg_path)],
                   check=True)


def write_frame(name, p, voices=(), t=0.0, frame_index=0, out_dir=HERE, png=True, release=1.2):
    F, _ = draw_scene(p, voices, t, frame_index, release)
    svg = out_dir / f"{name}.svg"
    svg.write_text(F.svg())
    if png:
        render_png(svg, out_dir / f"{name}.png")
    return svg


def stills():
    write_frame("rest", DEFAULTS)
    write_frame("playing", DEFAULTS, [Voice(0.0, 0, DEFAULTS["strike"])], t=0.09)
    for c in TITLES:
        for v in (0, 50, 100):
            p = dict(DEFAULTS)
            p[c] = v / 100
            write_frame(f"{c}-{v}", p)


def contact_png():
    from PIL import Image, ImageDraw
    rows = [["rest", "playing"]] + [[f"{c}-{v}" for v in (0, 50, 100)] for c in TITLES]
    gap, lab = 16, 18
    cols = 3
    sw = gap + cols * (W + gap)
    sh = gap + len(rows) * (H + lab + gap)
    sheet = Image.new("RGB", (sw, sh), (22, 22, 22))
    d = ImageDraw.Draw(sheet)
    for r, row in enumerate(rows):
        for c, name in enumerate(row):
            x = gap + c * (W + gap)
            y = gap + r * (lab + H + gap)
            d.text((x, y + 3), name.replace("-", " "), fill=(150, 150, 150))
            sheet.paste(Image.open(HERE / f"{name}.png").convert("RGB"), (x, y + lab))
    sheet.save(HERE / "contact.png")


# ---------------------------------------------------------------- motion
FPS = 16


def timeline_main():
    """A single note, then a rolled three-note chord, release, rest."""
    p = dict(DEFAULTS)
    voices = [Voice(0.50, 0, p["strike"], t_off=1.10),
              Voice(2.60, 0, p["strike"], t_off=3.90),
              Voice(2.78, 1, p["strike"], t_off=3.90),
              Voice(2.96, 2, p["strike"], t_off=3.90)]
    return [(p, voices)], 6.6


def timeline_compare(key, a, b):
    pa, pb = dict(DEFAULTS), dict(DEFAULTS)
    pa[key], pb[key] = a, b
    return [(pa, [Voice(0.4, 0, pa["strike"], t_off=0.9)]),
            (pb, [Voice(0.4, 0, pb["strike"], t_off=0.9)])], 4.2


def render_gif(name, segments, seg_len, scratch: Path, keep=()):
    from PIL import Image
    imgs, kept = [], {}
    fi = 0
    for p, voices in segments:
        n = int(round(seg_len * FPS))
        for i in range(n):
            t = i / FPS
            svg = write_frame(f"g{fi:04d}", p, voices, t, frame_index=fi, out_dir=scratch, png=True)
            im = Image.open(scratch / f"g{fi:04d}.png").convert("L")
            imgs.append(im)
            if round(t, 4) in keep:
                kept[round(t, 4)] = im.copy()
            svg.unlink()
            (scratch / f"g{fi:04d}.png").unlink()
            fi += 1
    pal = [im.convert("P", palette=Image.ADAPTIVE, colors=64) for im in imgs]
    pal[0].save(HERE / name, save_all=True, append_images=pal[1:], duration=int(1000 / FPS), loop=0,
                optimize=False, disposal=1)
    return kept


def motion_sheet(kept, times, captions):
    from PIL import Image, ImageDraw
    gap, lab = 16, 30
    cols = 2
    rows = math.ceil(len(times) / cols)
    sw = gap + cols * (W + gap)
    sh = gap + rows * (H + lab + gap)
    sheet = Image.new("RGB", (sw, sh), (22, 22, 22))
    d = ImageDraw.Draw(sheet)
    for i, t in enumerate(times):
        x = gap + (i % cols) * (W + gap)
        y = gap + (i // cols) * (H + lab + gap)
        d.text((x, y + 2), f"t = {t:.2f} s", fill=(205, 205, 205))
        d.text((x, y + 15), captions[i], fill=(150, 150, 150))
        sheet.paste(kept[round(t, 4)].convert("RGB"), (x, y + lab))
    sheet.save(HERE / "motion-sheet.png")


def motion():
    scratch = HERE / "_scratch"
    scratch.mkdir(exist_ok=True)
    try:
        segs, L = timeline_main()
        times = [0.25, 0.5, 0.5625, 0.75, 1.25, 2.6, 3.0, 3.375, 4.5, 6.25]
        times = [round(round(x * FPS) / FPS, 4) for x in times]
        caps = ["rest: still, nothing redraws",
                "note on: mallet on the rim, contact flash",
                "rebound; the lip starts to bend (n = 2..5)",
                "ringing: the fundamental's oval breathes",
                "note off at 1.10 s: the ring keeps its glaze decay",
                "chord: first strike (station 0, the mallet)",
                "second and third voices land along the rim",
                "three voices: patterns oriented by station",
                "released: decaying, faint upper shiver gone",
                "settled: identical to rest"]
        kept = render_gif("motion.gif", segs, L, scratch, keep=set(times))
        sel = [0, 1, 2, 3, 4, 6, 7, 9]
        motion_sheet(kept, [times[i] for i in sel], [caps[i] for i in sel])
        segs, L = timeline_compare("glaze", 0.0, 1.0)
        render_gif("motion-glaze.gif", segs, L, scratch)
        segs, L = timeline_compare("crack", 0.0, 1.0)
        render_gif("motion-crack.gif", segs, L, scratch)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def main():
    stills()
    contact_png()
    if "--stills" not in sys.argv:
        motion()


if __name__ == "__main__":
    main()
