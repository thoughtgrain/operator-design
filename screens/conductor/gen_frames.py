#!/usr/bin/env python3
"""Conductor's four pages as 480 x 220 frames, drawn as one star atlas.

The language (brief.md, phase 3): an ephemeris plate. Every lane is a moon, everywhere it appears; every chord is a
planet on one graduated orbit; time runs along ephemeris tracks with bodies on them. Outlines first, dark bodies
behind bright outlines, one brightest element per page.

  M1 song    a harmonic orrery, modelled in 3D and projected through one camera: the twelve pitch classes graduate
             one orbit, the scale's seven degrees are planets on it, the sounding chord's planet carries the eight
             lane moons in a row by register. Under it, the phrase track (where chords change) and the bar ruler
             (the groove, with swing plotted as lag).
  M2 lanes   an ephemeris table: a row per lane, hits as bodies sized by velocity. The selected lane's row opens to
             show its register (oct), gate (tails), vary (hollow bodies) and lock (ticks).
  M3 lane    the selected lane's chart: pitch up, time across, notes as bodies with beaded tracks while held.
  M4 route   a patch plate: each lane's line runs to the track it plays; the selected lane's register window on
             the right.

Nodes are authored the way the device draws them: one shape per node, moved by translation and a uniform scale,
painted from the palette. Shapes come from the shared pools in POOLS, so no page asks for a part another page's
shape can't lend it (handoff.md has the index map).

    python3 gen_frames.py [out_dir]      → <out_dir>/<page>/{rest,playing,c<N>-000,-050,-100}.svg
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREFIX = "cond"
FONT = "UniversNextPro-Light"
W, H = 480, 220

# ---- palette: the stock header's greys plus the stock text greys ---------------------------------------------------
BLACK, FILL, GROUND, QUIET, LABEL, SECOND, BRIGHT2, BRIGHT = (
    "#000000", "#323232", "#4B4B4B", "#646464", "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
TEXT_HI, TITLE_OFF, VALUE_OFF = "#CBCBCB", "#5A5A5A", "#707070"
# The device palette lends a node its fill, stroke and stroke width together, so each entry is a paint, not a
# colour: sixteen of them, which is the limit. Text colours are authored per text slot and never repaint.
PAINTS = [
    (BLACK, BLACK, 0.2),        # 0  the mask
    (FILL, FILL, 0.3),          # 1  the page strip's hairline
    (GROUND, GROUND, 0.3),      # 2  hairlines: orbit, rules, edges, stations
    (QUIET, QUIET, 0.3),        # 3  quiet lines: the phrase track, the playhead
    (LABEL, LABEL, 0.3),        # 4  rings, beads, the c mark
    (SECOND, SECOND, 0.3),      # 5  separators, strikes, lit track
    (BRIGHT2, BRIGHT2, 0.3),    # 6  the transfer arc, page mark; a lane or step that just played
    (BRIGHT, BRIGHT, 0.3),      # 7  what a note just hit, the selection, the caps
    (BLACK, GROUND, 1.0),       # 8  hollow, ground: outside the register window
    (BLACK, QUIET, 1.0),        # 9  hollow, quiet: off lanes, other degrees, skipped steps, plain steps
    (BLACK, LABEL, 1.2),        # 10 hollow, label: a lane at rest, quiet hits, the register window
    (BLACK, SECOND, 1.2),       # 11 hollow, second: hits, beat steps, notes, may-vary bodies, gate tails
    (BLACK, BRIGHT2, 1.2),      # 12 hollow, bright: accents, kicks, lanes that play here
    (BLACK, SECOND, 1.5),       # 13 hollow, line weight: the loop's chords
    (BLACK, BRIGHT, 2.0),       # 14 hollow, subject weight: the sounding chord
    (BLACK, BRIGHT, 1.2),       # 15 hollow, bright: the selected lane's route end
]
# Bodies are outlines: grey never fills a body. A body fills only for the moment a note hits it (6, 7).
PAINT_INDEX = {}
for _i, (_f, _s, _w) in enumerate(PAINTS):
    PAINT_INDEX.setdefault((_f, _s, _w), _i)
BODY_POOLS = {"dot", "moon", "octave", "tail", "halo"}


def body_paint(fill, stroke, sw):
    """The outline a body is drawn with: its brightest grey becomes the edge, nothing grey fills it."""
    if fill == BRIGHT:
        return (BRIGHT, BRIGHT, 0.3)                  # just hit: the one solid moment
    edge = max((fill, stroke), key=lambda c: int(c[1:3], 16)) if fill != BLACK else stroke
    if edge == BLACK:
        edge = GROUND
    if sw >= 2.0:
        return (BLACK, BRIGHT, 2.0)
    if sw >= 1.5:
        return (BLACK, SECOND, 1.5)
    w = {GROUND: 1.0, QUIET: 1.0}.get(edge, 1.2)
    return (BLACK, edge, w)


def line_paint(fill, stroke, sw):
    c = max((fill, stroke), key=lambda c: int(c[1:3], 16))
    return (c, c, 0.2 if c == BLACK else 0.3)

# Advance widths of ' '..'~' at 10 px in tenths of a pixel: display.cpp's table, measured in the device font.
GLYPHS = [28, 32, 36, 56, 56, 92, 69, 21, 29, 29, 44, 68, 28, 33, 28, 29, 56, 56, 56, 56, 56, 56, 56, 56,
          56, 56, 28, 28, 68, 68, 68, 48, 98, 69, 66, 66, 73, 60, 56, 72, 74, 28, 49, 62, 56, 94, 75, 74,
          60, 74, 66, 62, 55, 74, 65, 102, 64, 61, 56, 29, 29, 29, 68, 51, 29, 54, 58, 52, 58, 53, 32, 59,
          57, 24, 24, 51, 24, 89, 57, 57, 58, 58, 34, 48, 32, 57, 51, 82, 51, 51, 44, 38, 25, 38, 68]


def text_width(s: str, size: float) -> float:
    return sum(GLYPHS[ord(c) - 32] if 32 <= ord(c) <= 126 else 56 for c in s) * size / 100.0


def f(v: float) -> str:
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# ---- shape pools: every node index, its shape and what borrows it ---------------------------------------------------
# (name, count, shape kind). Order is draw order (back to front) and index order on the device.
POOLS = [
    ("header", 8, "bar"),          # page_header.hpp's stepped bar (preview only here)
    ("segment", 12, "segment"),    # M1: the orbit between neighbouring pitch classes; gaps mark the classes
    ("ringback", 4, "ringback"),   # M1: a seventh's ring, the half behind the planet (loop planets only)
    ("cell", 8, "cell"),           # M1: the phrase track's half-bar cells
    ("rule", 8, "rule"),           # M2 row baselines, M3 root and voice rows, M4 route lines (400 px, origin right)
    ("mask", 1, "mask"),           # M4: the black lane column the route lines slide out from behind
    ("octave", 11, "octave"),      # M4: the register scale's octave cells
    ("column", 8, "column"),       # M4: the eight track stations
    ("comb", 4, "comb"),           # M2, M3: the table's graduated top and bottom edges, two halves each
    ("rulercomb", 2, "rulercomb"), # M1: the bar ruler's on-time axis, two halves
    ("tail", 16, "tail"),          # M2: gate tails behind the selected lane's bodies
    ("dot", 128, "dot"),           # bodies: M1 planets and ruler steps, M2 hits, M3 notes and beads, M4 route ends
    ("ringfront", 4, "ringfront"), # M1: a seventh's ring, the half in front of the planet
    ("moon", 8, "moon"),           # the eight lanes, on every page
    ("tick", 9, "tick"),           # M1 chord separators, track playhead and the c mark; M2 lock ticks
    ("cap", 2, "cap"),             # M4: the register window's low and high caps
    ("strike", 8, "strike"),       # M2, M4: through a muted lane's label
    ("playhead", 1, "playhead"),   # M2, M3: the step column; M4: the register scale's spine
    ("bracket", 1, "bracket"),     # M2, M4: beside the selected lane
    ("pagemark", 4, "pagemark"),   # the page strip: a rule over the shown page
]
BASE = {}
_i = 0
for _name, _n, _ in POOLS:
    BASE[_name] = _i
    _i += _n
NODE_COUNT = _i
assert NODE_COUNT <= 256, NODE_COUNT

DOT_R, MOON_R, HALO_R = 4.0, 4.0, 10.0
# The radius each round pool is authored at on the device; every use must sit within scale (0, 2] of it.
POOL_BASE_R = {"dot": 7.5, "moon": 6.0, "halo": 10.0}


def circle_pts(r: float, n: int = 20, ry: float | None = None) -> list[tuple[float, float]]:
    ry = r if ry is None else ry
    return [(r * math.sin(2 * math.pi * k / n), -ry * math.cos(2 * math.pi * k / n)) for k in range(n)]


def rect_pts(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def comb_pts(length, teeth, pitch, up, beat_every=4, first=0):
    """A graduated edge as one closed outline: a 1 px base with 1 px teeth every `pitch`, beats 6 px, steps 3 px.
    Teeth point up (negative y) when `up`; origin at the left end of the base."""
    sgn = -1 if up else 1
    top = []
    for t in range(teeth):
        x = t * pitch + pitch / 2 if first else t * pitch
        h = 6 if ((t + first) % beat_every == 0) else 3
        top += [(x - 0.5, 0), (x - 0.5, sgn * h), (x + 0.5, sgn * h), (x + 0.5, 0)]
    if top[0][0] > 0:
        top = [(0, 0)] + top
    if top[-1][0] < length:
        top = top + [(length, 0)]
    base = [(length, -sgn * 1.0), (0, -sgn * 1.0)]
    return top + base


def arc_ribbon(pts_outer, pts_inner):
    return list(pts_outer) + list(reversed(pts_inner))


# ---- the frame --------------------------------------------------------------------------------------------------------
class Frame:
    def __init__(self):
        self.items: list[tuple[int, str]] = []    # (order key, svg)
        self.art: list[str] = []                  # static artwork, drawn before nodes
        self.art_over: list[str] = []             # static artwork drawn over nodes (M4's mask)
        self.over_after: int = NODE_COUNT         # nodes with index >= this draw after art_over
        self.texts: list[str] = []
        self.header_svg = ""
        self.used = set()

    # a bound node: shape points relative to its origin, already at its scale
    def node(self, pool: str, k: int, pts, x: float, y: float, fill: str, stroke: str, sw: float):
        idx = BASE[pool] + k
        assert k < dict((p[0], p[1]) for p in POOLS)[pool], (pool, k)
        assert idx not in self.used, (pool, k)
        self.used.add(idx)
        if pool in POOL_BASE_R:
            half = max(max(abs(a), abs(b)) for a, b in pts)
            assert half <= 2 * POOL_BASE_R[pool] + 0.01, (pool, k, half)
        paint = body_paint(fill, stroke, sw) if pool in BODY_POOLS else line_paint(fill, stroke, sw)
        if pool == "dot" and paint == (BLACK, BRIGHT, 1.2):
            paint = (BLACK, BRIGHT, 1.2)
        assert paint in PAINT_INDEX, (pool, fill, stroke, sw, paint)
        fill, stroke, sw = paint
        d = "M " + " L ".join(f"{f(px)} {f(py)}" for px, py in pts) + " Z"
        self.items.append((idx, f'<path id="{PREFIX}_node_{idx}" transform="matrix(1 0 0 1 {f(x)} {f(y)})" d="{d}" '
                                f'fill="{fill}" stroke="{stroke}" stroke-width="{f(sw)}"/>'))

    def static(self, pts, fill, stroke, sw, over=False):
        d = "M " + " L ".join(f"{f(px)} {f(py)}" for px, py in pts) + " Z"
        (self.art_over if over else self.art).append(
            f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{f(sw)}"/>')

    def text(self, slot: int, x: float, y: float, size: float, fill: str, s: str):
        if not s:
            return
        self.texts.append(f'<text id="{PREFIX}_text_{slot}" transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{fill}" '
                          f'stroke="none" font-family="{FONT}" font-size="{f(size)}px">{escape(s)}</text>')

    def svg(self) -> str:
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
               '<g id="preview_canvas"><rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/></g>',
               self.header_svg]
        for i, (fc, sc, w) in enumerate(PAINTS):  # noqa
            out.append(f'<path id="{PREFIX}_palette_{i}" d="M {700 + 8 * i} 300 L {704 + 8 * i} 300 L {704 + 8 * i} 304 Z" '
                       f'fill="{fc}" stroke="{sc}" stroke-width="{f(w)}"/>')
        out += self.art
        items = sorted(self.items)
        out += [s for i, s in items if i < self.over_after]
        out += self.art_over
        out += [s for i, s in items if i >= self.over_after]
        out += self.texts
        out.append("</svg>")
        return "\n".join(x for x in out if x) + "\n"


def escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# Text slots: 0-15 belong to page_header.hpp; the pages own 16-31.
T_PAGES = 16            # 4: the page strip
T_FREE = 20             # 12: each page's own


def header(fr: Frame, titles, values, row: int = 0):
    """Preview of page_header.hpp: the active row on the stepped bar, the other in grey below it."""
    g = ['<g id="preview_header">']
    steps = ["#000000", "#323232", "#4B4B4B", "#646464", "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD"]
    for i, c in enumerate(steps):
        g.append(f'<rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
    for col in range(4):
        for r in range(2):
            slot = r * 4 + col
            active = r == row
            t, v = titles[slot], values[slot]
            if active:
                tc = "#CBCBCB" if col < 2 else "#000000"
                vc = "#CBCBCB" if col < 2 else "#000000"
                g.append(_t(5 + 120 * col, 10, 10, tc, t))
                g.append(_t(65 + 120 * col, 17.44, 20, vc, v))
            else:
                g.append(_t(5 + 120 * col, 33, 10, TITLE_OFF, t))
                g.append(_t(65 + 120 * col, 33, 13, VALUE_OFF, v))
    g.append("</g>")
    fr.header_svg = "\n".join(g)


def _t(x, y, size, fill, s):
    return (f'<text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{fill}" stroke="none" font-family="{FONT}" '
            f'font-size="{f(size)}px">{escape(s)}</text>')


PAGE_NAMES = ["song", "lanes", "lane", "route"]


def page_strip(fr: Frame, page: int):
    for p in range(4):
        x = 120 * p
        fr.static(rect_pts(x + 2, 204, x + 118, 205), FILL, FILL, 0.3)           # hairline under every page name
        if p == page:
            fr.node("pagemark", p, rect_pts(0, 0, 116, 2), x + 2, 203, BRIGHT2, BRIGHT2, 0.3)
        fr.text(T_PAGES + p, x + 4, 216, 10, TEXT_HI if p == page else LABEL, PAGE_NAMES[p])


# ---- music: a small, deterministic stand-in for generator.h ---------------------------------------------------------
NOTE = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
SCALES = [[0, 2, 4, 5, 7, 9, 11], [0, 2, 3, 5, 7, 8, 10], [0, 2, 3, 5, 7, 9, 10], [0, 1, 3, 5, 7, 8, 10],
          [0, 2, 4, 6, 7, 9, 11], [0, 2, 4, 5, 7, 9, 10], [0, 2, 3, 5, 7, 8, 11]]
SCALE_NAMES = ["maj", "min", "dor", "phr", "lyd", "mix", "hmin"]
PROG_NAMES = ["pop", "minor", "mode", "drone", "jazz", "walk"]
HRATE_NAMES = ["1/2", "1", "2", "4"]
HRATE_STEPS = [8, 16, 32, 64]
LOOPS = {"pop": [0, 4, 5, 3], "minor": [0, 5, 2, 6], "mode": [0, 6, 0, 6], "drone": [0, 0, 0, 0],
         "jazz": [1, 4, 0, 0], "walk": [0, 3, 1, 4]}
ROLES = ["off", "drum", "bass", "chord", "pad", "arp", "lead"]
REGISTER = {"off": 0, "drum": 0, "bass": 0, "chord": 1, "pad": 1, "arp": 2, "lead": 2}
DEFAULT_ROLES = ["drum", "bass", "chord", "lead", "arp", "pad", "off", "off"]
ROLE_ORBIT = {"drum": 0.085, "bass": 0.12, "chord": 0.155, "pad": 0.19, "arp": 0.225, "lead": 0.26, "off": 0.26}


def pick(v: float, n: int) -> int:
    return min(n - 1, int(v * n))


def chord_quality(scale, d):
    third = (scale[(d + 2) % 7] - scale[d]) % 12
    fifth = (scale[(d + 4) % 7] - scale[d]) % 12
    return "dim" if fifth == 6 else ("min" if third == 3 else "maj")


def chord_name(key, scale, d, seventh=False):
    q = chord_quality(scale, d)
    root = NOTE[(key + scale[d]) % 12]
    return root + {"maj": "", "min": "m", "dim": "dim"}[q] + ("7" if seventh else "")


class Song:
    """The M1 controls at 0..1, read the way definition.json maps them."""

    def __init__(self, **kw):
        v = dict(key=0.0417, scale=0.0714, prog=0.0833, dens=0.5, cmplx=0.4, hrate=0.375, swing=0.0, evolve=0.3)
        v.update(kw)
        self.v = v
        self.key = pick(v["key"], 12)
        self.scale_i = pick(v["scale"], 7)
        self.scale = SCALES[self.scale_i]
        self.prog = PROG_NAMES[pick(v["prog"], 6)]
        self.dens = round(v["dens"] * 100)
        self.cmplx = round(v["cmplx"] * 100)
        self.hrate = pick(v["hrate"], 4)
        self.swing = round(v["swing"] * 100)
        self.evolve = round(v["evolve"] * 100)
        self.loop = LOOPS[self.prog]
        if self.prog == "minor" and chord_quality(self.scale, 0) == "maj":
            self.loop = [5, 3, 0, 4]
        self.seventh = self.prog == "jazz" or self.cmplx >= 65

    def kicks(self):
        k = 2 + (self.dens * 4 + 50) // 100
        base = [((i * k) % 16) < k for i in range(16)]
        kick = list(base)
        rnd = random.Random(377)
        for i in range(1, 16):
            if not base[i]:
                continue
            if rnd.random() < self.cmplx * 0.006:
                j = i - 1 if rnd.random() < 0.5 else i + 1
                if 0 < j < 16 and not kick[j]:
                    kick[i], kick[j] = False, True
        return kick

    def candidates(self):
        """Degrees evolve could swap into chords 2..4: the scale's other degrees, leading tone last."""
        others = [d for d in (1, 2, 5, 3, 4, 6) if d not in self.loop]
        return others[:3]

    def titles_values(self):
        t = ["key", "scale", "prog", "dens", "cmplx", "hrate", "swing", "evolve"]
        v = [NOTE[self.key], SCALE_NAMES[self.scale_i], self.prog, str(self.dens), str(self.cmplx),
             HRATE_NAMES[self.hrate], str(self.swing), str(self.evolve)]
        return t, v


