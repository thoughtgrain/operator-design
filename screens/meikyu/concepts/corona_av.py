#!/usr/bin/env python3
"""meikyu o2 corona, in motion with sound: the same 32 s score and player port as planets_av.py, on the picked
page alone: the corona sun, orbit trails, no keyboard, the text line along the bottom.

    python3 corona_av.py <tmpdir>      → corona.mp4
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import planets_av as A
import suns as S

HERE = Path(__file__).resolve().parent


def picture(out: Path, events):
    cache = {}
    for i in range(int(A.LENGTH * A.FPS)):
        p = A.page_at(i / A.FPS, events)
        key = (tuple(p.weights), p.phrase, p.root, p.count, round(p.density * 100), p.scale, round(p.corrupt * 100), p.drum)
        png = out / f"f{i:04d}.png"
        if key in cache:
            png.write_bytes(cache[key].read_bytes())
            continue
        svg = out / "t.svg"
        svg.write_text(S.frame(p, S.art(S.sun_corona, p)))
        subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(svg), "-o", str(png)], check=True)
        cache[key] = png


def main():
    tmp = Path(sys.argv[1])
    tmp.mkdir(parents=True, exist_ok=True)
    events, tones = A.run()
    wav = HERE / "planets.wav"
    if not wav.exists():
        A.sound(wav, tones)
    picture(tmp, events)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(A.FPS), "-i", str(tmp / "f%04d.png"), "-i", str(wav),
                    "-vf", "scale=960:440:flags=neighbor", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", str(HERE / "corona.mp4")], check=True)
    print("wrote corona.mp4")


if __name__ == "__main__":
    main()
