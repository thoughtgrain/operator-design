#!/usr/bin/env python3
"""Toro round 10: the owner's own one-bit bull, traced from two photos of the real screen and driven by toro's controls.

References (opxy/reference/): toro-ink-rest.jpg is the rest state, toro-ink-smoke.jpg is the same screen with the
steam up. I crop each photo to the display's active area and box-resample it to 480 × 220, one sample per display
pixel. Solid lines (a 3 × 3 neighbourhood mostly white) and lone dots are kept as they are; everything else is a
dithered region whose local density I quantise to 0/25/50/75/100 % and redraw as ordered (Bayer) dither. That gives
pixel-exact art that matches the photo without the camera's moiré. The same `regularise` pass runs after any raster
move, so the dither never smears. The steam is the difference between the two traces, kept as its own layer.

Control map (toro's eight):
  spread  horns scale outward from their roots      shape  the waveform glyphs morph saw → triangle
  fold    heat squiggles appear and tighten          noise  sparkles and grain fill the air
  cutoff  the eyes: dead → glint → wide open         drive  the steam comes out, puff by puff from the nostrils
  res     the burst beside the muzzle grows          aphx   the dither swatches slip, per key, with a torn scanline
  a note: the eyes flash and the steam flares a step further

    python3 screens/toro/concepts/ink_trace.py [--debug]
"""
from __future__ import annotations

import math
import random
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation, uniform_filter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import gen_frames as g  # noqa: E402

W, H, TOP = 480, 220, 40
REFDIR = HERE.parent.parent.parent / "opxy" / "reference"
REST = (REFDIR / "toro-ink-rest.jpg", (83, 71, 1283, 687))        # photo, display's active area in it
SMOKE = (REFDIR / "toro-ink-smoke.jpg", (66, 50, 966, 512))
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0 + 1 / 32
_yy, _xx = np.mgrid[0:H, 0:W]
BAY = BAYER[_yy % 4, _xx % 4]

# regions in logical px, read off the rest trace at 2×
HORN_L = (138, 42, 192, 102)
HORN_R = (276, 42, 332, 102)
EYES = ((210, 124, 12), (267, 124, 12))
FACE = (198, 76, 278, 150)
NOSE = (240, 166)
BURST = (150, 150)
WAVE = (78, 165, 150, 200)
WAVE_SMALL = (400, 98, 452, 130)
BLOCKS = [(90, 42, 128, 80), (90, 102, 125, 135), (362, 58, 396, 92), (366, 120, 398, 152)]
SQUIGGLES = [(140, 100), (62, 128), (345, 92), (300, 182)]
HEAD = (138, 42, 334, 180)                    # horns, ears, face and muzzle; the neck at the bottom edge stays put
TUFT = (368, 52, 404, 94)
PLUMES = [(44, 78), (120, 76), (152, 98), (226, 148), (226, 180), (150, 172), (88, 162), (40, 130)], \
         [(254, 150), (300, 118), (360, 98), (392, 76), (434, 82), (438, 120), (402, 142), (332, 160), (254, 180)]


# ---- tracing ---------------------------------------------------------------------------------------------------------
def regularise(on: np.ndarray, mask=None) -> np.ndarray:
    """keep solid lines and lone dots; redraw every dithered region as Bayer at its local density"""
    n3 = uniform_filter(on.astype(float), 3) * 9
    d5 = uniform_filter(on.astype(float), 5)
    tone = np.round(d5 * 4) / 4
    out = BAY < tone
    out[on & (n3 >= 6)] = True
    out[on & (n3 <= 2) & (d5 < 0.15)] = True
    out[~on & (n3 <= 1)] = False
    if mask is not None:
        out = np.where(mask, out, on)
    return out


def trace(ref, thresh=0.5, black=28, white=225) -> np.ndarray:
    path, box = ref
    im = Image.open(path).convert("L").crop(box).resize((W, H), Image.BOX)
    gray = np.clip((np.array(im).astype(float) - black) / (white - black), 0, 1)
    out = regularise(gray > thresh)
    out[:TOP] = False
    return out


