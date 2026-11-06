"""Mock rest frame for P18 Control tiles: a tremolo effect, "pulse" (illustration only, not a machine).

The page is light tiles on black, the way the stock modulator pages are built, and the tiles take the whole screen:
the artwork covers y 0-20, which hides the stock header (display.md, Artwork). One tile per encoder, each marked in
its top-left corner with the encoder's dot in the encoder grey code (1 black, 2 dark grey, 3 mid grey, 4 an outline),
and its label outside the tile, lower case, above the top row and below the bottom row. One more tile, with no dot
because no encoder owns it, shows what the four do together.

Each control tile holds one glyph that moves in one channel:
  depth    a ruler of static ticks (1 px, 6 px apart) and a pointer node that slides up it (position, 56 px)
  rate     the same ruler on its side, the pointer sliding along it
  attack   a rising line that turns about its foot, steep for fast and shallow for slow (rotation)
  release  a falling line that turns the same way
The result tile is one mutable outline (32 points, filled black): the gain over a few cycles, drawn from the
controls, not from audio (the rate sets how many cycles it shows, and the 30 points are shared out a
cycle at a time so every peak lands on one), since an effect page gets no signal (constraints.md, Which machines draw a screen). Every
control reshapes it as well as its own glyph, so each one changes enough of the screen to read.

Usage: python3 mock_tiles.py OUT.svg
"""
import math
import sys

TILE, INK, LABEL = "#CDCDCD", "#000000", "#CDCDCD"
DEPTH, RATE, ATTACK, RELEASE = 0.6, 0.35, 0.3, 0.7
FONT = 'font-family="UniversNextPro-Light" font-size="10"'
f = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")


def path(points):
    return "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in points) + " Z"


def bar(x0, y0, x1, y1, w=1.5):
    """A straight stroke as a thin filled outline."""
    dx, dy = x1 - x0, y1 - y0
    n = math.hypot(dx, dy)
    ox, oy = -dy / n * w / 2, dx / n * w / 2
    return path([(x0 + ox, y0 + oy), (x1 + ox, y1 + oy), (x1 - ox, y1 - oy), (x0 - ox, y0 - oy)])


out = ['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
       '  <!-- P18 Control tiles, mock rest frame (illustration only): a tremolo effect. -->',
       '  <g id="preview_canvas"><rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/></g>',
       f'  <path d="{path([(0, 0), (480, 0), (480, 20), (0, 20)])}" fill="#000000" stroke="none" stroke-width="0"/>']
add = out.append


def tile(x, y, w, h):
    add(f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{TILE}" stroke="none" stroke-width="0"/>')


def label(text, x, y):
    add(f'  <text x="{x}" y="{y}" {FONT} fill="{LABEL}" stroke="none" stroke-width="0">{text}</text>')


def dot(x, y, k):
    if k < 3:
        add(f'  <circle cx="{x}" cy="{y}" r="4" fill="{["#000000", "#4B4B4B", "#969696"][k]}" stroke="none" stroke-width="0"/>')
    else:
        add(f'  <circle cx="{x}" cy="{y}" r="3.25" fill="none" stroke="#000000" stroke-width="1.5"/>')


# the result: gain over time, from the controls
RX, RY, RW, RH = 16, 32, 220, 168
tile(RX, RY, RW, RH)
label("pulse", RX + 2, 26)
cycles = 3                                   # rate picks the count of cycles shown; 30 points share them
top, base = RY + 24, RY + RH - 16
n = 30 // cycles                             # points a cycle, so every peak lands on a point
a = ATTACK * 0.5 + 0.05                      # the rise, as a share of a cycle
pts = []
for c in range(cycles):
    phases = [0, a] + [a + (1 - a) * (j / (n - 2)) ** 1.6 for j in range(1, n - 1)]
    for t in phases:
        g = 1 - DEPTH if t == 0 else (1 - DEPTH * (1 - t / a) if t <= a
                                       else 1 - DEPTH * (1 - math.exp(-(t - a) / (0.08 + RELEASE * 0.35))))
        x = RX + 12 + (c + t) / cycles * (RW - 24) - (0.5 if t == 1 and c < cycles - 1 else 0)
        pts.append((x, base - g * (base - top)))
pts += [(RX + RW - 12, base), (RX + 12, base)]
assert len(pts) == 32
add(f'  <path d="{path(pts)}" fill="{INK}" stroke="none" stroke-width="0"/>')

# the controls: 2 x 2
CW, CH = 110, 80
cells = [("depth", 244, 32, 0, "above"), ("rate", 362, 32, 1, "above"),
         ("attack", 244, 120, 2, "below"), ("release", 362, 120, 3, "below")]
for name, x, y, k, where in cells:
    tile(x, y, CW, CH)
    dot(x + 11, y + 11, k)
    label(name, x + 2, 26 if where == "above" else 214)

# depth: vertical ruler and pointer
x, y = 244, 32
for j in range(10):
    ty = y + 12 + j * 6
    add(f'  <path d="{path([(x + 70, ty), (x + 82, ty), (x + 82, ty + 1), (x + 70, ty + 1)])}" fill="{INK}" stroke="none" stroke-width="0"/>')
py = y + 12 + (1 - DEPTH) * 54
add(f'  <path d="{path([(x + 46, py - 5), (x + 60, py - 5), (x + 66, py + 0.5), (x + 60, py + 6), (x + 46, py + 6)])}" fill="{INK}" stroke="none" stroke-width="0"/>')

# rate: horizontal ruler and pointer
x, y = 362, 32
for j in range(13):
    tx = x + 18 + j * 6
    add(f'  <path d="{path([(tx, y + 52), (tx + 1, y + 52), (tx + 1, y + 64), (tx, y + 64)])}" fill="{INK}" stroke="none" stroke-width="0"/>')
px = x + 18 + RATE * 72
add(f'  <path d="{path([(px - 5.5, y + 32), (px + 6.5, y + 32), (px + 6.5, y + 42), (px + 0.5, y + 48), (px - 5.5, y + 42)])}" fill="{INK}" stroke="none" stroke-width="0"/>')

# attack and release: lines turning about a foot
L = 62
for (x, y, v, rising) in ((244, 120, ATTACK, True), (362, 120, RELEASE, False)):
    ang = math.radians(75 - v * 55)            # fast is steep, slow is shallow
    if rising:
        fx, fy = x + 24, y + 68
        add(f'  <path d="{bar(fx, fy, fx + L * math.cos(ang), fy - L * math.sin(ang) * 0.85)}" fill="{INK}" stroke="none" stroke-width="0"/>')
    else:
        fx, fy = x + 24, y + 16
        add(f'  <path d="{bar(fx, fy, fx + L * math.cos(ang), fy + L * math.sin(ang) * 0.85)}" fill="{INK}" stroke="none" stroke-width="0"/>')
add("</svg>")
open(sys.argv[1], "w").write("\n".join(out) + "\n")
