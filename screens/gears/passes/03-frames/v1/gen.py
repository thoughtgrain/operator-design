#!/usr/bin/env python3
"""Frames pass 03, v1: low horizon, three-quarter isometric, brightest where
the note lands.

    python3 screens/gears/passes/03-frames/v1/gen.py

The two spur wheels lie flat on their arbors, seen by one orthographic
(isometric) camera from a low three-quarter angle, so the pair is a long low
band near the bottom of the body with black above it. Lit from the upper
left: flanks turned from the light carry 45-degree hairlines, top faces stay
black. B's web is drilled at the scale's degrees (maj: 7 of 12). The one
brightest mark is the meshing tooth pair at the pitch point: where the note
lands. Defaults: ratio 3:2, teeth 8, mesh 100 %, scale maj, at rest.

Reuses the drawing helpers of passes/02-subject/sketch.py (ribbons, hatching,
gear outline, prism); the camera here is orthographic.
"""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
SK = HERE.parent.parent / "02-subject" / "sketch.py"
spec = importlib.util.spec_from_file_location("gears_sketch", SK)
sk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sk)

poly, ribbon, loop, seg = sk.poly, sk.ribbon, sk.loop, sk.seg


def hatch(polys, spacing=3.3, w=1.0, fill=None, minlen=4.6):
    """sketch.hatch, dropping stubs shorter than ~3 px (they read as dots)."""
    out = []
    for h in sk.hatch(polys, spacing=spacing, w=w, fill=fill):
        nums = [float(t) for t in h.split('d="')[1].split('"')[0].replace("M", " ").replace("L", " ").replace("Z", " ").split()]
        xs, ys = nums[0::2], nums[1::2]
        if math.hypot(max(xs) - min(xs), max(ys) - min(ys)) >= minlen:
            out.append(h)
    return out
gear2d, ring, Disc = sk.gear2d, sk.ring, sk.Disc
add, sub, mul, dot, cross, norm = sk.add, sk.sub, sk.mul, sk.dot, sk.cross, sk.norm
G0, G1, G2, G3, G4, G5, G6, G7 = sk.G0, sk.G1, sk.G2, sk.G3, sk.G4, sk.G5, sk.G6, sk.G7
HAIR, LINE, SUBJ = 1.0, 1.5, 2.0
W, H = 480, 220
FONT = sk.FONT
DEFINITION = HERE.parent.parent.parent / "definition.json"
RATIOS = [(1, 1), (5, 4), (4, 3), (7, 5), (3, 2), (5, 3), (7, 4), (2, 1), (3, 1)]
RATIO_LABELS = ["1:1", "5:4", "4:3", "7:5", "3:2", "5:3", "7:4", "2:1", "3:1"]
TEETH = list(range(3, 17))
SCALES = [("maj", {0, 2, 4, 5, 7, 9, 11}), ("min", {0, 2, 3, 5, 7, 8, 10}),
          ("dor", {0, 2, 3, 5, 7, 9, 10}), ("phr", {0, 1, 3, 5, 7, 8, 10}),
          ("lyd", {0, 2, 4, 6, 7, 9, 11}), ("mix", {0, 2, 4, 5, 7, 9, 10}),
          ("pent", {0, 2, 4, 7, 9}), ("hira", {0, 2, 3, 7, 8})]   # positions of twelve
DEFAULTS = {"ratio": 0.5, "teeth": 0.3846, "mesh": 1.0, "scale": 0.0}
RP_A = 4.0          # A's pitch radius stays put; teeth re-cut it at a new module


def pick(v, n):
    return min(n - 1, max(0, round(min(1.0, max(0.0, float(v))) * (n - 1))))


def model(values=None):
    """Control values (0..1 by definition id) to the drawing's numbers."""
    vals = {**DEFAULTS, **(values or {})}
    p, q = RATIOS[pick(vals["ratio"], len(RATIOS))]
    na = TEETH[pick(vals["teeth"], len(TEETH))]
    nb = max(3, round(na * p / q))
    m = 8 / na                                  # module: A keeps its size
    md = min(m, 0.35 * RP_A)                    # tooth depth, kept off the bore at 3 teeth
    mesh = min(1.0, max(0.0, float(vals["mesh"])))
    sname, scale = SCALES[pick(vals["scale"], len(SCALES))]
    header = [("ratio", RATIO_LABELS[pick(vals["ratio"], len(RATIOS))]), ("teeth", str(na)),
              ("mesh", f"{round(mesh * 100)}%"), ("scale", sname)]
    return dict(na=na, nb=nb, rpA=na * m / 2, rpB=nb * m / 2, md=md, mesh=mesh,
                scale=scale, header=header)


