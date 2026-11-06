"""Mock rest frame for P16 Context strip, sample form: a sample engine (illustration only, not a machine).

The engine draws its own screen over the sampler page (SDK 1.8) and its drawing is a close-up: the part of the
sample between the markers, large. The map replaces the header: the artwork covers y 0-20 (display.md, Artwork) and
the band is the whole sample from the overview's 96 bins, as two filled outlines (mutable, scale 2, authored within
+-60 px so each spans 240 px drawn). Each holds 16 bins along the top edge and 16 mirrored below, one per three
overview bins (the max of the three highs on top, the min of the three lows below), so 32 points. The two halves
leave a 2 px gap at the middle rather than touching, because separately placed outlines can land apart on the
device. Both re-key only when the overview's generation changes. The begin and end markers are two small square
nodes on the band's bottom edge that slide when the markers move.

Usage: python3 mock_sample.py OUT.svg
"""
import math
import sys

BAND_H = 19
MID = 9.5
BEGIN, END = 0.31, 0.47            # the region the drawing shows, as fractions of the sample
X0, X1, FRAME_TOP, FRAME_BOT = 48, 432, 34, 206
f = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")


def path(points):
    return "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in points) + " Z"


def rect(x, y, w, h):
    return path([(x, y), (x + w, y), (x + w, y + h), (x, y + h)])


def overview(n=96):
    """A made-up recording: two phrases with a quiet gap, as 96 (low, high) bins in -1..1."""
    bins = []
    for i in range(n):
        t = i / n
        env = (math.exp(-((t - 0.18) / 0.10) ** 2) * 0.95 + math.exp(-((t - 0.42) / 0.07) ** 2) * 0.7
               + math.exp(-((t - 0.72) / 0.14) ** 2) * 0.85)
        wob = 0.75 + 0.25 * math.sin(i * 1.7)
        a = max(0.04, min(1.0, env * wob))
        bins.append((-a * (0.9 + 0.1 * math.cos(i)), a))
    return bins


def half_outline(bins, x_left):
    """16 cells of 3 bins each over 240 px: top edge left to right, bottom edge back. Filled, 32 points."""
    cells = [bins[k:k + 3] for k in range(0, 48, 3)]
    step = 238 / 15                   # points on the cells' edges, spanning the half's 238 px; 2 px left as the gap
    top = [(x_left + j * step, MID - max(0.5, max(h for _, h in c)) * (MID - 1)) for j, c in enumerate(cells)]
    bot = [(x_left + j * step, MID - min(-0.5, min(l for l, _ in c)) * (MID - 1)) for j, c in reversed(list(enumerate(cells)))]
    pts = top + bot
    k = len(top) // 2                 # start mid-way along a long edge, so the closing edge isn't a short end
    return pts[k:] + pts[:k]


bins = overview()
out = []
add = out.append
add('<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">')
add("  <!-- P16 Context strip, sample form, mock rest frame (illustration only): a sample engine. -->")
add('  <g id="preview_canvas"><rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/></g>')
add(f'  <path d="{rect(0, 0, 480, 20)}" fill="#000000" stroke="none" stroke-width="0"/>')
# the whole sample, two filled halves with a 2 px gap at x 239-241
add(f'  <path d="{path(half_outline(bins[:48], 0))}" fill="#4B4B4B" stroke="none" stroke-width="0"/>')
add(f'  <path d="{path(half_outline(bins[48:], 240))}" fill="#4B4B4B" stroke="none" stroke-width="0"/>')
# begin and end markers: two 5 px squares on the band's bottom edge, the region between them is the close-up
for frac in (BEGIN, END):
    x = round(frac * 480)
    add(f'  <path d="{rect(x - 2.5, 15, 5, 5)}" fill="#AFAFAF" stroke="none" stroke-width="0"/>')


def corner(x, y, sx, sy, arm=7, w=1):
    pts = [(x, y), (x + sx * arm, y), (x + sx * arm, y + sy * w), (x + sx * w, y + sy * w), (x + sx * w, y + sy * arm), (x, y + sy * arm)]
    return pts if sx * sy > 0 else list(reversed(pts))


for x, sx in ((X0, 1), (X1, -1)):
    for y, sy in ((FRAME_TOP, 1), (FRAME_BOT, -1)):
        add(f'  <path d="{path(corner(x, y, sx, sy))}" fill="#646464" stroke="none" stroke-width="0"/>')

# the drawing: the region between the markers, large, as a line trace of the waveform over a baseline
def ribbon(points, width):
    """A closed ribbon of even width: each point pushed out along the line's normal, then back along the other side."""
    import math as m
    def normal(i):
        a, b = points[max(i - 1, 0)], points[min(i + 1, len(points) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = m.hypot(dx, dy) or 1
        return -dy / n * width / 2, dx / n * width / 2
    left = [(x + normal(i)[0], y + normal(i)[1]) for i, (x, y) in enumerate(points)]
    right = [(x - normal(i)[0], y - normal(i)[1]) for i, (x, y) in reversed(list(enumerate(points)))]
    pts = left + right
    k = len(left) // 2
    return pts[k:] + pts[:k]


N, CY = 31, (FRAME_TOP + FRAME_BOT) / 2
add(f'  <path d="{rect(X0 + 8, round(CY), X1 - X0 - 16, 1)}" fill="#323232" stroke="none" stroke-width="0"/>')
for half in range(2):                 # two 31-point ribbons (62 points each), overlapping one point so they don't just touch
    pts = []
    for i in range(N):
        t = (half * (N - 1) + i) / (2 * (N - 1))
        s = BEGIN + (END - BEGIN) * t
        amp = 72 * (math.exp(-((s - 0.42) / 0.07) ** 2) * 0.75 + 0.2)
        pts.append((X0 + 8 + (X1 - X0 - 16) * t, CY - amp * math.sin(t * 2 * math.pi * 3.25)))
    add(f'  <path d="{path(ribbon(pts, 2))}" fill="#CDCDCD" stroke="none" stroke-width="0"/>')
add("</svg>")
open(sys.argv[1], "w").write("\n".join(out) + "\n")
