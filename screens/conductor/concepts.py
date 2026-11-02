#!/usr/bin/env python3
"""Five shape languages for each of Conductor's four pages: a round of concepts, not frame sets.

Brian's notes so far: the song page was too busy, the lane dots meant nothing, grey shouldn't fill a body
unless it's showing depth, one lane at a time on M2, and not everything has to be a circle or a square.
So every concept here is drawn in lines, ribbons, wedges, stems, chevrons and arcs, outline only, grey only,
and shows the page while the sequencer plays (step 6 of bar 2, so the second chord sounds).

  M1 song   1 dial · 2 root stair · 3 voicing stacks · 4 tide and seismograph · 5 arc diagram
  M2 lane   1 stems · 2 bars · 3 envelopes · 4 chevrons · 5 spokes
  M3 lane   1 contour · 2 step plot · 3 pitch stems · 4 direction arrows · 5 diamonds on a keyboard
  M4 route  1 patch cables · 2 straight wires · 3 cross matrix · 4 circuit traces · 5 arrows and register

    python3 concepts.py      → concepts/<page>-<n>.svg, concepts/<page>.svg + .png (1:1 contact sheet)

These are drawn freely to compare languages; the chosen one gets rebuilt into device node pools afterwards.
"""
from __future__ import annotations

import math
import subprocess
from pathlib import Path

import gen_frames as G

HERE = Path(__file__).resolve().parent
OUT = HERE / "concepts"
BLACK, FILL, GROUND, QUIET, LABEL, SECOND, BRIGHT2, BRIGHT = (
    G.BLACK, G.FILL, G.GROUND, G.QUIET, G.LABEL, G.SECOND, G.BRIGHT2, G.BRIGHT)
TEXT_HI = G.TEXT_HI
f = G.f
tw = G.text_width
STEP_NOW, BAR_NOW = 6, 1


class Canvas:
    def __init__(self, header_svg: str, page: int):
        self.els: list[str] = []
        self.header_svg = header_svg
        self.page = page

    # a line or polyline as a closed ribbon of width w
    def ribbon(self, pts, w, color):
        pts = _dedupe(pts)
        if len(pts) < 2:
            return
        if len(pts) > 31:                    # one path holds at most 64 points: split long lines, overlapping a point
            for i in range(0, len(pts) - 1, 30):
                self.ribbon(pts[i:i + 31], w, color)
            return
        left, right = [], []
        for i, p in enumerate(pts):
            if i == 0:
                n = _normal(pts[0], pts[1])
            elif i == len(pts) - 1:
                n = _normal(pts[-2], pts[-1])
            else:
                a, b = _normal(pts[i - 1], pts[i]), _normal(pts[i], pts[i + 1])
                n = (a[0] + b[0], a[1] + b[1])
                ln = math.hypot(*n) or 1
                n = (n[0] / ln, n[1] / ln)
                cos = a[0] * n[0] + a[1] * n[1]
                k = 1 / max(cos, 0.5)
                n = (n[0] * k, n[1] * k)
            left.append((p[0] + n[0] * w / 2, p[1] + n[1] * w / 2))
            right.append((p[0] - n[0] * w / 2, p[1] - n[1] * w / 2))
        self.poly(left + right[::-1], color, color, 0.2)

    def line(self, a, b, w, color):
        self.ribbon([a, b], w, color)

    def poly(self, pts, stroke, fill=BLACK, sw=1.2):
        pts = _dedupe(pts)
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
        self.els.append(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{f(sw)}"/>')

    def outline(self, pts, stroke, sw=1.2):
        self.poly(pts, stroke, BLACK, sw)

    def text(self, x, y, size, color, s):
        self.els.append(f'<text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{color}" stroke="none" '
                        f'font-family="{G.FONT}" font-size="{f(size)}px">{G.escape(s)}</text>')

    def svg(self):
        page_names = G.PAGE_NAMES
        strip = []
        for p in range(4):
            x = 120 * p
            strip.append(f'<path d="M {x + 2} 204 L {x + 118} 204 L {x + 118} 205 L {x + 2} 205 Z" fill="{FILL}" '
                         f'stroke="{FILL}" stroke-width="0.2"/>')
            if p == self.page:
                strip.append(f'<path d="M {x + 2} 203 L {x + 118} 203 L {x + 118} 205 L {x + 2} 205 Z" '
                             f'fill="{BRIGHT2}" stroke="{BRIGHT2}" stroke-width="0.2"/>')
            c = TEXT_HI if p == self.page else LABEL
            strip.append(f'<text transform="matrix(1 0 0 1 {x + 4} 216)" fill="{c}" stroke="none" '
                         f'font-family="{G.FONT}" font-size="10px">{page_names[p]}</text>')
        return "\n".join(['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
                          '<g id="preview_canvas"><rect x="0" y="0" width="480" height="220" fill="#000000" '
                          'stroke="none"/></g>', self.header_svg] + self.els + strip + ["</svg>"]) + "\n"


def _dedupe(pts):
    out = []
    for p in pts:
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > 0.3:
            out.append((round(p[0], 3), round(p[1], 3)))
    if len(out) > 2 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) < 0.3:
        out.pop()
    return out


