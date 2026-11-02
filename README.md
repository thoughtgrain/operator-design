# operators

My working context for designing for the Teenage Engineering OP-XY. Protocols, patterns, constraints and tooling live here so that I (and any agent I hand work to) design the same way every time.

Right now it holds one module: **`opxy/`**, the protocol for designing the screen a custom machine draws on the OP-XY through the [open-xy SDK](https://github.com/etcetc000/open-xy). More modules can sit beside it later (sequencing workflows, preset design, sound-design notes) without touching it.

It's also an **MCP server** (`mcp/`), so Claude Code, Claude Desktop, Codex, LM Studio and Ollama can run the protocol with the real tools: every generative design pass is five unique variants, and **training mode** (`training/`) is how the guidelines learn, through draft → audit → review → gate → my approval, with a separate agent at each stage.

## Quick start

```sh
# Claude Code: open this repo; .mcp.json registers the server.
python3 mcp/setup.py claude-desktop        # or: codex, lmstudio --model …, ollama --model …, print
python3 mcp/setup.py check
```

Details per client are in [`mcp/README.md`](mcp/README.md).

## Layout

```
operators/
├── README.md                      ← you are here
├── AGENTS.md                      ← agent entry point: what to load for which task
├── CLAUDE.md                      ← imports AGENTS.md for Claude Code
├── .mcp.json                      ← registers the MCP server for Claude Code
├── mcp/                           ← the MCP server, client setup and the training CLI
├── training/                      ← training mode: process, agent roles, proposals, changelog
├── .claude/agents/, .codex/agents/ ← designer, drafter, auditor, reviewer (generated from training/agents/)
├── .claude/skills/opxy-screen/    ← skill that runs the screen protocol end to end
├── .claude/skills/opxy-audit/     ← skill that audits a finished screen and adds passing ones to the library
├── opxy/
│   ├── README.md                  ← module index and reading order
│   ├── categories.md              ← engine, drum, sampler, effect, player, sequencer, function
│   ├── catalog.json               ← categories, patterns by category, library, five-iteration settings
│   ├── protocol.md                ← the phases, gates and outputs
│   ├── patterns.md                ← composition patterns and the visual-channel table
│   ├── constraints.md             ← hard limits distilled from open-xy, with sources
│   ├── craft.md                   ← one drawing language, line weights, the side-by-side review
│   ├── accessibility.md           ← legibility, contrast and motion on a 480 × 220 grey screen
│   ├── audit.md                   ← how a finished screen is judged and enters the library
│   ├── tokens.json                ← machine-readable numbers the tools and agents use
│   ├── templates/                 ← brief and starter frame
│   ├── tools/                     ← frame linter and contact-sheet builder (stdlib Python)
│   └── reference/                 ← annotated reference screens
├── screens/                       ← work in progress, one folder per machine
└── library/                       ← audited screens that met the guidelines, kept as references
```

## How it relates to open-xy

open-xy owns the truth about the device: the display ABI, the UX conventions machines are reviewed against, and `sdk.py test`. I don't fork those rules here. `opxy/constraints.md` restates the numbers I design against and links every one back to its source, so when the SDK moves I update one file.

What open-xy doesn't cover is the design process itself: going from "here's a sound and its parameters" to a screen where every control reads, inside the node budget, before anyone writes `display.cpp`. That's what this repo is for.

## Adding a module

1. Make a top-level folder named for the domain (`opxy-presets/`, `sequencing/`).
2. Give it a `README.md` with its reading order, and keep hard limits in one `constraints.md` with sources.
3. Add a routing line to `AGENTS.md` so agents know when to load it.
4. If an agent should run it end to end, add a skill under `.claude/skills/`.
5. If the MCP server should expose it, add its docs to `mcp/opxy_mcp/knowledge.py` → `DOCS` and its tools to `tools.py`.

Not affiliated with Teenage Engineering or the open-xy project. OP-XY is a Teenage Engineering trademark. Nothing in here copies stock artwork.
