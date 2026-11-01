#!/usr/bin/env python3
"""Toro's screen: stacked blocks (round 3's s4-iso, taken through the protocol).

A field of isometric columns whose heights are a small model of toro's voice, so turning a knob reshapes the field
the way it reshapes the sound:

  spread  the second oscillator's ratio: a second, slower wave runs across the field at that ratio, so the two
          waves beat into a moiré of ridges
  fold    the wavefolder: heights fold back on themselves, so ridges split into terraces
  cutoff  the filter: low = the two broad waves only; high = a fine ripple of harmonics on top
  res     the resonant peak: one row of tops lights up, moving front to back with the setting
  shape   saw → triangle: the main wave's ridges go from a sharp leading edge to symmetric
  noise   jitter in every column
  drive   soft clip: the tallest columns are flattened to a plateau
  aphx    per-key drift: each column wanders by its own amount, different for every key
  a note  a patch of six columns, placed by the key, jumps up and flashes white, then settles in ~0.4 s

On the device. Every column is three nodes (top, left face, right face). The side faces are fixed-length pillars that
move with the top, so a column changes height by translation alone, never by reshaping. Columns are drawn back to
front, so each pillar's overhang is hidden by the columns in front; the overhang of the front row is hidden by two
black skirt nodes drawn last. No mutable outlines are needed. A note moves 18 nodes; idle moves none.

    python3 screens/toro/gen_blocks.py
"""
from __future__ import annotations

import json
import math
import random
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen_frames as g  # noqa: E402

W, H = 480, 220
OUT = HERE / "blocks"
PREFIX = "toro"
NX, NY, S = 10, 7, 15                                      # columns along x and y; half-width of a cube in px
OX, OY = 240 - (NX - NY) * S / 2, 92                         # where column (0, 0)'s base centre sits
H_MIN, H_MAX = 8, 40                                       # column heights in px
PILLAR = 12                                                # side faces: a slab this thick, so the field can wrap round a drum
PATHS = 0
HEADER_FIRST = 0
f, poly, G, fold_signal = g.f, g.poly, g.G, g.fold_signal

# palette: (fill, stroke, width). Strokes match fills so faces meet without seams.
PALETTE = [(G[1], G[1], 0.3), (G[3], G[3], 0.3), (G[4], G[4], 0.3), (G[5], G[5], 0.3), (G[6], G[6], 0.3),
           (G[7], G[7], 0.3), ("#000000", "#000000", 0.3), ("#FFFFFF", "#FFFFFF", 0.3),
           ("#000000", G[4], 0.9), ("#000000", G[6], 0.9)]
P_RIGHT, P_LEFT, P_TOP_LO, P_TOP_MID, P_TOP_HI, P_LIT, P_BLACK, P_FLASH, P_WIRE, P_WIRE_TOP = range(10)
WIRE_BELOW = 0.3                                           # cubes in the lowest 30% of the voice's range are drawn hollow
KEY_SPOTS = [(2, 2), (6, 1), (4, 4), (8, 3), (1, 5), (5, 6), (7, 5), (3, 1)]   # where each key's patch lands


def kink(a):
    return 0.4 * a + 0.6 * a ** 3


def base_xy(i, j):
    return OX + (i - j) * S, OY + (i + j) * S * 0.5


# ---- the field: toro's voice as heights ----------------------------------------------------------------------------
def heights(v: dict, key: int = 0, phase: float = 0.0) -> list[list[float]]:
    ratio = 1 + 0.5 * v["spread"]
    gain = 1 + 7 * v["fold"]
    rnd = random.Random(4)
    out = [[0.0] * NY for _ in range(NX)]
    for i in range(NX):
        for j in range(NY):
            u, w = i / (NX - 1), j / (NY - 1)
            ph = (0.8 * u + 0.4 * w + phase) % 1
            saw = 2 * ph - 1
            tri = 1 - 4 * abs(ph - 0.5)
            osc1 = saw * (1 - v["shape"]) + tri * v["shape"]
            osc2 = 0.6 * math.sin(2 * math.pi * ratio * (0.6 * w - 0.5 * u + phase) + 1)
            detail = v["cutoff"] * 0.7 * math.sin(2 * math.pi * (3.3 * u + 2.1 * w) + 0.5)
            raw = 0.45 * (osc1 + osc2) + detail
            hv = fold_signal(gain * raw) if v["fold"] > 0.02 else max(-1.0, min(1.0, raw))
            hv = min(1 - 0.6 * v["drive"], hv)
            hv += v["noise"] * 0.5 * (rnd.random() - 0.5)
            hv += kink(v["aphx"]) * 0.45 * math.sin(i * 2.1 + j * 1.3 + key * 1.7)
            out[i][j] = H_MIN + (H_MAX - H_MIN) * (max(-1.0, min(1.0, hv)) + 1) / 2
    return out


