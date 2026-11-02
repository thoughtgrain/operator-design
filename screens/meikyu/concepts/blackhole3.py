#!/usr/bin/env python3
"""meikyu, black-hole version 3: the horizon first. Planets come later; four placeholders circle close in.

Brian's reference is the lensed-disc look: a flat bright disc seen nearly edge-on, crossing in front of the hole as a
thin band; the far side of that disc bent up over the top into a thick arch that flares out into the disc at both
sides; the underside bent down into a ring beneath; a thin bright photon ring at the edge of the black.

The device has no blur, gradients or opacity, so the light is made of strokes: each band is a stack of thin arcs
in alternating greys, which reads as the streaky texture of the reference. Every grey drifts slightly on its own
phase, so the streaks shimmer round the hole instead of sitting still.

  arch          the far disc lensed up and over: 7 bell-shaped arcs (round over the top, flaring flat at the sides)
  under ring    the near underside lensed down: 5 arcs below the hole
  disc          the near disc crossing in front: 5 thin flat half-ellipses, widest ones reaching off-page
  hole          black disc with a thin photon ring
  Dens          scales all of it, small at 0 to filling the page at 100

    python3 blackhole3.py <tmpdir>      → blackhole3.mp4, blackhole3-stills.png, blackhole3-closeup.png
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
path, smooth = O.path, B.smooth
CX, CY = B.CENTRE

R_MIN, R_MAX = 16.0, 50.0                                              # hole radius on screen at Dens 0 and 100


def hole_r(dens):
    return R_MIN + (R_MAX - R_MIN) * smooth(dens / 100) ** 0.85


def grey(v):
    v = max(0x10, min(0xF0, round(v)))
    return f"#{v:02X}{v:02X}{v:02X}"


def shimmer(base, i, t, depth=0.16):
    """a grey that drifts on its own phase: the streaks seem to run round the hole"""
    return base * (1 - depth / 2 + depth / 2 * math.sin(2 * math.pi * (t / 2.6 + i * 0.37)))


# ---- the light -----------------------------------------------------------------------------------------------------------
# (radius ÷ hole radius, grey) inner to outer. Stroke widths are a little wider than the spacing so neighbours overlap
# and each band reads as one body of light with streaks in it, not a set of contour lines.
ARCH = [(1.05, 0xF0), (1.12, 0xC8), (1.19, 0xE4), (1.26, 0xA8), (1.33, 0xD0), (1.40, 0x90), (1.48, 0xB0), (1.56, 0x68),
        (1.65, 0x40)]
UNDER = [(1.04, 0xE0), (1.11, 0xA8), (1.18, 0xC8), (1.25, 0x88), (1.32, 0xA0), (1.40, 0x50)]
ARCH_W, UNDER_W = 0.085, 0.08                                          # stroke width ÷ hole radius
# the flat disc: (half-width ÷ R, half-height ÷ R, grey). Near halves cross in front of the hole; far halves sit behind it
DISC = [(1.45, 0.035, 0xF0), (1.9, 0.06, 0xC0), (2.4, 0.085, 0xE0), (3.0, 0.11, 0x98), (3.7, 0.135, 0xB8), (4.5, 0.16, 0x70),
        (5.4, 0.185, 0x44)]
DISC_W = 0.05
DISC_DROP = 0.06                                                       # the disc crosses a touch below the centre


def arch(r, flare):
    """a bell: round over the top (radius r), then a smooth flare out to flat at r × (1 + flare), then a short tail.
    Heights are measured up from the disc line; the flare is a Hermite curve matching the circle's slope."""
    d0 = 0.86 * r                                                      # where the circle hands over to the flare
    h0 = 0.97 * math.sqrt(r * r - d0 * d0)
    m0 = -0.97 * d0 / math.sqrt(r * r - d0 * d0)                       # dh/dx there (falling)
    w = r * (1 + flare) - d0
    right = []
    for q in range(10):                                                # the flare, inside to out
        tau = (q + 1) / 10
        h00, h10 = 2 * tau ** 3 - 3 * tau ** 2 + 1, tau ** 3 - 2 * tau ** 2 + tau
        right.append((d0 + w * tau, h00 * h0 + h10 * w * m0))
    right.append((r * (1 + flare) + r * 0.5, 0.0))                     # tail into the disc
    top = [(-d0 + 2 * d0 * q / 30, 0.97 * math.sqrt(max(0.0, r * r - (-d0 + 2 * d0 * q / 30) ** 2))) for q in range(31)]
    left = [(-x, h) for x, h in reversed(right)]
    base = CY + DISC_DROP * r
    return [(CX + x, base - h) for x, h in left + top + right]


def under(r, R):
    """the lower ring, starting just under the disc so its ends don't poke up through it"""
    base, d = CY + DISC_DROP * R, 0.14
    return [(CX + r * math.cos(d + (math.pi - 2 * d) * q / 40), base + 0.97 * r * math.sin(d + (math.pi - 2 * d) * q / 40))
            for q in range(41)]


def disc_half(rx, ry, R, near):
    base = CY + DISC_DROP * R
    sgn = 1 if near else -1
    return [(CX + rx * math.cos(math.pi * q / 48), base + sgn * ry * math.sin(math.pi * q / 48)) for q in range(49)]


