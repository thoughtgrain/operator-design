#!/usr/bin/env python3
"""Find the program that turns an SVG frame into a PNG.

Order: $OPXY_RASTER, then opxy-raster (the Rust renderer in crates/opxy-raster: no system libraries, the same
pixels on every platform) on PATH or in this repo's target/release, then rsvg-convert (librsvg). Both take the
same flags (-w -h -b -o), so callers don't care which one they got.

    python3 opxy/tools/raster.py        prints the renderer in use, or exits 1 if there isn't one
"""
from __future__ import annotations

import functools
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EXE = ".exe" if os.name == "nt" else ""
HINT = ("no SVG renderer: build the Rust one (cargo build --release, from the repo root) or install librsvg "
        "(macOS: brew install librsvg · Debian/Ubuntu: apt install librsvg2-bin)")


def find() -> str | None:
    env = os.environ.get("OPXY_RASTER")
    if env:
        return env if Path(env).is_file() else shutil.which(env)
    for candidate in (shutil.which("opxy-raster"), REPO / "target" / "release" / f"opxy-raster{EXE}"):
        if candidate and Path(candidate).is_file():
            return str(candidate)
    return shutil.which("rsvg-convert")


def name(tool: str | None) -> str:
    return Path(tool).stem if tool else "none"


@functools.lru_cache(maxsize=8)
def speaks_luma(tool: str | None) -> bool:
    """True when the renderer is opxy-raster, which can write brightness (--luma) instead of a PNG to decode."""
    if not tool:
        return False
    try:
        out = subprocess.run([tool, "--version"], capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return False
    return out.startswith("opxy-raster")


if __name__ == "__main__":
    tool = find()
    print(tool or HINT)
    sys.exit(0 if tool else 1)
