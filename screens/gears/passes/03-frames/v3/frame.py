#!/usr/bin/env python3
"""Frames pass 03, v3: off-axis diagonal, front elevation, brightest on mesh.

    python3 screens/gears/passes/03-frames/v3/frame.py

The chosen subject (02-subject v4): two thick spur wheels, meshed, lit from
the upper left, shaded flanks hatched, faces black, B's web drilled at the
scale's seven of twelve positions.

This variant draws them in front elevation: the faces true shape, toward the
viewer, and the face width receding along one 45-degree diagonal (a cabinet
oblique, a parallel projection of the 3D model). Every flank therefore runs
down and right, away from the upper-left light, and is hatched across its
depth. The pair sits on a rising diagonal from lower left (A) to upper right
(B), off the screen's centre.

Mesh is the most-played control (score 5) and acts on face width: a tooth
that doesn't engage is milled to half width, so its flank is half as long on
the diagonal. The brightest element is the engaged tooth of A at full face
width: its front profile and its tip land run back the whole diagonal.

Defaults: ratio 3:2, teeth 8, mesh 100 %, scale maj. No text below the header.
"""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "gears_sketch02", HERE.parent.parent / "02-subject" / "sketch.py")
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)

poly, ribbon, loop, hatch, seg = S.poly, S.ribbon, S.loop, S.hatch, S.seg
G0, G1, G2, G3, G4, G5, G6, G7 = S.G0, S.G1, S.G2, S.G3, S.G4, S.G5, S.G6, S.G7
HAIR, LINE, SUBJ = S.HAIR, S.LINE, S.SUBJ
S.HEADER = [("ratio", "3:2"), ("teeth", "8"), ("mesh", "100%"), ("scale", "maj")]

TEETH_A, TEETH_B = S.TEETH_A, S.TEETH_B          # 8, 12
PCS = S.PCS                                       # maj pitch classes
MESH = 1.0
T = 4.0                                           # face width, world units
K = 0.55                                          # oblique foreshortening
DIRX, DIRY = math.cos(math.radians(45)), math.sin(math.radians(45))
THETA = math.radians(27)                          # line of centres, rising


def euclid(n, k):
    """Which of n teeth engage when k of them do (Euclidean order)."""
    return [((i * k) % n) < k for i in range(n)] if k else [False] * n


class View:
    def __init__(self):
        self.s, self.ox, self.oy = 1.0, 0.0, 0.0

    def raw(self, x, y, z):
        return (x + z * K * DIRX, -y + z * K * DIRY)

    def p(self, x, y, z=0.0):
        a, b = self.raw(x, y, z)
        return (self.ox + self.s * a, self.oy + self.s * b)

    def fit(self, pts, box):
        xs = [self.raw(*q)[0] for q in pts]
        ys = [self.raw(*q)[1] for q in pts]
        x0, y0, x1, y1 = box
        self.s = min((x1 - x0) / (max(xs) - min(xs)), (y1 - y0) / (max(ys) - min(ys)))
        self.ox = x0 - self.s * min(xs) + ((x1 - x0) - self.s * (max(xs) - min(xs))) / 2
        self.oy = y0 - self.s * min(ys) + ((y1 - y0) - self.s * (max(ys) - min(ys))) / 2


def wheel(N, rp, cx, cy, rot, width):
    """Outline (world, CCW) and per-edge face width (teeth milled or not)."""
    o = S.gear2d(N, rp, rot=rot)
    o = [(cx + x, cy + y) for x, y in o]
    # edges inside a tooth (root->tip, tip land, tip->root) take that tooth's
    # width; the root land between teeth stays full (the rim is never milled)
    w = []
    for t in range(N):
        for j in range(4):
            w.append(width[t] if j < 3 else T)
    return o, w


