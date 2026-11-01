#!/usr/bin/env python3
"""meikyu, round 1: five player pages.

meikyu (迷宮, "labyrinth") is a note player, not a synth: every key press plays the next eight steps of a sixteen-step
shift register (two halves, A and B) as a phrase, and Corrupt rewrites steps after they play, so the pattern drifts.

A player's page is far more limited than a synth's (open-xy `firmware/native-players`, sdk/include/opxy/player.hpp
and platform/opxy-1.2.1/screen_player.hpp):
  - static artwork, plus 24 "dots" the player shows or hides (any path; a hidden one moves off screen)
  - one centred text line (22 px stock font, ~y 157)
  - the stock four-control header (Dens, Scal, Crpt, Drum) and the SDK's output keyboard along the bottom (y 174+)
So nothing moves except dots switching on and off. meikyu's own mapping is kept: dots 0..15 are the register's steps
(lit when the step plays at the current density), dots 16..23 the last phrase's eight tones (lit where one sounded).
The text line names the last root, the half it started in, and the phrase count.

  m1 labyrinth   a seven-circuit Cretan labyrinth; the sixteen steps are stones along its path, the phrase is eight
                 footsteps walking in toward the centre
  m2 wheels      the register as two concentric dials, A outside and B inside; the phrase is eight lamps in an arc
  m3 tape        a punched tape loop: sixteen hole positions in two bars; the phrase is eight holes punched in a strip
  m4 blocks      the house's isometric blocks: two rows of eight (A, B) on a plinth; the phrase is a staircase
  m5 thread      Ariadne's thread winding through a maze of walls; steps are knots on it, the phrase is eight beads

    python3 screens/meikyu/concepts/pages.py      → p*/<pose>.svg and board-pages.png
"""
from __future__ import annotations

import math
import random
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "toro"))
import gen_frames as g  # noqa: E402

f, poly, G = g.f, g.poly, g.G
W, H = 480, 220
FONT = 'font-family="UniversNextPro-Light"'
TITLES = ["Dens", "Scal", "Crpt", "Drum"]
SCALES = ["minor", "major", "pent", "chrom"]
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
LINE, DIM, HOT, INK = G[5], G[3], "#F0F0F0", "#000000"
ART_BOTTOM = 146                                           # the text line sits at ~157 and the keyboard from 174


# ---- meikyu's state, enough to light the page -------------------------------------------------------------------------
class Page:
    def __init__(self, density=0.6, scale=0, corrupt=0.2, drum=False, phrase=None, root=None, start=0, count=0, seed=7):
        rnd = random.Random(seed)
        self.weights = [rnd.randrange(100) for _ in range(16)]
        self.density, self.scale, self.corrupt, self.drum = density, scale, corrupt, drum
        self.phrase, self.root, self.start, self.count = phrase, root, start, count

    def step_lit(self, i):
        return self.weights[i] < round(self.density * 100)

    def tone_lit(self, k):
        return self.phrase is not None and bool((self.phrase >> k) & 1)

    def line(self):
        if self.root is None:
            return "meikyu"
        return f"{NOTE_NAMES[self.root % 12]} {'A' if self.start < 8 else 'B'} phrase {self.count}"

    def played_keys(self):
        """output keyboard: the pitches the last phrase is sounding (24 keys from F)"""
        if self.phrase is None:
            return set()
        steps = [0, 3, 5, 7, 10, 12, 15, 17] if self.scale == 0 else [0, 2, 4, 7, 9, 12, 14, 16]
        return {(self.root - 5 + steps[k]) % 24 for k in range(8) if self.tone_lit(k)}


# ---- drawing helpers ---------------------------------------------------------------------------------------------------
def line_(pts, stroke=LINE, w=1.2, close=False, fill="none"):
    d = poly(pts) if close else "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts)
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{w}" stroke-linejoin="round" stroke-linecap="round"/>'


