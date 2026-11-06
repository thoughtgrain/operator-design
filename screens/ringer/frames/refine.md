# Ringer · v2 straight on · refine notes

The owner picked v2 from `passes/02-subject/` (hidden-line bells hung along a beam in striking order) and asked for "v2 straight on with the current detail". This is a cleanup of that pick, not a new generative pass. Everything here comes from `build.py`, and I judged every frame at 1:1.

```sh
python3 screens/ringer/frames/build.py            # frames + pngs, before-after, contact, motion.gif
python3 screens/ringer/frames/build.py --check    # lint + perceptibility (scratch folder, removed after)
python3 screens/ringer/frames/build.py --budget   # node plan and changed nodes per frame
```

Needs shapely for the swung bell's silhouette, plus rsvg-convert and Pillow.

## What changed and why

- **The camera.** v2 looked down the row from above and to the side, so the far bells shrank under 10 px and the order ran into the distance. Now the camera is orthographic, pitched 9° up with no yaw. You're looking up at the bells from just below the lips, the way you would in a tower. The beam runs level across the frame (x 12–468) and place 1 is on the left, so a change reads left to right in the order it strikes.
- **Why orthographic.** With no perspective, a bell looks exactly the same wherever it hangs on the beam. That makes method's trades pure translations on the device and keeps every bell's drawing dependent only on its size. The 9° pitch is all the 3D there is (craft.md, Think in 3D: one camera, modelled solids). It's enough to show each lip as an ellipse with the dark mouth inside and to curve the band lines into ∩ arcs.
- **One axle line.** Every headstock sits on the same axle, so bigger (lower) bells hang lower and their lips step down along the row. You get the scale of the ring without reading sizes off a perspective.
- **Detail kept.** Every bell keeps the crown edge, shoulder, waist, sound bow, lip and mouth, plus its headstock. I added two plain hangers per bell, from the beam down to the gudgeons, and the clapper's flight hanging below the lip. A bell is built as nested closed bands, each black-filled from one ring of the profile down to the lip: body, then shoulder, waist and sound bow, each band's top edge being its band line. A fill-none outline goes on top so the body edge stays one weight. That means each detail line is a node I can hide, and any line closer than 3 px to its neighbour at 1:1 gets dropped. At 12 bells the treble keeps only its waist line; the tenor keeps all three. The headstock never gets thinner than 5 px, so small bells don't turn it into a blob.
- **Brightness.** One bright element: the bell striking now (`#CDCDCD`, 2 px edge, `#969696` bands). At rest it's the bell that leads the current change. Everything else is `#7D7D7D` edges with `#646464` bands, hangers and beam, and the open-lead hatch is `#4B4B4B`. No text below the header, no grey-fill states. Body black is 91.6–92.3 % across the set.

## How a strike shows, and what it costs

A real tower bell swings a full circle about the axle running along the beam, from mouth-up balance through down and back up. From the front that's all out of the screen plane. I tried three ways of drawing it:

- **Pre-drawn poses.** Three or four poses × 12 bells × about 6 nodes is 200–300 extra nodes, with a 12-node swap per pose change. Too heavy for what it buys.
- **The bell tipping in plane.** Cheap (one turn), but it's the wrong axis, and it reads as a cartoon bell rocking side to side.
- **What I picked: the striking bell tips up toward you, re-projected each frame into the four mutable outlines.** The outlines are body silhouette, waist line, sound-bow line and mouth, 48 points each. The bell lights for its swing (sin-shaped, peak 22°), then falls back still. Meanwhile its six static body nodes are hidden. Its headstock (which moves under a pixel at 22°) and its flight stay where they are: the clapper hangs plumb as the bell rises to meet it, and that's how a strike actually happens. The mouth opens toward you with a bright lip and the clapper inside. That reads as "this bell is ringing" at 1:1.
- **It's a stand-in.** 22° is a gesture toward the swing, not the full circle. I tried 45–62° first: at 1:1 the bell collapses into a bright "O" (a mouth seen nearly end-on) and stops reading as a bell, so the angle stays small on purpose. The bells also hang mouth-down at rest, which a ringer would call "down", not "up at balance". I kept that because it's the readable pose and v2's.
- **Swing length.** T = min(0.24 s, 0.95 blow), so a swing never overlaps the next one and the four paths are always enough (one bell in the air at a time).
- **Cost per blow.** About 20 node changes on the hand-over frame: 6 hidden, 6 re-shown, 4 paths, 4 repaints. Then 4 per frame while it swings.

## Each control