def euclid(n, k):
    """Which of n teeth keep their full face: k of them, evenly, tooth 0 always."""
    k = max(1, min(n, k))
    return [(t * k) % n < k for t in range(n)]


def gear2d(N, rp, md, rot=0.0, tips=None):
    """sketch.gear2d with the tooth depth apart from the pitch (identical at md = 1)."""
    ra, rr = rp + md, rp - 1.25 * md
    pitch = 2 * math.pi / N
    pts = []
    for t in range(N):
        a = rot + t * pitch
        rt = rr + (ra - rr) * (1 if tips is None else tips[t])
        for da, r in ((-0.31, rr), (-0.17, rt), (0.17, rt), (0.31, rr)):
            ang = a + da * pitch
            pts.append((r * math.cos(ang), r * math.sin(ang)))
    return pts


class Ortho:
    """Isometric-style camera: parallel rays along fw; depth = distance along fw."""

    def __init__(self, yaw_deg, elev_deg):
        y, e = math.radians(yaw_deg), math.radians(elev_deg)
        # camera sits at azimuth `yaw` (from +z towards -x), raised `elev`
        back = (-math.sin(y) * math.cos(e), math.sin(e), math.cos(y) * math.cos(e))
        self.fw = mul(back, -1)
        self.rt = norm(cross(self.fw, (0, 1, 0)))
        self.up = cross(self.rt, self.fw)
        self.eye_dir = back
        self.s, self.ox, self.oy = 1.0, 0.0, 0.0
        self.eye = mul(back, 1000.0)    # far point, for Disc.facing tests

    def raw(self, P):
        return (dot(P, self.rt), -dot(P, self.up))

    def fit_scale(self, pts, box, s=None):
        x0, y0, x1, y1 = box
        r = [self.raw(p) for p in pts]
        rx0, rx1 = min(p[0] for p in r), max(p[0] for p in r)
        ry0, ry1 = min(p[1] for p in r), max(p[1] for p in r)
        self.s = s or min((x1 - x0) / (rx1 - rx0), (y1 - y0) / (ry1 - ry0))
        self.ox = (x0 + x1) / 2 - self.s * (rx0 + rx1) / 2
        self.oy = y1 - self.s * ry1              # sit the pair on the box's floor

    def p(self, P):
        x, y = self.raw(P)
        return (self.ox + self.s * x, self.oy + self.s * y)

    def ps(self, Ps):
        return [self.p(P) for P in Ps]

    def dist(self, P):
        return -dot(P, self.eye_dir)

    def facing(self, P, n):
        return dot(n, self.eye_dir) > 0


def frame(body, header):
    steps = [G0, G1, G2, G3, G4, G5, G6, G7]
    hdr = [f'<rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>'
           for i, c in enumerate(steps)]
    for i, (t, v) in enumerate(header):
        ink = "#CBCBCB" if i < 2 else G0
        hdr.append(f'<text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{ink}" stroke="none" '
                   f'font-family="{FONT}" font-size="10px">{t}</text>')
        hdr.append(f'<text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{ink}" stroke="none" '
                   f'font-family="{FONT}" font-size="20px">{v}</text>')
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        '<!-- gears frames pass 03, v1: low horizon, three-quarter isometric, brightest where the note lands. '
        'Generated by gen.py. Static artwork; preview_* groups are scaffolding. -->',
        '<g id="preview_canvas">', f'<rect x="0" y="0" width="{W}" height="{H}" fill="{G0}" stroke="none"/>', '</g>',
        '<g id="preview_header">', *hdr, '</g>',
        *[b for b in body if b],
        '</svg>', ""])


