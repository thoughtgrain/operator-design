#!/usr/bin/env python3
"""iris · subject pass 1 · v2: the rainbow itself, single-weight contour.

A primary rainbow modelled in 3D: four cones of light around the anti-solar
point (sun 13 degrees up behind the viewer), projected through one pinhole
camera looking at the horizon. Each cone is one band of the voice, and each
band is drawn as its own waveform riding the cone angle: the wave is an
offset in degrees of arc, so perspective bends and stretches it with the bow.

Order: sine outermost, saw innermost. In a real bow the outer band carries
the longest wavelength (red) and the inner the shortest (violet); iris orders
its bands by harmonic content the same way, plain to bright, so turning morph
right walks inward exactly as the spectrum does.

Controls (rest = defaults):
  morph   which band is lit (the one #CDCDCD line); window weight sets the
          other bands' greys
  overlap pulls the neighbours' cone angles toward the lit band, until at 100%
          all four crowd onto one radius and cross
  spread  gives each band its own cycle count round the bow, so the four waves
          drift out of step along the arc (beating)
  tone    low-pass on the drawn wave itself: fewer harmonics, rounder corners
  skew    moves each wave's breakpoint (pulse narrows, triangle leans)
  phase   slides each band's wave along the arc relative to the one outside it

All lines are closed ribbons (filled, no stroke), one weight: 1.5 px.
"""
import math, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "rest.svg")

P = dict(morph=0.3333, overlap=0.25, spread=0.0, tone=0.7, skew=0.0, phase=0.0)

W, H = 480, 220
CX, HORIZON_Y = 240.0, 198.0
SUN = math.radians(13.0)
LINE = 1.5                      # the one weight

# Cone half-angles, outer (sine) to inner (saw), degrees
BASE = [42.0, 38.0, 34.0, 30.0]
AMP = 1.15                      # wave amplitude, degrees of arc
CYCLES = 11.0                   # cycles across the half-turn of phi at spread 0
GREYS = ["#4B4B4B", "#646464", "#7D7D7D", "#969696", "#CDCDCD"]


