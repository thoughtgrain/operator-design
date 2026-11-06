#!/usr/bin/env python3
"""Relay, subject pass 01: five rest-frame sketches from one script.

Relay is a bucket-brigade delay with failing stages. Each variant is a different
pattern x drawing language (see pass.json). Every frame is 480 x 220, keeps the
stock header, and draws the controls at their defaults:

    stages 0.5 -> 1000 stages, 100 ms   leak 0   clock 0   feedback 0.35

An effect page gets its controls, not the audio, so every variant draws the
delay's answer to a notional test note (its impulse response through the chain),
not a live signal.

    python3 screens/relay/passes/01-subject/sketch.py

Device rules kept even at sketch stage: one subpath per path, <= 64 points,
lines as closed filled ribbons (no open strokes), explicit paint on every leaf,
grey only, <= 4 fractional digits.
"""
from __future__ import annotations

import math
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent

D = {"stages": 0.5, "leak": 0.0, "clock": 0.0, "feedback": 0.35}
LABELS = ["stages", "leak", "clock", "feedback"]
HEADER_VALUES = ["100ms", "0", "0.00", "35"]

G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
FONT = "UniversNextPro-Light"


def f(v: float) -> str:
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# ---------------------------------------------------------------- primitives
def dedupe(pts):
    out = []
    for p in pts:
        p = (round(p[0], 3), round(p[1], 3))
        if not out or math.dist(out[-1], p) >= 0.25:
            out.append(p)
    if len(out) > 2 and math.dist(out[0], out[-1]) < 0.3:
        out.pop()
    return out


class Frame:
    def __init__(self, title: str):
        self.title = title
        self.items: list[str] = []

    def add(self, s: str) -> None:
        self.items.append(s)

    def poly(self, pts, fill, stroke="none", sw=0.0):
        pts = dedupe(pts)
        assert 3 <= len(pts) <= 64, len(pts)
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
        sws = f' stroke-width="{f(sw)}"' if stroke != "none" else ' stroke-width="0"'
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def loop(self, pts, colour, sw, fill=G0):
        """A closed outline: a stroked closed path (<= 64 points)."""
        self.poly(pts, fill, colour, sw)

    def ribbon(self, pts, w, colour):
        """An open line of width w drawn as filled closed ribbons, <= 30 points a piece."""
        pts = dedupe(pts)
        n, i = 30, 0
        while i < len(pts) - 1:
            self._piece(pts[i:i + n + 1], w, colour)
            i += n

    def _piece(self, seg, w, colour):
        h = w / 2
        left, right = [], []
        for k, (x, y) in enumerate(seg):
            if k == 0:
                dx, dy = seg[1][0] - x, seg[1][1] - y
            elif k == len(seg) - 1:
                dx, dy = x - seg[k - 1][0], y - seg[k - 1][1]
            else:
                ax, ay = x - seg[k - 1][0], y - seg[k - 1][1]
                bx, by = seg[k + 1][0] - x, seg[k + 1][1] - y
                la, lb = math.hypot(ax, ay) or 1, math.hypot(bx, by) or 1
                dx, dy = ax / la + bx / lb, ay / la + by / lb
                if math.hypot(dx, dy) < 1e-6:
                    dx, dy = ax, ay
            ln = math.hypot(dx, dy) or 1
            nx, ny = -dy / ln, dx / ln
            left.append((x + nx * h, y + ny * h))
            right.append((x - nx * h, y - ny * h))
        self.poly(left + right[::-1], colour)

    def line(self, a, b, w, colour):
        self._piece([a, b], w, colour)

    def rect(self, x, y, w, h, fill, stroke="none", sw=0.0):
        sws = f' stroke-width="{f(sw)}"' if stroke != "none" else ' stroke-width="0"'
        self.add(f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def circle(self, cx, cy, r, fill, stroke="none", sw=0.0):
        sws = f' stroke-width="{f(sw)}"' if stroke != "none" else ' stroke-width="0"'
        self.add(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def text(self, x, y, s, colour=G4, size=10):
        self.add(f'<text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{colour}" stroke="none" '
                 f'stroke-width="0" font-family="{FONT}" font-size="{size}px">{s}</text>')

    def svg(self) -> str:
        head = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
            f"  <title>relay · subject pass 01 · {self.title}</title>",
            '  <g id="preview_canvas">',
            '    <rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>',
            "  </g>",
            '  <g id="preview_header">',
        ]
        for i, c in enumerate([G0, G1, G2, G3, G4, G5, G6, G7]):
            head.append(f'    <rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
        for i, lab in enumerate(LABELS):
            c = "#CBCBCB" if i < 2 else "#000000"
            head.append(f'    <text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{c}" stroke="none" '
                        f'font-family="{FONT}" font-size="10px">{lab}</text>')
            head.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{c}" stroke="none" '
                        f'font-family="{FONT}" font-size="20px">{HEADER_VALUES[i]}</text>')
        head.append("  </g>")
        return "\n".join(head + ["  " + s for s in self.items] + ["</svg>", ""])


def arc(cx, cy, rx, ry, a0, a1, n):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * k / n), cy + ry * math.sin(a0 + (a1 - a0) * k / n))
            for k in range(n + 1)]


