"""Video previews: the server asks and specifies; the agent renders.

The MCP server never makes a video. preview_brief tells whichever agent is driving (Claude, Codex, a local model)
what the preview has to show, how it's timed, where it goes and how it must be labelled, and the agent builds it
with its own tools (ffmpeg, a generator script like screens/toro/blocks_av.py).

Audio is always labelled a simulation. A preview's sound comes from the machine's engine code compiled and run on
a computer (screens/<id>/audio/render.cpp), with a stand-in envelope where the OP-XY would apply its own. It is
not a recording of the device: the real instrument's envelope, effects, mixer, output stage and DAC aren't in it.
"""
from __future__ import annotations

import re

from .paths import ToolError, colour_allowed, machine_dir, rel, tokens

AUDIO_NOTE = ("Simulated audio: the engine's own code run on a computer with a stand-in envelope, not recorded from an "
              "OP-XY. The device's envelope, effects, mixer and output stage aren't in it, so it can differ from what "
              "the instrument plays.")
AUDIO_LABEL = "Audio: simulated (engine code run on a computer, not a device recording)"
SHOWS = ("rest", "controls", "notes", "page")
QUESTIONS = [
    "Do you want a video preview of this screen?",
    "Silent, or with simulated engine audio? (It's the engine's code run on a computer, not a recording from an OP-XY.)",
    "What should it show: rest, each control turning, notes held, a page press? Any order or score you want?",
]


def preview_brief(machine_id: str, audio: str = "ask", shows: list[str] | None = None, score: str | None = None) -> dict:
    """What the agent needs to render a preview, or the questions to ask the person first."""
    d = machine_dir(machine_id)
    if audio not in ("ask", "none", "simulated"):
        raise ToolError("audio is ask, none or simulated")
    shows = shows or []
    bad = [s for s in shows if s not in SHOWS]
    if bad:
        raise ToolError(f"shows takes {', '.join(SHOWS)}")
    if audio == "ask" or not shows:
        return {"machine": machine_id, "state": "ask_first", "askThePerson": QUESTIONS, "audioNote": AUDIO_NOTE,
                "next": "Ask these, then call preview_brief again with audio (none or simulated) and shows. "
                        "Making the video is optional; a design is finished without one."}

    motion = d / "motion.md"
    frames_dir = d / "frames"
    frames = sorted(p.name for p in frames_dir.glob("*.svg")) if frames_dir.is_dir() else []
    controls = sorted({int(m.group(1)) for f in frames if (m := re.match(r"c(\d+)-", f))})
    missing = []
    if not motion.exists():
        missing.append("motion.md (phase 6): the preview's timing comes from it")
    if "rest.svg" not in frames:
        missing.append("frames/rest.svg")
    if "controls" in shows and not controls:
        missing.append("c<N>-000/050/100 frames for the controls")
    if "notes" in shows and "playing.svg" not in frames:
        missing.append("frames/playing.svg")
    if missing:
        return {"machine": machine_id, "state": "not_ready", "missing": missing,
                "next": "Finish these first; a preview drawn ahead of the motion spec shows motion nobody has designed."}

    renderer = d / "audio" / "render.cpp"
    m = tokens()["motion"]
    out = d / "preview" / f"{machine_id}-preview.mp4"
    audio_steps = []
    if audio == "simulated":
        audio_steps = [
            f"Render the sound from the same score the frames are drawn from, with the engine's own code"
            + (f" ({rel(renderer)} exists: compile it against the machine's engine.cpp and feed it the score)."
               if renderer.exists() else
               f". There's no {rel(renderer)} yet: write one that runs the machine's engine.cpp block by block, the way "
               "screens/toro/audio/render.cpp does, and say in it which envelope stands in for the OP-XY's."),
            "Every change on screen should be a change you hear: drive the frames and the audio from one score.",
            "Mux it as AAC; keep the level conservative (peaks around -3 dBFS) since it isn't the device's output stage.",
        ]
    storyboard = []
    if "rest" in shows:
        storyboard.append("rest: hold frames/rest.svg for 1.5 s; nothing moves (that's the point)")
    if "controls" in shows:
        storyboard.append(f"controls: for each of c{', c'.join(map(str, controls))}, turn 0 → 100 → back to default, "
                          f"each step settling in {m['easeSecondsMin']}–{m['easeSecondsMax']} s as motion.md specifies; "
                          "header value changes with it")
    if "notes" in shows:
        storyboard.append("notes: strike, sustain while held, release (motion.md → Notes); retriggers restart the ease, never toggle")
    if "page" in shows:
        storyboard.append("page: one encoder press, page header grows/shrinks over 0.15 s")
    return {
        "machine": machine_id,
        "state": "ready",
        "whoRenders": "You (the agent) render it with your own tools. The server only writes this brief.",
        "output": rel(out),
        "notes": rel(out.with_name(f"{machine_id}-preview.md")),
        "audio": audio,
        "audioNote": AUDIO_NOTE if audio == "simulated" else None,
        "score": score or "your choice; write it down in the notes file so the video can be rebuilt",
        "storyboard": storyboard,
        "frames": {"dir": rel(frames_dir), "controls": controls,
                   "fromMotion": rel(motion), "rule": "draw in-between frames from the same generator as the stills; never hand-patch"},
        "video": {"size": "480 × 220 (1:1). A 960 × 440 copy is fine for sharing if scaled nearest-neighbour, never smoothed",
                  "fps": 30, "codec": "H.264, yuv420p, -preset veryfast (ffmpeg -crf 18)",
                  "background": "#000000", "header": "the stock header as drawn in the frames' preview_* groups"},
        "audioSteps": audio_steps,
        "rules": [("colour as the screen uses it (this harness allows colour); never red" if colour_allowed()
                   else "grey only, never red"), "nothing moves at rest",
                  f"no element alternates bright/dark more than {m['maxFlashesPerSecond']}× a second",
                  "reduced motion isn't shown unless asked; if it is, it jumps to end states"],
        "labelling": ([f"Write '{AUDIO_LABEL}' into the file metadata (ffmpeg -metadata comment=…).",
                       "Put the same line at the top of the notes file, and in any caption, library card or audit that links the video.",
                       "Never describe it as how the OP-XY sounds; it's how the engine code sounds on a computer."]
                      if audio == "simulated" else
                      ["Silent preview: say 'no audio' in the notes file so nobody wonders if the track is missing."]),
        "afterwards": "Watch it yourself at 1:1 before showing it. Device behaviour stays pending until the real screen is filmed.",
    }
