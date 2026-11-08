#!/usr/bin/env python3
"""Ebb v5 (P10 voice field, star atlas): cleanup of the rest sketch.

    python3 screens/ebb/passes/01-subject/v5/clean.py

Writes clean.svg next to this file (render: rsvg-convert -w 480 -h 220 -b black
clean.svg -o clean.png). Same idea and composition as sketch.py's v5: a star
chart of the last 16 s where every scale degree at every moment is a star sized
by how near the tide passes it, the played notes tracing an ecliptic toward the
brightest star, now. Cleanup only: no figures on the chart (the declination and
time labels become ticks on the neat line), the chart is centred now the labels
are gone, stars that would touch a brighter neighbour are left out, and the
ecliptic's dashes are long enough to read. Rule and primitives copied from
../sketch.py.
"""
from __future__ import annotations

import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 480, 220

G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
FONT = "UniversNextPro-Light"

# defaults (definition.json)
TIDE = 12.0                       # semitones, 0.3333 of 0..36
PERIOD = 32 ** 0.6                # 8.0 s, exponential 1..32
FOAM = 0.0
SCALES = {
    "maj": [0, 2, 4, 5, 7, 9, 11],
    "min": [0, 2, 3, 5, 7, 8, 10],
    "dor": [0, 2, 3, 5, 7, 9, 10],
    "lyd": [0, 2, 4, 6, 7, 9, 11],
    "phr": [0, 1, 3, 5, 7, 8, 10],
    "pent": [0, 2, 4, 7, 9],
    "hira": [0, 2, 3, 7, 8],
}
SCALE = SCALES["maj"]
MEAN = 18.0                       # mid register, semitones above the bottom of the 3-octave span
HEADER = [("tide", "12"), ("period", "8.0s"), ("foam", "0"), ("scale", "maj")]


# ----------------------------------------------------------------- the rule
def degrees(scale=SCALE, top=36):
    out = []
    octave = 0
    while True:
        for s in scale:
            p = octave * 12 + s
            if p > top:
                return out
            out.append(p)
        octave += 1


def tide_pitch(t, tide=TIDE, period=PERIOD, phase=0.0):
    return MEAN + tide / 2 * math.sin(2 * math.pi * t / period + phase)


def quantise(p, scale=SCALE):
    ds = degrees(scale)
    return min(ds, key=lambda d: abs(d - p))


# ----------------------------------------------------------------- svg helpers
def f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def dedupe(pts):
    out = []
    for p in pts:
        if not out or math.dist(out[-1], p) >= 0.3:
            out.append(p)
    return out


def poly(pts, fill, stroke="none", sw=None):
    pts = dedupe(pts)
    if len(pts) > 2 and math.dist(pts[0], pts[-1]) < 0.3:
        pts = pts[:-1]
    d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
    s = f'<path d="{d}" fill="{fill}" stroke="{stroke}"'
    if stroke != "none":
        s += f' stroke-width="{sw}"'
    return s + "/>"


def rect(x, y, w, h, fill, stroke="none", sw=None):
    s = f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" fill="{fill}" stroke="{stroke}"'
    if stroke != "none":
        s += f' stroke-width="{sw}"'
    return s + "/>"


def circle(cx, cy, r, fill, stroke="none", sw=None):
    s = f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}" stroke="{stroke}"'
    if stroke != "none":
        s += f' stroke-width="{sw}"'
    return s + "/>"


def text(x, y, s, fill=G4, size=10):
    return (f'<text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{fill}" stroke="none" '
            f'font-family="{FONT}" font-size="{size}px">{s}</text>')


def _ribbon(pts, w):
    """Offset an open polyline both ways and close it: a filled ribbon of width w."""
    n = len(pts)
    left, right = [], []
    for i in range(n):
        if i == 0:
            dx, dy = pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]
            L = math.hypot(dx, dy)
            nx, ny, m = -dy / L, dx / L, 1.0
        elif i == n - 1:
            dx, dy = pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]
            L = math.hypot(dx, dy)
            nx, ny, m = -dy / L, dx / L, 1.0
        else:
            ax, ay = pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]
            bx, by = pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]
            la, lb = math.hypot(ax, ay), math.hypot(bx, by)
            n1 = (-ay / la, ax / la)
            n2 = (-by / lb, bx / lb)
            sx, sy = n1[0] + n2[0], n1[1] + n2[1]
            ls = math.hypot(sx, sy) or 1.0
            nx, ny = sx / ls, sy / ls
            cos = nx * n1[0] + ny * n1[1]
            m = min(1 / max(cos, 0.35), 2.5)
        h = w / 2 * m
        left.append((pts[i][0] + nx * h, pts[i][1] + ny * h))
        right.append((pts[i][0] - nx * h, pts[i][1] - ny * h))
    return left + right[::-1]


def line(pts, w, fill):
    """Open polyline as closed ribbons, chunked so each outline stays <= 62 points."""
    pts = dedupe(pts)
    out = []
    i = 0
    while i < len(pts) - 1:
        chunk = pts[i:i + 30]
        out.append(poly(_ribbon(chunk, w), fill))
        i += 29
    return "\n".join(out)


def seg(x0, y0, x1, y1, w, fill):
    return line([(x0, y0), (x1, y1)], w, fill)


