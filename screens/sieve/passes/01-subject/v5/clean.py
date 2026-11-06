#!/usr/bin/env python3
"""Sieve v5 (P11 instrument stack, star atlas), cleaned for today's rules.

    python3 screens/sieve/passes/01-subject/v5/clean.py

Writes clean.svg beside this file. Same plate as sketch.py's v5, minus the
star numbers under the kept stars and the "fistula" / "h1-h12" captions. The
kept partials are still told apart without numbers: they're larger, brightest
and joined by the figure line.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from sketch import (Frame, amp, kept, KEEP, MIX, HAIR, LINE,  # noqa: E402
                    C_HI, C_3, C_MID, C_LOW, C_GND, C_FILL)


def v5_clean() -> Frame:
    fr = Frame()
    n = 12
    X0, X1, mouth = 70, 420, 150
    xs = [X0 + (X1 - X0) * i / (n - 1) for i in range(n)]
    # atlas ground: two declination arcs and the graduated border, at ground grey
    for dec in (66, 186):
        pts = [(x, dec + 0.00045 * (x - 245) ** 2 * (1 if dec < 100 else -1)) for x in range(36, 456, 12)]
        fr.rib(pts, HAIR, C_FILL)
    for x in xs:
        fr.rib([(x, 206), (x, 211)], HAIR, C_LOW)
    fr.rib([(X0 - 14, 211), (X1 + 14, 211)], HAIR, C_GND)
    # figure lines: pipe outlines (body above the mouth, foot below)
    for i, x in enumerate(xs):
        k = i + 1
        L = 104 / k ** 0.72
        w = 6.5 - 2.6 * i / (n - 1)
        top = mouth - 6 - L
        fr.rib([(x - w, mouth - 4), (x - w, top), (x + w, top), (x + w, mouth - 4)], HAIR, C_GND)
        fr.rib([(x - w, mouth + 4), (x - 1.5, mouth + 22), (x + 1.5, mouth + 22), (x + w, mouth + 4)], HAIR, C_GND)
    # the figure line through the kept stars (constellation)
    kp = [(xs[i], mouth) for i in range(n) if kept(i + 1)]
    for a, b in zip(kp, kp[1:]):
        d = math.dist(a, b)
        ux, uy = (b[0] - a[0]) / d, (b[1] - a[1]) / d
        fr.rib([(a[0] + ux * 7, a[1] + uy * 7), (b[0] - ux * 7, b[1] - uy * 7)], LINE, C_3)
    # stars at the mouths: magnitude by amplitude; kept stars bright and large
    for i, x in enumerate(xs):
        k = i + 1
        if kept(k):
            fr.dot(x, mouth, (2.4 + 3.2 * amp(k)) * (0.8 + 0.4 * KEEP), C_HI, bind=True)
        else:
            fr.dot(x, mouth, 1.6 + 0.8 * (1 - MIX) + 0.6 * amp(k), C_MID, bind=True)
    return fr


if __name__ == "__main__":
    out = HERE / "clean.svg"
    out.write_text(v5_clean().svg())
    print(out)
