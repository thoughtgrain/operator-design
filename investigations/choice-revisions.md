# Choice revisions: a localhost bench for the five variants

Status: phases 1 and 2 built, plus MIDI knobs from phase 3 (see [What got built](#what-got-built)). Branch `choice-revisions`.

I'm looking at how to give the person a real place to look at a pass's five variants and pick one, the way [impeccable](https://github.com/pbakaus/impeccable)'s live mode gives a web designer a place to cycle through variants in the browser. I'm borrowing workflow ideas, not code or assets: impeccable is a web tool built around HTML, CSS, fonts and colour, and almost none of that survives contact with a 480 × 220 grey screen. What does survive is the shape of the loop (browser ↔ local server ↔ agent), the discipline around variants, and a few ways of generating ideas that aren't the obvious ones.

Everything below stays inside what this repo already decided: 480 × 220 at 1:1, grey by default, red never, one subject under the stock header, Shift replaces the header, no text in the drawing, exactly five variants per pass, the pick is the person's, device checks stay pending.

## Where we are today

The pass machinery already does the hard part. `design_pass_start` deals five directions (angle × drawing language for subjects, a Latin-square walk over composition × camera × emphasis for frames), `design_pass_submit` lints each variant and checks pairwise uniqueness (≥ 4 % body-pixel difference), and `design_pass_select` records the pick and the reason in `pass.json`.

The weak spot is the moment of choosing:

- **The person sees the variants wherever the chat client puts them.** `render_frame` hands back a PNG, and the client scales it however it likes. The protocol says judge at 1:1, and the one moment it matters most (the pick) is the one I can't control.
- **There's no side by side.** `craft.md` asks for the rest frame beside a reference at 1:1. Today that's five separate images in a scrolling chat.
- **Rendering depends on `rsvg-convert`.** Without it, `render_frame` errors and the uniqueness check in `passes.py` quietly records `pixel check skipped`. This container doesn't have it, which is exactly how a pass closes without its pixel check.
- **A pick arrives as chat text.** The agent then calls `design_pass_select` with `chosen_by` and `reason` taken from the conversation. It works, but the person never touches the record directly.

## What impeccable does that's worth learning from

| impeccable | What it's doing | What it becomes here |
| --- | --- | --- |
| Live mode: browser overlay, localhost server, agent long-poll | Puts the choice where the thing is rendered, and lets the agent keep working while the person looks | A **bench** page on `127.0.0.1` showing a pass's five variants at 1:1, and a pick goes back to the agent as an event |
| SSE (server → browser) + fetch POST (browser → server), zero dependencies | Avoids a websocket library so the scripts run without installs | Same split, on Python's stdlib `http.server`, so the repo's "no packages" promise holds |
| Agent long-poll (`GET /poll` blocks until a browser event) | Works in every harness, since every harness can run a command | An MCP tool `bench_poll` that blocks until the person picks, rejects or asks for something |
| Session journal (`.impeccable/live/sessions/`) | Survives a helper restart; nothing is lost if the agent disconnects | `pass.json` is already canonical; the bench appends events to `passes/<nn>/events.jsonl` beside it |
| Identity lock (one sentence of what's actually on screen, before any variant) | Stops variants drifting off-brand | A **stock-look lock** for frames and revision passes: the chosen subject, its drawing language, its brightest element, its line weights, in one sentence every variant has to hold |
| Default vs departure mode | Wrong-departure is unrecoverable, so departure needs an explicit ask | Revision passes keep the subject and language by default; changing either needs the person to say so ("start over", "different subject") |
| Squint test (label each variant with a concrete family; shared labels mean rework) | A human-readable uniqueness check on top of the rules | A **family label** per variant alongside the word-overlap and pixel checks we already run |
| "The rut" (name the predictable reading, spend at most one candidate on it) | Forces the other candidates out of the obvious | Before a subject pass, name the rut for this machine (the literal object in its name, a waveform, a row of meters) and allow at most one of five on it |
| Steering verbs (`bolder`, `quieter`, `distill`, `polish`…) mapped to axes | Gives the person words for a direction | OP-XY verbs mapped to things this screen can actually do (table below) |
| Params: 0–4 coarse knobs per variant, no regeneration | Lets the person tune without asking for a new pass | The machine's **own controls** as the knobs: scrub each control's drawn 0 / 50 / 100 frames on the variant |
| Detector overlay (findings drawn over the page) | Shows the problem where it is, not in a list | Lint, perceptibility and craft findings drawn over the frame at their coordinates |
| Rust engine: one static binary, no Node at runtime | Speed, one artefact per platform, byte-for-byte oracle tests | A Rust rasteriser for frames (below), and only that to start with |

What I'm leaving behind on purpose: HTML/CSS variant wrappers, HMR, source hot-swapping, typography and colour axes, the web slop rules, anything about fonts. None of it means anything on the OP-XY, and copying it would drag the screens towards looking like web UI, which is the failure `AGENTS.md` warns about.

## The bench

One page, three views, all at 1:1 by default.

### Board

The five variants of the open pass, each drawn at 480 × 220 inside a plain black frame with the stock header rendered from `definition.json` (labels and default values in the header's own positions). Under each one: the variant id, its direction (angle and drawing language, or composition / camera / emphasis), its family label, and its submit results (lint errors/warnings, pairwise uniqueness). The layout stacks vertically below about 1000 px of viewport so nothing ever scales down. If the window can't fit 480 px plus gutters, the bench says so instead of shrinking the frame.

### Cycle

One variant at a time in the same spot, flipped with `1`–`5` or the arrow keys. Flipping in place is how differences show up that side by side hides: whether the subject moved, whether the brightest element jumped, whether the ground went greyer. This is the closest thing to impeccable's variant cycler.

### Controls

For a frames or revision pass where the variant has its full set, a slider per control steps through the drawn `c<N>-000 / 050 / 100` frames, plus `rest` and `playing`. Only drawn frames, no in-betweens invented by the browser: if a pass ships a generator (`sketch.py`, like flock's), a later phase could ask it for arbitrary values, but that's a separate decision. A Shift toggle swaps the header's four slots for the Shift controls, as `shift_policy` says; it never adds a row unless the harness config sets `OPXY_SHIFT_HEADER=stack`.

### Overlays (any view, off by default)

- **Lint findings** pinned to where they are: text below the header, a clipped path, a fill that isn't `none` or `#RRGGBB`. Severity is a shape and a word, not a colour.
- **Value map**: the one brightest element outlined, and a count if there's more than one.
- **Body black**: the percentage of the body that's black, against the 40 % floor in `craft.md`.
- **Arm's length**: the frame rasterised at 480 × 220 and then shown downsampled and blurred, so the person can see what still reads from a distance. This is a squint view, not a measurement; `perceptibility.py` stays the measurement.
- **Device raster**: the frame drawn to a 480 × 220 canvas and scaled nearest-neighbour. A high-DPI laptop draws a 480 px SVG at 2× and makes it look crisper than the OP-XY ever will; this view takes that flattery away.

The bench itself labels every view "preview, not device". Nothing it shows ticks a device check.

### Picking

Pick and Reject need a reason (a text field that can't be empty) and a name for `chosen_by`. The browser sends the event; the agent receives it through `bench_poll`, reads it back to the person in one line, and calls `design_pass_select` or `design_pass_reject`. I'd rather keep the agent in that loop than let the server write `pass.json` itself, because then every pick goes through one code path and the gates that come with it. That's an open question below.

What the bench never does: approve a training proposal (that stays `python3 mcp/train.py approve`), switch colour on, close a pass with fewer than five variants, or show a colour picker.

### Accessibility of the bench

The bench is a tool people use for a long time, so it gets the same care as a screen:

- Keyboard first: `1`–`5` select, `←/→` cycle, `B` / `C` / `K` switch views, `Enter` opens the pick form with focus in the reason field. Every control is a real `button` or `input` with a visible focus ring.
- Each frame is an `<img>` with alt text built from its direction and subject sentence. The person's picking may be visual, but the record of what each variant was shouldn't need eyes.
- `prefers-reduced-motion` turns cycling into an instant swap with no crossfade.
- Findings use shape and text, never colour alone; the page itself is greys, which suits the material anyway.

## Architecture

Three parties, the same as impeccable's live mode, with our MCP server as the agent's side:

```
 browser (bench page)            local server                     agent
 ────────────────────            ────────────                     ─────
 GET /                    ──►    serves page + frames
 EventSource /events      ◄──    pass changed, variant submitted
 POST /events  (pick…)    ──►    queue + events.jsonl     ──►     bench_poll returns the event
                                                          ◄──     bench_reply (ack, "selected v3")
                                                                  design_pass_select(...)
```

- **Bind and auth.** `127.0.0.1` only, a random token in the URL and checked on every request, `Origin` checked on POST. Requests for files resolve under `screens/<id>/` and nowhere else.
- **SVGs are images.** Frames load through `<img src>`, never inlined, so anything scripted inside an SVG can't run. A strict CSP on the page (`default-src 'self'`).
- **Port.** First free from 8470. In a cloud session the agent calls `report_preview_port` so the app can show the page; locally it prints the URL.
- **Live updates.** When `design_pass_submit` writes a variant, the server pushes an event and the board redraws. A designer agent finishing v3 shows up while v4 is still drawing.
- **Restart-safe.** `events.jsonl` replays anything the agent hasn't acknowledged, the way impeccable's journal does.

## Where Rust earns a place

The case for Rust here is narrower than impeccable's, and stronger in one spot.

**The renderer.** A small crate on [resvg](https://github.com/linebender/resvg) (pure Rust, no system libraries, deterministic output across platforms) would:

- remove the `rsvg-convert` dependency that today stops `render_frame`, `perceptibility.py` and the pass pixel check from running at all on a machine without librsvg;
- give the bench, the uniqueness check and `perceptibility.py` the same pixels, byte for byte, on macOS, Linux and Windows;
- make golden-image tests possible: rasterise toro's and theseus's frames, commit the PNGs, and fail the suite if the rasteriser drifts. That's impeccable's oracle-test idea, pointed at our precedents.

Python would call it the way it calls `rsvg-convert` now, through `runner.render_png`, with a fallback order of `opxy-raster` → `rsvg-convert` → a clear error. Nothing else in the tools changes.

**Not yet: the server and the linters.** Moving the bench server or the frame linter to Rust buys speed nobody's asked for and costs two things this repo cares about: a second implementation of rules that the test suite pins in Python, and a binary to build and ship for every platform before anyone can run the protocol. The server is a few hundred lines of stdlib Python. If the bench later wants to run without the MCP server (a `opxy-bench` CLI on its own), that's when a single Rust binary for server plus rasteriser becomes worth it.

Toolchain note: this container has neither `cargo` nor `rsvg-convert`, which is the point. A contributor without Rust would still be fine, because the Python fallback chain stays.

## Ideas within the constraints

Workflow ideas from impeccable, rewritten for this screen. Anything that changes the guidelines (`opxy/`) goes through training mode as a proposal, not straight into the docs.

### The rut, per machine

Before a subject pass, write down the predictable readings of this machine: the object its name is (a "bell" machine drawing a bell), a waveform, a row of meters, the category's most-used pattern drawn as-is. At most one of the five variants spends its direction on the rut. `ideaAngles` already includes "the object in the machine's name, drawn literally and well"; the rut rule says that angle can't be dealt twice and nothing else can sneak back to it.

### Stock-look lock and family labels

For frames and revision passes, the pass record gets one sentence: the subject, its drawing language, the brightest element and where it sits, the line weights. Every variant has to hold it; a variant that changes the subject has crossed into departure without being asked. Each variant also gets a family label of a few concrete words ("survey plate, low horizon", "cutaway, bright core"). If two labels could swap, one variant is reworked. This sits beside the word-overlap and 4 % pixel checks, not instead of them.

### Steering verbs for revision passes

A revision pass already needs a `focus`. These would give that focus a vocabulary the person can use, each mapped to something measurable on this screen:

| Verb | What it varies across the five | Bounded by |
| --- | --- | --- |
| `quieter` | fewer nodes, more black body, dimmer secondary marks, smaller motion | 40 % black floor up is free; perceptibility floors still hold |
| `bolder` | more travel on the highest-scored controls, a stronger channel, a larger subject | perceptibility pass, ≤ ~20 changed nodes average, flash limit |
| `distill` | removes a different class of panel-ness each (strips, badges, legends, duplicate marks) | "picture, not panel" in `craft.md` |
| `deepen` | rebuilds the subject as a modelled, projected 3D scene from a different camera each | "think in 3D" in `craft.md`, node budget |
| `steady` | calmer motion: smaller amplitude, fewer moving parts, one part answering the note | 0.15–0.2 s eases, nothing moves at rest |

No `colorize`. With `OPXY_COLOUR=allow`, colour is still a config fact, not a verb.

### The machine's controls as the knobs

impeccable lets a variant expose a few coarse knobs. Here the knobs already exist: they're the machine's controls, and the definition says what they are. Scrubbing a variant through its own control frames at 1:1 is a better test of a frames pass than looking at five rest frames, because the pass is really choosing how the screen moves.

## Proposed file layout

The plan as first written. What actually landed is in [What got built](#what-got-built); `header.py` was dropped, since every frame already carries its own stock header.

```
mcp/opxy_mcp/bench/
├── __init__.py
├── server.py          stdlib ThreadingHTTPServer: page, frames, SSE /events, POST /events
├── events.py          queue, events.jsonl journal, replay of unacknowledged events
├── header.py          stock header from definition.json (labels, defaults, Shift slots)
└── static/
    ├── index.html     board / cycle / controls views
    ├── bench.js       no framework, no build step
    └── bench.css      greys only
mcp/opxy_mcp/tools.py  + bench_open, bench_poll, bench_reply, bench_close
opxy/tools/bench.py    the same server from a terminal, for people without an MCP client
mcp/tests/test_bench.py
crates/opxy-raster/    resvg-based rasteriser: `opxy-raster in.svg out.png --scale 1`
Cargo.toml             workspace with the one crate
mcp/opxy_mcp/runner.py render_png: opxy-raster → rsvg-convert → error
mcp/tests/golden/      toro + theseus rasters pinning the renderer
```

Docs that would change: `mcp/README.md` (the bench and its tools), the root `README.md` (Rust is optional), and a line in `opxy/protocol.md` phases 3 and 5 pointing at the bench for the pick. That protocol line is an edit to `opxy/`, so it waits for a direct go-ahead.

## Phases

1. **Bench, board and cycle views, Python only.** Uses `rsvg-convert` when it's there and the browser's own SVG rendering otherwise (labelled as such). Picks go to the agent through `bench_poll`.
2. **`opxy-raster` in Rust.** Swap it into `runner.render_png`, add the golden tests, make the device-raster and arm's-length overlays use it.
3. **Controls view and overlays.** Scrubbing drawn frames, Shift header, lint and value-map overlays.
4. **Training proposals** for the rut, the stock-look lock, family labels and the steering verbs, each through draft → audit → review → gate → the person's approval.

## Decisions

The person left these to me. What I chose and why:

1. **Rust scope: the renderer only.** `crates/opxy-raster` is a small resvg CLI that takes the same flags as `rsvg-convert`, so `runner.py`, `perceptibility.py` and `contact_sheet.py` use it without knowing which one they got (`opxy/tools/raster.py` finds it). The bench server stays stdlib Python: it's a few hundred lines, it lives inside the MCP process, and a second implementation of anything the tests pin would only drift.
2. **The bench records the pick itself.** I'd first said the agent should record it. What changed my mind: the server calls the very same `design_pass_select` / `design_pass_reject`, so every gate still applies, the name and reason come straight from the person instead of being retyped from chat, and it works from a terminal with no agent polling at all. The agent still hears about it through `bench_poll`, and `events.jsonl` keeps the trail beside the pass.
3. **Knobs: drawn keyframes by default, live frames when the machine opts in.** Without a generator the knob snaps to the nearest drawn 0 / 50 / 100 frame, and the dial shows a dashed tick where the drawn frame is. Blending two frames would show a grey ghost no frame contains. With `screens/<id>/bench.py` (one `frame(values, notes)` function) every position is drawn by the machine's own code, eased over the motion tokens' 0.15–0.2 s, with the note envelope rising and falling. beacon and toro have one.
4. **Guideline ideas wait for training mode.** The rut, the stock-look lock and family labels aren't filed yet. The steering verbs exist only as an optional tag on a note the person sends the agent from the bench; they don't change any doc.

## What got built

| Piece | Where | Notes |
| --- | --- | --- |
| Renderer | `crates/opxy-raster/`, `Cargo.toml`, `opxy/tools/raster.py` | resvg 0.45, sans fallback for the licensed device face; `cargo test` covers its flags |
| Golden images | `mcp/tests/golden/` | toro-blocks and theseus-tower rest frames; the test compares the body (not the header, whose fallback font differs by machine) with perceptibility's own measure |
| Bench server | `mcp/opxy_mcp/bench/` | `server.py` (routes, token, CSP), `model.py` (machines, passes, frame sets, both frame-naming schemes), `events.py` (SSE, agent queue, journal), `generator.py` + `worker.py` (live frames in a separate process, restarted on code changes) |
| Bench page | `mcp/opxy_mcp/bench/static/` | board, cycle, play; vector / device / arm's-length lenses; value map; body-black meter; Web MIDI with auto-bind, learn and relative encoders |
| Entry points | MCP `bench_open`, `bench_poll`, `bench_close`; `opxy/tools/bench.py` | the bench tools stay out of the compact profile (16-tool cap for small local models) |
| Tests | `mcp/tests/test_server.py` → `TestBench`, `TestRenderer` | token and confinement, a pick refused before the pass is ready and accepted after, notes, keyframe naming, live generator and its error path |

With `opxy-raster` built, the six tests that used to skip for want of `rsvg-convert` now run, including both precedents. All 48 pass.

## Not built yet

- **Shift in Play.** A toggle that swaps the header to the Shift controls needs frames drawn with Shift held; no screen has those yet.
- **Lint findings drawn on the frame.** The board shows lint counts with the rules on hover; pinning each finding to its coordinates needs the linter to report positions.
- **Training proposals** for the rut, the stock-look lock and family labels.
- **A `bench.py` for the other machines.** Each generator has its own shape (`draw(c, …)`, `frame(v, playing)`, `frame_for(…)`), so each adapter is a few lines written against it.
