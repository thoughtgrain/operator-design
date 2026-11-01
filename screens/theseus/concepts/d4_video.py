#!/usr/bin/env python3
"""d4 drum tower, animated: a two-bar groove at 120 bpm with the controls swept while it plays.

Revision 3: line drawing. Every shape is black with a grey outline, so the drums read as their outlines and don't
run together; only the drum being played fills with light. Revision 2 (after Brian's notes): each tier looks like the drum it plays, and only the drum that's hit moves, and
only upward. No ride-along, no wobble, no lean; the hit LFO now sets how high each hit jumps.

The board's d4 only showed single moments. In motion each hit is a small physical event:
  - the struck tier springs up and rings, and every tier above it rides along (hit the kick and the whole tower jumps)
  - the tower wobbles sideways after a hit, more with punch, and leans with the hit LFO, easing to each new step
  - the hi-hat on top tips and rocks; fm throws shimmer arcs off it
  - rings spread across the struck head (decay sets how many and how long), noise throws sizzle specks

    python3 d4_video.py <tmpdir>   then ffmpeg (see the end of main)
"""
from __future__ import annotations

import math
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from blocks import DEFAULTS, G, env, f, frame, lfo_at, path, poly, zone_of  # noqa: E402
from drums import cymbal, ellipse, head, shell, sizzle  # noqa: E402

FPS = 30
# the tower, bottom to top: each tier is drawn as the drum it plays
#   zone, radius, shell height, kind
TIERS = [(0.02, 86, 30, "kick"), (0.25, 62, 22, "floor"), (0.45, 50, 10, "snare"), (0.65, 38, 15, "tom"), (0.88, 36, 0, "hat")]
GAP = 9                                                          # room above each tier for it to rise into


def tier_of(z):
    return min(range(len(TIERS)), key=lambda k: abs(TIERS[k][0] - z))


def rise(dt, amp):
    """a hit only ever lifts: up fast, settle slowly, never below rest"""
    if dt < 0:
        return 0.0
    return amp * (1 - math.exp(-dt / 0.018)) * math.exp(-dt / 0.14)


class Phrase:
    """hits as (time, note); `now` is the moment drawn"""

    def __init__(self, seq, now):
        self.seq, self.now = seq, now

    def played(self):
        return [(i, t, n) for i, (t, n) in enumerate(self.seq) if t <= self.now]

    def last(self):
        p = self.played()
        return p[-1] if p else None

    def count(self):
        return len(self.played())


# ---- line drawing: black-filled shapes with grey strokes, so each drum reads as its outline and only the drum
# being played fills with light (revision 3: the solid fills made the drums run together)
LINE, DIM, HOT = G[5], G[3], G[7]


def shape(pts, stroke=LINE, w=1.2, fill="#000000", close=True):
    d = poly(pts) if close else "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts)
    return f'<path d="{d}" fill="{fill if close else "none"}" stroke="{stroke}" stroke-width="{w}" stroke-linejoin="round" stroke-linecap="round"/>'


def lit_fill(e, v):
    return "#000000" if e < 0.04 else G[max(1, min(5, round(1 + 4 * e * (0.5 + 0.5 * v["cutoff"]))))]


def body(x, top, r, ry, h, e, stroke=LINE):
    """the shell: its silhouette in black with a grey outline, the front of the lower hoop as a line"""
    front = ellipse(x, top + h, r, ry, 24, math.pi, 0)
    o = [shape([(x - r, top)] + front + [(x + r, top)], stroke if e < 0.04 else HOT, 1.2)]
    o.append(shape(ellipse(x, top + h - 2, r, ry, 24, math.pi, 0), DIM, 1.0, close=False))
    return o


def lugs(x, top, r, ry, h, n, stroke=DIM, inset=0.22):
    o = []
    for k in range(n):
        t = math.pi * (0.15 + 0.7 * k / max(1, n - 1))
        lx, ly = x + r * math.cos(t) * 0.98, top + h * 0.5 + ry * math.sin(t)
        o.append(shape([(lx, ly - h * inset), (lx, ly + h * inset)], stroke, 1.4, close=False))
    return o