def _normal(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy) or 1
    return (-dy / ln, dx / ln)


def arc(cx, cy, r, a0, a1, n=24, ry=None):
    ry = r if ry is None else ry
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + 1)]


def bezier(p0, p1, p2, p3, n=20):
    pts = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3
        pts.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return pts


def tri(cx, cy, size, direction):
    """A triangle pointing up, down, left or right, centred on (cx, cy)."""
    s = size
    return {"up": [(cx, cy - s), (cx + s * 0.9, cy + s * 0.6), (cx - s * 0.9, cy + s * 0.6)],
            "down": [(cx, cy + s), (cx - s * 0.9, cy - s * 0.6), (cx + s * 0.9, cy - s * 0.6)],
            "right": [(cx + s, cy), (cx - s * 0.6, cy + s * 0.9), (cx - s * 0.6, cy - s * 0.9)],
            "left": [(cx - s, cy), (cx + s * 0.6, cy - s * 0.9), (cx + s * 0.6, cy + s * 0.9)]}[direction]


def chevron(cx, cy, size, w=1.4):
    """A right-pointing chevron as one closed outline (a bent ribbon)."""
    s = size
    return [(cx - s * 0.5, cy - s), (cx + s * 0.5, cy), (cx - s * 0.5, cy + s),
            (cx - s * 0.5 - w, cy + s - w * 0.9), (cx + s * 0.5 - w * 1.3, cy), (cx - s * 0.5 - w, cy - s + w * 0.9)]


def diamond(cx, cy, s):
    return [(cx, cy - s), (cx + s * 0.8, cy), (cx, cy + s), (cx - s * 0.8, cy)]


# ---- shared music ----------------------------------------------------------------------------------------------------
SONG = G.Song()
LOOP = SONG.loop
SCALE, KEY = SONG.scale, SONG.key
NOW = LOOP[BAR_NOW]
KICKS = SONG.kicks()


def header_for(page: str) -> str:
    fr = G.Frame()
    if page == "m1":
        t, v = SONG.titles_values()
    elif page == "m2":
        t = ["lane", "role", "dens", "oct", "vel", "vary", "lock", "gate"]
        v = ["5", "arp", "50", "0", "80", "50", "acnt", "60"]
    elif page == "m3":
        t = ["mode", "rate", "range", "steps", "skip", "accent", "tones", "jump"]
        v = G.Arp().values()
    else:
        t = ["lane", "to", "xpose", "mute", "low", "high", "", ""]
        v = ["3", "t3", "0", "off", "C-1", "G9", "", ""]
    G.header(fr, t, v)
    return fr.header_svg


def name(d, seventh=False):
    return G.chord_name(KEY, SCALE, d, seventh)


def groove_weight(s):
    """0 plain step, 1 beat, 2 backbeat, 3 kick."""
    return 3 if KICKS[s] else 2 if s in (4, 12) else 1 if s % 4 == 0 else 0


def comb(c, x0, x1, y, steps=16, up=True, now=None):
    """The bar as a graduated line: kicks tallest, backbeats, beats, steps; the playing step bright."""
    pitch = (x1 - x0) / steps
    c.line((x0, y), (x1, y), 1.0, GROUND)
    for s in range(steps):
        x = x0 + pitch * s + pitch / 2
        h = [3, 6, 10, 14][groove_weight(s)]
        col = BRIGHT if s == now else [QUIET, LABEL, SECOND, SECOND][groove_weight(s)]
        c.line((x, y), (x, y - h if up else y + h), 1.6 if groove_weight(s) == 3 else 1.2, col)