# ---- M1: the camera -------------------------------------------------------------------------------------------------
CAM_D = 9.0
ORBIT_CX, ORBIT_CY, ORBIT_RX, ORBIT_RY = 240.0, 104.0, 200.0, 38.0


def _cam(el_deg):
    el = math.radians(el_deg)
    cam = (0.0, CAM_D * math.sin(el), -CAM_D * math.cos(el))
    fwd = tuple(-c / CAM_D for c in cam)
    right = (1.0, 0.0, 0.0)
    up = (fwd[1] * right[2] - fwd[2] * right[1], fwd[2] * right[0] - fwd[0] * right[2],
          fwd[0] * right[1] - fwd[1] * right[0])
    up = tuple(-u for u in up) if up[1] < 0 else up
    return cam, fwd, right, up


def _raw(p, cam):
    c, fwd, right, up = cam
    d = (p[0] - c[0], p[1] - c[1], p[2] - c[2])
    x = sum(a * b for a, b in zip(d, right))
    y = sum(a * b for a, b in zip(d, up))
    z = sum(a * b for a, b in zip(d, fwd))
    return x / z, -y / z, z


def _fit():
    """Find the camera height that gives the orbit its 200 x 38 px half-axes, then one uniform scale for both."""
    best = None
    for tenth in range(20, 400):
        el = tenth / 10
        cam = _cam(el)
        pts = [_raw((math.sin(t), 0, math.cos(t)), cam) for t in [k * math.pi / 90 for k in range(180)]]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        ratio = (max(ys) - min(ys)) / (max(xs) - min(xs))
        err = abs(ratio - ORBIT_RY / ORBIT_RX)
        if best is None or err < best[0]:
            best = (err, el, cam, min(xs), max(xs), min(ys), max(ys))
    _, el, cam, x0, x1, y0, y1 = best
    s = 2 * ORBIT_RX / (x1 - x0)
    return el, cam, s, (x0 + x1) / 2, (y0 + y1) / 2


