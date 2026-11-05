"""Mock rest frame for P16 Context strip, in-header form: a multisample synth (illustration only, not a machine).

The map replaces the stock header (the artwork covers y 0-20, which hides it; display.md, Artwork). The band is the
whole range the engine maps as a plain grey bar, one 60 px segment per octave over eight octaves, an echo of the
stock header's eight 60 px steps. Only the part the controls pick is drawn as real keys, at the same scale, in a
brighter grey: one octave as one closed outline (white keys with the black keys and key gaps notched in), so it's
one node and moves by sliding. No titles, no values, no text slots. The approach follows the stock multisampler page
(the whole range plain, the playable span as keys); the artwork is drawn here, not copied.

Below the band is the drawing: the selected zone's sample as an envelope silhouette inside corner marks.

Usage: python3 mock_header.py OUT.svg
"""
import math
import sys

OCT_W = 60                        # one octave per 60 px, eight across the screen
SEL_OCT = 4                       # the window sits on the fifth octave (x 240-300)
WK = OCT_W / 7                    # 8.57 px a white key
BAND_H = 19                       # y 0-19, a black row at 19 under it
ARM = 7
X0, X1, FRAME_TOP, FRAME_BOT = 48, 432, 34, 206
f = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")


def path(points):
    return "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in points) + " Z"


def rect(x, y, w, h):
    return path([(x, y), (x + w, y), (x + w, y + h), (x, y + h)])


def octave_outline(x0):
    """One octave of keys as a single closed outline: the white keys' area, with each black key notched in from the
    top (to y 11) and each key gap notched in from the bottom (1 px wide). E-F and B-C gaps stop 2 px short of the
    top so the outline stays one piece. 52 points."""
    black = {0: True, 1: True, 2: False, 3: True, 4: True, 5: True, 6: False}   # a black key after C D _ F G A _
    top, bottom = [(x0, 0)], []
    for k in range(1, 7):
        gx = x0 + k * WK
        if black[k - 1]:
            top += [(gx - 2.5, 0), (gx - 2.5, 11), (gx + 2.5, 11), (gx + 2.5, 0)]
            bottom += [(gx - 0.5, BAND_H), (gx - 0.5, 11.5), (gx + 0.5, 11.5), (gx + 0.5, BAND_H)]
        else:
            bottom += [(gx - 0.5, BAND_H), (gx - 0.5, 2), (gx + 0.5, 2), (gx + 0.5, BAND_H)]
    top += [(x0 + OCT_W - 1, 0), (x0 + OCT_W - 1, BAND_H)]
    pts = top + list(reversed(bottom)) + [(x0, BAND_H)]
    assert len(pts) <= 64, len(pts)
    return pts


out = []
add = out.append
add('<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">')
add("  <!-- P16 Context strip, in-header form, mock rest frame (illustration only): a multisample synth. -->")
add('  <g id="preview_canvas"><rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/></g>')
add(f'  <path d="{rect(0, 0, 480, 20)}" fill="#000000" stroke="none" stroke-width="0"/>')

# the whole range: eight plain octave segments with 1 px gaps (static artwork)
for o in range(8):
    add(f'  <path d="{rect(o * OCT_W, 0, OCT_W - 1, BAND_H)}" fill="#4B4B4B" stroke="none" stroke-width="0"/>')

# the part the controls pick: one octave drawn as keys, one outline, one node; it covers its segment
x0 = SEL_OCT * OCT_W
add(f'  <path d="{rect(x0, 0, OCT_W - 1, BAND_H)}" fill="#000000" stroke="none" stroke-width="0"/>')
add(f'  <path d="{path(octave_outline(x0))}" fill="#AFAFAF" stroke="none" stroke-width="0"/>')


def corner(x, y, sx, sy, w=1):
    pts = [(x, y), (x + sx * ARM, y), (x + sx * ARM, y + sy * w), (x + sx * w, y + sy * w), (x + sx * w, y + sy * ARM), (x, y + sy * ARM)]
    return pts if sx * sy > 0 else list(reversed(pts))


for x, sx in ((X0, 1), (X1, -1)):
    for y, sy in ((FRAME_TOP, 1), (FRAME_BOT, -1)):
        add(f'  <path d="{path(corner(x, y, sx, sy))}" fill="#646464" stroke="none" stroke-width="0"/>')

N, MID = 31, (FRAME_TOP + FRAME_BOT) / 2
def amp(t):
    attack = min(1.0, t / 0.05)
    return max(1.5, 70 * attack * math.exp(-2.4 * t) * (0.88 + 0.12 * math.sin(t * 19)))
top = [(X0 + 8 + (X1 - X0 - 16) * i / (N - 1), MID - amp(i / (N - 1))) for i in range(N)]
bot = [(x, MID + (MID - y) * 0.92) for x, y in reversed(top)]
pts = top + bot
pts = pts[N // 2:] + pts[:N // 2]
add(f'  <path d="{path(pts)}" fill="#323232" stroke="#CDCDCD" stroke-width="2"/>')
add(f'  <path d="{rect(X0 + 8, round(MID), X1 - X0 - 16, 1)}" fill="#4B4B4B" stroke="none" stroke-width="0"/>')
add("</svg>")
open(sys.argv[1], "w").write("\n".join(out) + "\n")
