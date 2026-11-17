"""Bench for 03-frames v3: frame(values, notes) -> the whole 480 x 220 SVG.

The drawing lives in frame.py (draw); rest.svg is draw(defaults, 0), so the
board and the knobs come from one function.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "gears_03_v3_frame", Path(__file__).resolve().parent / "frame.py")
_gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_gen)


def frame(values: dict[str, float], notes: float) -> str:
    return _gen.draw(values, notes)
