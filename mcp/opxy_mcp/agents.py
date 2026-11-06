"""Agent roles: one definition per role in training/agents/*.md, turned into briefs for whichever client runs them.

Three ways a role gets run, so the same pipeline works in Claude, Codex and local models:

1. Client subagents (default). The server returns a brief; Claude Code runs it with the matching
   .claude/agents/<role>.md subagent, Codex with .codex/agents/<role>.toml. Both are generated from these files
   by `python3 mcp/setup.py agents`.
2. An OpenAI-compatible endpoint (LM Studio, Ollama, llama.cpp, vLLM, or a hosted API). Set OPXY_AGENT_ENDPOINT
   and OPXY_AGENT_MODEL and pass run=true; the server calls the model itself and records the result.
3. By hand: a person reads the brief and records the verdict with training_record.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

from .paths import AGENT_ROLES, ToolError, rel

FRONT = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)


def parse_role(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = FRONT.match(text)
    if not m:
        raise ToolError(f"{rel(path)} has no frontmatter")
    meta: dict = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            meta[k.strip()] = [x.strip() for x in v[1:-1].split(",") if x.strip()]
        else:
            meta[k.strip()] = v
    meta["instructions"] = m.group(2).strip()
    meta["file"] = rel(path)
    return meta


def roles() -> dict[str, dict]:
    out = {}
    for p in sorted(AGENT_ROLES.glob("*.md")):
        r = parse_role(p)
        out[r["stage"]] = r
    return out


def role(stage: str) -> dict:
    r = roles().get(stage)
    if r is None:
        raise ToolError(f"no agent role for stage '{stage}' in training/agents/")
    return r


def how_to_run(r: dict) -> dict:
    return {
        "claudeCode": f"Task/Agent tool with subagent_type \"{r['name']}\" and the brief as its prompt.",
        "codex": f"Ask Codex to have {r['codex_name']} run the brief (custom agent in .codex/agents/).",
        "endpoint": "Set OPXY_AGENT_ENDPOINT + OPXY_AGENT_MODEL and call again with run=true.",
        "byHand": "Read the brief, do the work, record the result with the tool it names.",
    }


# ── endpoint ─────────────────────────────────────────────────────────────────

def endpoint() -> dict | None:
    base = os.environ.get("OPXY_AGENT_ENDPOINT")
    model = os.environ.get("OPXY_AGENT_MODEL")
    if not base or not model:
        return None
    return {"base": base.rstrip("/"), "model": model, "key": os.environ.get("OPXY_AGENT_API_KEY", ""),
            "timeout": float(os.environ.get("OPXY_AGENT_TIMEOUT", "300"))}


def chat(system: str, user: str) -> str:
    ep = endpoint()
    if ep is None:
        raise ToolError("run=true needs OPXY_AGENT_ENDPOINT (e.g. http://localhost:1234/v1 for LM Studio, "
                        "http://localhost:11434/v1 for Ollama) and OPXY_AGENT_MODEL")
    url = ep["base"] + ("" if ep["base"].endswith("/chat/completions") else "/chat/completions")
    body = json.dumps({"model": ep["model"], "temperature": 0.4,
                       "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}).encode()
    headers = {"Content-Type": "application/json"}
    if ep["key"]:
        headers["Authorization"] = f"Bearer {ep['key']}"
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=ep["timeout"]) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise ToolError(f"agent endpoint returned {exc.code}: {exc.read()[:300].decode('utf-8', 'replace')}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ToolError(f"can't reach the agent endpoint at {ep['base']}: {exc}") from exc
    try:
        return data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError) as exc:
        raise ToolError(f"agent endpoint answered in an unexpected shape: {str(data)[:300]}") from exc


def fenced(text: str, lang: str) -> str | None:
    m = re.search(rf"```{lang}\s*\n(.*?)```", text, re.S | re.I)
    if m:
        return m.group(1).strip()
    if lang == "json":
        m = re.search(r"\{.*\}", text, re.S)
        return m.group(0) if m else None
    if lang == "svg":
        m = re.search(r"<svg\b.*?</svg>", text, re.S)
        return m.group(0) if m else None
    return None


def run_json_role(stage: str, brief: str) -> dict:
    r = role(stage)
    reply = chat(r["instructions"], brief)
    raw = fenced(reply, "json")
    try:
        data = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        data = None
    if not isinstance(data, dict):
        raise ToolError(f"the {stage} agent didn't answer with the JSON the brief asks for; first 300 chars: {reply[:300]}")
    return data


# ── design briefs ────────────────────────────────────────────────────────────

def designer_brief(record: dict, direction: dict, pdir: Path) -> dict:
    r = role("design")
    out_dir = rel(pdir / direction["variant"])
    if record["kind"] == "subject":
        task = (f"Write {out_dir}/candidate.json with keys variant, angle, drawing_language, subject, controls "
                f"(list, one sentence per control in order), reference, risks, and pattern only if one inspired it (else \"none\").")
        reply = "Reply with the candidate as one ```json block."
    else:
        subj = record.get("subject") or {}
        task = (f"Draw {out_dir}/rest.svg (480 × 220, from opxy/templates/frame.svg) of the chosen subject"
                + (f": {subj.get('subject')} ({subj.get('angle') or subj.get('pattern')}, {subj.get('drawing_language')})" if subj else "")
                + ". Lint it with zero errors and look at it at 1:1.")
        reply = "Reply with the frame as one ```svg block."
    from .paths import colour_policy
    pol = colour_policy()
    brief = "\n".join([
        f"Machine: {record['machine']} · category: {record['category']} · pass: {record['kind']} #{record['number']}",
        f"Colour: {pol['mode']} ({pol['set']})",
        f"Your variant: {direction['variant']} of 5",
        f"Your direction: {direction['brief']}",
        "House rules for this pass: no text or numbers in the drawing (names and values live in the header); show a "
        "state with line weight, brightness or hatching, not a flat grey fill; fill only what is a solid body.",
        f"Focus: {record['focus']}" if record.get("focus") else "",
        f"Task: {task}",
        reply,
    ]).strip()
    return {"variant": direction["variant"], "agent": r["name"], "codexAgent": r["codex_name"],
            "outputDir": out_dir, "brief": brief, "howToRun": how_to_run(r)}


def run_designers(record: dict, pdir: Path, briefs: list[dict]) -> list[dict]:
    """Run each designer brief on the configured endpoint and write its output into its own variant folder."""
    r = role("design")
    out = []
    for b in briefs:
        try:
            reply = chat(r["instructions"], b["brief"])
            if record["kind"] == "subject":
                raw = fenced(reply, "json")
                data = json.loads(raw) if raw else None
                if not isinstance(data, dict):
                    raise ToolError("no JSON candidate in the reply")
                data["variant"] = b["variant"]
                (pdir / b["variant"] / "candidate.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
                out.append({"variant": b["variant"], "wrote": rel(pdir / b["variant"] / "candidate.json")})
            else:
                svg = fenced(reply, "svg")
                if not svg:
                    raise ToolError("no SVG in the reply")
                (pdir / b["variant"] / "rest.svg").write_text(svg + "\n", encoding="utf-8")
                out.append({"variant": b["variant"], "wrote": rel(pdir / b["variant"] / "rest.svg")})
        except (ToolError, json.JSONDecodeError) as exc:
            out.append({"variant": b["variant"], "error": str(exc)})
    return out
