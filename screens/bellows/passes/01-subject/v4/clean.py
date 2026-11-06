#!/usr/bin/env python3
"""Bellows v4 (P3 trace as subject, orthographic elevation), cleaned for today's rules.

    python3 screens/bellows/passes/01-subject/v4/clean.py

Writes clean.svg beside this file. Same elevation as sketch.py's v4 minus the
"wind", "datum" and "reed a elevation" captions; the level mark and the
dimension stay as drawn marks. With the captions gone the drawing sits a
little high, so the datum moves down 10 px to centre it in the body.
There was no grey-filled state to replace: the level mark is already an
outline over black and the ghost wave is a line.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import math  # noqa: E402

from sketch import (Frame, DEFAULTS, reed_wave, HAIR, LINE, SUBJ,  # noqa: E402
                    BRIGHT, G125, G100, G75)


def v4_clean() -> Frame:
    f = Frame()
    press, reed, choir = DEFAULTS["press"], DEFAULTS["reed"], DEFAULTS["choir"]
    x0, x1, datum = 34, 446, 160
    # Ground: datum line and short station ticks below it, as an elevation's ground line.
    f.line([(14, datum), (466, datum)], w=HAIR, colour=G100)
    for i in range(12):
        x = x0 + i * (x1 - x0) / 11
        f.line([(x, datum + 6), (x, datum + 12)], w=HAIR, colour=G75)
    # The wind line: pressure over a held stroke, sagging and recovering. Its height is press.
    wind_h = 30 + 70 * press
    wind = []
    for i in range(33):
        u = i / 32
        sag = 1 - 0.22 * math.sin(math.pi * u) ** 1.5
        wind.append((x0 + u * (x1 - x0), datum - wind_h * sag))
    f.line(wind, w=LINE, colour=G125, bound=True)
    # Level mark on the wind line at the left: a small open triangle, point on the line.
    lx, ly = 22, wind[0][1]
    f.poly([(lx - 5, ly - 8), (lx + 5, ly - 8), (lx, ly - 1)], fill="#000000", stroke=G125, sw=HAIR)
    # The trace: reed wave rectified upward from the datum, as a skyline under the wind line.
    cycles = 9
    pts, ghost = [], []
    k = 240
    for i in range(k + 1):
        u = i / k
        x = x0 + u * (x1 - x0)
        h_env = wind_h * (1 - 0.22 * math.sin(math.pi * u) ** 1.5) * 0.92
        w = reed_wave(cycles * u, reed)
        w2 = reed_wave(cycles * u * (1 + choir * 0.03), reed)
        pts.append((x, datum - h_env * (0.5 + 0.5 * w / 1.25)))
        ghost.append((x, datum - h_env * (0.5 + 0.5 * w2 / 1.25)))
    f.line(ghost[::2], w=LINE, colour=G75, bound=True)
    # Mullions: vertical hairlines from the datum up to the wave, so it stands as a facade.
    for i in range(1, 35):
        j = round(i * k / 35)
        x, y = pts[j]
        if datum - y > 8:
            f.line([(x, datum - 1), (x, y + 3)], w=HAIR, colour=G75)
    f.line(pts[::2], w=SUBJ, colour=BRIGHT, bound=True)
    # Dimension at the right: the height of the wind line at the right edge.
    dx = 458
    ytop = wind[-1][1]
    f.line([(dx, datum), (dx, ytop)], w=HAIR, colour=G125, bound=True)
    f.line([(dx - 4, ytop), (dx + 4, ytop)], w=HAIR, colour=G125, bound=True)
    f.line([(dx - 4, datum), (dx + 4, datum)], w=HAIR, colour=G125)
    return f


if __name__ == "__main__":
    out = HERE / "clean.svg"
    out.write_text(v4_clean().svg("v4 P3 orthographic elevation (clean)"))
    print(out)
