# Tide · motion (pass 02 v4, cleaned)

Everything here comes from `build.py` (`python3 screens/tide/frames/build.py --motion`): the frames, the contact sheet, `motion.gif` and the redraw numbers. The generator runs the same node model a `display.cpp` would. Its sound model is the brief's DSP as the screen reads it. It isn't audio and it isn't a device capture.

## The subject in a sentence

Foam on the rock pool, seen from just above the water with a long lens: eight black bubble domes, one per resonator and sized by partial (a bubble rings at a pitch its size sets), lit only along their back edges by a low sun behind the raft, with swell fronts running across the water under them.

## What I cleaned up

- **Empty top half.** I swapped the sketch's wide camera for a long lens (f 1950, 11.5° down, 19 units back). That compresses the pool's depth, so the swell fronts fill the body from the header down and the horizon sits off screen. The raft is also bigger: the fundamental's dome is 69 px in radius and reaches y ≈ 80. Fronts closer together than 3.6 px on screen are hidden, which keeps the far water above the hatching floor. The body is 90 % black at rest (81 % at swell 0).
- **Crescents turning into moons.** Each lit edge now comes from the 3D light. Brightness is (n·L)^1.6 along the dome's real contour circle. The meniscus darkens the foot of the film, so the light lifts off the waterline instead of running down to it. A neighbour that blocks the sun (a ray test against every other dome) cuts the arc. The ribbon tapers with the brightness, from 2.3 px (fundamental) or 1.8–1.9 px down to a 0.55 px flat end. The arcs run about 70° over the upper left, not a half circle. Partials 3, 5 and 8 are cut by neighbours' shadows to 49°, 30° and 53°. The other five share nearly the same span, because one sun lights them all. They still read differently from each other through size, taper and which neighbour hides part of them.
- **Brightest element.** At rest the fundamental's edge is `#AFAFAF` (step 6) and is the only thing that bright. Partials 2–3 are step 5, 4–8 are step 4, and the waterlines and spent foam are step 3. Fronts are step 1 far off, step 2 in the middle and step 3 in front of the raft. `#CDCDCD` is kept for the moment a crest hits (craft.md: "or the thing a note just hit").
- **Crowding and clipping.** Spent foam is placed so its dome can't tuck more than 40 % into a neighbour's, never sits where a nearer dome hides it, and stays whole on screen with room to drift. Drift clamps every bubble to x 4–476. The film's inner reflection hairline from the sketch is gone: with this light it fell below the dome's centre line, where it read as a smudge.
- No text below the header and no grey-fill states. Domes are black bodies, and foam that has stopped ringing is a hollow wireframe (black fill, step-3 outline, as in toro).

## Interactions

All control eases are exponential ease-out and settle in 0.2 s. Reduced motion and a track change jump to the end state. Turning a knob at rest moves only what that knob owns. Nothing moves on its own.

