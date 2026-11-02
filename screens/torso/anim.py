#!/usr/bin/env python3
"""Torso, round 2 in motion: one pattern playing while the view moves through M1 → M2 → M3 → M4, with knobs turned
on each page so every parameter's effect shows, and the pattern's notes as sound.

  0– 8 s   M1 sequencer   pulses 5 → 9, then cycles 4 → 6
  8–16 s   M2 repeats     repeats 1 → 4, then time shortens
 16–24 s   M3 groove      velocity 50 → 100 %, then swing 50 → 66 %
 24–32 s   M4 tonal       scale major → minor, then random 0 → 60 %

Page changes snap (the spec: a page opens at its state, no animation). Every change you hear is on the page you see.

    python3 anim.py <tmpdir>      → anim.mp4, anim-stills.png
"""
from __future__ import annotations

import math
import random
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / "meikyu" / "concepts"))
import clean as C                        # noqa: E402
import planets_av as A                   # noqa: E402

STEP = A.STEP
LENGTH = 32.0
DEG = [0, 2, 4, 1, 3, 5, 2, 6, 4, 0, 5, 3, 1, 6, 2, 4]               # each step's scale degree
VEL = [1.0, 0.5, 0.6, 0.8, 0.5, 0.9, 0.5, 0.6, 1.0, 0.7, 0.5, 0.85, 0.6, 0.5, 0.95, 0.75]
TMPL = [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0]


def lerp(t, t0, t1, a, b):
    u = max(0.0, min(1.0, (t - t0) / (t1 - t0)))
    return a + (b - a) * u


def state(t):
    s = {"page": min(4, int(t // 8) + 1), "steps": 16, "division": 1.0,
         "pulses": round(lerp(t, 2, 5, 5, 9)), "cycles": round(lerp(t, 6, 7, 4, 6)),
         "repeats": round(lerp(t, 9, 12, 1, 4)), "time": lerp(t, 13, 15, 1.0, 0.6), "voices": 3, "range": 1.0,
         "velocity": lerp(t, 17, 19, 0.5, 1.0), "sustain": 0.5, "accent": 1.0, "swing": lerp(t, 20, 22, 0.5, 0.66),
         "root": 6, "scale": "major" if t < 26 else "minor", "random": lerp(t, 28, 31, 0.0, 0.6)}
    return s


def notes():
    """(time, step, pitch, velocity): every pulse, its repeats, swing and random applied"""
    out = []
    rnd = random.Random(3)
    n = int(LENGTH / STEP)
    for i in range(n):
        t = i * STEP
        st = state(t)
        s = i % 16
        if s not in C.euclid(st["pulses"], 16):
            continue
        tt = t + (STEP * (st["swing"] - 0.5) * 2 if s % 2 else 0)
        scale = sorted(C.SCALES[st["scale"]])
        deg = DEG[s] % len(scale)
        pitch = 48 + st["root"] + scale[deg] + (rnd.choice([-2, -1, 1, 2]) if rnd.random() < st["random"] else 0)
        v = min(127, round(127 * st["velocity"] * VEL[s] * (1 + 0.3 * st["accent"] * TMPL[s])))
        out.append((tt, s, pitch, v))
        gap = STEP * 0.5 * st["time"]
        for r in range(1, st["repeats"]):                               # repeats, decaying, accelerating
            tt += gap
            gap *= 0.8
            out.append((tt, s, pitch, round(v * (1 - 0.2 * r))))
    return out


NOTES = notes()


def frame(t):
    st = state(t)
    step = int(t // STEP) % 16
    sounding = [n for n in NOTES if 0 <= t - n[0] < 0.1]
    pg = st["page"]
    if pg == 1:
        built = C.m1(st["steps"], st["pulses"], st["cycles"], st["division"], head=step, pass_idx=int(t // (16 * STEP)))
    elif pg == 2:
        lit = sounding[0][1] if sounding else -1
        built = C.m2(st["repeats"], round(st["time"], 1), st["voices"], st["range"], step=lit, on=C.euclid(st["pulses"], 16))
    elif pg == 3:
        built = C.m3(st["velocity"], st["sustain"], st["accent"], st["swing"], head=step if step in C.euclid(st["pulses"], 16) else -1, on=C.euclid(st["pulses"], 16))
    else:
        played = {n[2] - 48 for n in sounding if 0 <= n[2] - 48 < 24}
        built = C.m4(st["root"], st["scale"], 3, st["random"], played=played)
    return C.frame(*built)


def main():
    tmp = Path(sys.argv[1])
    tmp.mkdir(parents=True, exist_ok=True)
    A.LENGTH = LENGTH
    wav = tmp / "anim.wav"
    A.sound(wav, [(t, t + 0.1, p, v) for t, _, p, v in NOTES])
    n = int(LENGTH * A.FPS)
    keep = {int(tt * A.FPS) for tt in (3.0, 7.5, 13.0, 21.5, 26.5, 30.5)}

    def render(i):
        svg = tmp / f"f{i:04d}.svg"
        svg.write_text(frame(i / A.FPS))
        subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(svg), "-o", str(tmp / f"f{i:04d}.png")], check=True)
        if i not in keep:
            svg.unlink()

    with ThreadPoolExecutor(8) as ex:
        list(ex.map(render, range(n)))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(A.FPS), "-i", str(tmp / "f%04d.png"), "-i", str(wav),
                    "-vf", "scale=960:440:flags=neighbor", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", str(HERE / "anim.mp4")], check=True)
    ims = [Image.open(tmp / f"f{k:04d}.png") for k in sorted(keep)]
    sheet = Image.new("RGB", (960, 660))
    for k, im in enumerate(ims):
        sheet.paste(im, (480 * (k % 2), 220 * (k // 2)))
    sheet.save(HERE / "anim-stills.png")
    print("wrote anim.mp4,", len(NOTES), "notes")


if __name__ == "__main__":
    main()
