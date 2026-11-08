# Kiln · motion

The subject in a sentence: a yarn-wound mallet poised over the rim of a thrown bowl, drawn as hidden-line 3D, with the mallet head the brightest thing; a note is the mallet striking the rim, and the ring is the lip itself bending in the bowl's own mode shapes.

Everything here comes from `build.py` in this folder (stills, gifs, sheets). Judged at 1:1. Lint: 0 errors, 0 warnings on all 14 frames (`lint_frame.py --paths 4`).

## The idea the motion hangs on

The brief's mode ratios, 1 : 2.7 : 5.2 : 8.4, are almost exactly a ring's flexural modes n = 2, 3, 4, 5 (n(n²−1)/√(n²+1) gives 1 : 2.8 : 5.4 : 8.8). So I didn't need a waveform. The bowl's modes are shapes on the rim: n = 2 squeezes the lip into an oval and back, n = 3 into a soft trefoil, n = 4 and 5 into finer and finer ripples. I model those in 3D (a radial bend of the lip, `cos n(θ − θs)`, with its antinode at the struck point) and project them through the same camera as the bowl. The bend peaks at about 3 px at the sides of the lip and 1.5 px at the front and back, then decays. That's the whole ring: the lip shivers in its real mode shapes, a few pixels, and goes still.

On screen the modes are slowed into something the eye can follow: the fundamental breathes at 2 Hz, and the upper modes run at 2 Hz × (ratio × stretch)^0.6, so about 3.9, 5.8 and 7.7 Hz at the default fire. The ordering and spread are the sound's; the absolute speed is chosen to stay calm.

Pitch changes nothing. The display input has no pitch or velocity (`display.md`, Input: a note serial, `held_notes`, `note_off_serial`), and the brief dropped bowl size because stock tune covers transposition. I'm happy with that: one bowl, always the same size, reads calmer than a bowl that jumps in size with every note.

## Each interaction

**Note on.** On the first frame after the serial moves, the mallet is on the rim. It turns about the wrist in the screen plane (6–19° depending on head size and fire) so the head meets the lip at its right side, station 0. The struck point flashes: a short arc on the lip in `#CDCDCD` at subject weight, and the head drops to `#969696` for that beat so there's still one brightest thing. Then the mallet rebounds with an exponential ease-out (τ 42 ms, settled in about 0.2 s), the flash fades through `#969696` to a faint `#646464` mark just outside the lip that stays while the key is held, and the lip starts to bend. The first answer to the note is the subject itself.

**strike (hardness, not force).** I dropped the backswing. A bigger swing reads as hitting harder, and strike is the mallet's hardness. Now strike is the head: a yarn ball that unwinds onto its bare core. At 0 it's a fat, soft ball (r 30 px) striped with ten yarn wraps; as strike rises the wraps come off and the ball shrinks (one node scaled 1.0 → 0.4, stroke 2.5 → 1.0); from 96 up it's the bare core (r 11.5, subject weight) with its collar and one turned groove, a hard bead. Hardness also shows on the hit, because that's where you hear it:
- contact: soft is a broad (28 px), long flash (0.16 s) and the yarn sits on the rim a beat longer (dwell 0.1 s); hard is a crisp 8 px flash for 0.07 s and an immediate bounce;
- which modes ring: a soft mallet's 4 ms impulse barely reaches past the fundamental, so the lip only breathes in the slow oval (mode weights 1 : 0.11 : 0.01 : 0); a hard one's 0.15 ms impulse rings all four, so fine upper ripples ride on the oval (1 : 0.77 : 0.60 : 0.46).

**glaze (damping).** On the bowl, glaze is the hatched glazed interior below a glaze line. At 0 it's bare bisque, no hatching at all; it appears at the floor and rises to well up the wall at 100. It's one hatched disc scaled about the top of its own back arc (≤ 1.55×; hatch spacing 3.5 → 5.5 px, lines 1.2 → 1.9 px, so thick glaze reads heavier), occluded by a black front-wall mask, so it's a scale and translate on the device. In motion, glaze is the decay: the ring's T60 runs 6 s × 0.05^glaze, so about 6 s bare, 2.4 s at the default 30, 0.3 s thick, and the upper modes die harder (÷ (1 + 1.4 · glaze · k)). On screen, the lip moves for about 5 s on bare bisque, 1.9 s at the default, and 0.19 s under thick glaze, where it's one twitch and stillness (see `motion-glaze.gif`, key held in both, so this is the bowl's own decay). With glaze up, the fine ripple goes first and the oval breathes a little longer, which is what you hear.

