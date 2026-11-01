#!/usr/bin/env python3
"""meikyu player page, p2 wheels (picked from round 1): panel fragment, preview frames and board.

The register is a pair of dials: the A half's eight steps on the outer wheel, the B half's on the inner, step 0 at
the top and running clockwise. A step's lamp is lit when it plays at the current density, so Dens visibly empties or
fills the wheels and Corrupt shows up as lamps changing between phrases. The last phrase's eight tones are lamps on
an arc to the right, read left to right, lit where a tone sounded.

The page ABI is the one meikyu's player.cpp already drives, so this is a drop-in for labyrinth's gen_panel.py:
  dots 0..7    A steps (outer wheel)        dots 8..15  B steps (inner wheel)
  dots 16..23  phrase tones, first to last  meikyu_text the line ("D A phrase 5"), centred at x 240
  meikyu_key_* / meikyu_played_*            parked off screen; the SDK lays the keyboard out at y 174

Everything is grey line drawing: static rings and lamp sockets in mid grey, lamps (the dots) near white.

    python3 gen_wheels.py      → panel.svg.fragment, panel-lint.svg, frames/*.svg, board.png
"""
from __future__ import annotations

import math
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "concepts"))
import pages as P  # noqa: E402  (Page model, stock header and keyboard preview)

PREFIX = "meikyu"
RING, SOCKET, LAMP, LABEL, INK = "#6E6E6E", "#4A4A4A", "#F0F0F0", "#A4A4A4", "#000000"

# the dials
DX, DY = 132, 88                       # centre
R_RIM, R_A, R_MID, R_B, R_HUB = 56, 46, 37, 27, 14
LAMP_A, LAMP_B = 4.6, 3.8              # lamp radii; sockets are 1.6 px wider
# the phrase arc
AX, AY, AR = 352, 150, 84              # centre (below the lamps) and radius
A0, A1 = math.radians(200), math.radians(340)
LAMP_P = 5.4


def f(v: float) -> str:
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def circle_pts(cx, cy, r, n=48, a0=0.0, a1=2 * math.pi):
    return [(cx + r * math.cos(a0 + (a1 - a0) * k / n), cy + r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]


def stroke(pts, color=RING, w=1.2, close=False):
    d = "M" + " L".join(f"{f(x)},{f(y)}" for x, y in pts) + (" Z" if close else "")
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>'


def socket(x, y, r):
    """the unlit lamp: a dark disc with a grey rim, static art under the dot"""
    return f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r + 1.6)}" fill="{INK}" stroke="{SOCKET}" stroke-width="1"/>'


def lamp(k, x, y, r):
    return f'<circle id="{PREFIX}_dot_{k}" transform="matrix(1 0 0 1 {f(x)} {f(y)})" cx="0" cy="0" r="{f(r)}" fill="{LAMP}" stroke="{LAMP}" stroke-width="0.5"/>'


def label(x, y, s, size=10, color=LABEL, anchor="middle"):
    return f'<text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{color}" font-family="UniversNextPro-Light" font-size="{size}" text-anchor="{anchor}">{s}</text>'


def step_xy(i):
    """step i's lamp: 0..7 on the outer wheel, 8..15 on the inner, step 0 at the top, clockwise; each half's lamps sit
    between the eight spokes"""
    r = R_A if i < 8 else R_B
    a = -math.pi / 2 + 2 * math.pi * ((i % 8) + 0.5) / 8
    return DX + r * math.cos(a), DY + r * math.sin(a)


def tone_xy(k):
    a = A0 + (A1 - A0) * k / 7
    return AX + AR * math.cos(a), AY + AR * math.sin(a)


def static_art() -> list[str]:
    o = ['<rect x="0" y="20" width="480" height="200" fill="#000000" stroke="none"/>']
    # the dials: rim, the ring between the halves, the hub, and eight spokes from hub to rim
    for r, w in ((R_RIM, 1.4), (R_MID, 1.0), (R_HUB, 1.0)):
        o.append(stroke(circle_pts(DX, DY, r), RING, w, close=True))
    for s in range(8):
        a = -math.pi / 2 + 2 * math.pi * s / 8
        o.append(stroke([(DX + R_HUB * math.cos(a), DY + R_HUB * math.sin(a)), (DX + R_RIM * math.cos(a), DY + R_RIM * math.sin(a))], SOCKET, 0.8))
    # the index: a notch above step 0, where both halves start
    o.append(stroke([(DX - 4, DY - R_RIM - 6), (DX, DY - R_RIM - 1), (DX + 4, DY - R_RIM - 6)], LABEL, 1.2))
    o.append(label(DX + 9, DY - R_RIM - 1, "A", 11, LABEL, "start"))
    o.append(label(DX, DY + 4, "B", 11, LABEL))
    for i in range(16):
        o.append(socket(*step_xy(i), LAMP_A if i < 8 else LAMP_B))
    # the phrase: an arc of eight sockets under a rim, read left to right
    o.append(stroke(circle_pts(AX, AY, AR + 12, 40, A0 - 0.06, A1 + 0.06), RING, 1.0))
    for k in range(8):
        x, y = tone_xy(k)
        o.append(socket(x, y, LAMP_P))
        a = A0 + (A1 - A0) * k / 7
        o.append(label(AX + (AR - 16) * math.cos(a), AY + (AR - 16) * math.sin(a) + 3.5, str(k + 1), 9))
    return o


