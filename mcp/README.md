# operator-design MCP server

This turns the repo into an MCP server, so Claude, Codex or a local model can work through the opxy protocol with the real tools instead of reading the docs and hoping. It's stdlib Python 3.10+, same as `opxy/tools/`: no packages, no build. `python3 mcp/server.py` is the whole install.

What it gives a client:

- **The guidelines** as tools and resources: every doc and section, a search, the pattern index by machine category, the tokens and the library.
- **The checks** as tools: `lint_definition`, `lint_frames`, `check_perceptibility`, `contact_sheet`, `audit_run`, and `render_frame`, which hands back a 1:1 PNG so a vision model actually looks at the frame instead of reasoning about SVG text.
- **Design passes** that are always five unique variants: each gets its own direction up front, and the pass doesn't close until the five are really different.
- **Training mode**: proposals that teach the guidelines something new, through draft → audit → review → gate → a person's approval, with a separate agent at each stage. See [`training/README.md`](../training/README.md).

## Setup

Pick your client. Every command merges into the existing config (other servers stay), keeps the old file as `.bak`, and takes `--dry-run` to show what it would write.

### Claude Code

Nothing to do for this repo: `.mcp.json` at the root registers the server, and `.claude/agents/` holds the designer, drafter, auditor and reviewer subagents. Open the repo, approve the `operator-design` server when Claude Code asks, and it's there.

To have it in every project:

```sh
python3 mcp/setup.py claude-code --scope user
```

### Claude Desktop

```sh
python3 mcp/setup.py claude-desktop
```

Then restart Claude Desktop. It writes the absolute path to your Python, because Desktop doesn't start servers with your shell's `PATH`.

### Codex

```sh
python3 mcp/setup.py codex                 # ~/.codex/config.toml, every project
python3 mcp/setup.py codex --scope project # .codex/config.toml, this repo only (trusted projects)
```

The custom agents in `.codex/agents/` (`opxy_designer`, `opxy_drafter`, `opxy_auditor`, `opxy_reviewer`) are already in the repo. Codex reads `AGENTS.md` too, which routes design, audit and training work.

### LM Studio

```sh
python3 mcp/setup.py lmstudio --model qwen3-8b
```

Writes `~/.lmstudio/mcp.json` with the compact tool profile, and points `run: true` agent runs at LM Studio's own server (`http://localhost:1234/v1`) with that model. Use a model that does tool calls; the compact profile keeps the tool list to 15 with short descriptions so it fits a small context.

### Ollama

Ollama doesn't speak MCP itself, so I use [mcp-client-for-ollama](https://pypi.org/project/mcp-client-for-ollama/) as the bridge:

```sh
python3 mcp/setup.py ollama --model qwen3:8b
pip install mcp-client-for-ollama
ollmcp -j ~/.config/ollmcp/mcp-servers/operator-design.json -m qwen3:8b
```

Same compact profile, with agent runs pointed at `http://localhost:11434/v1`.

### Anything else

```sh
python3 mcp/setup.py print
```

prints the generic stdio entry (`command` + `args` + `env`) that every MCP client understands.

Check what's in place any time:

```sh
python3 mcp/setup.py check
```

`rsvg-convert` (librsvg) is the one outside tool: rendering frames to PNG needs it, which `render_frame`, contact-sheet PNGs and perceptibility on SVG frames all use. macOS `brew install librsvg`, Debian/Ubuntu `apt install librsvg2-bin`.

## Configuration

Set these in the client's `env` block for the server (the setup flags write them for you):

