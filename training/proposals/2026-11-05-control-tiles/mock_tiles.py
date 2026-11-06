"""Mock rest frame for P18 Control tiles (draft): a tremolo effect, "pulse" (illustration only, not a machine).

Light tiles on black take the whole screen: a static black backing covers y 0-20, which hides the stock header
(display.md, Artwork). One tile per encoder in reading order (encoders 1-4: top left, top right, bottom left, bottom
right), each marked in its top-left corner with the encoder's dot (1 black, 2 #4B4B4B, 3 #969696 with a black
outline so it clears 3:1 on the tile, 4 a black ring). Outside each tile, its title (10 px, #969696) and its value in
real units (13 px, #CDCDCD): the machine's own header text, eight text slots. One more tile, with no dot and no label
because no encoder owns it, shows what the four do together.

Tiles are single-subpath outlines with their corners cut in short segments, and text is placed by transform, so
open-xy's local preview takes them as well as the device build.

Each control tile holds one glyph that moves in one channel; the two pairs share a channel, but each glyph has its
own tile, so place keeps them apart:
  depth    a ruler of static ticks (1.5 px, 6 px apart) and a pointer node that slides up it (position, 54 px)
  rate     the same ruler on its side, the pointer sliding along it (position, 72 px)
  attack   a rising line turning about its foot (rotation, 60 deg: 80 deg above level when fast, 20 when slow)
  release  a falling line turning about its foot (rotation, 60 deg: 80 deg below level when fast, 20 when slow)
Each glyph moves with its own encoder only; it agrees with the result by direction (a steeper line is a faster rise
or fall in both). Glyph weights: the turning lines at the 1.5 px Line weight, ruler ticks 1.5 px wide (heavier than
craft.md's hairline on purpose: black hairlines on a light tile break up at 1:1), pointers small solid shapes.
The result tile is one mutable outline (32 points, filled black) at scale 2, authored within +-49 x +-32 so it
spans 196 x 128 px drawn: the gain over a few cycles, drawn from the controls, not from audio, since an effect page
gets no audio signal. Rate sets how many cycles it shows (2 + round(4 x rate)); 30 points are shared out a cycle at a
time (the remainder to the last cycles) so every peak lands on one; each peak has a 2 px flat top, so no tooth is a
needle, and the shortest rise is a tenth of a cycle; and the curve stays at least 1 px above the two bottom corners. Every setting gives 32 distinct points with no
turn within 2.5 deg of straight back (`--check` sweeps the controls and asserts both).

Usage: python3 mock_tiles.py OUT.svg [--thin]  (--thin: deepest dips, fastest rate and attack, slowest release)
       python3 mock_tiles.py --check
"""
import math
import sys

TILE, INK, TITLE, VALUE = "#CDCDCD", "#000000", "#969696", "#CDCDCD"
DEPTH, RATE, ATTACK, RELEASE = (1.0, 1.0, 0.0, 1.0) if "--thin" in sys.argv else (0.6, 0.35, 0.3, 0.7)
VALUES = ["100", "8.0hz", "4ms", "800ms"] if "--thin" in sys.argv else ["60", "2.1hz", "24ms", "180ms"]
f = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")


def path(points):
    return "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in points) + " Z"


def bar(x0, y0, x1, y1, w=1.5):
    dx, dy = x1 - x0, y1 - y0
    n = math.hypot(dx, dy)
    ox, oy = -dy / n * w / 2, dx / n * w / 2
    return path([(x0 + ox, y0 + oy), (x1 + ox, y1 + oy), (x1 - ox, y1 - oy), (x0 - ox, y0 - oy)])


