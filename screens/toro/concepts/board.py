#!/usr/bin/env python3
"""Concept board at 1:1: python3 board.py <out.png> <style-dir>... (columns are the poses found in the first dir)"""
import subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw

out, dirs = sys.argv[1], [Path(d) for d in sys.argv[2:]]
order = ["rest", "spread-100", "cutoff-000", "cutoff-100", "fold-100", "aphx-100", "playing"]
poses = [p for p in order if (dirs[0] / f"{p}.svg").exists()]
W, H, P = 480, 220, 8
B = Image.new("RGB", (P + len(poses) * (W + P), P + 18 + len(dirs) * (H + P)), (40, 40, 40))
d = ImageDraw.Draw(B)
with tempfile.TemporaryDirectory() as tmp:
    for j, p in enumerate(poses):
        d.text((P + j * (W + P), P), p, fill=(200, 200, 200))
    for i, s in enumerate(dirs):
        for j, p in enumerate(poses):
            png = Path(tmp) / f"{s.name}_{p}.png"
            subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(s / f"{p}.svg"), "-o", str(png)], check=True)
            B.paste(Image.open(png).convert("RGB"), (P + j * (W + P), P + 18 + i * (H + P)))
B.save(out)
