#!/usr/bin/env python3
"""iris v5 · subject pass 1 · one scene: a prism on an optical bench.

One beam (the note's pitch) enters a glass prism and leaves as four rays, one
per band (sine, triangle, square, saw), fanned by harmonic content. Each ray is
drawn as its own wave travelling. Further down the bench an adjustable slit (two
jaws on a rail) stands across the fan: morph slides the slit along the fan,
overlap opens its jaws, and only the rays the slit lets through carry on past it.

Everything is modelled in 3D (x along the bench, y into the bench, z up) and
projected through one camera. Detailed line art: outer edges Line weight, inner
structure Hairline, black fills so solids hide what's behind them.

    python3 sketch.py [out.svg] [morph overlap spread tone skew phase]
"""
import math
import sys

# ---- controls (defaults) -------------------------------------------------
P = dict(morph=0.3333, overlap=0.25, spread=0.0, tone=0.7, skew=0.0, phase=0.0)
if len(sys.argv) > 2:
    for k, v in zip(["morph", "overlap", "spread", "tone", "skew", "phase"], sys.argv[2:]):
        P[k] = float(v)
OUT = sys.argv[1] if len(sys.argv) > 1 else "rest.svg"

# ---- palette / weights ---------------------------------------------------
BRIGHT, G1, G2, G3, G4, G5 = "#CDCDCD", "#AFAFAF", "#969696", "#7D7D7D", "#646464", "#4B4B4B"
GROUND = "#323232"
HAIR, LINE, SUBJ = 1.0, 1.5, 2.2

# ---- camera --------------------------------------------------------------
TARGET = (150.0, 45.0, 10.0)
DIST, AZ, EL = 620.0, math.radians(-17), math.radians(27)
CAM = (TARGET[0] + DIST * math.cos(EL) * math.sin(AZ),
       TARGET[1] - DIST * math.cos(EL) * math.cos(AZ),
       TARGET[2] + DIST * math.sin(EL))


def _norm(v):
    l = math.sqrt(sum(c * c for c in v))
    return tuple(c / l for c in v)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


FWD = _norm(tuple(t - c for t, c in zip(TARGET, CAM)))
RIGHT = _norm(_cross(FWD, (0, 0, 1)))
UP = _cross(RIGHT, FWD)
FOCAL = 1.0
# screen fit (pixels per unit of the image plane, and where the target lands)
K, CX, CY = 640.0, 236.0, 128.0


def proj(p):
    d = tuple(a - c for a, c in zip(p, CAM))
    x, y, z = (sum(a * b for a, b in zip(d, RIGHT)), sum(a * b for a, b in zip(d, UP)),
               sum(a * b for a, b in zip(d, FWD)))
    return (CX + K * FOCAL * x / z, CY - K * FOCAL * y / z)


# ---- svg helpers ---------------------------------------------------------
els = []


def fmt(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def poly(pts3, stroke, w, fill="none", close=False, two_d=False):
    pts = pts3 if two_d else [proj(p) for p in pts3]
    # drop points closer than 1/4 px
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
    """Long open lines split into runs of <= n points (one subpath, <= 64 points)."""
    pts = [proj(p) for p in pts3]
    i = 0
    while i < len(pts) - 1:
        poly(pts[i:i + n], stroke, w, two_d=True)
        i += n - 1


def box(x0, x1, y0, y1, z0, z1, edge, inner, fill="#000000"):
    """Hidden-line box: black silhouette at Line weight, visible inner edges at Hairline."""
    V = {(i, j, k): (x, y, z) for i, x in enumerate((x0, x1)) for j, y in enumerate((y0, y1))
         for k, z in enumerate((z0, z1))}
    faces = {  # outward normal, corner keys (ccw-ish)
        (-1, 0, 0): [(0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)],
        (1, 0, 0): [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)],
        (0, -1, 0): [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)],
        (0, 1, 0): [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)],
        (0, 0, 1): [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)],
        (0, 0, -1): [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)],
    }
    vis = []
    for n, ks in faces.items():
        c = [sum(V[k][a] for k in ks) / 4 for a in range(3)]
        to_cam = tuple(cc - p for cc, p in zip(CAM, c))
        if sum(a * b for a, b in zip(n, to_cam)) > 0:
            vis.append(ks)
    for ks in vis:
        poly([V[k] for k in ks], fill, 0.01, fill=fill, close=True)
    # edges: count visible faces sharing each edge (1 = silhouette, 2 = inner)
    cnt = {}
    for ks in vis:
        for a, b in zip(ks, ks[1:] + ks[:1]):
            e = tuple(sorted((a, b)))
            cnt[e] = cnt.get(e, 0) + 1
    for (a, b), c in cnt.items():
        if c == 2:
            poly([V[a], V[b]], inner, HAIR)
    for (a, b), c in cnt.items():
        if c == 1:
            poly([V[a], V[b]], edge, LINE)


