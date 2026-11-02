#!/usr/bin/env python3
"""Loom, round 2: the four pages kept clean (Brian, Nov 2).

The graphic represents the parameters; it isn't the interface. So no strips of cells, mode-key grids or badges at
rest: each page is the stock two-page header plus one drawing in the loom's language (slabs on threads, modelled in
3D, one camera), where every encoder visibly changes the drawing. Only M4, where pitch is the interaction itself,
keeps a keyboard.

  M1 sequencer  the loom: steps are warp threads, pulses are slabs, each cycle is a woven row
                  steps     how many warp threads (2–16)
                  pulses    how many slabs on the front row (spread Euclidean)
                  cycles    how many rows of cycles behind it (1–6)
                  division  warp spacing: longer notes, wider cloth
                manual pulse: a slab with a raised rim; retrigger: a split slab; the step playing: brightest top
  M2 repeats    the front row only, close up: each pulse and its repeats as slices
                  repeats   slices per pulse
                  time      gap between slices (pace: accelerating gaps)
                  voicing   layers stacked on each slab (the chord's notes)
                  range     the phrase: slab heights follow its shape across the bar
  M3 groove     the front row as a velocity profile
                  velocity  slab heights
                  sustain   slab depth (front to back): the gate
                  accent    the groove template lifts some slabs, which get a cap
                  timing    swing: every second slab slides right
                probability: hollow slab
  M4 tonal      two octaves of keys, flat, the scale's notes dotted, the root brightest with a dot under it
                  pitch     the root moves
                  scale     which keys carry dots
                  channel   header only (it's routing, not sound)
                  random    the dots jitter off their keys by the amount

Grey only; shapes carry every role.

    python3 clean.py      → clean/m1..m4.svg/.png and clean/pages.png
"""
from __future__ import annotations

import math
import subprocess
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
OUT = HERE / "clean"
FONT = 'font-family="UniversNextPro-Light"'
STOCK = [0x32, 0x4B, 0x64, 0x7D, 0x96, 0xAF, 0xCD]


def G(v):
    v = min(STOCK, key=lambda s: abs(s - round(v)))
    return f"#{v:02X}{v:02X}{v:02X}"


def f(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def path(pts, stroke, w=1.0, fill="none"):
    d = "M" + " L".join(f"{f(x)},{f(y)}" for x, y in pts) + " Z"
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{f(w)}"/>'


def text(x, y, s, size, fill):
    return f'<text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{fill}" {FONT} font-size="{size}px">{s}</text>'


class Cam:
    def __init__(self, el=40, d=620.0, focal=760.0, target=(0.0, 0.0, 40.0), screen=(240.0, 132.0)):
        self.el, self.d, self.F, self.T, self.S = math.radians(el), d, focal, target, screen

    def __call__(self, p):
        x, y, z = p[0] - self.T[0], p[1] - self.T[1], p[2] - self.T[2]
        ce, se = math.cos(self.el), math.sin(self.el)
        yc, zc = y * ce + z * se, z * ce - y * se + self.d
        k = self.F / zc
        return self.S[0] + x * k, self.S[1] - yc * k

    def box(self, x0, x1, y0, y1, z0, z1, top, front, side, stroke, w=0.5):
        faces = [([(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)] if (x0 + x1) / 2 < 0 else
                  [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)], side),
                 ([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)], front),
                 ([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], top)]
        return [path([self(p) for p in face], stroke, w, fill) for face, fill in faces]

    def line(self, a, b, g, w=1.0):
        (x0, y0), (x1, y1) = self(a), self(b)
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L * w / 2, dx / L * w / 2                       # a thin closed ribbon
        return path([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)], G(g), 0.3, G(g))


def solid(cam, x0, x1, h, z0, z1, age=0, lit=False, y0=0.0):
    d = 0x18 * age
    return cam.box(x0, x1, y0, y0 + h, z0, z1, G(0xCD if lit else 0xAF - d), G(0x7D - d), G(0x64 - d), G(0x32))


def hollow(cam, x0, x1, h, z0, z1, age=0, y0=0.0):
    return cam.box(x0, x1, y0, y0 + h, z0, z1, "#000000", "#000000", "#000000", G(0xAF - 0x18 * age), 1.0)


def euclid(k, n):
    return {round(i * n / k) % n for i in range(k)} if k else set()


