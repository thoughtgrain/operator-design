#!/usr/bin/env python3
"""iris · frame generator (revision 03, v3 "slide + swell", picked by the owner; first built from frames pass 02 v3, (from frames pass 02, v3: centred hero, density gradient, picked by the owner).

The bow is seen square-on from above the anti-solar point, so every band is a
full half-circle about one centre on the horizon, centred in the body. Four
grey component bands (sine outermost, saw innermost) ride their arcs as chains
of one-cycle nodes. The cycle count rises inward (11, 13, 14, 16) while the
radius falls, so the wavelength on screen halves from the outer band to the
inner one: plain and long outside, bright and dense inside, the way a real
bow's wavelengths order. That density gradient is what reads as "spectrum".

The one bright line is the MIX: the window-weighted sum of the four waves,
low-passed by tone, riding at the radius morph sets, with the cycle density of
that radius. Drawn as four mutable outlines (iris_node_0..3), a quarter of the
half-turn each, 32 centreline points -> 64-point closed ribbon.

Differences from the pass sketch: the mix keeps its real level (no per-frame
normalising, so Tone visibly shrinks it), each band enters the mix at its own
spread cycle count (so Spread beats along the arc), and `travel` (cycles) is
how far the held-note motion has carried the mix.

Usage: gen_frames.py                 -> the whole set in frames/
       gen_frames.py out.svg key=value ... [held=1] [travel=0.4]
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))

DEFAULTS = dict(morph=0.3333, overlap=0.25, spread=0.0, tone=0.7, skew=0.0, phase=0.0)
P = dict(DEFAULTS)
CONTROLS = ["morph", "overlap", "spread", "tone", "skew", "phase"]

W, H = 480, 220
CX, CY = 240.0, 232.0                 # bow centre below the screen: the feet run off the bottom edge
RADII = [156.0, 146.0, 136.0, 126.0]  # sine, tri, square, saw: 10 px apart, so neighbouring crests interlock
CYCLES = [11, 13, 14, 16]             # denser inward: wavelength 44 -> 21 px
AMP_BAND = 5.0                        # px, radial (full height)
AMP_LEVELS = [0.8, 5.5]                # pre-drawn chain heights: out of the blend (a ripple), in it (full height).
                                       # Two, not three: panel.svg has to fit 64 KiB, so a band carries three chains
                                       # (ripple, full, full rounded) of 16 cycles
WIDTHS = [1.0, 1.6, 2.2]               # pre-drawn chain weights for "weight"
MODE = "both"                          # revision 03 v3: blended rings slide onto the bright line and swell
AMP_MIX = 5.0
BAND_W = 1.5                          # Line weight
MIX_W = 2.5                           # Subject weight
HAIR_W = 1.2
KINDS = ["sine", "tri", "square", "saw"]
GREYS = ["#646464", "#646464", "#7D7D7D", "#969696"]   # floor 3.55:1: a band out of the mix still carries meaning
MIX_REST, MIX_HELD = "#AFAFAF", "#CDCDCD"
HORIZON = "#4B4B4B"


# ---------------------------------------------------------------- waveforms
def skew_t(kind, t, skew):
    t %= 1.0
    if kind == "saw" or skew <= 0:
        return t
    b = 0.5 - 0.45 * skew
    return 0.5 * t / b if t < b else 0.5 + 0.5 * (t - b) / (1 - b)


def ideal(kind, t, skew=0.0):
    """Raw (un-filtered) component wave, t in cycles, range [-1, 1]."""
    t = skew_t(kind, t, skew)
    if kind == "sine":
        return math.sin(2 * math.pi * t)
    if kind == "tri":
        if t < 0.25:
            return 4 * t
        if t < 0.75:
            return 2 - 4 * t
        return 4 * t - 4
    if kind == "square":
        return 1.0 if t < 0.5 else -1.0
    # saw: rises through 0 at t=0, drops at t=0.5
    return 2 * t if t < 0.5 else 2 * t - 2


def gain(n, tone):
    # Drawn bandwidth, not the engine's: the engine's cutoff runs 0.5 .. 7.5 octaves above the note, but a mix line at
    # ~10 points per cycle can only show harmonics up to about the 5th. So the drawing spans 0 .. 3.5 octaves (from the
    # note itself to 11 harmonics): the same curve, fitted to what the screen resolves, with its low end at the
    # fundamental so a closed Tone visibly loses level (the engine's 0.5 octave already costs the fundamental ~1 dB).
    fc = 2 ** (3.5 * tone)
    return 1 / math.sqrt(1 + (n / fc) ** 4)


def series(kind, x, tone, nh=64):
    if kind == "sine":
        return gain(1, tone) * math.sin(x)
    s = 0.0
    for n in range(1, nh + 1):
        if kind == "tri" and n % 2:
            s += gain(n, tone) * ((-1) ** ((n - 1) // 2)) * math.sin(n * x) / n ** 2 * 8 / math.pi ** 2
        elif kind == "square" and n % 2:
            s += gain(n, tone) * math.sin(n * x) / n * 4 / math.pi
        elif kind == "saw":
            s += gain(n, tone) * ((-1) ** (n + 1)) * math.sin(n * x) / n * 2 / math.pi
    return s


def weights(morph, overlap):
    c = morph * 3.0
    width = 1 + 3 * overlap
    w = [max(0.0, 1 - abs(i - c) / width) for i in range(4)]
    s = sum(w)
    return [x / s for x in w], c


def lerp_band(vals, c):
    i = min(int(math.floor(c)), 2)
    f = c - i
    return vals[i] + (vals[i + 1] - vals[i]) * f


# ---------------------------------------------------------------- geometry
def polar(r, phi):
    """phi 0 = right foot, pi = left foot; y up from the horizon."""
    return (CX + r * math.cos(phi), CY - r * math.sin(phi))


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
            n1 = (-ay / La, ax / La)
            n2 = (-by / Lb, bx / Lb)
            sx, sy = n1[0] + n2[0], n1[1] + n2[1]
            Ls = math.hypot(sx, sy) or 1e-9
            nx, ny = sx / Ls, sy / Ls
            m = min(1.0 / max(nx * n1[0] + ny * n1[1], 1e-6), 2.0)
        left.append((line[k][0] + nx * hw * m, line[k][1] + ny * hw * m))
        right.append((line[k][0] - nx * hw * m, line[k][1] - ny * hw * m))
    return left + right[::-1]


def dedupe(line, gap=0.3):
    out = [line[0]]
    for q in line[1:]:
        if math.hypot(q[0] - out[-1][0], q[1] - out[-1][1]) >= gap:
            out.append(q)
    return out


def fmt(v):
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "", "-") else s


def d_of(poly, ox=0.0, oy=0.0):
    return "M " + " L ".join(f"{fmt(x - ox)} {fmt(y - oy)}" for x, y in poly) + " Z"


# ---------------------------------------------------------------- parts
def band_radius(i, c, wn):
    """wn: this band's mix weight over the top weight (0..1). How far it moves depends on MODE."""
    target = lerp_band(RADII, c)
    pull = min(1.0, wn * (0.6 + 0.6 * P["overlap"]))              # blended rings slide onto the bright line
    if MODE in ("slide", "both"):
        return RADII[i] + (target - RADII[i]) * pull
    if MODE == "gather":
        if wn > 0:                                                 # any share of the blend: onto the line
            return target
        away = 1 if RADII[i] > target else -1                      # out of the blend: pushed away from the line
        return RADII[i] + away * (12 + 8 * P["overlap"])
    return RADII[i] + (target - RADII[i]) * 0.8 * P["overlap"]    # swell / weight: overlap alone moves the rings