def rot(p, c, a):
    s, co = math.sin(a), math.cos(a)
    x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * co - y * s, c[1] + x * s + y * co)


def clip_below(poly, y):
    """Part of a convex-ish polygon at or below the horizontal y (screen y grows down)."""
    out = []
    for i, a in enumerate(poly):
        b = poly[(i + 1) % len(poly)]
        ina, inb = a[1] >= y, b[1] >= y
        if ina:
            out.append(a)
        if ina != inb:
            t = (y - a[1]) / (b[1] - a[1])
            out.append((a[0] + t * (b[0] - a[0]), y))
    return out


def area(poly):
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))) / 2


# ---------------------------------------------------------------- the model
# One small model shared by every variant, so the drawings agree.
# stages: 100..10000 buckets at a nominal 0.1 ms a bucket -> 10 ms .. 1 s.
STAGES = 100 * 100 ** D["stages"]                    # 1000 at the default
DELAY = STAGES * 1e-4                                # seconds
FB = D["feedback"]


def passes(fb=FB, cap=6):
    """How many trips through the chain stay above ~-28 dB: the visible echoes."""
    if fb <= 0:
        return 1
    return max(1, min(cap, 1 + int(math.log(0.04) / math.log(fb))))


def level(k, fb=FB):
    """Pass k's level, drawn on a dB scale (what's heard), 0..1."""
    if k == 0:
        return 1.0
    a = fb ** k
    return max(0.0, 1 + 20 * math.log10(max(a, 1e-6)) / 36)


def burst(u):
    """The notional test note: a plucked tone, u in 0..1 across its length."""
    if u < 0 or u > 1:
        return 0.0
    env = (1 - math.exp(-u * 14)) * math.exp(-u * 2.6)
    return env * math.sin(2 * math.pi * 4.5 * u)


def envelope(u):
    if u < 0 or u > 1:
        return 0.0
    return (1 - math.exp(-u * 14)) * math.exp(-u * 2.6) / 0.62


# ---------------------------------------------------------------- v1
def v1() -> Frame:
    """P4 Stack in depth, oscilloscope trace: each pass through the chain a scope sweep."""
    F = Frame("v1 · P4 stack in depth · oscilloscope trace")
    n = passes()
    W, H = 300, 52
    greys = [G7, G5, G4, G3, G2, G2]
    for k in reversed(range(n)):
        ox, oy = 30 + 28 * k, 152 - 30 * k
        base = oy + H / 2
        # the sweep's screen: black body (hidden line) with a dark graticule edge
        F.rect(ox, oy, W, H, G0, G1, 1.0)
        F.line((ox + 8, base), (ox + W - 8, base), 1.0, G2)
        for t in range(1, 10):
            x = ox + t * 30
            F.line((x, base - 3), (x, base + 3), 1.0, G2)
        # dry mark: where the note entered the chain
        F.line((ox + 14, base - 9), (ox + 14, base + 9), 1.0, G3)
        # the echo burst, where the stage count puts it on the sweep (log time)
        xb = ox + 34 + 200 * D["stages"]
        A = 22 * level(k)
        pts = [(ox + 8 + 0.01, base)]
        pts += [(xb - 6, base)]
        for i in range(0, 49):
            u = i / 48
            pts.append((xb + 66 * u, base - A * burst(u)))
        pts.append((ox + W - 8, base))
        F.ribbon(pts, 2.0 if k == 0 else 1.5, greys[k])
        F.text(ox + W + 6, base + 4, f"pass {k + 1}", G4 if k else G5)
    # sweep scale under the front screen
    F.text(30 + 34 + 200 * D["stages"] - 14, 216, "1000 stages", G4)
    return F


