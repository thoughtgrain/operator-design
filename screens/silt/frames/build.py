#!/usr/bin/env python3
"""Silt, frames and motion study for the picked subject (pass 02, v4).

A gold pan cut in half through its axis, edge-lit: the cut section is a thin dark
sheet with a lit inner edge, a rolled rim bead at each end, and three riffle steps
on the left wall. One grain per partial lies in a graded drift in the right-hand
crease (heavy grains at the bottom, fines on top). A note swirls the pan: the
water tips up the smooth right wall and the fines ride up in it, the finest
highest; then the water levels and the grains sink back at the settle rate.

Run from anywhere:  python3 screens/silt/frames/build.py [--no-gif]
Writes, beside this file: rest.svg/png, playing.svg/png, <control>-0/50/100.svg/png,
contact.png, motion.gif, motion-settle.gif, motion-sheet.png, and prints the
redraw estimate (changed nodes per frame, simulated at 60 Hz).

Device model (display.md, Frame): every bound part is a node that moves by
translate, uniform scale <= 2 and an in-plane turn. Mutable outlines (nodes 0, 1)
are the water's back edge, split in two to stay within +-64 px of their origins.
Node 2 is the waterline: a level ribbon turned, scaled and placed so its ends land
on the walls. Nodes 3..66 are the grains (translate + scale). Everything else is
static artwork. Frames bake each node's pose into its points so they lint as
plain previews (a bound transform must be matrix(1 0 0 1 x y)).
"""
from __future__ import annotations

import math
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 480, 220
FONT = "UniversNextPro-Light"
G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
HAIR, LINE, SUBJ = 1.0, 1.5, 2.2
PREFIX = "silt"

# ------------------------------------------------------------------ the sound
DEFAULTS = {"settle": 0.5, "layers": 0.5, "stir": 0.35, "grain": 0.0}
LAYERS = [2, 4, 8, 12, 16, 24, 32, 48, 64]
NMAX = 64


def settle_s(v):            # exponential 0.1 .. 10 s
    return 0.1 * (100 ** v)


def n_partials(v):
    return LAYERS[round(v * (len(LAYERS) - 1))]


def lift(k, n, stir):
    """Brief/DSP: a note lifts partial k by stir, more for higher partials (0..1)."""
    return stir * (((k - 1) / max(1, n - 1)) ** 0.8)


def jit(k, seed):
    return random.Random(seed * 7919 + k).random()


# ------------------------------------------------------------------- geometry
RB, RT, DEP = 1.0, 1.8, 0.8          # floor radius, rim radius, depth (world units)
KW = (RT - RB) / DEP                 # wall run per unit rise (45 degrees)
SHEET = 0.05                         # metal thickness
BEAD = 0.045                         # rolled rim bead radius
RIFFLES = [(0.25, 0.05), (0.40, 0.05), (0.55, 0.05)]   # (height, step) on the left wall
RIFFLE_SECTOR = (math.pi - 1.05, math.pi)               # back-left sector that carries them
ZW = 0.30                            # water depth at rest

TH0, TH1 = 3.0, 33.0                 # swirl tilt (world degrees) = TH0 + TH1 * stir
THMAX = 38.0                         # cap (chord boost)
HOLD = 0.2                           # held-note tilt, share of the swirl tilt
T_ATTACK = 0.18                      # swirl rise, s (ease-out, settles in 0.15-0.2 s)
TAU_UP = 0.05
TAU_WATER = 0.4                      # water levelling, s
TAU_RELEASE = 0.6                    # after the last note-off, grains finish within ~3 s


def wall_r(z, a=math.pi):
    """Inner radius at height z; the riffle steps live on the back-left sector (and the left cut)."""
    r = RB + KW * z
    if RIFFLE_SECTOR[0] <= a <= RIFFLE_SECTOR[1] + 1e-9:
        for zi, s in RIFFLES:
            if z >= zi:
                r += s
    return r


# ------------------------------------------------------------------- camera
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    L = math.sqrt(dot(a, a))
    return (a[0] / L, a[1] / L, a[2] / L)


class Camera:
    def __init__(self, eye, target, up=(0, 0, 1)):
        self.eye = eye
        self.fw = norm(sub(target, eye))
        self.rt = norm(cross(self.fw, up))
        self.up = cross(self.rt, self.fw)
        self.f, self.cx, self.cy = 1.0, 0.0, 0.0

    def raw(self, p):
        d = sub(p, self.eye)
        z = dot(d, self.fw)
        return dot(d, self.rt) / z, -dot(d, self.up) / z, z

    def fit(self, pts, box):
        r = [self.raw(p) for p in pts]
        xs, ys = [q[0] for q in r], [q[1] for q in r]
        x0, y0, x1, y1 = box
        s = min((x1 - x0) / (max(xs) - min(xs)), (y1 - y0) / (max(ys) - min(ys)))
        self.f = s
        self.cx = (x0 + x1) / 2 - s * (max(xs) + min(xs)) / 2
        self.cy = (y0 + y1) / 2 - s * (max(ys) + min(ys)) / 2

    def __call__(self, p):
        x, y, _ = self.raw(p)
        return (self.cx + self.f * x, self.cy + self.f * y)

    def ppu(self, p):
        return self.f / self.raw(p)[2]


