#!/usr/bin/env python3
"""Toro round 7: five different bulls, not one bull in five styles.

  u1 charge     side view, head down, mid-charge; solid stepped-grey silhouette, far legs a step darker
  u2 built      a standing bull constructed from circles, wedges and bars (constructivist)
  u3 bucranium  the skull, head-on: bone, sockets and long horns
  u4 dark       head-on and lowered, out of the dark: rim light, horns, eye glints, ring and breath
  u5 eye        extreme close-up: one eye, the brow, the root of a horn

    python3 screens/toro/concepts/uniques.py [u1-charge ...]
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import gen_frames as g  # noqa: E402

G, f, poly, dot, grey, annulus, rot = g.G, g.f, g.poly, g.dot, g.grey, g.annulus, g.rot


def kink(a):
    return 0.4 * a + 0.6 * a ** 3


# geometry helpers -----------------------------------------------------------------------------------------------------
def spline(pts, closed=True, per=6):
    """Catmull-Rom through the points: authored as a few dozen knots, drawn smooth"""
    n = len(pts)
    out = []
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if closed or i > 0 else pts[0]
        p1, p2 = pts[i], pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if closed or i + 2 < n else pts[-1]
        for k in range(per):
            t = k / per
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[c]) + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2
                                    + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in (0, 1)))
    if not closed:
        out.append(pts[-1])
    return out


def cap64(pts, cap=62):
    """drop points evenly until the path fits the SDK's 64-point limit"""
    if len(pts) <= cap:
        return pts
    step = len(pts) / cap
    return [pts[int(i * step)] for i in range(cap)]


def xf(pts, x=0.0, y=0.0, s=1.0, deg=0.0, flip=False):
    c, sn = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    out = []
    for px, py in pts:
        px = -px if flip else px
        out.append((x + (px * c - py * sn) * s, y + (px * sn + py * c) * s))
    return out


def bez(p, n=16):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        out.append((a * p[0][0] + b * p[1][0] + c * p[2][0] + d * p[3][0], a * p[0][1] + b * p[1][1] + c * p[2][1] + d * p[3][1]))
    return out


