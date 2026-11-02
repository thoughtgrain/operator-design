#!/usr/bin/env python3
"""Torso, round 3: a fresh pass at M2 and M3 (two candidates each, same slab language), and M4's keyboard in depth.

  M2a echo field   every pulse throws its repeats as rows behind it, so the bar becomes a field: across = the bar
                   (heights follow the phrase), back = the repeats (each row lower, spaced by time and pace),
                   up = voicing (layers on the front row)
  M2b close-up     the pulse sounding now, large in the middle: its chord's notes stacked (voicing) and its repeats
                   running back into the distance (repeats, time); the whole bar as a small row of slabs along
                   the bottom, heights following the phrase (range), the sounding one lit
  M3a groove ring  the bar as a ring of slabs seen from above at an angle: height = velocity, length along the
                   ring = sustain, swing pushes the off-beats round off their marks, accents capped
  M3b lanes        the last four bars as lanes, newest in front (the loom again, in time): height = velocity,
                   length = sustain, swing off the grid; bars behind show how the groove has held
  M4  keyboard     two octaves of keys as blocks in depth: the scale's notes dotted on the key tops, the root
                   brightest with a mark on its front face, a played key pressed down and lit, random jitters dots

    python3 round3.py      → round3/*.svg/.png and round3/sheet.png
"""
from __future__ import annotations

import math
import subprocess
from pathlib import Path

from PIL import Image

import clean as C
from clean import Cam, G, path, solid, hollow, header

HERE = Path(__file__).resolve().parent
OUT = HERE / "round3"
ON = {0, 2, 4, 5, 7, 9, 11, 12, 14}                                  # 9 pulses, as the demo's
PROF = [1.0, 0.5, 0.6, 0.8, 0.5, 0.9, 0.5, 0.6, 1.0, 0.7, 0.5, 0.85, 0.6, 0.5, 0.95, 0.75]
TMPL = [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0]


def phrase(s, rng=1.0):
    return 0.5 + 0.5 * rng * math.sin(2 * math.pi * s / 16)


def draw(items):
    o = []
    for _, _, g in sorted(items, key=lambda q: (-q[0], -q[1])):
        o += g
    return o


# ---- M2a echo field -----------------------------------------------------------------------------------------------------
def m2a(repeats=3, time=1.0, voices=3, rng=1.0, step=4, on=None):
    cam = Cam(el=44, d=520, focal=600, target=(0.0, 0.0, 38.0), screen=(240.0, 132.0))
    dx = 21.0
    items, o = [], []
    zmax = 0.0
    for s in sorted(on if on is not None else ON):
        x = (s - 7.5) * dx
        h = 8 + 22 * phrase(s, rng)
        lh = (h - 1.8 * (voices - 1)) / voices
        g = []
        for v in range(voices):
            g += solid(cam, x - 6, x + 6, lh, 0, 10, 0, lit=(s == step), y0=v * (lh + 1.8))
        items.append((0, abs(x), g))
        z, gap = 16.0, 16.0 * time
        for r in range(1, repeats + 1):
            rh = max(2.5, h * (1 - 0.2 * r))
            items.append((z, abs(x), solid(cam, x - 5, x + 5, rh, z, z + 8, min(r, 4), lit=False)))
            zmax = max(zmax, z + 8)
            z += 8 + gap
            gap *= 0.75
    o.append(cam.line((-8.5 * dx, 0, 5), (8.5 * dx, 0, 5), 0x4B, 1.0))
    return o + draw(items), header(("repeats", "time", "voicing", "range"),
                                   (str(repeats), {1.0: "1/32", 0.8: "1/32", 0.6: "1/64"}.get(round(time, 1), "1/32"), f"{voices} up", "sine"))


# ---- M2b close-up -------------------------------------------------------------------------------------------------------
def m2b(repeats=3, time=1.0, voices=3, rng=1.0, step=4):
    cam = Cam(el=46, d=420, focal=520, target=(0.0, 10.0, 46.0), screen=(240.0, 112.0))
    items = []
    h = 30 + 26 * phrase(step, rng)
    lh = (h - 3 * (voices - 1)) / voices
    g = []
    for v in range(voices):                                            # the chord, stacked
        g += solid(cam, -16, 16, lh, 0, 24, 0, lit=(v == voices - 1), y0=v * (lh + 3))
    items.append((0, 0, g))
    z, gap = 32.0, 22.0 * time
    for r in range(1, repeats + 1):                                    # its repeats, into the distance
        rh = max(4.0, h * (1 - 0.2 * r))
        items.append((z, 0, hollow(cam, -14, 14, rh, z, z + 14, min(r - 1, 3))))
        z += 14 + gap
        gap *= 0.75
    o = draw(items)
    # the whole bar along the bottom, small and flat: heights follow the phrase
    for s in range(16):
        x = 120 + s * 15
        if s not in ON:
            o.append(path([(x + 3, 206), (x + 7, 206), (x + 7, 207), (x + 3, 207)], G(0x4B), 0.4, G(0x4B)))
            continue
        bh = 4 + 14 * phrase(s, rng)
        g = 0xCD if s == step else 0x96
        o.append(path([(x, 207 - bh), (x + 10, 207 - bh), (x + 10, 207), (x, 207)], G(g), 0.4, G(g)))
    return o, header(("repeats", "time", "voicing", "range"), (str(repeats), "1/32", f"{voices} up", "sine"))


