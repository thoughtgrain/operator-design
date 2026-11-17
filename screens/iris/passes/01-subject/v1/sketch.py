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
CAM = (3.4, 1.6, -3.0)
LOOK = (-0.4, -0.2, 5.0)
FOC = 450.0
CX, CY = 262.0, 96.0

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
# Every part is a lamination: a sheet whose top edge is cut to one period of its
# wave, flat below, with a bore for the shaft. The assembled part (front) is the
# four sheets together, so its top edge is the mix.
W2, H_BOT = 1.3, -1.75                  # half width, flat bottom
PER = 1.16                              # half a period's width on the sheet
AMP = 0.5
BORE_Y = -1.2
PIN_X = 1.02                            # locating pin near the sheets' outer corner
Z_MIX, THICK = 0.0, 0.6               # the assembled part: four laminations thick
Z_COMP = [2.9, 5.2, 7.5, 9.8]         # sine, triangle, square, saw

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
    L = math.dist(a, b)
    if L < 1: return
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    s = 0.0; pat = [dash, gap, 4.5, gap] if chain else [dash, gap]; k = 0
    while s < L:
        e = min(L, s + pat[k % len(pat)])
        if k % 2 == 0 and e - s > 4.0:
            line([(a[0] + ux * s, a[1] + uy * s), (a[0] + ux * e, a[1] + uy * e)], w, col)
        s = e; k += 1

c = P["morph"] * 3
half = 0.5 + 1.5 * P["overlap"]
def style(i):
    d = abs(i - c)
    if d < 0.5: return 2.0, G5
    if d <= half + 0.5: return 1.5, G4
    return 1.2, G3

def profile(i, t):
    if i < 0: return AMP * mixed(t, P)
    return AMP * wave(i, t, P["skew"])

def ts(i):
    if i == 2:
        b = 0.5 - 0.45 * P["skew"]
        return [0.0, 0.25, b - 0.006, b + 0.006, 0.75, 1.0]
    if i == 3:
        return [0.0, 0.5, 0.994, 1.0]
    return [k / 56 for k in range(57)]

def sheet(i, z, rot=0.0, dx=0.0):
    """world points of the sheet's top profile and its outline."""
    def R(x, y):
        xx, yy = x - PIN_X, y - BORE_Y
        return (PIN_X + xx * math.cos(rot) - yy * math.sin(rot) + dx, BORE_Y + xx * math.sin(rot) + yy * math.cos(rot), z)
    T = ts(i)
    if i == 3:  # saw: the drop is a riser, give it a sliver of slope
        top = [R(-PER, profile(3, 0)), R(0, 0), R(PER - 0.012, profile(3, 0.994)), R(PER + 0.012, AMP)]
    else:
        top = [R(-PER + 2 * PER * t, profile(i, t)) for t in T]
    y0, y1 = top[0][1], top[-1][1]
    outline = [R(-W2, H_BOT), R(W2, H_BOT), R(W2, y1)] + top[::-1] + [R(-W2, y0)]
    return top, outline, R

draw = []

for i in range(4):
    z = Z_COMP[i]
    rot = (i - 1.5) * 0.08 * P["spread"]
    dx = i * 0.2 * P["phase"]
    def fn(i=i, z=z, rot=rot, dx=dx):
        top, outline, R = sheet(i, z, rot, dx)
        poly([proj(p) for p in outline], "#000000", G2, 1.2)
        bo = [proj(R(PIN_X + 0.12 * math.cos(a * math.pi / 8), BORE_Y + 0.12 * math.sin(a * math.pi / 8))) for a in range(16)]
        poly(bo, "#000000", G2, 1.2)
        sw, col = style(i)
        line([proj(p) for p in top], sw, col)
    draw.append((depth((0, 0, z)), fn))

# shaft: chain line through the bores, split per gap so plates hide it
zs = [Z_MIX + THICK] + Z_COMP + [Z_COMP[-1] + 2.0]
for k in range(len(zs) - 1):
    za, zb = zs[k], zs[k + 1]
    def fn(za=za, zb=zb):
        dashed(proj((PIN_X, BORE_Y, za)), proj((PIN_X, BORE_Y, zb)), G3, 1.0, chain=True)
    draw.append((depth((0, 0, (za + zb) / 2)), fn))

# sleeve on the shaft = the mixing window
zc = Z_COMP[0] + c * (Z_COMP[1] - Z_COMP[0])
hz = half * (Z_COMP[1] - Z_COMP[0])
z0, z1 = zc - hz, zc + hz
SR = 0.26
def ring(z):
    return [proj((PIN_X + SR * math.cos(a * math.pi / 12), BORE_Y + SR * math.sin(a * math.pi / 12), z)) for a in range(24)]
