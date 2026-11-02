#!/usr/bin/env python3
"""meikyu, black-hole version 2: no sun and no transition. It's a black hole from the start.

At low Dens it's a small hole with a couple of planets round it. As Dens rises the hole grows, the orbits widen with
it, and more planets arrive, inner orbits first, until the system fills the page. Turning Dens down runs it back.

  hole          black disc, photon ring, stacked-ring glow, two lensed arcs over the top; all of it scales with Dens
  orbits        six, each in its own fixed inclined plane (borrowed from blackhole.py); radius = hole size × a ratio,
                so the whole system grows together and never crowds the horizon
  planets       each has a Dens key, inner orbits first: it grows in from nothing as Dens passes its key and shrinks
                away when Dens drops below it. Step planets fill when their step plays and flash when it sounds
  links         as the orrery: along an orbit, in the direction of travel, fast in and slow out
  header        the stock header with Rthm; no text line

Geometry, glyphs, phases and the camera come from blackhole.py; the player port and header from orrery4.py.

    python3 blackhole2.py <tmpdir>      → blackhole2.mp4, blackhole2-stills.png
"""
from __future__ import annotations

import math
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

import blackhole as B
import orbits as O
import orrery2 as R2
import orrery4 as M4
import planets_av as A

HERE = Path(__file__).resolve().parent
path, ell, smooth = O.path, O.ell, B.smooth
CX, CY = B.CENTRE

# ---- Dens → hole size, orbit size, who's out ----------------------------------------------------------------------------
H_MIN, H_MAX = 12.0, 38.0                                             # horizon radius at Dens 0 and 100 (world units)
RATIO = [1.7 + 0.62 * o for o in range(len(B.ORBITS))]                 # orbit radius ÷ horizon radius, inner to outer
ARRIVE = 5.0                                                           # Dens units over which a planet grows in


def horizon(dens):
    return H_MIN + (H_MAX - H_MIN) * smooth(dens / 100) ** 0.9


def orbit_r(o, dens):
    return horizon(dens) * RATIO[o]


# each body's Dens key: inner orbits first, steps a little ahead of extras on the same orbit, so at low Dens there are
# a couple of step planets round the hole and the outer orbits fill last
_order = sorted(range(len(B.BODIES)), key=lambda k: (B.ORBIT_OF[k], B.STEP_OF[k] is None, B.SLOT_OF[k][0]))
KEY = {k: 2 + 92 * j / (len(_order) - 1) for j, k in enumerate(_order)}


def presence(k, dens):
    """0 (not out) … 1 (fully out)"""
    return smooth((dens - KEY[k]) / ARRIVE)


def eased_dens(t):
    return M4.eased(t, lambda tt: controls(tt)["dens"])


# ---- the hole -----------------------------------------------------------------------------------------------------------
GLOW = [(0.035, 0xD8, 2.2), (0.085, 0xA0, 2.4), (0.145, 0x6C, 2.6), (0.215, 0x44, 3.0), (0.3, 0x26, 3.6)]   # offset ÷ radius


def hole(h, t, flash=0.0):
    """glow rings (behind the disc), the lensed arcs, then the black disc with its photon ring"""
    rr = h * B.project((0.0, 0.0, 0.0))[3]
    breathe = 1.0 + 0.08 * math.sin(2 * math.pi * t / 4.0)
    out = []
    for d, g, w in reversed(GLOW):                                     # glow, outermost first; widths follow the size
        rad = rr * (1 + d * breathe)
        out.append(path(ell(CX, CY, rad, rad, n=60), f"#{g:02X}{g:02X}{g:02X}", w * (0.5 + 0.5 * h / H_MAX), close=True))
    for s, g in ((1.35, 0xC0), (1.7, 0x80)):                           # light bent up over the top
        for k, w in ((0.35, 2.4), (1.0, 1.0)):
            gg = round(0x10 + (g - 0x10) * k)
            out.append(path(ell(CX, CY, rr * s, rr * s * 0.95, math.pi * 1.04, math.pi * 1.96, 40), f"#{gg:02X}{gg:02X}{gg:02X}", w))
    out.append(path(ell(CX, CY, rr, rr, n=60), "#F0F0F0", 2.0, fill="#000000", close=True))
    return out


