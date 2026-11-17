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
HAIR, LINE, SUBJ = 1.0, 1.5, 2.0

RATIOS = [(1, 1), (5, 4), (4, 3), (7, 5), (3, 2), (5, 3), (7, 4), (2, 1), (3, 1)]
TEETH = list(range(3, 17))
SCALES = [("maj", [0, 2, 4, 5, 7, 9, 11]), ("min", [0, 2, 3, 5, 7, 8, 10]),
          ("dor", [0, 2, 3, 5, 7, 9, 10]), ("phr", [0, 1, 3, 5, 7, 8, 10]),
          ("lyd", [0, 2, 4, 6, 7, 9, 11]), ("mix", [0, 2, 4, 5, 7, 9, 10]),
          ("pent", [0, 2, 4, 7, 9]), ("hira", [0, 2, 3, 7, 8])]
DEFAULTS = {"ratio": 0.5, "teeth": 0.3846, "mesh": 1.0, "scale": 0.0}

# ---------------------------------------------------------------- camera
PHI = math.radians(36)                              # low camera
SINP, COSP = math.sin(PHI), math.cos(PHI)
T = 2.3                                             # face width (thick)
OY = 162                                            # screen row of the cut's floor


def pick(v, n):
    return min(n - 1, max(0, round(min(1.0, max(0.0, v)) * (n - 1))))


def setup(values, notes=0.0):
    """Every quantity the drawing reads, from the controls (0..1 by id)."""
    global HEADER, TEETH_A, TEETH_B, SCALE, MESH, NOTES, S, RP_A, RP_B, D_AB, XC
    global M, ADD_A, DED_A, ADD_B, DED_B, FULL_A, FULL_B
    v = {**DEFAULTS, **values}
    ratio = RATIOS[pick(v["ratio"], len(RATIOS))]
    TEETH_A = TEETH[pick(v["teeth"], len(TEETH))]
    sname, SCALE = SCALES[pick(v["scale"], len(SCALES))]
    MESH = min(1.0, max(0.0, v["mesh"]))
    NOTES = notes
    HEADER = [("ratio", f"{ratio[0]}:{ratio[1]}"), ("teeth", str(TEETH_A)),
              ("mesh", f"{round(MESH * 100)}%"), ("scale", sname)]
    TEETH_B = max(3, round(TEETH_A * ratio[0] / ratio[1]))
    M = 8 / TEETH_A                                  # module: A keeps its size, its teeth re-cut
    RP_A, RP_B = TEETH_A * M / 2, TEETH_B * M / 2
    ADD_A, DED_A = min(1.0 * M, 0.3 * RP_A), min(1.25 * M, 0.35 * RP_A)
    ADD_B, DED_B = min(1.0 * M, 0.3 * RP_B), min(1.25 * M, 0.35 * RP_B)
    D_AB = RP_A + RP_B
    span = D_AB + (RP_B + ADD_B) + (RP_A + ADD_A)
    vert = max(T * COSP + (RP_B + ADD_B) * SINP, (T + 0.55) * COSP + 1.55 * SINP)
    S = min(15.0, 440 / span, 134 / vert)           # px per world unit
    XC = 240 - S * (D_AB + (RP_B + ADD_B) - (RP_A + ADD_A)) / 2   # centre the pair's span
    FULL_A = euclid(MESH, TEETH_A)
    FULL_B = euclid(MESH, TEETH_B)


def euclid(mesh, n):
    """Which teeth keep full face width: round(mesh * n) of n in Euclidean order, tooth 0 always."""
    k = max(1, round(mesh * n))
    return [(i * k) % n < k for i in range(n)]


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
def tooth(rp, centre_a, n, add, ded):
    """One tooth, CCW: root, a slightly convex flank through the pitch circle, flat tip."""
    ra, rr = rp + add, rp - ded
    pitch_a = 2 * math.pi / n * wfac(n)
    lo, hi = 0.55 * (ded / 1.25), 0.55 * add
    prof = [(-0.30, rr), (-0.27, rp - lo), (-0.235, rp), (-0.19, rp + hi), (-0.15, ra),
            (0.15, ra), (0.19, rp + hi), (0.235, rp), (0.27, rp - lo), (0.30, rr)]
    out = []
    for fa, r in prof:
        a = centre_a + fa * pitch_a
        out.append((r * math.cos(a), r * math.sin(a)))
    return out


def wfac(n):
    """Few teeth: keep each tooth narrow so it still reads as a tooth, not a lobe."""
    return min(1.0, 0.45 + 0.55 * n / 8)


