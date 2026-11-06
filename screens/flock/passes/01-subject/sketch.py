#!/usr/bin/env python3
"""Flock, subject pass 01: five rest-frame sketches from one script.

    python3 screens/flock/passes/01-subject/sketch.py

One flock model (eight birds over a two-octave pitch field, seeded) feeds all
five variants, so the five frames show the same state at the defaults:
cohere 50 %, speed 1.00 cells a beat, scatter 0 %, scale penta.

Each variant is its own pattern x drawing language (pass.json). Sketch-stage
device rules kept: one subpath per path, <= 64 points, lines as closed filled
ribbons (no open strokes), explicit paint on every leaf, grey only, <= 4
fractional digits. No bound nodes yet: that's phase 4.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ------------------------------------------------------------------ state
COHERE, SPEED, SCATTER = 0.5, 1.0, 0.0          # control values at default
SCALE = [0, 2, 4, 7, 9]                          # penta, semitones in an octave
OCTAVES = 2
LABELS = ["cohere", "speed", "scatter", "scale"]
VALUES = ["50", "1.00", "0", "pent"]
N_BIRDS = 8

G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
FONT = "UniversNextPro-Light"


def degrees() -> list[int]:
    """Scale degrees across the field, in semitones from the bottom (c3 .. c5)."""
    out = [12 * o + s for o in range(OCTAVES) for s in SCALE]
    return out + [12 * OCTAVES]


DEG = degrees()                                   # 11 for penta


def flock_model(seed: int = 7):
    """Eight birds: (u pitch 0..1, v height 0..1, heading rad). Cohesion sets the spread."""
    rnd = random.Random(seed)
    cu, cv = 0.56, 0.46
    spread = 0.06 + 0.26 * (1 - COHERE)           # 0.19 at cohere 50 %
    head0 = math.radians(-18)
    birds = []
    for i in range(N_BIRDS):
        u = cu + rnd.gauss(0, spread * 0.9)
        v = cv + rnd.gauss(0, spread * 0.7)
        h = head0 + rnd.gauss(0, 0.22)
        birds.append((min(0.97, max(0.03, u)), min(0.95, max(0.05, v)), h))
    return birds, (cu, cv), spread


BIRDS, CENTRE, SPREAD = flock_model()


def cell(u: float) -> int:
    """Index of the scale degree under pitch position u."""
    return min(len(DEG) - 1, max(0, round(u * (len(DEG) - 1))))


def fmt(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def dedupe(pts):
    out = []
    for p in pts:
        if not out or math.dist(p, out[-1]) >= 0.2:
            out.append(p)
    if len(out) > 2 and math.dist(out[0], out[-1]) < 0.3:
        out.pop()
    return out


# ------------------------------------------------------------------ frame
class Frame:
    def __init__(self, title: str):
        self.title = title
        self.items: list[str] = []

    def add(self, s: str) -> None:
        self.items.append(s)

    def poly(self, pts, fill, stroke="none", sw=0.0):
        pts = dedupe(pts)
        assert 3 <= len(pts) <= 64, len(pts)
        d = "M " + " L ".join(f"{fmt(x)} {fmt(y)}" for x, y in pts) + " Z"
        sws = f' stroke-width="{fmt(sw)}"' if stroke != "none" else ' stroke-width="0"'
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def ribbon(self, pts, w, colour):
        """An open polyline of width w, drawn as closed filled ribbons of <= 31 points a side."""
        pts = dedupe(pts)
        if len(pts) < 2:
            return
        n = 30
        i = 0
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

    def dashed(self, a, b, w, colour, dash=4.0, gap=3.0):
        L = math.dist(a, b)
        if L == 0:
            return
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        t = 0.0
        while t < L:
            e = min(L, t + dash)
            if e - t > 1:
                self.line((a[0] + ux * t, a[1] + uy * t), (a[0] + ux * e, a[1] + uy * e), w, colour)
            t += dash + gap

    def outline(self, pts, colour, sw, fill="#000000"):
        """A closed outline (stroked loop with a fill), <= 64 points."""
        self.poly(pts, fill, colour, sw)

    def circle(self, cx, cy, r, fill, stroke="none", sw=0.0):
        sws = f' stroke-width="{fmt(sw)}"' if stroke != "none" else ' stroke-width="0"'
        self.add(f'<circle cx="{fmt(cx)}" cy="{fmt(cy)}" r="{fmt(r)}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def rect(self, x, y, w, h, fill):
        self.add(f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" fill="{fill}" '
                 f'stroke="none" stroke-width="0"/>')

    def text(self, x, y, s, colour=G4, size=10):
        self.add(f'<text transform="matrix(1 0 0 1 {fmt(x)} {fmt(y)})" fill="{colour}" stroke="none" '
                 f'stroke-width="0" font-family="{FONT}" font-size="{size}px">{s}</text>')

    def svg(self) -> str:
        out = ['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
               f"  <title>flock · subject pass 01 · {self.title}</title>",
               '  <g id="preview_canvas">',
               '    <rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>',
               "  </g>",
               '  <g id="preview_header">']
        for i, c in enumerate([G0, G1, G2, G3, G4, G5, G6, G7]):
            out.append(f'    <rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
        for i, (lab, val) in enumerate(zip(LABELS, VALUES)):
            c = "#CBCBCB" if i < 2 else "#000000"
            out.append(f'    <text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{c}" stroke="none" '
                       f'font-family="{FONT}" font-size="10px">{lab}</text>')
            out.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{c}" stroke="none" '
                       f'font-family="{FONT}" font-size="20px">{val}</text>')
        out.append("  </g>")
        out += ["  " + s for s in self.items]
        out.append("</svg>")
        return "\n".join(out) + "\n"


def ellipse_pts(cx, cy, rx, ry, n=48, a0=0.0, a1=2 * math.pi):
    full = abs(a1 - a0 - 2 * math.pi) < 1e-9
    k = n if full else n + 1
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(k)]


def clip_x(poly, lo, hi):
    """The part of a polyline with lo <= x <= hi, cut at the edges."""
    out = []
    for (xa, ya), (xb, yb) in zip(poly, poly[1:]):
        if xb < lo or xa > hi:
            continue
        def at(x):
            t = 0 if xb == xa else (x - xa) / (xb - xa)
            return (x, ya + (yb - ya) * t)
        a = (xa, ya) if xa >= lo else at(lo)
        b = (xb, yb) if xb <= hi else at(hi)
        if not out or math.dist(out[-1], a) > 0.01:
            out.append(a)
        out.append(b)
    return out


def note_name(semi: int) -> str:
    return f"c{3 + semi // 12}"


# ------------------------------------------------------------------ v1 · P5 field and figure · star atlas
def v1() -> Frame:
    """The pitch field as a conic atlas chart; the flock as one asterism over it."""
    F = Frame("v1 · P5 field and figure · star atlas")
    ax, ay = 240.0, 700.0                         # apex of the conic projection, far below
    r_top, r_bot = ay - 46, ay - 182               # parallels between y 46 and 182
    th = math.radians(17.5)                        # half-width of the chart in angle
    n = len(DEG)

    def P(u, v):                                   # u pitch 0..1 (left low), v height 0..1 (top)
        a = -th + 2 * th * u
        r = r_top + (r_bot - r_top) * v
        return (ax + r * math.sin(a), ay - r * math.cos(a))

    # parallels: four velocity bands (soft high, loud low)
    for j in range(5):
        v = j / 4
        F.ribbon([P(i / 40, v) for i in range(41)], 1, G2 if j in (0, 4) else G1)
    # meridians: one per scale degree; octave meridians a step brighter, labelled at the top
    for i, s in enumerate(DEG):
        u = i / (n - 1)
        octave = s % 12 == 0
        F.line(P(u, 0), P(u, 1), 1, G3 if octave else G2)
        if octave:
            x, y = P(u, 0)
            F.text(x - 6, y - 5, note_name(s), G4)
    F.text(8, 60, "pp", G4)
    F.text(8, 180, "ff", G4)

    pos = [P(u, v) for u, v, _ in BIRDS]
    # asterism lines: a minimum spanning tree, stopped short of each star as atlases draw them
    done, edges = {0}, []
    while len(done) < len(pos):
        best = min(((math.dist(pos[a], pos[b]), a, b) for a in done for b in range(len(pos)) if b not in done))
        edges.append((best[1], best[2]))
        done.add(best[2])
    for a, b in edges:
        (x0, y0), (x1, y1) = pos[a], pos[b]
        L = math.dist(pos[a], pos[b])
        if L < 14:
            continue
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        F.line((x0 + ux * 6, y0 + uy * 6), (x1 - ux * 6, y1 - uy * 6), 1, G5)
    # proper-motion vectors: length is the distance flown in one beat (speed)
    pm = 14 * SPEED ** 0.6
    for (x, y), (_, _, h) in zip(pos, BIRDS):
        ex, ey = x + math.cos(h) * (pm + 4), y + math.sin(h) * (pm + 4)
        F.line((x + math.cos(h) * 4, y + math.sin(h) * 4), (ex, ey), 1.2, G6)
        nx, ny = -math.sin(h), math.cos(h)
        F.line((ex - nx * 2.5, ey - ny * 2.5), (ex + nx * 2.5, ey + ny * 2.5), 1.2, G6)
    # stars: magnitude from how loud the bird plays (low on the chart = louder)
    for (x, y), (u, v, _) in zip(pos, BIRDS):
        r = 2.8 + 1.6 * v
        F.circle(x, y, r + 1.2, G0)
        F.circle(x, y, r, G7)
    # strip: one mark per pitch column, the ones a bird is over raised
    played = {cell(u) for u, _, _ in BIRDS}
    for i in range(n):
        x = P(i / (n - 1), 1)[0]
        if i in played:
            F.rect(x - 4, 198, 8, 10, G5)
        else:
            F.rect(x - 3, 204, 6, 3, G2)
    return F


# ------------------------------------------------------------------ 3D helper
class Camera:
    def __init__(self, eye, target, f, centre):
        self.e = eye
        fx, fy, fz = (target[i] - eye[i] for i in range(3))
        L = math.sqrt(fx * fx + fy * fy + fz * fz)
        self.fw = (fx / L, fy / L, fz / L)
        up = (0, 1, 0)
        rx = (self.fw[1] * up[2] - self.fw[2] * up[1], self.fw[2] * up[0] - self.fw[0] * up[2],
              self.fw[0] * up[1] - self.fw[1] * up[0])
        L = math.sqrt(sum(c * c for c in rx))
        self.rt = tuple(c / L for c in rx)
        f_ = self.fw
        r_ = self.rt
        self.up = (r_[1] * f_[2] - r_[2] * f_[1], r_[2] * f_[0] - r_[0] * f_[2], r_[0] * f_[1] - r_[1] * f_[0])
        self.f, self.c = f, centre

    def depth(self, p):
        d = [p[i] - self.e[i] for i in range(3)]
        return sum(d[i] * self.fw[i] for i in range(3))

    def __call__(self, p):
        d = [p[i] - self.e[i] for i in range(3)]
        z = sum(d[i] * self.fw[i] for i in range(3))
        x = sum(d[i] * self.rt[i] for i in range(3))
        y = sum(d[i] * self.up[i] for i in range(3))
        return (self.c[0] - self.f * x / z, self.c[1] - self.f * y / z)

    def ppu(self, p):
        return self.f / self.depth(p)


# ------------------------------------------------------------------ v2 · P12 orrery · engineering schematic
def v2() -> Frame:
    """Birds orbit the flock's centre of gravity; a graduated pitch rim reads the bearing each one plays."""
    F = Frame("v2 · P12 orrery · engineering schematic")
    elev = math.radians(30)
    dist = 16.0
    cam = Camera((0, dist * math.sin(elev), -dist * math.cos(elev)), (0, 0, 0), 600, (240, 114))
    R_RIM = 4.3
    orbits = [1.3, 2.0, 2.7, 3.4]

    def W(r, a, y=0.0):                            # world point on the plane, angle a (0 = right, ccw from above)
        return (r * math.cos(a), y, r * math.sin(a))

    # graduated pitch rim: two octaves round one turn, a tick per scale degree
    rim = [cam(W(R_RIM, 2 * math.pi * i / 63)) for i in range(63)]
    F.outline(rim, G3, 1.2, fill="none")
    for s in DEG[:-1]:
        a = 2 * math.pi * s / (12 * OCTAVES)
        octave = s % 12 == 0
        p0, p1 = cam(W(R_RIM, a)), cam(W(R_RIM + (0.42 if octave else 0.24), a))
        F.line(p0, p1, 1.2, G4 if octave else G3)
        if octave:
            lx, ly = cam(W(R_RIM + 0.75, a))
            F.text(lx - 5, ly + 4, note_name(s), G4)
    # orbits, hairline; the sun-side runs that pass behind the centre mark are broken
    for r in orbits:
        F.outline([cam(W(r, 2 * math.pi * i / 63)) for i in range(63)], G2, 1, fill="none")
    # centre of gravity: a small sphere, labelled
    cx, cy = cam((0, 0, 0))
    F.circle(cx, cy, 6.5, G1, G4, 1.2)
    F.line((cx - 11, cy), (cx - 8, cy), 1, G4)
    F.line((cx + 8, cy), (cx + 11, cy), 1, G4)
    F.text(cx + 10, cy - 7, "cg", G4)

    # birds: two per orbit, gathered in a sector whose width is cohesion
    sector_c = math.radians(-62)                  # front right of the plan
    half = math.radians(25 + 70 * (1 - COHERE))   # +-60 deg at 50 %
    rnd = random.Random(3)
    birds = []
    for i in range(N_BIRDS):
        r = orbits[i % 4]
        a = sector_c + half * (2 * (i + 0.5) / N_BIRDS - 1) + rnd.uniform(-0.08, 0.08)
        birds.append((r, a))
    # sector dimension on the rim: an angular dimension line with end ticks and its span in semitones
    a0, a1 = sector_c - half, sector_c + half
    arc = [cam(W(R_RIM - 0.35, a0 + (a1 - a0) * i / 30)) for i in range(31)]
    F.ribbon(arc, 1, G5)
    for a in (a0, a1):
        F.line(cam(W(R_RIM - 0.55, a)), cam(W(R_RIM - 0.12, a)), 1, G5)
        F.dashed(cam(W(0.6, a)), cam(W(R_RIM - 0.6, a)), 1, G2, 4, 4)
    span = round((a1 - a0) / (2 * math.pi) * 24)
    mx, my = cam(W(R_RIM - 0.35, sector_c))
    F.text(mx + 8, my + 14, f"{span} st", G5)

    order = sorted(range(N_BIRDS), key=lambda k: -cam.depth(W(birds[k][0], birds[k][1])))
    for k in order:
        r, a = birds[k]
        # trailing link along the orbit: one beat of travel (speed)
        sweep = math.radians(22 * SPEED)
        link = [cam(W(r, a + sweep * (1 - t / 12))) for t in range(13)]
        F.ribbon(link[:-1], 1.5, G4)
        # leader out to the rim: the bearing it plays
        p, q = cam(W(r + 0.25, a)), cam(W(R_RIM - 0.05, a))
        F.dashed(p, q, 1, G3, 4, 3)
        x, y = cam(W(r, a))
        rr = 4.6 * cam.ppu(W(r, a)) / cam.ppu((0, 0, 0))
        F.circle(x, y, rr + 1.3, G0)
        F.circle(x, y, rr, G7)
    # title block
    F.outline([(404, 192), (474, 192), (474, 212), (404, 212)], G2, 1, fill="none")
    F.text(409, 206, "plan · 1:1", G4)
    return F