def dashed(pts, w, fill, dash=4.0, gap=4.0):
    """Dashes along a polyline, each its own short ribbon."""
    out, cur, acc, on = [], [pts[0]], 0.0, True
    for a, b in zip(pts, pts[1:]):
        L = math.dist(a, b)
        t = 0.0
        while t < L:
            room = (dash if on else gap) - acc
            step = min(room, L - t)
            t += step
            acc += step
            p = (a[0] + (b[0] - a[0]) * t / L, a[1] + (b[1] - a[1]) * t / L)
            if on:
                cur.append(p)
            if acc >= (dash if on else gap) - 1e-9:
                if on and len(cur) > 1:
                    out.append(line(cur, w, fill))
                on, acc, cur = not on, 0.0, [p]
    if on and len(cur) > 1:
        out.append(line(cur, w, fill))
    return "\n".join(out)


def ellipse_pts(cx, cy, rx, ry, n=48, a0=0.0, a1=2 * math.pi):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / (n - 1 if a1 - a0 < 2 * math.pi else n)),
             cy + ry * math.sin(a0 + (a1 - a0) * i / (n - 1 if a1 - a0 < 2 * math.pi else n))) for i in range(n)]


def convex_hull(pts):
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in pts))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]


def header():
    steps = [G0, G1, G2, G3, G4, G5, G6, G7]
    out = ['<g id="preview_header">']
    for i, c in enumerate(steps):
        out.append(rect(i * 60, 0, 60, 20, c))
    for i, (label, value) in enumerate(HEADER):
        ink = "#CBCBCB" if i < 2 else G0
        out.append(text(5 + 120 * i, 10, label, ink, 10))
        out.append(text(65 + 120 * i, 17.44, value, ink, 20))
    out.append("</g>")
    return "\n".join(out)


def frame(body: list[str], note: str) -> str:
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        f"<!-- ebb, subject pass 01, {note}. Generated by clean.py; defaults, rest, not muted. -->",
        '<g id="preview_canvas">', rect(0, 0, W, H, G0), "</g>",
        header(),
        *body,
        "</svg>",
    ])


# ======================================================== v5 · P10 voice field · star atlas (clean)
def v5():
    b = []
    X0, X1, Y0, Y1 = 28.0, 452.0, 30.0, 200.0
    span = 16.0                            # seconds shown, now at the right
    py = (Y1 - Y0 - 10) / 36               # px per semitone

    def sx(t):
        return X0 + (t + span) / span * (X1 - X0 - 12)

    def syp(p):
        return Y1 - 5 - p * py

    # Neat line (Hairline, ground grey) and graticule (every 2 s, every octave) in the lowest grey.
    for a, c in (((X0, Y0), (X1, Y0)), ((X1, Y0), (X1, Y1)), ((X1, Y1), (X0, Y1)), ((X0, Y1), (X0, Y0))):
        b.append(seg(*a, *c, 1, G2))
    for s in range(-14, 1, 2):
        b.append(seg(sx(s), Y0 + 1, sx(s), Y1 - 1, 1, G1))
    for p in (12, 24):
        b.append(seg(X0 + 1, syp(p), X1 - 1, syp(p), 1, G1))
    # Atlas border ticks in place of figures, outside the neat line: the sketch's -16 s and -8 s
    # labels become Hairline ticks, "now" a longer Line-weight tick, and +0..+36 a tick per octave.
    for s in (-16, -8):
        b.append(seg(sx(s), Y1 + 0.5, sx(s), Y1 + 5, 1, G3))
    b.append(seg(sx(0), Y1 + 0.5, sx(0), Y1 + 7, 1.5, G4))
    for p in (0, 12, 24, 36):
        b.append(seg(X0 - 5, syp(p), X0 - 0.5, syp(p), 1, G3))

    # Ecliptic: the tide's own path, dashed at Hairline (5 px dashes, 4 px gaps).
    path = [(sx(t / 10), syp(tide_pitch(t / 10))) for t in range(-160, 1)]
    b.append(dashed(path, 1, G3, 5, 4))

    # The field: one star per (column, degree), magnitude from distance to the tide. Within a
    # column the brighter star wins: a fainter one that would come within 2 px of it is left out.
    cols = 40
    ds = degrees()
    now = (sx(0.0), syp(quantise(tide_pitch(0.0))), 3.5)
    for i in range(cols):
        t = -span + (i + 0.5) * span / cols
        p = tide_pitch(t)
        cand = sorted(((2.8 - abs(p - d) * 0.75, d) for d in ds), reverse=True)
        kept = []
        for r, d in cand:
            if r < 1.5:
                break
            y = syp(d)
            if all(abs(y - ky) - r - kr >= 2.0 for ky, kr in kept):
                kept.append((y, r))
        for y, r in kept:
            if math.dist((sx(t), y), now[:2]) - r - now[2] >= 2.0:
                b.append(circle(sx(t), y, r, G5))
    # The present: the one brightest star.
    b.append(circle(*now, G7))
    return frame(b, "v5 P10 voice field, star atlas, clean")


def main():
    (HERE / "clean.svg").write_text(v5() + "\n", encoding="utf-8")
    print(HERE / "clean.svg")


if __name__ == "__main__":
    main()
