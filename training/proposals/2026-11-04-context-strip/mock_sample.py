"""Mock rest frame for P16 Context strip, sample form: a sample engine (illustration only, not a machine).

The engine draws its own screen over the sampler page (SDK 1.8). Its drawing is a close-up of the stretch between the
markers. The map replaces the header: a static black backing covers y 0-20 (display.md, Artwork: covering the top
20 px hides the stock header), and over it the whole sample comes from the overview's 96 bins. All four mutable
outlines are used, and they share one point count (draw.hpp: every mutable outline has exactly Points points), 32:

  band   two filled halves, scale 2, authored within +-60.25 px so each spans 241 px drawn, overlapping 2 px at the
         middle, meant to hide the seam (pending a device check: separately placed parts can land apart). One
         mapping for everything: bin i covers x 5i to 5i + 5, and a marker at fraction f sits at x 480f. Each half
         has 16 points evenly across its 241 px, along the top and back along the bottom; a point takes the highest
         high (or lowest low) of the bins within half a point-spacing of its x, each at least +-0.5 px authored.
         Fill only, no stroke.
  close  the stretch between the markers, magnified, drawn the way the band is: two filled halves at scale 2,
         193 px each drawn (authored within +-48.25), overlapping 2 px (the same seam caveat). The same mapping,
         stretched: x 48-432 is the stretch from begin to end. One rule at every length: each point takes the
         highest high and lowest low of the bin centres within half a point-spacing of it. Every bin centre inside
         the stretch lies within half a spacing of some point, so none is missed (a bin straddling a marker with
         its centre outside can drop at the ends). On a long stretch a point gathers several centres and keeps
         their peaks; on a short one (under about 30 bins, where half a spacing is under half a bin) the point
         nearest each centre carries that bin's real value, drawn at most half a spacing (about 6 px) along from
         where it belongs, and a point with no centre near it takes the straight line between the two nearest.
         Nothing is invented and there are no plateaus. The rule never switches, but as a marker moves a point can
         step when a bin centre enters or leaves its window. Never less than one bin. Fill only.

Begin and end are two 5 px #969696 squares on the band's bottom edge. The band re-keys only when the overview's
generation differs from the one stored (display_reset clears it, so the first frame after a reset redraws too). The
close-up re-keys then too, and whenever begin or end moves, since they follow edits in any frame without
generation changing. Every such edit moves a marker node; the two close-up outlines reshape with it (a moving
fill, to check on the device). A new sample costs all four outlines and both markers.

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


def sample_at(bins, b, radius):
    """(low, high) at fractional bin position b: the extremes of bin centres within radius, else the straight line
    between the two nearest bin centres. Bin i's centre is at i + 0.5."""
    near = [bins[i] for i in range(len(bins)) if abs(i + 0.5 - b) <= radius] if radius > 0 else []
    if near:
        return min(l for l, _ in near), max(h for _, h in near)
    c = min(max(b - 0.5, 0), len(bins) - 1)
    i = min(int(c), len(bins) - 2) if len(bins) > 1 else 0
    t = c - i
    j = min(i + 1, len(bins) - 1)
    return (bins[i][0] * (1 - t) + bins[j][0] * t, bins[i][1] * (1 - t) + bins[j][1] * t)


def outline(xs, values, cy, half_h, floor=1.0):
    top = [(x, cy - max(floor, hi * half_h)) for x, (lo, hi) in zip(xs, values)]
    bot = [(x, cy + max(floor, -lo * half_h)) for x, (lo, hi) in reversed(list(zip(xs, values)))]
    return rotate(top + bot)


def band_half(bins, x_left, width=241):
    """16 points evenly over the half; x maps to bins at 5 px a bin, the markers' mapping."""
    xs = [x_left + j * width / 15 for j in range(16)]
    spacing = width / 15 / 5                         # in bins
    return outline(xs, [sample_at(bins, x / 5, spacing / 2) for x in xs], MID, MID - 0.5)


def close_half(bins, lo_b, hi_b, x_left, width, x0, x1, cy, half_h):
    """16 points evenly over the half; x 48-432 maps linearly onto the stretch lo_b..hi_b (in bins)."""
    xs = [x_left + j * width / 15 for j in range(16)]
    per_px = (hi_b - lo_b) / (x1 - x0)
    radius = width / 15 * per_px / 2           # half a point-spacing, in bins: every bin centre is caught
    return outline(xs, [sample_at(bins, lo_b + (x - x0) * per_px, radius) for x in xs], cy, half_h)


bins = overview()
out = []
add = out.append
add('<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">')
add("  <!-- P16 Context strip, sample form, mock rest frame (illustration only): a sample engine. -->")
add('  <g id="preview_canvas"><rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/></g>')
add(f'  <path d="{rect(0, 0, 480, 20)}" fill="#000000" stroke="none" stroke-width="0"/>')
for x in (0, 239):
    pts = band_half(bins, x)
    assert len(pts) == 32
    add(f'  <path d="{path(pts)}" fill="#4B4B4B" stroke="none" stroke-width="0"/>')
for frac in (BEGIN, END):
    x = frac * 480
    add(f'  <path d="{rect(x - 2.5, 15, 5, 5)}" fill="#969696" stroke="none" stroke-width="0"/>')


def corner(x, y, sx, sy, arm=7, w=1):
    pts = [(x, y), (x + sx * arm, y), (x + sx * arm, y + sy * w), (x + sx * w, y + sy * w), (x + sx * w, y + sy * arm), (x, y + sy * arm)]
    return pts if sx * sy > 0 else list(reversed(pts))


for x, sx in ((X0, 1), (X1, -1)):
    for y, sy in ((FRAME_TOP, 1), (FRAME_BOT, -1)):
        add(f'  <path d="{path(corner(x, y, sx, sy))}" fill="#646464" stroke="none" stroke-width="0"/>')

# the close-up: the stretch between the markers (at least one bin), on the same mapping, stretched
lo_b = BEGIN * 96
hi_b = max(lo_b + 1, END * 96)
CY = (FRAME_TOP + FRAME_BOT) / 2
add(f'  <path d="{rect(X0, round(CY), X1 - X0, 1)}" fill="#323232" stroke="none" stroke-width="0"/>')
for x in (X0, X0 + 191):
    pts = close_half(bins, lo_b, hi_b, x, 193, X0, X1, CY, 62)
    assert len(pts) == 32
    add(f'  <path d="{path(pts)}" fill="#AFAFAF" stroke="none" stroke-width="0"/>')
add("</svg>")
open(sys.argv[1], "w").write("\n".join(out) + "\n")
