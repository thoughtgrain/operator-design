#!/usr/bin/env python3
"""Check that every control visibly changes the screen, by enough for how much it changes the sound.

Renders each control's c<N>-000 / -050 / -100 frames at 1:1 and measures how much of the screen body
changes between them, plus the rest → playing pair for the note response. A pixel counts as changed
when its brightness moves by at least one stock grey step (~25/255), so a faint dimming doesn't count.
Thresholds come from tokens.json `perceptibility` and scale with each control's audible score (1–5).

Frames are SVG (rendered with rsvg-convert) or PNG captures of the screen at 480×220 or 960×440,
named c<N>-000 / -050 / -100 and optionally rest / playing.

Usage:
    python3 opxy/tools/perceptibility.py FRAMES_DIR --scores 4,5,5,3,3,2,3,2
        [--names spread,fold,...] [--header-bottom 38] [--tokens PATH] [--json]

SVG frames need rsvg-convert. Exit codes: 0 all pass, 1 a control or the note response is under its floor,
2 usage, missing tool or unreadable frame.
"""
from __future__ import annotations

import argparse
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

DEFAULT_TOKENS = Path(__file__).resolve().parent.parent / "tokens.json"
W, H = 480, 220


class PerceptError(Exception):
    pass


def decode_png(data: bytes) -> list[list[int]]:
    """8-bit RGB/RGBA/grey PNG → rows of luminance 0..255 (alpha composited on black)."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise PerceptError("not a PNG")
    pos, idat, width = 8, b"", 0
    height = depth = ctype = 0
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            width, height, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", body)
            if depth != 8 or interlace != 0 or ctype not in (0, 2, 4, 6):
                raise PerceptError(f"unsupported PNG (depth {depth}, type {ctype}, interlace {interlace})")
        elif kind == b"IDAT":
            idat += body
        elif kind == b"IEND":
            break
        pos += 12 + length
    channels = {0: 1, 2: 3, 4: 2, 6: 4}[ctype]
    raw = zlib.decompress(idat)
    stride = width * channels
    rows, prev = [], bytearray(stride)
    for y in range(height):
        start = y * (stride + 1)
        ftype, line = raw[start], bytearray(raw[start + 1:start + 1 + stride])
        for i in range(stride):
            a = line[i - channels] if i >= channels else 0
            b, c = prev[i], (prev[i - channels] if i >= channels else 0)
            if ftype == 1:
                line[i] = (line[i] + a) & 255
            elif ftype == 2:
                line[i] = (line[i] + b) & 255
            elif ftype == 3:
                line[i] = (line[i] + ((a + b) >> 1)) & 255
            elif ftype == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        prev = line
        lum = []
        for x in range(width):
            px = line[x * channels:(x + 1) * channels]
            if channels in (1, 2):
                v, alpha = px[0], (px[1] if channels == 2 else 255)
            else:
                v = (2126 * px[0] + 7152 * px[1] + 722 * px[2]) // 10000
                alpha = px[3] if channels == 4 else 255
            lum.append(v * alpha // 255)
        rows.append(lum)
    return rows


def png_size(data: bytes) -> tuple[int, int]:
    return struct.unpack(">II", data[16:24])


def downsample2(rows: list[list[int]]) -> list[list[int]]:
    """2× capture → 1:1 by averaging each 2×2 block"""
    return [[(rows[2 * y][2 * x] + rows[2 * y][2 * x + 1] + rows[2 * y + 1][2 * x] + rows[2 * y + 1][2 * x + 1]) // 4
             for x in range(W)] for y in range(H)]


def render(frame: Path, out_dir: Path, tool: str | None) -> list[list[int]]:
    """An SVG frame rendered at 1:1, or a PNG capture at 1:1 or exactly 2×."""
    if frame.suffix.lower() == ".png":
        data = frame.read_bytes()
        size = png_size(data)
        if size == (W, H):
            return decode_png(data)
        if size == (2 * W, 2 * H):
            return downsample2(decode_png(data))
        raise PerceptError(f"{frame} is {size[0]}×{size[1]}; captures must be 480×220 or 960×440 (crop to the screen)")
    if not tool:
        raise PerceptError("rsvg-convert not found (librsvg); install it to render SVG frames, or pass PNG captures")
    png = out_dir / (frame.stem + ".png")
    res = subprocess.run([tool, "-w", str(W), "-h", str(H), "-b", "black", "-o", str(png), str(frame)],
                         capture_output=True, text=True)
    if res.returncode != 0:
        raise PerceptError(f"rsvg-convert failed on {frame}: {res.stderr.strip()}")
    return decode_png(png.read_bytes())


def find(frames: Path, stem: str) -> Path | None:
    for ext in (".svg", ".png"):
        if (frames / (stem + ext)).exists():
            return frames / (stem + ext)
    return None


def diff(a, b, top: int, step: int) -> tuple[float, int]:
    """(% of body pixels changed by ≥ step, span of the change's bounding box in px)"""
    changed, x0, y0, x1, y1 = 0, W, H, -1, -1
    for y in range(top, H):
        ra, rb = a[y], b[y]
        for x in range(W):
            if abs(ra[x] - rb[x]) >= step:
                changed += 1
                x0, x1, y0, y1 = min(x0, x), max(x1, x), min(y0, y), max(y1, y)
    area = 100.0 * changed / (W * (H - top))
    span = 0 if x1 < 0 else max(x1 - x0 + 1, y1 - y0 + 1)
    return area, span


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Check each control changes enough of the screen for its audible score.")
    ap.add_argument("frames", type=Path)
    ap.add_argument("--scores", required=True, help="audible scores 1–5 in control order, e.g. 4,5,5,3")
    ap.add_argument("--names", help="control names in order (labels the report)")
    ap.add_argument("--header-bottom", type=int, default=38, help="ignore the header above this y (38 two-page, 20 stock)")
    ap.add_argument("--tokens", type=Path, default=DEFAULT_TOKENS)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    try:
        tokens = json.loads(args.tokens.read_text(encoding="utf-8"))["perceptibility"]
        scores = [int(s) for s in args.scores.split(",")]
        if not all(1 <= s <= 5 for s in scores):
            raise ValueError("scores must be 1..5")
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"perceptibility: {exc}", file=sys.stderr)
        return 2
    names = args.names.split(",") if args.names else [f"c{i + 1}" for i in range(len(scores))]
    tool = shutil.which("rsvg-convert")

    step, span_min, half = tokens["pixelStep"], tokens["minSpanPx"], tokens["halfStepShare"]
    results, failed = [], False
    try:
        with tempfile.TemporaryDirectory() as tmp:
            tmpd = Path(tmp)
            for i, score in enumerate(scores):
                paths = [find(args.frames, f"c{i + 1}-{v:03d}") for v in (0, 50, 100)]
                if None in paths:
                    raise PerceptError(f"missing c{i + 1}-000/050/100 (.svg or .png) in {args.frames}")
                f0, f50, f100 = (render(p, tmpd, tool) for p in paths)
                need = tokens["areaByScore"][str(score)]
                full, span = diff(f0, f100, args.header_bottom, step)
                lo, _ = diff(f0, f50, args.header_bottom, step)
                hi, _ = diff(f50, f100, args.header_bottom, step)
                ok = full >= need and span >= span_min and lo >= need * half and hi >= need * half
                failed |= not ok
                results.append({"control": names[i] if i < len(names) else f"c{i + 1}", "score": score, "need": need,
                                "full": round(full, 2), "lowHalf": round(lo, 2), "highHalf": round(hi, 2), "span": span, "ok": ok})
            rest, playing = find(args.frames, "rest"), find(args.frames, "playing")
            if rest and playing:
                area, span = diff(render(rest, tmpd, tool), render(playing, tmpd, tool), args.header_bottom, step)
                need = tokens["noteArea"]
                ok = area >= need and span >= span_min
                failed |= not ok
                results.append({"control": "note response", "score": None, "need": need, "full": round(area, 2),
                                "lowHalf": None, "highHalf": None, "span": span, "ok": ok})
    except PerceptError as exc:
        print(f"perceptibility: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"pass": not failed, "results": results}, indent=2))
    else:
        print(f"{'control':<14} {'score':>5} {'need %':>7} {'0→100 %':>8} {'0→50 %':>7} {'50→100 %':>9} {'span':>5}")
        for r in results:
            fmt = lambda v: "—" if v is None else f"{v:.2f}"
            mark = "ok" if r["ok"] else "UNDER"
            print(f"{r['control']:<14} {('—' if r['score'] is None else r['score']):>5} {r['need']:>7.2f} {r['full']:>8.2f} "
                  f"{fmt(r['lowHalf']):>7} {fmt(r['highHalf']):>9} {r['span']:>5}  {mark}")
        print("pass" if not failed else "some changes are under the floor: give those controls more travel or a stronger channel")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