def _cached(name, fn):
    p = HERE / "i2-trace" / name
    if p.exists():
        return np.array(Image.open(p).convert("L")) > 127
    p.parent.mkdir(exist_ok=True)
    out = fn()
    Image.fromarray((out * 255).astype("uint8")).save(p)
    return out


def base() -> np.ndarray:
    return _cached("base.png", lambda: trace(REST))


def smoke() -> tuple[np.ndarray, np.ndarray]:
    """the steam: the smoke trace, and the mask of where it differs from the rest trace"""
    def build():
        m = poly_mask(PLUMES[0]) | poly_mask(PLUMES[1])      # the two traces align within 2 px, so the plume regions can simply swap
        for keep in ((196, 70, 280, 150), (214, 150, 266, 180), (368, 52, 404, 92), WAVE_SMALL):   # the face, chin, tail tuft and right glyph stay the rest art
            m &= ~box_mask(keep)
        return m
    m = _cached("smoke-mask.png", build)
    s = _cached("smoke.png", lambda: trace(SMOKE))
    return s, m


# ---- raster region ops ------------------------------------------------------------------------------------------------
def poly_mask(pts) -> np.ndarray:
    im = Image.new("L", (W, H), 0)
    ImageDraw.Draw(im).polygon([(round(x), round(y)) for x, y in pts], fill=255)
    return np.array(im) > 0


def box_mask(b) -> np.ndarray:
    m = np.zeros((H, W), bool)
    m[b[1]:b[3], b[0]:b[2]] = True
    return m


def retone(px: np.ndarray, mask: np.ndarray, delta: float) -> None:
    """shift a region's dither density by `delta`, keeping its lines"""
    n3 = uniform_filter(px.astype(float), 3) * 9
    d5 = uniform_filter(px.astype(float), 5)
    lines = px & (n3 >= 6)
    tone = np.clip(np.round((d5 + delta) * 4) / 4, 0, 1)
    new = BAY < tone
    new[lines] = True
    px[mask] = new[mask]


def scale_region(px: np.ndarray, b, sx: float, sy: float, anchor: str) -> None:
    """scale a box's pixels, nearest-neighbour, keeping one corner ('bl' or 'br') fixed; then regularise"""
    x0, y0, x1, y1 = b
    src = Image.fromarray((px[y0:y1, x0:x1] * 255).astype("uint8"))
    nw, nh = max(1, round((x1 - x0) * sx)), max(1, round((y1 - y0) * sy))
    dst = np.array(src.resize((nw, nh), Image.NEAREST)) > 127
    px[y0:y1, x0:x1] = False
    ty = y1 - nh
    tx = x0 if anchor == "bl" else x1 - nw
    cy0, cx0 = max(0, ty), max(0, tx)
    sub = dst[cy0 - ty:, cx0 - tx:]
    sub = sub[: H - cy0, : W - cx0]
    px[cy0:cy0 + sub.shape[0], cx0:cx0 + sub.shape[1]] |= sub
    m = np.zeros((H, W), bool)
    m[cy0:cy0 + sub.shape[0], cx0:cx0 + sub.shape[1]] = True
    px[:] = regularise(px, m)


def skew_region(px: np.ndarray, b, amp: float) -> None:
    """lean a box sideways: each row shifts by amp at the top, tapering to 0 at the bottom (a head on a neck)"""
    x0, y0, x1, y1 = b
    src = px[y0:y1, x0:x1].copy()
    px[y0:y1, x0:x1] = False
    for i in range(y1 - y0):
        dx = int(round(amp * (1 - i / (y1 - y0))))
        tx = x0 + dx
        row = src[i]
        lo, hi = max(0, tx), min(W, tx + row.shape[0])
        px[y0 + i, lo:hi] |= row[lo - tx:hi - tx]


