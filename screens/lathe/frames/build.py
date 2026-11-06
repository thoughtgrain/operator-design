#!/usr/bin/env python3
"""Lathe · cleaned v3 frames: the lacquer under a microscope at grazing light.

One camera, one model. The lacquer coat is the plane z = 0, the grooves run away from the eye
along world y, and the near edge of the field is the coat's cut face (y = Y0), where every groove
shows as a V notch. Light comes in low from the right, so each groove's left wall is the lit one:
its left lip (the lit lip, Line weight) and its floor (hairline) bound that wall. The right walls,
the lands and the uncut lacquer are black. The newest groove (the one the cutter is laying down
now) is the one bright line; the turns already cut sit to its right, toward the rim; uncut lacquer
is to its left. Lines dim with depth (the objective's depth of field) and stop at a round field stop
centred below the frame.

Controls, each on its own channel (an effect page gets nothing live, so nothing else moves):
    cut     shape: the newest groove's swing widens and its crests flatten (nodes 0, 1)
    groove  count: further in, more earlier turns lie beside the newest one, the rim bevel steps out
    wear    count: specks and short scratches on the lands between earlier turns
    rumble  position: the newest lip shakes into a double exposure, two ghosts either side (nodes 2, 3)

    python3 screens/lathe/frames/build.py            # rest + per-control frames (svg + png)
    python3 screens/lathe/frames/build.py --sheets   # also before-after.png, contact.png, sweep.gif
"""
from __future__ import annotations

import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
W, H = 480, 220

G0, G1, G2, G3, G4, G5, G6, BK = ("#CDCDCD", "#AFAFAF", "#969696", "#7D7D7D",
                                  "#646464", "#4B4B4B", "#323232", "#000000")
PALETTE = [G0, G2, G3, G4, G5]
FONT = 'font-family="UniversNextPro-Light"'
HAIR, LINE, SUBJ = 1.0, 1.5, 2.0
PARK = (640, 320)
NPTS = 32                       # centre-line points of a mutable ribbon -> 64-point outline

# ------------------------------------------------------------------ model
P = 0.152                       # groove pitch (world)
HW = 0.036                      # groove half-width at the surface
DEPTH = 0.046                   # 90 degree stylus: depth = half-width
CENTRE_X = 172                  # principal point: the newest groove stands upright here
Y_NEAR_SCREEN, Y_FAR_SCREEN = 166.0, 44.0
FIELD = (236.0, 310.0, 275.0)   # field stop: centre x, centre y, radius (screen)
TOP = 40.0                      # nothing above this (header clearance)
SPLIT_SCREEN = 122.0            # depth of field: lips dim in three runs, walls dissolve at WALL_SCREEN
FAR_SCREEN = 70.0
WALL_SCREEN = 58.0
OLD_AMP = 0.014                 # earlier turns: swing as cut at 1.00
DEFAULT_TURNS, MAX_TURNS = 3, 6
COAT = 0.11                     # lacquer coat thickness over the aluminium


