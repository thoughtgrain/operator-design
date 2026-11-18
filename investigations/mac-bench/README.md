# Mac bench: a native app for the design journey

Status: UI direction under review. Nothing here is built, and nothing in `opxy/` has changed because of it.

I'm looking at a Mac-native app that sits beside the existing bench. It's a separate journey: the Python bench, the lint tools and the MCP server keep working as they do today for anyone who isn't on a Mac, and both paths write the same files under `screens/<machine-id>/` and pass the same lint and gates. That shared folder is the rule that keeps the two interchangeable.

## What I assessed

I read [rinste/turbo-mlx](https://github.com/rinste/turbo-mlx) at v1.11 (MIT). It's a SwiftUI app that drives a sandboxed engine process over JSON lines on stdin/stdout, which is the same shape as `mcp/opxy_mcp/bench/worker.py`. I'm borrowing its window layout and its process model. I'm not using diffusion output as frames, because a generated picture can't be linted, has no node budget and can't be handed to `display.cpp`.

## The journey I've drawn

1. **Concept.** An image model (SenseNova-U1.5 or Ming-Image) makes five pictures. The app shows them at 480 × 220 in grey with the stock header stamped on, and runs raster checks so I only approve something drawable. This approves a direction, not a frame.
2. **Frames.** The approved concept is traced (arithmetic), read once by a small vision model (what matters, what to drop), and drawn by a small code model as five variants. Checks run cheapest first: lint, then a pixel comparison, then the vision model only for borderline matches. A frame goes back to the model twice at most, then stops and asks.
3. **Play.** The picked frame at 1:1 with four encoders, lenses, hold-a-note and Shift. The local model draws keyframes, so the encoders snap between drawn positions; live easing still needs a generator script.

The header is never generated. The app stamps it from `opxy/templates/frame.svg` and the machine's `definition.json`, so the model only draws the body. A custom header gets designed once, then stored and stamped the same way.

## Files

`design/` holds the source of the mockup canvas: `canvas.json` is the index and each `.dc.html` is one screen (Concept, Frames, Play, and the Settings window). The machine, its controls and all the frame art in them are invented stand-ins drawn by code, and the check results are illustrative.

## The SwiftUI prototype

`prototype/` is the same three screens and the Settings window written in SwiftUI, with stub data and no models or engine behind it. I wrote it because an HTML mockup kept reading as a web app however I styled it: TurboMLX looks native because it's assembled from stock parts (a split view, a window toolbar, grouped forms, system sliders, switches and pop-up buttons), so the prototype uses those same parts and lets macOS draw them.

To run it on a Mac with Xcode 15 or later (macOS 14 or later):

```bash
cd investigations/mac-bench/prototype
```

```bash
swift run
```

Or open `Package.swift` in Xcode and press Run. Settings is under ⌘,.

It has not been compiled. I wrote it in a Linux container with no Swift toolchain and no Mac attached, so expect to fix a compile error or two on the first build. It's a look-and-feel check, not the start of the app: the real one would be an Xcode project with an engine process, the way TurboMLX is laid out.

## Still open

- Whether the pick needs all five variants side by side at 1:1, or flipping through the strip is enough.
- Which small vision model, which depends on what has Swift MLX support.
- Whether a 1.5B code model, tuned on this repo's passing frames and constrained to a compact frame format, holds a composition. That needs a spike on a Mac.
- The protocol change: Phase 3 would accept an approved concept as an alternative route to its gate. That goes through training mode, with my approval at the end.
- LTX clips are for early concept mood only, and silent. The motion preview stays a deterministic sweep of the drawn frames.