# ---- M3a groove ring ----------------------------------------------------------------------------------------------------
def m3a(velocity=0.8, sustain=0.5, accent=1.0, swing=0.62, head=5):
    cam = Cam(el=52, d=520, focal=560, target=(0.0, 0.0, 0.0), screen=(240.0, 128.0))
    R0, R1 = 62.0, 88.0
    items, o = [], []
    for s in range(16):                                                # the marks: straight 16ths, round the ring
        a = 2 * math.pi * s / 16 - math.pi / 2
        o.append(cam.line((R1 * math.cos(a), 0, R1 * math.sin(a)), ((R1 + 6) * math.cos(a), 0, (R1 + 6) * math.sin(a)),
                          0x64 if s % 4 == 0 else 0x4B, 1.0))
    for s in sorted(ON):
        a0 = 2 * math.pi * (s + ((swing - 0.5) * 2 if s % 2 else 0)) / 16 - math.pi / 2
        a1 = a0 + 2 * math.pi / 16 * (0.15 + 0.8 * sustain)
        h = 2 + 16 * velocity * PROF[s] * (1 + 0.35 * accent * TMPL[s])
        n = 4
        g = []
        for k in range(n):                                             # an arc slab, in short straight pieces
            b0, b1 = a0 + (a1 - a0) * k / n, a0 + (a1 - a0) * (k + 1) / n
            quad = lambda y, b0=b0, b1=b1: [(R0 * math.cos(b0), y, R0 * math.sin(b0)), (R0 * math.cos(b1), y, R0 * math.sin(b1)),
                                          (R1 * math.cos(b1), y, R1 * math.sin(b1)), (R1 * math.cos(b0), y, R1 * math.sin(b0))]
            top = quad(h)
            Rf = R1 if math.sin((b0 + b1) / 2) < 0 else R0              # the wall facing the camera
            outer = [(Rf * math.cos(b0), 0, Rf * math.sin(b0)), (Rf * math.cos(b1), 0, Rf * math.sin(b1)),
                     (Rf * math.cos(b1), h, Rf * math.sin(b1)), (Rf * math.cos(b0), h, Rf * math.sin(b0))]
            lit = s == head
            g.append(path([cam(p) for p in outer], G(0x32), 0.4, G(0x7D)))
            g.append(path([cam(p) for p in top], G(0x32), 0.4, G(0xCD if lit else 0xAF)))
            if TMPL[s] and accent > 0.05:
                cap = quad(h + 2)
                g.append(path([cam(p) for p in cap], G(0xCD), 0.6, "none"))
        mid = (a0 + a1) / 2
        items.append((R1 * math.sin(mid), 0, g))
    return o + draw(items), header(("velocity", "sustain", "accent", "timing"), (str(round(127 * velocity)), "1/2", "agogo", f"{round(swing * 100)}%"))


# ---- M3b lanes ----------------------------------------------------------------------------------------------------------
def m3b(velocity=0.8, sustain=0.5, accent=1.0, swing=0.62, head=5, on=None):
    cam = Cam(el=40, d=520, focal=560, target=(0.0, 0.0, 34.0), screen=(240.0, 132.0))
    dx = 21.0
    x0 = -8 * dx
    items, o = [], []
    for age in range(3, -1, -1):
        z = age * 22.0
        o.append(cam.line((x0, 0, z), (x0 + 16 * dx, 0, z), 0x4B if age == 0 else 0x32, 1.0))
        for s in range(17):
            if age == 0:
                o.append(cam.line((x0 + s * dx, 0, -3), (x0 + s * dx, 0, 0), 0x64 if s % 4 == 0 else 0x4B, 1.0))
        jit = [0.6 * math.sin(s * 3.1 + age * 1.7) for s in range(16)]  # the bars behind wander a little
        for s in sorted(on if on is not None else ON):
            x = x0 + s * dx + (dx * (swing - 0.5) * 2 if s % 2 else 0) + (jit[s] if age else 0)
            h = 3 + 26 * velocity * PROF[s] * (1 + 0.35 * accent * TMPL[s]) * (1 - 0.08 * age)
            L = max(3.0, dx * (0.15 + 0.85 * sustain))
            g = solid(cam, x, x + L, h, z + 1, z + 11, min(age, 3), lit=(age == 0 and s == head))
            if age == 0 and TMPL[s] and accent > 0.05:
                g += solid(cam, x - 1, x + L + 1, 1.8, z, z + 12, 0, True, y0=h + 1.2)
            items.append((z, abs(x), g))
    sus = "1/8" if sustain < 0.3 else "1/4" if sustain < 0.45 else "1/2"
    return o + draw(items), header(("velocity", "sustain", "accent", "timing"), (str(round(127 * velocity)), sus, "agogo", f"{round(swing * 100)}%"))