# ---------------------------------------------------------------- v2
def v2() -> Frame:
    """P10 Voice field, typeset diagram: the chain coiled into a spiral of bucket bars."""
    F = Frame("v2 · P10 voice field · typeset diagram")
    cx, cy = 240, 122
    R0, pitch, bar_max = 84, 14, 9
    turns = min(4, passes())
    N = round(24 + 48 * D["stages"])                  # buckets drawn per trip
    jb = round(N * 0.30)                              # where the test note sits in the chain
    span = max(6, round(N * 0.22))
    greys = [G7, G5, G4, G3]
    # the spiral the bars stand on, hairline
    guide = []
    for i in range(turns * 64 + 1):
        th = 2 * math.pi * i / 64
        r = R0 - pitch * th / (2 * math.pi)
        guide.append((cx + r * math.cos(th - math.pi / 2), cy + r * math.sin(th - math.pi / 2)))
    F.ribbon(guide, 1.0, G1)
    for k in range(turns):
        for j in range(N):
            th = 2 * math.pi * j / N
            r = R0 - pitch * (k + j / N)
            u = (j - jb) / span
            charge = abs(burst(u)) / 0.62
            ln = 4.0 + bar_max * level(k) * charge
            a = th - math.pi / 2
            p0 = (cx + r * math.cos(a), cy + r * math.sin(a))
            p1 = (cx + (r + ln) * math.cos(a), cy + (r + ln) * math.sin(a))
            F.line(p0, p1, 2.0 if k == 0 else 1.5, greys[k] if charge > 0.05 else G2)
    # typeset keys: in / out, the pass numerals in the gaps at nine o'clock, a caption
    F.text(cx - 22, cy - R0 + 4, "in", G5)
    r_end = R0 - pitch * turns
    F.text(cx - 8, cy - r_end + 16, "out", G4)
    for k in range(turns):
        r = R0 - pitch * (k + 0.75)
        F.text(cx - r - 12.5, cy + 4, str(k + 1), G5 if k == 0 else G4)
    F.text(28, 206, f"{N} of 1000 buckets", G4)
    F.text(28, 192, "fig. 1", G4)
    return F


# ---------------------------------------------------------------- v3
def v3() -> Frame:
    """P15 Cell field, orthographic elevation: a wall of bucket compartments seen face on."""
    F = Frame("v3 · P15 cell field · orthographic elevation")
    cols, rows, cell, top = 24, 9, 20, 28
    window = 2.0                                      # seconds of history the wall holds
    dt = window / (cols * rows)
    note = 0.028                                      # a test note fills a run of 3-4 compartments
    n = passes()
    # a steady test phrase (fixed, seeded): note starts and their levels
    phrase = [(0.0, 1.0), (0.29, 0.8), (0.47, 0.9), (0.83, 1.0), (1.05, 0.7), (1.31, 0.95), (1.62, 0.8), (1.79, 1.0)]
    bias = 0.3                                        # a BBD's buckets always hold a bias charge
    for idx in range(cols * rows):
        r, c = divmod(idx, cols)
        if r % 2:
            c = cols - 1 - c                          # the chain runs back and forth along the wall
        t0, t1 = idx * dt, (idx + 1) * dt
        sig = 0.0
        for start, amp in phrase:
            for k in range(n):
                for t in (t0, (t0 + t1) / 2, t1):
                    sig = max(sig, amp * level(k) * envelope((t - start - (k + 1) * DELAY) / note))
        x, y = c * cell, top + r * cell
        if sig < 0.12:
            # standing bias: the compartment's floor charge, a dark ground body
            F.rect(x + 2, y + cell - 2 - 6, cell - 4, 6, G1)
            continue
        lv = bias + (1 - bias) * min(1.0, sig)
        h = round(16 * lv)
        col = G7 if sig > 0.66 else (G5 if sig > 0.4 else G3)
        F.rect(x + 2, y + cell - 2 - h, cell - 4, h, col)
    # ground line of the elevation
    F.line((0, top + rows * cell + 1), (480, top + rows * cell + 1), 1.5, G2)
    return F


