---
name: opxy-train
description: Training mode for the operator-design guidelines — add a new pattern or category, write down a pitfall, or improve a doc through draft, audit, review, gate and the person's approval, with a separate agent at each stage. Use when a screen taught something the guidelines should keep.
---

# Training mode

You're running `training/README.md`. The guidelines only change through proposals, and every proposal passes an auditor, a reviewer and a deterministic gate before a person approves it.

## Steps

1. **Find the idea and its evidence.** One idea per proposal: a pattern, a category, a pitfall or an improvement. Point at the frames, contact sheets, audits or videos it comes from. Read the sections it touches (`opxy_guide`, `opxy_search`) and check it isn't already there.
2. **Draft** as the drafter (`training/agents/drafter.md`). Call `training_propose` with the smallest ops that do it. A new pattern is `insert_section` into `opxy/patterns.md` before `## P8 · Headers` with **The idea.**, **Why it works.**, a build or channel section and **Pitfalls.**; `set_json` on `/patterns/P<n>` in `opxy/catalog.json` with its categories; and its row in the `opxy/categories.md` table. First-person voice, the how and the why.
3. **Advance.** `training_advance` submits it and returns the auditor's brief. Run it in a **separate** `opxy-auditor` subagent that hasn't seen your drafting; it records its verdict with `training_record`.
4. **Advance again** for the reviewer brief and run it in a separate `opxy-reviewer` subagent. The reviewer doesn't see the audit.
5. **Sent back?** Revise with `training_revise` (say what changed), then advance from step 3. Both verdicts reset on every revision.
6. **Gate.** `training_advance` runs it when the review passes. Fix whatever fails and go round again; never work around a gate check.
7. **Stop at approval.** Show the person the diff (`training_get`) and the gate table, and tell them how to approve: `python3 mcp/train.py approve <id> --by "<name>"`. Never call `training_approve` yourself.

Without the MCP server, the same steps run from a terminal with `python3 mcp/train.py`, and the agent roles are in `.claude/agents/`.

## Hard rules

- Drafter, auditor and reviewer are three different agents. Don't record a verdict on a proposal you drafted.
- open-xy wins every disagreement. A proposal that contradicts `opxy/constraints.md` is rejected, not argued.
- A token change comes with its `constraints.md` change and a bumped `source.ref`, and it can't make a library entry worse.
- Five unique variants per design pass is fixed; no proposal changes it.
- Code in `opxy/tools/` changes through a normal pull request, not training mode.
