#!/usr/bin/env python3
"""iris · frames pass 1 · v2: full-bleed field, front elevation.

Direction: the bow is so large it fills the body edge to edge. The camera
looks straight at the anti-solar point (sun on the horizon behind the viewer),
so every band is a circle about one centre on the horizon, and the circles are
big enough that the outer bands run off the frame's sides and every band runs
off the top of the body. What's left on screen is two great legs of the bow
rising from the horizon and leaving through the top of the field: the
picture is a fragment of something larger than the screen, seen head-on.

The brightest element is the MIX, where a note lands: the window-weighted sum
of the four bands, low-passed by tone, riding at the radius morph sets.
It is drawn with the four mutable outlines, iris_node_0..3, two per leg
(a quarter of the visible arc each), each M + 63 L + Z round 32 centreline
points.

Grey bands: chains of one-cycle nodes, iris_node_4 upward, each a static
closed ribbon authored round its own origin with the rotation baked in,
placed by matrix(1 0 0 1 x y). Cycles that would reach into the two-page
header band (y < 40) or lie wholly off-screen are hidden (left out of the
frame; on the device display() parks them at 640, 320).

Usage: gen.py [key=value ...] [out=path.svg]   (keys: morph overlap spread
tone skew phase held)
"""
import math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

P = dict(morph=0.3333, overlap=0.25, spread=0.0, tone=0.7, skew=0.0, phase=0.0, held=0.0)
OUT = os.path.join(HERE, "rest.svg")
for a in sys.argv[1:]:
    k, v = a.split("=", 1)
    if k == "out":
        OUT = v if os.path.isabs(v) else os.path.join(HERE, v)
    else:
        P[k] = float(v)

W, H = 480, 220
CX, HY = 240.0, 211.0            # bow centre: on the horizon, mid-frame
TOP = 40.0                       # nothing above this (two-page header band)
R = [246.0, 214.0, 182.0, 150.0] # sine (outer) .. saw (inner); spacing 32 px
AMP = 8.0                        # wave amplitude, px, radial
CYCLES = 13                      # cycles round the half-turn at spread 0
KINDS = ["sine", "tri", "square", "saw"]

HAIR, LINE, SUBJ = 1.2, 1.5, 2.2
MIX_REST, MIX_HELD = "#AFAFAF", "#CDCDCD"
G_HI, G_MID, G_LO, BLACK = "#969696", "#7D7D7D", "#4B4B4B", "#000000"


# ---------------------------------------------------------------- engine maths
def raw(kind, t, skew=0.0):
    """Raw waveform, t in cycles (array), phase-distorted by skew, DC removed."""
    t = np.mod(t, 1.0)
    b = 0.5 - 0.45 * skew
    if kind == "saw":
        # ramp up, drop at t = 0.5 (Fourier: sum (-1)^(n+1) sin(nx)/n * 2/pi)
        return np.where(t < 0.5, 2 * t, 2 * t - 2)
    tp = np.where(t < b, 0.5 * t / b, 0.5 + 0.5 * (t - b) / (1 - b))
    if kind == "sine":
        y = np.sin(2 * np.pi * tp)
    elif kind == "tri":
        y = np.where(tp < 0.25, 4 * tp, np.where(tp < 0.75, 2 - 4 * tp, 4 * tp - 4))
    else:
        y = np.where(tp < 0.5, 1.0, -1.0)
    return y


def filtered_table(kind, skew, tone, n=2048):
    """One cycle of the band, low-passed as the engine's tone does."""
    t = np.arange(n) / n
    y = raw(kind, t, skew)
    y = y - y.mean()
    Y = np.fft.rfft(y)
    h = np.arange(len(Y))
    fc = 2 ** (0.5 + 7 * tone)
    Y *= 1 / np.sqrt(1 + (h / fc) ** 4)
    return np.fft.irfft(Y, n)


def lookup(table, t):
    n = len(table)
    x = np.mod(t, 1.0) * n
    i = np.floor(x).astype(int)
    f = x - i
    return table[i % n] * (1 - f) + table[(i + 1) % n] * f


def weights(morph, overlap):
    c = morph * 3
    width = 1 + 3 * overlap
    w = np.array([max(0.0, 1 - abs(i - c) / width) for i in range(4)])
    return w / w.sum(), c


