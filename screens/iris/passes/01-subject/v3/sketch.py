#!/usr/bin/env python3
"""iris · subject pass 1 · v3 · the diaphragm over the wave plate (hatched mass).

A bench mechanism seen from the front and above, one orthographic camera:
a flat plate engraved with four waveform tracks (sine far, saw near) rides
on two rails under a fixed iris diaphragm. Morph slides the plate, so a
different track sits under the aperture; Overlap opens the blades; what is
seen through the aperture is what sounds, and it is the brightest thing.

Run: python3 sketch.py [morph overlap spread tone skew phase] > rest.svg
"""
import math
import sys

# ---- controls (defaults) -------------------------------------------------
DEF = dict(morph=0.3333, overlap=0.25, spread=0.0, tone=0.7, skew=0.0, phase=0.0)
ARGS = [float(a) for a in sys.argv[1:7]]
P = dict(DEF)
for k, v in zip(DEF, ARGS):
    P[k] = v

# ---- camera --------------------------------------------------------------
PHI = math.radians(65)            # looking down at 65 degrees
S, C = math.sin(PHI), math.cos(PHI)
CX, CY0 = 240.0, 133.0


def proj(X, Y, Z):
    return (CX + X, CY0 - (Y * S + Z * C))


# ---- model ---------------------------------------------------------------
LANE_PITCH = 22.0
AMP = 6.0
PERIOD = 30.0
PLATE_HALF_W = 200.0
PLATE_HALF_D = 45.0
PLATE_T = 4.0
R_OUT, R_IN = 82.0, 70.0          # housing ring
H_TOP, H_BOT, H_BLADE = 12.0, 2.0, 4.0
R_AP0, R_AP1 = 11.0, 67.0         # aperture at overlap 0 / 1
NBLADE = 9
RAIL_X = 208.0

m = P["morph"] * 3.0
r_ap = R_AP0 + (R_AP1 - R_AP0) * P["overlap"]
y_view = H_BLADE * C / S          # where the ray through the aperture centre meets the plate
Yp = y_view - (1.5 - m) * LANE_PITCH

GREY = dict(g1="#323232", g2="#4B4B4B", g3="#646464", g4="#7D7D7D",
            g5="#969696", g6="#AFAFAF", g7="#CDCDCD")


# ---- waveforms -----------------------------------------------------------
def warp(t, b):
    return 0.5 * t / b if t < b else 0.5 + 0.5 * (t - b) / (1 - b)


def wave(kind, t):
    t %= 1.0
    b = 0.5 - 0.45 * P["skew"]
    if kind == 0:
        return math.sin(2 * math.pi * warp(t, b))
    if kind == 1:
        u = warp(t, b)
        return 1 - 4 * abs(u - 0.25) if u < 0.75 else -1 + 4 * (u - 0.75)
    if kind == 2:
        return 1.0 if t < b else -1.0
    return 1 - 2 * t


def lane_y(kind, X):
    per = PERIOD * (1 + 0.18 * P["spread"] * (kind - 1.5) / 1.5)
    shift = kind * 0.25 * P["phase"]
    win = (1 - P["tone"]) * 0.3     # low-pass: box-average the shape
    n = 9
    acc = 0.0
    for i in range(n):
        dt = (i / (n - 1) - 0.5) * win
        acc += wave(kind, X / per + shift + dt)
    return AMP * acc / n


def lane_centre(kind):
    return Yp + (1.5 - kind) * LANE_PITCH


# ---- svg helpers ---------------------------------------------------------
out = []