# ---- M1: song --------------------------------------------------------------------------------------------------------
def m1_dial():
    """A semicircular dial: twelve graduations for the key, the scale's degrees as pointers on the rim, the loop's
    chords as longer pointers, the sounding chord as the needle. The groove runs round an inner arc."""
    c = Canvas(header_for("m1"), 0)
    cx, cy, R = 240, 196, 140
    c.ribbon(arc(cx, cy, R, math.pi, 2 * math.pi, 40), 1.2, GROUND)
    def ang(pc):
        return math.pi + math.pi * (pc + 0.5) / 12
    for pc in range(12):
        a = ang(pc)
        c.line((cx + (R - 4) * math.cos(a), cy + (R - 4) * math.sin(a)),
               (cx + (R + 4) * math.cos(a), cy + (R + 4) * math.sin(a)), 1.0, QUIET)
    for d in range(7):
        pc = (KEY + SCALE[d]) % 12
        a = ang(pc)
        in_loop = d in LOOP
        L = 16 if in_loop else 8
        tip = (cx + (R - 2) * math.cos(a), cy + (R - 2) * math.sin(a))
        base_c = (cx + (R - 2 - L) * math.cos(a), cy + (R - 2 - L) * math.sin(a))
        nx, ny = -math.sin(a), math.cos(a)
        wd = 4 if in_loop else 2.5
        c.outline([tip, (base_c[0] + nx * wd, base_c[1] + ny * wd), (base_c[0] - nx * wd, base_c[1] - ny * wd)],
                  SECOND if in_loop else QUIET, 1.2)
        if in_loop:
            label = name(d) + " " + "·".join(str(i + 1) for i, x in enumerate(LOOP) if x == d)
            lx, ly = cx + (R + 14) * math.cos(a), cy + (R + 14) * math.sin(a)
            col = TEXT_HI if d == NOW else SECOND
            c.text(lx - tw(label, 10) / 2, ly + 4, 10, col, label)
    a = ang((KEY + SCALE[NOW]) % 12)
    nx, ny = -math.sin(a), math.cos(a)
    tip = (cx + (R - 22) * math.cos(a), cy + (R - 22) * math.sin(a))
    c.outline([tip, (cx + nx * 3, cy + ny * 3), (cx - nx * 3, cy - ny * 3)], BRIGHT, 1.6)
    # the groove on an inner arc, ticks pointing in
    r2 = 70
    for s in range(16):
        a2 = math.pi + math.pi * (s + 0.5) / 16
        h = [3, 6, 9, 13][groove_weight(s)]
        col = BRIGHT2 if s == STEP_NOW else [QUIET, LABEL, SECOND, SECOND][groove_weight(s)]
        c.line((cx + r2 * math.cos(a2), cy + r2 * math.sin(a2)),
               (cx + (r2 - h) * math.cos(a2), cy + (r2 - h) * math.sin(a2)), 1.4, col)
    c.text(10, 62, 20, TEXT_HI, name(NOW))
    c.text(10, 76, 10, LABEL, "next " + name(LOOP[(BAR_NOW + 1) % 4]))
    return c


def m1_stair():
    """Root stair: time runs across four bars, the scale's degrees are seven quiet staff lines, and the loop is one
    stepped line from chord to chord. The groove is a row of stems under it."""
    c = Canvas(header_for("m1"), 0)
    x0, x1 = 44, 460
    bar_w = (x1 - x0) / 4
    top, gap = 62, 14
    def yd(d):
        return top + gap * (6 - d)
    numerals = ["I", "ii", "iii", "IV", "V", "vi", "vii"]
    for d in range(7):
        c.line((x0, yd(d)), (x1, yd(d)), 0.8, FILL if d not in LOOP else GROUND)
        c.text(10 if len(numerals[d]) < 3 else 8, yd(d) + 4, 10, LABEL, numerals[d])
    pts = []
    for i, d in enumerate(LOOP):
        xa, xb = x0 + bar_w * i + 3, x0 + bar_w * (i + 1) - 3
        pts += [(xa, yd(d)), (xb, yd(d))]
        c.text(xa + 2, yd(d) - 5, 10, TEXT_HI if i == BAR_NOW else SECOND, name(d))
    c.ribbon(pts, 2.0, SECOND)
    xa, xb = x0 + bar_w * BAR_NOW + 3, x0 + bar_w * (BAR_NOW + 1) - 3
    c.line((xa, yd(NOW)), (xb, yd(NOW)), 3.0, BRIGHT)
    for i in range(1, 4):
        c.line((x0 + bar_w * i, top - 6), (x0 + bar_w * i, yd(0) + 6), 0.8, GROUND)
    px = x0 + bar_w * BAR_NOW + bar_w * STEP_NOW / 16
    c.line((px, top - 8), (px, yd(0) + 8), 1.0, LABEL)
    comb(c, x0, x1, 194, now=STEP_NOW)
    return c


def m1_stacks():
    """Voicing stacks: each of the loop's four chords stands as its three notes, short bars on one pitch axis, joined by
    a spine. You see the voicing move from chord to chord. A ladder at the left marks the scale."""
    c = Canvas(header_for("m1"), 0)
    lo = 52
    def yp(p):
        return 176 - (p - lo) * 3.4
    # the scale ladder
    for p in range(lo, lo + 36):
        in_scale = (p - KEY) % 12 in SCALE
        if in_scale:
            root = (p - KEY) % 12 == 0
            c.line((30, yp(p)), (30 + (12 if root else 6), yp(p)), 1.0, LABEL if root else QUIET)
    c.line((30, yp(lo + 35)), (30, yp(lo)), 1.0, GROUND)
    for i, d in enumerate(LOOP):
        cx = 110 + i * 96
        root = 48 + KEY + SCALE[d] + (12 if SCALE[d] < 5 else 0)
        tones = [root + (SCALE[(d + k) % 7] - SCALE[d]) % 12 for k in (0, 2, 4)]
        tones = sorted(t if t >= root else t + 12 for t in tones)
        sounding = i == BAR_NOW
        col = BRIGHT if sounding else SECOND
        w = 36 if sounding else 26
        c.line((cx, yp(tones[0])), (cx, yp(tones[-1])), 1.0, QUIET)
        for t in tones:
            c.line((cx - w / 2, yp(t)), (cx + w / 2, yp(t)), 2.4 if sounding else 1.6, col)
        c.text(cx - tw(name(d), 10) / 2, 192, 10, TEXT_HI if sounding else SECOND, name(d))
        c.text(cx - tw(str(i + 1), 10) / 2, yp(tones[-1]) - 8, 10, LABEL, str(i + 1))
    # the groove as chevrons along the top
    for s in range(16):
        x = 92 + s * 24
        g = groove_weight(s)
        if g:
            c.outline(chevron(x, 50, [0, 3, 4, 5.5][g]), BRIGHT2 if s == STEP_NOW else [QUIET, LABEL, SECOND, SECOND][g], 0.8)
        else:
            c.line((x - 1.5, 50), (x + 1.5, 50), 1.2, QUIET)
    return c


