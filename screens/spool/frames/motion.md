# Spool · motion

A spool of thread sits on a table and rolls while a note sounds. Each revolution lays one more repeat of the written cycle in thread behind it, and the laid trail slides off the left edge of the screen.

Everything below comes from `frames/build.py`. It's one 3D model seen through one camera, and it writes the stills, `contact.png`, `motion.gif` and `motion-sheet.png`, and prints the redraw it measured.

## What changed from pass 02 v1

- **Camera.** The camera is now low (about 15° above the table) and in front, turned about 20° toward the trail. The near flange faces us on the right with its hub, bore and three lightening holes. The winding and the far flange show to its left. The trail lies along the table and leaves through the left edge at about y 195, well clear of the header: the top of the spool is at y ≈ 50 and nothing goes above that. The trail comes slightly toward the camera as it runs left. That's the price of seeing the winding, because from a camera on the other side the near flange covers the point where the thread comes off the winding.
- **Line weights.** I dropped v1's single weight and went back to craft.md's three weights. The thread is now the subject weight: two 1.5 px plies 0.4 px apart, which reads as one ~1.9 px line. The spool's contours are Line (1.5 px, `#7D7D7D`) and the turns on the winding are Hairline (1.0 px, `#4B4B4B`). At 1:1 the single-weight version left the thread no heavier than the spool, so the eye had nothing to land on. Wear also needs the thread to have some body: at 1.5 px, no change to the thread alone could reach wear's 2.5 % floor (I measured 1.1–1.6 % with every shape change I tried).
- **The brightest thing.** The thread is the only `#CDCDCD`. The body is 95–96 % black in every frame. There's no text below the header and no grey-filled states.

## Interactions

Rates are what the screen shows. One revolution is one pass of the loop, but the screen shows at most 1.25 revolutions per second, so the eye can follow it and the holes don't strobe. With a loop of 0.8 s or longer, one revolution is exactly one pass. Shorter loops still turn at 1.25 rev/s, and each revolution stands for `1/length ÷ 1.25` passes. At the default 0.32 s that's 2.5 passes per revolution, and that's how many passes of wear each laid repeat carries. So a short loop's trail wears faster per repeat, just as the sound wears faster in time.

| trigger | what moves | from → to, timing | reduced motion / track change |
| --- | --- | --- | --- |
| **note on** | A fresh write. A new repeat starts at the laying point, crisp and `#CDCDCD`, spliced onto whatever the last note left. The spool spins up on an exponential ease (τ 60 ms, settled in ~0.18 s) to `min(1/length, 1.25)` rev/s | rest → rolling | no roll; the fresh repeat appears in place |
| **roll (held)** | Treadmill: the spool turns in place and the three holes travel round the near flange's face, clockwise, one turn per revolution. The trail slides left at one wavelength per revolution and exits the left edge. Each new repeat is laid one revolution's worth of passes more worn than the last, so the darkening sound shows up as the thread dulling repeat by repeat out of the spool | continuous while held | the trail steps one repeat per pass, the holes stay put |
| **wear** (5) | The thread on the table is a record of the note. The repeat laid on pass P has lost `s = 1 − (1 − 0.35·wear)^P` of its highs: harmonic h is scaled by `(1 − s)^(0.8(h−1))`, so corners round off toward a sine, and its level drops by `0.58·s`. The plies loosen, parting by up to 3.2 px between twist crossings, and at two dropouts per repeat they open up to 4.2 px wider (dropouts begin once `s > 0.25`). The thread's grey steps down `#CDCDCD → #AFAFAF (s ≥ 0.3) → #969696 (s ≥ 0.62)` along with the shape (never shade alone). At wear 0 nothing ever wears | knob turn: 0.15 s ease, then still | jump |
| **wow** (3) | Static: every repeat is laid with a once-per-revolution time warp, so each laid phase follows `u + 0.9·wow/2π · sin 2π(u − 0.3)`. The ramps lean and the steps bunch, the same way in every repeat, because wow is once per revolution. Moving: the spool's rate swings `±32 %·wow` once per revolution, the holes surge and lag, and the free run's slack breathes ±0.22·wow with it | 0 → 100 over the knob | rate steady, no breathing |
| **length** (2) | The wavelength of a laid repeat runs from about 7 repeats across the frame at 0.05 s to about 2 at 2.0 s, more than doubling. It also sets the roll rate below 0.8 s (see above) and how many passes of wear each repeat carries | 0.15 s ease | jump |
| **bias** (4) | Tension in the free run between the winding and the trail. Under-biased (−100), it's one taut straight line from the top of the winding down to the trail. Over-biased (+100), it falls almost at once to the table and lies in a loose bow toward us before the trail starts. Secondary, on the trail: under-biased repeats are 35 % taller and clip flat (saturating hard); over-biased ones are 38 % lower and duller (they lose more highs) | 0.15 s ease | jump |
| **chord** | Each new key is another fresh write (another splice, the newest repeat crisp again). With two or more keys held the plies sit 0.9 px apart instead of 0.4, so the thread reads ~2.4 px instead of ~1.9: still within the subject weight, and no extra nodes. The roll doesn't change, because every voice shares one loop length | on the key | same, without the roll |
| **note off / release** | The spool coasts. Its rate decays as `exp(−t/(release/3))`, and below 0.0015 rev/frame it stops dead. With the 0.45 s release I assumed, that's still about 0.6 s after the note-off. On SDK 1.10 the coast follows `amp`'s release; before that it's a fixed 0.45 s. The note-off is stock's gate, not the end of the sound, so the coast is a pacing choice | rolling → still | stop at once |
| **rest** | Nothing moves. The trail stays as the last note left it | 0 changed nodes | — |

