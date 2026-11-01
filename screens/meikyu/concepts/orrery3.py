#!/usr/bin/env python3
"""meikyu o2 corona, modelled in 3D: a sun, planets on circular orbits, an asteroid ring, one perspective camera.

Brian's note on orrery2: the orbits didn't follow the sun's curve and they bunched up near it, because they were 2D
ellipses bent by hand. So this one is built as a scene and projected, nothing drawn in screen space:

  world     the sun is a sphere of radius R at the origin. Orbits are circles in the ecliptic plane (y = 0) at even
            radii, so they stay evenly spaced all the way round; nothing can pinch near the sun.
  camera    one perspective camera 12° above the ecliptic and a little to the right, far enough back for gentle
            perspective. 12° is what lets the outermost orbit fit the screen's height. The projection is fitted so the
            sun lands where the corona page put it: half off the left edge, 62 px radius. Because the sun sits on the
            edge and every orbit circles it, about half of each orbit is always off screen; that's geometry, not a bug.
  depth     every body's distance from the camera decides its order: anything nearer than the sun's centre is drawn
            after the sun (in front of it), anything further before it, so the sun's black disc covers what's behind
            it. Orbit lines are split the same way, so their near arcs cross in front of the sun and their far arcs
            go behind it: they wrap round it because they really go round it.
  size      planet and rock sizes come from their distance to the camera.
  motion    every planet takes the same period, so the arrangement turns as one and the phases chosen to keep planets
            apart on screen hold for all time. Hops every HOP s; a planet's spin and a rock's tumble step per hop.
  planets   sixteen, two per orbit on roughly opposite sides; planet k carries register step k
  belt      90 rocks scattered through a 3D ring (radius and height), each tied to a step (n mod 16); Crpt jostles them
            in 3D. Two tumble variants per rock (half turns) keep the device budget at 16×4 + 90×2 + 8 = 252 nodes.

    python3 orrery3.py <tmpdir>      → orrery3.mp4, orrery3-stills.png, orrery3-sun.png
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
import planets_av as A
import suns as S

HERE = Path(__file__).resolve().parent
path = O.path
SUN_R = 60.0                                     # world units
SUN_SCREEN = (6.0, 116.0, 62.0)                  # where the sun must land: centre x, y and radius in px
HOP, PERIOD = 0.75, 120.0
GAP = 4.0
# eight planets: (orbit radius, planet radius) in world units, four inside the belt and four outside
ORBIT_RADII = [92, 128, 162, 198, 300, 340, 380, 414]       # four inside the belt, four outside
# sixteen planets, two per orbit on roughly opposite sides: (orbit radius, planet radius); planet k carries step k
# the inner four orbits carry one small or medium planet each; the outer four carry three each, a small, a medium and
# a large spaced a third of an orbit apart, so the weight sits outside the belt and the right side stays full
_SIZES = {92: [4.0], 128: [6.5], 162: [5.0], 198: [8.0],
          300: [4.0, 8.0, 12.0], 340: [9.0, 4.5, 13.5], 380: [13.0, 5.0, 8.5], 414: [8.0, 14.5, 4.0]}
PLANETS = [(rho, r) for rho in ORBIT_RADII for r in _SIZES[rho]]                 # sixteen; planet k carries step k
SLOTS = [(i, len(_SIZES[rho])) for rho in ORBIT_RADII for i in range(len(_SIZES[rho]))]
# Pluto: small, on its own outermost orbit, tilted out of the plane and reaching the right edge. The real tilt is
# 17°, but at that angle its path can't avoid touching other planets on screen; 8° is the steepest that stays clear.
PLUTO = dict(r=3.5, a=428.0, e=0.05, incl=math.radians(8))
BELT = (225, 275, 9.0)                           # inner and outer radius, half thickness
N_ROCKS, JOSTLE = 90, 6.0
CAM_AZ, CAM_EL, CAM_D = 350.0, 12.0, 2400.0      # camera: azimuth round the sun (0 = +x), height angle, distance
CAM = (CAM_D * math.cos(math.radians(CAM_EL)) * math.cos(math.radians(CAM_AZ)), CAM_D * math.sin(math.radians(CAM_EL)),
       -CAM_D * math.cos(math.radians(CAM_EL)) * math.sin(math.radians(CAM_AZ)))
LOOK = (0.0, 0.0, 0.0)
RING = (446, 200, 26)                            # the ringed phrase planet (screen px), kept as before


# ---- camera ---------------------------------------------------------------------------------------------------------------
def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    n = math.sqrt(dot(a, a))
    return (a[0] / n, a[1] / n, a[2] / n)


FWD = norm(sub(LOOK, CAM))
RIGHT = norm(cross((0, 1, 0), FWD))
UP = cross(FWD, RIGHT)


def camera_space(p):
    d = sub(p, CAM)
    return dot(d, RIGHT), dot(d, UP), dot(d, FWD)


def raw(p):
    x, y, z = camera_space(p)
    return x / z, -y / z, z


# fit: scale and offset so the sun's centre and radius land on SUN_SCREEN
_sx, _sy, _sz = raw((0, 0, 0))
_SCALE = SUN_SCREEN[2] / (SUN_R / _sz)
_OX, _OY = SUN_SCREEN[0] - _sx * _SCALE, SUN_SCREEN[1] - _sy * _SCALE
SUN_DIST = math.dist(CAM, (0.0, 0.0, 0.0))


def nearer_than_sun(p):
    """for two spheres (or a sphere and a line), painter's order by distance to the camera is exact: a body whose
    centre is nearer the camera than the sun's centre is drawn after the sun"""
    return math.dist(CAM, p) < SUN_DIST


