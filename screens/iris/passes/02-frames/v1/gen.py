#!/usr/bin/env python3
"""iris · frames pass 1 · v1: off-axis diagonal, low angle, negative space.

The same model as the chosen subject: the sun sits on the horizon behind the
viewer, so every band is a cone of light round the anti-solar point and draws
as a circle about one centre on the horizon. Here the camera is low (the
horizon is the frame's bottom edge, so the bow is as tall as the header lets
it be) and the picture is a shifted crop (a shift lens: rise and a slide to the
left), so the bow's centre sits near the left edge. Only the bow's right
shoulder is in frame: it comes in at the left edge, crowns over the first
column and falls on a long diagonal to its foot near the middle of the screen.
The right half is black sky over the horizon; the bow is read as much from
the space it cuts out (the black disc under it, the open sky beside it) as
from its lines.

Radii come from the cone angles through the camera (r = f tan theta), so the
band spacing narrows inward as it would in a photograph.

Structure (brief section 4):
  iris_node_0..3   the mix, four mutable outlines, 32 centreline points each
                   (64-point closed ribbons), the visible stretch of the bow
                   split in four equal angular quarters
  iris_node_4..67  band cycle nodes, 16 per band (sine, tri, square, saw),
                   one wave cycle each, rotation baked into the points,
                   placed by translation; cycles outside the frame park
  iris_node_68     ground mask (black, hides cycles slid below the horizon)
  iris_node_69     horizon (hairline ribbon)

usage: gen.py [out.svg] [param=value ...]   e.g. gen.py check.svg morph=1
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

P = dict(morph=0.3333, overlap=0.25, spread=0.0, tone=0.7, skew=0.0, phase=0.0)

W, H = 480, 220
HORIZON = 213.0                 # low camera: the ground is the bottom edge
CX = 78.0                       # bow centre, shifted hard left
THETA = [42.0, 38.0, 34.0, 30.0]  # cone half-angles, sine (outer) .. saw (inner)
R_OUTER = 160.0
F = R_OUTER / math.tan(math.radians(THETA[0]))
AMP_BAND = 0.95                 # band wave amplitude, degrees
AMP_MIX = 1.15                  # mix wave amplitude, degrees
CYCLES = 13                     # cycles per half-turn at spread 0
NODES_PER_BAND = 16
PHI_MIX = math.radians(128.0)   # the mix runs from the foot to past the left edge
KINDS = ["sine", "tri", "square", "saw"]

W_BAND = 1.5                    # line
W_MIX = 2.2                     # subject
W_HAIR = 1.2                    # hairline

MIX_REST = "#AFAFAF"
MIX_HELD = "#CDCDCD"
BAND_GREYS = ["#4B4B4B", "#646464", "#7D7D7D", "#969696"]
HORIZON_GREY = "#4B4B4B"
PARK = (640, 320)


# ---------------------------------------------------------------- the engine

def warp(t, b):
    """Phase distortion with one breakpoint b (0.5 = none)."""
    return np.where(t < b, 0.5 * t / b, 0.5 + 0.5 * (t - b) / (1 - b))


def raw(kind, t, skew):
    """Naive waveform, t in cycles (array), range [-1, 1]."""
    t = np.mod(t, 1.0)
    b = 0.5 - 0.45 * skew
    if kind == "sine":
        return np.sin(2 * np.pi * warp(t, b))
    if kind == "tri":       # -1 at 0, +1 at b, -1 at 1
        return np.where(t < b, -1 + 2 * t / b, 1 - 2 * (t - b) / (1 - b))
    if kind == "square":
        return np.where(t < b, 1.0, -1.0)
    return 2 * t - 1        # saw


def filtered_tables(skew, tone, n=4096):
    """Each band's wave low-passed by tone: harmonic n gain 1/sqrt(1+(n/fc)^4)."""
    fc = 2 ** (0.5 + 7 * tone)
    t = (np.arange(n) + 0.5) / n
    out = []
    for kind in KINDS:
        spec = np.fft.rfft(raw(kind, t, skew))
        h = np.arange(len(spec))
        spec *= 1 / np.sqrt(1 + (h / fc) ** 4)
        out.append(np.fft.irfft(spec, n))
    return out


def lookup(table, t):
    n = len(table)
    x = np.mod(np.asarray(t) * n - 0.5, n)
    i0 = np.floor(x).astype(int)
    fr = x - i0
    return table[i0] * (1 - fr) + table[(i0 + 1) % n] * fr


def kernel(morph, overlap):
    """Triangle window of width 1 + 3 overlap bands about morph*3."""
    c = morph * 3
    width = 1 + 3 * overlap
    return [max(0.0, 1 - abs(i - c) / width) for i in range(4)], c


# ---------------------------------------------------------------- the model

