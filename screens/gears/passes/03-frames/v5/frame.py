#!/usr/bin/env python3
"""Frames pass 03 for gears, v5: centred hero, section cut, negative space.

    python3 screens/gears/passes/03-frames/v5/frame.py

The chosen subject (02-subject/v4): two thick spur wheels on a low camera,
meshed, lit from the upper left, shaded flanks hatched, top faces black, B's
web drilled at the scale's positions. This variant cuts the pair through the
plane of both axles and takes the near halves away. What's left is the far
half of each wheel standing on its cut face; the missing halves are the black
in front. The cut runs through the meshing pair, so the tooth that plays is
drawn in profile: A's tooth reaching into B's gap.

Defaults: ratio 3:2, teeth 8, mesh 100 %, scale maj; at rest, not muted.
World: x right, y away from the camera, z up; module 1. One orthographic
camera at elevation PHI looking along +y. Static artwork only (no bound nodes
yet), grey only, no text below the header.
"""
from __future__ import annotations

import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 480, 220
G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
FONT = "UniversNextPro-Light"
HEADER = [("ratio", "3:2"), ("teeth", "8"), ("mesh", "100%"), ("scale", "maj")]
HAIR, LINE, SUBJ = 1.0, 1.5, 2.0

TEETH_A, RATIO = 8, (3, 2)
TEETH_B = TEETH_A * RATIO[0] // RATIO[1]          # 12
SCALE = [0, 2, 4, 5, 7, 9, 11]                     # maj, positions of 12

# ---------------------------------------------------------------- camera
PHI = math.radians(36)                              # low camera
S = 15.0                                            # px per module
SINP, COSP = math.sin(PHI), math.cos(PHI)
RP_A, RP_B = TEETH_A / 2, TEETH_B / 2
D_AB = RP_A + RP_B
T = 2.3                                             # face width (thick)
XC = 240 - S * (D_AB + RP_B + 1 - (RP_A + 1)) / 2   # centre the pair's span
OY = 162                                            # screen row of the cut's floor


def P(x, y, z):
    return (XC + S * x, OY - S * (z * COSP + y * SINP))


def Ps(pts3):
    return [P(*p) for p in pts3]


def depth(x, y, z):
    return y * COSP - z * SINP


# ---------------------------------------------------------------- svg out
def f(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def dedupe(pts, gap=0.3):
    out = []
    for p in pts:
        if not out or math.dist(out[-1], p) >= gap:
            out.append(p)
    if len(out) > 2 and math.dist(out[0], out[-1]) < gap:
        out.pop()
    return out


def poly(pts, fill, stroke="none", sw=None):
    pts = dedupe(pts)
    if len(pts) < 3:
        return ""
    if len(pts) > 64:
        step = math.ceil(len(pts) / 64)
        pts = pts[::step]
    d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
    s = f'<path d="{d}" fill="{fill}" stroke="{stroke}"'
    if stroke != "none":
        s += f' stroke-width="{sw}"'
    return s + "/>"


def body(pts, fill, edge, w):
    """Black body plus its outline as a ribbon loop (any point count)."""
    pts = dedupe(pts)
    return [poly(pts, fill), ribbon(pts + [pts[0]], w, edge)]


def ribbon(pts, w, fill):
    pts = dedupe(pts, 0.6)
    if len(pts) < 2:
        return ""
    out, i = [], 0
    while i < len(pts) - 1:
        out.append(_ribbon(pts[i:i + 31], w, fill))
        i += 30
    return "\n".join(out)


def _ribbon(pts, w, fill):
    h, n = w / 2, len(pts)
    left, right = [], []
    for k in range(n):
        if k == 0 or k == n - 1:
            a, b = (pts[0], pts[1]) if k == 0 else (pts[-2], pts[-1])
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy) or 1
            nx, ny, m = -dy / L, dx / L, h
        else:
            ax, ay = pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]
            bx, by = pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1]
            la, lb = math.hypot(ax, ay) or 1, math.hypot(bx, by) or 1
            n1, n2 = (-ay / la, ax / la), (-by / lb, bx / lb)
            nx, ny = n1[0] + n2[0], n1[1] + n2[1]
            ln = math.hypot(nx, ny) or 1
            nx, ny = nx / ln, ny / ln
            m = h / max(0.5, nx * n1[0] + ny * n1[1])
        x, y = pts[k]
        left.append((x + nx * m, y + ny * m))
        right.append((x - nx * m, y - ny * m))
    return poly(left + right[::-1], fill)