def shift_region(px: np.ndarray, b, dx: int, dy: int = 0) -> None:
    x0, y0, x1, y1 = b
    src = px[y0:y1, x0:x1].copy()
    px[y0:y1, x0:x1] = False
    tx0, ty0 = max(0, x0 + dx), max(0, y0 + dy)
    sub = src[ty0 - (y0 + dy):, tx0 - (x0 + dx):][: H - ty0, : W - tx0]
    px[ty0:ty0 + sub.shape[0], tx0:tx0 + sub.shape[1]] = sub


# ---- vector marks (drawn in white, PIL) --------------------------------------------------------------------------------
class Pen:
    def __init__(self, px):
        self.px = px

    def _draw(self, fn, value=True):
        im = Image.new("L", (W, H), 0)
        fn(ImageDraw.Draw(im))
        self.px[np.array(im) > 0] = value

    def line(self, pts, w=2, value=True):
        self._draw(lambda d: d.line([(round(x), round(y)) for x, y in pts], fill=255, width=w, joint="curve"), value)

    def disc(self, x, y, r, value=True):
        self._draw(lambda d: d.ellipse([x - r, y - r, x + r, y + r], fill=255), value)

    def ring(self, x, y, r, w=2):
        self._draw(lambda d: d.ellipse([x - r, y - r, x + r, y + r], outline=255, width=w))

    def tone_disc(self, x, y, r, tone):
        im = Image.new("L", (W, H), 0)
        ImageDraw.Draw(im).ellipse([x - r, y - r, x + r, y + r], fill=255)
        m = np.array(im) > 0
        self.px[m] = (BAY < tone)[m]

    def sparkle(self, x, y, r, rays=4, w=1):
        for k in range(rays):
            a = math.pi * k / rays
            self.line([(x - r * math.cos(a), y - r * math.sin(a)), (x + r * math.cos(a), y + r * math.sin(a))], w)

    def burst(self, x, y, r, rays=8):
        """the reference's sun-burst mark: short rays with a gap at the centre"""
        self.px[int(y - r - 2):int(y + r + 3), int(x - r - 2):int(x + r + 3)] = False
        for k in range(rays):
            a = 2 * math.pi * k / rays
            self.line([(x + r * 0.45 * math.cos(a), y + r * 0.45 * math.sin(a)), (x + r * math.cos(a), y + r * math.sin(a))], 2 if r > 8 else 1)

    def squiggle(self, x, y, length, amp, turns):
        pts = [(x + amp * math.sin(t / length * turns * 2 * math.pi), y + t) for t in range(0, int(length) + 1, 2)]
        self.line(pts, 2)

    def wave(self, b, shape_v, bar=4, gain=1.0):
        """the reference's bar glyph: a symmetric envelope that shape morphs from a saw ramp to a triangle"""
        x0, y0, x1, y1 = b
        self.px[y0 - 4:y1 + 4, x0:x1] = False
        n = (x1 - x0) // bar
        cy = (y0 + y1) / 2
        hmax = (y1 - y0) / 2 - 1
        for i in range(n):
            u = i / (n - 1)
            tri = 1 - abs(2 * u - 1)
            saw = (u * 2) if u < 0.5 else 1 - ((u - 0.5) * 2)
            saw = saw ** 3                                            # a sharp spike, the saw's edge
            env = tri * shape_v + saw * (1 - shape_v)
            h = max(1.5, min(hmax + 4, hmax * (0.12 + 0.88 * env) * gain))
            x = x0 + i * bar + 1
            self.line([(x, cy - h), (x, cy + h)], 2)


# ---- the frame ---------------------------------------------------------------------------------------------------------
def kink(a):
    return 0.4 * a + 0.6 * a ** 3


def note(t):
    """what a note does over time t (s): a decaying side-to-side wobble, a flash, a flare of steam"""
    if t is None:
        return dict(wobble=0.0, flash=0.0, flare=0.0, pulse=0.0)
    env = math.exp(-t / 0.5)
    return dict(wobble=7 * math.sin(2 * math.pi * 2.2 * t) * env, flash=1.0 if t < 0.15 else 0.0,
                flare=0.25 * math.exp(-t / 0.6), pulse=env)