def theta_at(index):
    """Cone angle at a fractional band index (morph sets the mix's)."""
    i = min(int(index), 2)
    f = index - i
    return THETA[i] + (THETA[i + 1] - THETA[i]) * f


def radius(theta_deg):
    return F * math.tan(math.radians(theta_deg))


def to_screen(r, phi):
    return (CX + r * math.cos(phi), HORIZON - r * math.sin(phi))


def band_geometry(i, k, c):
    """Cone angle, cycle length (rad) and phase offset (rad) of band i."""
    th_mix = theta_at(c)
    pull = 0.8 * P["overlap"] * k[i]
    th = THETA[i] + (th_mix - THETA[i]) * pull
    dphi = math.pi / CYCLES * (1 + 0.12 * P["spread"] * (i - 1.5))
    off = P["phase"] * i / 8 * dphi
    return th, dphi, off


# ---------------------------------------------------------------- drawing

def ribbon(line, w):
    hw = w / 2
    n = len(line)
    left, right = [], []
    for j in range(n):
        if j == 0 or j == n - 1:
            a, b = (line[0], line[1]) if j == 0 else (line[-2], line[-1])
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy)
            nx, ny, m = -dy / L, dx / L, 1.0
        else:
            ax, ay = line[j][0] - line[j - 1][0], line[j][1] - line[j - 1][1]
            bx, by = line[j + 1][0] - line[j][0], line[j + 1][1] - line[j][1]
            La, Lb = math.hypot(ax, ay), math.hypot(bx, by)
            n1, n2 = (-ay / La, ax / La), (-by / Lb, bx / Lb)
            sx, sy = n1[0] + n2[0], n1[1] + n2[1]
            Ls = math.hypot(sx, sy)
            nx, ny = sx / Ls, sy / Ls
            m = min(1 / max(nx * n1[0] + ny * n1[1], 1e-6), 2.0)
        left.append((line[j][0] + nx * hw * m, line[j][1] + ny * hw * m))
        right.append((line[j][0] - nx * hw * m, line[j][1] - ny * hw * m))
    return left + right[::-1]


def fmt(v):
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def d_attr(poly):
    return "M " + " L ".join(f"{fmt(x)} {fmt(y)}" for x, y in poly) + " Z"


def node(idx, origin, poly, fill):
    ox, oy = origin
    rel = [(x - ox, y - oy) for x, y in poly]
    return (f'<path id="iris_node_{idx}" transform="matrix(1 0 0 1 {fmt(ox)} {fmt(oy)})" '
            f'd="{d_attr(rel)}" fill="{fill}" stroke="none"/>')


def cycle_ts(kind, skew):
    b = 0.5 - 0.45 * skew
    e = 0.035
    keys = {"sine": [], "tri": [b], "square": [e, b, b + e], "saw": [1 - e]}[kind]
    grid = list(np.linspace(0, 1, 21))
    ts = sorted(set([round(x, 4) for x in grid + keys]))
    out = [ts[0]]
    for x in ts[1:]:
        if x - out[-1] > 0.012:
            out.append(x)
        elif x in keys:
            out[-1] = x
    if out[-1] != 1.0:
        out[-1] = 1.0
    return out


def cycle_shape(kind, t, skew):
    """Raw band wave for drawing, with steep finite edges (no vertical reversals)."""
    b = 0.5 - 0.45 * skew
    e = 0.035
    if kind == "square":
        if t <= e:
            return -1 + 2 * t / e
        if t <= b:
            return 1.0
        if t <= b + e:
            return 1 - 2 * (t - b) / e
        return -1.0
    if kind == "saw":
        return -1 + 2 * t / (1 - e) if t <= 1 - e else 1 - 2 * (t - (1 - e)) / e
    return float(raw(kind, np.array([t]), skew)[0])


def band_nodes(i, k, c, grey):
    th, dphi, off = band_geometry(i, k, c)
    kind = KINDS[i]
    ts = cycle_ts(kind, P["skew"])
    out = []
    start = -1 if off > 1e-9 else 0
    for slot in range(NODES_PER_BAND):
        cyc = start + slot
        phi0 = off + cyc * dphi
        line = []
        for t in ts:
            phi = phi0 + t * dphi
            r = radius(th + AMP_BAND * cycle_shape(kind, t, P["skew"]))
            line.append(to_screen(r, phi))
        mid = to_screen(radius(th), phi0 + 0.5 * dphi)
        origin = (round(mid[0], 2), round(mid[1], 2))
        visible = (phi0 < math.pi and origin[0] > -40 and origin[1] < HORIZON + 30)
        poly = ribbon(line, W_BAND)
        if visible:
            out.append(node(4 + 16 * i + slot, origin, poly, grey))
        else:
            rel = [(x - origin[0] + PARK[0], y - origin[1] + PARK[1]) for x, y in poly]
            out.append(node(4 + 16 * i + slot, PARK, rel, grey))
    return out


