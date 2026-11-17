"""Bench adapter for beacon: any knob position, drawn by frames/build.py, the same code as the stills.

The bench calls frame(values, notes) for every position the person turns to (opxy_mcp/bench/worker.py).
notes 0..1 is the note envelope: build.draw's note and cascade, so the beam lights outward as a note comes in.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "frames"))
import build  # noqa: E402


def frame(values: dict[str, float], notes: float) -> str:
    c = {k: values.get(k, build.DEFAULTS[k]) for k in build.CONTROLS}
    return build.draw(c, note=notes, cascade=notes).svg()