CAM_EL, CAM, CAM_S, CAM_MX, CAM_MY = _fit()
Z0 = CAM_D  # depth of the orbit's centre


def project(p):
    x, y, z = _raw(p, CAM)
    return ORBIT_CX + (x - CAM_MX) * CAM_S, ORBIT_CY + (y - CAM_MY) * CAM_S, z


def px_per_unit(z):
    return CAM_S / z


def pc_angle(pc: float) -> float:
    return 2 * math.pi * pc / 12.0


def orbit_point(pc: float, radius: float = 1.0):
    a = pc_angle(pc)
    return (radius * math.sin(a), 0.0, radius * math.cos(a))


PLANET_R = 0.034           # world units
MOON_WORLD_R = 0.02
RING_TILT = math.radians(30)


def draw_orbit_art(fr: Frame):
    return   # the orbit is drawn by its twelve segment nodes (device static art is shared by every page)


def segment_pts(k: int):
    """The orbit between pitch classes k and k+1, as a 1.6 px ribbon, relative to its own origin (its first point)."""
    n = 8
    outer, inner = [], []
    gap = 0.06                       # a pitch class is a small gap in the orbit
    for j in range(n + 1):
        pc = k + gap + (1 - 2 * gap) * j / n
        cx, cy, _ = project(orbit_point(pc))
        # offset along the ellipse's screen normal
        a = pc_angle(pc)
        nx, ny = math.sin(a) * ORBIT_RY, -math.cos(a) * ORBIT_RX
        ln = math.hypot(nx, ny)
        nx, ny = nx / ln, ny / ln
        outer.append((cx + nx * 0.8, cy + ny * 0.8))
        inner.append((cx - nx * 0.8, cy - ny * 0.8))
    pts = arc_ribbon(outer, inner)
    ox, oy = pts[0]
    return [(x - ox, y - oy) for x, y in pts], ox, oy