def light(R, t):
    """back-to-front: the arch and under ring, the black hole and its photon ring, then the near disc over it"""
    back, front = [], []
    for i, (sx, sy, g) in enumerate(reversed(DISC)):                   # far halves of the disc, behind everything
        back.append(path(disc_half(R * sx, R * sy, R, False), grey(shimmer(g * 0.8, i + 20, t, 0.22)), max(1.0, DISC_W * R)))
    n = len(ARCH)
    for i, (s, g) in enumerate(reversed(ARCH)):
        back.append(path(arch(R * s, 0.42 + 0.5 * (n - 1 - i) / (n - 1)), grey(shimmer(g, i, t)), max(0.9, ARCH_W * R)))
    for i, (s, g) in enumerate(reversed(UNDER)):
        back.append(path(under(R * s, R), grey(shimmer(g, i + 9, t)), max(0.9, UNDER_W * R)))
    hole = [path(O.ell(CX, CY + DISC_DROP * R, R, R * 0.97, n=60), "#E8E8E8", 0.9 + 0.02 * R, fill="#000000", close=True)]
    for i, (sx, sy, g) in enumerate(reversed(DISC)):                   # near halves, crossing in front of the hole
        front.append(path(disc_half(R * sx, R * sy, R, True), grey(shimmer(g, i + 12, t, 0.22)), max(1.0, DISC_W * R)))
    return back, hole, front


# ---- four placeholder planets close in -------------------------------------------------------------------------------
NEAR = [(2.0, 0, 0.00, 4.5), (2.3, 1, 0.31, 3.2), (2.6, 2, 0.58, 5.5), (2.95, 3, 0.83, 3.8)]   # radius ÷ R, plane, phase, size
NEAR_PERIOD = 14.0


def planets(R, t):
    ppu = B.project((0.0, 0.0, 0.0))[3]
    back, front = [], []
    for j, (s, plane, ph, size) in enumerate(NEAR):
        a = 2 * math.pi * (ph + t / (NEAR_PERIOD * s ** 1.5 / 2.0 ** 1.5))   # inner ones faster (Kepler)
        p3 = B.tilted_point(R * s / ppu, a, 0.0, plane)
        x, y, _, k = B.project(p3)
        rr = 1.6 * size * (0.5 + 0.5 * R / R_MAX) * k / ppu
        node = R2.node(B.GLYPHS[[0, 6, 14, 24][j]][0], x, y, rr / 10, *R2.WIRE, 0.9)
        (front if B.nearer_than_centre(p3) else back).append((math.dist(B.CAM, p3), node))
    order = lambda side: [n for _, n in sorted(side, key=lambda q: -q[0])]
    return order(back), order(front)


def scene(p, last, t):
    R = hole_r(M4.eased(t, lambda tt: controls(tt)["dens"]))
    back, hole, front = light(R, t)
    p_back, p_front = planets(R, t)
    out = p_back + back + hole + front + p_front
    return out + O.ringed(446, 40, 12, p, ring=(1.45, 1.8 + 1.4 * ((last["vel"] if last else 64) / 127)), tilt=0.3)


# ---- the demo -----------------------------------------------------------------------------------------------------------
LENGTH = 22.0


def controls(t):
    c = {"dens": 10, "crpt": 20, "scal": 0, "drum": False}
    for t0, t1, v0, v1 in ((3, 12, 10, 100), (12, 16, 100, 100), (16, 20, 100, 45)):
        if t0 <= t < t1:
            c["dens"] = round(v0 + (v1 - v0) * (t - t0) / (t1 - t0))
    if t >= 20:
        c["dens"] = 45
    return c


def main():
    tmp = Path(sys.argv[1])
    tmp.mkdir(parents=True, exist_ok=True)
    M4.controls = controls
    M4.LENGTH = A.LENGTH = LENGTH
    presses, tones = M4.run()
    wav = tmp / "blackhole3.wav"
    A.sound(wav, tones)
    n = int(LENGTH * A.FPS)

    def render(i):
        t = i / A.FPS
        p, last = M4.page_at(t, presses)
        svg = tmp / f"f{i:04d}.svg"
        svg.write_text(B.frame(p, scene(p, last, t)))
        subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(svg), "-o", str(tmp / f"f{i:04d}.png")], check=True)
        if i not in (60, 420):
            svg.unlink()

    with ThreadPoolExecutor(8) as ex:
        list(ex.map(render, range(n)))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(A.FPS), "-i", str(tmp / "f%04d.png"), "-i", str(wav),
                    "-vf", "scale=960:440:flags=neighbor", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", str(HERE / "blackhole3.mp4")], check=True)
    ims = [Image.open(tmp / f"f{int(tt * A.FPS):04d}.png") for tt in (2, 6, 9, 14, 18, 21)]
    sheet = Image.new("RGB", (960, 660))
    for k, im in enumerate(ims):
        sheet.paste(im, (480 * (k % 2), 220 * (k // 2)))
    sheet.save(HERE / "blackhole3-stills.png")
    Image.open(tmp / f"f{14 * A.FPS:04d}.png").resize((1440, 660), Image.NEAREST).save(HERE / "blackhole3-closeup.png")
    print("wrote blackhole3.mp4")


if __name__ == "__main__":
    main()
