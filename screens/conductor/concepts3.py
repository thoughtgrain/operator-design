#!/usr/bin/env python3
"""Round three for M3 (the arp): five takes on the staircase, after Brian's note that the arp still needs work and
the step plot was the way in. Outline only, grey only, playing at step 6.

  11 stair on chord lines · 12 stair section · 13 isometric stairs · 14 floating treads · 15 direction risers

    python3 concepts3.py      → concepts/m3c-<n>.svg, concepts/m3c.png
"""
from __future__ import annotations

import math

import concepts as C

G = C.G
BLACK, FILL, GROUND, QUIET, LABEL, SECOND, BRIGHT2, BRIGHT = (
    C.BLACK, C.FILL, C.GROUND, C.QUIET, C.LABEL, C.SECOND, C.BRIGHT2, C.BRIGHT)
TEXT_HI, tw, STEP_NOW = C.TEXT_HI, C.tw, C.STEP_NOW

ARP = G.Arp()
ALL = ARP.notes()                         # (step, pitch, accent, held, skipped)
NOTES = [n for n in ALL if not n[4]]
PLO, PHI = min(n[1] for n in NOTES), max(n[1] for n in NOTES)
X0, PITCH = 44.0, 26.0
TOP, BOTTOM = 60.0, 180.0


def xs(s):
    return X0 + PITCH * s


def yp(p):
    return BOTTOM - (p - PLO) / max(1, PHI - PLO) * (BOTTOM - TOP)


def colour(s, acc):
    return BRIGHT if s == STEP_NOW else (BRIGHT2 if acc else SECOND)


def corner(c):
    c.text(470 - tw("5 arp", 10), 52, 10, LABEL, "5 arp")


def range_labels(c):
    c.text(4, yp(PHI) + 4, 10, LABEL, G.note_label(PHI))
    c.text(4, yp(PLO) + 4, 10, LABEL, G.note_label(PLO))


def frame():
    c = C.Canvas(C.header_for("m3"), 2)
    corner(c)
    return c


def m3_stair_on_lines():
    """Stair on chord lines: the staircase runs over a hairline for each tone of the sounding chord, so each tread
    shows where the note sits in the chord; treads are the notes, risers are thin, accents are heavier treads."""
    c = frame()
    tones = {G.SCALES[0][k] % 12 for k in (0, 2, 4)}
    for p in range(PLO - 1, PHI + 2):
        if p % 12 in tones:
            root = p % 12 == 0
            c.line((X0, yp(p)), (X0 + PITCH * 16, yp(p)), 0.8, GROUND if root else FILL)
            if root:
                c.text(4, yp(p) + 4, 10, LABEL, G.note_label(p))
    prev = None
    for s, p, acc, *_ in NOTES:
        x0, x1, y = xs(s) + 1, xs(s + 1) - 1, yp(p)
        if prev is not None and prev[0] == s - 1 and prev[1] != y:
            c.line((x0 - 1, prev[1]), (x0 - 1, y), 1.0, QUIET)
        c.line((x0, y), (x1, y), 3.0 if acc else 2.0, colour(s, acc))
        prev = (s, y)
    return c


def m3_section():
    """Stair section: the staircase cut through, like an architect's section: one outline climbing the treads and
    risers and closing along the floor. Accents get a nosing tick at the tread's front edge."""
    c = frame()
    range_labels(c)
    floor = BOTTOM + 10
    profile = []
    last = None
    for s, p, acc, *_ in NOTES:
        if last is not None and s != last + 1:      # a skipped step: the section drops to the floor and climbs back
            profile += [(xs(last + 1), floor), (xs(s), floor)]
        profile += [(xs(s), yp(p)), (xs(s + 1), yp(p))]
        last = s
    first_x, last_x = profile[0][0], profile[-1][0]
    # walk the profile, then back along the floor; long outlines split into pieces of 30 points each way
    c.ribbon(profile, 1.6, SECOND)
    c.line((first_x, profile[0][1]), (first_x, floor), 1.0, QUIET)
    c.line((last_x, profile[-1][1]), (last_x, floor), 1.0, QUIET)
    c.line((first_x, floor), (last_x, floor), 1.0, GROUND)
    for s, p, acc, *_ in NOTES:
        if acc or s == STEP_NOW:
            col = colour(s, acc)
            c.line((xs(s), yp(p) - 5), (xs(s), yp(p) + 3), 1.6, col)
            if s == STEP_NOW:
                c.line((xs(s) + 1, yp(p)), (xs(s + 1) - 1, yp(p)), 2.6, BRIGHT)
    return c