def wave(kind, t, skew, nh):
    """Band-limited waveform (Lanczos-smoothed), t in cycles. Range ~[-1, 1]."""
    t = t % 1.0
    # skew: phase distortion with one breakpoint b (0.5 at skew 0)
    b = 0.5 - 0.45 * skew
    if kind != "saw":
        t = 0.5 * t / b if t < b else 0.5 + 0.5 * (t - b) / (1 - b)
    x = 2 * math.pi * t
    if kind == "sine":
        return math.sin(x)
    s = 0.0
    for n in range(1, nh + 1):
        sig = 1.0 if n == 1 else math.sin(math.pi * n / (nh + 1)) / (math.pi * n / (nh + 1))
        if kind == "tri" and n % 2:
            s += sig * ((-1) ** ((n - 1) // 2)) * math.sin(n * x) / n ** 2 * 8 / math.pi ** 2
        elif kind == "square" and n % 2:
            s += sig * math.sin(n * x) / n * 4 / math.pi
        elif kind == "saw":
            s += sig * ((-1) ** (n + 1)) * math.sin(n * x) / n * 2 / math.pi
    return s


KINDS = ["sine", "tri", "square", "saw"]


def window_weights(morph, overlap):
    c = morph * 3.0
    width = 0.5 + 2.5 * overlap          # half-width in bands
    w = [max(0.0, 1 - abs(i - c) / (width + 0.5)) for i in range(4)]
    m = max(w)
    return [x / m for x in w], c


def direction(theta, phi):
    A = (0.0, -math.sin(SUN), math.cos(SUN))
    U = (1.0, 0.0, 0.0)
    V = (0.0, math.cos(SUN), math.sin(SUN))
    ct, st = math.cos(theta), math.sin(theta)
    return tuple(ct * A[k] + st * (math.cos(phi) * U[k] + math.sin(phi) * V[k]) for k in range(3))


def fit_focal():
    # outer band (plus its wave) meets the horizon 14 px from the frame edge
    th = math.radians(BASE[0] + AMP)
    caz = math.cos(th) / math.cos(SUN)
    az = math.acos(caz)
    return (W / 2 - 14) / math.tan(az)


F = fit_focal()


def project(d):
    return (CX + F * d[0] / d[2], HORIZON_Y - F * d[1] / d[2])


def band_points(i, weights, centre):
    # overlap pulls neighbours' cone angles toward the lit band's angle
    lit = BASE[0] + (BASE[3] - BASE[0]) * centre / 3.0
    pull = 0.8 * P["overlap"] * weights[i]
    theta0 = BASE[i] + (lit - BASE[i]) * pull
    cyc = CYCLES * (1 + 0.12 * P["spread"] * (i - 1.5))
    shift = 0.25 * P["phase"] * i
    nh = 2 + int(round(14 * P["tone"]))
    pts = []
    N = 900
    for k in range(N + 1):
        phi = math.pi * k / N                      # right foot -> top -> left foot
        t = cyc * k / N + shift
        th = math.radians(theta0 + AMP * wave(KINDS[i], t, P["skew"], nh))
        d = direction(th, phi)
        x, y = project(d)
        pts.append((x, y, d[1] >= 0))
    # clip at the horizon
    out, run = [], []
    for a, b in zip(pts, pts[1:]):
        if a[2]:
            run.append(a[:2])
        if a[2] != b[2]:
            s = (HORIZON_Y - a[1]) / (b[1] - a[1])
            run.append((a[0] + s * (b[0] - a[0]), HORIZON_Y - 0.0))
            if not b[2] and run:
                out.append(run)
                run = []
    if pts[-1][2]:
        run.append(pts[-1][:2])
    if run:
        out.append(run)
    return out


def simplify(pts, tol=0.18):
    """Douglas-Peucker in screen space."""
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1e-9
    best, idx = -1, 0
    for k in range(1, len(pts) - 1):
        p = pts[k]
        dist = abs(dy * (p[0] - a[0]) - dx * (p[1] - a[1])) / L
        if dist > best:
            best, idx = dist, k
    if best <= tol:
        return [a, b]
    return simplify(pts[: idx + 1], tol)[:-1] + simplify(pts[idx:], tol)


def ribbon(line, hw):
    """Closed ribbon round a polyline, mitred joins (capped), flat ends."""
    n = len(line)
    left, right = [], []
    for k in range(n):
        if k == 0:
            dx, dy = line[1][0] - line[0][0], line[1][1] - line[0][1]
            L = math.hypot(dx, dy); nx, ny = -dy / L, dx / L; m = 1.0
        elif k == n - 1:
            dx, dy = line[-1][0] - line[-2][0], line[-1][1] - line[-2][1]
            L = math.hypot(dx, dy); nx, ny = -dy / L, dx / L; m = 1.0
        else:
            ax, ay = line[k][0] - line[k - 1][0], line[k][1] - line[k - 1][1]
            bx, by = line[k + 1][0] - line[k][0], line[k + 1][1] - line[k][1]
            La, Lb = math.hypot(ax, ay), math.hypot(bx, by)
            n1 = (-ay / La, ax / La); n2 = (-by / Lb, bx / Lb)
            sx, sy = n1[0] + n2[0], n1[1] + n2[1]
            Ls = math.hypot(sx, sy)
            nx, ny = sx / Ls, sy / Ls
            cosh = nx * n1[0] + ny * n1[1]
            m = min(1.0 / max(cosh, 1e-6), 2.0)
        left.append((line[k][0] + nx * hw * m, line[k][1] + ny * hw * m))
        right.append((line[k][0] - nx * hw * m, line[k][1] - ny * hw * m))
    return left + right[::-1]


def chunks(line, maxpts=31):
    """Split a polyline into pieces of <= maxpts points sharing end points."""
    out, k = [], 0
    while k < len(line) - 1:
        piece = line[k:k + maxpts]
        out.append(piece)
        k += maxpts - 1
    return out


def fmt(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def dedupe(poly, gap=0.3):
    out = [poly[0]]
    for q in poly[1:]:
        if math.hypot(q[0] - out[-1][0], q[1] - out[-1][1]) >= gap:
            out.append(q)
    if math.hypot(out[-1][0] - out[0][0], out[-1][1] - out[0][1]) < gap:
        out.pop()
    return out


def path(poly, fill):
    poly = dedupe(poly)
    d = "M " + " L ".join(f"{fmt(x)} {fmt(y)}" for x, y in poly) + " Z"
    return f'<path d="{d}" fill="{fill}" stroke="none"/>'


def header():
    titles = [("morph", "33%"), ("overlap", "25%"), ("spread", "0%"), ("tone", "70%")]
    alts = [("skew", "0%"), ("phase", "0%"), ("", ""), ("", "")]
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
    weights, centre = window_weights(P["morph"], P["overlap"])
    lit = int(round(centre))
    body = []
    # horizon: the ground line the bow stands on
    hz = [(10.0, HORIZON_Y + 0.75), (470.0, HORIZON_Y + 0.75)]
    body.append(path(ribbon(hz, LINE / 2), "#4B4B4B"))
    # bands, dimmest first so the lit one draws last
    order = sorted(range(4), key=lambda i: (i == lit, weights[i]))
    for i in order:
        if i == lit:
            grey = GREYS[4]
        elif weights[i] > 0.05:
            grey = GREYS[2] if weights[i] > 0.5 else GREYS[1]
        else:
            grey = GREYS[0]
        for run in band_points(i, weights, centre):
            line = dedupe(simplify(dedupe(run)))
            for piece in chunks(line):
                if len(piece) >= 2:
                    body.append(path(ribbon(piece, LINE / 2), grey))
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           '<g id="preview_canvas"><rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/></g>',
           header(),
           '<path id="iris_palette_0" d="M 700 300 L 704 300 L 704 304 Z" fill="#CDCDCD" stroke="#CDCDCD" stroke-width="2"/>',
           '<g id="iris_node_0">',
           *body,
           '</g>',
           '</svg>']
    with open(OUT, "w") as fh:
        fh.write("\n".join(svg) + "\n")
    print(OUT, "focal", round(F, 1))


if __name__ == "__main__":
    main()
