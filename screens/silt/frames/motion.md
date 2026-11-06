# Silt · motion study (pass 02, v4: the gold pan)

A gold pan cut in half through its axis: a note swirls it, the water tips up the smooth wall, and the grains (one per partial) lift off the drift in the crease, the fine ones most, then sink back at the settle rate as the tone darkens.

Everything here comes from `build.py` (frames, contact sheet, GIFs, redraw count). Each frame lints clean (`lint_frame.py --paths 2`: 0 errors, 0 warnings, no `text-in-drawing`). I checked the frames at 1:1. The body is 92–94 % black, and `#CDCDCD` (the waterline) is the only top grey.

## Cleanup: what changed from the v4 sketch

- **It reads as a pan now, not a bowl.** It has a flat floor 2.1 units across, a 45° flared wall only 0.85 deep (about 0.22 of the rim diameter), a rolled bead on both rims (and as a double line round the back rim), and three sawtooth riffles on the left wall. They show as steps in the cut, then run on as ledges round the back-left sector of the wall and stop there, as real riffles do. The cut is thin sheet metal: a `#323232` solid body with a lit inner edge.
- **The right side is calm.** It's just a smooth wall: no hatching, no back-wall hairlines. Everything busy sits on the riffle side.
- **The water isn't hatched any more.** Hatching that follows a moving outline needs a large moving fill or a moving mask, and the device has no clip-path. So the water is drawn in the edge-lit language: a dark body whose surface edge is lit. That edge is the waterline across the cut (the one bright line) and the waterline's run round the back wall (a mid-grey hairline).
- **Grains are solid `#7D7D7D` bodies with a black hairline edge.** The sketch drew them as rim-lit rings, and at 1:1 rings in water read as bubbles. A grain really is a solid body, so a fill is right here (craft.md, Value and fill), and it stays three steps below the waterline.
- **The rest frame shows the settled state: level water, every grain on its bed.** It has to, because rest has to be still (zero changed nodes), and a still frame with the water tipped or the fines hanging would show a brightness that isn't sounding. The settled pan is the dull tone. Three controls still read at rest: layers (how many grains), grain (their size) and settle (how far the fines are strewn: see settle below). Stir only shows when it acts, on a note or a turn.

## Interactions

| trigger | what moves | from → to, time | why it matches the sound |
| --- | --- | --- | --- |
| **note on** | The waterline turns (node 2: turn, place, scale). The water's back edge reshapes (nodes 0–1). The grains lift (nodes 3…). | Tilt goes from its current value to 2° + 13° × stir (world; on screen 1.9° → 14.4°), easing out with τ 0.05 s and settled within 0.18 s. Each grain's lift target is the DSP's own `stir × ((k−1)/(n−1))^0.8`. A grain travels √lift of the way from its bed toward a point high in the water column above its own spot, slid along the tilt toward the high wall. Partial 1 never moves. | The brightening is the high partials lifting. The fines go furthest because the DSP lifts high partials most. |
| **while held** | The water holds a small tilt, 20 % of the swirl. The grains keep sinking at the settle rate. | The tilt reaches its held value and stops (no redraw once it's there). The grains sink as e^(−t/τ). | A held note settles back to the dull tone even while it sounds, as the DSP does. The held tilt is the one cue that a note is still down. |
| **settle** (0.1–10 s) | How long the grains take to sink, and how fast the water levels. At rest, the drift's length. | Lift decays with τ = the settle time. The water levels with τ = ½ settle, clamped to 0.1–1.5 s (the brief: "the water levels and the grains sink back at the settle rate"). At rest, the fines' landing spots run 1.15 + 0.85 × settle units out from the crease, so a slow settle strews them further across the floor: a particle that falls slowly drifts further before it lands. | 0.1 s is a flick, the plucked brightness. 10 s is a slow glassy fall: the fines hang and the water stays tipped. Stills are 0.6 s after one note: at 0.1 s everything is back down; at 10 s the fines still hang and the water is still tipped. |
| **layers** (2–64) | How many grains. | 2 → 64 grains, doubling up the range. Each partial's grain has a fixed size (radius 7.0 × k^−0.19 px, 7 → 3.2 px) and a fixed landing spot, so turning layers adds or removes fines at the far end of the drift and the rest stay put. On a turn, an added grain sinks in from the waterline in 0.2 s, and a removed one rises to the waterline and is hidden. | One grain per partial: 2 is a bare pan, nearly a sine; 64 is a full drift, buzzy. |
| **stir** (0–100) | How far the water tips, and how high the grains ride. | Tilt 2° → 15° (world), 1.9° → 14.4° on screen. The waterline's high end climbs about 35 px up the right wall (y 146 → 111). The finest grain's lift goes 0 → 1. On a turn with no note: while the encoder moves, the water holds this stir's swirl and the grains lift to it; 0.25 s after the last change it levels and settles like a note (a preview swirl). | It's the main timbre control: no brightening at 0 (the water just rocks 2°, the grains stay down); a bright, buzzy lift at 100. |
| **grain** (0–100) | Every grain's size. | Node scale 1 → 1.6, eased over 0.2 s on a turn. The drift lays out longer so coarse grains still lie under the water. | Fine silt becomes coarse sand: the partials pulled off harmonic, rough and metallic. |
| **repeated notes** | Re-stir from wherever things are. | The tilt climbs again from its current value. Each grain's target becomes max(current, new), so nothing drops on a re-stir. At 16ths the water stays tipped and the fines stay up. | Fast notes keep the tone bright, so the pan never gets to settle. |
| **chord** | One swirl, harder. | m new notes in a frame (the serial merges them) give × (1 + 0.1 (m−1)), capped at × 1.25. The tilt is capped at 16.5° world, where this much water would start over the rim. It costs no more nodes than one note. | A chord stirs more partials at once. One harder swirl reads better than several in a row and doesn't double the redraw. |
| **note off / release** | The water levels; the grains finish sinking. | After `hold_ended` for the last note, the held tilt eases to level (τ as for settle). The remaining lift sinks with τ = min(settle, 0.6 s), so the frame is still within about 3 s even at a 10 s settle. | Once the tone has released there's nothing left to hear, so the motion fades with the release instead of crawling for another 50 s. (SDK 1.10 could pace this from `amp`'s release; silt is on 1.2.) |
| **rest** | Nothing. | Level water, every grain on its bed. Zero changed nodes. | Silence. |
| **reduced motion, track change, display reset** | Jump to the end state. | The settled frame, or the held tilt if a note is down. | |