# ---------------------------------------------------------------- v4
def v4() -> Frame:
    """P1 Section drawing, survey plan: the chip's charge wells cut open as a long-section."""
    F = Frame("v4 · P1 section drawing · survey plan")
    n = round(8 + 16 * D["stages"])                   # wells shown along the section
    x0, x1 = 44, 436
    p = (x1 - x0) / n
    ridge, floor = 62, 112
    # gates above each well (the clock's electrodes)
    for i in range(n):
        gx = x0 + i * p
        F.rect(gx + 7, 40, p - 9, 6, G0, G3, 1.0)
    # pools first (dark bodies) so the profile line sits on top
    jb, span = n * 0.30, n * 0.45
    for i in range(n):
        gx = x0 + i * p
        u = (i + 0.5 - jb) / span
        lv = 0.5 + 0.42 * (burst(u) / 0.62)
        ys = floor - (floor - ridge - 6) * lv
        cav = [(gx + 4, ridge), (gx + 8.5, floor), (gx + p - 3.5, floor), (gx + p, ridge)]
        pool = clip_below(cav, ys)
        F.poly(pool, G1)
        xs = [q[0] for q in pool if abs(q[1] - ys) < 1e-6]
        F.line((min(xs) + 0.6, ys), (max(xs) - 0.6, ys), 2.0, G7)
    # the potential profile, cut through the channel: ridges are barriers, troughs hold charge
    prof = [(x0 - 18, ridge)]
    for i in range(n):
        gx = x0 + i * p
        prof += [(gx, ridge), (gx + 4, ridge), (gx + 8.5, floor), (gx + p - 3.5, floor)]
    prof += [(x1, ridge), (x1 + 18, ridge)]
    F.ribbon(prof, 1.5, G5)
    # datum and chainage
    dy = 128
    F.line((x0 - 18, dy), (x1 + 18, dy), 1.0, G2)
    for q in range(5):
        x = x0 + (x1 - x0) * q / 4
        F.line((x, dy - 4), (x, dy + 4), 1.0, G3)
        s = str(250 * q)
        F.text(x - 3.2 * len(s), dy + 16, s, G4)
    F.text(x0 - 40, dy + 4, "ch", G4)
    # return leg below the datum: invert line and the hydraulic grade line (feedback)
    inv = 204
    F.ribbon([(x1 + 10, ridge + 6), (x1 + 10, inv), (x0 - 10, inv), (x0 - 10, ridge + 6)], 1.5, G3)
    yo = inv - 4 - 52 * FB
    F.line((x1 + 10, yo), (x0 - 10, yo + 6), 1.5, G5)
    F.text(x0 + 8, yo + 2, "hgl", G4)
    F.text(x0 - 34, 58, "in", G4)
    F.text(x1 + 16, 58, "out", G4)
    F.text(x1 - 50, inv - 6, "return", G4)
    return F


# ---------------------------------------------------------------- v5
def bucket_shapes(pivot, tilt):
    """A bucket in section: wall (closed U ribbon) and its cavity, hung on an axle at pivot."""
    px, py = pivot
    top, bot = py - 8, py + 20
    wo, wb = 17, 11                                   # half widths at rim and base (outer)
    t = 2.5
    outer = [(px - wo, top), (px - wb, bot), (px + wb, bot), (px + wo, top)]
    inner = [(px + wo - t, top), (px + wb - t * 0.8, bot - t), (px - wb + t * 0.8, bot - t), (px - wo + t, top)]
    wall = outer + inner
    cav = inner[::-1]
    wall = [rot(q, pivot, tilt) for q in wall]
    cav = [rot(q, pivot, tilt) for q in cav]
    return wall, cav


def water(cav, frac):
    lo, hi = min(q[1] for q in cav), max(q[1] for q in cav)
    full = area(cav)
    a, b = lo, hi
    for _ in range(40):
        m = (a + b) / 2
        part = clip_below(cav, m)
        if len(part) >= 3 and area(part) > frac * full:
            a = m
        else:
            b = m
    return clip_below(cav, (a + b) / 2), (a + b) / 2


