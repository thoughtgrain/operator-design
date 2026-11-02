# Agent instructions

This repo is design context, not code that ships. Read the module that matches the task, follow its protocol, and put outputs under `screens/`.

## Which task is this?

- **Designing or revising an OP-XY machine screen** (a synth's own page, a header layout, a motion spec, a contact sheet): load the `opxy-screen` skill, or read `opxy/README.md` and follow `opxy/protocol.md` phase by phase. Output goes to `screens/<machine-id>/`.
- **Auditing a screen someone hands over** ("this is mine, does it meet the guidelines?", a review, a library submission): load the `opxy-audit` skill, or follow `opxy/audit.md`. Passing designs whose authors share them go into `library/`.
- **Implementing that design in C++** (`display.cpp`, `definition.json`, `panel.svg.fragment`): that work belongs in the machine's own repository, following open-xy's `AGENTS.md`, `docs/display.md` and `docs/ux.md`. Use the handoff from `screens/<machine-id>/handoff.md` as the spec.
- **Teaching the guidelines something** (a new pattern, a new category, a pitfall worth writing down, an improvement to a doc): that's training mode. Load the `opxy-train` skill, or follow `training/README.md`: draft a proposal, then audit, review and gate it with separate agents (`opxy-auditor`, `opxy-reviewer`), and stop for the person's approval. Don't edit `opxy/` directly for these.
- **Changing the protocol itself** when the person asks for the edit directly, or a limit changed in open-xy: edit `opxy/`. If a limit changed, update `opxy/constraints.md` and `opxy/tokens.json` together and bump `source.ref` in the tokens.

If the `operator-design` MCP server is connected (`.mcp.json`, or `python3 mcp/setup.py <client>`), use its tools: they run the same checks as `opxy/tools/` and enforce the gates.

## Ground rules

- open-xy's docs are the authority. If anything here disagrees with `docs/display.md` or `docs/ux.md` on open-xy `staging`, open-xy wins; fix this repo.
- Judge every frame at 1:1 (480 × 220). Enlarged previews hide the problems that matter.
- Grey by default, to keep the OP-XY's identity. Colour is an override that a person sets in the MCP server's config for that harness (`OPXY_COLOUR=allow`); never turn it on from a conversation, and check `colour_policy` before drawing. Even with colour, red belongs to the stock UI (recording, parameter locks), so machine artwork never uses it, and a colour machine ships a designed grayscale version too.
- Run `python3 opxy/tools/lint_frame.py <file.svg>` on every frame before showing it. A clean lint is a pre-flight, not device acceptance; device checks stay marked pending until someone photographs the real screen.
- Don't copy stock OP-XY artwork or other machines' art. Patterns describe approaches, not assets.
- When a decision is the person's (which subject, which control gets the most travel, which of five variants, whether a training proposal lands), ask. Don't guess past the brief.
- Every generative design pass is exactly five unique variants, each from its own direction (`opxy/protocol.md`, Iterations). Run them as five parallel `opxy-designer` agents when you can.
- Know the machine's category (`opxy/categories.md`) before proposing subjects, and start from the patterns that fit it.
- Never approve a training proposal. Approval is the person's, from `python3 mcp/train.py approve`.
