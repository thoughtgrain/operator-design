# Toro, one-bit ink: the vector build

This folder is `gen_ink.py`'s output: the owner's bull rebuilt for the open-xy display ABI from the two photos of the device (`opxy/reference/toro-ink-rest.jpg`, `toro-ink-smoke.jpg`). `board.png` is every frame at 1:1; `frames/` has them as SVG; `panel.svg.fragment` is the artwork; `budget.json` is what `definition.json` will declare; `prototype.html` runs the same posing in a browser.

## v2: why the first build looked wrong, and what changed

The first build had two problems, and both showed on the device.

- **The trace.** I box-averaged the photo down to 480 × 220. A 2 px line photographed at 2.5 camera px per display px straddles sample boundaries, so averaging smeared every line into a dotted grey one. `ink_art.py` now point-samples the photo at the centre of each display pixel, searching scale and phase for the crispest result. The lines come back as clean 2 px strokes.
- **The head.** I redrew it by hand as smooth vector shapes with a 2 px vector stroke. That's a different drawing. Now nothing is redrawn: every node is cut from the owner's pixels.

How the drawing is rebuilt (`ink_art.py`):

1. **Solid** is whatever bright survives a 2 × 2 opening: lines, eye whites, nostrils, the dot grids, the glyph bars.
2. **Cells** are the regions between the lines.
3. Each cell is classified from the photo's own brightness: a **flat** cell is the panel's fine 1 px checker, which reads as a flat dark grey, so I draw `#4B4B4B`; **25 %** and **50 %** cells get clean Bayer dither; **dark** cells keep their isolated dots (swatches, stars, grain).

How the head moves without leaving the drawing: each of its fills and lines is a node whose outline is the exact staircase of its pixels, at whole-pixel coordinates. Moving a node by a whole pixel keeps it pixel-exact, so the head only ever moves by whole pixels: a note jolts it side to side, fold drops it. At the default settings the screen is the photo, pixel for pixel, with two exceptions: the forehead cap (25 % dither) and the left horn (50 % dither) are flat greys of the same brightness, because dither can't be a node and those two cells move with the head.

## Budget

235 nodes (122 head, 37 steam, 4 tuft, plus glyph bars, sparkles, grain, scanlines and the 8 header steps), 3 mutable outlines of ≤ 64 points, 14 palette entries, 16 texts, and 1476 static rects.

The cost to watch on hardware is the jolt: a note moves all 122 head nodes, but only on the frames where the whole-pixel offset changes (about eight per note), so the average over a note is well above ~20 changed nodes per frame for half a second and zero after. If the device stutters, the first fix is dropping the jolt to ±2 px.

## Control map

| Control | Score | What changes | Pixel-exact? |
| --- | --- | --- | --- |
| spread | 4 | a dim echo of each horn slides out up to 14 px: the oscillators detuning into a double image | yes |
| fold | 5 | the head drops up to 6 px; two heat squiggles appear and tighten | yes (squiggles are vector) |
| cutoff | 5 | cap, horn, ears and eye patches go dark toward 0 and light up toward 100; the eye whites narrow to slits or open wide | fills yes; eyes scale |
| res | 3 | the burst grows from a spark to 27 px with 8 rays; nostrils flare; the muzzle lights | burst is vector |
| shape | 3 | both bar glyphs morph from two spikes (a saw's edges) to one triangle | bars scale |
| noise | 2 | sparkles and grain | vector |
| drive | 3 | the steam clouds from the smoke photo, nearest the nostrils first; nothing at 0 | cloud bodies vector, curls exact |
| aphx | 2 | torn scanlines slip across the swatches; the right horn's echo nudges per key | vector |
| note | — | head jolts ±3 px at 2.2 Hz, settling over 0.5 s; eyes flash wide; tuft flicks; a drive-dependent puff more steam | yes (head) |

All eight and the note pass `opxy/tools/perceptibility.py`; every frame and the fragment pass `lint_frame.py` with no errors.

## Pending

- Device checks: the static rect count, the jolt's cost, and whether the node outlines (thin same-colour strokes on pixel staircases) render as crisply as the static rects.
- `display.cpp`: `gen_ink.py::pose()` is the spec. The old TAURUS atlas files in `screens/toro/` are superseded and get archived once this direction is confirmed.
