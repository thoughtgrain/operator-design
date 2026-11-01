#!/usr/bin/env python3
"""meikyu o2 corona, stop-motion orbits: each planet is one wireframe node that hops along its own orbit.

Brian's direction: the planets should look like they move. Each one vanishes and reappears a little further along
its orbit, scaled for where it now sits. They're wireframes for cost, and each fills when the step it stands for
plays at the current density.

Built to the synth display's rules, which is what this needs from the player page (see the device note):
  - a planet is ONE path node (outline, front equator and a meridian traced as a single line, ≤ 64 points), so it
    moves with a bound transform: translate plus a uniform scale (≤ 2), never a rotation
  - wire vs filled is a palette swap on that node: black fill with grey lines, or light fill with dark lines
  - it hops every HOP seconds down the visible front of its orbit, its scale set by depth; leaving at the bottom it
    comes back in at the top, and the sixteen are phased evenly so the screen's distribution never thins out
  - hops are staggered so only a few planets redraw on any frame
  - the sun is the corona as picked, static art
  - the ringed planet (the phrase) stays put; its eight segments light for the tones that sounded

Device note: today's player page is 24 on/off dots over static art. This needs the player page to expose bound
nodes (position, scale, palette) the way a synth's display does; see README.md.

    python3 stopmotion.py <tmpdir>      → stopmotion.mp4, stopmotion-stills.png
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
HOP = 0.75                                   # seconds between a planet's hops
PERIOD_OUTER = 360.0                         # seconds for the outermost orbit; others scale by (rx/rx_max)^1.5
WIRE = ("#000000", "#7A7A7A")                # palette: (fill, line) for a wireframe planet
FILLED = ("#BEBEBE", "#4A4A4A")              # palette: (fill, line) for a planet whose step plays


def f(v):
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def glyph(r=10.0):
    """a wireframe sphere as one path: the outline clockwise from the top, a meridian clockwise from the top, the
    outline again down the right side, then the front equator out to the left and back along itself. Every loop
    winds the same way and the rest retraces itself, so a nonzero fill covers the whole disc with no holes."""
    pts = [(r * math.sin(2 * math.pi * k / 20), -r * math.cos(2 * math.pi * k / 20)) for k in range(21)]             # outline
    pts += [(0.42 * r * math.sin(2 * math.pi * k / 16), -r * math.cos(2 * math.pi * k / 16)) for k in range(1, 17)]  # meridian
    pts += [(r * math.sin(math.pi / 2 * k / 5), -r * math.cos(math.pi / 2 * k / 5)) for k in range(1, 6)]             # top → right
    eq = [(r * math.cos(math.pi * k / 8), 0.3 * r * math.sin(math.pi * k / 8)) for k in range(1, 9)]                 # right → left, front
    pts += eq + eq[::-1][1:]
    assert len(pts) <= 64, len(pts)
    return pts


GLYPH = glyph()


def node(pts, x, y, s, fill, line, w=1.0):
    d = "M" + " L".join(f"{f(px)},{f(py)}" for px, py in pts)
    return (f'<path transform="matrix({f(s)} 0 0 {f(s)} {f(x)} {f(y)})" d="{d}" fill="{fill}" stroke="{line}" '
            f'stroke-width="{f(w / s)}" stroke-linejoin="round" stroke-linecap="round"/>')


def orbits_static():
    o = []
    for rx, ry, a, r, i in S.layout():
        o.append(path(ell(SX, SY, rx, ry, math.pi, 2 * math.pi, 40), "#1E1E1E", 0.8))      # far half, dimmer
        o.append(path(ell(SX, SY, rx, ry, 0, math.pi, 40), "#323232", 0.9))
    return o


def corona_nodes(t):
    """the corona as two nodes (≤ 64 points each), scaled together round the sun's centre: a slow breath"""
    rnd = random.Random(5)
    rays = []
    for k in range(36):
        a = -math.pi / 2 + 2 * math.pi * k / 36
        if math.cos(a) < -0.2:
            continue
        L = SR + 8 + (22 if k % 3 == 0 else 12 if k % 3 == 1 else 6) + rnd.random() * 4
        rays.append(((SR + 5) * math.cos(a), (SR + 5) * math.sin(a), L * math.cos(a), L * math.sin(a), k % 3 == 0))
    s = 1.0 + 0.045 * math.sin(2 * math.pi * t / 5.5)
    o = []
    for long_ in (True, False):                                       # each node: its rays as a zigzag of segments
        pts = []
        for x0, y0, x1, y1, lg in rays:
            if lg == long_:
                pts += [(x0, y0), (x1, y1), (x0, y0)]
        o.append(node(pts[:63], SX, SY, s, "none", "#A4A4A4" if long_ else "#6E6E6E", 1.2 if long_ else 0.9))
    return o


def sun():
    return [path(ell(SX, SY, SR, SR, n=60), "#A4A4A4", 1.4, fill="#000000", close=True)] + O.wire_sphere(SX, SY, SR, "#8A8A8A", 0.8)


STEP_PX = 6.0                                # how far a planet moves per hop along its path, on every orbit
GOLDEN = 0.6180339887


def planet_size(base, a, a0):
    return base * (0.62 + 0.38 * (math.sin(a) + 1) / 2) / (0.72 + 0.28 * (math.sin(a0) + 1) / 2)


