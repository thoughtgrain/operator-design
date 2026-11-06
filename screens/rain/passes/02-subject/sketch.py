#!/usr/bin/env python3
"""Rain, subject pass 02: five rest-frame sketches from one script.

Five directions from pass.json (angle x way of drawing), none of them the
first pass's roof plans, pulse trains or labelled sections:

    v1  the verge's tile ends at large scale          edge-lit silhouette
    v2  raindrops themselves, size is pitch           detailed line art
    v3  a rainstick, pins are the courses             hidden-line 3D
    v4  pantiles seen close, water in the pans        bold closed outlines
    v5  flowerpots under a dripping eave              cutaway section

    python3 screens/rain/passes/02-subject/sketch.py

Every frame is 480 x 220 with the stock header and the controls at their
defaults (rate 1.0 drops a beat, roof 12 st, gust 0, puddle 0). No text below
the header. Every 3D thing is modelled in world units and projected through
one camera per frame (craft.md, Think in 3D). Lines are closed filled ribbons;
outlines are closed paths; hatching is 45 deg hairlines >= 4 px apart, clipped
to the region in the generator. Grey only, never red.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent

D = {"rate": 0.4, "roof": 1 / 3, "gust": 0.5, "puddle": 0.0}
RATE = 0.25 * 32 ** D["rate"]          # drops per beat: 1.0
SPAN = 36 * D["roof"]                  # semitones: 12
GUST = 2 * D["gust"] - 1               # -1..1: 0
PUDDLE = D["puddle"]                   # 0..1: 0
LABELS = ["rate", "roof", "gust", "puddle"]
VALUES = ["1.0", "12", "0", "0"]

G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
FONT = "UniversNextPro-Light"
SCALE = [0, 2, 4, 5, 7, 9, 11]
HAIR, LINE, SUBJ = 1.0, 1.5, 2.5      # the three weights (craft.md)
TOP = 21.0                             # body starts below the stock header


def f(v: float) -> str:
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def courses(span: float) -> list[int]:
    out, octv = [], 0
    while True:
        for d in SCALE:
            st = 12 * octv + d
            if st > span + 1e-6:
                return out
            out.append(st)
        octv += 1


# ---------------------------------------------------------------- vectors / camera
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def mul(a, k): return (a[0] * k, a[1] * k, a[2] * k)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def norm(a):
    l = math.sqrt(dot(a, a)) or 1.0
    return (a[0] / l, a[1] / l, a[2] / l)


class Camera:
    """A look-at pinhole camera; world y is up. fit() scales and centres it so
    the given key points land in a screen box."""

    def __init__(self, eye, target, focal=1.0, cx=240.0, cy=120.0):
        self.eye = eye
        self.fwd = norm(sub(target, eye))
        self.right = norm(cross(self.fwd, (0, 1, 0)))
        self.up = cross(self.right, self.fwd)
        self.focal, self.cx, self.cy = focal, cx, cy

    def depth(self, p):
        return dot(sub(p, self.eye), self.fwd)

    def __call__(self, p):
        v = sub(p, self.eye)
        z = dot(v, self.fwd)
        return (self.cx + self.focal * dot(v, self.right) / z,
                self.cy - self.focal * dot(v, self.up) / z)

    def fit(self, pts, box):
        x0, y0, x1, y1 = box
        self.focal, self.cx, self.cy = 1.0, 0.0, 0.0
        sp = [self(p) for p in pts]
        sx0, sx1 = min(p[0] for p in sp), max(p[0] for p in sp)
        sy0, sy1 = min(p[1] for p in sp), max(p[1] for p in sp)
        k = min((x1 - x0) / (sx1 - sx0), (y1 - y0) / (sy1 - sy0))
        self.focal = k
        self.cx = (x0 + x1) / 2 - k * (sx0 + sx1) / 2
        self.cy = (y0 + y1) / 2 - k * (sy0 + sy1) / 2
        return self


# ---------------------------------------------------------------- 2D geometry
def dedupe(pts, close=True):
    out = []
    for p in pts:
        p = (round(p[0], 3), round(p[1], 3))
        if not out or math.dist(out[-1], p) >= 0.2:
            out.append(p)
    if close and len(out) > 2 and math.dist(out[0], out[-1]) < 0.3:
        out.pop()
    return out


def clip_poly(pts, x0=0.0, y0=TOP, x1=480.0, y1=220.0):
    """Sutherland-Hodgman against the body rectangle."""
    def clip(poly, inside, cut):
        out = []
        for i in range(len(poly)):
            a, b = poly[i - 1], poly[i]
            ia, ib = inside(a), inside(b)
            if ib:
                if not ia:
                    out.append(cut(a, b))
                out.append(b)
            elif ia:
                out.append(cut(a, b))
        return out

    def cx(v):
        return lambda a, b: (v, a[1] + (b[1] - a[1]) * (v - a[0]) / (b[0] - a[0]))

    def cy(v):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (v - a[1]) / (b[1] - a[1]), v)

    for inside, cut in ((lambda p: p[0] >= x0, cx(x0)), (lambda p: p[0] <= x1, cx(x1)),
                        (lambda p: p[1] >= y0, cy(y0)), (lambda p: p[1] <= y1, cy(y1))):
        if not pts:
            return []
        pts = clip(pts, inside, cut)
    return pts


def seg_in_poly(a, b, poly):
    """Pieces of segment ab inside a simple polygon (even-odd)."""
    ts = [0.0, 1.0]
    for i in range(len(poly)):
        p, q = poly[i - 1], poly[i]
        d1 = (b[0] - a[0], b[1] - a[1])
        d2 = (q[0] - p[0], q[1] - p[1])
        den = d1[0] * d2[1] - d1[1] * d2[0]
        if abs(den) < 1e-9:
            continue
        t = ((p[0] - a[0]) * d2[1] - (p[1] - a[1]) * d2[0]) / den
        u = ((p[0] - a[0]) * d1[1] - (p[1] - a[1]) * d1[0]) / den
        if 0 <= t <= 1 and 0 <= u <= 1:
            ts.append(t)
    ts.sort()
    out = []
    for t0, t1 in zip(ts, ts[1:]):
        m = (t0 + t1) / 2
        pm = (a[0] + (b[0] - a[0]) * m, a[1] + (b[1] - a[1]) * m)
        if t1 - t0 > 1e-6 and point_in(pm, poly):
            out.append(((a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0),
                        (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)))
    return out


def point_in(p, poly):
    c = False
    for i in range(len(poly)):
        a, b = poly[i - 1], poly[i]
        if (a[1] > p[1]) != (b[1] > p[1]):
            x = a[0] + (p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if x > p[0]:
                c = not c
    return c


def ellipse_pts(cx, cy, rx, ry, a0=0.0, a1=2 * math.pi, n=40):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * k / n), cy + ry * math.sin(a0 + (a1 - a0) * k / n))
            for k in range(n + 1)]


def hull(pts):
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in pts))
    if len(pts) < 3:
        return pts

    def half(ps):
        h = []
        for p in ps:
            while len(h) >= 2 and ((h[-1][0] - h[-2][0]) * (p[1] - h[-2][1]) -
                                   (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0])) <= 0:
                h.pop()
            h.append(p)
        return h
    lo, hi = half(pts), half(pts[::-1])
    return lo[:-1] + hi[:-1]


def resample(pts, n):
    """Reduce a polyline to n points (keeps ends)."""
    if len(pts) <= n:
        return pts
    return [pts[round(k * (len(pts) - 1) / (n - 1))] for k in range(n)]


# ---------------------------------------------------------------- frame
class Frame:
    def __init__(self, title: str):
        self.title = title
        self.items: list[str] = []

    def add(self, s):
        self.items.append(s)

    def poly(self, pts, fill, stroke="none", sw=0.0, clip=True):
        pts = dedupe(clip_poly(list(pts)) if clip else list(pts))
        if len(pts) < 3:
            return
        if len(pts) > 64:
            pts = resample(pts, 64)
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        if max(xs) - min(xs) < 3 and max(ys) - min(ys) < 3:
            return
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
        sws = f' stroke-width="{f(sw)}"' if stroke != "none" else ' stroke-width="0"'
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def outline(self, pts, colour, sw, fill=G0):
        """A closed body: black (or given) fill, outline stroke >= 1.5 px."""
        self.poly(pts, fill, colour, sw)

    def ribbon(self, pts, w, colour):
        pts = dedupe(pts, close=False)
        n, i = 26, 0
        while i < len(pts) - 1:
            self._piece(pts[i:i + n + 1], w, colour)
            i += n

    def _piece(self, seg, w, colour):
        if len(seg) < 2:
            return
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
            ln = math.hypot(dx, dy) or 1
            nx, ny = -dy / ln, dx / ln
            left.append((x + nx * h, y + ny * h))
            right.append((x - nx * h, y - ny * h))
        self.poly(left + right[::-1], colour)

    def line(self, a, b, w, colour):
        self._piece([a, b], w, colour)

    def disc(self, cx, cy, r, fill):
        self.add(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}" stroke="none" stroke-width="0"/>')

    def hatch(self, region, colour=G3, gap=4.0, w=HAIR):
        """45 deg hairlines across a closed region, >= gap px apart, clipped to it."""
        xs, ys = [p[0] for p in region], [p[1] for p in region]
        lo, hi = min(xs) + min(ys), max(xs) + max(ys)   # lines x + y = c
        c = lo + gap / 2
        while c < hi:
            a = (c - max(ys) - 2, max(ys) + 2)
            b = (c - min(ys) + 2, min(ys) - 2)
            for p, q in seg_in_poly(a, b, region):
                if math.dist(p, q) >= 3:
                    self.line(p, q, w, colour)
            c += gap * math.sqrt(2)

    def svg(self) -> str:
        head = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
            f"  <title>rain · subject pass 02 · {self.title}</title>",
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
        for i, v in enumerate(VALUES):
            c = "#CBCBCB" if i < 2 else "#000000"
            head.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{c}" stroke="none" '
                        f'font-family="{FONT}" font-size="20px">{v}</text>')
        head.append("  </g>")
        return "\n".join(head + ["  " + s for s in self.items] + ["</svg>", ""])


#@@VARIANTS@@

def main():
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        d = HERE / name
        d.mkdir(exist_ok=True)
        (d / "rest.svg").write_text(fn().svg())
        print(f"wrote {d / 'rest.svg'}")


if __name__ == "__main__":
    main()