def m1_tide():
    """Tide and seismograph: the loop's roots as one smooth line that eases from chord to chord across the phrase, the
    groove as a seismograph trace under it, kicks the tallest spikes."""
    c = Canvas(header_for("m1"), 0)
    x0, x1 = 24, 456
    bar_w = (x1 - x0) / 4
    def yd(d):
        return 140 - d * 12
    pts = []
    for i, d in enumerate(LOOP):
        nd = LOOP[(i + 1) % 4]
        for j in range(8):
            t = j / 8
            k = 0 if t < 0.7 else (1 - math.cos(math.pi * (t - 0.7) / 0.3)) / 2
            pts.append((x0 + bar_w * (i + t), yd(d) + (yd(nd) - yd(d)) * k))
    pts.append((x1, yd(LOOP[0])))
    c.ribbon(pts, 1.8, SECOND)
    for i, d in enumerate(LOOP):
        xm = x0 + bar_w * i + 6
        c.text(xm, yd(d) - 8, 10, TEXT_HI if i == BAR_NOW else LABEL, name(d))
        c.line((x0 + bar_w * i, 60), (x0 + bar_w * i, 150), 0.8, FILL)
    px = x0 + bar_w * (BAR_NOW + STEP_NOW / 16)
    py = yd(NOW)
    c.outline(tri(px, py - 7, 4, "down"), BRIGHT, 1.4)
    c.line((px, 60), (px, 192), 0.8, QUIET)
    # seismograph: one trace, a spike per step
    base = 178
    trace = [(x0, base)]
    pitch = (x1 - x0) / 16
    for s in range(16):
        x = x0 + pitch * s + pitch / 2
        h = [2, 5, 9, 15][groove_weight(s)]
        trace += [(x - 3, base), (x - 0.8, base - h), (x + 0.8, base + h * 0.4), (x + 3, base)]
    trace.append((x1, base))
    c.ribbon(trace[:31], 1.1, SECOND)
    c.ribbon(trace[30:], 1.1, SECOND)
    c.text(10, 62, 20, TEXT_HI, name(NOW))
    return c