The static frames (`rest`, `<control>-0/50/100`) show the record of one note held until its first repeat has just left the left edge. That way each frame shows wear's gradient, from the least worn at the left to the most worn at the spool. `playing` is 2.4 revolutions into a fresh note.

## Node plan and budget

| node | part | how it changes | |
| --- | --- | --- | --- |
| 0–2 | trail, three chunks (spool end, middle, left edge), each ≤ 124 px wide around its origin | **mutable**, 64 points, hollow ribbon (`fill="none"`, 1.5 px stroke); re-keyed every frame while rolling, and on any control turn | paint `#CDCDCD/#AFAFAF/#969696` by wear |
| 3 | free run | **mutable**, 64 points; re-keyed on bias, while wow breathes, when the current pass's wear changes and on a chord | same |
| 4 | far flange | static | `#7D7D7D` 1.5, black fill |
| 5 | winding | static | same |
| 6–9 | turns of thread on the winding | static, 1 px filled ribbons | `#4B4B4B` |
| 10, 11 | near flange rim and face | static | `#7D7D7D` 1.5, black fill |
| 12, 13 | hub, bore | static | `#4B4B4B` / `#7D7D7D` |
| 14–16 | lightening holes | **translate only**. A circle on the flange face projects to the same ellipse anywhere on it, so `display()` moves each origin round the projected face and never reshapes or turns it | `#7D7D7D` 1.5, black fill |

All 4 mutable outlines are used, each with 64 points. Proposed `resources.display`: `paths 4, points 64, nodes 17, texts 0, palette 6` (`#CDCDCD #AFAFAF #969696 #7D7D7D #4B4B4B #000000`). I haven't written it into `definition.json`; that's phase 4's change.

**Redraw**, measured by `build.py`, which diffs every node's origin, points and paint frame to frame through the motion score:

- **Playing at Attic** (wear 38, wow 35, 0.20 s, bias −40): 7 changed nodes per frame on average, peak 7. That's 3 trail re-keys, the free-run re-key and 3 hole moves.
- **At the heaviest setting** (wear 100, wow 100, 0.05 s, bias +100, two keys): also 7 average, peak 7.
- **With wow at 0**, the free run only re-keys when a pass changes its wear, so it's 6.
- **At rest, after the coast:** 0.

That's well under ~20 as a count of nodes, but four of the seven are 64-point re-keys every frame, which costs more than a move. How much more is a **device** question.

## Perceptibility

`perceptibility.py` on the 0/50/100 frames, with the scores from the brief (wear 5, wow 3, length 2, bias 4), `--header-bottom 20`:

```
control        score  need %  0→100 %  0→50 %  50→100 %  span
wear               5    2.50     2.92    2.27      2.78   342  ok
wow                3    1.20     2.76    2.48      2.54   341  ok
length             2    0.80     3.26    3.49      2.76   341  ok
bias               4    1.60     2.38    2.13      2.42   352  ok
note response      —    2.00     3.47       —         —   440  ok
pass
```

Wear only clears its floor because the rest record starts just past the left edge. In an earlier tuning, with the first, unworn repeat still on screen, it came in under (about 2.4 %). Lint (`lint_frame.py --paths 4`): 0 errors, 0 warnings on all 14 frames, no `text-in-drawing`.

## Pending

- **Device:** everything is unchecked on the device. It needs a photo of the real screen at 1:1. In particular:
  - Do the two plies 0.4 px apart draw as one clean line on the panel, or do they streak?
  - What do four 64-point re-keys a frame cost?
  - Is document order the paint order for bound nodes? I've assumed the trail and free run are painted after the far flange and winding, and before the near flange.
- **Header:** `0.32s` fits in the device font (carried over from the brief).
- **Reduced motion and `display_reset`** are specified above, but no frames have been drawn for them.
- **No video with sound;** that would be the optional phase 6 preview.
