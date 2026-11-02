"""MCP prompts (slash commands in clients that show them) and resources (every doc, library card and proposal)."""
from __future__ import annotations

from . import knowledge
from .paths import LIBRARY, PROPOSALS, ToolError, catalog

PROMPTS = {
    "design-screen": {
        "description": "Design an OP-XY machine screen through the opxy protocol, five unique variants per pass.",
        "arguments": [{"name": "machine_id", "description": "SDK machine id", "required": True},
                      {"name": "category", "description": "engine, drum, sampler, effect, player, sequencer or function", "required": False},
                      {"name": "notes", "description": "what the sound does, where the controls come from", "required": False}],
        "text": ("Design the screen for OP-XY machine `{machine_id}`{category_part}. {notes}\n\n"
                 "Use the operator-design tools. Read opxy_guide(doc='protocol') and opxy_guide(doc='categories') first. "
                 "Run screen_status (or screen_init if it's new), then follow the protocol phase by phase and don't pass a gate "
                 "that hasn't passed. Every generative pass is five unique variants: design_pass_start → run the five designer "
                 "briefs (in parallel subagents if you can) → design_pass_submit → show the person all five at 1:1 → "
                 "design_pass_select with their pick. Ask the person whenever a decision is theirs (the subject, which control "
                 "gets the most travel). Lint every frame, run check_perceptibility, look at contact_sheet at 1:1. Device checks "
                 "stay pending."),
    },
    "audit-screen": {
        "description": "Audit a finished screen against the guidelines and draft the report.",
        "arguments": [{"name": "material_dir", "description": "folder with definition.json and/or frames", "required": True},
                      {"name": "scores", "description": "audible scores 1–5 in control order, comma separated", "required": False}],
        "text": ("Audit the screen in `{material_dir}` per opxy/audit.md. Ask first, in one line, whether it's the person's own "
                 "work and under what licence. Run audit_run (scores: {scores}); if there are no scores, score from the sound "
                 "and ask the person to confirm. Then do the by-eye checks it lists, at 1:1, and give the verdict: meets, meets "
                 "with notes, or not yet with changes in order of impact. Never lower a score to reach meets."),
    },
    "propose-improvement": {
        "description": "Training mode: draft a new pattern, category or improvement and push it through audit, review and the gate.",
        "arguments": [{"name": "idea", "description": "what the guidelines should learn", "required": True},
                      {"name": "evidence", "description": "screens, frames or audits that show it", "required": False}],
        "text": ("Training mode. The guidelines should learn: {idea}\nEvidence: {evidence}\n\n"
                 "Read training/README.md (opxy_guide doc='training'). As the drafter, write one proposal with training_propose: "
                 "the smallest ops that do it, house structure for patterns, first-person voice, categories named. Then call "
                 "training_advance and run the agent it hands back for each stage (auditor, then reviewer, each a separate "
                 "subagent that hasn't seen the drafting). When something comes back, revise and advance again. Stop at "
                 "awaiting_approval and show the person the diff and gate results; approval is theirs."),
    },
    "run-training-queue": {
        "description": "Training mode: move every open proposal one stage on, triggering the agent each needs.",
        "arguments": [],
        "text": ("List open proposals with training_list. For each one not awaiting approval, call training_advance and run "
                 "the agent it names in its own subagent (opxy-auditor, opxy-reviewer, opxy-drafter). Never approve. Finish "
                 "with a short table: proposal, stage, what happened, what it needs next."),
    },
}


def list_prompts() -> list[dict]:
    return [{"name": k, "description": v["description"], "arguments": v["arguments"]} for k, v in PROMPTS.items()]


def get_prompt(name: str, args: dict) -> dict:
    p = PROMPTS.get(name)
    if p is None:
        raise ToolError(f"no prompt {name}")
    for a in p["arguments"]:
        if a["required"] and not args.get(a["name"]):
            raise ToolError(f"prompt {name} needs {a['name']}")
    vals = {a["name"]: (args.get(a["name"]) or "—") for a in p["arguments"]}
    vals["category_part"] = f" (category: {args['category']})" if args.get("category") else ""
    vals["notes"] = args.get("notes") or ""
    text = p["text"].format(**vals)
    return {"description": p["description"], "messages": [{"role": "user", "content": {"type": "text", "text": text}}]}


def list_resources() -> list[dict]:
    out = [{"uri": f"opxy://doc/{name}", "name": f"{name}.md", "mimeType": "text/markdown",
            "description": f"opxy doc: {name}"} for name, path in knowledge.DOCS.items() if path.exists()]
    out.append({"uri": "opxy://catalog", "name": "catalog.json", "mimeType": "application/json",
                "description": "Categories, patterns by category, library, iteration settings"})
    out.append({"uri": "opxy://tokens", "name": "tokens.json", "mimeType": "application/json", "description": "Device numbers"})
    for entry in catalog().get("library", {}):
        if (LIBRARY / entry / "README.md").exists():
            out.append({"uri": f"opxy://library/{entry}", "name": f"library/{entry}", "mimeType": "text/markdown",
                        "description": f"Library card: {entry}"})
    for p in sorted(PROPOSALS.glob("*/proposal.json")):
        out.append({"uri": f"opxy://proposal/{p.parent.name}", "name": f"proposal {p.parent.name}",
                    "mimeType": "application/json", "description": "Training proposal"})
    return out


def read_resource(uri: str) -> dict:
    from .paths import OPXY
    if uri.startswith("opxy://doc/"):
        name = uri.rsplit("/", 1)[1]
        return {"uri": uri, "mimeType": "text/markdown", "text": knowledge.doc_text(name)}
    if uri == "opxy://catalog":
        return {"uri": uri, "mimeType": "application/json", "text": (OPXY / "catalog.json").read_text(encoding="utf-8")}
    if uri == "opxy://tokens":
        return {"uri": uri, "mimeType": "application/json", "text": (OPXY / "tokens.json").read_text(encoding="utf-8")}
    if uri.startswith("opxy://library/"):
        entry = uri.rsplit("/", 1)[1]
        card = LIBRARY / entry / "README.md"
        if entry in catalog().get("library", {}) and card.exists():
            return {"uri": uri, "mimeType": "text/markdown", "text": card.read_text(encoding="utf-8")}
    if uri.startswith("opxy://proposal/"):
        pid = uri.rsplit("/", 1)[1]
        f = PROPOSALS / pid / "proposal.json"
        if f.exists() and "/" not in pid and ".." not in pid:
            return {"uri": uri, "mimeType": "application/json", "text": f.read_text(encoding="utf-8")}
    raise ToolError(f"no resource {uri}")
