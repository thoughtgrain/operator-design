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

TEETH_A = 8
TEETH_B = 12
SCALE = {0, 2, 4, 5, 7, 9, 11}  # maj: drilled positions of twelve
S = 24.0                        # px per module
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
def gear(N, rp, rot):
    """Involute spur outline (module 1, units), root lands rounded; tooth t at rot + t * pitch."""
    rr = rp - 1.25 * M
    pts = []
    pitch = 2 * math.pi / N
    for t in range(N):
        c = rot + t * pitch
        tooth = s02.involute_tooth(rp, M, c, n=6)
        pts += tooth
        # root land to the next tooth
        a0 = math.atan2(tooth[-1][1], tooth[-1][0])
        nxt = s02.involute_tooth(rp, M, c + pitch, n=6)[0]
        a1 = math.atan2(nxt[1], nxt[0])
        while a1 < a0:
            a1 += 2 * math.pi
        for k in (1, 2):
            a = a0 + (a1 - a0) * k / 3
            pts.append((rr * math.cos(a), rr * math.sin(a)))
    return pts


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
# Line of centres falls a few degrees to the right so the pair sits on a slant.
TILT = math.radians(-5)
rpA, rpB = TEETH_A / 2, TEETH_B / 2
e = (math.cos(TILT), math.sin(TILT))
CA = (98.0, 132.0)
CB = (CA[0] + S * (rpA + rpB) * e[0], CA[1] + S * (rpA + rpB) * e[1])
th = math.atan2(e[1], e[0])
rotA = th + math.pi / TEETH_A          # A shows a gap to B
rotB = th + math.pi                    # B's tooth 0 sits in it
OA = to_screen(CA, gear(TEETH_A, rpA, rotA))
OB = to_screen(CB, gear(TEETH_B, rpB, rotB))
HOLE_R, HOLE_AT = 0.66, 3.35
holes, spots = [], []
for k in range(12):
    a = rotB + 2 * math.pi * k / 12          # position 0 behind the meshing tooth, then clockwise on screen
    hc = (HOLE_AT * math.cos(a), HOLE_AT * math.sin(a))
    (holes if k in SCALE else spots).append(hc)
HOLES = [to_screen(CB, circle(HOLE_R, 32, h)) for h in holes]
ARBOR_A = to_screen(CA, circle(0.62, 28))
ARBOR_B = to_screen(CB, circle(0.75, 32))


def solid(p):
    if inside(p, OA):
        return True
    if inside(p, OB):
        return not any(inside(p, h) for h in HOLES)
    return False


def in_cast(p, d, src):
    for t in (0.2, 0.4, 0.6, 0.8, 1.0):
        if src((p[0] - d[0] * t, p[1] - d[1] * t)):
            return True
    return False


def plate_shadow(p):
    """Plate seen past the wheels, in the wheels' cast shadow."""
    return not solid(p) and in_cast(p, SHADOW, solid)


def arbor(p):
    return inside(p, ARBOR_A) or inside(p, ARBOR_B)


def face_shadow(p):
    """A top face, in the shadow of its arbor."""
    return solid(p) and not arbor(p) and in_cast(p, ARBOR_SHADOW, arbor)


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


def body():
    out = []
    box = (X0, TOP + 0.5, X1, Y1)
    # cast shadows on the plate: the wheels' mass
    out += hatch_by(plate_shadow, box)
    # arbor shadows on the faces (small, same hatch)
    for C, r in ((CA, 0.62), (CB, 0.75)):
        R = S * r + 8
        out += hatch_by(face_shadow, (C[0] - R, max(TOP + 0.5, C[1] - R), C[0] + R + 8, C[1] + R + 8))
    # top faces: outlines only, the face stays black
    for O in (OA, OB):
        out.append(ribbon(O + [O[0]], LINE, G5))
    # web detail: rim and hub turned on each face, hairlines
    out.append(loop(to_screen(CA, circle(rpA - 1.25 - 0.55, 56)), HAIR, G3))
    out.append(loop(to_screen(CA, circle(1.35, 36)), HAIR, G3))
    out.append(loop(to_screen(CB, circle(rpB - 1.25 - 0.55, 72)), HAIR, G3))
    out.append(loop(to_screen(CB, circle(1.75, 40)), HAIR, G3))
    # arbors: the shaft ends, standing proud of the faces
    out.append(loop(ARBOR_A, LINE, G4))
    out.append(loop(ARBOR_B, LINE, G4))
    # B's web: drilled through at the scale's degrees, a spot-face where it isn't
    for H in HOLES:
        out.append(loop(H, LINE, G4))
    for h in spots:
        out.append(loop(to_screen(CB, circle(0.28, 16, h)), HAIR, G3))
    # the sound source: B's tooth in A's gap, its top edge the one bright line
    tooth = to_screen(CB, s02.involute_tooth(rpB, M, rotB, n=6))
    out.append(ribbon(tooth, SUBJ, G7))
    return out


def main():
    s02.HEADER = [("ratio", "3:2"), ("teeth", "8"), ("mesh", "100%"), ("scale", "maj")]
    svg = s02.frame(body())
    (HERE / "rest.svg").write_text(svg)
    print(HERE / "rest.svg")


if __name__ == "__main__":
    main()
