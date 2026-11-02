#!/usr/bin/env python3
"""Conductor, revision 2: the four designs Brian chose from the concept rounds, built the way the device draws them.

  M1 song   arc diagram (concepts m1-5): the twelve pitch classes along a line, the scale's degrees as triangles under
            it, the loop drawn as arches from each chord to the next. A phrase line and the bar's groove underneath.
  M2 lane   arches (concepts m2b-6): one lane at a time, each note an arch on the lane's line, as big as it's loud,
            with a tick where it ends; notes that may vary are broken at the crown, accents carry an inner arch.
  M3 lane   chord-tone lines (concepts m3b-9): a hairline for every tone of the sounding chord across the lane's
            range, root lines named; each note a dash, on a line when it's a chord tone and between them when not.
  M4 route  circuit traces (concepts m4-4): each lane runs along its row to its track's bus, hopping over the buses it
            passes; the selected lane's register window along the bottom.

How the device shapes it (see handoff.md):
  - Every node is one fixed shape moved by translation and a uniform scale. Arches are half-ellipses whose height is
    half their width, so an arch of any span is the same shape scaled; they use stroke-only paint so overlapping
    arches don't hide each other.
  - Per-page furniture is nodes (static art shows on every page). The only static art is the page strip's hairline.
  - The palette is sixteen paints (fill, stroke, width). Grey never fills a body; nothing here fills except the mask,
    the hop gaps (black) and solid lines.

    python3 gen_frames2.py [out]     → <out>/<page>/{rest,playing,c<N>-000,-050,-100}.svg (default: frames2/)
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import gen_frames as G

HERE = Path(__file__).resolve().parent
PREFIX = "cond"
BLACK, FILL, GROUND, QUIET, LABEL, SECOND, BRIGHT2, BRIGHT = (
    G.BLACK, G.FILL, G.GROUND, G.QUIET, G.LABEL, G.SECOND, G.BRIGHT2, G.BRIGHT)
TEXT_HI = G.TEXT_HI
NONE = "none"
f, tw, escape = G.f, G.text_width, G.escape

# ---- paints: (fill, stroke, width). "solid" paints fill and stroke a shape; "line" paints only stroke it. ----------
PAINTS = [
    (BLACK, BLACK, 0.2),      # 0  mask, hop gaps
    (FILL, FILL, 0.2),        # 1  the page strip's hairline
    (GROUND, GROUND, 0.2),    # 2  ground lines: baselines, buses, chord-tone lines, pitch-class ticks
    (QUIET, QUIET, 0.2),      # 3  quiet lines and ticks
    (LABEL, LABEL, 0.2),      # 4  root lines, beat ticks
    (SECOND, SECOND, 0.2),    # 5  traces, dashes, kicks, separators
    (BRIGHT2, BRIGHT2, 0.2),  # 6  accents, lit register, the page mark
    (BRIGHT, BRIGHT, 0.2),    # 7  what's sounding now, the selection, caps
    (NONE, QUIET, 1.5),       # 8  outline, quiet: other degrees, hops
    (NONE, LABEL, 1.5),       # 9  outline, label: evolve's candidates
    (NONE, SECOND, 1.5),      # 10 outline, second: loop degrees, pads
    (NONE, SECOND, 1.6),      # 11 arch, second: a note, a link in the loop
    (NONE, BRIGHT2, 1.6),     # 12 arch, bright: an accent
    (NONE, BRIGHT, 2.2),      # 13 arch, brightest: the link sounding now, the note just hit
    (NONE, QUIET, 1.5),       # 14 arch, quiet: a note that may vary, a link that isn't sounding
    (NONE, BRIGHT, 1.6),      # 15 outline, bright: the selected lane's pad
]


def paint(name: str) -> tuple:
    return {
        "mask": PAINTS[0], "strip": PAINTS[1], "ground": PAINTS[2], "quiet": PAINTS[3], "label": PAINTS[4],
        "second": PAINTS[5], "bright2": PAINTS[6], "bright": PAINTS[7], "o-quiet": PAINTS[8], "o-label": PAINTS[9],
        "o-second": PAINTS[10], "a-second": PAINTS[11], "a-bright2": PAINTS[12], "a-bright": PAINTS[13],
        "a-quiet": PAINTS[14], "o-bright": PAINTS[15]}[name]


# ---- shapes, authored once per pool -----------------------------------------------------------------------------------
RULE_LEN = 430
TREAD_DX, TREAD_DY = 9.0, -6.0    # M3: a tread's depth, receding up and to the right
RISER_LEN = 60.0                  # M3: a riser at scale 1; stroke-only, so scale sets its length
ARC_RX = 102.0                    # an arch is a half-ellipse rx x rx/2; uniform scale gives every span
ARCH_RX, ARCH_RY = 12.0, 40.0     # M2: a note's arch at scale 1
HOP_R = 4.0


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def half_ellipse(rx, ry, n=22, broken=False):
    """An arch standing on y = 0, open side down, as a closed outline whose last edge runs along the ground."""
    pts = [(-rx * math.cos(math.pi * k / n), -ry * math.sin(math.pi * k / n)) for k in range(n + 1)]
    if broken:                    # unsettled: a notch at the crown, one continuous outline
        a, b = pts[: n // 2 - 1], pts[n // 2 + 2:]
        dip = ry * 0.22
        return a + [(0, -ry + dip)] + b
    return pts


def tri_up(s):
    return [(0, -s), (s * 0.9, s * 0.6), (-s * 0.9, s * 0.6)]


def diamond(s):
    return [(0, -s), (s * 0.8, 0), (0, s), (-s * 0.8, 0)]


SHAPES = {
    "rule": rect(-RULE_LEN, -0.6, 0, 0.6),
    "bus": rect(-0.5, 0, 0.5, 128),
    "mask": rect(0, 0, 70, 140),
    "hopgap": rect(-3, -2, 3, 2),
    "hop": half_ellipse(HOP_R, HOP_R, 10),
    "pad": diamond(3.5),
    "octseg": rect(0, -0.8, 32, 0.8),
    "cap": rect(-0.8, -6, 0.8, 6),
    "cell": rect(0, -0.8, 52, 0.8),
    "pctick": rect(-0.5, -3, 0.5, 3),
    "arc": half_ellipse(ARC_RX, ARC_RX / 2, 28),
    "tri": tri_up(4.0),
    "stepS": rect(-0.6, -4, 0.6, 0),
    "stepM": rect(-0.7, -8, 0.7, 0),
    "stepT": rect(-0.8, -13, 0.8, 0),
    "tick": rect(-0.7, -5, 0.7, 5),
    "lanetick": rect(-0.6, -3, 0.6, 3),
    "lanemark": rect(-1, -7, 1, 7),
    "archB": half_ellipse(ARCH_RX, ARCH_RY, 22, broken=True),
    "arch": half_ellipse(ARCH_RX, ARCH_RY, 22),
    "archI": half_ellipse(ARCH_RX - 3.5, ARCH_RY - 7, 18),
    "tread": [(-11.5, 0), (11.5, 0), (11.5 + TREAD_DX, TREAD_DY), (-11.5 + TREAD_DX, TREAD_DY)],
    "riserS": rect(-0.2, 0, 0.2, 12.0),
    "riser": rect(-0.2, 0, 0.2, RISER_LEN),
    "playhead": rect(-0.75, 0, 0.75, 120),
    "bracket": rect(0, -6.5, 2, 6.5),
    "strike": rect(0, -0.75, 46, 0.75),
    "pagemark": rect(0, 0, 116, 2),
}
# (pool, count): index order is draw order
POOLS = [
    ("header", 8), ("bus", 8), ("rule", 12), ("mask", 1), ("hopgap", 20), ("hop", 20), ("pad", 8),
    ("octseg", 11), ("cap", 2), ("cell", 8), ("pctick", 12), ("arc", 4), ("tri", 7), ("stepS", 16),
    ("stepT", 6), ("stepM", 2), ("tick", 8), ("lanetick", 8), ("lanemark", 1), ("archB", 16), ("arch", 16),
    ("archI", 16), ("riserS", 8), ("riser", 8), ("tread", 16), ("playhead", 1), ("bracket", 1), ("strike", 8), ("pagemark", 4),
]
BASE, COUNT = {}, {}
_i = 0
for _n, _c in POOLS:
    BASE[_n], COUNT[_n] = _i, _c
    _i += _c
NODE_COUNT = _i
assert NODE_COUNT <= 256, NODE_COUNT


class Frame:
    def __init__(self):
        self.preview_texts = None        # M4: where the device's spaced strings put each digit, for the preview font
        self.nodes: dict[int, str] = {}
        self.texts: list[str] = []
        self.header_svg = ""
        self.used = {p: 0 for p, _ in POOLS}

    def node(self, pool: str, x: float, y: float, paint_name: str, scale: float = 1.0):
        """Place the next free node of a pool: translation and uniform scale only, paint from the palette."""
        k = self.used[pool]
        if k >= COUNT[pool]:
            raise RuntimeError(f"pool {pool} exhausted ({COUNT[pool]})")
        self.used[pool] += 1
        assert 0 < scale <= 2.0 + 1e-9, (pool, scale)
        idx = BASE[pool] + k
        fill, stroke, w = paint(paint_name)
        pts = [(px * scale, py * scale) for px, py in SHAPES[pool]]
        d = "M " + " L ".join(f"{f(px)} {f(py)}" for px, py in pts) + " Z"
        self.nodes[idx] = (f'<path id="{PREFIX}_node_{idx}" transform="matrix(1 0 0 1 {f(x)} {f(y)})" d="{d}" '
                           f'fill="{fill}" stroke="{stroke}" stroke-width="{f(w)}"/>')

    def text(self, slot, x, y, size, fill, s):
        if s:
            self.texts.append(f'<text id="{PREFIX}_text_{slot}" transform="matrix(1 0 0 1 {f(x)} {f(y)})" '
                              f'fill="{fill}" stroke="none" font-family="{G.FONT}" font-size="{f(size)}px">'
                              f'{escape(s)}</text>')

    def svg(self, page: int) -> str:
        out = ['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
               '<g id="preview_canvas"><rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/></g>',
               self.header_svg]
        for i, (fc, sc, w) in enumerate(PAINTS):
            fc2 = fc if fc != NONE else "#000000"
            out.append(f'<path id="{PREFIX}_palette_{i}" d="M {700 + 8 * i} 300 L {704 + 8 * i} 300 L {704 + 8 * i} 304 Z" '
                       f'fill="{fc2}" stroke="{sc}" stroke-width="{f(w)}"/>')
        for p in range(4):            # the only static art: a hairline under the page names
            x = 120 * p
            out.append(f'<path d="M {x + 2} 204 L {x + 118} 204 L {x + 118} 205 L {x + 2} 205 Z" fill="{FILL}" '
                       f'stroke="{FILL}" stroke-width="0.2"/>')
        out += [self.nodes[i] for i in sorted(self.nodes)]
        texts = self.texts
        if self.preview_texts:
            # the device lays the bus numbers out with spaces in Univers; the preview font's spaces are narrower,
            # so the preview draws each digit where the device puts it (the linter skips preview_ groups)
            texts = [t for t in texts if "      " not in t]
            out.append('<g id="preview_labels">' + "".join(
                f'<text x="{f(x)}" y="{f(y)}" fill="{LABEL}" font-family="{G.FONT}" font-size="10px">{s}</text>'
                for x, y, s in self.preview_texts) + "</g>")
        out += texts
        out.append("</svg>")
        return "\n".join(x for x in out if x) + "\n"


T = 20   # first free text slot (0-15 header, 16-19 page strip)


def pages(fr: Frame, page: int):
    fr.node("pagemark", 120 * page + 2, 203, "bright2")
    for p in range(4):
        fr.text(16 + p, 120 * p + 4, 216, 10, TEXT_HI if p == page else LABEL, G.PAGE_NAMES[p])


# ---- M1: arc diagram ------------------------------------------------------------------------------------------------
LINE_Y, PC_X0, PC_STEP = 146.0, 40.0, 36.4


def pc_x(pc):
    return PC_X0 + PC_STEP * (pc % 12)


def draw_m1(song: G.Song, position=0, playing=False, step=0, frozen=False) -> Frame:
    fr = Frame()
    t, v = song.titles_values()
    G.header(fr, t, v)
    pages(fr, 0)
    key, scale, loop = song.key, song.scale, song.loop
    current, nxt = loop[position], loop[(position + 1) % 4]
    fr.node("rule", 454, LINE_Y, "ground")
    for pc in range(12):
        fr.node("pctick", pc_x(pc), LINE_Y, "ground")

    # the loop: an arch from each chord to the next; the one sounding now is brightest
    for i, d in enumerate(loop):
        a, b = pc_x(key + scale[d]), pc_x(key + scale[loop[(i + 1) % 4]])
        if abs(a - b) < 1:
            continue
        r = abs(a - b) / 2
        fr.node("arc", (a + b) / 2, LINE_Y - 1, "a-bright" if i == position else "a-quiet", r / ARC_RX)
        fr.text(T + 6 + i, (a + b) / 2 - 3, LINE_Y - 1 - r / 2 - 4, 10, LABEL, str(i + 1))

    # the scale's degrees: triangles under the line; the loop's bigger, evolve's candidates swell
    ev = 0 if frozen else song.evolve
    cands = song.candidates()
    label_k = 0
    for d in range(7):
        x = pc_x(key + scale[d])
        if d == current:
            fr.node("tri", x, LINE_Y + 8, "o-bright", 1.5)
        elif d in loop:
            fr.node("tri", x, LINE_Y + 8, "o-second", 1.3)
        elif d in cands and ev:
            fr.node("tri", x, LINE_Y + 8, "o-label", 1.0 + 0.8 * ev / 100)
        else:
            fr.node("tri", x, LINE_Y + 8, "o-quiet", 0.9)
        if d in loop:
            nm = G.chord_name(key, scale, d, song.seventh)
            fr.text(T + 2 + label_k, x - tw(nm, 10) / 2, LINE_Y + 26, 10, TEXT_HI if d == current else G.SECOND, nm)
            label_k += 1

    # the phrase: four bars as half-bar segments, the sounding chord's span lit, separators where chords change
    rate = G.HRATE_STEPS[song.hrate]
    chord_of = [(h * 8) // rate for h in range(8)]
    now_cell = ((position * 16 + step) // 8) % 8 if playing else 0
    for h in range(8):
        fr.node("cell", 24 + 54 * h, 180, "second" if chord_of[h] == chord_of[now_cell] else "ground")
    for h in range(1, 8):
        if chord_of[h] != chord_of[h - 1]:
            fr.node("tick", 24 + 54 * h - 1, 180, "second")
    if playing:
        fr.node("tick", 24 + (position * 16 + step) * 432 / 64, 180, "bright")

    # the bar's groove: kicks tall, backbeats middling, the rest short; swing pushes offbeats late
    kicks = song.kicks()
    fr.node("rule", 456, 198, "ground")
    for s in range(16):
        lag = song.swing / 100 * (10 / 24) if s % 2 else 0.0
        x = 24 + 27 * s + 13.5 + lag * 27
        live = playing and s == step
        if kicks[s]:
            fr.node("stepT", x, 198, "bright" if live else "second")
        elif s in (4, 12):
            fr.node("stepM", x, 198, "bright" if live else "label")
        else:
            fr.node("stepS", x, 198, "bright" if live else ("label" if s % 4 == 0 else "quiet"))

    fr.text(T, 10, 62, 20, TEXT_HI, G.chord_name(key, scale, current, song.seventh))
    fr.text(T + 1, 10, 76, 10, LABEL, "next " + G.chord_name(key, scale, nxt, song.seventh))
    if frozen:
        fr.text(T + 10, 470 - tw("frozen", 10), 52, 10, LABEL, "frozen")
    return fr


# ---- M2: arches -----------------------------------------------------------------------------------------------------
M2_X0, M2_PITCH = 40.0, 26.25


def draw_m2(lanes, sel=4, playing=False, step=0) -> Frame:
    fr = Frame()
    L = lanes[sel]
    G.header(fr, ["lane", "role", "dens", "oct", "vel", "vary", "lock", "gate"],
             [str(sel + 1), L.role, str(L.dens), str(L.oct), str(L.vel), str(L.vary),
              ["kick", "acnt", "free"][L.lock], str(L.gate)])
    pages(fr, 1)
    for i in range(8):                               # the lane index: eight ticks, the shown lane's tall and bright
        fr.node("lanetick", 300 + 22 * i, 54, "quiet" if lanes[i].role == "off" else "label")
    fr.node("lanemark", 300 + 22 * sel, 54, "bright")
    fr.text(T, 10, 62, 20, TEXT_HI, f"{sel + 1} {L.role}")
    if L.mute:
        fr.node("strike", 8, 55, "second", min(2.0, (tw(f"{sel + 1} {L.role}", 20) + 4) / 46))

    base = 184 - (L.oct + 2) * 9                     # oct lifts the lane's line 9 px an octave
    fr.node("rule", 456, base, "quiet")
    hits = G.lane_hits(L, sel)
    rnd = random.Random(100 + sel)
    cand = sorted(hits)
    rnd.shuffle(cand)
    vary = set(cand[: round(len(cand) * L.vary / 100)])
    for s, acc in sorted(hits.items()):
        x = M2_X0 + M2_PITCH * s + M2_PITCH / 2
        live = playing and s == step
        sc = 0.45 + 0.95 * L.vel / 100 * (1.08 if acc else 1.0)   # as big as it's loud
        pname = "a-bright" if live else ("a-quiet" if s in vary else ("a-bright2" if acc else "a-second"))
        fr.node("archB" if s in vary else "arch", x, base - 0.5, pname, min(sc, 1.9))
        if acc:
            fr.node("archI", x, base - 0.5, pname, min(sc, 1.9))
        if L.role != "drum":                         # gate: a tick on the line where the note lets go
            gx = x - ARCH_RX * sc + max(3.0, M2_PITCH * 1.8 * L.gate / 100)
            fr.node("stepS", gx, base + 5, "label")
    if L.role == "bass":                             # lock steers a bass: its anchor steps marked under the line
        locks = {0: set(G.SONG_KICKS), 1: set(G.SONG_KICKS) | {0, 4, 8, 12}, 2: set()}[L.lock]
        for i, s in enumerate(sorted(locks)):
            pool = "stepT" if i < 6 else "stepM"
            fr.node(pool, M2_X0 + M2_PITCH * s + M2_PITCH / 2, base + 16, "second")
    if playing:
        fr.node("playhead", M2_X0 + M2_PITCH * step + M2_PITCH / 2, 76, "quiet")
    return fr


# ---- M3: chord-tone lines -------------------------------------------------------------------------------------------
M3_X0, M3_PITCH = 44.0, 26.0


def draw_m3(arp: G.Arp | None = None, drum=False, playing=False, step=0, degree=0, lane_no=5) -> Frame:
    fr = Frame()
    pages(fr, 2)
    role = "drum" if drum else "arp"
    fr.text(T + 12, 470 - tw(f"{lane_no} {role}", 10), 52, 10, LABEL, f"{lane_no} {role}")
    if drum:
        G.header(fr, ["kick", "snare", "hats", "perc", "fills", "ghost", "human", "map"],
                 ["60", "60", "55", "30", "50", "25", "20", "xy"])
        hits = {0: [0, 8, 10], 1: [4, 12], 4: list(range(0, 16, 2)), 5: [14], 3: [7], 2: [12]}
        for r, name in enumerate(G.DRUM_VOICES):
            y = 64 + 17 * r
            fr.text(T + r, 4, y + 1, 10, LABEL, name)
            for s in hits.get(r, []):
                live = playing and s == step
                fr.node("tread", M3_X0 + M3_PITCH * s + M3_PITCH / 2 - 4, y,
                        "a-bright" if live else ("a-bright2" if r < 2 else "a-second"))
    else:
        # isometric stairs: each note a tread with depth at its pitch; each leap a riser on the treads' front edge
        arp = arp or G.Arp()
        G.header(fr, ["mode", "rate", "range", "steps", "skip", "accent", "tones", "jump"], arp.values())
        notes = [n for n in arp.notes(degree=degree) if not n[4]]
        pitches = [n[1] for n in notes]
        lo, hi = (min(pitches), max(pitches)) if pitches else (60, 72)
        span = max(hi - lo, 12)
        def yp(p):
            return 184 - (p - lo) / span * 120
        fr.text(T, 4, yp(hi) + 1, 10, LABEL, G.note_label(hi))
        fr.text(T + 1, 4, yp(lo) + 1, 10, LABEL, G.note_label(lo))
        prev = None
        for s, p, acc, *_ in notes:
            x = M3_X0 + M3_PITCH * s + M3_PITCH / 2 - 4
            y = yp(p)
            if prev is not None and prev[0] == s - 1 and abs(prev[1] - y) > 1:
                top, leap = min(prev[1], y), abs(prev[1] - y)
                short = leap < 24 and fr.used["riserS"] < COUNT["riserS"] or fr.used["riser"] >= COUNT["riser"]
                if short:                    # two riser lengths keep every scale inside (0.4, 2]
                    fr.node("riserS", x - 11.5 - 1.25, top, "o-quiet", max(0.4, min(2.0, leap / 12.0)))
                else:
                    fr.node("riser", x - 11.5 - 1.25, top, "o-quiet", max(0.4, min(2.0, leap / RISER_LEN)))
            live = playing and s == step
            fr.node("tread", x, y, "a-bright" if live else ("a-bright2" if acc else "a-second"))
            prev = (s, y)
    if playing:
        fr.node("playhead", M3_X0 + M3_PITCH * step + M3_PITCH / 2, 60, "quiet")
    return fr


# ---- M4: circuit traces ---------------------------------------------------------------------------------------------
BUS_X0, BUS_STEP, ROW_Y0, ROW_STEP = 300.0, 22.4, 60.0, 16.0


def bus_x(t):
    return BUS_X0 + BUS_STEP * t


def draw_m4(lanes, sel=2, end_override=None) -> Frame:
    fr = Frame()
    L = lanes[sel]
    tgt = L.target if L.target is not None else sel
    G.header(fr, ["lane", "to", "xpose", "mute", "low", "high", "", ""],
             [str(sel + 1), f"t{tgt + 1}", str(L.xpose), "on" if L.mute else "off", G.note_label(L.low),
              G.note_label(L.high), "", ""])
    pages(fr, 3)
    for t in range(8):
        fr.node("bus", bus_x(t), 52, "ground")
    # bus numbers: two text slots, each four digits six spaces apart (a digit and six spaces is 22.4 px in the font)
    fr.text(T + 8, bus_x(0) - 2.8, 48, 10, LABEL, "1      2      3      4")
    fr.text(T + 9, bus_x(4) - 2.8, 48, 10, LABEL, "5      6      7      8")
    fr.preview_texts = [(bus_x(t) - 2.8, 48, str(t + 1)) for t in range(8)]
    hops = []
    for i, ln in enumerate(lanes):
        y = ROW_Y0 + ROW_STEP * i
        t = ln.target if ln.target is not None else i
        live = ln.role != "off" and not ln.mute
        end = bus_x(t) if live else 70
        if end_override and i in end_override:
            end = end_override[i]
        fr.node("rule", end, y, "bright" if i == sel and live else ("second" if live else "quiet"))
        if end > 72:
            fr.node("pad", end, y, "o-bright" if i == sel else "o-second")
            hops += [(bus_x(k), y, i == sel) for k in range(8) if bus_x(k) < end - 1]
        label = f"{i + 1} {ln.role}"
        fr.text(T + i, 10, y + 4, 10, TEXT_HI if i == sel else G.SECOND, label)
        if ln.mute and ln.role != "off":
            fr.node("strike", 8, y + 0.5, "second", min(2.0, (tw(label, 10) + 4) / 46))
    fr.node("mask", 0, 50, "mask")
    for x, y, selected in hops[: COUNT["hop"]]:      # a trace crossing a bus it doesn't join hops over it
        fr.node("hopgap", x, y, "mask")
        fr.node("hop", x, y + 0.6, "o-bright" if selected else "o-quiet")
    fr.node("bracket", 2, ROW_Y0 + ROW_STEP * sel, "bright")

    # the register: eleven octaves along the bottom; the window lit quietly, the lane's notes (after xpose) bright
    ry = 192
    natural = G.FOOTPRINT[L.role]
    lo_n, hi_n = natural[0] + L.xpose, natural[1] + L.xpose
    for o in range(11):
        n0, n1 = 12 * o, 12 * o + 11
        inside = n1 >= L.low and n0 <= L.high
        plays = inside and not L.mute and L.role != "off" and n1 >= max(lo_n, L.low) and n0 <= min(hi_n, L.high)
        fr.node("octseg", 80 + 34.4 * o, ry, "bright2" if plays else ("quiet" if inside else "ground"))
    for n in (L.low, L.high):
        fr.node("cap", 80 + 34.4 * 11 * n / 132, ry, "bright")
    return fr


# ---- frame sets -----------------------------------------------------------------------------------------------------
def write(fr: Frame, page: int, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(fr.svg(page))


def build(out: Path):
    d = out / "m1"
    write(draw_m1(G.Song()), 0, d / "rest.svg")
    write(draw_m1(G.Song(), position=1, playing=True, step=6), 0, d / "playing.svg")
    for n, k in enumerate(G.M1_KEYS, 1):
        for v in (0.0, 0.5, 1.0):
            write(draw_m1(G.Song(**{k: v})), 0, d / f"c{n}-{round(v * 100):03d}.svg")

    d = out / "m2"
    write(draw_m2(G.default_lanes()), 1, d / "rest.svg")
    write(draw_m2(G.default_lanes(), playing=True, step=6), 1, d / "playing.svg")
    m2 = [("lane", [0, 3, 7]), ("role", ["off", "chord", "lead"]), ("dens", [0, 50, 100]), ("oct", [-2, 0, 2]),
          ("vel", [0, 50, 100]), ("vary", [0, 50, 100]), ("lock", [0, 1, 2]), ("gate", [5, 52, 100])]
    for n, (k, vals) in enumerate(m2, 1):
        for tag, v in zip(("000", "050", "100"), vals):
            lanes = G.default_lanes()
            s = 1 if k == "lock" else 4
            if k == "lane":
                s = v
            else:
                setattr(lanes[s], k, v)
            write(draw_m2(lanes, s), 1, d / f"c{n}-{tag}.svg")

    d = out / "m3"
    write(draw_m3(G.Arp()), 2, d / "rest.svg")
    write(draw_m3(G.Arp(), playing=True, step=6), 2, d / "playing.svg")
    sets = [("mode", [0, 3, 5]), ("rate", [0, 1, 2]), ("range", [0, 1, 2]), ("steps", [3, 5, 8]),
            ("skip", [0, 50, 100]), ("accent", [0, 50, 100]), ("tones", [0, 1, 1]), ("jump", [0, 50, 100])]
    for n, (k, vals) in enumerate(sets, 1):
        for tag, v in zip(("000", "050", "100"), vals):
            a = G.Arp()
            setattr(a, k, v)
            write(draw_m3(a), 2, d / f"c{n}-{tag}.svg")
    write(draw_m3(drum=True, lane_no=1), 2, out / "m3-drum" / "rest.svg")
    write(draw_m3(drum=True, playing=True, step=6, lane_no=1), 2, out / "m3-drum" / "playing.svg")

    d = out / "m4"
    write(draw_m4(G.default_lanes()), 3, d / "rest.svg")
    m4 = [("lane", [0, 3, 7]), ("target", [0, 4, 7]), ("xpose", [-24, 0, 24]), ("mute", [False, False, True]),
          ("low", [0, 64, 127]), ("high", [0, 64, 127])]
    for n, (k, vals) in enumerate(m4, 1):
        for tag, v in zip(("000", "050", "100"), vals):
            lanes = G.default_lanes()
            s = 2
            if k == "lane":
                s = v
            else:
                setattr(lanes[s], k, v)
                if k == "high":
                    lanes[s].low = 0
            write(draw_m4(lanes, s), 3, d / f"c{n}-{tag}.svg")
    print(f"nodes declared: {NODE_COUNT}")


if __name__ == "__main__":
    build(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "frames2")
