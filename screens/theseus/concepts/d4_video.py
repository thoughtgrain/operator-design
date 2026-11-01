#!/usr/bin/env python3
"""d4 drum tower, animated: a two-bar groove at 120 bpm with the controls swept while it plays.

Revision 2 (after Brian's notes): each tier looks like the drum it plays, and only the drum that's hit moves, and
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
from blocks import DEFAULTS, G, env, frame, lfo_at, path, zone_of  # noqa: E402
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


def block(x0, y0, x1, y1, fill):
    return path([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill)


def kick(x, top, r, ry, h, e, v):
    """the bass drum: the deepest, darkest shell with a pale wrap stripe, claw hooks, and a felt beater patch"""
    o = shell(x, top, r, ry, h, side=G[2], edge="#141414", lugs=0)
    o.append(path([(x - r, top + h * 0.42), (x + r, top + h * 0.42)] + ellipse(x, top + h * 0.58, r, ry, 20, 0, math.pi)[::-1][::-1][::-1] if False else
                  [(x - r, top + h * 0.40)] + ellipse(x, top + h * 0.40, r, ry, 20, math.pi, 0) + [(x + r, top + h * 0.40), (x + r, top + h * 0.56)] + ellipse(x, top + h * 0.56, r, ry, 20, 0, math.pi) + [(x - r, top + h * 0.56)], G[4]))
    for k in range(8):                                            # claw hooks round the front
        t = math.pi * (0.1 + 0.8 * k / 7)
        lx, ly = x + r * math.cos(t) * 0.99, top + 4 + ry * math.sin(t)
        o.append(block(lx - 1.4, ly - 2, lx + 1.4, ly + 4, G[5]))
    o += head(x, top, r, ry, e, v, tone=G[5])
    o.append(path(ellipse(x + r * 0.28, top + ry * 0.15, r * 0.16, ry * 0.16), G[2]))   # felt beater patch
    return o


def floor_tom(x, top, r, ry, h, e, v):
    """the floor tom: tall, with three legs out to the sides"""
    o = []
    for sx in (-1, 1):
        o.append(path([(x + sx * (r - 2), top + h * 0.3), (x + sx * (r + 8), top + h + 6), (x + sx * (r + 6.5), top + h + 6), (x + sx * (r - 3.5), top + h * 0.3)], G[4]))
    o += shell(x, top, r, ry, h, side=G[3], lugs=4)
    o += head(x, top, r, ry, e, v)
    return o


def snare(x, top, r, ry, h, e, v):
    """the snare: a shallow bright metal shell, many lugs, the strainer, and wires showing under the bottom hoop"""
    o = []
    for k in range(7):                                             # the wires, a little wider than the shell
        yy = top + h + ry * 0.35 + 1.2 * k - 2
        o.append(block(x - r * 0.62, yy, x + r * 0.62, yy + 0.7, G[5]))
    o += shell(x, top, r, ry, h, side=G[5], edge=G[3], lugs=7, lug=G[7])
    o.append(block(x - r * 0.05, top + ry * 0.9 + 1, x + r * 0.12, top + ry * 0.9 + h - 1, G[7]))   # strainer
    o += head(x, top, r, ry, e, v, tone=G[6])
    return o


def rack_tom(x, top, r, ry, h, e, v):
    """the rack tom: medium depth, a mount bracket on its side"""
    o = shell(x, top, r, ry, h, side=G[3], lugs=3)
    o.append(block(x - r - 6, top + h * 0.25, x - r + 2, top + h * 0.75, G[5]))                    # mount
    o.append(block(x - r - 9, top + h * 0.40, x - r - 4, top + h * 0.60, G[4]))
    o += head(x, top, r, ry, e, v)
    return o


def hi_hat(x, top, r, e, v):
    """the hi-hat: two cymbals on a clutch rod; a hit opens the top one"""
    o = [block(x - 0.9, top - 22, x + 0.9, top + 6, G[4])]          # rod
    o += cymbal(x, top + 4, r, 0, v)
    open_ = rise(0, 0)
    o += cymbal(x, top - 2 - e * 0, r, e, v, wob=0.0)
    return o


DRAW = {"kick": kick, "floor": floor_tom, "snare": snare, "tom": rack_tom}


def tower(v, hits):
    o = []
    now = hits.now
    lift = [0.0] * len(TIERS)
    e_t = [0.0] * len(TIERS)
    for i, t, note in hits.played()[-12:]:
        z = zone_of(note, v)
        k = tier_of(z)
        dt = now - t
        lfo = 1 + v["lfo"] * 0.6 * lfo_at(i + 1, v)                 # the hit LFO makes some hits jump higher than others
        lift[k] = max(lift[k], rise(dt, (3 + 8 * v["punch"]) * lfo))
        e_t[k] = max(e_t[k], env(dt, v, z))
    y = 204
    o.append(path(ellipse(240, 206, 108, 14), "#1E1E1E"))
    for k, (z, r, hgt, kind) in enumerate(TIERS):
        ry = r * 0.26
        e = e_t[k]
        if kind == "hat":
            base = y - 6
            o.append(block(239.1, base - 26, 240.9, base + 4, G[4]))   # the clutch rod
            o += cymbal(240, base + 2, r, 0, v)                         # bottom hat stays
            o += cymbal(240, base - 3 - lift[k] * 1.4, r, e, v)         # the top hat lifts open on a hit
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


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    K, S_, T1, T2, HH = 0.02, 0.45, 0.25, 0.65, 0.9
    beat = [K, HH, T1, HH, S_, HH, K, T2, K, HH, T1, HH, S_, HH, T2, S_]
    fill = [K, None, T2, T2, T1, T1, S_, S_, K, HH, S_, HH, T2, T1, S_, K]
    seq = groove(0.6, 2, beat) + groove(4.6, 1, fill) + groove(6.6, 8, beat) + groove(22.6, 1, fill)
    D = dict(DEFAULTS)
    # control automation: (start, end, name, from, to) — each swept up and back while the groove plays
    sweeps = [(6.6, 8.6, "punch", D["punch"], 1.0), (8.6, 10.6, "decay", D["decay"], 0.9), (10.6, 12.6, "lfo", 0.0, 1.0),
              (12.6, 14.6, "fm", D["fm"], 1.0), (14.6, 16.6, "noise", D["noise"], 1.0), (16.6, 18.6, "cutoff", D["cutoff"], 1.0),
              (18.6, 20.6, "tune", 0.5, 0.2), (20.6, 22.6, "rate", D["rate"], 0.95)]
    length = 25.0

    def values(t):
        v = dict(D, lfo=0.35, decay=0.4)
        for t0, t1, name, a, b in sweeps:
            if t0 <= t <= t1:
                u = (t - t0) / (t1 - t0)
                u = math.sin(math.pi * u)                 # up and back
                v[name] = a + (b - a) * u
        return v

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