class Camera:
    """Pinhole camera; world z is up."""

    def __init__(self, pos, look, focal, centre):
        self.p = pos
        f = [look[i] - pos[i] for i in range(3)]
        L = math.sqrt(sum(v * v for v in f))
        self.fw = [v / L for v in f]
        r = (self.fw[1], -self.fw[0], 0.0)
        L = math.hypot(r[0], r[1])
        self.rt = (r[0] / L, r[1] / L, 0.0)
        a, b = self.rt, self.fw
        self.up = (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
        self.F, self.c = focal, centre

    def __call__(self, q):
        d = [q[i] - self.p[i] for i in range(3)]
        x = sum(d[i] * self.rt[i] for i in range(3))
        y = sum(d[i] * self.up[i] for i in range(3))
        z = sum(d[i] * self.fw[i] for i in range(3))
        return (self.c[0] + self.F * x / z, self.c[1] - self.F * y / z)


_ang = math.radians(56)
CAM = Camera((0.0, 0.0, 2.0), (0.0, 2.0 / math.tan(_ang), 0.0), 680, (CENTRE_X, 104))


def _y_for_screen(target):
    lo, hi = 0.01, 40.0
    for _ in range(80):
        m = (lo + hi) / 2
        if CAM((0, m, 0))[1] > target:
            lo = m
        else:
            hi = m
    return (lo + hi) / 2


Y0 = _y_for_screen(Y_NEAR_SCREEN)
Y1 = _y_for_screen(Y_FAR_SCREEN)
Y_WALL = _y_for_screen(WALL_SCREEN)


# ------------------------------------------------------------------ the controls
def cut_ratio(k):
    return 0.5 * 8 ** k


def amounts(cut=1 / 3, groove=0.0, wear=0.0, rumble=0.0):
    """Knob positions (0..1) -> what the drawing uses, plus the header captions."""
    ratio = cut_ratio(cut)
    wear_v = wear ** 1.5
    rumble_v = rumble ** 2
    return {
        "ratio": ratio,
        "turns": DEFAULT_TURNS + int(math.floor(groove * (MAX_TURNS - DEFAULT_TURNS) + 0.5)),
        "wear": wear_v,
        "rumble": rumble_v,
        "values": [f"{ratio:.2f}", f"{round(groove * 100)}", f"{round(wear_v * 100)}", f"{round(rumble_v * 100)}"],
    }


def signal(t, k):
    """The modulation cut into turn k, along its length t 0..1; zero at the near face."""
    if k == 0:
        s = 0.8 * math.sin(2 * math.pi * 2.25 * t) + 0.2 * math.sin(2 * math.pi * 4.5 * t)
        return s / 0.93
    f1 = 1.25 + 0.3 * k
    return (0.8 * math.sin(2 * math.pi * f1 * t) + 0.2 * math.sin(2 * math.pi * (2.6 * f1) * t)) / 0.93


def swing(t, ratio):
    """The cutter: gain into a soft limit. Amplitude grows with the ratio and the crests flatten."""
    amax = 0.052
    return amax * math.tanh(0.3 * ratio * signal(t, 0))


def lateral(k, t, ratio):
    if k == 0:
        return swing(t, ratio)
    return OLD_AMP * signal(t, k)


def in_field(p):
    cx, cy, r = FIELD
    return math.hypot(p[0] - cx, p[1] - cy) <= r and p[1] >= TOP


# ------------------------------------------------------------------ svg writer
def f(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def ribbon_outline(pts, w):
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


class Frame:
    def __init__(self, values):
        self.values = values
        self.out: list[str] = []
        self.nodes = 0

    def _emit(self, pts, fill, stroke="none", sw=0.0, node=None, origin=None, exact=None):
        clean = []
        for x, y in pts:
            p = (round(x, 2), round(y, 2))
            if exact is None and clean and math.dist(p, clean[-1]) < 0.3:
                continue
            clean.append(p)
        if exact is None:
            while len(clean) > 2 and math.dist(clean[0], clean[-1]) < 0.4:
                clean.pop()
        else:
            assert len(clean) == exact, (len(clean), exact)
            assert len(set(clean)) == exact, "mutable outline points must be distinct"
        assert 3 <= len(clean) <= 64, len(clean)
        tr = ""
        if origin is not None:
            ox, oy = origin
            clean = [(round(x - ox, 2), round(y - oy, 2)) for x, y in clean]
            tr = f' transform="matrix(1 0 0 1 {f(ox)} {f(oy)})"'
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in clean) + " Z"
        ident = f' id="lathe_node_{node}"' if node is not None else ""
        self.out.append(f'  <path{ident} d="{d}"{tr} fill="{fill}" stroke="{stroke}" stroke-width="{f(sw)}"/>')

    def ribbon(self, pts, w, fill, node=None, origin=None, shown=True, exact=None):
        if len(pts) < 2:
            return
        outline = ribbon_outline(pts, w)
        if node is not None:
            if origin is None:
                xs = [p[0] for p in outline]
                ys = [p[1] for p in outline]
                origin = (round((min(xs) + max(xs)) / 2, 1), round((min(ys) + max(ys)) / 2, 1))
            if not shown:   # parked: same shape, origin moved off canvas
                outline = [(x - origin[0] + PARK[0], y - origin[1] + PARK[1]) for x, y in outline]
                origin = PARK
        self._emit(outline, fill, node=node, origin=origin, exact=exact)

    def blob(self, pts, fill, node=None, shown=True):
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        origin = (round((min(xs) + max(xs)) / 2, 1), round((min(ys) + max(ys)) / 2, 1))
        if not shown:
            pts = [(x - origin[0] + PARK[0], y - origin[1] + PARK[1]) for x, y in pts]
            origin = PARK
        self._emit(pts, fill, node=node, origin=origin if node is not None else None)

    def svg(self):
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
        titles = ["cut", "groove", "wear", "rumble"]
        for k in range(4):
            ink = "#CBCBCB" if k < 2 else "#000000"
            head.append(f'    <text transform="matrix(1 0 0 1 {5 + 120 * k} 10)" fill="{ink}" stroke="none" '
                        f'{FONT} font-size="10px">{titles[k]}</text>')
        for k in range(4):
            ink = "#CBCBCB" if k < 2 else "#000000"
            head.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * k} 17.44)" fill="{ink}" stroke="none" '
                        f'{FONT} font-size="20px">{self.values[k]}</text>')
        head.append('  </g>')
        pal = [f'  <path id="lathe_palette_{i}" d="M {700 + 10 * i} 300 L {704 + 10 * i} 300 L {704 + 10 * i} 304 Z" '
               f'fill="{c}" stroke="{c}" stroke-width="2"/>' for i, c in enumerate(PALETTE)]
        return "\n".join(head + pal + self.out + ["</svg>", ""])