def project(p):
    """world point → (screen x, screen y, depth, px per world unit at that depth)"""
    x, y, z = raw(p)
    return _OX + x * _SCALE, _OY + y * _SCALE, z, _SCALE / z


def orbit_point(rho, a, h=0.0):
    """a point on a circle of radius rho in the ecliptic, angle a (0 toward +x, increasing toward the camera side)"""
    return (rho * math.cos(a), h, -rho * math.sin(a))


def occluded(p):
    """behind the sun as seen from the camera"""
    d = sub(p, CAM)
    L = math.sqrt(dot(d, d))
    u = (d[0] / L, d[1] / L, d[2] / L)
    oc = sub(CAM, (0, 0, 0))
    b = dot(oc, u)
    c = dot(oc, oc) - SUN_R * SUN_R
    disc = b * b - c
    if disc < 0:
        return False
    t = -b - math.sqrt(disc)
    return 0 < t < L


# ---- scene ----------------------------------------------------------------------------------------------------------------
def on_screen(x, y, r):
    return x + r > 0 and x - r < 480 and y + r > 20 and y - r < 220


def pluto_point(a, scale=1.0):
    """Pluto's orbit: an ellipse with the sun at a focus, aphelion out toward the right of the screen (this camera's
    right is world +z), its near/far axis tilted out of the ecliptic by the inclination"""
    A_, e = PLUTO["a"] * scale, PLUTO["e"]
    b = A_ * math.sqrt(1 - e * e)
    across = A_ * math.cos(a) + A_ * e                                  # along the screen: aphelion (a = 0) right
    depth = b * math.sin(a)                                             # toward / away from the camera
    ci, si = math.cos(PLUTO["incl"]), math.sin(PLUTO["incl"])
    return (depth * ci, depth * si, across)


def body_point(k, a, scale=1.0):
    return pluto_point(a, scale) if k == len(PLANETS) else orbit_point(PLANETS[k][0] * scale, a)


def body_radius(k):
    return PLUTO["r"] if k == len(PLANETS) else PLANETS[k][1]


def planet_at(k, u):
    r = body_radius(k)
    a = 2 * math.pi * (u % 1.0)
    p = body_point(k, a)
    x, y, z, ppu = project(p)
    return x, y, r * ppu, z, p