| Variable | What it does |
| --- | --- |
| `OPXY_PROFILE` | `full` (default, 29 tools) or `compact` (15, short descriptions) |
| `OPXY_WORKSPACE` | Where `screens/` lives, if not this repo (a machine's own checkout, say). Paths outside the repo and workspace are refused |
| `OPXY_AGENT_ENDPOINT` | OpenAI-compatible base URL for `run: true`: LM Studio, Ollama, llama.cpp, vLLM, or a hosted API |
| `OPXY_AGENT_MODEL` | Model name on that endpoint |
| `OPXY_AGENT_API_KEY` | Bearer token, if the endpoint needs one |
| `OPXY_AGENT_TIMEOUT` | Seconds per agent call (default 300) |
| `OPXY_APPROVERS` | Comma-separated names allowed to approve training proposals over MCP. Unset by default, so approval happens in a terminal |

## Tools

| Group | Tools | Compact |
| --- | --- | --- |
| Knowledge | `opxy_guide`, `opxy_search`, `opxy_categories`, `opxy_patterns`, `opxy_tokens`, `opxy_library` | guide, search, patterns |
| Screens | `screen_init`, `screen_status`, `lint_definition`, `lint_frames`, `check_perceptibility`, `contact_sheet`, `render_frame`, `audit_run`, `preview_brief` | status, lint_frames, perceptibility, render, preview |
| Design passes | `design_pass_start`, `design_pass_submit`, `design_pass_select`, `design_pass_get` | start, submit, select |
| Training | `training_propose`, `training_revise`, `training_list`, `training_get`, `training_advance`, `training_record`, `training_gate`, `training_approve`, `training_reject`, `training_roles` | propose, get, advance, record |

Prompts (slash commands in clients that show them): `design-screen`, `audit-screen`, `propose-improvement`, `run-training-queue`. Resources: `opxy://doc/<name>`, `opxy://catalog`, `opxy://tokens`, `opxy://library/<entry>`, `opxy://proposal/<id>`.

## Video previews

The server asks about them and specifies them; it never renders one. After the motion spec, `preview_brief` returns the questions for the person (want a preview? silent or with sound? what should it show?). With their answers it returns the storyboard, timing from `motion.md`, size, output path and labelling, and the agent (Claude, Codex or a local model) builds the video with its own tools.

Engine audio in a preview is a **simulation**: the machine's engine code compiled and run on a computer with a stand-in envelope, not a recording from an OP-XY. The brief has the agent write that into the video's metadata and notes, and into any caption, card or audit that links it.

## How a design pass runs

Every generative pass (the subject candidates, the rest-frame variants, any revision after a review) is exactly five variants. I picked five because two or three candidates kept collapsing into "the first idea plus two strawmen", and five is still few enough to judge side by side at 1:1.

1. `design_pass_start(machine_id, kind)` assigns five directions before anything is drawn. For subjects that's five pattern × drawing-language pairs drawn from the patterns that fit the machine's category (`opxy/categories.md`), with one slot held for a stretch outside the column. For frames it's a Latin square over composition, camera and emphasis, so every pair of variants differs on all three.
2. It returns five designer briefs. In Claude Code and Codex they run as five parallel `opxy-designer` subagents, each writing only into its own `v<N>/` folder. With `run: true` the server runs them on the configured endpoint.
3. `design_pass_submit` checks the five are really different: subjects must differ in at least two of pattern, drawing language and wording (word overlap under 0.6); frames must each lint clean and differ pairwise on at least 4% of the body at 1:1, measured the same way `perceptibility.py` measures change. A pass with near-duplicates goes back as `needs_revision`, never down to four.
4. The person picks. `design_pass_select` records who picked which variant and why. The server never picks.

The numbers live in `opxy/catalog.json` → `iterations`, and the training gate refuses any proposal that changes `perPass` from five.

## Layout

```
mcp/
├── server.py            stdio entry point (--check for a self-test)
├── setup.py             client configs and generated agents
├── train.py             training mode from a terminal, approval included
├── opxy_mcp/
│   ├── rpc.py           JSON-RPC over stdio, MCP lifecycle, argument checks
│   ├── tools.py         the tool registry and profiles
│   ├── prompts.py       prompts and resources
│   ├── knowledge.py     docs, sections, search, patterns, categories, library
│   ├── screens.py       scaffolding, status, checks, render, audit_run
│   ├── passes.py        five-variant design passes and the uniqueness checks
│   ├── training.py      proposals, ops, the gate, approval
│   ├── agents.py        roles, briefs, the OpenAI-compatible runner
│   ├── runner.py        calls opxy/tools/*.py main() in-process with --json
│   └── paths.py         repo paths and path confinement
└── tests/               python3 -m unittest discover mcp/tests
```

The server never reimplements a check. `runner.py` calls each tool's own `main()` with `--json`, so a rule fixed in `lint_frame.py` is fixed for every client at once, and the CLI output stays exactly what it was.

## Safety

- Paths are confined to the repo (and `OPXY_WORKSPACE`). Anything else is refused.
- Auditing a library entry writes its outputs under `screens/<name>/audit/`, never over the published files.
- Training ops can only touch the guidelines (docs, tokens, catalog, skills, agent roles), never code.
- Nothing in training mode lands without a person's approval, and the generated subagents never get the approve tool.
- stdout carries only protocol messages; tools' own output is captured, and logs go to stderr.
