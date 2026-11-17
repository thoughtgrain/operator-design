#!/usr/bin/env python3
"""iris v1 - exploded view. One period of the mixed wave, large, on the front
plate (the assembled part), cut off by the frame's left and bottom edges. Its four
component waves are laminations pulled off it in depth along one shaft, sine
nearest, saw furthest. A sleeve on the shaft is the mixing window: morph slides
it, overlap lengthens it. Built in 3D, projected through one camera.

    python3 sketch.py [out.svg]
"""
import math, sys, os

P = dict(morph=0.3333, overlap=0.25, spread=0.0, tone=0.7, skew=0.0, phase=0.0)

# ---- greys (stock steps) ----------------------------------------------------
G1, G2, G3, G4, G5, G6, G7 = "#323232", "#4B4B4B", "#646464", "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD"

# ---- waves ------------------------------------------------------------------
def frac(t): return t - math.floor(t)

def skewed(t, k):
    """phase breakpoint: half the cycle in b of it (b = 0.5 -> 0.05)."""
    b = 0.5 - 0.45 * k
    t = frac(t)
    return 0.5 * t / b if t < b else 0.5 + 0.5 * (t - b) / (1 - b)

def wave(i, t, k=0.0):
    t = frac(t)
    if i == 0:  # sine
        return math.sin(2 * math.pi * skewed(t, k))
    if i == 1:  # triangle, leaning to a ramp
        b = 0.5 - 0.45 * k
        u = frac(t + b / 2)
        v = u / b if u < b else 1 - (u - b) / (1 - b)
        return 2 * v - 1
    if i == 2:  # square narrowing to a pulse
        b = 0.5 - 0.45 * k
        return 1.0 if t < b else -1.0
    return 1 - 2 * t  # saw

def weights(morph, overlap):
    c = morph * 3
    half = 0.5 + 1.5 * overlap
    w = []
    for i in range(4):
        d = abs(i - c)
        w.append(max(0.0, 1 - max(0.0, d - 0.15) / (half + 0.5)) ** 2)
    s = sum(w) or 1
    return [x / s for x in w]

def mixed(t, p):
    w = weights(p["morph"], p["overlap"])
    # tone: 2-pole low-pass, applied as a zero-phase harmonic roll-off
    N = 48
    fc = 1.5 + 30 * p["tone"] ** 2
    acc = 0.0
    for i, wi in enumerate(w):
        if wi < 1e-4:
            continue
        ph = i * 0.25 * p["phase"]
        # harmonic analysis of the component (numeric, coarse)
        M = 256
        for n in range(1, N + 1):
            a = sum(wave(i, m / M + ph, p["skew"]) * math.cos(2 * math.pi * n * m / M) for m in range(M)) * 2 / M
            b = sum(wave(i, m / M + ph, p["skew"]) * math.sin(2 * math.pi * n * m / M) for m in range(M)) * 2 / M
            g = 1 / math.sqrt(1 + (n / fc) ** 4)
            acc += wi * g * (a * math.cos(2 * math.pi * n * t) + b * math.sin(2 * math.pi * n * t))
    return acc

# ---- camera -----------------------------------------------------------------
CAM = (2.9, 2.9, -1.35)
LOOK = (-0.6, -0.4, 4.6)
FOC = 330.0
CX, CY = 262.0, 124.0

def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def norm(a):
    l = math.sqrt(dot(a, a)); return (a[0] / l, a[1] / l, a[2] / l)

FWD = norm(sub(LOOK, CAM))
RIGHT = norm(cross((0, 1, 0), FWD))
UP = cross(FWD, RIGHT)

def proj(p):
    d = sub(p, CAM)
    x, y, z = dot(d, RIGHT), dot(d, UP), dot(d, FWD)
    return (CX + FOC * x / z, CY - FOC * y / z)

def depth(p): return dot(sub(p, CAM), FWD)

