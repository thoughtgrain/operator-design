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

build(values, notes) is the one drawing: rest.svg is build(defaults, 0) and
bench.py's frame() calls the same function.
    ratio  B's tooth count is A's times the ratio; B grows and slides right.
    teeth  A re-cut with 3..16 teeth (module eased so the pair keeps its size).
    mesh   teeth outside a Euclidean pattern are milled to half the face width.
    scale  B's drilled holes move to the scale's positions of twelve.
    notes  the hatch thickens toward the mesh: a density gradient centred on
           the tooth in contact, and the root hole's bore closes up.
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

DEF = Path(__file__).resolve().parents[3] / "definition.json"
RATIOS = [(1, 1), (5, 4), (4, 3), (7, 5), (3, 2), (5, 3), (7, 4), (2, 1), (3, 1)]
SCALES = {
    "maj": {0, 2, 4, 5, 7, 9, 11}, "min": {0, 2, 3, 5, 7, 8, 10},
    "dor": {0, 2, 3, 5, 7, 9, 10}, "phr": {0, 1, 3, 5, 7, 8, 10},
    "lyd": {0, 2, 4, 6, 7, 9, 11}, "mix": {0, 2, 4, 5, 7, 9, 10},
    "pent": {0, 2, 4, 7, 9}, "hira": {0, 2, 3, 7, 8},
}

# where the column discipline wants things (screen x of the wheel centres)
XA, XB = 192, 374
X_RIGHT = 520        # B's rim box may run off the right edge this far (it does at rest)
SPAN = 180           # tallest the pair's rim box may get in the body


def params():
    import json
    return json.loads(DEF.read_text())["parameters"]


def defaults():
    return {p["id"]: float(p["default"]) for p in params()}


def pick(v, labels):
    i = round(min(1.0, max(0.0, v)) * (len(labels) - 1))
    return i, labels[i]


def euclid(k, n):
    """k hits spread over n steps, a hit at step 0."""
    return [((i * k) % n) < k for i in range(n)]


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