def header(titles, values):
    o = []
    for i, g in enumerate([0x00, 0x32, 0x4B, 0x64, 0x7D, 0x96, 0xAF, 0xCD]):
        o.append(f'<rect x="{60 * i}" y="0" width="60" height="20" fill="{G(g) if g else "#000000"}" stroke="none"/>')
    for col, (t, v) in enumerate(zip(titles, values)):                 # the stock header, flush with the top
        light = "#CBCBCB" if col < 2 else "#000000"
        o.append(text(5 + 120 * col, 10, t, 10, light))
        o.append(text(65 + 120 * col, 17.4, v, 20 if len(v) <= 4 else 13, light))
    return o


# ---- M1 sequencer: the loom ---------------------------------------------------------------------------------------------
ROWS_SHOWN = 4                                                         # at most four rows of cycles on screen


def m1_pattern(pulses, steps, shift):
    """which steps sound in a cycle: the Euclidean pulses, rotated by the cycle's shift"""
    on = euclid(pulses, steps)
    return {s for s in range(steps) if (s + shift) % steps in on}


def m1(steps=16, pulses=5, cycles=4, division=1.0, head=6, pass_idx=0, held=None, recall=0.0):
    """held: the shift of a cycle the player froze, kept on the back row with brackets so they can go back to it;
    recall 0..1 slides it forward to the front, where it becomes what plays"""
    cam = Cam(el=42, target=(0.0, 0.0, 30.0), screen=(240.0, 128.0))
    dx = 18.0 * division
    xs = [(s - (steps - 1) / 2) * dx for s in range(steps)]
    DZ = 20.0
    live_rows = min(cycles, ROWS_SHOWN - (1 if held is not None else 0))
    o, items = [], []
    zback = (ROWS_SHOWN - 0.4) * DZ
    for x in xs:
        o.append(cam.line((x, 0, -6), (x, 0, zback), 0x32, 1.0))      # warp
    w = min(11.0, dx * 0.62)

    def row(z, shift, age, lit_head, bright=False):
        o.append(cam.line((xs[0] - 9, 0, z + 5), (xs[-1] + 9, 0, z + 5), 0x4B if age == 0 else 0x32, 1.0))   # weft
        on = m1_pattern(pulses, steps, shift)
        for s in range(steps):
            if s not in on:
                continue
            x = xs[s]
            h = 7 + 3 * ((s * 5) % 4)
            lit = lit_head and s == head
            a = 0 if bright else min(age, 4)
            if s == max(on) and len(on) > 2:                           # retrigger: a split slab
                g = solid(cam, x - w / 2, x - 0.8, h, z, z + 10, a, lit) + solid(cam, x + 0.8, x + w / 2, h, z, z + 10, a, lit)
            else:
                g = solid(cam, x - w / 2, x + w / 2, h, z, z + 10, a, lit)
            items.append((z, abs(x), g))

    for age in range(live_rows - 1, -1, -1):
        row(age * DZ, (age + pass_idx) % 3, age, age == 0 and recall < 1)
    if held is not None:                                               # the held cycle: brackets either side
        z = (ROWS_SHOWN - 1) * DZ * (1 - recall)
        row(z, held, 0 if recall else 2, recall >= 1, bright=True)
        for side in (-1, 1):
            x = xs[0] - 14 if side < 0 else xs[-1] + 14
            br = [(x, 0, z - 1), (x, 0, z + 11), (x - 4 * side, 0, z + 11), (x - 4 * side, 0, z + 9.6), (x - 1.4 * side, 0, z + 9.6),
                  (x - 1.4 * side, 0, z + 0.4), (x - 4 * side, 0, z + 0.4), (x - 4 * side, 0, z - 1)]
            o.append(path([cam(p) for p in br], "#CDCDCD", 0.6, "#CDCDCD"))
    for _, _, g in sorted(items, key=lambda q: (-q[0], -q[1])):
        o += g
    hx = xs[head]
    o.append(path([cam(p) for p in [(hx - 14, 0, -11), (hx - 8, 0, -14), (hx + 8, 0, -14), (hx + 14, 0, -11), (hx + 8, 0, -8), (hx - 8, 0, -8)]],
                  "#CDCDCD", 1.2, "#000000"))
    if held is not None:
        lx, ly = cam((xs[-1] + 22, 0, (ROWS_SHOWN - 1) * DZ * (1 - recall) + 5))
        o.append(text(lx, ly + 3, "held", 10, "#AFAFAF"))
    return o, header(("steps", "pulses", "cycles", "division"), (str(steps), str(pulses), str(cycles), {1.0: "1/16", 1.4: "1/8", 0.75: "1/32"}.get(division, "1/16")))


