# Toro, stacked blocks

The direction Brian picked from round 3 (`concepts/s4-iso`), taken through the protocol. `gen_blocks.py` writes everything here: `board.png` (every frame at 1:1), `frames/` (SVG), `panel.svg.fragment`, `budget.json`, `model.json`, `prototype.html` and `toro-blocks.mp4`.

## The idea

An isometric field of seventy grey slab blocks whose heights are a small model of toro's voice. I didn't want the blocks to be decoration with knobs bolted on, so each control changes the field the way it changes the sound:

| Control | Score | What the field does | Why |
| --- | --- | --- | --- |
| spread | 4 | a second wave runs across the field at the oscillator ratio, beating against the first into a moiré of ridges | spread is osc 2's ratio; two waves at a ratio beat |
| fold | 5 | heights fold back on themselves into terraces, and the whole field rolls up into a drum (flat at 0, ~340° at 100); the voice's relief sinks into the drum and notes push blocks out of it | the wavefolder folds the signal back on itself; the field folds back on itself |
| cutoff | 5 | 0: only the two broad waves; 100: a fine ripple of harmonics on top | the filter decides how much fine detail gets through |
| res | 3 | one row of tops lights up, moving front to back | a resonant peak is one bright band |
| shape | 3 | the main wave's ridges go from a sharp leading edge to symmetric | saw → triangle |
| noise | 2 | jitter in every column | noise |
| drive | 3 | the tallest columns clip flat to a plateau | soft clip flattens peaks |
| aphx | 2 | every column drifts its own amount, different for every key | APHX is per-key drift |
| note | — | the whole field rolls forward a step (the waves travel); a six-column patch where the key lands jumps up 22 px and flashes white; a ripple rings out from it across the field and fades in ~0.6 s | the sound moving, located by the key |

All eight and the note pass `opxy/tools/perceptibility.py`. Every frame and the fragment pass `lint_frame.py` with no errors; `definition.json` passes `lint_definition.py`.

## How it's built for the device

Every block is three nodes: the top, the left face and the right face. The faces are a 12 px slab (`PILLAR`) that moves with the top, so a block changes height, or position, by translation alone. Nothing is ever reshaped, so there are no mutable outlines (`paths: 0`).

I started with 64 px pillars running to the floor, which made heights read as solid columns. They broke the fold roll: a node can't tilt, so pillars hanging off a curved field filled the drum in as a mound. Slabs leave the floor freely. The two skirt nodes that masked the pillars' overhang are still in the budget but always hidden.

The roll (`roll_amount`, `rolled_top`): fold bends the field into an arc of up to 1.9π with its middle row on top, its radius shrinking as the arc grows, and the ends resting on the floor. Each block slides to its point on the circle and out along the radius by its height. As it wraps, the rows part by up to half a row so the staves read, the relief shrinks by 92% so the drum doesn't read as a heap, and tops on the underside go dark. Note lifts and ripples are added after the shrink, so notes push blocks out of the drum at full size. Draw order is fixed back to front, which keeps the drum's back behind its front; the lower-front staves are drawn last but only overlap slab sides.

Budget: 220 nodes (8 header steps, 210 block faces, 2 hidden skirts), 0 paths, 16 texts, 8 palette entries, no static art. `stateBytes` 136: the page header's 20, eased control values, the note serial and time, and one eased height byte per column.

Redraw: Brian asked for more movement, and movement costs nodes. With the roll and the ripple a note changes about 72 nodes per frame averaged over the second after it (135 in the first half second, peaking near 190), against ux.md's ~20. Heights snap to whole pixels, so a column only redraws when it really moves. Idle moves none. This is the first thing to check on hardware; the lighter fallbacks, in order, are dropping the roll (`PHASE_STEP = 0`), then narrowing the ripple. A control turn moves every column while it eases (~0.15 s), which is a turn, not a held note, so it sits outside the per-note budget, but it's the frame to watch on hardware.

## Motion

- **Idle** is still.
- **Controls** ease exponentially and settle in about 0.15 s. Reduced motion jumps straight to the end state.
- **A note** rolls the field's waves forward 0.11 of a cycle (easing over ~0.22 s), lifts its patch, flashes the tops white for 120 ms, and sends a ring outward at 14 columns a second that fades over ~0.55 s. Reduced motion jumps the roll and skips the lift and ripple, keeping the flash.
- **The key** chooses where the patch lands (eight spots across the field), so a phrase walks across it.

## Handoff to `display.cpp`

`gen_blocks.py::heights()` and `pose()` are the spec; the prototype is the same maths in JavaScript.

- **Nodes:** `0..7` are the header bar. Each column is three nodes from `8`: left, right, top, in back-to-front order (`(i + j, i)` ascending). The two skirts are `218..219`.
- **Each frame:** for each column, compute the height, place all three nodes at `(base_x, base_y - h)`, and set the top's shade: low, mid or high by height, lit on the res row, white during the note flash.
- **Fixed nodes:** the side faces never change shade, and the skirts never move.
- **Pending device checks:** the cost of a full-field ease on a control turn, and whether the 0.3 px same-colour strokes leave hairline seams between faces on the panel.

## Sound

`toro-blocks.mp4` has a soundtrack from toro's own engine (`labyrinth/opxy/machines/toro/engine.cpp`). `blocks_av.py` holds one score: a D minor pentatonic riff, a note every 300 ms, with each control swept up and back while it plays. It draws the frames from that score with `gen_blocks` and renders the audio from the same score through `audio/render.cpp`, so every change on screen is a change you hear.

The order is drive, spread, cutoff up then down, fold, res, shape, noise, then aphx. Each of the eight keys plays its own pitch and lands its patch on its own spot on the field.

toro has no amplitude envelope of its own (the OP-XY's comes after), so the harness applies a plain one: 6 ms attack, full sustain, 280 ms release.
