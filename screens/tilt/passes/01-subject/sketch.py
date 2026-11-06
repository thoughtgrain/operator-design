#!/usr/bin/env python3
"""Subject-pass sketches for tilt: five rest frames, one per direction.

    python3 screens/tilt/passes/01-subject/sketch.py

Writes v1..v5/rest.svg beside this file. Every variant draws the same fixed
test material (a harmonic source with three formants, three hits in time)
through the same model of the effect at its defaults, so the five differ in
idea, not in data:

    focus  1 kHz   centre of the focal band (sharp inside, about ±0.5 oct)
    tilt   0       spectral tilt about the focus, ±6 dB/oct
    blur   40 %    smear outside the band, in frequency and in time
    mix    100 %   wet only

An effect page gets no audio and no notes, so the drawing is the settings
applied to a fixed test chart, not the live signal.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------- defaults
FOCUS = 1000.0
TILT = 0.0      # -1..1  (±6 dB/oct)
BLUR = 0.4      # 0..1
MIX = 1.0       # 0..1
CAPTIONS = ("1k", "0", "40", "100")
LABELS = ("focus", "tilt", "blur", "mix")

F_LO, F_HI = 50.0, 12800.0          # 8 octaves
BAND = 0.5                           # half-width of the focal band, octaves

G = dict(c0="#000000", c1="#323232", c2="#4B4B4B", c3="#646464", c4="#7D7D7D",
         c5="#969696", c6="#AFAFAF", c7="#CDCDCD")


# ---------------------------------------------------------------- test material + effect model
def oct_of(f: float) -> float:
    return math.log2(f / F_LO)


def source_db(f: float) -> float:
    """Fixed test source: 82.4 Hz harmonics, 1/k^0.7, three formants, a floor."""
    f0 = 82.4
    x = oct_of(f)
    amp = 0.0
    for k in range(1, 160):
        fk = f0 * k
        if fk > F_HI * 1.1:
            break
        d = (x - oct_of(fk)) / 0.02
        if abs(d) < 5:
            form = (0.5 + 4.0 * math.exp(-((math.log2(fk / 520)) / 0.4) ** 2)
                    + 2.6 * math.exp(-((math.log2(fk / 1550)) / 0.3) ** 2)
                    + 1.6 * math.exp(-((math.log2(fk / 2900)) / 0.3) ** 2))
            amp += (k ** -0.85) * form * math.exp(-0.5 * d * d)
    amp += 0.012
    return max(-48.0, min(0.0, 20 * math.log10(amp) - 4))


GRID = [F_LO * 2 ** (i / 256) for i in range(8 * 256 + 1)]
SRC = [source_db(f) for f in GRID]


def in_band(f: float, focus: float = FOCUS) -> float:
    d = math.log2(f / focus) / BAND
    return math.exp(-0.5 * (d * 1.6) ** 4)       # flat-topped window, ~1 inside, ~0 outside


def smooth_db(sig_oct: float) -> list[float]:
    """Gaussian smoothing in log-frequency, averaged in power."""
    if sig_oct <= 0:
        return SRC[:]
    step = 1 / 256
    r = int(3 * sig_oct / step)
    ker = [math.exp(-0.5 * ((j * step) / sig_oct) ** 2) for j in range(-r, r + 1)]
    pw = [10 ** (v / 10) for v in SRC]
    out = []
    n = len(pw)
    for i in range(n):
        s = w = 0.0
        for j, k in enumerate(ker):
            t = i + j - r
            if 0 <= t < n:
                s += pw[t] * k
                w += k
        out.append(10 * math.log10(s / w))
    return out


SMOOTH = smooth_db(0.04 + BLUR * 0.6)


def wet_db(i: int, focus=FOCUS, tilt=TILT) -> float:
    f = GRID[i]
    w = in_band(f, focus)
    v = w * SRC[i] + (1 - w) * SMOOTH[i]
    v += tilt * 6 * math.log2(f / focus)
    return v


def level_at(f: float, wet=True) -> float:
    i = max(0, min(len(GRID) - 1, round(oct_of(f) * 256)))
    return wet_db(i) if wet else SRC[i]


def band_db(fc: float, width_oct: float, wet=True) -> float:
    """Power-average level over a band."""
    lo, hi = oct_of(fc) - width_oct / 2, oct_of(fc) + width_oct / 2
    i0, i1 = max(0, int(lo * 256)), min(len(GRID) - 1, int(hi * 256))
    vals = [(wet_db(i) if wet else SRC[i]) for i in range(i0, i1 + 1)]
    return 10 * math.log10(sum(10 ** (v / 10) for v in vals) / len(vals))


# time: three hits (rows), each decays; the effect smears time outside the band
def hits(t: float) -> float:
    e = 0.0
    for t0, a in ((0.0, 1.0), (3 / 7, 0.8), (5 / 7, 0.9)):
        if t >= t0 - 1e-9:
            e = max(e, a * math.exp(-max(0.0, t - t0) / 0.05))
    return e


def time_env(t: float, f: float) -> float:
    """Envelope at time t (0..1) for band f: sharp in the band, smeared outside."""
    w = in_band(f)
    sig = 0.004 + (1 - w) * BLUR * 0.2
    if sig < 0.012:
        return hits(t)
    n = 24
    s = ws = 0.0
    for j in range(-n, n + 1):
        tt = t + j * sig * 3 / n
        k = math.exp(-0.5 * (j * 3 / n) ** 2)
        s += hits(min(1.0, max(0.0, tt))) * k
        ws += k
    return s / ws


# ---------------------------------------------------------------- drawing helpers
def n4(v: float) -> str:
    s = f"{v:.2f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def clean(pts, min_gap=0.4):
    out = []
    for p in pts:
        if not out or math.dist(out[-1], p) >= min_gap:
            out.append(p)
    return out


def ribbon_pts(pts, w):
    pts = clean(pts)
    hw = w / 2
    n = len(pts)
    left, right = [], []
    for i in range(n):
        if i == 0:
            dx, dy = pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]
            L = math.hypot(dx, dy)
            nx, ny = -dy / L, dx / L
            sc = 1.0
        elif i == n - 1:
            dx, dy = pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]
            L = math.hypot(dx, dy)
            nx, ny = -dy / L, dx / L
            sc = 1.0
        else:
            ax, ay = pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]
            bx, by = pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]
            la, lb = math.hypot(ax, ay), math.hypot(bx, by)
            n1 = (-ay / la, ax / la)
            n2 = (-by / lb, bx / lb)
            mx, my = n1[0] + n2[0], n1[1] + n2[1]
            lm = math.hypot(mx, my) or 1
            nx, ny = mx / lm, my / lm
            cos = nx * n1[0] + ny * n1[1]
            sc = min(2.0, 1 / max(cos, 0.5))
        left.append((pts[i][0] + nx * hw * sc, pts[i][1] + ny * hw * sc))
        right.append((pts[i][0] - nx * hw * sc, pts[i][1] - ny * hw * sc))
    return left + right[::-1]


def d_of(poly):
    poly = clean(poly, 0.2)
    if len(poly) > 2 and math.dist(poly[0], poly[-1]) < 0.3:
        poly = poly[:-1]
    return "M " + " L ".join(f"{n4(x)} {n4(y)}" for x, y in poly) + " Z"


def ribbon(pts, w, col):
    """Open polyline -> thin closed filled ribbon(s), ≤ 64 points each."""
    pts = clean(pts)
    out = []
    i = 0
    while i < len(pts) - 1:
        chunk = pts[i:i + 31]
        if len(chunk) >= 2:
            out.append(f'<path d="{d_of(ribbon_pts(chunk, w))}" fill="{col}" stroke="none"/>')
        i += 30
    return out


def poly(pts, fill, stroke="none", sw=None):
    sw_attr = f' stroke-width="{n4(sw)}"' if stroke != "none" else ""
    return f'<path d="{d_of(pts)}" fill="{fill}" stroke="{stroke}"{sw_attr} stroke-linejoin="round"/>'


def text(x, y, s, col=G["c4"], size=10):
    return (f'<text transform="matrix(1 0 0 1 {n4(x)} {n4(y)})" fill="{col}" stroke="none" '
            f'font-family="UniversNextPro-Light" font-size="{size}px">{s}</text>')


def text_c(x, y, s, col=G["c4"], size=10):
    w = len(s) * 0.56 * size
    return text(x - w / 2, y, s, col, size)


def header():
    steps = ["#000000", "#323232", "#4B4B4B", "#646464", "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD"]
    out = ['<g id="preview_header">']
    for i, c in enumerate(steps):
        out.append(f'  <rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
    for i, lab in enumerate(LABELS):
        col = "#CBCBCB" if i < 2 else "#000000"
        out.append(f'  <text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{col}" stroke="none" '
                   f'font-family="UniversNextPro-Light" font-size="10px">{lab}</text>')
    for i, val in enumerate(CAPTIONS):
        col = "#CBCBCB" if i < 2 else "#000000"
        out.append(f'  <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{col}" stroke="none" '
                   f'font-family="UniversNextPro-Light" font-size="20px">{val}</text>')
    out.append("</g>")
    return out


def frame(body, note):
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
             f"  <!-- tilt · subject pass 01 · {note} -->",
             '<g id="preview_canvas">',
             '  <rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>',
             "</g>"]
    lines += header()
    lines += body
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- v1 · P3 trace · typeset diagram
def v1():
    X0, X1 = 40.0, 450.0
    ppo = (X1 - X0) / 8

    def fx(f):
        return X0 + oct_of(f) * ppo

    def fy(db):
        return 52 + (-db) / 48 * 92

    body = []
    # axis: hairline baseline with octave ticks; the focal span on it at line weight
    AX = 192
    body += ribbon([(X0, AX), (X1, AX)], 1.0, G["c3"])
    for k in range(9):
        x = X0 + k * ppo
        body += ribbon([(x, AX), (x, AX + 4)], 1.0, G["c3"])
    for f, s in ((100, "100"), (1000, "1k"), (10000, "10k")):
        body.append(text_c(fx(f), AX + 15, s))
    body.append(text(X0 - 2, 44, "dB", G["c4"]))
    body.append(text(X1 - 8, AX + 15, "Hz", G["c4"]))
    # left scale: three hairline ticks at 0, -24, -48 dB
    for db in (0, -24, -48):
        body += ribbon([(X0 - 7, fy(db)), (X0 - 3, fy(db))], 1.0, G["c3"])
    lo, hi = FOCUS * 2 ** -BAND, FOCUS * 2 ** BAND
    body += ribbon([(fx(lo), AX - 1), (fx(hi), AX - 1)], 1.5, G["c5"])
    for f in (lo, hi):
        body += ribbon([(fx(f), AX - 9), (fx(f), AX)], 1.5, G["c5"])
    # pivot: a short hairline from the axis to the trace at the focus (tilt turns about it)
    piv_y = fy(level_at(FOCUS))
    body += ribbon([(fx(FOCUS), AX - 9), (fx(FOCUS), AX - 22)], 1.0, G["c3"])

    # dry ghost: sharp everywhere, dark hairline, dropped by mix
    drop = 34 * MIX
    dry = [(fx(GRID[i]), fy(SRC[i]) + drop) for i in range(0, len(GRID), 8)]
    dry = [(x, min(y, AX - 4)) for x, y in dry]
    body += ribbon(dry, 1.0, G["c2"])

    # wet trace: sparse where it's smooth, dense in the band (3 mutable outlines of 31 points)
    o_lo, o_hi = oct_of(lo) - 0.15, oct_of(hi) + 0.15
    segs = [(0.0, o_lo), (o_lo, o_hi), (o_hi, 8.0)]
    for si, (a, b) in enumerate(segs):
        if si == 1:
            # in the band the outline puts its points on the partials and the gaps between them
            os_ = [a, b]
            k = 1
            while 82.4 * k < F_HI:
                ok = oct_of(82.4 * k)
                om = oct_of(82.4 * (k + 0.5))
                os_ += [o for o in (ok, om) if a < o < b]
                k += 1
            os_ = sorted(os_)
        else:
            os_ = [a + (b - a) * j / 30 for j in range(31)]
        pts = []
        for o in os_:
            i = max(0, min(len(GRID) - 1, round(o * 256)))
            pts.append((X0 + o * ppo, fy(wet_db(i))))
        body += ribbon(pts, 2.0, G["c7"])
    return frame(body, "v1 P3 trace as subject, typeset diagram")


# ---------------------------------------------------------------- v2 · P4 stack · orthographic elevation
def v2():
    bands = [125, 250, 500, 1000, 2000, 4000]
    cyc = [1.5, 2.5, 3.5, 5, 7, 9.5]
    fi = min(range(6), key=lambda i: abs(math.log2(bands[i] / FOCUS)))
    W = 196
    DX, DY = 36 * MIX + 4, -15 * MIX - 1
    X0, Y0 = 44, 205
    body = []
    # ground line and the depth dimension (elevation conventions), hairline
    body += ribbon([(24, Y0 + 0.5), (456, Y0 + 0.5)], 1.0, G["c2"])
    lv = [band_db(b, 1.0) for b in bands]
    for i in reversed(range(6)):
        ox, oy = X0 + DX * i, Y0 + DY * i
        h = 30 + (lv[i] + 48) / 48 * 44
        dist = abs(i - fi)
        sharp = 1.0 if dist == 0 else max(0.0, 1 - BLUR * (0.9 + 0.35 * dist))
        amp = 11 * (0.15 + 0.85 * sharp)
        n = 44
        top = []
        for j in range(n):
            u = j / (n - 1)
            x = ox + u * W
            ph = 2 * math.pi * cyc[i] * u
            wave = math.sin(ph) + (0.35 * sharp) * math.sin(3 * ph + 0.6) + (0.2 * sharp) * math.sin(5 * ph)
            top.append((x, oy - h + amp * wave * 0.75))
        if dist:
            # the smear: the contour echoed behind, lifted by the blur
            off = 3 + BLUR * 16 * min(1.0, 0.55 + 0.25 * dist)
            body += ribbon([(x, y - off) for x, y in top], 1.0, G["c2"])
        outline = top + [(ox + W, oy), (ox, oy)]
        if dist == 0:
            body.append(poly(outline, G["c0"], G["c7"], 2.0))
        else:
            body.append(poly(outline, G["c0"], G["c4"] if dist == 1 else G["c3"], 1.5))
    # elevation dimension under the stack: depth of the stack (static ticks)
    return frame(body, "v2 P4 stack in depth, orthographic elevation")


# ---------------------------------------------------------------- v3 · P10 voice field · survey plan
def v3():
    NC, NR = 24, 8
    X0, Y0, PX, PY = 58, 46, 16, 19
    fcols = [63 * 2 ** (i * 7.3 / (NC - 1)) for i in range(NC)]
    body = []
    # neat line (hairline frame) of the plan, chainage ticks + labels below
    L, T, R, B = X0 - 14, Y0 - 14, X0 + PX * (NC - 1) + 14, Y0 + PY * (NR - 1) + 14
    body += ribbon([(L, T), (R, T), (R, B), (L, B), (L, T + 0.6)], 1.0, G["c2"])

    def colx(f):
        return X0 + math.log2(f / 63) / 7.3 * (PX * (NC - 1))

    for f, s in ((100, "100"), (1000, "1k"), (10000, "10k")):
        x = colx(f)
        body += ribbon([(x, B), (x, B + 5)], 1.0, G["c3"])
        body.append(text_c(x, B + 17, s))
    for k in range(NR):
        y = Y0 + k * PY
        body += ribbon([(L - 5, y), (L, y)], 1.0, G["c3"])
    # focal strip boundaries, line weight, past the neat line at both ends
    for f in (FOCUS * 2 ** -BAND, FOCUS * 2 ** BAND):
        x = colx(f)
        body += ribbon([(x, T - 6), (x, B + 6)], 1.5, G["c4"])
    # plots
    rnd = random.Random(7)
    for c, f in enumerate(fcols):
        lev = band_db(f, 0.33)
        w = in_band(f)
        for r in range(NR):
            t = r / (NR - 1)
            e = time_env(t, f)
            edb = 20 * math.log10(max(e, 1e-4))
            v = max(0.0, min(1.0, (lev + edb + 54) / 42))
            s = 4 + 10 * v
            cx, cy = X0 + c * PX, Y0 + r * PY
            sq = [(cx - s / 2, cy - s / 2), (cx + s / 2, cy - s / 2), (cx + s / 2, cy + s / 2), (cx - s / 2, cy + s / 2)]
            if w > 0.5:
                body.append(poly(sq, G["c7"]))
            else:
                body.append(poly(sq, G["c0"], G["c4"] if w > 0.08 else G["c3"], 1.5))
    rnd.random()
    return frame(body, "v3 P10 voice field, survey plan")


# ---------------------------------------------------------------- v4 · P15 cell field · patent section
THR4 = 0.3


def v4():
    C = 22
    NC, NR = 20, 8
    X0, Y0 = 20, 30
    fcols = [55 * 2 ** (i * 7.8 / (NC - 1)) for i in range(NC)]
    body = []
    rnd = random.Random(11)
    hatched = total = 0
    # section outline of the block, line weight
    L, T, R, B = X0, Y0, X0 + NC * C, Y0 + NR * C
    body.append(poly([(L, T), (R, T), (R, B), (L, B)], "none", G["c3"], 1.5))
    for c, f in enumerate(fcols):
        lev = band_db(f, 0.36)
        w = in_band(f)
        base = max(0.0, min(1.0, (lev + 44) / 40))
        for r in range(NR):
            t = r / (NR - 1)
            e = time_env(t, f)
            edb = 20 * math.log10(max(e, 1e-4))
            x, y = X0 + c * C, Y0 + r * C
            jitter = rnd.random()
            if w > 0.2:
                if hits(t) > 0.25:  # inside the band the hits stay sharp
                    body.append(poly([(x, y), (x + C, y), (x + C, y + C), (x, y + C)], G["c7"]))
                continue
            val = (lev + edb + 54) / 42 + 0.3 * (jitter - 0.5)
            total += 1
            if val > THR4:
                # cut material: 45° section hatching, 1 px, 5 px pitch, kept inside the cell
                hatched += 1
                # lines x + y = k on one global 5 px pitch, so a run of cells reads as one cut face
                for k in range(int(x + y) // 5 * 5, int(x + C + y + C) + 5, 5):
                    ya, yb = max(y, k - (x + C)), min(y + C, k - x)
                    if yb - ya > 3.0:
                        body += ribbon([(k - ya, ya), (k - yb, yb)], 1.0, G["c4"] if w > 0.08 else G["c3"])
    print(f"v4 hatched {hatched}/{total}")
    return frame(body, "v4 P15 cell field, patent section")


# ---------------------------------------------------------------- v5 · P13 capture · hidden-line isometric
def v5():
    a = math.radians(24)
    b = math.radians(30)
    LU, LV = 318, 58
    O = (92, 70)

    def P(u, v, h=0.0):
        return (O[0] + u * LU * math.cos(a) - v * LV * math.cos(b),
                O[1] + u * LU * math.sin(a) + v * LV * math.sin(b) - h)

    body = []
    # the base plate (hairline) and its front edge as the mix scale
    plate = [P(0, 0), P(1, 0), P(1, 1), P(0, 1)]
    body.append(poly(plate, G["c0"], G["c2"], 1.5))
    for k in range(9):
        u = k / 8
        body += ribbon([P(u, 1), P(u, 1.16)], 1.0, G["c3"])
    body += ribbon([P(0, 1.08), P(MIX, 1.08)], 1.5, G["c5"])

    NF = 22
    fins = [55 * 2 ** (i * 7.7 / (NF - 1)) for i in range(NF)]
    uf = math.log2(FOCUS / 55) / 7.7
    du = 0.012
    v0, v1_ = 0.3, 0.7
    ulo = math.log2(FOCUS * 2 ** -BAND / 55) / 7.7
    uhi = math.log2(FOCUS * 2 ** BAND / 55) / 7.7
    # plane of focus: lines where its two faces meet the plate (far line now)
    body += ribbon([P(ulo, -0.12), P(ulo, 1.0)], 1.0, G["c4"])

    def fin(u, h, solid, ghost_off=0.0):
        out = []
        top = [P(u, v0, h), P(u + du, v0, h), P(u + du, v1_, h), P(u, v1_, h)]
        side = [P(u + du, v0, h), P(u + du, v1_, h), P(u + du, v1_, 0), P(u + du, v0, 0)]
        front = [P(u, v1_, h), P(u + du, v1_, h), P(u + du, v1_, 0), P(u, v1_, 0)]
        if solid:
            out.append(poly(side, G["c5"]))
            out.append(poly(front, G["c3"]))
            out.append(poly(top, G["c7"]))
        else:
            sil = [P(u, v0, h), P(u + du, v0, h), P(u + du, v0, 0), P(u + du, v1_, 0), P(u, v1_, 0), P(u, v1_, h)]
            if ghost_off > 0:
                g = [(x - ghost_off * 0.6, y - ghost_off * 0.35) for x, y in sil]
                out.append(poly(g, G["c0"], G["c2"], 1.5))
            out.append(poly(side, G["c0"], G["c3"], 1.5))
            out.append(poly(front, G["c0"], G["c3"], 1.5))
        return out

    focus_plane_drawn = False
    for i, f in enumerate(fins):
        u = math.log2(f / 55) / 7.7 - du / 2
        if not focus_plane_drawn and u > uf:
            # the plane of focus: an upright sheet across the plate, edges only (glass)
            sheet = [P(uf, -0.14, 0), P(uf, -0.14, 70), P(uf, 1.14, 70), P(uf, 1.14, 0)]
            body.append(poly(sheet, "none", G["c4"], 1.5))
            focus_plane_drawn = True
        if u > uhi and not getattr(v5, "_hi", False):
            body += ribbon([P(uhi, -0.12), P(uhi, 1.0)], 1.0, G["c4"])
            v5._hi = True
        w = in_band(f)
        lev = band_db(f, 0.35)
        h = 8 + max(0.0, min(1.0, (lev + 40) / 30)) * 48
        dist = abs(math.log2(f / FOCUS))
        body += fin(u, h, w > 0.5, 0.0 if w > 0.5 else BLUR * 14 * min(1.0, 0.4 + dist / 3))
    _ = uf
    return frame(body, "v5 P13 capture, hidden-line isometric (stretch)")


def main():
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        d = HERE / name
        d.mkdir(exist_ok=True)
        (d / "rest.svg").write_text(fn())
        print("wrote", d / "rest.svg")


if __name__ == "__main__":
    main()
