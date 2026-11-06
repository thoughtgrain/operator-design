#!/usr/bin/env python3
"""Subject-pass sketches for sieve: five rest frames, one per direction.

    python3 screens/sieve/passes/01-subject/sketch.py

Writes v1..v5/rest.svg (480 x 220, stock header kept, controls at default).
Sketches, not frames: they show the subject at rest so the five can be judged
side by side at 1:1. Moving parts carry sieve_node_<i> ids to show intent.

Defaults (definition.json): mesh 2nd (keep every 2nd harmonic), shake 0,
keep 83 ms, mix 100 %.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Defaults, as the screen would see them.
MESH = 2          # keep every 2nd harmonic
SHAKE = 0.0
KEEP = 0.4        # normalised control position (83 ms)
MIX = 1.0
H = 16            # harmonics drawn

C_HI, C_2, C_3, C_MID, C_LOW, C_GND, C_FILL = ("#CDCDCD", "#AFAFAF", "#969696", "#7D7D7D",
                                               "#646464", "#4B4B4B", "#323232")
HAIR, LINE, SUBJ = 1.1, 1.5, 2.2
FONT = "UniversNextPro-Light"


def kept(k: int) -> bool:
    return k % MESH == 0


def amp(k: int) -> float:
    return 1.0 / k ** 0.7


def f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


class Frame:
    def __init__(self) -> None:
        self.items: list[str] = []
        self.node = 0

    def nid(self, bind: bool) -> str:
        if not bind:
            return ""
        s = f' id="sieve_node_{self.node}"'
        self.node += 1
        return s

    # A line: a thin closed ribbon of width w around a polyline.
    def rib(self, pts, w, col, bind=False):
        pts = [p for i, p in enumerate(pts) if i == 0 or math.dist(p, pts[i - 1]) > 0.3]
        if len(pts) < 2:
            return
        if len(pts) > 32:  # one subpath holds 64 points: split long lines into runs
            for a in range(0, len(pts) - 1, 31):
                self.rib(pts[a:a + 32], w, col, bind)
            return
        h = w / 2
        left, right = [], []
        n = len(pts)
        for i in range(n):
            if i == 0:
                dx, dy = pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]
                L = math.hypot(dx, dy); nx, ny = -dy / L, dx / L; m = 1
            elif i == n - 1:
                dx, dy = pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]
                L = math.hypot(dx, dy); nx, ny = -dy / L, dx / L; m = 1
            else:
                ax, ay = pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]
                bx, by = pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]
                la, lb = math.hypot(ax, ay), math.hypot(bx, by)
                n1 = (-ay / la, ax / la); n2 = (-by / lb, bx / lb)
                nx, ny = n1[0] + n2[0], n1[1] + n2[1]
                L = math.hypot(nx, ny) or 1
                nx, ny = nx / L, ny / L
                cos = max(0.3, nx * n1[0] + ny * n1[1])
                m = min(1 / cos, 2.5)
            left.append((pts[i][0] + nx * h * m, pts[i][1] + ny * h * m))
            right.append((pts[i][0] - nx * h * m, pts[i][1] - ny * h * m))
        ring = left + right[::-1]
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in ring) + " Z"
        self.items.append(f'<path{self.nid(bind)} d="{d}" fill="{col}" stroke="none" stroke-width="0"/>')

    # A closed outline with a black body (hidden-line), or an explicit fill.
    def shape(self, pts, w, col, fill="#000000", bind=False):
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
        self.items.append(f'<path{self.nid(bind)} d="{d}" fill="{fill}" stroke="{col}" stroke-width="{w}"/>')

    def circle(self, cx, cy, r, col, fill="#000000", w=LINE, bind=False):
        self.items.append(f'<circle{self.nid(bind)} cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}" stroke="{col}" stroke-width="{w}"/>')

    def dot(self, cx, cy, r, col, bind=False):
        self.items.append(f'<circle{self.nid(bind)} cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{col}" stroke="none" stroke-width="0"/>')

    def text(self, x, y, s, col=C_MID, size=10):
        self.items.append(f'<text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{col}" stroke="none" '
                          f'font-family="{FONT}" font-size="{size}px">{s}</text>')

    def dashes(self, a, b, w, col, dash=4, gap=4):
        L = math.dist(a, b)
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        t = 0.0
        while t < L:
            e = min(t + dash, L)
            if e - t >= 3:
                self.rib([(a[0] + ux * t, a[1] + uy * t), (a[0] + ux * e, a[1] + uy * e)], w, col)
            t += dash + gap

    def svg(self) -> str:
        header = HEADER
        body = "\n  ".join(self.items)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">\n'
                f'  <g id="preview_canvas">\n    <rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>\n  </g>\n'
                f'{header}\n'
                f'  <path id="sieve_palette_0" d="M 700 300 L 704 300 L 704 304 Z" fill="#CDCDCD" stroke="#CDCDCD" stroke-width="2"/>\n'
                f'  <path id="sieve_palette_1" d="M 710 300 L 714 300 L 714 304 Z" fill="#7D7D7D" stroke="#7D7D7D" stroke-width="2"/>\n'
                f'  <path id="sieve_palette_2" d="M 720 300 L 724 300 L 724 304 Z" fill="#4B4B4B" stroke="#4B4B4B" stroke-width="2"/>\n'
                f'  {body}\n</svg>\n')


def _header() -> str:
    steps = ["#000000", "#323232", "#4B4B4B", "#646464", "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD"]
    out = ['  <g id="preview_header">']
    for i, c in enumerate(steps):
        out.append(f'    <rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
    titles = ["mesh", "shake", "keep", "mix"]
    values = ["2nd", "0", "83ms", "100"]
    for i in range(4):
        col = "#CBCBCB" if i < 2 else "#000000"
        out.append(f'    <text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{col}" stroke="none" '
                   f'font-family="{FONT}" font-size="10px">{titles[i]}</text>')
        out.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{col}" stroke="none" '
                   f'font-family="{FONT}" font-size="20px">{values[i]}</text>')
    out.append("  </g>")
    return "\n".join(out)


HEADER = _header()


def ellipse(cx, cy, rx, ry, n=40, a0=0.0, a1=2 * math.pi):
    full = abs(a1 - a0 - 2 * math.pi) < 1e-9
    m = n if full else n + 1
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(m)]


# ---------------------------------------------------------------- v1
def v1() -> Frame:
    """P1 section drawing, orthographic elevation: a riddle seen dead side-on,
    the input's harmonics falling as rods onto its mesh plate."""
    fr = Frame()
    x0, x1 = 112, 372            # plate span
    py = 122                     # plate line
    xs = [x0 + 10 + (k - 1) * (x1 - x0 - 20) / (H - 1) for k in range(1, H + 1)]
    cx = (x0 + x1) / 2
    # centre line (chain), hairline, dim
    for y in range(30, 212, 12):
        fr.rib([(cx, y), (cx, min(y + 6, 210))], HAIR, C_GND)
    # rods above the plate: the input spectrum, lengths by amplitude
    for k, x in enumerate(xs, 1):
        top = py - 6 - 74 * amp(k)
        col = C_3 if kept(k) else C_LOW
        fr.rib([(x, top), (x, py - 6)], LINE if kept(k) else HAIR, col)
    # riddle rim in elevation: a shallow band (black body, line outline)
    fr.shape([(x0 - 8, py - 5), (x1 + 8, py - 5), (x1 + 8, py + 9), (x0 - 8, py + 9)], LINE, C_MID)
    # rim thickness ticks
    for x in (x0 - 2, x1 + 2):
        fr.rib([(x, py - 4), (x, py + 8)], HAIR, C_LOW)
    # the mesh plate: one bright subject ribbon segment between each hole
    hole = 5.0
    segs, start = [], x0
    for k, x in enumerate(xs, 1):
        if kept(k):
            segs.append((start, x - hole))
            start = x + hole
    segs.append((start, x1))
    for a, b in segs:
        fr.rib([(a, py + 2), (b, py + 2)], SUBJ, C_HI, bind=True)
    # rejected rods rest on the plate: short stubs, dim
    # kept rods fall through: below the plate, bright-ish, length = ring (keep)
    ring = 18 + 70 * KEEP
    for k, x in enumerate(xs, 1):
        if kept(k):
            fr.rib([(x, py + 12), (x, py + 12 + ring * (0.45 + 0.55 * amp(k) / amp(MESH)))], LINE, C_2, bind=True)
    # the bypass gate on the left rim: closed (flush) at mix 100, swings down as mix falls
    ang = math.radians(70 * (1 - MIX))
    gx, gy = x0 - 8, py + 9
    L = 30
    fr.rib([(gx, gy + 1), (gx - L * math.cos(ang), gy + 1 + L * math.sin(ang))], LINE, C_MID, bind=True)
    fr.circle(gx, gy + 1, 2.5, C_MID, w=LINE)
    # shake: offset dimension under the riddle (0 at rest): extension lines + leader
    dy = 204
    fr.rib([(x0 - 8, py + 14), (x0 - 8, dy + 3)], HAIR, C_GND)
    fr.rib([(x1 + 8, py + 14), (x1 + 8, dy + 3)], HAIR, C_GND)
    fr.rib([(x0 - 8, dy), (x1 + 8, dy)], HAIR, C_LOW)
    for x in (x0 - 8, x1 + 8):
        fr.rib([(x - 3, dy + 3), (x + 3, dy - 3)], HAIR, C_LOW)
    fr.text(cx - 9, dy - 4, "± 0", C_MID)
    # harmonic labels at the plate ends
    fr.text(xs[0] - 6, py - 84, "h1", C_MID)
    fr.text(xs[-1] - 8, py - 84 + 60, "h16", C_MID)
    fr.text(392, py + 6, "elev. a", C_MID)
    return fr