# ------------------------------------------------------------------ geometry
def gx(k):
    return k * P


def run(k, side, ratio, y_from, y_to, n=None, clip=True):
    """Screen points along turn k's lit lip (side 'lip') or floor ('floor'), from y_from to y_to."""
    n = n or 40
    pts = []
    for i in range(n):
        y = y_from + (y_to - y_from) * i / (n - 1)
        t = (y - Y0) / (Y1 - Y0)
        x = gx(k) + lateral(k, t, ratio)
        if side == "lip":
            q = CAM((x - HW, y, 0.0))
        elif side == "mid":
            q = CAM((x - HW / 2, y, -DEPTH / 2))
        else:
            q = CAM((x, y, -DEPTH))
        if clip and not in_field(q):
            break
        pts.append(q)
    return pts


def section_piece(k_from, k_to, x_start=None):
    """The cut face's lit top edge: from turn k_from's shadow lip (or x_start) to turn k_to's notch."""
    pts = []
    if x_start is not None:
        pts.append(CAM((x_start, Y0, 0.0)))
    else:
        pts.append(CAM((gx(k_from) + HW, Y0, 0.0)))
    c = gx(k_to)
    pts += [CAM((c - HW, Y0, 0.0)), CAM((c - 0.003, Y0, -DEPTH)), CAM((c + 0.003, Y0, -DEPTH)),
            CAM((c + HW, Y0, 0.0))]
    return pts


def field_x(y_screen):
    """Right edge of the field stop on a screen row."""
    cx, cy, r = FIELD
    return cx + math.sqrt(max(0.0, r * r - (y_screen - cy) ** 2))


def world_x_at(screen_x, z):
    lo, hi = -2.0, 4.0
    for _ in range(60):
        m = (lo + hi) / 2
        if CAM((m, Y0, z))[0] < screen_x:
            lo = m
        else:
            hi = m
    return lo


def rim_x(n):
    return gx(n) + 0.62 * P


