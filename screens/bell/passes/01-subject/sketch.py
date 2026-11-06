#!/usr/bin/env python3
"""Bell, subject pass 01: five rest-frame sketches, one per direction.

    python3 screens/bell/passes/01-subject/sketch.py

Writes v1..v5/rest.svg (480 x 220, from opxy/templates/frame.svg's header and
authoring rules) and v1..v5/candidate.json. Every control at its default:
depth 12 dB, air 0.2 s, knee 6 dB, gain x2.00.

An effect page gets the slots, not the audio (constraints.md, Which machines
draw a screen), so every trace below is the compressor's model run on one fixed
reference passage (four hits), computed from the parameters alone. Nothing here
follows the live signal.

Every leaf is a closed path, circle or text with explicit paint; lines are
closed ribbons; grey only. Parts that a control moves carry device ids
(bell_node_<i>); still artwork is unbound.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 480, 220

# Stock greys (constraints.md, Header greys).
BRIGHT, G175, G150, G125, G100, G75, G50 = ("#CDCDCD", "#AFAFAF", "#969696", "#7D7D7D",
                                           "#646464", "#4B4B4B", "#323232")
BLACK = "#000000"
HAIR, LINE, SUBJ = 1.0, 1.5, 2.0   # craft.md line weights
FONT = "UniversNextPro-Light"

# Defaults from definition.json (normalised) and their real values.
P = {"depth": 0.25, "air": 0.5, "knee": 0.25, "gain": 0.25}
DEPTH_DB = 48 * P["depth"]                       # 12 dB under full scale
AIR_S = 0.02 * (2 / 0.02) ** P["air"]            # 0.2 s release
KNEE_DB = 24 * P["knee"]                         # 6 dB knee
GAIN = 1 * 16 ** P["gain"]                       # x2.00 makeup
RATIO = 4.0                                      # fixed above the threshold
ATTACK_S = 0.005
CAPTIONS = ["12", "0.2s", "6.0", "2.00"]


# ---------------------------------------------------------------- the compressor model
HITS = [(0.05, 1.0), (0.31, 0.5), (0.50, 0.9), (0.76, 0.42)]   # reference passage: time s, peak
SR = 1000                                                       # model rate, 1 ms steps


def env_in(t: float) -> float:
    a = 0.012
    for t0, pk in HITS:
        if t >= t0:
            dt = t - t0
            a += pk * (dt / 0.004 if dt < 0.004 else math.exp(-(dt - 0.004) / 0.09))
    return min(a, 1.0)


def curve(x: float, thr: float, knee: float) -> float:
    """Static gain computer (dB in, dB out), soft knee of width `knee`."""
    over = x - thr
    if 2 * over < -knee:
        return x
    if knee > 0 and 2 * abs(over) <= knee:
        return x + (1 / RATIO - 1) * (over + knee / 2) ** 2 / (2 * knee)
    return thr + over / RATIO


def run(depth=DEPTH_DB, air=AIR_S, knee=KNEE_DB, gain=GAIN, length=1.0):
    """Returns per-ms lists: input dB, gain reduction dB (smoothed), output dB (with makeup)."""
    att = math.exp(-1 / (ATTACK_S * SR))
    rel = math.exp(-1 / (air * SR))
    g = 0.0
    xs, grs, ys = [], [], []
    for i in range(int(length * SR)):
        x = 20 * math.log10(env_in(i / SR))
        target = curve(x, -depth, knee) - x
        c = att if target < g else rel
        g = c * g + (1 - c) * target
        xs.append(x)
        grs.append(g)
        ys.append(x + g + 20 * math.log10(gain))
    return xs, grs, ys


def amp(db: float) -> float:
    return 10 ** (db / 20)


# ---------------------------------------------------------------- drawing kit
def n(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


class Frame:
    def __init__(self) -> None:
        self.parts: list[str] = []
        self.node = 0

    def _id(self, bound: bool) -> str:
        if not bound:
            return ""
        i = self.node
        self.node += 1
        return f' id="bell_node_{i}"'

    def poly(self, pts, fill="none", stroke=BRIGHT, sw=SUBJ, bound=False) -> None:
        pts = dedupe(pts)
        assert 3 <= len(pts) <= 64, len(pts)
        d = "M " + " L ".join(f"{n(x)} {n(y)}" for x, y in pts) + " Z"
        stroke_attr = f'stroke="{stroke}" stroke-width="{n(sw)}"' if stroke != "none" else 'stroke="none"'
        self.parts.append(f'<path{self._id(bound)} d="{d}" fill="{fill}" {stroke_attr}/>')

    def line(self, pts, w=HAIR, colour=G100, bound=False) -> None:
        """A polyline as a thin filled closed ribbon (constraints.md: never a stroke traced back)."""
        pts = dedupe(pts)
        for chunk in chunks(pts, 31):
            self.poly(ribbon(chunk, w), fill=colour, stroke="none", bound=bound)

    def dashes(self, a, b, dash=4, gap=4, w=HAIR, colour=G100) -> None:
        L = math.dist(a, b)
        k = 0.0
        while k < L - 1:
            e = min(k + dash, L)
            if e - k < 3:
                break
            p = (a[0] + (b[0] - a[0]) * k / L, a[1] + (b[1] - a[1]) * k / L)
            q = (a[0] + (b[0] - a[0]) * e / L, a[1] + (b[1] - a[1]) * e / L)
            self.line([p, q], w=w, colour=colour)
            k += dash + gap

    def circle(self, cx, cy, r, fill=BLACK, stroke=G100, sw=HAIR, bound=False) -> None:
        stroke_attr = f'stroke="{stroke}" stroke-width="{n(sw)}"' if stroke != "none" else 'stroke="none"'
        self.parts.append(f'<circle{self._id(bound)} cx="{n(cx)}" cy="{n(cy)}" r="{n(r)}" fill="{fill}" {stroke_attr}/>')

    def text(self, x, y, s, colour=G125, size=10) -> None:
        self.parts.append(f'<text transform="matrix(1 0 0 1 {n(x)} {n(y)})" fill="{colour}" stroke="none" '
                          f'font-family="{FONT}" font-size="{size}px">{s}</text>')

    def svg(self, title: str) -> str:
        palette = "\n  ".join(
            f'<path id="bell_palette_{i}" d="M {700 + 10 * i} 300 L {704 + 10 * i} 300 L {704 + 10 * i} 304 Z" '
            f'fill="{c}" stroke="{c}" stroke-width="2"/>'
            for i, c in enumerate([BRIGHT, G150, G100, G75, G50, BLACK]))
        body = "\n  ".join(self.parts)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n'
                f'  <!-- bell · subject pass 01 · {title} · rest (defaults). Generated by sketch.py -->\n'
                f'  <g id="preview_canvas">\n    <rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>\n  </g>\n'
                f'{header()}\n  {palette}\n  {body}\n</svg>\n')


def dedupe(pts):
    out = []
    for p in pts:
        p = (round(p[0], 2), round(p[1], 2))
        if not out or math.dist(out[-1], p) >= 0.25:
            out.append(p)
    if len(out) > 2 and math.dist(out[0], out[-1]) < 0.25:
        out.pop()
    return out


def chunks(pts, size):
    if len(pts) <= size:
        yield pts
        return
    i = 0
    while i < len(pts) - 1:
        yield pts[i:i + size]
        i += size - 1


def norm(v):
    l = math.hypot(*v) or 1.0
    return (v[0] / l, v[1] / l)


def ribbon(pts, w):
    """Offset a polyline both ways by w/2 with limited mitre joins and flat ends."""
    h = w / 2
    left, right = [], []
    for i, p in enumerate(pts):
        if i == 0:
            d = (pts[1][0] - p[0], pts[1][1] - p[1])
            nx, ny = norm((-d[1], d[0]))
            m = 1.0
        elif i == len(pts) - 1:
            d = (p[0] - pts[i - 1][0], p[1] - pts[i - 1][1])
            nx, ny = norm((-d[1], d[0]))
            m = 1.0
        else:
            a = norm((p[0] - pts[i - 1][0], p[1] - pts[i - 1][1]))
            b = norm((pts[i + 1][0] - p[0], pts[i + 1][1] - p[1]))
            n1, n2 = (-a[1], a[0]), (-b[1], b[0])
            nx, ny = norm((n1[0] + n2[0], n1[1] + n2[1]))
            cos = nx * n1[0] + ny * n1[1]
            m = min(1 / max(cos, 1e-3), 2.5)
        left.append((p[0] + nx * h * m, p[1] + ny * h * m))
        right.append((p[0] - nx * h * m, p[1] - ny * h * m))
    return left + right[::-1]


def header() -> str:
    steps = [BLACK, G50, G75, G100, G125, G150, G175, BRIGHT]
    rows = [f'    <rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>' for i, c in enumerate(steps)]
    for i, label in enumerate(["depth", "air", "knee", "gain"]):
        ink = "#CBCBCB" if i < 2 else BLACK
        rows.append(f'    <text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{ink}" stroke="none" '
                    f'font-family="{FONT}" font-size="10px">{label}</text>')
        rows.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{ink}" stroke="none" '
                    f'font-family="{FONT}" font-size="20px">{CAPTIONS[i]}</text>')
    return '  <g id="preview_header">\n' + "\n".join(rows) + "\n  </g>"


def arc(cx, cy, r, a0, a1, k=8):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / k), cy + r * math.sin(a0 + (a1 - a0) * i / k)) for i in range(k + 1)]


def resample(vals, k):
    """k evenly spaced samples (max-hold per bucket, so peaks survive)."""
    step = len(vals) / k
    return [max(vals[int(i * step):max(int((i + 1) * step), int(i * step) + 1)]) for i in range(k)]


def bell_profile(cx, top, rim, half_rim, half_top, r):
    """Outer profile of a bell in section, left rim -> crown -> right rim. r is the shoulder radius (knee)."""
    r = max(2.0, min(r, half_top - 2, rim - top - 4))
    left = [(cx - half_rim, rim), (cx - half_top, top + r)]
    left += arc(cx - half_top + r, top + r, r, math.pi, 1.5 * math.pi, 6)[1:]
    right = arc(cx + half_top - r, top + r, r, 1.5 * math.pi, 2 * math.pi, 6)
    return left + right + [(cx + half_rim, rim)]


# ---------------------------------------------------------------- v1 · P2 diagram + trace, patent section
def v1() -> Frame:
    """Fig. 1: the bell in section on its cable under a surface line, water rising inside to the air pocket.
    Fig. 2: the output of the reference passage (bright) over the input (grey)."""
    f = Frame()
    # --- fig. 1 (columns 1-2): the bell
    surf = 42
    cx = 118
    f.line([(14, surf), (226, surf)], w=HAIR, colour=G100)
    for row, y in enumerate((surf + 6, surf + 12)):           # patent liquid convention: short dashes
        for x in range(20 + row * 9, 222, 18):
            if abs(x + 3 - cx) > 60:
                f.line([(x, y), (x + 6, y)], w=HAIR, colour=G75)
    top = 58 + DEPTH_DB * 1.5                                 # depth: position, 72 px over the range
    rim = top + 80
    half_rim, half_top, wall = 54, 32, 5
    r = 4 + KNEE_DB * 1.4                                     # knee: shoulder radius, 4 -> 38 px
    outer = bell_profile(cx, top, rim, half_rim, half_top, r)
    inner = bell_profile(cx, top + wall, rim, half_rim - wall, half_top - wall, r - wall)
    # air: the pocket's share of the bell, 35 % -> 90 %
    air_frac = 0.35 + 0.55 * P["air"]
    water_y = top + wall + (rim - top - wall) * air_frac
    iw = half_rim - wall - (half_rim - half_top) * (rim - water_y) / (rim - top) + 0.5
    for y in range(int(water_y) + 6, int(rim) - 2, 6):       # water inside, below the waterline
        wy = half_rim - wall - (half_rim - half_top) * (rim - y) / (rim - top)
        for x in range(int(cx - wy) + 6, int(cx + wy) - 10, 14):
            f.line([(x, y), (x + 6, y)], w=HAIR, colour=G75)
    f.line([(cx - iw, water_y), (cx + iw, water_y)], w=LINE, colour=G150, bound=True)
    f.line([(cx, 22), (cx, top - 6)], w=HAIR, colour=G125)    # cable
    f.circle(cx, top - 3, 3.5, fill=BLACK, stroke=G125, sw=HAIR)
    f.poly(outer + inner[::-1], fill=G75, stroke=G175, sw=LINE, bound=True)   # wall in section
    # depth dimension: surface to crown
    dx = 32
    f.line([(dx, surf + 3), (dx, top)], w=HAIR, colour=G100)
    f.poly([(dx, surf + 1), (dx - 3, surf + 8), (dx + 3, surf + 8)], fill=G100, stroke="none")
    f.poly([(dx, top + 1), (dx - 3, top - 6), (dx + 3, top - 6)], fill=G100, stroke="none")
    f.line([(dx + 4, top), (cx - half_top - 6, top)], w=HAIR, colour=G75)
    # reference numerals with leaders
    f.line([(cx + half_rim - 4, rim - 20), (196, rim - 8)], w=HAIR, colour=G100)
    f.text(199, rim - 4, "10", colour=G125)
    f.line([(cx + 12, (top + water_y) / 2), (196, top + 6)], w=HAIR, colour=G100)
    f.text(199, top + 10, "12", colour=G125)
    f.text(14, 210, "fig. 1", colour=G125)
    # --- fig. 2 (columns 3-4): the output trace
    x0, x1, base, scale = 262, 466, 124, 60
    f.line([(x0, base), (x1, base)], w=HAIR, colour=G50)
    xs, _, ys = run()
    k = 31
    ins = [min(amp(v), 1.0) for v in resample(xs, k)]
    outs = [min(amp(v), 1.0) for v in resample(ys, k)]
    px = [x0 + (x1 - x0) * i / (k - 1) for i in range(k)]
    f.line([(x, base - a * scale) for x, a in zip(px, ins)], w=HAIR, colour=G100)
    f.line([(x, base + a * scale) for x, a in zip(px, ins)], w=HAIR, colour=G100)
    ta = amp(-DEPTH_DB) * scale                                 # threshold, both polarities
    f.dashes((x0, base - ta), (x1, base - ta), colour=G75)
    f.dashes((x0, base + ta), (x1, base + ta), colour=G75)
    top_edge = [(x, base - max(a, 0.03) * scale) for x, a in zip(px, outs)]
    bot_edge = [(x, base + max(a, 0.03) * scale) for x, a in zip(px, outs)]
    f.poly(top_edge + bot_edge[::-1], fill=G50, stroke=BRIGHT, sw=SUBJ, bound=True)
    f.text(262, 210, "fig. 2", colour=G125)
    return f


# ---------------------------------------------------------------- v2 · P3 trace as subject, hidden-line isometric
ISO_C, ISO_S = math.cos(math.radians(30)), math.sin(math.radians(30))


def iso(t, d, z, ox=62, oy=204):
    """World: t along the passage (up-right), d across the wall's thickness (down-right), z up. True isometric."""
    return (ox + (t + d) * ISO_C, oy + (d - t) * ISO_S - z)


