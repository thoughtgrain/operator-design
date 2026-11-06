"""Mock rest frame for P17 Level columns (draft): a four-tap delay effect (illustration only, not a machine).

Four columns take the whole screen, one per encoder, left to right, and their greys step from dark to light in encoder
order: #323232, #4B4B4B, #7D7D7D, #AFAFAF. The columns cover y 0-20, which hides the stock header (display.md,
Artwork), so the top 20 px of each column carries its own title (10 px) and value (20 px) as the machine's own
header text, at the stock template's positions: title at (5 + 120i, 10), value at (65 + 120i, 17.44). Values are
amounts 0-100 with no percent sign (ux.md, Controls). Text, bar and hatching follow the stock header's rule, light on
the two dark columns and black on the two light ones; text contrast is 7.9, 5.4, 5.1 and 9.6:1.

Each column's level is one node: a 12 px bar across the column (inset 4 px each side), #CDCDCD on the dark columns
and black on the light ones. 0 rests at y 206-218 and 100 at y 24-36, under the text band: 182 px of travel.

Each tap has an on/off switch on the Shift row. A column's hatching is static artwork from y 20 down, one path per
diagonal strip running bottom-left to top-right, 1.5 px wide, 10 px apart along x (about 7 px square to the strips,
leaving about 5.6 px of the column's own grey between them): #7D7D7D on the darkest column, #AFAFAF on the second,
black on the two light ones, which clears 3:1 on every column (3.1, 4.0, 5.1, 9.6:1). The bar differs from the
hatching by form, a solid 12 px band across 1.5 px diagonals. A cover node in the column's own grey sits over the
hatching while the tap is on; switching off slides it down out of the column (eased 0.15-0.2 s), then parks it.

Usage: python3 mock_columns.py OUT.svg [--all-off]
"""
import sys

RAMP = ["#323232", "#4B4B4B", "#7D7D7D", "#AFAFAF"]       # encoder order, dark to light
BAR = ["#CDCDCD", "#CDCDCD", "#000000", "#000000"]         # the stock header's rule: light on dark, black on light
HATCH = ["#7D7D7D", "#AFAFAF", "#000000", "#000000"]      # at least 3:1 on each column
OFF = {0, 1, 2, 3} if "--all-off" in sys.argv else {0, 2}  # taps 1 and 3 off: their covers are away
TEXT = ["#CBCBCB", "#CBCBCB", "#000000", "#000000"]        # the stock header's rule
TITLES = ["tap 1", "tap 2", "tap 3", "tap 4"]
LEVEL = [0.72, 0.38, 0.55, 0.18]
W, H, BAR_H, INSET = 120, 220, 12, 4
Y0, Y100 = 206, 24                                         # the bar's top at 0 and at 100
f = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")


def path(points):
    return "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in points) + " Z"


HH = H - 20                                                # the hatched band, y 20-220


def hatch(x0, step=10, w=1.5):
    """Diagonal strips (bottom-left to top-right) clipped to the column by construction, one subpath each."""
    subs = []
    k = -HH
    while k < W:
        # a strip between lines x - x0 + (H - y) = k and = k + w*1.414, clipped to the column box
        pts = []
        for c in (k, k + w * 1.414):
            a = (x0 + max(0, c), H - max(0, -c))                 # entry on the bottom or left edge
            b = (x0 + min(W, c + HH), H - (min(W, c + HH) - c))  # exit on the top of the band (y 20) or right edge
            pts.append((a, b))
        (a1, b1), (a2, b2) = pts
        if b1[0] - a1[0] > 1 and b2[0] - a2[0] > 1:
            subs.append(path([a1, b1, b2, a2]))
        k += step
    return subs


out = ['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
       "  <!-- P17 Level columns, mock rest frame (illustration only): a four-tap delay effect, taps 1 and 3 switched off. -->",
       '  <g id="preview_canvas"><rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/></g>']
for i, g in enumerate(RAMP):
    x = i * W
    out.append(f'  <path d="{path([(x, 0), (x + W, 0), (x + W, H), (x, H)])}" fill="{g}" stroke="none" stroke-width="0"/>')
    for d in hatch(x):
        out.append(f'  <path d="{d}" fill="{HATCH[i]}" stroke="none" stroke-width="0"/>')
    if i not in OFF:  # the cover node, in the column's own grey, over the hatched band
        out.append(f'  <path d="{path([(x, 20), (x + W, 20), (x + W, H), (x, H)])}" fill="{g}" stroke="none" stroke-width="0"/>')
    y = round(Y0 - LEVEL[i] * (Y0 - Y100))
    out.append(f'  <path d="{path([(x + INSET, y), (x + W - INSET, y), (x + W - INSET, y + BAR_H), (x + INSET, y + BAR_H)])}" '
               f'fill="{BAR[i]}" stroke="none" stroke-width="0"/>')
    add_text = out.append
    add_text(f'  <text x="{x + 5}" y="10" font-family="UniversNextPro-Light" font-size="10" fill="{TEXT[i]}" stroke="none" stroke-width="0">{TITLES[i]}</text>')
    add_text(f'  <text x="{x + 65}" y="17.44" font-family="UniversNextPro-Light" font-size="20" fill="{TEXT[i]}" stroke="none" stroke-width="0">{round(LEVEL[i] * 100)}</text>')
out.append("</svg>")
open(sys.argv[1], "w").write("\n".join(out) + "\n")
