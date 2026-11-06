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
P = 0.165                       # groove pitch (world)
HW = 0.028                      # groove half-width at the surface
DEPTH = 0.028                   # 90 degree stylus: depth = half-width
CENTRE_X = 120                  # principal point: the newest groove stands upright here
Y_NEAR_SCREEN, Y_FAR_SCREEN = 166.0, 40.0
FIELD = (250.0, 236.0, 236.0)   # field stop: centre x, centre y, radius (screen)
TOP = 34.0                      # nothing above this (header clearance)
SPLIT_SCREEN = 104.0            # depth of field: brighter runs below, dimmer above
OLD_AMP = 0.016                 # earlier turns: swing as cut at 1.00
DEFAULT_TURNS, MAX_TURNS = 3, 7


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


_ang = math.radians(50)
CAM = Camera((0.0, 0.0, 2.0), (0.0, 2.0 / math.tan(_ang), 0.0), 700, (CENTRE_X, 104))


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
Y_SPLIT = _y_for_screen(SPLIT_SCREEN)


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
        s = (0.66 * math.sin(2 * math.pi * 3.5 * t) + 0.24 * math.sin(2 * math.pi * 7.0 * t)
             + 0.10 * math.sin(2 * math.pi * 10.5 * t))
        return s / 0.95
    f1 = 2.6 + 0.37 * k
    return (0.7 * math.sin(2 * math.pi * f1 * t) + 0.3 * math.sin(2 * math.pi * (2.3 * f1) * t + 0.0)) / 0.95


def swing(t, ratio):
    """The cutter: gain into a soft limit. Amplitude grows with the ratio and the crests flatten."""
    amax = 0.068
    return amax * math.tanh(0.42 * ratio * signal(t, 0)) / 1.0


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
        q = CAM((x - HW, y, 0.0)) if side == "lip" else CAM((x, y, -DEPTH))
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


def rim_parts(n):
    """The rim bevel just outside turn n: the land out to it, its lit top edge receding, the fall."""
    xr = gx(n) + 0.62 * P
    land = [CAM((gx(n) + HW, Y0, 0.0)), CAM((xr, Y0, 0.0))]
    edge = []
    for i in range(30):
        y = Y0 + (Y1 - Y0) * i / 29
        q = CAM((xr, y, 0.0))
        if not in_field(q):
            break
        edge.append(q)
    fall = [CAM((xr + 0.03 * (1 - math.cos(a)), Y0, -0.05 * math.sin(a)))
            for a in [math.pi / 2 * i / 8 for i in range(9)]]
    fall += [CAM((xr + 0.03, Y0, -0.05 - 0.05 * i / 4)) for i in range(1, 5)]
    foot = []
    for i in range(30):
        y = Y0 + (Y1 - Y0) * i / 29
        q = CAM((xr + 0.03, y, -0.05))
        if not in_field(q) or q[1] < Y_FAR_SCREEN + 30:
            break
        foot.append(q)
    return land + edge[1:], fall, foot


def split(pts):
    near = [p for p in pts if p[1] >= SPLIT_SCREEN]
    far = [p for p in pts if p[1] <= SPLIT_SCREEN + 0.01]
    if near and far:
        far = [near[-1]] + far
    return near, far


# wear: specks (bright grains) and short scratches across the lands between earlier turns
def _wear_items():
    items = []
    # (land index k = between turn k and k+1, across 0..1, depth 0..1, kind, angle)
    spec = [
        (1, 0.55, 0.18, "speck", 0), (2, 0.40, 0.55, "scratch", 35), (3, 0.45, 0.30, "speck", 0),
        (1, 0.35, 0.70, "speck", 0), (2, 0.60, 0.12, "speck", 0), (1, 0.50, 0.44, "scratch", -40),
        (3, 0.50, 0.68, "speck", 0), (2, 0.45, 0.82, "speck", 0), (3, 0.40, 0.08, "scratch", 50),
        (1, 0.60, 0.92, "speck", 0), (2, 0.55, 0.36, "speck", 0), (3, 0.55, 0.50, "scratch", -30),
        (1, 0.45, 0.06, "speck", 0), (2, 0.35, 0.68, "scratch", -55), (3, 0.45, 0.88, "speck", 0),
        (1, 0.40, 0.58, "speck", 0),
    ]
    for k, a, d, kind, ang in spec:
        lo = gx(k) + HW + 0.012
        hi = (gx(k + 1) - HW - 0.012) if k < 3 else gx(3) + 0.62 * P - 0.014
        y = Y0 + 0.04 + (Y1 - Y0 - 0.1) * d
        x = lo + (hi - lo) * a
        cx, cy = CAM((x, y, 0.0))
        items.append((kind, cx, cy, ang))
    return items


WEAR = _wear_items()


