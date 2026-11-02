#!/usr/bin/env python3
"""meikyu, an alternative to the orrery: the sun in the centre grows with Dens and becomes a black hole.

Brian's idea: put the sun in the centre, small; as Dens rises it grows out to the second planet's orbit; past that
it turns into a black hole and every planet falls into it. Built the same way as the orrery (a 3D scene projected
through one camera), but centred, so every orbit is on screen.

  Dens 0 → 75     the sun grows from small to the edge of the second orbit; planets it reaches slip inside it
  Dens 75 → 100   the sun becomes a black hole: its wireframe and corona fade, leaving a black disc with a bright
                  photon ring and light bent up over the top; asteroids fall in from every direction. The
                  orbits fall in, inner first, and turn to face the camera, ending as true circles just outside the
                  horizon, concentric with its outline; the planets keep circling there, faster, stay round, their surface detail fading out to plain circles as they fall, and
                  still fill, flash and link with the sequence
  Dens back down  all of it runs backwards: the hole relaxes into a sun and the planets come back out

Everything else carries over from the orrery: sixteen step planets (they fill when their step plays, flash when it
sounds) and sixteen extras, four subtle kinds, a few tilted rings, links along an orbit in the direction of travel
(fast in, slow out), and the stock header with Rthm. No text line.

    python3 blackhole.py <tmpdir>      → blackhole.mp4, blackhole-stills.png
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
import orrery4 as M4
import planet_kinds as PK
import planets_av as A

HERE = Path(__file__).resolve().parent
path, ell = O.path, O.ell

# ---- camera: sun at the centre of the page -----------------------------------------------------------------------------
CENTRE = (240.0, 120.0)
CAM_EL, CAM_D = math.radians(20), 2600.0
CAM = (0.0, CAM_D * math.sin(CAM_EL), -CAM_D * math.cos(CAM_EL))      # in front, a little above, looking at the sun


def project(p):
    """world → (screen x, screen y, depth, px per world unit). One unit is one pixel at the sun's depth."""
    dx, dy, dz = p[0] - CAM[0], p[1] - CAM[1], p[2] - CAM[2]
    ce, se = math.cos(CAM_EL), math.sin(CAM_EL)
    zc = dz * ce - dy * se                                            # depth along the view
    yc = dy * ce + dz * se                                            # up on screen
    k = CAM_D / zc
    return CENTRE[0] + dx * k, CENTRE[1] - yc * k, zc, k


def orbit_point(rho, a, h=0.0):
    return (rho * math.cos(a), h, rho * math.sin(a))


def nearer_than_centre(p):
    return math.dist(CAM, p) < math.dist(CAM, (0.0, 0.0, 0.0))


# ---- layout -------------------------------------------------------------------------------------------------------------
ORBITS = [70, 100, 132, 165, 198, 228]
SLOTS = [(3, 2), (4, 2), (5, 3), (6, 3), (7, 3), (7, 3)]             # planets, of which steps, per orbit
HOP, PERIOD = 0.75, 90.0
_rnd = random.Random(19)
BODIES, STEP_OF, ORBIT_OF, SLOT_OF, KIND, RINGED = [], [], [], [], [], {}
_step = 0
for o, (rho, (n, steps)) in enumerate(zip(ORBITS, SLOTS)):
    step_slots = {round(j * n / steps) for j in range(steps)}
    for i in range(n):
        is_step = i in step_slots
        size = _rnd.choice([3.0, 4.0, 5.0, 6.5, 8.0, 10.0]) if is_step else _rnd.choice([1.5, 2.0, 2.6, 3.2, 4.0])
        BODIES.append((rho, size))
        ORBIT_OF.append(o)
        SLOT_OF.append((i, n))
        STEP_OF.append(_step if is_step else None)
        _step += is_step
        KIND.append(_rnd.choices(["wire", "smooth", "banded", "rocky"], [35, 25, 20, 20])[0])
for k in (6, 14, 24):                                                 # three ringed worlds, each ring tilted its own way
    RINGED[k] = (math.radians(_rnd.uniform(12, 30)), _rnd.uniform(0, math.pi))
    KIND[k] = _rnd.choice(["smooth", "banded"])
STEP_BODY = {s: k for k, s in enumerate(STEP_OF) if s is not None}
GLYPHS = {k: [PK.glyph(KIND[k], v, 500 + k) for v in range(PK.SPINS[KIND[k]])] for k in range(len(BODIES))}


