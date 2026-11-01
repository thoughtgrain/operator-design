# Toro, one-bit ink: the vector build

This folder is `gen_ink.py`'s output: the owner's bull (`opxy/reference/toro-ink-rest.jpg`) rebuilt for the open-xy display ABI. `board.png` is every frame at 1:1; `frames/` has them as SVG; `panel.svg.fragment` is the artwork draft; `budget.json` is what `definition.json` will declare.

## Why it's two layers

On the device only nodes change at runtime, and a node is one path or circle of at most 64 points. A dithered area is hundreds of one-pixel marks, so dither can only live in things that never move. I split the screen on that line:

- **Static artwork.** The body, legs, hump, tail, both bar glyphs, the swatches and the ground dots come straight from the trace of the photo, as run-length `<rect>`s in white: 1,847 of them at 1 px. `panel-cell2.svg.fragment` is the same art at 2 × 2 px dither cells (430 rects) in case the device's SVG parser balks at the count. That's the first thing to test on hardware.
- **Nodes.** Everything that moves or changes: the head group (face, brow, ears, horns, eye patches, eye whites, pupils, muzzle, nostrils), the tail tuft, 28 steam puffs, 8 sparkles, 12 grain dots and 4 torn scanlines. These are flat palette greys with a 2 px white outline, matched to the dither density they replace (25 % → `#4B4B4B`, 50 % → `#7D7D7D`, 75 % → `#AFAFAF`). This is the compromise: the horns, ears and muzzle lose their dither texture so they can move. If that's unacceptable, the alternative is a head that doesn't wobble.
- **Mutable outlines (3).** The burst beside the muzzle (res) and two heat squiggles (fold).

Budget: 79 nodes, 3 paths of ≤ 64 points, 16 texts, 9 palette entries. The head group is 16 nodes, so a note's wobble costs 17 node updates a frame (head plus tuft) for about half a second, under the ~20 average.

## Control map

| Control | Score | What changes | Gate (0→100 % of body, need) |
| --- | --- | --- | --- |
| spread | 4 | horns scale out from their roots, 0.9× → 1.4× | 5.9 (1.6) |
| fold | 5 | the head lowers 10 px and tilts 4° to charge; two heat squiggles appear and tighten | 11.3 (2.5) |
| cutoff | 5 | 0: eye whites gone, horns and ears dark, ears flat · default: the photo · 100: eye whites fill the patch with a pupil, face lit two steps | 13.1 (2.5) |
| res | 3 | muzzle flushes white, nostrils flare and invert, burst grows from 4 to 16 px with 8 rays | 1.8 (1.2) |
| shape | 3 | horn tips turn up and out, 35° | 4.2 (1.2) |
| noise | 2 | sparkles (up to 8) and grain (up to 12) | 1.5 (0.8) |
| drive | 3 | steam, puff by puff, 14 a side | 6.3 (1.2) |
| aphx | 2 | torn scanlines slip across the swatches per key; the right horn turns on its own | 2.1 (0.8) |
| note | — | head wobbles 3.5° at 2.2 Hz, settling over 0.5 s; eyes flash wide; tuft flicks; one more puff | 6.4 (2.0) |

All eight and the note pass `opxy/tools/perceptibility.py`; every frame and the fragment pass `lint_frame.py` with no errors. The warnings it does raise are expected: the 1 px dither rects are under its legibility floor by design (the photos prove the panel shows them), and `#FFFFFF` isn't a stock header grey.

## What's pending

- Device checks: the static rect count, whether 1 px dither and 2 px outlines render as the photo shows, and the wobble's cost.
- `display.cpp`: the pose maths in `gen_ink.py::pose()` is the spec; `handoff.md` gets rewritten from it once this direction is confirmed.
- The old TAURUS atlas files in `screens/toro/` are superseded by this folder and will be archived at that point.
