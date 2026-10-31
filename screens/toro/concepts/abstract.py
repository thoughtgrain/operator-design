#!/usr/bin/env python3
"""Toro reset, round 2: five abstract concepts in the spirit of the stock OP-XY engines.

Language for all five: bold geometry, solid fills from the stepped grey ramp (the header's own motif),
few elements, lots of black, no illustration and no labels. Rest, fold 100, cutoff 100 and playing at 1:1.

    python3 screens/toro/concepts/abstract.py
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
TOP, BOT = 44, 214


def shape(pts, color, x=0.0, y=0.0):
    return f'<path transform="matrix(1 0 0 1 {f(x)} {f(y)})" d="{poly(pts)}" fill="{color}" stroke="none"/>'


def rect(w, h):
    return [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]


def open_frame(v):
    return ['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
            '<rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>']


def close_frame(o, v):
    return "\n".join(o + g.header(v) + ["</svg>"])


def wave(u, shape_v):
    """one cycle of saw → triangle, u in [0, 1)"""
    saw = 2 * u - 1
    tri = 1 - 4 * abs(u - 0.5)
    return saw * (1 - shape_v) + tri * shape_v


# 1 · fold strip ------------------------------------------------------------------------------------------------------
def fold_strip(v, playing=False):
    o = open_frame(v)
    x0, x1 = 44, 436
    creases = 2 + round(14 * v["fold"])
    squeeze = 0.86 if playing else 1.0
    def strip(cy, n, thick, depth, bright, offset=0.0):
        xs = [240 + (x0 + (x1 - x0) * i / n - 240) * squeeze for i in range(n + 1)]
        ys = []
        for i in range(n + 1):
            u = (i / n + offset) % 1
            asym = wave(u, v["shape"]) if v["shape"] < 0.99 else 0
            ys.append(cy + depth * (1 if i % 2 else -1) * (0.7 + 0.3 * abs(asym)))
        out = []
        for i in range(n):
            a, b = (xs[i], ys[i]), (xs[i + 1], ys[i + 1])
            facing = (b[1] - a[1]) < 0                              # faces tilting up catch the light
            lit_edge = x0 + (x1 - x0) * v["cutoff"]
            in_light = (a[0] + b[0]) / 2 < lit_edge
            level = (5 if facing else 3) if in_light else (2 if facing else 1)
            level = min(7, level + bright)
            t = thick / 2
            out.append(shape([(a[0], a[1] - t), (b[0], b[1] - t), (b[0], b[1] + t), (a[0], a[1] + t)], G[level]))
            if in_light and facing and v["res"] > 0.05 and abs((a[0] + b[0]) / 2 - lit_edge) < 60:
                out.append(shape(ribbon([(b[0], b[1] - t), (b[0], b[1] + t)], 1.6), grey((4 + 3 * v["res"]) / 7)))
        return out
    thick = 34 + 26 * v["drive"]
    depth = 6 + 22 * v["fold"]
    if v["spread"] > 0.02:
        o += strip(150, max(2, round(creases * (1 + 0.5 * v["spread"]))), thick * 0.55, depth * 0.6, 0, offset=0.13)
    o += strip(122 - 10 * v["spread"], creases, thick, depth, 1 if playing else 0)
    rnd = random.Random(1)
    for k in range(int(60 * v["noise"])):
        o.append(shape(dot(1.6, 6), G[4], rnd.uniform(44, 436), rnd.uniform(70, 180)))
    return close_frame(o, v)


# 2 · moiré rings ------------------------------------------------------------------------------------------------------
def moire(v, playing=False):
    o = open_frame(v)
    cy = 128
    sep = 6 + 70 * v["spread"]
    c1, c2 = (240 - sep / 2, cy), (240 + sep / 2, cy)
    rings = 4 + round(9 * v["cutoff"])
    gain = 1 + 7 * v["fold"]
    for center, color, width_k in ((c1, G[6], 1.0), (c2, G[4], 0.85)):
        for k in range(1, rings + 1):
            u = k / 13
            r = 82 * (0.5 + 0.5 * fold_signal(gain * (2 * u - 1))) if v["fold"] > 0.02 else 82 * u
            r = max(3.5, r)
            duty = 0.25 + 0.45 * (1 - v["shape"]) * (k % 2) + 0.25 * v["shape"]
            w = (1.6 + 4.2 * duty + 3 * v["drive"]) * width_k
            col = G[7] if (v["res"] > 0.05 and k == rings) or playing and k == 1 else color
            if r + w / 2 < 86:                                      # stagger each ring's seam so they never line up
                o.append(shape(rot(annulus(r, w, 31, 0.8), 137.5 * k + (40 if color == G[4] else 0)), col, *center))
    o.append(shape(dot(3.2, 12), G[7], *c1))
    rnd = random.Random(2)
    for k in range(int(50 * v["noise"])):
        o.append(shape(dot(1.6, 6), G[3], rnd.uniform(120, 360), rnd.uniform(48, 210)))
    return close_frame(o, v)


# 3 · field lines ------------------------------------------------------------------------------------------------------
def field(v, playing=False):
    o = open_frame(v)
    sep = 50 + 110 * v["spread"]
    p1, p2 = (240 - sep / 2, 130), (240 + sep / 2, 130)
    gain = 1 + 7 * v["fold"]
    length = 6 + 16 * v["cutoff"]
    jit = 0.4 * v["aphx"] + 0.6 * v["aphx"] ** 3
    rnd = random.Random(3)
    for row in range(7):
        for col in range(17):
            x, y = 24 + col * 27, 56 + row * 25
            vx = vy = 0.0
            for (px, py), q in ((p1, 1), (p2, -1)):
                dx, dy = x - px, y - py
                d2 = dx * dx + dy * dy + 40
                vx += q * dx / d2 ** 1.5 * 4000
                vy += q * dy / d2 ** 1.5 * 4000
            ang = math.atan2(vy, vx)
            ang = math.pi * fold_signal(gain * ang / math.pi) if v["fold"] > 0.02 else ang
            ang += jit * (rnd.random() - 0.5) * 1.6 + v["noise"] * (rnd.random() - 0.5) * 0.9
            strength = min(1.0, math.hypot(vx, vy) / 2.2)
            level = 2 + round(4 * strength)
            if playing and strength > 0.6:
                level = 7
            w = 2.2 + 2.0 * v["drive"]
            tick = [(-length / 2, -w / 2), (length / 2, -w / 2 * (1 - 0.6 * v["shape"])), (length / 2, w / 2 * (1 - 0.6 * v["shape"])), (-length / 2, w / 2)]
            o.append(shape(rot(tick, math.degrees(ang)), G[level], x, y))
    for p in (p1, p2):
        o.append(shape(dot(5, 16), G[7], *p))
    if v["res"] > 0.05:
        o.append(shape(annulus(16 + 30 * v["res"], 1.8, 31), grey((2 + 4 * v["res"]) / 7), *p1))
    return close_frame(o, v)


# 4 · louvres ----------------------------------------------------------------------------------------------------------
def louvres(v, playing=False):
    o = open_frame(v)
    cols, rows = 8, 10
    tw, th = 44, 15
    gain = 1 + 7 * v["fold"]
    rnd = random.Random(4)
    jit = 0.4 * v["aphx"] + 0.6 * v["aphx"] ** 3
    for c in range(cols):
        for r in range(rows):
            x, y = 70 + c * 48, 56 + r * 16
            u = c / (cols - 1)
            side = 1 + 0.5 * v["spread"] if c >= cols // 2 else 1.0
            openness = v["cutoff"] * (0.55 + 0.45 * (0.5 + 0.5 * wave(u, v["shape"]))) * side
            direction = fold_signal(gain * (r / (rows - 1) - 0.5) * 2) if v["fold"] > 0.02 else 1.0
            ang = 78 * min(1.0, openness) * direction + jit * 30 * (rnd.random() - 0.5)
            if playing:
                ang *= 1.12
            face = math.cos(math.radians(ang))
            level = 1 + round(5 * abs(math.sin(math.radians(ang)))) + round(2 * v["drive"])
            if v["res"] > 0.05 and c == round((cols - 1) * v["res"]):
                level += 2
            o.append(shape(rot(rect(tw, max(3.2, th * abs(face))), ang * 0.15), G[min(7, level)], x, y))
    return close_frame(o, v)


# 5 · card fan ---------------------------------------------------------------------------------------------------------
def card_fan(v, playing=False):
    o = open_frame(v)
    n = 16
    pivot = (240, 212)
    spread_deg = 10 + 150 * v["cutoff"]
    gain = 1 + 7 * v["fold"]
    jit = 0.4 * v["aphx"] + 0.6 * v["aphx"] ** 3
    rnd = random.Random(5)
    w, h = 36, 140 + 20 * v["drive"]
    for i in range(n):
        u = i / (n - 1)
        side = 1 + 0.5 * v["spread"] if u > 0.5 else 1.0
        base = (u - 0.5) * spread_deg * side
        pleat = fold_signal(gain * (u - 0.5) * 2) * 18 * v["fold"]
        ease = wave(u, v["shape"]) * 6
        ang = base + pleat + ease + jit * 14 * (rnd.random() - 0.5)
        if playing:
            ang *= 1.08
        level = 1 + round(6 * u)
        if v["res"] > 0.05 and i == n - 1:
            level = 7
        card = [(-w / 2, 0), (w / 2, 0), (w / 2, -h), (-w / 2, -h)]
        o.append(shape(rot(card, ang), G[0], *pivot))                 # a black edge between cards
        inset = [(-w / 2 + 1.5, -1.5), (w / 2 - 1.5, -1.5), (w / 2 - 1.5, -h + 1.5), (-w / 2 + 1.5, -h + 1.5)]
        o.append(shape(rot(inset, ang), G[min(7, level)], *pivot))
    o.append(shape(dot(4, 16), G[7], *pivot))
    return close_frame(o, v)


CONCEPTS = {"a1-fold-strip": fold_strip, "a2-moire": moire, "a3-field": field, "a4-louvres": louvres, "a5-card-fan": card_fan}


def main():
    D = dict(g.DEFAULTS)
    poses = {"rest": (D, False), "fold-100": (dict(D, fold=1), False), "cutoff-100": (dict(D, cutoff=1), False),
             "cutoff-000": (dict(D, cutoff=0), False), "spread-100": (dict(D, spread=1), False), "playing": (D, True)}
    for name, fn in CONCEPTS.items():
        d = HERE / name
        d.mkdir(exist_ok=True)
        for pose, (vals, playing) in poses.items():
            (d / f"{pose}.svg").write_text(fn(vals, playing), encoding="utf-8")
    print("wrote", len(CONCEPTS) * len(poses), "frames")


if __name__ == "__main__":
    main()
