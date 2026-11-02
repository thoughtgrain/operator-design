#!/usr/bin/env python3
"""Round two for M2 (one lane) and M3 (the arp): five more shape languages each.

Brian picked M1 5 (arc diagram) and M4 4 (circuit traces) from round one, so these lean the same way: lines, arcs
and hops, outline only, grey only, playing at step 6 of bar 2.

  M2  6 arches · 7 gate signal · 8 notches · 9 plumb lines · 10 slashes
  M3  6 interval arcs · 7 brushstroke · 8 interval bars · 9 chord-tone lines · 10 falling roll

    python3 concepts2.py      → concepts/m2b-<n>.svg, concepts/m3b-<n>.svg, concepts/m2b.png, concepts/m3b.png
"""
from __future__ import annotations

import math

import concepts as C

G = C.G
BLACK, FILL, GROUND, QUIET, LABEL, SECOND, BRIGHT2, BRIGHT = (
    C.BLACK, C.FILL, C.GROUND, C.QUIET, C.LABEL, C.SECOND, C.BRIGHT2, C.BRIGHT)
TEXT_HI, tw, STEP_NOW = C.TEXT_HI, C.tw, C.STEP_NOW
LANE, HITS = C.LANE, C.HITS
X0, X1 = 40, 460
PITCH = (X1 - X0) / 16


def vary_steps():
    rnd = G.random.Random(104)
    cand = sorted(HITS)
    rnd.shuffle(cand)
    return set(cand[: round(len(cand) * LANE.vary / 100)])


def col_for(s, acc, varies=False):
    if s == STEP_NOW:
        return BRIGHT
    if varies:
        return QUIET
    return BRIGHT2 if acc else SECOND


def gate_px():
    return max(4.0, PITCH * 1.8 * LANE.gate / 100)


def m2_frame():
    c = C.Canvas(C.header_for("m2"), 1)
    C.lane_strip(c)
    return c


# ---- M2, round two --------------------------------------------------------------------------------------------------
def m2_arches():
    """Arches: each note an arch standing on the line, as wide as it holds and as tall as it's loud. Notes that may
    vary are broken at the crown; accents carry a second, inner arch. The octave lifts the line."""
    c = m2_frame()
    base = 180 - (LANE.oct + 2) * 8
    c.line((X0, base), (X1, base), 1.0, GROUND)
    vs = vary_steps()
    for s, acc in HITS.items():
        xa = X0 + PITCH * s + 2
        w = gate_px()
        h = 18 + LANE.vel / 100 * 56
        col = col_for(s, acc, s in vs)
        pts = C.arc(xa + w / 2, base, w / 2, math.pi, 2 * math.pi, 18, ry=h)
        if s in vs:
            c.ribbon(pts[:8], 1.4, col)
            c.ribbon(pts[11:], 1.4, col)
        else:
            c.ribbon(pts, 1.6, col)
        if acc:
            c.ribbon(C.arc(xa + w / 2, base, w / 2 - 3, math.pi, 2 * math.pi, 14, ry=h - 6), 1.0, col)
    return c


def m2_gate():
    """Gate signal: the lane as one trace, the way a scope would draw its gate: up for as long as each note holds,
    as high as it's loud, back down between. Accents spike above the plateau."""
    c = m2_frame()
    base = 176 - (LANE.oct + 2) * 8
    pts = [(X0, base)]
    for s in sorted(HITS):
        acc = HITS[s]
        xa = X0 + PITCH * s + 1
        xb = min(xa + gate_px(), X0 + PITCH * (s + 1) + PITCH * 0.8)
        h = 16 + LANE.vel / 100 * 50
        pts += [(xa, base), (xa + 1.2, base - h)]
        if acc:
            pts += [(xa + 3, base - h - 8), (xa + 5, base - h)]
        pts += [(xb - 1.2, base - h), (xb, base)]
    pts.append((X1, base))
    c.ribbon(pts, 1.4, SECOND)
    x = X0 + PITCH * STEP_NOW + 1
    c.line((x, base + 6), (x, base + 14), 2.0, BRIGHT)
    for s in range(16):
        xs = X0 + PITCH * s
        c.line((xs, base + 6), (xs, base + (12 if s % 4 == 0 else 9)), 1.0, GROUND)
    return c