# ------------------------------------------------------------------ v3 · P13 capture · oscilloscope trace
def v3() -> Frame:
    """Each bird's pitch over the last beats as a stepped trace; cohesion is a pair of cursors that captures them."""
    F = Frame("v3 · P13 capture · oscilloscope trace")
    x0, x1, y0, y1 = 40.0, 440.0, 34.0, 210.0     # graticule 10 x 8 divisions
    for i in range(11):
        x = x0 + (x1 - x0) * i / 10
        F.line((x, y0), (x, y1), 1, G2 if i in (0, 10) else G1)
    for j in range(9):
        y = y0 + (y1 - y0) * j / 8
        F.line((x0, y), (x1, y), 1, G2 if j in (0, 8) else G1)
    # pitch axis: a tick per scale degree on the left rail, octaves labelled
    top = 12 * OCTAVES

    def Y(semi):
        return y1 - 8 - (y1 - y0 - 16) * semi / top

    for s in DEG:
        octave = s % 12 == 0
        F.line((x0, Y(s)), (x0 + (8 if octave else 5), Y(s)), 1.2, G4 if octave else G3)
        if octave:
            F.text(12, Y(s) + 4, note_name(s), G4)
    F.text(x1 - 26, y1 - 6, "now", G4)

    # capture cursors: the cohesion band around the flock's centre pitch
    centre = CENTRE[0] * top
    half = 1.5 + 8 * (1 - COHERE)                 # semitones, 5.5 at 50 %
    for s in (centre - half, centre + half):
        F.dashed((x0 + 2, Y(s)), (x1 - 2, Y(s)), 1, G6, 6, 4)
    F.text(x1 - 58, Y(centre + half) - 5, f"Δ {round(2 * half)} st", G5)

    # traces: pitch quantised to the scale, one step each time the bird crosses a cell
    rnd = random.Random(11)
    beat_px = 80.0                                # 2 divisions a beat, five beats on screen
    step_px = beat_px / SPEED                     # one cell crossed per beat at speed 1.00
    greys = [G2, G3, G4, G5]
    ends = []
    for b, (u, v, h) in enumerate(BIRDS):
        now = cell(u)
        # older steps sit further out: the trace shows each bird being drawn into the band
        far = rnd.choice([-1, 1]) * rnd.randint(3, 6)
        seq = []                                  # (x where the step starts, level), oldest first
        x = x1 - 6
        k = 0
        while x > x0:
            age = (x1 - x) / (x1 - x0)
            lvl = now + round(far * age ** 1.4) + (rnd.choice([-1, 0, 1]) if 0 < k else 0)
            seq.append((x, min(len(DEG) - 1, max(0, lvl))))
            x -= step_px * rnd.uniform(0.75, 1.25)
            k += 1
        seq.append((x0, seq[-1][1]))
        seq = seq[::-1]
        stair = []
        for (xa, la), (xb, lb) in zip(seq, seq[1:]):
            stair.append((xa, Y(DEG[la])))
            if la != lb:
                stair.append((xb - 1.5, Y(DEG[la])))
        stair.append((x1 - 6, Y(DEG[seq[-1][1]])))
        for q in range(4):
            lo, hi = x0 + (x1 - x0) * q / 4, x0 + (x1 - x0) * (q + 1) / 4
            seg = clip_x(stair, lo, hi)
            if len(seg) >= 2:
                F.ribbon(seg, 1.2, greys[q])
        ends.append((x1 - 6, Y(DEG[now])))
    # beam spots at "now"; brighter inside the cursors
    for (x, y), (u, _, _) in zip(ends, BIRDS):
        inside = abs(DEG[cell(u)] - centre) <= half
        F.circle(x, y, 3.6, G7 if inside else G4)
    return F


