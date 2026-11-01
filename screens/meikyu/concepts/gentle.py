#!/usr/bin/env python3
"""meikyu o2 corona, gentle motion: the corona page as Brian picked it, with three slow movements.

After the orbit-motion version, Brian's direction: keep the planets where they were and the sun as it was, and
let the motion be gentle. So:
  planets  stay on their sixteen orbits; a step turning on or off fades its planet between wireframe and solid
           (~0.35 s), instead of switching
  trails   the dashes behind each planet flow slowly along its orbit toward it, brightening as they arrive, so the
           planets read as travelling while they hold still; inner orbits flow faster, as real orbits do
  sun      the corona's rays drift slowly round the sun and breathe a few pixels; no flares
  phrase   the ringed planet's segments fade in for the tones that sounded and fade out after the phrase

Device note. This is a design target, not something today's player page can draw: a player page has 24 dots that
are on or off and static art that never moves. Fades need a level per dot (or a pair of dots per planet), and the
flowing trails and drifting corona need nodes the player can move. Either the player page ABI grows (dot levels
and a few bound nodes, like a synth's display) or the motion stays in preview. See README.md.

    python3 gentle.py <tmpdir>      → gentle.mp4, gentle-stills.png
"""
from __future__ import annotations

import math
import random
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

import orbits as O
import planets_av as A
import suns as S

HERE = Path(__file__).resolve().parent
path, ell = O.path, O.ell
SX, SY, SR = S.SX, S.SY, S.SR
FADE_STEP, FADE_TONE = 0.35, 0.25                  # seconds: planet fade, ring segment fade
DASHES, DASH_SPAN = 4, 0.42                        # trail dashes per orbit and the arc they cover behind the planet (rad)
CORONA_TURN, BREATH = 0.035, 3.0                   # rad/s the rays drift; px they breathe


def grey(level, lo=0x00, hi=0xBE):
    v = round(lo + (hi - lo) * max(0.0, min(1.0, level)))
    return f"#{v:02X}{v:02X}{v:02X}"


def faded_sphere(cx, cy, r, level):
    """a planet between wireframe (0) and solid (1): the disc fills in and the lines brighten a little"""
    n = min(60, max(16, int(r * 2)))
    o = [path(ell(cx, cy, r, r, n=n), "#000000", 0.5, fill="#000000", close=True)]
    if level > 0.02:
        o.append(path(ell(cx, cy, r, r, n=n), grey(level), 0.5, fill=grey(level), close=True))
    # lines go from mid grey on black to a darker grey on the filled disc, so they read at both ends of the fade
    return o + O.wire_sphere(cx, cy, r, grey(0.64 - 0.25 * level, hi=0xBE), 0.8)


def trails(t):
    """each orbit: dim behind, a little brighter ahead, and dashes flowing toward the planet"""
    o = []
    for rx, ry, a, r, i in S.layout():
        n = (i % 8) * 2 + (0 if i < 8 else 1)
        o.append(path(ell(SX, SY, rx, ry, -0.9, a - DASH_SPAN - 0.02, 14), "#222222", 0.8))
        o.append(path(ell(SX, SY, rx, ry, a + r / rx, a + 0.62, 12), "#3C3C3C", 0.9))
        speed = 0.55 * (300 / rx) ** 1.5                      # Kepler-ish: inner orbits flow faster (dashes per second)
        phase = (t * speed + n * 0.37) % 1.0
        stop = a - r / rx * 0.7
        for d in range(DASHES):
            u = (d + phase) / DASHES                          # 0 at the tail, 1 at the planet
            a1 = stop - DASH_SPAN * (1 - u)
            a0 = a1 - DASH_SPAN / DASHES * 0.55
            if a1 <= stop - DASH_SPAN or a0 >= stop:
                continue
            level = u * u                                     # dim at the tail, bright arriving
            o.append(path(ell(SX, SY, rx, ry, max(a0, stop - DASH_SPAN), min(a1, stop), 5), grey(0.15 + 0.4 * level, hi=0xC8), 0.8 + 1.4 * u))
    return o


