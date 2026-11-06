"""Mock rest frame for P17 Level columns: a four-tap delay effect (illustration only, not a machine).

Four columns take the whole screen, one per encoder, left to right. Their greys step from dark to light in encoder
order, the same order as the encoder dots on the stock tile pages, so the ramp ties each column to its encoder
without a label. The columns cover y 0-20, which hides the stock header (display.md, Artwork); there are no titles,
values or text slots.

Each column's level is one node: a 10 px bar across the column (inset 4 px each side), light on the darkest column
and black on the rest, so it contrasts with its own ground. 0 rests on the bottom edge, 100 at the top: 196 px of
travel. Each tap has an on/off switch on the Shift row (an effect's `shift` enum, SDK 1.7). The device wants one
subpath per path (display.md, Artwork), so the hatching can't be one node. Instead every column's hatching is static
artwork, one path per diagonal strip (1.5 px, 10 px apart, two grey steps from the column), and a cover node, a
rectangle in the column's own grey, sits over it while the tap is on. Switching the tap off parks the cover at
(640, 320) (`hide`), which shows the hatching: one node per column, nothing at rest. The level bar draws over both, so
the setting stays visible. Here tap 3 is off, so its cover is parked (left out of this still).

Usage: python3 mock_columns.py OUT.svg
"""
import sys

RAMP = ["#323232", "#646464", "#969696", "#CDCDCD"]       # encoder order, dark to light
BAR = ["#CDCDCD", "#000000", "#000000", "#000000"]         # contrasts with its own column
HATCH = ["#646464", "#323232", "#646464", "#969696"]      # two steps from each column
OFF = {2}                                                  # tap 3 off: its cover is parked
LEVEL = [0.72, 0.38, 0.55, 0.18]
W, H, BAR_H, INSET = 120, 220, 10, 4
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
    y = round(H - 2 - BAR_H - LEVEL[i] * (H - 4 - BAR_H - 10))
    out.append(f'  <path d="{path([(x + INSET, y), (x + W - INSET, y), (x + W - INSET, y + BAR_H), (x + INSET, y + BAR_H)])}" '
               f'fill="{BAR[i]}" stroke="none" stroke-width="0"/>')
out.append("</svg>")
open(sys.argv[1], "w").write("\n".join(out) + "\n")
