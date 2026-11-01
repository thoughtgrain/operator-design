#!/usr/bin/env python3
"""Toro's screen: the owner's one-bit bull, built for the open-xy display ABI.

Why it's split the way it is. On the device only nodes change at runtime, and a node is one path or circle of at
most 64 points. A dithered area is hundreds of one-pixel marks, so dither can only live in things that never move.
So the screen is two layers:

  static artwork   the body, legs, hump, tail, swatches, ground dots and both bar glyphs, straight from the trace of
                   the owner's photo (opxy/reference/toro-ink-rest.jpg) as run-length <rect>s in white, 1 px dither
  nodes            everything that moves or changes: the head group (face, brow, ears, horns, eyes, muzzle, nostrils),
                   the tail tuft, the steam puffs, sparkles, grain and the torn scanlines. These are flat palette
                   greys with a 2 px white outline, matched to the dither density they replace
  mutable outlines the burst beside the muzzle (res) and two heat squiggles (fold)

Controls (the OP-1 order the header shows):
  spread  horns scale out from their roots             shape   horn tips turn up and out
  fold    the head lowers and tilts forward to charge; heat squiggles appear and tighten
  cutoff  0: dead eyes, dark horns, ears flat · default: the photo · 100: eyes wide, face lit
  res     the muzzle flushes bright, the nostrils flare, the burst grows
  noise   sparkles and grain                            drive   steam, puff by puff from the nostrils
  aphx    torn scanlines slip across the swatches, per key; one horn turns off on its own
  a note  the head wobbles on its neck (3.5° at 2.2 Hz, settling in ~0.5 s), the eyes flash wide, one more puff

    python3 screens/toro/gen_ink.py            # frames into screens/toro/ink/frames, fragment, board
    python3 screens/toro/gen_ink.py --debug    # the vector parts over the trace at 4×
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "concepts"))
import gen_frames as g  # noqa: E402  (helpers: f, poly, header preview, DEFAULTS, CONTROLS)
import ink_trace  # noqa: E402  (the trace of the owner's photo)

W, H, TOP = 480, 220, 40
OUT = HERE / "ink"
PREFIX = "toro"
PATHS = 3                                                  # mutable outlines: burst, squiggle A, squiggle B
HEADER_FIRST = PATHS                                       # the two-page header's 8 bar nodes follow the outlines
FIRST_ART = HEADER_FIRST + 8

f, poly = g.f, g.poly
WHITE, BLACK = "#FFFFFF", "#000000"
# palette: (fill, stroke, width). Greys match the dither densities they stand in for: 25 % → #4B4B4B, 50 % → #7D7D7D, 75 % → #AFAFAF
PALETTE = [(BLACK, WHITE, 2), ("#7D7D7D", WHITE, 2), ("#AFAFAF", WHITE, 2), (WHITE, WHITE, 2), ("#4B4B4B", WHITE, 2),
           ("#323232", WHITE, 2), ("#646464", WHITE, 2), (WHITE, WHITE, 1), (BLACK, WHITE, 2)]
P_INK, P_MID, P_LIGHT, P_WHITE, P_DARK, P_LIT1, P_LIT2, P_GRAIN, P_OUTLINE = range(9)

# ---- geometry, absolute px, read off the trace at 4× ---------------------------------------------------------------
PIVOT = (238, 174)                                         # the neck: the head wobbles and lowers about this
FACE = [(188, 77), (194, 64), (206, 55), (224, 50), (245, 50), (264, 54), (278, 62), (287, 72), (290, 78), (281, 81),
        (281, 108), (290, 120), (290, 140), (282, 152), (266, 155), (212, 174), (205, 174), (192, 166), (182, 152),
        (177, 134), (181, 118), (194, 110), (194, 81)]
BROW = [(194, 78), (281, 78)]
EYE_L = [(196, 108), (220, 107), (224, 114), (223, 134), (214, 138), (199, 136), (195, 126)]
EYE_R = [(252, 107), (276, 108), (280, 120), (279, 134), (266, 138), (254, 135), (251, 116)]
EYE_C = ((210, 124), (265, 124))
MUZZLE = [(216, 152), (261, 152), (266, 158), (266, 168), (261, 173), (216, 173), (211, 168), (211, 158)]
NOSTRILS = ((226, 164), (249, 164))
EAR_L = [(196, 100), (183, 101), (172, 109), (172, 119), (182, 126), (196, 124)]
EAR_R = [(475 - x, y) for x, y in EAR_L]
HORN_L = [(192, 101), (176, 104), (160, 101), (148, 92), (142, 78), (143, 63), (149, 52), (157, 45), (164, 45),
          (162, 56), (161, 68), (166, 78), (177, 83), (190, 80)]
HORN_R = [(475 - x, y) for x, y in HORN_L]
HORN_ROOT = ((191, 90), (284, 90))
EAR_ROOT = ((194, 112), (281, 112))
TUFT = [(387, 56), (393, 66), (396, 78), (392, 88), (383, 92), (374, 88), (371, 77), (376, 66)]
TUFT_ROOT = (380, 92)
BURST = (150, 150)
SQUIGGLES = ((140, 112), (345, 104))
PUFFS_L = [(214, 166, 4), (199, 165, 5), (184, 161, 6), (168, 154, 7), (152, 146, 8), (136, 138, 8), (120, 128, 9),
           (105, 117, 9), (92, 105, 10), (84, 92, 10), (76, 80, 9), (62, 86, 7), (52, 100, 6), (60, 112, 5)]
PUFFS_R = [(262, 166, 4), (278, 163, 5), (294, 157, 6), (310, 149, 7), (326, 140, 8), (342, 130, 8), (356, 119, 9),
           (368, 108, 9), (380, 96, 10), (392, 85, 10), (406, 80, 9), (418, 90, 7), (424, 104, 6), (414, 112, 5)]
SPARKLES = [(60, 70), (430, 60), (70, 180), (420, 150), (120, 60), (330, 200), (40, 120), (450, 110)]
GRAIN = [(32, 90), (90, 200), (160, 60), (300, 50), (440, 190), (380, 190), (20, 170), (200, 205), (270, 205), (460, 80), (130, 150), (350, 60)]
SWATCHES = [(90, 42, 128, 80), (90, 102, 125, 135), (362, 58, 396, 92), (366, 120, 398, 152)]
STATIC_CLEAR = [(142, 142, 158, 158)]                      # where the trace has the burst; it's a mutable outline now


def smooth(pts, per=3):
    """Catmull-Rom through a closed polygon: authored as a few corners, drawn rounded like the photo"""
    n = len(pts)
    out = []
    for i in range(n):
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        for k in range(per):
            t = k / per
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[c]) + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2
                                    + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in (0, 1)))
    return out


def centroid(pts):
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def rel(pts, o):
    return [(x - o[0], y - o[1]) for x, y in pts]


def ribbon(pts, w):
    """a line as one closed outline"""
    n = len(pts)
    out_l, out_r = [], []
    for i, (x, y) in enumerate(pts):
        a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        out_l.append((x - dy / ln * w / 2, y + dx / ln * w / 2))
        out_r.append((x + dy / ln * w / 2, y - dx / ln * w / 2))
    return out_l + out_r[::-1]


def star4(r):
    return [(0, -r), (r * 0.3, -r * 0.3), (r, 0), (r * 0.3, r * 0.3), (0, r), (-r * 0.3, r * 0.3), (-r, 0), (-r * 0.3, -r * 0.3)]


def burst_outline(r, rays=8):
    """rays with a hollow centre, as one closed outline; each tip has a small flat end (no reversal)"""
    pts = []
    r_in, half = r * 0.42, 0.4
    for k in range(rays):
        a = 2 * math.pi * k / rays
        c, s = math.cos(a), math.sin(a)
        nx, ny = -s * half, c * half
        pts += [(c * r_in - nx, s * r_in - ny), (c * r - nx, s * r - ny), (c * r + nx, s * r + ny), (c * r_in + nx, s * r_in + ny)]
    return pts


def squiggle_outline(length, amp, turns, w=2.0):
    pts = [(amp * math.sin(t / length * turns * 2 * math.pi), t) for t in np.linspace(0, length, 14)]
    return ribbon(pts, w)


def cloud(r, lobes=5, n=40):
    """a puff of steam: a circle with soft lobes, one closed outline"""
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        rr = r * (0.86 + 0.14 * abs(math.cos(lobes * a / 2)) ** 0.6)
        pts.append((math.cos(a) * rr, math.sin(a) * rr))
    return pts


def circle_pts(r, n=12):
    return [(math.cos(2 * math.pi * k / n) * r, math.sin(2 * math.pi * k / n) * r) for k in range(n)]


# ---- the parts (node table) -------------------------------------------------------------------------------------------
class Part:
    def __init__(self, name, origin, pts=None, palette=P_INK, r=None, group="free"):
        self.name, self.origin, self.pts, self.palette, self.r, self.group = name, origin, pts, palette, r, group


def parts() -> list[Part]:
    P = []
    P.append(Part("burst", BURST, burst_outline(6), P_OUTLINE))                    # mutable 0
    P.append(Part("squiggle_a", SQUIGGLES[0], squiggle_outline(26, 3.5, 1.5), P_OUTLINE))
    P.append(Part("squiggle_b", SQUIGGLES[1], squiggle_outline(26, 3.5, 1.5), P_OUTLINE))
    for i in range(8):                                                             # header bar steps (SDK two-page header)
        P.append(Part(f"header_{i}", (60 * i, 0), [(0, 0), (60, 0), (60, 20), (0, 20)], P_INK, group="header"))
    head = "head"
    P.append(Part("horn_l", HORN_ROOT[0], rel(smooth(HORN_L, 3), HORN_ROOT[0]), P_MID, group=head))
    P.append(Part("horn_r", HORN_ROOT[1], rel(smooth(HORN_R, 3), HORN_ROOT[1]), P_MID, group=head))
    P.append(Part("ear_l", EAR_ROOT[0], rel(smooth(EAR_L, 4), EAR_ROOT[0]), P_MID, group=head))
    P.append(Part("ear_r", EAR_ROOT[1], rel(smooth(EAR_R, 4), EAR_ROOT[1]), P_MID, group=head))
    c = centroid(FACE)
    P.append(Part("face", c, rel(smooth(FACE, 2), c), P_INK, group=head))
    P.append(Part("brow", (237.5, 78), rel(ribbon(BROW, 2), (237.5, 78)), P_WHITE, group=head))
    for n, (patch, ec) in (("l", (EYE_L, EYE_C[0])), ("r", (EYE_R, EYE_C[1]))):
        P.append(Part(f"eye_{n}", ec, rel(smooth(patch, 4), ec), P_INK, group=head))
    for n, ec in (("l", EYE_C[0]), ("r", EYE_C[1])):
        P.append(Part(f"white_{n}", ec, None, P_WHITE, r=6, group=head))                   # the photo's white disc
    for n, ec in (("l", EYE_C[0]), ("r", EYE_C[1])):
        P.append(Part(f"pupil_{n}", (ec[0] + 1, ec[1] - 1), None, P_INK, r=3.5, group=head))
    c = centroid(MUZZLE)
    P.append(Part("muzzle", c, rel(smooth(MUZZLE, 4), c), P_LIGHT, group=head))
    for n, nc in (("l", NOSTRILS[0]), ("r", NOSTRILS[1])):
        P.append(Part(f"nostril_{n}", nc, None, P_WHITE, r=5, group=head))
    P.append(Part("tuft", TUFT_ROOT, rel(smooth(TUFT, 4), TUFT_ROOT), P_MID))
    for side, puffs in (("l", PUFFS_L), ("r", PUFFS_R)):
        for i, (x, y, r) in enumerate(puffs):
            P.append(Part(f"puff_{side}{i}", (x, y), cloud(6, lobes=4 + i % 3), P_MID, group="steam"))
            P[-1].puff_scale = r / 6
    for i, (x, y) in enumerate(SPARKLES):
        P.append(Part(f"sparkle_{i}", (x, y), star4(5), P_WHITE, group="sparkle"))
    for i, (x, y) in enumerate(GRAIN):
        P.append(Part(f"grain_{i}", (x, y), None, P_GRAIN, r=1, group="grain"))
    for i, (x0, y0, x1, y1) in enumerate(SWATCHES):
        P.append(Part(f"scan_{i}", ((x0 + x1) / 2, (y0 + y1) / 2), [(-(x1 - x0) / 2, -1), ((x1 - x0) / 2, -1), ((x1 - x0) / 2, 1), (-(x1 - x0) / 2, 1)], P_WHITE, group="scan"))
    return P


PARTS = parts()
INDEX = {p.name: i for i, p in enumerate(PARTS)}


# ---- the static layer ------------------------------------------------------------------------------------------------
def static_pixels() -> np.ndarray:
    """the trace minus everything a node now draws"""
    base = ink_trace.base().copy()
    im = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(im)
    for pts in (FACE, HORN_L, HORN_R, EAR_L, EAR_R, MUZZLE, TUFT, EYE_L, EYE_R):
        d.polygon([(round(x), round(y)) for x, y in pts], fill=255)
    for x0, y0, x1, y1 in STATIC_CLEAR:
        d.rectangle([x0, y0, x1, y1], fill=255)
    m = binary_dilation(np.array(im) > 0, iterations=3)
    base[m] = False
    base[:TOP] = False
    return base


def static_rects(px: np.ndarray, cell: int = 1) -> list[tuple[int, int, int, int]]:
    """horizontal runs of white as (x, y, w, h); cell=2 coarsens the dither to 2 × 2 blocks"""
    if cell > 1:
        hh, ww = H // cell, W // cell
        px = px[:hh * cell, :ww * cell].reshape(hh, cell, ww, cell).mean(axis=(1, 3)) > 0.5
    rects = []
    for y, row in enumerate(px):
        x = 0
        n = len(row)
        while x < n:
            if row[x]:
                x0 = x
                while x < n and row[x]:
                    x += 1
                rects.append((x0 * cell, y * cell, (x - x0) * cell, cell))
            else:
                x += 1
    return rects


# ---- posing ----------------------------------------------------------------------------------------------------------
def kink(a):
    return 0.4 * a + 0.6 * a ** 3


def note(t):
    if t is None:
        return dict(wobble=0.0, flash=0.0, flare=0)
    env = math.exp(-t / 0.5)
    return dict(wobble=3.5 * math.sin(2 * math.pi * 2.2 * t) * env, flash=1.0 if t < 0.15 else 0.0, flare=1 if t < 0.6 else 0)


def rot(pts, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [(x * c - y * s, x * s + y * c) for x, y in pts]


class Pose:
    """one node's frame: origin, uniform scale, turn, palette, visible; `pts` only for mutable outlines"""

    def __init__(self, x, y, scale=1.0, turn=0.0, palette=None, visible=True, pts=None):
        self.x, self.y, self.scale, self.turn, self.palette, self.visible, self.pts = x, y, scale, turn, palette, visible, pts