def frame(v, playing=False, key=0) -> np.ndarray:
    """`playing` is False, or the time in seconds since note-on (True means 0.05 s)"""
    t = None if playing is False else (0.05 if playing is True else float(playing))
    n = note(t)
    playing = t is not None
    px = base().copy()
    pen = Pen(px)
    D = g.DEFAULTS

    # drive: the steam comes out of the nostrils and reaches further the harder toro is driven; a note flares it
    reach = v["drive"] + n["flare"]
    if reach > 0.02:
        s, m = smoke()
        dist = np.hypot(_xx - NOSE[0], _yy - NOSE[1])
        near = m & (dist < 24 + 200 * min(1.0, reach))
        px[near] = s[near]

    # spread: horns scale outward about their roots
    k = 1 + 0.42 * (v["spread"] - D["spread"]) / (1 - D["spread"]) if v["spread"] >= D["spread"] else 1 - 0.1 * (D["spread"] - v["spread"]) / D["spread"]
    if abs(k - 1) > 0.01:
        scale_region(px, HORN_L, k, 1 + (k - 1) * 0.5, "br")
        scale_region(px, HORN_R, k, 1 + (k - 1) * 0.5, "bl")

    # cutoff: the eyes. dead at 0, the reference's glint by the middle, wide open at 100; a note flashes them
    cut = v["cutoff"]
    d0 = D["cutoff"]
    open_ = max(n["flash"], (cut - d0) / (1 - d0))                 # above the default the white fills in; a note flashes them wide
    glint = 3 * min(1.0, cut / d0)                                 # below it the glint shrinks away: dead eyes at 0
    for (ex, ey, er) in EYES:
        pen.disc(ex, ey, er + 1, False)
        pen.tone_disc(ex, ey, er - 2, open_)
        pen.ring(ex, ey, er, 2)
        if open_ > 0.6:
            pen.disc(ex + 1, ey - 1, 3.5, False)                   # a black pupil in a wide white eye
        elif glint >= 1:
            gx, gy = int(ex + 2 - glint / 2), int(ey - 1 - glint / 2)
            px[gy:gy + int(round(glint)), gx:gx + int(round(glint))] = True   # the reference's square glint

    # a note: the head wobbles side to side on its neck (horns, ears and face lean together) and the tail tuft flicks
    if abs(n["wobble"]) >= 0.5:
        skew_region(px, HEAD, n["wobble"])
        shift_region(px, TUFT, int(round(-n["wobble"] * 0.3)), int(round(-abs(n["wobble"]) * 0.3)))

    # res: the burst beside the muzzle grows
    pen.burst(*BURST, 4 + 10 * v["res"], rays=8 if v["res"] > 0.5 else 6)

    # fold: heat squiggles appear and tighten
    n_sq = round(4 * v["fold"])
    for i, (sx, sy) in enumerate(SQUIGGLES[:n_sq]):
        px[sy - 2:sy + 30, sx - 6:sx + 6] = False
        pen.squiggle(sx, sy, 26, 3.5, 1.5 + 1.5 * v["fold"])

    # noise: sparkles and grain
    rnd = random.Random(5)
    for i in range(round(24 * v["noise"])):
        x, y = rnd.uniform(20, 460), rnd.uniform(TOP + 6, 212)
        if i % 4 == 0:
            pen.sparkle(x, y, 3 + 3 * v["noise"])
        else:
            px[int(y), int(x)] = True

    # shape: the waveform glyphs morph
    pen.wave(WAVE, 1 - v["shape"], gain=1 + 0.35 * n["pulse"])
    pen.wave(WAVE_SMALL, 1 - v["shape"], bar=3, gain=1 + 0.35 * n["pulse"])

    # aphx: the dither swatches slip, per key, with a torn scanline
    slip = kink(v["aphx"]) * (1 + 0.3 * n["pulse"])
    if slip > 0.03:
        rk = random.Random(21 + key)
        for b in BLOCKS:
            dx = int(round(slip * 18 * (rk.random() - 0.5) * 2))
            shift_region(px, b, dx)
            ty = (b[1] + b[3]) // 2
            px[ty:ty + 2, max(0, b[0] - dx):min(W, b[2] - dx)] = True
    px[:TOP] = False
    return px


