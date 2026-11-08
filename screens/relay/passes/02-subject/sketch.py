#!/usr/bin/env python3
"""Relay, subject pass 02: five rest-frame sketches from one script.

Relay is a bucket-brigade delay with failing stages: some buckets leak, the clock
wanders, feedback recirculates. Pass 01 (scope sweeps, a bar spiral, a cell wall,
a well long-section, tipping buckets) was turned down; these five start again from
what the machine is and does, one direction each (pass.json):

    v1  the material the sound acts on, seen close     exploded view
    v2  one scene where this happens, one subject       single-weight contour
    v3  the machine's rule on a real object             hatched mass
    v4  a cutaway of the object at work                 edge-lit silhouette
    v5  the mark the process leaves behind              detailed line art

Every frame is 480 x 220, keeps the stock header, and draws the controls at their
defaults (stages 0.5 -> 1000 stages / 100 ms, leak 0, clock 0, feedback 0.35).
An effect page gets its controls, not the audio, so each variant shows a notional
test note, not what's playing.

Every 3D thing is modelled in world units and projected through one camera per
variant (craft.md, Think in 3D). No text below the header: the drawing carries no
labels, numbers or captions. States are line weight, brightness, movement or 45°
hatching, never a lighter grey fill.

    python3 screens/relay/passes/02-subject/sketch.py

Device rules kept even at sketch stage: one subpath per path, <= 64 points, open
lines as closed filled ribbons, explicit paint on every leaf, grey only (never red),
<= 4 fractional digits.
"""
from __future__ import annotations

import math
import random
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Controls at their defaults (definition.json), 0..1 each.
D = {"stages": 0.5, "leak": 0.0, "clock": 0.0, "feedback": 0.35}
LABELS = ["stages", "leak", "clock", "feedback"]
HEADER_VALUES = ["100ms", "0", "0.00", "35"]

G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
FONT = "UniversNextPro-Light"
HAIR, LINE, SUBJ = 1.0, 1.5, 2.0          # the three weights (craft.md)


def f(v: float) -> str:
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def passes(fb: float, floor: float = 0.06, cap: int = 6) -> list[float]:
    """Level of each trip round the chain: 1, fb, fb^2 ... while still audible."""
    out, a = [], 1.0
    while a >= floor and len(out) < cap:
        out.append(a)
        a *= fb * 0.89  # ~1 dB insertion loss per pass
    return out


# ---------------------------------------------------------------- 2D primitives
def dedupe(pts):
    out = []
    for p in pts:
        p = (round(p[0], 3), round(p[1], 3))
        if not out or math.dist(out[-1], p) >= 0.25:
            out.append(p)
    if len(out) > 2 and math.dist(out[0], out[-1]) < 0.3:
        out.pop()
    return out


def clip_poly(subject, clipper):
    """Sutherland-Hodgman: subject clipped by a convex clipper (both screen polys)."""
    def inside(p, a, b, s):
        return s * ((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])) >= 0

    def inter(p, q, a, b):
        x1, y1, x2, y2 = p[0], p[1], q[0], q[1]
        x3, y3, x4, y4 = a[0], a[1], b[0], b[1]
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(den) < 1e-9:
            return q
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))

    s = 1 if signed_area(clipper) > 0 else -1
    out = list(subject)
    for i in range(len(clipper)):
        a, b = clipper[i], clipper[(i + 1) % len(clipper)]
        inp, out = out, []
        if not inp:
            break
        for j in range(len(inp)):
            p, q = inp[j - 1], inp[j]
            if inside(q, a, b, s):
                if not inside(p, a, b, s):
                    out.append(inter(p, q, a, b))
                out.append(q)
            elif inside(p, a, b, s):
                out.append(inter(p, q, a, b))
    return out


def signed_area(poly):
    return 0.5 * sum(poly[i - 1][0] * poly[i][1] - poly[i][0] * poly[i - 1][1] for i in range(len(poly)))


