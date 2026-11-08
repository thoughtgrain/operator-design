#!/usr/bin/env python3
"""Marble v4, cleaned: the board in front elevation, simplified to one subject.

    python3 screens/marble/passes/01-subject/v4/clean.py

Writes clean.svg beside this file. Same model and defaults as sketch.py
(6 rows -> 7 bins, drop 1/8, bounce 0, major); the helpers and the model are
imported from it, the drawing is new. No text below the header.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from sketch import (ROWS, DROPS, G0, G3, G4, G5, G7,  # noqa: E402
                    Frame, bins)


def marble(F: Frame, x, y, r, edge, glint, sw=1.5, fill=G0):
    """A marble in elevation: a round outline and one short glint arc, upper left."""
    F.circle(x, y, r, fill, edge, sw)
    a0, a1 = math.radians(185), math.radians(265)
    rg = r * 0.6
    pts = [(x + rg * math.cos(a0 + (a1 - a0) * k / 6), y + rg * math.sin(a0 + (a1 - a0) * k / 6))
           for k in range(7)]
    F.ribbon(pts, 1.0, glint)


def clean() -> Frame:
    F = Frame("v4 clean · P13 capture · orthographic elevation")
    cx = 240.0
    B = bins()
    nb = len(B)
    bw = 30.0                              # bin pitch = peg pitch
    left = cx - nb * bw / 2
    top = 58.0                             # first peg row
    row_dy = 13.0
    bins_top = top + ROWS * row_dy + 2     # dividers start just under the last row
    floor0 = 200.0                         # deepest floor (lowest note)
    semi_px = 4.0                          # 1 semitone = 4 px of pipe
    lowest = B[0][1]

    # hopper: a plain funnel in outline, the gate a gap at its throat (drop opens it)
    F.loop([(cx - 34, 28), (cx + 34, 28), (cx + 7, 42), (cx - 7, 42)], G4, 1.5, fill=G0)
    gap = 2.0 + 4.0 * 0.5
    F.line((cx - 14, 45), (cx - gap, 45), 1.5, G4)
    F.line((cx + gap, 45), (cx + 14, 45), 1.5, G4)

    # pegs: a triangle of small round pins, hairline outlines
    for k in range(ROWS):
        y = top + k * row_dy
        for j in range(k + 1):
            F.circle(cx + (j - k / 2) * bw, y, 2.2, G0, G3, 1.0)

    # bins: hairline dividers, each floor a short Line-weight bar at its pitch
    for i in range(nb + 1):
        x = left + i * bw
        F.line((x, bins_top), (x, floor0 + 6), 1.0, G3)
    F.line((left, floor0 + 6), (left + nb * bw, floor0 + 6), 1.0, G3)
    floors = []
    for i, (d, s, p) in enumerate(B):
        fy = floor0 - (s - lowest) * semi_px
        floors.append(fy)
        F.line((left + i * bw + 3, fy), (left + (i + 1) * bw - 3, fy), 1.5, G4)

    # the pile: two bars' worth at the expected counts, two marbles to a layer
    r = 6.0
    hist = [round(p * 2 * DROPS) for _, _, p in B]
    for i in range(nb):
        xc = left + i * bw + bw / 2
        n = hist[i]
        for k in range(n):
            layer, side = divmod(k, 2)
            ox = 0.0 if (n - layer * 2 == 1 and side == 0) else (-6.5 if side == 0 else 6.5)
            yk = floors[i] - 0.75 - r - layer * (2 * r + 0.5)
            marble(F, xc + ox, yk, r, G5, G3)

    # the one marble in flight, solid and brightest: through the gap in the third
    # row, about to strike the peg under it (that peg's row decides left or right)
    mr = 5.0
    mx = cx + bw / 2
    my = top + 3 * row_dy - 2.2 - mr - 1.0
    marble(F, mx, my, mr, G7, G0, sw=1.0, fill=G7)
    return F


if __name__ == "__main__":
    out = HERE / "clean.svg"
    out.write_text(clean().svg(), encoding="utf-8")
    print(out)
