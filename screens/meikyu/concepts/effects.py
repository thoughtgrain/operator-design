#!/usr/bin/env python3
"""meikyu, round 2: five pages about what the player does, not what it is.

Round 1 drew the register (dials, tape, a labyrinth). Brian liked the wheels but found them too literal: the page
should show the player's effect as it changes. So these draw no sequencer at all. Each is an abstract figure whose
24 dots are pieces of the figure itself, and the player's three changes each do something visible to it:
  - Dens decides how much of the figure is there (dots 0..15 lit when their step plays)
  - Crpt rewrites steps between phrases, so pieces of the figure go missing or come back
  - a press lights the phrase (dots 16..23), the figure's accent, wherever a tone sounded
Same ABI as round 1 (24 on/off dots, one text line, the SDK keyboard at y 174) and the same player.cpp mapping.

  e1 shards     a ring broken into sixteen arc shards; the phrase is eight rays fired from its centre
  e2 strata     sixteen long horizontal strata stacked like a cross-section; the phrase is eight vertical seams
  e3 bloom      sixteen petals of a flower in two whorls; the phrase is eight seeds in a spiral at its heart
  e4 interference  sixteen concentric rings, half from each of two centres, so density makes moiré; the phrase
                is eight sparks where the two ring sets cross
  e5 skyline    sixteen towers of fixed heights along a horizon; the phrase is eight windows lit in a row

    python3 effects.py      → e*/<pose>.svg and board-effects.png
"""
from __future__ import annotations

import math
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

import pages as P

HERE = Path(__file__).resolve().parent
W, H = 480, 220
GHOST, LINE, HOT, INK = "#2E2E2E", "#6E6E6E", "#F0F0F0", "#000000"


