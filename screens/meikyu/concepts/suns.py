#!/usr/bin/env python3
"""meikyu o2 orrery, round 4: five suns, and planets that look like they're moving.

Brian picked o2 and asked for a sun with more wonder, and for the planets to look like they orbit. A player page
can't move a dot (24 lamps, on or off), so the motion is drawn: every planet trails a fading arc along its orbit
behind it, like a long exposure, in three steps of grey that thin toward the tail. Each orbit is drawn brighter
ahead of its planet than behind, so the eye reads a direction of travel.

The sun is static art. It's now big and half off the left edge, so the orbits sweep out of it. There's no
keyboard: the SDK skips output-key nodes the artwork doesn't have, so the page leaves them out and the system
uses the whole screen, with the text line along the bottom.

  s1 corona     a wireframe sun with a crown of rays of uneven length, like a woodcut sun
  s2 eclipse    a black disc with a thin bright rim and a corona of curved flame strokes
  s3 armillary  three tilted great circles turning round a small solid core, like an armillary sphere
  s4 flare      a bright core with long cross-flare streaks and a scatter of small star points across the page
  s5 rings      a banded gas giant sun: latitude bands and a wide tilted ring sweeping round it

    python3 suns.py      → s*/<pose>.svg and board-suns.png
"""
from __future__ import annotations

import math
import random
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

import effects as E
import orbits as O
import pages as P

HERE = Path(__file__).resolve().parent
W, H = 480, 220
path, ell, wire_sphere, planet = O.path, O.ell, O.wire_sphere, O.planet
TRAIL = ["#262626", "#3A3A3A", "#565656"]
ORBIT_BACK, ORBIT_AHEAD, SUNLINE, CORE, INK, HOT = "#262626", "#3C3C3C", "#A4A4A4", "#D8D8D8", "#000000", "#F0F0F0"
SX, SY, SR = 6, 116, 62                                  # the sun: centre near the left edge, radius
TEXT_Y = 213                                             # the text line; no keyboard, so the art uses the whole page


def layout():
    """sixteen orbits round the sun, a planet on each: (orbit rx, ry, angle, planet radius, step)"""
    out = []
    for i in range(16):
        n = (i % 8) * 2 + (0 if i < 8 else 1)
        rx = 100 + n * 21.5
        ry = rx * 0.24
        a = 0.35 + 0.42 * math.sin(n * 1.9)
        a = a if n % 2 else -a
        base = 8.5 + 6.5 * math.sin(n * 0.7 + 0.4) ** 2
        out.append((rx, ry, a, base * (0.72 + 0.28 * (math.sin(a) + 1) / 2), i))
    return out


def orbits_and_trails():
    """static: each orbit dim behind its planet and brighter ahead; a fading trail just behind the planet.
    Planets travel toward increasing angle (down the front of the orbit, toward the viewer)."""
    o = []
    for rx, ry, a, r, i in layout():
        span = 0.62
        o.append(path(ell(SX, SY, rx, ry, -0.9, a - 0.32, 14), ORBIT_BACK, 0.8))
        o.append(path(ell(SX, SY, rx, ry, a + r / rx, a + span, 12), ORBIT_AHEAD, 0.9))
        for k, (c, w) in enumerate(zip(TRAIL, (1.0, 1.6, 2.2))):            # tail → head: darker and thinner at the tail
            a0 = a - 0.32 + 0.1 * k
            a1 = a0 + 0.1
            o.append(path(ell(SX, SY, rx, ry, a0, min(a1, a - r / rx * 0.6), 6), c, w))
    return o


def planets(p):
    o = []
    for rx, ry, a, r, i in sorted(layout(), key=lambda t: SY + t[1] * math.sin(t[2])):
        o += planet(SX + rx * math.cos(a), SY + ry * math.sin(a), r, p.step_lit(i))
    return o


def phrase(p):
    return O.ringed(424, 178, 14, p, ring=(1.5, 2.3), tilt=0.3)


# ---- the five suns -------------------------------------------------------------------------------------------------------
def sun_corona():
    o = []
    rnd = random.Random(5)
    for k in range(36):                                                    # rays of uneven length, gaps between
        a = -math.pi / 2 + 2 * math.pi * k / 36
        if math.cos(a) < -0.2:
            continue
        L = SR + 8 + (22 if k % 3 == 0 else 12 if k % 3 == 1 else 6) + rnd.random() * 4
        o.append(path([(SX + (SR + 5) * math.cos(a), SY + (SR + 5) * math.sin(a)), (SX + L * math.cos(a), SY + L * math.sin(a))],
                      SUNLINE if k % 3 == 0 else "#6E6E6E", 1.2 if k % 3 == 0 else 0.9))
    o.append(path(ell(SX, SY, SR, SR, n=60), SUNLINE, 1.4, fill=INK, close=True))
    o += wire_sphere(SX, SY, SR, "#8A8A8A", 0.8)
    return o


def sun_eclipse():
    o = []
    rnd = random.Random(9)
    for k in range(22):                                                    # curved flames licking off the rim
        a = -1.35 + 2.7 * k / 21 + rnd.uniform(-0.04, 0.04)
        L = 10 + rnd.random() * 20
        bend = rnd.choice((-1, 1)) * 0.22
        pts = []
        for s in range(7):
            u = s / 6
            rr = SR + 2 + L * u
            aa = a + bend * u * u
            pts.append((SX + rr * math.cos(aa), SY + rr * math.sin(aa)))
        o.append(path(pts, "#5A5A5A" if k % 2 else "#8A8A8A", 1.0 if k % 2 else 1.3))
    o.append(path(ell(SX, SY, SR + 3, SR + 3, n=60), "#4A4A4A", 1.0, close=True))
    o.append(path(ell(SX, SY, SR, SR, n=60), CORE, 2.0, fill=INK, close=True))     # the bright rim round a black disc
    return o


