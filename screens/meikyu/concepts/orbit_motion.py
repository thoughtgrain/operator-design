#!/usr/bin/env python3
"""meikyu o2 corona, with real motion: planets that orbit and a sun that flares.

A player page only switches its 24 dots, but display() runs once per GUI frame, so it can keep a frame counter and
animate them (open-xy's ABI docs show machines holding file-scope statics). This page uses that:

  orbits   the 16 steps sit in 16 slots on two orbits (A: 8 outer slots, B: 8 inner), every slot a static wireframe
           sphere. display() rotates which step each slot shows, one slot per tick, so the solid planets (steps that
           play at the density) travel round. The inner orbit turns faster than the outer, as real orbits do. The
           register is a loop, so circulating it is also what it is.
  flare    the 8 phrase dots are the corona's long rays. When a phrase starts, ray k flares at tone k's step if that
           tone sounded, and the rays die back once the phrase is over: the sun pulses with every press.

Device sketch for display() (labyrinth meikyu/player.cpp), no change to press() or the sound:
    static u32 frame; ++frame;
    const u32 a = frame / kOuterFrames % 8, b = frame / kInnerFrames % 8;      // orbit offsets
    for slot in 0..7:  lit A slot if plays(s, (slot + 8 - a) % 8, density);  B slot likewise with b, steps 8..15
    rays: lit tone k while frame - s.phrase_frame is within [k, 8) steps of the phrase (needs the press's frame:
          display() can latch it when s.phrases changes)
The step length on the device would come from frames; this preview uses the score's 120 BPM.

    python3 orbit_motion.py <tmpdir>     → orbit-motion.mp4, plus orbit-stills.png
"""
from __future__ import annotations

import math
import random
import subprocess
import sys
from pathlib import Path

from PIL import Image

import orbits as O
import pages as P
import planets_av as A
import suns as S

HERE = Path(__file__).resolve().parent
path, ell, wire_sphere = O.path, O.ell, O.wire_sphere
SX, SY, SR = 6, 116, 62
OUTER, INNER = (335, 94), (190, 70)              # orbit radii
ARC = (-0.98, 0.98)                               # the visible part of each orbit, radians (0 = straight right)
OUTER_TICK, INNER_TICK = 0.42, 0.26               # seconds per slot: the inner orbit is faster
GHOST, WIRE_DIM, BODY, HOT, INK = "#2E2E2E", "#5A5A5A", "#BEBEBE", "#F0F0F0", "#000000"


def slots():
    """(x, y, r, orbit 0/1, slot 0..7); slot 0 at the top of the arc, rising angle runs down toward the viewer"""
    out = []
    for o, (rx, ry) in enumerate((OUTER, INNER)):
        for s in range(8):
            a = ARC[0] + (ARC[1] - ARC[0]) * (s + 0.5) / 8
            x, y = SX + rx * math.cos(a), SY + ry * math.sin(a)
            base = 12.5 if o == 0 else 10.0
            out.append((x, y, base * (0.7 + 0.3 * (math.sin(a) + 1) / 2), o, s))
    return out


def sun_and_rays(rays_lit):
    o = []
    rnd = random.Random(5)
    for k in range(36):                                               # the static corona (the short and mid rays)
        a = -math.pi / 2 + 2 * math.pi * k / 36
        if math.cos(a) < -0.2 or any(abs(a - fa) < 0.06 for fa in FLARES):
            continue
        L = SR + 8 + (12 if k % 3 == 1 else 6) + rnd.random() * 4
        o.append(path([(SX + (SR + 5) * math.cos(a), SY + (SR + 5) * math.sin(a)), (SX + L * math.cos(a), SY + L * math.sin(a))], "#6E6E6E", 0.9))
    flares = FLARES
    for k, a in enumerate(flares):                                    # the eight long rays: the phrase dots
        base = [(SX + (SR + 5) * math.cos(a - 0.03), SY + (SR + 5) * math.sin(a - 0.03)),
                (SX + (SR + 5) * math.cos(a + 0.03), SY + (SR + 5) * math.sin(a + 0.03))]
        tip = (SX + (SR + 46) * math.cos(a), SY + (SR + 46) * math.sin(a))
        stub = (SX + (SR + 22) * math.cos(a), SY + (SR + 22) * math.sin(a))
        o.append(path([base[0], stub, base[1]], "#8A8A8A", 1.0, close=True))     # at rest: a short ray
        if k in rays_lit:
            o.append(path([base[0], tip, base[1]], HOT, 0.8, fill=HOT, close=True))
    o.append(path(ell(SX, SY, SR, SR, n=60), "#A4A4A4", 1.4, fill=INK, close=True))
    o += wire_sphere(SX, SY, SR, "#8A8A8A", 0.8)
    return o