| trigger | what moves | by how much | why it matches the sound |
| --- | --- | --- | --- |
| **swell** (score 5) | spacing of the fronts on the water (position, 30 nodes) | wavelength ∝ T^0.5: 0.34 → 0.95 → 1.9 world units, so the frame goes from about 30 fronts 4–8 px apart to about 7, 30–40 px apart | Longer period, longer wave (deep water goes as T²; I drew T^0.5 so 0.25 s stays above the 3 px floor). While a note sounds, fronts travel one wavelength per period, so their speed in px/s follows swell too. |
| **depth** (score 5) | **Playing:** how long the lit edges stay bright after a crest (shade). **Rest:** how much spent foam lingers round the raft (count, 0 → 30 hollow bubbles) | Each edge falls one grey step per 6 dB, with T60 = depth·k^-0.5, so its last visible step goes out after about T60/2: 25 ms at 50 ms (a flicker), 0.25 s at 0.5 s, 2.5 s at 5 s (with a 2 s swell the raft never goes dark: the drone) | See "depth: why not the voiced bubble count" below. |
| **salt** (score 3) | sizes of the voiced bubbles (uniform scale per bubble, about its waterline centre) | Bubble k scales by k^(-0.3·salt) (Minnaert: radius ∝ 1/frequency). The fundamental doesn't change, partial 2 shrinks to 0.81, partial 8 to 0.54 | The partials stretch apart, so the small bubbles shrink away from the big one, and gaps open in the raft. The small edges are authored heavier, so at 0.54× they still draw 1 px. |
| **drift** (score 2) | where each bubble floats (position) | Each bubble is pushed up to 28 px off its packed place in its own direction (mostly sideways, a third of that in depth), then a short relaxation pushes touching bubbles apart. While notes sound, each direction does a slow random walk (0.25 rad/√s), about 7 px/s at 100 | Each resonator wanders on its own, so the raft loosens and jostles. The ±40 cents of pitch is invisible as size, so the wander is drawn as where the bubble floats. |
| **note on** | the fronts start rolling, and the raft starts lighting at once | Fronts ease into the voice's phase (at most half a wavelength, 0.2 s), then move one wavelength per period. Edges climb with the wave envelope from the first frame, and every bubble rides the front up and down: 2 px at swell ≥ 2 s, scaling to 0 at 0.5 s and below | The noise starts rising at note-on, so the resonators fill straight away. The raft answers before the first crest arrives. |
| **crest** (each period) | a front reaches the raft's centre line exactly when the wave envelope peaks (rise = 0.15·T, clamped to 0.03–0.6 s); edges brighten, and the front nearest the raft gains up to 2 steps | Edge step = base + ⌊(dB + 18)/6⌋, capped at `#CDCDCD`. At a full crest the fundamental and partials 2–3 reach step 7 and 4–8 reach 6. Small bubbles decay first (T60 ∝ k^-0.5) | Brightness follows each partial's level (amplitude k^-0.5). The fall follows depth. Higher, smaller bubbles go dark first, as higher resonators do. |
| **held chord** | Edges show the power sum of every voice's partial k. Fronts follow the **oldest** sounding voice's clock | Struck together: one train, and the edges hold their top steps longer. Rolled: the fronts keep the first note's timing, and the raft re-lights at each later voice's own crest, more often than the fronts arrive | Each voice's swell starts at its own note-on, which is what you hear. One train per voice would cost 30 nodes each, and a front that re-phases on every new note would jump. When the oldest voice is released, the fronts ease (0.2 s) to the next oldest. |
| **note off / release** | fronts slow with the amp release (speed ∝ √level) and coast to a stop; edges decay over depth; bubbles settle at their last pixel | With the stand-in 0.5 s release, the water stops about 0.3 s after note-off at the defaults, 0.5 s at swell 0 or drift 100, and 1.5 s at the heaviest (depth 5 s) | The waves keep coming only while the noise does. The resonators keep ringing for depth after it stops, so the edges outlast the water. |
| **rest** | nothing | 0 changed nodes, measured in every case below, from the frame the last edge reaches its base step | Idle is still. The fronts stay wherever they stopped. The next note-on eases them into the new phase. |

**depth: why not the voiced bubble count.** The candidate drew depth as how many bubbles survive (6 → 18). That has two problems. First, the eight voiced bubbles are the eight resonators. At depth 0 the voice still has eight partials (they just ring for 50 ms), so removing bubbles says the sound has fewer partials, which it doesn't. Second, it ties a count to the decay I'm animating, so a turn of depth during play would add and remove the very bubbles that are lighting up. So the eight voiced bubbles never change in number, and depth's main channel is time: how long the lit edges hold. That's the honest reading of T60. A knob has to change the picture at rest too, so depth also sets how much **spent foam** lingers: hollow bubbles that have finished ringing. Foam that lasts longer piles up. It's on different nodes (never the voiced bubbles), drawn in a different state (wireframe, not lit), and it moves in the same direction as the sound: none at 50 ms, a thick lee at 5 s. Spent foam doesn't light at a crest; it just bobs with the front.

## Node plan

| part | nodes | geometry | driven by | channel |
| --- | --- | --- | --- | --- |
| swell fronts | 30 (0–29) | a 62-point closed ribbon (31 samples × 2 edges), 1.1 px at scale 1, spanning x −292..292 about its origin | wave `w` uses node `w mod 30`, so a node keeps its front from far to near and wraps to the far end. The phase walks once round the 30 nodes, so a wrapped front matches its new neighbours | translate y; uniform scale 0.86 → 1.22 with screen y (width 0.95–1.34 px, wobble growing as it nears); shade 1–5 |
| spent foam | 30 | a dome of ≤ 62 points, black fill, step-3 stroke (closed, encloses area) | count by depth, hidden at (640, 320); positions by drift | place, hide |
| voiced dome | 8 | the hemisphere's real contour above the water plus the front half of its waterline, ≤ 62 points, black fill | salt (scale), drift (place), crest (bob) | place, scale |
| voiced waterline | 8 | hairline ribbon of the waterline's front half, step 3 | same pose as its dome | place, scale |
| voiced lit edge | 8 | tapered ribbon, 52 points | same pose; shade from that partial's level | place, scale, shade 4–7 |

