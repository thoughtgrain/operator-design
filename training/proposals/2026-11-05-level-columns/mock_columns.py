"""Mock rest frame for P17 Level columns (draft): a four-tap delay effect (illustration only, not a machine).

Four columns take the whole screen, one per encoder, left to right, and their greys step from dark to light in encoder
order. The columns cover y 0-20, which hides the stock header (display.md, Artwork), so each column carries its own
title (10 px) and value (20 px) at its top, as the machine's own header text (ux.md, Controls: real units in the header,
or the machine's own header text). Each column is 120 px, the stock header's column width, and the text follows the
stock header's rule: light (#CBCBCB) on the two dark columns, black on the two light ones.

Each column's level is one node: a 12 px bar across the column (inset 4 px each side), light on the darkest column and
black on the rest. 0 rests at y 206-218 and 100 at y 46-58, under the text: 160 px of travel. A 112 x 12 bar sweeping
that far changes about 2,690 px, 2.55 % of the whole 480 x 220 screen (perceptibility.py --header-bottom 0).

Each tap has an on/off switch on the Shift row (an effect's `shift` enum, SDK 1.7). The device wants one subpath per
path (display.md, Artwork), so a column's hatching is static artwork, one path per diagonal strip (1.5 px wide, 10 px
apart along x, about 7 px apart square to them, two grey steps from the column: lighter on the darkest, darker on the
rest), and a cover node, a rectangle in the column's own grey, sits over it while the tap is on. Switching off slides
the cover down out of the column (eased 0.15-0.2 s), then parks it; switching on slides it back. Here taps 1 and 3
are off, so their covers are away and the darkest column's hatching is on show.

Usage: python3 mock_columns.py OUT.svg
"""
import sys

RAMP = ["#323232", "#646464", "#969696", "#CDCDCD"]       # encoder order, dark to light
BAR = ["#CDCDCD", "#000000", "#000000", "#000000"]         # contrasts with its own column
HATCH = ["#646464", "#323232", "#646464", "#969696"]      # two steps from each column
OFF = {0, 2}                                               # taps 1 and 3 off: their covers are away
TEXT = ["#CBCBCB", "#CBCBCB", "#000000", "#000000"]        # the stock header's rule
TITLES = ["tap 1", "tap 2", "tap 3", "tap 4"]
LEVEL = [0.72, 0.38, 0.55, 0.18]
W, H, BAR_H, INSET = 120, 220, 12, 4
Y0, Y100 = 206, 46                                         # the bar's top at 0 and at 100
f = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")


def path(points):
    return "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in points) + " Z"


def hatch(x0, step=10, w=1.5):
    """Diagonal strips (bottom-left to top-right) clipped to the column by construction, one subpath each."""
    subs = []
    k = -H
    while k < W:
        # a strip between lines x - x0 + (H - y) = k and = k + w*1.414, clipped to the column box
        pts = []
        for c in (k, k + w * 1.414):
            a = (x0 + max(0, c), H - max(0, -c))                 # entry on the bottom or left edge
            b = (x0 + min(W, c + H), H - (min(W, c + H) - c))    # exit on the top or right edge
            pts.append((a, b))
        (a1, b1), (a2, b2) = pts
        if b1[0] - a1[0] > 1 and b2[0] - a2[0] > 1:
            subs.append(path([a1, b1, b2, a2]))
        k += step
    return subs


out = ['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
       "  <!-- P17 Level columns, mock rest frame (illustration only): a four-tap delay effect, tap 3 switched off. -->",
       '  <g id="preview_canvas"><rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/></g>']
for i, g in enumerate(RAMP):
    x = i * W
    out.append(f'  <path d="{path([(x, 0), (x + W, 0), (x + W, H), (x, H)])}" fill="{g}" stroke="none" stroke-width="0"/>')
    for d in hatch(x):
        out.append(f'  <path d="{d}" fill="{HATCH[i]}" stroke="none" stroke-width="0"/>')
    if i not in OFF:  # the cover node, in the column's own grey
        out.append(f'  <path d="{path([(x, 0), (x + W, 0), (x + W, H), (x, H)])}" fill="{g}" stroke="none" stroke-width="0"/>')
    y = round(Y0 - LEVEL[i] * (Y0 - Y100))
    out.append(f'  <path d="{path([(x + INSET, y), (x + W - INSET, y), (x + W - INSET, y + BAR_H), (x + INSET, y + BAR_H)])}" '
               f'fill="{BAR[i]}" stroke="none" stroke-width="0"/>')
    add_text = out.append
    add_text(f'  <text x="{x + 8}" y="16" font-family="UniversNextPro-Light" font-size="10" fill="{TEXT[i]}" stroke="none" stroke-width="0">{TITLES[i]}</text>')
    add_text(f'  <text x="{x + 8}" y="38" font-family="UniversNextPro-Light" font-size="20" fill="{TEXT[i]}" stroke="none" stroke-width="0">{round(LEVEL[i] * 100)}%</text>')
out.append("</svg>")
open(sys.argv[1], "w").write("\n".join(out) + "\n")