CAM = Camera(eye=(0, -8.0, 2.6), target=(0, 0.25, 0.25))
CAM.fit([(-RT - 2 * BEAD, 0, DEP + BEAD), (RT + 2 * BEAD, 0, DEP + BEAD),
         (0, RT + 2 * BEAD, DEP + 2 * BEAD), (0, 0, -SHEET)], (62, 40, 418, 192))
PPU = CAM.ppu((0, 0, ZW))


def S(x, z, y=0.0):
    """Project a point of the section plane (or the pan) to the screen."""
    return CAM((x, y, z))


# ------------------------------------------------------------------- svg bits
def fmt(v):
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def ribbon_pts(pts, w):
    """Open centre line -> closed ribbon outline (left edge out, right edge back)."""
    h = w / 2
    n = len(pts)
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        if i == 0:
            dx, dy = pts[1][0] - x, pts[1][1] - y
        elif i == n - 1:
            dx, dy = x - pts[i - 1][0], y - pts[i - 1][1]
        else:
            ax, ay = x - pts[i - 1][0], y - pts[i - 1][1]
            bx, by = pts[i + 1][0] - x, pts[i + 1][1] - y
            la, lb = math.hypot(ax, ay) or 1, math.hypot(bx, by) or 1
            dx, dy = ax / la + bx / lb, ay / la + by / lb
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        m = 1.0
        if 0 < i < n - 1:
            ax, ay = x - pts[i - 1][0], y - pts[i - 1][1]
            la = math.hypot(ax, ay) or 1
            c = abs(nx * (-ay / la) + ny * (ax / la))
            m = min(2.0, 1 / max(c, 0.5))
        left.append((x + nx * h * m, y + ny * h * m))
        right.append((x - nx * h * m, y - ny * h * m))
    return left + right[::-1]


def thin(pts, minstep=0.6):
    out = []
    for p in pts:
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) >= minstep:
            out.append(p)
    return out


