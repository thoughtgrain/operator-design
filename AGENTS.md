# Agent instructions

This repo is design context, not code that ships. Read the module that matches the task, follow its protocol, and put outputs under `screens/`.

## Which task is this?

- **Designing or revising an OP-XY machine screen** (a synth's own page, a header layout, a motion spec, a contact sheet): load the `opxy-screen` skill, or read `opxy/README.md` and follow `opxy/protocol.md` phase by phase. Output goes to `screens/<machine-id>/`.
- **Auditing a screen someone hands over** ("this is mine, does it meet the guidelines?", a review, a library submission): load the `opxy-audit` skill, or follow `opxy/audit.md`. Passing designs whose authors share them go into `library/`.
- **Implementing that design in C++** (`display.cpp`, `definition.json`, `panel.svg.fragment`): that work belongs in the machine's own repository, following open-xy's `AGENTS.md`, `docs/display.md` and `docs/ux.md`. Use the handoff from `screens/<machine-id>/handoff.md` as the spec.
- **Changing the protocol itself**: edit `opxy/`. If a limit changed in open-xy, update `opxy/constraints.md` and `opxy/tokens.json` together and bump `source.ref` in the tokens.

## Ground rules

- open-xy's docs are the authority. If anything here disagrees with `docs/display.md` or `docs/ux.md` on open-xy `staging`, open-xy wins; fix this repo.
- Judge every frame at 1:1 (480 × 220). Enlarged previews hide the problems that matter.
- Grey only. Red belongs to the stock UI (recording, parameter locks), so machine artwork never uses it.
- Run `python3 opxy/tools/lint_frame.py <file.svg>` on every frame before showing it. A clean lint is a pre-flight, not device acceptance; device checks stay marked pending until someone photographs the real screen.
- Don't copy stock OP-XY artwork or other machines' art. Patterns describe approaches, not assets.
- When a decision is the person's (which subject, which control gets the most travel), ask. Don't guess past the brief.
