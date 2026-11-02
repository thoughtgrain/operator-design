"""open-xy's own checker, `sdk.py test --machine`, run against a local open-xy checkout.

The opxy tools mirror open-xy's rules so a design can be checked before there's a machine; this is the real
validator once there is one (records, sources, both SVGs, the browser preview build, host tests). It needs a
checkout of open-xy (OPXY_SDK) and whatever compilers sdk.py itself asks for; a host pass is still not device
acceptance.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from .paths import ToolError, rel, resolve

TAIL = 6000


def sdk_root() -> Path:
    env = os.environ.get("OPXY_SDK")
    if not env:
        raise ToolError("sdk_test needs a local open-xy checkout: set OPXY_SDK in this server's config "
                        "(python3 mcp/setup.py <client> --sdk ../open-xy). Clone https://github.com/etcetc000/open-xy "
                        "and use its staging branch.")
    root = Path(env).expanduser().resolve()
    if not (root / "sdk.py").is_file():
        raise ToolError(f"OPXY_SDK={root} has no sdk.py; point it at the root of an open-xy checkout")
    return root


def sdk_test(machine: str, no_cpu: bool = True, cxx: str | None = None, host_cxx: str | None = None,
             timeout: int = 170) -> dict:
    root = sdk_root()
    folder = resolve(machine)
    if not (folder / "machine.json").exists() and not (folder / "definition.json").exists():
        raise ToolError(f"{rel(folder)} doesn't look like a machine folder (no machine.json or definition.json)")
    cmd = [sys.executable, str(root / "sdk.py"), "test", "--machine", str(folder)]
    if no_cpu:
        cmd.append("--no-cpu")
    if cxx:
        cmd += ["--cxx", cxx]
    if host_cxx:
        cmd += ["--host-cxx", host_cxx]
    try:
        res = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=max(10, min(timeout, 590)))
    except subprocess.TimeoutExpired:
        raise ToolError(f"sdk.py test ran past {timeout} s; run it in a terminal: {' '.join(cmd)}")
    out = (res.stdout + ("\n" + res.stderr if res.stderr.strip() else "")).strip()
    return {"machine": rel(folder), "sdk": str(root), "pass": res.returncode == 0, "exitCode": res.returncode,
            "command": " ".join(cmd), "output": out[-TAIL:], "truncated": len(out) > TAIL,
            "note": "A host pass is not device acceptance: CPU on hardware, rasterization and the real screen stay pending."
                    + (" CPU estimate skipped (no_cpu); open-xy's catalog needs the hardware readout anyway." if no_cpu else "")}