def m2_notches():
    """Notches: the bar as a ruler's edge with a V cut where each note falls, as deep as it's loud and as wide as it
    holds. Accents are cut twice. Turning oct raises or lowers the whole edge."""
    c = m2_frame()
    edge = 120 - LANE.oct * 14
    pts = [(X0, edge)]
    for s in sorted(HITS):
        acc = HITS[s]
        xc = X0 + PITCH * s + PITCH / 2
        half = max(3, gate_px() / 3)
        depth = 10 + LANE.vel / 100 * 34
        pts += [(xc - half, edge), (xc, edge + depth), (xc + half, edge)]
    pts.append((X1, edge))
    c.ribbon(pts, 1.4, SECOND)
    for s, acc in HITS.items():
        xc = X0 + PITCH * s + PITCH / 2
        depth = 10 + LANE.vel / 100 * 34
        if acc:
            c.line((xc, edge + depth + 4), (xc, edge + depth + 10), 1.6, BRIGHT2)
        if s == STEP_NOW:
            c.outline(C.tri(xc, edge - 8, 3.5, "down"), BRIGHT, 1.4)
    for o in range(-2, 3):
        y = 120 - o * 14
        c.line((24, y), (30, y), 1.0, BRIGHT2 if o == LANE.oct else QUIET)
    return c


def m2_plumbs():
    """Plumb lines: each note hangs from a rail on a line as long as it's loud, a small weight at the end; the weight
    swings right for as long as the note holds. Notes that may vary hang on a dotted line."""
    c = m2_frame()
    rail = 84 + (2 - (LANE.oct + 2)) * 6
    c.line((X0, rail), (X1, rail), 1.2, GROUND)
    vs = vary_steps()
    for s, acc in HITS.items():
        x = X0 + PITCH * s + PITCH / 2
        L = 22 + LANE.vel / 100 * 60
        col = col_for(s, acc, s in vs)
        swing = LANE.gate / 100 * 10
        end = (x + swing, rail + L)
        if s in vs:
            for k in range(4):
                a, b = k / 4, (k + 0.55) / 4
                c.line((x + swing * a, rail + L * a), (x + swing * b, rail + L * b), 1.2, col)
        else:
            c.line((x, rail), end, 1.4, col)
        c.outline(C.tri(end[0], end[1] + 4, 5 if acc else 3.6, "down"), col, 1.2)
    return c


def m2_slashes():
    """Slashes: each note a stroke leaning forward, steeper the louder it is and longer the longer it holds, like
    handwritten tally marks. Accents are doubled; notes that may vary are short."""
    c = m2_frame()
    base = 160 - (LANE.oct + 2) * 10
    c.line((X0, base + 18), (X1, base + 18), 0.8, FILL)
    vs = vary_steps()
    for s, acc in HITS.items():
        x = X0 + PITCH * s + 4
        L = (16 + LANE.gate / 100 * 30) * (0.5 if s in vs else 1)
        ang = math.radians(25 + LANE.vel / 100 * 50)
        col = col_for(s, acc, s in vs)
        p0 = (x, base + 14)
        p1 = (x + L * math.cos(ang), base + 14 - L * math.sin(ang))
        c.line(p0, p1, 1.8, col)
        if acc:
            c.line((p0[0] + 5, p0[1]), (p1[0] + 5, p1[1]), 1.8, col)
    return c


# ---- M3, round two --------------------------------------------------------------------------------------------------
NOTES = C.NOTES
PLO, PHI = C.PLO, C.PHI
x3 = C.x3


def yp(p, top=60, bottom=180):
    return bottom - (p - PLO) / max(1, PHI - PLO) * (bottom - top)


def m3_interval_arcs():
    """Interval arcs: the notes sit as short dashes on a time line; each step to the next note is an arc above the
    line when the arp climbs and below it when it falls, as tall as the leap. It's the same arc language as M1."""
    c = C.Canvas(C.header_for("m3"), 2)
    y = 128
    c.line((40, y), (460, y), 1.0, GROUND)
    prev = None
    for s, p, acc, *_ in NOTES:
        x = x3(s)
        col = BRIGHT if s == STEP_NOW else (BRIGHT2 if acc else SECOND)
        c.line((x - 4, y), (x + 4, y), 2.4, col)
        if prev is not None:
            ps, pp = prev
            dx = x - x3(ps)
            leap = p - pp
            if leap:
                h = min(64, 6 + abs(leap) * 3.2)
                a0, a1 = (math.pi, 2 * math.pi) if leap > 0 else (math.pi, 0)
                pts = C.arc(x3(ps) + dx / 2, y + (-2 if leap > 0 else 2), dx / 2, a0, a1, 14, ry=h)
                c.ribbon(pts, 1.2, col if s == STEP_NOW else QUIET if abs(leap) < 4 else LABEL)
        prev = (s, p)
    c.text(4, 72, 10, LABEL, "up")
    c.text(4, 190, 10, LABEL, "down")
    return c