class Frame:
    def __init__(self, title: str):
        self.title = title
        self.items: list[str] = []

    def add(self, s: str) -> None:
        self.items.append(s)

    def poly(self, pts, fill, stroke="none", sw=0.0):
        pts = dedupe(pts)
        if len(pts) < 3:
            return
        assert len(pts) <= 64, len(pts)
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
        sws = f' stroke-width="{f(sw)}"' if stroke != "none" else ' stroke-width="0"'
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def face(self, pts, colour, sw=LINE, fill=G0):
        """A closed outline over a black body (hidden-line)."""
        self.poly(pts, fill, colour, sw)

    def ribbon(self, pts, w, colour):
        """An open line of width w drawn as filled closed ribbons, <= 30 points a piece."""
        pts = dedupe(pts)
        if len(pts) < 2:
            return
        n, i = 30, 0
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
                if math.hypot(dx, dy) < 1e-6:
                    dx, dy = ax, ay
            ln = math.hypot(dx, dy) or 1
            nx, ny = -dy / ln, dx / ln
            left.append((x + nx * h, y + ny * h))
            right.append((x - nx * h, y - ny * h))
        self.poly(left + right[::-1], colour)

    def line(self, a, b, w, colour):
        if math.dist(a, b) >= 3.0:  # anything shorter doesn't read at 1:1
            self._piece([a, b], w, colour)

    def dashed(self, pts, w, colour, on=4.0, off=3.0):
        """A dashed open line: dashes as separate ribbons, each >= 3 px long."""
        pts = dedupe(pts)
        acc, draw, cur = 0.0, True, [pts[0]] if pts else []
        for a, b in zip(pts, pts[1:]):
            seg = math.dist(a, b)
            t = 0.0
            while t < seg:
                lim = on if draw else off
                step = min(lim - acc, seg - t)
                t += step
                acc += step
                p = (a[0] + (b[0] - a[0]) * t / seg, a[1] + (b[1] - a[1]) * t / seg)
                if draw:
                    cur.append(p)
                if acc >= lim - 1e-9:
                    if draw and len(cur) > 1:
                        self.ribbon(cur, w, colour)
                    draw, acc, cur = not draw, 0.0, [p]
        if draw and len(cur) > 1 and acc >= 3:
            self.ribbon(cur, w, colour)

    def hatch(self, poly, colour=G3, gap=4.0, w=HAIR, minlen=4.0):
        """45° hairlines clipped to a polygon (any simple shape), gap px apart."""
        poly = dedupe(poly)
        if len(poly) < 3:
            return
        us = [x + y for x, y in poly]
        step = gap * math.sqrt(2)
        c = math.floor(min(us) / step) * step + step / 2
        while c < max(us):
            hits = []
            for i in range(len(poly)):
                (x1, y1), (x2, y2) = poly[i - 1], poly[i]
                u1, u2 = x1 + y1, x2 + y2
                if (u1 - c) * (u2 - c) < 0:
                    t = (c - u1) / (u2 - u1)
                    hits.append((x1 + t * (x2 - x1), y1 + t * (y2 - y1)))
            hits.sort(key=lambda p: p[0] - p[1])
            for a, b in zip(hits[0::2], hits[1::2]):
                if math.dist(a, b) >= minlen:
                    self.line(a, b, w, colour)
            c += step

    def svg(self) -> str:
        head = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
            f"  <title>relay · subject pass 02 · {self.title}</title>",
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


# ---------------------------------------------------------------- 3D: one camera
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def add3(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def mul(a, k): return (a[0] * k, a[1] * k, a[2] * k)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    ln = math.sqrt(dot(a, a)) or 1.0
    return mul(a, 1 / ln)


class Camera:
    """Perspective camera, z up. Fit it to a set of world points and a screen box."""

    def __init__(self, eye, target, up=(0, 0, 1)):
        self.eye = eye
        self.fwd = norm(sub(target, eye))
        self.right = norm(cross(self.fwd, up))
        self.up = cross(self.right, self.fwd)
        self.f, self.cx, self.cy = 1.0, 0.0, 0.0

    def raw(self, p):
        d = sub(p, self.eye)
        z = dot(d, self.fwd)
        return dot(d, self.right) / z, -dot(d, self.up) / z

    def fit(self, pts, box):
        """Scale and shift so the key points fill box = (x0, y0, x1, y1), centred."""
        r = [self.raw(p) for p in pts]
        xs, ys = [p[0] for p in r], [p[1] for p in r]
        bw, bh = max(xs) - min(xs), max(ys) - min(ys)
        x0, y0, x1, y1 = box
        self.f = min((x1 - x0) / bw, (y1 - y0) / bh)
        self.cx = (x0 + x1) / 2 - self.f * (min(xs) + max(xs)) / 2
        self.cy = (y0 + y1) / 2 - self.f * (min(ys) + max(ys)) / 2
        return self

    def p(self, P):
        x, y = self.raw(P)
        return (self.cx + self.f * x, self.cy + self.f * y)

    def ps(self, pts):
        return [self.p(P) for P in pts]

    def depth(self, P):
        return dot(sub(P, self.eye), self.fwd)


def box_corners(o, ux, uy, uz):
    """Eight corners of a box from origin o along edge vectors ux, uy, uz."""
    c = {}
    for i in (0, 1):
        for j in (0, 1):
            for k in (0, 1):
                c[i, j, k] = add3(add3(add3(o, mul(ux, i)), mul(uy, j)), mul(uz, k))
    return c


BOX_FACES = {  # name: corner keys, outward normal sign/axis
    "x0": [(0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)],
    "x1": [(1, 0, 0), (1, 0, 1), (1, 1, 1), (1, 1, 0)],
    "y0": [(0, 0, 0), (0, 0, 1), (1, 0, 1), (1, 0, 0)],
    "y1": [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)],
    "z0": [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)],
    "z1": [(0, 0, 1), (0, 1, 1), (1, 1, 1), (1, 0, 1)],
}


