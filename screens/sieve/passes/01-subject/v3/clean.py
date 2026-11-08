#!/usr/bin/env python3
"""Sieve v3 (P3 trace as subject, patent section), cleaned for today's rules.

    python3 screens/sieve/passes/01-subject/v3/clean.py

Writes clean.svg beside this file. Same drawing as sketch.py's v3, minus the
reference numerals, their leader lines and the "fig. 1" caption: the header
names and values every control, so the picture carries no text.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from sketch import (Frame, amp, kept, KEEP, HAIR, SUBJ,  # noqa: E402
                    C_HI, C_MID, C_LOW, C_GND)


def v3_clean() -> Frame:
    fr = Frame()
    X0, X1, cy = 52, 452, 116
    tau = 60 + 900 * KEEP ** 2           # px: ring-out length grows with keep
    A = 46
    # wall in section at the left: outline + 45 degree hatch (section convention)
    wx0, wx1, wy0, wy1 = 34, 46, 58, 176
    fr.shape([(wx0, wy0), (wx1, wy0), (wx1, wy1), (wx0, wy1)], 1.5, C_MID)
    for t in range(int(wy0) + 6, int(wy1) + 8, 6):
        a = (wx0 + 1.5, min(t, wy1 - 1.5)); b = (wx1 - 1.5, t - (wx1 - wx0 - 3))
        if b[1] < wy0 + 1.5:
            b = (wx0 + 1.5 + (t - wy0 - 1.5), wy0 + 1.5)
        if a[1] > wy1 - 1.5:
            continue
        if math.dist(a, b) > 3:
            fr.rib([a, b], HAIR, C_LOW)
    # axis
    fr.rib([(wx1 + 2, cy), (X1 + 6, cy)], HAIR, C_GND)
    # envelope lines (dashed hairline): the keep control's own part
    for s in (-1, 1):
        prev = None
        for i in range(0, 41):
            x = X0 + (X1 - X0) * i / 40
            y = cy + s * (A * math.exp(-(x - X0) / tau) + 6)
            if prev and i % 2 == 1:
                fr.rib([prev, (x, y)], HAIR, C_MID)
            prev = (x, y)
    # the trace: kept harmonics over two fundamental periods, ringing out
    n = 150
    P = (X1 - X0) / 2
    raw = []
    for i in range(n):
        x = X0 + (X1 - X0) * i / (n - 1)
        s = sum(amp(k) * math.sin(2 * math.pi * k * (x - X0) / P) for k in range(1, 9) if kept(k))
        raw.append((x, s))
    peak = max(abs(s) for _, s in raw)
    pts = [(x, cy - A * (s / peak) * math.exp(-(x - X0) / tau)) for x, s in raw]
    for a in range(0, n - 1, 49):
        fr.rib(pts[a:a + 51], SUBJ, C_HI, bind=True)
    return fr


if __name__ == "__main__":
    out = HERE / "clean.svg"
    out.write_text(v3_clean().svg())
    print(out)
