#!/usr/bin/env python3
"""Frames pass 03, v4: full-bleed field, top-down plan, brightest at the sound source.

    python3 screens/gears/passes/03-frames/v4/sketch.py

The chosen subject (two thick spur wheels, hatched mass, B's web drilled at the
scale's degrees) seen straight down from above, so close that both wheels run
off the frame. The wheels stand on a plate; light from the upper left throws
their thickness down and right as a cast shadow, hatched in hairlines. Top
faces stay black. The one bright line is B's tooth sitting in A's gap: the
pair that meets is the note.

Defaults: ratio 3:2 (A 8 teeth, B 12), teeth 8, mesh 100 %, scale maj.
Reuses the svg helpers of passes/02-subject/sketch.py (imported, unchanged).
"""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("s02", HERE.parent.parent / "02-subject" / "sketch.py")
s02 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s02)

G0, G1, G2, G3, G4, G5, G6, G7 = s02.G0, s02.G1, s02.G2, s02.G3, s02.G4, s02.G5, s02.G6, s02.G7
HAIR, LINE, SUBJ = 1.0, 1.5, 2.0
TOP = 22.0                      # nothing above this row: the stock header owns y 0-20
X0, X1, Y1 = 0.0, 480.0, 220.0

RATIOS = [("1:1", 1.0), ("5:4", 5 / 4), ("4:3", 4 / 3), ("7:5", 7 / 5), ("3:2", 3 / 2),
          ("5:3", 5 / 3), ("7:4", 7 / 4), ("2:1", 2.0), ("3:1", 3.0)]
TEETH = list(range(3, 17))
SCALES = [("maj", {0, 2, 4, 5, 7, 9, 11}), ("min", {0, 2, 3, 5, 7, 8, 10}), ("dor", {0, 2, 3, 5, 7, 9, 10}),
          ("phr", {0, 1, 3, 5, 7, 8, 10}), ("lyd", {0, 2, 4, 6, 7, 9, 11}), ("mix", {0, 2, 4, 5, 7, 9, 10}),
          ("pent", {0, 2, 4, 7, 9}), ("hira", {0, 2, 3, 7, 8})]   # drilled positions of twelve
RA_PX = 96.0                    # A's pitch radius on screen: teeth re-cut the wheel, they don't resize it
S = 24.0                        # px per module (set per frame: RA_PX / A's pitch radius)
M = 1.0
SHADOW = (11.0, 9.5)             # the wheels' thickness, cast down-right by light from the upper left
ARBOR_SHADOW = (5.0, 4.5)       # the arbors stand a little above the faces


# ------------------------------------------------------------- clipping
def clip_top(pts):
    """Sutherland-Hodgman against y >= TOP."""
    out = []
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        ia, ib = a[1] >= TOP, b[1] >= TOP
        if ia:
            out.append(a)
        if ia != ib:
            t = (TOP - a[1]) / (b[1] - a[1])
            out.append((a[0] + (b[0] - a[0]) * t, TOP))
    return out


_poly = s02.poly


def poly(pts, fill, stroke="none", sw=None):
    pts = clip_top(list(pts))
    if len(pts) < 3:
        return ""
    return _poly(pts, fill, stroke, sw)


s02.poly = poly          # ribbons and segments go through the clipped poly


def ribbon(pts, w, fill):
    return s02.ribbon(pts, w, fill)


def loop(pts, w, fill):
    return s02.loop(pts, w, fill)


# ------------------------------------------------------------- geometry
def gear_parts(N, rp, rot):
    """Involute spur outline (module 1, units) as [(tooth, land)] per tooth; tooth t at rot + t * pitch."""
    rr = rp - 1.25 * M
    parts = []
    pitch = 2 * math.pi / N
    for t in range(N):
        c = rot + t * pitch
        tooth = s02.involute_tooth(rp, M, c, n=6)
        land = []
        # root land to the next tooth
        a0 = math.atan2(tooth[-1][1], tooth[-1][0])
        nxt = s02.involute_tooth(rp, M, c + pitch, n=6)[0]
        a1 = math.atan2(nxt[1], nxt[0])
        while a1 < a0:
            a1 += 2 * math.pi
        for k in (1, 2):
            a = a0 + (a1 - a0) * k / 3
            land.append((rr * math.cos(a), rr * math.sin(a)))
        parts.append((tooth, land))
    return parts


def gear(N, rp, rot):
    pts = []
    for tooth, land in gear_parts(N, rp, rot):
        pts += tooth + land
    return pts