# ---------------------------------------------------------------- geometry
def fmt(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def ribbon(line, hw):
    """Closed ribbon round a polyline, mitred joins (capped), flat ends."""
    n = len(line)
    left, right = [], []
    for k in range(n):
        if k in (0, n - 1):
            a, b = (line[0], line[1]) if k == 0 else (line[-2], line[-1])
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy)
            nx, ny, m = -dy / L, dx / L, 1.0
        else:
            ax, ay = line[k][0] - line[k - 1][0], line[k][1] - line[k - 1][1]
            bx, by = line[k + 1][0] - line[k][0], line[k + 1][1] - line[k][1]
            La, Lb = math.hypot(ax, ay), math.hypot(bx, by)
            n1 = (-ay / La, ax / La); n2 = (-by / Lb, bx / Lb)
            sx, sy = n1[0] + n2[0], n1[1] + n2[1]
            Ls = math.hypot(sx, sy) or 1e-9
            nx, ny = sx / Ls, sy / Ls
            m = min(1.0 / max(nx * n1[0] + ny * n1[1], 1e-6), 2.0)
        left.append((line[k][0] + nx * hw * m, line[k][1] + ny * hw * m))
        right.append((line[k][0] - nx * hw * m, line[k][1] - ny * hw * m))
    return left + right[::-1]


def polar(r, phi):
    return (CX + r * math.cos(phi), HY - r * math.sin(phi))


def d_of(poly, ox, oy):
    return "M " + " L ".join(f"{fmt(x - ox)} {fmt(y - oy)}" for x, y in poly) + " Z"


# ---------------------------------------------------------------- bands
# Where each band's cycle nodes start: on a smooth stretch, so neighbouring
# nodes meet without a corner at the seam.
SEAM = {"sine": 0.0, "tri": 0.0, "square": 0.25, "saw": 0.0}
CORNERS = {"sine": [], "tri": [0.25, 0.75], "square": [0.5, 1.0], "saw": [0.5]}


def cycle_ts(kind):
    s = SEAM[kind]
    ts = [s + k / 24 for k in range(25)]
    eps = 0.03
    for c in CORNERS[kind]:
        for cc in (c, c + 1):
            if s < cc < s + 1:
                if kind == "tri":
                    ts.append(cc)
                else:                    # a jump: two points a hair apart
                    ts = [t for t in ts if abs(t - cc) > 1.5 * eps]
                    ts += [cc - eps, cc + eps]
    ts = sorted(set(round(t, 5) for t in ts))
    out = []
    for t in ts:
        if not out or t - out[-1] > 0.006:
            out.append(t)
    return out


def band_nodes(i, w, c):
    kind = KINDS[i]
    r_mix = np.interp(c, [0, 1, 2, 3], R)
    pull = 0.8 * P["overlap"] * (w[i] / w.max())
    r0 = R[i] + (r_mix - R[i]) * pull
    scale = 1 + 0.12 * P["spread"] * (i - 1.5)
    dphi = math.pi / CYCLES * scale
    shift = P["phase"] * i / 8               # cycles
    ts = cycle_ts(kind)
    nodes = []
    k = -2                                   # first pass makes k = -1: the cycle crossing the foot
    while True:
        k += 1
        t0 = k + SEAM[kind] - shift
        phi_a = t0 * dphi
        if phi_a > math.pi:
            break
        pts = []
        for t in ts:
            tt = k + t - shift
            phi = tt * dphi
            v = float(raw(kind, np.array([t]))[0])
            pts.append(polar(r0 + AMP * v, phi))
        ys = [p[1] for p in pts]
        xs = [p[0] for p in pts]
        if min(ys) < TOP or max(xs) < 0 or min(xs) > W:
            continue                        # hidden: header band or off-screen
        if sum(1 for y in ys if y < HY - 0.5) < 2:
            continue                        # below the horizon
        mid = polar(r0, (k + 0.5 + SEAM[kind] - shift) * dphi)
        ox, oy = round(mid[0], 2), round(mid[1], 2)
        nodes.append((ox, oy, ribbon(pts, LINE / 2)))
    return nodes


# ---------------------------------------------------------------- mix
def mix_outlines(w, c):
    r = float(np.interp(c, [0, 1, 2, 3], R))
    tables = [filtered_table(k, P["skew"], P["tone"]) for k in KINDS]
    reach = AMP + SUBJ
    # visible arc of the right leg: from the frame's side (or the horizon)
    # up to where the line would enter the header band
    phi_top = math.asin(min(1.0, (HY - TOP - reach) / r))
    phi_side = math.acos(min(1.0, (W - CX + 2) / r)) if r > W - CX + 2 else 0.0
    legs = [(phi_side, phi_top), (math.pi - phi_top, math.pi - phi_side)]
    held_phase = P["held"]
    outs = []
    for a, b in legs:
        m = (a + b) / 2
        for lo, hi in ((a, m), (m, b)):
            phis = np.linspace(lo, hi, 32)
            v = np.zeros_like(phis)
            for i in range(4):
                if w[i] == 0:
                    continue
                scale = 1 + 0.12 * P["spread"] * (i - 1.5)
                t = phis / (math.pi / CYCLES * scale) + P["phase"] * i / 8 + held_phase
                v += w[i] * lookup(tables[i], t)
            pts = [polar(r + AMP * vv, ph) for vv, ph in zip(v, phis)]
            mid = polar(r, (lo + hi) / 2)
            outs.append((round(mid[0], 2), round(mid[1], 2), ribbon(pts, SUBJ / 2)))
    return outs


