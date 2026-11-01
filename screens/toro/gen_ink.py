#!/usr/bin/env python3
"""Toro's screen: the owner's one-bit bull, rebuilt for the open-xy display ABI from the photos of the device.

v2. The first build traced the photo by box-averaging it, which turned every 2 px line into a dotted one, and then
redrew the head by hand as a cartoon. Both were wrong. This build takes its art from ink_art.py, which point-samples
the photos at display-pixel centres and rebuilds them pixel-exact (clean 2 px lines, clean dither, the fine checker as
the flat grey it reads as on the panel). Nothing is redrawn by hand: every node's outline is the contour of a cell
of the owner's drawing.

The split is the same as before, for the same reason (only nodes move, and a node is one path of ≤ 64 points, so
dither can only live in still art):

  static artwork   everything that never moves, pixel for pixel from the rest photo: white as run-length <rect>s,
                   the fine-checker grey as <rect>s in #4B4B4B. Includes the face's dot grid
  head nodes       each cell of the head (horns, forehead cap, face, ears, eye patches, muzzle) as its own outline,
                   pushed out 1 px so its 2 px white stroke lands exactly on the drawing's line; eye whites and nostrils
                   as white shapes. Flat-grey cells keep their exact grey; the cap and the left horn are the only two
                   dithered cells that move, so they become flat greys of the same brightness
  steam nodes      the cells of the steam, from the smoke photo, revealed by drive from the nostrils outward
  tail tuft        its cells as nodes, so it can flick
  mutable outlines the burst beside the muzzle (res) and two heat squiggles (fold)

    python3 screens/toro/gen_ink.py            # frames, fragment, board, model.json for the prototype
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation, binary_erosion, binary_fill_holes, label

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen_frames as g  # noqa: E402  (helpers: f, poly, header preview, DEFAULTS, CONTROLS)
import ink_art as A  # noqa: E402

W, H, TOP = 480, 220, 40
OUT = HERE / "ink"
PREFIX = "toro"
PATHS = 3                                                  # mutable outlines: burst, squiggle A, squiggle B
HEADER_FIRST = PATHS
f, poly = g.f, g.poly
WHITE, BLACK = "#FFFFFF", "#000000"
GREY_FINE = "#4B4B4B"                                      # A.G_FINE: the fine checker on the panel

# palette: (fill, stroke, width, paint). paint "stroke" draws the outline only (a hollow cell); "fill" fills and strokes
PALETTE = [(BLACK, WHITE, 2, "stroke"), (GREY_FINE, GREY_FINE, 0.1, "fill"), ("#3A3A3A", "#3A3A3A", 0.1, "fill"), ("#6E6E6E", "#6E6E6E", 0.1, "fill"),
           (WHITE, WHITE, 1, "fill"), ("#262626", "#262626", 0.1, "fill"), ("#8C8C8C", "#8C8C8C", 0.1, "fill"), ("#AFAFAF", "#AFAFAF", 0.1, "fill"),
           (WHITE, WHITE, 1, "fill"), (BLACK, WHITE, 2, "stroke"), (WHITE, WHITE, 0.1, "fill"), (GREY_FINE, GREY_FINE, 0.1, "fill"), ("#7D7D7D", "#7D7D7D", 0.1, "fill"), ("#4B4B4B", WHITE, 2, "fill")]
P_HOLLOW, P_FINE, P_D25, P_D50, P_WHITE, P_DIM, P_LIT1, P_LIT2, P_GRAIN, P_OUTLINE, P_WHITE_EXACT, P_FINE_EXACT, P_ECHO, P_STEAM = range(14)
KIND_PALETTE = {A.DARK: P_HOLLOW, A.FLAT: P_FINE, A.D25: P_D25, A.D50: P_D50}

# ---- where things are, absolute px on the rest photo -------------------------------------------------------------------
PIVOT = (238, 186)                                         # the neck: the head wobbles and lowers about this
HEAD_SEEDS = {"horn_l": (160, 85), "horn_r": (300, 80), "cap": (235, 65), "ear_l": (183, 110), "ear_r": (290, 108),
              "face": (235, 132), "patch_l": (205, 140), "patch_r": (265, 140), "muzzle": (238, 166)}
HORN_ROOTS = {"horn_l": (195, 88), "horn_r": (281, 80)}
NOSTRIL_AT = (238, 165)
TUFT_BOX = (372, 54, 402, 92)
TUFT_ROOT = (382, 92)
BURST_BOX = (136, 134, 166, 166)
GLYPH_BOXES = ((70, 158, 160, 206), (396, 95, 465, 135))  # the two bar glyphs: shape reshapes their envelopes
BURST = (151, 150)
SQUIGGLES = ((140, 102), (345, 96))
PLUMES = ([(38, 76), (132, 74), (162, 100), (162, 157), (229, 159), (229, 182), (150, 178), (88, 166), (34, 132)],
          [(251, 160), (300, 157), (300, 122), (360, 98), (392, 72), (411, 72), (411, 140), (332, 164), (251, 182)])
SPARKLES = [(60, 70), (430, 60), (70, 180), (420, 150), (120, 60), (330, 205), (40, 120), (450, 110)]
GRAIN = [(32, 90), (90, 205), (160, 60), (300, 50), (440, 195), (380, 195), (20, 170), (200, 210), (270, 210), (460, 80), (130, 150), (350, 60)]
SWATCHES = [(90, 46, 126, 74), (88, 104, 124, 136), (350, 58, 388, 92), (362, 122, 394, 162)]


def centroid(pts):
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def rel(pts, o):
    return [(x - o[0], y - o[1]) for x, y in pts]


def ribbon(pts, w):
    n = len(pts)
    a_, b_ = [], []
    for i, (x, y) in enumerate(pts):
        a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        a_.append((x - dy / ln * w / 2, y + dx / ln * w / 2))
        b_.append((x + dy / ln * w / 2, y - dx / ln * w / 2))
    return a_ + b_[::-1]


def star4(r):
    return [(0, -r), (r * 0.3, -r * 0.3), (r, 0), (r * 0.3, r * 0.3), (0, r), (-r * 0.3, r * 0.3), (-r, 0), (-r * 0.3, -r * 0.3)]


def burst_outline(r, rays=8):
    """rays round a hollow centre as one closed outline, each tip squared off (no reversal)"""
    pts, r_in, half = [], max(1.6, r * 0.42), 0.6
    for k in range(rays):
        a = 2 * math.pi * k / rays + math.pi / rays
        c, s = math.cos(a), math.sin(a)
        nx, ny = -s * half, c * half
        pts += [(c * r_in - nx, s * r_in - ny), (c * r - nx, s * r - ny), (c * r + nx, s * r + ny), (c * r_in + nx, s * r_in + ny)]
    return pts


def squiggle_outline(length, amp, turns, w=2.0):
    pts = [(amp * math.sin(t / length * turns * 2 * math.pi), t) for t in np.linspace(0, length, 14)]
    return ribbon(pts, w)


def tiny(r, n=10):
    return [(math.cos(2 * math.pi * k / n) * r, math.sin(2 * math.pi * k / n) * r) for k in range(n)]


# ---- the parts, all cut from the owner's drawing -------------------------------------------------------------------------
class Part:
    def __init__(self, name, pts, palette, group="free", origin=None, order=0):
        self.name, self.palette, self.group, self.order = name, palette, group, order
        self.origin = origin or centroid(pts)
        self.pts = rel(pts, self.origin)
        self.abs = pts


def register(a: np.ndarray, b: np.ndarray, r=5):
    """the (dx, dy) that best lays mask b over mask a"""
    best = (-1, 0, 0)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            sh = np.roll(np.roll(b, dy, 0), dx, 1)
            score = (a & sh).sum()
            if score > best[0]:
                best = (score, dx, dy)
    return best[1], best[2]


def build():
    img, cells, kind, solid = A.load("rest")
    parts, head_mask = [], np.zeros((H, W), bool)

    # mutable outlines first: they are nodes 0..PATHS-1
    parts.append(Part("burst", [(BURST[0] + x, BURST[1] + y) for x, y in burst_outline(3 + 24 * g.DEFAULTS["res"])], P_OUTLINE, "path", BURST))
    for i, (x, y) in enumerate(SQUIGGLES):
        parts.append(Part(f"squiggle_{'ab'[i]}", [(x + px, y + py) for px, py in squiggle_outline(26, 3.5, 1.5)], P_OUTLINE, "path", (x, y)))
    for i in range(8):                                       # the SDK's two-page header bar
        parts.append(Part(f"header_{i}", [(60 * i, 0), (60 * i + 60, 0), (60 * i + 60, 20), (60 * i, 20)], P_HOLLOW, "header", (60 * i, 0)))

    # the head, pixel-exact: its fills and its lines as staircase outlines at whole-pixel coordinates, so at rest it
    # draws exactly like the photo, and a whole-pixel move (the wobble, the drop) keeps it exact
    head_cells = {name: A.cell_at(cells, x, y) for name, (x, y) in HEAD_SEEDS.items()}
    region = {name: binary_dilation(A.region(cells, k), iterations=2) for name, k in head_cells.items()}
    head_mask = np.zeros((H, W), bool)
    for m in region.values():
        head_mask |= m
    core = {name: A.region(cells, k) for name, k in head_cells.items()}
    horn_zone = {}
    for name, ear in (("horn_l", "ear_l"), ("horn_r", "ear_r")):
        others = binary_dilation(core["cap"] | core["face"] | core[ear], iterations=1)
        horn_zone[name] = binary_dilation(core[name], iterations=2) & ~others

    def group_of(piece):
        ys, xs = np.nonzero(piece)
        for name in ("horn_l", "horn_r"):
            if (piece & horn_zone[name]).sum() >= 0.5 * piece.sum():
                return name
        return "head"

    def add(piece, corners, palette, kind_name, order, grp=None):
        grp = grp or group_of(piece)
        order = order + (0 if grp in HORN_ROOTS else 1000 if kind_name != "line" else 2000)
        if grp in HORN_ROOTS:
            origin = HORN_ROOTS[grp]
            p = Part(f"{grp}_{kind_name}_{order}", [(float(x), float(y)) for x, y in corners], palette, "head", origin, order)
            p.horn = grp
        else:
            ox, oy = min(x for x, _ in corners), min(y for _, y in corners)
            p = Part(f"head_{kind_name}_{order}", [(float(x), float(y)) for x, y in corners], palette, "head", (ox, oy), order)
            p.horn = None
        parts.append(p)

    order = 0
    # fills first: the flat cells keep their exact grey; the two dithered cells that move become flat greys; the face
    # is filled black so the horns can slide out from under it
    for name, k in head_cells.items():
        if kind[k] == A.DARK:
            continue
        zl, zr = horn_zone["horn_l"], horn_zone["horn_r"]
        for piece, corners in [pc for zone in (zl, zr, ~(zl | zr)) for pc in A.pieces((cells == k) & zone)]:
            add(piece, corners, {A.FLAT: P_FINE, A.D25: P_D25, A.D50: P_D50}[int(kind[k])], name, order)
            order += 1
    # the eye whites and nostrils, each a single node so cutoff and res can scale them
    sl, n = label(solid)
    specials = np.zeros((H, W), bool)
    for name_, k_name in (("white_l", "patch_l"), ("white_r", "patch_r"), ("nostril_l", "muzzle"), ("nostril_r", "muzzle")):
        holder = A.region(cells, head_cells[k_name])
        cand = [j for j in range(1, n + 1) if ((sl == j) & holder).sum() >= 0.8 * (sl == j).sum() and (sl == j).sum() >= 12]
        cand.sort(key=lambda j: np.where(sl == j)[1].mean())
        j = cand[0] if name_.endswith("_l") else cand[-1]
        m = sl == j
        specials |= m
        corners = A.loops(m)[0]
        parts.append(Part(name_, [(float(x), float(y)) for x, y in corners], P_WHITE_EXACT, "head", None, 3000 + order))
        parts[-1].horn = None
        parts[-1].special = True
        order += 1
    # the lines (and the face's dot grid)
    lines = solid & head_mask & ~specials
    zl, zr = horn_zone["horn_l"], horn_zone["horn_r"]
    for zone in (zl, zr, ~(zl | zr)):
        for piece, corners in A.pieces(lines & zone):
            add(piece, corners, P_WHITE_EXACT, "line", 500 + order)
            order += 1
    # spread: an echo of each horn's line, in a dim grey, drawn behind the horns. At the default it sits exactly
    # under the horn; spread slides the echoes apart, the two oscillators detuning into a double image
    for horn in ("horn_l", "horn_r"):
        body = (A.region(cells, head_cells[horn]) | (lines & horn_zone[horn]))
        for piece, corners in A.pieces(body):
            p = Part(f"echo_{horn}_{order}", [(float(x), float(y)) for x, y in corners], P_ECHO, "head",
                     (min(x for x, _ in corners), min(y for _, y in corners)), -500 + order)
            p.horn = None
            p.echo = horn
            parts.append(p)
            order += 1

    # the tail tuft, pixel-exact too, turning about its root on a note
    x0, y0, x1, y1 = TUFT_BOX
    tuft_mask = np.zeros((H, W), bool)
    tuft_mask[y0:y1, x0:x1] = True
    tuft_px = (img > 0) & tuft_mask
    tuft_fill = np.zeros((H, W), bool)
    for k in np.unique(cells[y0:y1, x0:x1]):
        if k > 1 and kind[k] != A.DARK and (cells == k)[y0:y1, x0:x1].sum() >= 0.9 * (cells == k).sum():
            tuft_fill |= cells == k
    for piece, corners in A.pieces(tuft_fill):            # its dither becomes a flat grey so it can flick
        parts.append(Part(f"tuft_fill_{len(parts)}", [(float(x), float(y)) for x, y in corners], P_D50, "tuft", TUFT_ROOT))
    for piece, corners in A.pieces(solid & tuft_mask):
        parts.append(Part(f"tuft_line_{len(parts)}", [(float(x), float(y)) for x, y in corners], P_WHITE_EXACT, "tuft", TUFT_ROOT))
    tuft_mask = tuft_fill | (solid & tuft_mask)

    # steam: cells of the smoke photo inside the plumes, laid over the rest drawing
    s_img, s_cells, s_kind, s_solid = A.load("smoke")
    dx, dy = register(solid, s_solid)
    plume = np.zeros((H, W), bool)
    for pl in PLUMES:
        im = Image.new("L", (W, H), 0)
        ImageDraw.Draw(im).polygon(pl, fill=255)
        plume |= np.array(im) > 0
    # the steam as the photo draws it: one silhouette per cloud (where the smoke photo is brighter than the black
    # ground), its outline and inner curls in white, its body in the grey the photo's dither reads as
    from scipy.ndimage import binary_closing, binary_opening, gaussian_filter
    raw = np.roll(np.roll(A.sample("smoke"), dy, 0), dx, 1)
    soft = gaussian_filter(raw, 1.0)
    sil = binary_fill_holes(binary_opening(binary_closing((soft > 48) & plume, iterations=1), iterations=1))
    lab_, n_ = label(sil)
    sz = np.bincount(lab_.ravel())
    sil = np.isin(lab_, [k for k in range(1, n_ + 1) if sz[k] >= 80])
    # each cloud is one node: its silhouette, eased, filled grey and stroked with the 2 px white outline. Its inner
    # curls are pixel-exact line pieces on top
    curls = binary_opening(raw > 175, structure=np.ones((2, 2))) & binary_erosion(sil, iterations=3)
    puffs = []
    lab_, n_ = label(sil)
    for k in range(1, n_ + 1):
        comp = lab_ == k
        ys, xs = np.nonzero(comp)
        puffs.append((math.dist((xs.mean(), ys.mean()), NOSTRIL_AT), A.outline(comp, grow=0, smooth=1.0), P_STEAM))
    for piece, corners in A.pieces(curls, min_px=14):
        ys, xs = np.nonzero(piece)
        puffs.append((math.dist((xs.mean(), ys.mean()), NOSTRIL_AT), corners, P_WHITE_EXACT))
    for i, (d, corners, pal) in enumerate(sorted(puffs, key=lambda p: ({P_STEAM: 0}.get(p[2], 1), p[0]))):
        parts.append(Part(f"puff_{i}", [(float(x), float(y)) for x, y in corners], pal, "steam", (round(min(x for x, _ in corners)), round(min(y for _, y in corners)))))
        parts[-1].reach = d

    glyph_mask = np.zeros((H, W), bool)
    for gi, (gx0, gy0, gx1, gy1) in enumerate(GLYPH_BOXES):
        gm = np.zeros((H, W), bool)
        gm[gy0:gy1, gx0:gx1] = img[gy0:gy1, gx0:gx1] == 255
        glyph_mask |= gm
        for piece, corners in sorted(A.pieces(gm), key=lambda pc: np.nonzero(pc[0])[1].mean()):
            ys, xs = np.nonzero(piece)
            p = Part(f"bar_{gi}_{len([q for q in parts if q.group == 'bar'])}", [(float(x), float(y)) for x, y in corners], P_WHITE_EXACT, "bar",
                     ((xs.min() + xs.max() + 1) / 2, (ys.min() + ys.max() + 1) / 2))
            p.height, p.glyph = ys.max() - ys.min() + 1, gi
            parts.append(p)

    for i, (x, y) in enumerate(SPARKLES):
        parts.append(Part(f"sparkle_{i}", [(x + px, y + py) for px, py in star4(5)], P_WHITE, "sparkle", (x, y)))
    for i, (x, y) in enumerate(GRAIN):
        parts.append(Part(f"grain_{i}", [(x + px, y + py) for px, py in tiny(1.1, 6)], P_GRAIN, "grain", (x, y)))
    for i, (x0, y0, x1, y1) in enumerate(SWATCHES):
        cy = (y0 + y1) / 2
        parts.append(Part(f"scan_{i}", [(x0 - 6, cy - 1.5), (x1 + 6, cy - 1.5), (x1 + 6, cy + 1.5), (x0 - 6, cy + 1.5)], P_WHITE, "scan"))

    # the still art: the rest drawing minus everything a node now draws
    still = img.copy()
    still[head_mask | tuft_mask | glyph_mask] = 0
    bx0, by0, bx1, by1 = BURST_BOX
    still[by0:by1, bx0:bx1] = 0
    return parts, still, (dx, dy)


PARTS, STILL, SMOKE_SHIFT = build()
INDEX = {p.name: i for i, p in enumerate(PARTS)}
GROUP = lambda name: [i for i, p in enumerate(PARTS) if p.group == name]
MAX_REACH = max(p.reach for p in PARTS if p.group == "steam")


def still_rects(still: np.ndarray):
    """runs of each value per row, merged down while a run repeats exactly: (x, y, w, h, value)"""
    rows = []
    for y in range(H):
        row, runs, x = still[y], [], 0
        while x < W:
            v = int(row[x])
            if v:
                x0 = x
                while x < W and row[x] == v:
                    x += 1
                runs.append((x0, x - x0, v))
            else:
                x += 1
        rows.append(runs)
    out, open_ = [], {}
    for y, runs in enumerate(rows):
        nxt = {}
        for x0, w, v in runs:
            key = (x0, w, v)
            if key in open_:
                nxt[key] = open_[key]
            else:
                nxt[key] = y
        for key, y0 in open_.items():
            if key not in nxt:
                out.append((key[0], y0, key[1], y - y0, key[2]))
        open_ = nxt
    for key, y0 in open_.items():
        out.append((key[0], y0, key[1], H - y0, key[2]))
    return out


RECTS = still_rects(STILL)


# ---- posing ----------------------------------------------------------------------------------------------------------
def kink(a):
    return 0.4 * a + 0.6 * a ** 3


def note(t):
    if t is None:
        return dict(wobble=0.0, flash=0.0, flare=0.0)
    env = math.exp(-t / 0.5)
    return dict(wobble=3.0 * math.sin(2 * math.pi * 2.2 * t) * env, flash=1.0 if t < 0.15 else 0.0, flare=0.12 * math.exp(-t / 0.6))


def rot(pts, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [(x * c - y * s, x * s + y * c) for x, y in pts]


class Pose:
    def __init__(self, x, y, palette):
        self.x, self.y, self.scale, self.turn, self.palette, self.visible, self.pts = x, y, 1.0, 0.0, palette, True, None


def pose(v: dict, t=None, key: int = 0) -> list[Pose]:
    D = g.DEFAULTS
    n = note(t)
    out = [Pose(p.origin[0], p.origin[1], p.palette) for p in PARTS]
    cut, res, fold = v["cutoff"], v["res"], v["fold"]

    # the head moves by whole pixels only, so it stays pixel-exact: a note jolts it side to side, fold drops it
    ox = int(round(n["wobble"]))
    oy = int(round(6 * fold + (1 if n["flash"] else 0)))
    for i in GROUP("head"):
        out[i].x += ox
        out[i].y += oy
    # spread slides the horns' echoes apart by whole pixels (the horns themselves never move off the drawing);
    # aphx nudges the right echo a pixel or two per key
    sp = v["spread"]
    apart = round(14 * (sp - D["spread"]) / (1 - D["spread"])) if sp >= D["spread"] else 0
    nudge = round(kink(v["aphx"]) * 3 * ((((key * 7919) % 11) / 10) - 0.5) * 2)
    for i in GROUP("head"):
        echo = getattr(PARTS[i], "echo", None)
        if echo == "horn_l":
            out[i].x -= apart
            out[i].y -= apart // 2
        elif echo == "horn_r":
            out[i].x += apart + nudge
            out[i].y -= apart // 2
    # cutoff: the light on the head. The cap, horn and ears go dark toward 0 and light up toward 100; the eyes
    # narrow toward 0 and open wide toward 100
    lift = (cut - D["cutoff"]) / (1 - D["cutoff"]) if cut > D["cutoff"] else 0.0
    dim = (D["cutoff"] - cut) / D["cutoff"] if cut < D["cutoff"] else 0.0
    for i in GROUP("head"):
        nm = PARTS[i].name
        if nm.startswith("head_cap_"):
            out[i].palette = P_DIM if dim > 0.5 else P_D25 if lift < 0.5 else P_LIT1
        elif nm.startswith("horn_l_horn_l_"):
            out[i].palette = P_DIM if dim > 0.5 else P_D50 if lift < 0.5 else P_LIT2
        elif nm.startswith("head_ear_") or nm.startswith("head_patch_"):
            out[i].palette = P_DIM if dim > 0.6 else P_FINE if lift < 0.5 else P_LIT1
    for side in "lr":
        out[INDEX[f"white_{side}"]].scale = max(0.25, 1 - 0.75 * dim) * (1 + 0.55 * max(lift, n["flash"]))
    # res: the muzzle flushes and the nostrils flare; the burst grows
    for i in GROUP("head"):
        if PARTS[i].name.startswith("head_muzzle_"):
            out[i].palette = P_FINE if res < 0.6 else P_LIT2
    flare = 1 + 0.55 * (res - D["res"]) / (1 - D["res"]) if res >= D["res"] else 1 - 0.35 * (D["res"] - res) / D["res"]
    for side in "lr":
        out[INDEX[f"nostril_{side}"]].scale = flare
    out[INDEX["burst"]].pts = burst_outline(3 + 24 * res, rays=8 if res > 0.4 else 6)
    # shape: the bar glyph's envelope morphs from the photo's two spikes (a saw's edges) to one broad triangle
    for gi in range(len(GLYPH_BOXES)):
        bars = [i for i in GROUP("bar") if PARTS[i].glyph == gi]
        xs = [PARTS[i].origin[0] for i in bars]
        cx, half = (min(xs) + max(xs)) / 2, (max(xs) - min(xs)) / 2
        tallest = max(PARTS[i].height for i in bars)
        for i in bars:
            h0 = PARTS[i].height
            tri = max(2.0, tallest * (1 - abs(PARTS[i].origin[0] - cx) / (half + 4)))
            out[i].scale = min(2.0, max(0.4, 1 + (tri / h0 - 1) * v["shape"]))

    # fold: heat squiggles appear and tighten
    for nm, k_ in (("squiggle_a", 0.3), ("squiggle_b", 0.65)):
        out[INDEX[nm]].visible = fold >= k_
        out[INDEX[nm]].pts = squiggle_outline(26, 3.5, 1.5 + 1.5 * fold)
    # drive: the steam reaches further from the nostrils; a note flares it a step
    reach = min(1.0, v["drive"] + n["flare"]) if v["drive"] > 0.02 else 0.0   # no steam at all without drive
    for i in GROUP("steam"):
        out[i].visible = PARTS[i].reach <= 6 + reach ** 0.6 * (MAX_REACH - 6) and reach > 0
    # noise: sparkles and grain
    ns = round(len(SPARKLES) * v["noise"])
    for j, i in enumerate(GROUP("sparkle")):
        out[i].visible = j < ns
        out[i].scale = 0.6 + 0.9 * v["noise"]
    ng = round(len(GRAIN) * v["noise"])
    for j, i in enumerate(GROUP("grain")):
        out[i].visible = j < ng
    # aphx: torn scanlines slip across the swatches, per key
    slip = kink(v["aphx"])
    for j, i in enumerate(GROUP("scan")):
        out[i].visible = slip > 0.05
        out[i].x += slip * 14 * (((((key + j) * 7919) % 11) / 10) - 0.5) * 2
    # a note: the tuft flicks against the wobble
    for i in GROUP("tuft"):
        out[i].turn = -n["wobble"] * 4
    return out


# ---- rendering -------------------------------------------------------------------------------------------------------
def node_svg(i: int, p: Part, q: Pose, fragment: bool) -> str:
    fill, stroke, width, paint = PALETTE[q.palette]
    if i < PATHS or paint == "stroke":
        fill = "none"
    x, y = (640, 320) if (not q.visible and not fragment) else (q.x, q.y)
    pts = q.pts if (q.pts is not None and not fragment) else p.pts
    if not fragment:
        pts = rot([(px * q.scale, py * q.scale) for px, py in pts], q.turn)
    if fragment and fill == "none" and i >= PATHS:
        fill = BLACK                                       # the authored element carries its palette's fill; paint decides
    return f'<path id="{PREFIX}_node_{i}" transform="matrix(1 0 0 1 {f(x)} {f(y)})" d="{poly(pts)}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round"/>'


def body_svg(v, t=None, key=0, fragment=False) -> list[str]:
    poses = pose(v, t, key)
    o = []
    if fragment:
        o.append('<!-- SDK two-page header: keep this block before machine artwork below y=38. -->')
        o.append('<path d="M0,0 L480,0 L480,38 L0,38 Z" fill="#000000" stroke="none"/>')
        for i in range(8):
            o.append(f'<path id="{PREFIX}_node_{HEADER_FIRST + i}" transform="matrix(1 0 0 1 {60 * i} 0)" d="M0,0 L60,0 L60,20 L0,20 Z" fill="{g.G[i]}" stroke="{g.G[i]}" stroke-width="0.5"/>')
        for k in range(4):
            o.append(f'<text id="{PREFIX}_text_{k}" transform="matrix(1 0 0 1 {5 + 120 * k} 10)" fill="{"#CBCBCB" if k < 2 else "#000000"}" font-family="UniversNextPro-Light" font-size="10px">-</text>')
        for k in range(4):
            o.append(f'<text id="{PREFIX}_text_{4 + k}" transform="matrix(1 0 0 1 {65 + 120 * k} 17.4)" fill="{"#CBCBCB" if k < 2 else "#000000"}" font-family="UniversNextPro-Light" font-size="20px">-</text>')
        for k in range(4):
            o.append(f'<text id="{PREFIX}_text_{8 + k}" transform="matrix(1 0 0 1 {5 + 120 * k} 33)" fill="#5A5A5A" font-family="UniversNextPro-Light" font-size="10px">-</text>')
        for k in range(4):
            o.append(f'<text id="{PREFIX}_text_{12 + k}" transform="matrix(1 0 0 1 {65 + 120 * k} 33)" fill="#707070" font-family="UniversNextPro-Light" font-size="13px">-</text>')
    o.append(f'<g id="{PREFIX}_static">')
    for x, y, w, h, val in RECTS:
        col = WHITE if val == 255 else GREY_FINE
        o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{col}" stroke="none"/>')
    o.append("</g>")
    head = sorted(GROUP("head"), key=lambda i: PARTS[i].order)
    order = GROUP("steam") + head + GROUP("tuft") + GROUP("bar") + GROUP("sparkle") + GROUP("grain") + GROUP("scan") + list(range(PATHS))
    for i in order:
        o.append(node_svg(i, PARTS[i], poses[i], fragment))
    if fragment:
        for i, (fill, stroke, width, _) in enumerate(PALETTE):
            o.append(f'<path id="{PREFIX}_palette_{i}" transform="matrix(1 0 0 1 640 320)" d="M0,0 L4,0 L4,4 L0,4 Z" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')
    return o


def frame_svg(v, t=None, key=0) -> str:
    return "\n".join(['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
                      '<rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>'] + body_svg(v, t, key) + g.header(v) + ["</svg>"])


def fragment_svg() -> str:
    return "\n".join([f'<g id="{PREFIX}_panel">'] + body_svg(dict(g.DEFAULTS), None, 0, fragment=True) + ["</g>"])


def export_model() -> dict:
    parts_ = [{"i": i, "name": p.name, "origin": [float(c) for c in p.origin], "pts": [[float(x), float(y)] for x, y in p.pts],
               "palette": p.palette, "group": p.group, "order": p.order, "reach": getattr(p, "reach", None),
               "horn": getattr(p, "horn", None), "echo": getattr(p, "echo", None), "glyph": getattr(p, "glyph", None),
               "height": int(p.height) if hasattr(p, "height") else None} for i, p in enumerate(PARTS)]
    head = sorted(GROUP("head"), key=lambda i: PARTS[i].order)
    draw_order = GROUP("steam") + head + GROUP("tuft") + GROUP("bar") + GROUP("sparkle") + GROUP("grain") + GROUP("scan") + list(range(PATHS))
    return {"static": [[int(c) for c in r] for r in RECTS], "parts": parts_, "order": draw_order, "glyphs": len(GLYPH_BOXES),
            "sparkles": len(SPARKLES), "grain": len(GRAIN), "index": {k: INDEX[k] for k in ("burst", "squiggle_a", "squiggle_b", "white_l", "white_r", "nostril_l", "nostril_r")}, "palette": PALETTE, "paths": PATHS, "pivot": PIVOT, "maxReach": MAX_REACH,
            "defaults": g.DEFAULTS, "controls": g.CONTROLS, "greys": g.G, "greyFine": GREY_FINE}


def board(names, out):
    import subprocess
    import tempfile
    cols, P_ = 4, 8
    rows = math.ceil(len(names) / cols)
    sheet = Image.new("RGB", (P_ + cols * (W + P_), P_ + rows * (H + 18 + P_)), (40, 40, 40))
    d = ImageDraw.Draw(sheet)
    with tempfile.TemporaryDirectory() as tmp:
        for k, name in enumerate(names):
            png = Path(tmp) / f"{name}.png"
            subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(OUT / "frames" / f"{name}.svg"), "-o", str(png)], check=True)
            x, y = P_ + (k % cols) * (W + P_), P_ + (k // cols) * (H + 18 + P_)
            label_ = name if not name.startswith("c") else f"{g.CONTROLS[int(name[1]) - 1]} {int(name[-3:])}"
            d.text((x, y), label_, fill=(200, 200, 200))
            sheet.paste(Image.open(png).convert("RGB"), (x, y + 18))
    sheet.save(out)


def main():
    (OUT / "frames").mkdir(parents=True, exist_ok=True)
    D = dict(g.DEFAULTS)
    frames = {"rest": (D, None), "playing": (D, 0.05), "note-0.25s": (D, 0.25), "note-0.6s": (D, 0.6)}
    for i, name in enumerate(g.CONTROLS):
        for val in (0, 50, 100):
            frames[f"c{i + 1}-{val:03d}"] = (dict(D, **{name: val / 100}), None)
    for name, (vals, t) in frames.items():
        (OUT / "frames" / f"{name}.svg").write_text(frame_svg(vals, t), encoding="utf-8")
    (OUT / "panel.svg.fragment").write_text(fragment_svg(), encoding="utf-8")
    (OUT / "panel-lint.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">\n' + fragment_svg() + "\n</svg>", encoding="utf-8")
    for old in ("panel-cell2.svg.fragment", "debug.png"):
        (OUT / old).unlink(missing_ok=True)
    info = {"nodes": len(PARTS), "paths": PATHS, "points": 64, "texts": 16, "palette": len(PALETTE), "staticRects": len(RECTS),
            "headNodes": len(GROUP("head")), "steamNodes": len(GROUP("steam")), "tuftNodes": len(GROUP("tuft")),
            "maxPoints": max(len(p.pts) for p in PARTS), "smokeShift": [int(c) for c in SMOKE_SHIFT], "controls": g.CONTROLS}
    (OUT / "budget.json").write_text(json.dumps(info, indent=2))
    (OUT / "model.json").write_text(json.dumps(export_model()))
    print(json.dumps(info))
    board(["rest", "playing", "note-0.25s", "note-0.6s"] + [f"c{i + 1}-{v:03d}" for i in range(8) for v in (0, 50, 100)], OUT / "board.png")


if __name__ == "__main__":
    main()