def v2() -> Frame:
    """The output envelope (dB) extruded into a wall in hidden-line isometric, standing in a water
    plane at the threshold; the input's crests stand behind it as a thin grey wall the bell pressed down."""
    f = Frame()
    xs, _, ys = run()
    k = 30
    L, th = 220, 22                             # passage length and wall thickness, world px
    sc = 1.3
    plinth = 20 * math.log10(GAIN) * sc         # gain: the makeup lifts the wall on a plinth
    zs = lambda db: plinth + max(0.0, (db + 42) * sc)   # dB -> world height, floor at -42 dB
    mk = 20 * math.log10(GAIN)
    outs = [zs(v - mk) for v in resample(ys, k)]   # crest before makeup, standing on the plinth
    ins = [zs(v) for v in resample(xs, k)]
    ts = [L * i / (k - 1) for i in range(k)]
    z_thr = zs(-DEPTH_DB)
    kb = KNEE_DB * sc / 2
    pad = 14
    back, front_d = -14, th + pad
    # floor plate and the plinth (makeup) under the wall
    f.line([iso(-pad, front_d, 0), iso(L + pad, front_d, 0)], w=HAIR, colour=G75)
    f.line([iso(-pad, back, 0), iso(-pad, front_d, 0)], w=HAIR, colour=G75)
    f.poly([iso(-4, th + 4, 0), iso(-4, th + 4, plinth), iso(L + 4, th + 4, plinth), iso(L + 4, th + 4, 0)],
           fill=BLACK, stroke=G100, sw=HAIR, bound=True)
    # input wall behind (grey layer): crest line and its far end
    ghost = [iso(t, -8, z) for t, z in zip(ts, ins)]
    f.poly([iso(0, -8, plinth)] + ghost + [iso(L, -8, plinth)], fill=BLACK, stroke=G100, sw=HAIR)
    # water plane, far half (behind the wall): the knee band's lower edge first
    f.dashes(iso(-pad, back, z_thr - kb), iso(L + pad, back, z_thr - kb), dash=4, gap=4, colour=G75)
    f.line([iso(-pad, back, z_thr), iso(L + pad, back, z_thr), iso(L + pad, front_d, z_thr)], w=HAIR, colour=G125)
    f.dashes(iso(-pad, back, z_thr + kb), iso(L + pad, back, z_thr + kb), dash=4, gap=4, colour=G75)
    # the output wall: back crest, then the visible top facets where the crest turns, then the front face
    f.line([iso(t, 0, z) for t, z in zip(ts, outs)], w=HAIR, colour=G100)
    for i in range(1, k - 1):
        turn = (outs[i] - outs[i - 1]) * (outs[i + 1] - outs[i]) < 0
        if turn and outs[i] > plinth + 4:
            f.line([iso(ts[i], 0, outs[i]), iso(ts[i], th, outs[i])], w=HAIR, colour=G100)
    f.line([iso(L, 0, outs[-1]), iso(L, th, outs[-1])], w=HAIR, colour=G100)
    front = [iso(0, th, plinth)] + [iso(t, th, z) for t, z in zip(ts, outs)] + [iso(L, th, plinth)]
    f.poly(front, fill=BLACK, stroke=BRIGHT, sw=SUBJ, bound=True)
    f.poly([iso(0, 0, plinth), iso(0, 0, outs[0]), iso(0, th, outs[0]), iso(0, th, plinth)], fill=BLACK, stroke=G125, sw=LINE)
    # water plane, near half, over the wall
    f.line([iso(L + pad, front_d, z_thr), iso(-pad, front_d, z_thr), iso(-pad, back, z_thr)], w=HAIR, colour=G125)
    for z in (z_thr - kb, z_thr + kb):
        f.dashes(iso(-pad, front_d, z), iso(L + pad, front_d, z), dash=4, gap=4, colour=G75)
    lx, ly = iso(L + pad, front_d, z_thr)
    f.text(lx + 6, ly + 4, "\u221212 dB", colour=G125)
    return f