def ring_pts(r_px, front: bool):
    """Half a seventh's ring: a flat ring tilted 30 degrees off the orbit plane, seen through the camera."""
    ry = r_px * math.sin(math.radians(CAM_EL) + RING_TILT)
    n = 14
    rng = range(n + 1)
    a0, a1 = (0, math.pi) if front else (math.pi, 2 * math.pi)
    outer = [(r_px * math.cos(a0 + (a1 - a0) * j / n), ry * math.sin(a0 + (a1 - a0) * j / n)) for j in rng]
    rin, ryin = r_px - 1.1, ry - 1.1 * ry / r_px
    inner = [(rin * math.cos(a0 + (a1 - a0) * j / n), ryin * math.sin(a0 + (a1 - a0) * j / n)) for j in rng]
    return arc_ribbon(outer, inner)


def lane_energy(song: Song, role: str) -> int:
    return 0 if role == "off" else song.dens


def moon_style(role, lit, muted=False):
    if role == "off" or muted:
        return BLACK, QUIET, 1.0
    if lit:
        return SECOND, BRIGHT2, 1.2
    return FILL, LABEL, 1.2


def moon_radius(song_dens: int, role: str) -> float:
    """A lane's size is how much it plays: dens 0 → 0.6x, dens 100 → 1.5x."""
    if role == "off":
        return MOON_R * 0.55
    return MOON_R * (0.45 + 1.35 * song_dens / 100)


