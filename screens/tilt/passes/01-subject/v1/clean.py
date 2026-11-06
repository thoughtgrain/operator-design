#!/usr/bin/env python3
"""tilt v1 cleanup: the owner's pick, tidied. Writes v1/clean.svg beside this file.

    python3 screens/tilt/passes/01-subject/v1/clean.py

The model and drawing helpers are copied from ../sketch.py (unchanged); only
the v1 drawing differs: no text or figures, no left scale, the dry ghost kept
under the trace, the pivot mark tied to the focus bracket.
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

# ---------------------------------------------------------------- v1 · cleaned
X0, X1 = 40.0, 440.0                 # 8 octaves, 50 Hz .. 12.8 kHz
PPO = (X1 - X0) / 8
AX = 188                             # the frequency axis


def fx(f):
    return X0 + oct_of(f) * PPO


def fy(db):
    return 50 + (-db) / 48 * 92


def wet_trace():
    """The wet line as three runs (left, band, right), as the device would hold it."""
    lo, hi = FOCUS * 2 ** -BAND, FOCUS * 2 ** BAND
    o_lo, o_hi = oct_of(lo) - 0.15, oct_of(hi) + 0.15
    runs = []
    for si, (a, b) in enumerate([(0.0, o_lo), (o_lo, o_hi), (o_hi, 8.0)]):
        if si == 1:
            # in the band the outline puts its points on the partials and the gaps between them
            os_ = [a, b]
            k = 1
            while 82.4 * k < F_HI:
                os_ += [o for o in (oct_of(82.4 * k), oct_of(82.4 * (k + 0.5))) if a < o < b]
                k += 1
            os_ = sorted(os_)
        else:
            os_ = [a + (b - a) * j / 30 for j in range(31)]
        runs.append([(X0 + o * PPO, fy(wet_db(max(0, min(len(GRID) - 1, round(o * 256)))))) for o in os_])
    return runs


def lowest_y_near(runs, x, reach=5.0):
    """The lowest point (largest y) the wet line reaches within `reach` px of x."""
    best = None
    for run in runs:
        for (xa, ya), (xb, yb) in zip(run, run[1:]):
            if xb < x - reach or xa > x + reach:
                continue
            for t in (0.0, 0.5, 1.0):
                xx, yy = xa + (xb - xa) * t, ya + (yb - ya) * t
                if abs(xx - x) <= reach:
                    best = yy if best is None else max(best, yy)
    return best


def v1_clean():
    body = []
    lo, hi = FOCUS * 2 ** -BAND, FOCUS * 2 ** BAND
    # axis: a hairline with octave ticks, no figures (the header names the focus)
    body += ribbon([(X0, AX), (X1, AX)], 1.0, G["c3"])
    for k in range(9):
        x = X0 + k * PPO
        body += ribbon([(x, AX), (x, AX + 4)], 1.0, G["c3"])
    # the focal band on the axis: a bracket at Line weight, its centre marked as the tilt's pivot
    body += ribbon([(fx(lo), AX - 1), (fx(hi), AX - 1)], 1.5, G["c5"])
    for f in (lo, hi):
        body += ribbon([(fx(f), AX - 8), (fx(f), AX)], 1.5, G["c5"])
    body += ribbon([(fx(FOCUS), AX - 1), (fx(FOCUS), AX - 6)], 1.5, G["c5"])

    runs = wet_trace()
    # dry ghost: sharp everywhere, a dark hairline dropped by mix; kept at least 8 px under
    # the wet line so the two never touch, and clear of the bracket
    drop = 34 * MIX
    dry = []
    for i in range(0, len(GRID), 8):
        x = fx(GRID[i])
        y = fy(SRC[i]) + drop
        under = lowest_y_near(runs, x)
        if under is not None:
            y = max(y, under + 8)
        dry.append((x, min(y, AX - 12)))
    body += ribbon(dry, 1.0, G["c2"])

    # wet trace: the subject, the one brightest element
    # drawn as one continuous line so the run joins are mitred, not notched
    line = runs[0] + runs[1][1:] + runs[2][1:]
    body += ribbon(line, 2.0, G["c7"])
    return frame(body, "v1 cleaned: P3 trace as subject, typeset diagram")


def main():
    out = HERE / "clean.svg"
    out.write_text(v1_clean())
    print("wrote", out)


if __name__ == "__main__":
    main()
