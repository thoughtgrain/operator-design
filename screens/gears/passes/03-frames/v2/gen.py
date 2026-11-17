#!/usr/bin/env python3
"""Frames pass 03, v2: column-affine (P7), low angle, density gradient.

    python3 screens/gears/passes/03-frames/v2/gen.py

The two thick spur wheels lie flat on one plane and are seen from a low
camera, so their flanks are tall and their top faces thin. Lit from the upper
left: every flank quad is hatched with lines parallel to the wheel's axis,
and their spacing follows how far that flank is turned from the light, so the
form is modelled by line density alone (dense on the shaded right, open on the
lit left, none on flanks facing the light). Top faces stay black.

Column affinity: A (teeth) stands under the teeth column, the mesh under the
mesh column, B's drilled web (scale) under the scale column. Ratio's part,
B's size, is read at B's near rim crossing column 2; column 0 is the lit side
and stays open.

Defaults: ratio 3:2 (A 8 teeth, B 12), mesh 100 %, scale maj (holes at
0 2 4 5 7 9 11 of 12). Not muted, no notes. Helpers from passes/02-subject.
"""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "sketch02", HERE.parent.parent / "02-subject" / "sketch.py")
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)

G0, G1, G2, G3, G4, G5, G6, G7 = S.G0, S.G1, S.G2, S.G3, S.G4, S.G5, S.G6, S.G7
HAIR, LINE, SUBJ = S.HAIR, S.LINE, S.SUBJ
poly, ribbon, seg, loop = S.poly, S.ribbon, S.seg, S.loop
cross, dot, norm, add, sub, mul = S.cross, S.dot, S.norm, S.add, S.sub, S.mul

TEETH_A, TEETH_B = 8, 12
PCS = {0, 2, 4, 5, 7, 9, 11}           # maj, on B's twelve positions

# where the column discipline wants things (screen x of the wheel centres)
XA, XB = 192, 374
S.HEADER = [("ratio", "3:2"), ("teeth", "8"), ("mesh", "100%"), ("scale", "maj")]


def axial_hatch(cam, q, spacing):
    """Lines parallel to the wheel axis across one flank quad
    (q = a0, b0, b1, a1 in world), `spacing` px apart along its screen width."""
    a0, b0, b1, a1 = q
    pa0, pb0 = cam.p(a0), cam.p(b0)
    pa1, pb1 = cam.p(a1), cam.p(b1)
    wpx = max(math.dist(pa0, pb0), math.dist(pa1, pb1))
    n = int(wpx / spacing)
    if n < 1:
        return []
    out = []
    edge = 1.6 / wpx                     # keep a sliver of black inside each edge
    for k in range(n):
        s = (k + 0.5) / n
        if s < edge or s > 1 - edge:
            continue
        top = cam.p(add(a1, mul(sub(b1, a1), s)))
        bot = cam.p(add(a0, mul(sub(b0, a0), s)))
        # inset 1 px from top and bottom edges
        L = math.dist(top, bot)
        if L < 4:
            continue
        ux, uy = (bot[0] - top[0]) / L, (bot[1] - top[1]) / L
        out.append(seg((top[0] + ux * 1.2, top[1] + uy * 1.2),
                       (bot[0] - ux * 1.2, bot[1] - uy * 1.2), HAIR, G4))
    return out


def vertical_hatch(P, spacing):
    """Vertical hairlines clipped to a screen polygon, `spacing` px apart."""
    xs = [p[0] for p in P]
    x0, x1 = min(xs), max(xs)
    n = int((x1 - x0) / spacing)
    out = []
    for k in range(n):
        x = x0 + (x1 - x0) * (k + 0.5) / n
        ys = []
        for a, b in zip(P, P[1:] + P[:1]):
            if (a[0] - x) * (b[0] - x) < 0:
                ys.append(a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]))
        ys.sort()
        for ya, yb in zip(ys[::2], ys[1::2]):
            if yb - ya > 5.6:
                out.append(seg((x, ya + 1.2), (x, yb - 1.2), HAIR, G3))
    return out