T = 2.2                                       # face width (wheel thickness)
ARB = 1.6                                     # arbor rise above the top face
BOX = (40, 60, 440, 208)


def geometry(M):
    """Camera and the two wheels' placement for a model."""
    rpA, rpB, md = M["rpA"], M["rpB"], M["md"]
    dAB = rpA + rpB
    cam = Ortho(yaw_deg=34, elev_deg=21)
    # wheels lie flat: outline plane (u, v) horizontal, n = +y up
    u, v = (1, 0, 0), (0, 0, -1)
    # line of centres: B to the right and a little behind, roughly across the view
    # rt in (u, v) = (x, -z) coordinates, then turned a little away from the camera
    phi = math.atan2(-cam.rt[2], cam.rt[0]) + math.radians(9)
    cB2 = (dAB * math.cos(phi), dAB * math.sin(phi))
    rotA = phi                                 # A's tooth 0 points into B's gap
    rotB = phi + math.pi + math.pi / M["nb"]   # B presents a gap to A
    gA = Disc((0, 0, 0), u, v, gear2d(M["na"], rpA, md, rot=rotA), T)
    cB = gA.w(*cB2, 0)
    gB = Disc(cB, u, v, gear2d(M["nb"], rpB, md, rot=rotB), T)
    pts = [gA.w(x, y, z) for x, y in ring(rpA + md, 24) for z in (0, T)] + \
          [gB.w(x, y, z) for x, y in ring(rpB + md, 24) for z in (0, T + ARB)]
    return cam, gA, gB, rotA, rotB, pts


_S_REF = None


def s_ref():
    """The rest frame's scale: wheels never draw larger than this, so B visibly
    grows and shrinks against A instead of the fit cancelling the ratio."""
    global _S_REF
    if _S_REF is None:
        cam, *_, pts = geometry(model())
        cam.fit_scale(pts, BOX)
        _S_REF = cam.s
    return _S_REF