def rim_parts(n):
    """Just outside turn n: the land out to the rim and the rim's lit edge receding, then the coat
    falling away over the edge. At MAX_TURNS there's no rim in the field: the land runs to the stop."""
    if n >= MAX_TURNS:
        xe = world_x_at(field_x(Y_NEAR_SCREEN) - 4, 0.0)
        return [CAM((gx(n) + HW, Y0, 0.0)), CAM((xe, Y0, 0.0))], None
    xr = rim_x(n)
    edge = [CAM((gx(n) + HW, Y0, 0.0))]
    for i in range(30):
        y = Y0 + (Y1 - Y0) * i / 29
        q = CAM((xr, y, 0.0))
        if not in_field(q):
            break
        edge.append(q)
    fall = [CAM((xr + 0.03 * (1 - math.cos(t)), Y0, -0.04 * math.sin(t)))
            for t in [math.pi / 2 * i / 8 for i in range(9)]]
    fall += [CAM((xr + 0.03, Y0, -0.04 - (COAT - 0.04) * i / 3)) for i in range(1, 4)]
    return edge, fall


def runs(pts, cuts):
    """Split a line at screen rows (descending) into near-to-far runs that share their joints."""
    out, cur = [], []
    edges = list(cuts)
    for p in pts:
        while edges and p[1] < edges[0]:
            if cur:
                out.append(cur)
                cur = [cur[-1]]
            else:
                out.append([])
            edges.pop(0)
        cur.append(p)
    out.append(cur)
    while len(out) < len(cuts) + 1:
        out.append([])
    return [r if len(r) >= 2 else [] for r in out]


def turn_parts(k):
    """An earlier turn, cut at 1.00: its notch in the cut face, its lit wall as a dark body that the
    depth of field dissolves halfway up, then its lip (three runs, dimming) and floor (two runs)."""
    lip = run(k, "lip", 1.0, Y0, Y1 + 0.5, n=48)
    floor = run(k, "floor", 1.0, Y0, Y_WALL, n=32)
    l1, l2, l3 = runs(lip, (SPLIT_SCREEN, FAR_SCREEN))
    f1, f2 = runs(floor, (SPLIT_SCREEN,))
    return [("fill", wall_body(k, 1.0), G6), ("line", section_piece(k - 1, k), LINE, G3),
            ("line", l1, LINE, G3), ("line", l2, LINE, G4), ("line", l3, HAIR, G5),
            ("line", f1, HAIR, G4), ("line", f2, HAIR, G5)]


def wall_body(k, ratio, n=24, clip=True):
    """The lit wall between lip and floor as one closed outline (lip near->far, floor far->near),
    cut off where either edge leaves the field stop."""
    lip = run(k, "lip", ratio, Y0, Y_WALL, n=n, clip=False)
    floor = run(k, "floor", ratio, Y0, Y_WALL, n=n, clip=False)
    if clip:
        m = 0
        while m < n and in_field(lip[m]) and in_field(floor[m]):
            m += 1
        lip, floor = lip[:m], floor[:m]
    return lip + floor[::-1]


def draw_part(F, part, node=None, shown=True):
    if part[0] == "fill":
        F.blob(part[1], part[2], node=node, shown=shown)
    else:
        F.ribbon(part[1], part[2], part[3], node=node, shown=shown)


# wear: specks (bright grains) and scratches on the lands between earlier turns, placed once in the
# world and kept 3 px clear of every groove edge; bigger marks come first so the first half of the
# knob already reads
def _land_x(k, y, t_from_lip):
    """Screen x across land k (between turn k's dark wall and turn k+1's lit lip) at world depth y."""
    t = (y - Y0) / (Y1 - Y0)
    left = gx(k) + lateral(k, t, 1.0) + HW
    right = (gx(k + 1) + lateral(k + 1, t, 1.0) - HW) if k < DEFAULT_TURNS else rim_x(k)
    return CAM((left + (right - left) * t_from_lip, y, 0.0))