def f(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def path(pts, stroke, w=1.2, fill="none", close=False):
    d = "M" + " L".join(f"{f(x)},{f(y)}" for x, y in pts) + (" Z" if close else "")
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{w}" stroke-linejoin="round" stroke-linecap="round"/>'


def arc(cx, cy, r, a0, a1, n=12, ry=None):
    ry = r if ry is None else ry
    return [(cx + r * math.cos(a0 + (a1 - a0) * k / n), cy + ry * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]


def piece(pts, lit, w=1.4, close=False, solid=False):
    """one dot: a ghost always drawn (static art) and, when lit, the piece itself on top (the dot node)"""
    o = [path(pts, GHOST, w, INK if solid else "none", close)]
    if lit:
        o.append(path(pts, HOT, w, HOT if solid else "none", close))
    return o


# ---- e1 · shards -------------------------------------------------------------------------------------------------------
def shards(p):
    o, cx, cy = [], 240, 86
    for i in range(16):                                           # A: outer ring, B: inner ring, each eight shards
        r, w = (54, 5.0) if i < 8 else (40, 3.0)
        k = i % 8
        a0 = -math.pi / 2 + 2 * math.pi * k / 8 + 0.07 + (0.2 if i >= 8 else 0)
        o += piece(arc(cx, cy, r, a0, a0 + 2 * math.pi / 8 - 0.14, 10), p.step_lit(i), w)
    for k in range(8):                                            # rays fired from the centre, fanning right
        a = -math.pi / 2 + 2 * math.pi * (k + 0.5) / 8
        o += piece([(cx + 12 * math.cos(a), cy + 12 * math.sin(a)), (cx + 30 * math.cos(a), cy + 30 * math.sin(a))], p.tone_lit(k), 2.0)
    return o


# ---- e2 · strata -------------------------------------------------------------------------------------------------------
def strata(p):
    o = []
    for i in range(16):                                           # long strata, each its own length, A above B
        y = 36 + i * 6.6 + (6 if i >= 8 else 0)
        x0 = 60 + 34 * math.sin(i * 1.7) + 20
        x1 = 420 - 30 * math.cos(i * 2.3) - 10
        o += piece([(x0, y), (x1, y)], p.step_lit(i), 3.2)
    for k in range(8):                                            # seams cutting down through them
        x = 110 + k * 37
        o += piece([(x, 30), (x + 6, 88), (x - 2, 142)], p.tone_lit(k), 1.6)
    return o


# ---- e3 · bloom --------------------------------------------------------------------------------------------------------
def bloom(p):
    o, cx, cy = [], 240, 88
    for i in range(16):
        outer = i < 8
        k = i % 8
        a = -math.pi / 2 + 2 * math.pi * (k + (0 if outer else 0.5)) / 8
        L, Wd = (58, 13) if outer else (34, 9)
        tip = (cx + L * math.cos(a), cy + L * math.sin(a))
        side = lambda s: (cx + L * 0.5 * math.cos(a) + s * Wd * math.cos(a + math.pi / 2), cy + L * 0.5 * math.sin(a) + s * Wd * math.sin(a + math.pi / 2))
        base = (cx + 8 * math.cos(a), cy + 8 * math.sin(a))
        pts = [base, side(1), tip, side(-1)]
        o += piece(pts, p.step_lit(i), 1.3, close=True)
    for k in range(8):                                            # seeds on a small golden-angle spiral
        r, a = 2.2 * math.sqrt(k + 1) * 2.0, k * 2.39996
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        o += piece([(x - 1.8, y), (x, y - 1.8), (x + 1.8, y), (x, y + 1.8)], p.tone_lit(k), 1.0, close=True, solid=True)
    return o


# ---- e4 · interference -------------------------------------------------------------------------------------------------
def interference(p):
    o = []
    c1, c2 = (200, 88), (280, 88)
    for i in range(16):                                           # A's rings round the left centre, B's round the right
        cx, cy = c1 if i < 8 else c2
        r = 10 + 6.6 * (i % 8)
        o += piece(arc(cx, cy, r, 0, 2 * math.pi, 40), p.step_lit(i), 1.2, close=True)
    for k in range(8):                                            # sparks on the line where the two sets cross
        x, y = 240, 88 - 42 + k * 12
        o += piece([(x - 2.4, y), (x, y - 2.4), (x + 2.4, y), (x, y + 2.4)], p.tone_lit(k), 1.0, close=True, solid=True)
    return o


# ---- e5 · skyline ------------------------------------------------------------------------------------------------------
def skyline(p):
    o = []
    hz = 140
    o.append(path([(36, hz), (444, hz)], LINE, 1.0))
    heights = [62, 38, 88, 50, 104, 70, 44, 96, 58, 80, 34, 72, 100, 46, 66, 54]
    for i in range(16):                                           # towers interleaved A, B along the horizon
        x = 52 + i * 24.5
        h = heights[i]
        o += piece([(x - 8, hz), (x - 8, hz - h), (x + 8, hz - h), (x + 8, hz)], p.step_lit(i), 1.3)
    for k in range(8):                                            # windows lit in a row across the skyline
        x = 52 + (2 * k + 1) * 24.5
        o += piece([(x - 3, 116), (x + 3, 116), (x + 3, 124), (x - 3, 124)], p.tone_lit(k), 1.0, close=True, solid=True)
    return o


STYLES = {"e1-shards": shards, "e2-strata": strata, "e3-bloom": bloom, "e4-interference": interference, "e5-skyline": skyline}


def poses():
    before = P.Page(corrupt=0.8, phrase=0b11011011, root=60, start=0, count=9)
    after = P.Page(corrupt=0.8, phrase=0b10011110, root=60, start=8, count=10)
    for i, w in ((1, 92), (4, 12), (10, 85), (13, 3)):
        after.weights[i] = w
    return {
        "rest": P.Page(),
        "phrase": P.Page(phrase=0b10110111, root=62, start=0, count=5),
        "dens-0": P.Page(density=0.0, phrase=0, root=62, start=8, count=7),
        "dens-100": P.Page(density=1.0, phrase=0xFF, root=62, start=0, count=8),
        "crpt-before": before,
        "crpt-after": after,
    }


def main():
    ps = poses()
    for name, fn in STYLES.items():
        d = HERE / name
        d.mkdir(exist_ok=True)
        for pose, p in ps.items():
            (d / f"{pose}.svg").write_text(P.frame(p, fn(p)), encoding="utf-8")
    pad = 8
    sheet = Image.new("RGB", (pad + len(ps) * (W + pad), pad + 18 + len(STYLES) * (H + pad)), (40, 40, 40))
    dr = ImageDraw.Draw(sheet)
    with tempfile.TemporaryDirectory() as tmp:
        for j, pose in enumerate(ps):
            dr.text((pad + j * (W + pad), pad), pose, fill=(200, 200, 200))
        for i, name in enumerate(STYLES):
            for j, pose in enumerate(ps):
                png = Path(tmp) / f"{name}-{pose}.png"
                subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(HERE / name / f"{pose}.svg"), "-o", str(png)], check=True)
                sheet.paste(Image.open(png).convert("RGB"), (pad + j * (W + pad), pad + 18 + i * (H + pad)))
    sheet.save(HERE / "board-effects.png")
    print("wrote", len(STYLES) * len(ps), "frames")


if __name__ == "__main__":
    main()