def band_cycles(i):
    """spread stretches band i's cycle length by 1 + 0.12 (i - 1.5)."""
    return CYCLES[i] / (1 + 0.12 * P["spread"] * (i - 1.5) * 1.0)


START = {"sine": 0.0, "tri": 0.0, "square": 0.25, "saw": 0.0}


def cycle_line(kind, r, phi0, dphi, t0, skew, amp=None):
    """One cycle's centreline from phi0 over dphi (negative = clockwise), as the panel authors it: a sine at 12
    points, straight-sided waves by their corners only (a jump leans by a hair, 0.02 cycle, so the ribbon has a flat
    end, not a fold). Few points, because panel.svg has to fit 64 KiB."""
    e = 0.01
    a = AMP_BAND if amp is None else amp
    if kind == "sine":
        pts = [(k / 12, math.sin(2 * math.pi * (t0 + k / 12))) for k in range(13)]
    else:
        b = 0.5 - 0.45 * skew
        if kind == "tri":
            pts = [(0, 0), (b / 2, 1), (b + (1 - b) / 2, -1), (1, 0)]
        elif kind == "square":     # starts on the high plateau (t0 = 0.25)
            q = b / 2
            pts = [(0, 1), (q - e, 1), (q + e, -1), (q + 1 - b - e, -1), (q + 1 - b + e, 1), (1, 1)]
        else:
            pts = [(0, 0), (0.5 - e, 1), (0.5 + e, -1), (1, 0)]
    line = [polar(r + a * v, phi0 + dphi * u) for u, v in pts]
    return dedupe(line)


