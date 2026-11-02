"""Where things live, and keeping every path the server touches inside the repo (or the configured workspace)."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OPXY = ROOT / "opxy"
TOOLS = OPXY / "tools"
LIBRARY = ROOT / "library"
TRAINING = ROOT / "training"
PROPOSALS = TRAINING / "proposals"
AGENT_ROLES = TRAINING / "agents"

MACHINE_ID = re.compile(r"^[a-z][a-z0-9_]{0,14}$")


class ToolError(Exception):
    """A problem the caller can fix (bad argument, missing file). Reported as a tool error, not a crash."""


def workspace() -> Path:
    """Where screens/ lives. Defaults to the repo; OPXY_WORKSPACE points it at another checkout."""
    env = os.environ.get("OPXY_WORKSPACE")
    return Path(env).expanduser().resolve() if env else ROOT


def screens_dir() -> Path:
    return workspace() / "screens"


def allowed_roots() -> list[Path]:
    roots = [ROOT, workspace()]
    return list(dict.fromkeys(roots))


def resolve(path: str | os.PathLike, *, must_exist: bool = True, base: Path | None = None) -> Path:
    """Resolve a user-supplied path relative to the workspace and refuse anything outside the allowed roots."""
    if path is None or str(path).strip() == "":
        raise ToolError("path is empty")
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = (base or workspace()) / p
    p = p.resolve()
    if not any(p == r or r in p.parents for r in allowed_roots()):
        raise ToolError(f"{path} is outside the repo and workspace; set OPXY_WORKSPACE to work elsewhere")
    if must_exist and not p.exists():
        raise ToolError(f"not found: {rel(p)}")
    return p


def rel(p: Path) -> str:
    """A path as the person would write it: relative to the repo or workspace when it's inside one."""
    for r in allowed_roots():
        try:
            return str(p.resolve().relative_to(r))
        except ValueError:
            continue
    return str(p)


def machine_dir(machine_id: str, *, must_exist: bool = True) -> Path:
    if not isinstance(machine_id, str) or not MACHINE_ID.match(machine_id):
        raise ToolError("machine_id must be lower case, start with a letter, ≤ 15 chars of a-z, 0-9, _ (the SDK id rule)")
    d = screens_dir() / machine_id
    if must_exist and not d.is_dir():
        raise ToolError(f"no screen folder for {machine_id}; run screen_init first")
    return d


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ToolError(f"not found: {rel(path)}") from exc
    except json.JSONDecodeError as exc:
        raise ToolError(f"{rel(path)} is not valid JSON: {exc}") from exc


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def colour_allowed() -> bool:
    """Colour is an override set in the harness's MCP config (OPXY_COLOUR=allow), never from a tool call."""
    return os.environ.get("OPXY_COLOUR", "").strip().lower() in ("allow", "allowed", "on", "1", "true")


def colour_policy() -> dict:
    if colour_allowed():
        return {"mode": "colour allowed", "set": "OPXY_COLOUR=allow in this harness's MCP config",
                "rules": ["grey is still the default; use colour only where the brief says why",
                          "red stays reserved for stock recording and parameter locks",
                          "two to four accent hues, each with a role, kept the same across pages and animation",
                          "ship a designed panel.grayscale.svg.fragment (sdk 1.5) and lint it with grayscale_of",
                          "every hue difference also has a shape, label, position or outline difference"]}
    return {"mode": "grey only", "set": "default; colour needs OPXY_COLOUR=allow in the harness's MCP config "
                                       "(python3 mcp/setup.py <client> --colour). An agent can't turn it on."}


def catalog() -> dict:
    return load_json(OPXY / "catalog.json")


def tokens() -> dict:
    return load_json(OPXY / "tokens.json")