def pose(v: dict, t=None, key: int = 0) -> list[Pose]:
    D = g.DEFAULTS
    n = note(t)
    out = [Pose(p.origin[0], p.origin[1], palette=p.palette) for p in PARTS]
    cut, res, fold = v["cutoff"], v["res"], v["fold"]

    # the head group: lowered and tilted by fold, wobbling with the note, all about the neck
    tilt = 4 * fold + n["wobble"]
    drop = 10 * fold
    c, s = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
    for i, p in enumerate(PARTS):
        if p.group != "head":
            continue
        dx, dy = p.origin[0] - PIVOT[0], p.origin[1] - PIVOT[1]
        out[i].x, out[i].y = PIVOT[0] + dx * c - dy * s, PIVOT[1] + drop + dx * s + dy * c
        out[i].turn = tilt

    # spread scales the horns from their roots; shape turns their tips up and out; aphx lets one horn go its own way
    k = 0.9 + 0.5 * v["spread"]
    curl = 35 * v["shape"]
    drift = kink(v["aphx"]) * 18 * (((key * 7919) % 11) / 10 - 0.5) * 2
    out[INDEX["horn_l"]].scale, out[INDEX["horn_l"]].turn = k, tilt - curl
    out[INDEX["horn_r"]].scale, out[INDEX["horn_r"]].turn = k, tilt + curl + drift
    # cutoff: horns and ears darken toward 0 and the ears go flat; the face lights up toward 100
    horn_pal = P_MID if cut >= 0.3 else P_DARK
    for nm in ("horn_l", "horn_r", "ear_l", "ear_r"):
        out[INDEX[nm]].palette = horn_pal
    droop = 25 * max(0.0, (D["cutoff"] - cut) / D["cutoff"])
    out[INDEX["ear_l"]].turn += -droop
    out[INDEX["ear_r"]].turn += droop
    out[INDEX["face"]].palette = P_INK if cut < 0.7 else P_LIT1 if cut < 0.85 else P_LIT2
    # the eyes: dead at 0, the photo's glint by default, wide open at 100; a note flashes them wide
    open_ = max(n["flash"], (cut - D["cutoff"]) / (1 - D["cutoff"]))   # above the default the white disc grows to fill the eye
    eye = (0.15 + 0.85 * min(1.0, cut / D["cutoff"])) * (1 + 0.7 * max(0.0, open_))   # below it, it shrinks toward dead
    for side in "lr":
        out[INDEX[f"white_{side}"]].visible = cut > 0.03 or n["flash"] > 0
        out[INDEX[f"white_{side}"]].scale = min(1.7, eye)
        out[INDEX[f"pupil_{side}"]].visible = open_ > 0.6
    # res: the muzzle flushes, the nostrils flare, the burst grows
    out[INDEX["muzzle"]].palette = P_LIGHT if res < 0.5 else P_WHITE
    for side in "lr":
        out[INDEX[f"nostril_{side}"]].scale = 1 + 0.6 * res
        out[INDEX[f"nostril_{side}"]].palette = P_WHITE if res < 0.5 else P_INK
    out[INDEX["burst"]].pts = burst_outline(4 + 12 * res, rays=8 if res > 0.5 else 6)
    # fold: heat squiggles
    for nm, k_ in (("squiggle_a", 0.3), ("squiggle_b", 0.65)):
        out[INDEX[nm]].visible = fold >= k_
        out[INDEX[nm]].pts = squiggle_outline(26, 3.5, 1.5 + 1.5 * fold)
    # drive: steam, puff by puff; the note flares one more
    shown = round(len(PUFFS_L) * min(1.0, v["drive"])) + n["flare"] * (1 if v["drive"] > 0.02 or t is not None else 0)
    for side, puffs in (("l", PUFFS_L), ("r", PUFFS_R)):
        for i in range(len(puffs)):
            q = out[INDEX[f"puff_{side}{i}"]]
            q.visible = i < shown
            q.scale = PARTS[INDEX[f"puff_{side}{i}"]].puff_scale
            q.turn = 37 * i
    # noise: sparkles and grain
    ns = round(len(SPARKLES) * v["noise"])
    for i in range(len(SPARKLES)):
        out[INDEX[f"sparkle_{i}"]].visible = i < ns
        out[INDEX[f"sparkle_{i}"]].scale = 0.6 + 0.9 * v["noise"]
    ng = round(len(GRAIN) * v["noise"])
    for i in range(len(GRAIN)):
        out[INDEX[f"grain_{i}"]].visible = i < ng
    # aphx: torn scanlines across the swatches
    slip = kink(v["aphx"])
    for i, (x0, y0, x1, y1) in enumerate(SWATCHES):
        p = out[INDEX[f"scan_{i}"]]
        p.visible = slip > 0.05
        p.x += slip * 14 * ((((key + i) * 7919) % 11) / 10 - 0.5) * 2
        p.y += (i - 1.5) * 2 * slip
    # a note: the tuft flicks against the wobble
    out[INDEX["tuft"]].turn = -n["wobble"] * 3
    return out