def phases_for(bases):
    return [(bases[ORBIT_OF[k]] + i / n) % 1.0 for k, (i, n) in enumerate(SLOT_OF)]


def clearance(ph, samples=120):
    worst = 1e9
    for s in range(samples):
        u = s / samples
        pts = []
        for k, p0 in enumerate(ph):
            if STEP_OF[k] is None:
                continue
            rho, r = BODIES[k]
            x, y, _, ppu = project(orbit_point(rho, 2 * math.pi * (u + p0)))
            pts.append((x, y, r * ppu * (2.0 if k in RINGED else 1.0)))
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                worst = min(worst, math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1]) - pts[i][2] - pts[j][2])
    return worst


def choose():
    rnd = random.Random(3)
    best, best_c = None, -1e9
    for _ in range(2500):
        b = [rnd.random() for _ in ORBITS]
        c = clearance(phases_for(b), 60)
        if c > best_c:
            best, best_c = b, c
    ph = phases_for(best)
    return ph, clearance(ph, 360)


PHASES, CLEAR = choose()


# ---- Dens → sun, black hole, infall ---------------------------------------------------------------------------------------
GROW_END = 75                                                         # Dens where the sun reaches the second orbit
SUN_MIN, SUN_MAX = 16.0, ORBITS[1] - 8.0
HORIZON = 34.0


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def stage(dens):
    """(sun radius, black-hole amount 0..1)"""
    grow = smooth(dens / GROW_END)
    hole = smooth((dens - GROW_END) / (100 - GROW_END))
    radius = SUN_MIN + (SUN_MAX - SUN_MIN) * grow ** 1.2
    return radius + (HORIZON - radius) * hole, hole


def infall(o, hole):
    """how far orbit o has fallen in (0 = in place, 1 = through the horizon): inner orbits go first"""
    start = 0.08 * o
    return smooth((hole - start) / (1.0 - start))


def eased_dens(t):
    return M4.eased(t, lambda tt: controls(tt)["dens"])


# ---- drawing ---------------------------------------------------------------------------------------------------------------
def sun(radius, hole):
    """the corona sun, fading into a black hole as `hole` goes to 1"""
    o = []
    cx, cy = CENTRE
    rr = radius * project((0.0, 0.0, 0.0))[3]
    rnd = random.Random(5)
    keep = 1.0 - hole
    if keep > 0.03:                                                    # corona rays, shrinking away
        for k in range(36):
            a = 2 * math.pi * k / 36
            L = rr + (6 + (14 if k % 3 == 0 else 7 if k % 3 == 1 else 3) + rnd.random() * 3) * keep * (rr / 40) ** 0.5
            g = round(0x30 + (0xA4 - 0x30) * keep) if k % 3 == 0 else round(0x28 + (0x6E - 0x28) * keep)
            o.append(path([(cx + (rr + 3) * math.cos(a), cy + (rr + 3) * math.sin(a)), (cx + L * math.cos(a), cy + L * math.sin(a))],
                          f"#{g:02X}{g:02X}{g:02X}", 1.1 if k % 3 == 0 else 0.8))
    rim = round(0xA4 + (0xF0 - 0xA4) * hole)                            # the sun's rim brightens into the photon ring
    o.append(path(ell(cx, cy, rr, rr, n=60), f"#{rim:02X}{rim:02X}{rim:02X}", 1.4 + 0.6 * hole, fill="#000000", close=True))
    if keep > 0.03:
        g = round(0x30 + (0x8A - 0x30) * keep)
        o += O.wire_sphere(cx, cy, rr, f"#{g:02X}{g:02X}{g:02X}", 0.8)
    return o


def lensing(hole):
    """light from behind the hole, bent up over the top of it (no flat disc: those tilted lines are gone)"""
    if hole < 0.05:
        return []
    o = []
    cx, cy = CENTRE
    rr = HORIZON * project((0.0, 0.0, 0.0))[3]
    for s, g in ((1.35, 0xC0), (1.7, 0x80)):
        g = round(0x20 + (g - 0x20) * hole)
        o.append(path(ell(cx, cy, rr * s, rr * s * 0.95, math.pi * 1.04, math.pi * 1.96, 40), f"#{g:02X}{g:02X}{g:02X}", 1.0))
    return o


N_INFALL, INFALL_LIFE = 18, 4.0                                        # infalling asteroids, and seconds each takes to fall