def _clear(pts, k, margin=3.2):
    """Every point at least `margin` px inside land k on its own screen row."""
    for x, y in pts:
        lo, hi = Y0, Y1
        for _ in range(40):
            m = (lo + hi) / 2
            if CAM((0, m, 0))[1] > y:
                lo = m
            else:
                hi = m
        left = _land_x(k, lo, 0.0)[0]
        right = _land_x(k, lo, 1.0)[0]
        if not (left + margin <= x <= right - margin) or y < WALL_SCREEN:
            return False
    return True


def _row_y(screen_y):
    lo, hi = Y0, Y1
    for _ in range(40):
        m = (lo + hi) / 2
        if CAM((0, m, 0))[1] > screen_y:
            lo = m
        else:
            hi = m
    return lo


def _scratch_ok(pts):
    """A scratch may cross earlier turns, but stays off the newest groove's land and inside the cut area."""
    for x, y in pts:
        if y < WALL_SCREEN + 4 or y > Y_NEAR_SCREEN - 8:
            return False
        yw = _row_y(y)
        t = (yw - Y0) / (Y1 - Y0)
        x_min = CAM((gx(1) + lateral(1, t, 1.0) - HW - 0.012, yw, 0.0))[0]
        x_max = CAM((rim_x(DEFAULT_TURNS) - 0.012, yw, 0.0))[0]
        if not (x_min <= x <= x_max):
            return False
    return True


def _skates():
    """Long scratches where a stylus skated across the earlier turns, all running one way."""
    out = []
    for i, (cy, ang, L) in enumerate(((84, 27, 128), (112, 31, 118), (138, 24, 124), (98, 34, 96))):
        for dx in [0.5 * j for j in range(0, 80)]:
            for sgn in (1, -1):
                cx = 268 + sgn * dx
                pts = scratch(cx, cy, ang, L, 3 * i + 1)
                if _scratch_ok(pts):
                    out.append(("scratch", cx, cy, pts))
                    break
            else:
                continue
            break
    return out


def _wear_items():
    import random
    rng = random.Random(3)
    skates = _skates()
    items = []
    plan = (["speck", "speck", "scratch"] * 8)[:22]
    for n, kind in enumerate(plan):
        for _ in range(4000):
            k = (1, 2, 3)[(n + rng.randrange(3)) % 3]
            y = Y0 + 0.02 + (Y1 - Y0) * rng.uniform(0.02, 0.66)
            cx, cy = _land_x(k, y, rng.uniform(0.25, 0.75))
            if kind == "speck":
                pts = speck(cx, cy, n)
            else:
                pts = scratch(cx, cy, rng.uniform(55, 80) * rng.choice([-1, 1]), rng.uniform(11, 17), n)
            if not _clear(pts, k):
                continue
            if any(math.dist((cx, cy), (o[1], o[2])) < 11 for o in items):
                continue
            if any(min(math.dist(p, q) for q in o[3]) < 5 for o in skates for p in pts):
                continue
            items.append((kind, cx, cy, pts))
            break
    # skates first, then the small marks, interleaved so each half of the knob does its share
    order = []
    for i in range(max(len(skates), len(items))):
        if i < len(skates):
            order.append(skates[i])
        order += items[i * 5:(i + 1) * 5] if i < len(skates) else []
    order += items[len(skates) * 5:]
    return order


def speck(cx, cy, seed):
    r = 3.0 + 0.4 * (seed % 3)
    pts = []
    for i in range(7):
        a = 2 * math.pi * i / 7 + seed
        rr = r * (0.8 + 0.22 * math.sin(3 * a + seed))
        pts.append((cx + rr * math.cos(a), cy + 0.85 * rr * math.sin(a)))
    return pts


def scratch(cx, cy, ang, L, seed):
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    n = max(9, min(30, int(L / 5)))
    return [(cx + ux * L * (i / (n - 1) - 0.5) - uy * 0.8 * math.sin(i * 0.7 + seed),
             cy + uy * L * (i / (n - 1) - 0.5) + ux * 0.8 * math.sin(i * 0.7 + seed)) for i in range(n)]


