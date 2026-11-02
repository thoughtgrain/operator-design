"""MCP over stdio, by hand: newline-delimited JSON-RPC 2.0 on stdin/stdout, logs on stderr.

Stdlib only so `python3 mcp/server.py` is the whole install. stdout carries protocol messages and nothing else;
anything a tool prints is captured by the runner, and logging goes to stderr.
"""
from __future__ import annotations

import json
import sys
import traceback

from . import SERVER_NAME, __version__, prompts, tools
from .paths import ToolError

SUPPORTED = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
INSTRUCTIONS = (
    "operator-design: the protocol, tools and library for designing OP-XY machine screens (open-xy SDK). "
    "Start with opxy_guide(doc='protocol') and opxy_guide(doc='categories'). Every generative design pass is exactly five "
    "unique variants (design_pass_start → five designer briefs → design_pass_submit → the person picks). Judge frames at 1:1 "
    "with render_frame. Grey is the default; colour only when this harness's config sets OPXY_COLOUR=allow (check "
    "colour_policy), and red never. Video previews are asked about after the motion spec and rendered by you, not the server; engine "
    "audio in them is a simulation (engine code on a computer), never a device recording. Training mode (training_*) changes the guidelines through draft → audit → review → gate → the "
    "person's approval; never approve on your own initiative. Decisions that are the person's (the subject, the pick, "
    "approval) are asked, not guessed."
)


def log(msg: str) -> None:
    print(f"[{SERVER_NAME}] {msg}", file=sys.stderr, flush=True)


class Server:
    def __init__(self, out=None):
        self.out = out or sys.stdout
        self.initialized = False

    # transport ───────────────────────────────────────────────────────────
    def send(self, msg: dict) -> None:
        self.out.write(json.dumps(msg, ensure_ascii=False, separators=(",", ":")) + "\n")
        self.out.flush()

    def reply(self, mid, result=None, error=None) -> None:
        msg = {"jsonrpc": "2.0", "id": mid}
        if error is not None:
            msg["error"] = error
        else:
            msg["result"] = result if result is not None else {}
        self.send(msg)

    def serve(self, stream=None) -> None:
        stream = stream or sys.stdin
        log(f"v{__version__} ready (profile {tools.profile()})")
        for line in stream:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError as exc:
                self.reply(None, error={"code": -32700, "message": f"parse error: {exc}"})
                continue
            batch = msg if isinstance(msg, list) else [msg]
            for m in batch:
                self.dispatch(m)

    # dispatch ────────────────────────────────────────────────────────────
    def dispatch(self, msg: dict) -> None:
        if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0":
            self.reply(msg.get("id") if isinstance(msg, dict) else None,
                       error={"code": -32600, "message": "invalid request"})
            return
        method, mid, params = msg.get("method"), msg.get("id"), msg.get("params") or {}
        if method is None:  # a response to something we never sent
            return
        notification = "id" not in msg
        handler = {
            "initialize": self.initialize, "ping": lambda p: {},
            "tools/list": self.tools_list, "tools/call": self.tools_call,
            "prompts/list": lambda p: {"prompts": prompts.list_prompts()},
            "prompts/get": lambda p: prompts.get_prompt(p.get("name", ""), p.get("arguments") or {}),
            "resources/list": lambda p: {"resources": prompts.list_resources()},
            "resources/templates/list": lambda p: {"resourceTemplates": []},
            "resources/read": lambda p: {"contents": [prompts.read_resource(p.get("uri", ""))]},
            "logging/setLevel": lambda p: {},
            "completion/complete": lambda p: {"completion": {"values": [], "hasMore": False}},
        }.get(method)
        if method.startswith("notifications/"):
            if method == "notifications/initialized":
                self.initialized = True
            return
        if handler is None:
            if not notification:
                self.reply(mid, error={"code": -32601, "message": f"method not found: {method}"})
            return
        try:
            result = handler(params)
        except ToolError as exc:
            if not notification:
                self.reply(mid, error={"code": -32602, "message": str(exc)})
            return
        except Exception as exc:  # never let one bad call take the server down
            log(traceback.format_exc())
            if not notification:
                self.reply(mid, error={"code": -32603, "message": f"internal error: {exc}"})
            return
        if not notification:
            self.reply(mid, result)

    # methods ─────────────────────────────────────────────────────────────
    def initialize(self, p: dict) -> dict:
        asked = p.get("protocolVersion")
        version = asked if asked in SUPPORTED else SUPPORTED[0]
        client = (p.get("clientInfo") or {}).get("name", "unknown client")
        log(f"initialize from {client}, protocol {version}")
        return {"protocolVersion": version,
                "capabilities": {"tools": {"listChanged": False}, "prompts": {"listChanged": False},
                                 "resources": {"listChanged": False, "subscribe": False}, "logging": {}},
                "serverInfo": {"name": SERVER_NAME, "title": "operator-design (OP-XY screens)", "version": __version__},
                "instructions": INSTRUCTIONS}

    def tools_list(self, p: dict) -> dict:
        prof = tools.profile()
        return {"tools": [t.describe(prof) for t in tools.visible()]}

    def tools_call(self, p: dict) -> dict:
        name, args = p.get("name"), p.get("arguments") or {}
        tool = tools.BY_NAME.get(name)
        if tool is None or tool not in tools.visible():
            raise ToolError(f"unknown tool: {name}")
        try:
            problems = check_args(tool, args)
            if problems:
                raise ToolError("; ".join(problems))
            out = tool.handler(args)
        except ToolError as exc:
            return {"content": [{"type": "text", "text": f"{name}: {exc}"}], "isError": True}
        except Exception as exc:
            log(traceback.format_exc())
            return {"content": [{"type": "text", "text": f"{name} failed unexpectedly: {exc}"}], "isError": True}
        return {"content": to_content(out), "isError": False}


def check_args(tool, args: dict) -> list[str]:
    if not isinstance(args, dict):
        return ["arguments must be an object"]
    props = tool.props
    problems = [f"missing {k}" for k in tool.required if args.get(k) in (None, "")]
    problems += [f"unknown argument {k} (expected: {', '.join(props) or 'none'})" for k in args if k not in props]
    types = {"string": str, "boolean": bool, "integer": int, "array": list, "object": dict}
    for k, v in args.items():
        spec = props.get(k) or {}
        t = spec.get("type")
        if t in types and v is not None:
            ok = isinstance(v, types[t]) and not (t == "integer" and isinstance(v, bool))
            if not ok:
                problems.append(f"{k} must be {t}")
            elif "enum" in spec and v not in spec["enum"]:
                problems.append(f"{k} must be one of {', '.join(map(str, spec['enum']))}")
    return problems


def to_content(out) -> list[dict]:
    items = out if isinstance(out, list) and out and isinstance(out[0], dict) and "type" in out[0] else [{"type": "json", "data": out}]
    content = []
    for it in items:
        if it["type"] == "json":
            content.append({"type": "text", "text": json.dumps(it["data"], indent=1, ensure_ascii=False)})
        else:
            content.append(it)
    return content