def infalling(t, hole):
    """asteroids falling into the hole from all round: each on its own tilted path, spiralling in faster, shrinking
    and tumbling until it crosses the horizon. More of them as the hole deepens. (world point, svg) pairs"""
    if hole < 0.1:
        return []
    out = []
    for i in range(N_INFALL):
        rnd = random.Random(900 + i)
        if rnd.random() > hole:                                       # fewer while the hole is still forming
            continue
        offset = rnd.uniform(0, INFALL_LIFE)
        cycle = math.floor((t + offset) / INFALL_LIFE)
        u = ((t + offset) % INFALL_LIFE) / INFALL_LIFE                # 0 at the edge … 1 at the horizon
        crnd = random.Random(900 + i * 97 + cycle)                    # each fall comes from somewhere new
        a0, tilt, yaw = crnd.uniform(0, 2 * math.pi), crnd.uniform(-1.2, 1.2), crnd.uniform(0, math.pi)
        rho = HORIZON + (250.0 - HORIZON) * (1 - u) ** 1.6
        a = a0 + 2 * math.pi * 1.6 * u * u                            # spinning up as it falls
        x0, z0 = rho * math.cos(a), rho * math.sin(a)                 # in its own plane, then tilted and turned
        y1, z1 = z0 * math.sin(tilt), z0 * math.cos(tilt)
        p3 = (x0 * math.cos(yaw) - z1 * math.sin(yaw), y1, x0 * math.sin(yaw) + z1 * math.cos(yaw))
        x, y, _, ppu = project(p3)
        size = crnd.uniform(4.0, 8.0) * (1 - 0.65 * u) * ppu
        if math.hypot(x - CENTRE[0], y - CENTRE[1]) < HORIZON * project((0.0, 0.0, 0.0))[3] + size and not nearer_than_centre(p3):
            continue
        g = round(0x5A + (0xC8 - 0x5A) * u)                            # brightening as it heats on the way in
        out.append((p3, R2.node(R2.rock_glyph(800 + i, cycle % 3), x, y, size / 10, "#000000", f"#{g:02X}{g:02X}{g:02X}", 0.8)))
    return out


def ring_halves(c3, r, line, tilt, yaw):
    u = (math.cos(yaw), 0.0, math.sin(yaw))
    v = (-math.sin(yaw) * math.cos(tilt), math.sin(tilt), math.cos(yaw) * math.cos(tilt))
    cam_d = math.dist(CAM, c3)
    out = {"back": [], "front": []}
    for half in ("back", "front"):
        for rad in (1.45 * r, 2.0 * r):
            pts = []
            for q in range(41):
                th = 2 * math.pi * q / 40
                w = tuple(c3[i] + rad * (math.cos(th) * u[i] + math.sin(th) * v[i]) for i in range(3))
                if (math.dist(CAM, w) > cam_d) == (half == "back"):
                    pts.append(project(w)[:2])
                else:
                    if len(pts) > 1:
                        out[half].append(path(pts, line, 0.8))
                    pts = []
            if len(pts) > 1:
                out[half].append(path(pts, line, 0.8))
    return out


FINAL = [HORIZON * (1.3 + 0.2 * o) for o in range(len(ORBITS))]       # where each orbit ends up: rings hugging the horizon


def tilted_point(rho, a, fall):
    """a point on an orbit whose plane turns, as it falls, from the orbit plane to face the camera: at fall 1 the
    orbit is a true circle on screen, concentric with the horizon's outline"""
    beta = fall * (math.pi / 2 - CAM_EL)                               # rotate the depth axis up toward the view plane
    return (rho * math.cos(a), rho * math.sin(a) * math.sin(beta), rho * math.sin(a) * math.cos(beta))
DETAIL_STEPS = 3                                                       # grey steps the surface detail fades through
SPIN_UP = 4.0                                                          # how much faster a fully fallen orbit turns


def orbit_radius(o, hole):
    return ORBITS[o] + (FINAL[o] - ORBITS[o]) * infall(o, hole)


_ANGLE = {}


def turned(o, t):
    """how far orbit o has turned by time t (turns), integrated so speeding up never makes a planet jump"""
    key = (o, round(t * 30))
    if key not in _ANGLE:
        n = round(t * 30)
        total, dt = 0.0, 1 / 30
        for i in range(n):
            tt = i * dt
            total += dt / PERIOD * (1 + SPIN_UP * infall(o, stage(eased_dens(tt))[1]))
        _ANGLE[key] = total
    return _ANGLE[key]


