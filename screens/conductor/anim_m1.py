#!/usr/bin/env python3
"""M1 in motion: a phrase playing, a key turn while stopped, then the song again in the new key.

Timeline at 30 fps, 120 BPM (a 16th is 0.125 s, a bar 2 s, hrate 1 bar):
  0.0 – 8.0 s   C major pop plays four bars. Each lane's moon lights when it plays and fades over 0.2 s; on each
                chord change the moons travel the short way round the orbit to the new planet in 0.2 s.
  8.0 – 8.4 s   stop: the moons ease back to chord 1, the playheads go.
  8.6 – 10.0 s  key is turned C → G, one click every 0.2 s; each click eases the planets round in 0.2 s.
  10.4 – 14.4 s G major plays two bars.

    python3 anim_m1.py <out.mp4> [--scale 2]
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import gen_frames as G

FPS, STEP, EASE = 30, 0.125, 0.2


def ease(u: float) -> float:
    """Exponential-ish ease-out that settles at 1 when u reaches 1."""
    u = min(max(u, 0.0), 1.0)
    return 1 - (1 - u) ** 3


def short(a: float, b: float) -> float:
    return ((b - a + 6) % 12) - 6


def hits_at(step: int) -> set[int]:
    lanes = G.default_lanes()
    return {i for i, ln in enumerate(lanes) if step in G.lane_hits(ln, i)}


def glow_at(t: float, t0: float) -> dict:
    """Each lane's light at time t: 1 on the step it plays, fading to 0 over 0.2 s."""
    g = {}
    for lane in range(8):
        best = 0.0
        for back in range(3):
            s_time = (int((t - t0) / STEP) - back) * STEP + t0
            if s_time < t0:
                continue
            step = int(round((s_time - t0) / STEP)) % 16
            if lane in hits_at(step):
                best = max(best, 1 - (t - s_time) / EASE)
        g[lane] = max(0.0, best)
    return g


def song_for(key: int) -> G.Song:
    return G.Song(key=(key + 0.5) / 12)


def frame_at(t: float) -> G.Frame:
    if t < 8.0:                       # playing in C
        return playing(t, 0.0, song_for(0))
    if t < 10.4:                      # stopped; turn key at 8.6 + 0.2 i
        clicks = [8.6 + 0.2 * i for i in range(7)]
        done = sum(1 for c in clicks if t >= c)
        key_from = max(done - 1, 0)
        frac = ease((t - clicks[done - 1]) / EASE) if done else 1.0
        target = done
        rot = (key_from + frac) - target if done else 0.0
        song = song_for(target)
        # the moons drift home to chord 1 after the stop
        loop = song_for(0).loop
        last_pc = (0 + G.SCALES[0][loop[3]]) % 12
        if t < 8.6:
            moon_pc = last_pc + short(last_pc, 0) * ease((t - 8.0) / EASE)
        else:
            moon_pc = (target + G.SCALES[0][loop[0]]) % 12 + rot
        return G.draw_m1(song, position=0, playing=False, rot=rot, moon_pc=moon_pc)
    if t < 10.4 + 4.0:
        return playing(t, 10.4, song_for(7))
    return G.draw_m1(song_for(7))


def playing(t: float, t0: float, song: G.Song) -> G.Frame:
    el = t - t0
    step_abs = int(el / STEP)
    step = step_abs % 16
    bar = step_abs // 16
    pos = bar % 4
    loop = song.loop
    pc_now = (song.key + song.scale[loop[pos]]) % 12
    since_bar = el - bar * 16 * STEP
    if bar > 0 and since_bar < EASE:            # moons on their way from the last chord
        pc_prev = (song.key + song.scale[loop[(pos - 1) % 4]]) % 12
        moon_pc = pc_prev + short(pc_prev, pc_now) * ease(since_bar / EASE)
    else:
        moon_pc = float(pc_now)
    return G.draw_m1(song, position=pos, playing=True, step=step, glow=glow_at(t, t0), moon_pc=moon_pc)


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "m1-motion.mp4").resolve()
    scale = 2
    if "--scale" in sys.argv:
        scale = int(sys.argv[sys.argv.index("--scale") + 1])
    total = 14.8
    n = int(total * FPS)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        def render(i):
            svg = tmp / f"f{i:04d}.svg"
            svg.write_text(frame_at(i / FPS).svg())
            subprocess.run(["rsvg-convert", "-z", str(scale), str(svg), "-o", str(tmp / f"f{i:04d}.png")], check=True)
            svg.unlink()

        with ThreadPoolExecutor(4) as ex:
            list(ex.map(render, range(n)))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(tmp / "f%04d.png"),
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", str(out)],
                       check=True)
    print(f"wrote {out} ({n} frames)")


if __name__ == "__main__":
    main()
