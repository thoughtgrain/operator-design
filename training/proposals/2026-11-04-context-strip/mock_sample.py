"""Mock rest frame for P16 Context strip, sample form: a sample engine (illustration only, not a machine).

The engine draws its own screen over the sampler page (SDK 1.8). Its drawing is a close-up of the stretch between the
markers. The map replaces the header: a static black backing covers y 0-20 (display.md, Artwork: covering the top
20 px hides the stock header), and over it the whole sample comes from the overview's 96 bins. All four mutable
outlines are used, and they share one point count (draw.hpp: every mutable outline has exactly Points points), 32:

  band   two filled halves, scale 2, authored within +-60.25 px so each spans 241 px drawn, overlapping 2 px at the
         middle so they never show a seam. 16 points along the top (one per three bins, the highest high) and 16
         back along the bottom (the lowest low), each at least +-0.5 px authored. Fill only, no stroke.
  close  the bins between the markers, magnified: two filled halves at scale 2, 194 px each drawn (authored within
         +-48.5), overlapping 4 px; eight bins a half as flat steps, two points a bin (each step inset 0.5 px so
         equal neighbours never repeat a point), so it shows what the device knows and nothing finer. Fill only.

Begin and end are two 5 px #969696 squares on the band's bottom edge. Everything re-keys only when the overview's generation
differs from the one stored; display_reset clears the stored one, so the first frame after a reset redraws too.

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


def close_half(cells, x_left, width, cy, half_h, floor=1.0):
    """Eight bins as flat steps: two points a bin along the top, the same back along the bottom. 32 points."""
    w = width / len(cells)
    top, bot = [], []
    for j, (lo, hi) in enumerate(cells):
        a, b = x_left + j * w + 0.5, x_left + (j + 1) * w - 0.5   # inset, so equal neighbours never repeat a point
        top += [(a, cy - max(floor, hi * half_h)), (b, cy - max(floor, hi * half_h))]
        bot += [(a, cy + max(floor, -lo * half_h)), (b, cy + max(floor, -lo * half_h))]
    return rotate(top + list(reversed(bot)))


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

# the close-up: the bins between the markers, resampled to sixteen (eight a half), as flat steps
lo_i, hi_i = round(BEGIN * 96), round(END * 96)
region = bins[lo_i:hi_i]
cells = [region[min(len(region) - 1, int(k * len(region) / 16))] for k in range(16)]
CY = (FRAME_TOP + FRAME_BOT) / 2
add(f'  <path d="{rect(X0, round(CY), X1 - X0, 1)}" fill="#323232" stroke="none" stroke-width="0"/>')
for k, x in ((0, X0), (1, X0 + 190)):
    pts = close_half(cells[k * 8:(k + 1) * 8], x, 194, CY, 62)
    assert len(pts) == 32
    add(f'  <path d="{path(pts)}" fill="#AFAFAF" stroke="none" stroke-width="0"/>')
add("</svg>")
open(sys.argv[1], "w").write("\n".join(out) + "\n")