def resample(pts, n):
    """n points evenly spaced by arc length along an open polyline."""
    d = [0.0]
    for a, b in zip(pts, pts[1:]):
        d.append(d[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    total = d[-1]
    out, j = [], 0
    for i in range(n):
        s = total * i / (n - 1)
        while j < len(d) - 2 and d[j + 1] < s:
            j += 1
        seg = d[j + 1] - d[j] or 1
        t = (s - d[j]) / seg
        a, b = pts[j], pts[j + 1]
        out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def path_d(pts, ox=0.0, oy=0.0):
    return "M " + " L ".join(f"{fmt(x - ox)} {fmt(y - oy)}" for x, y in pts) + " Z"


class Frame:
    def __init__(self):
        self.items = []

    def poly(self, pts, fill, stroke="none", sw=None, ident=None, origin=None):
        attrs = ""
        if ident:
            attrs += f' id="{ident}"'
        ox, oy = origin if origin else (0.0, 0.0)
        if origin:
            attrs += f' transform="matrix(1 0 0 1 {fmt(ox)} {fmt(oy)})"'
        swa = f' stroke-width="{fmt(sw)}"' if stroke != "none" else ""
        self.items.append(f'  <path{attrs} d="{path_d(pts, ox, oy)}" fill="{fill}" stroke="{stroke}"{swa}/>')

    def line(self, pts, w, fill):
        """Static open line as closed ribbons of <= 31 points per edge."""
        pts = thin(pts)
        i = 0
        while i < len(pts) - 1:
            seg = pts[i:i + 31]
            if len(seg) >= 2:
                self.poly(ribbon_pts(seg, w), fill)
            i += 30

    def svg(self, captions):
        head = HEADER.format(*captions)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n'
                f"{head}\n" + "\n".join(self.items) + "\n</svg>\n")


HEADER = """  <g id="preview_canvas">
    <rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>
  </g>
  <g id="preview_header">
    <rect x="0" y="0" width="60" height="20" fill="#000000" stroke="none"/>
    <rect x="60" y="0" width="60" height="20" fill="#323232" stroke="none"/>
    <rect x="120" y="0" width="60" height="20" fill="#4B4B4B" stroke="none"/>
    <rect x="180" y="0" width="60" height="20" fill="#646464" stroke="none"/>
    <rect x="240" y="0" width="60" height="20" fill="#7D7D7D" stroke="none"/>
    <rect x="300" y="0" width="60" height="20" fill="#969696" stroke="none"/>
    <rect x="360" y="0" width="60" height="20" fill="#AFAFAF" stroke="none"/>
    <rect x="420" y="0" width="60" height="20" fill="#CDCDCD" stroke="none"/>
    <text transform="matrix(1 0 0 1 5 10)" fill="#CBCBCB" stroke="none" font-family="UniversNextPro-Light" font-size="10px">settle</text>
    <text transform="matrix(1 0 0 1 125 10)" fill="#CBCBCB" stroke="none" font-family="UniversNextPro-Light" font-size="10px">layers</text>
    <text transform="matrix(1 0 0 1 245 10)" fill="#000000" stroke="none" font-family="UniversNextPro-Light" font-size="10px">stir</text>
    <text transform="matrix(1 0 0 1 365 10)" fill="#000000" stroke="none" font-family="UniversNextPro-Light" font-size="10px">grain</text>
    <text transform="matrix(1 0 0 1 65 17.44)" fill="#CBCBCB" stroke="none" font-family="UniversNextPro-Light" font-size="20px">{0}</text>
    <text transform="matrix(1 0 0 1 185 17.44)" fill="#CBCBCB" stroke="none" font-family="UniversNextPro-Light" font-size="20px">{1}</text>
    <text transform="matrix(1 0 0 1 305 17.44)" fill="#000000" stroke="none" font-family="UniversNextPro-Light" font-size="20px">{2}</text>
    <text transform="matrix(1 0 0 1 425 17.44)" fill="#000000" stroke="none" font-family="UniversNextPro-Light" font-size="20px">{3}</text>
  </g>"""


def captions(c):
    s = settle_s(c["settle"])
    st = f"{s:.1f}s" if s < 9.95 else f"{s:.0f}s"
    return st, str(n_partials(c["layers"])), str(round(c["stir"] * 100)), str(round(c["grain"] * 100))


# ------------------------------------------------------------ static artwork
def arc(r_of_a, z_of_a, a0, a1, m=48):
    pts = []
    for i in range(m):
        a = a0 + (a1 - a0) * i / (m - 1)
        r = r_of_a(a)
        pts.append(CAM((r * math.cos(a), r * math.sin(a), z_of_a(a))))
    return pts


def section_profile(side):
    """Inner surface of the cut wall + floor half, from the floor centre out to the rim (section plane)."""
    pts = [(0.0, 0.0), (side * RB, 0.0)]
    if side < 0:
        z = 0.0
        for zi, s in RIFFLES:
            pts.append((-(wall_r(zi - 1e-6)), zi))           # up the slope to the riffle
            pts.append((-(wall_r(zi)), zi))                   # step out (the ledge)
        pts.append((-wall_r(DEP), DEP))
    else:
        pts.append((RT, DEP))
    return pts


def static_art(f: Frame):
    # back rim: the lit top of the rolled bead (Line), its inner lip (hairline)
    f.line(arc(lambda a: RT + 2 * BEAD, lambda a: DEP + BEAD, 0, math.pi, 64), LINE, G5)
    f.line(arc(lambda a: RT, lambda a: DEP, 0.03, math.pi - 0.03, 64), HAIR, G3)
    # back floor edge, where the floor meets the back wall
    f.line(arc(lambda a: RB, lambda a: 0.0, 0.02, math.pi - 0.02, 48), HAIR, G3)
    # riffles: the ledges on the back-left wall, ending where the sector ends
    a0, a1 = RIFFLE_SECTOR
    for zi, s in RIFFLES:
        f.line(arc(lambda a, zi=zi: wall_r(zi), lambda a, zi=zi: zi, a0 + 0.04, a1 - 0.02, 32), HAIR, G4)
    # the cut: a thin dark sheet (solid body) with a lit inner edge and a bead at each rim
    for side in (-1, 1):
        inner = section_profile(side)
        outer = []
        # outer skin: offset by the sheet thickness along the outward normal of each segment
        for i, (x, z) in enumerate(inner):
            if i == 0:
                outer.append((x, z - SHEET))
                continue
            px, pz = inner[i - 1]
            dx, dz = x - px, z - pz
            L = math.hypot(dx, dz) or 1
            nx, nz = side * dz / L, -side * dx / L      # outward/down
            outer.append((x + nx * SHEET, z + nz * SHEET))
        # simplify: the outer skin is the plain trapezoid (riffles are pressed in, the outside is smooth)
        outer = [(0.0, -SHEET), (side * (RB + SHEET * 0.41), -SHEET), (side * (RT + SHEET * 1.41), DEP)]
        body = [S(x, z) for x, z in inner] + [S(x, z) for x, z in outer[::-1]]
        f.poly(body, G1)
    for side in (-1, 1):
        inner = section_profile(side)
        f.line([S(x, z) for x, z in inner][::side] if side > 0 else [S(x, z) for x, z in inner], LINE, G5)
        # rolled rim bead
        cx, cz = side * (RT + BEAD), DEP + BEAD * 0.2
        bead = [S(cx + BEAD * math.cos(t / 14 * 2 * math.pi), cz + BEAD * math.sin(t / 14 * 2 * math.pi)) for t in range(14)]
        f.poly(bead, G1, G5, 1.2)


# ------------------------------------------------------------------ the water
def surface_z(x, c, t):
    return c + t * x


def section_area(c, t, steps=240):
    """Water area in the section: between floor and surface, inside the walls."""
    xl, xr = -wall_r(DEP), RT
    area = 0.0
    dx = (xr - xl) / steps
    for i in range(steps):
        x = xl + (i + 0.5) * dx
        zs = surface_z(x, c, t)
        if zs <= 0:
            continue
        # the wall at this x: lowest z the water can have here
        if abs(x) <= RB:
            zfloor = 0.0
        elif x > 0:
            zfloor = (x - RB) / KW
        else:
            zfloor = 0.0
            # left stepped wall: find z where wall_r(z) == -x
            lo, hi = 0.0, DEP
            if wall_r(DEP) < -x:
                continue
            for _ in range(30):
                mid = (lo + hi) / 2
                if wall_r(mid) < -x:
                    lo = mid
                else:
                    hi = mid
            zfloor = hi
        if zs > zfloor:
            area += (zs - zfloor) * dx
    return area


A0 = None


def water_c(theta_deg):
    """Offset c of the tilted surface that keeps the section's water area constant."""
    global A0
    if A0 is None:
        A0 = section_area(ZW, 0.0)
    t = math.tan(math.radians(theta_deg))
    lo, hi = -2.0, 2.0
    for _ in range(50):
        mid = (lo + hi) / 2
        if section_area(mid, t) < A0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def solve_wall(c, t, a):
    """Where the surface plane z = c + t x meets the pan at azimuth a: (x, y, z), on the wall or the floor."""
    ca = math.cos(a)

    def f(z):
        return c + t * wall_r(z, a) * ca - z
    if f(0.0) < 0:
        # the surface is below the floor at the wall: the edge is on the floor, where c + t x = 0
        if abs(t) < 1e-9:
            return None
        x0 = -c / t
        return ("floor", x0)
    lo, hi = 0.0, DEP
    if f(DEP) > 0:
        z = DEP
    else:
        for _ in range(40):
            mid = (lo + hi) / 2
            if f(mid) > 0:
                lo = mid
            else:
                hi = mid
        z = (lo + hi) / 2
    r = wall_r(z, a)
    return ("wall", (r * ca, r * math.sin(a), z))


def water_geometry(theta_deg):
    """Chord ends (section plane) and the water's back edge (screen points)."""
    c = water_c(theta_deg)
    t = math.tan(math.radians(theta_deg))
    back = []
    floor_x0 = None
    for i in range(121):
        a = i / 120 * math.pi
        hit = solve_wall(c, t, a)
        if hit[0] == "wall":
            back.append(hit[1])
        else:
            floor_x0 = hit[1]
            back.append(None)
    # the floor run: where the surface meets the floor, a straight line x = x0 from the back wall to the cut
    pts3 = []
    for i, p in enumerate(back):
        if p is not None:
            pts3.append(p)
        elif floor_x0 is not None and (i == 0 or back[i - 1] is not None):
            yb = math.sqrt(max(RB * RB - floor_x0 * floor_x0, 0))
            pts3.append((floor_x0, yb, 0.0))
            # walk toward the camera along the floor to the cut
            for j in range(1, 9):
                pts3.append((floor_x0, yb * (1 - j / 8), 0.0))
            break
    # ends in the section plane
    right = pts3[0]
    left = pts3[-1]
    scr = [CAM(p) for p in pts3]
    return {"c": c, "t": t, "left": (left[0], left[2]), "right": (right[0], right[2]), "back": scr}


# ------------------------------------------------------------------ grains
R1_PX, ALPHA = 4.8, 0.26          # grain radius in px at scale 1: k = 1 -> 4.8, k = 64 -> ~1.65


def grain_r_px(k):
    return R1_PX * k ** -ALPHA


def grain_shape(k):
    """Authored outline, relative to the grain's origin, at scale 1: an irregular 7-gon."""
    r = grain_r_px(k)
    rng = random.Random(400 + k)
    rot = rng.uniform(0, math.pi)
    return [(r * (1 + 0.18 * rng.uniform(-1, 1)) * math.cos(rot + i / 7 * 2 * math.pi),
             r * (0.82 + 0.14 * rng.uniform(-1, 1)) * math.sin(rot + i / 7 * 2 * math.pi)) for i in range(7)]


_BED = {}


def bed(n, gscale):
    """Graded drift in the right crease, in section coordinates (x, z). Heavy first, at the bottom."""
    key = (n, round(gscale, 3))
    if key in _BED:
        return _BED[key]
    placed = []
    root = math.sqrt(1 + KW * KW)
    for k in range(1, n + 1):
        r = grain_r_px(k) * gscale / PPU * 0.92
        best = None
        for i in range(260):
            x = RB + RT - RB - i * 0.006 - 0.8      # sweep from up the wall leftwards across the floor
            x = RB + 0.35 - i * 0.006
            zmin = max(r + SHEET * 0 + 0.012, (x - RB + r * root) / KW if KW else r)
            z = zmin
            for (xj, zj, rj) in placed:
                d = r + rj + 0.004
                if abs(x - xj) < d:
                    z = max(z, zj + math.sqrt(d * d - (x - xj) ** 2))
            cost = z + 0.30 * (RB - x)
            if best is None or cost < best[0]:
                best = (cost, x, z)
        placed.append((best[1], best[2], r))
    _BED[key] = [(x, z) for x, z, _ in placed]
    return _BED[key]


def grain_target(k, n, geo, gscale):
    """Where grain k rides to at full lift: up the right wall, inset, just under the surface."""
    c, t = geo["c"], geo["t"]
    d = 0.10 + 0.42 * jit(k, 3)                      # inset from the wall
    m = 0.05 + grain_r_px(k) * gscale / PPU
    den = 1 - t * KW
    z = (c + t * (RB - d)) / den if den > 0.05 else DEP
    z = min(z, DEP - 0.05)
    z = (z - m) * (0.80 + 0.20 * jit(k, 5))
    x = RB + KW * max(z, 0) - d
    return x, z


# ------------------------------------------------------------------ the state
class State:
    """Everything display() would keep: eased tilt, per-grain lift, the note gate."""

    def __init__(self, ctl):
        self.ctl = dict(ctl)
        self.theta = 0.0
        self.lam = [0.0] * (NMAX + 1)
        self.attack = 0.0
        self.since = 9.0
        self.peak = 0.0
        self.lt = [0.0] * (NMAX + 1)
        self.held = False
        self.released = True

    def note_on(self, m=1):
        stir = self.ctl["stir"]
        boost = min(1.25, 1 + 0.1 * (m - 1))
        base = TH0 + TH1 * stir
        self.peak = min(THMAX, max(self.theta, base * boost))
        n = n_partials(self.ctl["layers"])
        for k in range(1, n + 1):
            self.lt[k] = min(1.0, max(self.lam[k], lift(k, n, stir) * boost))
        self.attack = T_ATTACK
        self.since = 0.0
        self.held = True
        self.released = False

    def note_off(self):
        self.held = False
        self.released = True

    def step(self, dt):
        tau = settle_s(self.ctl["settle"])
        if self.released:
            tau = min(tau, TAU_RELEASE)
        n = n_partials(self.ctl["layers"])
        base = TH0 + TH1 * self.ctl["stir"]
        self.since += dt
        if self.attack > 0:
            a = 1 - math.exp(-dt / TAU_UP)
            self.theta += (self.peak - self.theta) * a
            decay = math.exp(-self.since / tau)
            for k in range(1, n + 1):
                tgt = self.lt[k] * decay
                if tgt > self.lam[k]:
                    self.lam[k] += (tgt - self.lam[k]) * a
                else:
                    self.lam[k] *= math.exp(-dt / tau)
            self.attack -= dt
        else:
            rest = HOLD * base if self.held else 0.0
            self.theta += (rest - self.theta) * (1 - math.exp(-dt / TAU_WATER))
            if abs(self.theta - rest) < 0.15:
                self.theta = rest
            for k in range(1, n + 1):
                self.lam[k] *= math.exp(-dt / tau)
        for k in range(n + 1, NMAX + 1):
            self.lam[k] = 0.0


def pose(state):
    """Node poses for a state: what display() writes. Returns dict with screen geometry."""
    ctl = state.ctl
    n = n_partials(ctl["layers"])
    gscale = 1 + ctl["grain"]                     # node scale 1 .. 2
    th = round(state.theta / 0.2) * 0.2           # quantised tilt: the outlines' key
    geo = water_geometry(th)
    beds = bed(n, gscale)
    grains = []
    for k in range(1, n + 1):
        bx, bz = beds[k - 1]
        lam = state.lam[k]
        if lam > 0:
            tx, tz = grain_target(k, n, geo, gscale)
            x, z = bx + (tx - bx) * lam, bz + (tz - bz) * lam
            # stay in the water and inside the wall
            zs = surface_z(x, geo["c"], geo["t"]) - grain_r_px(k) * gscale / PPU - 0.02
            z = max(bz if lam < 1e-3 else 0.02, min(z, zs)) if zs > bz else bz
            p = S(x, z)
            pb = S(bx, bz)
            if math.hypot(p[0] - pb[0], p[1] - pb[1]) < 0.5:
                state.lam[k] = 0.0
                p = pb
        else:
            p = S(bx, bz)
        grains.append((k, (round(p[0]), round(p[1])), gscale))
    return {"theta": th, "geo": geo, "grains": grains, "n": n}


# --------------------------------------------------------------- the frame
WL_W0 = 2.0          # waterline ribbon width as authored (level, scale 1)
WL_L0 = None         # authored length = the level chord on screen


def waterline_pose(geo):
    global WL_L0
    a, b = S(*geo["left"]), S(*geo["right"])
    if WL_L0 is None:
        g0 = water_geometry(0.0)
        a0, b0 = S(*g0["left"]), S(*g0["right"])
        WL_L0 = math.hypot(b0[0] - a0[0], b0[1] - a0[1])
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    return mid, ang, L / WL_L0, a, b


def draw(state, captions_=None):
    p = pose(state)
    f = Frame()
    # palette entries, parked off screen
    f.items.append(f'  <path id="{PREFIX}_palette_0" d="M 700 300 L 704 300 L 704 304 Z" fill="{G7}" stroke="none"/>')
    f.items.append(f'  <path id="{PREFIX}_palette_1" d="M 710 300 L 714 300 L 714 304 Z" fill="{G0}" stroke="{G5}" stroke-width="1"/>')
    f.items.append(f'  <path id="{PREFIX}_palette_2" d="M 720 300 L 724 300 L 724 304 Z" fill="{G4}" stroke="none"/>')
    # back half and the cut (static)
    static_back = Frame()
    static_art(static_back)
    # split static: everything before the cut is drawn first, the cut after the water edge
    items = static_back.items
    cut_from = next(i for i, s in enumerate(items) if f'fill="{G1}"' in s)
    f.items += items[:cut_from]
    # nodes 0, 1: the water's back edge, two halves of one ribbon line, overlapping 3 px at the seam
    back = p["geo"]["back"]
    half = resample(back, 200)
    mid = 100
    for i, part in enumerate((half[:mid + 3], half[mid - 3:])):
        cl = resample(part, 24)
        rib = ribbon_pts(cl, 1.2)
        xs, ys = [q[0] for q in rib], [q[1] for q in rib]
        org = (round((min(xs) + max(xs)) / 2, 1), round((min(ys) + max(ys)) / 2, 1))
        f.poly(rib, G4, ident=f"{PREFIX}_node_{i}", origin=org)
    # the cut wall, drawn over the ends of the water's edge
    f.items += items[cut_from:]
    # grains: nodes 3.., hidden ones parked
    gpos = {k: (xy, sc) for k, xy, sc in p["grains"]}
    for k in range(1, NMAX + 1):
        ident = f"{PREFIX}_node_{k + 2}"
        shape = grain_shape(k)
        if k in gpos:
            (x, y), sc = gpos[k]
            pts = [(x + sc * u, y + sc * v) for u, v in shape]
            f.poly(pts, G0, G5, 1.0, ident=ident, origin=(x, y))
        else:
            pts = [(640 + u, 320 + v) for u, v in shape]
            f.poly(pts, G0, G5, 1.0, ident=ident, origin=(640, 320))
    # node 2: the waterline, brightest, last
    mid_, ang, sc, a, b = waterline_pose(p["geo"])
    rib = ribbon_pts([a, b], WL_W0 * sc)
    f.items.append(f'  <path id="{PREFIX}_node_2" transform="matrix(1 0 0 1 {fmt(mid_[0])} {fmt(mid_[1])})" '
                   f'd="{path_d(rib, *mid_)}" fill="{G7}" stroke="none"/>')
    return f.svg(captions_ or captions(state.ctl)), p


# --------------------------------------------------------------- scenarios
def run(ctl, events, t_end, fps=60, sample=None):
    """Simulate: events = [(t, 'on', m) | (t, 'off')]. Returns sampled states (deep copies) and redraw counts."""
    import copy
    st = State(ctl)
    dt = 1 / fps
    ev = sorted(events, key=lambda e: e[0])
    out, counts = [], []
    prev = None
    sounding = False
    tt = 0.0
    i = 0
    samples = sorted(sample or [])
    si = 0
    frame = 0
    while tt <= t_end + 1e-9:
        while i < len(ev) and ev[i][0] <= tt + 1e-9:
            e = ev[i]
            if e[1] == "on":
                st.note_on(e[2] if len(e) > 2 else 1)
                sounding = True
            else:
                st.note_off()
            i += 1
        st.step(dt)
        ps = pose(st)
        sig = (round(ps["theta"], 2), tuple(xy for _, xy, _ in ps["grains"]))
        if prev is not None:
            changed = 0
            if sig[0] != prev[0]:
                changed += 3                      # both outline halves + the waterline
            changed += sum(1 for a_, b_ in zip(sig[1], prev[1]) if a_ != b_)
            counts.append((tt, changed, sounding))
        prev = sig
        while si < len(samples) and samples[si] <= tt + 1e-9:
            out.append((samples[si], copy.deepcopy(st)))
            si += 1
        tt += dt
        frame += 1
    return out, counts


def snapshot(ctl, t):
    """State t seconds after one held note."""
    res, _ = run(ctl, [(0.0, "on", 1)], t + 0.001, fps=120, sample=[t])
    return res[0][1]


def rest_state(ctl):
    return State(ctl)


# --------------------------------------------------------------- rendering
RSVG = shutil.which("rsvg-convert")


def to_png(svg_path, png_path, w=W, h=H):
    subprocess.run([RSVG, "-w", str(w), "-h", str(h), "-b", "black", "-o", str(png_path), str(svg_path)], check=True)


def write(name, svg):
    p = HERE / f"{name}.svg"
    p.write_text(svg)
    to_png(p, HERE / f"{name}.png")
    return p


STIR_T = 0.20       # stir stills: the swirl at its peak
SETTLE_T = 0.60     # settle stills: mid-fall


def stills():
    files = []
    svg, _ = draw(rest_state(DEFAULTS))
    files.append(write("rest", svg))
    svg, _ = draw(snapshot(DEFAULTS, STIR_T))
    files.append(write("playing", svg))
    for ctl_name in ("settle", "layers", "stir", "grain"):
        for v in (0, 50, 100):
            c = dict(DEFAULTS)
            c[ctl_name] = v / 100
            if ctl_name == "stir":
                s = snapshot(c, STIR_T)
            elif ctl_name == "settle":
                s = snapshot(c, SETTLE_T)
            else:
                s = rest_state(c)
            svg, _ = draw(s)
            files.append(write(f"{ctl_name}-{v}", svg))
    return files


def label_font(size=12):
    from PIL import ImageFont
    for cand in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "/usr/share/fonts/dejavu/DejaVuSans.ttf"):
        if Path(cand).exists():
            return ImageFont.truetype(cand, size)
    return ImageFont.load_default()