# ---- M2 repeats and phrase ----------------------------------------------------------------------------------------------
def m2(repeats=3, time=1.0, voices=3, rng=1.0, head=4, step=None, on=None, last=None):
    """the bar's pulses in a row, heights following the phrase; only the pulse sounding (or the last one) throws its
    repeats, as an echo train running back into the distance: spacing by time and pace, each slice lower and hollow"""
    cam = Cam(el=36, d=430, focal=480, target=(0.0, 10.0, 40.0), screen=(240.0, 120.0))
    pulses = sorted(on) if on is not None else [0, 3, 6, 10, 13]
    dx = 22.0
    o, items = [], []
    o.append(cam.line((-8.5 * dx, 0, 5), (8.5 * dx, 0, 5), 0x4B, 1.0))
    src = step if step is not None and step >= 0 else last
    for s in pulses:
        x = (s - 7.5) * dx
        h = 16 + 22 * rng * (0.5 + 0.5 * math.sin(2 * math.pi * s / 16))      # the phrase
        lh = (h - 2.0 * (voices - 1)) / voices
        g = []
        for v in range(voices):                                        # voicing: the chord's notes as layers
            g += solid(cam, x - 6, x + 6, lh, 0, 12, 0, lit=(s == step), y0=v * (lh + 2.0))
        items.append((0, abs(x), g))
        if s == src:                                                   # the echo train, back into the distance
            z, gap = 20.0, 22.0 * time
            for r in range(1, repeats + 1):
                rh = max(3.0, h * (1 - 0.18 * r))
                items.append((z, abs(x), hollow(cam, x - 6, x + 6, rh, z, z + 8, min(r - 1, 3))))
                z += 8 + gap
                gap *= 0.75                                            # accelerating pace
    for _, _, g in sorted(items, key=lambda q: (-q[0], -q[1])):
        o += g
    return o, header(("repeats", "time", "voicing", "range"), (str(repeats), {1.0: "1/32", 1.8: "1/16", 0.6: "1/64"}.get(time, "1/32"), f"{voices} up", "sine"))


# ---- M3 groove: a bar seen from the front, time running left to right ------------------------------------------------------
def m3(velocity=0.8, sustain=0.5, accent=1.0, swing=0.58, head=5, on=None):
    """the bar as a lane: grid ticks mark the straight 16ths; each pulse is a slab whose height is its velocity and
    whose length along the lane is its sustain (the gate), slid off its tick by swing; accents get a cap; an
    uncertain pulse (probability) is hollow"""
    cam = Cam(el=30, d=520, focal=560, target=(0.0, 14.0, 6.0), screen=(240.0, 128.0))
    prof = [1.0, 0.5, 0.6, 0.8, 0.5, 0.9, 0.5, 0.6, 1.0, 0.7, 0.5, 0.85, 0.6, 0.5, 0.95, 0.75]
    on = on if on is not None else {0, 2, 3, 5, 6, 8, 9, 11, 12, 14, 15}
    tmpl = [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0]
    prob = {6, 12}
    dx = 21.0
    x0 = -8 * dx
    o, items = [], []
    o.append(cam.line((x0, 0, 0), (x0 + 16 * dx, 0, 0), 0x4B, 1.0))    # the lane's front edge
    o.append(cam.line((x0, 0, 12), (x0 + 16 * dx, 0, 12), 0x32, 1.0))  # and its back edge
    for s in range(17):                                                # grid: the straight 16ths
        x = x0 + s * dx
        o.append(cam.line((x, 0, -3), (x, 0, 0), 0x64 if s % 4 == 0 else 0x4B, 1.0))
    for s in sorted(on):
        x = x0 + s * dx + (dx * (swing - 0.5) * 2 if s % 2 else 0)      # swing slides the off-beats
        lift = 1 + 0.35 * accent * tmpl[s]
        h = 3 + 34 * velocity * prof[s] * lift
        length = max(3.0, dx * (0.15 + 0.85 * sustain))                # the gate, along the lane
        lit = s == head
        g = hollow(cam, x, x + length, h, 1, 11) if s in prob else solid(cam, x, x + length, h, 1, 11, 0, lit)
        if tmpl[s] and accent > 0.05 and s not in prob:
            g += solid(cam, x - 1, x + length + 1, 1.8, 0, 12, 0, True, y0=h + 1.2)
        items.append((abs(x + length / 2), g))
    for _, g in sorted(items, key=lambda q: -q[0]):
        o += g
    return o, header(("velocity", "sustain", "accent", "timing"), (str(round(127 * velocity)), {0.5: "1/2", 0.15: "1/8", 1.0: "1x"}.get(round(sustain, 2), "1/2"), "agogo", f"{round(swing * 100)}%"))


