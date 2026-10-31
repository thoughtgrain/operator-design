#!/usr/bin/env python3
"""Toro reset, round 4: the five styles from round 3, each now drawing toro's own signal.

toro_wave() is a small model of the engine (engine.cpp): two saw→triangle oscillators (osc 2 at the spread
ratio) plus noise, a 1–8× wavefolder, a resonant 2-pole low-pass, soft-clip drive, and APHX per-key drift.
Every style draws its output, so what you see is toro folding, filtering, clipping and drifting.

  c1 CRT waterfall of the waveform        c2 halftone oscillogram      c3 ensō: the wave wrapped into a brush circle
  c4 isometric keys: APHX drift per key   c5 Bauhaus signal chain

    python3 screens/toro/concepts/character.py
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import gen_frames as g  # noqa: E402

G, f, poly, dot, ribbon, annulus, rot, fold_signal, grey = g.G, g.f, g.poly, g.dot, g.ribbon, g.annulus, g.rot, g.fold_signal, g.grey


def kink(a):
    return 0.4 * a + 0.6 * a ** 3


def key_offsets(key: int, aphx: float):
    """APHX: each key gets its own fixed offsets to tuning, cutoff, fold and shape (a hash of the key)"""
    k = kink(aphx)
    h = lambda s: g.hrand(key + 1, s) - 0.5
    return {"tune": k * 0.06 * h(1), "cutoff": k * 0.5 * h(2), "fold": k * 0.6 * h(3), "shape": k * 0.8 * h(4)}


def toro_wave(v, n=64, cycles=2.0, phase=0.0, key=0):
    """n samples of toro's steady-state output over `cycles` periods of osc 1, in [-1, 1]"""
    off = key_offsets(key, v["aphx"])
    ratio = (1 + 0.5 * v["spread"]) * (1 + off["tune"])
    shape_v = min(1.0, max(0.0, v["shape"] + off["shape"]))
    gain = 1 + 7 * min(1.0, max(0.0, v["fold"] + off["fold"]))
    cut = min(1.0, max(0.0, v["cutoff"] + off["cutoff"]))
    fc = 0.045 + 0.55 * cut ** 2                                   # squared response, like the engine; dark but never silent
    damp = 2.0 - 1.85 * v["res"]
    drive = 1 + 3 * v["drive"]
    over = 8
    m = n * over
    rnd = random.Random(17 + key)
    low = band = 0.0
    out = []
    for pass_ in range(3):                                         # run three times so the filter settles
        for t in range(m):
            p1 = (t * cycles / m + phase) % 1
            p2 = (t * cycles / m * ratio + phase * 1.3) % 1
            o = lambda p: (2 * p - 1) * (1 - shape_v) + (1 - 4 * abs(p - 0.5)) * shape_v
            s = 0.5 * (o(p1) + o(p2)) + v["noise"] * 0.45 * (rnd.random() - 0.5)
            x = fold_signal(gain * s * 0.95)
            low += fc * band
            high = x - low - damp * band
            band += fc * high
            y = math.tanh(low * drive * 1.15) / math.tanh(drive)
            if pass_ == 2 and t % over == 0:
                out.append(max(-1.2, min(1.2, y)))
    return out


def shape(pts, color, x=0.0, y=0.0):
    return f'<path transform="matrix(1 0 0 1 {f(x)} {f(y)})" d="{poly(pts)}" fill="{color}" stroke="none"/>'


def stroke(pts, color, w):
    return f'<path d="M {" L ".join(f"{f(x)} {f(y)}" for x, y in pts)}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linejoin="round"/>'


def frame(v, body):
    return "\n".join(['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
                      '<rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>'] + body + g.header(v) + ["</svg>"])


# c1 · CRT waterfall: cycles of the real waveform receding; a note charges them forward --------------------------------
def crt(v, playing=False):
    o = []
    rows, horizon = 12, 90
    o.append(shape(ribbon([(0, horizon), (480, horizon)], 1.0), G[2]))
    advance = 0.35 if playing else 0.0
    for i in reversed(range(rows)):
        t = max(0.0, (i - advance)) / (rows - 1)
        p = 1 / (1 + 3.2 * t)
        y0 = horizon + 124 * p
        w = toro_wave(v, n=48, cycles=2, phase=i * 0.07, key=i)
        pts = [(240 + (k / (len(w) - 1) - 0.5) * 900 * p, y0 - 34 * p * w[k] * (1.25 if playing and i < 3 else 1)) for k in range(len(w))]
        o.append(shape(pts + [(pts[-1][0], 222), (pts[0][0], 222)], G[0]))
        o.append(stroke(pts, grey((2 + 5 * (1 - t) ** 1.4) / 7), 1.6 if i < 4 else 1.2))
    return frame(v, o)


