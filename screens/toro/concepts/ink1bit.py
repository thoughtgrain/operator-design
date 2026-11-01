#!/usr/bin/env python3
"""Toro round 9: one-bit ink. A study in the language of the reference the user picked (see concepts.md, round 9).

The language, as I read it from the reference, not its artwork:
  - every shape gets a hard 2 px white outline; nothing is anti-aliased
  - tone comes from ordered (Bayer) dither in white, never from grey values: black, 25 %, 50 %, 75 %, white
  - one hero figure, centred, between figure and symbol; chunky, friendly, readable at 1:1
  - small sound-glyphs orbit it (a waveform, sparkles, squiggles, dither blocks), and each one is a control

My bull is head-on and lowered, front legs planted, snorting two bursts down into the dust:
  spread  horns sweep wider            shape  the waveform glyph morphs saw → triangle
  fold    the steam curls fold tighter  noise  sparkles and grain in the air
  cutoff  the face's dither lightens    drive  the steam bursts grow
  res     the nose ring swings bigger   aphx   dither blocks slip out of place, per key
  a note: the head drops 4 px and the bursts puff out

    python3 screens/toro/concepts/ink1bit.py   →  i1-ink/<pose>.png and board-ink.png
"""
from __future__ import annotations

import math
import random
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import gen_frames as g  # noqa: E402
from uniques import spline, bez, tube  # noqa: E402

W, H, TOP = 480, 220, 40
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0 + 1 / 32


class Ink:
    """a one-bit canvas: paint black to occlude, dither to tone, outline to draw"""

    def __init__(self):
        self.px = np.zeros((H, W), dtype=np.uint8)
        yy, xx = np.mgrid[0:H, 0:W]
        self.bayer = BAYER[yy % 4, xx % 4]

    def _mask(self, pts):
        im = Image.new("L", (W, H), 0)
        ImageDraw.Draw(im).polygon([(round(x), round(y)) for x, y in pts], fill=255)
        return np.array(im) > 0

    def fill(self, pts, tone, line=2):
        """black-out the shape, dither it to `tone` (0 black .. 1 white), then outline it"""
        m = self._mask(pts)
        self.px[m] = 0
        if tone > 0:
            self.px[m & (self.bayer < tone)] = 255
        if line:
            self.line(pts + pts[:1], line)

    def line(self, pts, w=2):
        im = Image.new("L", (W, H), 0)
        ImageDraw.Draw(im).line([(round(x), round(y)) for x, y in pts], fill=255, width=w, joint="curve")
        self.px[np.array(im) > 0] = 255

    def erase_line(self, pts, w=2):
        im = Image.new("L", (W, H), 0)
        ImageDraw.Draw(im).line([(round(x), round(y)) for x, y in pts], fill=255, width=w, joint="curve")
        self.px[np.array(im) > 0] = 0

    def dot(self, x, y, r, tone=1.0, line=0):
        pts = [(x + r * math.cos(t), y + r * math.sin(t)) for t in [i * math.pi / 12 for i in range(24)]]
        self.fill(pts, tone, line)

    def block(self, x, y, w, h, tone):
        """a dither swatch, no outline"""
        x, y = int(x), int(y)
        sl = (slice(max(0, y), min(H, y + h)), slice(max(0, x), min(W, x + w)))
        self.px[sl] = np.where(self.bayer[sl] < tone, 255, 0)

    def pixel(self, x, y):
        if 0 <= int(y) < H and 0 <= int(x) < W:
            self.px[int(y), int(x)] = 255

    def image(self, v):
        im = Image.fromarray(self.px, "L").convert("RGB")
        im.paste(header(v), (0, 0))
        return im


def header(v):
    svg = "\n".join(['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="38" viewBox="0 0 480 38">'] + g.header(v) + ["</svg>"])
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / "h.svg").write_text(svg)
        subprocess.run(["rsvg-convert", "-w", "480", "-h", "38", str(p / "h.svg"), "-o", str(p / "h.png")], check=True)
        return Image.open(p / "h.png").convert("RGB")


# ---- the sound-glyphs ------------------------------------------------------------------------------------------------
def sparkle(c, x, y, r):
    c.line([(x - r, y), (x + r, y)], 1)
    c.line([(x, y - r), (x, y + r)], 1)
    c.line([(x - r * 0.4, y - r * 0.4), (x + r * 0.4, y + r * 0.4)], 1)
    c.line([(x - r * 0.4, y + r * 0.4), (x + r * 0.4, y - r * 0.4)], 1)


