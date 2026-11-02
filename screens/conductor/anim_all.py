#!/usr/bin/env python3
"""All four revision-2 pages in one film, with the sequencer running at 120 BPM (a 16th is 0.125 s, a bar 2 s).

   0 –  8 s   M1 song: four bars of C major pop. The bright arch is the link sounding now (this chord to the next);
              the playhead runs the phrase line and the bar's groove.
   8 – 14 s   M2 lanes: lane 5 (arp) plays, then the lane encoder turns through 1 drum, 2 bass and 3 chord.
  14 – 22 s   M3 lane: the arp plays four bars; the chord-tone lines follow each chord as it changes.
  22 – 28 s   M4 route: lane 3 is re-routed from t3 to t6 (its trace slides along the buses, hopping each one it
              passes), then muted (it slides back behind the lane names), then unmuted.

    python3 anim_all.py <out.mp4> [--scale 2]
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import gen_frames as G
import gen_frames2 as R

FPS, STEP, EASE = 30, 0.125, 0.2


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return 1 - (1 - u) ** 3


def m1(t):
    step_abs = int(t / STEP)
    return R.draw_m1(G.Song(), position=(step_abs // 16) % 4, playing=True, step=step_abs % 16).svg(0)


def m2(t):
    el = t - 8
    sel = 4 if el < 3 else (0 if el < 4 else (1 if el < 5 else 2))
    step_abs = int(el / STEP)
    return R.draw_m2(G.default_lanes(), sel=sel, playing=True, step=step_abs % 16).svg(1)


def m3(t):
    el = t - 14
    step_abs = int(el / STEP)
    bar = (step_abs // 16) % 4
    return R.draw_m3(G.Arp(), playing=True, step=step_abs % 16, degree=G.Song().loop[bar]).svg(2)


def m4(t):
    el = t - 22
    lanes = G.default_lanes()
    over = None
    if el < 1.0:
        pass
    elif el < 1.6:                                   # turn "to" t3 -> t6, three clicks 0.2 s apart, each eased
        clicks = [1.0 + 0.2 * i for i in range(3)]
        done = sum(1 for c in clicks if el >= c)
        frac = ease((el - clicks[done - 1]) / EASE)
        lanes[2].target = 2 + done
        over = {2: R.bus_x(2 + done - 1) + (R.bus_x(2 + done) - R.bus_x(2 + done - 1)) * frac}
    elif el < 3.2:
        lanes[2].target = 5
    elif el < 4.6:                                   # mute: the trace slides back behind the names
        lanes[2].target = 5
        u = ease((el - 3.2) / 0.3)
        lanes[2].mute = True
        if u < 1:
            over = {2: R.bus_x(5) + (70 - R.bus_x(5)) * u}
    else:                                            # unmute: out again
        lanes[2].target = 5
        u = ease((el - 4.6) / 0.3)
        over = {2: 70 + (R.bus_x(5) - 70) * u}
    return R.draw_m4(lanes, sel=2, end_override=over).svg(3)


def frame_at(t):
    if t < 8:
        return m1(t)
    if t < 14:
        return m2(t)
    if t < 22:
        return m3(t)
    return m4(t)


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "conductor-pages.mp4").resolve()
    scale = int(sys.argv[sys.argv.index("--scale") + 1]) if "--scale" in sys.argv else 2
    n = int(28 * FPS)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        def render(i):
            svg = tmp / f"f{i:04d}.svg"
            svg.write_text(frame_at(i / FPS))
            subprocess.run(["rsvg-convert", "-z", str(scale), str(svg), "-o", str(tmp / f"f{i:04d}.png")], check=True)
            svg.unlink()

        with ThreadPoolExecutor(4) as ex:
            list(ex.map(render, range(n)))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(tmp / "f%04d.png"),
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", str(out)],
                       check=True)
    print(f"wrote {out} ({n} frames)")


if __name__ == "__main__":
    main()