# ---- scene geometry ------------------------------------------------------
ZR = 26.0                      # ray height above the bench
PRISM_Z = (8.0, 52.0)          # prism sits on a small table
S = 34.0                       # prism side
apex = (0.0, -S / math.sqrt(3))
bl = (-S / 2, S / (2 * math.sqrt(3)))
br = (S / 2, S / (2 * math.sqrt(3)))
entry = ((apex[0] + bl[0]) / 2, (apex[1] + bl[1]) / 2)
exitp = ((apex[0] + br[0]) / 2, (apex[1] + br[1]) / 2)

BASE_DEV = math.radians(9)
ANG = [BASE_DEV + math.radians(6.5) * i for i in range(4)]   # sine .. saw
XC = 300.0                                                     # slit plane
BENCH_Y = (-70.0, 190.0)


def ray_y(i, x):
    return exitp[1] + (x - exitp[0]) * math.tan(ANG[i])


SPACING = (ray_y(3, XC) - ray_y(0, XC)) / 3

# slit: morph slides the centre along the fan, overlap opens the jaws
slit_c = ray_y(0, XC) + P["morph"] * 3 * SPACING
slit_h = SPACING * (0.5 + 2.6 * P["overlap"])
JAW = 46.0
JAW_Z = 74.0
JAW_T = 5.0


def wave(i, ph):
    """One band's waveform at phase ph (cycles), with skew. Returns -1..1."""
    f = ph % 1.0
    k = 0.5 * (1 - 0.9 * P["skew"])  # breakpoint
    if i == 0:      # sine, phase-distorted
        g = f / k * 0.5 if f < k else 0.5 + (f - k) / (1 - k) * 0.5
        return math.sin(2 * math.pi * g)
    if i == 1:      # triangle leaning to a ramp
        g = (f + 0.25) % 1.0
        kk = 0.5 + 0.45 * P["skew"]
        return -1 + 2 * g / kk if g < kk else 1 - 2 * (g - kk) / (1 - kk)
    if i == 2:      # square narrowing to a pulse
        w = 0.5 - 0.45 * P["skew"]
        return 1.0 if f < w else -1.0
    return 1 - 2 * f  # saw


AMP = 6.0
LAM0 = 30.0


def ray_points(i, x0, x1):
    lam = LAM0 * (1 - 0.18 * P["spread"] * (i - 1.5) / 1.5)
    ph0 = 0.25 * P["phase"] * i
    smooth = 0.012 + 0.16 * (1 - P["tone"]) ** 2 * (1 + 0.5 * i / 3)  # tone rounds corners
    pts = []
    x = x0
    step = 0.6
    while x <= x1 + 1e-6:
        t = math.hypot(x - exitp[0], ray_y(i, x) - exitp[1])
        env = min(1.0, max(0.0, (t - 6) / 46))
        env = env * env * (3 - 2 * env)
        ph = ph0 + t / lam
        # box-filter the waveform: the low-pass softens edges, hits saw/square hardest
        n = 6
        v = sum(wave(i, ph + smooth * (j / (n - 1) - 0.5)) for j in range(n)) / n
        pts.append((x, ray_y(i, x), ZR + AMP * env * v))
        x += step
    # thin to keep corners and drop near-collinear points
    keep = [pts[0]]
    for a, b in zip(pts[1:-1], pts[2:]):
        pa, pb, pk = proj(a), proj(b), proj(keep[-1])
        # deviation of a from line keep->b
        dx, dy = pb[0] - pk[0], pb[1] - pk[1]
        L = math.hypot(dx, dy) or 1
        dev = abs((pa[0] - pk[0]) * dy - (pa[1] - pk[1]) * dx) / L
        if dev > 0.18 or math.dist(pk, pa) > 7:
            keep.append(a)
    keep.append(pts[-1])
    return keep


