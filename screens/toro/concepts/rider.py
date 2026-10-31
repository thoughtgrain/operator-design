#!/usr/bin/env python3
"""Toro round 5: the OP-1 RIDER bull, rendered in the five styles from round 3.

The rig geometry is ported from thoughtgrain/labyrinth toro/gen_svg.py and toro_screen.c (GPL-3.0-or-later,
(c) 2026 briannhinton): body plate, shoulder lines, hump, ear plates, faceplate, eye slots and slits, nose plate,
nostrils, telescoping horns on a Bézier spine, nose ring, ram, base and turntable. The control mapping is the OP-1's:
spread → horn spread, shape → horn curl, cutoff → eye slits, fold → how hard the bull rocks (lean and lift),
res → nose ring, drive → steam, noise → sparks, aphx → glitch slices.

  r1 vector CRT   r2 halftone   r3 sumi-e ink   r4 isometric blocks   r5 Bauhaus

    python3 screens/toro/concepts/rider.py
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import gen_frames as g  # noqa: E402

G, f, poly, dot, ribbon, annulus, rot, grey = g.G, g.f, g.poly, g.dot, g.ribbon, g.annulus, g.rot, g.grey
HK, HY = 1.17, -30                                  # faceplate scale and offset, rig units (gen_svg.py)
S = 1.32                                            # rig unit → px on the XY
CX, TOP, BASE = 240, 170, 212


def kink(a):
    return 0.4 * a + 0.6 * a ** 3


def bez(p0, p1, p2, p3, n):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def h(x, y):                                         # head-local → rig units
    return (x * HK, y * HK + HY)


class Rig:
    """the bull's parts in rig units, then placed on screen by lean and lift"""

    def __init__(self, v, playing=False):
        self.v = v
        self.lean = math.radians(-14 * v["fold"] * (1.35 if playing else 1) + (6 if playing else 0))
        self.lift = 10 * v["fold"] + (6 if playing else 0)
        self.top = TOP - self.lift

    def to(self, pts):
        c, s = math.cos(self.lean), math.sin(self.lean)
        return [(CX + (x * c - y * s) * S, self.top + (x * s + y * c) * S) for x, y in pts]

    def body(self):
        a = bez((-36, -40), (-26, -50), (26, -50), (36, -40), 10)
        b = bez((36, -40), (47, -28), (47, -8), (34, -2), 8)[1:]
        c = [(-34, -2)]
        d = bez((-34, -2), (-47, -8), (-47, -28), (-36, -40), 8)[1:-1]
        return self.to(a + b + c + d)

    def hump(self):
        return self.to(bez((-6, -52), (-6, -64), (6, -64), (6, -52), 8))

    def shoulders(self):
        return [self.to(bez((30 * sd, -44), (40 * sd, -36), (42 * sd, -18), (34 * sd, -4), 8)) for sd in (-1, 1)]

    def ears(self):
        return [self.to([h(x * sd, y) for x, y in [(25, -12), (41, -11), (44, -6), (40, -2), (25, -2)]]) for sd in (-1, 1)]

    def face(self):
        head = [(-20, -22), (20, -22), (27, -10), (24, 4), (17, 16), (14, 28), (8, 32), (-8, 32), (-14, 28), (-17, 16), (-24, 4), (-27, -10)]
        return self.to([h(*p) for p in head])

    def eye_slots(self):
        return [self.to([h(x * sd, y) for x, y in [(21, -9), (8, -5.2), (8, 1.5), (20, -1.8)]]) for sd in (-1, 1)]

    def eye_slits(self):
        eh = 0.8 + 5.4 * self.v["cutoff"]             # the OP-1 range (1.4 + 3.4·cut) stretched to pass the area floor
        return [self.to([h(19.5 * sd, -7.8), h(9.3 * sd, -4.6), h(9.3 * sd, -4.6 + eh), h(18.8 * sd, -7.8 + eh * 0.9)]) for sd in (-1, 1)]

    def brows(self):
        return [self.to([h(27 * sd, -10), h(10 * sd, -7)]) for sd in (-1, 1)]

    def nose(self):
        return self.to([h(-12, 13), h(12, 13), h(14, 24), h(9, 31), h(-9, 31), h(-14, 24)])

    def nostrils(self):
        return [self.to([h(x * sd, y) for x, y in [(3.5, 18), (9, 18), (8, 23), (4, 23)]]) for sd in (-1, 1)]

    def horn(self, sd):
        sp, curl = self.v["spread"], self.v["shape"]
        px = [18, 32 + 10 * sp, 42 + 20 * sp, 44 + 25 * sp - 12 * curl]
        py = [-18, -21, -21 - (4 + 3 * sp), -18 - (16 + 4 * sp) + 8 * curl]
        pts = bez((px[0] * sd, py[0]), (px[1] * sd, py[1]), (px[2] * sd, py[2]), (px[3] * sd, py[3]), 24)
        spine = [h(x, y) for x, y in pts]
        widths = [5.4 - 3.4 * (u * (0.7 + 0.3 * u)) for u in [(j + 0.5) / 24 for j in range(25)]]
        return self.to(spine[3:]), [w * HK for w in widths[3:]]

    def ring(self):
        swing = math.radians(18 * self.v["res"])
        cx, cy = h(0, 33)
        r = 4 + 6 * self.v["res"]
        return self.to([(cx + math.sin(swing) * r, cy + math.cos(swing) * r)])[0], r * S

    def ram(self):
        return [(CX + math.sin(self.lean) * 0, self.top), (CX, BASE - 8)]