def clearance(phases, samples=240):
    worst = 1e9
    for s in range(samples):
        u = s / samples
        bodies = []
        for k, ph in enumerate(phases):
            x, y, r, z, p = planet_at(k, u + ph)
            if on_screen(x, y, r) and not occluded(p):
                bodies.append((x, y, r))
        for i in range(len(bodies)):
            x, y, r = bodies[i]
            worst = min(worst, math.hypot(x - RING[0], y - RING[1]) - r - RING[2])
            for j in range(i + 1, len(bodies)):
                x2, y2, r2 = bodies[j]
                worst = min(worst, math.hypot(x - x2, y - y2) - r - r2)
    return worst


def right_fill(phases, samples=60):
    """on average, how many visible planets sit on the right half of the screen"""
    n = 0
    for s in range(samples):
        for k, ph in enumerate(phases):
            x, y, r, z, p = planet_at(k, s / samples + ph)
            n += on_screen(x, y, r) and not occluded(p) and x > 240
    return n / samples


def choose_phases(tries=4000):
    """keep every pair of planets at least GAP apart, and among arrangements that do, fill the right side most"""
    rnd = random.Random(11)
    best, best_score = None, -1e9
    for _ in range(tries):
        base = {rho: rnd.random() for rho in ORBIT_RADII}                # planets sharing an orbit are spread evenly
        ph = [(base[rho] + i / n + (rnd.uniform(-0.1, 0.1) if n > 1 else 0)) % 1.0
              for (rho, _), (i, n) in zip(PLANETS, SLOTS)] + [rnd.random()]   # + Pluto
        c = clearance(ph, 120)
        score = c - 100 if c < GAP + 0.5 else right_fill(ph)
        if score > best_score:
            best, best_score = ph, score
    return best, clearance(best)


def place_pluto(phases, steps=240):
    """with the others fixed, slide Pluto's starting point round its orbit to where it stays clearest of them"""
    best = max(((clearance(phases[:-1] + [k / steps], 480), k / steps) for k in range(steps)))
    return phases[:-1] + [best[1]]


PHASES, CLEAR = choose_phases()
PHASES = place_pluto(PHASES)
CLEAR = clearance(PHASES, 480)


def rocks():
    rnd = random.Random(23)
    out = []
    for n in range(N_ROCKS):
        rho = rnd.uniform(BELT[0], BELT[1])
        h = rnd.uniform(-BELT[2], BELT[2])
        roll = rnd.random()
        size = rnd.uniform(7.0, 10.5) if roll < 0.12 else rnd.uniform(4.5, 7.0) if roll < 0.4 else rnd.uniform(2.0, 4.5)
        out.append((100 + n, rho, h, rnd.random(), 1 if rnd.random() < 0.7 else -1, size, n % 16))
    return out


ROCKS = rocks()
ROCK_PERIOD = 90.0


def stagger(n):
    return (n * 0.37) % 1.0 * HOP


def orbit_segments(rho, n=96, point=None):
    """an orbit as projected polylines, split into runs that are nearer than the sun (front) or further (back),
    each ≤ 60 points"""
    pts = []
    for k in range(n + 1):
        p = point(2 * math.pi * k / n) if point else orbit_point(rho, 2 * math.pi * k / n)
        x, y, z, _ = project(p)
        pts.append((x, y, nearer_than_sun(p)))
    runs, cur, side = [], [], None
    for x, y, front in pts:
        if side is None or front == side:
            cur.append((x, y))
        else:
            runs.append((side, cur + [(x, y)]))
            cur = [(x, y)]
        side = front
        if len(cur) >= 60:
            runs.append((side, cur))
            cur = [(x, y)]
    if len(cur) > 1:
        runs.append((side, cur))
    return runs


ORBITS = [orbit_segments(rho) for rho in ORBIT_RADII] + [orbit_segments(0, 120, pluto_point)]
GLYPHS = {k: [R2.planet_glyph(s, r=10.0) for s in range(4)] for k in range(len(PLANETS) + 1)}


