# drill · refining v3 (the brace boring a board)

The owner picked pass 02 v3 and said it needed to be "more refined, and readable visually". I treated readability at 1:1 as the whole job. Everything here comes from `build.py` in this folder, which models the brace in millimetres and projects it through one camera. `before-after.png` shows the change at 1:1, and `contact.png` shows rest plus every control at 0 / 50 / 100.

## What changed and why

**It's a modelled object now, not a bent line.** v3 was a centreline offset by 4 units, with revolved knobs stuck on the ends. Now every part is built in 3D and projected:

- the head pad (a turned mushroom with a domed end) and its knob neck with a bead
- the bow, a 16 mm rod with two filleted bends at each end
- the turned grip on the throw, with four grooves and a metal ferrule at each end
- the ratchet collar with a stepped cam ring and five ribs
- the chuck shell with two beads, and two jaws closing on the shank
- the auger: shank, throat, core, the twist's lands, two spurs, cutting lips, and a lead screw with one and a half threads

**Camera.** It's orthographic, yawed 18° and raised 8°, then rolled so the brace's axis stays dead level on screen. The yaw is what makes it read as 3D: you see the pad's dome, each turned part's end ellipses, the board's entry face and top, and the crank's sweep as a sweep. Without the roll, the axis climbed about 18 px over the width and the board ran into the header. The scale is 0.67 px/mm, and it uses the full width: the head pad sits about 10 px in from the left edge at bite 0, and the board's back face is about 8 px from the right.

**Bigger and bolder, with real thickness.** At 1:1:

| part | v3 | now |
| --- | --- | --- |
| rod | ~7 px | ~11 px |
| head pad | — | 47 px across |
| grip | — | 26 px |
| chuck | — | 25 px |
| auger twist | ~8 px | 20 px |

Nothing is a hairline rod any more. Parts meet at collars (neck, ferrules, ratchet, jaws), so there's black between every pair.

**Edge-lit vs line art: I tried both and kept line art.** I built the edge-lit version with the same model: black fills, a dim #4B4B4B edge and bright lit runs on the up-left faces. At 1:1 it fell apart. Every underside vanished, the bow read as dashes, and the brace became six bright crescents instead of one tool. There were also a dozen bright ribbons competing, so "one brightest element" was broken by construction.

Detailed line art keeps each silhouette whole:

- outer edges at Line weight (1.5 px) in #969696, over black fill
- inner detail at Hairline (1 px) in #646464: grooves, beads, ribs, the dome edge
- a #7D7D7D highlight streak on every turned part, all from the same light (up and towards the camera), so the light is consistent part to part

The board is quieter: edges #7D7D7D/#646464, grain at #4B4B4B.

**One brightest element: the auger.** Its lands, top edge, spurs and screw are the only #CDCDCD on screen (274 px of it at rest). That's where the sound is made, and it's where teeth, wear and bite all act. The body is 91.8 % black.

**Teeth moved onto parts you can count.** v3's teeth were hairline grooves on a 7 px rod. Now each turn of the twist is a land: a black band with a bright edge, curved the way a helix projects (a sine), hanging from the lit top edge, with the core showing in the flutes between lands. At the default (6) you can count six bright lands, about 25 px apart. At 3 they're long sweeping bands, and at 24 they're about 6 px apart (a 3 px land, then a 3 px gap), which is still at the hatching floor. I kept teeth on the bit rather than the ratchet: a ratchet ring's teeth seen side-on bunch to sub-pixel spacing at the edges and can't be counted at 1:1.

**The board** is a block cut through the bore. You see the cut face, the far half's entry face with half the hole, and its top. Grain runs up and down the plank, so the bore visibly cuts across it. The bore is filled black (it erases the grain it crosses), and its floor follows the cutting head: the spur grooves, the lips' cone and the screw's hole.

**Header:** ratio 2.00, teeth 6, wear 0, bite 35. Amounts are shown without %, and there's no text below the header (8 text elements, all in the header). Nothing comes within 4 px of the header at any setting or crank angle. I checked the full sweep at ratio 100: its top is at y 25 and its bottom at y 208.

## How it plays