def walls(view, o, w):
    """Visible flank quads: (order key, screen quad, edge index)."""
    out = []
    d = (DIRX, -DIRY)                             # depth direction in world x, y
    n = len(o)
    for i in range(n):
        a, b = o[i], o[(i + 1) % n]
        ex, ey = b[0] - a[0], b[1] - a[1]
        L = math.hypot(ex, ey)
        nx, ny = ey / L, -ex / L                  # CCW: right of edge is outside
        if nx * d[0] + ny * d[1] <= 0.02:
            continue
        z = w[i]
        q = [view.p(*a, 0), view.p(*b, 0), view.p(*b, z), view.p(*a, z)]
        key = ((a[0] + b[0]) / 2) * d[0] + ((a[1] + b[1]) / 2) * d[1]
        out.append((key, q, i))
    return out


def circle(cx, cy, r, n=28):
    return [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def main():
    rpA, rpB = TEETH_A / 2, TEETH_B / 2
    dAB = rpA + rpB
    A = (0.0, 0.0)
    B = (dAB * math.cos(THETA), dAB * math.sin(THETA))
    rotA = THETA                                   # A's tooth 0 points at B
    rotB = THETA + math.pi + math.pi / TEETH_B     # B shows a gap to it
    wA = [T if e else T / 2 for e in euclid(TEETH_A, round(MESH * TEETH_A))]
    wB = [T if e else T / 2 for e in euclid(TEETH_B, round(MESH * TEETH_B))]
    oA, eA = wheel(TEETH_A, rpA, *A, rotA, wA)
    oB, eB = wheel(TEETH_B, rpB, *B, rotB, wB)

    view = View()
    pts = [(x, y, z) for x, y in oA + oB for z in (0, T)]
    view.fit(pts, (40, 27, 440, 213))
    view.ox += 48                                  # off-axis: mesh point right of centre

    out = []
    # flanks of both wheels, painter's order along the depth diagonal
    allw = [(k, q, "A", i) for k, q, i in walls(view, oA, eA)] + \
           [(k, q, "B", i) for k, q, i in walls(view, oB, eB)]
    allw.sort(key=lambda r: r[0])
    for _, q, _, _ in allw:
        out.append(poly(q, G0, G4, LINE))
        out += hatch([q], spacing=3.3, fill=G3, slope=1)

    # front faces, black, nearest of all
    for o, (cx, cy), rp, N in ((oB, B, rpB, TEETH_B), (oA, A, rpA, TEETH_A)):
        face = [view.p(x, y) for x, y in o]
        out.append(poly(face, G0, G5, LINE))
        out.append(loop([view.p(x, y) for x, y in circle(cx, cy, rp - 1.75, 48)], HAIR, G3))

    # A's hub: a bore, its wall seen down the diagonal, hatched
    for (cx, cy), r in ((A, 1.0), (B, 1.25)):
        bore = [view.p(x, y) for x, y in circle(cx, cy, r, 28)]
        out.append(poly(bore, G0, G4, LINE))
        out += hatch([bore], spacing=3.3, fill=G3, slope=1)
        out.append(loop([view.p(x, y) for x, y in circle(cx, cy, r + 0.75, 32)], HAIR, G3))

    # B's web: drilled at the scale's degrees, spot-faced elsewhere
    for k in range(12):
        a = rotB + math.pi / 2 - 2 * math.pi * k / 12
        hx, hy = B[0] + 3.2 * math.cos(a), B[1] + 3.2 * math.sin(a)
        if k in PCS:
            hole = [view.p(x, y) for x, y in circle(hx, hy, 0.62, 20)]
            out.append(poly(hole, G0, G4, LINE))
            out += hatch([hole], spacing=3.3, fill=G3, slope=1)
        else:
            out.append(loop([view.p(x, y) for x, y in circle(hx, hy, 0.34, 14)], HAIR, G3))

    # brightest: A's engaged tooth at full face width -- the part mesh moves.
    # Front profile (root, flank, tip, flank, root) and the tip land's far edge.
    t0 = oA[0:4]
    prof = [view.p(x, y) for x, y in t0]
    out.append(ribbon(prof, SUBJ, G7))
    return S.frame(out)


if __name__ == "__main__":
    (HERE / "rest.svg").write_text(main())
    print(HERE / "rest.svg")
