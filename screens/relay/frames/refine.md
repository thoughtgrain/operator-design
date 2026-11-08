# Relay · v3 clean-up (cradle of stages)

The owner picked v3 from `passes/02-subject` ("I like v3, just needs some clean up and readability tweaks"). I kept the idea and the composition: a long cradle of hanging steel balls in hatched mass, the blow handed down the row and out the far end, the input ball swinging back in as the recirculation. Everything here comes from `build.py` (one script, one camera, every point projected from a world model), and I judged it all at 1:1. `before-after.png` puts the picked v3 next to the cleaned rest, and `contact.png` has rest plus each control at 0 / 50 / 100.

## What changed and why

- **Camera.** It's more frontal now (yaw 8°, pitch 13°, a long lens) and fitted tighter to the frame. v3 looked down and across, so the front and back rails and four uprights crossed each other and the strings. Now the frame reads as two solid end posts, one pair of top rails about 10 px apart, two short crossbars and a quiet slab. Ball radius at the default went from 11.3 to 12.6 px, about 25 % more area. The row's centre sits at y 128 (v3 had it at 132, and the ball row now sits mid-body rather than low). I couldn't get the balls much bigger: the frame's width is set by the room both end balls need to swing (see open questions).
- **Strings.** Each ball now hangs from one narrow V, with a leg from the front rail and a leg from the back rail at the same x, the way a real cradle hangs. The small yaw opens each V to about half a ball's width, so neighbouring V's never touch. v3 ran every string to one point per ball from both rails, and from that camera they fanned and crossed.
- **Roundness and light.** One light, from the upper left. Each ball has a black body, a Line outline, a 45° hatched shadow crescent on the lower right (behind a flattened terminator, ≥ 3.2 px apart) and a short hairline highlight arc on the upper left. v3 had the crescent but no highlight, and on the small balls it read as a scribble.
- **One bright element.** The output ball (far right, swung out) is the only `#CDCDCD`: a 2 px Subject outline, highlight and hatching one step up. Next comes the input ball (`#969696` outline) with its sweep and path, then the resting balls in `#7D7D7D`, with strings and frame in `#646464` / `#4B4B4B`.
- **Swings.** v3 drew a faint dashed hairline through each end ball's centre. Now each end ball gets its *sweep*, the band it swung through, hatched in `#4B4B4B` as a ghost (there, but not a body: craft.md, semi-opaque areas are hatched), with its path as a dashed 1.5 px `#969696` line just under the ball. The end balls' string legs go up to Line weight. The return on the left now reads as a movement, not a gap.
- **Base.** The 45° hatch on the slab was the heaviest texture in v3, so it's gone. The slab is a `#4B4B4B` outline. The posts carry the only frame hatching, on their thin side faces, and it barely registers at 1:1, which is the intent.
- **No text, no grey-fill states, nothing near the header.** The art spans y 45–198 and x 10–470 in every frame, 25 px clear of the header. Body black share is 85.0–86.5 % across all frames and the worst-case combos.

## The four controls

| control | score | channel | what moves | travel at 1:1 |
| --- | --- | --- | --- | --- |
| stages | 5 | count (+ size) | 7 → 18 balls in a row of fixed length. They shrink as they multiply, so the cradle stays one size | 7 / 12 / 18 balls; radius 21.6 / 12.6 / 8.3 px |
| leak | 4 | shape | Interior balls take a dent in their struck (left) face. The dent is a smooth concave bite with the lost metal hatched inside the old outline. Dented balls lose their highlight and shrink to 84 %, so they stop touching their neighbours. More balls dent as leak rises (seeded order, so a dent never jumps to another ball), and the dents get deeper | 0 / 3 / 6 of 12 dented, depth 28 → 50 % of r; gaps open on both sides |
| clock | 3 | position | Each ball hangs on its own string length (seeded), so the straight touching row goes ragged | spread of ball centres 0 / ~19 / 37 px |
| feedback | 4 | rotation | How far the input ball has swung back out, with its hatched sweep growing behind it. At 0 it hangs touching the row: nothing comes back | 0° / 30° / 60°; centre moves 61 px across, 36 px up |

The channels stay separate: count, shape, vertical position and the one end ball's rotation. The output ball's swing is fixed at 36°, so feedback is the only thing that rotates anything. I checked the extremes together (18 balls, leak, clock and feedback all at 100; 7 balls with clock and feedback at 100): nothing clips a post or the header. At 18 balls with full leak and clock it gets busy but each ball stays readable.

Two changes from v3's candidate, for the record. Feedback's range went from 6–40° to 0–60°: 40° failed perceptibility, and 0 now means no return. Leak's dent moved from a flat on the upper left to a concave bite on the left. A vertical flat on the left side drew a "D", which reads as a letter, and on the upper left the 45° hatch ran parallel to the dent and vanished. The left face is also where a cradle ball actually takes the blow.

## What an effect page can react to

From open-xy `docs/display.md`, Effect pages (SDK 1.7):