def tile_outline(x, y, w, h, r=6, seg=3):
    """A rounded rectangle as one closed outline: each corner cut in `seg` short segments."""
    pts = []
    for cx, cy, a0 in ((x + w - r, y + r, -90), (x + w - r, y + h - r, 0), (x + r, y + h - r, 90), (x + r, y + r, 180)):
        for k in range(seg + 1):
            a = math.radians(a0 + 90 * k / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


out = ['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
       '  <!-- P18 Control tiles, mock rest frame (illustration only): a tremolo effect. -->',
       '  <g id="preview_canvas"><rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/></g>',
       f'  <path d="{path([(0, 0), (480, 0), (480, 20), (0, 20)])}" fill="#000000" stroke="none" stroke-width="0"/>']
add = out.append


def tile(x, y, w, h):
    add(f'  <path d="{path(tile_outline(x, y, w, h))}" fill="{TILE}" stroke="none" stroke-width="0"/>')


def text(s, x, y, size, fill):
    add(f'  <text transform="matrix(1 0 0 1 {f(x)} {f(y)})" font-family="UniversNextPro-Light" font-size="{size}" '
        f'fill="{fill}" stroke="none" stroke-width="0">{s}</text>')


def dot(x, y, k):
    if k < 2:
        add(f'  <circle cx="{x}" cy="{y}" r="4" fill="{["#000000", "#4B4B4B"][k]}" stroke="none" stroke-width="0"/>')
    elif k == 2:
        add(f'  <circle cx="{x}" cy="{y}" r="3.25" fill="#969696" stroke="#000000" stroke-width="1.5"/>')
    else:
        add(f'  <circle cx="{x}" cy="{y}" r="3.25" fill="none" stroke="#000000" stroke-width="1.5"/>')


# the result: gain over time, from the controls
RX, RY, RW, RH = 16, 32, 220, 168
top, base = RY + 24, RY + RH - 16


def result_points(depth, rate, attack, release):
    cycles = 2 + round(4 * rate)
    counts = [30 // cycles + (1 if k >= cycles - 30 % cycles else 0) for k in range(cycles)]
    a = attack * 0.5 + 0.1                   # the rise, as a share of a cycle (never a needle)
    tau = 0.08 + release * 0.35              # the fall's time constant, as a share of a cycle
    cw = (RW - 24) / cycles
    pts = []
    for c, n in enumerate(counts):
        flat = 2.0 / cw                       # a 2 px flat top on each peak, so no tooth is a needle
        phases = [0, a, a + flat] + [a + flat + (1 - a - flat) * (j / (n - 3)) ** 1.6 for j in range(1, n - 2)]
        for t in phases:
            g = 1 - depth if t == 0 else (1 - depth * (1 - t / a) if t <= a else
                                         1 if t <= a + flat + 1e-9 else 1 - depth * (1 - math.exp(-(t - a - flat) / tau)))
            x = RX + 12 + (c + t) * cw - (1.5 if abs(t - 1) < 1e-9 and c < cycles - 1 else 0)
            pts.append((x, min(base - 1, base - g * (base - top))))
    pts += [(RX + RW - 12, base + 1), (RX + 12, base + 1)]
    return pts


if "--check" in sys.argv:
    steps = [i / 8 for i in range(9)] + [0.99]
    worst = 0
    for d in steps:
        for r in steps:
            for at in steps:
                for rl in steps:
                    pts = result_points(d, r, at, rl)
                    assert len(pts) == 32, (d, r, at, rl, len(pts))
                    for i in range(32):
                        x0, y0 = pts[i]; x1, y1 = pts[(i + 1) % 32]
                        assert math.hypot(x1 - x0, y1 - y0) >= 0.25, (d, r, at, rl, i)
                        xp, yp = pts[i - 1]
                        u = (x0 - xp, y0 - yp); v = (x1 - x0, y1 - y0)
                        ang = math.degrees(math.acos(max(-1, min(1, (u[0] * v[0] + u[1] * v[1]) / (math.hypot(*u) * math.hypot(*v))))))
                        worst = max(worst, ang)
                        assert 180 - ang >= 2.5, (d, r, at, rl, i, 180 - ang)
    print(f"32 distinct points, at least 0.25 px apart, no turn within 2.5 deg of straight back (sharpest {180 - worst:.2f} deg), at every setting on the grid")
    sys.exit(0)

tile(RX, RY, RW, RH)
pts = result_points(DEPTH, RATE, ATTACK, RELEASE)
assert len(pts) == 32
add(f'  <path d="{path(pts)}" fill="{INK}" stroke="none" stroke-width="0"/>')

# the controls: 2 x 2, encoders 1-4 in reading order
CW, CH = 110, 80
cells = [("depth", 244, 32, 0, "above"), ("rate", 362, 32, 1, "above"),
         ("attack", 244, 120, 2, "below"), ("release", 362, 120, 3, "below")]
for (name, x, y, k, where), value in zip(cells, VALUES):
    tile(x, y, CW, CH)
    dot(x + 11, y + 11, k)
    ty = 26 if where == "above" else 214
    text(name, x + 2, ty, 10, TITLE)
    text(value, x + CW - 2 - len(value) * 13 * 0.64, ty + 1, 13, VALUE)

# depth: vertical ruler and pointer
x, y = 244, 32
for j in range(10):
    ty = y + 12 + j * 6
    add(f'  <path d="{path([(x + 70, ty), (x + 82, ty), (x + 82, ty + 1.5), (x + 70, ty + 1.5)])}" fill="{INK}" stroke="none" stroke-width="0"/>')
py = y + 12 + (1 - DEPTH) * 54
add(f'  <path d="{path([(x + 46, py - 5), (x + 60, py - 5), (x + 66, py + 0.5), (x + 60, py + 6), (x + 46, py + 6)])}" fill="{INK}" stroke="none" stroke-width="0"/>')

# rate: horizontal ruler and pointer
x, y = 362, 32
for j in range(13):
    tx = x + 18 + j * 6
    add(f'  <path d="{path([(tx, y + 52), (tx + 1.5, y + 52), (tx + 1.5, y + 64), (tx, y + 64)])}" fill="{INK}" stroke="none" stroke-width="0"/>')
px = x + 18 + RATE * 72
add(f'  <path d="{path([(px - 5.5, y + 32), (px + 6.5, y + 32), (px + 6.5, y + 42), (px + 0.5, y + 48), (px - 5.5, y + 42)])}" fill="{INK}" stroke="none" stroke-width="0"/>')

# attack and release: lines turning about a foot, each with its own encoder only (60 deg of travel)
L = 60
rise = math.radians(80 - 60 * ATTACK)       # fast attack is steep
fall = math.radians(80 - 60 * RELEASE)      # fast release is steep
fx, fy = 244 + 30, 120 + 68
add(f'  <path d="{bar(fx, fy, fx + L * math.cos(rise), fy - L * math.sin(rise))}" fill="{INK}" stroke="none" stroke-width="0"/>')
fx, fy = 362 + 24, 120 + 16
add(f'  <path d="{bar(fx, fy, fx + L * math.cos(fall), fy + L * math.sin(fall))}" fill="{INK}" stroke="none" stroke-width="0"/>')
add("</svg>")
open(sys.argv[1], "w").write("\n".join(out) + "\n")