def f(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def closed(pts, stroke, w, fill="none"):
    d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
    sw = f' stroke-width="{w}"' if stroke != "none" else ""
    out.append(f'<path d="{d}" fill="{fill}" stroke="{stroke}"{sw}/>')


def dedupe(pts, tol=0.3):
    res = [pts[0]]
    for p in pts[1:]:
        if math.dist(p, res[-1]) >= tol:
            res.append(p)
    return res


def ribbon(pts, w, colour):
    """An open line drawn the device's way: a thin closed filled ribbon."""
    pts = dedupe(pts)
    if len(pts) < 2:
        return
    if sum(math.dist(a, b) for a, b in zip(pts, pts[1:])) < 3:
        return
    # chunk so each ribbon stays <= 64 points
    chunks, i = [], 0
    while i < len(pts) - 1:
        chunks.append(pts[i:i + 31])
        i += 30
    h = w / 2
    for ch in chunks:
        if len(ch) < 2:
            continue
        left, right = [], []
        for j, p in enumerate(ch):
            a = ch[max(j - 1, 0)]
            b = ch[min(j + 1, len(ch) - 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy) or 1
            nx, ny = -dy / L * h, dx / L * h
            left.append((p[0] + nx, p[1] + ny))
            right.append((p[0] - nx, p[1] - ny))
        closed(left + right[::-1], "none", 0, fill=colour)


def hatch(rings, spacing, direction, colour, w=1.0):
    """45-degree hatching clipped (even-odd) to the given screen rings."""
    r2 = math.sqrt(2)
    if direction == "/":
        to_uv = lambda x, y: ((x + y) / r2, (x - y) / r2)
        to_xy = lambda u, v: ((u + v) / r2, (u - v) / r2)
    else:
        to_uv = lambda x, y: ((x - y) / r2, (x + y) / r2)
        to_xy = lambda u, v: ((u + v) / r2, (v - u) / r2)
    edges = []
    for ring in rings:
        uv = [to_uv(*p) for p in ring]
        for a, b in zip(uv, uv[1:] + uv[:1]):
            edges.append((a, b))
    us = [p[0] for e in edges for p in e]
    u = math.floor(min(us) / spacing) * spacing + spacing / 2
    while u < max(us):
        vs = []
        for (u0, v0), (u1, v1) in edges:
            if (u0 <= u < u1) or (u1 <= u < u0):
                t = (u - u0) / (u1 - u0)
                vs.append(v0 + t * (v1 - v0))
        vs.sort()
        for v0, v1 in zip(vs[0::2], vs[1::2]):
            if v1 - v0 > 4.5:
                ribbon([to_xy(u, v0 + 0.6), to_xy(u, v1 - 0.6)], w, colour)
        u += spacing


def ellipse(R, Z, n=60, a0=0.0, a1=2 * math.pi, cx=0.0, cy=0.0):
    return [proj(cx + R * math.cos(a0 + (a1 - a0) * i / n),
                 cy + R * math.sin(a0 + (a1 - a0) * i / n), Z) for i in range(n + (0 if a1 - a0 >= 2 * math.pi - 1e-9 else 1))]


def runs(pts, visible):
    cur, res = [], []
    for p in pts:
        if visible(p):
            cur.append(p)
        else:
            if len(cur) > 1:
                res.append(cur)
            cur = []
    if len(cur) > 1:
        res.append(cur)
    return res


def inside(poly, p):
    x, y = p
    c = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            c = not c
    return c


# housing silhouette test (screen space)
def hidden_by_housing(p):
    dx = p[0] - CX
    if abs(dx) >= R_OUT:
        return False
    e = math.sqrt(R_OUT ** 2 - dx ** 2) * S
    top = CY0 - H_TOP * C - e
    bot = CY0 - H_BOT * C + e
    return top <= p[1] <= bot


# aperture: nine blades leave a nine-sided opening with bowed sides
blade_a0 = math.radians(90)


def aperture_world(n_per_side=6):
    pts = []
    rv = r_ap / math.cos(math.pi / NBLADE)
    for i in range(NBLADE):
        a = blade_a0 + 2 * math.pi * i / NBLADE
        b = blade_a0 + 2 * math.pi * (i + 1) / NBLADE
        A = (rv * math.cos(a), rv * math.sin(a))
        B = (rv * math.cos(b), rv * math.sin(b))
        mid = (a + b) / 2
        bow = r_ap * 0.06
        for j in range(n_per_side):
            t = j / n_per_side
            x = A[0] + (B[0] - A[0]) * t
            y = A[1] + (B[1] - A[1]) * t
            k = 4 * t * (1 - t) * bow
            pts.append((x + k * math.cos(mid), y + k * math.sin(mid)))
    return pts


AP_W = aperture_world()
AP = [proj(x, y, H_BLADE) for x, y in AP_W]

# ---- draw ----------------------------------------------------------------
# 1 rails: two rods on the bench, fixed
for sgn in (-1, 1):
    x = sgn * RAIL_X
    y0, y1 = -84.0, 84.0
    rod = [proj(x - 3, y0, -4), proj(x + 3, y0, -4), proj(x + 3, y1, -4), proj(x - 3, y1, -4)]
    closed(rod, GREY["g3"], 1.5, fill="#000000")
    for yy in (y0, y1):      # end blocks: solid, hatched
        top = [proj(x - 8, yy - 5, 2), proj(x + 8, yy - 5, 2), proj(x + 8, yy + 5, 2), proj(x - 8, yy + 5, 2)]
        front = [proj(x - 8, yy - 5, 2), proj(x + 8, yy - 5, 2), proj(x + 8, yy - 5, -6), proj(x - 8, yy - 5, -6)]
        closed(front, GREY["g4"], 1.5, fill="#000000")
        hatch([front], 4, "/", GREY["g3"])
        closed(top, GREY["g4"], 1.5, fill="#000000")
        hatch([top], 4, "/", GREY["g3"])

# 2 the plate (the carriage): top face, front edge, shoes on the rails
y_near, y_far = Yp - PLATE_HALF_D, Yp + PLATE_HALF_D
face = [proj(-PLATE_HALF_W, y_near, 0), proj(PLATE_HALF_W, y_near, 0),
        proj(PLATE_HALF_W, y_far, 0), proj(-PLATE_HALF_W, y_far, 0)]
edge = [proj(-PLATE_HALF_W, y_near, 0), proj(PLATE_HALF_W, y_near, 0),
        proj(PLATE_HALF_W, y_near, -PLATE_T), proj(-PLATE_HALF_W, y_near, -PLATE_T)]
closed(edge, GREY["g3"], 1.5, fill="#000000")
closed(face, GREY["g4"], 1.5, fill="#000000")
for sgn in (-1, 1):
    x0, x1 = sorted((sgn * PLATE_HALF_W, sgn * (RAIL_X + 9)))
    top = [proj(x0, y_near, 6), proj(x1, y_near, 6), proj(x1, y_far, 6), proj(x0, y_far, 6)]
    front = [proj(x0, y_near, 6), proj(x1, y_near, 6), proj(x1, y_near, -6), proj(x0, y_near, -6)]
    closed(front, GREY["g4"], 1.5, fill="#000000")
    hatch([front], 4, "\\", GREY["g3"])
    closed(top, GREY["g4"], 1.5, fill="#000000")
    hatch([top], 4, "\\", GREY["g3"])

# 3 the four engraved tracks, seen on the plate outside the housing
xs = [-PLATE_HALF_W + 8 + i * 1.5 for i in range(int((2 * PLATE_HALF_W - 16) / 1.5) + 1)]
lane_pts = {}
for k in range(4):
    lane_pts[k] = [proj(X, lane_centre(k) + lane_y(k, X), 0) for X in xs]
    for run in runs(lane_pts[k], lambda p: not hidden_by_housing(p)):
        ribbon(run, 1.5, GREY["g3"])

# 4 housing side wall (near half), solid, hatched
wall = ellipse(R_OUT, H_TOP, 30, math.pi, 2 * math.pi) + ellipse(R_OUT, H_BOT, 30, 2 * math.pi, math.pi)
closed(wall, GREY["g4"], 1.5, fill="#000000")
hatch([wall], 4, "/", GREY["g2"])

# 5 the blades, at their own depth, hatched the other way
blade_outer = ellipse(R_IN, H_BLADE, 48)
closed(blade_outer, GREY["g4"], 1.5, fill="#000000")
hatch([blade_outer, AP], 4, "\\", GREY["g3"])
for i in range(NBLADE):
    a = blade_a0 + 2 * math.pi * i / NBLADE
    rv = r_ap / math.cos(math.pi / NBLADE)
    pts = []
    for j in range(17):
        t = j / 16
        rho = rv + (R_IN - rv) * t
        ang = a + math.radians(70) * math.sin(t * math.pi / 2)
        pts.append(proj(rho * math.cos(ang), rho * math.sin(ang), H_BLADE))
    ribbon(pts, 1.2, GREY["g4"])

# 6 through the aperture: what sounds
closed(AP, "none", 0, fill="#000000")
for k in range(4):
    d = abs(k - m)
    if d < 0.5:
        w, col = 2.5, GREY["g7"]
    else:
        w, col = 1.5, GREY["g5"]
    for run in runs(lane_pts[k], lambda p: inside(AP, p)):
        ribbon(run, w, col)
closed(AP, GREY["g5"], 1.5)

# 7 housing top ring, solid, hatched; inner bore rim
ring = ellipse(R_OUT, H_TOP, 30)
hole = ellipse(R_IN, H_TOP, 30)
keyhole = ring + [proj(R_OUT, 0.0, H_TOP)][:0] + [proj(R_IN, 0.0, H_TOP)] + hole[::-1][:-1]
# one subpath: outer loop, cut in, inner loop the other way round
closed(keyhole, "none", 0, fill="#000000")
hatch([ring, hole], 4, "/", GREY["g2"])
closed(ring, GREY["g5"], 1.5)
closed(hole, GREY["g4"], 1.5)

# 8 the focus lever (tone), on the ring
a = math.radians(210 - 240 * P["tone"])
ux, uy = math.cos(a), math.sin(a)
vx, vy = -uy, ux
hw = 6.0
lev = [(R_OUT - 1, -hw), (R_OUT + 12, -hw), (R_OUT + 12, hw), (R_OUT - 1, hw)]
lev = [proj(ux * r + vx * s, uy * r + vy * s, H_TOP) for r, s in lev]
closed(lev, GREY["g5"], 1.5, fill="#000000")
hatch([lev], 4, "\\", GREY["g3"])

# ---- frame ---------------------------------------------------------------
def pct(v):
    return f"{round(v * 100)}%"


titles = ["morph", "overlap", "spread", "tone"]
vals = [pct(P[t]) for t in titles]
hdr = []
steps = ["#000000", "#323232", "#4B4B4B", "#646464", "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD"]
for i, s in enumerate(steps):
    hdr.append(f'<rect x="{i * 60}" y="0" width="60" height="20" fill="{s}" stroke="none"/>')
for i in range(4):
    col = "#CBCBCB" if i < 2 else "#000000"
    hdr.append(f'<text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{col}" stroke="none" '
               f'font-family="UniversNextPro-Light" font-size="10px">{titles[i]}</text>')
    hdr.append(f'<text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{col}" stroke="none" '
               f'font-family="UniversNextPro-Light" font-size="20px">{vals[i]}</text>')
for i, t in enumerate(["skew", "phase"]):
    hdr.append(f'<text transform="matrix(1 0 0 1 {5 + 120 * i} 31)" fill="#5A5A5A" stroke="none" '
               f'font-family="UniversNextPro-Light" font-size="10px">{t}</text>')
    hdr.append(f'<text transform="matrix(1 0 0 1 {65 + 120 * i} 33)" fill="#707070" stroke="none" '
               f'font-family="UniversNextPro-Light" font-size="13px">{pct(P[t])}</text>')

print('<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">')
print('  <!-- iris v3: iris diaphragm over a sliding wave plate. Generated by sketch.py. -->')
print('  <g id="preview_canvas">\n    <rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>\n  </g>')
print('  <g id="preview_header">')
for h in hdr:
    print("    " + h)
print('  </g>')
print('  <path id="iris_palette_0" d="M 700 300 L 704 300 L 704 304 Z" fill="#CDCDCD" stroke="#CDCDCD" stroke-width="2"/>')
print('  <g id="iris_art">')
for o in out:
    print("    " + o)
print('  </g>')
print('</svg>')