# ---------------------------------------------------------------- v3 · P4 stack in depth, star atlas
def v3() -> Frame:
    """Water strata as stacked atlas plates every 6 dB; the bell is a body plotted on the plate at its
    depth, its lit part the air pocket, its ephemeris track running down from the surface."""
    f = Frame()
    plates = 7                     # every 8 dB, 0 to 48
    w, dpx = 232, 44               # plate width, receding depth (sheared)
    sx, sy = 26, 20                # offset per plate (down-right = deeper)
    x0, y0 = 46, 32
    cur = DEPTH_DB / 8             # 1.5 at 12 dB: between plates 8 and 16
    shear = 52
    def corners(i):
        x, y = x0 + i * sx, y0 + i * sy
        return [(x, y + dpx), (x + shear, y), (x + shear + w, y), (x + w, y + dpx)]
    for i in range(plates):
        c = corners(i)
        on = i == math.ceil(cur - 1e-9)
        f.poly(c, fill=BLACK, stroke=G125 if on else G75, sw=LINE if on else HAIR)
        # graticule ticks along the near edge, every 16 px (atlas border)
        a, b = c[0], c[3]
        for k in range(1, int(w / 16)):
            t = k * 16 / w
            p = (a[0] + (b[0] - a[0]) * t, a[1])
            f.line([p, (p[0], p[1] - (4 if k % 4 else 7))], w=HAIR, colour=G100 if on else G50)
        f.text(c[0][0] - 22, c[0][1] + 3, f"{8 * i}", colour=G125 if on else G100)
    # the body's position on its plate (interpolated between plates)
    i0 = min(int(cur), plates - 2)
    fr = cur - i0
    def on_plate(u, v, i):  # u along width 0..1, v depth 0..1 (0 = near edge)
        c = corners(0)
        x, y = x0 + i * sx, y0 + i * sy
        return (x + u * w + (1 - v) * 0 + v * shear, y + dpx - v * dpx)
    bx, by = on_plate(0.42, 0.5, i0 + fr)
    # ephemeris track: from the surface plate down to the body, ticks at release steps
    track = []
    steps = 14
    for s in range(steps + 1):
        q = s / steps
        ease = 1 - (1 - q) ** (1 + KNEE_DB / 6)      # knee: how gently the track settles
        track.append(on_plate(0.42 - 0.3 * (1 - q), 0.5, (i0 + fr) * ease))
    f.line(track[:-1], w=HAIR, colour=G100)
    for p, q in zip(track[1:-2], track[2:-1]):
        d = norm((q[0] - p[0], q[1] - p[1]))
        nrm = (-d[1], d[0])
        f.line([(p[0] - nrm[0] * 3, p[1] - nrm[1] * 3), (p[0] + nrm[0] * 3, p[1] + nrm[1] * 3)], w=HAIR, colour=G100)
    # the body: magnitude (radius) from gain, phase (lit share) from air
    r = 13 * (1 + P["gain"])           # gain: scale, 13 -> 26 px (2x)
    lit = 0.35 + 0.55 * P["air"]       # air pocket share, as an atlas phase
    f.circle(bx, by, r + 4, fill=BLACK, stroke="none")
    f.circle(bx, by, r, fill=G50, stroke=BRIGHT, sw=SUBJ, bound=True)
    # terminator: the lit part is the top (air rises), a cap down to height lit*2r
    yc = by - r + 2 * r * lit
    hw = math.sqrt(max(r * r - (yc - by) ** 2, 0))
    a0 = math.atan2(yc - by, hw)
    cap = arc(bx, by, r - 1, a0, math.pi - a0 - 2 * math.pi, 16)
    f.poly(cap, fill=G175, stroke="none", bound=True)
    f.text(bx + r + 8, by - 4, "bell", colour=G150)
    f.text(bx + r + 8, by + 8, "12 dB", colour=G125)
    return f


