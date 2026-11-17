"""Knob bench for frames pass 03, v2: frame(values, notes) -> the 480 x 220 SVG.

The drawing lives in gen.py's build(); rest.svg is build(defaults, 0).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "gears_v2_gen", Path(__file__).resolve().parent / "gen.py")
_gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_gen)


def frame(values: dict[str, float], notes: float) -> str:
    return _gen.build(values, notes)