def ray_style(i):
    d = abs(ray_y(i, XC) - slit_c)
    if d < slit_h:
        wgt = 1 - d / slit_h
        if d < SPACING * 0.5:
            return True, BRIGHT, SUBJ, wgt
        return True, (G2 if wgt > 0.5 else G3), LINE, wgt
    return False, G4, HAIR, 0


# ---- draw ----------------------------------------------------------------
els.append('<rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>')

# bench: top face and front edge, grain in the ground grey
X0, X1 = -400.0, 900.0
poly([(X0, BENCH_Y[0], 0), (X1, BENCH_Y[0], 0), (X1, BENCH_Y[0], -16), (X0, BENCH_Y[0], -16)],
     "#000000", 0.01, fill="#000000", close=True)
for yy in (-30.0, 20.0, 75.0, 135.0):
    poly([(X0, yy, 0), (X1, yy, 0)], GROUND, HAIR)
poly([(X0, BENCH_Y[0], -16), (X1, BENCH_Y[0], -16)], G5, HAIR)
poly([(X0, BENCH_Y[0], 0), (X1, BENCH_Y[0], 0)], G4, LINE)
poly([(X0, BENCH_Y[1], 0), (X1, BENCH_Y[1], 0)], G5, HAIR)

# rail the slit rides on (morph slides it along y)
for dx in (-7.0, 13.0):
    poly([(XC + dx, BENCH_Y[0] + 6, 0), (XC + dx, BENCH_Y[1] - 6, 0)], G5, HAIR)

# rays beyond the slit (behind the jaws from this camera)
for i in range(4):
    passes, col, w, _ = ray_style(i)
    if passes:
        polyline_chunks(ray_points(i, XC + JAW_T, 820.0), col, w)

# slit: carriage, then far jaw, then near jaw
lo, hi = slit_c - slit_h, slit_c + slit_h
box(XC - 9, XC + 15, lo - JAW - 4, hi + JAW + 4, 0, 6, G3, G5)
box(XC, XC + JAW_T, hi, hi + JAW, 6, JAW_Z, G3, G4)
box(XC, XC + JAW_T, lo - JAW, lo, 6, JAW_Z, G3, G4)

# rays from the prism to the slit
for i in range(4):
    passes, col, w, _ = ray_style(i)
    x_end = XC if not passes else XC + JAW_T
    pre_col, pre_w = (col, w) if col == BRIGHT else (G3, HAIR if not passes else LINE)
    if passes and col != BRIGHT:
        pre_col, pre_w = col, LINE
    polyline_chunks(ray_points(i, exitp[0], x_end), pre_col, pre_w)

# prism table: a low disc on a short post
R_T = 30.0


def ring(r, z, n=48):
    return [(r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n), z) for k in range(n)]


top = [proj(p) for p in ring(R_T, 8)]
bot = [proj(p) for p in ring(R_T, 3)]
# silhouette of the disc: hull of both ellipses (lower half of bottom + upper half of top)
hull = sorted(top + bot)
lower, upper = [], []
for p in hull:
    while len(lower) >= 2 and ((lower[-1][0] - lower[-2][0]) * (p[1] - lower[-2][1]) -
                               (lower[-1][1] - lower[-2][1]) * (p[0] - lower[-2][0])) <= 0:
        lower.pop()
    lower.append(p)
for p in reversed(hull):
    while len(upper) >= 2 and ((upper[-1][0] - upper[-2][0]) * (p[1] - upper[-2][1]) -
                               (upper[-1][1] - upper[-2][1]) * (p[0] - upper[-2][0])) <= 0:
        upper.pop()
    upper.append(p)