def note(t):
    """a note's lift and flash over time t (s since note-on)"""
    if t is None:
        return 0.0, False
    return 22 * math.exp(-t / 0.18) if t >= 0 else 0.0, t < 0.12


# ---- nodes -------------------------------------------------------------------------------------------------------------
def top_pts():
    return [(0, 0), (S, S * 0.5), (0, S), (-S, S * 0.5)]


def left_pts():
    return [(-S, S * 0.5), (0, S), (0, S + PILLAR), (-S, S * 0.5 + PILLAR)]


def right_pts():
    return [(0, S), (S, S * 0.5), (S, S * 0.5 + PILLAR), (0, S + PILLAR)]


def skirts():
    """two black shapes below the field's front edges, drawn last, hiding the front pillars' overhang"""
    fx, fy = base_xy(NX - 1, NY - 1)                     # the front corner column's base
    lx, ly = base_xy(0, NY - 1)                          # left end of the front-left edge
    rx, ry = base_xy(NX - 1, 0)                          # right end of the front-right edge
    left = [(lx - S - 2, ly + S * 0.5 - 1), (fx, fy + S), (fx, 220 + 40), (lx - S - 2, 220 + 40)]    # 2 px past the edge: no seam
    right = [(fx, fy + S), (rx + S + 2, ry + S * 0.5 - 1), (rx + S + 2, 220 + 40), (fx, 220 + 40)]
    return left, right


ORDER = sorted([(i, j) for i in range(NX) for j in range(NY)], key=lambda c: (c[0] + c[1], c[0]))
FIRST_COL = HEADER_FIRST + 8                               # nodes 0..7: the two-page header bar
COL_INDEX = {c: FIRST_COL + 3 * k for k, c in enumerate(ORDER)}   # +0 left, +1 right, +2 top
SKIRT_FIRST = FIRST_COL + 3 * len(ORDER)
NODES = SKIRT_FIRST + 2


class Pose:
    def __init__(self, x, y, palette, visible=True):
        self.x, self.y, self.palette, self.visible = x, y, palette, visible


RIPPLE_SPEED, RIPPLE_WIDTH, RIPPLE_HEIGHT, RIPPLE_DECAY = 14.0, 1.3, 11.0, 0.55   # columns/s, columns, px, s
PHASE_STEP, PHASE_EASE = 0.11, 0.22                                           # cycles per note, s


def ease(t, tau):
    return 1 - math.exp(-t / tau) if t is not None else 1.0


ROLL_ARC, ROW_PX, RELIEF_SHRINK, ROLL_SPREAD, ROLL_DROP = 1.9 * math.pi, 16.8, 0.92, 0.5, 14    # arc the field wraps at fold 1 (~280°); px per row upward; relief cut
ROLL_MID = (NX - 1) / 2                                    # the row that stays on top as the field wraps


def roll_amount(fold: float) -> float:
    """0 at fold 0 (flat field) to 1 at fold 1 (wrapped almost all the way round)"""
    s = max(0.0, fold - 0.05) / 0.95
    return 0.5 - 0.5 * math.cos(math.pi * s)


def rolled_top(i: int, j: int, h: float, c: float) -> tuple[float, float, float]:
    """where column (i, j)'s top face sits (h: how far it stands out, px) when the field is wrapped round a cylinder lying along j.

    The field bends into an arc of ROLL_ARC·c with its middle row on top, so at fold 0 it's flat and at fold 1 it's
    almost a closed drum. Each column's height becomes how far it stands out from the drum, along the surface's
    outward normal, so the voice's relief turns into blocks pushing out of the cylinder. The arc's ends rest on the
    floor. The display can only slide a node, so each cube stays upright and slides to its place; the rows are drawn
    back to front, so the back of the drum is drawn first and the front last. Returns (x, y, angle from the top)."""
    A = ROLL_ARC * c
    sp = 1 + ROLL_SPREAD * c                                 # rows part a little as they wrap, so the drum's staves read
    L = NX * sp
    if A < 1e-4:
        bx, by = base_xy(i, j)
        return bx, by - h, 0.0
    R = L / A
    psi = (i - ROLL_MID) * sp * A / L
    lift = R * (1 - math.cos(min(A / 2, math.pi)))           # rows: raise the top so the arc's ends touch the floor
    along = R * math.sin(psi) + (h / ROW_PX) * math.sin(psi)
    up_px = (lift - R * (1 - math.cos(psi))) * ROW_PX + h * math.cos(psi)
    px, py = OX + (ROLL_MID - j) * S, OY + (ROLL_MID + j) * S * 0.5
    return px + along * S, py + along * S * 0.5 - up_px + ROLL_DROP * c, psi