> Its input's `slots` hold all eight of its controls, `track` is the send (14 or 15), and two fields follow the note activity: `shift`, 1 while Shift is held on an effect with a shift row, and `choices`, each shift control's choice (0 beyond the declared ones).

Add the general input (`elapsed`, the reduced-motion preference) plus `display_reset` and the optional `display_parameter_reset`. There's no audio, no level and no tempo. Relay has no shift row, so in practice the screen reacts to **its four controls being turned**, nothing else. I haven't designed any motion that would need the signal. The cradle is a frozen moment, a notional test note just leaving the far end, and it's still at rest. On a turn, the affected parts ease to their new pose with the exponential 0.15–0.2 s ease (jump under reduced motion). A `display_reset` could allow a short entrance (the output ball swinging out once to its rest angle), but I haven't drawn it and it's optional.

## Node plan and redraw estimate

The frames are 107–146 `path`s (worst case: 18 balls with leak, clock and feedback at 100). For the device:

- **Static panel art, no nodes:** base slab, posts, rails and crossbars (~18 paths).
- **Per ball slot, 18 slots:** a round outline, a dented outline (one of the two is shown), a highlight arc, two string legs (lines with their origin at the pivot, turned and scaled), three shadow-hatch lines and two dent-hatch lines. That's about 10 nodes a slot, ~180 in all. Every part of a slot shares the ball centre as its origin, so a slot moves and scales as one (constraints.md, touching parts). Slots past the current count park off screen.
- **Swing extras:** the input ball's sweep is pre-drawn at its 60° maximum (~14 hatch lines) and its dashed path (~8 dashes), revealed up to the current angle. The output sweep and path are ~11 more.
- **Total:** ~215 nodes, under the 256 that `"sdk": "1.7"` allows. `definition.json`'s `resources.display` (nodes 64) is still the placeholder and will need raising in phase 4 (I didn't change it here).
- **Redraw:** zero at rest. With no notes on an effect page, changes come only from turns: about 25 nodes a frame during a feedback ease, ~10 a dented ball for leak, ~130 for clock (every slot translates and its strings rescale), and up to ~180 when stages crosses a count step (every slot rescales). Those turn eases run well over the ~20-a-frame average. That figure is for notes, but on a page like this a turn is the only event, so I'm marking it pending a device check. If stages is slow there, the fallback is to snap the count on the detent instead of easing every slot.
- **Scaling caveat:** the hatch and ribbon widths scale with a node. Across stages' 2.6× size range the shadow hatch has to be authored at the smallest ball's spacing (≥ 3 px) or pre-drawn in two or three size bands. Scale ≤ 2 forces size bands anyway (21.6 / 8.3 px is 2.6×).

## Lint and perceptibility

- `python3 opxy/tools/lint_frame.py` on all 13 frames: **0 errors, 0 warnings**, no `text-in-drawing`. My first pass threw 26 legibility warnings a frame: hatch pieces 2.9 px long on the small shapes. I fixed that by dropping hatch lines under 4.6 px.
- `python3 opxy/tools/perceptibility.py --scores 5,4,3,4` (frames copied to `c<N>-NNN` names in a scratch folder, since deleted):

| control | need | 0→100 | 0→50 | 50→100 | span | |
| --- | --- | --- | --- | --- | --- | --- |
| stages | 2.50 % | 11.31 % | 10.13 % | 10.57 % | 374 px | ok |
| leak | 1.60 % | 2.03 % | 0.98 % | 1.15 % | 204 px | ok |
| clock | 1.20 % | 7.38 % | 5.81 % | 5.85 % | 375 px | ok |
| feedback | 1.60 % | 1.73 % | 1.28 % | 1.27 % | 93 px | ok |

  Feedback was 0.96 % with v3's 40° swing and only a path line. The hatched sweep, the 60° range and Line-weight end strings got it to 1.73 %. That's thin, so a later change that thins the left end could drop it back under.

## Pending and open

- **Device:** everything here is pending a photo of the real screen. That covers the 1 px string V's on the `#646464`/`#4B4B4B` greys, the hatched sweep bands, and whether the dents read on 8 px balls.
- **Header:** `100ms` runs into `leak` in the preview font. It's the known header-font issue, and I've left it. The brief already lists the fallback (a header override in seconds, `0.10`), still pending device measurement.
- **Ball size:** I only got +25 % area at the default, because the width is set by the swing room at both ends. Narrowing the count range (6–16 instead of 7–18) would get bigger balls at the cost of the count travel. That's the owner's call.
- **Asymmetric frame:** the input end has more room than the output end (60° vs 36° swing), so the row sits a little right of centre and at feedback 0 the left end is empty. That's deliberate (it's where the return comes back in), but worth a look.
- **Desk-toy reading:** a Newton's cradle can still read as "momentum" rather than "delay". The sweep at the input end does more of the recirculation story than v3's arc did, but that's the owner's judgement.
