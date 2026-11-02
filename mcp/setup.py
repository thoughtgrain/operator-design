#!/usr/bin/env python3
"""Hook the operator-design MCP server into a client, and generate the agent roles for Claude Code and Codex.

    python3 mcp/setup.py claude-code [--scope project|user]
    python3 mcp/setup.py claude-desktop
    python3 mcp/setup.py codex [--scope user|project]
    python3 mcp/setup.py lmstudio [--model qwen3-8b]
    python3 mcp/setup.py ollama   [--model qwen3:8b]
    python3 mcp/setup.py print                       the generic stdio entry, for any other client
    python3 mcp/setup.py agents                      regenerate .claude/agents and .codex/agents from training/agents
    python3 mcp/setup.py check                       is everything in place?

Common flags: --dry-run (show, don't write), --python PATH, --profile full|compact, --endpoint URL, --model NAME,
--approver "Name" (lets that person approve training proposals over MCP; off by default), --colour (allow colour in
this harness; grey is the default), --sdk PATH (a local open-xy checkout for sdk_test).

Every config write merges into what's there, keeps other servers, and saves the old file as <name>.bak first.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SERVER = HERE / "server.py"
NAME = "operator-design"
sys.path.insert(0, str(HERE))

from opxy_mcp import agents as roles_mod  # noqa: E402
from opxy_mcp.tools import TOOLS  # noqa: E402

LOCAL_DEFAULTS = {"lmstudio": "http://localhost:1234/v1", "ollama": "http://localhost:11434/v1"}


def env_for(args, local: str | None = None) -> dict:
    env = {}
    profile = args.profile or ("compact" if local else None)
    if profile:
        env["OPXY_PROFILE"] = profile
    endpoint = args.endpoint or (LOCAL_DEFAULTS.get(local) if args.model else None)
    if endpoint:
        env["OPXY_AGENT_ENDPOINT"] = endpoint
    if args.model:
        env["OPXY_AGENT_MODEL"] = args.model
    if args.approver:
        env["OPXY_APPROVERS"] = args.approver
    if getattr(args, "colour", False):
        env["OPXY_COLOUR"] = "allow"
    if getattr(args, "sdk", None):
        env["OPXY_SDK"] = str(Path(args.sdk).expanduser().resolve())
    return env


def stdio_entry(args, local: str | None = None, portable: bool = False) -> dict:
    entry = {"command": args.python if not portable else "python3",
             "args": ["${CLAUDE_PROJECT_DIR:-.}/mcp/server.py"] if portable else [str(SERVER)]}
    env = env_for(args, local)
    if env:
        entry["env"] = env
    return entry


def merge_json(path: Path, entry: dict, dry: bool, key: str = "mcpServers") -> None:
    data = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8") or "{}")
        except json.JSONDecodeError as exc:
            sys.exit(f"{path} isn't valid JSON ({exc}); fix it or move it aside, then run this again")
    data.setdefault(key, {})[NAME] = entry
    text = json.dumps(data, indent=2) + "\n"
    if dry:
        print(f"--- would write {path}\n{text}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.copy2(path, path.with_name(path.name + ".bak"))
    path.write_text(text, encoding="utf-8")
    print(f"wrote {path}" + (" (old version in .bak)" if path.with_name(path.name + ".bak").exists() else ""))


def toml_str(s: str) -> str:
    return json.dumps(s)  # JSON string escaping is valid TOML basic-string escaping


def codex_block(args) -> str:
    lines = [f"[mcp_servers.{NAME.replace('-', '_')}]",
             f"command = {toml_str(args.python)}",
             f"args = [{toml_str(str(SERVER))}]",
             "startup_timeout_sec = 20",
             "tool_timeout_sec = 180"]
    env = env_for(args)
    if env:
        lines.append("")
        lines.append(f"[mcp_servers.{NAME.replace('-', '_')}.env]")
        lines += [f"{k} = {toml_str(v)}" for k, v in env.items()]
    return "\n".join(lines) + "\n"


def write_codex(path: Path, args) -> None:
    block = codex_block(args)
    table = f"[mcp_servers.{NAME.replace('-', '_')}]"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if table in text:
        # replace our own tables only, leave everything else alone
        out, skip = [], False
        for line in text.splitlines():
            if line.strip().startswith("["):
                skip = line.strip().startswith(table[:-1])
            if not skip:
                out.append(line)
        text = "\n".join(out).rstrip() + "\n"
    new = (text.rstrip() + "\n\n" if text.strip() else "") + block
    if args.dry_run:
        print(f"--- would write {path}\n{new}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.copy2(path, path.with_name(path.name + ".bak"))
    path.write_text(new, encoding="utf-8")
    print(f"wrote {path}")


def desktop_config() -> Path:
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
    if system == "Windows":
        return Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming")) / "Claude/claude_desktop_config.json"
    return Path.home() / ".config/Claude/claude_desktop_config.json"


# ── agent roles ──────────────────────────────────────────────────────────────

def gen_agents(dry: bool) -> None:
    known = {t.name for t in TOOLS}
    for stage, r in roles_mod.roles().items():
        mcp = [t for t in r.get("mcp_tools", []) if t in known]
        if "training_approve" in mcp:
            sys.exit(f"{r['file']} lists training_approve; approval stays with a person")
        missing = [t for t in r.get("mcp_tools", []) if t not in known]
        if missing:
            sys.exit(f"{r['file']} names tools the server doesn't have: {', '.join(missing)}")
        header = f"<!-- Generated by `python3 mcp/setup.py agents` from {r['file']}. Edit that file, not this one. -->\n\n"
        tools = r.get("tools", []) + [f"mcp__{NAME}__{t}" for t in mcp]
        claude = (f"---\nname: {r['name']}\ndescription: {r['description']}\ntools: {', '.join(tools)}\n---\n\n"
                  + header + r["instructions"] + "\n")
        mcp_note = ("\n\nTools from the operator-design MCP server you should use: " + ", ".join(mcp) + "."
                    "\nNever call training_approve; approval is the person's.")
        body = r["instructions"] + mcp_note
        if "'''" in body:
            sys.exit(f"{r['file']} contains ''' which can't go in a TOML literal string")
        codex = (f"# Generated by `python3 mcp/setup.py agents` from {r['file']}. Edit that file, not this one.\n"
                 f"name = {toml_str(r['codex_name'])}\ndescription = {toml_str(r['description'])}\n"
                 f"developer_instructions = '''\n{body}\n'''\n")
        if stage in ("review", "draft"):
            codex += "\n[features]\nshell_tool = false\n"
        for path, text in ((ROOT / ".claude/agents" / f"{r['name']}.md", claude),
                           (ROOT / ".codex/agents" / f"{r['codex_name']}.toml", codex)):
            if dry:
                print(f"--- would write {path.relative_to(ROOT)}")
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            print(f"wrote {path.relative_to(ROOT)}")


# ── check ────────────────────────────────────────────────────────────────────

def check(args) -> int:
    ok = True

    def line(good: bool, text: str):
        nonlocal ok
        ok &= good
        print(("  ok   " if good else "  --   ") + text)

    print(f"operator-design at {ROOT}")
    line(sys.version_info >= (3, 10), f"Python {platform.python_version()} ({args.python})")
    res = subprocess.run([args.python, str(SERVER), "--check"], capture_output=True, text=True, timeout=60)
    line(res.returncode == 0, "server starts: " + (res.stdout.splitlines()[0] if res.stdout else res.stderr.strip()[:200]))
    line(shutil.which("rsvg-convert") is not None, "rsvg-convert (frames render to PNG; needed for render_frame and perceptibility)")
    line((ROOT / ".mcp.json").exists(), ".mcp.json (Claude Code picks the server up when it opens this repo)")
    for r in roles_mod.roles().values():
        line((ROOT / ".claude/agents" / f"{r['name']}.md").exists(), f".claude/agents/{r['name']}.md")
        line((ROOT / ".codex/agents" / f"{r['codex_name']}.toml").exists(), f".codex/agents/{r['codex_name']}.toml")
    line(desktop_config().exists() and NAME in desktop_config().read_text(encoding="utf-8"), f"Claude Desktop config ({desktop_config()})")
    cx = Path.home() / ".codex/config.toml"
    line(cx.exists() and "mcp_servers.operator_design" in cx.read_text(encoding="utf-8"), f"Codex config ({cx})")
    lm = Path.home() / ".lmstudio/mcp.json"
    line(lm.exists() and NAME in lm.read_text(encoding="utf-8"), f"LM Studio ({lm})")
    print("Missing client configs are fine for clients you don't use.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Set up the operator-design MCP server in a client.")
    ap.add_argument("client", choices=["claude-code", "claude-desktop", "codex", "lmstudio", "ollama", "print", "agents", "check"])
    ap.add_argument("--scope", choices=["project", "user"])
    ap.add_argument("--python", default=sys.executable, help="interpreter the client should run (default: this one)")
    ap.add_argument("--profile", choices=["full", "compact"])
    ap.add_argument("--endpoint", help="OpenAI-compatible base URL the server uses for run=true agents")
    ap.add_argument("--model", help="model name on that endpoint")
    ap.add_argument("--approver", help="name allowed to approve training proposals over MCP")
    ap.add_argument("--colour", "--color", action="store_true",
                    help="allow colour in this harness (grey is the default; red stays reserved)")
    ap.add_argument("--sdk", help="path to a local open-xy checkout, for the sdk_test tool")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    c = args.client

    if c == "agents":
        gen_agents(args.dry_run)
    elif c == "check":
        return check(args)
    elif c == "print":
        print(json.dumps({"mcpServers": {NAME: stdio_entry(args)}}, indent=2))
        print(f"\nCommand line: {args.python} {SERVER}")
    elif c == "claude-code":
        if (args.scope or "project") == "project":
            merge_json(ROOT / ".mcp.json", stdio_entry(args, portable=True), args.dry_run)
            print("Open this repo in Claude Code and approve the operator-design server when asked.")
        else:
            cmd = ["claude", "mcp", "add", "-s", "user"]
            for k, v in env_for(args).items():
                cmd += ["-e", f"{k}={v}"]
            cmd += ["-t", "stdio", NAME, "--", args.python, str(SERVER)]  # -t between -e and the name, per the CLI
            if args.dry_run or not shutil.which("claude"):
                print(("--- would run: " if args.dry_run else "claude CLI not found; run this once it's installed:\n  ") + " ".join(cmd))
            else:
                subprocess.run(cmd, check=False)
        gen_agents(args.dry_run)
    elif c == "claude-desktop":
        merge_json(desktop_config(), stdio_entry(args), args.dry_run)
        print("Restart Claude Desktop to load it.")
    elif c == "codex":
        path = (ROOT / ".codex/config.toml") if args.scope == "project" else Path.home() / ".codex/config.toml"
        write_codex(path, args)
        if args.scope == "project":
            print("Project config only loads in trusted projects (Codex asks the first time).")
        gen_agents(args.dry_run)
    elif c == "lmstudio":
        merge_json(Path.home() / ".lmstudio/mcp.json", stdio_entry(args, "lmstudio"), args.dry_run)
        print("In LM Studio: Program tab → Install → Edit mcp.json shows it. Pick a model with tool use; the compact "
              "profile keeps the tool list short.")
    elif c == "ollama":
        path = Path.home() / ".config/ollmcp/mcp-servers/operator-design.json"
        merge_json(path, stdio_entry(args, "ollama"), args.dry_run)
        model = args.model or "qwen3:8b"
        print(f"Ollama has no MCP client of its own; use mcp-client-for-ollama:\n"
              f"  pip install mcp-client-for-ollama   (or: uvx ollmcp)\n"
              f"  ollmcp -j {path} -m {model}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