# ---------------------------------------------------------------- v4 · P10 voice field, engineering schematic
def v4() -> Frame:
    """A row of identical air columns in elevation, one per input level from -42 to 0 dB, each standing
    as tall as the compressor lets that level out: a transfer curve built from parts. Columns past the
    threshold are pressed under the bell; a dashed second crown shows where each sits 50 ms after the
    level falls, still held down while the air refills. Dimensioned like a drawing sheet."""
    f = Frame()
    k, x0, pitch, cw = 22, 74, 16, 11
    base = 196
    s = 2.5                                        # px per dB
    mk = 20 * math.log10(GAIN)
    datum = base - mk * s                          # gain: the field stands on a datum raised by the makeup
    lv = [-42 + 42 * i / (k - 1) for i in range(k)]
    thr = -DEPTH_DB
    xof = lambda db: x0 + (db + 42) / 42 * (k - 1) * pitch + cw / 2
    # sheet furniture: ground line, datum with its dimension
    f.line([(x0 - 30, base), (x0 + k * pitch + 8, base)], w=HAIR, colour=G75)
    f.line([(x0 - 8, datum), (x0 + k * pitch, datum)], w=HAIR, colour=G100)
    f.line([(x0 - 20, base), (x0 - 20, datum)], w=HAIR, colour=G100)
    for y in (base, datum):
        f.line([(x0 - 24, y), (x0 - 16, y)], w=HAIR, colour=G100)
    f.text(x0 - 62, (base + datum) / 2 + 4, "+6 dB", colour=G125)
    # knee band (tolerance zone round the threshold) and the threshold itself
    kx0, kx1 = xof(thr - KNEE_DB / 2), xof(thr + KNEE_DB / 2)
    for x in (kx0, kx1):
        f.dashes((x, 40), (x, base - 2), dash=5, gap=3, colour=G75)
    tx = xof(thr)
    f.line([(tx, 34), (tx, base + 8)], w=LINE, colour=G150, bound=True)
    f.text(tx + 4, 44, "thr \u221212", colour=G125)
    f.text(kx0 - 28, 58, "knee", colour=G100)
    # the columns
    for i, x_db in enumerate(lv):
        y_db = curve(x_db, thr, KNEE_DB)
        gr = y_db - x_db
        later = (x_db - 12) + gr * math.exp(-0.05 / AIR_S)        # 50 ms after the level falls 12 dB
        later = min(later, curve(x_db - 12, thr, KNEE_DB))
        h = (y_db + 42) * s + 6
        hl = max((later + 42) * s + 6, 4)
        x = x0 + i * pitch
        top = datum - h
        pressed = gr < -0.5
        f.poly([(x, datum), (x, top), (x + cw, top), (x + cw, datum)], fill=BLACK, stroke=G100, sw=HAIR, bound=True)
        f.poly([(x + 1, top), (x + cw - 1, top), (x + cw - 1, top + 4), (x + 1, top + 4)],
               fill=BRIGHT if pressed else G150, stroke="none", bound=True)
        if datum - hl > top + 9:
            f.dashes((x + 1.5, datum - hl), (x + cw - 1.5, datum - hl), dash=3.5, gap=1, colour=G125)
        if pressed:   # what the input would have stood: a hairline ghost above the crown
            hx = (x_db + 42) * s + 6
            f.line([(x + 2, datum - hx), (x + cw - 2, datum - hx)], w=HAIR, colour=G75)
    return f