def body_state(k, t, dens_now, hole):
    """where body k is: (world point, screen x, y, radius px, hops, flattening stage) or None if it's inside the sun.
    Past the black-hole point the orbits fall in to a band just outside the horizon and keep circling there, faster;
    the planets flatten into streaks along their orbits as they fall (stepped: the device can only scale uniformly)."""
    rho, r = BODIES[k]
    o = ORBIT_OF[k]
    fall = infall(o, hole)
    hops = math.floor((t + (k * 0.37) % 1.0 * HOP) / HOP)
    hop_t = hops * HOP
    a = 2 * math.pi * (PHASES[k] + turned(o, max(0.0, hop_t)))
    rho_now = orbit_radius(o, hole)
    radius, _ = stage(dens_now)
    size = r * (1 - 0.45 * fall)                                       # smaller as they crowd round the horizon
    fade = min(DETAIL_STEPS, int(fall * (DETAIL_STEPS + 1)))           # 0 full detail … DETAIL_STEPS plain circle
    if rho_now - size <= radius:                                       # inside the sun while it's big
        return None
    p3 = tilted_point(rho_now, a, fall)
    x, y, _, ppu = project(p3)
    return p3, x, y, size * ppu, hops, fade, a


CIRCLE = [(10.0 * math.sin(2 * math.pi * q / 32), -10.0 * math.cos(2 * math.pi * q / 32)) for q in range(33)]


def mix(c0, c1, u):
    """two #RRGGBB greys mixed; the device steps through a few palette entries instead"""
    a, b = int(c0[1:3], 16), int(c1[1:3], 16) if c1.startswith("#") else 0
    v = round(a + (b - a) * u)
    return f"#{v:02X}{v:02X}{v:02X}"


def scene(p, last, t, presses):
    dens_now = eased_dens(t)
    radius, hole = stage(dens_now)
    back, front = [], []
    for o, rho in enumerate(ORBITS):                                   # orbit lines, falling in with their planets
        fall = infall(o, hole)
        rho_now = orbit_radius(o, hole)
        if rho_now <= radius + 1:
            continue
        for front_half in (False, True):                               # far half behind the sun, near half in front
            g = round(0x3A if front_half else 0x1E)
            pts = [project(tilted_point(rho_now, (math.pi if front_half else 0) + math.pi * q / 60, fall))[:2] for q in range(61)]
            (front if front_half else back).append((1e9, path(pts, f"#{g:02X}{g:02X}{g:02X}", 0.9 if front_half else 0.8)))
    flashed = {i for th, i in (last["hits"] if last else []) if 0 <= t - th < M4.FLASH}
    pos, placed = {}, []
    order = sorted(range(len(BODIES)), key=lambda k: STEP_OF[k] is None)
    for k in order:
        st = body_state(k, t, dens_now, hole)
        if st is None:
            continue
        p3, x, y, rr, hops, fade, ang = st
        step = STEP_OF[k]
        foot = rr * (2.0 if k in RINGED else 1.0)
        if step is None and any(math.hypot(x - x2, y - y2) - foot - f2 < 3 for x2, y2, f2 in placed):
            continue
        placed.append((x, y, foot))
        if step is not None:
            pos[step] = (p3, ORBIT_OF[k], ang, orbit_radius(ORBIT_OF[k], hole), infall(ORBIT_OF[k], hole))
        lit = step is not None and p.step_lit(step) and not p.drum
        fill, line = R2.FILLED if lit else R2.WIRE
        if step in flashed:
            fill, line = ("#F0F0F0", "#7A7A7A")
        d = math.dist(CAM, p3)
        side = front if nearer_than_centre(p3) else back
        if fade == 0:
            side.append((d, R2.node(GLYPHS[k][hops % len(GLYPHS[k])], x, y, rr / 10, fill, line, 0.9)))
        else:                                                          # falling in: a plain circle, the surface fading
            side.append((d, R2.node(CIRCLE, x, y, rr / 10, fill, line, 0.9)))
            if fade < DETAIL_STEPS:
                faded = mix(line, fill, fade / DETAIL_STEPS)            # detail lines step toward the fill colour
                side.append((d - 0.1, R2.node(GLYPHS[k][hops % len(GLYPHS[k])], x, y, rr / 10, "none", faded, 0.9)))
        if k in RINGED and fade == 0:
            halves = ring_halves(p3, BODIES[k][1] * (rr / BODIES[k][1] / project(p3)[3]), line, *RINGED[k])
            side += [(d + 0.5, s) for s in halves["back"]] + [(d - 0.5, s) for s in halves["front"]]
    for p3r, svg in infalling(t, hole):                                # asteroids, ordered with everything else
        (front if nearer_than_centre(p3r) else back).append((math.dist(CAM, p3r), svg))
    out = [s for _, s in sorted(back, key=lambda q: -q[0])]
    out += lensing(hole)
    out += sun(radius, hole)
    out += [s for _, s in sorted(front, key=lambda q: -q[0])]
    out += links(t, presses, pos, hole)
    return out + O.ringed(446, 40, 12, p, ring=(1.45, 1.8 + 1.4 * ((last["vel"] if last else 64) / 127)), tilt=0.3)