def visible_faces(cam, c):
    """Faces of a box (corners c) that face the camera, as (name, world pts, screen pts)."""
    centre = mul(add3(c[0, 0, 0], c[1, 1, 1]), 0.5)
    out = []
    for name, keys in BOX_FACES.items():
        W = [c[k] for k in keys]
        n = cross(sub(W[1], W[0]), sub(W[3], W[0]))
        fc = mul(add3(W[0], W[2]), 0.5)
        if dot(n, sub(fc, centre)) < 0:
            n = mul(n, -1)
        if dot(n, sub(cam.eye, fc)) > 0:
            out.append((name, W, cam.ps(W)))
    return out


def circle3(c, r, n=48, a0=0.0, a1=2 * math.pi, axis="z"):
    pts = []
    for k in range(n + 1):
        a = a0 + (a1 - a0) * k / n
        if axis == "z":
            pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a), c[2]))
        elif axis == "x":
            pts.append((c[0], c[1] + r * math.cos(a), c[2] + r * math.sin(a)))
    return pts


# ================================================================= v1
def v1() -> Frame:
    """Exploded view of the held charge: a stretch of the chain's buckets drawn as thin
    capacitor plates pulled apart along the line they sit on, each plate as tall as the
    charge it holds (the bias plus the note), the note and its recirculations riding
    down the row."""
    fr = Frame("v1 · the held charge, exploded")
    st, lk, ck, fb = D["stages"], D["leak"], D["clock"], D["feedback"]
    rnd = random.Random(7)

    n = 30                                   # plates in view: a window on the chain
    gap = 5.0 * (6.0 ** st)                  # plates from one pass to the next: 5 (10 ms) .. 30 (1 s)
    lv = [math.sqrt(a) for a in passes(fb)]  # drawn on a sqrt scale so quiet passes still read
    pitch, thick, deep = 3.0, 0.4, 5.5
    bias, swing = 6.0, 6.0
    xs, x = [], 0.0
    for i in range(n):                       # clock: plates drift off their even pitch
        xs.append(x)
        x += pitch * (1 + ck * 0.8 * (rnd.random() - 0.5) * 2)
    leaky = {i for i in range(n) if rnd.random() < lk * 0.45}

    def sig(i):
        v = 0.0
        for k, a in enumerate(lv):
            u = i - (1 + k * gap)
            if 0 <= u < 9:
                v += a * math.sin(u * 1.4 + 0.5) * math.exp(-u / 4.0)
        return v

    mid = xs[-1] * 0.5
    cam = Camera(eye=(mid - 95, -100, 50), target=(mid + 4, deep / 2, bias))
    key = [(xs[0], 0, 0), (xs[-1], deep, 0), (xs[0], 0, bias + swing), (xs[-1], deep, bias + swing),
           (xs[0] - 6, 0, 0), (xs[-1], deep, -1)]
    cam.fit(key, (22, 40, 458, 206))

    # the assembly axis the plates were pulled apart along: hairline, drawn first so
    # each plate hides its own stretch of it
    fr.dashed([cam.p((xs[0] - 7, deep / 2, bias * 0.5)), cam.p((xs[-1] + 5, deep / 2, bias * 0.5))],
              HAIR, G3, on=8, off=3)

    peak = max(range(12), key=lambda i: sig(i))
    order = sorted(range(n), key=lambda i: -cam.depth((xs[i], deep / 2, 3)))
    for i in order:
        full = bias + swing * sig(i)
        h = full * (1 - 0.75 * lk) if i in leaky else full
        c = box_corners((xs[i], 0, 0), (thick, 0, 0), (0, deep, 0), (0, 0, h))
        note = i < 11 and abs(sig(i)) > 0.15
        colour = G7 if i == peak else (G5 if note else G4)
        sw = SUBJ if i == peak else LINE
        for name, W, S in visible_faces(cam, c):
            if name == "x0":
                fr.face(S, colour, sw)
            else:
                fr.face(S, G3, LINE)
        # inner structure: the plate's electrode, an inset hairline outline
        if i != peak and h > 3.0:
            e = cam.ps([(xs[i], 1.0, 1.0), (xs[i], deep - 1.0, 1.0), (xs[i], deep - 1.0, h - 1.0), (xs[i], 1.0, h - 1.0)])
            if min(math.dist(e[0], e[1]), math.dist(e[1], e[2])) >= 6:
                fr.ribbon(e + [e[0]], HAIR, G2)
        if i in leaky:  # the charge it lost: hatched ghost above what's left
            g = cam.ps([(xs[i], 0, h), (xs[i], deep, h), (xs[i], deep, full), (xs[i], 0, full)])
            fr.ribbon(g[1:] + [g[0]], HAIR, G3)
            fr.hatch(g, G3)
    # the input end: the block of the chip the plates were drawn out of
    c = box_corners((xs[0] - 7, 0, 0), (3.5, 0, 0), (0, deep, 0), (0, 0, bias))
    for name, W, S in visible_faces(cam, c):
        fr.face(S, G3, LINE)
        if name == "y0":
            fr.hatch(S, G2)
    return fr


