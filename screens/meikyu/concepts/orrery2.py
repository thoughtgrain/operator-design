#!/usr/bin/env python3
"""meikyu o2 corona, round 2 of the moving orrery: eight spinning planets and an asteroid belt.

Brian's notes on stopmotion.py: too many planets, so they touch; space them out, vary their sizes more; and put an
asteroid field near the centre, between planets, made of wire rocks that light up as needed, some rolling front to
back, tumbling to fill the space. So:

  planets   the register's A half: eight planets on eight orbits (two inside the belt, six outside), sizes from
            tiny to large. They share one cycle with phases chosen by search so no two ever touch, and none touches
            the ringed planet. Each spins: two front meridians step round a quarter turn through four pre-drawn
            variants of the same one-path wireframe (one shown at a time). A planet fills while its step plays.
  belt      the B half: 24 wire rocks in three lanes between the inner and outer planets, three rocks per step,
            each filling while its step plays. Rocks tumble through three rotated variants. The outer and inner
            lanes roll front to back, the middle lane back to front, all hopping like the planets.
  sun       the corona as picked, static, drawn over everything so planets and rocks pass behind it
  phrase    the ringed planet as before; its segments light for the tones that sounded

Node cost if the player page gets bound nodes (see README.md): planets 8 × 4 variants, rocks 24 × 3, ring 8:
112 nodes. Hops are staggered; a hop redraws a node pair (hide one variant, show the next).

    python3 orrery2.py <tmpdir>      → orrery2.mp4, orrery2-stills.png
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
HOP = 0.75                                   # seconds between hops
CYCLE = 64.0                                 # seconds for a planet to cross its path (same for all: spacing holds)
ROCK_CYCLE = 40.0
WIRE = ("#000000", "#7A7A7A")
FILLED = ("#BEBEBE", "#4A4A4A")
ROCK_WIRE = ("#000000", "#6E6E6E")
ROCK_FILLED = ("#D0D0D0", "#5A5A5A")
GAP = 4.0                                    # px kept clear between any two bodies

# eight planets: (orbit rx, radius px). Two inside the belt, six outside; sizes deliberately uneven.
PLANETS = [(92, 6.0), (124, 11.0), (246, 19.0), (286, 8.0), (326, 14.0), (364, 5.5), (402, 17.0), (442, 9.5)]
LANES = [(160, 1), (180, -1), (200, 1)]      # belt lanes: rx and direction (1: back to front, -1: front to back)
ROCKS_PER_LANE = 8
RING = (446, 200, 26)                        # the ringed planet's centre and reach, an obstacle (bottom-right corner)


def f(v):
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def ry_of(rx):
    return rx * 0.24


# ---- shapes: each one path ≤ 64 points, loops all clockwise so a nonzero fill covers the body --------------------------
def planet_glyph(spin: int, r=10.0):
    """outline, two front meridians 90° apart turned by spin × 22.5°, and the front equator, as one path"""
    def arc(a0, a1, n):
        return [(r * math.sin(a0 + (a1 - a0) * k / n), -r * math.cos(a0 + (a1 - a0) * k / n)) for k in range(1, n + 1)]
    pts = [(0.0, -r)] + arc(0, 2 * math.pi, 16)                                   # outline, clockwise from the top
    for phi in (math.radians(22.5 * spin), math.radians(22.5 * spin - 90)):
        s = math.sin(phi)
        pts += [(r * s * math.cos(th), r * math.sin(th)) for th in
                [-math.pi / 2 + math.pi * k / 7 for k in range(1, 8)]]             # meridian, top → bottom (front half)
        pts += arc(math.pi, 2 * math.pi, 8)                                       # left side, bottom → top
    pts += arc(0, math.pi / 2, 4)                                                 # top → right
    pts += [(r * math.cos(math.pi * k / 7), 0.3 * r * math.sin(math.pi * k / 7)) for k in range(1, 8)]   # equator → left
    pts += arc(3 * math.pi / 2, 2 * math.pi, 4)                                   # left → top
    assert len(pts) <= 64, len(pts)
    return pts


def rock_glyph(seed: int, turn: int, r=10.0):
    rnd = random.Random(seed)
    radii = [r * rnd.uniform(0.62, 1.0) for _ in range(8)]
    rot = turn * 2 * math.pi / 3 / 8 * 3 + seed
    pts = [(radii[k] * math.sin(rot + 2 * math.pi * k / 8), -radii[k] * math.cos(rot + 2 * math.pi * k / 8)) for k in range(8)]
    # a facet line across the rock so it reads as a solid with a near face, not a flat blob
    return pts + [pts[0], pts[3], pts[0]]


def node(pts, x, y, s, fill, line, w=1.0):
    d = "M" + " L".join(f"{f(px)},{f(py)}" for px, py in pts)
    return (f'<path transform="matrix({f(s)} 0 0 {f(s)} {f(x)} {f(y)})" d="{d}" fill="{fill}" stroke="{line}" '
            f'stroke-width="{f(w / s)}" stroke-linejoin="round" stroke-linecap="round"/>')


# ---- paths --------------------------------------------------------------------------------------------------------------
def depth_scale(a):
    return 0.7 + 0.3 * (math.sin(a) + 1) / 2


def hidden(x, y, r):
    return math.hypot(x - SX, y - SY) + r <= SR or y + r <= 20 or y - r >= 220 or x + r <= 0


def visible_arc(rx, r):
    ends = []
    for sign in (-1, 1):
        a = 0.0
        while abs(a) < math.pi:
            a += sign * 0.005
            if hidden(SX + rx * math.cos(a), SY + ry_of(rx) * math.sin(a), r * depth_scale(a)):
                break
        ends.append(a)
    lo, hi = ends
    margin = (hi - lo) * 0.05
    return lo - margin, hi + margin                       # a little past both ends: the wrap happens out of sight


ARCS = [visible_arc(rx, r) for rx, r in PLANETS]


def planet_at(k, u):
    """planet k at path fraction u (0 entering, 1 leaving): (x, y, radius, angle)"""
    rx, r = PLANETS[k]
    lo, hi = ARCS[k]
    a = lo + (hi - lo) * (u % 1.0)
    return SX + rx * math.cos(a), SY + ry_of(rx) * math.sin(a), r * depth_scale(a), a


def clearance(phases, samples=240):
    """the closest any two visible planets (or a planet and the ringed planet) come, over a whole cycle"""
    worst = 1e9
    for s in range(samples):
        u = s / samples
        bodies = []
        for k, ph in enumerate(phases):
            x, y, r, a = planet_at(k, u + ph)
            if not hidden(x, y, r):
                bodies.append((x, y, r))
        for i in range(len(bodies)):
            x, y, r = bodies[i]
            worst = min(worst, math.hypot(x - RING[0], y - RING[1]) - r - RING[2])
            for j in range(i + 1, len(bodies)):
                x2, y2, r2 = bodies[j]
                worst = min(worst, math.hypot(x - x2, y - y2) - r - r2)
    return worst


def choose_phases(tries=3000):
    rnd = random.Random(11)
    best, best_c = None, -1e9
    for _ in range(tries):
        ph = [rnd.random() for _ in PLANETS]
        c = clearance(ph, 60)
        if c > best_c:
            best, best_c = ph, c
    return best, clearance(best)


PHASES, CLEAR = choose_phases()


def rocks():
    """(lane, index, seed, size, step) for every rock"""
    out = []
    rnd = random.Random(23)
    for lane in range(len(LANES)):
        for j in range(ROCKS_PER_LANE):
            n = lane * ROCKS_PER_LANE + j
            out.append((lane, j, 100 + n, rnd.uniform(3.4, 6.2), 8 + (n * 3) % 8))
    return out


ROCKS = rocks()
LANE_ARCS = [visible_arc(rx, 4) for rx, _ in LANES]


def stagger(n):
    return (n * 0.37) % 1.0 * HOP


# ---- the scene ----------------------------------------------------------------------------------------------------------
def scene(p, t):
    o = []
    for rx, _ in PLANETS:                                                    # orbits: far half dim, near half a little brighter
        o.append(path(ell(SX, SY, rx, ry_of(rx), math.pi, 2 * math.pi, 40), "#1C1C1C", 0.8))
        o.append(path(ell(SX, SY, rx, ry_of(rx), 0, math.pi, 40), "#2E2E2E", 0.9))
    bodies = []
    for k, (rx, r) in enumerate(PLANETS):
        hops = math.floor((t + stagger(k)) / HOP)
        x, y, rr, a = planet_at(k, PHASES[k] + hops * HOP / CYCLE)
        lit = p.step_lit(k)
        fill, line = FILLED if lit else WIRE
        bodies.append((y, node(planet_glyph(hops % 4), x, y, rr / 10, fill, line, 0.9)))
    for lane, j, seed, size, step in ROCKS:
        rx, direction = LANES[lane]
        lo, hi = LANE_ARCS[lane]
        n = lane * ROCKS_PER_LANE + j
        hops = math.floor((t + stagger(n + 8)) / HOP)
        u = (j / ROCKS_PER_LANE + direction * hops * HOP / ROCK_CYCLE + lane * 0.13) % 1.0
        a = lo + (hi - lo) * u
        x, y = SX + rx * math.cos(a), SY + ry_of(rx) * math.sin(a)
        s = size * depth_scale(a) / 10
        fill, line = ROCK_FILLED if p.step_lit(step) else ROCK_WIRE
        bodies.append((y, node(rock_glyph(seed, hops % 3), x, y, s, fill, line, 0.8)))
    o += [svg for _, svg in sorted(bodies, key=lambda b: b[0])]
    o += S.sun_corona()                                                      # the corona sun as picked, over the bodies
    return o + O.ringed(RING[0], RING[1], 12, p, ring=(1.5, 2.3), tilt=0.3)


def main():
    tmp = Path(sys.argv[1])
    tmp.mkdir(parents=True, exist_ok=True)
    print(f"planet clearance over a cycle: {CLEAR:.1f} px (need ≥ {GAP})")
    assert CLEAR >= GAP, "planets would touch; widen the orbits or shrink the planets"
    events, tones = A.run()
    wav = HERE / "planets.wav"
    if not wav.exists():
        A.sound(wav, tones)
    n = int(A.LENGTH * A.FPS)

    def render(i):
        t = i / A.FPS
        p = A.page_at(t, events)
        svg = tmp / f"f{i:04d}.svg"
        svg.write_text(S.frame(p, scene(p, t)))
        subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(svg), "-o", str(tmp / f"f{i:04d}.png")], check=True)
        if i != 300:
            svg.unlink()

    with ThreadPoolExecutor(8) as ex:
        list(ex.map(render, range(n)))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(A.FPS), "-i", str(tmp / "f%04d.png"), "-i", str(wav),
                    "-vf", "scale=960:440:flags=neighbor", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", str(HERE / "orrery2.mp4")], check=True)
    ims = [Image.open(tmp / f"f{i:04d}.png") for i in (30, 150, 300, 420, 600, 870)]
    sheet = Image.new("RGB", (960, 660))
    for k, im in enumerate(ims):
        sheet.paste(im, (480 * (k % 2), 220 * (k // 2)))
    sheet.save(HERE / "orrery2-stills.png")
    print("wrote orrery2.mp4")


if __name__ == "__main__":
    main()