def tube(spine, w0, w1):
    left, right = [], []
    n = len(spine) - 1
    for i, (x, y) in enumerate(spine):
        a, b = spine[max(0, i - 1)], spine[min(n, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        w = (w0 + (w1 - w0) * (i / n) ** 0.9) / 2
        left.append((x - dy / ln * w, y + dx / ln * w))
        right.append((x + dy / ln * w, y - dx / ln * w))
    return left + right[::-1]


def shape(pts, color):
    return f'<path d="{poly(cap64(pts))}" fill="{color}" stroke="none"/>'


def stroke(pts, color, w, close=False):
    pts = cap64(pts)
    d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + (" Z" if close else "")
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{f(w)}" stroke-linejoin="round" stroke-linecap="round"/>'


def frame(v, body):
    return "\n".join(['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
                      '<rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>'] + body + g.header(v) + ["</svg>"])


# u1 · charge ----------------------------------------------------------------------------------------------------------
# bull faces left, authored in a 0..300 × 0..150 box, ground at y 150
BODY = [(16, 127), (11, 113), (16, 99), (30, 84), (46, 71), (64, 54), (84, 34), (106, 21), (130, 21), (156, 32),
        (186, 39), (214, 42), (236, 46), (248, 58), (251, 76), (245, 92), (232, 101), (206, 105), (176, 108),
        (150, 110), (130, 113), (110, 123), (90, 124), (70, 119), (54, 124), (40, 133), (24, 134)]
NEAR_FORE = [(94, 104), (124, 106), (120, 122), (104, 134), (90, 143), (86, 150), (66, 150), (67, 143), (80, 133), (93, 120)]
FAR_FORE = [(116, 104), (142, 106), (143, 124), (150, 139), (156, 150), (140, 150), (134, 137), (121, 121)]
NEAR_HIND = [(210, 96), (244, 88), (247, 110), (259, 128), (272, 144), (274, 150), (258, 150), (243, 134), (225, 119), (213, 108)]
FAR_HIND = [(198, 98), (226, 98), (224, 116), (213, 134), (208, 150), (194, 150), (198, 131), (203, 115)]
TAIL = [(246, 50), (258, 58), (266, 76), (270, 94), (268, 106)]


def charge(v, playing=False):
    o = []
    s, x0, y0 = 1.08, 100, 47                                        # place the 300 × 150 box on the screen
    lean = 4 * v["fold"] + (3 if playing else 0)                  # fold: the bull drops lower into the charge
    P = lambda pts: xf(pts, x0, y0 + 2 * v["fold"], s, -lean * 0.4)
    # speed lines behind: drive makes them thicker, noise breaks them up
    rnd = random.Random(2)
    for k in range(5 + round(4 * v["drive"])):
        y = 74 + k * 26 * (0.9 - 0.3 * v["drive"])
        x1 = 384 + rnd.uniform(-10, 30)
        ln = 40 + 60 * rnd.random() + (30 if playing else 0)
        o.append(stroke([(x1, y), (x1 + ln, y)], G[2 + (k % 2)], 1.4 + 1.2 * v["drive"]))
    # dust kicked up by the hooves
    for k in range(int(3 + 18 * v["noise"])):
        o.append(shape(xf(dot(1.4 + 1.4 * rnd.random(), 8), 330 + rnd.uniform(-20, 90), 208 - rnd.uniform(0, 26)), G[3]))
    o.append(shape(P(spline(FAR_FORE)), G[3]))
    o.append(shape(P(spline(FAR_HIND)), G[3]))
    o.append(shape(P(spline(TAIL, closed=False) + [(263, 104), (260, 82), (250, 62)]), G[4]))
    o.append(shape(P(spline(BODY)), G[5]))
    o.append(shape(P(spline(NEAR_FORE)), G[5]))
    o.append(shape(P(spline(NEAR_HIND)), G[5]))
    # light along the hump: cutoff decides how far the light runs down the back
    lit = v["cutoff"]
    crest = spline(BODY)[24:66]
    n = max(2, int(len(crest) * (0.15 + 0.85 * lit)))
    o.append(stroke(P(crest[:n]), G[7], 2.2))
    # horn: spread sweeps it forward, shape curls the tip up
    sp, cu = v["spread"], v["shape"]
    horn = bez([(44, 76), (30, 68 - 4 * sp), (8 - 16 * sp, 66 - 6 * sp), (-6 - 24 * sp, 52 - 22 * cu)], 14)
    o.append(shape(P(tube(horn, 9, 1.6)), G[7]))
    far = bez([(52, 70), (44, 58), (30 - 12 * sp, 50), (22 - 18 * sp, 36 - 18 * cu)], 12)
    o.append(shape(P(tube(far, 7, 1.4)), G[4]))
    o.append(shape(P(spline([(56, 80), (70, 74), (78, 80), (66, 86)])), G[4]))   # ear, behind the horn root
    # eye and nostril: res puts a glint in the eye
    o.append(shape(P(xf(dot(2.6, 10), 36, 92)), G[1]))
    if v["res"] > 0.05:
        o.append(shape(P(xf(dot(0.9 + 1.4 * v["res"], 8), 35.4, 91.2)), G[7]))
    o.append(shape(P(xf(dot(2.2, 8), 16, 120)), G[2]))
    o.append(stroke(P([(30, 92), (40, 89), (48, 92)]), G[3], 1.2))          # heavy brow over the eye
    # breath: a note blows two puffs from the nostril
    if playing or v["drive"] > 0.3:
        for k, r in enumerate((4, 6)):
            o.append(stroke(P([(4 - 14 * k + r * math.cos(a), 130 - 4 * k + r * math.sin(a)) for a in [i * math.pi / 8 for i in range(17)]]), G[4], 1.2))
    o.append(stroke([(40, 211), (440, 211)], G[2], 1.2))         # ground
    return frame(v, o)


# u2 · built ---------------------------------------------------------------------------------------------------------
def arc_pts(cx, cy, r, a0, a1, n=24):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def built(v, playing=False):
    o = []
    ground = 208
    sun_r = 20 + 46 * v["cutoff"]                                  # cutoff: the sun behind the bull rises and grows
    o.append(shape(xf(dot(sun_r, 48), 190, 150 - 50 * v["cutoff"]), G[2]))
    o.append(shape([(70, ground), (420, ground), (420, ground + 3), (70, ground + 3)], G[3]))
    # far legs, a step darker
    for x in (206, 316):
        o.append(shape([(x, 150), (x + 13, 150), (x + 13, ground), (x, ground)], G[3]))
    # tail: a bar and a ball
    o.append(shape(tube([(160, 118), (150, 150), (148, 182)], 4, 3), G[4]))
    o.append(shape(xf(dot(6, 16), 148, 186), G[4]))
    # body: hind circle, hump circle, a bar between
    o.append(shape(xf(dot(34, 40), 186, 136), G[4]))
    o.append(shape([(186, 102), (292, 76), (300, 168), (186, 170)], G[5]))
    o.append(shape(xf(dot(46, 48), 292, 118), G[5]))
    # near legs
    for x in (190, 298):
        o.append(shape([(x, 156), (x + 15, 156), (x + 15, ground), (x, ground)], G[5]))
    # head: a wedge that drops with fold (the bull lowers to charge)
    drop = 30 * v["fold"] + (10 if playing else 0)
    pivot = (330, 112)
    head = [(322, 98), (366, 104), (380, 150), (364, 166), (344, 160)]
    head = [(pivot[0] + (x - pivot[0]) * math.cos(math.radians(drop)) - (y - pivot[1]) * math.sin(math.radians(drop)),
             pivot[1] + (x - pivot[0]) * math.sin(math.radians(drop)) + (y - pivot[1]) * math.cos(math.radians(drop))) for x, y in head]
    hx, hy = (head[0][0] + head[1][0]) / 2, (head[0][1] + head[1][1]) / 2
    o.append(shape(head, G[6]))
    # horns: one from each top corner of the head; spread sweeps them out, shape lifts the tips
    sp, cu = v["spread"], v["shape"]
    for base, sd, col in ((head[0], -1, G[4]), (head[1], 1, G[7])):
        bx, by = base
        h = bez([(bx, by + 2), (bx + sd * (10 + 10 * sp), by - 6), (bx + sd * (22 + 22 * sp), by - 12 - 8 * cu), (bx + sd * (20 + 26 * sp - 10 * cu), by - 30 - 14 * cu)], 14)
        o.append(shape(tube(h, 8, 1.8), col))
    # eye and nose: a dot and a bar
    ex, ey = head[0][0] * 0.4 + head[2][0] * 0.6 - 4, head[0][1] * 0.6 + head[2][1] * 0.4
    o.append(shape(xf(dot(3.2, 12), ex, ey), G[0]))
    if v["res"] > 0.05:
        o.append(shape(annulus(5 + 5 * v["res"], 1.6, 24), G[7]).replace('d="', f'transform="translate({f(head[3][0])} {f(head[3][1] - 2)})" d="'))
    return frame(v, o)


# u3 · bucranium ----------------------------------------------------------------------------------------------------------
SKULL = [(0, -62), (18, -61), (32, -56), (38, -46), (36, -30), (30, -16), (22, -2), (18, 18), (17, 38), (19, 52), (14, 62),
         (0, 66), (-14, 62), (-19, 52), (-17, 38), (-18, 18), (-22, -2), (-30, -16), (-36, -30), (-38, -46), (-32, -56), (-18, -61)]


def bucranium(v, playing=False):
    o = []
    cx, cy, s = 240, 138, 1.0
    P = lambda pts: xf(pts, cx, cy, s)
    # horns first: lyre-shaped, banded; spread opens them, shape curls the tips in
    sp, cu = v["spread"], v["shape"]
    for sd in (-1, 1):
        spine = bez([(sd * 30, -52), (sd * (62 + 26 * sp), -54), (sd * (92 + 40 * sp), -70 - 4 * cu),
                     (sd * (96 + 40 * sp - 34 * cu), -96 + 2 * sp)], 22)
        o.append(shape(P(tube(spine, 15, 2.0)), G[6]))
        for j in (5, 9, 13):                                        # growth rings on the horn
            a, b = spine[j], spine[j + 1]
            nx, ny = -(b[1] - a[1]), b[0] - a[0]
            ln = math.hypot(nx, ny) or 1
            w = (15 + (2 - 15) * (j / 22) ** 0.9) / 2
            o.append(stroke(P([(a[0] + nx / ln * w, a[1] + ny / ln * w), (a[0] - nx / ln * w, a[1] - ny / ln * w)]), G[4], 1.4))
    o.append(shape(P(spline(SKULL)), G[5]))
    # the side planes of the face, a step darker
    for sd in (-1, 1):
        o.append(shape(P([(sd * 36, -30), (sd * 30, -16), (sd * 22, -2), (sd * 18, 18), (sd * 17, 38), (sd * 12, 38), (sd * 13, 14), (sd * 18, -6), (sd * 26, -26)]), G[4]))
    # brow ridge
    o.append(stroke(P(spline([(-34, -36), (-18, -40), (0, -36), (18, -40), (34, -36)], closed=False)), G[6], 2.0))
    # sockets: cutoff lights embers inside; a note flares them
    glow = v["cutoff"] * (1.25 if playing else 1)
    for sd in (-1, 1):
        sock = spline([(sd * 10, -30), (sd * 24, -34), (sd * 32, -24), (sd * 26, -12), (sd * 13, -14)])
        o.append(shape(P(sock), G[0]))
        if glow > 0.04:
            k = 0.15 + 0.7 * min(1.0, glow)                        # the ember fills the socket from its centre
            ember = [(sd * 21 + (x - sd * 21) * k, -23 + (y + 23) * k) for x, y in sock]
            o.append(shape(P(ember), grey(min(7, 2 + 5 * glow) / 7)))
    # nasal cavity
    o.append(shape(P(spline([(0, 6), (7, 20), (6, 36), (0, 42), (-6, 36), (-7, 20)])), G[0]))
    # fold: cracks branch across the bone
    rnd = random.Random(4)
    for k in range(round(1 + 6 * v["fold"])):
        x, y = rnd.uniform(-20, 20), rnd.uniform(-58, -44)
        pts = [(x, y)]
        for _ in range(4):
            x += rnd.uniform(-5, 5); y += rnd.uniform(4, 8)
            pts.append((x, y))
        o.append(stroke(P(pts), G[2], 1.2))
    # res: a ring through the nose
    if v["res"] > 0.05:
        rr = 5 + 6 * v["res"]
        o.append(shape(P(xf(annulus(rr, 2.2, 24), 0, 64 + rr)), G[7]))
    return frame(v, o)


# u4 · in the dark -------------------------------------------------------------------------------------------------------
def dark(v, playing=False):
    """head-on, lowered, out of the dark: only rim light, horns, eyes, ring and breath show"""
    o = []
    lit = v["cutoff"]
    drop = 10 * v["fold"] + (6 if playing else 0)                 # fold: the head drops lower, ready to charge
    cx, cy = 240, 112 + drop
    P = lambda pts: xf(pts, cx, cy)
    sp, cu = v["spread"], v["shape"]
    # horns: huge, nearly the frame's width; the upper edge catches the light
    spine = bez([(26, -12), (80 + 30 * sp, -34), (140 + 50 * sp, -38 - 6 * cu), (166 + 44 * sp - 30 * cu, -70 - 6 * sp - 18 * cu)], 22)
    edge = []
    for i, (x, y) in enumerate(spine):
        a_, b_ = spine[max(0, i - 1)], spine[min(22, i + 1)]
        dx, dy = b_[0] - a_[0], b_[1] - a_[1]
        ln = math.hypot(dx, dy) or 1
        w = (22 + (2.4 - 22) * (i / 22) ** 0.9) / 2 * 0.75
        edge.append((x + dy / ln * w, y - dx / ln * w))
    n = max(3, int(len(edge) * (0.3 + 0.7 * lit)))
    for sd, col in ((1, G[7]), (-1, G[5])):
        o.append(shape(P(xf(tube(spine, 22, 2.4), flip=sd < 0)), grey((2 + 2 * lit) / 7)))
        o.append(stroke(P(xf(edge[1:n], flip=sd < 0)), col, 1.8))
    o.append(shape(P(spline([(-30, -8), (-20, -22), (0, -26), (20, -22), (30, -8), (0, -14)], per=4)), G[1]))   # the poll between them
    # rim light down the face: cutoff decides how far round the head the light reaches
    face_r = spline([(30, -6), (35, 8), (31, 26), (25, 44), (24, 58), (16, 68), (0, 71)], closed=False, per=5)
    face_l = [(-x, y) for x, y in face_r]
    n = max(3, int(len(face_r) * (0.2 + 0.8 * lit)))
    o.append(stroke(P(face_r[:n]), G[6], 2.0))
    o.append(stroke(P(face_l[:max(2, int(n * 0.45))]), G[3], 1.4))
    # eyes: two hard glints; res makes them brighter and larger
    for sd in (-1, 1):
        o.append(shape(P(xf(spline([(-5, 0), (0, -2.2), (5, 0), (0, 2.2)], per=3), sd * 24, 4)), G[2]))
        o.append(shape(P(xf(dot(1.2 + 1.2 * v["res"], 10), sd * 24 + 1.5, 3.4)), G[7]))
    # nose ring
    rr = 6 + 5 * v["res"]
    o.append(shape(P(xf(annulus(rr, 2.0, 24), 0, 66 + rr)), G[6]))
    # breath: drive grows the plumes; a note blows them out
    puffs = 1 + round(3 * v["drive"]) + (2 if playing else 0)
    for sd in (-1, 1):
        for k in range(puffs):
            r = 5 + 3 * k
            x, y = sd * (14 + 12 * k), 64 + 6 * k
            o.append(stroke(P([(x + r * math.cos(t), y + r * 0.7 * math.sin(t)) for t in [i * math.pi / 10 for i in range(21)]]), grey(max(1, 4 - k) / 7), 1.4))
    # noise: dust hanging in the light
    rnd = random.Random(6)
    for k in range(int(4 + 40 * v["noise"])):
        o.append(shape(xf(dot(0.9 + rnd.random(), 6), rnd.uniform(60, 420), rnd.uniform(60, 210)), G[3]))
    return frame(v, o)


# u5 · eye ---------------------------------------------------------------------------------------------------------------
def eye(v, playing=False):
    o = []
    # the face fills the lower left: skin in two steps
    o.append(shape(spline([(-20, 60), (120, 44), (250, 54), (360, 90), (430, 160), (450, 240), (-20, 240)], per=4), G[2]))
    o.append(shape(spline([(-20, 110), (120, 88), (230, 96), (300, 128), (330, 180), (320, 240), (-20, 240)], per=4), G[3]))
    # horn root: rises from the top right, ringed; spread leans it out, shape curls it back over
    sp, cu = v["spread"], v["shape"]
    spine = bez([(330, 96), (360, 60 - 4 * sp), (400 + 30 * sp, 40 - 10 * sp), (430 + 40 * sp - 40 * cu, -10 + 26 * cu)], 20)
    o.append(shape(tube(spine, 54, 18), G[5]))
    for j in range(2, 18, 3):
        a, b = spine[j], spine[j + 1]
        nx, ny = -(b[1] - a[1]), b[0] - a[0]
        ln = math.hypot(nx, ny) or 1
        w = (54 + (18 - 54) * (j / 20) ** 0.9) / 2
        o.append(stroke([(a[0] + nx / ln * w * 0.92, a[1] + ny / ln * w * 0.92), (a[0] - nx / ln * w * 0.92, a[1] - ny / ln * w * 0.92)], G[4], 1.4))
    # fold: wrinkles stack up around the eye
    for k in range(2 + round(5 * v["fold"])):
        off = 12 + 7 * k                                          # skin folds under and behind the eye
        o.append(stroke(spline([(170 - off * 0.8, 150 + off * 0.3), (222, 162 + off * 0.7), (300 + off * 0.3, 140 + off * 0.4)], closed=False, per=8), G[4], 1.4))
    # the eye: cutoff opens the lid; a note widens it
    open_ = 0.12 + 0.88 * v["cutoff"] * (1.12 if playing else 1)
    top = [(160, 140), (190, 140 - 34 * open_), (232, 140 - 40 * open_), (276, 134 - 16 * open_), (290, 136)]
    bottom = [(290, 136), (262, 152), (220, 160), (182, 154)]
    white = spline(top + bottom, per=5)
    o.append(shape(white, G[5]))
    # iris and pupil inside the opening (the pupil is a bar, like a bull's)
    ir = 22
    iris = [(225 + ir * math.cos(a), 140 + ir * math.sin(a)) for a in [i * math.pi / 16 for i in range(32)]]
    clip_top = lambda pts: [(x, max(y, min(yy for xx, yy in spline(top, closed=False, per=6) if abs(xx - x) < 6) if any(abs(xx - x) < 6 for xx, yy in spline(top, closed=False, per=6)) else y)) for x, y in pts]
    o.append(shape(clip_top([(x, min(y, 156)) for x, y in iris]), G[1]))
    o.append(shape(clip_top([(208, 136), (242, 136), (242, 144), (208, 144)]), G[0]))
    if v["res"] > 0.05 and open_ > 0.3:
        o.append(shape(xf(dot(1.6 + 3.2 * v["res"], 12), 236, 130), G[7]))
    # lid fold and lashes
    o.append(stroke(spline(top, closed=False, per=6), G[6], 2.4))
    for k in range(9):
        t = 0.12 + 0.76 * k / 8
        pts = spline(top, closed=False, per=6)
        x, y = pts[int(t * (len(pts) - 1))]
        o.append(stroke([(x, y), (x + 6 + 4 * t, y - 9 + 2 * t)], G[6], 1.4))
    # noise: short hair strokes over the face
    rnd = random.Random(12)
    for k in range(int(10 + 50 * v["noise"])):
        x, y = rnd.uniform(10, 320), rnd.uniform(160, 214)
        o.append(stroke([(x, y), (x + 5, y - 3)], G[4], 1.2))
    return frame(v, o)


STYLES = {"u1-charge": charge, "u2-built": built, "u3-bucranium": bucranium, "u4-dark": dark, "u5-eye": eye}


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