def contact():
    from PIL import Image, ImageDraw
    rows = [["rest", "playing"]] + [[f"{c}-{v}" for v in (0, 50, 100)] for c in ("settle", "layers", "stir", "grain")]
    notes = {"playing": "playing (0.2 s after a note)", "settle-0": "settle 0 (0.6 s after a note)",
             "settle-50": "settle 50 (0.6 s after a note)", "settle-100": "settle 100 (0.6 s after a note)",
             "stir-0": "stir 0 (0.2 s after a note)", "stir-50": "stir 50 (0.2 s after a note)",
             "stir-100": "stir 100 (0.2 s after a note)"}
    gap, lab = 16, 18
    sw = gap + 3 * (W + gap)
    sh = gap + len(rows) * (H + lab + gap)
    sheet = Image.new("RGB", (sw, sh), (22, 22, 22))
    d = ImageDraw.Draw(sheet)
    font = label_font(12)
    for r, row in enumerate(rows):
        for c, name in enumerate(row):
            x, y = gap + c * (W + gap), gap + r * (H + lab + gap)
            sheet.paste(Image.open(HERE / f"{name}.png").convert("RGB"), (x, y))
            text = notes.get(name, name.replace("-", " ") if name != "rest" else "rest (settled)")
            d.text((x, y + H + 3), text, fill=(200, 200, 200), font=font)
    sheet.save(HERE / "contact.png")


