#!/usr/bin/env python3
"""iris · frames pass 1 · v5: column-affine, three-quarter, bright at the source.

The rainbow of brief section 4 (one semicircle family about one centre on the
ground, four grey component bands of one-cycle nodes, one bright mix line in
four mutable outlines), seen from a three-quarter camera instead of head on.

Model: the bow stands in a vertical plane, centre O on the ground, radius r per
band; every wave is a radial offset in that plane. Camera: orthographic, yawed
YAW about the vertical and pitched PITCH down, so every circle projects to a
half-ellipse about one centre and the bow's base diameter becomes a slanted
ground line. The near foot is low on the left, the far foot high on the right.

Column affinity (P7): the four mix outlines are cut where the header's columns
are cut (x = 120, 240, 360), so each mutable outline sits under one control:
  col 0 morph   the near foot: where the bright line meets the ground among the
                band feet, so its step inward across the bands reads as a step
                along the ground. This is the sound source; waves are counted
                from here and the mix ribbon is heaviest here (2.5 px, tapering
                to 2 px at the far foot, the depth cue of the near side).
  col 1 overlap the rising shoulder, where the band spacing is widest on screen
  col 2 spread  the crown (the apex falls here); cycles are counted from the
                source, so spread's drift has grown by the time it gets here
  col 3 tone    the far foot
Skew and phase (page 2) act along the whole line.

Usage: gen.py [out.svg] [key=value ...]   e.g. gen.py check.svg morph=1
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))

P = dict(morph=0.3333, overlap=0.25, spread=0.0, tone=0.7, skew=0.0, phase=0.0)

W, H = 480, 220
YAW, PITCH = math.radians(10.0), math.radians(56.0)
CA, SA = math.cos(YAW), math.sin(YAW)
CB, SB = math.cos(PITCH), math.sin(PITCH)

SPACING = 20.0        # band spacing in the model (≈20 px at the feet, ≈10 at the crown)
A_BAND = 5.0          # band wave amplitude, model units
A_MIX = 7.0           # mix amplitude
CYCLES = 13           # cycles round the half-turn at spread 0
KINDS = ["sine", "tri", "square", "saw"]
GREY_HI, GREY_MID, GREY_LO = "#969696", "#646464", "#4B4B4B"
MIX_REST, MIX_HELD = "#AFAFAF", "#CDCDCD"
HORIZON = "#4B4B4B"
COLS = [120.0, 240.0, 360.0]

# fitted below
R0 = 220.0            # outer (sine) band radius
CX, CY = 240.0, 170.0


def project(x, y):
    """model (x along the ground, y up, in the bow's plane) -> screen."""
    u = x * CA
    v = y * CB + x * SA * SB
    return (CX + u, CY - v)


def radii():
    return [R0 - SPACING * i for i in range(4)]


# ---------------------------------------------------------------- waves
def cycle_line(kind):
    """One cycle of a raw band wave as (t, value) pairs, t in [0, 1].

    Every cycle starts and ends at 0 (the square's rising edge is split
    between neighbouring cycles), so a chain of cycle nodes joins up.
    """
    if kind == "sine":
        return [(k / 24, math.sin(2 * math.pi * k / 24)) for k in range(25)]
    if kind == "tri":
        pts = [(k / 24, 0.0) for k in range(25)]
        return [(t, 4 * t if t < .25 else (2 - 4 * t if t < .75 else 4 * t - 4)) for t, _ in pts]
    if kind == "square":
        e = .004
        top = [(e + (.5 - 2 * e) * k / 6, 1.0) for k in range(7)]
        bot = [(.5 + e + (.5 - 2 * e) * k / 6, -1.0) for k in range(7)]
        return [(0.0, 0.0)] + top + bot + [(1.0, 0.0)]
    e = .006                                    # saw: ramp up, drop, ramp up
    up = [(.5 * k / 6, k / 6) for k in range(6)] + [(.5 - e, 1 - 2 * e)]
    up2 = [(.5 + e, -1 + 2 * e)] + [(.5 + .5 * k / 6, -1 + k / 6) for k in range(1, 7)]
    return up + up2


def series(kind, t, skew, tone):
    """Engine-side wave: harmonic series, skewed, low-passed by tone."""
    b = 0.5 - 0.45 * skew
    tt = t % 1.0
    if kind != "saw":
        tt = 0.5 * tt / b if tt < b else 0.5 + 0.5 * (tt - b) / (1 - b)
    x = 2 * math.pi * tt
    fc = 2 ** (0.5 + 7 * tone)
    g = lambda n: 1 / math.sqrt(1 + (n / fc) ** 4)
    if kind == "sine":
        return g(1) * math.sin(x)
    s = 0.0
    for n in range(1, 64):
        if kind == "tri" and n % 2:
            s += g(n) * (-1) ** ((n - 1) // 2) * math.sin(n * x) / n ** 2 * 8 / math.pi ** 2
        elif kind == "square" and n % 2:
            s += g(n) * math.sin(n * x) / n * 4 / math.pi
        elif kind == "saw":
            s += g(n) * (-1) ** (n + 1) * math.sin(n * x) / n * 2 / math.pi
    return s


def weights():
    c = P["morph"] * 3
    w = 1 + 3 * P["overlap"]
    k = [max(0.0, 1 - abs(i - c) / w) for i in range(4)]
    s = sum(k)
    return [x / s for x in k]


def mix_radius():
    c = P["morph"] * 3
    r = radii()
    i = min(int(c), 2)
    return r[i] + (r[i + 1] - r[i]) * (c - i)


def band_radius(i):
    r = radii()[i]
    return r + (mix_radius() - r) * 0.8 * P["overlap"]


def cycles(i):
    return CYCLES / (1 + 0.12 * P["spread"] * (i - 1.5))


def shift(i):
    return P["phase"] * i / 8


# ---------------------------------------------------------------- geometry
def point(r, phi, off):
    """Model point at angle phi (pi = near foot), radius r + offset."""
    rr = r + off
    return project(rr * math.cos(phi), rr * math.sin(phi))


def phi_of(s):
    """s in [0, 1] from the near (left) foot to the far foot."""
    return math.pi * (1 - s)


def ribbon(line, hws):
    n = len(line)
    left, right = [], []
    for k in range(n):
        hw = hws[k]
        if k == 0 or k == n - 1:
            a, b = (line[0], line[1]) if k == 0 else (line[-2], line[-1])
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy); nx, ny = -dy / L, dx / L; m = 1.0
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


def fmt(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def d_of(poly, ox=0.0, oy=0.0):
    return "M " + " L ".join(f"{fmt(x - ox)} {fmt(y - oy)}" for x, y in poly) + " Z"


def dedupe(line, gap=0.3):
    out = [line[0]]
    for q in line[1:]:
        if math.hypot(q[0] - out[-1][0], q[1] - out[-1][1]) >= gap:
            out.append(q)
    return out


# ---------------------------------------------------------------- fit
def fit():
    """Choose R0 and the centre so the bow at its widest settings fills the body."""
    global R0, CX, CY
    R0, CX, CY = 220.0, 0.0, 0.0
    for _ in range(30):
        pts = []
        for k in range(181):
            phi = math.pi * k / 180
            pts.append(point(R0 + A_MIX + 1, phi, 0))
        # the low near foot must also clear the bottom with the inner band
        pts.append(point(R0 - 3 * SPACING - A_MIX, math.pi, 0))
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        sx = (468 - 12) / (max(xs) - min(xs))
        sy = (206 - 48) / (max(ys) - min(ys))
        R0 *= min(sx, sy)
    pts = [point(R0 + A_MIX + 1, math.pi * k / 180, 0) for k in range(181)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    CX = 240 - (max(xs) + min(xs)) / 2
    CY = 48 - min(ys)
    # push down so the near foot sits near the bottom of the body
    foot_y = point(R0, math.pi, 0)[1]
    CY += max(0.0, 0.0)  # (kept explicit: top is the binding edge)
    return foot_y


# ---------------------------------------------------------------- parts
def band_nodes(i, grey, start_id):
    """One-cycle nodes of band i: each authored at its own origin."""
    out = []
    r = band_radius(i)
    n = cycles(i)
    kind = KINDS[i]
    cyc = cycle_line(kind)
    k = 0
    nid = start_id
    while True:
        t0 = k - shift(i)                       # cycle k starts at this t
        s0 = t0 / n
        if s0 >= 1.0:
            break
        if (k + 1 - shift(i)) / n <= 0:
            k += 1
            continue
        line = []
        for t, val in cyc:
            s = (t0 + t) / n
            line.append(point(r, phi_of(s), A_BAND * val))
        line = dedupe(line, 0.2)
        mid = point(r, phi_of((t0 + 0.5) / n), 0)
        ox, oy = round(mid[0], 2), round(mid[1], 2)
        poly = ribbon(line, [0.75] * len(line))
        out.append(f'<g id="iris_node_{nid}" transform="matrix(1 0 0 1 {fmt(ox)} {fmt(oy)})">'
                   f'<path d="{d_of(poly, ox, oy)}" fill="{grey}" stroke="none" stroke-width="0"/></g>')
        nid += 1
        k += 1
    return out, nid


def mix_value(s, w):
    v = 0.0
    for i in range(4):
        if w[i] > 0:
            v += w[i] * series(KINDS[i], s * cycles(i) + shift(i), P["skew"], P["tone"])
    return v


def s_at_x(x, r):
    """Arc position s whose base point (radius r) projects to screen x."""
    lo, hi = 0.0, 1.0
    for _ in range(50):
        m = (lo + hi) / 2
        if point(r, phi_of(m), 0)[0] < x:
            lo = m
        else:
            hi = m
    return (lo + hi) / 2


def mix_outlines(fill):
    w = weights()
    r = mix_radius()
    cuts = [0.0] + [s_at_x(x, r) for x in COLS] + [1.0]
    out = []
    for q in range(4):
        sa, sb = cuts[q], cuts[q + 1]
        ss = [sa + (sb - sa) * k / 31 for k in range(32)]
        line = [point(r, phi_of(s), A_MIX * mix_value(s, w)) for s in ss]
        hws = [1.25 - 0.25 * s for s in ss]          # 2.5 px at the source -> 2 px far
        poly = ribbon(line, hws)
        xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
        ox, oy = round((max(xs) + min(xs)) / 2, 2), round((max(ys) + min(ys)) / 2, 2)
        out.append(f'<path id="iris_node_{q}" transform="matrix(1 0 0 1 {fmt(ox)} {fmt(oy)})" '
                   f'd="{d_of(poly, ox, oy)}" fill="{fill}" stroke="none" stroke-width="0"/>')
    return out


def ground(nid):
    """Black ground mask below the base line, then the base line (hairline)."""
    yl = point(-1e3 / CA, 0, 0)  # unused helper guard
    # base line: the bow's diameter extended across the frame
    def base_y(x):
        # x = CX + m*CA, y = CY - m*SA*SB
        m = (x - CX) / CA
        return CY - m * SA * SB
    x0, x1 = 4.0, 476.0
    mask = [(0, base_y(0) + 0.6), (480, base_y(480) + 0.6), (480, 220), (0, 220)]
    out = [f'<path id="iris_node_{nid}" d="{d_of(mask)}" fill="#000000" stroke="none" stroke-width="0"/>']
    line = [(x0, base_y(x0)), (x1, base_y(x1))]
    out.append(f'<path id="iris_node_{nid + 1}" d="{d_of(ribbon(line, [0.5, 0.5]))}" fill="{HORIZON}" stroke="none" stroke-width="0"/>')
    return out


def header():
    pct = lambda v: f"{round(v * 100)}%"
    titles = [("morph", pct(P["morph"])), ("overlap", pct(P["overlap"])),
              ("spread", pct(P["spread"])), ("tone", pct(P["tone"]))]
    alts = [("skew", pct(P["skew"])), ("phase", pct(P["phase"])), ("", ""), ("", "")]
    g = ['<g id="preview_header">',
         '<rect x="0" y="0" width="480" height="38" fill="#000000" stroke="none"/>']
    steps = ["#000000", "#323232", "#4B4B4B", "#646464", "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD"]
    for i, c in enumerate(steps):
        g.append(f'<rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
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


def main():
    out = os.path.join(HERE, "rest.svg")
    for a in sys.argv[1:]:
        if "=" in a:
            k, v = a.split("=")
            P[k] = float(v)
        else:
            out = a if os.path.isabs(a) else os.path.join(HERE, a)
    fit()
    w = weights()
    m = max(w)
    body = []
    nid = 4
    # dimmest band first, so heavier-weighted bands draw over lighter ones
    for i in sorted(range(4), key=lambda i: w[i]):
        rel = w[i] / m
        grey = GREY_HI if rel > 0.75 else (GREY_MID if rel > 0.15 else GREY_LO)
        nodes, nid = band_nodes(i, grey, nid)
        body += nodes
    body += ground(nid)
    pal = [MIX_REST, MIX_HELD, GREY_HI, GREY_MID, GREY_LO, "#000000"]
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           '<g id="preview_canvas"><rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/></g>',
           header()]
    for k, c in enumerate(pal):
        x = 700 + 10 * k
        svg.append(f'<path id="iris_palette_{k}" d="M {x} 300 L {x + 4} 300 L {x + 4} 304 Z" fill="{c}" stroke="{c}" stroke-width="2"/>')
    svg += body
    svg += mix_outlines(MIX_REST)
    svg.append("</svg>")
    with open(out, "w") as fh:
        fh.write("\n".join(svg) + "\n")
    print(out, "R0", round(R0, 1), "nodes", nid + 2, "weights", [round(x, 2) for x in w])


if __name__ == "__main__":
    main()