def _emit_wall(F, wall):
    """Node 1: the newest groove's lit wall, a dark body whose floor edge is its hairline outline."""
    xs = [p[0] for p in wall]
    ys = [p[1] for p in wall]
    origin = (round((min(xs) + max(xs)) / 2, 1), round((min(ys) + max(ys)) / 2, 1))
    F._emit(wall, G6, stroke=G3, sw=HAIR, node=1, origin=origin, exact=2 * NPTS)


WEAR = _wear_items()


# ------------------------------------------------------------------ the frame
def build(cut=1 / 3, groove=0.0, wear=0.0, rumble=0.0) -> Frame:
    a = amounts(cut, groove, wear, rumble)
    F = Frame(a["values"])
    ratio, turns = a["ratio"], a["turns"]

    # --- static: uncut lacquer edge, newest notch, and earlier turns 1..3 with their notches
    F.ribbon([CAM((-0.42, Y0, 0.0)), CAM((-0.3, Y0, 0.0))], HAIR, G5)
    F.ribbon([CAM((-0.3, Y0, 0.0)), CAM((-HW, Y0, 0.0)), CAM((-0.003, Y0, -DEPTH)),
              CAM((0.003, Y0, -DEPTH)), CAM((HW, Y0, 0.0))], LINE, G3)
    for k in range(1, DEFAULT_TURNS + 1):
        for part in turn_parts(k):
            draw_part(F, part)

    node = 4
    # --- groove: turns 4..7 appear as the cutter is further in (5 nodes each)
    for k in range(DEFAULT_TURNS + 1, MAX_TURNS + 1):
        shown = k <= turns
        for part in turn_parts(k):
            if len(part[1]) >= 2:
                draw_part(F, part, node=node, shown=shown)
                node += 1
    # --- groove: the rim just outside the last turn, or the open field at the last (2 nodes per position)
    for n in range(DEFAULT_TURNS, MAX_TURNS + 1):
        shown = n == turns
        edge, fall = rim_parts(n)
        F.ribbon(edge, LINE, G4 if n < MAX_TURNS else G3, node=node, shown=shown)
        if fall:
            F.ribbon(fall, LINE, G4, node=node + 1, shown=shown)
            node += 2
        else:
            node += 1

    # --- wear: specks and scratches on the lands (one node each)
    n_wear = int(math.floor(a["wear"] * len(WEAR) + 0.5))
    for i, (kind, cx, cy, pts) in enumerate(WEAR):
        shown = i < n_wear
        if kind == "speck":
            F.blob(pts, G2, node=node, shown=shown)
        else:
            F.ribbon(pts, HAIR, G3, node=node, shown=shown)
        node += 1
    F.nodes = node

    # --- the newest groove: rumble ghosts (nodes 2, 3) under its lit wall (node 1), lit lip (node 0) on top
    lip = run(0, "lip", ratio, Y0, Y1, n=NPTS, clip=False)
    shake = 13.0 * a["rumble"] ** 0.6
    lip_out = ribbon_outline(lip, SUBJ)
    xs = [p[0] for p in lip_out]
    ys = [p[1] for p in lip_out]
    lip_origin = (round((min(xs) + max(xs)) / 2, 1), round((min(ys) + max(ys)) / 2, 1))
    for nd, s, c in ((2, -2, G4), (3, -1, G3)):
        ghost_shown = a["rumble"] > 0
        org = (lip_origin[0] + s * shake, lip_origin[1])
        F.ribbon([(x + s * shake, y) for x, y in lip], 2.5, c, node=nd, origin=org, shown=ghost_shown,
                 exact=2 * NPTS)
    _emit_wall(F, wall_body(0, ratio, n=NPTS, clip=False))
    F.ribbon(lip, SUBJ, G0, node=0, origin=lip_origin, exact=2 * NPTS)
    return F