def sun_armillary():
    o = [path(ell(SX, SY, SR, SR, n=60), "#4A4A4A", 0.8, fill=INK, close=True)]
    for tilt, rot, c in ((0.28, 0.0, SUNLINE), (0.35, 0.9, "#8A8A8A"), (0.3, -0.85, "#8A8A8A"), (1.0, 0.0, "#5A5A5A")):
        pts = []
        for k in range(61):                                                # a tilted great circle, rotated in the picture plane
            t = 2 * math.pi * k / 60
            x, y = SR * math.cos(t), SR * tilt * math.sin(t)
            pts.append((SX + x * math.cos(rot) - y * math.sin(rot), SY + x * math.sin(rot) + y * math.cos(rot)))
        o.append(path(pts, c, 1.1))
    o.append(path(ell(SX, SY, 15, 15, n=30), CORE, 1.0, fill=CORE, close=True))   # the core
    o.append(path(ell(SX, SY, 21, 21, n=30), "#6E6E6E", 0.8, close=True))
    return o


def sun_flare():
    o = []
    rnd = random.Random(3)
    for _ in range(38):                                                    # far stars across the page
        x, y = rnd.uniform(80, 470), rnd.uniform(28, 200)
        s = rnd.choice((0.8, 1.0, 1.4))
        o.append(path([(x - s, y), (x, y - s), (x + s, y), (x, y + s)], "#4A4A4A", 0.6, fill="#4A4A4A", close=True))
    for a, L, w in ((0.0, 150, 1.4), (math.pi / 2, 60, 1.2), (-math.pi / 2, 60, 1.2), (0.42, 90, 0.8), (-0.42, 90, 0.8)):
        o.append(path([(SX + 20 * math.cos(a), SY + 20 * math.sin(a)), (SX + L * math.cos(a), SY + L * math.sin(a))], "#8A8A8A", w))
    o.append(path(ell(SX, SY, SR, SR, n=60), "#5A5A5A", 1.0, fill=INK, close=True))
    o.append(path(ell(SX, SY, 30, 30, n=40), "#8A8A8A", 1.0, close=True))
    o.append(path(ell(SX, SY, 17, 17, n=30), CORE, 1.0, fill=CORE, close=True))
    return o


def sun_rings():
    o = []
    back = ell(SX, SY, SR * 1.75, SR * 0.36, math.pi, 2 * math.pi, 40)
    front = ell(SX, SY, SR * 1.75, SR * 0.36, 0, math.pi, 40)
    o.append(path(back, "#6E6E6E", 2.4))
    o.append(path(ell(SX, SY, SR, SR, n=60), SUNLINE, 1.4, fill=INK, close=True))
    for lat in (-0.7, -0.45, -0.2, 0.08, 0.35, 0.62):                       # banded latitudes, front halves
        rr, yy = SR * math.cos(lat * math.pi / 2), SY + SR * math.sin(lat * math.pi / 2)
        o.append(path(ell(SX, yy, rr, rr * 0.3, 0, math.pi, 24), "#6E6E6E" if lat < 0 else "#8A8A8A", 1.0))
    o.append(path(front, SUNLINE, 2.4))
    o.append(path(ell(SX, SY, SR * 1.95, SR * 0.4, 0.15, math.pi - 0.15, 40), "#4A4A4A", 0.8))
    return o


SUNS = {"s1-corona": sun_corona, "s2-eclipse": sun_eclipse, "s3-armillary": sun_armillary, "s4-flare": sun_flare, "s5-rings": sun_rings}


def art(sun_fn, p):
    return orbits_and_trails() + sun_fn() + planets(p) + phrase(p)


def frame(p, body):
    line = f'<text transform="matrix(1 0 0 1 240 {TEXT_Y})" fill="#F2F2F2" font-family="UniversNextPro-Light" font-size="16px" text-anchor="middle">{p.line()}</text>'
    return "\n".join(['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
                      '<rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>'] + body + [line] + P.header(p) + ["</svg>"])


def main():
    ps = {k: v for k, v in E.poses().items() if k in ("rest", "phrase", "dens-0", "dens-100")}
    for name, fn in SUNS.items():
        d = HERE / name
        d.mkdir(exist_ok=True)
        for pose, p in ps.items():
            (d / f"{pose}.svg").write_text(frame(p, art(fn, p)), encoding="utf-8")
    pad = 8
    sheet = Image.new("RGB", (pad + len(ps) * (W + pad), pad + 18 + len(SUNS) * (H + pad)), (40, 40, 40))
    dr = ImageDraw.Draw(sheet)
    with tempfile.TemporaryDirectory() as tmp:
        for j, pose in enumerate(ps):
            dr.text((pad + j * (W + pad), pad), pose, fill=(200, 200, 200))
        for i, name in enumerate(SUNS):
            for j, pose in enumerate(ps):
                png = Path(tmp) / f"{name}-{pose}.png"
                subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(HERE / name / f"{pose}.svg"), "-o", str(png)], check=True)
                sheet.paste(Image.open(png).convert("RGB"), (pad + j * (W + pad), pad + 18 + i * (H + pad)))
    sheet.save(HERE / "board-suns.png")
    print("wrote", len(SUNS) * len(ps), "frames")


if __name__ == "__main__":
    main()