def build(values=None, notes=0.0):
    M = model(values)
    na, nb, rpA, rpB, md = M["na"], M["nb"], M["rpA"], M["rpB"], M["md"]
    cam, gA, gB, rotA, rotB, pts = geometry(M)
    probe = Ortho(yaw_deg=34, elev_deg=21)
    probe.fit_scale(pts, BOX)
    cam.fit_scale(pts, BOX, s=min(probe.s, s_ref()))
    light = norm((-1.0, 1.1, 0.5))
    out = []
    keepA = euclid(na, round(M["mesh"] * na))
    keepB = euclid(nb, round(M["mesh"] * nb))

    def shade(sq, nw):
        o = [poly(sq, G0, G4, LINE)]
        if dot(nw, light) < 0.15:
            o += hatch([sq], spacing=3.3, fill=G3)
        return o

    def sides(g):
        o = []
        for _, q, nw in g.sides(cam):
            o += shade(cam.ps(q), nw)
        return o

    def milled(g, keep):
        """A wheel whose non-engaging teeth are milled to half the face width:
        their faces stop at T/2 and the full-height body steps back to the root."""
        o4, n = g.o, len(g.o) // 4
        quads = []

        def side(a, b, z0, z1):
            ex, ey = b[0] - a[0], b[1] - a[1]
            L = math.hypot(ex, ey)
            if L < 1e-6:
                return
            nw = add(mul(g.u, ey / L), mul(g.v, -ex / L))
            mid = g.w((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (z0 + z1) / 2)
            if dot(nw, cam.eye_dir) > 0.06:                # skip walls seen edge-on
                quads.append((cam.dist(mid), [g.w(*a, z0), g.w(*b, z0), g.w(*b, z1), g.w(*a, z1)], nw))
        roots = []
        for t in range(n):
            rl, tl, tr, rr_ = o4[4 * t:4 * t + 4]
            nxt = o4[(4 * t + 4) % len(o4)]
            top = T if keep[t] else T / 2
            for a, b in ((rl, tl), (tl, tr), (tr, rr_)):
                side(a, b, 0, top)
            side(rr_, nxt, 0, T)                       # root land, full height
            if not keep[t]:
                # the step: the full body's wall across the tooth's root, T/2 up to T
                side(rl, rr_, T / 2, T)
                roots.append([rl, tl, tr, rr_])
        quads.sort(key=lambda r: -r[0])
        o = []
        for _, q, nw in quads:
            o += shade(cam.ps(q), nw)
        for tooth in roots:                            # milled faces at T/2
            o.append(poly(cam.ps([g.w(x, y, T / 2) for x, y in tooth]), G0, G5, LINE))
        return o

    def arbor(g, r, rise):
        # a plain round arbor standing up out of the hub: silhouette + top end
        top = [g.w(x, y, T + rise) for x, y in ring(r, 28)]
        bot = [g.w(x, y, T) for x, y in ring(r, 28)]
        hull = sk.convex_hull(cam.ps(top + bot))
        return [poly(hull, G0, G4, LINE), poly(cam.ps(top), G0, G5, LINE)]

    def web(g, rp, boss, outline):
        cap = cam.ps([g.w(x, y, T) for x, y in outline])
        o = [poly(cap, G0, G5, LINE) if len(cap) <= 64 else sk.big_poly(cap, G0, G5, LINE)]
        o.append(loop(cam.ps([g.w(x, y, T) for x, y in ring(rp - 1.25 * md - 0.55, 60)]), HAIR, G3))
        o.append(loop(cam.ps([g.w(x, y, T) for x, y in ring(boss, 36)]), HAIR, G3))
        return o

    def body(g, keep, N, rp, rot, boss):
        if all(keep):
            return sides(g) + web(g, rp, boss, g.o)
        top = [p for t, k in enumerate(keep) for p in (g.o[4 * t:4 * t + 4] if k else
                                                       (g.o[4 * t], g.o[4 * t + 3]))]
        return milled(g, keep) + web(g, rp, boss, top)

    # web furniture follows each wheel's root circle (1.0 at the rest frame's wheels)
    kA = (rpA - 1.25 * md) / 2.75
    kB = (rpB - 1.25 * md) / 4.75

    # ---- B, the far wheel
    out += body(gB, keepB, nb, rpB, rotB, 1.75 * kB)
    for k in range(12):
        a = rotB - 2 * math.pi * k / 12 + math.pi / 2
        hx, hy = 3.4 * kB * math.cos(a), 3.4 * kB * math.sin(a)
        if k in M["scale"]:
            hole = [(hx + 0.66 * kB * math.cos(t), hy + 0.66 * kB * math.sin(t))
                    for t in [2 * math.pi * i / 28 for i in range(28)]]
            hs = cam.ps([gB.w(x, y, T) for x, y in hole])
            out.append(poly(hs, G0, G4, LINE))
            out += hatch([hs], spacing=3.3, fill=G3)      # the bore wall, in shade
        else:
            mark = [(hx + 0.46 * kB * math.cos(t), hy + 0.46 * kB * math.sin(t))
                    for t in [2 * math.pi * i / 14 for i in range(14)]]
            out.append(loop(cam.ps([gB.w(x, y, T) for x, y in mark]), HAIR, G3))
    out += arbor(gB, 0.7 * kB, ARB)

    if notes >= 0.5:
        # a note held (drawn under A, which stands in front of it): the gap in B that the tooth lands in lights too, so the
        # meshing pair reads as one bright pinch at the pitch point
        oB = gB.o
        gap = [oB[-3], oB[-2], oB[-1], oB[0], oB[1], oB[2]]
        out.append(ribbon(cam.ps([gB.w(x, y, T) for x, y in gap]), 2.5, G7))

    # ---- A, the near driver
    out += body(gA, keepA, na, rpA, rotA, 1.3 * kA)
    out += arbor(gA, 0.6 * kA, ARB * 0.8)

    # ---- where the note lands: A's tooth 0 in B's gap, its top face's edge
    # at the subject weight, the one #CDCDCD mark in the frame
    tA = gA.o
    tooth = [tA[-1]] + tA[0:4] + [tA[4]]
    out.append(ribbon(cam.ps([gA.w(x, y, T) for x, y in tooth]), 2.5, G7))
    return frame(out, M["header"])


def main():
    (HERE / "rest.svg").write_text(build())
    print(HERE / "rest.svg")


if __name__ == "__main__":
    main()