def spacing_for(lit):
    """Light on a flank (-1..1) to hatch spacing in px; None = left open."""
    if lit > 0.62:
        return None
    t = max(0.0, min(1.0, (lit + 0.45) / 1.07))  # 0 darkest .. 1 nearly lit
    return 3.2 + t * t * 10.0


def build():
    rpA, rpB = TEETH_A / 2, TEETH_B / 2
    dAB = rpA + rpB
    T = 2.3
    yaw = math.radians(18)                       # B sits behind and right of A
    u = (math.cos(yaw), 0.0, -math.sin(yaw))
    up = (0.0, 1.0, 0.0)
    v = cross(up, u)                              # u x v = up
    rotA = math.pi / TEETH_A                      # A shows a gap toward B
    rotB = math.pi                                # B's tooth 0 sits in it
    gA = S.Disc((0, 0, 0), u, v, S.gear2d(TEETH_A, rpA, rot=rotA), T)
    gB = S.Disc(mul(u, dAB), u, v, S.gear2d(TEETH_B, rpB, rot=rotB), T)

    # low camera: about 21 degrees over the top faces
    cam = S.Cam(eye=(2.0, 9.0, 24.0), target=(5.0, 0.4, -2.0))
    # fit: A's centre to XA, B's centre to XB, the pair centred in the body
    ca, cb = cam.raw(gA.w(0, 0, T)), cam.raw(gB.w(0, 0, T))
    cam.s = (XB - XA) / (cb[0] - ca[0])
    cam.ox = XA - cam.s * ca[0]
    pts = [g.w(x, y, z) for g, r in ((gA, rpA + 1), (gB, rpB + 1))
           for x, y in S.ring(r, 24) for z in (0, T)]
    ys = [cam.raw(p)[1] for p in pts]
    y0, y1 = min(ys), max(ys)
    cam.oy = (38 + 214) / 2 - cam.s * (y0 + y1) / 2

    light = norm((-1.0, 0.8, 0.85))
    out = []

    def mass(g):
        o = []
        for _, q, nw in g.sides(cam):
            sq = cam.ps(q)
            o.append(poly(sq, G0, G4, LINE))
            sp = spacing_for(dot(nw, light))
            if sp:
                o += axial_hatch(cam, q, sp)
        cap = g.cap(cam, g.o)
        o.append(poly(cap, G0, G5, LINE))
        return o

    # B is further: draw it first
    out += mass(gB)
    out.append(loop(gB.cap(cam, S.ring(rpB - 1.25 - 0.55, 60)), HAIR, G3))
    out.append(loop(gB.cap(cam, S.ring(1.6, 32)), HAIR, G3))
    out.append(loop(gB.cap(cam, S.ring(0.7, 20)), LINE, G4))
    for k in range(12):
        a = rotB - 2 * math.pi * k / 12 + math.pi / 2
        hx, hy = 3.3 * math.cos(a), 3.3 * math.sin(a)
        if k in PCS:
            hole = [(hx + 0.6 * math.cos(t), hy + 0.6 * math.sin(t))
                    for t in [2 * math.pi * i / 24 for i in range(24)]]
            hs = gB.cap(cam, hole)
            out.append(poly(hs, G0, G4, LINE))
            out += vertical_hatch(hs, 3.2)          # the bore's wall, in shade
        else:
            mark = [(hx + 0.32 * math.cos(t), hy + 0.32 * math.sin(t))
                    for t in [2 * math.pi * i / 12 for i in range(12)]]
            out.append(loop(gB.cap(cam, mark), HAIR, G3))
    out += mass(gA)
    out.append(loop(gA.cap(cam, S.ring(rpA - 1.25 - 0.5, 40)), HAIR, G3))
    out.append(loop(gA.cap(cam, S.ring(1.2, 28)), HAIR, G3))
    out.append(loop(gA.cap(cam, S.ring(0.55, 20)), LINE, G4))
    # brightest: the top edge of B's tooth standing in A's gap (the mesh)
    tB = S.gear2d(TEETH_B, rpB, rot=rotB)[0:4]
    out.append(ribbon(gB.cap(cam, tB), SUBJ, G7))
    return S.frame(out)


if __name__ == "__main__":
    (HERE / "rest.svg").write_text(build())
    print(HERE / "rest.svg")