# ================================================================= v2
def v2() -> Frame:
    """One scene: a telegraph line running away over open ground, the old relay chain that
    handed a signal on from station to station. The poles are the stages; the note is a
    lit span of the top wire, its recirculations dimmer spans further down the line.
    Single-weight contour: the scene in one 1.5 px line, the pulse heavier, distance in hairline."""
    fr = Frame("v2 · the relay line")
    st, lk, ck, fb = D["stages"], D["leak"], D["clock"], D["feedback"]
    rnd = random.Random(11)

    npoles = round(7 + 13 * st)                       # 7 .. 20 poles to the horizon
    L = 170.0
    span = L / (npoles - 1)
    xs = [k * span * (1 + ck * 0.55 * (rnd.random() - 0.5) * 2) if 0 < k < npoles - 1 else k * span
          for k in range(npoles)]
    lean = [ck * 9 * (rnd.random() - 0.5) * 2 for _ in range(npoles)]
    broken = {k for k in range(1, npoles - 1) if rnd.random() < lk * 0.5}
    H, arm = 10.0, 1.8
    # two wires: one on the crossarm, one on a lower bracket, so they never merge
    wires = [(-arm, H - 0.8), (arm * 0.6, H - 3.0)]

    cam = Camera(eye=(-12, -24, 3.2), target=(48, 2, 5.5))
    cam.fit([(0, 0, -0.2), (0, -arm, H + 0.3), (L, 0, 0), (L, 0, H)], (44, 40, 470, 208))

    def at(k, dy, z):
        a = math.radians(lean[k])
        return (xs[k] + math.sin(a) * z, dy, z * math.cos(a))

    # ground: the horizon and a low rise far behind the line, hairline
    hz = cam.p((L * 4, 0, 0))
    fr.line((0, hz[1] + 1), (480, hz[1] + 1), HAIR, G2)
    rise = [cam.p((x, 420, max(0.0, 26 * math.exp(-((x - 260) / 140) ** 2) - 2 + 4 * math.sin(x / 41))))
            for x in range(-260, 900, 16)]
    fr.ribbon([p for p in rise if -10 < p[0] < 490], HAIR, G2)
    # the track along the line: two ruts, single contour
    for dy in (-5.0, -8.0):
        fr.ribbon(cam.ps([(-2, dy, 0), (L * 3, dy, 0)]), HAIR if dy < -6 else LINE, G3)

    lv = passes(fb)
    every = max(2, round((npoles - 2) / len(lv)))
    pulse_at = [1 + k * every for k in range(len(lv)) if 1 + k * every < npoles - 1]

    for k in range(npoles - 1):
        near = xs[k] < 70
        for side, (dy, z) in enumerate(wires):
            a, b = at(k, dy, z), at(k + 1, dy, z)
            sag = 0.35 + (2.4 if (k in broken and side == 0) else 0)
            pts = [cam.p((a[0] + (b[0] - a[0]) * t, dy, a[2] + (b[2] - a[2]) * t - 4 * sag * t * (1 - t)))
                   for t in [j / 16 for j in range(17)]]
            w, colour = (LINE, G4) if near else (HAIR, G3)
            if side == 0 and k in pulse_at:
                i = pulse_at.index(k)
                colour, w = (G7, SUBJ) if i == 0 else ((G5, LINE) if i == 1 else (G4, LINE))
            fr.ribbon(pts, w, colour)
    for k in range(npoles):
        near = xs[k] < 70
        w, colour = (LINE, G4) if near else (HAIR, G3)
        fr.line(cam.p(at(k, 0, 0)), cam.p(at(k, 0, H)), w + (0.5 if xs[k] < 20 else 0), colour)
        fr.line(cam.p(at(k, -arm - 0.5, H - 0.8)), cam.p(at(k, arm + 0.5, H - 0.8)), w, colour)
        fr.line(cam.p(at(k, 0, H - 3.0)), cam.p(at(k, arm * 0.6 + 0.3, H - 3.0)), w, colour)
    return fr


# ================================================================= v3
def sphere_disc(cam, c, r, n=40):
    """Screen outline of a sphere: its centre projected, radius from distance."""
    cx, cy = cam.p(c)
    rr = r * cam.f / cam.depth(c)
    return (cx, cy, rr), [(cx + rr * math.cos(2 * math.pi * k / n), cy + rr * math.sin(2 * math.pi * k / n))
                          for k in range(n)]