def header(v) -> Image.Image:
    svg = "\n".join(['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="38" viewBox="0 0 480 38">'] + g.header(v) + ["</svg>"])
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / "h.svg").write_text(svg)
        subprocess.run(["rsvg-convert", "-w", "480", "-h", "38", str(p / "h.svg"), "-o", str(p / "h.png")], check=True)
        return Image.open(p / "h.png").convert("RGB")


def image(v, playing=False, key=0) -> Image.Image:
    im = Image.fromarray((frame(v, playing, key) * 255).astype("uint8"), "L").convert("RGB")
    im.paste(header(v), (0, 0))
    return im


def debug_overlay() -> Image.Image:
    s, m = smoke()
    rgb = np.zeros((H, W, 3), np.uint8)
    rgb[..., 0] = rgb[..., 1] = rgb[..., 2] = base() * 255
    rgb[m & s] = (90, 200, 255)
    im = Image.fromarray(rgb).resize((960, 440), Image.NEAREST)
    d = ImageDraw.Draw(im)
    S = lambda p: (p[0] * 2, p[1] * 2)
    for b in (HORN_L, HORN_R, FACE, WAVE, WAVE_SMALL, *BLOCKS):
        d.rectangle([S(b[:2]), S(b[2:])], outline=(255, 80, 80))
    for ex, ey, er in EYES:
        d.ellipse([S((ex - er, ey - er)), S((ex + er, ey + er))], outline=(80, 255, 80))
    d.ellipse([S((BURST[0] - 8, BURST[1] - 8)), S((BURST[0] + 8, BURST[1] + 8))], outline=(80, 255, 80))
    for sx, sy in SQUIGGLES:
        d.rectangle([S((sx - 6, sy - 2)), S((sx + 6, sy + 30))], outline=(255, 255, 80))
    return im


def main():
    if "--debug" in sys.argv:
        debug_overlay().save(HERE / "i2-trace" / "debug.png")
        print("wrote debug.png")
        return
    D = dict(g.DEFAULTS)
    poses = {"rest": (D, False), "spread-100": (dict(D, spread=1), False), "cutoff-000": (dict(D, cutoff=0), False),
             "cutoff-100": (dict(D, cutoff=1), False), "fold-shape-100": (dict(D, fold=1, shape=1), False), "drive-50": (dict(D, drive=0.5), False),
             "drive-res-100": (dict(D, drive=1, res=1), False), "noise-aphx-100": (dict(D, noise=1, aphx=1), False),
             "note-0.05s": (D, 0.05), "note-0.25s": (D, 0.25), "note-0.6s": (D, 0.6)}
    d = HERE / "i2-trace"
    d.mkdir(exist_ok=True)
    tiles = []
    for pose, (vals, playing) in poses.items():
        im = image(vals, playing)
        im.save(d / f"{pose}.png")
        tiles.append((pose, im))
    P_, cols = 8, 2
    rows = math.ceil(len(tiles) / cols)
    board = Image.new("RGB", (P_ + cols * (W + P_), P_ + rows * (H + 18 + P_)), (40, 40, 40))
    dr = ImageDraw.Draw(board)
    for i, (pose, im) in enumerate(tiles):
        x, y = P_ + (i % cols) * (W + P_), P_ + (i // cols) * (H + 18 + P_)
        dr.text((x, y), pose, fill=(200, 200, 200))
        board.paste(im, (x, y + 18))
    board.save(HERE / "board-trace.png")
    print("wrote", len(tiles), "frames")


if __name__ == "__main__":
    main()