def mix_nodes(k, c, tables, fill):
    s = sum(k)
    wts = [x / s for x in k]
    th_mix = theta_at(c)
    geo = [band_geometry(i, k, c) for i in range(4)]
    out = []
    for q in range(4):
        phis = np.linspace(PHI_MIX * q / 4, PHI_MIX * (q + 1) / 4, 32)
        line = []
        for phi in phis:
            v = 0.0
            for i in range(4):
                if wts[i] == 0:
                    continue
                _, dphi, off = geo[i]
                v += wts[i] * float(lookup(tables[i], (phi - off) / dphi))
            line.append(to_screen(radius(th_mix + AMP_MIX * v), phi))
        poly = ribbon(line, W_MIX)
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        origin = (round((min(xs) + max(xs)) / 2, 1), round((min(ys) + max(ys)) / 2, 1))
        out.append(node(q, origin, poly, fill))
    return out


def header():
    vals = [("morph", P["morph"]), ("overlap", P["overlap"]), ("spread", P["spread"]), ("tone", P["tone"])]
    alts = [("skew", P["skew"]), ("phase", P["phase"]), ("", None), ("", None)]
    g = ['<g id="preview_header">',
         '<rect x="0" y="0" width="480" height="38" fill="#000000" stroke="none"/>']
    steps = ["#000000", "#323232", "#4B4B4B", "#646464", "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD"]
    for i, col in enumerate(steps):
        g.append(f'<rect x="{60 * i}" y="0" width="60" height="20" fill="{col}" stroke="none"/>')
    for i, ((t, v), (at, av)) in enumerate(zip(vals, alts)):
        ink = "#CBCBCB" if i < 2 else "#000000"
        x = 120 * i
        g.append(f'<text transform="matrix(1 0 0 1 {x + 5} 10)" fill="{ink}" stroke="none" '
                 f'font-family="UniversNextPro-Light" font-size="10px">{t}</text>')
        g.append(f'<text transform="matrix(1 0 0 1 {x + 65} 17.44)" fill="{ink}" stroke="none" '
                 f'font-family="UniversNextPro-Light" font-size="20px">{round(v * 100)}%</text>')
        if at:
            g.append(f'<text transform="matrix(1 0 0 1 {x + 5} 33)" fill="#5A5A5A" stroke="none" '
                     f'font-family="UniversNextPro-Light" font-size="10px">{at}</text>')
            g.append(f'<text transform="matrix(1 0 0 1 {x + 65} 33)" fill="#707070" stroke="none" '
                     f'font-family="UniversNextPro-Light" font-size="13px">{round(av * 100)}%</text>')
    g.append("</g>")
    return "\n".join(g)


def band_grey(w):
    if w <= 0:
        return BAND_GREYS[0]
    if w < 0.34:
        return BAND_GREYS[1]
    if w < 0.67:
        return BAND_GREYS[2]
    return BAND_GREYS[3]


def build(held=False):
    k, c = kernel(P["morph"], P["overlap"])
    kmax = max(k)
    tables = filtered_tables(P["skew"], P["tone"])
    body = []
    # dimmest band first, so the brighter ones sit on top where they cross
    for i in sorted(range(4), key=lambda j: k[j]):
        body += band_nodes(i, k, c, band_grey(k[i] / kmax))
    ground = [(-2, HORIZON + 0.6), (482, HORIZON + 0.6), (482, 222), (-2, 222)]
    body.append(node(68, (240, 217), ground, "#000000"))
    hz = ribbon([(0.5, HORIZON), (240, HORIZON), (479.5, HORIZON)], W_HAIR)
    body.append(node(69, (240, HORIZON), hz, HORIZON_GREY))
    body += mix_nodes(k, c, tables, MIX_HELD if held else MIX_REST)
    palette = [MIX_REST, MIX_HELD, "#969696", "#7D7D7D", "#646464", "#4B4B4B"]
    pal = [f'<path id="iris_palette_{j}" d="M {700 + 10 * j} 300 L {704 + 10 * j} 300 L {704 + 10 * j} 304 Z" '
           f'fill="{col}" stroke="{col}" stroke-width="2"/>' for j, col in enumerate(palette)]
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           '<g id="preview_canvas"><rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/></g>',
           header(), *pal, *body, '</svg>']
    return "\n".join(svg) + "\n"


def main(argv):
    out = os.path.join(HERE, "rest.svg")
    held = False
    for a in argv:
        if "=" in a:
            key, v = a.split("=")
            if key == "held":
                held = v == "1"
            else:
                P[key] = float(v)
        else:
            out = a if os.path.isabs(a) else os.path.join(HERE, a)
    with open(out, "w") as fh:
        fh.write(build(held))
    print(out)


if __name__ == "__main__":
    main(sys.argv[1:])