# ---------------------------------------------------------------- v2
def v2() -> Frame:
    """P2 diagram + trace, survey plan: the riddle surveyed from above (left)
    and the output spectrum as a long-section profile (right)."""
    fr = Frame()
    cx, cy, R = 120, 120, 80
    # rim, plan
    fr.shape(ellipse(cx, cy, R, R, 56), LINE, C_MID)
    # survey grid ticks inside: hairline crosses at the grid nodes, dim
    sp = 30
    origin = (cx - 1.5 * sp + 40 * SHAKE, cy - 1.5 * sp)
    k = 0
    for j in range(4):
        for i in range(4):
            k += 1
            x, y = origin[0] + i * sp, origin[1] + j * sp
            if kept(k):
                fr.circle(x, y, 5.5, C_2, w=LINE, bind=True)
            else:
                fr.rib([(x - 4, y), (x + 4, y)], HAIR, C_LOW)
                fr.rib([(x, y - 4), (x, y + 4)], HAIR, C_LOW)
            fr.text(x + 7, y - 6, str(k), C_MID)
    # traverse line from the rim to the first open station (survey leg)
    fr.text(16, 48, "plan", C_MID)
    # right: long-section profile of the output spectrum
    X0, X1, base = 262, 462, 182
    fr.rib([(X0, base), (X1, base)], HAIR, C_LOW)                       # datum
    for kk in range(1, H + 1):
        x = X0 + 6 + (kk - 1) * (X1 - X0 - 12) / (H - 1)
        fr.rib([(x, base), (x, base + (6 if kk % 4 == 0 else 3) + 1)], HAIR, C_LOW)  # chainage
    fr.text(X0 + 2, base + 18, "h1", C_MID)
    fr.text(X1 - 16, base + 18, "h16", C_MID)
    width = 1.6 + 7 * (1 - KEEP)        # peak half-width in px: narrower as keep rises
    pts = []
    for i in range(62):
        x = X0 + (X1 - X0) * i / 61
        y = 0.0
        for kk in range(1, H + 1):
            if not kept(kk):
                continue
            xk = X0 + 6 + (kk - 1) * (X1 - X0 - 12) / (H - 1)
            y = max(y, amp(kk) * math.exp(-((x - xk) / width) ** 2))
        pts.append((x, base - 6 - 120 * y))
    fr.rib(pts, SUBJ, C_HI, bind=True)
    # dry profile: lies on the datum at mix 100 (hidden under it)
    fr.rib([(X0, base - 3 - 60 * (1 - MIX)), (X1, base - 3 - 60 * (1 - MIX) * 0.3)], HAIR, C_GND, bind=True)
    fr.text(X0, 48, "long section", C_MID)
    return fr