All of this is pre-drawn geometry moved in the screen plane. The waterline is a true in-plane rotation: a level ribbon authored at the rest chord's length (230.7 px), turned, scaled 0.99–1.02× (so its 2.0 px width stays at 1.99–2.03 px) and placed at the chord's midpoint, so its ends land on the walls at any tilt. Grains only translate and scale.

## Node plan

| node | part | how it moves | driven by |
| --- | --- | --- | --- |
| 0, 1 | The water's back edge, two halves of one 1.2 px ribbon that overlap 3 px at the seam (`#7D7D7D` fill). The edge is where the tilted surface meets the cone, plus the straight run across the dry floor when the swirl uncovers it | **Mutable outlines, 48 points each** (24 per ribbon edge). The points come from a 3D model where the water's volume is conserved over the whole pan, not just the cut. Max extent is 63.1 px from the node origin, so it stays within ±64 | Tilt. The path key is the tilt in 0.2° steps, so the key changes only when the points do |
| 2 | Waterline (`#CDCDCD`, 2.0 px ribbon, 4 points) | turn + place + scale | Tilt |
| 3–66 | Grains 1–64 (7-point outline, `#7D7D7D` fill, black 0.6 px edge) | translate at whole pixels; scale 1–1.6; hidden at (640, 320) past the layers count | Lift, the bed layout (layers, grain, settle) |
| static | Back rim (bead and lip), back floor edge, riffle ledges, the cut sheet with its lit edge and beads | never | — |

- **Mutable outlines used: 2 of 4.** The water's back edge is about 240 px wide, so one outline can't hold it within ±64 px. I split it in two rather than author it at half size and scale it 2×, because a ribbon's width would scale with it.
- **Proposed `resources.display`:** `paths 2, points 48, nodes 67, texts 0, palette 3`, and about 544 `stateBytes`: the tilt, peak, attack and since timers and flags; Q15 lift and target per grain (64 × 2 × 2 bytes); and the shown positions for the stagger (64 × 2 × 2 bytes). `definition.json` still has the placeholder; I haven't changed it.
- **The stagger.** With more than 17 grains, they take turns: grain j moves only on frames where `frame % ceil(n/17) == j % ceil(n/17)`. At 64 layers each grain moves on every 4th frame. That holds the peak at 19.

## Redraw

Simulated at 60 Hz. A node counts as changed when its whole-pixel position, its scale, or the 0.2° tilt step differs from the previous frame. The three water nodes count as changed whenever the tilt step changes.