# ---- the scene ----------------------------------------------------------------------------------------------------------
def scene(p, last, t, presses):
    dens = eased_dens(t)
    h = horizon(dens)
    back, front = [], []
    for o in range(len(B.ORBITS)):                                    # orbit lines: an orbit shows once a planet is on it
        seen = max(presence(k, dens) for k in range(len(B.BODIES)) if B.ORBIT_OF[k] == o)
        if seen < 0.1:
            continue
        rho = orbit_r(o, dens)
        for front_half in (False, True):
            g = round(0x10 + ((0x3A if front_half else 0x1E) - 0x10) * seen)
            pts = [B.project(B.tilted_point(rho, (math.pi if front_half else 0) + math.pi * q / 60, 0.0, o))[:2] for q in range(61)]
            (front if front_half else back).append((1e9, path(pts, f"#{g:02X}{g:02X}{g:02X}", 0.9 if front_half else 0.8)))

    flashed = {i for th, i in (last["hits"] if last else []) if 0 <= t - th < M4.FLASH}
    pos, placed = {}, []
    scale = 0.55 + 0.45 * h / H_MAX                                    # planets grow with the system, a little
    for k in sorted(range(len(B.BODIES)), key=lambda k: B.STEP_OF[k] is None):
        here = presence(k, dens)
        if here < 0.05:
            continue
        o, step = B.ORBIT_OF[k], B.STEP_OF[k]
        hops = math.floor((t + (k * 0.37) % 1.0 * B.HOP) / B.HOP)
        a = 2 * math.pi * (B.PHASES[k] + hops * B.HOP / B.PERIOD)
        p3 = B.tilted_point(orbit_r(o, dens), a, 0.0, o)
        x, y, _, ppu = B.project(p3)
        rr = B.BODIES[k][1] * scale * here * ppu
        foot = rr * (2.0 if k in B.RINGED else 1.0)
        if step is None and any(math.hypot(x - x2, y - y2) - foot - f2 < 3 for x2, y2, f2 in placed):
            continue                                                   # extras step aside rather than touch
        placed.append((x, y, foot))
        if step is not None:
            pos[step] = (o, a)
        lit = step is not None and p.step_lit(step) and not p.drum
        fill, line = R2.FILLED if lit else R2.WIRE
        if step in flashed:
            fill, line = "#F0F0F0", "#7A7A7A"
        d = math.dist(B.CAM, p3)
        side = front if B.nearer_than_centre(p3) else back
        side.append((d, R2.node(B.GLYPHS[k][hops % len(B.GLYPHS[k])], x, y, rr / 10, fill, line, 0.9)))
        if k in B.RINGED:
            halves = B.ring_halves(p3, rr / ppu, line, *B.RINGED[k])
            side += [(d + 0.5, s) for s in halves["back"]] + [(d - 0.5, s) for s in halves["front"]]

    out = [s for _, s in sorted(back, key=lambda q: -q[0])]
    out += hole(h, t)
    out += [s for _, s in sorted(front, key=lambda q: -q[0])]
    out += links(t, presses, pos, dens, h)
    return out + O.ringed(446, 40, 12, p, ring=(1.45, 1.8 + 1.4 * ((last["vel"] if last else 64) / 127)), tilt=0.3)


def links(t, presses, pos, dens, h):
    """along an orbit from one played planet to the next, in the direction of travel; the stretch behind the hole hides"""
    lk = []
    for pr in presses:
        lk += [(t0, i0, t1, i1) for (t0, i0), (t1, i1) in zip(pr["hits"], pr["hits"][1:]) if t0 <= t]
    lk = [q for q in lk if q[1] in pos and q[3] in pos and pos[q[1]][0] == pos[q[3]][0]]
    hole_px = h * B.project((0.0, 0.0, 0.0))[3] + 1
    out = []
    for t0, i0, t1, i1 in lk[-M4.LINKS:]:
        age = t - t0
        if age > M4.CONNECT + M4.FADE:
            continue
        (o, a0), (_, a1) = pos[i0], pos[i1]
        da = (a1 - a0) % (2 * math.pi)
        reach = min(1.0, age / M4.CONNECT)
        fade = 1.0 if age < M4.CONNECT else 1.0 - (age - M4.CONNECT) / M4.FADE
        g = 0xF0 if fade > 0.66 else 0x8A if fade > 0.33 else 0x4A
        colour, w = f"#{g:02X}{g:02X}{g:02X}", 1.4 if g == 0xF0 else 1.1
        run = []
        for q in range(48):
            w3 = B.tilted_point(orbit_r(o, dens), a0 + da * reach * q / 47, 0.0, o)
            x, y = B.project(w3)[:2]
            if not B.nearer_than_centre(w3) and math.hypot(x - CX, y - CY) < hole_px:
                if len(run) > 1:
                    out.append(path(run, colour, w))
                run = []
            else:
                run.append((x, y))
        if len(run) > 1:
            out.append(path(run, colour, w))
    return out


# ---- the demo -----------------------------------------------------------------------------------------------------------
LENGTH = 32.0


def controls(t):
    c = {"dens": 8, "crpt": 20, "scal": 0, "drum": False}
    for t0, t1, v0, v1 in ((4, 20, 8, 100), (20, 24, 100, 100), (24, 29, 100, 30)):
        if t0 <= t < t1:
            c["dens"] = round(v0 + (v1 - v0) * (t - t0) / (t1 - t0))
    if t >= 29:
        c["dens"] = 30
    return c


def main():
    tmp = Path(sys.argv[1])
    tmp.mkdir(parents=True, exist_ok=True)
    M4.controls = controls
    M4.LENGTH = A.LENGTH = LENGTH
    presses, tones = M4.run()
    wav = tmp / "blackhole2.wav"
    A.sound(wav, tones)
    n = int(LENGTH * A.FPS)

    def render(i):
        t = i / A.FPS
        p, last = M4.page_at(t, presses)
        svg = tmp / f"f{i:04d}.svg"
        svg.write_text(B.frame(p, scene(p, last, t, presses)))
        subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(svg), "-o", str(tmp / f"f{i:04d}.png")], check=True)
        if i not in (90, 600):
            svg.unlink()

    with ThreadPoolExecutor(8) as ex:
        list(ex.map(render, range(n)))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(A.FPS), "-i", str(tmp / "f%04d.png"), "-i", str(wav),
                    "-vf", "scale=960:440:flags=neighbor", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", str(HERE / "blackhole2.mp4")], check=True)
    ims = [Image.open(tmp / f"f{int(tt * A.FPS):04d}.png") for tt in (3, 8, 12, 16, 22, 30)]
    sheet = Image.new("RGB", (960, 660))
    for k, im in enumerate(ims):
        sheet.paste(im, (480 * (k % 2), 220 * (k // 2)))
    sheet.save(HERE / "blackhole2-stills.png")
    print("wrote blackhole2.mp4")


if __name__ == "__main__":
    main()