| | what moves |
| --- | --- |
| **ratio** (score 5) | The bow's throw, 32 → 118 mm. The grip and ferrules drop about 58 px and the arms lengthen (a shape change of path 0, plus the grip translating). On a note the crank also turns faster at higher ratio (0.55 → 1.15 rev/s), echoing "the wheel turns ratio times per cycle". |
| **teeth** (score 4) | The number of lands on the twist, 3 → 24 (a count change on paths 1–2). |
| **wear** (score 3) | The cutting head blunts: spurs 11 → 1 mm and the lead screw 19 → 8 mm, with the screw's point flattening and its threads going shallow. The lands thin (48 → 28 % of the pitch) and their lower corners wear back. It's a smoothing, matching the sound getting rounder. |
| **bite** (score 5) | The whole brace slides along its axis into the board, from just the screw in the wood (bite 0) to the cutting head 74 mm deep (bite 100). The bore deepens with it. At 100 the head pad has moved 50 px right. |
| **note on** | The crank spins up in about 0.18 s and turns. The grip rides round the bow's throw: it's on the far side of the axis for half a turn (drawn behind the head and ratchet), then comes round in front. Each crank turn turns the bit once, so the lands crawl back towards the chuck by one pitch per turn, the way a twist carries chips out. The bit "bores" by turning in place; bite stays the control for depth. |
| **release** | The crank coasts on and settles, critically damped, at the next crank-down (gravity holds a level brace's bow down). That takes about 1.3 s in the preview, then the frame is identical to rest and changes nothing. |

`motion.gif` shows this at 1:1: 0.4 s rest, a 2.4 s note, the release coasting to a stop, then rest.

**The crank is a faked sweep, not an in-plane rotation.** The brace turns about its own axis, which lies level across the screen, so it's a tilt out of the screen plane and a node can't do it (display.md: turn is in-plane only). Instead, the bow is a mutable outline whose points are recomputed from the 3D centreline every frame. The grip is a static node that only translates along the projected circle. Under an orthographic camera a turned part looks the same at every crank angle, so translating the grip is exact.

## Node plan and redraw

The only other way to show a true in-plane rotation would be a camera looking down the axis, which loses the brace entirely.

**Mutable outlines (4, all at 64 points on device, each within ±64 px of its node origin):**

| path | what | points in the sketch | changes on |
| --- | --- | --- | --- |
| 0 | the bow rod | 48–52 | ratio, note |
| 1 | twist lands, left part, plus its stretch of the top edge | ≤ 64 | teeth, wear, bite, note |
| 2 | twist lands, right part, plus the top edge and the cutting head (spurs, lips, lead screw) | ≤ 64 | teeth, wear, bite, note |
| 3 | the bore: black fill, cut-edge stroke | ~18 | bite, wear |

Paths 1–2 are combs: the lit top edge is the spine and the lands hang from it, so every land fits in a single subpath. The split between the two is chosen per frame so both fit. I checked teeth 3/6/14/24, wear 0/100, bite 0/100 and ratio 0/100 at 22 crank angles each: everything fits, and all 704 frames lint clean.

**Static nodes: 43**, translate-only.

| group | nodes |
| --- | --- |
| head pad, dome, streak, neck, bead | 5 |
| grip, 2 ferrules, 4 grooves, streak | 8 |
| ratchet, 5 ribs, step, streak | 8 |
| chuck, 2 beads, streak | 4 |
| jaws | 2 |
| shank and its streak | 2 |
| core | 1 |
| board: top, entry face, section | 3 |
| grain | 10 |

That's **47 nodes** in all. Six greys are used (#000, #4B, #64, #7D, #96, #CD), so palette 6. `definition.json`'s `resources.display` is still the phase-1 placeholder (paths 1, nodes 24). Phase 4 needs paths 4, points 64, nodes ~48, palette 6. I didn't edit it, since that's outside this refinement.

**Redraw, measured from the generator** (elements that change between consecutive preview frames):

| state | nodes changed per frame |
| --- | --- |
| at rest | 0 |
| playing, any setting including teeth 24 | 11: bow + twist 1 + twist 2 + the grip's 8 nodes |
| release coast | 11 until it settles, then 0 |

Average and peak are both 11, under ~20. Three of the 11 are path redraws, which are heavier than transforms, and how heavy only a device will tell.

A control turn costs more: bite translates the whole brace plus the bore (about 34 nodes, one frame per change), and ratio, teeth and wear touch 1–3 paths plus the grip.

## Perceptibility

I ran `opxy/tools/perceptibility.py` with scores 5, 4, 3, 5. For the note response I used a scratch `playing` frame at a crank angle of 2.3 rad, since no `playing.svg` was asked for.

| control | need % | 0→100 % | 0→50 % | 50→100 % | span (px) | result |
| --- | --- | --- | --- | --- | --- | --- |
| ratio | 2.50 | 2.59 | 2.26 | 2.66 | 115 | ok |
| teeth | 1.60 | 2.53 | 1.89 | 2.45 | 142 | ok |
| wear | 1.20 | 1.29 | 0.96 | 1.08 | 152 | ok |
| bite | 2.50 | 7.55 | 6.70 | 6.69 | 462 | ok |
| note | 2.00 | 4.44 | — | — | 351 | ok |

Two controls needed work to get there:

- **Ratio** started at 2.22 %. Widening the throw stopped helping once the grip's start and end positions no longer overlapped. What pushed it over was the grip's ferrules and two more turned grooves, both of which are honest detail.
- **Wear** started at 0.51 %. Thinning the lands as they wear, and lengthening the spurs and screw so blunting them moves more, brought it to 1.29 %. That's still the closest margin.

I also tried a hairline circle showing the grip's sweep (it took ratio to 3.0 %). At 1:1 it read as a floating oval, not a sweep, so I dropped it.

## Lint

`python3 opxy/tools/lint_frame.py screens/drill/frames/*.svg` gives 0 errors and 0 warnings on all 13 frames, with no text in the drawing. A sweep of 704 in-motion frames (crank angles × the control extremes) is also clean. To get there I had to:

- keep one attachment point where a land's edge runs up under the top edge (it was folding back)
- hang the part of a land that's gone behind the throat from the throat's corner
- add a tidy pass that drops repeated points and hairpins from the twist outlines

## Pending

- **Device:** everything. The lands at teeth 24 (3 px land, 3 px gap) and the 1 px groove arcs on the grip need checking on the real screen. So does whether three path redraws per frame plus 8 translations stays smooth, and whether the 18° yaw's end ellipses survive the panel.
- **Frames not bound yet:** these are design frames without `drill_node_<i>` IDs, and the paths aren't padded to 64 points. The node plan above is the binding.
- **Wear** passes by 0.09 %. If the device renders lines thinner, it may need the lands to wear a little more.
- **No `playing.svg` or `motion.md`** yet. The motion is described here and previewed in the GIF.
- **Speed choice:** the crank speed following ratio is my addition; it's easy to drop if a constant hand speed reads better.