# c2 · halftone oscillogram: the waveform printed as dots, densest at its peaks ----------------------------------------
def halftone(v, playing=False):
    o = []
    cols, step, base = 40, 11, 130
    w = toro_wave(v, n=cols, cycles=2)
    amp = 70 * (1.08 if playing else 1)
    for c in range(cols):
        x = 26 + c * step
        top = base - amp * w[c]
        lo, hi = sorted((base, top))
        y = base
        k = 0
        rows = int(abs(top - base) // 9) + 1
        for r in range(rows):
            yy = base + (r * 9 if top > base else -r * 9)
            frac = (r + 1) / rows                                   # dots grow toward the wave's edge
            rad = 1.6 + 3.2 * frac ** 0.8
            if (c + r) % 2 and v["shape"] < 0.5:
                pass
            o.append(shape(dot(rad, 12), G[7] if frac > 0.85 else G[6] if frac > 0.5 else G[5], x + (4.5 if r % 2 else 0), yy))
    o.append(shape(ribbon([(16, base), (464, base)], 1.0), G[3]))
    return frame(v, o)


# c3 · ensō: toro's wave wrapped around the brush circle ---------------------------------------------------------------
def enso(v, playing=False):
    o = []
    cx, cy, r0 = 240, 130, 62
    dabs = 120
    w = toro_wave(v, n=dabs, cycles=5)
    load = 4.2 + 3.5 * v["drive"]
    start = -math.pi * 0.62
    sweep = 2 * math.pi * 0.9
    for k in range(dabs):
        s = k / (dabs - 1)
        th = start + sweep * s
        r = r0 + 15 * w[k] * (1.15 if playing else 1)
        x, y = cx + math.cos(th) * r, cy + math.sin(th) * r * 0.92
        press = (1 - s) ** 0.7 * 0.85 + 0.15
        width = load * press
        ell = [(math.cos(a) * width, math.sin(a) * width * 0.5) for a in [i * math.pi / 6 for i in range(12)]]
        o.append(shape(rot(ell, math.degrees(th) + 90), G[6] if s < 0.65 else G[5], x, y))
    rnd = random.Random(3)
    for k in range(3 + int(14 * v["noise"])):
        a = start + sweep + rnd.uniform(-0.3, 0.25)
        d = r0 + rnd.uniform(6, 24)
        o.append(shape(dot(rnd.uniform(1.6, 2.4), 8), G[5], cx + math.cos(a) * d, cy + math.sin(a) * d * 0.92))
    return frame(v, o)


# c4 · isometric keys: each row is one key's waveform; APHX drifts the rows apart ---------------------------------------
def iso(v, playing=False):
    o = []
    nx, ny, s = 14, 8, 12
    cells = []
    for j in range(ny):
        w = toro_wave(v, n=nx, cycles=1, key=j)
        for i in range(nx):
            h = 10 + 26 * (w[i] + 1) / 2 * (1.15 if playing else 1)
            cells.append((i + j, i, j, h))
    for _, i, j, h in sorted(cells):
        x = 240 + (i - j) * s
        y = 64 + (i + j) * s * 0.5
        top = [(x, y - h), (x + s, y + s * 0.5 - h), (x, y + s - h), (x - s, y + s * 0.5 - h)]
        left = [(x - s, y + s * 0.5 - h), (x, y + s - h), (x, y + s), (x - s, y + s * 0.5)]
        right = [(x, y + s - h), (x + s, y + s * 0.5 - h), (x + s, y + s * 0.5), (x, y + s)]
        o.append(shape(left, G[3])); o.append(shape(right, G[1]))
        o.append(shape(top, G[6] if h > 30 else G[5] if h > 20 else G[4]))
    return frame(v, o)


# c5 · Bauhaus signal chain: oscillators → folder → filter → drive, left to right ---------------------------------------
def bauhaus(v, playing=False):
    o = []
    push = 6 if playing else 0
    o.append(shape(ribbon([(20, 132), (460, 132)], 1.2), G[3]))      # the signal line
    ratio = 1 + 0.5 * v["spread"]
    o.append(shape(dot(24, 40), G[6], 64 + push, 104))                # osc 1
    o.append(shape(dot(24 / ratio ** 0.5, 40), G[4], 64 + push + 10 + 46 * v["spread"], 162))   # osc 2
    gain = 1 + 7 * v["fold"]
    n = 4 + round(10 * v["fold"])                                     # the folder: stripes fold their spacing
    for k in range(n):
        u = k / max(1, n - 1)
        x = 140 + push + 80 * (0.5 + 0.5 * fold_signal(gain * (u - 0.5)))
        o.append(shape([(x, 62), (x + 4, 62), (x + 4, 202), (x, 202)], G[3]))
    r = 18 + 50 * v["cutoff"] ** 1.2 * (1.06 if playing else 1)       # the filter: a circle that opens
    fx = 330 + push
    o.append(shape(dot(r, 48), G[6], fx, 132))
    if v["res"] > 0.05:
        a = math.radians(-50 + 100 * v["res"])
        o.append(shape(dot(4 + 4 * v["res"], 16), G[7], fx + math.cos(a) * (r + 14), 132 + math.sin(a) * (r + 14)))
    arc = [(fx + math.cos(a) * (r + 7), 132 + math.sin(a) * (r + 7)) for a in [math.radians(-70 + 140 * k / 15) for k in range(16)]]
    o.append(shape(ribbon(arc, 2 + 10 * v["drive"]), G[4]))           # drive presses on the filter
    sx = 438 + push
    apex = sx - 18 + 18 * v["shape"]                                  # the wedge: saw → triangle
    o.append(shape([(sx - 18, 202), (sx + 18, 202), (apex, 150)], G[5]))
    return frame(v, o)


STYLES = {"c1-crt": crt, "c2-halftone": halftone, "c3-enso": enso, "c4-iso": iso, "c5-bauhaus": bauhaus}


def main():
    D = dict(g.DEFAULTS)
    poses = {"rest": (D, False), "cutoff-000": (dict(D, cutoff=0), False), "cutoff-100": (dict(D, cutoff=1), False),
             "fold-100": (dict(D, fold=1), False), "aphx-100": (dict(D, aphx=1), False), "playing": (D, True)}
    for name, fn in STYLES.items():
        d = HERE / name
        d.mkdir(exist_ok=True)
        for pose, (vals, playing) in poses.items():
            (d / f"{pose}.svg").write_text(fn(vals, playing), encoding="utf-8")
    print("wrote", len(STYLES) * len(poses), "frames")


if __name__ == "__main__":
    main()