def m1_arcs():
    """Arc diagram: the twelve pitch classes along a line, the scale's degrees marked by small triangles, and the
    progression drawn as arches from each chord to the next; the arch that's sounding is bright."""
    c = Canvas(header_for("m1"), 0)
    x0, x1, y = 36, 444, 150
    pitch = (x1 - x0) / 11
    c.line((x0 - 10, y), (x1 + 10, y), 1.0, GROUND)
    def xp(pc):
        return x0 + pitch * pc
    for pc in range(12):
        in_scale = (pc - KEY) % 12 in SCALE
        if in_scale:
            d = SCALE.index((pc - KEY) % 12)
            c.outline(tri(xp(pc), y + 6, 4 if d in LOOP else 3, "up"), SECOND if d in LOOP else QUIET, 1.2)
            if d in LOOP:
                c.text(xp(pc) - tw(name(d), 10) / 2, y + 22, 10, TEXT_HI if d == NOW else SECOND, name(d))
        else:
            c.line((xp(pc), y - 2), (xp(pc), y + 2), 1.0, QUIET)
    for i, d in enumerate(LOOP):
        a = xp((KEY + SCALE[d]) % 12)
        b = xp((KEY + SCALE[LOOP[(i + 1) % 4]]) % 12)
        if abs(a - b) < 1:
            continue
        cx, r = (a + b) / 2, abs(a - b) / 2
        pts = arc(cx, y - 4, r, math.pi, 2 * math.pi, 28, ry=min(r * 0.8, 84))
        if a > b:
            pts = pts[::-1]
        sounding = i == BAR_NOW
        c.ribbon(pts, 2.2 if sounding else 1.2, BRIGHT if sounding else QUIET)
        mid = pts[len(pts) // 2]
        c.text(mid[0] - 3, mid[1] - 5, 10, LABEL, str(i + 1))
    comb(c, 24, 456, 196, now=STEP_NOW)
    c.text(10, 62, 20, TEXT_HI, name(NOW))
    return c


# ---- M2: one lane ----------------------------------------------------------------------------------------------------
LANE = G.Lane("arp")
HITS = G.lane_hits(LANE, 4)


def lane_strip(c: Canvas, sel=4, style="ticks"):
    """Which lane is shown, among eight: short bars whose height is how much each lane plays; the shown one bright."""
    lanes = G.default_lanes()
    for i, ln in enumerate(lanes):
        x = 300 + i * 22
        h = 3 if ln.role == "off" else 4 + ln.dens / 100 * 10
        col = BRIGHT if i == sel else (QUIET if ln.role == "off" else LABEL)
        c.line((x, 58), (x, 58 - h), 2.0 if i == sel else 1.2, col)
    c.text(300 - 4 + sel * 22 - 1, 70, 10, TEXT_HI, str(sel + 1))
    c.text(10, 62, 20, TEXT_HI, "5 arp")


def steps_x(s, x0=40, x1=460):
    return x0 + (x1 - x0) / 16 * (s + 0.5)


def m2_stems():
    """Stems: each hit a stem up from the line, as tall as it's loud; its flag reaches right as long as the note
    holds; may-vary hits are broken stems; the octave lifts the line."""
    c = Canvas(header_for("m2"), 1)
    lane_strip(c)
    base = 180 - (LANE.oct + 2) * 4
    c.line((40, base), (460, base), 1.0, GROUND)
    rnd = G.random.Random(104)
    cand = sorted(HITS)
    rnd.shuffle(cand)
    vary = set(cand[: round(len(cand) * LANE.vary / 100)])
    for s, acc in HITS.items():
        x = steps_x(s)
        h = 20 + LANE.vel / 100 * 60 * (1.15 if acc else 1)
        col = BRIGHT if s == STEP_NOW else (BRIGHT2 if acc else SECOND)
        if s in vary:
            c.line((x, base), (x, base - h * 0.45), 1.6, QUIET)
            c.line((x, base - h * 0.6), (x, base - h), 1.6, QUIET)
        else:
            c.line((x, base), (x, base - h), 1.8, col)
        flag = 4 + LANE.gate / 100 * 18
        c.ribbon([(x, base - h), (x + flag, base - h + 5)], 1.4, col if s not in vary else QUIET)
    return c


def m2_bars():
    """Bars: each note a bar as long as it holds, at the lane's register; accents carry a notch at their start."""
    c = Canvas(header_for("m2"), 1)
    lane_strip(c)
    for o in range(5):
        y = 176 - o * 24
        c.line((40, y), (460, y), 0.8, FILL if o != LANE.oct + 2 else GROUND)
        c.text(14, y + 4, 10, LABEL, ["-2", "-1", "0", "+1", "+2"][o])
    y = 176 - (LANE.oct + 2) * 24
    step = 420 / 16
    for s, acc in HITS.items():
        xa = 40 + step * s + 1
        length = max(3, step * LANE.gate / 100 * 1.6)
        hgt = 3 + LANE.vel / 100 * 6
        col = BRIGHT if s == STEP_NOW else (BRIGHT2 if acc else SECOND)
        c.outline([(xa, y - hgt), (xa + length, y - hgt), (xa + length, y), (xa, y)], col, 1.2)
        if acc:
            c.line((xa, y - hgt - 5), (xa, y + 3), 1.4, col)
    return c


def m2_envelopes():
    """Envelopes: each note drawn as its own shape on the line: it rises as high as it's loud, holds as long as its
    gate, falls away. Accents peak; may-vary notes are drawn half-height."""
    c = Canvas(header_for("m2"), 1)
    lane_strip(c)
    base = 182
    c.line((36, base), (464, base), 1.0, GROUND)
    step = 420 / 16
    lift = (LANE.oct + 2) * 6
    for s, acc in HITS.items():
        xa = 40 + step * s + 2
        h = (24 + LANE.vel / 100 * 56) * (1.2 if acc else 1)
        hold = max(2, step * 1.6 * LANE.gate / 100 - 8)
        col = BRIGHT if s == STEP_NOW else (BRIGHT2 if acc else SECOND)
        top = base - lift - h
        pts = [(xa, base), (xa + 3, top), (xa + 3 + hold, top + h * 0.35), (xa + 6 + hold, base)]
        c.outline(pts, col, 1.2)
    return c


def m2_chevrons():
    """Chevrons: each hit a chevron pointing the way time goes, as big as it's loud, on the lane's register line;
    accents are doubled; the gate trails behind as a hairline."""
    c = Canvas(header_for("m2"), 1)
    lane_strip(c)
    y = 130 - LANE.oct * 18
    c.line((40, y), (460, y), 0.8, GROUND)
    for s, acc in HITS.items():
        x = steps_x(s)
        size = 5 + LANE.vel / 100 * 8
        col = BRIGHT if s == STEP_NOW else (BRIGHT2 if acc else SECOND)
        c.line((x - size * 0.5 - LANE.gate / 100 * 16, y), (x - size * 0.5 - 2, y), 1.0, QUIET)
        c.outline(chevron(x, y, size, 1.8), col, 0.6)
        if acc:
            c.outline(chevron(x + 5, y, size, 1.8), col, 0.6)
    for o in range(-2, 3):
        yy = 130 - o * 18
        c.line((24, yy), (30, yy), 1.0, BRIGHT2 if o == LANE.oct else QUIET)
    return c


def m2_spokes():
    """Spokes: the bar goes round once; each hit a spoke out from the rim, as long as it's loud, bent at the end for
    as long as it holds. A hand points at the step that's playing."""
    c = Canvas(header_for("m2"), 1)
    lane_strip(c)
    cx, cy, r0 = 240, 132, 26 + (LANE.oct + 2) * 4
    c.ribbon(arc(cx, cy, r0, 0, 2 * math.pi * 0.999, 40), 1.0, GROUND)
    for s in range(16):
        a = -math.pi / 2 + 2 * math.pi * s / 16
        if s in HITS:
            acc = HITS[s]
            L = 10 + LANE.vel / 100 * 18 * (1.2 if acc else 1)
            col = BRIGHT if s == STEP_NOW else (BRIGHT2 if acc else SECOND)
            p0 = (cx + r0 * math.cos(a), cy + r0 * math.sin(a))
            p1 = (cx + (r0 + L) * math.cos(a), cy + (r0 + L) * math.sin(a))
            bend = a + LANE.gate / 100 * 0.32
            p2 = (cx + (r0 + L) * math.cos(bend), cy + (r0 + L) * math.sin(bend))
            c.ribbon([p0, p1, p2], 1.6, col)
        else:
            p0 = (cx + r0 * math.cos(a), cy + r0 * math.sin(a))
            c.line(p0, (cx + (r0 + 3) * math.cos(a), cy + (r0 + 3) * math.sin(a)), 1.0, QUIET)
    a = -math.pi / 2 + 2 * math.pi * STEP_NOW / 16
    c.line((cx, cy), (cx + (r0 - 6) * math.cos(a), cy + (r0 - 6) * math.sin(a)), 1.4, LABEL)
    return c


# ---- M3: the arp -----------------------------------------------------------------------------------------------------
ARP = G.Arp()
NOTES = [n for n in ARP.notes() if not n[4]]
PITCHES = [n[1] for n in NOTES]
PLO, PHI = min(PITCHES), max(PITCHES)


def yp3(p, top=56, bottom=184):
    return bottom - (p - PLO) / max(1, PHI - PLO) * (bottom - top)


def x3(s):
    return 44 + 26 * s + 13


def range_labels(c):
    c.text(4, yp3(PHI) + 4, 10, LABEL, G.note_label(PHI))
    c.text(4, yp3(PLO) + 4, 10, LABEL, G.note_label(PLO))


def m3_contour():
    """Contour: the arp as one line through its notes, a short level tick at each; accents add a vertical tick."""
    c = Canvas(header_for("m3"), 2)
    range_labels(c)
    pts = [(x3(s), yp3(p)) for s, p, *_ in NOTES]
    c.ribbon(pts, 1.4, QUIET)
    for s, p, acc, *_ in NOTES:
        x, y = x3(s), yp3(p)
        col = BRIGHT if s == STEP_NOW else (BRIGHT2 if acc else SECOND)
        c.line((x - 6, y), (x + 6, y), 2.2, col)
        if acc:
            c.line((x, y - 5), (x, y + 5), 1.4, col)
    c.line((x3(STEP_NOW), 46), (x3(STEP_NOW), 194), 0.8, GROUND)
    return c


def m3_steps():
    """Step plot: each note held level for its step, risers between them, so the arp reads as a staircase."""
    c = Canvas(header_for("m3"), 2)
    range_labels(c)
    pts = []
    for i, (s, p, acc, *_r) in enumerate(NOTES):
        y = yp3(p)
        pts += [(x3(s) - 12, y), (x3(s) + 12, y)]
    for chunk in (pts[:32], pts[30:]):
        if len(chunk) > 1:
            c.ribbon(chunk, 1.6, SECOND)
    for s, p, acc, *_ in NOTES:
        if acc or s == STEP_NOW:
            y = yp3(p)
            c.line((x3(s) - 12, y), (x3(s) + 12, y), 3.0, BRIGHT if s == STEP_NOW else BRIGHT2)
    return c


def m3_stems():
    """Pitch stems: a stem from the floor up to each note, a cap on top; the arp's shape is the skyline."""
    c = Canvas(header_for("m3"), 2)
    range_labels(c)
    floor = 190
    c.line((44, floor), (460, floor), 1.0, GROUND)
    for s, p, acc, *_ in NOTES:
        x, y = x3(s), yp3(p)
        col = BRIGHT if s == STEP_NOW else (BRIGHT2 if acc else SECOND)
        c.line((x, floor), (x, y), 1.0, QUIET)
        c.line((x - (6 if acc else 4), y), (x + (6 if acc else 4), y), 2.4, col)
    return c


def m3_arrows():
    """Direction arrows: each note a triangle pointing where the arp went from the note before, up, down or level.
    The mode reads straight off it: up is all up, updn is a run of ups then downs."""
    c = Canvas(header_for("m3"), 2)
    range_labels(c)
    prev = None
    for s, p, acc, *_ in NOTES:
        x, y = x3(s), yp3(p)
        direction = "right" if prev is None or p == prev else ("up" if p > prev else "down")
        col = BRIGHT if s == STEP_NOW else (BRIGHT2 if acc else SECOND)
        c.outline(tri(x, y, 6 if acc else 4.5, direction), col, 1.3)
        prev = p
    return c


def m3_keyboard():
    """Diamonds on a keyboard: a one-octave-per-band keyboard runs up the left edge; each note a diamond on its pitch
    row, its row's key lit there, so the chord tones and the range sit against something you know."""
    c = Canvas(header_for("m3"), 2)
    lo, hi = PLO - 1, PHI + 1
    def yk(p):
        return 188 - (p - lo) / (hi - lo) * 136
    sharps = {1, 3, 6, 8, 10}
    for p in range(lo, hi + 1):
        y = yk(p)
        is_sharp = p % 12 in sharps
        used = p in PITCHES
        c.line((6, y), (6 + (10 if is_sharp else 18), y), 1.0, SECOND if used else (QUIET if not is_sharp else GROUND))
        if p % 12 == 0:
            c.text(28, y + 4, 10, LABEL, G.note_label(p))
    for s, p, acc, *_ in NOTES:
        x, y = x3(s) + 10, yk(p)
        col = BRIGHT if s == STEP_NOW else (BRIGHT2 if acc else SECOND)
        c.outline(diamond(x, y, 6 if acc else 4.5), col, 1.3)
    return c


# ---- M4: route -------------------------------------------------------------------------------------------------------
LANES = G.default_lanes()
SEL4 = 2


def lane_names(c, x=8, top=58, gap=17, sel=SEL4):
    for i, ln in enumerate(LANES):
        col = TEXT_HI if i == sel else (LABEL if ln.role == "off" else SECOND)
        c.text(x, top + gap * i + 4, 10, col, f"{i + 1} {ln.role}")


def m4_cables():
    """Patch cables: each lane's jack on the left, each track's jack on the right, a cable sagging between them.
    An off lane's cable hangs unplugged."""
    c = Canvas(header_for("m4"), 3)
    lane_names(c)
    for t in range(8):
        y = 58 + 17 * t
        c.outline(tri(436, y, 4, "left"), QUIET, 1.0)
        c.text(446, y + 4, 10, SECOND, f"t{t + 1}")
    for i, ln in enumerate(LANES):
        y0 = 58 + 17 * i
        c.outline(tri(70, y0, 4, "right"), SECOND if ln.role != "off" else QUIET, 1.0)
        if ln.role == "off":
            c.ribbon(bezier((74, y0), (90, y0 + 6), (96, y0 + 14), (100, y0 + 16), 8), 1.0, QUIET)
            continue
        t = i
        y1 = 58 + 17 * t
        sag = 8 + abs(y1 - y0) * 0.2
        pts = bezier((74, y0), (200, y0 + sag), (310, y1 + sag), (430, y1), 22)
        c.ribbon(pts, 2.0 if i == SEL4 else 1.2, BRIGHT if i == SEL4 else SECOND)
    return c


def m4_wires():
    """Straight wires: lanes in a column on the left, tracks in a column on the right, one straight wire each;
    crossings show a remap at a glance. The selected lane's wire is bright."""
    c = Canvas(header_for("m4"), 3)
    lane_names(c)
    targets = [0, 1, 4, 3, 2, 5, 6, 7]
    for t in range(8):
        y = 58 + 17 * t
        c.line((408, y), (416, y), 1.4, QUIET)
        c.text(424, y + 4, 10, SECOND, f"t{t + 1}")
    for i, ln in enumerate(LANES):
        y0 = 58 + 17 * i
        c.line((72, y0), (80, y0), 1.4, SECOND if ln.role != "off" else QUIET)
        if ln.role == "off":
            continue
        y1 = 58 + 17 * targets[i]
        c.line((80, y0), (408, y1), 2.0 if i == SEL4 else 1.0, BRIGHT if i == SEL4 else SECOND)
    return c


def m4_crosses():
    """Cross matrix: lanes down, tracks across, a quiet plus at every junction and a bold cross where a lane plays a
    track. A muted lane's cross is open (the arms don't meet)."""
    c = Canvas(header_for("m4"), 3)
    lane_names(c)
    col0, col = 130, 36
    for t in range(8):
        c.text(col0 + col * t - 3, 48, 10, LABEL, str(t + 1))
    for i, ln in enumerate(LANES):
        y = 58 + 17 * i
        for t in range(8):
            x = col0 + col * t
            if t == i and ln.role != "off":
                cc = BRIGHT if i == SEL4 else SECOND
                s = 6 if i == SEL4 else 5
                c.line((x - s, y - s), (x + s, y + s), 1.8, cc)
                c.line((x - s, y + s), (x + s, y - s), 1.8, cc)
            else:
                c.line((x - 2, y), (x + 2, y), 1.0, GROUND)
                c.line((x, y - 2), (x, y + 2), 1.0, GROUND)
    return c


def m4_traces():
    """Circuit traces: eight track buses stand at the right; each lane runs along its own row and lands on its
    track's bus with a pad. Where a trace passes a bus it doesn't join, it hops over it, the way a circuit drawing
    shows wires that cross without connecting."""
    c = Canvas(header_for("m4"), 3)
    lane_names(c)
    targets = [0, 1, 4, 3, 2, 5, 6, 7]
    bus0, bus = 300, 22
    for t in range(8):
        x = bus0 + bus * t
        c.line((x, 52), (x, 182), 1.0, GROUND)
        c.text(x - 3, 192, 10, LABEL, str(t + 1))
    for i, ln in enumerate(LANES):
        if ln.role == "off":
            continue
        y = 58 + 17 * i
        end = bus0 + bus * targets[i]
        col = BRIGHT if i == SEL4 else SECOND
        pts = [(72, y)]
        for t in range(8):
            x = bus0 + bus * t
            if x >= end:
                break
            pts += [(x - 4, y)] + [(x + 4 * math.cos(math.pi - math.pi * k / 6), y - 4 * math.sin(math.pi * k / 6))
                                   for k in range(1, 6)] + [(x + 4, y)]
        pts.append((end, y))
        c.ribbon(pts, 1.6 if i == SEL4 else 1.0, col)
        c.outline(diamond(end, y, 3.5), col, 1.2)
    return c


def m4_arrows():
    """Arrows and register: each lane a long arrow to the track number it plays; on the right the selected lane's
    register window as a bracket on a keyboard ruler, its notes after xpose as a bar inside."""
    c = Canvas(header_for("m4"), 3)
    lane_names(c)
    for i, ln in enumerate(LANES):
        y = 58 + 17 * i
        if ln.role == "off":
            c.line((72, y), (90, y), 1.0, QUIET)
            continue
        col = BRIGHT if i == SEL4 else SECOND
        c.line((72, y), (282, y), 1.4 if i == SEL4 else 1.0, col)
        c.outline(tri(288, y, 4, "right"), col, 1.2)
        c.text(298, y + 4, 10, TEXT_HI if i == SEL4 else SECOND, f"t{i + 1}")
    # register ruler
    rx, ytop, ybot = 400, 56, 186
    c.line((rx, ytop), (rx, ybot), 1.0, GROUND)
    for o in range(11):
        y = ybot - (ybot - ytop) * o * 12 / 127
        c.line((rx - 4, y), (rx + 4, y), 1.0, QUIET)
    lo_y, hi_y = ybot, ytop
    c.ribbon([(rx + 14, hi_y), (rx + 20, hi_y), (rx + 20, lo_y), (rx + 14, lo_y)], 1.2, LABEL)
    n0, n1 = G.FOOTPRINT["chord"]
    y0 = ybot - (ybot - ytop) * n0 / 127
    y1 = ybot - (ybot - ytop) * n1 / 127
    c.line((rx + 8, y0), (rx + 8, y1), 3.0, BRIGHT2)
    c.text(rx + 26, hi_y + 4, 10, LABEL, "G9")
    c.text(rx + 26, lo_y + 4, 10, LABEL, "C-1")
    return c


VIEWS = {
    "m1": [("dial", m1_dial), ("root stair", m1_stair), ("voicing stacks", m1_stacks), ("tide", m1_tide),
           ("arc diagram", m1_arcs)],
    "m2": [("stems", m2_stems), ("bars", m2_bars), ("envelopes", m2_envelopes), ("chevrons", m2_chevrons),
           ("spokes", m2_spokes)],
    "m3": [("contour", m3_contour), ("step plot", m3_steps), ("pitch stems", m3_stems), ("arrows", m3_arrows),
           ("keyboard", m3_keyboard)],
    "m4": [("cables", m4_cables), ("wires", m4_wires), ("crosses", m4_crosses), ("traces", m4_traces),
           ("arrows", m4_arrows)],
}


def sheet(page, items):
    """A 1:1 contact sheet: five frames in a column, each captioned."""
    gap, cap = 10, 16
    h = len(items) * (220 + cap + gap)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="480" height="{h}" viewBox="0 0 480 {h}">',
             f'<rect x="0" y="0" width="480" height="{h}" fill="#181818"/>']
    for i, (label, svg_path) in enumerate(items):
        y = i * (220 + cap + gap)
        parts.append(f'<text x="2" y="{y + 12}" fill="#969696" font-family="sans-serif" font-size="11">{i + 1} · {label}</text>')
        parts.append(f'<image x="0" y="{y + cap}" width="480" height="220" href="{svg_path.name}"/>')
    parts.append("</svg>")
    out = OUT / f"{page}.svg"
    out.write_text("\n".join(parts))
    subprocess.run(["rsvg-convert", str(out), "-o", str(OUT / f"{page}.png")], check=True, cwd=OUT)


def main():
    OUT.mkdir(exist_ok=True)
    for page, fns in VIEWS.items():
        items = []
        for n, (label, fn) in enumerate(fns, 1):
            p = OUT / f"{page}-{n}.svg"
            p.write_text(fn().svg())
            items.append((label, p))
        sheet(page, items)
    print("wrote", ", ".join(f"concepts/{p}.png" for p in VIEWS))


if __name__ == "__main__":
    main()
