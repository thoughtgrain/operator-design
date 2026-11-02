#!/usr/bin/env python3
"""Torso, round 2 in motion: one pattern playing while the view moves through M1 → M2 → M3 → M4, with knobs turned
on each page so every parameter's effect shows, and the pattern's notes as sound.

  0–12 s   M1 sequencer   pulses 5 → 9, cycles 4 → 6 (four rows show), a cycle held at 6 s, recalled at 9.5 s
 12–20 s   M2 repeats     repeats 1 → 4, then time shortens
 20–28 s   M3 groove      velocity 50 → 100 %, sustain shortens, swing 50 → 66 %
 28–36 s   M4 tonal       scale major → minor, then random 0 → 60 %

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
LENGTH = 36.0
DEG = [0, 2, 4, 1, 3, 5, 2, 6, 4, 0, 5, 3, 1, 6, 2, 4]               # each step's scale degree
VEL = [1.0, 0.5, 0.6, 0.8, 0.5, 0.9, 0.5, 0.6, 1.0, 0.7, 0.5, 0.85, 0.6, 0.5, 0.95, 0.75]
TMPL = [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0]


def lerp(t, t0, t1, a, b):
    u = max(0.0, min(1.0, (t - t0) / (t1 - t0)))
    return a + (b - a) * u


FREEZE_T, RECALL_T = 6.0, 9.5                                          # hold a cycle; go back to it


def pass_of(t):
    return int(t // (16 * STEP))


HELD = pass_of(FREEZE_T) % 3                                           # the cycle frozen at FREEZE_T (its rotation)


def shift_at(t):
    """the rotation the front row plays: each pass moves on, until the held cycle is recalled"""
    return HELD if t >= RECALL_T else pass_of(t) % 3


def state(t):
    page = 1 if t < 12 else 2 if t < 20 else 3 if t < 28 else 4
    return {"page": page, "steps": 16, "division": 1.0,
            "pulses": round(lerp(t, 1, 4, 5, 9)), "cycles": round(lerp(t, 4.5, 5.5, 4, 6)),
            "repeats": round(lerp(t, 13, 16, 1, 4)), "time": lerp(t, 17, 19, 1.0, 0.6), "voices": 3, "range": 1.0,
            "velocity": lerp(t, 21, 23, 0.5, 1.0), "sustain": lerp(t, 23.5, 25, 0.5, 0.15), "accent": 1.0,
            "swing": lerp(t, 25.5, 27.5, 0.5, 0.66),
            "root": 6, "scale": "major" if t < 30 else "minor", "random": lerp(t, 32, 35, 0.0, 0.6)}


def notes():
    """(time, step, pitch, velocity): every pulse (rotated by the cycle), its repeats, swing and random applied"""
    out = []
    rnd = random.Random(3)
    n = int(LENGTH / STEP)
    for i in range(n):
        t = i * STEP
        st = state(t)
        s = i % 16
        if s not in C.m1_pattern(st["pulses"], 16, shift_at(t)):
            continue
        tt = t + (STEP * (st["swing"] - 0.5) * 2 if s % 2 else 0)
        scale = sorted(C.SCALES[st["scale"]])
        deg = DEG[s] % len(scale)
        pitch = 48 + st["root"] + scale[deg] + (rnd.choice([-2, -1, 1, 2]) if rnd.random() < st["random"] else 0)
        v = min(127, round(127 * st["velocity"] * VEL[s] * (1 + 0.3 * st["accent"] * TMPL[s])))
        out.append((tt, s, pitch, v, 0.03 + 0.2 * st["sustain"]))
        gap = STEP * 0.5 * st["time"]
        for r in range(1, st["repeats"]):                               # repeats, decaying, accelerating
            tt += gap
            gap *= 0.8
            out.append((tt, s, pitch, round(v * (1 - 0.2 * r)), 0.05))
    return out


NOTES = notes()


def frame(t):
    st = state(t)
    step = int(t // STEP) % 16
    on = C.m1_pattern(st["pulses"], 16, shift_at(t))
    sounding = [n for n in NOTES if 0 <= t - n[0] < 0.1]
    pg = st["page"]
    if pg == 1:
        held = HELD if t >= FREEZE_T else None
        recall = 0.0 if t < RECALL_T else min(1.0, (t - RECALL_T) / 0.25)
        built = C.m1(st["steps"], st["pulses"], st["cycles"], st["division"], head=step, pass_idx=pass_of(t),
                     held=held, recall=recall)
    elif pg == 2:
        lit = sounding[0][1] if sounding else -1
        past = [n[1] for n in NOTES if n[0] <= t]
        built = C.m2(st["repeats"], round(st["time"], 1), st["voices"], st["range"], step=lit, on=on,
                     last=past[-1] if past else None)
    elif pg == 3:
        built = C.m3(st["velocity"], st["sustain"], st["accent"], st["swing"], head=step if step in on else -1, on=on)
    else:
        played = {n[2] - 48 for n in sounding if 0 <= n[2] - 48 < 24}
        built = C.m4(st["root"], st["scale"], 3, st["random"], played=played)
    return C.frame(*built)


def main():
    tmp = Path(sys.argv[1])
    tmp.mkdir(parents=True, exist_ok=True)
    A.LENGTH = LENGTH
    wav = tmp / "anim.wav"
    A.sound(wav, [(t, t + g, p, v) for t, _, p, v, g in NOTES])
    n = int(LENGTH * A.FPS)
    keep = {int(tt * A.FPS) for tt in (7.0, 9.9, 16.5, 19.5, 24.0, 27.8)}

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