def tube(spine, widths, scale=S):
    """a horn as one closed outline: offset both sides of the spine, flat tip"""
    left, right = [], []
    for i, (x, y) in enumerate(spine):
        a, b = spine[max(0, i - 1)], spine[min(len(spine) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        w = widths[i] * scale / 2
        left.append((x - dy / ln * w, y + dx / ln * w))
        right.append((x + dy / ln * w, y - dx / ln * w))
    return left + right[::-1]


def glow(slit, cut, grow=1.0):
    """cutoff: light spilling out of an eye slit, the slit scaled up about its centre"""
    cx = sum(p[0] for p in slit) / len(slit); cy = sum(p[1] for p in slit) / len(slit)
    k = 1.25 + 0.9 * cut * grow
    return [(cx + (x - cx) * k, cy + (y - cy) * k) for x, y in slit]


def shape(pts, color, x=0.0, y=0.0):
    return f'<path transform="matrix(1 0 0 1 {f(x)} {f(y)})" d="{poly(pts)}" fill="{color}" stroke="none"/>'


def outline(pts, color, w, close=True):
    d = poly(pts) if close else "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts)
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linejoin="round"/>'


def frame(v, body):
    return "\n".join(['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
                      '<rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>'] + body + g.header(v) + ["</svg>"])


def steam(v, rig, playing):
    """drive: puffs from the vents, rising from both sides of the hump"""
    out = []
    puffs = round(1 + 4 * v["drive"]) if v["drive"] > 0.02 else 0
    for sd in (-1, 1):
        for i in range(puffs):
            base = rig.to([(14 * sd, -50)])[0]
            out.append((base[0] + sd * (10 + 11 * i), base[1] - 8 - 9 * i - (6 if playing else 0), 4 + 2.2 * i))
    return out


def glitch(v, playing):
    """aphx: horizontal slices of the screen shifted sideways, laid out by the key"""
    k = kink(v["aphx"]) * (1.3 if playing else 1)
    n = round(6 * k)
    rnd = random.Random(42)
    return [(rnd.uniform(74, 196), rnd.uniform(3, 7), (rnd.random() - 0.5) * 40 * k) for _ in range(n)]


# r1 · vector CRT ------------------------------------------------------------------------------------------------------
def crt(v, playing=False):
    rig = Rig(v, playing)
    o = []
    for k in range(4):                                             # the turntable as perspective ellipses
        rx, ry = 34 + 30 * k, 3 + 2.4 * k
        o.append(outline([(CX + math.cos(a) * rx, BASE + 2 + math.sin(a) * ry) for a in [i * math.pi / 24 for i in range(48)]], G[3 if k else 4], 1.2))
    o.append(outline([(CX - 9, BASE - 2), (CX - 9, BASE - 14), (CX + 9, BASE - 14), (CX + 9, BASE - 2)], G[5], 1.5))
    o.append(outline([(CX, BASE - 14), (CX, rig.top)], G[6], 2))
    for parts, col, w in ((rig.shoulders(), G[4], 1.2), (rig.ears(), G[5], 1.5), (rig.brows(), G[4], 1.2)):
        for p in parts:
            o.append(outline(p, col, w, close=parts is rig.ears()))
    o.append(outline(rig.body(), G[5], 1.5))
    o.append(outline(rig.hump(), G[6], 1.8, close=False))
    for sd in (-1, 1):
        spine, widths = rig.horn(sd)
        o.append(outline(tube(spine, widths), G[7], 1.6))
        for j in (5, 10, 15):                                      # telescoping joints as wire rings
            a, b = spine[j], spine[j + 1]
            nx, ny = -(b[1] - a[1]), b[0] - a[0]
            ln = math.hypot(nx, ny) or 1
            w = widths[j] * S / 2
            o.append(outline([(a[0] + nx / ln * w, a[1] + ny / ln * w), (a[0] - nx / ln * w, a[1] - ny / ln * w)], G[5], 1.2, close=False))
    o.append(outline(rig.face(), G[7], 2))
    for p in rig.eye_slots():
        o.append(outline(p, G[4], 1.2))
    for p in rig.eye_slits():
        o.append(outline(glow(p, v["cutoff"]), grey((2 + 3 * v["cutoff"]) / 7), 1.2))
        o.append(shape(p, G[7]))
    o.append(outline(rig.nose(), G[6], 1.5))
    for p in rig.nostrils():
        o.append(shape(p, G[5]))
    (rx, ry), rr = rig.ring()
    o.append(outline([(rx + math.cos(a) * rr, ry + math.sin(a) * rr) for a in [i * math.pi / 12 for i in range(24)]], G[6], 1.6))
    for x, y, r in steam(v, rig, playing):
        o.append(outline([(x + math.cos(a) * r, y + math.sin(a) * r) for a in [i * math.pi / 8 for i in range(16)]], G[4], 1.2))
    for y, hgt, dx in glitch(v, playing):                          # CRT tear: a band of scanlines offset
        o.append(shape([(CX - 60 + dx, y), (CX + 60 + dx, y), (CX + 60 + dx, y + 1.4), (CX - 60 + dx, y + 1.4)], G[6]))
    rnd = random.Random(8)
    for k in range(int(14 * v["noise"])):
        x = CX + rnd.uniform(-110, 110)
        o.append(outline([(x, BASE - 2), (x + rnd.uniform(-8, 8), BASE - 10 - rnd.uniform(0, 10))], G[6], 1.2, close=False))
    return frame(v, o)


# r2 · halftone --------------------------------------------------------------------------------------------------------
def inside(pt, polygon):
    x, y = pt
    c = False
    for (x1, y1), (x2, y2) in zip(polygon, polygon[1:] + polygon[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c


def halftone(v, playing=False):
    rig = Rig(v, playing)
    o = []
    regions = [(rig.body(), 0.22), (rig.face(), 0.85), (rig.nose(), 0.3)] + [(e, 0.45) for e in rig.ears()]
    glows = [glow(p, v["cutoff"]) for p in rig.eye_slits()]
    horns = [tube(*rig.horn(sd)) for sd in (-1, 1)]
    step = 5.0
    light = (-0.6, -0.8)
    xs = [p[0] for r, _ in regions for p in r] + [p[0] for hp in horns for p in hp]
    ys = [p[1] for r, _ in regions for p in r] + [p[1] for hp in horns for p in hp]
    for j in range(int(min(ys) / (step * 0.87)) - 1, int(max(ys) / (step * 0.87)) + 2):
        for i in range(int(min(xs) / step) - 1, int(max(xs) / step) + 2):
            x, y = i * step + (step / 2 if j % 2 else 0), j * step * 0.87
            tone = None
            for hp in horns:
                if inside((x, y), hp):
                    tone = 0.95
            for region, base in regions[::-1] if tone is None else []:
                if inside((x, y), region):
                    cx = sum(p[0] for p in region) / len(region); cy = sum(p[1] for p in region) / len(region)
                    tone = base + 0.35 * max(-1, min(1, ((x - cx) * light[0] + (y - cy) * light[1]) / 40))
                    break
            if tone is None:
                continue
            for slot in rig.eye_slots():
                if inside((x, y), slot):
                    tone = 0.0
            for gl in glows:
                if inside((x, y), gl):
                    tone = 1.0
            for slit in rig.eye_slits():
                if inside((x, y), slit):
                    tone = 1.0
            r = 0.3 + 2.3 * max(0.0, min(1.0, tone))
            if r >= 1.1:
                o.append(shape(dot(r, 10), G[7] if tone > 0.85 else G[6] if tone > 0.55 else G[5], x, y))
    o.append(shape(ribbon([(CX, BASE - 12), (CX, rig.top)], 7), G[4]))
    o.append(shape([(CX - 26, BASE), (CX + 26, BASE), (CX + 20, BASE - 10), (CX - 20, BASE - 10)], G[3]))
    (rx, ry), rr = rig.ring()
    o.append(shape(annulus(rr, 2.2, 24), G[7], rx, ry))
    for x, y, r in steam(v, rig, playing):
        for k in range(5):
            a = k * 2 * math.pi / 5
            o.append(shape(dot(1.6 + r * 0.25, 8), G[5], x + math.cos(a) * r * 0.7, y + math.sin(a) * r * 0.7))
    for y, hgt, dx in glitch(v, playing):
        o.append(shape([(CX - 70 + dx, y), (CX + 70 + dx, y), (CX + 70 + dx, y + hgt), (CX - 70 + dx, y + hgt)], G[0]))
    return frame(v, o)


# r3 · sumi-e ink --------------------------------------------------------------------------------------------------------
def brush(points, w0, w1, color, step=1.3):
    out = []
    pts = []
    for a, b in zip(points, points[1:]):
        d = math.dist(a, b)
        for k in range(max(1, int(d / step))):
            t = k / max(1, int(d / step))
            pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, math.atan2(b[1] - a[1], b[0] - a[0])))
    for i, (x, y, ang) in enumerate(pts):
        s = i / max(1, len(pts) - 1)
        w = w0 + (w1 - w0) * s
        ell = [(math.cos(t) * w, math.sin(t) * w * 0.55) for t in [k * math.pi / 6 for k in range(12)]]
        out.append(shape(rot(ell, math.degrees(ang) + 90), color, x, y))
    return out


def ink(v, playing=False):
    rig = Rig(v, playing)
    o = []
    cx, cy = CX, rig.top - 30 * S
    sweep = [(cx + math.cos(a) * 96, cy + 10 + math.sin(a) * 74) for a in [-math.pi * 0.62 + 2 * math.pi * 0.88 * k / 60 for k in range(61)]]
    o += brush(sweep, 3.4, 0.8, G[3])                              # an ensō frames the head
    for sd in (-1, 1):                                             # horns: one tapering stroke each
        spine, widths = rig.horn(sd)
        o += brush(spine, 4.2 * (1.1 if playing else 1), 1.0, G[7])
    face = rig.face()
    o += brush(face + face[:1], 1.8, 1.8, G[6])
    o += brush(rig.hump(), 2.2, 1.2, G[5])
    body = rig.body()
    o += brush(body[:12], 1.4, 1.0, G[4])
    for p in rig.eye_slits():
        gl = glow(p, v["cutoff"])
        o += brush(gl + gl[:1], 0.9, 0.9, grey((2 + 3 * v["cutoff"]) / 7))
        o.append(shape(p, G[7]))
    o += brush(rig.nose() + rig.nose()[:1], 1.3, 1.3, G[5])
    (rx, ry), rr = rig.ring()
    ring = [(rx + math.cos(a) * rr, ry + math.sin(a) * rr) for a in [-1.2 + 5.6 * k / 20 for k in range(21)]]
    o += brush(ring, 1.8, 0.8, G[6])
    o += brush([(CX, rig.top), (CX, BASE - 4)], 2.6, 2.2, G[4])
    o += brush([(CX - 40, BASE), (CX + 40, BASE)], 1.6, 0.6, G[3])
    rnd = random.Random(5)
    for x, y, r in steam(v, rig, playing):                        # drive: ink flung off as splatter
        for k in range(3):
            o.append(shape(dot(rnd.uniform(1.6, 2.8), 8), G[5], x + rnd.uniform(-r, r), y + rnd.uniform(-r, r)))
    for y, hgt, dx in glitch(v, playing):
        o.append(shape([(CX - 70 + dx, y), (CX + 70 + dx, y), (CX + 70 + dx, y + 1.6), (CX - 70 + dx, y + 1.6)], G[0]))
    return frame(v, o)


# r4 · isometric blocks ------------------------------------------------------------------------------------------------
def cube(x, y, s, hgt, top, left, right):
    t = [(x, y - hgt), (x + s, y + s * 0.5 - hgt), (x, y + s - hgt), (x - s, y + s * 0.5 - hgt)]
    l = [(x - s, y + s * 0.5 - hgt), (x, y + s - hgt), (x, y + s), (x - s, y + s * 0.5)]
    r = [(x, y + s - hgt), (x + s, y + s * 0.5 - hgt), (x + s, y + s * 0.5), (x, y + s)]
    return [shape(l, left), shape(r, right), shape(t, top)]


def iso(v, playing=False):
    rig = Rig(v, playing)
    o = []
    s = 5.5
    for i in range(-6, 7):                                         # platform
        for j in range(-2, 3):
            if abs(i) + abs(j) * 2 < 9:
                o += cube(CX + (i - j) * s, BASE - 12 + (i + j) * s * 0.35, s, 3, G[3], G[2], G[1])
    for k in range(6):                                             # the ram, a column of blocks
        o += cube(CX, BASE - 12 - k * 5, s, 5, G[4], G[3], G[2])
    def voxelize(polygon, depth_h, top, left, right):
        xs, ys = [p[0] for p in polygon], [p[1] for p in polygon]
        out = []
        for gy in range(int(min(ys)), int(max(ys)) + 1, 6):
            for gx in range(int(min(xs)), int(max(xs)) + 1, 6):
                if inside((gx + 3, gy + 3), polygon):
                    out += cube(gx + 3, gy + 3 - depth_h, 3.2, depth_h, top, left, right)
        return out
    o += voxelize(rig.body(), 4, G[3], G[2], G[1])
    for sd in (-1, 1):
        spine, widths = rig.horn(sd)
        for k, (x, y) in enumerate(spine[::2]):
            o += cube(x, y, 3.0 + 1.8 * (1 - k / 11), 4, G[7] if k > 8 else G[6], G[4], G[3])
    o += voxelize(rig.face(), 6, G[5], G[4], G[3])
    for p in rig.eye_slots():                                     # cutoff lights the whole socket, black → bright
        o.append(shape(p, grey(5.5 * v["cutoff"] / 7)))
    for p in rig.eye_slits():
        o.append(shape(p, G[7]))
    o += voxelize(rig.nose(), 7, G[6], G[4], G[3])
    (rx, ry), rr = rig.ring()
    o.append(shape(annulus(rr, 2.6, 24), G[6], rx, ry + 4))
    for x, y, r in steam(v, rig, playing):
        o += cube(x, y, 2.6 + r * 0.3, 2.6 + r * 0.3, G[4], G[3], G[2])
    for y, hgt, dx in glitch(v, playing):
        o.append(shape([(CX - 70 + dx, y), (CX + 70 + dx, y), (CX + 70 + dx, y + hgt), (CX - 70 + dx, y + hgt)], G[0]))
    return frame(v, o)


# r5 · Bauhaus -----------------------------------------------------------------------------------------------------------
def bauhaus(v, playing=False):
    rig = Rig(v, playing)
    o = []
    o.append(shape([(CX - 60, BASE + 2), (CX + 60, BASE + 2), (CX + 60, BASE - 4), (CX - 60, BASE - 4)], G[3]))  # floor bar
    o.append(shape(ribbon([(CX, BASE - 4), (CX, rig.top)], 9), G[4]))                                            # the ram
    o.append(shape(rig.body(), G[2]))
    o.append(shape(dot(14 * S, 40), G[3], *rig.to([(0, -46)])[0]))  # the hump as a circle behind the head
    for sd in (-1, 1):                                             # horns as thick tapering arcs
        spine, widths = rig.horn(sd)
        o.append(shape(tube(spine, [w * 1.25 for w in widths]), G[7] if sd > 0 else G[6]))
    o.append(shape(rig.face(), G[5]))
    for p in rig.eye_slots():                                     # cutoff lights the whole socket, black → bright
        o.append(shape(p, grey(5.5 * v["cutoff"] / 7)))
    for p in rig.eye_slits():
        o.append(shape(p, G[7]))
    o.append(shape(rig.nose(), G[4]))
    (rx, ry), rr = rig.ring()
    o.append(shape(annulus(rr, 3.2, 24), G[7], rx, ry))
    for x, y, r in steam(v, rig, playing):
        o.append(shape(dot(r, 24), G[3], x, y))
    rnd = random.Random(2)
    for k in range(int(20 * v["noise"])):
        x = CX + rnd.uniform(-90, 90)
        o.append(shape([(-2, -2), (2, -2), (2, 2), (-2, 2)], G[5], x, BASE - 8 - rnd.uniform(0, 12)))
    for y, hgt, dx in glitch(v, playing):
        o.append(shape([(CX - 70 + dx, y), (CX + 70 + dx, y), (CX + 70 + dx, y + hgt), (CX - 70 + dx, y + hgt)], G[0]))
    return frame(v, o)


STYLES = {"r1-crt": crt, "r2-halftone": halftone, "r3-ink": ink, "r4-iso": iso, "r5-bauhaus": bauhaus}


def main():
    D = dict(g.DEFAULTS)
    poses = {"rest": (D, False), "spread-100": (dict(D, spread=1), False), "cutoff-100": (dict(D, cutoff=1), False),
             "fold-100": (dict(D, fold=1), False), "aphx-100": (dict(D, aphx=1), False), "playing": (dict(D, drive=0.6), True)}
    for name, fn in STYLES.items():
        d = HERE / name
        d.mkdir(exist_ok=True)
        for pose, (vals, playing) in poses.items():
            (d / f"{pose}.svg").write_text(fn(vals, playing), encoding="utf-8")
    print("wrote", len(STYLES) * len(poses), "frames")


if __name__ == "__main__":
    main()