# ------------------------------------------------------------------ output
DEFAULTS = {"cut": 1 / 3, "groove": 0.0, "wear": 0.0, "rumble": 0.0}
CONTROLS = ["cut", "groove", "wear", "rumble"]


def render_png(svg: Path, png: Path):
    subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H), "-b", "#000000", "-o", str(png), str(svg)],
                   check=True)


def write(name, **kw):
    params = dict(DEFAULTS)
    params.update(kw)
    fr = build(**params)
    svg = HERE / f"{name}.svg"
    svg.write_text(fr.svg())
    render_png(svg, HERE / f"{name}.png")
    return svg


def frames():
    out = [write("rest")]
    for c in CONTROLS:
        for v in (0, 50, 100):
            out.append(write(f"{c}-{v}", **{c: v / 100}))
    return out


def sheets():
    from PIL import Image, ImageDraw

    def label(img, text, xy):
        ImageDraw.Draw(img).text(xy, text, fill=(200, 200, 200))

    pad, cap = 12, 16
    bg = (38, 38, 38)
    # before / after at 1:1
    old = Image.open(ROOT / "screens/lathe/passes/02-subject/v3/rest.png").convert("RGB")
    new = Image.open(HERE / "rest.png").convert("RGB")
    sheet = Image.new("RGB", (2 * W + 3 * pad, H + cap + 2 * pad), bg)
    sheet.paste(old, (pad, pad + cap))
    sheet.paste(new, (2 * pad + W, pad + cap))
    label(sheet, "before: pass 02 v3", (pad, pad))
    label(sheet, "after: cleaned rest", (2 * pad + W, pad))
    sheet.save(HERE / "before-after.png")
    # contact: rest, then each control's 0 / 50 / 100, all at 1:1
    cells = [("rest", "rest")] + [(f"{c}-{v}", f"{c} {v}") for c in CONTROLS for v in (0, 50, 100)]
    cols = 3
    rows = [cells[:1]] + [cells[1 + 3 * i:4 + 3 * i] for i in range(4)]
    sheet = Image.new("RGB", (cols * W + (cols + 1) * pad, len(rows) * (H + cap + pad) + pad), bg)
    for r, row in enumerate(rows):
        for c, (stem, text) in enumerate(row):
            x = pad + c * (W + pad)
            y = pad + r * (H + cap + pad)
            label(sheet, text, (x, y))
            sheet.paste(Image.open(HERE / f"{stem}.png").convert("RGB"), (x, y + cap))
    sheet.save(HERE / "contact.png")
    # sweep: each control turned slowly 0 -> 100 in turn, then back to its default, at 1:1
    with tempfile.TemporaryDirectory(dir=HERE) as tmp:
        tmpd = Path(tmp)
        imgs, durs = [], []

        def shot(dur, **kw):
            params = dict(DEFAULTS)
            params.update(kw)
            s = tmpd / f"s{len(imgs):04d}.svg"
            s.write_text(build(**params).svg())
            p = s.with_suffix(".png")
            render_png(s, p)
            imgs.append(Image.open(p).convert("RGB"))
            durs.append(dur)

        shot(1200)
        for c in CONTROLS:
            steps = 40
            for i in range(steps + 1):
                shot(1000 if i == steps else 60, **{c: i / steps})
            shot(900)   # back at the default
        frames_p = [im.convert("P", palette=Image.ADAPTIVE, colors=32) for im in imgs]
        frames_p[0].save(HERE / "sweep.gif", save_all=True, append_images=frames_p[1:], duration=durs,
                         loop=0, optimize=False, disposal=1)


if __name__ == "__main__":
    if not shutil.which("rsvg-convert"):
        sys.exit("needs rsvg-convert")
    for p in frames():
        print(p.relative_to(ROOT))
    if "--sheets" in sys.argv:
        sheets()
        print("before-after.png, contact.png, sweep.gif")