# ---------------------------------------------------------------- v3
def v3() -> Frame:
    """P3 trace as subject, patent section: the sieve's output wave emerging
    from a sectioned wall and ringing out between its envelope lines."""
    fr = Frame()
    X0, X1, cy = 52, 452, 116
    tau = 60 + 900 * KEEP ** 2           # px: ring-out length grows with keep
    A = 46
    # wall in section at the left: outline + 45 degree hatch
    wx0, wx1, wy0, wy1 = 34, 46, 58, 176
    fr.shape([(wx0, wy0), (wx1, wy0), (wx1, wy1), (wx0, wy1)], LINE, C_MID)
    for t in range(int(wy0) + 6, int(wy1) + 8, 6):
        a = (wx0 + 1.5, min(t, wy1 - 1.5)); b = (wx1 - 1.5, t - (wx1 - wx0 - 3))
        if b[1] < wy0 + 1.5:
            b = (wx0 + 1.5 + (t - wy0 - 1.5), wy0 + 1.5)
        if a[1] > wy1 - 1.5:
            continue
        if math.dist(a, b) > 3:
            fr.rib([a, b], HAIR, C_LOW)
    # axis
    fr.rib([(wx1 + 2, cy), (X1 + 6, cy)], HAIR, C_GND)
    # envelope lines (dashed hairline): the keep control's own part
    for s in (-1, 1):
        prev = None
        for i in range(0, 41):
            x = X0 + (X1 - X0) * i / 40
            y = cy + s * (A * math.exp(-(x - X0) / tau) + 6)
            if prev and i % 2 == 1:
                fr.rib([prev, (x, y)], HAIR, C_MID)
            prev = (x, y)
    # the trace: kept harmonics over two fundamental periods, ringing out
    n = 150
    P = (X1 - X0) / 2
    raw = []
    for i in range(n):
        x = X0 + (X1 - X0) * i / (n - 1)
        s = sum(amp(k) * math.sin(2 * math.pi * k * (x - X0) / P) for k in range(1, 9) if kept(k))
        raw.append((x, s))
    peak = max(abs(s) for _, s in raw)
    pts = [(x, cy - A * (s / peak) * math.exp(-(x - X0) / tau)) for x, s in raw]
    for a in range(0, n - 1, 49):
        fr.rib(pts[a:a + 51], SUBJ, C_HI, bind=True)
    # reference numerals with hairline leaders
    def ref(num, tx, ty, px, py):
        fr.rib([(tx + 6, ty + 3), (px, py)], HAIR, C_LOW)
        fr.text(tx - 6, ty, num, C_MID)
    ref("10", 120, 196, 132, pts[int((132 - X0) / (X1 - X0) * (n - 1))][1] + 4)
    ref("12", 300, 56, 296, cy - A * math.exp(-(296 - X0) / tau) - 9)
    ref("14", 410, 150, 404, cy + 2)
    ref("16", 26, 196, 37, 172)
    fr.text(400, 206, "fig. 1", C_MID)
    return fr