def render_seq(states_ctl, tmp, fps):
    """states: list of (State) -> list of PIL images at 1:1."""
    from PIL import Image
    imgs = []
    for i, st in enumerate(states_ctl):
        svg, _ = draw(st)
        sp = Path(tmp) / f"f{i:04d}.svg"
        pp = Path(tmp) / f"f{i:04d}.png"
        sp.write_text(svg)
        to_png(sp, pp)
        imgs.append(Image.open(pp).convert("RGB"))
    return imgs


PHRASE = [(0.40, "on", 1), (0.95, "off"),                       # one note, settles
          (3.60, "on", 1), (3.78, "off"), (3.80, "on", 1), (3.98, "off"),
          (4.00, "on", 1), (4.18, "off"), (4.40, "on", 3), (5.20, "off")]   # a quick phrase, a chord
PHRASE_END = 8.6


def gif_frames(ctl, events, t_end, fps):
    times = [i / fps for i in range(int(t_end * fps) + 1)]
    res, _ = run(ctl, events, t_end, fps=120, sample=times)
    return [s for _, s in res], times


def motion_gif(tmp):
    from PIL import Image
    fps = 15
    states, times = gif_frames(DEFAULTS, PHRASE, PHRASE_END, fps)
    imgs = render_seq(states, tmp, fps)
    gimgs = [im.convert("P", palette=Image.ADAPTIVE, colors=64) for im in imgs]
    gimgs[0].save(HERE / "motion.gif", save_all=True, append_images=gimgs[1:], duration=int(1000 / fps), loop=0,
                  optimize=False, disposal=1)
    # key frames
    keys = [0.0, 0.52, 0.62, 1.0, 1.6, 3.4, 3.92, 4.6, 5.6, 8.5]
    return imgs, times, keys


