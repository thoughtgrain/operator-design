"""Mock rest frame for P16 Context strip: a wavetable engine (illustration only, not a machine).

The drawing is the selected wavetable frame, large, with its two neighbours behind it in depth. Above it, a locator
of all 32 frames in the same drawing language (each frame a small tick sized by its brightness), an outlined bracket
on the selected frame, and two hairline callout leaders down to the close-up, the way a technical drawing marks a
detail. Usage: python3 mock_strip.py OUT.svg
"""
import math
import sys

FRAMES, SEL = 32, 13
X0, X1 = 60.0, 420.0            # the drawing's width; the locator follows it, not the full screen
STRIP_TOP, STRIP_BASE = 23.0, 33.0
SUBJ_Y, SUBJ_AMP = 128.0, 54.0
f = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")


def wave(t: float, m: float) -> float:
    """A frame of the table: sine morphing toward a band-limited saw as m goes 0 → 1."""
    saw = sum(math.sin(2 * math.pi * k * t) / k for k in range(1, 7)) * 0.62
    return (1 - m) * math.sin(2 * math.pi * t) + m * saw


def brightness(m: float) -> float:
    return 0.25 + 0.75 * m ** 0.8


def ribbon(points, width):
    """A thin closed ribbon along a polyline: one edge out, the other back `width` px below. ≤ 64 points."""
    top = [(x, y) for x, y in points]
    back = [(x, y + width) for x, y in reversed(points)]
    pts = top + back
    assert len(pts) <= 64
    # start mid-way along the long top edge, so the closing edge isn't a short end
    k = len(top) // 2
    pts = pts[k:] + pts[:k]
    return "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"


def rect(x, y, w, h):
    return f"M {f(x)} {f(y)} L {f(x + w)} {f(y)} L {f(x + w)} {f(y + h)} L {f(x)} {f(y + h)} Z"


def quad(a, b, c, d):
    return "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in (a, b, c, d)) + " Z"


def frame_points(m, dx=0.0, dy=0.0, n=31):
    return [(X0 + dx + (X1 - X0 - dx) * i / (n - 1), SUBJ_Y + dy - SUBJ_AMP * wave(i / (n - 1), m)) for i in range(n)]


out = []
add = out.append
add('<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">')
add("  <!-- P16 Context strip, mock rest frame (illustration only): a wavetable engine. -->")
add('  <g id="preview_canvas"><rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/></g>')
add('  <g id="preview_header">')
for i, g in enumerate(["#000000", "#323232", "#4B4B4B", "#646464", "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD"]):
    add(f'    <rect x="{60 * i}" y="0" width="60" height="20" fill="{g}" stroke="none"/>')
for i, (t, v) in enumerate([("pos", "13"), ("warp", "40"), ("tone", "62"), ("level", "80")]):
    c = "#CBCBCB" if i < 2 else "#000000"
    add(f'    <text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{c}" stroke="none" font-family="UniversNextPro-Light" font-size="10px">{t}</text>')
    add(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{c}" stroke="none" font-family="UniversNextPro-Light" font-size="20px">{v}</text>')
add("  </g>")

# locator: a hairline baseline, then one tick per frame, sized by that frame's brightness
step = (X1 - X0) / (FRAMES - 1)
add(f'  <path d="{rect(X0, STRIP_BASE, X1 - X0, 1)}" fill="#4B4B4B" stroke="none" stroke-width="0"/>')
for i in range(FRAMES):
    m = i / (FRAMES - 1)
    h = 2 + 7 * brightness(m)
    x = X0 + i * step - 0.5
    shade = "#969696" if i == SEL else "#646464"
    add(f'  <path d="{rect(x, STRIP_BASE - h, 1, h)}" fill="{shade}" stroke="none" stroke-width="0"/>')

# bracket: an outlined window on the selected frame (not a filled bar)
bx = X0 + SEL * step
add(f'  <path d="{rect(bx - 4.5, STRIP_TOP - 1, 9, STRIP_BASE - STRIP_TOP + 3)}" fill="none" stroke="#AFAFAF" stroke-width="1.5"/>')

# the close-up's frame: corner marks, as a technical drawing marks a detail
CROP_TOP, CROP_BOT, ARM = SUBJ_Y - SUBJ_AMP - 10, SUBJ_Y + SUBJ_AMP + 22, 8
for xe, sgn in ((X0 - 4, 1), (X1 + 4, -1)):
    xa = xe if sgn > 0 else xe - 1
    add(f'  <path d="{rect(xa, CROP_TOP, 1, ARM)}" fill="#646464" stroke="none" stroke-width="0"/>')
    add(f'  <path d="{rect(min(xe, xe + sgn * ARM), CROP_TOP, ARM, 1)}" fill="#646464" stroke="none" stroke-width="0"/>')

# callout leaders: from the bracket's foot to those corners, hairline, decoration grey
foot = STRIP_BASE + 2.75
for xe in (X0 - 4, X1 + 4):
    sgn = -1 if xe < bx else 1
    a, b = (bx + sgn * 4.5, foot), (xe, CROP_TOP)
    add(f'  <path d="{quad(a, (a[0] - sgn * 1, a[1]), (b[0] - sgn * 1, b[1]), b)}" fill="#4B4B4B" stroke="none" stroke-width="0"/>')

# the drawing: neighbours behind in depth, the selected frame in front and brightest
for k, (dx, dy, g) in enumerate([(14, -10, "#4B4B4B"), (7, -5, "#646464")]):
    m = (SEL - 2 + k) / (FRAMES - 1)
    add(f'  <path d="{ribbon(frame_points(m, dx, dy), 1.5)}" fill="{g}" stroke="none" stroke-width="0"/>')
add(f'  <path d="{ribbon(frame_points(SEL / (FRAMES - 1), n=32), 2.5)}" fill="#CDCDCD" stroke="none" stroke-width="0"/>')
# bottom corner marks close the detail frame
for xe, sgn in ((X0 - 4, 1), (X1 + 4, -1)):
    xa = xe if sgn > 0 else xe - 1
    add(f'  <path d="{rect(xa, CROP_BOT - ARM + 1, 1, ARM)}" fill="#646464" stroke="none" stroke-width="0"/>')
    add(f'  <path d="{rect(min(xe, xe + sgn * ARM), CROP_BOT, ARM, 1)}" fill="#646464" stroke="none" stroke-width="0"/>')
add("</svg>")
open(sys.argv[1], "w").write("\n".join(out) + "\n")
