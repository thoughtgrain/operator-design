#!/usr/bin/env python3
"""Tile a machine's frames into one contact sheet at 1:1.

PR #260's ux.md (open, kept here as a house rule) asks for a contact sheet of every control at 0, 50 and 100, judged at
1:1. This lays frames out as one row per control (c<N>-000/050/100), with
rest and playing frames on the first row, each at exactly 480 x 220, labelled
underneath. Output is SVG; if rsvg-convert is installed, a PNG at 1:1 too.

Usage:
    python3 opxy/tools/contact_sheet.py FRAMES_DIR --out contact.svg [--png]

Exit codes: 0 ok, 2 usage or I/O failure.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

W, H = 480, 220
GAP, LABEL = 16, 18
CONTROL_FRAME = re.compile(r"^c(?P<n>\d+)-(?P<v>\d{3})$")
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


def collect(frames_dir: Path) -> list[list[Path]]:
    """Rows of frames: [rest, playing], then one row per control sorted by value."""
    if not frames_dir.is_dir():
        raise FileNotFoundError(f"frames directory not found: {frames_dir}")
    files = {p.stem: p for p in sorted(frames_dir.glob("*.svg"))}
    if not files:
        raise FileNotFoundError(f"no .svg frames in {frames_dir}")
    rows: list[list[Path]] = []
    lead = [files.pop(name) for name in ("rest", "playing") if name in files]
    if lead:
        rows.append(lead)
    controls: dict[int, list[tuple[int, Path]]] = {}
    others: list[Path] = []
    for stem, path in files.items():
        m = CONTROL_FRAME.match(stem)
        if m:
            controls.setdefault(int(m["n"]), []).append((int(m["v"]), path))
        else:
            others.append(path)
    for n in sorted(controls):
        rows.append([p for _, p in sorted(controls[n])])
    if others:
        rows.append(others)
    return rows


def inner(path: Path) -> ET.Element:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise ValueError(f"not well-formed XML ({path}): {exc}") from exc
    if root.tag.rsplit("}", 1)[-1] != "svg":
        raise ValueError(f"{path} isn't an <svg> document")
    return root


def build(rows: list[list[Path]]) -> ET.ElementTree:
    cols = max(len(r) for r in rows)
    sheet_w = GAP + cols * (W + GAP)
    sheet_h = GAP + len(rows) * (H + LABEL + GAP)
    sheet = ET.Element(f"{{{SVG_NS}}}svg", {
        "width": str(sheet_w), "height": str(sheet_h),
        "viewBox": f"0 0 {sheet_w} {sheet_h}",
    })
    ET.SubElement(sheet, f"{{{SVG_NS}}}rect", {
        "width": str(sheet_w), "height": str(sheet_h), "fill": "#161616"})
    for r, row in enumerate(rows):
        for c, path in enumerate(row):
            x = GAP + c * (W + GAP)
            y = GAP + r * (H + LABEL + GAP)
            frame = inner(path)
            nested = ET.SubElement(sheet, f"{{{SVG_NS}}}svg", {
                "x": str(x), "y": str(y), "width": str(W), "height": str(H),
                "viewBox": f"0 0 {W} {H}", "overflow": "hidden"})
            ET.SubElement(nested, f"{{{SVG_NS}}}rect", {"width": str(W), "height": str(H), "fill": "#000000"})
            for child in list(frame):
                nested.append(child)
            label = ET.SubElement(sheet, f"{{{SVG_NS}}}text", {
                "x": str(x), "y": str(y + H + 13), "fill": "#969696",
                "font-family": "UniversNextPro-Light, Helvetica Neue, sans-serif", "font-size": "11"})
            label.text = path.stem
    return ET.ElementTree(sheet)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Tile 480 × 220 frames into a 1:1 contact sheet.")
    ap.add_argument("frames", type=Path, help="directory of frame SVGs")
    ap.add_argument("--out", type=Path, required=True, help="output SVG path")
    ap.add_argument("--png", action="store_true", help="also render a 1:1 PNG (needs rsvg-convert)")
    args = ap.parse_args(argv)
    try:
        rows = collect(args.frames)
        tree = build(rows)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        tree.write(args.out, encoding="utf-8", xml_declaration=True)
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"contact_sheet: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {args.out} ({sum(len(r) for r in rows)} frames, {len(rows)} rows)")
    if args.png:
        tool = shutil.which("rsvg-convert")
        if not tool:
            print("contact_sheet: rsvg-convert not found; skipped PNG", file=sys.stderr)
            return 0
        png = args.out.with_suffix(".png")
        result = subprocess.run([tool, "-o", str(png), str(args.out)], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"contact_sheet: PNG render failed: {result.stderr.strip()}", file=sys.stderr)
            return 2
        print(f"wrote {png}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