def pose(v: dict, t=None, key: int = 0, notes: int = 0) -> dict[int, Pose]:
    """`notes` counts notes played before this one: every note rolls the whole field forward a step (the wave
    travelling), and sends a ripple out from where it lands"""
    phase = PHASE_STEP * (notes + (ease(t, PHASE_EASE) if t is not None else 0))
    hs = heights(v, key, phase)
    lift, flash = note(t)
    ci, cj = KEY_SPOTS[key % len(KEY_SPOTS)]
    patch = {(ci + di, cj + dj) for di in (-1, 0, 1) for dj in (-1, 0, 1) if abs(di) + abs(dj) <= 1 or (di, dj) == (1, 1)}
    lit_row = round((NY - 1) * v["res"]) if v["res"] > 0.05 else None
    c = roll_amount(v["fold"])
    out = {}
    for (i, j), n in COL_INDEX.items():
        # as the field wraps, the voice's own relief sinks into the drum's surface, and notes push blocks out of it
        h = H_MIN + (hs[i][j] - H_MIN) * (1 - RELIEF_SHRINK * c) + (lift * (1.0 if (i, j) == (ci, cj) else 0.6) if (i, j) in patch else 0.0)
        if t is not None:                                        # the ripple: a ring spreading from the patch
            d = math.hypot(i - ci, j - cj)
            ring = math.exp(-((d - RIPPLE_SPEED * t) / RIPPLE_WIDTH) ** 2) * math.exp(-t / RIPPLE_DECAY)
            h += RIPPLE_HEIGHT * ring
        h = round(h)                                             # whole pixels: crisp edges, and a column only redraws when it really moves
        tx, ty, psi = rolled_top(i, j, h, c)
        tx, ty = round(tx), round(ty)
        top = P_TOP_HI if h > 0.75 * H_MAX else P_TOP_MID if h > 0.45 * H_MAX else P_TOP_LO
        if j == lit_row:
            top = P_LIT
        if math.cos(psi) < -0.2:                                # on the drum's underside: the top faces away, so it's dark
            top = P_TOP_LO if top != P_FLASH else top
        if flash and (i, j) in patch:
            top = P_FLASH
        # the quiet part of the wave is hollow: black faces with grey edges. Decided on the voice's own height (before
        # notes and the drum's flattening), so it follows the sound; a struck or lit cube stays solid
        wire = hs[i][j] < H_MIN + WIRE_BELOW * (H_MAX - H_MIN) and top not in (P_FLASH, P_LIT)
        out[n] = Pose(tx, ty, P_WIRE if wire else P_LEFT)
        out[n + 1] = Pose(tx, ty, P_WIRE if wire else P_RIGHT)
        out[n + 2] = Pose(tx, ty, P_WIRE_TOP if wire else top)
    # the skirts only existed to mask floor-length pillars; slabs don't overhang, and a skirt would cut into the drum
    out[SKIRT_FIRST] = Pose(0, 0, P_BLACK, visible=False)
    out[SKIRT_FIRST + 1] = Pose(0, 0, P_BLACK, visible=False)
    return out


def node_pts(n):
    if n >= SKIRT_FIRST:
        return skirts()[n - SKIRT_FIRST]
    return (left_pts, right_pts, top_pts)[(n - FIRST_COL) % 3]()


# ---- rendering -------------------------------------------------------------------------------------------------------
def node_svg(n: int, q: Pose) -> str:
    fill, stroke, width = PALETTE[q.palette]
    x, y = (q.x, q.y) if q.visible else (640, 320)
    return f'<path id="{PREFIX}_node_{n}" transform="matrix(1 0 0 1 {f(x)} {f(y)})" d="{poly(node_pts(n))}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'


