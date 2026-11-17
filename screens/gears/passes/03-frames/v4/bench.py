#!/usr/bin/env python3
"""Knob bench for frames pass 03, v4: the same drawing as sketch.py, driven by the controls.

frame(values, notes): values by definition id at 0..1 (enum index = round(v * (count - 1))), notes 0 rest, 1 held.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("gears_03_v4_sketch", HERE / "sketch.py")
sk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sk)


def _idx(v, n):
    return max(0, min(n - 1, round(min(1.0, max(0.0, float(v))) * (n - 1))))


def frame(values: dict[str, float], notes: float) -> str:
    return sk.draw(
        ratio_i=_idx(values.get("ratio", 0.5), len(sk.RATIOS)),
        teeth_i=_idx(values.get("teeth", 0.3846), len(sk.TEETH)),
        mesh=min(1.0, max(0.0, float(values.get("mesh", 1.0)))),
        scale_i=_idx(values.get("scale", 0.0), len(sk.SCALES)),
        notes=1.0 if notes >= 0.5 else 0.0,
    )
