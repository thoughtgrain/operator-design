"""The tool registry: names, descriptions, input schemas, handlers and which profile exposes each one.

Profiles:
    full     everything (Claude Code, Claude Desktop, Codex)
    compact  a short list with short descriptions for local models with small context windows
Set with OPXY_PROFILE.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable

from . import knowledge, passes, screens, training
from .agents import roles

S = "string"
STR = {"type": S}
BOOL = {"type": "boolean"}
INT = {"type": "integer"}
STRS = {"type": "array", "items": STR}
INTS = {"type": "array", "items": {"type": "integer", "minimum": 1, "maximum": 5}}
CATEGORY = {"type": S, "enum": ["engine", "drum", "sampler", "effect", "player", "sequencer", "function"]}
PATHS = {"anyOf": [STR, STRS], "description": "a file, a directory of SVGs, a glob, or a list of those"}
OPS_SCHEMA = {"type": "array", "description": "edit ops; see training/README.md → Ops", "items": {
    "type": "object", "required": ["op", "file"], "properties": {
        "op": {"type": S, "enum": list(training.OPS)}, "file": STR, "heading": STR, "before": STR, "after": STR,
        "content": STR, "find": STR, "replace": STR, "pointer": STR, "value": {}, "delete": BOOL}}}


@dataclass
class Tool:
    name: str
    description: str
    props: dict
    handler: Callable
    required: list[str] = field(default_factory=list)
    compact: bool = False
    short: str | None = None
    read_only: bool = True
    destructive: bool = False

    def schema(self) -> dict:
        return {"type": "object", "properties": self.props, "required": self.required, "additionalProperties": False}

    def describe(self, profile: str) -> dict:
        d = {"name": self.name, "description": (self.short if profile == "compact" and self.short else self.description),
             "inputSchema": self.schema(),
             "annotations": {"readOnlyHint": self.read_only, "destructiveHint": self.destructive,
                             "idempotentHint": self.read_only, "openWorldHint": False}}
        return d


def _p(**props):
    return props


TOOLS: list[Tool] = [
    # knowledge ──────────────────────────────────────────────────────────────
    Tool("opxy_guide",
         "Read the opxy design docs (protocol, categories, constraints, patterns, craft, accessibility, audit, reference, "
         "agents, library, training, template-brief, template-audit, template-library-card). Without section, returns the "
         "outline and as much text as fits; with section, just that heading's text. Start here before designing.",
         _p(doc={"type": S, "enum": list(knowledge.DOCS)}, section=STR, max_chars=INT),
         lambda a: knowledge.guide(a.get("doc", "index"), a.get("section"), a.get("max_chars", knowledge.DEFAULT_MAX)),
         compact=True, short="Read an opxy doc or one section of it (doc: protocol, constraints, patterns, craft, ...)."),
    Tool("opxy_search", "Search every opxy doc for a phrase; returns the best-matching sections with a snippet.",
         _p(query=STR, limit=INT, docs=STRS), lambda a: knowledge.search(a["query"], a.get("limit", 8), a.get("docs")),
         ["query"], compact=True, short="Search the opxy docs."),
    Tool("opxy_categories", "Machine categories (engine, drum, sampler, effect, player, sequencer, function) with their SDK "
         "kinds, the patterns that fit each, and the library entries in each.",
         {}, lambda a: knowledge.categories()),
    Tool("opxy_patterns", "List composition patterns (optionally only those that fit a category), or get one pattern's "
         "full text by id (P1–P15…).",
         _p(pattern_id=STR, category=CATEGORY), lambda a: knowledge.patterns(a.get("pattern_id"), a.get("category")),
         compact=True, short="List patterns (filter by category) or read one by id."),
    Tool("opxy_tokens", "The device numbers from opxy/tokens.json, whole or at a JSON pointer (e.g. /perceptibility/channelFloors).",
         _p(pointer=STR), lambda a: knowledge.token_value(a.get("pointer"))),
    Tool("opxy_library", "Audited reference screens: list them (optionally by category) or read one entry's card, audit and files.",
         _p(entry=STR, category=CATEGORY), lambda a: knowledge.library(a.get("entry"), a.get("category"))),
    # screens ────────────────────────────────────────────────────────────────
    Tool("screen_init", "Start screens/<machine_id>/ with a brief (machine id, SDK kind and category filled in) and a starter "
         "rest frame. Refuses to overwrite an existing brief.",
         _p(machine_id=STR, category=CATEGORY, kind={"type": S, "enum": ["synth", "sample", "effect"]}, name=STR),
         lambda a: screens.screen_init(a["machine_id"], a["category"], a.get("kind", "synth"), a.get("name")),
         ["machine_id", "category"], read_only=False),
    Tool("screen_status", "Where a screen is in the protocol: which phase files exist, frames present and missing, design "
         "passes and their state, and the next step.",
         _p(machine_id=STR), lambda a: screens.screen_status(a["machine_id"]), ["machine_id"], compact=True,
         short="Which protocol phase a screen is at, and what's next."),
    Tool("lint_definition", "Review a definition.json against open-xy's contract and the ux.md rules (wraps opxy/tools/lint_definition.py).",
         _p(path=STR, machine_json=STR, kind={"type": S, "enum": ["synth", "sample", "effect"]}, strict=BOOL),
         lambda a: screens.lint_definition(a["path"], a.get("machine_json"), a.get("kind"), a.get("strict", False)), ["path"]),
    Tool("lint_frames", "Check frames against the device drawing rules (wraps opxy/tools/lint_frame.py). Findings are grouped "
         "by rule; every error is kept. A clean lint is a pre-flight, not device acceptance.",
         _p(paths=PATHS, definition=STR, two_page=BOOL, own_header=BOOL, fragment=BOOL, strict=BOOL),
         lambda a: screens.lint_frames(a["paths"], a.get("definition"), a.get("two_page", False), a.get("own_header", False),
                                       a.get("fragment", False), a.get("strict", False)),
         ["paths"], compact=True, short="Lint SVG frames against the device rules."),
    Tool("check_perceptibility", "Measure how much of the screen each control changes at 0/50/100 against floors scaled by its "
         "audible score 1–5, plus the note response (wraps opxy/tools/perceptibility.py). Never lower a score to pass.",
         _p(frames_dir=STR, scores=INTS, names=STRS, two_page=BOOL, header_bottom=INT),
         lambda a: screens.check_perceptibility(a["frames_dir"], a["scores"], a.get("names"), a.get("header_bottom"),
                                                a.get("two_page", True)),
         ["frames_dir", "scores"], compact=True, short="Check each control changes enough of the screen for its score."),
    Tool("contact_sheet", "Tile rest, playing and c<N>-000/050/100 frames into a 1:1 contact sheet; returns the PNG so you can look at it.",
         _p(frames_dir=STR, out=STR, png=BOOL, show=BOOL),
         lambda a: screens.contact_sheet(a["frames_dir"], a.get("out"), a.get("png", True), a.get("show", True)),
         ["frames_dir"], read_only=False),
    Tool("render_frame", "Render one frame (SVG, or a PNG capture) at 1:1 on black and return it as an image, so you judge "
         "what the device would show. scale 2 is for inspection only.",
         _p(path=STR, scale={"type": "integer", "enum": [1, 2]}),
         lambda a: screens.render_frame(a["path"], a.get("scale", 1)), ["path"], compact=True,
         short="Render a frame at 1:1 and return the image."),
    Tool("audit_run", "Run every check that applies to a folder of material (definition, frames, fragment, scores) and write a "
         "draft audit report where anything by eye says 'not checked'. The verdict stays the auditor's.",
         _p(material_dir=STR, scores=INTS, names=STRS, definition=STR, two_page=BOOL, fragment=STR, author=STR, licence=STR,
            write_report=BOOL, out_dir=STR),
         lambda a: screens.audit_run(a["material_dir"], a.get("scores"), a.get("names"), a.get("definition"),
                                     a.get("two_page", False), a.get("fragment"), a.get("author"), a.get("licence"),
                                     a.get("write_report", True), a.get("out_dir")),
         ["material_dir"], read_only=False),
    # design passes ──────────────────────────────────────────────────────────
    Tool("design_pass_start", "Open a design pass for a screen. Every pass (subject, frames, revision) is exactly five unique "
         "variants: this assigns each its own direction (pattern × drawing language for subjects, composition × camera × "
         "emphasis for frames) and returns five designer briefs to run in parallel. run=true runs them on "
         "OPXY_AGENT_ENDPOINT instead.",
         _p(machine_id=STR, kind={"type": S, "enum": ["subject", "frames", "revision"]}, category=CATEGORY, focus=STR,
            exclude_patterns=STRS, run=BOOL),
         lambda a: passes.design_pass_start(a["machine_id"], a["kind"], a.get("category"), a.get("focus"),
                                            a.get("exclude_patterns"), a.get("run", False)),
         ["machine_id", "kind"], compact=True, read_only=False,
         short="Open a five-variant design pass and get five designer briefs."),
    Tool("design_pass_submit", "Submit the five variants of the open pass and check they're unique. Subject variants: "
         "[{variant, pattern, drawing_language, subject, controls, reference, risks}] (or leave out to read each "
         "v<N>/candidate.json). Frames: each v<N>/rest.svg is linted and compared pairwise at 1:1.",
         _p(machine_id=STR, variants={"type": "array", "items": {"type": "object"}}, pass_name=STR, two_page=BOOL, definition=STR),
         lambda a: passes.design_pass_submit(a["machine_id"], a.get("variants"), a.get("pass_name"), a.get("two_page", False),
                                             a.get("definition")),
         ["machine_id"], compact=True, read_only=False, short="Submit five variants; checks they're unique."),
    Tool("design_pass_select", "Record the person's pick from a pass that passed uniqueness, who picked it and why. "
         "apply=true copies a picked frame to frames/rest.svg. Only call this with the person's choice.",
         _p(machine_id=STR, variant=STR, reason=STR, chosen_by=STR, pass_name=STR, apply=BOOL),
         lambda a: passes.design_pass_select(a["machine_id"], a["variant"], a["reason"], a["chosen_by"], a.get("pass_name"),
                                             a.get("apply", False)),
         ["machine_id", "variant", "reason", "chosen_by"], compact=True, read_only=False,
         short="Record the person's pick from a five-variant pass."),
    Tool("design_pass_get", "Read a pass record: directions, variants, uniqueness results and the pick.",
         _p(machine_id=STR, pass_name=STR), lambda a: passes.design_pass_get(a["machine_id"], a.get("pass_name")), ["machine_id"]),
    # training ───────────────────────────────────────────────────────────────
    Tool("training_propose", "Draft a proposal that teaches the guidelines something: a new pattern, a new category, an "
         "improvement or a constraint change. Ops apply to a temporary copy first; nothing real changes until approval.",
         _p(kind={"type": S, "enum": list(training.KINDS)}, title=STR, summary=STR, rationale=STR, changes=OPS_SCHEMA,
            evidence=STRS, categories={"type": "array", "items": CATEGORY}, by=STR),
         lambda a: training.propose(a["kind"], a["title"], a["summary"], a["rationale"], a["changes"], a.get("evidence"),
                                    a.get("categories"), a.get("by", "opxy-drafter")),
         ["kind", "title", "summary", "rationale", "changes"], compact=True, read_only=False,
         short="Draft a guideline proposal (pattern, category, improvement)."),
    Tool("training_revise", "Revise a proposal after audit, review or the gate sent it back. Clears earlier verdicts; note says what changed.",
         _p(id=STR, note=STR, changes=OPS_SCHEMA, title=STR, summary=STR, rationale=STR, evidence=STRS,
            categories={"type": "array", "items": CATEGORY}, by=STR),
         lambda a: training.revise(a["id"], a.get("changes"), a.get("note", ""), a.get("by", "opxy-drafter"),
                                   title=a.get("title"), summary=a.get("summary"), rationale=a.get("rationale"),
                                   evidence=a.get("evidence"), categories=a.get("categories")),
         ["id", "note"], read_only=False),
    Tool("training_list", "List training proposals, optionally by state (draft, audit, review, gate, awaiting_approval, approved, rejected).",
         _p(state={"type": S, "enum": list(training.STAGES)}), lambda a: training.list_proposals(a.get("state"))),
    Tool("training_get", "Read a proposal with its history, verdicts, gate results and a diff against the current docs.",
         _p(id=STR, diff=BOOL), lambda a: training.get(a["id"], a.get("diff", True)), ["id"], compact=True,
         short="Read a proposal and its diff."),
    Tool("training_advance", "Move a proposal to its next stage and trigger the agent it needs: returns the brief for the "
         "auditor, reviewer or drafter (with how to run it in Claude Code, Codex or by hand), runs the gate when it's due, "
         "and stops at approval. run=true runs audit and review on OPXY_AGENT_ENDPOINT and keeps going.",
         _p(id=STR, run=BOOL, max_steps=INT), lambda a: training.advance(a["id"], a.get("run", False), a.get("max_steps", 4)),
         ["id"], compact=True, read_only=False, short="Trigger the next stage's agent for a proposal."),
    Tool("training_record", "Record an audit or review verdict (pass, changes_requested, reject) with findings. by names the "
         "agent and client; it must differ from the drafter and the earlier stage.",
         _p(id=STR, stage={"type": S, "enum": ["audit", "review"]}, verdict={"type": S, "enum": list(training.VERDICTS)},
            findings={"anyOf": [STR, STRS]}, by=STR),
         lambda a: training.record(a["id"], a["stage"], a["verdict"], a.get("findings", []), a["by"]),
         ["id", "stage", "verdict", "by"], compact=True, read_only=False, short="Record an audit or review verdict."),
    Tool("training_gate", "Run the deterministic gate on a reviewed proposal: verdicts match the current changes, three "
         "different agents, ops apply, JSON valid, pattern structure and numbering, categories, five-variant rule, tokens with "
         "constraints and source.ref, links, no colour, and a library regression under any new tokens.",
         _p(id=STR), lambda a: training.gate(a["id"]), ["id"], read_only=False),
    Tool("training_approve", "Apply an approved proposal to the docs. The person's decision: refused unless OPXY_APPROVERS "
         "lists the approver (otherwise approve from a terminal with mcp/train.py). Never call this on your own initiative.",
         _p(id=STR, approver=STR, note=STR), lambda a: training.approve(a["id"], a["approver"], a.get("note", "")),
         ["id", "approver"], read_only=False, destructive=True),
    Tool("training_reject", "Close a proposal without applying it.",
         _p(id=STR, by=STR, reason=STR), lambda a: training.reject(a["id"], a["by"], a["reason"]),
         ["id", "by", "reason"], read_only=False),
    Tool("training_roles", "The agent roles (designer, drafter, auditor, reviewer): what each does and how each client runs it.",
         {}, lambda a: {k: {kk: vv for kk, vv in v.items() if kk != "instructions"} for k, v in roles().items()}),
]

BY_NAME = {t.name: t for t in TOOLS}


def profile() -> str:
    p = os.environ.get("OPXY_PROFILE", "full").strip().lower()
    return p if p in ("full", "compact") else "full"


def visible() -> list[Tool]:
    if profile() == "compact":
        return [t for t in TOOLS if t.compact]
    return TOOLS
