#!/usr/bin/env python3
"""Toro round 8: halfway between the bull and the sign. Each concept is a bull reduced to a few bold marks.

  m1 glyph     the Taurus glyph (a disc under a crescent) given just enough face to be a bull
  m2 totem     a head-on mask of flat planes in the stepped greys: trapezoids, slits and bars
  m3 strokes   the whole bull, side-on, in seven brush-weight lines
  m4 meter     a field of level bars; the bull's head and horns rise out of it like a spectrum
  m5 reduce    cutoff morphs the sign into the bull: glyph at 0, mask at 100

    python3 screens/toro/concepts/semi.py [m1-glyph ...]
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import gen_frames as g  # noqa: E402
from uniques import spline, tube, bez, xf, shape, stroke, frame, arc_pts  # noqa: E402

G, dot, grey, annulus = g.G, g.dot, g.grey, g.annulus


def lerp(a, b, t):
    return [(p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t) for p, q in zip(a, b)]


def ring_band(cx, cy, r0, r1, n=40):
    outer = [(cx + r1 * math.cos(2 * math.pi * i / n), cy + r1 * math.sin(2 * math.pi * i / n)) for i in range(n)]
    inner = [(cx + r0 * math.cos(2 * math.pi * i / n), cy + r0 * math.sin(2 * math.pi * i / n)) for i in range(n)]
    # one outline: outer round, a hairline seam, inner round backwards
    return outer + [outer[0], (inner[0][0], inner[0][1] + 0.01)] + inner[::-1]


def crescent(cx, cy, r, span, w0, w1, curl=0.0):
    """horns as a crescent opening upward: one tube per side, from the middle out"""
    out = []
    for sd in (-1, 1):
        a = [math.radians(90 + sd * span * i / 14) for i in range(15)]
        pts = [(cx + r * math.cos(t) * (1 - 0.12 * curl * (i / 14) ** 2), cy + r * math.sin(t) - curl * 10 * (i / 14) ** 3) for i, t in enumerate(a)]
        out.append(tube(pts, w0, w1))
    return out


# m1 · glyph ----------------------------------------------------------------------------------------------------------
def glyph(v, playing=False):
    o = []
    cx, cy, R = 240, 158, 44
    sp, cu = v["spread"], v["shape"]
    # horns: the crescent sits on top of the disc
    for h in crescent(cx, cy - R - 2, 38 + 14 * sp, 150 + 10 * sp, 13, 3, cu):
        o.append(shape(h, G[7]))
    # disc in rings: cutoff lights them from the centre out; fold alternates their widths
    n = 5
    lit = v["cutoff"] * (1.15 if playing else 1)
    edges = [0]
    for k in range(n):
        w = 1 + 0.9 * v["fold"] * (1 if k % 2 else -0.6)
        edges.append(edges[-1] + w)
    edges = [R * e / edges[-1] for e in edges]
    for k in range(n - 1, -1, -1):
        u = (k + 0.5) / n
        level = 2 + round(5 * max(0.0, min(1.0, (lit - u) * 2.2 + 0.5)))
        o.append(shape(xf(dot(edges[k + 1], 40), cx, cy), G[max(1, level - (k % 2))]))
    # just enough face: two slit eyes and a nose ring
    for sd in (-1, 1):
        o.append(shape([(cx + sd * 14, cy - 10), (cx + sd * 30, cy - 14), (cx + sd * 28, cy - 9), (cx + sd * 14, cy - 7)], G[0]))
    rr = 6 + 5 * v["res"]
    o.append(shape(xf(annulus(rr, 2.2, 24), cx, cy + R - 4 + rr), G[7]))
    return frame(v, o)


# m2 · totem ----------------------------------------------------------------------------------------------------------
def totem(v, playing=False):
    o = []
    cx, cy = 240, 130
    lit = v["cutoff"]
    drop = 8 * v["fold"] + (5 if playing else 0)
    P = lambda pts: xf(pts, cx, cy + drop)
    sp, cu = v["spread"], v["shape"]
    # horns: a bar out, a bar up, in three stepped segments
    for sd in (-1, 1):
        reach = 60 + 34 * sp
        rise = 34 + 16 * cu
        o.append(shape(P([(sd * 30, -42), (sd * reach, -46), (sd * reach, -34), (sd * 30, -28)]), G[5]))
        o.append(shape(P([(sd * reach, -46), (sd * (reach + 16), -50 - rise * 0.4), (sd * (reach + 10), -50 - rise), (sd * (reach - 4), -34)]), G[6]))
        o.append(shape(P([(sd * (reach + 10), -50 - rise), (sd * (reach + 16), -50 - rise * 0.4), (sd * (reach + 18 - 12 * cu), -56 - rise * 1.2)]), G[7]))
    # ears: wedges under the horn bars
    for sd in (-1, 1):
        o.append(shape(P([(sd * 34, -26), (sd * 60, -24), (sd * 36, -12)]), G[3]))
    # head planes: forehead, two cheeks, the bridge, the muzzle
    o.append(shape(P([(-34, -44), (34, -44), (30, -10), (-30, -10)]), G[4]))
    for sd in (-1, 1):
        o.append(shape(P([(sd * 30, -10), (sd * 8, -10), (sd * 8, 42), (sd * 18, 42)]), G[3 + (1 if sd > 0 and lit > 0.5 else 0)]))
    o.append(shape(P([(-8, -10), (8, -10), (10, 42), (-10, 42)]), grey((3 + 3 * lit) / 7)))       # cutoff lights the bridge
    o.append(shape(P([(-22, 42), (22, 42), (26, 64), (16, 76), (-16, 76), (-26, 64)]), G[5]))
    for sd in (-1, 1):
        o.append(shape(P([(sd * 7, 58), (sd * 15, 56), (sd * 15, 64), (sd * 8, 64)]), G[1]))       # nostrils
        open_ = 1.5 + 5 * lit                                         # cutoff opens the eye slits
        o.append(shape(P([(sd * 12, -22), (sd * 28, -26), (sd * 28, -26 + open_), (sd * 12, -22 + open_ * 0.6)]), G[7] if lit > 0.3 else G[5]))
    rr = 6 + 6 * v["res"]
    o.append(shape(P(xf(annulus(rr, 2.4, 24), 0, 76 + rr - 2)), G[7]))
    return frame(v, o)


# m3 · strokes --------------------------------------------------------------------------------------------------------
def strokes(v, playing=False):
    o = []
    gallop = v["fold"] + (0.3 if playing else 0)                    # fold: from a stand to a gallop
    w = 3.2 + 2.6 * v["drive"]
    col = grey((4 + 3 * v["cutoff"]) / 7)                           # cutoff: how bright the ink line is
    X = lambda pts: xf(pts, 96, 52, 1.0)
    # back: from tail root over the hump to the poll, one brush line
    o.append(stroke(X(spline([(252, 66), (200, 56), (150, 50), (116, 26), (92, 30), (70, 52), (52, 66)], closed=False, per=8)), col, w + 1.2))
    # belly and chest
    o.append(stroke(X(spline([(240, 108), (190, 114), (140, 114), (104, 106)], closed=False, per=8)), col, w))
    # head: a single hooked line, brow to muzzle to jaw
    o.append(stroke(X(spline([(52, 66), (34, 82), (24, 104), (34, 112), (56, 100), (78, 96)], closed=False, per=8)), col, w))
    # legs: four strokes; the gallop throws them forward and back
    for x0, y0, sw, dx in ((110, 108, -1, 0), (130, 112, 1, 8), (210, 112, -1, 0), (234, 104, 1, 8)):
        a = math.radians(sw * 22 * gallop)
        L = 50
        o.append(stroke(X([(x0, y0), (x0 + dx * 0.2 + math.sin(a) * L * 0.5, y0 + L * 0.55), (x0 + math.sin(a) * L, y0 + math.cos(a) * L)]), col if dx == 0 else grey((2 + 2 * v["cutoff"]) / 7), w - 0.6))
    # tail
    o.append(stroke(X(spline([(252, 66), (268, 82), (272, 104), (266, 120)], closed=False, per=6)), col, w - 1.2))
    # horn: one sweep, the brightest mark
    sp, cu = v["spread"], v["shape"]
    o.append(shape(X(tube(bez([(62, 56), (54, 34 - 6 * sp), (32 - 20 * sp, 22 - 6 * sp), (18 - 30 * sp, 22 - 24 * cu)], 14), 7, 1.6)), G[7]))
    o.append(shape(X(xf(dot(2.4, 10), 44, 82)), G[7]))              # eye
    if v["res"] > 0.05:
        rr = 4 + 4 * v["res"]
        o.append(shape(X(xf(annulus(rr, 1.8, 20), 30, 114 + rr)), G[6]))
    return frame(v, o)


# m4 · meter ----------------------------------------------------------------------------------------------------------
HEAD_Y = [(-60, 0.0), (-50, 0.15), (-40, 0.2), (-34, 0.62), (-26, 0.8), (-14, 0.86), (0, 0.9)]


def meter(v, playing=False):
    o = []
    bars, gap = 44, 10
    x0 = 240 - (bars - 1) * gap / 2
    base = 210
    sp, cu = v["spread"], v["shape"]
    rnd = random.Random(3)
    for i in range(bars):
        x = x0 + i * gap
        u = (x - 240)
        au = abs(u)
        # the head: a broad column with ears; the horns: two peaks that spread and curl
        head = 0.0
        if au < 40:
            head = 0.78 - 0.14 * (au / 40) ** 2
        elif au < 62:
            head = 0.5 - 0.6 * ((au - 40) / 22)                      # ears
        horn_x = 74 + 50 * sp
        horn = max(0.0, 1.0 - abs(au - horn_x) / (12 + 10 * cu)) * (0.92 + 0.08 * cu)
        trail = max(0.0, 0.42 - abs(au - (horn_x - 26)) / 60) if au < horn_x else 0.0
        level = max(head, horn, trail)
        level *= 0.55 + 0.45 * v["cutoff"] + (0.08 if playing else 0)   # cutoff: how loud the meter reads
        level += v["noise"] * 0.08 * rnd.random() + 0.04
        h = 150 * min(1.0, level)
        # fold: each bar breaks into segments, like a stepped LED meter
        segs = 3 + round(9 * v["fold"])
        sh = h / segs
        for k in range(segs):
            y1 = base - k * sh
            t = k / max(1, segs - 1)
            col = grey(min(7, 2 + 5 * (k + 1) / segs * min(1.0, level * 1.2)) / 7)
            o.append(shape([(x - 3, y1), (x + 3, y1), (x + 3, y1 - sh + 1.2), (x - 3, y1 - sh + 1.2)], col))
    # eyes: two dark gaps cut into the head columns
    for sd in (-1, 1):
        o.append(shape([(240 + sd * 12, 128), (240 + sd * 32, 124), (240 + sd * 32, 130), (240 + sd * 12, 133)], G[0]))
    rr = 6 + 5 * v["res"]
    o.append(shape(xf(annulus(rr, 2.2, 24), 240, 210 - rr - 2), G[7]))
    return frame(v, o)


# m5 · reduce ---------------------------------------------------------------------------------------------------------
def head_outline(n=40):
    half = [(0, -46), (14, -46), (28, -40), (34, -28), (32, -10), (28, 8), (24, 24), (24, 40), (22, 52), (14, 60), (0, 62)]
    pts = spline(half, closed=False, per=2)
    pts = pts[:n // 2 + 1]
    while len(pts) < n // 2 + 1:
        pts.append(pts[-1])
    return pts + [(-x, y) for x, y in pts[-2:0:-1]]


def reduce(v, playing=False):
    o = []
    t = v["cutoff"] * (1.0 if not playing else min(1.0, v["cutoff"] + 0.15))   # cutoff: sign at 0, bull at 100
    cx, cy = 240, 140
    n = 40
    bull = head_outline(n)
    disc = [(40 * math.sin(2 * math.pi * i / n), -40 * math.cos(2 * math.pi * i / n) + 10) for i in range(n)]
    # align the disc to start at the top like the head outline, going clockwise
    shape_pts = lerp(disc, bull, t)
    sp, cu = v["spread"], v["shape"]
    # horns: crescent on the disc → horns from the poll
    for sd in (-1, 1):
        r_ = 28 + 12 * sp
        sign_h = [(r_ * math.cos(math.radians(90 - sd * (20 + 9.5 * i))), -58 + r_ * math.sin(math.radians(90 - sd * (20 + 9.5 * i)))) for i in range(15)]
        bull_h = bez([(sd * 22, -42), (sd * (52 + 24 * sp), -52), (sd * (78 + 30 * sp), -58), (sd * (82 + 30 * sp - 20 * cu), -86 - 12 * cu)], 14)
        o.append(shape(xf(tube(lerp(sign_h, bull_h, t), 13 - 2 * t, 2.2), cx, cy), G[7]))
    o.append(shape(xf(shape_pts, cx, cy), grey((4 + 1.5 * t) / 7)))
    # features fade in as the filter opens: ears, eyes, muzzle, nostrils
    if t > 0.25:
        k = min(1.0, (t - 0.25) / 0.3)
        for sd in (-1, 1):
            o.append(shape(xf([(sd * 30, -30), (sd * (30 + 26 * k), -30), (sd * (30 + 22 * k), -20), (sd * 31, -18)], cx, cy), G[3]))
    if t > 0.45:
        k = min(1.0, (t - 0.45) / 0.3)
        o.append(shape(xf([(-20, 38), (20, 38), (22, 54), (12, 61), (-12, 61), (-22, 54)], cx, cy), grey((4 + 2 * k) / 7)))
    for sd in (-1, 1):                                               # eyes: present at every stage, as in the glyph's face
        o.append(shape(xf([(sd * 12, -12), (sd * 26, -16), (sd * 25, -11), (sd * 12, -9)], cx, cy), G[0]))
    rr = 6 + 5 * v["res"]
    o.append(shape(xf(annulus(rr, 2.2, 24), cx, cy + 52 + 10 * t + rr - 4), G[7]))
    return frame(v, o)


STYLES = {"m1-glyph": glyph, "m2-totem": totem, "m3-strokes": strokes, "m4-meter": meter, "m5-reduce": reduce}


def main():
    D = dict(g.DEFAULTS)
    poses = {"rest": (D, False), "spread-100": (dict(D, spread=1, shape=0.6), False), "cutoff-000": (dict(D, cutoff=0), False),
             "cutoff-100": (dict(D, cutoff=1), False), "fold-100": (dict(D, fold=1), False), "playing": (D, True)}
    only = sys.argv[1:] or list(STYLES)
    for name in only:
        d = HERE / name
        d.mkdir(exist_ok=True)
        for pose, (vals, playing) in poses.items():
            (d / f"{pose}.svg").write_text(STYLES[name](vals, playing), encoding="utf-8")
    print("wrote", len(only) * len(poses), "frames")


if __name__ == "__main__":
    main()