def seg(p, q, w, fill):
    return ribbon([p, q], w, fill)


def hatch(polys, spacing=3.5, w=HAIR, fill=G3, slope=1.0):
    """Hairlines y = -slope*x + c clipped to the region (even-odd over polys)."""
    edges, xs, ys = [], [], []
    for Pp in polys:
        for a, b in zip(Pp, Pp[1:] + Pp[:1]):
            edges.append((a, b))
        xs += [p[0] for p in Pp]
        ys += [p[1] for p in Pp]
    if not edges:
        return []
    cs = [y + slope * x for x, y in zip(xs, ys)]
    c0, c1 = min(cs), max(cs)
    stepc = spacing * math.sqrt(1 + slope * slope)
    out = []
    c = math.floor(c0 / stepc) * stepc + stepc / 2
    while c < c1:
        ts = []
        for (ax, ay), (bx, by) in edges:
            ga, gb = ay + slope * ax - c, by + slope * bx - c
            if (ga > 0) != (gb > 0):
                t = ga / (ga - gb)
                ts.append(ax + (bx - ax) * t)
        ts.sort()
        for x0, x1 in zip(ts[::2], ts[1::2]):
            if x1 - x0 > 3.4:
                out.append(seg((x0 + 0.4, c - slope * (x0 + 0.4)),
                               (x1 - 0.4, c - slope * (x1 - 0.4)), w, fill))
        c += stepc
    return out


def frame(parts):
    steps = [G0, G1, G2, G3, G4, G5, G6, G7]
    hdr = [f'<rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>'
           for i, c in enumerate(steps)]
    for i, (t, v) in enumerate(HEADER):
        ink = "#CBCBCB" if i < 2 else G0
        hdr.append(f'<text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{ink}" stroke="none" '
                   f'font-family="{FONT}" font-size="10px">{t}</text>')
        hdr.append(f'<text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{ink}" stroke="none" '
                   f'font-family="{FONT}" font-size="20px">{v}</text>')
    flat = []
    for p in parts:
        if isinstance(p, list):
            flat += [q for q in p if q]
        elif p:
            flat.append(p)
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        '<g id="preview_canvas">', f'<rect x="0" y="0" width="{W}" height="{H}" fill="{G0}" stroke="none"/>', '</g>',
        '<g id="preview_header">', *hdr, '</g>',
        *flat, '</svg>', ""])


# ---------------------------------------------------------------- gears
def tooth(rp, centre_a):
    """One tooth, CCW: root, a slightly convex flank through the pitch circle, flat tip."""
    ra, rr = rp + 1.0, rp - 1.25
    pitch_a = 2 * math.pi / (2 * rp)
    prof = [(-0.30, rr), (-0.27, rp - 0.55), (-0.235, rp), (-0.19, rp + 0.55), (-0.15, ra),
            (0.15, ra), (0.19, rp + 0.55), (0.235, rp), (0.27, rp - 0.55), (0.30, rr)]
    out = []
    for fa, r in prof:
        a = centre_a + fa * pitch_a
        out.append((r * math.cos(a), r * math.sin(a)))
    return out


def gear(N, rp, rot):
    """CCW outline, teeth centred on rot + k * pitch, root arcs between."""
    pts = []
    rr = rp - 1.25
    pitch = 2 * math.pi / N
    for k in range(N):
        pts += tooth(rp, rot + k * pitch)
        a0, a1 = rot + k * pitch + 0.30 * pitch, rot + (k + 1) * pitch - 0.30 * pitch
        for i in range(1, 3):
            a = a0 + (a1 - a0) * i / 3
            pts.append((rr * math.cos(a), rr * math.sin(a)))
    return pts


def clip_far(pts):
    """Keep y >= 0 (the far half): Sutherland-Hodgman against one plane."""
    out = []
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        ina, inb = a[1] >= 0, b[1] >= 0
        if ina:
            out.append(a)
        if ina != inb:
            t = a[1] / (a[1] - b[1])
            out.append((a[0] + (b[0] - a[0]) * t, 0.0))
    return out