# ---------------------------------------------------------------- v5 · P6 figures, oscilloscope trace (stretch)
def v5() -> Frame:
    """A diver drawn as one beam on a scope graticule, crouched on the bell's stage; the bell above
    him on channel 2, the water line pressing down from its rim, air escaping as dots."""
    f = Frame()
    # graticule: 10 x 4 divisions of 40 px, dotted, centre axes ticked
    gx0, gx1, gy0, gy1 = 40, 440, 34, 210
    for x in range(gx0, gx1 + 1, 40):
        f.dashes((x, gy0), (x, gy1), dash=4, gap=6, colour=G50)
    for y in range(gy0, gy1 + 1, 44):
        f.dashes((gx0, y), (gx1, y), dash=4, gap=6, colour=G50)
    cx = 240
    # bell on channel 2 (dimmer beam): crown lowered by depth
    top = 54 + DEPTH_DB * 1.2
    rim = top + 66
    r = 4 + KNEE_DB * 1.4
    prof = bell_profile(cx, top, rim, 60, 44, r)
    f.line(prof, w=LINE, colour=G125)
    f.line([(cx, 36), (cx, top)], w=HAIR, colour=G100)
    # the stage under the bell
    f.line([(cx - 48, rim + 52), (cx + 48, rim + 52)], w=LINE, colour=G125)
    for sxx in (cx - 44, cx + 44):
        f.line([(sxx, rim + 1), (sxx, rim + 52)], w=HAIR, colour=G100)
    # water line inside the bell (air pocket = air)
    air_frac = 0.35 + 0.55 * P["air"]
    wy = top + (rim - top) * air_frac
    f.dashes((cx - 52, wy), (cx + 52, wy), dash=6, gap=4, colour=G100)
    # the diver: one beam. Head in the air pocket, knees bent by the knee setting.
    fy = rim + 51                     # feet on the stage
    bend = math.radians(15 + KNEE_DB * 2.5)
    shin, thigh = 22, 22
    hipx = cx - 6
    kneep = (hipx + 10 + shin * math.sin(bend) * 0.4, fy - shin * math.cos(bend * 0.6))
    hip = (hipx, kneep[1] - thigh * math.cos(bend))
    head_c = (hip[0] + 2, hip[1] - 40)
    beam = [(cx - 20, fy), (cx - 4, fy), kneep, hip, (hip[0] + 1, hip[1] - 26)]
    beam += [(hip[0] + 14, hip[1] - 14), (hip[0] + 20, hip[1] - 2)]          # arm to the knee
    beam += [(hip[0] + 13, hip[1] - 15), (hip[0] + 1.5, hip[1] - 27)]
    helm = arc(head_c[0], head_c[1], 9, math.pi * 0.5 + 0.3, math.pi * 2.5 - 0.3, 18)
    beam += helm
    f.line(beam, w=SUBJ, colour=BRIGHT, bound=True)
    f.line(arc(head_c[0] + 2, head_c[1], 4, -math.pi / 2, math.pi / 2, 6), w=HAIR, colour=G150)   # faceplate
    # air leaving the rim: dots (count rises as air shortens? no: count = venting rate)
    for i in range(6):
        f.circle(cx + 66 + (i % 2) * 5, rim - 6 - i * 11, 2.2, fill=BLACK, stroke=G125, sw=HAIR)
    f.text(gx0 + 4, gy1 - 4, "ch1 diver", colour=G125)
    f.text(gx1 - 52, gy1 - 4, "ch2 bell", colour=G100)
    return f


