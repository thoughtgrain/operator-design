# Training mode

How the guidelines learn. When a screen teaches me something (a new pattern that worked, a pitfall that cost a week, a category nothing fits), it goes back into `opxy/` through this pipeline instead of an ad-hoc edit:

```
draft ──▶ audit ──▶ review ──▶ gate ──▶ approval
  ▲         │         │          │          
  └─────────┴─────────┴──────────┘  sent back with findings
```

Each stage is a different actor, on purpose. The person who wrote a pattern is the worst-placed to spot what's wrong with it, so the auditor, the reviewer and the gate each look at it fresh, and nothing lands until a person says so.

| Stage | Who | Question it answers | Tool |
| --- | --- | --- | --- |
| **Draft** | drafter agent (`agents/drafter.md`) | What should change, and what's the evidence? | `training_propose`, `training_revise` |
| **Audit** | auditor agent (`agents/auditor.md`) | Is it true? Against open-xy, the constraints and its own evidence | `training_record` stage `audit` |
| **Review** | reviewer agent (`agents/reviewer.md`), without seeing the audit | Will it make the next screen better, and will the next designer understand it? | `training_record` stage `review` |
| **Gate** | the server, no model | Does it hold together mechanically? | `training_gate` |
| **Approval** | a person | Do I want this in my guidelines? | `python3 mcp/train.py approve` |

Nothing touches the real docs before approval. Every check runs on a temporary copy of the repo with the proposal's ops applied, and approval applies the same ops for real and writes a line to `CHANGELOG.md`.

## What a proposal is

`proposals/<date>-<slug>/proposal.json`: a kind (`new_pattern`, `new_category`, `improve_doc`, `constraint_change`), a title, a summary, the rationale, the evidence it rests on (files in this repo or links), the categories it touches, the list of ops, and its whole history: every verdict with who gave it and on which exact version of the changes.

I keep proposals small. One idea each: a pattern, a category, or one improvement. Two ideas in one proposal means a reviewer can't pass one and send back the other.

## Ops

Ops are edits the server can apply to a copy, diff and check. They only touch the guidelines: `opxy/*.md`, `opxy/templates/*.md`, `opxy/reference/*.md`, `opxy/tokens.json`, `opxy/catalog.json`, `AGENTS.md`, `library/README.md`, skill files, the agent roles and this file. Code in `opxy/tools/` changes through a normal pull request, not here, because a reviewer agent reading a diff isn't a test suite.

| op | fields | does |
| --- | --- | --- |
| `insert_section` | `file`, `before` or `after` (a heading), `content` | Adds a section before a heading, or after a heading's whole section |
| `replace_section` | `file`, `heading`, `content` | Replaces a heading and everything under it |
| `replace_text` | `file`, `find`, `replace` | Exact text swap; `find` must match exactly once |
| `append` | `file`, `content` | Adds to the end |
| `set_json` | `file`, `pointer`, `value` (or `delete: true`) | Sets a JSON pointer in `tokens.json` or `catalog.json` |
| `create_file` | `file`, `content` | A new doc that doesn't exist yet |

A new pattern is usually three ops: `insert_section` into `patterns.md` before `## P8 · Headers`, `set_json` on `/patterns/P<n>` in `catalog.json`, and `replace_text` adding its row to the table in `categories.md`.

## The gate

The gate is the part with no judgement in it, so it can't be talked round. It fails (and sends the proposal back to draft) if any of these is false:

- The audit and the review both passed, on these exact changes (a revision after review clears both verdicts).
- The drafter, auditor and reviewer are three different agents.
- Every op is valid, editable and applies cleanly to the current docs. If the docs moved since drafting, it says "rebase needed".
- `tokens.json` and `catalog.json` are valid, every category a pattern or library entry names exists, and design passes stay at **five variants**.
- Pattern numbers are unique, and every pattern in `patterns.md` has a `catalog.json` row (and the reverse).
- A new pattern has **The idea.**, **Why it works.** and **Pitfalls.**, a row in the `categories.md` table and the categories it fits.
- A changed token comes with a `constraints.md` change and a bumped `source.ref` (the same rule as `AGENTS.md`).
- Every link in a changed doc resolves, and no added line introduces a colour (grey only; red is stock).
- **Library regression**: when tokens change, every library entry with frames is re-linted and re-measured under the old and the new numbers. An entry that gets worse fails the gate, because `audit.md` says a moved floor means a re-audit.

Warnings (a pattern with no worked example, a "we" in first-person docs) are shown but don't block.

## Triggering the agents

`training_advance` is the one call that moves things along. It looks at the state, moves the proposal on if it can (draft → audit, gate when it's due), and hands back the brief for whichever agent the stage needs, with how to run it:

- **Claude Code** runs the brief as a subagent (`.claude/agents/opxy-auditor.md` and friends).
- **Codex** runs it as a custom agent (`.codex/agents/opxy_auditor.toml` and friends).
- **A local model** (LM Studio, Ollama, llama.cpp, or any OpenAI-compatible endpoint): set `OPXY_AGENT_ENDPOINT` and `OPXY_AGENT_MODEL` in the server's config and call `training_advance` with `run: true`. The server runs the auditor, then the reviewer, then the gate, and stops at approval or as soon as something is sent back.
- **By hand**: read the brief, record the verdict with `training_record`.

The agent definitions live once, in `agents/*.md`. `python3 mcp/setup.py agents` regenerates the Claude Code and Codex versions from them, so the roles can't drift between clients.

The reviewer's brief leaves out the drafter's rationale and the audit's findings. It gets the diff and the evidence, and judges the change on what it is, not on the argument for it.

## Approval

Approval is mine (or whoever owns the guidelines), and it's deliberately awkward for an agent to do:

```sh
python3 mcp/train.py list --state awaiting_approval
python3 mcp/train.py show <id>                 # history, verdicts, gate, the full diff
python3 mcp/train.py approve <id> --by "Brian Hinton" --note "…"
python3 mcp/train.py reject  <id> --by "Brian Hinton" --reason "…"
```

`training_approve` exists over MCP too, but it refuses unless `OPXY_APPROVERS` in the server config names the approver. I only set that in a client where every tool call asks me first. The generated subagents never get the approve tool.

After approving, I commit the changed docs together with the proposal folder, so the history of why the guidelines say what they say sits next to them in git.

## Design passes are separate

Training mode changes the guidelines. Designing a screen follows `opxy/protocol.md`, where every generative pass is five unique variants (the Iterations section) run by the designer role in `agents/designer.md`. A design pass that teaches something new is where a training proposal usually starts.