def arc(r, a0, a1, n=24):
    return [(r * math.cos(a0 + (a1 - a0) * i / n), r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def shift(pts, cx):
    return [(x + cx, y) for x, y in pts]


# ---------------------------------------------------------------- drawing
LIGHT = (-0.8, -0.35, 0.5)          # from the upper left, a little toward the camera


def flanks(outline, cx):
    """Visible outer side faces (normal toward the camera) of a far half."""
    faces = []
    o = outline
    for a, b in zip(o, o[1:] + o[:1]):
        ex, ey = b[0] - a[0], b[1] - a[1]
        L = math.hypot(ex, ey)
        if L < 1e-6 or (abs(a[1]) < 1e-9 and abs(b[1]) < 1e-9):
            continue                                  # the cut edge: drawn as section
        nx, ny = ey / L, -ex / L
        if ny > -0.1:                                 # edge-on slivers stay hidden
            continue
        q = [(a[0] + cx, a[1], 0), (b[0] + cx, b[1], 0), (b[0] + cx, b[1], T), (a[0] + cx, a[1], T)]
        lit = nx * LIGHT[0] + ny * LIGHT[1]
        dep = depth((a[0] + b[0]) / 2 + cx, (a[1] + b[1]) / 2, T / 2)
        faces.append((dep, q, lit))
    return faces


def draw():
    out = []
    rotA = 0.0                                   # A's tooth on the line of centres, toward B
    rotB = math.pi + math.pi / TEETH_B           # B shows a gap to A there
    gA = clip_far(gear(TEETH_A, RP_A, rotA))
    gB = clip_far(gear(TEETH_B, RP_B, rotB))
    cA, cB = 0.0, D_AB

    # dimensions in module units
    boreA, hubA, bossA = 0.75, 1.55, 0.55
    boreB, hubB = 0.9, 2.0
    riB = RP_B - 1.25 - 0.9                      # rim inside
    w0, w1 = 0.75, T - 0.75                      # web, centred
    holeR, holeC = 0.62, (hubB + riB) / 2

    # 1. outer flanks of both far halves, far first
    faces = flanks(gA, cA) + flanks(gB, cB)
    faces.sort(key=lambda r: -r[0])
    for _, q, lit in faces:
        sq = Ps(q)
        if max(p[0] for p in sq) - min(p[0] for p in sq) < 3.0:
            continue                                  # a sliver the outline would fold over
        out += body(sq, G0, G4, LINE)
        if lit < 0.05:
            out += hatch([sq], spacing=3.2, fill=G3)

    # 2. B: pocket floor, holes, rim's inner wall, rim top, hub top
    floor = [(x + cB, y, w1) for x, y in arc(riB, 0, math.pi, 32)] + \
            [(x + cB, y, w1) for x, y in arc(hubB, math.pi, 0, 16)]
    out += body(Ps(floor), G0, G3, HAIR)
    for k in range(6):                           # positions 0..5 lie in the far half
        a = math.radians(165 - 30 * k)
        hx, hy = cB + holeC * math.cos(a), holeC * math.sin(a)
        if k in SCALE:
            top = [(hx + holeR * math.cos(t), hy + holeR * math.sin(t), w1)
                   for t in [2 * math.pi * i / 28 for i in range(28)]]
            out += body(Ps(top), G0, G4, LINE)
            # the hole's far wall: bottom rim seen through the opening
            st = Ps(top)
            cx_, cy_ = sum(p[0] for p in st) / len(st), sum(p[1] for p in st) / len(st)
            rx = S * holeR
            ry = S * holeR * SINP
            drop = S * (w1 - w0) * COSP
            run = []
            for i in range(29):
                t = math.pi + math.pi * i / 28
                px, py = cx_ + rx * math.cos(t) * 0.999, cy_ + drop + ry * math.sin(t)
                inside = ((px - cx_) / rx) ** 2 + ((py - cy_) / ry) ** 2 < 0.92
                if inside:
                    run.append((px, py))
            if len(run) > 2:
                out.append(ribbon(run, HAIR, G3))
        else:
            ring = [(hx + 0.32 * math.cos(t), hy + 0.32 * math.sin(t), w1)
                    for t in [2 * math.pi * i / 16 for i in range(16)]]
            sr = Ps(ring)
            out.append(ribbon(sr + [sr[0]], HAIR, G3))
    wall = [(x + cB, y, w1) for x, y in arc(riB, math.pi, 0, 32)] + \
           [(x + cB, y, T) for x, y in arc(riB, 0, math.pi, 32)]
    sw = Ps(wall)
    out += body(sw, G0, G4, LINE)
    out += hatch([sw], spacing=3.2, fill=G2, slope=-1.0)
    rimB = [(x, y, T) for x, y in gB if x * x + y * y > 0]
    # rim top: outline (far half) back along the inner circle
    rim_pts = [(x + cB, y, T) for x, y in gB] + \
              [(x + cB, y, T) for x, y in arc(riB, 0, math.pi, 32)][::-1][::-1]
    # gB runs CCW from the right cut point round to the left cut point; close inward
    rim_pts = [(x + cB, y, T) for x, y in gB]
    rim_pts = rim_pts + [(x + cB, y, T) for x, y in arc(riB, math.pi, 0, 32)]
    out += body(Ps(rim_pts), G0, G5, LINE)
    hub_top = [(x + cB, y, T) for x, y in arc(hubB, 0, math.pi, 20)] + \
              [(x + cB, y, T) for x, y in arc(boreB, math.pi, 0, 12)]
    out += body(Ps(hub_top), G0, G5, LINE)
    bore = [(x + cB, y, T) for x, y in arc(boreB, math.pi, 0, 12)] + \
           [(x + cB, y, 0) for x, y in arc(boreB, 0, math.pi, 12)]
    sb = Ps(bore)
    out += body(sb, G0, G3, HAIR)

    # 3. A: top face, boss, bore
    topA = [(x + cA, y, T) for x, y in gA]
    out += body(Ps(topA), G0, G5, LINE)
    out.append(ribbon(Ps([(x + cA, y, T) for x, y in arc(RP_A - 1.25 - 0.45, 0.04, math.pi - 0.04, 28)]), HAIR, G3))
    boss = [(x + cA, y, T + bossA) for x, y in arc(hubA, 0, math.pi, 20)] + \
           [(x + cA, y, T + bossA) for x, y in arc(boreA, math.pi, 0, 12)]
    out += body(Ps(boss), G0, G5, LINE)
    boreA_w = [(x + cA, y, T + bossA) for x, y in arc(boreA, math.pi, 0, 12)] + \
              [(x + cA, y, 0) for x, y in arc(boreA, 0, math.pi, 12)]
    out += body(Ps(boreA_w), G0, G3, HAIR)

    # 4. the cut faces, in the plane y = 0, hatched (A one way, B the other)
    tipA, tipB = RP_A + 1.0, RP_B - 1.25            # A cut through teeth both sides, B through gaps
    rrA = RP_A - 1.25

    def sec(prof, cx):
        return Ps([(x + cx, 0.0, z) for x, z in prof])

    secA = [
        [(-tipA, 0), (-boreA, 0), (-boreA, T + bossA), (-hubA, T + bossA), (-hubA, T), (-tipA, T)],
        [(boreA, 0), (tipA, 0), (tipA, T), (hubA, T), (hubA, T + bossA), (boreA, T + bossA)],
    ]
    secB = []
    for s in (-1, 1):
        prof = [(tipB, 0), (tipB, T), (riB, T), (riB, w1), (hubB, w1), (hubB, T),
                (boreB, T), (boreB, 0), (hubB, 0), (hubB, w0), (riB, w0), (riB, 0)]
        prof = [(s * x, z) for x, z in prof]
        if s < 0:
            prof = prof[::-1]
        secB.append(prof)
    for prof in secA:
        sp = sec(prof, cA)
        out.append(poly(sp, G0))
        out += hatch([sp], spacing=3.4, fill=G4, slope=1.0)
        out.append(ribbon(sp + [sp[0]], LINE, G5))
    for prof in secB:
        sp = sec(prof, cB)
        out.append(poly(sp, G0))
        out += hatch([sp], spacing=3.4, fill=G4, slope=-1.0)
        out.append(ribbon(sp + [sp[0]], LINE, G5))

    # the tooth that plays: A's tooth cut in profile, standing in B's gap
    tooth = sec([(rrA, 0), (tipA, 0), (tipA, T), (rrA, T)], cA)
    out.append(ribbon(tooth, SUBJ, G7))

    # axles: chain centre lines through each bore, hairline, quiet
    for cx, top in ((cA, T + bossA), (cB, T)):
        x = XC + S * cx
        bore = boreA if cx == cA else boreB
        ya, yb = OY + 12, OY - S * (top * COSP + bore * SINP) + 1      # up through the bore only
        y = ya
        long_, gap, short = 9.0, 3.0, 2.5
        on = 0
        pattern = [long_, gap, short, gap]
        while y > yb:
            L = pattern[on % 4]
            y2 = max(yb, y - L)
            if on % 2 == 0:
                out.append(seg((x, y), (x, y2), HAIR, G2))
            y = y2
            on += 1
    return frame(out)


if __name__ == "__main__":
    (HERE / "rest.svg").write_text(draw())
    print("wrote", HERE / "rest.svg")
