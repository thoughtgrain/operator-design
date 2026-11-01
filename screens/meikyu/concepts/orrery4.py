#!/usr/bin/env python3
"""meikyu orrery, every control on screen: the 3D orrery (orrery3) with each parameter given a visible job, plus
beams that follow the sound from step to step.

Brian's direction after reading what each control did: lines should move to where the sound is going, Scal, Drum
and velocity all need a visible effect, and with Drum on, Scal should mean something else. So:

  beams     between triggers a comet travels from the previous sounding step's planet to the next, along the orbits
            (radius and angle round the sun, the short way, lifted slightly), so a phrase's path steps outward in order;
            steps that don't play are skipped,
            arriving exactly on the trigger; its tail grades dark to bright and it fades in leaving and out landing,
            with a ring opening at the target. On the device: three graded mutable outlines plus the ring.
  Dens      which steps play: their planets fill (normal mode) and their rocks fill
  Crpt      rewrites steps after each phrase, so fills change between phrases; and it jostles the belt every hop
  Scal      normal mode: spreads the orbits and the asteroid belt with them, pentatonic tightest → minor → major →
            chromatic widest (eased)
            drum mode: Scal becomes Kit (kit 1–4): it picks the pad set and spreads the asteroid belt instead
  Drum      on: the belt rises out of the orbit plane (it's the kit now), planets stop filling, and each hit makes its
            step's rocks jump up and fall back. Off: the belt settles back down and planets fill again.
  velocity  how far the ring planet's lit segments reach: soft presses short, hard presses long
  a press   the ring segments light for the tones that sounded; the text line names root, half and phrase count;
            Pluto (small, on its own tilted outermost orbit) is the sixteenth step's planet

The sound comes from a port of meikyu's press() with one proposed change: in drum mode Scal selects one of four pad
sets (KITS) instead of being ignored. That needs the same change in labyrinth's player.cpp.

    python3 orrery4.py <tmpdir>      → orrery4.mp4, orrery4-stills.png
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
import orrery2 as R2
import orrery3 as M3
import pages as P
import planets_av as A
import suns as S

HERE = Path(__file__).resolve().parent
path = O.path
LENGTH = 44.0
STEP = A.STEP
SPREAD = {2: 0.86, 0: 0.93, 1: 1.0, 3: 1.07}      # Scal → orbit spread: pentatonic, minor, major, chromatic
                                                    # (planet sizes scale with it, so spacing scales instead of closing)
BELT_SPREAD = [0.85, 1.0, 1.15, 1.3]               # Kit → belt spread (drum mode)
KITS = [[0, 5, 7, 12, 17, 24, 31, 36],             # kit 1: meikyu's own pads
        [0, 3, 7, 10, 12, 15, 19, 24],             # kit 2: tighter, minor-ish toms
        [0, 7, 12, 19, 24, 31, 36, 43],            # kit 3: wide, fifths and octaves
        [0, 1, 6, 7, 12, 13, 18, 19]]              # kit 4: clangy semitone pairs
EASE = 0.35                                         # seconds for spreads to settle
PULSE = 0.26                                        # seconds a struck rock's bounce lasts
BOUNCE_UP = 16.0                                    # world units a struck rock jumps
DRUM_LIFT = 10.0                                    # world units the whole belt rises while Drum is on
TAIL, LAND = 0.7, 0.22                              # comet tail (fraction of the path); seconds it takes to land


# ---- the score ------------------------------------------------------------------------------------------------------------
def controls(t):
    c = {"dens": 60, "crpt": 20, "scal": 0, "drum": False}
    if 5 <= t < 11:                                 # Dens 60 → 100 → 15 → 60
        u = (t - 5) / 6
        c["dens"] = round(60 + 40 * math.sin(math.pi * u / 0.5) if u < 0.25 else 100 - 85 * (u - 0.25) / 0.5 if u < 0.75 else 15 + 45 * (u - 0.75) / 0.25)
    if 11 <= t < 16:
        c["crpt"] = 85
    for t0, s in ((16, 2), (18, 0), (20, 1), (22, 3)):   # Scal: pent → minor → major → chrom
        if t >= t0:
            c["scal"] = s
    if 24 <= t < 34:                                # Drum on, kits 1 → 4
        c["drum"] = True
        c["scal"] = min(3, int((t - 24) / 2.5))
    if t >= 34:
        c["scal"] = 0                               # drum off, back to minor
        if t >= 39:
            c["scal"] = 1
    return c


ROOTS = [50, 50, 53, 45, 50, 57, 53, 48]
VELS = [40, 96, 64, 124, 80, 112, 52, 100]


class Player(A.Meikyu):
    def press(self, c, note, velocity):
        """meikyu's press(), with the proposed drum-mode change: Scal picks the pad set"""
        density, corrupt, mask, drum = c["dens"], c["crpt"], A.MASKS[c["scal"]], c["drum"]
        pads = KITS[c["scal"]]
        rng_ = 3 + (velocity * 13) // 128
        start, tones, sounded = self.head, [], 0
        for k in range(8):
            i = (start + k) % 16
            if self.plays(i, density):
                deg = (self.val[i] * rng_) // 15
                pitch = note + pads[(deg >> 1) & 7] if drum else self.scale_note(note, mask, deg)
                if 0 <= pitch <= 127:
                    acc = self.wt[i] < density // 4
                    tones.append((k, i, pitch, min(127, velocity + 27) if acc else velocity))
                    sounded |= 1 << k
            if corrupt and self.pct() < corrupt:
                self.roll(i)
        self.head = (start + 8) % 16
        self.phrases = (self.phrases + 1) % 256
        self.last_root, self.last_start, self.last_mask = note, start, sounded
        return tones


