"""Run the existing opxy/tools scripts in-process, exactly as the CLI does, and hand back their JSON.

I call each tool's own main() with --json instead of reimplementing it, so the CLI stays the single source of
truth: a rule fixed in lint_frame.py is fixed for the MCP server too.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .paths import TOOLS, ToolError

_modules: dict[str, object] = {}


def tool_module(name: str):
    """Import opxy/tools/<name>.py once."""
    if name not in _modules:
        path = TOOLS / f"{name}.py"
        spec = importlib.util.spec_from_file_location(f"opxy_tools_{name}", path)
        if spec is None or spec.loader is None:
            raise ToolError(f"can't load {path}")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod  # dataclasses with `from __future__ import annotations` look themselves up here
        try:
            spec.loader.exec_module(mod)
        except Exception:
            sys.modules.pop(spec.name, None)
            raise
        _modules[name] = mod
    return _modules[name]


def run_cli(name: str, argv: list[str]) -> tuple[int, str, str]:
    """main(argv) with stdout/stderr captured. argparse errors become exit code 2 with their message."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = tool_module(name).main([str(a) for a in argv])
        except SystemExit as exc:  # argparse
            code = exc.code if isinstance(exc.code, int) else 2
    return int(code or 0), out.getvalue(), err.getvalue().strip()


def run_json(name: str, argv: list[str]) -> tuple[int, dict]:
    """Run a tool with --json. Exit 2 (usage, I/O, missing renderer) raises ToolError with the tool's message."""
    code, out, err = run_cli(name, [*argv, "--json"])
    if code == 2 or not out.strip():
        raise ToolError(err or f"{name} failed (exit {code})")
    try:
        return code, json.loads(out)
    except json.JSONDecodeError as exc:
        raise ToolError(f"{name} printed something that isn't JSON: {exc}") from exc


def rsvg() -> str | None:
    return shutil.which("rsvg-convert")


def render_png(svg: Path, scale: int = 1) -> bytes:
    """An SVG frame at 1:1 (or 2×) on black, as PNG bytes."""
    tool = rsvg()
    if not tool:
        raise ToolError("rsvg-convert isn't installed (librsvg). macOS: brew install librsvg · Debian/Ubuntu: apt install librsvg2-bin")
    with tempfile.TemporaryDirectory() as tmp:
        png = Path(tmp) / "frame.png"
        res = subprocess.run([tool, "-w", str(480 * scale), "-h", str(220 * scale), "-b", "black", "-o", str(png), str(svg)],
                             capture_output=True, text=True, timeout=60)
        if res.returncode != 0:
            raise ToolError(f"rsvg-convert failed on {svg.name}: {res.stderr.strip()}")
        return png.read_bytes()


def luminance(frame: Path) -> list[list[int]]:
    """A frame (SVG or 480×220 / 960×440 PNG) as rows of 0..255, using perceptibility.py's own decoder."""
    mod = tool_module("perceptibility")
    with tempfile.TemporaryDirectory() as tmp:
        try:
            return mod.render(frame, Path(tmp), rsvg())
        except mod.PerceptError as exc:
            raise ToolError(str(exc)) from exc


def body_diff_pct(a: list[list[int]], b: list[list[int]], top: int) -> float:
    """% of body pixels whose brightness moves by ≥ one stock grey step, the same measure perceptibility uses."""
    mod = tool_module("perceptibility")
    from .paths import tokens
    step = tokens()["perceptibility"]["pixelStep"]
    area, _ = mod.diff(a, b, top, step)
    return area
