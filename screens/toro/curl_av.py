#!/usr/bin/env python3
"""toro fold curl, in motion with sound: the riff plays while fold sweeps 0 → 1, holds, and comes back.

    python3 curl_av.py <tmpdir>      → blocks/toro-curl.mp4
"""
from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import blocks_av as A  # noqa: E402
import gen_frames as g  # noqa: E402


def score():
    D = dict(g.DEFAULTS)
    length = 14.0
    notes, t, k = [], 0.6, 0
    while t < length - 0.6:
        notes.append((t, t + A.HOLD, A.RIFF[k % len(A.RIFF)]))
        t += A.STEP
        k += 1

    def values(t):
        v = dict(D)
        if 2.0 <= t < 6.0:                                    # rise
            u = (t - 2.0) / 4.0
        elif 6.0 <= t < 9.0:                                  # hold the crest
            u = 1.0
        elif 9.0 <= t < 12.5:                                 # fall back
            u = 1 - (t - 9.0) / 3.5
        else:
            u = 0.0
        v["fold"] = D["fold"] + (1.0 - D["fold"]) * (0.5 - 0.5 * math.cos(math.pi * u))
        return v

    return notes, values, length


def main():
    tmp = Path(sys.argv[1])
    tmp.mkdir(parents=True, exist_ok=True)
    notes, values, length = score()
    wav = HERE / "audio" / "toro-curl.wav"
    A.sound(wav, notes, values, length)
    A.picture(tmp, notes, values, length)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(A.FPS), "-i", str(tmp / "f%04d.png"), "-i", str(wav),
                    "-vf", "scale=960:440:flags=neighbor", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", str(HERE / "blocks" / "toro-curl.mp4")], check=True)
    print("wrote blocks/toro-curl.mp4")


if __name__ == "__main__":
    main()
