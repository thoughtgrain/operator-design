"""Mock rest frame for P16 Context strip, sample form: a sample engine (illustration only, not a machine).

The engine draws its own screen over the sampler page (SDK 1.8). Its drawing is a close-up of the stretch between the
markers. The map replaces the header: a static black backing covers y 0-20 (display.md, Artwork: covering the top
20 px hides the stock header), and over it the whole sample comes from the overview's 96 bins. All four mutable
outlines are used, and they share one point count (draw.hpp: every mutable outline has exactly Points points), 32:

  band   two filled halves, scale 2, authored within +-60.25 px so each spans 241 px drawn, overlapping 2 px at the
         middle so they never show a seam. 16 points along the top (one per three bins, the highest high) and 16
         back along the bottom (the lowest low), each at least +-0.5 px authored. Fill only, no stroke.
  close  the bins between the markers, magnified, drawn the way the band is: two filled halves at scale 2, 193 px
         each drawn (authored within +-48.25), overlapping 2 px. The stretch is split into 32 groups, 16 a half;
         each group's point takes the highest high (top) and lowest low (bottom) of its bins, so peaks survive a
         long stretch, and a bin repeats across groups when the stretch is shorter than 32 bins (never under one).
         Points are joined by straight lines, which invents nothing between real values. Fill only.

Begin and end are two 5 px #969696 squares on the band's bottom edge. The band re-keys only when the overview's
generation differs from the one stored (display_reset clears it, so the first frame after a reset redraws too). The
close-up re-keys then, and also whenever begin or end moves the stretch onto different bins, since they follow edits
in any frame without generation changing: two outlines and a marker node on such a frame, a moving fill to check on
the device. A new sample costs all four outlines and both markers.

Usage: python3 mock_sample.py OUT.svg
"""
import math
import sys

BAND_H, MID = 19, 9.5
BEGIN, END = 0.31, 0.47            # the outer markers, as fractions of the sample
X0, X1, FRAME_TOP, FRAME_BOT = 48, 432, 34, 206
f = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")


def path(points):
    return "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in points) + " Z"


def rect(x, y, w, h):
    return path([(x, y), (x + w, y), (x + w, y + h), (x, y + h)])


def overview(n=96):
    """A made-up recording: phrases with a quiet gap, as 96 (low, high) bins in -1..1."""
    bins = []
    for i in range(n):
        t = i / n
        env = (math.exp(-((t - 0.18) / 0.10) ** 2) * 0.95 + math.exp(-((t - 0.40) / 0.06) ** 2) * 0.8
               + math.exp(-((t - 0.72) / 0.14) ** 2) * 0.85)
        a = max(0.0, min(1.0, env * (0.75 + 0.25 * math.sin(i * 1.7))))
        bins.append((-a * (0.9 + 0.1 * math.cos(i)), a))
    return bins


def rotate(pts):
    k = len(pts) // 4                  # start mid-way along the top edge, so the closing edge is long
    return pts[k:] + pts[:k]


def band_half(bins, x_left, width=241, half_h=MID - 0.5, floor=1.0):
    """16 cells of 3 bins; points on the cells' edges. floor: +-0.5 px authored is +-1 px drawn at scale 2."""
    cells = [bins[k:k + 3] for k in range(0, 48, 3)]
    step = width / 15
    top = [(x_left + j * step, MID - max(floor, max(h for _, h in c) * half_h)) for j, c in enumerate(cells)]
    bot = [(x_left + j * step, MID + max(floor, -min(l for l, _ in c) * half_h)) for j, c in reversed(list(enumerate(cells)))]
    return rotate(top + bot)


def groups(region, n=32):
    """Split the stretch into n groups: each takes the highest high and lowest low of its bins; short stretches repeat."""
    out = []
    for k in range(n):
        i0 = int(k * len(region) / n)
        i1 = max(i0 + 1, int((k + 1) * len(region) / n))
        cell = region[i0:i1]
        out.append((min(l for l, _ in cell), max(h for _, h in cell)))
    return out


def close_half(cells, x_left, width, cy, half_h, floor=1.0):
    """16 groups as joined vertices: 16 points along the top, 16 back along the bottom. 32 points."""
    step = width / (len(cells) - 1)
    top = [(x_left + j * step, cy - max(floor, hi * half_h)) for j, (lo, hi) in enumerate(cells)]
    bot = [(x_left + j * step, cy + max(floor, -lo * half_h)) for j, (lo, hi) in reversed(list(enumerate(cells)))]
    return rotate(top + bot)


bins = overview()
out = []
add = out.append
add('<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">')
add("  <!-- P16 Context strip, sample form, mock rest frame (illustration only): a sample engine. -->")
add('  <g id="preview_canvas"><rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/></g>')
add(f'  <path d="{rect(0, 0, 480, 20)}" fill="#000000" stroke="none" stroke-width="0"/>')
for half, x in ((bins[:48], 0), (bins[48:], 239)):
    pts = band_half(half, x)
    assert len(pts) == 32
    add(f'  <path d="{path(pts)}" fill="#4B4B4B" stroke="none" stroke-width="0"/>')
for frac in (BEGIN, END):
    x = round(frac * 480)
    add(f'  <path d="{rect(x - 2.5, 15, 5, 5)}" fill="#969696" stroke="none" stroke-width="0"/>')


def corner(x, y, sx, sy, arm=7, w=1):
    pts = [(x, y), (x + sx * arm, y), (x + sx * arm, y + sy * w), (x + sx * w, y + sy * w), (x + sx * w, y + sy * arm), (x, y + sy * arm)]
    return pts if sx * sy > 0 else list(reversed(pts))


for x, sx in ((X0, 1), (X1, -1)):
    for y, sy in ((FRAME_TOP, 1), (FRAME_BOT, -1)):
        add(f'  <path d="{path(corner(x, y, sx, sy))}" fill="#646464" stroke="none" stroke-width="0"/>')

# the close-up: the bins between the markers (at least one), in 32 groups, 16 a half
lo_i = min(95, round(BEGIN * 96))
hi_i = max(lo_i + 1, round(END * 96))
cells = groups(bins[lo_i:hi_i])
CY = (FRAME_TOP + FRAME_BOT) / 2
add(f'  <path d="{rect(X0, round(CY), X1 - X0, 1)}" fill="#323232" stroke="none" stroke-width="0"/>')
for k, x in ((0, X0), (1, X0 + 191)):
    pts = close_half(cells[k * 16:(k + 1) * 16], x, 193, CY, 62)
    assert len(pts) == 32
    add(f'  <path d="{path(pts)}" fill="#AFAFAF" stroke="none" stroke-width="0"/>')
add("</svg>")
open(sys.argv[1], "w").write("\n".join(out) + "\n")