def gear(N, rp, rot, add, ded, full, top=False):
    """CCW outline, teeth centred on rot + k * pitch, root arcs between.

    Returns (points, tags): tag k for a point of tooth k, None on the root. A milled
    tooth (full[k] False) is cut back to its root chord when top is set (the face at T)."""
    pts, tags = [], []
    rr = rp - ded
    pitch = 2 * math.pi / N
    for k in range(N):
        tp = tooth(rp, rot + k * pitch, N, add, ded)
        if top and not full[k]:
            tp = [tp[0], tp[-1]]
        pts += tp
        tags += [k] * len(tp)
        a0, a1 = rot + k * pitch + 0.30 * pitch * wfac(N), rot + (k + 1) * pitch - 0.30 * pitch * wfac(N)
        for i in range(1, 3):
            a = a0 + (a1 - a0) * i / 3
            pts.append((rr * math.cos(a), rr * math.sin(a)))
            tags.append(None)
    return pts, tags


def clip_far(pts_tags):
    """Keep y >= 0 (the far half): Sutherland-Hodgman against one plane. Tags ride along."""
    pts, tags = pts_tags
    out, otags = [], []
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        ina, inb = a[1] >= 0, b[1] >= 0
        if ina:
            out.append(a)
            otags.append(tags[i])
        if ina != inb:
            t = a[1] / (a[1] - b[1])
            out.append((a[0] + (b[0] - a[0]) * t, 0.0))
            otags.append(tags[i] if tags[i] == tags[(i + 1) % n] else None)
    return out, otags