def main(out, held=False, travel=0.0, shift_held=False):
    w, c = weights(P["morph"], P["overlap"])
    wmax = max(w)
    body = []
    nid = 4

    # bands: chains of one-cycle nodes, left foot -> right foot
    band_nodes = []
    for i, kind in enumerate(KINDS):
        lvl3 = int(round(3 * w[i] / wmax))                        # 0..3, as the device picks it
        r = band_radius(i, c, w[i] / wmax)
        amp, width = AMP_BAND, BAND_W
        ripple = False
        if MODE in ("swell", "both"):
            ripple = lvl3 == 0
            amp = AMP_LEVELS[0 if ripple else 1]
        if MODE == "weight":
            width = WIDTHS[0 if lvl3 == 0 else 1 if lvl3 < 3 else 2]
        n = band_cycles(i)
        dphi = -math.pi / n
        shift = P["phase"] * i / 8.0
        grey = GREYS[int(round(3 * w[i] / wmax))]
        if MODE == "weight":
            grey = GREYS[0] if lvl3 == 0 else GREYS[3] if lvl3 == 3 else GREYS[2]
        # Tone's second channel: the bands run plain (outside) to bright (inside), so a low-pass is drawn as the
        # cut sweeping outward band by band as Tone closes: a cut band is drawn as the rounded hump that gets
        # through. Nothing cut at 100, everything but the sine cut at 0. On the device that's a second, pre-drawn
        # hump chain per band, shown in place of the raw one.
        # By band, not by drawn radius (Overlap moves the radii): saw cut below 65 %, square below 60 %, triangle
        # below 25 %; the sine is never cut. All four stand raw at the 70 % default.
        cut = P["tone"] < (0.0, 0.25, 0.60, 0.65)[i]
        if cut:                                     # rounded to the hump that gets through, one grey step down
            grey = GREYS[max(0, int(round(3 * w[i] / wmax)) - 1)]
        # whole cycles only; phase slides the chain along the arc and the
        # cycles that pass a foot go under the ground mask (parked when wholly
        # below it), so the chain wraps instead of leaving a gap
        frac = shift - math.floor(shift)
        for k in range(-1, int(math.ceil(n)) + 1):
            phi0 = math.pi + dphi * (k + frac)
            phi1 = phi0 + dphi
            if phi0 <= 0 or phi1 >= math.pi:
                continue                        # wholly below the horizon
            mid = phi0 + dphi / 2
            ox, oy = polar(r, mid)
            # skew 0: the bands are fixed one-cycle nodes on the device and can't lean; Skew acts on the mix line only
            line = cycle_line("sine" if (cut or ripple) else kind, r, phi0, dphi, START[kind], 0.0, amp)
            poly = ribbon(line, width / 2)
            band_nodes.append(
                f'<path id="iris_node_{nid}" transform="matrix(1 0 0 1 {fmt(ox)} {fmt(oy)})" '
                f'd="{d_of(poly, ox, oy)}" fill="{grey}" stroke="none"/>')
            nid += 1

    # the mix: four quarter outlines, 32 centreline points each
    r_mix = lerp_band(RADII, c)
    n_mix = lerp_band(CYCLES, c)
    tone, skew = P["tone"], P["skew"]
    mix_nodes = []
    norm = None
    samples = []
    for q in range(4):
        line = []
        for k in range(32):
            # 32 points per quarter, quarters meet end to end
            u = (q + k / 31) / 4               # 0..1 across the half-turn
            phi = math.pi * (1 - u)
            v = 0.0
            for i, kind in enumerate(KINDS):
                if w[i] <= 0:
                    continue
                t = n_mix * u * (1 + 0.12 * P["spread"] * (i - 1.5)) - travel
                tt = skew_t(kind, t + P["phase"] * i / 8.0, skew)
                v += w[i] * series(kind, 2 * math.pi * tt, tone)
            line.append((phi, v))
        samples.append(line)
    peak = 1.0                             # real level: Tone and Phase shrink it
    for q, line in enumerate(samples):
        pts = [polar(r_mix + AMP_MIX * v / peak, phi) for phi, v in line]
        poly = ribbon(pts, MIX_W / 2)
        mid = polar(r_mix, math.pi * (1 - (q + 0.5) / 4))
        mix_nodes.append(
            f'<path id="iris_node_{q}" transform="matrix(1 0 0 1 {fmt(mid[0])} {fmt(mid[1])})" '
            f'd="{d_of(poly, *mid)}" fill="{MIX_HELD if held else MIX_REST}" stroke="none"/>')

    # horizon (hairline ribbon) and the ground mask below it
    hy = CY + 0.6
    hz = [(CX - 200, hy - HAIR_W / 2), (CX + 200, hy - HAIR_W / 2), (CX + 200, hy + HAIR_W / 2), (CX - 200, hy + HAIR_W / 2)]
    mask = [(CX - 200, hy + HAIR_W / 2), (CX + 200, hy + HAIR_W / 2), (CX + 200, 220), (CX - 200, 220)]
    ground = [] and [  # revision 03: no horizon or mask, the screen edge cuts the bow (kept for reference)
        # static art, not nodes (as on the device: a bound black mask would take its palette entry's paint)
        f'<path transform="matrix(1 0 0 1 {fmt(CX)} {fmt(hy)})" d="{d_of(mask, CX, hy)}" fill="#000000" stroke="none"/>',
        f'<path transform="matrix(1 0 0 1 {fmt(CX)} {fmt(hy)})" d="{d_of(hz, CX, hy)}" fill="{HORIZON}" stroke="none"/>',
    ]

    palette = [MIX_REST, MIX_HELD, GREYS[0], GREYS[2], GREYS[3]]
    pal = [f'<path id="iris_palette_{k}" d="M {700 + 10 * k} 300 L {704 + 10 * k} 300 L {704 + 10 * k} 304 Z" '
           f'fill="{col}" stroke="{col}" stroke-width="2"/>' for k, col in enumerate(palette)]

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           '<g id="preview_canvas"><rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/></g>',
           header(shift_held),
           *pal,
           *band_nodes, *ground, *mix_nodes,
           '</svg>']
    with open(out, "w") as fh:
        fh.write("\n".join(svg) + "\n")
    print(out, "band nodes", len(band_nodes), "weights", [round(x, 2) for x in w])


