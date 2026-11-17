#!/usr/bin/env python3
"""iris v5 · subject pass 1 · one scene: a prism on an optical bench.

One beam (the note's single pitch) enters a glass prism and leaves as four rays,
one per band (sine, triangle, square, saw), fanned by harmonic content. Each ray
is drawn as its own wave travelling. Down the bench an adjustable slit (two jaws
on a carriage) stands across the fan: morph slides the slit along the fan,
overlap opens the jaws, and only the rays the slit lets through carry on past it.

Modelled in 3D (x along the bench, y into the bench, z up) and projected through
one camera. Detailed line art: outer edges Line weight, inner structure Hairline,
black fills so solids hide what's behind them. No text in the drawing.

    python3 sketch.py [out.svg] [morph overlap spread tone skew phase]
"""
import math
import sys

# ---- controls (defaults) -------------------------------------------------
NAMES = ["morph", "overlap", "spread", "tone", "skew", "phase"]
P = dict(morph=0.3333, overlap=0.25, spread=0.0, tone=0.7, skew=0.0, phase=0.0)
for k, v in zip(NAMES, sys.argv[2:]):
    P[k] = float(v)
OUT = sys.argv[1] if len(sys.argv) > 1 else "rest.svg"

# ---- palette / weights (craft.md) ----------------------------------------
BRIGHT, G1, G2, G3, G4, G5 = "#CDCDCD", "#AFAFAF", "#969696", "#7D7D7D", "#646464", "#4B4B4B"
GROUND = "#323232"
HAIR, LINE, SUBJ = 1.0, 1.5, 2.2

# ---- camera --------------------------------------------------------------
TARGET = (170.0, 0.0, 20.0)
DIST, AZ, EL = 1300.0, math.radians(-12), math.radians(38)
K, CX, CY = 1500.0, 258.0, 132.0      # image-plane fit: px per unit, where the target lands


def norm(v):
    l = math.sqrt(sum(c * c for c in v))
    return tuple(c / l for c in v)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


CAM = (TARGET[0] + DIST * math.cos(EL) * math.sin(AZ),
       TARGET[1] - DIST * math.cos(EL) * math.cos(AZ),
       TARGET[2] + DIST * math.sin(EL))
FWD = norm(sub(TARGET, CAM))
RIGHT = norm(cross(FWD, (0, 0, 1)))
UP = cross(RIGHT, FWD)


def proj(p):
    d = sub(p, CAM)
    z = dot(d, FWD)
    return (CX + K * dot(d, RIGHT) / z, CY - K * dot(d, UP) / z)


# ---- svg helpers ---------------------------------------------------------
els = []


def fmt(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def poly(pts, stroke, w, fill="none", close=False, two_d=False):
    pts = pts if two_d else [proj(p) for p in pts]
    out = [pts[0]]
    for q in pts[1:]:
        if math.dist(q, out[-1]) >= 0.25:
            out.append(q)
    if close and len(out) > 2 and math.dist(out[0], out[-1]) < 0.25:
        out.pop()
    if len(out) < 2:
        return
    d = "M " + " L ".join(f"{fmt(x)} {fmt(y)}" for x, y in out) + (" Z" if close else "")
    els.append(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{w}" '
               f'stroke-linejoin="round" stroke-linecap="round"/>')


def polyline_chunks(pts3, stroke, w, n=60):
    """Long lines split into runs of <= n points (one subpath, <= 64 points each)."""
    pts = [proj(p) for p in pts3]
    i = 0
    while i < len(pts) - 1:
        poly(pts[i:i + n], stroke, w, two_d=True)
        i += n - 1


def clip_line(a, b, x0=-2.0, x1=482.0, y0=40.0, y1=222.0):
    """Liang-Barsky: a 2D segment clipped to the body, so nothing climbs into the header."""
    (ax, ay), (bx, by) = a, b
    dx, dy = bx - ax, by - ay
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, ax - x0), (dx, x1 - ax), (-dy, ay - y0), (dy, y1 - ay)):
        if p == 0:
            if q < 0:
                return None
            continue
        r = q / p
        if p < 0:
            t0 = max(t0, r)
        else:
            t1 = min(t1, r)
    return None if t0 >= t1 else [(ax + t0 * dx, ay + t0 * dy), (ax + t1 * dx, ay + t1 * dy)]


