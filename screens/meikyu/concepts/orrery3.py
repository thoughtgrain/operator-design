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
import os
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
DEPTH_CUE = 0.0                                  # extra powers of (sun depth / depth) on body sizes (0: true perspective)
GAP = 4.0
# eight planets: (orbit radius, planet radius) in world units, four inside the belt and four outside
ORBIT_RADII = [138, 198, 320, 380, 440]                      # two inside the belt, three outside (Pluto's on the last)
# sixteen planets, three or four to an orbit spaced evenly round it; steps are numbered orbit by orbit, from the inside
# out, going round each orbit in its direction of travel. A phrase's links run along an orbit from planet to planet;
# when the sequence moves on to the next orbit, no line crosses: that planet fills and the next link starts from it.
ORBIT_PLANETS = {138: [5.0, 8.0, 4.0], 198: [9.0, 4.5, 7.0], 320: [12.0, 5.0, 9.0], 380: [14.0, 6.0, 10.0],
                 440: [8.0, 3.5, 11.0, 5.0]}                       # 440's 3.5 is Pluto
# variant "no-belt" (MEIKYU_VARIANT=no-belt): no asteroids; a sixth orbit takes the belt's place, and the sixteen
# planets spread two to each inner orbit and three to each outer one
VARIANT = os.environ.get("MEIKYU_VARIANT", "")
if VARIANT == "no-belt":
    ORBIT_RADII = [130, 186, 252, 318, 380, 440]
    ORBIT_PLANETS = {130: [5.0, 8.0], 186: [9.0, 4.5], 252: [7.0, 12.0, 5.0], 318: [10.0, 4.5, 14.0],
                     380: [6.0, 13.0, 8.0], 440: [11.0, 3.5, 7.0]}  # 440's 3.5 is Pluto
BODIES = [(rho, r) for rho in ORBIT_RADII for r in ORBIT_PLANETS[rho]]
ORBIT_OF = [ORBIT_RADII.index(rho) for rho, _ in BODIES]
SLOT = [(i, len(ORBIT_PLANETS[rho])) for rho in ORBIT_RADII for i in range(len(ORBIT_PLANETS[rho]))]
PLANETS = list(BODIES)                           # planet k carries step k
BELT = (214, 288, 14.0)                          # inner and outer radius, half thickness: wide by default
N_ROCKS, JOSTLE = 76, 6.0
if VARIANT == "no-belt":
    N_ROCKS = 0
CAM_AZ, CAM_EL, CAM_D = 350.0, 12.0, 2400.0      # camera: azimuth round the sun (0 = +x), height angle, distance
CAM = (CAM_D * math.cos(math.radians(CAM_EL)) * math.cos(math.radians(CAM_AZ)), CAM_D * math.sin(math.radians(CAM_EL)),
       -CAM_D * math.cos(math.radians(CAM_EL)) * math.sin(math.radians(CAM_AZ)))
LOOK = (0.0, 0.0, 0.0)
RING = (446, 40, 26)                             # the ringed phrase planet (screen px), kept as before


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
    # sizes: the camera sits far back for gentle perspective, which leaves near and far bodies within ~10% of each
    # other. Positions stay true; only the depth-to-size relation is exaggerated (cubed) so depth reads in the sizes.
    return _OX + x * _SCALE, _OY + y * _SCALE, z, _SCALE / z * (_sz / z) ** DEPTH_CUE


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


def body_point(k, a, scale=1.0):
    return orbit_point(PLANETS[k][0] * scale, a)


def body_radius(k):
    return PLANETS[k][1]


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


def orbit_phases(bases):
    """every planet's starting point: its orbit's base angle plus its even slot round the orbit. Slots run backwards
    in angle so that, as the planets orbit, step k+1 is the next planet coming round in the direction of travel."""
    return [(bases[o] - i / n) % 1.0 for o, (i, n) in zip(ORBIT_OF, SLOT)]


def choose_phases(tries=4000):
    """one base angle per orbit, searched for the widest spacing between planets on neighbouring orbits"""
    rnd = random.Random(11)
    best, best_c = None, -1e9
    for _ in range(tries):
        ph = orbit_phases([rnd.random() for _ in ORBIT_RADII])
        c = clearance(ph, 90)
        if c > best_c:
            best, best_c = ph, c
    return best, clearance(best, 480)


PHASES, CLEAR = choose_phases()
PLUTO_STEP = next(k for k, (rho, r) in enumerate(PLANETS) if rho == 440 and r == 3.5)


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


ORBITS = [orbit_segments(rho) for rho in ORBIT_RADII]
SPINS = 3                                        # spin variants per planet: meridians step 30°, looping seamlessly
GLYPHS = {k: [R2.planet_glyph(s * 30 / 22.5, r=10.0) for s in range(SPINS)] for k in range(len(PLANETS))}
TUMBLE_MIN = 3.0                                 # rocks smaller than this don't tumble: the turn isn't visible


def scene(p, t):
    back, front = [], []                                         # (depth, svg); back drawn before the sun, front after
    for runs in ORBITS:
        for is_front, pts in runs:
            (front if is_front else back).append((1e9 if not is_front else 1e9, path(pts, "#3E3E3E" if is_front else "#1E1E1E", 0.9 if is_front else 0.8)))
    for k, (rho, r) in enumerate(PLANETS):
        hops = math.floor((t + stagger(k)) / HOP)
        x, y, rr, z, p3 = planet_at(k, PHASES[k] + hops * HOP / PERIOD)
        fill, line = R2.FILLED if p.step_lit(k) else R2.WIRE
        svg = R2.node(GLYPHS[k][hops % SPINS], x, y, rr / 10, fill, line, 0.9)
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