# ------------------------------------------------------------------ v4 · P14 loom · typeset diagram
def v4() -> Frame:
    """The flock's last four bars woven as cloth: warp threads are the field's pitches, slabs are what the birds played."""
    F = Frame("v4 · P14 loom · typeset diagram")
    cam = Camera((0, 5.2, -7.4), (0, 0, 2.2), 400, (240, 112))
    n = len(DEG)
    width = 8.4
    rows = 4
    depth_step = 1.45

    def X(i):
        return -width / 2 + width * i / (n - 1)

    # warp threads, back to front
    for i in range(n):
        p0, p1 = cam((X(i), 0, -0.6)), cam((X(i), 0, depth_step * (rows - 1) + 0.7))
        F.line(p0, p1, 1, G3 if DEG[i] % 12 == 0 else G2)
    # note names set under the front edge, octaves only, plus the degree count
    for i, s in enumerate(DEG):
        if s % 12 == 0:
            x, y = cam((X(i), 0, -0.6))
            F.text(x - 6, y + 14, note_name(s), G4)
    # row rules and row numbers, typeset at the left margin
    for r in range(rows):
        z = depth_step * r
        pa, pb = cam((-width / 2 - 0.5, 0, z)), cam((width / 2 + 0.5, 0, z))
        F.line(pa, pb, 1, G1)
        F.text(pa[0] - 22, pa[1] + 4, "0" if r == 0 else f"−{r}", G4)
    F.text(18, 206, "fig. 1  last four bars", G4)

    # hits per row: the flock's cells, drifting a little bar to bar (seeded)
    rnd = random.Random(5)
    hits = []
    for r in range(rows):
        row = {}
        for u, v, h in BIRDS:
            c = cell(u + rnd.gauss(0, 0.035 * r))
            row[c] = row.get(c, 0) + max(1, round(SPEED * rnd.uniform(0.6, 1.6)))
        hits.append(row)

    # slabs drawn back to front: front row solid, older rows wire (black fill) a grey step darker each
    edge = [G7, G5, G4, G3]
    face = [(G5, G4), None, None, None]
    sw_, sd = 0.34, 0.42
    for r in reversed(range(rows)):
        z = depth_step * r
        for i in sorted(hits[r], key=lambda k: abs(X(k))):
            hgt = 0.3 * min(4, hits[r][i])
            x = X(i)
            A = [cam((x - sw_, hgt, z - sd)), cam((x + sw_, hgt, z - sd)), cam((x + sw_, hgt, z + sd)), cam((x - sw_, hgt, z + sd))]
            Fr = [cam((x - sw_, 0, z - sd)), cam((x + sw_, 0, z - sd)), cam((x + sw_, hgt, z - sd)), cam((x - sw_, hgt, z - sd))]
            if face[r]:
                F.outline(Fr, G0, 1.2, fill=face[r][1])
                F.outline(A, G0, 1.2, fill=G7)
            else:
                F.outline(Fr, edge[r], 1, fill=G0)
                F.outline(A, edge[r], 1, fill=G0)
    return F