FLARES = [math.radians(-58 + 128 * k / 7) for k in range(8)]       # the eight long rays, top to bottom across the sun's face


def ray_angles_count():
    return len(FLARES)


def art(p, t, last_press_t):
    o = []
    for k in range(10):                                               # far, faint orbits for the o2 sweep
        rx = 120 + k * 36
        o.append(path(ell(SX, SY, rx, rx * 0.25, -1.1, 1.1, 30), "#1E1E1E", 0.8))
    for rx, ry in (OUTER, INNER):
        o.append(path(ell(SX, SY, rx, ry, -1.25, 1.25, 40), "#3C3C3C", 1.0))
    # the phrase as flares: ray k lights at tone k's step after the press, if it sounded, until the phrase ends
    rays = set()
    if last_press_t is not None and p.phrase is not None:
        since = t - last_press_t
        for k in range(8):
            if p.tone_lit(k) and k * A.STEP <= since < 8 * A.STEP + 0.15:
                rays.add(k)
    o += sun_and_rays(rays)
    off = (int(t / OUTER_TICK) % 8, int(t / INNER_TICK) % 8)
    for x, y, r, orb, s in sorted(slots(), key=lambda q: q[1]):
        step = (s - off[orb]) % 8 + 8 * orb
        o.append(path(ell(x, y, r, r, n=min(60, max(16, int(r * 2)))), INK, 0.5, fill=INK, close=True))
        if p.step_lit(step):
            o.append(path(ell(x, y, r, r, n=min(60, max(16, int(r * 2)))), BODY, 0.5, fill=BODY, close=True))
            o += wire_sphere(x, y, r)
        else:
            o += wire_sphere(x, y, r, WIRE_DIM, 0.7)
    return o


def frame(p, t, last_press_t):
    return S.frame(p, art(p, t, last_press_t))


def picture(out: Path, events):
    presses = [et for et, _ in events]
    cache = {}
    for i in range(int(A.LENGTH * A.FPS)):
        t = i / A.FPS
        p = A.page_at(t, events)
        lp = max((x for x in presses if x <= t), default=None)
        since = None if lp is None else t - lp
        rays = tuple(k for k in range(8) if since is not None and p.tone_lit(k) and k * A.STEP <= since < 8 * A.STEP + 0.15)
        key = (tuple(p.weights), p.phrase, p.root, p.count, round(p.density * 100), p.scale, round(p.corrupt * 100), p.drum,
               int(t / OUTER_TICK) % 8, int(t / INNER_TICK) % 8, rays)
        png = out / f"f{i:04d}.png"
        if key in cache:
            png.write_bytes(cache[key].read_bytes())
            continue
        svg = out / "t.svg"
        svg.write_text(frame(p, t, lp))
        subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(svg), "-o", str(png)], check=True)
        cache[key] = png


def main():
    tmp = Path(sys.argv[1])
    tmp.mkdir(parents=True, exist_ok=True)
    assert ray_angles_count() >= 8, "need eight flare positions"
    events, tones = A.run()
    wav = HERE / "planets.wav"
    if not wav.exists():
        A.sound(wav, tones)
    picture(tmp, events)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(A.FPS), "-i", str(tmp / "f%04d.png"), "-i", str(wav),
                    "-vf", "scale=960:440:flags=neighbor", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", str(HERE / "orbit-motion.mp4")], check=True)
    ims = [Image.open(tmp / f"f{i:04d}.png") for i in (30, 36, 42, 48, 245, 380)]
    sheet = Image.new("RGB", (960, 660))
    for k, im in enumerate(ims):
        sheet.paste(im, (480 * (k % 2), 220 * (k // 2)))
    sheet.save(HERE / "orbit-stills.png")
    print("wrote orbit-motion.mp4")


if __name__ == "__main__":
    main()