def motion_sheet(imgs, times, keys, fps):
    from PIL import Image, ImageDraw
    gap, lab = 14, 20
    cols = 2
    rows = (len(keys) + cols - 1) // cols
    sheet = Image.new("RGB", (gap + cols * (W + gap), gap + rows * (H + lab + gap)), (22, 22, 22))
    d = ImageDraw.Draw(sheet)
    font = label_font(12)
    descr = {0.0: "rest: level water, grains in the crease", 0.52: "note on: the swirl tips the water",
             0.62: "swirl at its peak, fines highest", 1.0: "note off: water levels, fines sinking",
             1.6: "fines still falling (settle 1.0 s)", 3.4: "settled, still",
             3.92: "repeated notes re-stir before it settles", 4.6: "a chord: one harder swirl",
             5.6: "released: water levels, grains sink", 8.5: "rest again: zero changed nodes"}
    for i, t in enumerate(keys):
        j = min(range(len(times)), key=lambda q: abs(times[q] - t))
        x = gap + (i % cols) * (W + gap)
        y = gap + (i // cols) * (H + lab + gap)
        sheet.paste(imgs[j], (x, y))
        d.text((x, y + H + 4), f"t = {times[j]:.2f} s   {descr.get(t, '')}", fill=(200, 200, 200), font=font)
    sheet.save(HERE / "motion-sheet.png")


def settle_gif(tmp):
    from PIL import Image, ImageDraw
    fps = 15
    ev = [(0.4, "on", 1), (4.4, "off")]
    t_end = 5.6
    panes = []
    for v in (0.0, 1.0):
        c = dict(DEFAULTS, settle=v, stir=0.8)
        states, times = gif_frames(c, ev, t_end, fps)
        sub_ = Path(tmp) / f"s{int(v)}"
        sub_.mkdir()
        panes.append(render_seq(states, sub_, fps))
    gap = 8
    frames = []
    for a, b in zip(*panes):
        im = Image.new("RGB", (2 * W + gap, H), (22, 22, 22))
        im.paste(a, (0, 0))
        im.paste(b, (W + gap, 0))
        frames.append(im.convert("P", palette=Image.ADAPTIVE, colors=64))
    frames[0].save(HERE / "motion-settle.gif", save_all=True, append_images=frames[1:], duration=int(1000 / fps),
                   loop=0, disposal=1)


# --------------------------------------------------------------- budget
def budget():
    """Changed nodes per frame at 60 Hz while sounding (note on to the last still frame)."""
    rows = []
    rapid = [(0.0 + i * 0.125, "on", 1) for i in range(16)] + [(2.0, "off")]
    cases = [("defaults, the GIF phrase", DEFAULTS, PHRASE, PHRASE_END + 3),
             ("defaults, 16ths for 2 s", DEFAULTS, rapid, 8),
             ("heaviest: 64 layers, stir 100, grain 100, settle 0.1 s, 16ths", dict(settle=0.0, layers=1.0, stir=1.0, grain=1.0), rapid, 8),
             ("heaviest: 64 layers, stir 100, grain 100, settle 1 s, 16ths", dict(settle=0.5, layers=1.0, stir=1.0, grain=1.0), rapid, 8),
             ("heaviest: 64 layers, stir 100, grain 100, settle 10 s, 16ths", dict(settle=1.0, layers=1.0, stir=1.0, grain=1.0), rapid, 8),
             ("64 layers, stir 100, settle 10 s, one held note (4 s)", dict(settle=1.0, layers=1.0, stir=1.0, grain=0.0), [(0.0, "on", 1), (4.0, "off")], 9)]
    for name, c, ev, t_end in cases:
        _, counts = run(c, ev, t_end, fps=60)
        # active span: from the first note to the last frame with any change
        last = max((t for t, n, _ in counts if n > 0), default=0)
        first = min(e[0] for e in ev)
        act = [n for t, n, _ in counts if first <= t <= last]
        tail = [n for t, n, _ in counts if t > last]
        rows.append((name, sum(act) / max(1, len(act)), max(act), last, sum(tail)))
    return rows


def main():
    if not RSVG:
        sys.exit("needs rsvg-convert")
    stills()
    contact()
    if "--no-gif" not in sys.argv:
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            imgs, times, keys = motion_gif(tmp)
            motion_sheet(imgs, times, keys, 15)
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            settle_gif(tmp)
    if "--budget" in sys.argv:
        for name, avg, peak, last, tail in budget():
            print(f"{name}: average {avg:.1f}, peak {peak}, still from {last:.2f} s (after that: {tail} changes)")


if __name__ == "__main__":
    main()