def corona(t):
    o = []
    rnd = random.Random(5)
    spin = t * CORONA_TURN
    for k in range(36):
        a = -math.pi / 2 + 2 * math.pi * k / 36 + spin
        if math.cos(a) < -0.2:
            continue
        L = SR + 8 + (22 if k % 3 == 0 else 12 if k % 3 == 1 else 6) + rnd.random() * 4
        L += BREATH * math.sin(t * 1.1 + k * 0.9)
        o.append(path([(SX + (SR + 5) * math.cos(a), SY + (SR + 5) * math.sin(a)), (SX + L * math.cos(a), SY + L * math.sin(a))],
                      "#A4A4A4" if k % 3 == 0 else "#6E6E6E", 1.2 if k % 3 == 0 else 0.9))
    o.append(path(ell(SX, SY, SR, SR, n=60), "#A4A4A4", 1.4, fill="#000000", close=True))
    return o + O.wire_sphere(SX, SY, SR, "#8A8A8A", 0.8)


def ringed(levels, cx=424, cy=178, r=14, ring=(1.5, 2.3), tilt=0.3):
    o = []
    r0, r1 = r * ring[0], r * ring[1]
    order = [3, 2, 1, 0, 7, 6, 5, 4]
    segs = []
    for k in range(8):
        a0 = math.pi * k / 4 + 0.05
        a1 = a0 + math.pi / 4 - 0.1
        segs.append((order.index(k), ell(cx, cy, r1, r1 * tilt, a0, a1, 8) + ell(cx, cy, r0, r0 * tilt, a1, a0, 8), (a0 + a1) / 2))
    for front in (False, True):
        if front:
            o += faded_sphere(cx, cy, r, 0.0)
        for tone, pts, mid in segs:
            if (math.sin(mid) >= 0) != front:
                continue
            o.append(path(pts, "#3C3C3C", 0.8, close=True))
            if levels[tone] > 0.02:
                c = grey(levels[tone], hi=0xF0)
                o.append(path(pts, c, 0.5, fill=c, close=True))
    return o


def art(t, step_levels, tone_levels):
    o = trails(t) + corona(t)
    for rx, ry, a, r, i in sorted(S.layout(), key=lambda q: SY + q[1] * math.sin(q[2])):
        o += faded_sphere(SX + rx * math.cos(a), SY + ry * math.sin(a), r, step_levels[i])
    return o + ringed(tone_levels)


def levels(events):
    """ease every planet and ring segment toward its on/off target, frame by frame"""
    n = int(A.LENGTH * A.FPS)
    dt = 1 / A.FPS
    steps, tones = [0.0] * 16, [0.0] * 8
    out = []
    presses = [et for et, _ in events]
    for i in range(n):
        t = i * dt
        p = A.page_at(t, events)
        lp = max((x for x in presses if x <= t), default=None)
        for s in range(16):
            target = 1.0 if p.step_lit(s) else 0.0
            steps[s] += (target - steps[s]) * (1 - math.exp(-dt / FADE_STEP))
        for k in range(8):                                      # a tone fades in at its step and out after the phrase
            on = lp is not None and p.tone_lit(k) and k * A.STEP <= t - lp < 8 * A.STEP + 0.2
            tones[k] += ((1.0 if on else 0.0) - tones[k]) * (1 - math.exp(-dt / FADE_TONE))
        out.append((p, list(steps), list(tones)))
    return out


def main():
    tmp = Path(sys.argv[1])
    tmp.mkdir(parents=True, exist_ok=True)
    events, tones = A.run()
    wav = HERE / "planets.wav"
    if not wav.exists():
        A.sound(wav, tones)
    lv = levels(events)

    def render(i):
        p, sl, tl = lv[i]
        svg = tmp / f"f{i:04d}.svg"
        svg.write_text(S.frame(p, art(i / A.FPS, sl, tl)))
        subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(svg), "-o", str(tmp / f"f{i:04d}.png")], check=True)
        if i != 300:
            svg.unlink()

    with ThreadPoolExecutor(8) as ex:
        list(ex.map(render, range(len(lv))))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(A.FPS), "-i", str(tmp / "f%04d.png"), "-i", str(wav),
                    "-vf", "scale=960:440:flags=neighbor", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", str(HERE / "gentle.mp4")], check=True)
    ims = [Image.open(tmp / f"f{i:04d}.png") for i in (30, 45, 60, 300, 360, 480)]
    sheet = Image.new("RGB", (960, 660))
    for k, im in enumerate(ims):
        sheet.paste(im, (480 * (k % 2), 220 * (k // 2)))
    sheet.save(HERE / "gentle-stills.png")
    print("wrote gentle.mp4")


if __name__ == "__main__":
    main()