# ---- scene ------------------------------------------------------------------
W2, H_TOP, H_BOT = 1.12, 1.22, -1.5     # plate half width, top, bottom
BORE_Y = -1.2
AMP = 0.92
Z_MIX = 0.0
THICK = 0.22                            # the assembled part has body
Z_COMP = [2.5, 3.95, 5.4, 6.85]

def fmt(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s

def pathd(pts, close=True):
    d = "M " + " L ".join(f"{fmt(x)} {fmt(y)}" for x, y in pts)
    return d + (" Z" if close else "")

def ribbon(pts, w):
    """polyline -> closed ribbon outlines of <= 64 points, mitred."""
    out = []
    step = 30
    i = 0
    while i < len(pts) - 1:
        seg = pts[i:i + step + 1]
        i += step
        L, R = [], []
        for k, p in enumerate(seg):
            a = seg[k - 1] if k > 0 else None
            b = seg[k + 1] if k < len(seg) - 1 else None
            def n_of(u, v):
                dx, dy = v[0] - u[0], v[1] - u[1]; l = math.hypot(dx, dy) or 1
                return (-dy / l, dx / l)
            if a and b:
                n1, n2 = n_of(a, p), n_of(p, b)
                nx, ny = n1[0] + n2[0], n1[1] + n2[1]; l = math.hypot(nx, ny) or 1
                nx, ny = nx / l, ny / l
                c = max(0.5, nx * n1[0] + ny * n1[1])
                m = w / 2 / c
            else:
                nx, ny = n_of(a, p) if a else n_of(p, b)
                m = w / 2
            L.append((p[0] + nx * m, p[1] + ny * m)); R.append((p[0] - nx * m, p[1] - ny * m))
        out.append(L + R[::-1])
    return out

els = []
def poly(pts, fill="#000000", stroke=G2, sw=1.2):
    els.append(f'<path d="{pathd(pts)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
def line(pts, w, col):
    for r in ribbon(pts, w):
        els.append(f'<path d="{pathd(r)}" fill="{col}" stroke="none"/>')

def dashed(a, b, col, w=1.0, dash=7.0, gap=4.0, chain=False):
    """dashed / chain line between two screen points, as small ribbons."""
    L = math.dist(a, b); ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    s = 0.0; pat = [dash, gap, 2.0, gap] if chain else [dash, gap]; k = 0
    while s < L:
        e = min(L, s + pat[k % len(pat)])
        if k % 2 == 0 and e - s > 1.5:
            line([(a[0] + ux * s, a[1] + uy * s), (a[0] + ux * e, a[1] + uy * e)], w, col)
        s = e; k += 1

def plate(z, i, active, near_ok=True):
    pass

# window / emphasis
w = weights(P["morph"], P["overlap"])
c = P["morph"] * 3
half = 0.5 + 1.5 * P["overlap"]
def style(i):
    d = abs(i - c)
    if d < 0.5: return 2.0, G5
    if d <= half + 0.5: return 1.5, G4
    return 1.2, G3

T = [k / 60 for k in range(61)]

def card_corners(z, rot=0.0, dx=0.0):
    def R(x, y):
        # spread: each plate turns about the shaft (bore) in its own plane
        yy = y - BORE_Y
        return (x * math.cos(rot) - yy * math.sin(rot) + dx, BORE_Y + x * math.sin(rot) + yy * math.cos(rot), z)
    return R

draw = []   # (depth, fn)

# components, far to near
for i in range(4):
    z = Z_COMP[i]
    rot = (i - 1.5) * 0.06 * P["spread"]
    dx = i * 0.18 * P["phase"]
    R = card_corners(z, rot, dx)
    def fn(i=i, R=R):
        corners = [proj(R(-W2, H_BOT)), proj(R(W2, H_BOT)), proj(R(W2, H_TOP)), proj(R(-W2, H_TOP))]
        poly(corners, "#000000", G2, 1.2)
        # zero line, hairline
        line([proj(R(-1.0, 0)), proj(R(1.0, 0))], 1.0, G1)
        # bore
        bo = [proj(R(0.13 * math.cos(a * math.pi / 8), BORE_Y + 0.13 * math.sin(a * math.pi / 8))) for a in range(16)]
        poly(bo, "#000000", G2, 1.2)
        sw, col = style(i)
        pts = [proj(R(-1 + 2 * t, AMP * wave(i, t, P["skew"]))) for t in T]
        if i == 2:  # square: give the risers a sliver of slope
            pts = []
            b = 0.5 - 0.45 * P["skew"]
            for t, v in [(0, 1), (b - 0.004, 1), (b + 0.004, -1), (0.996, -1)]:
                pts.append(proj(R(-1 + 2 * t, AMP * v)))
            # dense enough for the mitre
        if i == 3:
            pts = [proj(R(-1 + 2 * t, AMP * wave(3, t))) for t in (0, 0.5, 0.998)]
        line(pts, sw, col)
    draw.append((depth((0, 0, z)), fn))

# shaft (chain line) and the window sleeve, split per gap
zs = [Z_MIX + THICK] + Z_COMP + [Z_COMP[-1] + 1.4]
for k in range(len(zs) - 1):
    za, zb = zs[k], zs[k + 1]
    def fn(za=za, zb=zb):
        dashed(proj((0, BORE_Y, za)), proj((0, BORE_Y, zb)), G3, 1.0, chain=True)
    draw.append((depth((0, 0, (za + zb) / 2)) + 0.01, fn))

# sleeve = mixing window on the shaft
zc = Z_COMP[0] + c * (Z_COMP[1] - Z_COMP[0])
hz = half * (Z_COMP[1] - Z_COMP[0])
z0, z1 = zc - hz, zc + hz
SR = 0.26
def ring(z):
    return [proj((SR * math.cos(a * math.pi / 12), BORE_Y + SR * math.sin(a * math.pi / 12), z)) for a in range(24)]
# sleeve pieces between plates
cuts = sorted(set([z0, z1] + [zz for zz in Z_COMP if z0 < zz < z1]))
for a, b in zip(cuts, cuts[1:]):
    def fn(a=a, b=b):
        ra, rb = ring(a), ring(b)
        # silhouette: extreme points across the shaft direction
        ax = proj((0, BORE_Y, a)); bx = proj((0, BORE_Y, b))
        ux, uy = bx[0] - ax[0], bx[1] - ax[1]; l = math.hypot(ux, uy) or 1
        nx, ny = -uy / l, ux / l
        hi_a = max(ra, key=lambda p: p[0] * nx + p[1] * ny); lo_a = min(ra, key=lambda p: p[0] * nx + p[1] * ny)
        hi_b = max(rb, key=lambda p: p[0] * nx + p[1] * ny); lo_b = min(rb, key=lambda p: p[0] * nx + p[1] * ny)
        poly([hi_a, hi_b, lo_b, lo_a], "#000000", G5, 1.5)
        if b == z1:
            poly(rb, "#000000", G5, 1.5)
    draw.append((depth((0, 0, (a + b) / 2)) - 0.02, fn))

# the assembled part (mix), front, with body
def mixfn():
    Rf = lambda x, y: (x, y, Z_MIX)
    Rb = lambda x, y: (x, y, Z_MIX + THICK)
    # visible side: top and right faces
    poly([proj(Rf(-W2, H_TOP)), proj(Rf(W2, H_TOP)), proj(Rb(W2, H_TOP)), proj(Rb(-W2, H_TOP))], "#000000", G3, 1.5)
    poly([proj(Rf(W2, H_BOT)), proj(Rb(W2, H_BOT)), proj(Rb(W2, H_TOP)), proj(Rf(W2, H_TOP))], "#000000", G3, 1.5)
    poly([proj(Rf(-W2, H_BOT)), proj(Rf(W2, H_BOT)), proj(Rf(W2, H_TOP)), proj(Rf(-W2, H_TOP))], "#000000", G3, 1.5)
    line([proj(Rf(-1.0, 0)), proj(Rf(1.0, 0))], 1.0, G2)
    bo = [proj((0.13 * math.cos(a * math.pi / 8), BORE_Y + 0.13 * math.sin(a * math.pi / 8), Z_MIX)) for a in range(16)]
    poly(bo, "#000000", G3, 1.2)
    pts = [proj(Rf(-1 + 2 * t, AMP * mixed(t, P))) for t in [k / 90 for k in range(91)]]
    line(pts, 2.5, G7)
draw.append((depth((0, 0, Z_MIX)) - 1, mixfn))

for _, fn in sorted(draw, key=lambda d: -d[0]):
    fn()

# ---- frame ------------------------------------------------------------------
HEAD = """<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">
  <!-- iris v1, subject pass 01: exploded view. Generated by sketch.py; edit that, not this. -->
  <g id="preview_canvas">
    <rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>
  </g>
  <g id="preview_header">
    <rect x="0" y="0" width="60" height="20" fill="#000000" stroke="none"/>
    <rect x="60" y="0" width="60" height="20" fill="#323232" stroke="none"/>
    <rect x="120" y="0" width="60" height="20" fill="#4B4B4B" stroke="none"/>
    <rect x="180" y="0" width="60" height="20" fill="#646464" stroke="none"/>
    <rect x="240" y="0" width="60" height="20" fill="#7D7D7D" stroke="none"/>
    <rect x="300" y="0" width="60" height="20" fill="#969696" stroke="none"/>
    <rect x="360" y="0" width="60" height="20" fill="#AFAFAF" stroke="none"/>
    <rect x="420" y="0" width="60" height="20" fill="#CDCDCD" stroke="none"/>
    <text transform="matrix(1 0 0 1 5 10)" fill="#CBCBCB" stroke="none" font-family="UniversNextPro-Light" font-size="10px">morph</text>
    <text transform="matrix(1 0 0 1 125 10)" fill="#CBCBCB" stroke="none" font-family="UniversNextPro-Light" font-size="10px">overlap</text>
    <text transform="matrix(1 0 0 1 245 10)" fill="#000000" stroke="none" font-family="UniversNextPro-Light" font-size="10px">spread</text>
    <text transform="matrix(1 0 0 1 365 10)" fill="#000000" stroke="none" font-family="UniversNextPro-Light" font-size="10px">tone</text>
    <text transform="matrix(1 0 0 1 65 17.44)" fill="#CBCBCB" stroke="none" font-family="UniversNextPro-Light" font-size="20px">33%</text>
    <text transform="matrix(1 0 0 1 185 17.44)" fill="#CBCBCB" stroke="none" font-family="UniversNextPro-Light" font-size="20px">25%</text>
    <text transform="matrix(1 0 0 1 305 17.44)" fill="#000000" stroke="none" font-family="UniversNextPro-Light" font-size="20px">0%</text>
    <text transform="matrix(1 0 0 1 425 17.44)" fill="#000000" stroke="none" font-family="UniversNextPro-Light" font-size="20px">70%</text>
    <text transform="matrix(1 0 0 1 5 32)" fill="#5A5A5A" stroke="none" font-family="UniversNextPro-Light" font-size="10px">skew</text>
    <text transform="matrix(1 0 0 1 65 34)" fill="#707070" stroke="none" font-family="UniversNextPro-Light" font-size="13px">0%</text>
    <text transform="matrix(1 0 0 1 125 32)" fill="#5A5A5A" stroke="none" font-family="UniversNextPro-Light" font-size="10px">phase</text>
    <text transform="matrix(1 0 0 1 185 34)" fill="#707070" stroke="none" font-family="UniversNextPro-Light" font-size="13px">0%</text>
  </g>
  <path id="iris_palette_0" d="M 700 300 L 704 300 L 704 304 Z" fill="#CDCDCD" stroke="none"/>
"""
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "rest.svg")
with open(out, "w") as f:
    f.write(HEAD + "\n".join("  " + e for e in els) + "\n</svg>\n")
print(out, len(els), "elements")