# ---------------------------------------------------------------- v4
def tray(fr, cx, y, rx, ry, rim, w, col, bind=False):
    """One round sieve in isometric: the front of its side band, then its screen."""
    front_top = ellipse(cx, y, rx, ry, 30, 0, math.pi)                 # right -> left, via the front
    front_bot = ellipse(cx, y + rim, rx, ry, 30, math.pi, 0)[::-1]     # left -> right
    front_bot = ellipse(cx, y + rim, rx, ry, 30, 0, math.pi)[::-1]
    fr.shape(front_top + front_bot, w, col, bind=bind)
    fr.shape(ellipse(cx, y, rx, ry, 48), w, col, bind=bind)


def v4() -> Frame:
    """P4 stack in depth, hidden-line isometric: the eight meshes as an
    exploded stack of round sieves receding up and to the right, coarsest at
    the back; the tray at the mesh is lit and holds the kept harmonics."""
    fr = Frame()
    rx, ry, rim = 46, 11, 5
    dx, dy = 27, -16
    fx, fy = 134, 184                     # front (finest) tray centre
    labels = ["all", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th"]
    lit = MESH - 1
    centre = lambda i: (fx + (7 - i) * dx, fy + (7 - i) * dy)
    # feed spout behind the coarsest tray: aimed into the stack at mix 100,
    # swings aside as mix falls
    bx, by = centre(0)
    ang = math.radians(115 - 60 * (1 - MIX))
    px, py = bx + 34, by - 30
    fr.rib([(px, py), (px + 18 * math.cos(ang), py + 18 * math.sin(ang))], 3.0, C_MID, bind=True)
    fr.circle(px, py, 3, C_MID, w=LINE)
    rnd = random.Random(3)
    for i in range(8):                    # back to front
        cx, y = centre(i)
        on = i == lit
        tray(fr, cx, y, rx, ry, rim, SUBJ if on else LINE, C_HI if on else C_LOW, bind=on)
        if on:
            for t in range(-36, 37, 9):   # mesh chords on the lit screen
                e = math.sqrt(max(0.0, 1 - (t / rx) ** 2))
                fr.rib([(cx + t, y - ry * e * 0.7), (cx + t, y + ry * e * 0.7)], HAIR, C_GND)
            ks = [k for k in range(1, H + 1) if kept(k)]
            for j, k in enumerate(ks):    # kept harmonics heaped; heap height = keep
                gx = cx - 30 + 60 * j / max(1, len(ks) - 1)
                gy = y + 2 - (4 + 14 * KEEP) * math.exp(-((gx - cx) / 22) ** 2) + rnd.uniform(-1, 1)
                fr.dot(gx, gy, 1.9 + 1.0 * amp(k) / amp(MESH), C_HI, bind=True)
        fr.rib([(cx + rx + 3, y + 6), (cx + rx + 9, y + 6)], HAIR, C_GND)
        fr.text(cx + rx + 12, y + 10, labels[i], C_HI if on else C_MID)
    fr.text(fx - rx - 2, fy - 26, "fine", C_MID)
    fr.text(bx + 64, by - 26, "coarse", C_MID)
    return fr


# ---------------------------------------------------------------- v5
def v5() -> Frame:
    """P11 instrument stack, star atlas: the harmonic series charted as a
    constellation figure of an organ rank; the sieve's kept partials are the
    named stars, joined by the figure line."""
    fr = Frame()
    n = 12
    X0, X1, mouth = 70, 420, 150
    xs = [X0 + (X1 - X0) * i / (n - 1) for i in range(n)]
    # atlas ground: two declination arcs and the graduated border, at ground grey
    for dec in (66, 186):
        pts = [(x, dec + 0.00045 * (x - 245) ** 2 * (1 if dec < 100 else -1)) for x in range(36, 456, 12)]
        fr.rib(pts, HAIR, C_FILL)
    for i, x in enumerate(xs):
        fr.rib([(x, 206), (x, 211)], HAIR, C_LOW)
    fr.rib([(X0 - 14, 211), (X1 + 14, 211)], HAIR, C_GND)
    # figure lines: pipe outlines (body above the mouth, foot below), hairline ground grey
    for i, x in enumerate(xs):
        k = i + 1
        L = 104 / k ** 0.72
        w = 6.5 - 2.6 * i / (n - 1)
        top = mouth - 6 - L
        fr.rib([(x - w, mouth - 4), (x - w, top), (x + w, top), (x + w, mouth - 4)], HAIR, C_GND)
        fr.rib([(x - w, mouth + 4), (x - 1.5, mouth + 22), (x + 1.5, mouth + 22), (x + w, mouth + 4)], HAIR, C_GND)
    # the figure line through the kept stars (constellation), line weight, mid-bright
    kp = [(xs[i], mouth) for i in range(n) if kept(i + 1)]
    for a, b in zip(kp, kp[1:]):
        d = math.dist(a, b)
        ux, uy = (b[0] - a[0]) / d, (b[1] - a[1]) / d
        fr.rib([(a[0] + ux * 7, a[1] + uy * 7), (b[0] - ux * 7, b[1] - uy * 7)], LINE, C_3)
    # stars at the mouths: magnitude by amplitude; kept stars bright and large
    for i, x in enumerate(xs):
        k = i + 1
        if kept(k):
            fr.dot(x, mouth, (2.4 + 3.2 * amp(k)) * (0.8 + 0.4 * KEEP), C_HI, bind=True)
            fr.text(x - 3, mouth + 36, str(k), C_3)
        else:
            fr.dot(x, mouth, 1.6 + 0.8 * (1 - MIX) + 0.6 * amp(k), C_MID, bind=True)
    fr.text(14, 56, "fistula", C_MID)
    fr.text(X1 + 4, 56, "h1–h12", C_MID)
    return fr


def main() -> None:
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        out = HERE / name / "rest.svg"
        out.parent.mkdir(exist_ok=True)
        out.write_text(fn().svg())
        print(out)


if __name__ == "__main__":
    main()