def milled_outline(N, rp, rot, high):
    """The full-height outline: a milled tooth is cut back to the root circle, so the step shows as an arc."""
    rr = rp - 1.25 * M
    pts = []
    for t, (tooth, land) in enumerate(gear_parts(N, rp, rot)):
        if high[t]:
            pts += tooth
        else:
            a0 = math.atan2(tooth[0][1], tooth[0][0])
            a1 = math.atan2(tooth[-1][1], tooth[-1][0])
            while a1 < a0:
                a1 += 2 * math.pi
            pts += [(rr * math.cos(a0 + (a1 - a0) * k / 4), rr * math.sin(a0 + (a1 - a0) * k / 4)) for k in range(5)]
        pts += land
    return pts


def euclid(k, n):
    """Euclidean hits of k in n, tooth 0 always a hit when k > 0."""
    return [(i * k) % n < k for i in range(n)]

def circle(r, n=40, c=(0.0, 0.0)):
    return [(c[0] + r * math.cos(2 * math.pi * k / n), c[1] + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def to_screen(C, pts):
    return [(C[0] + S * x, C[1] + S * y) for x, y in pts]


def inside(p, P):
    x, y = p
    c = False
    j = len(P) - 1
    for i in range(len(P)):
        xi, yi = P[i]
        xj, yj = P[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


# ------------------------------------------------------------- the scene
def hatch_by(pred, box, spacing=3.2, w=HAIR, fill=G3):
    """45-degree hairlines (rising to the right) wherever pred holds, sampled along each line."""
    x0, y0, x1, y1 = box
    stepc = spacing * math.sqrt(2)
    out = []
    c = math.floor((x0 + y0) / stepc) * stepc + stepc / 2
    ds = 0.25
    while c < x1 + y1:
        xs = max(x0, c - y1)
        xe = min(x1, c - y0)
        run = None
        x = xs
        while x <= xe + ds:
            p = (x, c - x)
            ok = x <= xe and pred(p)
            if ok and run is None:
                run = x
            elif not ok and run is not None:
                a, b = run + 0.4, x - ds - 0.4
                if b - a > 2.4:
                    out.append(s02.seg((a, c - a), (b, c - b), w, fill))
                run = None
            x += ds
        c += stepc
    return out


def in_cast(p, d, src):
    for t in (0.2, 0.4, 0.6, 0.8, 1.0):
        if src((p[0] - d[0] * t, p[1] - d[1] * t)):
            return True
    return False


def body(ratio_i=4, teeth_i=5, mesh=1.0, scale_i=0, notes=0.0):
    """The plan. ratio_i, teeth_i, scale_i are enum indices; mesh and notes run 0..1."""
    global S
    TEETH_A = TEETH[teeth_i]
    TEETH_B = max(3, round(TEETH_A * RATIOS[ratio_i][1]))
    SCALE = SCALES[scale_i][1]
    rpA, rpB = TEETH_A / 2, TEETH_B / 2
    S = RA_PX / rpA
    k = 24.0 / S                     # hub, arbor and hole sizes stay put on screen
    kb = rpB / 6.0                   # the ring of holes follows B's size
    # Line of centres falls a few degrees to the right so the pair sits on a slant.
    TILT = math.radians(-5)
    e = (math.cos(TILT), math.sin(TILT))
    CA = (98.0, 132.0)
    CB = (CA[0] + S * (rpA + rpB) * e[0], CA[1] + S * (rpA + rpB) * e[1])
    th = math.atan2(e[1], e[0])
    rotA = th + math.pi / TEETH_A          # A shows a gap to B
    rotB = th + math.pi                    # B's tooth 0 sits in it
    if notes > 0:
        # the note: the pair drives a quarter of a tooth further into contact
        d = notes * 0.25 * 2 * math.pi / TEETH_A
        rotA += d
        rotB -= d * TEETH_A / TEETH_B
    # mesh: A's teeth that don't engage are milled down, in Euclidean order
    hits = round(mesh * TEETH_A)
    high = euclid(hits, TEETH_A) if hits < TEETH_A else [True] * TEETH_A
    milled = not all(high)
    OA = to_screen(CA, gear(TEETH_A, rpA, rotA))
    OB = to_screen(CB, gear(TEETH_B, rpB, rotB))
    OA_HIGH = to_screen(CA, milled_outline(TEETH_A, rpA, rotA, high)) if milled else OA
    f = min(1.0, rpB * S / 144.0)      # B smaller than at rest: its hub, arbor and holes shrink with it
    hubB = 1.75 * k * f
    if f == 1.0:
        HOLE_R, HOLE_AT = 0.66 * k, 3.35 * kb
    else:
        rimB = rpB - 1.25 - 0.55
        HOLE_AT = hubB + (max(rimB, hubB) - hubB) * 0.55
        HOLE_R = min(0.66 * k * f, max(0.12, (max(rimB, hubB) - hubB) * 0.38))
    holes, spots = [], []
    for j in range(12):
        a = rotB + 2 * math.pi * j / 12          # position 0 behind the meshing tooth, then clockwise on screen
        hc = (HOLE_AT * math.cos(a), HOLE_AT * math.sin(a))
        (holes if j in SCALE else spots).append(hc)
    HOLES = [to_screen(CB, circle(HOLE_R, 32, h)) for h in holes]
    ARBOR_A = to_screen(CA, circle(0.62 * k, 28))
    ARBOR_B = to_screen(CB, circle(0.75 * k * f, 32))

    def solid_b(p):
        return inside(p, OB) and not any(inside(p, h) for h in HOLES)

    def solid(p):
        if inside(p, OA):
            return True
        if inside(p, OB):
            return not any(inside(p, h) for h in HOLES)
        return False

    def high_solid(p):
        return inside(p, OA_HIGH) or solid_b(p)

    def plate_shadow(p):
        """Plate seen past the wheels, in the wheels' cast shadow."""
        if not milled:
            return not solid(p) and in_cast(p, SHADOW, solid)
        if solid(p):
            # a milled tooth's top face, in the shadow of the full-height step
            return not high_solid(p) and in_cast(p, (SHADOW[0] / 2, SHADOW[1] / 2), high_solid)
        return in_cast(p, SHADOW, high_solid) or in_cast(p, (SHADOW[0] / 2, SHADOW[1] / 2), solid)

    def arbor(p):
        return inside(p, ARBOR_A) or inside(p, ARBOR_B)

    def face_shadow(p):
        """A top face, in the shadow of its arbor."""
        return solid(p) and not arbor(p) and in_cast(p, ARBOR_SHADOW, arbor)

    out = []
    box = (X0, TOP + 0.5, X1, Y1)
    # cast shadows on the plate: the wheels' mass
    out += hatch_by(plate_shadow, box)
    # arbor shadows on the faces (small, same hatch)
    for C, r in ((CA, 0.62 * k), (CB, 0.75 * k * f)):
        R = S * r + 8
        out += hatch_by(face_shadow, (C[0] - R, max(TOP + 0.5, C[1] - R), C[0] + R + 8, C[1] + R + 8))
    # top faces: outlines only, the face stays black
    for O in (OA_HIGH, OB):
        out.append(ribbon(O + [O[0]], LINE, G5))
    # milled teeth: their lower top faces in hairline, below the step
    if milled:
        for t, (tooth, _) in enumerate(gear_parts(TEETH_A, rpA, rotA)):
            if not high[t]:
                out.append(ribbon(to_screen(CA, tooth), HAIR, G4))
    # web detail: rim and hub turned on each face, hairlines
    for C, rp, hub, n_rim, n_hub in ((CA, rpA, 1.35 * k, 56, 36), (CB, rpB, hubB, 72, 40)):
        rim = rp - 1.25 - 0.55
        if rim > hub + 0.4 * k:
            out.append(loop(to_screen(C, circle(rim, n_rim)), HAIR, G3))
        out.append(loop(to_screen(C, circle(hub, n_hub)), HAIR, G3))
    # arbors: the shaft ends, standing proud of the faces
    out.append(loop(ARBOR_A, LINE, G4))
    out.append(loop(ARBOR_B, LINE, G4))
    # B's web: drilled through at the scale's degrees, a spot-face where it isn't
    for i, H in enumerate(HOLES):
        # playing: the hole for the sounding degree (position 0, beside the meshing tooth) lights
        out.append(loop(H, LINE, G6 if (notes > 0 and i == 0) else G4))
    for h in spots:
        out.append(loop(to_screen(CB, circle(0.28 * k * f, 16, h)), HAIR, G3))
    # the sound source: B's tooth in A's gap, its top edge the one bright line
    tooth = to_screen(CB, s02.involute_tooth(rpB, M, rotB, n=6))
    out.append(ribbon(tooth, SUBJ, G7))
    return out


def draw(ratio_i=4, teeth_i=5, mesh=1.0, scale_i=0, notes=0.0):
    s02.HEADER = [("ratio", RATIOS[ratio_i][0]), ("teeth", str(TEETH[teeth_i])),
                  ("mesh", f"{round(mesh * 100)}%"), ("scale", SCALES[scale_i][0])]
    return s02.frame(body(ratio_i, teeth_i, mesh, scale_i, notes))


def main():
    (HERE / "rest.svg").write_text(draw())
    print(HERE / "rest.svg")


if __name__ == "__main__":
    main()