# ---------------------------------------------------------------- header
def header():
    def pct(x):
        return f"{int(round(x * 100))}%"
    titles = [("morph", pct(P["morph"])), ("overlap", pct(P["overlap"])),
              ("spread", pct(P["spread"])), ("tone", pct(P["tone"]))]
    alts = [("skew", pct(P["skew"])), ("phase", pct(P["phase"])), ("", ""), ("", "")]
    g = ['<g id="preview_header">',
         '<rect x="0" y="0" width="480" height="38" fill="#000000" stroke="none"/>']
    steps = ["#000000", "#323232", "#4B4B4B", "#646464", "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD"]
    for i, col in enumerate(steps):
        g.append(f'<rect x="{60 * i}" y="0" width="60" height="20" fill="{col}" stroke="none"/>')
    for i, ((t, v), (at, av)) in enumerate(zip(titles, alts)):
        ink = "#CBCBCB" if i < 2 else "#000000"
        x = 120 * i
        g.append(f'<text transform="matrix(1 0 0 1 {x + 5} 10)" fill="{ink}" stroke="none" font-family="UniversNextPro-Light" font-size="10px">{t}</text>')
        g.append(f'<text transform="matrix(1 0 0 1 {x + 65} 17.44)" fill="{ink}" stroke="none" font-family="UniversNextPro-Light" font-size="20px">{v}</text>')
        if at:
            g.append(f'<text transform="matrix(1 0 0 1 {x + 5} 33)" fill="#5A5A5A" stroke="none" font-family="UniversNextPro-Light" font-size="10px">{at}</text>')
            g.append(f'<text transform="matrix(1 0 0 1 {x + 65} 33)" fill="#707070" stroke="none" font-family="UniversNextPro-Light" font-size="13px">{av}</text>')
    g.append("</g>")
    return "\n".join(g)


def band_grey(wn):
    if wn >= 0.75:
        return G_HI
    if wn >= 0.2:
        return G_MID
    return G_LO


def main():
    w, c = weights(P["morph"], P["overlap"])
    wn = w / w.max()
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           '<g id="preview_canvas"><rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/></g>',
           header()]
    pal = [MIX_REST, MIX_HELD, G_HI, G_MID, G_LO, BLACK]
    for j, col in enumerate(pal):
        svg.append(f'<path id="iris_palette_{j}" d="M {700 + 10 * j} 300 L {704 + 10 * j} 300 L {704 + 10 * j} 304 Z" fill="{col}" stroke="none"/>')

    nid = 4
    body = []
    # bands, dimmest first
    for i in sorted(range(4), key=lambda i: wn[i]):
        grey = band_grey(wn[i])
        for ox, oy, rib in band_nodes(i, w, c):
            body.append(f'<path id="iris_node_{nid}" transform="matrix(1 0 0 1 {fmt(ox)} {fmt(oy)})" '
                        f'd="{d_of(rib, ox, oy)}" fill="{grey}" stroke="none"/>')
            nid += 1
    assert nid <= 68, nid
    # ground mask (hides cycles that slide below the horizon), then the horizon
    gm = [(0, HY + 1), (W, HY + 1), (W, H), (0, H)]
    body.append(f'<path id="iris_node_69" transform="matrix(1 0 0 1 240 212)" d="{d_of(gm, 240, 212)}" fill="{BLACK}" stroke="none"/>')
    hz = ribbon([(0.0, HY + 0.4), (480.0, HY + 0.4)], HAIR / 2)
    body.append(f'<path id="iris_node_68" transform="matrix(1 0 0 1 240 {fmt(HY)})" d="{d_of(hz, 240, HY)}" fill="{G_LO}" stroke="none"/>')
    # the mix, last: the one bright line
    col = MIX_HELD if P["held"] else MIX_REST
    mix = []
    for j, (ox, oy, rib) in enumerate(mix_outlines(w, c)):
        assert len(rib) == 64
        mix.append(f'<path id="iris_node_{j}" transform="matrix(1 0 0 1 {fmt(ox)} {fmt(oy)})" '
                   f'd="{d_of(rib, ox, oy)}" fill="{col}" stroke="none"/>')
    svg += body + mix + ["</svg>"]
    with open(OUT, "w") as fh:
        fh.write("\n".join(svg) + "\n")
    print(OUT, "band nodes", nid - 4)


if __name__ == "__main__":
    main()