def draw_m1(song: Song, position: int = 0, playing: bool = False, step: int = 0, lit=frozenset(),
            frozen: bool = False, roles=DEFAULT_ROLES, rot: float = 0.0, moon_pc: float | None = None,
            glow: dict | None = None, show_moons: bool = False) -> Frame:
    """rot: an easing offset in pitch classes for the planets (a key turn in progress); moon_pc: where the moons
    are on their way between planets; glow: each lane's light, 0..1 (fades after it plays)."""
    fr = Frame()
    t, v = song.titles_values()
    header(fr, t, v)
    page_strip(fr, 0)
    draw_orbit_art(fr)

    key, scale, loop = song.key, song.scale, song.loop
    current = loop[position]
    nxt = loop[(position + 1) % 4]
    rate = HRATE_STEPS[song.hrate]

    # planets on the orbit: where each degree sits, and its depth
    planets = []
    for d in range(7):
        pc = (key + scale[d]) % 12
        x, y, z = project(orbit_point(pc + rot))
        planets.append((d, pc, x, y, z))

    # evolve: halos round the degrees evolve could swap in, scaling up from nothing
    ev = 0 if frozen else song.evolve
    for i, d in enumerate(song.candidates()):
        _, pc, x, y, z = planets[d]
        r = PLANET_R * px_per_unit(z) * (1 + 1.4 * ev / 100)
        pass                               # evolve now scales the candidate planets themselves (below)

    # the transfer arc: from the sounding chord's planet to the next, the short way round
    a_pc, b_pc = planets[current][1], planets[nxt][1]
    cw = (b_pc - a_pc) % 12
    segs = set()
    if cw:
        segs = set([(a_pc + j) % 12 for j in range(cw)] if cw <= 6 else [(b_pc + j) % 12 for j in range(12 - cw)])
    # the orbit: twelve segments, the transfer arc (sounding chord to the next, the short way) lit
    for k in range(12):
        pts, ox, oy = segment_pts(k)
        lit_seg = k in segs
        fr.node("segment", k, pts, ox, oy, BRIGHT2 if lit_seg else GROUND, BRIGHT2 if lit_seg else GROUND,
                0.9 if lit_seg else 0.2)
    # the c mark: where pitch class 0 sits, so a turn of key reads against something fixed
    cx0, cy0, _ = project(orbit_point(0))
    fr.node("tick", 8, rect_pts(-0.6, 15, 0.6, 21), cx0, cy0, LABEL, LABEL, 0.2)

    # moons: the eight lanes in a row round the sounding planet, by register; cmplx scatters them
    d_cur, pc_cur, cxp, cyp, czp = planets[current]
    host_pc = moon_pc if moon_pc is not None else pc_cur + rot
    cxp, cyp, czp = project(orbit_point(host_pc))
    rnd = random.Random(12)
    moons = []
    centre_side = 1 if cxp < 110 else (-1 if cxp > 370 else 0)
    for lane, role in enumerate(roles):
        rho = ROLE_ORBIT[role]
        side = centre_side or (1 if lane % 2 else -1)
        phi = 0.0 if side > 0 else math.pi
        spread = rnd.uniform(-1.0, 1.0)
        ecc = rnd.uniform(-0.45, 0.45)
        phi += song.cmplx / 100 * spread * 1.6
        rho *= 1 + song.cmplx / 100 * ecc
        a = pc_angle(host_pc)
        world = (math.sin(a) + rho * math.cos(phi), 0.0, math.cos(a) + rho * math.sin(phi))
        mx, my, mz = project(world)
        moons.append((mz, lane, role, mx, my))

    # depth order: far moons, then the planets, then near moons
    def draw_moon(lane, role, mx, my, mz):
        r = moon_radius(lane_energy(song, role), role) * (Z0 / mz)
        g = (glow or {}).get(lane, 1.0 if (playing and lane in lit) else 0.0) if role != "off" else 0.0
        on = g > 0.35
        r *= 1 + 0.4 * g
        fill, stroke, sw = moon_style(role, on)
        fr.node("moon", lane, circle_pts(r, 16), mx, my, fill, stroke, sw)

    for mz, lane, role, mx, my in sorted(moons, reverse=True) if show_moons else []:
        if mz > czp:
            draw_moon(lane, role, mx, my, mz)

    ring_i = 0
    for d, pc, x, y, z in sorted(planets, key=lambda p: -p[4]):
        in_loop = d in loop
        r = PLANET_R * px_per_unit(z)
        if d == current:
            r *= 1.95
            fill, stroke, sw = FILL, BRIGHT, 2.0
        elif in_loop:
            r *= 1.85
            fill, stroke, sw = FILL, SECOND, 1.5
        elif ev > 0 and d in song.candidates():
            r *= 1 + 0.9 * ev / 100                  # what evolve could bring in swells with how likely it is
            fill, stroke, sw = BLACK, LABEL, 1.2
        else:
            fill, stroke, sw = BLACK, QUIET, 1.2
        ringed = song.seventh and in_loop
        if ringed:
            fr.node("ringback", ring_i, ring_pts(r * 1.75, False), x, y, LABEL, LABEL, 0.2)
        fr.node("dot", d, circle_pts(r, 24), x, y, fill, stroke, sw)
        if ringed:
            fr.node("ringfront", ring_i, ring_pts(r * 1.75, True), x, y, LABEL, LABEL, 0.2)
            ring_i += 1

    for mz, lane, role, mx, my in sorted(moons, reverse=True) if show_moons else []:
        if mz <= czp:
            draw_moon(lane, role, mx, my, mz)

    # planet labels: chord name, and the loop positions it plays ("Am 3"), outside the orbit
    for d, pc, x, y, z in planets:
        positions = [str(i + 1) for i, dd in enumerate(loop) if dd == d]
        if not positions:
            continue                       # only the loop's chords are named; the rest stay quiet
        label = chord_name(key, scale, d, song.seventh and d in loop)
        if positions:
            label += " " + "·".join(positions)
        a = pc_angle(pc)
        nx, ny = math.sin(a), -math.cos(a)
        lx = x + nx * 15
        ly = y + ny * 16 + 4
        size = 10
        w = text_width(label, size)
        if nx > 0.35:
            tx = lx - 2
        elif nx < -0.35:
            tx = lx - w + 2
        else:
            tx = lx - w / 2
        if tx < 4 or tx + w > 476:         # no room beside it at the screen's edge: label it underneath
            tx, ly = max(4.0, min(476.0 - w, x - w / 2)), y + 23
        if tx < 92 and ly < 84:            # keep clear of the plate's title in the corner
            tx = 92
        fill = TEXT_HI if d == current else (SECOND if d in loop else LABEL)
        fr.text(T_FREE + d, tx, ly, size, fill, label)

    # the plate's title: the sounding chord, and what comes next
    fr.text(T_FREE + 7, 10, 62, 20, TEXT_HI, chord_name(key, scale, current, song.seventh))
    fr.text(T_FREE + 8, 10, 76, 10, LABEL, "next " + chord_name(key, scale, nxt, song.seventh))
    if frozen:
        fr.text(T_FREE + 9, 470 - text_width("frozen", 10), 52, 10, LABEL, "frozen")

    # the phrase track: four bars as eight half-bar cells; the sounding chord's span is lit, chords are separated
    x0, cw_px, ty = 24, 54, 160
    sounding_chord = (position if not playing else position)
    chord_of_cell = [(h * 8) // rate for h in range(8)]
    # which chord index is sounding: the first one at rest; while playing, the one under the playhead
    now_cell = (position * rate) // 8 % 8 if playing else 0
    now_chord = chord_of_cell[now_cell]
    for h in range(8):
        lit_cell = chord_of_cell[h] == now_chord
        fr.node("cell", h, rect_pts(0, 2, cw_px - 2, 4), x0 + h * cw_px, ty, SECOND if lit_cell else GROUND,
                QUIET if lit_cell else FILL, 0.3)
    sep = 0
    for h in range(1, 8):
        if chord_of_cell[h] != chord_of_cell[h - 1]:
            fr.node("tick", sep, rect_pts(-1, 0, 1, 12), x0 + h * cw_px - 1, ty - 3, SECOND, SECOND, 0.3)
            sep += 1
    if playing:
        px_track = x0 + (now_cell * 8 + step / 2) * cw_px / 8
        fr.node("tick", 7, rect_pts(-1, 0, 1, 12), px_track, ty - 3, BRIGHT2, BRIGHT2, 0.3)

    # the bar ruler: the axis is on time; each step a body on it, offbeats late (right) and plotted low by swing
    ax, pitch, ry_axis = 24, 27, 177
    for half in range(2):
        fr.node("rulercomb", half, comb_pts(8 * pitch, 8, pitch, True, first=1), ax + half * 8 * pitch, ry_axis + 0.5,
                GROUND, GROUND, 0.2)
    kick = song.kicks()
    energy = 0.55 + 0.9 * song.dens / 100      # dens is every lane's energy: the bar's other bodies swell with it
    for s in range(16):
        lag = song.swing / 100 * (10 / 24) if s % 2 else 0.0
        bx = ax + pitch * s + pitch / 2 + lag * pitch
        by = ry_axis + lag * 48          # lateness plotted below the axis: 20 px at the most
        if kick[s]:
            r, fill, stroke, sw = DOT_R * 1.5, SECOND, SECOND, 1.2
        elif s in (4, 12):
            r, fill, stroke, sw = DOT_R * 0.95 * energy, LABEL, LABEL, 1.2
        elif s % 4 == 0:
            r, fill, stroke, sw = DOT_R * 0.8 * energy, FILL, SECOND, 1.2
        else:
            r, fill, stroke, sw = DOT_R * 1.0 * energy, FILL, QUIET, 1.2
        if playing and s == step:
            r *= 1.35
            fill, stroke = BRIGHT, BRIGHT
        fr.node("dot", 7 + s, circle_pts(r, 16), bx, by, fill, stroke, sw)
    return fr


TABLE_X0, TABLE_PITCH = 60, 25          # M2 and M3 share one table, so they share its edge nodes
RULE_PTS = rect_pts(-400, -0.6, 0, 0.6)


def table_edges(fr: Frame, top: float, bottom: float):
    """The table's graduated edges: beats long, steps short, ticks pointing into the table."""
    for half in range(2):
        x = TABLE_X0 + half * 8 * TABLE_PITCH
        fr.node("comb", half, comb_pts(8 * TABLE_PITCH, 8, TABLE_PITCH, False), x, top, GROUND, GROUND, 0.2)
        fr.node("comb", 2 + half, comb_pts(8 * TABLE_PITCH, 8, TABLE_PITCH, True), x, bottom, GROUND, GROUND, 0.2)


# ---- the lanes: a stand-in for each lane's bar -----------------------------------------------------------------------
class Lane:
    def __init__(self, role, dens=50, oct=0, vel=80, vary=50, lock=1, gate=60, mute=False, target=None,
                 xpose=0, low=0, high=127):
        self.role, self.dens, self.oct, self.vel, self.vary = role, dens, oct, vel, vary
        self.lock, self.gate, self.mute, self.target = lock, gate, mute, target
        self.xpose, self.low, self.high = xpose, low, high


PATTERNS = {   # hits per role at lane dens 50: step → accent?
    "drum": {0: 1, 2: 0, 4: 1, 6: 0, 8: 1, 10: 0, 11: 0, 12: 1, 14: 0},
    "bass": {0: 1, 3: 0, 6: 0, 8: 1, 11: 0, 14: 0},
    "chord": {0: 1, 1: 0, 6: 0, 8: 1, 9: 0, 15: 0},
    "lead": {0: 1, 2: 0, 3: 0, 6: 0, 8: 1, 10: 0, 11: 0, 13: 0},
    "arp": {s: (1 if s % 4 == 0 else 0) for s in range(0, 16, 2)},
    "pad": {0: 1},
    "off": {},
}
EXTRA = [3, 7, 9, 13, 15, 1, 5, 11]          # steps a denser lane adds, in order
KICK_STEPS = {0, 4, 8, 12}
ACCENT_STEPS = {0, 4, 8, 12}


SONG_KICKS = [i for i, k in enumerate(Song().kicks()) if k]


def lane_hits(lane: Lane, idx: int):
    base = dict(PATTERNS[lane.role])
    if lane.role == "bass":       # generator.h: a bass's hits follow its lock: the kick, the accents, or its own
        steps = {0: SONG_KICKS, 1: sorted(set(SONG_KICKS) | {0, 4, 8, 12}), 2: [0, 3, 6, 10, 13]}[lane.lock]
        base = {st: (1 if st % 8 == 0 else 0) for st in steps}
    if lane.role == "off":
        return {}
    extra = round((lane.dens - 50) / 50 * 6)
    if extra > 0:
        for s in EXTRA:
            if extra <= 0:
                break
            if s not in base:
                base[s] = 0
                extra -= 1
    elif extra < 0:
        for s in sorted([s for s in base if not base[s]], key=lambda s: -s)[: -extra]:
            del base[s]
        if lane.dens <= 5:
            base = {s: a for s, a in base.items() if a}
    return base


def default_lanes():
    return [Lane(r) for r in DEFAULT_ROLES]


def draw_m2(lanes, sel=0, playing=False, step=0, lit=frozenset()) -> Frame:
    fr = Frame()
    L = lanes[sel]
    titles = ["lane", "role", "dens", "oct", "vel", "vary", "lock", "gate"]
    values = [str(sel + 1), L.role, str(L.dens), str(L.oct), str(L.vel), str(L.vary),
              ["kick", "acnt", "free"][L.lock], str(L.gate)]
    header(fr, titles, values)
    page_strip(fr, 1)
    x0, pitch = TABLE_X0, TABLE_PITCH
    table_edges(fr, 42, 194)
    y = 48
    dot_k = 0
    tail_k = tick_k = 0
    for i, ln in enumerate(lanes):
        open_row = i == sel
        hgt = 52 if open_row else 10
        base_y = y + hgt - 3
        fr.node("rule", i, RULE_PTS, 460, base_y, QUIET if open_row else GROUND,
                QUIET if open_row else GROUND, 0.2)
        # the lane: moon and name
        on = playing and i in lit and ln.role != "off"
        mr = moon_radius(ln.dens, ln.role) * (1.65 if on else 1.0)
        fill, stroke, sw = moon_style(ln.role, on, ln.mute)
        fr.node("moon", i, circle_pts(mr, 16), 11, (y + 6.5) if open_row else base_y - 4, fill, stroke, sw)
        fr.text(T_FREE + i, 25, (y + 10) if open_row else base_y, 10, TEXT_HI if open_row else SECOND,
                f"{i + 1} {ln.role}")
        if ln.mute:
            fr.node("strike", i, rect_pts(0, -0.75, text_width(f"{i + 1} {ln.role}", 10) + 4, 0.75), 23,
                    ((y + 10) if open_row else base_y) - 3.5,
                    SECOND, SECOND, 0.2)
        if open_row:
            fr.node("bracket", 0, rect_pts(0, 0, 2, hgt - 2), 2, y, BRIGHT, BRIGHT, 0.3)
        hits = lane_hits(ln, i)
        rnd = random.Random(100 + i)
        vary_steps = set()
        if open_row:
            cand = sorted(hits)
            rnd.shuffle(cand)
            vary_steps = set(cand[: round(len(cand) * ln.vary / 100)])
        for s, acc in sorted(hits.items()):
            cx = x0 + pitch * s + pitch / 2
            live = playing and s == step
            if open_row:
                cy = base_y - 8 - (ln.oct + 2) * 7 - REGISTER[ln.role] * 4
                r = DOT_R * (0.8 + 1.1 * ln.vel / 100) * (1.05 if acc else 1.0)
                hollow = s in vary_steps
                if ln.role not in ("drum",):
                    # gate: a tail behind the body, as long as the note holds
                    sc = 0.1 + 0.9 * (ln.gate / 100) ** 0.6
                    wedge = [(0, -9 * sc), (23 * sc, -0.6), (23 * sc, 0.6), (0, 9 * sc)]
                    fr.node("tail", tail_k, wedge, cx, cy, GROUND, GROUND, 0.3)
                    tail_k += 1
                fill = BRIGHT if live else (BLACK if hollow else (BRIGHT2 if (acc or (playing and s < step)) else SECOND))
                stroke = BRIGHT if live else (SECOND if hollow else (BRIGHT2 if acc else SECOND))
            else:
                cy = base_y - 4
                r = DOT_R * (0.75 if acc else 0.55) * (1.8 if live else 1)
                fill = stroke = BRIGHT if live else (SECOND if (acc or (playing and s < step)) else QUIET)
                if ln.mute:
                    fill, stroke = BLACK, QUIET
            fr.node("dot", dot_k, circle_pts(r, 14), cx, cy, fill, stroke, 1.2)
            dot_k += 1
        if open_row and ln.role == "off":
            # an off lane's open row: every step a hollow ring, nothing plays here
            for s_ in range(16):
                fr.node("dot", dot_k, circle_pts(DOT_R * 1.15, 14), x0 + pitch * s_ + pitch / 2, base_y - 22,
                        BLACK, QUIET, 1.0)
                dot_k += 1
        if open_row and ln.role == "bass":      # lock only steers a bass (generator.h)
            locks = {0: set(SONG_KICKS), 1: set(SONG_KICKS) | {0, 4, 8, 12}, 2: set()}[ln.lock]
            for s in sorted(locks):
                cx = x0 + pitch * s + pitch / 2
                fr.node("tick", tick_k, rect_pts(-1, 0, 1, 5), cx, base_y + 1, SECOND, SECOND, 0.3)
                tick_k += 1
        y += hgt + 3 if open_row else hgt + 3
    if playing:
        px_ = x0 + pitch * step + pitch / 2
        fr.node("playhead", 0, rect_pts(-1.5, 0, 1.5, 144), px_, 46, QUIET, QUIET, 0.2)
    return fr


# ---- M3: the selected lane's chart ------------------------------------------------------------------------------------
ARP_MODES = ["up", "down", "updn", "rand", "conv", "order"]


class Arp:
    def __init__(self, mode=2, rate=2, rng=1, steps=8, skip=15, accent=50, tones=0, jump=10):
        self.mode, self.rate, self.range, self.steps = mode, rate, rng, steps
        self.skip, self.accent, self.tones, self.jump = skip, accent, tones, jump

    def values(self):
        return [ARP_MODES[self.mode], ["1/4", "1/8", "1/16"][self.rate], str(self.range + 1), str(self.steps),
                str(self.skip), str(self.accent), ["chord", "scale"][self.tones], str(self.jump)]

    def notes(self, key=0, scale=SCALES[0], degree=0):
        """(step, pitch, accent, held) for one bar."""
        if self.tones == 0:
            pcs = [scale[(degree + k) % 7] + 12 * ((degree + k) // 7) for k in (0, 2, 4)]
        else:
            pcs = [scale[(degree + k) % 7] + 12 * ((degree + k) // 7) for k in range(7)]
        pool = [60 + key + p + 12 * o for o in range(self.range + 1) for p in pcs]
        pool = sorted(pool)[: max(3, self.steps)] if self.mode != 5 else pool[: max(3, self.steps)]
        seq = {0: pool, 1: pool[::-1], 2: pool + pool[-2:0:-1], 3: None, 4: None, 5: pool}[self.mode]
        if self.mode == 3:
            rnd = random.Random(9)
            seq = [rnd.choice(pool) for _ in range(len(pool))]
        if self.mode == 4:
            seq, lo, hi = [], 0, len(pool) - 1
            while lo <= hi:
                seq.append(pool[lo])
                if lo != hi:
                    seq.append(pool[hi])
                lo, hi = lo + 1, hi - 1
        if self.mode == 5:
            rnd = random.Random(5)
            seq = list(pool)
            rnd.shuffle(seq)
        seq = seq[: self.steps]
        every = [4, 2, 1][self.rate]
        rnd = random.Random(31)
        out = []
        for i, s in enumerate(range(0, 16, every)):
            if rnd.random() < self.skip / 100:
                out.append((s, seq[i % len(seq)], False, 0, True))
                continue
            p = seq[i % len(seq)]
            if rnd.random() < self.jump / 100 * 0.8:
                p += 12
            acc = rnd.random() < self.accent / 100
            out.append((s, p, acc, 1 if every > 1 else 0, False))
        return out


DRUM_VOICES = ["kick", "snare", "clap", "rim", "hat", "open", "tom", "low"]


def draw_m3(arp: Arp | None = None, drum: bool = False, playing=False, step=0, lane_no=5) -> Frame:
    fr = Frame()
    page_strip(fr, 2)
    x0, pitch = TABLE_X0, TABLE_PITCH
    table_edges(fr, 42, 196)
    k = 0
    if drum:
        titles = ["kick", "snare", "hats", "perc", "fills", "ghost", "human", "map"]
        header(fr, titles, ["60", "60", "55", "30", "50", "25", "20", "xy"])
        top, rp = 50, 18
        hits = {0: [0, 8, 10], 1: [4, 12], 4: list(range(0, 16, 2)), 5: [14], 3: [7], 2: [12]}
        for r, name in enumerate(DRUM_VOICES):
            y = top + rp * r
            fr.text(T_FREE + r, 4, y + 4, 10, LABEL, name)
            fr.node("rule", r, RULE_PTS, 460, y, FILL, FILL, 0.2)
            for s in hits.get(r, []):
                live = playing and s == step
                rr = DOT_R * (1.1 if r < 2 else 0.8) * (1.35 if live else 1)
                c = BRIGHT if live else (BRIGHT2 if r < 2 else SECOND)
                fr.node("dot", k, circle_pts(rr, 16), x0 + pitch * s + pitch / 2, y, c, c, 1.2)
                k += 1
    else:
        arp = arp or Arp()
        titles = ["mode", "rate", "range", "steps", "skip", "accent", "tones", "jump"]
        header(fr, titles, arp.values())
        notes = arp.notes()
        pitches = [p for _, p, _, _, _ in notes]
        lo, hi = min(pitches), max(pitches)
        rows = 12
        span = hi - lo + 1
        band = 1 if span <= rows else -(-span // rows)
        if band == 1:
            lo = lo - (rows - span) // 2
        top, rp = 52, 12
        def row_y(p):
            return top + rp * (rows - 1 - (p - lo) // band)
        # root rows: a rule at each row holding the key's root, labelled with its octave
        rule_k = 0
        for r in range(rows):
            p = lo + r * band
            if any((q % 12) == 0 for q in range(p, p + band)) and rule_k < 2:
                yy = top + rp * (rows - 1 - r)
                fr.node("rule", rule_k, RULE_PTS, 460, yy, GROUND, GROUND, 0.2)
                rule_k += 1
        hi_label = NOTE[(lo + band * rows - 1) % 12] + str((lo + band * rows - 1) // 12 - 1)
        lo_label = NOTE[lo % 12] + str(lo // 12 - 1)
        fr.text(T_FREE, 4, top + 4, 10, LABEL, hi_label)
        fr.text(T_FREE + 1, 4, top + rp * (rows - 1) + 4, 10, LABEL, lo_label)
        for s, p, acc, held, skipped in notes:
            y = row_y(p)
            cx = x0 + pitch * s + pitch / 2
            live = playing and s == step
            if skipped:
                fr.node("dot", k, circle_pts(DOT_R * 0.6, 14), cx, y, BLACK, QUIET, 1.0)
                k += 1
                continue
            for h in range(1, held + 1):
                fr.node("dot", k, circle_pts(DOT_R * 0.4, 10), cx + h * pitch * 0.5, y, LABEL, LABEL, 0.6)
                k += 1
            r = DOT_R * (1.5 if acc else 0.9) * (1.8 if live else 1)
            ahead = playing and s > step
            c = BRIGHT if live else (BRIGHT2 if acc else SECOND)
            # notes still to come this bar are hollow while it plays
            fr.node("dot", k, circle_pts(r, 16), cx, y, BLACK if ahead else c, c, 1.2)
            k += 1
    if playing:
        fr.node("playhead", 0, rect_pts(-1.5, 0, 1.5, 148), x0 + pitch * step + pitch / 2, 46, QUIET, QUIET, 0.2)
    # the plate's corner: which lane this is, its moon lit while it plays
    role = "drum" if drum else "arp"
    fill, stroke, sw = moon_style(role, playing)
    fr.node("moon", lane_no - 1, circle_pts(moon_radius(50, role) * (1.7 if playing else 1), 16), 448, 48,
            fill, stroke, sw)
    fr.text(T_FREE + 10, 440 - text_width(f"{lane_no} {role}", 10), 52, 10, TEXT_HI, f"{lane_no} {role}")
    return fr


# ---- M4: the patch plate ----------------------------------------------------------------------------------------------
def note_label(n):
    return NOTE[n % 12] + str(n // 12 - 1)


FOOTPRINT = {"drum": (36, 50), "bass": (28, 43), "chord": (48, 64), "lead": (67, 84), "arp": (64, 88),
             "pad": (48, 67), "off": (60, 60)}


def draw_m4(lanes, sel=0) -> Frame:
    fr = Frame()
    L = lanes[sel]
    tgt = L.target if L.target is not None else sel
    titles = ["lane", "to", "xpose", "mute", "low", "high", "", ""]
    values = [str(sel + 1), f"t{tgt + 1}", str(L.xpose), "on" if L.mute else "off", note_label(L.low),
              note_label(L.high), "", ""]
    header(fr, titles, values)
    page_strip(fr, 3)
    top, rp = 60, 17
    col0, col = 136.0, 30.8        # a digit and nine spaces in the device font
    # track stations: a column a track, numbered along the top (three text slots, spaced)
    cols = ["1         2         3", "4         5         6", "7         8"]
    for i, s in enumerate(cols):
        fr.text(T_FREE + 8 + i, col0 + 3 * i * col - 2.8, 50, 10, LABEL, s)
    for t in range(8):
        cx = col0 + t * col
        fr.node("column", t, rect_pts(-0.5, 0, 0.5, 136), cx, 54, GROUND, GROUND, 0.2)
    # the mask the route lines slide out from (drawn after them by index), then each lane's moon and name over it
    fr.node("mask", 0, rect_pts(0, 0, 116, 144), 0, 52, BLACK, BLACK, 0.1)
    for i, ln in enumerate(lanes):
        y = top + rp * i
        t = ln.target if ln.target is not None else i
        off = ln.role == "off"
        end_x = col0 + t * col
        if ln.mute or off:
            end_x = 110          # retracted behind the mask
        if i == sel:
            pass                          # the selected route is told by its bright line, end and bracket
        fr.node("rule", i, RULE_PTS, end_x, y,
                QUIET if (ln.mute or off) else (BRIGHT2 if i == sel else SECOND),
                QUIET if (ln.mute or off) else (BRIGHT2 if i == sel else SECOND), 0.2)
        if not (ln.mute or off):
            fr.node("dot", i, circle_pts(DOT_R * (1.2 if i == sel else 0.9), 16), end_x, y,
                    BRIGHT if i == sel else SECOND, BRIGHT if i == sel else SECOND, 1.2)
        fill, stroke, sw = moon_style(ln.role, False, ln.mute)
        fr.node("moon", i, circle_pts(moon_radius(ln.dens, ln.role), 16), 11, y, fill, stroke, sw)
        label = f"{i + 1} {ln.role}"
        fr.text(T_FREE + i, 25, y + 4, 10, TEXT_HI if i == sel else SECOND, label)
        if ln.mute and not off:
            fr.node("strike", i, rect_pts(0, -0.75, text_width(label, 10) + 4, 0.75), 23, y + 0.5, SECOND, SECOND, 0.2)
    fr.node("bracket", 0, rect_pts(0, 0, 2, 13), 2, top + rp * sel - 6.5, BRIGHT, BRIGHT, 0.3)

    # the register scale: eleven octave cells, c-1 at the bottom; the window [low, high] is ground, the lane's
    # notes (its range moved by xpose) inside the window are lit
    sx, sy0, cell_h = 420, 190, 12.4
    fr.node("playhead", 0, rect_pts(-1.5, 0, 1.5, 136), sx - 4, 54, GROUND, GROUND, 0.2)
    natural = FOOTPRINT[L.role]             # the selected lane's notes before xpose
    lo_n, hi_n = natural[0] + L.xpose, natural[1] + L.xpose
    for o in range(11):
        n0, n1 = 12 * o, 12 * o + 11
        in_window = n1 >= L.low and n0 <= L.high
        plays = in_window and not L.mute and n1 >= max(lo_n, L.low) and n0 <= min(hi_n, L.high)
        c = BRIGHT2 if plays else (FILL if in_window else BLACK)
        s = BRIGHT2 if plays else (QUIET if in_window else GROUND)
        fr.node("octave", o, rect_pts(0, -cell_h + 1.5, 30, 0), sx, sy0 - o * cell_h, c, s, 1.0)
    for k, n in enumerate((L.low, L.high)):
        y = sy0 - (n / 128) * 11 * cell_h - (0 if k == 0 else 0)
        fr.node("cap", k, rect_pts(-6, -0.75, 36, 0.75), sx, y, BRIGHT, BRIGHT, 0.3)
    return fr


# ---- frame sets -----------------------------------------------------------------------------------------------------
def write(fr: Frame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(fr.svg())


M1_KEYS = ["key", "scale", "prog", "dens", "cmplx", "hrate", "swing", "evolve"]


def build(out: Path):
    # M1
    d = out / "m1"
    write(draw_m1(Song()), d / "rest.svg")
    write(draw_m1(Song(), position=1, playing=True, step=4, lit={0, 1, 2, 4}), d / "playing.svg")
    for n, k in enumerate(M1_KEYS, 1):
        for v in (0.0, 0.5, 1.0):
            write(draw_m1(Song(**{k: v})), d / f"c{n}-{round(v * 100):03d}.svg")
    # M2: the selected lane is 5 (arp)
    d = out / "m2"
    sel = 4
    write(draw_m2(default_lanes(), sel), d / "rest.svg")
    write(draw_m2(default_lanes(), sel, playing=True, step=15, lit={0, 1, 2, 4}), d / "playing.svg")
    m2 = [("lane", [0, 3, 7]), ("role", ["off", "chord", "lead"]), ("dens", [0, 50, 100]), ("oct", [-2, 0, 2]),
          ("vel", [0, 50, 100]), ("vary", [0, 50, 100]), ("lock", [0, 1, 2]), ("gate", [5, 52, 100])]
    for n, (k, vals) in enumerate(m2, 1):
        for tag, v in zip(("000", "050", "100"), vals):
            lanes = default_lanes()
            s = 1 if k == "lock" else sel      # lock only steers a bass lane (generator.h), so show it on one
            if k == "lane":
                s = v
            else:
                setattr(lanes[s], k, v)
            write(draw_m2(lanes, s), d / f"c{n}-{tag}.svg")
    # M3: an arp lane, then a drum lane's rest and playing
    d = out / "m3"
    write(draw_m3(Arp()), d / "rest.svg")
    write(draw_m3(Arp(), playing=True, step=2), d / "playing.svg")
    arp_sets = [("mode", [0, 3, 5]), ("rate", [0, 1, 2]), ("range", [0, 1, 2]), ("steps", [3, 5, 8]),
                ("skip", [0, 50, 100]), ("accent", [0, 50, 100]), ("tones", [0, 1, 1]), ("jump", [0, 50, 100])]
    for n, (k, vals) in enumerate(arp_sets, 1):
        for tag, v in zip(("000", "050", "100"), vals):
            a = Arp()
            setattr(a, k, v)
            write(draw_m3(a), d / f"c{n}-{tag}.svg")
    write(draw_m3(drum=True, lane_no=1), out / "m3-drum" / "rest.svg")
    write(draw_m3(drum=True, playing=True, step=4, lane_no=1), out / "m3-drum" / "playing.svg")
    # M4: lane 3 selected
    d = out / "m4"
    sel = 2
    write(draw_m4(default_lanes(), sel), d / "rest.svg")
    m4 = [("lane", [0, 3, 7]), ("target", [0, 4, 7]), ("xpose", [-24, 0, 24]), ("mute", [False, False, True]),
          ("low", [0, 64, 127]), ("high", [0, 64, 127])]
    for n, (k, vals) in enumerate(m4, 1):
        for tag, v in zip(("000", "050", "100"), vals):
            lanes = default_lanes()
            s = sel
            if k == "lane":
                s = v
            else:
                setattr(lanes[sel], k, v)
                if k == "high":
                    lanes[sel].low = 0
            write(draw_m4(lanes, s), d / f"c{n}-{tag}.svg")
    print(f"nodes declared: {NODE_COUNT}; camera elevation {CAM_EL:.1f} degrees")


if __name__ == "__main__":
    build(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "frames")