cuts = sorted(set([z0, z1] + [zz for zz in Z_COMP if z0 < zz < z1]))
for a, b in zip(cuts, cuts[1:]):
    def fn(a=a, b=b):
        ra, rb = ring(a), ring(b)
        ax = proj((PIN_X, BORE_Y, a)); bx = proj((PIN_X, BORE_Y, b))
        ux, uy = bx[0] - ax[0], bx[1] - ax[1]; l = math.hypot(ux, uy) or 1
        nx, ny = -uy / l, ux / l
        key = lambda p: p[0] * nx + p[1] * ny
        hi_a, lo_a = max(ra, key=key), min(ra, key=key)
        hi_b, lo_b = max(rb, key=key), min(rb, key=key)
        poly([hi_a, hi_b, lo_b, lo_a], "#000000", G5, 1.5)
        if b == z1:
            poly(rb, "#000000", G5, 1.5)
    draw.append((depth((0, 0, (a + b) / 2)) - 0.01, fn))

# the assembled part, front, with body
def mixfn():
    T = [k / 90 for k in range(91)]
    front = [(-PER + 2 * PER * t, profile(-1, t), Z_MIX) for t in T]
    back = [(x, y, Z_MIX + THICK) for x, y, _ in front]
    fo = [(-W2, H_BOT, Z_MIX), (W2, H_BOT, Z_MIX), (W2, front[-1][1], Z_MIX)] + front[::-1] + [(-W2, front[0][1], Z_MIX)]
    bo = [(x, y, Z_MIX + THICK) for x, y, _ in fo]
    # back face, then the top surface edge, then the front face
    for part in (bo[:3] + bo[3:3 + 30][::-1][::-1],):
        pass
    for k in range(0, len(fo), 30):
        pass
    for chunk in (bo,):
        pts = [proj(p) for p in chunk]
        # too many points: draw as two halves
        poly(pts[:3] + pts[3:3 + 46] + [proj((back[45][0], H_BOT, Z_MIX + THICK))], "#000000", G2, 1.2) if False else None
    # back face outline (split into halves so each path stays <= 64 points)
    hb = 45
    left = [(-W2, H_BOT), (back[hb][0], H_BOT)] + [(p[0], p[1]) for p in back[:hb + 1]][::-1] + [(-W2, back[0][1])]
    right = [(back[hb][0], H_BOT), (W2, H_BOT), (W2, back[-1][1])] + [(p[0], p[1]) for p in back[hb:]][::-1]
    for half_ in (left, right):
        poly([proj((x, y, Z_MIX + THICK)) for x, y in half_], "#000000", "#000000", 0.6)
    line([proj(p) for p in back], 1.0, G3)
    # seams: where the four laminations meet on the top surface
    for q in (1, 2, 3):
        zq = Z_MIX + THICK * q / 4
        line([proj((p[0], p[1], zq)) for p in front[::2]], 1.0, G2)
    line([proj((W2, front[-1][1], Z_MIX)), proj((W2, front[-1][1], Z_MIX + THICK))], 1.0, G3)
    line([proj((W2, back[-1][1], Z_MIX + THICK)), proj((W2, H_BOT, Z_MIX + THICK))], 1.0, G3)
    # front face
    leftf = [(-W2, H_BOT), (front[hb][0], H_BOT)] + [(p[0], p[1]) for p in front[:hb + 1]][::-1] + [(-W2, front[0][1])]
    rightf = [(front[hb][0], H_BOT), (W2, H_BOT), (W2, front[-1][1])] + [(p[0], p[1]) for p in front[hb:]][::-1]
    for half_ in (leftf, rightf):
        poly([proj((x, y, Z_MIX)) for x, y in half_], "#000000", "#000000", 0.6)
    line([proj((W2, front[-1][1], Z_MIX)), proj((W2, H_BOT, Z_MIX))], 1.5, G3)
    line([proj((-W2, front[0][1], Z_MIX)), proj((-PER, front[0][1], Z_MIX))], 1.5, G3)
    line([proj((PER, front[-1][1], Z_MIX)), proj((W2, front[-1][1], Z_MIX))], 1.5, G3)
    bo = [proj((PIN_X + 0.12 * math.cos(a * math.pi / 8), BORE_Y + 0.12 * math.sin(a * math.pi / 8), Z_MIX)) for a in range(16)]
    poly(bo, "#000000", G3, 1.2)
    line([proj(p) for p in front], 2.5, G7)
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