def waveform(c, x, y, shape_v, n=19):
    """shape: the glyph's bars trace a saw at 0 and a triangle at 1"""
    for i in range(n):
        u = (i / (n - 1) * 2) % 1
        saw = u
        tri = 1 - abs(2 * u - 1)
        h = 3 + 22 * (saw * (1 - shape_v) + tri * shape_v)
        c.line([(x + i * 4, y - h / 2), (x + i * 4, y + h / 2)], 2)


def squiggle(c, x, y, length, amp, turns):
    pts = [(x + amp * math.sin(t / length * turns * 2 * math.pi), y + t) for t in range(0, int(length) + 1, 2)]
    c.line(pts, 2)


def cloud(c, cx, cy, r, tone, curls, seed):
    """a cumulus of overlapping puffs, each outlined, with a curl drawn inside the biggest"""
    rnd = random.Random(seed)
    puffs = [(cx, cy, r)]
    for k in range(4):
        a = math.pi * (0.9 + 1.2 * k / 3)
        puffs.append((cx + math.cos(a) * r * 0.85, cy + math.sin(a) * r * 0.55, r * rnd.uniform(0.55, 0.75)))
    for px_, py_, pr in sorted(puffs, key=lambda p: p[1]):
        c.dot(px_, py_, pr, tone, line=2)
    for k in range(curls):                                        # fold: curls inside the steam
        rr = r * (0.55 - 0.12 * k)
        if rr < 2.5:
            break
        arc = [(cx + rr * math.cos(t), cy + rr * math.sin(t)) for t in np.linspace(math.pi * 0.2, math.pi * 1.6, 12)]
        c.erase_line(arc, 2)


# ---- the bull --------------------------------------------------------------------------------------------------------
HEAD = [(-30, -38), (-14, -44), (14, -44), (30, -38), (38, -24), (38, -6), (32, 14), (27, 28),
        (-27, 28), (-32, 14), (-38, -6), (-38, -24)]
MUZZLE = [(-28, 22), (28, 22), (32, 36), (28, 52), (16, 58), (-16, 58), (-28, 52), (-32, 36)]
EAR = [(36, -22), (52, -30), (64, -26), (58, -16), (40, -10)]
HUMP = [(-58, -22), (-30, -40), (30, -40), (58, -22), (72, 0), (70, 30), (56, 44), (-56, 44), (-70, 30), (-72, 0)]
LEG = [(-11, 0), (11, 0), (11, 34), (14, 40), (14, 46), (-13, 46), (-13, 40), (-11, 34)]


