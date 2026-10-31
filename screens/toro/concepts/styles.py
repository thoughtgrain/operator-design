#!/usr/bin/env python3
"""Toro reset, round 3: five different visual styles, each driven by toro's sound.

  s1 vector CRT wireframe terrain     s2 halftone print sphere     s3 sumi-e ink ensō
  s4 isometric blocks                 s5 Bauhaus composition

Rest, cutoff 0, cutoff 100, fold 100 and playing at 1:1, grey only.

    python3 screens/toro/concepts/styles.py
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


def shape(pts, color, x=0.0, y=0.0):
    return f'<path transform="matrix(1 0 0 1 {f(x)} {f(y)})" d="{poly(pts)}" fill="{color}" stroke="none"/>'


def stroke(pts, color, w, close=False):
    d = poly(pts) if close else "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts)
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linejoin="round"/>'


def frame(v, body):
    return "\n".join(['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
                      '<rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>'] + body + g.header(v) + ["</svg>"])


def kink(a):
    return 0.4 * a + 0.6 * a ** 3


# s1 · vector CRT wireframe terrain ------------------------------------------------------------------------------------
def crt(v, playing=False):
    o = []
    rows, cols = 12, 44
    gain = 1 + 7 * v["fold"]
    ratio = 1 + 0.5 * v["spread"]
    horizon = 92
    o.append(shape(ribbon([(0, horizon), (480, horizon)], 1.0), G[2]))
    for i in reversed(range(rows)):                               # far → near, each ridge hides what's behind it
        t = i / (rows - 1)
        p = 1 / (1 + 3.2 * t)
        y0 = horizon + 122 * p
        pts = []
        for k in range(cols):
            u = k / (cols - 1)
            x = 240 + (u - 0.5) * 980 * p
            phase = i * 0.55 + kink(v["aphx"]) * 2 * math.sin(i * 1.7)
            low = math.sin(2 * math.pi * (1.3 * u) + phase) + 0.5 * math.sin(2 * math.pi * 1.3 * ratio * u + phase * 1.3)
            detail = v["cutoff"] * (0.55 * math.sin(2 * math.pi * 6.1 * u + phase * 2) + 0.3 * math.sin(2 * math.pi * 11.3 * u + phase))
            hraw = (low * 0.6 + detail) * (1 + 0.9 * v["res"] * math.exp(-((u - 0.5) * 7) ** 2))
            h = fold_signal(gain * hraw * 0.8) if v["fold"] > 0.02 else max(-1, min(1, hraw * 0.8))
            h = max(-1, min(1 - 0.5 * v["drive"], h))
            h += v["noise"] * 0.25 * (random.Random(i * 99 + k).random() - 0.5)
            pts.append((x, y0 - (16 + 22 * (1.2 if playing and i < 3 else 1)) * p * h * 1.6))
        o.append(shape(pts + [(pts[-1][0], 222), (pts[0][0], 222)], G[0]))
        o.append(stroke(pts, grey((2 + 5 * (1 - t) ** 1.4) / 7), 1.5 if i < 4 else 1.2))
    return frame(v, o)


# s2 · halftone print sphere -------------------------------------------------------------------------------------------
def halftone(v, playing=False):
    o = []
    cx, cy, R, step = 240, 128, 80, 11
    gain = 1 + 7 * v["fold"]
    la = math.radians(200 - 160 * v["cutoff"])                     # light swings from behind to the front
    light = (math.cos(la) * 0.8, -0.55, math.sin(la))
    ln = math.sqrt(sum(c * c for c in light)); light = tuple(c / ln for c in light)
    light2 = (0.9, 0.2, 0.3)
    jit = kink(v["aphx"])
    rnd = random.Random(7)
    for j in range(-8, 9):
        for i in range(-8, 9):
            x, y = cx + i * step + (step / 2 if j % 2 else 0), cy + j * step * 0.87
            dx, dy = (x - cx) / R, (y - cy) / R
            if dx * dx + dy * dy > 1:
                continue
            nz = math.sqrt(1 - dx * dx - dy * dy)
            b = max(0.0, dx * light[0] + dy * light[1] + nz * light[2])
            b += v["spread"] * 0.6 * max(0.0, dx * light2[0] + dy * light2[1] + nz * light2[2])
            b += v["res"] * 0.9 * max(0.0, 1 - nz * 2.6)            # rim light
            b = min(1.0, b)
            if v["fold"] > 0.02:
                b = 0.5 + 0.5 * fold_signal(gain * (2 * b - 1))
            b = min(1.0, b * (1 + 0.6 * v["drive"]) + (0.15 if playing else 0))
            b += v["noise"] * 0.3 * (rnd.random() - 0.5)
            r = max(0.0, 0.6 + 5.0 * b)
            if r < 1.6:
                continue
            px, py = x + jit * 3 * (rnd.random() - 0.5), y + jit * 3 * (rnd.random() - 0.5)
            sq = v["shape"]
            pts = dot(r, 12) if sq < 0.5 else [(-r * 0.9, -r * 0.9), (r * 0.9, -r * 0.9), (r * 0.9, r * 0.9), (-r * 0.9, r * 0.9)]
            o.append(shape(pts, G[7] if b > 0.85 else G[6] if b > 0.55 else G[5], px, py))
    return frame(v, o)


# s3 · sumi-e ink ensō ---------------------------------------------------------------------------------------------------
def enso(v, playing=False):
    o = []
    cx, cy = 240, 130
    dabs = 96
    sweep = 2 * math.pi * (0.86 + 0.45 * v["fold"])               # fold carries the stroke past its start and inward
    load = 3.5 + 8 * v["cutoff"]
    rnd = random.Random(11)
    wob = kink(v["aphx"])
    def stroke_at(r0, scale_w, level_shift, phase=-math.pi * 0.62):
        out = []
        for k in range(dabs):
            s = k / (dabs - 1)
            th = phase + sweep * s
            r = r0 * (1 - 0.18 * v["fold"] * max(0.0, (sweep * s - 2 * math.pi) / (0.45 * 2 * math.pi + 1e-6)))
            r *= 1 + wob * 0.05 * math.sin(9 * s * math.pi + 1.3)
            x, y = cx + math.cos(th) * r, cy + math.sin(th) * r * 0.92
            press = (1 - s) ** (0.5 + 1.5 * (1 - v["shape"])) * 0.85 + 0.15
            w = load * press * scale_w * (1.15 if playing else 1)
            if v["drive"] > 0.05 and (k % 5 in (1, 3)) and s > 0.35:
                continue                                           # dry brush: the stroke breaks into streaks
            tangent = math.degrees(th) + 90
            ell = [(math.cos(a) * w, math.sin(a) * w * 0.5) for a in [i * math.pi / 6 for i in range(12)]]
            level = 6 if s < 0.6 else 5
            out.append(shape(rot(ell, tangent), G[min(7, level + level_shift)], x, y))
        return out
    if v["spread"] > 0.02:
        o += stroke_at(66 * (1 + 0.35 * v["spread"]), 0.45, -3, phase=-math.pi * 0.62 + 0.4 * v["spread"])
    o += stroke_at(66, 1.0, 1 if playing else 0)
    for k in range(int(3 + 18 * max(v["noise"], v["res"] * 0.7))):  # splatter, flung off the tail
        a = -math.pi * 0.62 + sweep + rnd.uniform(-0.4, 0.2)
        d = 66 + rnd.uniform(4, 26)
        o.append(shape(dot(rnd.uniform(1.6, 2.6), 8), G[5], cx + math.cos(a) * d, cy + math.sin(a) * d * 0.92))
    return frame(v, o)


# s4 · isometric blocks ------------------------------------------------------------------------------------------------
def iso(v, playing=False):
    o = []
    nx, ny, s = 12, 8, 13
    gain = 1 + 7 * v["fold"]
    ratio = 1 + 0.5 * v["spread"]
    rnd = random.Random(4)
    cells = []
    for i in range(nx):
        for j in range(ny):
            u, w = i / (nx - 1), j / (ny - 1)
            low = math.sin(2 * math.pi * (0.8 * u + 0.4 * w)) + 0.6 * math.sin(2 * math.pi * ratio * (0.6 * w - 0.5 * u) + 1)
            detail = v["cutoff"] * 0.7 * math.sin(2 * math.pi * (3.3 * u + 2.1 * w) + 0.5)
            hraw = 0.45 * low + detail
            hv = fold_signal(gain * hraw) if v["fold"] > 0.02 else max(-1, min(1, hraw))
            hv = min(1 - 0.6 * v["drive"], hv) + v["noise"] * 0.5 * (rnd.random() - 0.5)
            hv += kink(v["aphx"]) * 0.4 * math.sin(i * 2.1 + j * 1.3)
            h = 10 + 22 * (hv + 1) / 2 * (1.15 if playing else 1)
            cells.append((i + j, i, j, h))
    for _, i, j, h in sorted(cells):
        x = 240 + (i - j) * s
        y = 70 + (i + j) * s * 0.5
        top = [(x, y - h), (x + s, y + s * 0.5 - h), (x, y + s - h), (x - s, y + s * 0.5 - h)]
        left = [(x - s, y + s * 0.5 - h), (x, y + s - h), (x, y + s), (x - s, y + s * 0.5)]
        right = [(x, y + s - h), (x + s, y + s * 0.5 - h), (x + s, y + s * 0.5), (x, y + s)]
        hi = v["res"] > 0.05 and j == round((ny - 1) * v["res"])
        o.append(shape(left, G[3])); o.append(shape(right, G[1]))
        o.append(shape(top, G[7] if hi else G[5 if h > 24 else 4]))
    return frame(v, o)


# s5 · Bauhaus composition ---------------------------------------------------------------------------------------------
def bauhaus(v, playing=False):
    o = []
    jit = kink(v["aphx"])
    # stripes in a square: fold folds their spacing
    gain = 1 + 7 * v["fold"]
    n = 4 + round(10 * v["fold"])
    for k in range(n):
        u = k / max(1, n - 1)
        x = 60 + 110 * (0.5 + 0.5 * fold_signal(gain * (u - 0.5))) if v["fold"] > 0.02 else 60 + 110 * u
        o.append(shape([(x, 60), (x + 4, 60), (x + 4, 206), (x, 206)], G[3]))
    # the big circle: cutoff
    r = 22 + 62 * v["cutoff"] * (1.08 if playing else 1)
    o.append(shape(dot(r, 48), G[6], 300, 128))
    # drive: a thick arc hugging the circle
    if v["drive"] > 0.02:
        arc = [(300 + math.cos(a) * (r + 8), 128 + math.sin(a) * (r + 8)) for a in [math.radians(200 + 100 * k / 15) for k in range(16)]]
        o.append(shape(ribbon(arc, 3 + 9 * v["drive"]), G[4]))
    # spread: two bars, separating in angle
    for k, (shade, sign) in enumerate(((G[7], 1), (G[4], -1))):
        if k == 1 and v["spread"] < 0.02:
            continue
        ang = -18 + sign * 34 * v["spread"] * (1 if k else 0.4) + jit * 8 * (k - 0.5)
        o.append(shape(rot([(-150, -4), (150, -4), (150, 4), (-150, 4)], ang), shade, 236, 150 - 14 * k))
    # shape: the wedge, saw (right triangle) to triangle (isosceles)
    sx = 410
    apex = sx - 26 + 26 * v["shape"]
    o.append(shape([(sx - 26, 206), (sx + 26, 206), (apex, 132)], G[5]))
    # res: a small dot riding the circle's edge
    if v["res"] > 0.05:
        a = math.radians(-60 + 120 * v["res"])
        o.append(shape(dot(5 + 4 * v["res"], 16), G[7], 300 + math.cos(a) * (r + 18), 128 + math.sin(a) * (r + 18)))
    rnd = random.Random(9)
    for k in range(int(30 * v["noise"])):
        o.append(shape([(-2, -2), (2, -2), (2, 2), (-2, 2)], G[4], rnd.uniform(20, 460), rnd.uniform(48, 210)))
    return frame(v, o)


STYLES = {"s1-crt": crt, "s2-halftone": halftone, "s3-enso": enso, "s4-iso": iso, "s5-bauhaus": bauhaus}


def main():
    D = dict(g.DEFAULTS)
    poses = {"rest": (D, False), "cutoff-000": (dict(D, cutoff=0), False), "cutoff-100": (dict(D, cutoff=1), False),
             "fold-100": (dict(D, fold=1), False), "playing": (D, True)}
    for name, fn in STYLES.items():
        d = HERE / name
        d.mkdir(exist_ok=True)
        for pose, (vals, playing) in poses.items():
            (d / f"{pose}.svg").write_text(fn(vals, playing), encoding="utf-8")
    print("wrote", len(STYLES) * len(poses), "frames")


if __name__ == "__main__":
    main()