def arc(r, a0, a1, n=24):
    return [(r * math.cos(a0 + (a1 - a0) * i / n), r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def shift(pts, cx):
    return [(x + cx, y) for x, y in pts]


# ---------------------------------------------------------------- drawing
LIGHT = (-0.8, -0.35, 0.5)          # from the upper left, a little toward the camera


def flanks(outline, cx, full=None):
    """Visible outer side faces (normal toward the camera) of a far half.

    A milled tooth's flanks stand only T/2; the root chord above it is a step wall."""
    faces = []
    o, tags = outline
    for i, (a, b) in enumerate(zip(o, o[1:] + o[:1])):
        ta, tb = tags[i], tags[(i + 1) % len(o)]
        z0, z1 = 0, T
        if full is not None and ta is not None and ta == tb and not full[ta]:
            z1 = T / 2
        ex, ey = b[0] - a[0], b[1] - a[1]
        L = math.hypot(ex, ey)
        if L < 1e-6 or (abs(a[1]) < 1e-9 and abs(b[1]) < 1e-9):
            continue                                  # the cut edge: drawn as section
        nx, ny = ey / L, -ex / L
        if ny > -0.1:                                 # edge-on slivers stay hidden
            continue
        q = [(a[0] + cx, a[1], z0), (b[0] + cx, b[1], z0), (b[0] + cx, b[1], z1), (a[0] + cx, a[1], z1)]
        lit = nx * LIGHT[0] + ny * LIGHT[1]
        dep = depth((a[0] + b[0]) / 2 + cx, (a[1] + b[1]) / 2, (z0 + z1) / 2)
        faces.append((dep, q, lit, "flank"))
    if full is None:
        return faces
    # milled teeth: the stepped-down top face, and the root-chord wall above it
    n = len(o)
    seen = set()
    for i in range(n):
        k = tags[i]
        if k is None or full[k] or k in seen:
            continue
        seen.add(k)
        idx = [j for j in range(n) if tags[j] == k]
        run = [o[j] for j in idx]
        if len(run) < 3:
            continue
        top = [(x + cx, y, T / 2) for x, y in run]
        cxm = sum(p[0] for p in top) / len(top)
        cym = sum(p[1] for p in top) / len(top)
        faces.append((depth(cxm, cym, T / 2) - 0.01, top, 1.0, "mill"))
        a, b = run[-1], run[0]                         # root chord, outward normal
        ex, ey = b[0] - a[0], b[1] - a[1]
        L = math.hypot(ex, ey)
        if L > 1e-6 and min(a[1], b[1]) > 1e-9:
            nx, ny = ey / L, -ex / L
            if ny < -0.1:
                q = [(a[0] + cx, a[1], T / 2), (b[0] + cx, b[1], T / 2), (b[0] + cx, b[1], T), (a[0] + cx, a[1], T)]
                lit = nx * LIGHT[0] + ny * LIGHT[1]
                faces.append((depth((a[0] + b[0]) / 2 + cx, (a[1] + b[1]) / 2, 3 * T / 4), q, lit, "flank"))
    return faces


def draw():
    out = []
    rotA = 0.0                                   # A's tooth on the line of centres, toward B
    rotB = math.pi + math.pi / TEETH_B           # B shows a gap to A there
    gA_all = clip_far(gear(TEETH_A, RP_A, rotA, ADD_A, DED_A, FULL_A))
    gB_all = clip_far(gear(TEETH_B, RP_B, rotB, ADD_B, DED_B, FULL_B))
    gA = clip_far(gear(TEETH_A, RP_A, rotA, ADD_A, DED_A, FULL_A, top=True))[0]
    gB = clip_far(gear(TEETH_B, RP_B, rotB, ADD_B, DED_B, FULL_B, top=True))[0]
    cA, cB = 0.0, D_AB

    # dimensions in world units (A's pitch radius is 4); a small B shrinks its web to fit
    boreA, hubA, bossA = 0.75, 1.55, 0.55
    rrB = RP_B - DED_B
    kB = min(1.6, rrB / 4.75)
    boreB, hubB = 0.9 * min(kB, 1.0), 2.0 * kB     # the axle bore never grows
    riB = rrB - 0.9 * kB                         # rim inside
    w0, w1 = 0.75, T - 0.75                      # web, centred
    holeR, holeC = 0.62 * kB, (hubB + riB) / 2

    # 1. outer flanks of both far halves, far first (milled tops among them)
    faces = flanks(gA_all, cA, FULL_A) + flanks(gB_all, cB, FULL_B)
    faces.sort(key=lambda r: -r[0])
    for _, q, lit, kind in faces:
        sq = Ps(q)
        if kind == "mill":
            out += body(sq, G0, G4, LINE)
            continue
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
            if NOTES > 0 and k == 0:                 # the note lands in the root's hole
                out += body(Ps(top), G0, G7, SUBJ)
            else:
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
                out.append(ribbon(run, LINE if NOTES > 0 and k == 0 else HAIR,
                                  G5 if NOTES > 0 and k == 0 else G3))
        else:
            ring = [(hx + 0.32 * kB * math.cos(t), hy + 0.32 * kB * math.sin(t), w1)
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
    out.append(ribbon(Ps([(x + cA, y, T) for x, y in arc(RP_A - DED_A - 0.45, 0.04, math.pi - 0.04, 28)]), HAIR, G3))
    boss = [(x + cA, y, T + bossA) for x, y in arc(hubA, 0, math.pi, 20)] + \
           [(x + cA, y, T + bossA) for x, y in arc(boreA, math.pi, 0, 12)]
    out += body(Ps(boss), G0, G5, LINE)
    boreA_w = [(x + cA, y, T + bossA) for x, y in arc(boreA, math.pi, 0, 12)] + \
              [(x + cA, y, 0) for x, y in arc(boreA, 0, math.pi, 12)]
    out += body(Ps(boreA_w), G0, G3, HAIR)

    # 4. the cut faces, in the plane y = 0, hatched (A one way, B the other)
    rrA = RP_A - DED_A
    tipA = RP_A + ADD_A                             # A's tooth 0 always faces B

    def cut(N, rot, theta, ra, rr, full):
        """What the cut plane meets at angle theta: (radius, top) of a tooth, or the root."""
        pitch = 2 * math.pi / N
        j = (theta - rot) / pitch
        k = round(j)
        if abs(j - k) < 1e-6:
            return ra, (T if full[k % N] else T / 2)
        return rr, T

    def sec(prof, cx):
        return Ps([(x + cx, 0.0, z) for x, z in prof])

    tL, hL = cut(TEETH_A, rotA, math.pi, tipA, rrA, FULL_A)
    if hL == T:
        left = [(-tL, 0), (-boreA, 0), (-boreA, T + bossA), (-hubA, T + bossA), (-hubA, T), (-tL, T)]
    else:
        left = [(-tL, 0), (-boreA, 0), (-boreA, T + bossA), (-hubA, T + bossA), (-hubA, T),
                (-rrA, T), (-rrA, hL), (-tL, hL)]
    secA = [
        left,
        [(boreA, 0), (tipA, 0), (tipA, T), (hubA, T), (hubA, T + bossA), (boreA, T + bossA)],
    ]
    secB = []
    for s in (-1, 1):
        tipB, hB = cut(TEETH_B, rotB, 0.0 if s > 0 else math.pi, RP_B + ADD_B, rrB, FULL_B)
        rim = [(tipB, 0), (tipB, T)] if hB == T else [(tipB, 0), (tipB, hB), (rrB, hB), (rrB, T)]
        prof = rim + [(riB, T), (riB, w1), (hubB, w1), (hubB, T),
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
    out.append(ribbon(tooth, SUBJ, G6 if NOTES > 0 else G7))

    # axles: chain centre lines through each bore, hairline, quiet
    for cx, top in ((cA, T + bossA), (cB, T)):
        x = XC + S * cx
        bore = boreA if cx == cA else boreB
        ya, yb = OY + 12, OY - S * (top * COSP + bore * SINP) + 1      # up through the bore only
        y = ya
        long_, gap, short = 9.0, 3.0, 3.5
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


def render(values=None, notes=0.0):
    setup(values or {}, notes)
    return draw()


setup({})


if __name__ == "__main__":
    (HERE / "rest.svg").write_text(render())
    print("wrote", HERE / "rest.svg")