def header_fragment() -> list[str]:
    o = ['<!-- SDK two-page header: keep this block before machine artwork below y=38. -->',
         '<path d="M0,0 L480,0 L480,38 L0,38 Z" fill="#000000" stroke="none"/>']
    for i in range(8):
        o.append(f'<path id="{PREFIX}_node_{HEADER_FIRST + i}" transform="matrix(1 0 0 1 {60 * i} 0)" d="M0,0 L60,0 L60,20 L0,20 Z" fill="{G[i]}" stroke="{G[i]}" stroke-width="0.5"/>')
    for k in range(4):
        o.append(f'<text id="{PREFIX}_text_{k}" transform="matrix(1 0 0 1 {5 + 120 * k} 10)" fill="{"#CBCBCB" if k < 2 else "#000000"}" font-family="UniversNextPro-Light" font-size="10px">-</text>')
    for k in range(4):
        o.append(f'<text id="{PREFIX}_text_{4 + k}" transform="matrix(1 0 0 1 {65 + 120 * k} 17.4)" fill="{"#CBCBCB" if k < 2 else "#000000"}" font-family="UniversNextPro-Light" font-size="20px">-</text>')
    for k in range(4):
        o.append(f'<text id="{PREFIX}_text_{8 + k}" transform="matrix(1 0 0 1 {5 + 120 * k} 33)" fill="#5A5A5A" font-family="UniversNextPro-Light" font-size="10px">-</text>')
    for k in range(4):
        o.append(f'<text id="{PREFIX}_text_{12 + k}" transform="matrix(1 0 0 1 {65 + 120 * k} 33)" fill="#707070" font-family="UniversNextPro-Light" font-size="13px">-</text>')
    return o


def body(v, t=None, key=0, notes=0) -> list[str]:
    poses = pose(v, t, key, notes)
    return [node_svg(n, poses[n]) for n in sorted(poses)]


def frame_svg(v, t=None, key=0, notes=0) -> str:
    return "\n".join(['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
                      '<rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>'] + body(v, t, key, notes) + g.header(v) + ["</svg>"])


def fragment_svg() -> str:
    o = [f'<g id="{PREFIX}_panel">'] + header_fragment() + body(dict(g.DEFAULTS))
    for i, (fill, stroke, width) in enumerate(PALETTE):
        o.append(f'<path id="{PREFIX}_palette_{i}" transform="matrix(1 0 0 1 640 320)" d="M0,0 L4,0 L4,4 L0,4 Z" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')
    return "\n".join(o + ["</g>"])


def export_model() -> dict:
    return {"nx": NX, "ny": NY, "s": S, "ox": OX, "oy": OY, "hMin": H_MIN, "hMax": H_MAX, "pillar": PILLAR,
            "palette": PALETTE, "order": ORDER, "colIndex": {f"{i},{j}": n for (i, j), n in COL_INDEX.items()},
            "skirtFirst": SKIRT_FIRST, "skirts": skirts(), "keySpots": KEY_SPOTS, "defaults": g.DEFAULTS,
            "controls": g.CONTROLS, "greys": G}


def board(names, out):
    cols, P_ = 4, 8
    rows = math.ceil(len(names) / cols)
    sheet = Image.new("RGB", (P_ + cols * (W + P_), P_ + rows * (H + 18 + P_)), (40, 40, 40))
    d = ImageDraw.Draw(sheet)
    with tempfile.TemporaryDirectory() as tmp:
        for k, name in enumerate(names):
            png = Path(tmp) / f"{name}.png"
            subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(OUT / "frames" / f"{name}.svg"), "-o", str(png)], check=True)
            x, y = P_ + (k % cols) * (W + P_), P_ + (k // cols) * (H + 18 + P_)
            label = name if not name.startswith("c") else f"{g.CONTROLS[int(name[1]) - 1]} {int(name[-3:])}"
            d.text((x, y), label, fill=(200, 200, 200))
            sheet.paste(Image.open(png).convert("RGB"), (x, y + 18))
    sheet.save(out)


def main():
    (OUT / "frames").mkdir(parents=True, exist_ok=True)
    D = dict(g.DEFAULTS)
    frames = {"rest": (D, None, 0), "playing": (D, 0.12, 0), "note-0.2s": (D, 0.2, 0), "note-key4": (D, 0.12, 3)}
    for i, name in enumerate(g.CONTROLS):
        for val in (0, 50, 100):
            frames[f"c{i + 1}-{val:03d}"] = (dict(D, **{name: val / 100}), None, 0)
    for name, (vals, t, key) in frames.items():
        (OUT / "frames" / f"{name}.svg").write_text(frame_svg(vals, t, key), encoding="utf-8")
    (OUT / "panel.svg.fragment").write_text(fragment_svg(), encoding="utf-8")
    (OUT / "panel-lint.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">\n' + fragment_svg() + "\n</svg>", encoding="utf-8")
    (OUT / "model.json").write_text(json.dumps(export_model()))
    info = {"nodes": NODES, "paths": PATHS, "texts": 16, "palette": len(PALETTE), "columns": NX * NY, "noteNodes": 18}
    (OUT / "budget.json").write_text(json.dumps(info, indent=2))
    print(json.dumps(info))
    board(list(frames), OUT / "board.png")


if __name__ == "__main__":
    main()