def scene(p, t):
    back, front = [], []                                         # (depth, svg); back drawn before the sun, front after
    for runs in ORBITS:
        for is_front, pts in runs:
            (front if is_front else back).append((1e9 if not is_front else 1e9, path(pts, "#3E3E3E" if is_front else "#1E1E1E", 0.9 if is_front else 0.8)))
    for k, (rho, r) in enumerate(PLANETS):
        hops = math.floor((t + stagger(k)) / HOP)
        x, y, rr, z, p3 = planet_at(k, PHASES[k] + hops * HOP / PERIOD)
        fill, line = R2.FILLED if p.step_lit(k) else R2.WIRE
        svg = R2.node(GLYPHS[k][hops % 4], x, y, rr / 10, fill, line, 0.9)
        (front if nearer_than_sun(p3) else back).append((math.dist(CAM, p3), svg))
    for n, (seed, rho, h, phase, direction, size, step) in enumerate(ROCKS):
        hops = math.floor((t + stagger(n + 8)) / HOP)
        a = 2 * math.pi * ((phase + direction * hops * HOP / ROCK_PERIOD) % 1.0)
        jr = random.Random(seed * 7919 + hops)
        k = JOSTLE * p.corrupt
        p3 = orbit_point(rho + jr.uniform(-k, k), a + jr.uniform(-k, k) / rho, h + jr.uniform(-k, k) * 0.5)
        x, y, z, ppu = project(p3)
        fill, line = R2.ROCK_FILLED if p.step_lit(step) else R2.ROCK_WIRE
        svg = R2.node(R2.rock_glyph(seed, (hops % 2) * 1.5), x, y, size * ppu / 10, fill, line, 0.8)   # two half-turn variants
        (front if nearer_than_sun(p3) else back).append((math.dist(CAM, p3), svg))
    o = [svg for _, svg in sorted(back, key=lambda q: -q[0])]          # far to near
    o += S.sun_corona()
    o += [svg for _, svg in sorted(front, key=lambda q: -q[0])]
    return o + O.ringed(RING[0], RING[1], 12, p, ring=(1.5, 2.3), tilt=0.3)


def main():
    tmp = Path(sys.argv[1])
    tmp.mkdir(parents=True, exist_ok=True)
    print(f"camera fit: {_SCALE:.1f} px/unit at unit depth; planet clearance {CLEAR:.1f} px")
    for rho, _ in PLANETS[::3] + PLANETS[-1:]:
        xs = [project(orbit_point(rho, 2 * math.pi * k / 72))[:2] for k in range(72)]
        print(f"orbit {rho}: x {min(x for x, _ in xs):.0f}..{max(x for x, _ in xs):.0f}  y {min(y for _, y in xs):.0f}..{max(y for _, y in xs):.0f}")
    events, tones = A.run()
    wav = HERE / "planets.wav"
    if not wav.exists():
        A.sound(wav, tones)
    n = int(A.LENGTH * A.FPS)

    def render(i):
        t = i / A.FPS
        pg = A.page_at(t, events)
        svg = tmp / f"f{i:04d}.svg"
        svg.write_text(S.frame(pg, scene(pg, t)))
        subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(svg), "-o", str(tmp / f"f{i:04d}.png")], check=True)
        if i != 300:
            svg.unlink()

    with ThreadPoolExecutor(8) as ex:
        list(ex.map(render, range(n)))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(A.FPS), "-i", str(tmp / "f%04d.png"), "-i", str(wav),
                    "-vf", "scale=960:440:flags=neighbor", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", str(HERE / "orrery3.mp4")], check=True)
    ims = [Image.open(tmp / f"f{i:04d}.png") for i in (30, 150, 300, 420, 600, 870)]
    sheet = Image.new("RGB", (960, 660))
    for k, im in enumerate(ims):
        sheet.paste(im, (480 * (k % 2), 220 * (k // 2)))
    sheet.save(HERE / "orrery3-stills.png")
    Image.open(tmp / "f0300.png").crop((0, 20, 220, 220)).resize((660, 600), Image.NEAREST).save(HERE / "orrery3-sun.png")
    print("wrote orrery3.mp4")


if __name__ == "__main__":
    main()