def pct(v):
    return f"{round(v * 100)}%"


def header(shift=False):
    """The stock single-row header. While Shift is held its four slots show the Shift row instead (skew, phase, and
    nothing under encoders 3 and 4): Shift replaces the header's contents, it never adds a row."""
    if shift:
        slots = [("skew", pct(P["skew"])), ("phase", pct(P["phase"])), ("", ""), ("", "")]
    else:
        slots = [("morph", pct(P["morph"])), ("overlap", pct(P["overlap"])), ("spread", pct(P["spread"])), ("tone", pct(P["tone"]))]
    g = ['<g id="preview_header">',
         '<rect x="0" y="0" width="480" height="20" fill="#000000" stroke="none"/>']
    steps = ["#000000", "#323232", "#4B4B4B", "#646464", "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD"]
    for i, col in enumerate(steps):
        g.append(f'<rect x="{60 * i}" y="0" width="60" height="20" fill="{col}" stroke="none"/>')
    for i, (t, v) in enumerate(slots):
        if not t:
            continue
        ink = "#CBCBCB" if i < 2 else "#000000"
        x = 120 * i
        g.append(f'<text transform="matrix(1 0 0 1 {x + 5} 10)" fill="{ink}" stroke="none" font-family="UniversNextPro-Light" font-size="10px">{t}</text>')
        g.append(f'<text transform="matrix(1 0 0 1 {x + 65} 17.44)" fill="{ink}" stroke="none" font-family="UniversNextPro-Light" font-size="20px">{v}</text>')
    g.append("</g>")
    return "\n".join(g)


def frame_set():
    d = os.path.join(HERE, "frames")
    os.makedirs(d, exist_ok=True)
    P.clear(); P.update(DEFAULTS)
    main(os.path.join(d, "rest.svg"))
    main(os.path.join(d, "playing.svg"), held=True, travel=0.4)
    main(os.path.join(d, "shift.svg"), shift_held=True)                 # Shift held at the defaults: only the header changes
    for n, k in enumerate(CONTROLS, 1):
        for v in (0.0, 0.5, 1.0):
            P.clear(); P.update(DEFAULTS); P[k] = v
            main(os.path.join(d, f"c{n}-{int(v * 100):03d}.svg"), shift_held=k in ("skew", "phase"))   # turned with Shift held
    P.clear(); P.update(DEFAULTS)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        frame_set()
        sys.exit(0)
    out, held, travel, shift = os.path.join(HERE, "frames", "out.svg"), False, 0.0, False
    for a in sys.argv[1:]:
        if "=" in a:
            k, v = a.split("=")
            if k == "held":
                held = v == "1"
            elif k == "shift":
                shift = v == "1"
            elif k == "travel":
                travel = float(v)
            else:
                P[k] = float(v)
        else:
            out = a
    main(out, held, travel, shift_held=shift)