# ---- rendering -------------------------------------------------------------------------------------------------------
def node_svg(i: int, p: Part, q: Pose, fragment: bool) -> str:
    fill, stroke, width = PALETTE[q.palette if q.palette is not None else p.palette]
    if i < PATHS:
        fill = "none"
    if not q.visible and not fragment:
        x, y = 640, 320
    else:
        x, y = q.x, q.y
    ident = f'id="{PREFIX}_node_{i}" '
    if p.r is not None:
        r = p.r * (1 if fragment else q.scale)
        return f'<circle {ident}transform="matrix(1 0 0 1 {f(x)} {f(y)})" cx="0" cy="0" r="{f(r)}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'
    pts = q.pts if (q.pts is not None and not fragment) else p.pts
    if not fragment:
        pts = rot([(px * q.scale, py * q.scale) for px, py in pts], q.turn)
    return f'<path {ident}transform="matrix(1 0 0 1 {f(x)} {f(y)})" d="{poly(pts)}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'


def body_svg(v, t=None, key=0, fragment=False, cell=1) -> list[str]:
    poses = pose(v, t, key)
    rects = static_rects(static_pixels(), cell)
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
    o += [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{WHITE}" stroke="none"/>' for x, y, w, h in rects]
    o.append("</g>")
    order = [i for i, p in enumerate(PARTS) if p.group == "steam"] + [i for i, p in enumerate(PARTS) if p.group == "head"] + \
            [INDEX["tuft"]] + [i for i, p in enumerate(PARTS) if p.group in ("sparkle", "grain", "scan")] + list(range(PATHS))
    for i in order:
        o.append(node_svg(i, PARTS[i], poses[i], fragment))
    if fragment:
        for i, (fill, stroke, width) in enumerate(PALETTE):
            o.append(f'<path id="{PREFIX}_palette_{i}" transform="matrix(1 0 0 1 640 320)" d="M0,0 L4,0 L4,4 L0,4 Z" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')
    return o


def frame_svg(v, t=None, key=0) -> str:
    return "\n".join(['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
                      '<rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>'] + body_svg(v, t, key) + g.header(v) + ["</svg>"])


def fragment_svg(cell=1) -> str:
    return "\n".join([f'<g id="{PREFIX}_panel">'] + body_svg(dict(g.DEFAULTS), None, 0, fragment=True, cell=cell) + ["</g>"])


def debug_png() -> Image.Image:
    base = ink_trace.base()
    rgb = np.zeros((H, W, 3), np.uint8)
    rgb[base] = (90, 90, 90)
    im = Image.fromarray(rgb).resize((W * 4, H * 4), Image.NEAREST)
    d = ImageDraw.Draw(im)
    S = lambda pts: [(x * 4, y * 4) for x, y in pts]
    for pts, col in ((FACE, (255, 90, 90)), (EYE_L, (90, 255, 90)), (EYE_R, (90, 255, 90)), (MUZZLE, (90, 160, 255)),
                     (EAR_L, (255, 255, 90)), (EAR_R, (255, 255, 90)), (HORN_L, (255, 150, 60)), (HORN_R, (255, 150, 60)), (TUFT, (255, 90, 255))):
        d.polygon(S(pts), outline=col)
    for (x, y, r) in PUFFS_L + PUFFS_R:
        d.ellipse([(x - r) * 4, (y - r) * 4, (x + r) * 4, (y + r) * 4], outline=(120, 200, 255))
    return im.crop((100, 150, 1760, 880))


def main():
    OUT.mkdir(exist_ok=True)
    (OUT / "frames").mkdir(exist_ok=True)
    if "--debug" in sys.argv:
        debug_png().save(OUT / "debug.png")
        print("wrote", OUT / "debug.png")
        return
    D = dict(g.DEFAULTS)
    frames = {"rest": (D, None), "playing": (D, 0.05), "note-0.25s": (D, 0.25), "note-0.6s": (D, 0.6)}
    for i, name in enumerate(g.CONTROLS):
        for val in (0, 50, 100):
            frames[f"c{i + 1}-{val:03d}"] = (dict(D, **{name: val / 100}), None)
    for name, (vals, t) in frames.items():
        (OUT / "frames" / f"{name}.svg").write_text(frame_svg(vals, t), encoding="utf-8")
    (OUT / "panel.svg.fragment").write_text(fragment_svg(), encoding="utf-8")
    (OUT / "panel-lint.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">\n' + fragment_svg() + "\n</svg>", encoding="utf-8")
    (OUT / "panel-cell2.svg.fragment").write_text(fragment_svg(cell=2), encoding="utf-8")
    px = static_pixels()
    info = {"nodes": len(PARTS), "paths": PATHS, "points": 64, "texts": 16, "palette": len(PALETTE),
            "staticRects": len(static_rects(px)), "staticRectsCell2": len(static_rects(px, 2)),
            "controls": g.CONTROLS}
    (OUT / "budget.json").write_text(json.dumps(info, indent=2))
    print(json.dumps(info))
    board(frames)


def board(frames):
    """every frame at 1:1 on one sheet: the controls in rows of three (0, 50, 100), the note frames on top"""
    import subprocess, tempfile
    names = ["rest", "playing", "note-0.25s", "note-0.6s"] + [f"c{i + 1}-{v:03d}" for i in range(8) for v in (0, 50, 100)]
    cols, P_ = 4, 8
    rows = math.ceil(len(names) / cols)
    sheet = Image.new("RGB", (P_ + cols * (W + P_), P_ + rows * (H + 18 + P_)), (40, 40, 40))
    d = ImageDraw.Draw(sheet)
    with tempfile.TemporaryDirectory() as tmp:
        for k, name in enumerate(names):
            png = Path(tmp) / f"{name}.png"
            subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(OUT / "frames" / f"{name}.svg"), "-o", str(png)], check=True)
            x, y = P_ + (k % cols) * (W + P_), P_ + (k // cols) * (H + 18 + P_)
            label = name if k < 4 else f"{g.CONTROLS[int(name[1]) - 1]} {int(name[-3:])}"
            d.text((x, y), label, fill=(200, 200, 200))
            sheet.paste(Image.open(png).convert("RGB"), (x, y + 18))
    sheet.save(OUT / "board.png")


if __name__ == "__main__":
    main()