def v5() -> Frame:
    """P11 Instrument stack (stretch), patent section: a cascade of tipping buckets."""
    F = Frame("v5 · P11 instrument stack · patent section")
    nb = round(4 + 6 * D["stages"])                   # buckets in the cascade
    a, b = (64, 64), (372, 156)
    pivots = [(a[0] + (b[0] - a[0]) * i / (nb - 1), a[1] + (b[1] - a[1]) * i / (nb - 1)) for i in range(nb)]
    ip = 2                                            # the bucket carrying the test note
    # frame beam above the axles, with hangers
    off = 26
    slope = (b[1] - a[1]) / (b[0] - a[0])
    F.ribbon([(a[0] + 10, a[1] - off + slope * 10), (b[0] + 18, b[1] - off + slope * 18)], 1.5, G3)
    slope = (b[1] - a[1]) / (b[0] - a[0])
    for (px, py) in pivots:
        F.line((px, py - off + 0.6), (px, py - 3), 1.0, G3)
    # return riser (feedback): basin at the foot, riser up the right edge, back over the top
    bx0, bx1, by0, by1 = 392, 452, 186, 206
    F.loop([(bx0, by0), (bx0 + 4, by1), (bx1 - 4, by1), (bx1, by0), (bx1 - 2, by0), (bx1 - 5.5, by1 - 2),
            (bx0 + 5.5, by1 - 2), (bx0 + 2, by0)], G4, 1.0, G0)
    F.poly([(bx0 + 3.2, by0 + 8), (bx0 + 5.2, by1 - 2.5), (bx1 - 5.2, by1 - 2.5), (bx1 - 3.2, by0 + 8)], G1)
    rx = 462
    top_y = 27
    F.ribbon([(bx1 - 2, by1 - 4), (rx, by1 - 4), (rx, top_y), (a[0] - 4, top_y), (a[0] - 4, a[1] - 12)], 1.5, G3)
    F.ribbon([(rx - 6, by1 - 10), (rx - 6, top_y + 6), (a[0] + 2, top_y + 6), (a[0] + 2, a[1] - 14)], 1.0, G2)
    col = by1 - 10 - (by1 - 10 - top_y - 6) * FB     # water column in the riser
    F.rect(rx - 4.5, col, 3, by1 - 10 - col, G2)
    F.line((rx - 6, col), (rx, col), 1.5, G5)
    # buckets: wall in section, axle, water held level
    for i, pv in enumerate(pivots):
        tilt = math.radians(38) if i == ip else 0.0
        wall, cav = bucket_shapes(pv, tilt)
        frac = 0.82 if i == ip else 0.5
        pool, ys = water(cav, frac)
        F.poly(pool, G1)
        xs = [q[0] for q in pool if abs(q[1] - ys) < 1e-6]
        F.line((min(xs) + 0.8, ys), (max(xs) - 0.8, ys), 2.0 if i == ip else 1.5, G7 if i == ip else G5)
        F.loop(wall, G7 if i == ip else G5, 1.5 if i == ip else 1.2, G0)
        F.circle(pv[0], pv[1], 2.5, G0, G6, 1.0)
    # the pour from the tipped bucket into the next: a falling ribbon
    wall, cav = bucket_shapes(pivots[ip], math.radians(38))
    lip = max(wall, key=lambda q: q[0] - q[1] * 0.2)
    nx, ny = pivots[ip + 1]
    fall = [(lip[0] + 1, lip[1] + 1)] + [(lip[0] + 3 + 6 * s ** 0.6, lip[1] + 2 + (ny - 10 - lip[1]) * s)
                                         for s in (0.25, 0.5, 0.75, 1.0)]
    F.ribbon(fall, 2.0, G7)
    # reference numerals with leaders, patent style
    def ref(num, tx, ty, to):
        F.line((tx + 12, ty - 4), to, 1.0, G3)
        F.text(tx - 2, ty, num, G4)
    p3 = pivots[3]
    ref("10", p3[0] - 70, p3[1] + 62, (p3[0] - 10, p3[1] + 20))
    ref("12", pivots[1][0] - 52, pivots[1][1] + 66, (pivots[1][0] - 3, pivots[1][1] + 3))
    ref("14", 250, 62, (232, a[1] - off + slope * (232 - a[0]) - 1)) if False else None
    F.line((236, a[1] - off + slope * (236 - a[0]) - 2), (246, 50), 1.0, G3)
    F.text(249, 52, "14", G4)
    ref("16", rx - 52, 120, (rx - 7, 120))
    ref("18", bx0 - 40, by1 + 2, (bx0 + 1, by0 + 10))
    F.text(30, 210, "fig. 1", G4)
    return F


# ---------------------------------------------------------------- build
def main() -> None:
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        out = HERE / name
        out.mkdir(exist_ok=True)
        svg = out / "rest.svg"
        svg.write_text(fn().svg())
        try:
            subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", "-b", "black", str(svg),
                            "-o", str(out / "rest.png")], check=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            print(f"{name}: no png ({exc})")
        print(svg)


if __name__ == "__main__":
    main()