**crack (inharmonic doublets).** On the bowl: a dunting crack runs from the lip down the front-left wall and forks as crack rises (a tree of 30 branches revealed by path length from the mouth, so it lengthens, forks, and its forks fork; on the device each branch is a node that scales up from its root). The crack also springs the lip: the far side stands proud by up to ~2.4 px and the near side sinks a little, so the rim's round is visibly broken at the crack. In motion, the crack does what it does to the sound. A round bowl's modes are degenerate; a crack splits each mode above the fundamental into a doublet, one shape with its antinode at the crack and one with its node there, at slightly different frequencies (split 11 % × the mapped crack amount, plus +5/−6/+7 % detune). I draw both. Struck away from the crack, the pattern starts as a clean `cos n(θ − θs)` and then drifts: the two halves beat, so the ripple swings round and back about the crack instead of standing still (about a 0.4 Hz beat on n = 3 at crack 100). Past crack 15 the crack also chatters while the bowl rings: the lip jogs across the crack and the crack's mouth opens and closes frame by frame, scaled by how much ring is left. That's the buzzing clink (`motion-crack.gif`: the same strike uncracked, then at 100).

**fire (modal stretch).** On the bowl, high fire is a vitrified body: it shrinks (firing shrinkage, 1.00 → 0.92 about the foot; ~9 px at the rim's ends) and the lip thins (wall 0.10 → 0.065). Shrinkage is a uniform scale of every bowl node about one pivot; the thinner lip is in the mutable rim outlines. Weights are authored at fire 0 so hairline 1.2 → 1.1 and line 1.6 → 1.47 stay inside craft.md's table. In motion, fire stretches the upper modes: they shiver faster (n = 5 goes from 7.2 to 8.2 Hz across the range), and with the extra Q they last a little longer (upper T60 × up to 1.45). Higher fire makes a finer, glassier shimmer that outlasts the oval's breathing. The fundamental's speed doesn't change, which matches the sound: fire is a timbre change, not a pitch change.

**Chord, several voices.** One bowl and one hand. Every note start strikes: the mallet hits station 0 again, but each new voice lands on its own station along the front of the lip (−14°, −58°, −92°, −162°, then round again) and gets its own flash and held mark there. Each voice's ring pattern is oriented to its own station, so a chord is a superposition of differently oriented shapes: the lip's shiver loses its single symmetry and shimmers (rolled chord at 2.6 s in `motion.gif`). When starts coalesce into one frame (the serial jumps by k), the mallet strikes once and k stations flash together. It costs nothing extra: the same four outlines carry any number of voices, and stock caps a track at 8. Held marks show `held_notes` (up to four), newest stations first.

**Note off and release.** Nothing restarts at a note-off: the held mark at that station goes, and the ring carries on with its glaze decay. If the stock envelope's release is shorter than the ring, the shiver also fades with it (a gate exp(−t / (release / 3)) from the note-off; SDK 1.10 reads it from `amp.release`, and older SDKs assume a default). So the screen never shows ringing after the sound has gone. With several voices held, `note_released` releases the oldest held voices first, since the tracker can't say which pitch let go; `hold_ended` releases them all.

**Rest.** Once every voice's bend is under 0.3 px, it snaps to exactly zero, the outlines take their rest points and stop being re-keyed, and nothing moves. The last frame of `motion.gif` is byte-identical to `rest.svg` (checked). A held note whose ring has decayed is still too: the bowl's silent, so is the screen, and only the held mark shows the key is down.

**Reduced motion, track change.** No swing and no ring: a note shows the flash as the held mark straight away, and the mark goes at release. Track change and `display_reset` jump to rest.

**Control turns.** Every control eases to its new value with an exponential ease-out (settled in 0.15–0.2 s) and then stops.

## Node plan

| part | nodes | how it moves |
| --- | --- | --- |
| lip: outer L, outer R, inner L, inner R | 4 mutable outlines (nodes 0–3), 64 points each (32-point centreline ribbons) | ring bend, crack spring and fire's lip thinning move their points; fire moves their origins. Split front/back so every outline stays within ±64 px of its origin (checked in `build.py`) |
| body fill, front-wall mask | 2 | fire scale |
| lower silhouette, throwing rings in and out, foot | ~22 ribbon chunks | fire scale |
| glaze disc: 25 hatch chords + outline | ~28 | glaze scale + translate, fire scale; hidden at 0 |
| crack: main (3 chunks) + 29 branches | ~32 | each scales up from its root as the reveal passes; hidden until reached; fire scale |
| contact flash per station × 3 widths (8 / 16 / 28 px), held mark per station | 16 | shade and hide |
| mallet: rod, two edges, butt cap and line, yarn ball, 10 wraps, core, collar, groove | 19 | all turn about the wrist; ball and wraps scale with strike; wraps hide one by one |

About **130 nodes**, under 256, so no SDK 1.8 needed. **paths 4, points 64, texts 0, palette 7** (the six greys `#CDCDCD`–`#4B4B4B` plus black). State: NoteTracker (16 B), up to 8 voices × {start time, station, strike at the hit, release start} (~12 B each), the mallet's last strike, five eased control values: about **160 bytes**. SDK 1.1 for note activity, and 1.10 if the release follows `amp`. I haven't touched `definition.json`: its `resources.display` is still the placeholder, and these numbers are the proposal for phase 4.

## Redraw estimate

Counting changed nodes per frame, a re-keyed mutable outline as one node:

- **Ringing (any setting):** the 4 lip outlines every frame, plus 1 for crack chatter above crack 15, plus a flash fading now and then: **4–6**.
- **The 0.2 s after a strike:** the mallet's turn moves every visible mallet node (rod 5, ball 1, wraps 0–10, core 3 once bare) plus the flash: **about 17 at the default, 22 at strike 0 (peak), 13 at strike 100**.
- **Average while notes sound:** at the defaults one note averages about **6** over its 1.9 s ring. The heaviest case is a fast run at strike 0 under thick glaze, where most frames are mallet turns: about **20**, at the guideline. Chords add stations, not nodes.
- **Rest: 0.** Voices snap to zero under 0.3 px, the outlines stop being re-keyed, and the mallet parks exactly at its rest angle.
- **Control turns** aren't in that budget, but for the record: fire rescales the whole bowl (~100 nodes a frame for its 0.2 s ease), like toro's fold turn. Glaze is ~28, crack ≤ 32, strike ~14.

## Perceptibility

`perceptibility.py` on each control's 0 / 50 / 100 (copies named c1–c4 in a scratch folder, deleted after), scores 4, 5, 3, 3 from the brief, header bottom 20:

| control | score | need % | 0→100 % | 0→50 % | 50→100 % | span | |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strike | 4 | 1.60 | 1.70 | 1.96 | 0.87 | 63 | ok |
| glaze | 5 | 2.50 | 3.07 | 1.66 | 3.61 | 168 | ok |
| crack | 3 | 1.20 | 1.82 | 1.00 | 0.99 | 219 | ok |
| fire | 3 | 1.20 | 9.96 | 9.15 | 8.80 | 238 | ok |
| note response | — | 2.00 | 4.80 | — | — | 384 | ok |

All pass. Strike only just clears its floor (1.70 against 1.60), and that's with a 30 px yarn ball. Fire's area is high because a whole-figure scale shifts every line. Its real travel is modest (~9 px at the rim's ends), and I already cut shrinkage from 14 % to 8 % so it doesn't shout louder than its score.

## Files

`rest`, `playing`, `strike|glaze|crack|fire-0|50|100` (.svg + .png), `contact.png` (rest, playing, then one row per control), `motion.gif` (6.6 s at 16 fps: rest, one note held 0.6 s, its decay, a rolled three-note chord held to 3.9 s, release, rest), `motion-glaze.gif` (bare, then thick, key held), `motion-crack.gif` (uncracked, then 100), `motion-sheet.png` (eight frames of `motion.gif`, timestamps outside the frames), `build.py`.

## Pending

- **Device:** whether four 64-point outlines re-keyed every frame stay cheap enough (the redraw estimate counts each as one node); whether a 1.5–3 px bend reads on the real panel; how the 7–8 Hz upper shiver looks at the device's frame rate (it aliases a little at the gif's 16 fps); that node stroke widths scale with node scale as assumed; the fire turn's ~100-node redraw.
- **Ear:** the scores 4/5/3/3 are from the DSP, not listened to; the visual decay times follow the brief's T60s and should be checked against the engine.
- **Header:** how `ratio` rounds 1.12 and whether `1.24` fits 53 px in Univers (from the brief).
- **Phase 4/8:** write the display block into `definition.json`, and turn this node plan into the handoff's index map.