def crescent(cx, cy, r, light=(-0.6, -0.8), k=0.45, n=20):
    """The shadow side of a lit ball: the far half of its outline back along an offset arc."""
    a0 = math.atan2(-light[1], -light[0])
    outer = [(cx + r * math.cos(a0 - math.pi / 2 + math.pi * j / n), cy + r * math.sin(a0 - math.pi / 2 + math.pi * j / n))
             for j in range(n + 1)]
    # terminator as a flattened half-ellipse on the dark side
    term = []
    for j in range(1, n):
        t = math.pi * j / n
        u = math.cos(t)                         # along the terminator's long axis
        v = math.sin(t) * k                     # bulge toward the dark side
        ax, ay = math.cos(a0 + math.pi / 2), math.sin(a0 + math.pi / 2)
        dx, dy = math.cos(a0), math.sin(a0)
        term.append((cx + r * (ax * u + dx * v), cy + r * (ay * u + dy * v)))
    return outer + term


def v3() -> Frame:
    """The machine's rule on a real object: a long cradle of hanging steel balls. Knock
    one end and the blow is handed ball to ball down the row and out the other end,
    then swings back in. Each ball is a stage; stages adds balls, leak dents some so
    they soak up the blow, clock hangs them unevenly, feedback is how far the input
    ball swings back up as the output returns. Hatched mass: shadow sides in hatching."""
    fr = Frame("v3 · a cradle of stages")
    st, lk, ck, fb = D["stages"], D["leak"], D["clock"], D["feedback"]
    rnd = random.Random(5)

    n = round(7 + 11 * st)                     # 7 .. 18 balls
    r = 1.0
    L = 30.0                                   # the frame stays one length; balls get smaller
    r = min(1.3, L / (2 * n + 1))
    pitch = 2 * r
    xs = []
    x = r
    for i in range(n):
        xs.append(x)
        x += pitch + ck * r * 0.9 * rnd.random()
    x0 = (L - (xs[-1] + r)) / 2
    xs = [v + x0 for v in xs]
    drop = [ck * 1.6 * (rnd.random() - 0.5) * 2 for _ in range(n)]
    dented = {i for i in range(1, n - 1) if rnd.random() < lk * 0.5}
    top, wide, hang = 10.0, 3.2, 8.0
    fx0, fx1 = -6.5, L + 6.5                   # the frame clears both swinging end balls

    out_a = math.radians(42)                   # the note leaving at the output end
    back_a = math.radians(6 + 34 * fb)         # what comes back round to the input

    def ball(i):
        pivot_z = top
        l = hang + drop[i]
        if i == n - 1:
            return (xs[i] + l * math.sin(out_a), 0, pivot_z - l * math.cos(out_a)), (xs[i], pivot_z)
        if i == 0:
            return (xs[i] - l * math.sin(back_a), 0, pivot_z - l * math.cos(back_a)), (xs[i], pivot_z)
        return (xs[i], 0, pivot_z - l), (xs[i], pivot_z)

    cam = Camera(eye=(L * 0.5 - 9, -42, 13), target=(L * 0.5, 0, 4))
    cam.fit([(fx0, -wide, -1.6), (fx1, wide, -1.6), (fx0, -wide, top + 0.4), (fx1, wide, top + 0.4)], (34, 34, 446, 206))

    # the frame: base slab and two end posts, hatched mass on their shadow faces
    base = box_corners((fx0, -wide - 1, -1.6), (fx1 - fx0, 0, 0), (0, 2 * wide + 2, 0), (0, 0, 0.6))
    for name, W, S in visible_faces(cam, base):
        fr.face(S, G3, LINE)
        if name == "y0":
            fr.hatch(S, G2)
    # back rail first (behind the balls), then strings, balls, front rail
    def rail(dy):
        return [cam.p((fx0, dy, top)), cam.p((fx1, dy, top))]
    posts = []
    for px in (fx0, fx1):
        for dy in (-wide, wide):
            posts.append((px, dy))
    for px, dy in posts:
        if dy > 0:
            fr.line(cam.p((px, dy, -1)), cam.p((px, dy, top)), LINE, G3)
    fr.ribbon(rail(wide), LINE, G3)

    centres = [ball(i) for i in range(n)]
    for i, (c, (px, pz)) in enumerate(centres):   # strings from each rail to the ball top
        for dy in (wide, -wide):
            fr.line(cam.p((px, dy, pz)), cam.p((c[0], 0, c[2] + r)), HAIR, G3)
    order = sorted(range(n), key=lambda i: -cam.depth(centres[i][0]))
    for i in order:
        c = centres[i][0]
        (cx, cy, rr), disc = sphere_disc(cam, c, r)
        if i == n - 1:
            fr.face(disc, G7, SUBJ)
        else:
            fr.face(disc, G5 if i == 0 else G4, LINE)
        cres = crescent(cx, cy, rr - 1.2)
        fr.hatch(cres, G3 if i != n - 1 else G4, gap=3.2)
        if i in dented:   # a dent: a flat on the lit side, hatched as lost mass
            a = [(cx - rr * 0.75, cy - rr * 0.65), (cx - rr * 0.1, cy - rr * 1.0), (cx - rr * 0.3, cy - rr * 0.35)]
            fr.face(a, G4, HAIR + 0.5)
    for px, dy in posts:
        if dy < 0:
            fr.line(cam.p((px, dy, -1)), cam.p((px, dy, top)), LINE, G4)
    fr.ribbon(rail(-wide), LINE, G4)
    # swing arcs: where the two end balls travel, hairline
    for i, a1 in ((n - 1, out_a), (0, -back_a)):
        px, pz = centres[i][1]
        l = hang + drop[i]
        arc_pts = [cam.p((px + l * math.sin(a1 * t), 0, pz - l * math.cos(a1 * t))) for t in [j / 10 for j in range(11)]]
        fr.dashed(arc_pts, HAIR, G3, on=4, off=3)
    return fr