def lamps() -> list[tuple[int, float, float, float]]:
    out = [(i, *step_xy(i), LAMP_A if i < 8 else LAMP_B) for i in range(16)]
    return out + [(16 + k, *tone_xy(k), LAMP_P) for k in range(8)]


def fragment() -> str:
    """the device artwork, in the format labyrinth's gen_panel.py writes"""
    o = [f'<g id="{PREFIX}_panel">'] + static_art()
    o += [lamp(k, x, y, r) for k, x, y, r in lamps()]
    o.append(f'<text id="{PREFIX}_text" transform="matrix(1 0 0 1 240 157)" fill="#F2F2F2" font-family="UniversNextPro-Light" font-size="18" text-anchor="middle">meikyu</text>')

    def black(n):
        return n % 12 in (1, 3, 6, 8, 10)
    for is_black in (False, True):                       # the SDK lays these out; they're authored parked off screen
        for n in range(128):
            if black(n) != is_black:
                continue
            w, h = (6, 27) if is_black else (10, 44)
            o.append(f'<path id="{PREFIX}_key_{n}" transform="matrix(1 0 0 1 1024 174)" d="M0 0 H{w} V{h} H0 Z" fill="{"#000000" if is_black else "#F0F0F0"}" stroke="#000000" stroke-width="0.5"/>')
    for n in range(128):
        fill = "#F0F0F0" if black(n) else "#000000"
        o.append(f'<circle id="{PREFIX}_played_{n}" transform="matrix(1 0 0 1 1024 0)" cx="0" cy="0" r="2.5" fill="{fill}" stroke="{fill}" stroke-width="0.5"/>')
    o.append("</g>")
    return "\n".join(o)


def frame(p: P.Page) -> str:
    """a preview frame: static art, the lit lamps, the stock header and the SDK's keyboard as it would draw them"""
    lit = [p.step_lit(i) for i in range(16)] + [p.tone_lit(k) for k in range(8)]
    body = static_art() + [lamp(k, x, y, r) for k, x, y, r in lamps() if lit[k]]
    return "\n".join(['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
                      '<rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>'] + body + P.footer(p) + P.header(p) + ["</svg>"])


POSES = {
    "rest": P.Page(),
    "phrase-a": P.Page(phrase=0b10110111, root=62, start=0, count=5),
    "phrase-b": P.Page(phrase=0b01101101, root=57, start=8, count=6, scale=2),
    "dens-000": P.Page(density=0.0, phrase=0, root=62, start=8, count=7),
    "dens-050": P.Page(density=0.5, phrase=0b01011011, root=62, start=0, count=7),
    "dens-100": P.Page(density=1.0, phrase=0xFF, root=62, start=0, count=8),
    "crpt-before": P.Page(corrupt=0.8, phrase=0b11011011, root=60, start=0, count=9, seed=7),
    "crpt-after": P.Page(corrupt=0.8, phrase=0b10011110, root=60, start=8, count=10),
    "drum": P.Page(drum=True, phrase=0b11011011, root=60, start=0, count=9),
}


# Corrupt rewrites steps after they play: the same register as crpt-before with three steps' weights rewritten
for _i, _w in ((1, 92), (4, 12), (10, 85)):
    POSES["crpt-after"].weights[_i] = _w


def main():
    (HERE / "frames").mkdir(exist_ok=True)
    frag = fragment()
    (HERE / "panel.svg.fragment").write_text(frag + "\n", encoding="utf-8")
    (HERE / "panel-lint.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">\n' + frag + "\n</svg>\n", encoding="utf-8")
    for name, p in POSES.items():
        (HERE / "frames" / f"{name}.svg").write_text(frame(p), encoding="utf-8")
    cols, pad = 3, 8
    rows = math.ceil(len(POSES) / cols)
    sheet = Image.new("RGB", (pad + cols * (480 + pad), pad + rows * (220 + 18 + pad)), (40, 40, 40))
    dr = ImageDraw.Draw(sheet)
    with tempfile.TemporaryDirectory() as tmp:
        for n, name in enumerate(POSES):
            x, y = pad + (n % cols) * (480 + pad), pad + (n // cols) * (220 + 18 + pad)
            png = Path(tmp) / f"{name}.png"
            subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(HERE / "frames" / f"{name}.svg"), "-o", str(png)], check=True)
            dr.text((x, y), name, fill=(200, 200, 200))
            sheet.paste(Image.open(png).convert("RGB"), (x, y + 18))
    sheet.save(HERE / "board.png")
    print(f"wrote {len(POSES)} frames, fragment with {frag.count(PREFIX + '_dot_')} dots")


if __name__ == "__main__":
    main()
