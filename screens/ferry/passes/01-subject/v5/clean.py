#!/usr/bin/env python3
"""Ferry v5, cleaned: survey sheets of each port stacked in route order.

    python3 screens/ferry/passes/01-subject/v5/clean.py

Writes clean.svg beside this file. Same model and defaults as sketch.py
(route up, 4 ports, swell 0, dwell 1/8); the helpers and the model are
imported from it, the drawing is new. No text below the header: a sheet
says which port it is by its height in the stack (its pitch), not a name.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from sketch import (DEFAULTS, G0, G2, G3, G4, G5, G7,  # noqa: E402
                    Svg, captions, n_ports, order, pitches, route)

SHEET_W, SHEET_H = 216, 108
STEP_X = 34            # one sheet back = this far right
STEP_Y = -4            # ... and this far up, before pitch
SEMI_Y = -1.6          # each semitone over the front port lifts a sheet this far
BODY_TOP, BODY_BOT = 26, 212


def ferry_hull(cx, cy, ang, L=30, B=10):
    """A double-ended ferry in plan: both ends the same blunt point, 10 points."""
    ca, sa = math.cos(ang), math.sin(ang)
    h = B / 2
    local = [(L / 2, 0), (L / 2 - 4, -h * 0.75), (L / 2 - 9, -h), (-L / 2 + 9, -h), (-L / 2 + 4, -h * 0.75),
             (-L / 2, 0), (-L / 2 + 4, h * 0.75), (-L / 2 + 9, h), (L / 2 - 9, h), (L / 2 - 4, h * 0.75)]
    return [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in local]


def wheelhouse(cx, cy, ang, l=8, b=5):
    ca, sa = math.cos(ang), math.sin(ang)
    local = [(l / 2, -b / 2), (l / 2, b / 2), (-l / 2, b / 2), (-l / 2, -b / 2)]
    return [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in local]


def clean(c=DEFAULTS) -> Svg:
    s = Svg()
    sw = c["swell"]
    n = n_ports(c)
    ps = pitches(n)
    seq = order(route(c), n, n)
    vis = min(n, 6)

    # sheet offsets from the model: back by route order, up by pitch over the front port
    offs = []
    for layer in range(vis):
        dp = ps[seq[layer]] - ps[seq[0]]
        offs.append((STEP_X * layer, STEP_Y * layer + SEMI_Y * dp))
    # place the stack so its whole extent sits in the body, centred both ways
    xs = [ox for ox, _ in offs]
    ys = [oy for _, oy in offs]
    span_x = max(xs) + SHEET_W
    span_y = max(ys) - min(ys) + SHEET_H
    fx = round((480 - span_x) / 2)
    fy = round(BODY_TOP + (BODY_BOT - BODY_TOP - span_y) / 2 - min(ys))

    # back sheets first: plain outlines, each a step quieter than the one in front
    edge = {1: G4, 2: G3, 3: G3, 4: G2, 5: G2}
    for layer in range(vis - 1, 0, -1):
        ox, oy = offs[layer]
        s.rect(fx + ox, fy + oy, SHEET_W, SHEET_H, G0, edge[layer], 1.0)

    # the front sheet: the port the ferry lies at, a harbour in plan
    x, y = fx, fy
    s.rect(x, y, SHEET_W, SHEET_H, G0, G5, 1.5)

    # land in the top-left corner: the coast a quarter ellipse, two depth contours seaward
    rx0, ry0 = 96.0, 48.0
    k = rx0 / ry0                           # contours keep the coast's proportions

    def shore(t, off):
        a = t * math.pi / 2
        wob = sw * 3 * math.sin(t * 15 + off * 0.3)
        return (x + (rx0 + off * k + wob) * math.sin(a), y + (ry0 + off + wob) * math.cos(a))

    inset = 3.0
    for j, off in enumerate((0, 8, 16)):
        pts = [shore(t / 40, off) for t in range(41)]
        pts = [(px, py) for px, py in pts if px > x + inset and py > y + inset
               and px < x + SHEET_W - inset and py < y + SHEET_H - inset]
        s.ribbon(pts, 1.5 if j == 0 else 1.0, G5 if j == 0 else G3)

    # the pier: straight out from the coast, square to it, past the contours
    t0 = 0.5
    px0, py0 = shore(t0, 0)
    a = t0 * math.pi / 2
    nx, ny = math.sin(a) / rx0, math.cos(a) / ry0          # outward normal of the ellipse
    L = math.hypot(nx, ny)
    ux, uy = nx / L, ny / L
    vx, vy = uy, -ux                                       # along the coast, left to right
    pier = 40.0
    ex, ey = px0 + ux * pier, py0 + uy * pier
    s.line(px0, py0, ex, ey, 1.5, G5)

    # the berth across the pier head: a dashed box, as long as the dwell
    blen = 30 + 24 * c["dwell"]
    bwid = 14.0
    gap = 3.0
    cxb, cyb = ex + ux * (gap + bwid / 2), ey + uy * (gap + bwid / 2)
    corners = [(cxb + vx * sgx * blen / 2 + ux * sgy * bwid / 2, cyb + vy * sgx * blen / 2 + uy * sgy * bwid / 2)
               for sgx, sgy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    s.dashed(corners + [corners[0]], 1.0, G4, dash=4, gap=3)

    # the ferry in its berth: solid, the one brightest thing, its wheelhouse cut in black;
    # swell turns it off the berth's line
    ang = math.atan2(vy, vx) + sw * 0.15
    s.poly(ferry_hull(cxb, cyb, ang, L=min(blen - 6, 34), B=10), G7)
    s.poly(wheelhouse(cxb, cyb, ang, l=7, b=4), G0, G0, 1.0)
    return s


if __name__ == "__main__":
    out = HERE / "clean.svg"
    clean().write(out, captions(DEFAULTS))
    print(out)