def build(values=None, notes=0.0):
    ps = {p["id"]: p for p in params()}
    vals = {**defaults(), **(values or {})}
    ri, rlab = pick(vals["ratio"], ps["ratio"]["mapping"]["labels"])
    ti, tlab = pick(vals["teeth"], ps["teeth"]["mapping"]["labels"])
    _, slab = pick(vals["scale"], ps["scale"]["mapping"]["labels"])
    mesh = min(1.0, max(0.0, vals["mesh"]))
    notes = min(1.0, max(0.0, notes))
    S.HEADER = [("ratio", rlab), ("teeth", tlab), ("mesh", f"{round(mesh * 100)}%"),
                ("scale", slab)]
    p, q = RATIOS[ri]
    NA = int(tlab)
    NB = max(3, round(NA * p / q))
    pcs = SCALES[slab]

    # module eased so A at 3:2 keeps the rest frame's pair width; capped for
    # very few teeth so a three-tooth wheel reads small, not bloated
    m = min(1.6, 10.0 / (NA * 1.25))
    rpA, rpB = NA * m / 2, NB * m / 2
    dAB = rpA + rpB
    dRef = rpA * 2.5                             # where B's centre is at 3:2
    T = 2.3
    yaw = math.radians(18)                       # B sits behind and right of A
    u = (math.cos(yaw), 0.0, -math.sin(yaw))
    up = (0.0, 1.0, 0.0)
    v = cross(up, u)                              # u x v = up
    rotA = math.pi / NA                           # A shows a gap toward B
    rotB = math.pi                                # B's tooth 0 sits in it
    oA = S.gear2d(NA, rpA, m=m, rot=rotA)
    oB = S.gear2d(NB, rpB, m=m, rot=rotB)
    cB = mul(u, dAB)

    # low camera: about 21 degrees over the top faces
    cam = S.Cam(eye=(2.0, 9.0, 24.0), target=(5.0, 0.4, -2.0))
    # fit: A's centre to XA, B's centre (at 3:2) to XB, the pair centred in the body
    gA0 = S.Disc((0, 0, 0), u, v, oA, T)
    ca, cb = cam.raw(gA0.w(0, 0, T)), cam.raw(S.Disc(mul(u, dRef), u, v, oB, T).w(0, 0, T))
    gB0 = S.Disc(cB, u, v, oB, T)
    pts = [g.w(x, y, z) for g, r in ((gA0, rpA + m), (gB0, rpB + m))
           for x, y in S.ring(r, 24) for z in (0, T)]
    raw = [cam.raw(pt) for pt in pts]

    def place(s):
        cam.s = s
        cam.ox = XA - cam.s * ca[0]
        ys = [r[1] for r in raw]
        y0, y1 = min(ys), max(ys)
        cam.oy = (38 + 214) / 2 - cam.s * (y0 + y1) / 2
        return y0, y1

    y0, y1 = place((XB - XA) / (cb[0] - ca[0]))
    # a bigger B shrinks the pair about A's centre until it fits
    right = cam.ox + cam.s * max(r[0] for r in raw)
    span = cam.s * (y1 - y0)
    k = min(1.0, (X_RIGHT - XA) / (right - XA), SPAN / span)
    if k < 1.0:
        place(cam.s * k)

    light = norm((-1.0, 0.8, 0.85))
    out = []

    # playing: hatch density gathers toward the tooth in contact
    hot = cam.p(add(mul(u, rpA), (0.0, T, 0.0)))
    reach = 0.30 * cam.s * dAB

    def heat(q):
        if notes <= 0:
            return 0.0
        c = cam.ps(q)
        mx, my = sum(x for x, _ in c) / 4, sum(y for _, y in c) / 4
        d = math.dist((mx, my), hot)
        return notes * max(0.0, 1.0 - d / reach)

    def prism(g):
        o = []
        for _, q, nw in g.sides(cam):
            sq = cam.ps(q)
            o.append(poly(sq, G0, G4, LINE))
            sp = spacing_for(dot(nw, light))
            h = heat(q)
            if h > 0:
                sp = max(2.4, (sp or 9.0) * (1 - 0.6 * h)) if (sp or h > 0.35) else sp
            if sp:
                o += axial_hatch(cam, q, sp)
        cap = g.cap(cam, g.o)
        o.append(poly(cap, G0, G5, LINE))
        return o

    def wheel(c, N, rp, rot, hits):
        """The wheel as one prism, or a full-width lower half and a top half
        whose milled teeth are cut back to the root."""
        full = S.Disc(c, u, v, S.gear2d(N, rp, m=m, rot=rot), T)
        if all(hits):
            return full, prism(full)
        low = S.Disc(c, u, v, S.gear2d(N, rp, m=m, rot=rot), T / 2)
        top = S.Disc(add(c, (0.0, T / 2, 0.0)), u, v,
                     S.gear2d(N, rp, m=m, rot=rot, tips=[1 if h else 0 for h in hits]), T / 2)
        return top, prism(low) + prism(top)

    hitsA = euclid(round(mesh * NA), NA)
    hitsB = euclid(round(mesh * NB), NB)

    # B is further: draw it first
    gB, o = wheel(cB, NB, rpB, rotB, hitsB)
    out += o
    rrB = rpB - 1.25 * m
    out.append(loop(gB.cap(cam, S.ring(rpB - 1.25 * m - 0.55 * m, 60)), HAIR, G3))
    out.append(loop(gB.cap(cam, S.ring(min(1.6, 0.27 * rpB), 32)), HAIR, G3))
    out.append(loop(gB.cap(cam, S.ring(min(0.7, 0.12 * rpB), 20)), LINE, G4))
    rh = 3.3 * (rpB / 6.0)                        # the drilled web's pitch circle
    hr = min(0.6, 0.2 * rh, 0.4 * (rrB - rh))
    for k in range(12):
        a = rotB - 2 * math.pi * k / 12 + math.pi / 2
        hx, hy = rh * math.cos(a), rh * math.sin(a)
        if k in pcs:
            hole = [(hx + hr * math.cos(t), hy + hr * math.sin(t))
                    for t in [2 * math.pi * i / 24 for i in range(24)]]
            hs = gB.cap(cam, hole)
            out.append(poly(hs, G0, G4, LINE))
            # the bore's wall, in shade; the root's bore closes up while a note sounds
            out += vertical_hatch(hs, 3.2 - (0.8 * notes if k == 0 else 0.0))
        else:
            mr = 0.32 * hr / 0.6
            mark = [(hx + mr * math.cos(t), hy + mr * math.sin(t))
                    for t in [2 * math.pi * i / 12 for i in range(12)]]
            out.append(loop(gB.cap(cam, mark), HAIR, G3))
    gA, o = wheel((0, 0, 0), NA, rpA, rotA, hitsA)
    out += o
    rrA = rpA - 1.25 * m
    out.append(loop(gA.cap(cam, S.ring(rpA - 1.25 * m - 0.5 * m, 40)), HAIR, G3))
    out.append(loop(gA.cap(cam, S.ring(min(1.2, 0.5 * rrA), 28)), HAIR, G3))
    out.append(loop(gA.cap(cam, S.ring(min(0.55, 0.25 * rrA), 20)), LINE, G4))
    # brightest: the top edge of B's tooth standing in A's gap (the mesh)
    tB = S.gear2d(NB, rpB, m=m, rot=rotB)[0:4]
    if hitsB[0]:
        out.append(ribbon(gB.cap(cam, tB), SUBJ, G7))
    else:
        out.append(ribbon(cam.ps([gB0.w(x, y, T / 2) for x, y in tB]), SUBJ, G7))
    return S.frame(out)


if __name__ == "__main__":
    (HERE / "rest.svg").write_text(build())
    print(HERE / "rest.svg")