def batter(x, top, r, ry, e, v):
    """the head: its hoop as a line, the skin lit by a hit, rings spreading across it with decay"""
    o = [shape(ellipse(x, top, r, ry, 32), HOT if e >= 0.04 else G[6], 1.5, fill=lit_fill(e, v))]
    if e > 0.03:
        for k in range(1 + round(3 * v["decay"])):
            u = ((1 - e) * 0.9 + k * 0.22) % 1
            o.append(shape(ellipse(x, top + 0.4, r * 0.84 * u + 1.5, ry * 0.84 * u + 0.8, 24), HOT if k == 0 else G[6], 1.0, fill="none"))
    return o


def kick(x, top, r, ry, h, e, v):
    o = body(x, top, r, ry, h, e)
    for yy in (0.38, 0.6):                                          # the wrap stripe: two lines round the shell
        o.append(shape(ellipse(x, top + h * yy, r, ry, 24, math.pi, 0), DIM, 1.0, close=False))
    o += lugs(x, top, r, ry, h, 8, inset=0.12)
    o += batter(x, top, r, ry, e, v)
    o.append(shape(ellipse(x + r * 0.3, top + ry * 0.12, r * 0.15, ry * 0.15, 16), DIM, 1.0, fill="none"))   # beater patch
    return o


def floor_tom(x, top, r, ry, h, e, v):
    o = []
    for sx in (-1, 1):
        o.append(shape([(x + sx * (r - 3), top + h * 0.35), (x + sx * (r + 8), top + h + 6)], DIM, 1.4, close=False))
    o += body(x, top, r, ry, h, e)
    o += lugs(x, top, r, ry, h, 4)
    o += batter(x, top, r, ry, e, v)
    return o


def snare(x, top, r, ry, h, e, v):
    o = []
    for k in range(4):                                              # the wires under the bottom hoop
        yy = top + h + ry * 0.55 + 1.6 * k
        o.append(shape([(x - r * 0.6, yy), (x + r * 0.6, yy)], DIM, 0.8, close=False))
    o += body(x, top, r, ry, h, e, stroke=G[6])
    o += lugs(x, top, r, ry, h, 8, stroke=G[6], inset=0.3)
    o += batter(x, top, r, ry, e, v)
    return o


def rack_tom(x, top, r, ry, h, e, v):
    o = body(x, top, r, ry, h, e)
    o.append(shape([(x - r - 7, top + h * 0.3), (x - r, top + h * 0.3), (x - r, top + h * 0.7), (x - r - 7, top + h * 0.7)], DIM, 1.0))  # mount
    o += lugs(x, top, r, ry, h, 3)
    o += batter(x, top, r, ry, e, v)
    return o


def tilt(pts, cx, cy, deg):
    c, s_ = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [(cx + (px - cx) * c - (py - cy) * s_, cy + (px - cx) * s_ + (py - cy) * c) for px, py in pts]


def hat(x, base, r, e, open_, v, rock=(0.0, 0.0)):
    """two cymbals on a rod; a hit lifts the top one open, lights it and rocks it (one edge up, the other down)"""
    o = [shape([(x, base - 30), (x, base + 6)], DIM, 1.4, close=False)]
    for (y, lit), deg in zip(((base + 2, False), (base - 3 - open_, True)), rock):
        ry = r * 0.22
        on = lit and e >= 0.04
        T = lambda pts: tilt(pts, x, y, deg)
        o.append(shape(T(ellipse(x, y, r, ry, 32)), HOT if on else G[6], 1.3, fill=lit_fill(e, v) if on else "#000000"))
        for k in (0.45, 0.75):
            o.append(shape(T(ellipse(x, y, r * k, ry * k, 24)), DIM, 0.8, fill="none"))
        o.append(shape(T(ellipse(x, y - 0.6, r * 0.13, ry * 0.35, 12)), G[6], 1.0, fill="none"))
    if v["fm"] > 0.05 and e > 0.05:                                 # fm: shimmer arcs off the open hat
        for k in range(round(1 + 3 * v["fm"])):
            a = -0.5 - 0.45 * k
            o.append(shape(ellipse(x, base - 3 - open_, r + 4 + 3 * k, r * 0.22 + 2 + k, 8, a - 0.3, a + 0.3), G[6], 1.0, close=False))
    return o