def bull(v, playing=False, key=0):
    c = Ink()
    cx, cy = 240, 110 + (4 if playing else 0)
    P = lambda pts, dx=0, dy=0, sx=1: [(cx + dx + x * sx, cy + dy + y) for x, y in pts]
    lit = v["cutoff"]
    rnd = random.Random(11 + key)

    # air: grain (noise) and dither blocks (aphx slips them sideways, per key)
    for k in range(int(10 + 60 * v["noise"])):
        c.pixel(rnd.uniform(16, 464), rnd.uniform(TOP + 4, 214))
    slip = (0.4 * v["aphx"] + 0.6 * v["aphx"] ** 3) * (1.3 if playing else 1)
    for k, (bx, by, bw, bh, t) in enumerate([(108, 54, 28, 22, 0.5), (352, 60, 24, 28, 0.25), (86, 150, 20, 16, 0.25), (372, 150, 26, 18, 0.5)]):
        dx = slip * 22 * (rnd.random() - 0.5) * 2
        c.block(bx + dx, by, bw, bh, t)
        if slip > 0.05:
            c.block(bx - dx * 0.6, by + bh // 2, bw, 3, 1.0)       # a torn scanline from the slip
    # ground shadow
    c.fill([(cx + 96 * math.cos(t), 206 + 6 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 40)[:-1]], 0.25, line=0)

    # the body behind, shoulders and hump
    c.fill(P(HUMP, dy=12), 0.25)
    for sd in (-1, 1):                                             # front legs, planted
        c.fill(P(LEG, dx=sd * 34, dy=48), 0.5)
        c.fill(P([(-13, 40), (14, 40), (14, 46), (-13, 46)], dx=sd * 34, dy=48), 1.0)   # hooves

    # horns: thick crescents; spread sweeps them wider, the base gets two dither rings
    sp, cu = v["spread"], v["shape"]
    for sd in (-1, 1):
        spine = bez([(sd * 26, -38), (sd * (56 + 24 * sp), -44), (sd * (80 + 36 * sp), -52 - 4 * cu), (sd * (80 + 36 * sp - 16 * cu), -62 - 3 * cu)], 18)
        horn = tube(spine, 18, 3)
        c.fill(P(horn), 1.0)
        for j in (2, 5):
            band = tube(spine[j:j + 3], 18 - 15 * (j / 18) ** 0.9, 18 - 15 * ((j + 2) / 18) ** 0.9)
            c.fill(P(band), 0.5, line=0)

    # ears
    for sd in (-1, 1):
        c.fill(P(EAR, sx=sd), 0.5)
        c.line(P([(44, -20), (56, -24)], sx=sd), 2)

    # the head: cutoff lightens its dither
    c.fill(P(HEAD), 0.62 * lit)
    # forelock: a crest of three curls
    for k, dx in enumerate((-12, 0, 12)):
        c.dot(cx + dx, cy - 40 + (2 if k != 1 else -2), 7, 1.0 if k == 1 else 0.75, line=2)
    # brow: a heavy bar over angry eyes
    for sd in (-1, 1):
        c.fill(P([(sd * 8, -20), (sd * 32, -26), (sd * 32, -20), (sd * 10, -14)]), 1.0, line=0)
        eye = P([(sd * 12, -10), (sd * 28, -14), (sd * 26, -4), (sd * 14, -4)])
        c.fill(eye, 1.0)
        c.dot(cx + sd * 21, cy - 8, 2.4, 0.0)
    # the muzzle: lighter, two nostrils
    c.fill(P(MUZZLE), 0.75)
    for sd in (-1, 1):
        c.fill(P([(sd * 8, 34), (sd * 18, 32), (sd * 20, 40), (sd * 10, 42)]), 0.0)
    # nose ring: res swings it bigger
    rr = 7 + 6 * v["res"]
    ring = [(cx + rr * math.cos(t), cy + 50 + rr + rr * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 24)]
    c.line(ring, 4)
    c.line(ring, 2)

    # steam: two bursts snorted down and out from the nostrils; drive grows them, fold curls them, a note puffs them
    burst = 0.4 + 0.6 * v["drive"] + (0.35 if playing else 0)
    curls = 1 + round(3 * v["fold"])
    for sd in (-1, 1):
        for k in range(1 + round(2 * burst)):
            r = (9 + 7 * burst) * (1 - 0.18 * k)
            cloud(c, cx + sd * (62 + 30 * k * burst + 8 * burst), cy + 78 - 12 * k, r, 0.5 if k else 0.75, curls, seed=k * 7 + (sd > 0))

    # sound-glyphs: a waveform (shape), sparkles (noise), squiggles (spread of the drift)
    waveform(c, 26, 190, v["shape"])
    for k, (x, y, r) in enumerate([(392, 92, 6), (420, 70, 4), (70, 100, 5), (60, 72, 3)]):
        if k < 2 + round(2 * v["noise"]):
            sparkle(c, x, y, r + 3 * v["noise"])
    squiggle(c, 140, 70, 34, 4, 2 + round(2 * v["fold"]))
    squiggle(c, 338, 104, 30, 4, 2 + round(2 * v["fold"]))
    return c


def main():
    D = dict(g.DEFAULTS)
    poses = {"rest": (D, False), "spread-100": (dict(D, spread=1, shape=0.6), False), "cutoff-000": (dict(D, cutoff=0), False),
             "cutoff-100": (dict(D, cutoff=1), False), "fold-100": (dict(D, fold=1), False), "drive-100": (dict(D, drive=1), False),
             "noise-aphx-100": (dict(D, noise=1, aphx=1), False), "playing": (D, True)}
    d = HERE / "i1-ink"
    d.mkdir(exist_ok=True)
    tiles = []
    for pose, (vals, playing) in poses.items():
        im = bull(vals, playing).image(vals)
        im.save(d / f"{pose}.png")
        tiles.append((pose, im))
    P_, cols = 8, 2
    rows = math.ceil(len(tiles) / cols)
    board = Image.new("RGB", (P_ + cols * (W + P_), P_ + rows * (H + 18 + P_)), (40, 40, 40))
    dr = ImageDraw.Draw(board)
    for i, (pose, im) in enumerate(tiles):
        x, y = P_ + (i % cols) * (W + P_), P_ + (i // cols) * (H + 18 + P_)
        dr.text((x, y), pose, fill=(200, 200, 200))
        board.paste(im, (x, y + 18))
    board.save(HERE / "board-ink.png")
    print("wrote", len(tiles), "frames")


if __name__ == "__main__":
    main()