def m3_brush():
    """Brushstroke: the arp as one stroke through its notes that swells where it's accented and thins between,
    like a pen pressed harder on the loud notes."""
    c = C.Canvas(C.header_for("m3"), 2)
    C.range_labels(c)
    pts = [(x3(s), yp(p)) for s, p, *_ in NOTES]
    widths = [4.5 if acc else 1.6 for _, _, acc, *_ in NOTES]
    # a variable-width ribbon: offset each point by its own half width
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        n = C._normal(a, b)
        w = widths[i] / 2
        left.append((x + n[0] * w, y + n[1] * w))
        right.append((x - n[0] * w, y - n[1] * w))
    c.poly(left + right[::-1], SECOND, SECOND, 0.4)
    s_now = [s for s, *_ in NOTES].index(STEP_NOW) if STEP_NOW in [s for s, *_ in NOTES] else None
    if s_now is not None:
        x, y = pts[s_now]
        c.outline(C.tri(x, y - 10, 3.5, "down"), BRIGHT, 1.4)
    return c


def m3_interval_bars():
    """Interval bars: each step drawn as the leap itself, a vertical bar from the last note to this one with a tick
    where it lands. Climbs and falls read as bars going up and down; repeated notes are just ticks."""
    c = C.Canvas(C.header_for("m3"), 2)
    C.range_labels(c)
    prev = None
    for s, p, acc, *_ in NOTES:
        x, y = x3(s), yp(p)
        col = BRIGHT if s == STEP_NOW else (BRIGHT2 if acc else SECOND)
        if prev is not None and prev != p:
            c.line((x, yp(prev)), (x, y), 1.2, QUIET)
        c.line((x - 5, y), (x + 5, y), 2.2, col)
        prev = p
    return c


def m3_chord_lines():
    """Chord-tone lines: a hairline for every chord tone across the range, like a tab staff, root lines heavier and
    named; each note a short dash on its line. Tones that aren't in the chord sit between the lines."""
    c = C.Canvas(C.header_for("m3"), 2)
    tones = sorted({(G.SCALES[0][k]) % 12 for k in (0, 2, 4)})
    for p in range(PLO - 2, PHI + 3):
        if p % 12 in tones:
            root = p % 12 == 0
            c.line((44, yp(p)), (460, yp(p)), 1.0 if root else 0.6, GROUND if root else FILL)
            if root:
                c.text(4, yp(p) + 4, 10, LABEL, G.note_label(p))
    for s, p, acc, *_ in NOTES:
        x, y = x3(s), yp(p)
        col = BRIGHT if s == STEP_NOW else (BRIGHT2 if acc else SECOND)
        c.line((x - 8, y), (x + 8, y), 3.0 if acc else 2.0, col)
    return c


def m3_roll_down():
    """Falling roll: turned on its side. Pitch runs across, low to high, and time falls down the page; each note is a
    short dash and a thread joins them, so the arp reads as a path dropping through the bar."""
    c = C.Canvas(C.header_for("m3"), 2)
    def xp(p):
        return 60 + (p - PLO) / max(1, PHI - PLO) * 380
    def yt(s):
        return 48 + s * 9.2
    c.text(60 - tw(G.note_label(PLO), 10) / 2, 196, 10, LABEL, G.note_label(PLO))
    c.text(440 - tw(G.note_label(PHI), 10) / 2, 196, 10, LABEL, G.note_label(PHI))
    pts = [(xp(p), yt(s)) for s, p, *_ in NOTES]
    c.ribbon(pts, 1.0, QUIET)
    for s, p, acc, *_ in NOTES:
        col = BRIGHT if s == STEP_NOW else (BRIGHT2 if acc else SECOND)
        c.line((xp(p) - 7, yt(s)), (xp(p) + 7, yt(s)), 2.4 if acc else 1.8, col)
    for s in range(0, 16, 4):
        c.line((30, yt(s)), (38, yt(s)), 1.0, GROUND)
        c.text(14, yt(s) + 4, 10, LABEL, str(s // 4 + 1))
    return c


ROUND2 = {
    "m2b": [("arches", m2_arches), ("gate signal", m2_gate), ("notches", m2_notches), ("plumb lines", m2_plumbs),
            ("slashes", m2_slashes)],
    "m3b": [("interval arcs", m3_interval_arcs), ("brushstroke", m3_brush), ("interval bars", m3_interval_bars),
            ("chord-tone lines", m3_chord_lines), ("falling roll", m3_roll_down)],
}


def main():
    C.OUT.mkdir(exist_ok=True)
    for page, fns in ROUND2.items():
        items = []
        for n, (label, fn) in enumerate(fns, 6):
            p = C.OUT / f"{page}-{n}.svg"
            p.write_text(fn().svg())
            items.append((label, p))
        C.sheet(page, items, start=6)
    print("wrote concepts/m2b.png, concepts/m3b.png")


if __name__ == "__main__":
    main()