def speck(cx, cy, seed):
    r = 1.9 + 0.3 * (seed % 3)
    pts = []
    for i in range(6):
        a = 2 * math.pi * i / 6 + seed
        rr = r * (0.8 + 0.25 * math.sin(3 * a + seed))
        pts.append((cx + rr * math.cos(a), cy + 0.8 * rr * math.sin(a)))
    return pts


def scratch(cx, cy, ang, seed):
    L = 9 + 3 * (seed % 3)
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    return [(cx - ux * L / 2 + 0.6 * uy * math.sin(i), cy - uy * L / 2 + 0.3 * math.cos(i)) if False else
            (cx + ux * L * (i / 4 - 0.5), cy + uy * L * (i / 4 - 0.5) + 0.5 * math.sin(i * 1.3 + seed))
            for i in range(5)]


# ------------------------------------------------------------------ the frame
def build(cut=1 / 3, groove=0.0, wear=0.0, rumble=0.0) -> Frame:
    a = amounts(cut, groove, wear, rumble)
    F = Frame(a["values"])
    ratio, turns = a["ratio"], a["turns"]

    # --- static: uncut lacquer edge, newest notch, and earlier turns 1..3 with their notches
    F.ribbon([CAM((-0.62, Y0, 0.0)), CAM((-0.48, Y0, 0.0))], HAIR, G5)
    F.ribbon([CAM((-0.48, Y0, 0.0)), CAM((-HW, Y0, 0.0)), CAM((-0.003, Y0, -DEPTH)),
              CAM((0.003, Y0, -DEPTH)), CAM((HW, Y0, 0.0))], LINE, G3)
    for k in range(1, DEFAULT_TURNS + 1):
        F.ribbon(section_piece(k - 1, k), LINE, G3)
        ln, lf = split(run(k, "lip", 1.0, Y0, Y1 + 0.5))
        fn, ff = split(run(k, "floor", 1.0, Y0, Y1 + 0.5))
        F.ribbon(ln, LINE, G3)
        F.ribbon(lf, LINE, G4)
        F.ribbon(fn, HAIR, G4)
        F.ribbon(ff, HAIR, G5)

    node = 4
    # --- groove: turns 4..7 appear as the cutter is further in (5 nodes each)
    for k in range(DEFAULT_TURNS + 1, MAX_TURNS + 1):
        shown = k <= turns
        ln, lf = split(run(k, "lip", 1.0, Y0, Y1 + 0.5))
        fn, ff = split(run(k, "floor", 1.0, Y0, Y1 + 0.5))
        F.ribbon(section_piece(k - 1, k), LINE, G3, node=node, shown=shown)
        F.ribbon(ln, LINE, G3, node=node + 1, shown=shown)
        F.ribbon(lf, LINE, G4, node=node + 2, shown=shown)
        F.ribbon(fn, HAIR, G4, node=node + 3, shown=shown)
        F.ribbon(ff, HAIR, G5, node=node + 4, shown=shown)
        node += 5
    # --- groove: the rim bevel just outside the last turn (3 nodes per position; gone at 7)
    for n in range(DEFAULT_TURNS, MAX_TURNS):
        shown = n == turns
        edge, fall, foot = rim_parts(n)
        F.ribbon(edge, LINE, G3, node=node, shown=shown)
        F.ribbon(fall, LINE, G3, node=node + 1, shown=shown)
        F.ribbon(foot, HAIR, G5, node=node + 2, shown=shown)
        node += 3

    # --- wear: specks and scratches on the lands (16 nodes)
    n_wear = int(math.floor(a["wear"] * len(WEAR) + 0.5))
    for i, (kind, cx, cy, ang) in enumerate(WEAR):
        shown = i < n_wear
        if kind == "speck":
            F.blob(speck(cx, cy, i), G2, node=node, shown=shown)
        else:
            F.ribbon(scratch(cx, cy, ang, i), HAIR, G3, node=node, shown=shown)
        node += 1
    F.nodes = node

    # --- the newest groove: floor (node 1), rumble ghosts (nodes 2, 3), lit lip (node 0) on top
    floor = run(0, "floor", ratio, Y0, Y1, n=NPTS, clip=False)
    lip = run(0, "lip", ratio, Y0, Y1, n=NPTS, clip=False)
    F.ribbon(floor, HAIR, G3, node=1, exact=2 * NPTS)
    shake = 12.0 * a["rumble"] ** 0.6
    lip_out = ribbon_outline(lip, SUBJ)
    xs = [p[0] for p in lip_out]
    ys = [p[1] for p in lip_out]
    lip_origin = (round((min(xs) + max(xs)) / 2, 1), round((min(ys) + max(ys)) / 2, 1))
    for nd, s in ((2, -1), (3, 1)):
        ghost_shown = a["rumble"] > 0
        org = (lip_origin[0] + s * shake, lip_origin[1])
        F.ribbon([(x + s * shake, y) for x, y in lip], LINE, G5, node=nd, origin=org, shown=ghost_shown,
                 exact=2 * NPTS)
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
    cols = 4
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