def line3(a, b, stroke, w):
    seg = clip_line(proj(a), proj(b))
    if seg:
        poly(seg, stroke, w, two_d=True)


def obox(o, U, N, a, b, z, edge, inner):
    """Oriented hidden-line box: corners o + a*U + b*N + z. Black body,
    silhouette at Line weight, edges between two visible faces at Hairline."""
    V = {(i, j, k): (o[0] + a[i] * U[0] + b[j] * N[0], o[1] + a[i] * U[1] + b[j] * N[1], z[k])
         for i in (0, 1) for j in (0, 1) for k in (0, 1)}
    faces = [[(0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)], [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)],
             [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)], [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)],
             [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)], [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]]
    cen = [sum(V[k][c] for k in V) / 8 for c in range(3)]
    vis = []
    for ks in faces:
        fc = [sum(V[k][c] for k in ks) / 4 for c in range(3)]
        if dot(sub(fc, cen), sub(CAM, fc)) > 0:
            vis.append(ks)
    for ks in vis:
        poly([V[k] for k in ks], "#000000", 0.01, fill="#000000", close=True)
    cnt = {}
    for ks in vis:
        for e in zip(ks, ks[1:] + ks[:1]):
            e = tuple(sorted(e))
            cnt[e] = cnt.get(e, 0) + 1
    for (p, q), c in sorted(cnt.items(), key=lambda kv: kv[1], reverse=True):
        poly([V[p], V[q]], inner if c == 2 else edge, HAIR if c == 2 else LINE)


# ---- scene: prism ----------------------------------------------------------
ZR = 38.0                      # ray height above the bench
PRISM_Z = (8.0, 80.0)          # the prism stands on a low table
S = 40.0                       # prism side
BASE_DEV = math.radians(9)
STEP = math.radians(8.5)       # angle between neighbouring rays
BETA = BASE_DEV + 1.5 * STEP
RHO = -BETA                    # prism turned so the fan's centre runs along the bench


def rot(p, a=RHO):
    return (p[0] * math.cos(a) - p[1] * math.sin(a), p[0] * math.sin(a) + p[1] * math.cos(a))


apex = rot((0.0, -S / math.sqrt(3)))
bl = rot((-S / 2, S / (2 * math.sqrt(3))))
br = rot((S / 2, S / (2 * math.sqrt(3))))
entry = ((apex[0] + bl[0]) / 2, (apex[1] + bl[1]) / 2)
exitp = ((apex[0] + br[0]) / 2, (apex[1] + br[1]) / 2)
ANG = [BASE_DEV + STEP * i + RHO for i in range(4)]   # sine, triangle, square, saw
IN_ANG = -BETA + RHO
DIRS = [(math.cos(a), math.sin(a)) for a in ANG]

# ---- scene: the slit -------------------------------------------------------
PHI = math.radians(26)                       # plate turned toward the camera
NP = (math.cos(PHI), math.sin(PHI))          # plate normal (rays cross along +NP)
UP_ = (-math.sin(PHI), math.cos(PHI))        # along the plate, across the fan
C0 = (235.0, 0.0)                            # where the plate crosses the fan's centre


def hit_t(i):
    return dot(NP, sub(C0, exitp)) / dot(NP, DIRS[i])


def at(i, t):
    return (exitp[0] + DIRS[i][0] * t, exitp[1] + DIRS[i][1] * t)


S_RAY = [dot(UP_, sub(at(i, hit_t(i)), C0)) for i in range(4)]   # where each ray meets the plate
SPACING = (S_RAY[3] - S_RAY[0]) / 3
s_c = S_RAY[0] + P["morph"] * 3 * SPACING                         # morph slides the slit
s_h = abs(SPACING) * (0.5 + 2.6 * P["overlap"])                    # overlap opens it
JAW, JAW_T, JAW_Z = 30.0, 5.0, 66.0
BENCH_Y = (-120.0, 150.0)


def ray_style(i):
    d = abs(S_RAY[i] - s_c)
    if d < s_h:
        if d < abs(SPACING) * 0.5:
            return True, BRIGHT, SUBJ
        return True, (G2 if 1 - d / s_h > 0.5 else G3), LINE
    return False, G3, HAIR


# ---- the four waves ----------------------------------------------------------
AMP, LAM0 = 7.0, 38.0