# ================================================================= v4
def v4() -> Frame:
    """A cutaway of the chip at work: an eight-pin bucket-brigade package with the top of
    its moulding cut off, showing the die on its lead frame and the chain itself, a
    meander of stages folded back and forth across the silicon, with the test note as a
    lit stretch of it and a return trace carrying it round again. Edge-lit silhouette:
    black bodies, a bright rim only on edges facing the light, section faces hatched."""
    fr = Frame("v4 · the chip, cut open")
    st, lk, ck, fb = D["stages"], D["leak"], D["clock"], D["feedback"]
    rnd = random.Random(3)

    Lx, Wy, Hz, cut_x, cut_z = 10.0, 6.4, 3.0, 3.0, 1.5
    cam = Camera(eye=(8.5, -6.0, 17), target=(5.8, 3.2, 0.6))
    cam.fit([(0.6, -1.0, 0), (Lx, -1.0, 0), (0.6, Wy, Hz), (Lx, Wy + 1.0, cut_z), (0.6, -1.0, -0.6)],
            (24, 26, 466, 216))

    def rim(S, edges, colour=G5, w=LINE):
        for i in edges:
            fr.line(S[i], S[(i + 1) % len(S)], w, colour)

    pins = [1.25 + 2.5 * k for k in range(4)]

    def lead(px, side):
        y0, dy = (0.0, -1.0) if side == 0 else (Wy, 1.0)
        sh = box_corners((px - 0.3, y0, 0.9), (0.6, 0, 0), (0, dy * 0.9, 0), (0, 0, 0.3))
        leg = box_corners((px - 0.3, y0 + dy * 0.6, -2.4), (0.6, 0, 0), (0, dy * 0.3, 0), (0, 0, 3.6))
        for c in (leg, sh):
            for name, W, S in visible_faces(cam, c):
                fr.face(S, G1, LINE)
                if name == "z1":
                    rim(S, [1, 2])

    # back leads first, then the body, then the front leads
    for px in pins:
        lead(px, 1)
    lower = box_corners((0, 0, 0), (Lx, 0, 0), (0, Wy, 0), (0, 0, cut_z))
    upper = box_corners((0, 0, cut_z), (cut_x, 0, 0), (0, Wy, 0), (0, 0, Hz - cut_z))
    for name, W, S in visible_faces(cam, lower):
        fr.face(S, G1, LINE)
        if name == "z1":
            fr.hatch(S, G2, gap=4.0)          # the cut through the moulding
            rim(S, [2])
        elif name == "y0":
            rim(S, [0])
    # lead-frame: paddle under the die and fingers running in to it, black metal over the section
    pad = cam.ps([(3.7, 1.1, cut_z), (9.3, 1.1, cut_z), (9.3, 5.3, cut_z), (3.7, 5.3, cut_z)])
    fr.face(pad, G2, LINE)
    fingers = []
    for px in pins:
        if px > cut_x:
            for side in (0, 1):
                ya, yb = (0.0, 1.0) if side == 0 else (Wy - 1.0, Wy)
                f_pts = cam.ps([(px - 0.3, ya, cut_z), (px + 0.3, ya, cut_z), (px + 0.3, yb, cut_z), (px - 0.3, yb, cut_z)])
                fr.face(f_pts, G2, LINE)
                fingers.append(((px, 0.85, cut_z) if side == 0 else (px, Wy - 0.85, cut_z)))
    # the die
    dx0, dx1, dy0, dy1, dz = 4.0, 9.0, 1.4, 5.0, cut_z + 0.25
    die = box_corners((dx0, dy0, cut_z), (dx1 - dx0, 0, 0), (0, dy1 - dy0, 0), (0, 0, 0.25))
    for name, W, S in visible_faces(cam, die):
        fr.face(S, G2, LINE)
        if name == "z1":
            rim(S, [0, 1], G5)
    # bond wires: hairline arcs from die-edge pads to the fingers
    for fx, fy, fz in fingers:
        py = dy0 + 0.25 if fy < Wy / 2 else dy1 - 0.25
        px = min(max(fx, dx0 + 0.3), dx1 - 0.3)
        arc_pts = []
        for j in range(9):
            t = j / 8
            arc_pts.append(cam.p((px + (fx - px) * t, py + (fy - py) * t, dz + (fz - dz) * t + 0.45 * math.sin(math.pi * t))))
        fr.ribbon(arc_pts, HAIR, G4)

    # the chain: a meander of stages across the die, rows unevenly pitched when the clock wanders
    rows = round(3 + 6 * st)                     # 3 .. 9 folds
    ys, y = [], dy0 + 0.55
    base = (dy1 - dy0 - 1.1) / (rows - 1)
    for r in range(rows):
        ys.append(y)
        y += base * (1 + ck * 0.7 * (rnd.random() - 0.5) * 2)
    scale_y = (dy1 - 0.55 - ys[0]) / (ys[-1] - ys[0])
    ys = [ys[0] + (v - ys[0]) * scale_y for v in ys]
    xa, xb = dx0 + 0.7, dx1 - 0.35
    path = []
    for r, yv in enumerate(ys):
        a, b = (xa, xb) if r % 2 == 0 else (xb, xa)
        path += [(a, yv, dz), (b, yv, dz)]
    # return trace: from the last fold back down the die's left margin to the first
    ret = [path[-1], (xa - 0.35, ys[-1], dz), (xa - 0.35, ys[0], dz), path[0]]

    def resample(P, step=0.12):
        out = [P[0]]
        for a, b in zip(P, P[1:]):
            d = math.dist(a, b)
            k = max(1, int(d / step))
            out += [(a[0] + (b[0] - a[0]) * j / k, a[1] + (b[1] - a[1]) * j / k, a[2]) for j in range(1, k + 1)]
        return out

    chain = resample(path)
    fr.ribbon(cam.ps(resample(ret, 0.5)), HAIR, G4)
    # leaky stages: gaps in the meander, hatched patches where the charge escapes
    gaps = sorted(rnd.sample(range(10, len(chain) - 10), 14))
    gaps = [g for k, g in enumerate(gaps) if rnd.random() < lk * 0.8]
    alive = [True] * len(chain)
    for g in gaps:
        for j in range(g - 2, g + 3):
            alive[j] = False
    run = []
    for j, P in enumerate(chain):
        if alive[j]:
            run.append(cam.p(P))
        elif run:
            fr.ribbon(run, LINE, G3)
            run = []
    if run:
        fr.ribbon(run, LINE, G3)
    for g in gaps:
        c = chain[g]
        fr.hatch(cam.ps([(c[0] - 0.3, c[1] - 0.18, dz), (c[0] + 0.3, c[1] - 0.18, dz),
                         (c[0] + 0.3, c[1] + 0.18, dz), (c[0] - 0.3, c[1] + 0.18, dz)]), G3, gap=3)
    # the note and the passes still going round: lit stretches, one per audible pass
    lv = passes(fb)
    n = len(chain)
    for k, a in reversed(list(enumerate(lv))):
        s0 = int(n * (0.04 + 0.86 * k / max(1, len(lv))))
        ln = int(12 + 16 * a)
        seg = [cam.p(P) for j, P in enumerate(chain[s0:s0 + ln]) if alive[s0 + j]]
        colour, w = (G7, SUBJ) if k == 0 else (G5, LINE)
        fr.ribbon(seg, w, colour)

    # the uncut top of the moulding, with its pin-1 dimple, rim-lit
    for name, W, S in visible_faces(cam, upper):
        fr.face(S, G1, LINE)
        if name == "x1":
            fr.hatch(S, G2, gap=4.0)         # the cut face
        if name == "z1":
            rim(S, [0, 1])
    dimple = cam.ps(circle3((1.0, 1.0, Hz), 0.45, n=24)[:-1])
    fr.face(dimple, G2, LINE)
    for px in pins:
        lead(px, 0)
    return fr