| case | average while the notes play | peak | still after |
| --- | --- | --- | --- |
| Defaults, the GIF phrase (one note, then a quick phrase and a chord) | 4.0 | 17 | 7.6 s, then 0 |
| Defaults, 16ths for 2 s | 1.4 | 17 | 4.6 s, then 0 |
| Flood preset, 16ths | 3.7 | 19 | — |
| **Heaviest:** 64 layers, stir 100, grain 100, settle 0.1 s, 16ths | **14.4** | **19** | 2.5 s, then 0 |
| Heaviest, settle 1 s | 9.1 | 19 | 4.4 s, then 0 |
| Heaviest, settle 10 s | 3.1 | 19 | 7.9 s, then 0 |
| 64 layers, stir 100, settle 10 s, one note held 4 s | 4.6 (over the whole tail) | 19 | 8.9 s, then 0 |

So the heaviest case averages about 14 changed nodes a frame with a peak of 19, and rest is 0. Without the stagger, the heaviest case averaged 42 with a peak of 64.

## Perceptibility

I ran `perceptibility.py --header-bottom 20` on the stills, copied to `c<N>-000/050/100` names in a temporary folder (since deleted). The scores come from the brief.

| control | score | need | 0 → 100 | 0 → 50 | 50 → 100 | span | |
| --- | --- | --- | --- | --- | --- | --- | --- |
| settle | 4 | 1.60 % | 3.01 | 2.71 | 2.39 | 240 | ok |
| layers | 4 | 1.60 % | 1.86 | 0.70 | 1.19 | 183 | ok (low half 0.70 against 0.64: tight) |
| stir | 5 | 2.50 % | 3.17 | 3.20 | 3.08 | 263 | ok |
| grain | 3 | 1.20 % | 1.81 | 1.46 | 1.70 | 177 | ok |
| note response (rest → playing) | — | 2.00 % | 3.09 | | | 245 | ok |

What each still shows: **rest**, **layers** and **grain** are settled, with no note. **playing** and **stir** are 0.2 s after one held note (the swirl at its peak). **settle** is 0.6 s after one held note (the fines mid-fall).

## Departures, said plainly

- **Stir's rotation is 12.5° on screen, under the 30° channel floor.** A 45° pan this shallow can't hold a steeper surface: with the volume conserved, the water reaches the rim at about 17°. The brief also asks for "a pan swirled gently, not sloshing". So stir's travel is the tilt plus the high end's 35 px climb up the wall (a position change) plus the grains' lift, and it measures 3.17 % against a 2.5 % need. The candidate's 38° isn't buildable without a bowl.
- **Settle and stir both move the water's tilt in a still.** Stir sets how far it tips and settle how long it stays tipped, so in motion they're different channels (amplitude against time). At a fixed instant they both look like a tilt. Settle's own marks are where the fines hang and how far the drift is strewn.
- **Grain scales to 1.6×, not the candidate's 2.4×.** Node scale stops at 2, and the drift has to stay under 24 px of water.
- **At the heaviest settings the drift becomes a dense pile.** With 64 layers and grain 100 the grains overlap in the cut (a pile in depth), and at a big swirl the drift on the left sits on the floor the water has just uncovered. That's physically right; it's busier than the rest of the range.
- **I can't find the brief's DSP paragraph.** `brief.md` has only the port map, so I used its rule: lift grows with partial number, one time constant to sink. The `^0.8` lift curve comes from the sketch.

## Pending

- **Device:** whether the grains' 0.6 px black edge scales with the node, at 1.6×. Whether the two halves of the water's edge meet cleanly on the device (they overlap 3 px; they're separately placed nodes). The mutable outline at 63.1 of 64 px. The waterline's 2 px width at scale 0.99–1.02. The real redraw cost. The display rate: I assumed 60 Hz, and at 30 Hz the stagger moves each grain at 7.5 Hz with 64 layers.
- **Not in the GIFs:** control turns (the preview swirl for stir, layers adding and removing grains, grain easing). These are specified here but not rendered.
- **Not done yet:** updating `definition.json` `resources.display` and re-running `lint_definition.py`; the craft review side by side with theseus-tower at 1:1; checking the outlines over a sweep of every pair of controls.
- **The owner's call:** the held-note tilt, the preview swirl when stir is turned at rest, and the release cutting a 10 s settle short to about 3 s once the note is let go.

## Files

`rest`, `playing`, `{settle,layers,stir,grain}-{0,50,100}` (.svg and .png), `contact.png`, `motion.gif` (480 × 220, 15 fps, about 8 s: one note swirling and settling, then a quick phrase, a chord and the release settling to a still frame), `motion-settle.gif` (settle 0.1 s and 10 s side by side, each pane 1:1, stir 80, one note held 4 s), `motion-sheet.png` (10 key frames with their times outside the frames), and `build.py`.