# ------------------------------------------------------------------ v5 · P11 instrument stack · orthographic elevation
def v5() -> Frame:
    """Birds on wires: a stack of telegraph wires, one per scale degree, drawn in elevation; a perched bird plays its wire."""
    F = Frame("v5 · P11 instrument stack · orthographic elevation")
    xl, xr = 34.0, 446.0
    yt, yb = 44.0, 176.0
    n = len(DEG)
    sag = 9.0

    def wire_y(i, x):
        y = yb - (yb - yt) * i / (n - 1)
        t = (x - xl) / (xr - xl)
        return y + sag * 4 * t * (1 - t)

    # ground line and poles in elevation: a shaft, a cap, a crossarm per octave
    F.line((8, 206), (472, 206), 1, G2)
    for px in (xl, xr):
        F.outline([(px - 3, 36), (px + 3, 36), (px + 3, 206), (px - 3, 206)], G4, 1.2)
        for i, s in enumerate(DEG):
            y = wire_y(i, px)
            F.outline([(px - 6, y - 1.5), (px + 6, y - 1.5), (px + 6, y + 1.5), (px - 6, y + 1.5)], G3, 1)
    # wires: catenaries, octave wires a step brighter and labelled on the left pole
    for i, s in enumerate(DEG):
        pts = [(xl + (xr - xl) * k / 40, wire_y(i, xl + (xr - xl) * k / 40)) for k in range(41)]
        F.ribbon(pts, 1, G3 if s % 12 == 0 else G2)
        if s % 12 == 0:
            F.text(12, wire_y(i, xl) + 4, note_name(s), G4)

    # birds: perched on the wire under them, bunched along the span by cohesion
    rnd = random.Random(9)
    span_c = 70 + 340 * CENTRE[0]
    perched = []
    for b, (u, v, h) in enumerate(BIRDS):
        i = cell(u)
        x = span_c + (b - (N_BIRDS - 1) / 2) * (16 + 40 * SPREAD) + rnd.uniform(-4, 4)
        perched.append((x, i))
    # one bird in each beat lifts off: speed sets how many are between wires
    aloft = max(1, round(2 * SPEED))

    def bird(x, y):
        """Side elevation of a perched bird: one closed outline, belly on the wire at (x, y)."""
        return [(x - 13, y - 2), (x - 13, y - 4.5), (x - 6, y - 7.5), (x - 1, y - 9), (x + 2.5, y - 12.5),
                (x + 5.5, y - 13), (x + 8, y - 11), (x + 11, y - 10.2), (x + 8, y - 8.8), (x + 6.5, y - 6),
                (x + 4, y - 2.2), (x, y - 0.5), (x - 5, y - 0.8)]

    for k, (x, i) in enumerate(perched):
        y = wire_y(i, x)
        if k < aloft:
            # between wires: lifted off its wire towards the one above, wing raised, the hop dashed
            bx = x - 20 - 60 * k
            y2 = wire_y(min(n - 1, i + 1), bx) - 12 - 10 * k
            F.dashed((x - 4, y - 3), (bx + 6, y2 - 3), 1, G3, 3.5, 3)
            F.outline(bird(bx, y2), G7, 1.5)
            F.line((bx - 1, y2 - 8), (bx - 9, y2 - 18), 1.5, G7)
            continue
        F.outline(bird(x, y), G7, 1.5)
    F.text(352, 200, "elevation · 2 oct", G4)
    return F


def main() -> None:
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        d = HERE / name
        d.mkdir(exist_ok=True)
        (d / "rest.svg").write_text(fn().svg(), encoding="utf-8")
        print(f"wrote {d / 'rest.svg'}")


if __name__ == "__main__":
    main()