# ================================================================= v5
def v5() -> Frame:
    """The mark the process leaves behind: the ring stains a bucket brigade leaves on a
    plank floor, one wet ring wherever a bucket stood. The row of rings shows how many
    stages there were, how evenly they stood (clock), which leaked (drip trails) and how
    many times the line came round (later rings set down over the first, each fainter
    and more broken). The freshest ring, where the note is now, is the bright one."""
    fr = Frame("v5 · ring stains")
    st, lk, ck, fb = D["stages"], D["leak"], D["clock"], D["feedback"]
    rnd = random.Random(19)

    n = round(5 + 10 * st)                     # 5 .. 15 rings
    L, r, row_y = 50.0, 2.1, 5.0
    xs = [L * i / (n - 1) for i in range(n)]
    xs = [x + (ck * (L / (n - 1)) * 0.4 * (rnd.random() - 0.5) * 2 if 0 < i < n - 1 else 0) for i, x in enumerate(xs)]
    ys = [row_y + ck * 0.9 * (rnd.random() - 0.5) * 2 for _ in range(n)]
    leaky = [i for i in range(n - 1) if rnd.random() < lk * 0.5]
    lv = passes(fb)

    cam = Camera(eye=(14, -30, 34), target=(25, 5, 0))
    cam.fit([(-2.5, row_y - r - 0.5, 0), (L + 2.5, row_y - r - 0.5, 0), (-2.5, row_y + r + 4, 0), (L + 2.5, row_y + r + 4, 0)],
            (30, 52, 452, 196))

    # floorboards: seams along the row, staggered end joints, a grain line on every other
    # board; everything clipped to the body so the floor never runs under the header
    BOX = (2, 26, 478, 218)

    def clipped(P, Q):
        (x0, y0), (x1, y1) = P, Q
        t0, t1, dx, dy = 0.0, 1.0, x1 - x0, y1 - y0
        for p_, q_ in ((-dx, x0 - BOX[0]), (dx, BOX[2] - x0), (-dy, y0 - BOX[1]), (dy, BOX[3] - y0)):
            if p_ == 0:
                if q_ < 0:
                    return None
                continue
            t = q_ / p_
            if p_ < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
        if t0 >= t1:
            return None
        return (x0 + dx * t0, y0 + dy * t0), (x0 + dx * t1, y0 + dy * t1)

    def seg(P, Q, w, colour):
        c = clipped(cam.p(P), cam.p(Q))
        if c:
            fr.line(c[0], c[1], w, colour)

    bw = 4.2
    xa, xb = -40.0, 100.0
    for k in range(-6, 12):
        y = k * bw
        seg((xa, y, 0), (xb, y, 0), HAIR, G2)
        off = (k * 13.7) % 21
        for x in [off - 42 + 21 * j for j in range(8)]:
            seg((x, y, 0), (x, y + bw, 0), HAIR, G2)
        if k % 2 == 0:
            gx = [xa + j * 4.0 for j in range(36)]
            for j in range(0, len(gx) - 1, 3):
                for jj in range(j, j + 2):
                    g0 = (gx[jj], y + bw * 0.5 + 0.3 * math.sin(gx[jj] / 5.3 + k), 0)
                    g1 = (gx[jj + 1], y + bw * 0.5 + 0.3 * math.sin(gx[jj + 1] / 5.3 + k), 0)
                    seg(g0, g1, HAIR, G1)

    def ring(cx, cy, rad, a0, cover, w, colour, npts=40):
        a1 = a0 + 2 * math.pi * cover
        pts = cam.ps([(cx + rad * math.cos(a0 + (a1 - a0) * j / npts), cy + rad * math.sin(a0 + (a1 - a0) * j / npts), 0)
                      for j in range(npts + 1)])
        fr.ribbon(pts, w, colour)

    note = 3
    # later passes first (they're fainter), offset a little each time round, more broken
    for k in range(len(lv) - 1, 0, -1):
        for i in range(n):
            ox, oy = 0.55 * k * (1 if k % 2 else -1), 0.45 * k
            cover = max(0.25, 0.85 - 0.22 * k) * (0.7 + 0.3 * lv[k] / lv[1])
            ring(xs[i] + ox, ys[i] + oy, r * (1 - 0.04 * k), rnd.uniform(0, 6.28), cover, HAIR, G3)
    # the first pass: a full ring with the darker tide-mark inside it, broken
    for i in range(n):
        if i == note:
            ring(xs[i], ys[i], r, 0, 1.0, SUBJ, G7)
            ring(xs[i], ys[i], r - 0.5, 0.6, 0.55, HAIR, G5)
        else:
            ring(xs[i], ys[i], r, 0, 1.0, LINE, G4)
            ring(xs[i], ys[i], r - 0.5, rnd.uniform(0, 6.28), 0.45, HAIR, G3)
    # drips: a trail of spots from each leaky bucket toward the next, hatched spots
    for i in leaky:
        for j in range(4):
            t = 0.25 + 0.17 * j
            x = xs[i] + (xs[i + 1] - xs[i]) * t
            y = ys[i] - r * 0.4 + 0.35 * math.sin(j * 2.1)
            sp = cam.ps(circle3((x, y, 0), 0.38 - 0.05 * j, n=16)[:-1])
            fr.face(sp, G3, LINE)
    return fr


VARIANTS = {"v1": v1, "v2": v2, "v3": v3, "v4": v4, "v5": v5}


def main() -> None:
    for name, fn in VARIANTS.items():
        out = HERE / name
        out.mkdir(exist_ok=True)
        svg = out / "rest.svg"
        svg.write_text(fn().svg())
        subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", "-b", "black", str(svg),
                        "-o", str(out / "rest.png")], check=True)
        print(svg)


if __name__ == "__main__":
    main()