def run():
    m = Player()
    presses, tones = [], []
    t, n = 0.5, 0
    while t < LENGTH - 1.0:
        c = controls(t)
        note, vel = ROOTS[n % 8], VELS[n % 8]
        plan = m.press(c, note, vel)
        presses.append(dict(t=t, wt=list(m.wt), mask=m.last_mask, root=note, start=m.last_start, count=m.phrases, vel=vel,
                            hits=[(t + k * STEP, i) for k, i, _, _ in plan]))
        for k, i, pitch, v in plan:
            tones.append((t + k * STEP, t + k * STEP + A.GATE, pitch, v))
        t += 8 * STEP
        n += 1
    return presses, tones


# ---- state at time t ------------------------------------------------------------------------------------------------------
def eased(t, fn):
    """an exponential ease toward fn(t) (sampled backwards), for spreads"""
    v, dt = None, 1 / 30
    for k in range(int(3 * EASE * 30), -1, -1):
        target = fn(t - k * dt)
        v = target if v is None else v + (target - v) * (1 - math.exp(-dt / EASE))
    return v


def page_at(t, presses):
    c = controls(t)
    p = P.Page(density=c["dens"] / 100, scale=c["scal"], corrupt=c["crpt"] / 100, drum=c["drum"])
    last = None
    for pr in presses:
        if pr["t"] <= t:
            last = pr
    if last:
        p.weights = list(last["wt"])
        p.phrase, p.root, p.start, p.count = last["mask"], last["root"], last["start"], last["count"]
    else:
        p.weights = list(Player().wt)
    return p, last


def header(p):
    """the stock header; with Drum on, Scal reads as the kit"""
    o = P.header(p)
    if p.drum:
        o = [line.replace(f">{P.SCALES[p.scale]}<", f">kit {p.scale + 1}<").replace(">Scal<", ">Kit<") for line in o]
    return o


# ---- scene ----------------------------------------------------------------------------------------------------------------
def planet_pos(k, t, spread):
    r = M3.body_radius(k)
    hops = math.floor((t + M3.stagger(k)) / M3.HOP)
    a = 2 * math.pi * ((M3.PHASES[k] + hops * M3.HOP / M3.PERIOD) % 1.0)
    p3 = M3.body_point(k, a, spread)
    x, y, z, ppu = M3.project(p3)
    return x, y, r * spread * ppu, p3, hops