sil = lower[:-1] + upper[:-1]
poly(sil, G3, LINE, fill="#000000", close=True, two_d=True)
poly(top, G5, HAIR, close=True, two_d=True)

# the prism: hidden-line triangular prism, black glass
tri = [apex, br, bl]
z0, z1 = PRISM_Z
faces = []
for a, b in zip(tri, tri[1:] + tri[:1]):
    n = (b[1] - a[1], -(b[0] - a[0]))  # outward for clockwise-in-xy order
    c = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    if n[0] * (CAM[0] - c[0]) + n[1] * (CAM[1] - c[1]) > 0:
        faces.append((a, b))
sil_pts = []
for a, b in faces:
    poly([(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)],
         "#000000", 0.01, fill="#000000", close=True)
poly([(p[0], p[1], z1) for p in tri], "#000000", 0.01, fill="#000000", close=True)
# glass detail: the beam's path through the glass, and a bevel line inside the top face
poly([(entry[0], entry[1], ZR), (exitp[0], exitp[1], ZR)], G4, HAIR)
inset = [(p[0] * 0.78, p[1] * 0.78 + 0.0, z1) for p in tri]
poly(inset, G5, HAIR, close=True)
# visible vertical edges between visible faces = inner edges
vis_edges_inner = [apex]  # apex edge sits between the two visible faces
for p in vis_edges_inner:
    poly([(p[0], p[1], z0), (p[0], p[1], z1)], G4, HAIR)
# top triangle edges (silhouette where the top meets the hidden face, inner where it meets a visible one)
poly([(apex[0], apex[1], z1), (br[0], br[1], z1)], G3, HAIR)
poly([(apex[0], apex[1], z1), (bl[0], bl[1], z1)], G3, HAIR)
# silhouette
poly([(bl[0], bl[1], z1), (br[0], br[1], z1), (br[0], br[1], z0), (apex[0], apex[1], z0),
      (bl[0], bl[1], z0)], G2, LINE, close=True)

# incoming beam: one line from off the bench's left, ending at the entry face
dirx = math.cos(BASE_DEV + math.radians(9.75))
diry = math.sin(BASE_DEV + math.radians(9.75))
start = (entry[0] - 400 * dirx, entry[1] + 400 * diry, ZR)
poly([start, (entry[0], entry[1], ZR)], G2, LINE)

svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
       '  <!-- iris v5 rest: prism on an optical bench, generated by sketch.py -->',
       '  <g id="preview_canvas">', '    ' + els[0], '  </g>']
steps = ["#000000", "#323232", "#4B4B4B", "#646464", "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD"]
svg.append('  <g id="preview_header">')
for i, c in enumerate(steps):
    svg.append(f'    <rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
titles = ["morph", "overlap", "spread", "tone"]
vals = [f"{round(P[k] * 100)}%" for k in titles]
for i, (t, v) in enumerate(zip(titles, vals)):
    tc = "#CBCBCB" if i < 2 else "#000000"
    svg.append(f'    <text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{tc}" stroke="none" '
               f'font-family="UniversNextPro-Light" font-size="10px">{t}</text>')
    svg.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{tc}" stroke="none" '
               f'font-family="UniversNextPro-Light" font-size="20px">{v}</text>')
# inactive page row (two-page header)
for i, t in enumerate(["skew", "phase"]):
    svg.append(f'    <text transform="matrix(1 0 0 1 {5 + 120 * i} 31)" fill="#5A5A5A" stroke="none" '
               f'font-family="UniversNextPro-Light" font-size="10px">{t}</text>')
    svg.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 33)" fill="#707070" stroke="none" '
               f'font-family="UniversNextPro-Light" font-size="13px">{round(P[t] * 100)}%</text>')
svg.append('  </g>')
svg += ['  ' + e for e in els[1:]]
svg.append('</svg>')
open(OUT, "w").write("\n".join(svg) + "\n")
print(OUT, len(els) - 1, "paths")