# ---- M4 keyboard in depth -----------------------------------------------------------------------------------------------
WHITE = [0, 2, 4, 5, 7, 9, 11]
BLACK_LEFT = {1: 1, 3: 2, 6: 4, 8: 5, 10: 6}


def m4(root=6, scale="major", channel=3, random_amt=0.25, played=(13,)):
    cam = Cam(el=40, d=520, focal=620, target=(0.0, 0.0, 30.0), screen=(240.0, 120.0))
    ww, wd, wh = 25.0, 76.0, 10.0                                      # white key: width, depth, height
    bw, bd, bh = 15.0, 46.0, 15.0
    x0 = -7 * ww
    items = []
    tops = {}
    for n in range(24):
        o_, pc = divmod(n, 12)
        press = 2.5 if n in played else 0.0
        if pc in BLACK_LEFT:
            x = x0 + (o_ * 7 + BLACK_LEFT[pc]) * ww - bw / 2
            g = cam.box(x, x + bw, 0, bh - press, wd - bd, wd, "#000000", "#000000", "#000000",
                        "#CDCDCD", 1.6 if n in played else 1.0)          # black keys: black, in white wire
            items.append((-1, abs(x + bw / 2), g))
            tops[n] = (x + bw / 2, bh - press, wd - bd + 9)
        else:
            x = x0 + (o_ * 7 + WHITE.index(pc)) * ww
            g = cam.box(x + 0.6, x + ww - 0.6, 0, wh - press, 0, wd, G(0xCD if n in played else 0x96), G(0x64), G(0x4B), G(0x32), 0.6)
            items.append((0, abs(x + ww / 2), g))
            tops[n] = (x + ww / 2, wh - press, 12.0)
    o = []
    for _, _, g in sorted(items, key=lambda q: (-q[0], -q[1])):
        o += g
    scale_set = C.SCALES[scale]
    for n in range(24):
        if (n - root) % 12 not in scale_set:
            continue
        x, y, z = tops[n]
        z += random_amt * 10 * math.sin(n * 2.3 + 1.1)
        cx, cy = cam((x, y, z))
        r = (4.0 if (n - root) % 12 == 0 else 2.8) * 620 / (520 + z)
        dark = n in played
        o.append(path([(cx + r * math.cos(2 * math.pi * k / 16), cy + r * math.sin(2 * math.pi * k / 16) * 0.75) for k in range(16)],
                      "#000000" if dark else "#CDCDCD", 0.6, "#000000" if dark else "#CDCDCD"))
        if (n - root) % 12 == 0:                                       # the root: a mark on the key's front face
            fx, fy = cam((x, y * 0.5, -0.1))
            o.append(path([(fx - 4, fy - 1.5), (fx + 4, fy - 1.5), (fx + 4, fy + 1.5), (fx - 4, fy + 1.5)], "#000000", 0.4, "#000000"))
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    return o, header(("pitch", "scale", "channel", "random"), (names[root], scale, f"ch {channel}", f"{round(random_amt * 100)}%"))


def main():
    OUT.mkdir(exist_ok=True)
    ims = []
    for name, built in (("m2a", m2a()), ("m2b", m2b()), ("m3a", m3a()), ("m3b", m3b()), ("m4", m4())):
        svg = OUT / f"{name}.svg"
        svg.write_text(C.frame(*built))
        subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(svg), "-o", str(OUT / f"{name}.png")], check=True)
        ims.append(Image.open(OUT / f"{name}.png"))
    sheet = Image.new("RGB", (960, 3 * 230), "#1A1A1A")
    for k, im in enumerate(ims):
        sheet.paste(im, (480 * (k % 2), 230 * (k // 2)))
    sheet.save(OUT / "sheet.png")
    print("wrote round3/sheet.png")


if __name__ == "__main__":
    main()
