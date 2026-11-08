# lichen · refining v1 (cutaway: stone block under a lichen crust)

The owner picked v1 of `passes/02-subject/` and asked for it "cleaned up a bit and more solid shapes". This is a clean-up of the pick, not a generative pass (protocol.md, Iterations: a clean-up edits the pick and doesn't need five). Everything here comes from `build.py`, which uses the same colony model, seed and tick as the pass-02 sketch (tick 14: the start row cut open, 2 births, a hollowing centre), so `before-after.png` compares like with like. All frames judged at 1:1.

## What changed and why

- **Solid bodies instead of wire.** The stone and the crust are now flat faces lit from the upper left. Stone top `#4B4B4B`, the cut face and the end `#323232`, crust tops `#969696`, crust walls `#646464`. Tops are lighter than sides, and everything sits at least two steps under the bright element. Edges come from the value steps plus a 1 px black seam round every plate. The seam is what keeps packed areolae apart at 1:1, and it reads as the crack between areolae rather than as an outline. The block keeps a hairline `#646464` silhouette and a lit `#7D7D7D` arris along the cut, so it doesn't melt into the black.
- **Areolae, not tiles.** Each plate is a rounded, slightly uneven areola. Sides that meet a living neighbour stay straight and close (packed crust split by narrow cracks). Sides at the margin bulge into two rounded lobes each, the way a crustose edge does. Thickness is the cell's age in three steps (0.13 / 0.21 / 0.29 world units, so about 6 / 10 / 14 px). These are low, lumpy plates on a big slab, not stacked cubes, so the silhouette stays away from toro-blocks.
- **Tongues are crust lobes you can see.** Each one is a thin solid lobe (half a plate's thickness) that comes out from under a margin plate onto bare stone and widens to a notched, two-lobed tip. There's one per free margin cell, and a plate sends out at most two. At the default (grow 35) a tongue sticks out about 17 px past its plate; in v1 it was a hairline sliver.
- **Dead crust is hatched and stands up.** In v1 decay tilted a small flake off the back of a hatched remnant, and you couldn't see it at the default. Now the whole dried areola (86 % of the plate) peels up on a hinge along its front edge, so its face turns towards the viewer as it lifts. It's a black body with a 1.5 px `#7D7D7D` edge and `#646464` 45° hairlines 4 px apart. That's hatched because it's there but inactive, never a grey fill. Where it lay, the stone keeps a dark scar. At the default it stands at 27°, which already reads clearly.
- **Spores read as spores.** I removed the lone dashed stalk at top right. A spore is now a solid `#969696` grain with a black rim, hanging 0.36 units over the bare cell it'll land on, with its black shadow on the stone directly below. The height and the shadow make it a body in the air, not a stray dot. They're placed in a fixed order on bare stone inside the block, so seed adds grains and never moves them.
- **Cracks are splits in the stone.** The floating `//` dashes on the stone top are gone. At each half step along the cut row, the block is split for its whole height: a black wedge down the cut face, wide at the top, with a lit `#7D7D7D` lip on the broken edge. The split continues back across the top and narrows towards the back face. Where crust lies over a split, the crust splits too: a black cut across the plate's top and down its section. The cracks move with the mode, and the pentatonics have none.
- **A calm section.** Each row-2 plate shows on the cut face in two bands, a thin `#969696` cortex over a `#646464` medulla, at the plate's real thickness. Under them are short `#646464` rhizine hairlines 5–6 px apart going into the stone. In the stone are two faint `#4B4B4B` bedding lines that break at the cracks. Nothing else is on the face.
- **One bright element.** This tick's births are the only `#CDCDCD`: the top `#CDCDCD`, the wall `#969696`, and the section's cortex and medulla on the cut row. At rest the last growth stays lit (it's the last note played). It dims when the next growth arrives.
- **Clearances.** The drawing runs from y 45 (seed 8's highest grain) to y 176 in every frame, so nothing comes within 25 px of the header. The header shows lichen's titles and values (35 / 20 / 1 / maj at rest; 0·50·100, 0·3·8 and maj·lyd·pmin on the control frames). There's no text in the drawing.
- **Black share.** 56–57 % of the body is black in every frame (pixels under 12/255, y 21–219), so it's above the 40 % floor.

## Fills and contrast

Every fill is a solid body: the stone, crust plates and tongues, spores, and the born plate as the single bright mass. Black is used for seams, cracks, scars, shadows, and the bodies of dead flakes under their hatch. No state is shown as a grey fill. Living vs new is `#969696` → `#CDCDCD` plus the swell, and dead is black plus hatching, not a darker grey.

WCAG contrast where it matters (non-text 3:1):

| boundary | ratio | note |
| --- | --- | --- |
| crust top / black seam | 7.10 | carries every plate edge |
| born top / stone top | 5.49 | the bright element, against the ground |
| born top / crust top | 1.86 | not alone: the born plate also swells, and is three steps up |
| crust top / stone top | 2.95 | just under 3, so every plate and tongue has the black seam (7.10) round it |
| flake edge / black body | 5.10 | dead flakes; their hatch is 3.55 on black |
| crack lip / crack | 5.10 | the black split on the stone top alone is 2.41, so the lit lip carries it |
| spore / black rim | 7.10 | the grain on stone alone is 2.95, so it gets a rim |
| block silhouette / canvas | 3.55 | the stone top on black alone is 2.41 |
| arris / cut face | 3.11 | the lit edge along the section |
| cortex / medulla, medulla / cut face, rhizines / cut face | 2.00, 2.17, 2.17 | inner detail, hairline language, below 3:1 on purpose (calm) |
| bedding / cut face | 1.47 | texture only |

## How it plays

- **Tick (a note).** Each new cell grows in. Its plate swells from 55 % to full size and rises to its thickness, `#CDCDCD`, easing out over about 0.18 s (τ = 50 ms). Its tongues lengthen with it. At the same moment, last tick's growth steps down `#CDCDCD` → `#AFAFAF` → `#969696` (living grey). A cell that dies this tick loses its plate: a scar appears and the hatched flake peels up from flat to the decay angle on the same ease. A cell whose 5-tick regrowth delay ends loses its scar and flake, and the stone is bare again.
- **grow** (score 5, shape). Tongue length past the plate edge is `0.85 · grow^0.7` world units: none at 0, about 17 px at 35, about 37 px at 100. The tip widens from 0.26 to 0.44 units. The colony itself isn't redrawn by the knob.
- **decay** (score 4, rotation, pre-drawn). The flakes' lift is 14° + 66° · decay: 14° at 0, 27° at the default, 47° at 50, 80° at 100. It's a tilt out of the plane, so the device uses pre-drawn variants.
- **seed** (score 2, count). The grains hanging over bare stone, each over its shadow: 0, 1, 2, 3, 4, 6, 8. On the bar's beats a grain drops onto its shadow and becomes a cell.
- **scale** (score 3, position). Splits through stone and crust at each half step along the cut row. maj has two, lyd moves one of them, pmin and pent have none.
- **Rest.** Once the last swell and lift have settled (about 0.2 s after the last tick), nothing changes. The last growth stays lit.
- **Muted** (unchanged from the candidate). The block stays, the born plates drop to living grey, and the spores hide.

`motion.gif` shows ticks 10–14 at defaults, 400 ms a tick so you can follow it (the real clock is 1/16, 125 ms at 120 bpm), and then holds still on the rest frame.

## Node plan and redraw

The rest frame is one hand-off's worth of artwork, but the cells and their states have to fit the frame budget, so this is the plan the build follows:

| part | nodes | how it changes |
| --- | --- | --- |
| areola per visible cell (34 cells: rows 2–5, 9 + 8 + 9 + 8) | top 1, wall 3 (one per thickness step, shared pivot with the top), scar 1 → 5 × 34 = 170 | shade (living / born / dim), uniform scale for the swell, show/hide |
| row-2 section (9 cells) | medulla 2 + cortex 2 (thin/thick variants) + rhizine comb 1 → 45 | shown with the plate |
| dead flakes, a pool | 12 flakes × 3 tilt variants × (body + hatch comb) → 72 | placed on a dead cell, uniform scale for depth, variant picked by decay |
| tongues, a pool | 16 → 16 | placed, turned and uniformly scaled to the projected direction and length |
| stone splits | 8 joint positions × (front wedge, front lip, top split, top lip) → 32 | show/hide by mode |
| crust splits over plates | about 40 (joint × cell pairs that can cross) | ride the plate's transform |
| spores | 8 × (grain, shadow) → 16 | show/hide, the grain drops on the beat |
| **total** | **≈ 391 nodes** (needs `"sdk": "1.8"`, more than 256), 0 paths, 0 texts, palette about 12 fill/stroke entries from the 8 stock greys (within 16) | |

The stone, its arris, silhouette and bedding are static artwork, not nodes.

From the model, measured over 400 ticks on visible cells: about 1.2 births, 1.2 deaths and 1.2 regrowth expiries a tick at the defaults, and about 1.05 / 1.04 / 1.01 at the heaviest (grow 100, decay 100, seed 8; decay kills cells before they can spread). Per tick, about 1.2 births × (top + wall over 4 swell steps, plus a dimming step) ≈ 12, deaths × 9 (hide plate, show scar and flake, two lift steps) ≈ 11, expiries × 3 ≈ 4, and tongues re-placed ≈ 3. That's about 30–32 node changes a tick, or **≈ 4–5 per frame on average** at 60 fps and 120 bpm, with the heaviest about the same plus a spore drop every other tick (+2). The **peak** is about 40 on a tick frame where 5 cells die at once. **Rest is 0.** I'm assuming 60 fps, since open-xy's docs don't state a frame rate. Pending device.

## Checks

- `lint_frame.py` on all 13 frames with `--definition`: **0 errors, 0 warnings, 0 text-in-drawing.**
- `perceptibility.py`, run on scratch copies named `c1..c4-000/050/100` plus a rest/playing pair (tick 15, 80 ms into the swell):

| control | score | need % | 0→100 | 0→50 | 50→100 | span | |
| --- | --- | --- | --- | --- | --- | --- | --- |
| grow | 5 | 2.50 | 3.08 | 1.52 | 2.08 | 348 | ok |
| decay | 4 | 1.60 | 2.35 | 2.10 | 0.76 | 110 | ok |
| seed | 2 | 0.80 | 1.52 | 0.58 | 0.96 | 324 | ok |
| scale | 3 | 1.20 | 1.45 | 1.44 | 1.36 | 190 | ok |
| note response | — | 2.00 | 9.17 | — | — | 330 | ok |

Decay's 50→100 half (0.76 against a 0.64 floor) is the closest; past 50 the flakes are mostly turning their face to you rather than growing.

## Pending

- Device: everything (greys on the panel, the 1 px black seams, the 3-step thickness, rhizine hairlines at 5–6 px spacing, flakes and tongues as node approximations). Device acceptance stays pending until someone photographs the real screen.
- Tongue turn approximation: a tongue turned and scaled in the screen plane won't foreshorten its width the way the modelled one does. It needs checking against the generator on the device.
- The node budget needs SDK 1.8 (more than 256 nodes). If the target is lower, the first things to cut are the crust-over-plate splits (about 40) and one wall thickness step (34).
- The section still shows only the start row, as the pass-02 notes flagged. I left it alone because the brief didn't ask for it.
- `definition.json` `resources.display` is still the phase-1A placeholder; it gets filled at phase 4 from the table above.