# ---- M4 tonal: keys ------------------------------------------------------------------------------------------------------
WHITE = [0, 2, 4, 5, 7, 9, 11]
BLACK_LEFT = {1: 1, 3: 2, 6: 4, 8: 5, 10: 6}
SCALES = {"major": {0, 2, 4, 5, 7, 9, 11}, "minor": {0, 2, 3, 5, 7, 8, 10}, "penta": {0, 2, 4, 7, 9}, "chrom": set(range(12))}


def m4(root=6, scale="major", channel=3, random_amt=0.25, played=()):
    o = []
    kx, ky, ww, wh, bw, bh = 100.0, 74.0, 20.0, 80.0, 12.0, 50.0
    jit = lambda n: random_amt * 14 * math.sin(n * 2.3 + 1.1)
    for black in (False, True):
        for n in range(24):
            octv, pc = divmod(n, 12)
            if (pc in BLACK_LEFT) != black:
                continue
            if black:
                x, w, h = kx + (octv * 7 + BLACK_LEFT[pc]) * ww - bw / 2, bw, bh
                fill = "#4B4B4B"
            else:
                x, w, h = kx + (octv * 7 + WHITE.index(pc)) * ww, ww, wh
                fill = "#000000"
            if n in played:
                fill = "#AFAFAF"
            o.append(path([(x, ky), (x + w, ky), (x + w, ky + h), (x, ky + h)], G(0x7D), 1.0, fill))
    for n in range(24):
        rel = (n - root) % 12
        if rel not in SCALES[scale]:
            continue
        octv, pc = divmod(n, 12)
        if pc in BLACK_LEFT:
            cx, cy = kx + (octv * 7 + BLACK_LEFT[pc]) * ww, ky + bh - 9
        else:
            cx, cy = kx + (octv * 7 + WHITE.index(pc)) * ww + ww / 2, ky + wh - 12
        cy += jit(n)
        r = 4.2 if rel == 0 else 3.0
        o.append(path([(cx + r * math.cos(2 * math.pi * k / 16), cy + r * math.sin(2 * math.pi * k / 16)) for k in range(16)],
                      "#CDCDCD", 0.6, "#CDCDCD"))
        if rel == 0:                                                   # the root: brightest dot, plus one under the key
            o.append(path([(cx - 3, ky + wh + 6), (cx + 3, ky + wh + 6), (cx, ky + wh + 11)], "#CDCDCD", 0.6, "#CDCDCD"))
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    return o, header(("pitch", "scale", "channel", "random"), (names[root], scale, f"ch {channel}", f"{round(random_amt * 100)}%"))


def frame(body, head):
    return "\n".join(['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
                      '<rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>'] + body + head + ["</svg>"])


def render(name, built):
    svg = OUT / f"{name}.svg"
    svg.write_text(frame(*built))
    subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(svg), "-o", str(OUT / f"{name}.png")], check=True)
    return Image.open(OUT / f"{name}.png")


def main():
    OUT.mkdir(exist_ok=True)
    ims = [render("m1", m1()), render("m2", m2()), render("m3", m3()), render("m4", m4())]
    sheet = Image.new("RGB", (960, 2 * 230), "#1A1A1A")
    for k, im in enumerate(ims):
        sheet.paste(im, (480 * (k % 2), 230 * (k // 2)))
    sheet.save(OUT / "pages.png")
    print("wrote clean/pages.png")


if __name__ == "__main__":
    main()