| control | score | channel | at 0 / 50 / 100 | notes |
| --- | --- | --- | --- | --- |
| bells | 4 | count, with a uniform scale to fit | 4 / 8 / 12 bells; treble lip radius 30 / 14 / 8 px (scale 1.0 / 0.46 / 0.27 of the 4-bell art) | Bells beyond N are hidden. Size is set so the widest row (pace 0, stroke 100) fits 440 px. Detail lines under 3 px are hidden per bell |
| method | 3 | position (translation along the beam) | hunt `214365` · sted `354216` · camb `524613` (bob `312546` at rest) | Rest shows row 13 of each method, the first row where all six differ and none is rounds. Grandsire and Stedman ring on 5 with the tenor covering. Kent and Cambridge use their real minor/major notation; other stages use a stand-in |
| pace | 5 | spacing between lips | gap 14.2 / 8.9 / 3.5 px at 6 bells (never under 3.5) | Spacing reads at rest, which timing alone never would. On the device it also sets the time between blows |
| stroke | 2 | count: a hatched band under the beam, left of the lead | 0 / 6 / 12 hairlines at 6 bells (pool of 18, 45°, 4 px apart, 20 px tall) | The open lead drawn as an empty bay: the row steps right by up to one blow's pitch. The step is the same position channel pace uses, so the hatch has to carry it. On the device it's also the pause before each handstroke row |
| rest | — | — | still: the lead lit, nothing moving | Zero node changes once the last swing and trade settle |

**Ringing.** Bells strike left to right. Behind the strike front, each pair that trades in the next change slides past the other along the beam (ease-out, min(0.15 s, one blow) long). A trade starts half a blow into the next bell's swing once both bells of the pair have struck, so the next change builds up behind the bells still ringing and is ready when the row ends. Draw order is fixed, so during a trade the smaller bell passes in front. When notes stop, the current swing and trades finish and everything is still. `motion.gif` shows two plain bob changes at the defaults (120 bpm, 2 a beat), then settled.

## Node plan and redraw

- **Nodes:** 4 mutable outlines × 48 points, beam 2, open-lead hatch pool 18, and 12 bells × 10 (two hangers, headstock, body, shoulder, waist, sound bow, outline, mouth, flight). That's **144 nodes**, 0 texts, about 10 palette entries.
- **Not declared yet.** `definition.json`'s `resources.display` still holds the placeholder (`paths 0, nodes 1`). It wants `paths 4, points 48, nodes 144, texts 0, palette ~10` once this is accepted.

Changed nodes per frame at 60 fps while ringing (`--budget`, which simulates the same schedule as the gif):

| setting | 90 bpm | 120 bpm | 180 bpm |
| --- | --- | --- | --- |
| defaults (6, bob, 2.0, 0) | 7.4 avg / 32 peak | 9.8 / 44 | 12.7 / 44 |
| 12 bells | 7.9 / 32 | 10.6 / 44 | 13.7 / 44 |
| pace 8 | 15.5 / 44 | 16.8 / 44 | 19.4 / 44 |
| 12 bells, pace 8 (heaviest) | 16.4 / 44 | 17.9 / 44 | 20.3 / 44 |

- **The heaviest setting sits on the ~20 line at 180 bpm.**
- **The peak of 44** is a hand-over frame landing while a pair is still mid-trade (20 + 20 + 4). Starting the two bells of a pair a frame apart, or a shorter trade at fast paces, would bring it to about 34.
- **At rest it's 0.**
- **When a control turns,** every bell moves (bells, method, pace, stroke), as with any control turn.

## Checks

- **Lint:** `lint_frame.py` on all 13 frames gives 0 errors, 0 warnings and no text in the drawing. Longest path is 56 points, and nothing touches the header (the beam top is at y ≈ 86).
- **Perceptibility,** 0 vs 50 vs 100 for every control (`--scores 4,3,5,2`):

| control | need | 0→100 | 0→50 | 50→100 | span | |
| --- | --- | --- | --- | --- | --- | --- |
| bells | 1.6 % | 9.08 % | 9.13 % | 8.13 % | 366 px | ok |
| method | 1.2 % | 8.34 % | 8.19 % | 7.62 % | 334 px | ok |
| pace | 2.5 % | 7.49 % | 6.48 % | 6.44 % | 360 px | ok |
| stroke | 0.8 % | 9.14 % | 8.47 % | 8.33 % | 408 px | ok |
| note response | 2.0 % | 3.59 % | | | 210 px | ok |

- **Note response:** compared against a mid-row frame (the fourth bell at the top of its swing, the first pair already traded), it's 3.59 %. **A lone first blow is 1.09 %, under the floor.** One bell tipping 22° is about 50 px of change. It only clears the floor once the change starts building behind it, from the second or third blow on.

## Pending

- **On the device:** a 1:1 photograph; whether palette stroke widths stay put under a node scale of 0.27 (if they scale, swap palette entries per size band); that the mutable outlines can be authored after the bells so the swinging bell draws in front; whether a 22° tip reads on the real screen; the measured redraw and the 44-node peak.
- **Mute** isn't drawn yet. My proposal: no bell lit, the row still, and the hangers dropping to `#4B4B4B`, a "bells stood" look. It needs a frame and a check.
- **`resources.display`** in `definition.json`: update it once the owner accepts this.
- **The open-lead band is static.** It doesn't flicker on and off between hand and back rows. I think that's calmer, but it's a choice.