def hidden(x, y, r):
    """fully out of sight: behind the sun (drawn over the planets), under the header, below the screen or off left"""
    return math.hypot(x - SX, y - SY) + r <= SR or y + r <= 20 or y - r >= 220 or x + r <= 0


def visible_arc(rx, ry, base, a0):
    """the whole path a planet can be seen on: from where it emerges (behind the sun or under the header) round the
    front to where it's hidden again. Found by walking out from the front of the orbit in both directions."""
    ends = []
    for sign in (-1, 1):
        a = 0.0
        while abs(a) < math.pi:
            a += sign * 0.005
            r = planet_size(base, a, a0)
            if hidden(SX + rx * math.cos(a), SY + ry * math.sin(a), r):
                break
        ends.append(a)
    return ends[0], ends[1]


def planet_states(t):
    """(depth key, behind?, x, y, scale, step) per planet at time t.

    Each planet runs its whole visible path: it emerges from behind the sun (or from under the header), crosses the
    front of its orbit, and goes behind the sun or off the bottom before it wraps, so its re-entry comes just after
    its exit and never happens in plain sight. Every planet moves STEP_PX per hop, so long outer paths take longer
    than short inner ones; starting phases are spread evenly (golden-ratio offsets) so the planets begin evenly
    distributed and each orbit always holds its one planet, out of sight only for the hop or two of its wrap. Positions only change on hops."""
    out = []
    for rx, ry, a0, base, i in S.layout():
        n = (i % 8) * 2 + (0 if i < 8 else 1)
        lo, hi = visible_arc(rx, ry, base, a0)
        length = sum(math.hypot(rx * (math.cos(lo + (hi - lo) * (k + 1) / 200) - math.cos(lo + (hi - lo) * k / 200)),
                                ry * (math.sin(lo + (hi - lo) * (k + 1) / 200) - math.sin(lo + (hi - lo) * k / 200))) for k in range(200))
        hops_per_cycle = max(8, round(length / STEP_PX))
        hop = (hi - lo) / hops_per_cycle
        lo, hi = lo - 1.5 * hop, hi + 1.5 * hop                     # a hop or two out of sight at each end: the wrap is never seen
        cycle = (hops_per_cycle + 3) * HOP
        stagger = (n * 0.37) % 1.0 * HOP                              # hops spread across frames
        hops = math.floor((t + stagger) / HOP)
        u = ((n * GOLDEN) + hops * HOP / cycle) % 1.0                 # 0 entering at the top, 1 leaving at the bottom
        a = lo + (hi - lo) * u
        x, y = SX + rx * math.cos(a), SY + ry * math.sin(a)
        out.append((y, True, x, y, planet_size(base, a, a0) / 10.0, i))      # all drawn before the sun: they pass behind it
    return out


def art(p, t):
    states = planet_states(t)
    o = orbits_static()

    def draw(st):
        _, _, x, y, s, i = st
        fill, line = FILLED if p.step_lit(i) else WIRE
        return node(GLYPH, x, y, s, fill, line, 0.9)

    for st in sorted([q for q in states if q[1]], key=lambda q: q[0]):          # far half: behind the sun
        o.append(draw(st))
    o += S.sun_corona()                                                         # the corona sun as picked, unchanged
    for st in sorted([q for q in states if not q[1]], key=lambda q: q[0]):
        o.append(draw(st))
    return o + S.phrase(p)


def main():
    tmp = Path(sys.argv[1])
    tmp.mkdir(parents=True, exist_ok=True)
    events, tones = A.run()
    wav = HERE / "planets.wav"
    if not wav.exists():
        A.sound(wav, tones)
    n = int(A.LENGTH * A.FPS)

    def render(i):
        t = i / A.FPS
        svg = tmp / f"f{i:04d}.svg"
        svg.write_text(S.frame(A.page_at(t, events), art(A.page_at(t, events), t)))
        subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(svg), "-o", str(tmp / f"f{i:04d}.png")], check=True)
        if i != 300:
            svg.unlink()

    with ThreadPoolExecutor(8) as ex:
        list(ex.map(render, range(n)))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(A.FPS), "-i", str(tmp / "f%04d.png"), "-i", str(wav),
                    "-vf", "scale=960:440:flags=neighbor", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", str(HERE / "stopmotion.mp4")], check=True)
    ims = [Image.open(tmp / f"f{i:04d}.png") for i in (30, 60, 90, 300, 480, 690)]
    sheet = Image.new("RGB", (960, 660))
    for k, im in enumerate(ims):
        sheet.paste(im, (480 * (k % 2), 220 * (k // 2)))
    sheet.save(HERE / "stopmotion-stills.png")
    # redraw cost: how many planet nodes change per frame
    changes = []
    prev = None
    for i in range(n):
        cur = [(round(q[2]), round(q[3])) for q in planet_states(i / A.FPS)]
        if prev:
            changes.append(sum(1 for a, b in zip(cur, prev) if a != b))
        prev = cur
    print("wrote stopmotion.mp4; planet nodes changed per frame: max", max(changes), "mean", round(sum(changes) / len(changes), 2))


if __name__ == "__main__":
    main()
