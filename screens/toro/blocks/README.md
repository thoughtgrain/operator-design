# Toro, stacked blocks

The direction Brian picked from round 3 (`concepts/s4-iso`), taken through the protocol. `gen_blocks.py` writes everything here: `board.png` (every frame at 1:1), `frames/` (SVG), `panel.svg.fragment`, `budget.json`, `model.json`, `prototype.html` and `toro-blocks.mp4`.

## The idea

An isometric field of seventy grey columns whose heights are a small model of toro's voice. I didn't want the blocks to be decoration with knobs bolted on, so each control changes the field the way it changes the sound:

| Control | Score | What the field does | Why |
| --- | --- | --- | --- |
| spread | 4 | a second wave runs across the field at the oscillator ratio, beating against the first into a moiré of ridges | spread is osc 2's ratio; two waves at a ratio beat |
| fold | 5 | heights fold back on themselves, ridges split into terraces | the wavefolder does exactly this to the signal |
| cutoff | 5 | 0: only the two broad waves; 100: a fine ripple of harmonics on top | the filter decides how much fine detail gets through |
| res | 3 | one row of tops lights up, moving front to back | a resonant peak is one bright band |
| shape | 3 | the main wave's ridges go from a sharp leading edge to symmetric | saw → triangle |
| noise | 2 | jitter in every column | noise |
| drive | 3 | the tallest columns clip flat to a plateau | soft clip flattens peaks |
| aphx | 2 | every column drifts its own amount, different for every key | APHX is per-key drift |
| note | — | a six-column patch placed by the key jumps up 22 px, flashes white for 120 ms, settles in ~0.4 s | one visible event per note, located by the key |

All eight and the note pass `opxy/tools/perceptibility.py`. Every frame and the fragment pass `lint_frame.py` with no errors; `definition.json` passes `lint_definition.py`.

## How it's built for the device

Every column is three nodes: the top, the left face and the right face. The faces are fixed-length pillars (64 px) that move with the top, so a column changes height by translation alone. Nothing is ever reshaped, so there are no mutable outlines (`paths: 0`).

That works because of draw order. Columns are drawn back to front, so the part of each pillar that hangs below its column's base is always covered by the columns in front of it. The front row's overhang is covered by two black skirt nodes drawn last.

Budget: 220 nodes (8 header steps, 210 column faces, 2 skirts), 0 paths, 16 texts, 8 palette entries, no static art. `stateBytes` 136: the page header's 20, eased control values, the note serial and time, and one eased height byte per column.

Redraw: a note moves 18 nodes (six columns) for about 0.4 s, under the ~20 per frame guideline; idle moves none. A control turn moves every column while it eases (~0.15 s), which is a turn, not a held note, so it sits outside the per-note budget, but it's the frame to watch on hardware.

## Motion

- **Idle** is still.
- **Controls** ease exponentially and settle in about 0.15 s. Reduced motion jumps straight to the end state.
- **A note** lifts its patch on note-on, flashes the tops white for 120 ms, and decays with a 0.18 s time constant. Reduced motion skips the lift and keeps the flash.
- **The key** chooses where the patch lands (eight spots across the field), so a phrase walks across it.

## Handoff to `display.cpp`

`gen_blocks.py::heights()` and `pose()` are the spec; the prototype is the same maths in JavaScript.

- **Nodes:** `0..7` are the header bar. Each column is three nodes from `8`: left, right, top, in back-to-front order (`(i + j, i)` ascending). The two skirts are `218..219`.
- **Each frame:** for each column, compute the height, place all three nodes at `(base_x, base_y - h)`, and set the top's shade: low, mid or high by height, lit on the res row, white during the note flash.
- **Fixed nodes:** the side faces never change shade, and the skirts never move.
- **Pending device checks:** the cost of a full-field ease on a control turn, and whether the 0.3 px same-colour strokes leave hairline seams between faces on the panel.
