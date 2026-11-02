# Toro (stacked blocks)

![contact sheet](contact.png)

| | |
| --- | --- |
| Machine | `toro` · synth · [labyrinth](https://github.com/thoughtgrain/labyrinth) (OP-XY port of the OP-1 plugin) |
| Author | Brian Hinton (thoughtgrain) · MIT |
| Pattern | P10 Voice field (from `opxy/patterns.md`) |
| Audit | **meets, with notes** · 2026-10-31 · tokens `source.ref` pull/260 · [audit.md](audit.md) |
| Device | **device pending** |
| Source | `screens/toro/gen_blocks.py` (frames, fragment, prototype); `screens/toro/blocks/` |
| Video | [toro-blocks.mp4](toro-blocks.mp4), every control swept with toro's own engine as the soundtrack (`screens/toro/blocks_av.py`). Audio: **simulated**, toro's engine code run on a computer with a stand-in envelope, not a recording from an OP-XY; [toro-drum.mp4](toro-drum.mp4), fold rolling the field into a drum (`screens/toro/curl_av.py`) |

## The screen

An isometric field of seventy grey slab blocks, the lowest and a fixed scatter drawn as hollow wireframes, whose heights are a small model of toro's voice: two oscillators at the spread ratio, a folder, a filter's fine detail, a soft clip, noise and per-key drift. Turning a knob reshapes the field the way it reshapes the sound, and every note rolls the field forward and rings a ripple out from where the key lands. Fold goes furthest: it bends the whole field round a drum, nearly closed at 100, and notes push blocks straight out of the drum's surface.

## Controls

| control | score | channel | what the player sees |
| --- | --- | --- | --- |
| spread | 4 | shape (heights) | a second wave beats against the first |
| fold | 5 | shape + position | ridges fold into terraces while the field rolls up into a drum; notes push blocks out of it |
| cutoff | 5 | shape | broad waves at 0, fine ripple on top at 100 |
| res | 3 | shade + position | one row of tops lights up, front to back |
| shape | 3 | shape | ridges go from a sharp edge to symmetric |
| noise | 2 | shape | jitter in every column |
| drive | 3 | shape | the tallest columns clip to a plateau |
| aphx | 2 | shape | each column drifts its own amount, per key |

## What makes it work

- **The model is the drawing.** Heights come from the same signal path the sound does, so the mapping explains itself and no control needs a legend.
- **Slabs, not pillars.** Each block is three nodes (top, left, right) whose faces are a 12 px slab that only ever translates. An earlier version hung 64 px pillars to the floor so heights read as solid columns, but pillars can't follow a curve: any wrap filled in as a mound. Slabs let the field leave the floor entirely. The two skirt nodes that masked the pillars stay in the budget, hidden.
- **Hollow where the wave is quiet.** Cubes in the lowest 35% of the voice's range, plus a fixed scatter of about a quarter of the rest, swap to two wire palette entries (black fill, grey edge), so the field's troughs read as empty space and shift as the sound reshapes it, while the scatter keeps hollow cubes all through the field, peaks included. The test uses the voice's own height, before notes and the drum's flattening, and a struck or lit cube stays solid. Black fills keep it a hidden-line wireframe: hollow cubes still hide what's behind them.
- **Rolling with translation alone.** The device can't tilt a node, so the drum is built by sliding each upright block to its place on the circle and pushing it out along the radius by its height. Rows are drawn back to front, so the drum's back is drawn first. The voice's relief sinks into the surface as it wraps (an un-flattened drum reads as a heap), leaving notes to push blocks out.
- **Whole-pixel heights.** Snapping heights keeps edges crisp and means a column only redraws when it actually moves.

## Notes

- Over the redraw guideline by request; see the audit. The fold roll moves every block while fold is turning, like any control turn.
- Device pending.
