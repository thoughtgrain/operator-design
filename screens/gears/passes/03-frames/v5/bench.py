"""Knob sweep for gears 03-frames v5: the same drawing as frame.py, with the controls as inputs."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("gears_v5_frame", Path(__file__).resolve().parent / "frame.py")
_gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_gen)


def frame(values: dict[str, float], notes: float) -> str:
    return _gen.render(dict(values), notes)