- **Totals:** 84 nodes (one draw order: fronts first, then bubbles far to near), 0 texts, 8 palette entries (the stock grey steps). Every path is one subpath with ≤ 62 points.
- **Mutable outlines: 0 of 4.** A mutable outline's points must stay within ±64 px of its origin, and even at scale 2 that's 256 px, so a front can't cross the 480 px body. A front also never needs a new shape: on this camera a front coming toward the viewer is a translation plus a small uniform scale, which is one node change instead of a whole path re-key. The bubbles don't reshape either; salt is a uniform scale. That leaves all four outlines free, which matters if the device check shows a shape is needed (for instance a front that bends round the raft).
- **Suggested `resources.display`:** `paths 0, points 0, nodes 84, texts 0, palette 8`. I haven't written it into `definition.json`, which is still the placeholder `nodes 1, palette 1`. Phase 4 should set it and re-run `lint_definition.py`. `stateBytes` needs room for: 30 snapped front y values, 38 bubble poses with 8 walk angles, 8 edge levels, the front phase, the locked voice and the release level. That's roughly 300–400 bytes, not 4.
- **Whole pixels, with hysteresis.** Bubble poses only redraw when the continuous position has moved more than 0.8 px from the last drawn pixel. Fronts move in whole pixels at swell ≥ 1 s and in 2 px steps below that (at 0.25 s they cross the body as a blur anyway). Edge shades change only when a 6 dB step is crossed. Without the hysteresis, drift 100 cost 17 nodes a frame of pure rounding chatter.

### Redraw (simulated, 60 fps assumed, changed nodes per frame while sounding)

| case | average | peak | still after last note-off | changes once still |
| --- | --- | --- | --- | --- |
| defaults, one note held 6 s | 2.8 | 11 | 0.30 s | 0 |
| defaults, 4-note chord rolled over 0.9 s | 3.9 | 12 | 0.30 s | 0 |
| swell 0 (0.25 s), one note | 7.4 | 17 | 0.47 s | 0 |
| swell 100 (8 s), one note | 1.2 | 9 | 0.07 s | 0 |
| drift 100, one note | 11.4 | 26 | 0.48 s | 0 |
| **heaviest:** swell 0, depth/salt/drift 100, 8 voices | **18.9** | **32** | 1.52 s | 0 |

The heaviest case sits just under the ~20 average. The peak (32) comes from frames where a crest bob and a drift step land together. Rest is zero in every case. A control turn costs every node that control owns for its 0.2 s ease (swell 30, salt 24, drift up to 54), the same as any control turn.

## Perceptibility

`python3 opxy/tools/perceptibility.py` on the 0/50/100 frames (renamed `c1..c4` in a scratch folder), scores from the brief: swell 5, depth 5, salt 3, drift 2:

```
control        score  need %  0→100 %  0→50 %  50→100 %  span
swell              5    2.50    20.44   22.61     11.20   480  ok
depth              5    2.50     2.82    1.61      1.26   444  ok
salt               3    1.20     1.72    1.50      1.15   385  ok
drift              2    0.80     5.00    4.33      4.29   458  ok
note response      —    2.00    15.55       —         —   480  ok
pass
```

The note response compares `rest` with the motion study's second-crest frame (t = +2.32 s). Most of its 15.6 % is the fronts moving on, not the edges brightening. The edge flash alone (step 6 → 7 on the fundamental, 4 → 6 on the small ones, plus a 2 px bob) is only a few hundred pixels and isn't measured separately. Depth passes only just (2.82 against 2.50), and only through its rest channel. Its playing channel (how long the edges hold) isn't something the tool can measure from stills.

## Still pending

- **Device check, all of it.** Nothing here has been on an OP-XY. In particular: whether the 1.1 px fronts at step 1–2 read on the real panel, or vanish or merge; whether the 0.55 px ends of the tapered ribbons draw cleanly (they're flat ends, with points ≥ 0.15 px apart and the closing edge on the longest edge, and lint is clean); whether a step 6 → 7 edge flash is visible at arm's length; and the real redraw cost of 84 nodes at the device's own frame rate (I assumed 60 fps).
- **Perceptibility of the motion** (crest flash, decay length across depth) is judged by eye from `motion.gif` only, not measured.
- **Release timing** uses a stand-in 0.5 s amp release. On SDK 1.10 the fade should be paced from `amp`'s release word (with `envelope_unavailable` treated as the default).
- **Header:** `0.25s` at swell 0 is 5 characters and may overflow 53 px. That's still open from the brief.
- `motion.gif` shows one note at the defaults only. Control turns, chords and the heaviest case are covered by stills and the simulated numbers, not by animation.
