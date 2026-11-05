"""Mock rest frame for P16 Context strip: a multisample synth (illustration only, not a machine).

The drawing is a close-up of the sample the selected zone plays: its envelope as a silhouette inside corner marks.
Above it, the map: the keyboard the engine covers, split into its zones, with a tick per C, and an open bracket
above the zone the controls select. Each bracket piece is two of the frame's corners joined by an upright,
one closed outline; only weight and grey differ.

Usage: python3 mock_strip.py OUT.svg
"""
import math
import sys

X0, X1 = 48, 432                  # the drawing's frame; the map lines up with it, not the header's columns
OCTAVES = 6                        # the engine maps C1..C7
KEY = (X1 - X0) / (12 * OCTAVES)   # 384 / 72 = 5.33 px a key here (width / keys, not 480 / 128)
GAP, TOP, BASE = 6, 26, 33         # 6 px under the stock header (y 20); the map is y 26-35
ARM, W, BH = 7, 1.5, 6             # shared corner arm; bracket weight; bracket height (y 26-32, 1 px clear of the baseline)
ZONES = [0, 18, 30, 43, 51, 61, 72]   # zone splits, in keys from C1
SEL = 2                            # the zone the controls select: keys 30..42 (F#3..F#4)
FRAME_TOP, FRAME_BOT = 50, 204
f = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")


def path(points):
    return "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in points) + " Z"


def rect(x, y, w, h):
    return path([(x, y), (x + w, y), (x + w, y + h), (x, y + h)])


def kx(key):
    return round(X0 + key * KEY)


out = []
add = out.append
add('<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">')
add("  <!-- P16 Context strip, mock rest frame (illustration only): a multisample synth. -->")
add('  <g id="preview_canvas"><rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/></g>')
add('  <g id="preview_header">')
for i, g in enumerate(["#000000", "#323232", "#4B4B4B", "#646464", "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD"]):
    add(f'    <rect x="{60 * i}" y="0" width="60" height="20" fill="{g}" stroke="none"/>')
for i, (t, v) in enumerate([("zone", "3"), ("tune", "0"), ("tone", "62"), ("level", "80")]):
    c = "#CBCBCB" if i < 2 else "#000000"
    add(f'    <text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{c}" stroke="none" font-family="UniversNextPro-Light" font-size="10px">{t}</text>')
    add(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{c}" stroke="none" font-family="UniversNextPro-Light" font-size="20px">{v}</text>')
add("  </g>")

# the map: zones as 2 px segments of the baseline, split by 3 px gaps (position, not shade, tells them apart)
for a, b in zip(ZONES, ZONES[1:]):
    xa, xb = kx(a) + (2 if a else 0), kx(b) - (1 if b < ZONES[-1] else 0)
    add(f'  <path d="{rect(xa, BASE, xb - xa, 2)}" fill="#646464" stroke="none" stroke-width="0"/>')
# a tick per C, uniform, on whole pixels: a guide, so hairline
for o in range(OCTAVES + 1):
    x = min(kx(12 * o), X1 - 1)
    add(f'  <path d="{rect(x, BASE - 4, 1, 4)}" fill="#646464" stroke="none" stroke-width="0"/>')

# the bracket: two pieces, each one closed 8-point outline, uprights centred over the selected zone's split gaps
def piece(xc, s):
    """A '[' (s=1) or ']' (s=-1): two frame corners joined by an upright, centred on x = xc."""
    x, y = xc - s * W / 2, TOP
    pts = [(x, y), (x + s * ARM, y), (x + s * ARM, y + W), (x + s * W, y + W),
           (x + s * W, y + BH - W), (x + s * ARM, y + BH - W), (x + s * ARM, y + BH), (x, y + BH)]
    return pts if s > 0 else list(reversed(pts))
for k, s in ((ZONES[SEL], 1), (ZONES[SEL + 1], -1)):
    gap_centre = kx(k) + 0.5          # the split gap runs kx-1 .. kx+2
    add(f'  <path d="{path(piece(gap_centre, s))}" fill="#AFAFAF" stroke="none" stroke-width="0"/>')

# the close-up's frame: corner marks at the map's ends, the same 7 px arm, hairline, quieter; one outline each
def corner(x, y, sx, sy, w=1):
    pts = [(x, y), (x + sx * ARM, y), (x + sx * ARM, y + sy * w), (x + sx * w, y + sy * w), (x + sx * w, y + sy * ARM), (x, y + sy * ARM)]
    return pts if sx * sy > 0 else list(reversed(pts))
for x, sx in ((X0, 1), (X1, -1)):
    for y, sy in ((FRAME_TOP, 1), (FRAME_BOT, -1)):
        add(f'  <path d="{path(corner(x, y, sx, sy))}" fill="#646464" stroke="none" stroke-width="0"/>')

# the drawing: the selected zone's sample as an envelope silhouette, bright edge, dark body
N, MID = 31, (FRAME_TOP + FRAME_BOT) / 2
def amp(t):
    attack = min(1.0, t / 0.05)
    return max(1.5, 66 * attack * math.exp(-2.6 * t) * (0.88 + 0.12 * math.sin(t * 23)))
top = [(X0 + 8 + (X1 - X0 - 16) * i / (N - 1), MID - amp(i / (N - 1))) for i in range(N)]
bot = [(x, MID + (MID - y) * 0.92) for x, y in reversed(top)]
pts = top + bot
pts = pts[N // 2:] + pts[:N // 2]           # start mid-way along a long edge
add(f'  <path d="{path(pts)}" fill="#323232" stroke="#CDCDCD" stroke-width="2"/>')
# the centre line, hairline guide
add(f'  <path d="{rect(X0 + 8, round(MID), X1 - X0 - 16, 1)}" fill="#4B4B4B" stroke="none" stroke-width="0"/>')
add("</svg>")
open(sys.argv[1], "w").write("\n".join(out) + "\n")
