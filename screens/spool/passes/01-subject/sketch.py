#!/usr/bin/env python3
"""Spool, subject pass 01: five rest-frame sketches, one per direction.

    python3 screens/spool/passes/01-subject/sketch.py

Writes v1..v5/rest.svg (480 x 220) beside this file. Every variant draws from
the same small tape model (`Tape`), so the sketches can be re-run at other
control values: `python3 sketch.py wear=0.6 wow=0.4` writes the same five
frames at that state (still named rest.svg, so only do that in a scratch copy).

These are subject sketches, not device frames: parts are static artwork
(lines as filled closed ribbons, one subpath, <= 64 points each) and no
nodes are bound yet. Binding and the budget belong to phase 4/5.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent

# Stock greys (constraints.md, header steps).
B, S2, S, M, G, D, F, K = ("#CDCDCD", "#AFAFAF", "#969696", "#7D7D7D",
                           "#646464", "#4B4B4B", "#323232", "#000000")
FONT = "UniversNextPro-Light"

# ---------------------------------------------------------------- the model

DEFAULTS = {"wear": 0.0, "wow": 0.0, "length": 0.5, "bias": 0.5}


class Tape:
    """Control positions (0..1) -> what the tape loop is doing."""

    # The cycle as written: a ramp, a step down to a shelf, a drop, a floor.
    # Piecewise linear so the fresh drawing keeps its corners.
    WRITTEN = [(0.0, -0.9), (0.55, 0.9), (0.6, -0.1), (0.85, 0.15), (0.9, -0.9), (1.0, -0.9)]

    def __init__(self, **kv: float) -> None:
        v = {**DEFAULTS, **kv}
        self.wear_pos, self.wow_pos, self.length_pos, self.bias_pos = v["wear"], v["wow"], v["length"], v["bias"]
        self.wear = v["wear"] ** 2                     # power mapping, exponent 2: erosion per pass
        self.wow = v["wow"]                            # depth 0..1
        self.length = 0.05 * (2.0 / 0.05) ** v["length"]  # seconds, exponential 0.05..2
        self.bias = v["bias"] * 2 - 1                  # -1 under .. +1 over

    def written(self, x: float) -> float:
        x %= 1.0
        pts = self.WRITTEN
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            if x0 <= x <= x1:
                return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
        return pts[-1][1]

    def played(self, passes: float = 4.0, n: int = 256) -> np.ndarray:
        """The cycle after `passes` passes at this wear: high partials go first,
        a couple of dropouts open, bias clips (under) or dulls (over)."""
        xs = np.arange(n) / n
        y = np.array([self.written(x) for x in xs])
        spec = np.fft.rfft(y)
        k = np.arange(len(spec))
        loss = self.wear * passes * 0.35 + max(self.bias, 0) * 0.12
        spec *= np.exp(-loss * k)
        y = np.fft.irfft(spec, n)
        for c, w in ((0.3, 0.05), (0.72, 0.04)):
            d = np.exp(-((xs - c) / w) ** 2) * min(1.0, self.wear * passes * 0.6)
            y *= 1 - 0.8 * d
        if self.bias < 0:  # under-bias: hotter, harder edges
            ceiling = 1 + self.bias * 0.45
            y = np.clip(y * (1 - self.bias * 0.2), -ceiling, ceiling)
        else:
            y *= 1 - 0.25 * self.bias
        return y

    def written_points(self) -> list[tuple[float, float]]:
        return list(self.WRITTEN)

    def length_frac(self) -> float:
        return self.length_pos


# ---------------------------------------------------------------- drawing kit

def n(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def dedupe(pts, gap=0.3):
    out = []
    for p in pts:
        if not out or math.dist(out[-1], p) >= gap:
            out.append(p)
    return out


def offset(pts, w):
    """Closed ribbon polygon of width w around an open polyline (mitred)."""
    h = w / 2
    left, right = [], []
    for i, p in enumerate(pts):
        a = pts[i - 1] if i > 0 else None
        b = pts[i + 1] if i < len(pts) - 1 else None
        normals = []
        for q0, q1 in ((a, p), (p, b)):
            if q0 is None or q1 is None:
                continue
            dx, dy = q1[0] - q0[0], q1[1] - q0[1]
            ln = math.hypot(dx, dy)
            normals.append((-dy / ln, dx / ln))
        nx = sum(v[0] for v in normals)
        ny = sum(v[1] for v in normals)
        ln = math.hypot(nx, ny) or 1
        nx, ny = nx / ln, ny / ln
        cos = max(0.45, nx * normals[0][0] + ny * normals[0][1])
        m = h / cos
        left.append((p[0] + nx * m, p[1] + ny * m))
        right.append((p[0] - nx * m, p[1] - ny * m))
    return left + right[::-1]


class Frame:
    def __init__(self, title: str, values: list[str]) -> None:
        self.title = title
        self.values = values
        self.body: list[str] = []

    def poly(self, pts, fill=K, stroke="none", sw=0.0, ident=None):
        pts = dedupe(pts)
        if len(pts) > 64:
            raise ValueError(f"{len(pts)} points in one path")
        d = "M " + " L ".join(f"{n(x)} {n(y)}" for x, y in pts) + " Z"
        sw_attr = f' stroke-width="{n(sw)}"' if stroke != "none" else ""
        idattr = f' id="{ident}"' if ident else ""
        self.body.append(f'<path{idattr} d="{d}" fill="{fill}" stroke="{stroke}"{sw_attr}/>')

    def line(self, pts, w, col):
        """An open line as filled closed ribbons, split so each stays <= 64 points."""
        pts = dedupe(pts, 0.6)
        i = 0
        while i < len(pts) - 1:
            chunk = pts[i:i + 31]
            self.poly(offset(chunk, w), fill=col)
            i += 30

    def circle(self, cx, cy, r, stroke, sw, fill=K):
        self.body.append(f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n(r)}" fill="{fill}" stroke="{stroke}" stroke-width="{n(sw)}"/>')

    def rect(self, x, y, w, h, fill):
        self.body.append(f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" fill="{fill}" stroke="none"/>')

    def text(self, x, y, s, col=M, size=10, anchor=None):
        a = f' text-anchor="{anchor}"' if anchor else ""
        self.body.append(f'<text transform="matrix(1 0 0 1 {n(x)} {n(y)})" fill="{col}" stroke="none" '
                         f'font-family="{FONT}" font-size="{size}px"{a}>{s}</text>')

    def svg(self) -> str:
        steps = [K, F, D, G, M, S, S2, B]
        head = ['<g id="preview_canvas">', '  <rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>', '</g>',
                '<g id="preview_header">']
        for i, c in enumerate(steps):
            head.append(f'  <rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
        for i, t in enumerate(["wear", "wow", "length", "bias"]):
            col = "#CBCBCB" if i < 2 else "#000000"
            head.append(f'  <text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{col}" stroke="none" '
                        f'font-family="{FONT}" font-size="10px">{t}</text>')
            head.append(f'  <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{col}" stroke="none" '
                        f'font-family="{FONT}" font-size="20px">{self.values[i]}</text>')
        head.append('</g>')
        body = "\n  ".join(self.body)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">\n'
                f'  <!-- spool · subject pass 01 · {self.title} -->\n  ' + "\n  ".join(head) + "\n  " + body + "\n</svg>\n")


def header_values(t: Tape) -> list[str]:
    ms = t.length * 1000
    # duration caption: proposed header override, 2 decimals of a second (fits 53 px; "316ms" does not)
    length = f"{t.length:.2f}s" if t.length < 10 else f"{t.length:.0f}s"
    bias = round(t.bias * 100)
    return [str(round(t.wear * 100)), str(round(t.wow * 100)), length,
            ("+" if bias > 0 else "") + str(bias)]


def wave_xy(t: Tape, x0, x1, yc, amp, cycles=1.0, worn=True, wobble=None, per_cycle=90):
    """Polyline of the cycle across x0..x1. Fresh at wear 0 keeps its corners."""
    pts = []
    if worn and (t.wear > 0 or t.bias != 0):
        y = t.played()
        N = len(y)
        steps = int(per_cycle * cycles)
        for i in range(steps + 1):
            u = i / steps * cycles
            v = y[int(round((u % 1) * N)) % N]
            pts.append((x0 + (x1 - x0) * i / steps, yc - amp * v))
    else:
        for c in range(int(math.ceil(cycles))):
            for px, py in t.written_points():
                u = c + px
                if u > cycles + 1e-9:
                    break
                pts.append((x0 + (x1 - x0) * u / cycles, yc - amp * py))
    if wobble:
        pts = [(x + wobble(x), y) for x, y in pts]
    return dedupe(pts)


# ---------------------------------------------------------------- v1 · P2 diagram + trace, typeset diagram

def v1(t: Tape) -> Frame:
    f = Frame("v1 · P2 diagram + trace · typeset diagram", header_values(t))
    # left half: the tape path. Capstan fixed; the tension roller sits at the loop's length.
    cy, r = 104, 17
    xa = 44
    xb = xa + 80 + 100 * t.length_pos            # length: position, 80..180 px
    top, bot = cy - r, cy + r
    loop = []
    for i in range(21):                           # around the right roller
        a = -math.pi / 2 + math.pi * i / 20
        loop.append((xb + r * math.cos(a), cy + r * math.sin(a)))
    for i in range(21):                           # around the capstan
        a = math.pi / 2 + math.pi * i / 20
        loop.append((xa + r * math.cos(a), cy + r * math.sin(a)))
    f.poly(loop, fill="none", stroke=S, sw=1.5)
    for x in (xa, xb):
        f.circle(x, cy, r - 3, M, 1.5)
        f.circle(x, cy, 3, G, 1.5)
    # heads under the bottom run
    rec_x, play_x = xa + 40, xa + 72
    for hx in (rec_x, play_x):
        f.poly([(hx - 8, bot + 2), (hx + 8, bot + 2), (hx + 8, bot + 14), (hx - 8, bot + 14)], fill=F, stroke=M, sw=1.5)
        f.rect(hx - 0.75, bot + 2, 1.5, 6, K)                       # head gap
    # bias: field lines fringing from the record gap into the tape (scale)
    sc = 1 + 0.45 * t.bias
    for rr in (4, 8, 12):
        arc = [(rec_x + rr * sc * math.cos(a), bot + 1 - rr * sc * 0.8 * math.sin(a))
               for a in np.linspace(0.15, math.pi - 0.15, 14)]
        f.line(arc, 1.2, G)
    # wow: the flutter arm resting on the top run (rotation about its pivot)
    px, py = xa + 56, top - 30
    ang = math.radians(36 * t.wow)
    arm = top - 4.5 - py
    tip = (px + arm * math.sin(ang), py + arm * math.cos(ang))
    f.line([(px, py), tip], 2, S)
    f.circle(px, py, 3, M, 1.5)
    f.circle(tip[0], tip[1], 3.5, S, 1.5)
    # typeset labels
    f.text(rec_x, bot + 27, "rec", anchor="middle")
    f.text(play_x, bot + 27, "play", anchor="middle")
    f.text(px + 8, py + 4, "wow arm")
    # rule from the play head to the cycle's time axis
    ax_y = 184
    f.line([(play_x, bot + 32), (play_x, ax_y), (458, ax_y)], 1.2, D)
    for i in range(5):
        x = 262 + 49 * i
        f.rect(x - 0.6, ax_y - 4, 1.2, 4, G)
    f.text(262, 200, "0", anchor="middle")
    f.text(458, 200, "1 cycle", anchor="end")
    # right half: the cycle as it plays now; the written cycle ghosted behind once it has worn
    if t.wear > 0:
        f.line(wave_xy(t, 262, 458, 110, 46, worn=False), 1.5, D)
    f.line(wave_xy(t, 262, 458, 110, 46), 2.5, B)
    return f


# ---------------------------------------------------------------- v2 · P3 trace as subject, orthographic elevation

def v2(t: Tape) -> Frame:
    f = Frame("v2 · P3 trace as subject · orthographic elevation", header_values(t))
    yc, half = 112, 44
    x0, x1 = 20, 460

    def edge(y):
        pts = []
        for i in range(61):
            x = x0 + (x1 - x0) * i / 60
            pts.append((x, y + 6 * t.wow * math.sin(x / 34)))     # wow: the tape weaves (edge shape)
        return pts
    f.line(edge(yc - half), 1.5, M)
    f.line(edge(yc + half), 1.5, M)
    # saturation rails: under-bias pulls them in, the trace clips against them (position)
    rail = 36 + 10 * t.bias
    for s in (-1, 1):
        f.line([(x0 + 6, yc + s * rail), (x1 - 6, yc + s * rail)], 1.2, D)
    # splices: one fixed at the left, one at the loop's length; diagonal cuts across the tape
    sx0 = 44
    sx1 = sx0 + 140 + 270 * t.length_pos
    for sx in (sx0, sx1):
        f.line([(sx - 9, yc + half - 2), (sx + 9, yc - half + 2)], 1.5, S)
    # the magnetised cycle along the tape, the subject
    period = 104
    cyc = (x1 - 8 - (x0 + 8)) / period
    wob = None
    f.line(wave_xy(t, x0 + 8, x1 - 8, yc, 30, cycles=cyc), 2.5, B)
    # dimension line under the band: the loop, splice to splice
    dy = 186
    for sx in (sx0, sx1):
        f.line([(sx, yc + half + 6), (sx, dy + 5)], 1.2, G)
    f.line([(sx0, dy), (sx1, dy)], 1.2, G)
    for sx in (sx0, sx1):
        f.line([(sx - 4, dy + 4), (sx + 4, dy - 4)], 1.5, M)        # architect's ticks
    f.text((sx0 + sx1) / 2, dy + 14, "loop", anchor="middle")
    f.text(x1, 52, "elevation", anchor="end")
    return f


# ---------------------------------------------------------------- v3 · P4 stack in depth, survey plan

def v3(t: Tape) -> Frame:
    f = Frame("v3 · P4 stack in depth · survey plan", header_values(t))
    width, amp = 236, 24
    step = 12 + 14 * t.length_pos                  # length: spacing between passes (position)
    ox, oy = 64, 174
    layers = 5
    greys = [B, M, G, D, D]
    # offset line joining the stations at each pass's start (survey traverse)
    f.line([(ox, oy), (ox + step * (layers - 1), oy - step * 0.9 * (layers - 1))], 1.2, F)
    f.line([(ox + width, oy), (ox + width + step * (layers - 1), oy - step * 0.9 * (layers - 1))], 1.2, F)
    for k in reversed(range(layers)):              # back (oldest) first
        bx = ox + step * k + 10 * t.wow * math.sin(k * 1.9)   # wow: passes shear along the tape
        by = oy - step * 0.9 * k
        passes = 4 - k + 4                          # older layers have seen fewer passes
        tk = Tape(wear=t.wear_pos, wow=t.wow, length=t.length_pos, bias=t.bias_pos)
        tk.wear = t.wear * passes / 8
        a = amp * ((1 - 0.3 * t.bias) if k == 0 else 1)          # bias: front layer's level (scale)
        prof = wave_xy(tk, bx, bx + width, by - a - 2, a, per_cycle=56)
        f.poly(prof + [(bx + width, by), (bx, by)], fill=K)     # hidden line: black ground under each profile
        f.line([(bx, by), (bx + width, by)], 1.2, D if k else G)
        f.line(prof, 2 if k == 0 else 1.5, greys[k])
        f.text(bx + width + 8, by + 3, "0" if k == 0 else f"-{k}", col=M if k else S)
    # chainage ticks on the front pass
    for i in range(9):
        x = ox + width * i / 8
        h = 6 if i % 4 == 0 else 3
        f.rect(x - 0.6, oy, 1.2, h, M)
    f.text(ox, oy + 18, "0+00")
    f.text(ox + width, oy + 18, "1+00", anchor="end")
    f.text(ox + width + 8 + step * 4, oy - step * 3.6 - 14, "pass", anchor="start")
    return f


# ---------------------------------------------------------------- v4 · P5 field and figure, patent section

def v4(t: Tape) -> Frame:
    f = Frame("v4 · P5 field and figure · patent section", header_values(t))
    # field: the tape running away from the viewer, in perspective
    vx, near_y, far_y = 240, 192, 124
    nh, fh = 150, 62                              # half widths near/far

    def at(z):                                    # z 0 near .. 1 far, perspective spacing
        p = 1 / (1 + 2.2 * z)
        y = far_y + (near_y - far_y) * (p - 1 / 3.2) / (1 - 1 / 3.2)
        hw = fh + (nh - fh) * (p - 1 / 3.2) / (1 - 1 / 3.2)
        return y, hw
    # wow: the tape's near edge weaves (shape); the far edge is drawn plain
    edge_l = [(vx - nh + 0.0, near_y)]
    f.line([(vx - nh, near_y), (vx - fh, far_y)], 1.5, G)
    f.line([(vx + nh, near_y), (vx + fh, far_y)], 1.5, G)
    last = None
    for i in range(1, 16):
        y, hw = at(i / 15)
        if last is not None and last - y < 5:
            break
        f.line([(vx - hw + 2, y), (vx + hw - 2, y)], 1.2, D)
        last = y
    near = [(vx - nh + 300 * i / 40, near_y + 4 * t.wow * math.sin(i * 0.9)) for i in range(41)]
    f.line(near, 2, S)
    # length: the splice, a brighter cut across the tape, recedes as the loop grows (position)
    ys, hws = at(0.04 + 0.42 * t.length_pos)
    f.line([(vx - hws + 2, ys + 3), (vx + hws - 2, ys - 3)], 1.5, S)
    # figure: the head core in section, the one bright outline
    cx, top, bottom = 240, 50, 148
    oL, oR, iL, iR, iT, iB, g = cx - 42, cx + 42, cx - 28, cx + 28, top + 14, bottom - 16, 2.5
    core = [(cx - g, bottom), (oL + 6, bottom), (oL, bottom - 6), (oL, top + 6), (oL + 6, top),
            (oR - 6, top), (oR, top + 6), (oR, bottom - 6), (oR - 6, bottom), (cx + g, bottom),
            (cx + g, iB + 4), (iR - 4, iB), (iR, iB - 4), (iR, iT + 4), (iR - 4, iT),
            (iL + 4, iT), (iL, iT + 4), (iL, iB - 4), (iL + 4, iB), (cx - g, iB + 4)]
    f.poly(core, fill=K, stroke=B, sw=2)
    # section hatching at 45 degrees, clipped to the core's bars
    bars = [(oL, top, oR, iT), (oL, iT, iL, iB), (iR, iT, oR, iB), (oL, iB, cx - g, bottom), (cx + g, iB, oR, bottom)]
    inset = 2.5
    for c in range(-300, 300, 6):
        for (ax, ay, bx_, by_) in bars:
            ax2, ay2, bx2, by2 = ax + inset, ay + inset, bx_ - inset, by_ - inset
            # line y = x + c clipped to the rect
            lo = max(ax2, ay2 - c)
            hi = min(bx2, by2 - c)
            if hi - lo > 2:
                f.line([(lo, lo + c), (hi, hi + c)], 1, F)
    # coil in section: turns either side of the left leg
    for i in range(5):
        y = iT + 8 + i * 9
        f.circle(oL - 6, y, 3, S, 1.5)
        f.circle(iL + 6, y, 3, S, 1.5)
    # bias: field fringing out of the gap into the tape (scale)
    sc = 1 + 0.45 * t.bias
    for rr in (5, 10, 15):
        arc = [(cx + rr * sc * math.cos(a), bottom + 1 + rr * sc * 0.55 * math.sin(a))
               for a in np.linspace(0.2, math.pi - 0.2, 16)]
        f.line(arc, 1.2, M)
    # reference numerals, patent style
    for (lx, ly, tx, ty, s) in ((oR, top + 18, 318, 54, "10"), (cx + 3, bottom + 4, 318, 140, "12"),
                                 (vx + 120, 178, 410, 170, "14"), (oL - 9, iT + 12, 162, 64, "16")):
        f.line([(lx, ly), (tx - (4 if tx > lx else -4), ty - 3)], 1, G)
        f.text(tx, ty, s, anchor="start" if tx > lx else "end")
    # activity strip: the loop in 24 segments; worn-through segments are dropouts (count)
    cells = 24
    worn = int(round(cells * min(1.0, t.wear * 1.6)))
    order = [(i * 7) % cells for i in range(cells)]
    for i in range(cells):
        x = 96 + i * 12
        if i in order[:worn]:
            f.rect(x, 200, 8, 6, S)
        else:
            f.poly([(x, 200), (x + 8, 200), (x + 8, 206), (x, 206)], fill=K, stroke=D, sw=1.5)
    return f


# ---------------------------------------------------------------- v5 · P14 loom, hidden-line isometric

def v5(t: Tape) -> Frame:
    f = Frame("v5 · P14 loom · hidden-line isometric (stretch)", header_values(t))
    threads = int(round(8 * 3 ** t.length_pos))     # length: thread count, 8..24 (count)
    rows = 4
    u = 12 * 14 / max(threads, 14) if threads > 14 else 12
    c, s = math.cos(math.radians(30)) * u, math.sin(math.radians(30)) * u
    depth = 1.7
    span_x = (threads - 1 + 0.7) * c + (rows - 1) * depth * c
    ox = 240 - span_x / 2 + (rows - 1) * depth * c
    oy = 64

    def P(X, Y, Z):
        return (ox + (X - Y) * c, oy + (X + Y) * s - Z)

    ceiling = 30 + 10 * min(t.bias, 0) * 1.2          # bias: under-bias lowers the cap height
    # warp threads under the slabs
    for i in range(threads):
        X = i + 0.35
        f.line([P(X, -0.6, 0), P(X, (rows - 1) * depth + 1.3, 0)], 1.2, F)
    boxes = []
    for r in range(rows):                           # r 0 = oldest (back), rows-1 = now (front)
        age = rows - 1 - r
        tr = Tape(wear=t.wear_pos, wow=t.wow, length=t.length_pos, bias=t.bias_pos)
        tr.wear = t.wear * (r + 1) / rows
        prof = tr.played() if (tr.wear > 0 or tr.bias != 0) else None
        shear = 1.4 * t.wow * math.sin(r * 2.1)        # wow: rows slide along the warp (position)
        for i in range(threads):
            x = (i + 0.5) / threads
            v = prof[int(x * len(prof)) % len(prof)] if prof is not None else tr.written(x)
            h = 5 + 13 * (v + 1)
            capped = h > ceiling
            h = min(h, ceiling)
            boxes.append((i + r * depth + shear, i + shear, r * depth, h, age, capped))
    boxes.sort(key=lambda b: b[0])
    edge = {0: B, 1: M, 2: G, 3: D}
    for _, X, Y, h, age, capped in boxes:
        w, d = 0.7, 0.7
        top = [P(X, Y, h), P(X + w, Y, h), P(X + w, Y + d, h), P(X, Y + d, h)]
        right = [P(X + w, Y, h), P(X + w, Y + d, h), P(X + w, Y + d, 0), P(X + w, Y, 0)]
        front = [P(X, Y + d, h), P(X + w, Y + d, h), P(X + w, Y + d, 0), P(X, Y + d, 0)]
        col = edge[age]
        if age == 0:   # the pass playing now: solid
            f.poly(right, fill=F, stroke=col, sw=1.5)
            f.poly(front, fill=D, stroke=col, sw=1.5)
            f.poly(top, fill=S if not capped else S2, stroke=col, sw=1.5)
        else:          # earlier passes: hidden-line wire, black fill
            f.poly(right, fill=K, stroke=col, sw=1.2)
            f.poly(front, fill=K, stroke=col, sw=1.2)
            f.poly(top, fill=K, stroke=col, sw=1.2)
    # pass labels at the right end of each row
    for r in range(rows):
        age = rows - 1 - r
        x, y = P(threads + 0.6, r * depth + 0.35, 0)
        f.text(x + 4, y + 4, "now" if age == 0 else f"-{age}", col=S if age == 0 else M)
    return f


def main(argv: list[str]) -> None:
    kv = {}
    for a in argv:
        k, v = a.split("=")
        kv[k] = float(v)
    t = Tape(**kv)
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        out = HERE / name / "rest.svg"
        out.parent.mkdir(exist_ok=True)
        out.write_text(fn(t).svg())
        print(out)


if __name__ == "__main__":
    main(sys.argv[1:])
