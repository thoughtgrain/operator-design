#!/usr/bin/env python3
"""Lattice v2 (P1 section drawing, hidden-line isometric), cleaned for today's rules.

    python3 screens/lattice/passes/01-subject/v2/clean.py

Writes clean.svg beside this file. Same plate, frame, striker, stylus and
damper as sketch.py's v2, with three changes:

- No text: the "strike", "pickup" and "damper" labels and the pickup's leader
  to its label are gone. The parts tell themselves apart by shape: the striker
  is a rod with a hammer head, the pickup a stylus pin on a short tonearm with
  a pivot, the damper a hanging block on its cord.
- No grey-filled solids: the frame's near faces, the striker head and the
  damper were filled #323232/#4B4B4B. They're now hidden-line, black bodies
  with mid-grey edges.
- The damper's landing footprint (a ghost of where it will be) is hatched at
  45 degrees inside a hairline outline over a black body (so the mesh doesn't
  cross the hatching), instead of a 3 px dashed outline.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from sketch import (Svg, HEADER, DEF, STRIKE, size_n, pickup_xy, field,  # noqa: E402
                    seg)


def clip_convex(p, q, poly):
    """Cyrus-Beck clip of segment pq to a convex polygon (any winding)."""
    t0, t1 = 0.0, 1.0
    d = (q[0] - p[0], q[1] - p[1])
    n = len(poly)
    area = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    sgn = 1 if area > 0 else -1
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        # inward normal
        nx, ny = -(b[1] - a[1]) * sgn, (b[0] - a[0]) * sgn
        num = nx * (p[0] - a[0]) + ny * (p[1] - a[1])
        den = nx * d[0] + ny * d[1]
        if den == 0:
            if num < 0:
                return None
            continue
        t = -num / den
        if den > 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
    if t0 >= t1:
        return None
    return (p[0] + t0 * d[0], p[1] + t0 * d[1]), (p[0] + t1 * d[0], p[1] + t1 * d[1])


def hatch_poly(s: Svg, poly, gap, fill, w=1.0, inset=1.0):
    """45-degree hairlines, gap px apart, clipped to a convex polygon (shrunk by inset)."""
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    inner = []
    for x, y in poly:
        dx, dy = x - cx, y - cy
        L = math.hypot(dx, dy) or 1
        inner.append((x - dx / L * inset, y - dy / L * inset))
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    c = min(xs) - (max(ys) - min(ys)) - gap
    while c < max(xs) + gap:
        r = clip_convex((c, max(ys) + 1), (c + (max(ys) - min(ys)) + 2, min(ys) - 1), inner)
        if r and math.dist(*r) > 2.5:
            seg(r[0], r[1], w, fill, s)
        c += gap * math.sqrt(2)


def v2_clean():
    s = Svg(*HEADER)
    n = size_n(DEF["size"])
    k = 105 + (n - 4) * 6.5
    cx, cy = 222, 128
    vals = {}
    zs = 18.0

    def P(u, v, z=0.0):
        return (cx + (u - v) * k * 0.866, cy + (u + v - 1) * k * 0.5 - z)

    top = max(abs(field(u / 20, v / 20)) for u in range(21) for v in range(21)) or 1

    def Z(u, v):
        key = (round(u, 4), round(v, 4))
        if key not in vals:
            vals[key] = field(u, v) / top * zs
        return vals[key]

    e = 0.07
    # clamp frame: top ring and its two near faces, hidden-line (black body, grey edge)
    outer = [P(-e, -e), P(1 + e, -e), P(1 + e, 1 + e), P(-e, 1 + e)]
    th = 8
    s.path([P(1 + e, -e), P(1 + e, 1 + e), (P(1 + e, 1 + e)[0], P(1 + e, 1 + e)[1] + th),
            (P(1 + e, -e)[0], P(1 + e, -e)[1] + th)], "#000000", "#646464", 1.0)
    s.path([P(1 + e, 1 + e), P(-e, 1 + e), (P(-e, 1 + e)[0], P(-e, 1 + e)[1] + th),
            (P(1 + e, 1 + e)[0], P(1 + e, 1 + e)[1] + th)], "#000000", "#646464", 1.0)
    s.path(outer, "#000000", "#7D7D7D", 1.5)
    for (u, v) in ((-e / 2, -e / 2), (1 + e / 2, -e / 2), (1 + e / 2, 1 + e / 2), (-e / 2, 1 + e / 2),
                   (0.5, -e / 2), (0.5, 1 + e / 2), (-e / 2, 0.5), (1 + e / 2, 0.5)):
        x, y = P(u, v)
        s.circle(x, y, 2, "#000000", "#7D7D7D", 1.0)
    # plate: black body hides the frame's inner edge, then mesh lines, then outline
    edge = ([P(t / 16, 0, Z(t / 16, 0)) for t in range(16)] + [P(1, t / 16, Z(1, t / 16)) for t in range(16)] +
            [P(1 - t / 16, 1, Z(1 - t / 16, 1)) for t in range(16)] + [P(0, 1 - t / 16, Z(0, 1 - t / 16)) for t in range(16)])
    s.path(edge, "#000000", "none")
    for i in range(1, n - 1):
        a = i / (n - 1)
        s.line([P(a, t / 24, Z(a, t / 24)) for t in range(25)], 1.0, "#646464")
        s.line([P(t / 24, a, Z(t / 24, a)) for t in range(25)], 1.0, "#646464")
    # damper footprint on the plate: where the felt lands, hatched (a ghost, not a body)
    du, dv = 0.78, 0.12
    bw, bd, bh = 0.16, 0.08, 7
    base = [P(du - bw / 2, dv - bd / 2), P(du + bw / 2, dv - bd / 2), P(du + bw / 2, dv + bd / 2), P(du - bw / 2, dv + bd / 2)]
    s.path(base, "#000000", "#646464", 1.0)
    hatch_poly(s, base, 3.5, "#646464", 1.0, inset=1.5)
    s.path(edge, "none", "#CDCDCD", 2.25)
    # striker: rod and hammer head above the strike point
    sx, sy = P(*STRIKE, Z(*STRIKE))
    s.line([(sx, sy - 3), (sx, sy - 44)], 1.5, "#969696")
    s.path([(sx - 5, sy - 44), (sx + 5, sy - 44), (sx + 5, sy - 54), (sx - 5, sy - 54)], "#000000", "#AFAFAF", 1.5)
    s.circle(sx, sy, 2.5, "#000000", "#AFAFAF", 1.5)
    # pickup: a stylus pin at its point on a short tonearm to a pivot
    pu, pv = pickup_xy(DEF["pickup"])
    qx, qy = P(pu, pv, Z(pu, pv))
    s.line([(qx, qy - 3), (qx, qy - 26)], 1.5, "#969696")
    s.line([(qx, qy - 26), (qx + 36, qy - 26)], 1.5, "#969696")
    s.circle(qx + 39, qy - 26, 3, "#000000", "#969696", 1.5)
    s.circle(qx, qy, 2.5, "#000000", "#AFAFAF", 1.5)
    # damper: a felt block hanging on its cord; its height is set by damp
    lift = (1 - DEF["damp"]) * 40
    up = lambda p, h: (p[0], p[1] - h)
    b = [up(p, lift) for p in base]
    t = [up(p, lift + bh) for p in base]
    s.path([b[1], b[2], b[3], t[3], t[2], t[1]], "#000000", "#7D7D7D", 1.5)
    s.path(t, "#000000", "#7D7D7D", 1.5)
    s.line([((t[0][0] + t[2][0]) / 2, (t[0][1] + t[2][1]) / 2), ((t[0][0] + t[2][0]) / 2, 30)], 1.0, "#646464")
    return s


if __name__ == "__main__":
    out = HERE / "clean.svg"
    v2_clean().save(out)
    print(out)
