#!/usr/bin/env python3
"""d4 drum tower, animated: a two-bar groove at 120 bpm with the controls swept while it plays.

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
TIERS = [(0.02, 80, 24), (0.25, 66, 18), (0.45, 54, 16), (0.65, 44, 12), (0.88, 38, 0)]   # zone, radius, height


def tier_of(z):
    return min(range(len(TIERS)), key=lambda k: abs(TIERS[k][0] - z))


def spring(dt, amp, f_hz=5.5, tau=0.16):
    return amp * math.exp(-dt / tau) * math.cos(2 * math.pi * f_hz * dt) if dt >= 0 else 0.0


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


def tower(v, hits):
    o = []
    now = hits.now
    played = hits.played()
    # per-tier: spring lift and the envelope that drives rings and brightness
    lift = [0.0] * len(TIERS)
    e_t = [0.0] * len(TIERS)
    wobble = 0.0
    tip = 0.0
    for i, t, note in played[-12:]:
        z = zone_of(note, v)
        k = tier_of(z)
        dt = now - t
        lift[k] += spring(dt, 8 + 22 * v["punch"])
        e_t[k] = max(e_t[k], env(dt, v, z))
        side = 1 if i % 2 else -1
        wobble += spring(dt, side * (3 + 7 * v["punch"]) * (1 + 0.8 * (k == 0)), f_hz=2.6, tau=0.35)
        if k == len(TIERS) - 1:
            tip += spring(dt, 1.6, f_hz=4.0, tau=0.3)
    # the LFO lean eases from the previous hit's value to this one's
    n = hits.count()
    if n:
        t_last = played[-1][1]
        a = 1 - math.exp(-(now - t_last) / 0.12)
        lean = v["lfo"] * ((1 - a) * lfo_at(n - 1, v) + a * lfo_at(n, v))
    else:
        lean = 0.0
    y = 198
    o.append(path(ellipse(240 + wobble * 0.3, 202, 104, 14), "#1E1E1E"))
    rise = 0.0
    for k, (z, r, hgt) in enumerate(TIERS):
        rise += max(-5.0, lift[k])                       # every tier rides on the ones below
        x = 240 + lean * k * 12 + wobble * (k + 1) * 0.7
        ry = r * 0.26
        e = e_t[k]
        if hgt == 0:                                     # the top: a hi-hat pair that tips and rocks
            o += cymbal(x, y - 9 - rise, r, e, v, wob=max(0.0, min(1.0, abs(tip))))
            o += cymbal(x - tip * 2, y - 2 - rise * 0.5, r, 0, v)
            break
        top = y - hgt - rise
        o += shell(x, top, r, ry, hgt, lugs=3 + (k == 0))
        o += head(x, top, r, ry, e, v)
        y = y - hgt - 4
    o += sizzle(v, hits, 240 + lean * 20, 64 - (rise * 0.5), 120, 4)
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