DRAW = {"kick": kick, "floor": floor_tom, "snare": snare, "tom": rack_tom}


def tower(v, hits):
    o = []
    now = hits.now
    lift = [0.0] * len(TIERS)
    e_t = [0.0] * len(TIERS)
    rock_top = rock_bottom = 0.0
    for i, t, note in hits.played()[-12:]:
        z = zone_of(note, v)
        k = tier_of(z)
        dt = now - t
        if k == len(TIERS) - 1:                                   # a hat hit rocks the cymbals, alternating sides
            side = 1 if i % 2 else -1
            amp = (5 + 7 * v["punch"]) * math.exp(-dt / 0.45)
            rock_top += side * amp * math.cos(2 * math.pi * 2.4 * dt)
            rock_bottom += side * 0.35 * amp * math.cos(2 * math.pi * 2.4 * dt + 0.6)
        lfo = 1 + v["lfo"] * 0.6 * lfo_at(i + 1, v)                 # the hit LFO makes some hits jump higher than others
        lift[k] = max(lift[k], rise(dt, (3 + 8 * v["punch"]) * lfo))
        e_t[k] = max(e_t[k], env(dt, v, z))
    y = 194
    # the floor: centred under the kick's bottom hoop, in the same perspective as every head (ry = 0.26 r)
    kr = TIERS[0][1]
    o.append(shape(ellipse(240, y + 1, kr + 8, (kr + 8) * 0.26, 40), G[2], 1.0, fill="none"))
    for k, (z, r, hgt, kind) in enumerate(TIERS):
        ry = r * 0.26
        e = e_t[k]
        if kind == "hat":
            o += hat(240, y - 6, r, e, lift[k] * 1.4, v, rock=(rock_bottom, rock_top))
            break
        top = y - hgt - lift[k]
        o += DRAW[kind](240, top, r, ry, hgt, e, v)
        y = y - hgt - GAP
    o += sizzle(v, hits, 240, 54, 120, 4)
    return o


def groove(start, bars, notes):
    seq = []
    for b in range(bars):
        for k, n in enumerate(notes):
            if n is not None:
                seq.append((start + b * 2.0 + k * 0.125, n))
    return seq


def score():
    """the groove and the control automation, shared with the soundtrack (../audio/soundtrack.py)"""
    K, S_, T1, T2, HH = 0.02, 0.45, 0.25, 0.65, 0.9
    beat = [K, HH, T1, HH, S_, HH, K, T2, K, HH, T1, HH, S_, HH, T2, S_]
    fill = [K, None, T2, T2, T1, T1, S_, S_, K, HH, S_, HH, T2, T1, S_, K]
    seq = groove(0.6, 2, beat) + groove(4.6, 1, fill) + groove(6.6, 8, beat) + groove(22.6, 1, fill)
    D = dict(DEFAULTS)
    sweeps = [(6.6, 8.6, "punch", D["punch"], 1.0), (8.6, 10.6, "decay", D["decay"], 0.9), (10.6, 12.6, "lfo", 0.0, 1.0),
              (12.6, 14.6, "fm", D["fm"], 1.0), (14.6, 16.6, "noise", D["noise"], 1.0), (16.6, 18.6, "cutoff", D["cutoff"], 1.0),
              (18.6, 20.6, "tune", 0.5, 0.2), (20.6, 22.6, "rate", D["rate"], 0.95)]

    def values(t):
        v = dict(D, lfo=0.35, decay=0.4)
        for t0, t1, name, a, b in sweeps:
            if t0 <= t <= t1:
                u = math.sin(math.pi * (t - t0) / (t1 - t0))     # up and back
                v[name] = a + (b - a) * u
        return v

    return seq, values, 25.0


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    seq, values, length = score()
    frames = int(length * FPS)

    def render(i):
        t = i / FPS
        v = values(t)
        svg = out / f"f{i:04d}.svg"
        svg.write_text(frame(v, tower(v, Phrase(seq, t))))
        subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(svg), "-o", str(out / f"f{i:04d}.png")], check=True)
        svg.unlink()

    with ThreadPoolExecutor(8) as ex:
        list(ex.map(render, range(frames)))
    print(frames, "frames")


if __name__ == "__main__":
    main()