def scene(p, last, t, presses):
    c = controls(t)
    spread = eased(t, lambda tt: 1.0 if controls(tt)["drum"] else SPREAD[controls(tt)["scal"]])
    belt = eased(t, lambda tt: BELT_SPREAD[controls(tt)["scal"]] if controls(tt)["drum"] else 1.0)
    lift = eased(t, lambda tt: DRUM_LIFT if controls(tt)["drum"] else 0.0)    # the belt rises when it becomes the kit
    back, front = [], []
    orbit_lines = [M3.orbit_segments(rho * spread) for rho in M3.ORBIT_RADII]
    for runs in orbit_lines:                                         # orbit lines, split near/far of the sun
        for is_front, pts in runs:
            (front if is_front else back).append((1e9, path(pts, "#3E3E3E" if is_front else "#1E1E1E", 0.9 if is_front else 0.8)))
    pos = {}
    phrase_on = last is not None and t - last["t"] < 8 * STEP
    for k in range(len(M3.PLANETS)):                                  # sixteen step planets (Pluto is step 7)
        x, y, rr, p3, hops = planet_pos(k, t, spread)
        pos[k] = p3                                                  # world position: comets travel in 3D
        lit = p.step_lit(k) and not c["drum"]                        # Pluto (k = 15) carries the sixteenth step
        fill, line = R2.FILLED if lit else R2.WIRE
        svg = R2.node(M3.GLYPHS[k][hops % M3.SPINS], x, y, rr / 10, fill, line, 0.9)
        (front if M3.nearer_than_sun(p3) else back).append((math.dist(M3.CAM, p3), svg))
    struck = {}                                                      # drum mode: step → seconds since its hit
    if c["drum"] and last:
        for th, i in last["hits"]:
            if 0 <= t - th < PULSE:
                struck[i] = t - th
    mid = (M3.BELT[0] + M3.BELT[1]) / 2
    for n, (seed, rho, h, phase, direction, size, step) in enumerate(M3.ROCKS):
        hops = math.floor((t + M3.stagger(n + 8)) / M3.HOP)
        a = 2 * math.pi * ((phase + direction * hops * M3.HOP / M3.ROCK_PERIOD) % 1.0)
        jr = random.Random(seed * 7919 + hops)
        k = M3.JOSTLE * p.corrupt
        rr_ = (mid + (rho - mid) * belt) * spread                    # the belt scales out with the orbits (Scal), plus the kit spread in drum mode
        hop_up = BOUNCE_UP * math.sin(math.pi * struck[step] / PULSE) if step in struck else 0.0   # a hit: up and back down
        p3 = M3.orbit_point(rr_ + jr.uniform(-k, k), a + jr.uniform(-k, k) / rho,
                            h * belt + lift + hop_up + jr.uniform(-k, k) * 0.5)
        x, y, z, ppu = M3.project(p3)
        s = size * ppu / 10
        if step in struck:
            fill, line = ("#F0F0F0", "#8A8A8A")
        else:
            fill, line = R2.ROCK_FILLED if p.step_lit(step) else R2.ROCK_WIRE
        turn = (hops % 2) * 1.5 if size >= M3.TUMBLE_MIN else 0      # small rocks don't tumble: one node each
        svg = R2.node(R2.rock_glyph(seed, turn), x, y, s, fill, line, 0.8)
        (front if M3.nearer_than_sun(p3) else back).append((math.dist(M3.CAM, p3), svg))
    o = [svg for _, svg in sorted(back, key=lambda q: -q[0])]
    o += S.sun_corona()
    o += [svg for _, svg in sorted(front, key=lambda q: -q[0])]
    o += beams(t, presses, pos)
    reach = 1.8 + 1.4 * ((last["vel"] if last else 64) / 127)        # velocity → how far the ring's segments reach
    return o + O.ringed(M3.RING[0], M3.RING[1], 12, p, ring=(1.45, reach), tilt=0.3)