def links(t, presses, pos, hole):
    out = []
    lk = []
    for pr in presses:
        lk += [(t0, i0, t1, i1) for (t0, i0), (t1, i1) in zip(pr["hits"], pr["hits"][1:]) if t0 <= t]
    lk = [q for q in lk if q[1] in pos and q[3] in pos and pos[q[1]][1] == pos[q[3]][1]]
    for t0, i0, t1, i1 in lk[-M4.LINKS:]:
        age = t - t0
        if age > M4.CONNECT + M4.FADE:
            continue
        (p0, o, a0, rho, fall), (p1, _, a1, _, _) = pos[i0], pos[i1]
        da = (a1 - a0) % (2 * math.pi)
        reach = min(1.0, age / M4.CONNECT)
        fade = 1.0 if age < M4.CONNECT else 1.0 - (age - M4.CONNECT) / M4.FADE
        g = 0xF0 if fade > 0.66 else 0x8A if fade > 0.33 else 0x4A
        pts = [project(tilted_point(rho, a0 + da * reach * q / 47, fall))[:2] for q in range(48)]
        out.append(path(pts, f"#{g:02X}{g:02X}{g:02X}", 1.4 if g == 0xF0 else 1.1))
    return out


# ---- the demo ---------------------------------------------------------------------------------------------------------------
LENGTH = 36.0


def controls(t):
    c = {"dens": 30, "crpt": 20, "scal": 0, "drum": False}
    for t0, t1, v0, v1 in ((4, 12, 30, 75), (12, 14, 75, 75), (14, 22, 75, 100), (22, 25, 100, 100), (25, 31, 100, 40)):
        if t0 <= t < t1:
            c["dens"] = round(v0 + (v1 - v0) * (t - t0) / (t1 - t0))
    if t >= 31:
        c["dens"] = 40
    return c


def frame(p, body):
    return "\n".join(['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
                      '<rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>'] + body + M4.header(p) + ["</svg>"])


def main():
    tmp = Path(sys.argv[1])
    tmp.mkdir(parents=True, exist_ok=True)
    M4.controls = controls                                            # the player port and pages follow this score
    M4.LENGTH = A.LENGTH = LENGTH
    print(f"step planets clear by {CLEAR:.1f} px; {len(BODIES)} bodies")
    presses, tones = M4.run()
    wav = HERE / "blackhole.wav"
    A.sound(wav, tones)
    n = int(LENGTH * A.FPS)

    def render(i):
        t = i / A.FPS
        p, last = M4.page_at(t, presses)
        svg = tmp / f"f{i:04d}.svg"
        svg.write_text(frame(p, scene(p, last, t, presses)))
        subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(svg), "-o", str(tmp / f"f{i:04d}.png")], check=True)
        if i not in (300, 660):
            svg.unlink()

    with ThreadPoolExecutor(8) as ex:
        list(ex.map(render, range(n)))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(A.FPS), "-i", str(tmp / "f%04d.png"), "-i", str(wav),
                    "-vf", "scale=960:440:flags=neighbor", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", str(HERE / "blackhole.mp4")], check=True)
    ims = [Image.open(tmp / f"f{int(tt * A.FPS):04d}.png") for tt in (2, 9, 13, 17, 20, 23.5)]
    sheet = Image.new("RGB", (960, 660))
    for k, im in enumerate(ims):
        sheet.paste(im, (480 * (k % 2), 220 * (k // 2)))
    sheet.save(HERE / "blackhole-stills.png")
    print("wrote blackhole.mp4")


if __name__ == "__main__":
    main()