def wave(i, ph):
    """Band i at phase ph (cycles), with skew's breakpoint. Returns -1..1."""
    f = ph % 1.0
    if i == 0:      # sine, phase-distorted
        k = 0.5 * (1 - 0.9 * P["skew"])
        g = f / k * 0.5 if f < k else 0.5 + (f - k) / (1 - k) * 0.5
        return math.sin(2 * math.pi * g)
    if i == 1:      # triangle leaning to a ramp
        g = (f + 0.25) % 1.0
        kk = 0.5 + 0.45 * P["skew"]
        return -1 + 2 * g / kk if g < kk else 1 - 2 * (g - kk) / (1 - kk)
    if i == 2:      # square narrowing to a pulse
        return 1.0 if f < 0.5 - 0.45 * P["skew"] else -1.0
    return 1 - 2 * f  # saw: no breakpoint


def ray_points(i, t0, t1):
    lam = LAM0 * (1 - 0.18 * P["spread"] * (i - 1.5) / 1.5)      # spread pulls crest spacings apart
    ph0 = 0.25 * P["phase"] * i                                  # phase offsets each band
    smooth = 0.012 + 0.16 * (1 - P["tone"]) ** 2 * (1 + 0.5 * i / 3)  # tone rounds the edges
    pts, t = [], t0
    while t <= t1 + 1e-6:
        env = min(1.0, max(0.0, (t - 10) / 70))
        env = env * env * (3 - 2 * env)          # rays leave the glass close, open out as they part
        v = sum(wave(i, ph0 + t / lam + smooth * (j / 5 - 0.5)) for j in range(6)) / 6
        x, y = at(i, t)
        pts.append((x, y, ZR + AMP * env * v))
        t += 0.6
    keep = [pts[0]]
    for a, b in zip(pts[1:-1], pts[2:]):
        pa, pb, pk = proj(a), proj(b), proj(keep[-1])
        dx, dy = pb[0] - pk[0], pb[1] - pk[1]
        L = math.hypot(dx, dy) or 1
        if abs((pa[0] - pk[0]) * dy - (pa[1] - pk[1]) * dx) / L > 0.18 or math.dist(pk, pa) > 7:
            keep.append(a)
    keep.append(pts[-1])
    return keep


def t_screen_edge(i):
    t = hit_t(i)
    while proj((*at(i, t), ZR))[0] < 486 and t < 2000:
        t += 4
    return t


# ---- draw, back to front -------------------------------------------------------
# bench: front edge, a grain line, the far edge, all clipped to the body
X0, X1 = -600.0, 1200.0
poly([(X0, BENCH_Y[0], 0), (X1, BENCH_Y[0], 0), (X1, BENCH_Y[0], -16), (X0, BENCH_Y[0], -16)],
     "#000000", 0.01, fill="#000000", close=True)
line3((X0, 70.0, 0), (X1, 70.0, 0), GROUND, HAIR)
line3((X0, -50.0, 0), (X1, -50.0, 0), GROUND, HAIR)
line3((X0, BENCH_Y[1], 0), (X1, BENCH_Y[1], 0), G5, HAIR)
line3((X0, BENCH_Y[0], -16), (X1, BENCH_Y[0], -16), G5, HAIR)
line3((X0, BENCH_Y[0], 0), (X1, BENCH_Y[0], 0), G4, LINE)

# the rail the slit's carriage rides along (morph's travel)
for dn in (-9.0, 13.0):
    a = S_RAY[0] - JAW - 26
    b = S_RAY[3] + JAW + 26
    line3((C0[0] + a * UP_[0] + dn * NP[0], C0[1] + a * UP_[1] + dn * NP[1], 0),
          (C0[0] + b * UP_[0] + dn * NP[0], C0[1] + b * UP_[1] + dn * NP[1], 0), G5, HAIR)

# rays beyond the slit (behind the plate from here)
styles = [ray_style(i) for i in range(4)]
for i, (passes, col, w) in enumerate(styles):
    if passes:
        polyline_chunks(ray_points(i, hit_t(i) + JAW_T, t_screen_edge(i)), col, w)