def beams(t, presses, pos):
    """lines that follow the sound: between consecutive hits, a comet travels a curved path from the previous hit's
    planet to this one, leaving as the previous tone sounds and arriving exactly as this one does. Its tail runs
    dark to bright toward the head, and the whole comet fades in as it leaves and out as it arrives. On the device
    it's three graded mutable outlines plus the landing ring: four paths."""
    hits = []
    for pr in presses:
        hits += pr["hits"]
    o = []
    for (t0, i0), (t1, i1) in zip(hits, hits[1:]):
        if t1 - t0 > 0.6 or not (t0 <= t <= t1 + LAND):
            continue
        # the path follows the orbits: radius and angle round the sun are interpolated in the world (the short way
        # round), with a gentle lift out of the plane, then projected, so a comet curves round the sun from one
        # planet to the next instead of cutting across the screen
        p0, p1 = pos[i0], pos[i1]
        r0, r1 = math.hypot(p0[0], p0[2]), math.hypot(p1[0], p1[2])
        a0, a1 = math.atan2(-p0[2], p0[0]), math.atan2(-p1[2], p1[0])
        da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        lift = 10.0 + 0.08 * abs(r1 - r0)

        def at(u):
            r, a = r0 + (r1 - r0) * u, a0 + da * u
            x, y, _, _ = M3.project(M3.orbit_point(r, a, lift * math.sin(math.pi * u)))
            return x, y
        x1, y1 = at(1.0)

        head = min(1.0, (t - t0) / max(1e-3, t1 - t0))
        landed = max(0.0, t - t1) / LAND                            # 0..1 after arrival: the tail draws into the target
        tail = max(0.0, head - TAIL) + landed * TAIL
        fade = min(1.0, head / 0.3) * (1.0 - landed)
        if head - tail > 0.01 and fade > 0.02:
            for g in range(3):                                      # three graded pieces, dim tail → bright head
                u0 = tail + (head - tail) * g / 3
                u1 = tail + (head - tail) * (g + 1) / 3
                level = fade * (0.35 + 0.65 * (g + 1) / 3)
                v = round(0x30 + (0xF0 - 0x30) * level)
                o.append(path([at(u0 + (u1 - u0) * k / 6) for k in range(7)], f"#{v:02X}{v:02X}{v:02X}", 1.0 + 0.8 * g))
        if 0 <= t - t1 < LAND:                                      # the landing: a ring opening round the target
            age = (t - t1) / LAND
            v = round(0x40 + (0xF0 - 0x40) * (1 - age))
            o.append(path(M3_ring(x1, y1, 4 + 9 * age), f"#{v:02X}{v:02X}{v:02X}", 0.9, close=True))
    return o


def M3_ring(x, y, r):
    return [(x + r * math.cos(2 * math.pi * k / 20), y + r * math.sin(2 * math.pi * k / 20)) for k in range(20)]


def frame(p, body):
    line = f'<text transform="matrix(1 0 0 1 240 {S.TEXT_Y})" fill="#F2F2F2" font-family="UniversNextPro-Light" font-size="16px" text-anchor="middle">{p.line()}</text>'
    return "\n".join(['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
                      '<rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>'] + body + [line] + header(p) + ["</svg>"])


def main():
    tmp = Path(sys.argv[1])
    tmp.mkdir(parents=True, exist_ok=True)
    presses, tones = run()
    A.LENGTH = LENGTH
    wav = HERE / "orrery4.wav"
    A.sound(wav, tones)
    n = int(LENGTH * A.FPS)

    def render(i):
        t = i / A.FPS
        p, last = page_at(t, presses)
        svg = tmp / f"f{i:04d}.svg"
        svg.write_text(frame(p, scene(p, last, t, presses)))
        subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(svg), "-o", str(tmp / f"f{i:04d}.png")], check=True)
        if i not in (100, 760):
            svg.unlink()

    with ThreadPoolExecutor(8) as ex:
        list(ex.map(render, range(n)))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(A.FPS), "-i", str(tmp / "f%04d.png"), "-i", str(wav),
                    "-vf", "scale=960:440:flags=neighbor", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", str(HERE / "orrery4.mp4")], check=True)
    picks = (100, 250, 500, 620, 760, 1080)                          # defaults, dens, scal pent, scal chrom, drum kit 1, drum off
    ims = [Image.open(tmp / f"f{i:04d}.png") for i in picks]
    sheet = Image.new("RGB", (960, 660))
    for k, im in enumerate(ims):
        sheet.paste(im, (480 * (k % 2), 220 * (k // 2)))
    sheet.save(HERE / "orrery4-stills.png")
    print("wrote orrery4.mp4")


if __name__ == "__main__":
    main()
