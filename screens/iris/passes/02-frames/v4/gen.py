#!/usr/bin/env python3
"""iris · frames pass 2 · v4: low horizon, section cut, Morph's line brightest.

Direction: the horizon sits on the very bottom of the body (y 212) and the bow
is drawn at the largest size the body allows (outer band crown at y ~41), with
its centre pushed right so the frame's right edge cuts through the right
shoulder. What's inside the frame is the left foot, the left shoulder and the
crown; the cut edges are the frame itself. The left of the sky stays black.

Structure (brief section 4):
  * one bow centre on the horizon; four grey component bands, sine outermost,
    saw innermost; each band a chain of one-cycle nodes (iris_node_4 up),
    each cycle a closed ribbon authored at its own origin with its turn baked
    into the coordinates, placed by matrix(1 0 0 1 x y)
  * the one bright line is the MIX: window-weighted sum of the four waves,
    low-passed by tone, riding at the radius morph sets. Four mutable outlines
    iris_node_0..3, each a quarter of the VISIBLE arc (the section cut means
    the 4 x 32 centreline points are spent only on what's on screen)
  * black ground mask below the horizon, then the horizon hairline

Usage: gen.py [out.svg] [param=value ...]   e.g. gen.py check.svg morph=1
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))

P = dict(morph=0.3333, overlap=0.25, spread=0.0, tone=0.7, skew=0.0, phase=0.0)
OUT = os.path.join(HERE, "rest.svg")
for a in sys.argv[1:]:
    if "=" in a:
        k, v = a.split("=")
        P[k] = float(v)
    else:
        OUT = os.path.abspath(a)

W, H = 480, 220
HORIZON = 212.0          # low horizon: the bottom of the body
CX = 404.0               # bow centre, pushed right: the frame cuts the right shoulder
R_OUT = 166.0            # sine band radius (crown + wave + spread scale stays below y 38)
SPACING = 14.0           # band spacing: morph travels 3 x 14 = 42 px
AMP = 4.0                # wave amplitude, px
CYCLES = 14.0            # cycles round the half-turn
BAND_W = 1.5             # Line weight
MIX_W = 2.0              # Subject weight
CUT_X = 486.0            # mix line runs just past the frame edge so the cut is clean

KINDS = ["sine", "tri", "square", "saw"]
BAND_GREY = ["#4B4B4B", "#646464", "#7D7D7D", "#969696"]
MIX_REST, MIX_HELD = "#AFAFAF", "#CDCDCD"


def radius(i):
    return R_OUT - SPACING * i


# ---------------------------------------------------------------- waves
def raw(kind, t, skew):
    """Naive waveform, t in cycles, range [-1, 1]. skew moves the breakpoint."""
    t = t % 1.0
    if kind != "saw":
        b = 0.5 - 0.45 * skew
        t = 0.5 * t / b if t < b else 0.5 + 0.5 * (t - b) / (1 - b)
    if kind == "sine":
        return math.sin(2 * math.pi * t)
    if kind == "tri":
        return 4 * t if t < 0.25 else (2 - 4 * t if t < 0.75 else 4 * t - 4)
    if kind == "square":
        return 1.0 if t < 0.5 else -1.0
    # saw: ramp up through 0 at t=0, drop at t=0.5
    return 2 * t if t < 0.5 else 2 * t - 2


def spectrum(kind, skew, n=512, hmax=48):
    xs = [raw(kind, k / n, skew) for k in range(n)]
    out = []
    for h in range(1, hmax + 1):
        re = sum(x * math.cos(2 * math.pi * h * k / n) for k, x in enumerate(xs)) * 2 / n
        im = sum(x * math.sin(2 * math.pi * h * k / n) for k, x in enumerate(xs)) * 2 / n
        out.append((re, im))
    return out


def tone_gain(h, tone):
    fc = 2 ** (0.5 + 7 * tone)
    return 1 / math.sqrt(1 + (h / fc) ** 4)


def weights(morph, overlap):
    c = morph * 3
    width = 1 + 3 * overlap
    w = [max(0.0, 1 - abs(i - c) / width) for i in range(4)]
    s = sum(w)
    return [x / s for x in w], c


# ---------------------------------------------------------------- geometry
def ribbon(line, hw):
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
            n1, n2 = (-ay / La, ax / La), (-by / Lb, bx / Lb)
            sx, sy = n1[0] + n2[0], n1[1] + n2[1]
            Ls = math.hypot(sx, sy) or 1e-9
            nx, ny = sx / Ls, sy / Ls
            m = min(1 / max(nx * n1[0] + ny * n1[1], 1e-6), 2.0)
        left.append((line[k][0] + nx * hw * m, line[k][1] + ny * hw * m))
        right.append((line[k][0] - nx * hw * m, line[k][1] - ny * hw * m))
    return left + right[::-1]


def dedupe(pts, gap=0.3):
    out = [pts[0]]
    for q in pts[1:]:
        if math.hypot(q[0] - out[-1][0], q[1] - out[-1][1]) >= gap:
            out.append(q)
    return out


def simplify(pts, tol=0.15):
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1e-9
    best, idx = -1, 0
    for k in range(1, len(pts) - 1):
        d = abs(dy * (pts[k][0] - a[0]) - dx * (pts[k][1] - a[1])) / L
        if d > best:
            best, idx = d, k
    if best <= tol:
        return [a, b]
    return simplify(pts[: idx + 1], tol)[:-1] + simplify(pts[idx:], tol)


def fmt(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "", "-") else s


def d_attr(poly):
    return "M " + " L ".join(f"{fmt(x)} {fmt(y)}" for x, y in poly) + " Z"


def polar(r, phi):
    return (CX + r * math.cos(phi), HORIZON - r * math.sin(phi))


# ---------------------------------------------------------------- parts
def band_nodes(w, c, first_id):
    """Grey component bands as one-cycle nodes. Returns (svg, next id)."""
    wmax = max(w)
    r_mix = R_OUT - SPACING * c
    out, nid = [], first_id
    for i in range(4):
        pull = 0.8 * P["overlap"] * (w[i] / wmax)
        r0 = radius(i) + (r_mix - radius(i)) * pull
        scale = 1 + 0.12 * P["spread"] * (i - 1.5)
        dphi = math.pi / CYCLES * scale            # one cycle, in angle
        shift = (i / 8) * P["phase"]               # cycles
        ratio = w[i] / wmax
        grey = BAND_GREY[0] if ratio <= 0.02 else BAND_GREY[1] if ratio < 0.4 \
            else BAND_GREY[2] if ratio < 0.75 else BAND_GREY[3]
        # cycles start where the wave is smooth (square on its plateau)
        t0 = 0.25 if KINDS[i] == "square" else 0.0
        k = -1
        while True:
            k += 1
            # left foot at phi = pi; cycles run clockwise (toward the right)
            a0 = math.pi - (k - shift) * dphi
            a1 = a0 - dphi
            if k > 30:
                break
            if a0 > math.pi + dphi:      # wholly under the ground
                continue
            mid = (a0 + a1) / 2
            ox, oy = polar(r0, mid)
            if ox - r0 * dphi > W + 4:   # wholly past the cut
                break
            line = []
            N = 48
            for s in range(N + 1):
                u = s / N
                phi = a0 + (a1 - a0) * u
                r = r0 + AMP * scale * raw(KINDS[i], t0 + u, 0.0)
                x, y = polar(r, phi)
                line.append((x - ox, y - oy))
            line = dedupe(simplify(dedupe(line)))
            rib = dedupe(ribbon(line, BAND_W / 2))
            if math.hypot(rib[-1][0] - rib[0][0], rib[-1][1] - rib[0][1]) < 0.3:
                rib.pop()
            assert len(rib) <= 64, len(rib)
            out.append(f'<g id="iris_node_{nid}" transform="matrix(1 0 0 1 {fmt(ox)} {fmt(oy)})">'
                       f'<path d="{d_attr(rib)}" fill="{grey}" stroke="none"/></g>')
            nid += 1
    return out, nid


def mix_nodes(w, c):
    """The bright mix line: four mutable outlines, 64 points each."""
    r_mix = R_OUT - SPACING * c
    specs = [spectrum(KINDS[i], P["skew"]) for i in range(4)]
    gains = [tone_gain(h + 1, P["tone"]) for h in range(48)]
    t0s = [0.0, 0.0, 0.25, 0.0]

    def value(phi):
        v = 0.0
        for i in range(4):
            if w[i] == 0:
                continue
            scale = 1 + 0.12 * P["spread"] * (i - 1.5)
            cyc = (math.pi - phi) / (math.pi / CYCLES * scale) + t0s[i] - (i / 8) * P["phase"]
            s = 0.0
            for h, (re, im) in enumerate(specs[i]):
                g = gains[h]
                s += g * (re * math.cos(2 * math.pi * (h + 1) * cyc) + im * math.sin(2 * math.pi * (h + 1) * cyc))
            v += w[i] * s
        return v

    # visible arc: from just under the ground at the left foot to just past the cut
    a_start = math.pi + math.asin(min(1.0, 7 / r_mix))
    a_end = math.acos(min(1.0, (CUT_X - CX) / r_mix)) if CUT_X - CX < r_mix else 0.0
    out = []
    span = (a_start - a_end) / 4
    for q in range(4):
        b0 = a_start - q * span
        mid = b0 - span / 2
        ox, oy = polar(r_mix, mid)
        line = []
        for s in range(32):
            phi = b0 - span * s / 31
            x, y = polar(r_mix + AMP * value(phi), phi)
            line.append((x - ox, y - oy))
        rib = ribbon(line, MIX_W / 2)
        assert len(rib) == 64
        for a, b in zip(rib, rib[1:] + rib[:1]):
            assert math.hypot(b[0] - a[0], b[1] - a[1]) >= 0.125
        assert max(max(abs(x), abs(y)) for x, y in rib) <= 64
        out.append(f'<path id="iris_node_{q}" transform="matrix(1 0 0 1 {fmt(ox)} {fmt(oy)})" '
                   f'd="{d_attr(rib)}" fill="{MIX_REST}" stroke="none"/>')
    return out


def header():
    pct = lambda v: f"{round(v * 100)}%"
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


def main():
    w, c = weights(P["morph"], P["overlap"])
    mix = mix_nodes(w, c)
    bands, nid = band_nodes(w, c, 4)
    # ground mask (a solid body: the earth under the horizon) and the horizon hairline
    mask = (f'<g id="iris_node_{nid}" transform="matrix(1 0 0 1 240 216)">'
            f'<path d="M -244 -3.4 L 244 -3.4 L 244 6 L -244 6 Z" fill="#000000" stroke="none"/></g>')
    hz = (f'<g id="iris_node_{nid + 1}" transform="matrix(1 0 0 1 240 {fmt(HORIZON)})">'
          f'<path d="M -244 -0.6 L 244 -0.6 L 244 0.6 L -244 0.6 Z" fill="#4B4B4B" stroke="none"/></g>')
    pal = [MIX_REST, MIX_HELD] + BAND_GREY[::-1]
    palette = [f'<path id="iris_palette_{k}" d="M {700 + 10 * k} 300 L {704 + 10 * k} 300 L {704 + 10 * k} 304 Z" '
               f'fill="{col}" stroke="{col}" stroke-width="2"/>' for k, col in enumerate(pal)]
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           '<g id="preview_canvas"><rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/></g>',
           header(), *palette,
           *bands,       # grey components underneath
           *mix,         # the one bright line over them
           mask, hz,     # the ground hides whatever slides below the horizon
           '</svg>']
    with open(OUT, "w") as fh:
        fh.write("\n".join(svg) + "\n")
    print(OUT, "nodes", nid + 2, "weights", [round(x, 3) for x in w])


if __name__ == "__main__":
    main()