def m3_iso():
    """Isometric stairs: the arp built as a real staircase in 3D and seen from above and to the side; each note a
    tread with depth, each leap a riser, so climbing really climbs. One camera, as craft.md asks."""
    c = frame()
    range_labels(c)
    dx, dy = 9.0, -6.0                    # the tread's depth, receding up and right
    prev = None
    for s, p, acc, *_ in NOTES:
        x0, x1, y = xs(s), xs(s + 1) - 2, yp(p) + 4
        col = colour(s, acc)
        # tread: a parallelogram (front edge, back edge)
        c.outline([(x0, y), (x1, y), (x1 + dx, y + dy), (x0 + dx, y + dy)], col, 1.5 if acc else 1.2)
        # riser from the previous tread, on its front face
        if prev is not None and prev[0] == s - 1 and abs(prev[1] - y) > 1:
            c.line((x0, prev[1]), (x0, y), 1.0, QUIET)
        prev = (s, y)
    return c


def m3_floating():
    """Floating treads: just the treads, no risers, each hung on a fine drop line to the floor so its height reads
    against the ground; a skipped step leaves its drop line standing with no tread on it."""
    c = frame()
    range_labels(c)
    floor = BOTTOM + 10
    c.line((X0, floor), (X0 + PITCH * 16, floor), 1.0, GROUND)
    for s, p, acc, held, skipped in ALL:
        x = xs(s) + PITCH / 2
        if skipped:
            c.line((x, floor), (x, floor - 6), 1.0, QUIET)
            continue
        y = yp(p)
        c.line((x, floor), (x, y + 3), 0.8, FILL)
        c.line((xs(s) + 3, y), (xs(s + 1) - 3, y), 3.0 if acc else 2.0, colour(s, acc))
    return c


def m3_direction():
    """Direction risers: treads for the notes, and each riser drawn as a chevron pointing the way the arp moved,
    up or down, sized by the leap; a repeated note gets a short landing mark instead."""
    c = frame()
    range_labels(c)
    prev = None
    for s, p, acc, *_ in NOTES:
        x0, x1, y = xs(s) + 2, xs(s + 1) - 2, yp(p)
        c.line((x0, y), (x1, y), 2.6 if acc else 1.8, colour(s, acc))
        if prev is not None and prev[0] == s - 1:
            py, pp = prev[1], prev[2]
            mid = (py + y) / 2
            size = min(6, 2.5 + abs(p - pp) * 0.4)
            if p > pp:
                c.outline(C.tri(x0 - 2, mid, size, "up"), QUIET, 1.2)
            elif p < pp:
                c.outline(C.tri(x0 - 2, mid, size, "down"), QUIET, 1.2)
            else:
                c.line((x0 - 4, y - 4), (x0 - 4, y + 4), 1.0, QUIET)
        prev = (s, y, p)
    return c


ROUND3 = [("stair on chord lines", m3_stair_on_lines), ("stair section", m3_section), ("isometric stairs", m3_iso),
          ("floating treads", m3_floating), ("direction risers", m3_direction)]


def main():
    C.OUT.mkdir(exist_ok=True)
    items = []
    for n, (label, fn) in enumerate(ROUND3, 11):
        p = C.OUT / f"m3c-{n}.svg"
        p.write_text(fn().svg())
        items.append((label, p))
    C.sheet("m3c", items, start=11)
    print("wrote concepts/m3c.png")


if __name__ == "__main__":
    main()