def arc(cx, cy, r, a0, a1, n=24, ry=None):
    ry = r if ry is None else ry
    return [(cx + r * math.cos(a0 + (a1 - a0) * k / n), cy + ry * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]


def chunks(pts, size=60):
    """long lines split into runs of ≤ 61 points (the device's 64-point path limit)"""
    return [pts[k:k + size + 1] for k in range(0, len(pts) - 1, size)]


def dot_shape(kind, x, y, s, lit):
    """a page dot: drawn lit (bright, filled) or unlit (its dim outline is static art underneath)"""
    if kind == "diamond":
        pts = [(x, y - s), (x + s, y), (x, y + s), (x - s, y)]
    elif kind == "square":
        pts = [(x - s, y - s), (x + s, y - s), (x + s, y + s), (x - s, y + s)]
    else:
        pts = [(x + s * math.cos(2 * math.pi * k / 12), y + s * math.sin(2 * math.pi * k / 12)) for k in range(12)]
    base = line_(pts, DIM, 1.0, close=True, fill=INK)
    return [base] + ([line_(pts, HOT, 0.6, close=True, fill=HOT)] if lit else [])


def header(p: Page) -> list[str]:
    o = ['<rect x="0" y="0" width="480" height="20" fill="#000000" stroke="none"/>']
    for i, c in enumerate(G):
        o.append(f'<rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
    vals = [str(round(p.density * 100)), SCALES[p.scale], str(round(p.corrupt * 100)), "on" if p.drum else "off"]
    for col in range(4):
        light = "#CBCBCB" if col < 2 else "#000000"
        size = 20 if len(vals[col]) <= 4 else 13
        o.append(f'<text transform="matrix(1 0 0 1 {5 + 120 * col} 10)" fill="{light}" {FONT} font-size="10px">{TITLES[col]}</text>')
        o.append(f'<text transform="matrix(1 0 0 1 {65 + 120 * col} 17.4)" fill="{light}" {FONT} font-size="{size}px">{vals[col]}</text>')
    return o


def footer(p: Page) -> list[str]:
    """the SDK's parts: the centred chord line and the output keyboard (24 keys from F, played ones marked)"""
    o = [f'<text transform="matrix(1 0 0 1 240 160)" fill="#F2F2F2" {FONT} font-size="18px" text-anchor="middle">{p.line()}</text>']
    played = p.played_keys()
    white = [k for k in range(24) if (k + 5) % 12 in (0, 2, 4, 5, 7, 9, 11)]
    kw = 480 / len(white)
    xs = {}
    for n, k in enumerate(white):
        x = n * kw
        xs[k] = x + kw / 2
        o.append(f'<rect x="{f(x + 0.5)}" y="174" width="{f(kw - 1)}" height="44" fill="#F0F0F0" stroke="none"/>')
    for k in range(24):
        if (k + 5) % 12 in (1, 3, 6, 8, 10):
            x = xs[k - 1] + kw / 2
            xs[k] = x
            o.append(f'<rect x="{f(x - kw * 0.3)}" y="174" width="{f(kw * 0.6)}" height="26" fill="#1A1A1A" stroke="none"/>')
    for k in played:
        black = (k + 5) % 12 in (1, 3, 6, 8, 10)
        o.append(f'<circle cx="{f(xs[k])}" cy="{190 if black else 208}" r="2.5" fill="{"#F0F0F0" if black else "#000000"}" stroke="none"/>')
    return o


def frame(p: Page, art: list[str]) -> str:
    return "\n".join(['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
                      '<rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>'] + art + footer(p) + header(p) + ["</svg>"])


# ---- m1 · labyrinth ----------------------------------------------------------------------------------------------------
def labyrinth(p: Page):
    """the classic seven-circuit Cretan labyrinth, drawn as concentric arcs open at the bottom, in perspective"""
    o = []
    cx, cy, sy = 240, 92, 0.62
    rings = [14 + 7.6 * k for k in range(8)]
    for k, r in enumerate(rings):
        gap = 0.36 if k % 2 else 0.2
        pts = arc(cx, cy, r, math.pi / 2 + gap, math.pi / 2 + 2 * math.pi - gap, 40, r * sy)
        o.append(line_(pts, LINE if k == len(rings) - 1 else G[4], 1.6 if k == len(rings) - 1 else 1.1))
    o.append(line_([(cx, cy + 14 * sy), (cx, cy + rings[-1] * sy + 6)], G[4], 1.1))       # the seed's spine
    # the sixteen steps as stones in the corridors: A on the outer two, B on the inner two, four per corridor
    for i in range(16):
        c = (6, 5, 3, 2)[i // 4]
        r = (rings[c] + rings[c + 1]) / 2
        a = math.pi / 2 + 0.7 + (2 * math.pi - 1.4) * ((i % 4) + 0.5 * (c % 2)) / 4
        o += dot_shape("diamond", cx + r * math.cos(a), cy + r * sy * math.sin(a), 3.2, p.step_lit(i))
    # the phrase: eight footsteps walking in along the spine from the mouth
    for k in range(8):
        o += dot_shape("circle", 330 + k * 16, 128 - k * 6, 3.2, p.tone_lit(k))
    o.append(line_([(330 - 8, 134), (330 + 7 * 16 + 8, 128 - 7 * 6 - 6)], DIM, 0.8))
    return o


# ---- m2 · wheels -------------------------------------------------------------------------------------------------------
def wheels(p: Page):
    o = []
    cx, cy = 150, 86
    for r, w in ((56, 1.4), (40, 1.0), (24, 1.0)):
        o.append(line_(arc(cx, cy, r, 0, 2 * math.pi, 48), G[4], w))
    for i in range(16):
        r = 48 if i < 8 else 32
        a = -math.pi / 2 + 2 * math.pi * (i % 8) / 8
        o.append(line_([(cx + (r - 6) * math.cos(a), cy + (r - 6) * math.sin(a)), (cx + (r + 6) * math.cos(a + 0.0), cy + (r + 6) * math.sin(a))], DIM, 0.8))
        o += dot_shape("circle", cx + r * math.cos(a + math.pi / 8), cy + r * math.sin(a + math.pi / 8), 4.2 if i < 8 else 3.6, p.step_lit(i))
    o.append(f'<text transform="matrix(1 0 0 1 {cx - 4} {cy - 60})" fill="{G[4]}" {FONT} font-size="10px">A</text>')
    o.append(f'<text transform="matrix(1 0 0 1 {cx - 3} {cy + 4})" fill="{G[4]}" {FONT} font-size="10px">B</text>')
    # the phrase: eight lamps on an arc to the right, like a VU meter's bulbs
    for k in range(8):
        a = math.pi * (1.15 + 0.7 * k / 7)
        x, y = 380 + 84 * math.cos(a), 132 + 84 * math.sin(a)
        o += dot_shape("circle", x, y, 5.2, p.tone_lit(k))
    o.append(line_(arc(380, 132, 96, math.pi * 1.12, math.pi * 1.88, 30), DIM, 1.0))
    return o


# ---- m3 · tape ---------------------------------------------------------------------------------------------------------
def tape(p: Page):
    o = []
    x0, x1, y0, y1 = 40, 440, 40, 92
    o.append(line_([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], LINE, 1.2, close=True))
    for k in range(32):
        x = x0 + 8 + k * 12.25
        o.append(line_([(x - 1.2, y0 + 7), (x + 1.2, y0 + 7), (x + 1.2, y0 + 9.4), (x - 1.2, y0 + 9.4)], DIM, 0.6, close=True, fill=DIM))
    o.append(line_([(240, y0 + 2), (240, y1 - 2)], G[4], 1.0))     # the A | B bar line
    for i in range(16):
        x = x0 + 25 + i * 24.4 + (6 if i >= 8 else 0)
        o += dot_shape("square", x, 72, 5, p.step_lit(i))
    o.append(f'<text transform="matrix(1 0 0 1 {x0 + 4} {y1 + 12})" fill="{G[4]}" {FONT} font-size="10px">A</text>')
    o.append(f'<text transform="matrix(1 0 0 1 244 {y1 + 12})" fill="{G[4]}" {FONT} font-size="10px">B</text>')
    # the phrase: a strip punched below, curling off the loop
    sx0, sy0 = 150, 112
    o.append(line_([(sx0, sy0), (sx0 + 180, sy0), (sx0 + 180, sy0 + 26), (sx0, sy0 + 26)], LINE, 1.0, close=True))
    o.append(line_(arc(sx0, sy0 + 13, 13, math.pi / 2, math.pi * 1.5, 12), DIM, 1.0))
    for k in range(8):
        o += dot_shape("circle", sx0 + 14 + k * 22, sy0 + 13, 4.4, p.tone_lit(k))
    return o


# ---- m4 · blocks -------------------------------------------------------------------------------------------------------
def cube(x, y, s, h, top, left=None, right=None, stroke=None):
    t = [(x, y - h - s * 0.5), (x + s, y - h), (x, y - h + s * 0.5), (x - s, y - h)]
    l_ = [(x - s, y - h), (x, y - h + s * 0.5), (x, y + s * 0.5), (x - s, y)]
    r_ = [(x, y - h + s * 0.5), (x + s, y - h), (x + s, y), (x, y + s * 0.5)]
    st = stroke or G[4]
    return [line_(l_, st, 0.9, close=True, fill=INK), line_(r_, st, 0.9, close=True, fill=INK),
            line_(t, st, 0.9, close=True, fill=INK)]


def blocks(p: Page):
    o = []
    s = 13
    ox, oy = 150, 70
    # the plinth
    for j, half in enumerate((0, 1)):                             # A behind, B in front
        for k in range(8):
            i = half * 8 + k
            x = ox + (k - j) * s
            y = oy + (k + j) * s * 0.5 + j * 18
            lit = p.step_lit(i)
            o += cube(x, y, s, 10, G[3])
            if lit:                                               # the dot: the top face lit
                o.append(line_([(x, y - 10 - s * 0.5), (x + s, y - 10), (x, y - 10 + s * 0.5), (x - s, y - 10)], HOT, 0.6, close=True, fill=HOT))
    # the phrase: a staircase of eight rising to the right
    sx, sy = 330, 140
    for k in range(8):
        x, y = sx + k * 12, sy - k * 9
        o += cube(x, y, 9, 6 + k * 0, G[3])
        if p.tone_lit(k):
            o.append(line_([(x, y - 6 - 4.5), (x + 9, y - 6), (x, y - 6 + 4.5), (x - 9, y - 6)], HOT, 0.6, close=True, fill=HOT))
    return o


# ---- m5 · thread -------------------------------------------------------------------------------------------------------
def thread(p: Page):
    o = []
    # a maze of walls on a grid; the thread winds through the corridors
    walls = [((40, 40), (40, 140)), ((40, 40), (300, 40)), ((300, 40), (300, 80)), ((80, 70), (260, 70)), ((80, 70), (80, 140)),
             ((120, 100), (300, 100)), ((300, 100), (300, 140)), ((40, 140), (260, 140)), ((260, 120), (260, 140)), ((120, 100), (120, 120)),
             ((160, 120), (240, 120)), ((260, 70), (260, 84))]
    for a, b in walls:
        o.append(line_([a, b], G[4], 2.4))
    path = [(60, 136), (60, 55), (280, 55), (280, 85), (100, 85), (100, 130), (140, 130), (140, 110), (280, 110), (280, 130)]
    pts = []
    for a, b in zip(path, path[1:]):
        n = max(2, int(math.dist(a, b) / 3))
        for k in range(n):
            t = k / n
            pts.append((a[0] + (b[0] - a[0]) * t + 0.8 * math.sin(k * 0.9), a[1] + (b[1] - a[1]) * t + 0.8 * math.cos(k * 0.7)))
    pts.append(path[-1])
    for run in chunks(pts):
        o.append(line_(run, G[6], 1.0))
    total = sum(math.dist(a, b) for a, b in zip(path, path[1:]))
    for i in range(16):                                           # knots spaced along the thread
        d = total * (i + 0.5) / 16
        for a, b in zip(path, path[1:]):
            seg = math.dist(a, b)
            if d <= seg:
                x, y = a[0] + (b[0] - a[0]) * d / seg, a[1] + (b[1] - a[1]) * d / seg
                break
            d -= seg
        o += dot_shape("circle", x, y, 3.6, p.step_lit(i))
    # the phrase: eight beads on a strand hanging from the maze's exit
    o.append(line_([(350, 40), (350, 46)] + [(350 + 8 * math.sin(k * 0.6), 46 + k * 12) for k in range(9)], G[6], 1.0))
    for k in range(8):
        o += dot_shape("circle", 350 + 8 * math.sin((k + 0.5) * 0.6), 52 + k * 12, 4.4, p.tone_lit(k))
    return o


STYLES = {"p1-labyrinth": labyrinth, "p2-wheels": wheels, "p3-tape": tape, "p4-blocks": blocks, "p5-thread": thread}


def main():
    poses = {
        "rest": Page(),
        "phrase": Page(phrase=0b10110111, root=62, start=0, count=5),
        "phrase-b": Page(phrase=0b01101101, root=57, start=8, count=6, scale=2),
        "dens-0": Page(density=0.0, phrase=0, root=62, start=8, count=7),
        "dens-100": Page(density=1.0, phrase=0xFF, root=62, start=0, count=8),
        "drum": Page(drum=True, phrase=0b11011011, root=60, start=0, count=9),
    }
    for name, fn in STYLES.items():
        d = HERE / name
        d.mkdir(exist_ok=True)
        for pose, p in poses.items():
            (d / f"{pose}.svg").write_text(frame(p, fn(p)), encoding="utf-8")
    cols, P_ = len(poses), 8
    sheet = Image.new("RGB", (P_ + cols * (W + P_), P_ + 18 + len(STYLES) * (H + P_)), (40, 40, 40))
    dr = ImageDraw.Draw(sheet)
    with tempfile.TemporaryDirectory() as tmp:
        for j, pose in enumerate(poses):
            dr.text((P_ + j * (W + P_), P_), pose, fill=(200, 200, 200))
        for i, name in enumerate(STYLES):
            for j, pose in enumerate(poses):
                png = Path(tmp) / f"{name}-{pose}.png"
                subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(HERE / name / f"{pose}.svg"), "-o", str(png)], check=True)
                sheet.paste(Image.open(png).convert("RGB"), (P_ + j * (W + P_), P_ + 18 + i * (H + P_)))
    sheet.save(HERE / "board-pages.png")
    print("wrote", len(STYLES) * len(poses), "frames")


if __name__ == "__main__":
    main()
