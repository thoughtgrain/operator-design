#!/usr/bin/env python3
"""ariadne, round 2: the loom (Brian's pick from round 1), modelled in 3D and animated with sound.

Ariadne is a function track: its keys are functions (ratchet, thin, mutate, random…) acting on a target track. Its
screen weaves the target track's sequence as cloth:

  warp          16 threads running back from the front edge, one per step of the target track
  a pass        each time the target's pattern plays through, a new row is woven at the front edge and the cloth
                moves back one row; six rows show, the oldest at the back, fading
  a note        a float: a slab raised on its warp thread, height by pitch
  locked step   solid: it plays as written, so it's the same slab row after row and forms a column down the cloth
  generated     hollow (wireframe): a function rewrites it each pass, so it changes row to row, or drops out
  p-lock        a pin on the slab with a bead per locked parameter (up to three)
  playhead      the shuttle: it runs along the front edge under the step playing; steps behind it are woven, steps
                ahead show dim outlines of what's coming (the last pass's value)
  functions     ratchet ×N splits a step's slab into N slices; thin drops steps to their footprints
  controls      targ swaps the cloth for another track's; amt is how many steps are generated (hollow) vs locked
                (solid); rate is how often a function fires (the reed: tick marks under the front edge); hold
                mom/latch (the shuttle's tail: open or pinned)

Built as a scene (warp along x, passes along z, height along y) projected through one camera; slabs are boxes drawn
back to front, so nearer slabs hide farther ones and the cloth's depth is real.

    python3 loom.py <tmpdir>      → loom.mp4, loom-stills.png
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
sys.path.insert(0, str(HERE.parents[1] / "meikyu" / "concepts"))
import orbits as O                       # noqa: E402
import pages as P                        # noqa: E402
import planets_av as A                   # noqa: E402

path, ell = O.path, O.ell
STOCK = [0x32, 0x4B, 0x64, 0x7D, 0x96, 0xAF, 0xCD]


def G(v):
    v = min(STOCK, key=lambda s: abs(s - round(v)))
    return f"#{v:02X}{v:02X}{v:02X}"


# ---- camera ------------------------------------------------------------------------------------------------------------
CAM_EL, CAM_D, F = math.radians(44), 620.0, 760.0
TARGET = (0.0, 0.0, 46.0)
SCREEN = (240.0, 128.0)


def project(p):
    x, y, z = p[0] - TARGET[0], p[1] - TARGET[1], p[2] - TARGET[2]
    ce, se = math.cos(CAM_EL), math.sin(CAM_EL)
    yc = y * ce + z * se                                               # camera in front (-z), above, looking down
    zc = z * ce - y * se + CAM_D
    k = F / zc
    return SCREEN[0] + x * k, SCREEN[1] - yc * k, zc


def P2(p):
    return project(p)[:2]


# ---- the cloth ---------------------------------------------------------------------------------------------------------
STEPS, ROWS = 16, 6
DX, DZ = 19.0, 20.0                                                    # warp spacing, row spacing (world)
SW, SD = 11.0, 11.0                                                    # slab width (x) and depth (z)
H0, HP = 3.0, 1.15                                                     # slab height: base + per semitone
STEP_T = A.STEP                                                        # 1/16 at 120 bpm
PASS_T = STEPS * STEP_T


def warp_x(s):
    return (s - (STEPS - 1) / 2) * DX


TRACKS = {                                                             # two target tracks: (pitch or None, p-locks)
    "T3": [(5, 0), (None, 0), (8, 2), (3, 0), (None, 0), (7, 1), (5, 0), (None, 0),
           (10, 0), (2, 0), (None, 0), (6, 3), (None, 0), (9, 0), (4, 0), (None, 0)],
    "T5": [(0, 0), (0, 0), (None, 0), (7, 1), (0, 0), (None, 0), (12, 0), (0, 2),
           (0, 0), (None, 0), (5, 0), (0, 0), (3, 1), (None, 0), (0, 0), (10, 0)],
}
GEN_ORDER = {k: [s for s in random.Random(11 + i).sample(range(STEPS), STEPS) if TRACKS[k][s][0] is not None]
             for i, k in enumerate(TRACKS)}                            # which steps go generated first as amt rises

# ---- the score ---------------------------------------------------------------------------------------------------------
LENGTH = 26.0


def controls(t):
    c = {"targ": "T3", "amt": 25, "rate": "1/16", "hold": "mom", "fn": None}
    if 4 <= t < 10:
        c["amt"] = round(25 + 60 * min(1.0, (t - 4) / 4))
    elif 10 <= t < 22:
        c["amt"] = 85
    if t >= 22:
        c["amt"] = 40
    if 8.5 <= t < 12.5:
        c["fn"] = ("ratchet", 3)
    if 14.5 <= t < 18.5:
        c["fn"] = ("thin", 0.45)
    if t >= 18.5:
        c["targ"] = "T5"
    if t >= 20.5:
        c["hold"] = "latch"
    return c


def pass_of(t):
    return int(max(0.0, t) // PASS_T)


_ROWS = {}


def row(j):
    """what pass j wove: per step (pitch or None, p-locks, generated?, ratchet n, thinned?), from the controls at the
    time that step played"""
    if j in _ROWS:
        return _ROWS[j]
    out = []
    rnd = random.Random(1000 + j)
    for s in range(STEPS):
        t = j * PASS_T + s * STEP_T
        c = controls(t)
        base = TRACKS[c["targ"]][s]
        order = GEN_ORDER[c["targ"]]
        gen = s in order[:round(len(order) * c["amt"] / 100)]
        pitch, locks = base
        if gen:
            pitch = None if rnd.random() < 0.25 else rnd.randint(0, 12)
            locks = 0
        rat, thin = 1, False
        fn = c["fn"]
        if fn and pitch is not None:
            if fn[0] == "ratchet":
                rat = fn[1]
            elif fn[0] == "thin" and rnd.random() < fn[1]:
                thin = True
        out.append((pitch, locks, gen, rat, thin, c["targ"]))
    _ROWS[j] = out
    return out


def tones():
    out = []
    for j in range(pass_of(LENGTH) + 1):
        for s, (pitch, locks, gen, rat, thin, _) in enumerate(row(j)):
            t = j * PASS_T + s * STEP_T
            if pitch is None or thin or t >= LENGTH:
                continue
            for r in range(rat):
                tt = t + r * STEP_T / rat
                out.append((tt, tt + 0.08, 48 + pitch, 70 + 8 * locks if r == 0 else 55))
    return out


# ---- drawing -----------------------------------------------------------------------------------------------------------
def box(x0, x1, y0, y1, z0, z1, fills, stroke, w):
    """a box's visible faces from this camera: top, front, and the side facing the camera's x"""
    top = [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)]
    front = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)]
    cx = (x0 + x1) / 2
    side = [(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)] if cx < 0 else \
           [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)]
    o = []
    for face, fill in ((side, fills[2]), (front, fills[1]), (top, fills[0])):
        o.append(path([P2(p) for p in face], stroke, w, fill=fill, close=True))
    return o


def slab(x, z, h, kind, age, lit=False, rat=1):
    """kind: solid | hollow | preview | footprint. age 0 = the row being woven; older rows step down in grey"""
    dim = 0x18 * age
    if kind == "footprint":
        return [path([P2((x - SW / 2, 0, z)), P2((x + SW / 2, 0, z)), P2((x + SW / 2, 0, z + SD)), P2((x - SW / 2, 0, z + SD))],
                     G(0x64 - dim), 0.9, fill="#000000", close=True)]
    o = []
    gap = 1.6
    sw = (SW - gap * (rat - 1)) / rat
    for r in range(rat):
        x0 = x - SW / 2 + r * (sw + gap)
        if kind == "solid":
            top = 0xCD if lit else 0xAF - dim
            fills = (G(top), G(0x7D - dim), G(0x64 - dim))
            o += box(x0, x0 + sw, 0, h, z, z + SD, fills, G(0x32), 0.5)
        elif kind == "hollow":
            o += box(x0, x0 + sw, 0, h, z, z + SD, ("#CDCDCD" if lit else "#000000", "#000000", "#000000"),
                     G(0xCD if lit else 0xAF - dim), 1.0)
        else:                                                          # preview: what's coming, a dim outline
            o += box(x0, x0 + sw, 0, h, z, z + SD, ("#000000",) * 3, G(0x4B), 0.8)
    return o


def pins(x, z, h, n, age):
    o = []
    if n == 0:
        return o
    cx, cz = x, z + SD / 2
    top = h + 4 + 4.5 * n
    o.append(path([P2((cx, h, cz)), P2((cx, top, cz))], G(0xAF - 0x18 * age), 1.4))
    for b in range(n):
        y = h + 6 + 4.5 * b
        px, py = P2((cx, y, cz))
        r = 2.4 * F / project((cx, y, cz))[2]
        o.append(path(ell(px, py, r, r, n=12), G(0xCD - 0x18 * age), 0.8, fill=G(0xCD - 0x18 * age), close=True))
    return o


def ease(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def scene(t):
    c = controls(t)
    cur = pass_of(t)
    in_pass = t - cur * PASS_T
    head = int(in_pass // STEP_T)
    slide = 1 - ease(in_pass / 0.25)                                    # the cloth moves back one row as a pass begins
    o = []
    z_back = (ROWS + 0.5) * DZ
    for s in range(STEPS):                                             # warp threads on the ground
        x = warp_x(s)
        o.append(path([P2((x, 0, -6)), P2((x, 0, z_back))], G(0x32), 1.0))
    items = []
    for age in range(ROWS - 1, -1, -1):
        j = cur - age
        if j < 0:
            continue
        z = (age - slide) * DZ if age > 0 else 0.0
        rw = row(j)
        if age > 0 and rw[0][5] != c["targ"]:
            continue                                                   # another track's cloth: not this one's history
        o.append(path([P2((warp_x(0) - 10, 0, z + SD / 2)), P2((warp_x(STEPS - 1) + 10, 0, z + SD / 2))],
                      G(0x4B if age == 0 else 0x32), 1.0))             # the weft
        for s in range(STEPS):
            pitch, locks, gen, rat, thin, _ = rw[s]
            x = warp_x(s)
            if age == 0 and s > head:                                  # not woven yet: last pass's value, dim
                prev = row(j - 1)[s] if j > 0 else rw[s]
                if prev[0] is not None and prev[5] == c["targ"]:
                    items.append((z, x, slab(x, z, H0 + HP * prev[0], "preview", 0)))
                continue
            if pitch is None:
                continue
            h = H0 + HP * pitch
            kind = "footprint" if thin else ("hollow" if gen else "solid")
            lit = age == 0 and s == head and not thin
            g = slab(x, z, h, kind, min(age, 4), lit, rat)
            if not gen and not thin:
                g += pins(x, z, h, locks, min(age, 4))
            items.append((z, x, g))
    for z, x, g in sorted(items, key=lambda q: (-q[0], -abs(q[1]))):   # back to front, outside in
        o += g
    # the reed: ticks under the front edge, one per function tick at this rate
    every = {"1/8": 2, "1/16": 1, "1/32": 0.5}[c["rate"]]
    for s in range(STEPS):
        if s % max(1, int(every)) == 0:
            x = warp_x(s)
            o.append(path([P2((x, 0, -9)), P2((x, 0, -13))], G(0x64), 1.0))
    # the shuttle, under the step playing
    hx = warp_x(head)
    sh = [(hx - 16, 0, -11), (hx - 9, 0, -14), (hx + 9, 0, -14), (hx + 16, 0, -11), (hx + 9, 0, -8), (hx - 9, 0, -8)]
    o.append(path([P2(p) for p in sh], "#CDCDCD", 1.2, fill="#000000" if c["hold"] == "mom" else "#CDCDCD", close=True))
    return o


def header(c):
    p = P.Page(density=c["amt"] / 100, scale=0, corrupt=0.2, drum=False)
    o = P.header(p)
    labels = {"Dens": "targ", "Scal": "amt", "Crpt": "rate", "Drum": "hold"}
    vals = [(str(round(c["amt"])), c["targ"]), ("minor", str(round(c["amt"]))), ("20", c["rate"]), ("off", c["hold"])]
    out = []
    for line in o:
        for a, b in labels.items():
            line = line.replace(f">{a}<", f">{b}<")
        out.append(line)
    done = [False] * 4
    res = []
    for line in out:
        for k, (a, b) in enumerate(vals):
            if not done[k] and f">{a}<" in line and "17.4" in line:
                line = line.replace(f">{a}<", f">{b}<")
                done[k] = True
                break
        res.append(line)
    return res


def frame(t):
    return "\n".join(['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
                      '<rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>'] + scene(t) + header(controls(t)) + ["</svg>"])


def main():
    tmp = Path(sys.argv[1])
    tmp.mkdir(parents=True, exist_ok=True)
    A.LENGTH = LENGTH
    wav = tmp / "loom.wav"
    A.sound(wav, tones())
    n = int(LENGTH * A.FPS)
    keep = {int(tt * A.FPS) for tt in (3.1, 7.1, 11.1, 16.1, 19.6, 24.1)}

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
                    "-c:a", "aac", "-b:a", "192k", "-shortest", str(HERE / "loom.mp4")], check=True)
    ims = [Image.open(tmp / f"f{k:04d}.png") for k in sorted(keep)]
    sheet = Image.new("RGB", (960, 660))
    for k, im in enumerate(ims):
        sheet.paste(im, (480 * (k % 2), 220 * (k // 2)))
    sheet.save(HERE / "loom-stills.png")
    print("wrote loom.mp4")


if __name__ == "__main__":
    main()