DIRECTIONS = {
    "v1": ("P2", "patent section", v1),
    "v2": ("P3", "hidden-line isometric", v2),
    "v3": ("P4", "star atlas", v3),
    "v4": ("P10", "engineering schematic", v4),
    "v5": ("P6", "oscilloscope trace", v5),
}

CANDIDATES: dict[str, dict] = {
    "v1": {
        "subject": "A patent plate in two figures: the bell in section hanging on its cable under the surface line, water risen inside it to the air pocket, beside the reference passage's output trace pressed down from its grey input.",
        "controls": [
            "depth: the bell is lowered on its cable, crown 58 to 130 px below the surface (position), and the threshold dashes in fig. 2 close in on the trace as its crests are pressed lower (shape).",
            "air: the waterline inside the bell drops as the air pocket grows from 35 % to 90 % of the bell (position of the waterline), and in fig. 2 the trace's recovery tail after each hit stretches (shape, same path as depth, so the waterline is the primary).",
            "knee: the bell's shoulders go from a hard corner to a full round crown, shoulder radius 4 to about 30 px (shape of the wall in section).",
            "gain: fig. 2's output trace scales about its centre line, x1 to x16 clipped at the frame of the figure (scale)."
        ],
        "reference": "opxy/reference/README.md (field-and-figure: one bright subject, quiet ground) and library/theseus-tower (line drawing, outlines over black bodies)",
        "risks": "P2 splits the body into two half-size pictures, and the bright trace, not the bell, is where the eye lands; the bell is secondary in its own screen. Depth and air both reshape the fig. 2 trace, so their primaries must be the bell's position and the waterline or two knobs read as one. Gain has no part in fig. 1 (a bell has no makeup), so fig. 1 is three controls and fig. 2 is the fourth plus echoes. The trace is the model on a fixed four-hit passage, not the live signal: an effect page gets the slots, not the audio. Patent numerals (10, 12) and fig. captions are four labels; legible at 10 px #7D7D7D but they add up."
    },
    "v2": {
        "subject": "The output envelope of a fixed four-hit passage extruded into a wall in hidden-line isometric, standing on a makeup plinth with its crests pressed down through a water plane, the unpressed input wall standing grey behind it.",
        "controls": [
            "depth: the water plane drops down the wall from 0 to -48 dB (position, about 62 world px), and every crest that crosses it is pressed flatter (shape of the bright front face).",
            "air: the slope of the wall after each crest, from a sheer drop back to the input at 20 ms to a long ramp that never recovers between hits at 2 s (shape; the primary for the front face).",
            "knee: two dashed planes open either side of the water plane, 0 to 24 dB apart (position of the band edges), the crests rounding into it.",
            "gain: the plinth under the wall grows from 0 to 24 dB tall and carries the wall and its water plane up with it (position of the whole wall)."
        ],
        "reference": "library/toro-blocks (hidden-line isometric, black bodies, mid-grey edges, one bright edge)",
        "risks": "P3's own pitfall: an extruded envelope is still an oscilloscope with a camera on it, and nothing in it is a bell except the water plane. Depth and air both reshape the bright front face, which breaks one-channel-per-part unless depth's primary is the plane's position and the crest change is read as consequence. The wall's height is only about 50 px at 1:1 to keep the far corner of the plane out of the header; a taller crest pushes the scene into y 0-20. The front face is one 60-point outline re-keyed on depth, air and knee turns, fine at rest but it's the whole path budget. Like every variant, it's the model on a fixed passage: no live audio on an effect page."
    },
    "v3": {
        "subject": "A star atlas of the water column: depth strata stacked as chart plates every 8 dB, receding down and right, with the bell plotted as a body on the plate at its depth, its lit phase the air pocket and its ephemeris track running down from the surface.",
        "controls": [
            "depth: the body moves down the stack from plate 0 to plate 48, 26 px right and 20 px down per 8 dB (position), and the plate below it brightens (shade as second cue).",
            "air: the body's phase: the lit air cap above a flat waterline grows from 35 % to 90 % of the disc (shape of the lit part).",
            "knee: the ephemeris track's approach, from a straight drop that stops dead at a hard knee to a long easing curve that settles onto the plate at 24 dB (shape of the track).",
            "gain: the body's magnitude, radius 13 to 26 px, the way an atlas sizes a bright star (scale)."
        ],
        "reference": "library/meikyu-orrery (an atlas-drawn body with a terminator, labelled lightly) and library/theseus-tower (black bodies, grey outlines, a stack)",
        "risks": "P4 is for things the sound moves through; here it's the threshold setting moving through depth, not the audio, so the stack is a scale, not a set of frames. Seven plates at 20 px steps overlap heavily: plates read as a stack at 1:1, but their tick borders are close to hatching. A disc with a flat waterline sits one step from a 'level indicator' icon; the atlas labels (plate depths, the body's name) and the ephemeris track are what keep it authored. Nothing shows the signal at all: it's a picture of the settings, which ux.md allows but which makes it the most 'diagram of knobs' of the five. Gain as magnitude is a metaphor only (a bell doesn't get louder by being bigger)."
    },
    "v4": {
        "subject": "A field of identical air columns in engineering elevation, one per input level from -42 to 0 dB, each standing as tall as the bell lets that level out, so the row of crowns is the compressor's transfer curve built from parts, with a second dashed crown in each showing where it still sits 50 ms after the level falls.",
        "controls": [
            "depth: the threshold line slides left across the field from x about 420 at 0 dB to past its left edge at -48 dB (position), and every column right of it is pressed down and its crown turns bright (shape of the field, shade as second cue).",
            "air: the dashed second crowns inside the pressed columns sink lower as the air refills more slowly, about 0 to 30 px below the crown (position of 22 marks).",
            "knee: the dashed tolerance band either side of the threshold opens from 0 to about 200 px wide, and the crowns inside it round from a sharp corner to a smooth bend (position of the band edges).",
            "gain: the datum the whole field stands on rises 0 to 60 px with the makeup, dimensioned at the left (position of the field)."
        ],
        "reference": "library/toro-blocks (P10: a field of identical parts whose heights come from the machine's own model)",
        "risks": "It's the transfer curve drawn as bars, which is one step from a level meter or a bar chart, the dashboard the protocol rejects; the schematic furniture (datum, dimensions, tolerance band) is what argues against that, and it may not be enough at 1:1. The dashed second crowns are 9 px marks inside 11 px columns and barely read at 1:1; air needs a stronger channel. 22 columns x 2 nodes is 44 nodes, cheap, but a depth turn redraws most of them at once. At gain x16 the tallest crowns reach y 25, right under the header; the scale needs a ceiling. Static: the field is the curve, so nothing in it reacts to the audio (there's no audio on an effect page anyway)."
    },
    "v5": {
        "subject": "A diver traced in one scope beam, crouched on the stage under a diving bell drawn on the second channel, his helmet in the air pocket, the water line pressing down from the rim and air escaping as dots past the bell's lip.",
        "controls": [
            "depth: the bell and its stage are lowered on the cable, crown 54 to 112 px (position of channel 2 and the diver with it).",
            "air: the water line inside the bell drops as the air pocket grows, and the dots of escaping air thin from 14 to 2 as the bell holds its air longer (count).",
            "knee: the diver's knees bend from locked straight (hard knee) to a deep crouch (soft knee), 15 to 75 degrees at the knee joint (rotation of the shins and thighs).",
            "gain: the whole trace, bell and diver, scales about the stage, x1 to x2 (scale)."
        ],
        "reference": "opxy/reference/README.md (field-and-figure: a single bright figure over a quiet ground)",
        "risks": "Stretch, and it doesn't really fit. A compressor has no performer; the only figure the metaphor offers is the bell's occupant, and a diver doesn't do anything a compressor does. Knee as the diver's crouch is a pun on the word, not the sound. The exception would be that a diving bell is person-scale, so a figure gives the screen a size and a body under pressure; that's mood, not mapping. At 1:1 the stick figure reads as clip art, exactly the failure the P6 caution names (toro's bulls), and the scope language makes it look like a vector-display toy. Recommend dropping it unless the owner wants a mascot."
    },
}


def main() -> None:
    for vid, (pattern, language, draw) in DIRECTIONS.items():
        out = HERE / vid
        out.mkdir(exist_ok=True)
        frame = draw()
        (out / "rest.svg").write_text(frame.svg(f"{vid} {pattern} {language}"))
        if vid in CANDIDATES:
            cand = {"variant": vid, "pattern": pattern, "drawing_language": language, **CANDIDATES[vid]}
            (out / "candidate.json").write_text(json.dumps(cand, indent=2, ensure_ascii=False) + "\n")
        print(f"{vid}: {frame.node} bound nodes")


if __name__ == "__main__":
    main()