# carriage, then the jaw further from the camera, then the nearer one
obox(C0, UP_, NP, (s_c - s_h - JAW - 5, s_c + s_h + JAW + 5), (-9, 13), (0, 6), G3, G5)
jaws = [(s_c + s_h, s_c + s_h + JAW), (s_c - s_h - JAW, s_c - s_h)]
jaws.sort(key=lambda j: -math.dist(CAM, (C0[0] + UP_[0] * sum(j) / 2, C0[1] + UP_[1] * sum(j) / 2, 30)))
for ja in jaws:
    obox(C0, UP_, NP, ja, (0, JAW_T), (6, JAW_Z), G2, G4)

# rays from the prism to the plate (in front of it)
for i, (passes, col, w) in enumerate(styles):
    end = hit_t(i) + (JAW_T if passes else 0)
    polyline_chunks(ray_points(i, 0, end), col, w)

# prism table: a low disc


def ring(r, z, n=48):
    return [(r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n), z) for k in range(n)]


def hull(pts):
    pts = sorted(pts)

    def half(seq):
        h = []
        for p in seq:
            while len(h) >= 2 and ((h[-1][0] - h[-2][0]) * (p[1] - h[-2][1]) -
                                   (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0])) <= 0:
                h.pop()
            h.append(p)
        return h
    lo, up = half(pts), half(list(reversed(pts)))
    return lo[:-1] + up[:-1]


R_T = 31.0
top = [proj(p) for p in ring(R_T, 8)]
poly(hull(top + [proj(p) for p in ring(R_T, 2)]), G3, LINE, fill="#000000", close=True, two_d=True)
poly(top, G5, HAIR, close=True, two_d=True)

# the prism: black glass, hidden-line
tri = [apex, br, bl]
z0, z1 = PRISM_Z
for a, b in zip(tri, tri[1:] + tri[:1]):
    n = (b[1] - a[1], -(b[0] - a[0]))
    c = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    if n[0] * (CAM[0] - c[0]) + n[1] * (CAM[1] - c[1]) > 0:
        poly([(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)],
             "#000000", 0.01, fill="#000000", close=True)
poly([(p[0], p[1], z1) for p in tri], "#000000", 0.01, fill="#000000", close=True)
poly([(entry[0], entry[1], ZR), (exitp[0], exitp[1], ZR)], G4, HAIR)      # the beam inside the glass
poly([(apex[0], apex[1], z0), (apex[0], apex[1], z1)], G4, HAIR)          # front edge between lit faces
poly([(apex[0], apex[1], z1), (br[0], br[1], z1)], G3, HAIR)
poly([(apex[0], apex[1], z1), (bl[0], bl[1], z1)], G3, HAIR)
poly([(bl[0], bl[1], z1), (br[0], br[1], z1), (br[0], br[1], z0), (apex[0], apex[1], z0),
      (bl[0], bl[1], z0)], G2, LINE, close=True)

# the incoming beam, from off the bench's left
line3((entry[0] - 900 * math.cos(IN_ANG), entry[1] - 900 * math.sin(IN_ANG), ZR),
      (entry[0], entry[1], ZR), G2, LINE)

# ---- frame -----------------------------------------------------------------
steps = ["#000000", "#323232", "#4B4B4B", "#646464", "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD"]
svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
       '  <!-- iris v5 rest: a prism on an optical bench. Generated by sketch.py. -->',
       '  <g id="preview_canvas">',
       '    <rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>',
       '  </g>', '  <g id="preview_header">']
for i, c in enumerate(steps):
    svg.append(f'    <rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
for i, t in enumerate(NAMES[:4]):
    tc = "#CBCBCB" if i < 2 else "#000000"
    svg.append(f'    <text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{tc}" stroke="none" '
               f'font-family="UniversNextPro-Light" font-size="10px">{t}</text>')
    svg.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{tc}" stroke="none" '
               f'font-family="UniversNextPro-Light" font-size="20px">{round(P[t] * 100)}%</text>')
for i, t in enumerate(NAMES[4:]):   # inactive page row of the two-page header
    svg.append(f'    <text transform="matrix(1 0 0 1 {5 + 120 * i} 32)" fill="#5A5A5A" stroke="none" '
               f'font-family="UniversNextPro-Light" font-size="10px">{t}</text>')
    svg.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 33)" fill="#707070" stroke="none" '
               f'font-family="UniversNextPro-Light" font-size="13px">{round(P[t] * 100)}%</text>')
svg.append('  </g>')
svg += ['  ' + e for e in els]
svg.append('</svg>')
open(OUT, "w").write("\n".join(svg) + "\n")
print(OUT, len(els), "paths")
