"""Knob sweep for gears frames pass 03, v1: the same drawing as rest.svg (gen.build),
driven by the four controls at 0..1 and a held note."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("gears_v1_gen", Path(__file__).resolve().parent / "gen.py")
_gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_gen)


def frame(values: dict[str, float], notes: float) -> str:
    return _gen.build(values, notes)
