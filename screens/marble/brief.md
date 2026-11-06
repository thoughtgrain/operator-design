# Marble · screen brief

## 0 · Screen or stock page?

- Subject in one sentence: marbles dropping from a hopper through rows of pegs into bins pitched on a scale, where the pile they build is the distribution of notes the machine plays; the screen draws that board or its pile (which object carries it is the subject pass's question, `passes/01-subject/`).
- Not stock: a track-control player has no stock page that binds nodes, and there is one rule every control acts on (rows, rate, rebound and the bins' pitches), so a custom screen can meet "one subject, every control reads". It must also show when the track is muted (mute is the player's bypass).

## 1 · Intake

| | |
| --- | --- |
| Machine id | `marble` |
| Kind | synth + trackControl (`resources.trackControl`, aux track 12, `sdk` 1.9) |
| Category | player |
| Colour | grey (default) |
| Concept | A Galton board: marbles drop through pegs into pitched bins; peg spacing shapes the distribution of notes. |
| Sounds like | Nothing itself: it runs on aux track 12 (kept silent) and plays the target track. Few rows give a melody that hugs the root, many rows a wandering line with rare wide leaps, always weighted to the middle like a bell. |
| Controls | 4: pegs, drop, bounce, scale (stock header) |
| Control source | new (the "source" is the player logic below; no port) |

Player logic as designed: every drop interval (`drop`, a tempo division) one marble leaves the hopper and passes `pegs` rows; at each row it goes left or right with even odds. It lands in bin k = number of rights (0..rows), which is the scale degree k − rows/2 around the held or last played root, in `scale`. The note goes to the target track. `bounce` is the chance the marble rebounds in its bin and strikes again: up to three retriggers of the same note, each quieter and sooner than the last (a bouncing-ball ratchet). Muted (the aux track's bypass): no marbles drop.

### 1A · Port map (new machine: source = the logic above)

| source control | source range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| peg rows | 1–12, integer | 0 | Pegs | enum "1".."12" | enum | 0.4545 (index 5 → 6 rows, 7 bins) | keep | Rows set the width of the bell: 1 row is root or one degree up; 12 rows reach six degrees either side |
| drop interval | tempo divisions | 1 | Drop | linear 0..1 | division | 0.5 (1/8 on the host's division table, pending device) | keep | Division display requires linear 0..1; the host owns the steps |
| rebound chance | 0–100 %, linear | 2 | Bounce | linear 0..1 | percent | 0 | keep | Ornament: defaults off |
| scale | major, minor, pent, blues, whole, chrom | 3 | Scale | enum | enum | 0 (major) | keep | Labels ≤ 5 chars; "dorian" was dropped to keep the header width (lint warning), blues takes its slot |

Presets: **Plinko** (the defaults: 6 rows, 1/8, no bounce, major) and **Cascade** (12 rows, ~1/16, 35 % bounce, pent).

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/marble/definition.json` → 0 errors, 0 warnings (one note: show the muted state, passing `control::Input.muted` through `Overlay::display`). The one warning seen on the way (`dorian`, 6 characters, over the header column) was fixed by replacing it with `blues`.

`resources.display` is a placeholder (2 paths × 64 points, 96 nodes, 6 palette) until phase 4. `voiceCapacity` 8 is kept to match a synth's usual declaration even though track 12 is silent; it avoids the low-capacity warning and costs nothing audible.

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | pass | more peg rows, faster drops, more bounce; scale is an enum, ordered roughly from fewest accidentals outward |
| Header values in real units, ≤ ~5 chars | pass, pending device | `6`, `1/8`, `0`, `major` (5 chars, 64 px estimated: the one tight caption) |
| Defaults plainest useful; presets sound good (by ear) | pass by design, pending ear | bounce 0; 6 rows in major is a calm, root-centred line |
| Engine page holds only the machine's own parameters | pass | all four are the board's own |
| Page 1 holds what's played most | pass | one page |
| Port parity | n/a | new machine |
| Saved sounds compatible | n/a | unreleased |
| `id` final | pass | `marble` |

### Captions

| # | label (≤ 8, lower) | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | pegs | 1–12 | rows | 6 | 1 / 6 or 7 / 12 | 2 chars, 26 px | yes |
| 2 | drop | host divisions | division | 1/8 | host's slowest / 1/8 / host's fastest | 3–4 chars, 38–51 px | yes, pending device |
| 3 | bounce | 0–100 | % | 0 | 0 / 50 / 100 | 3 chars, 38 px | yes |
| 4 | scale | 6 scales | enum | major | major / pent or blues / chrom | 4–5 chars, 51–64 px | tight for `major` and `blues`, `chrom`; pending device |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device.

Page 1 (played most): all four · Page 2: none · Repeated controls: none.

## 2 · Listen and rank

Scored from the DSP, to confirm by ear. (Marble makes no sound of its own; "audible" means what changes in the notes it plays on the target track.)

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 pegs | from a line pinned to the root and its neighbour to a wide, wandering line with rare far leaps: the whole melodic range | 5 |
| 2 drop | from one note a bar to a 1/32 stream: the density of the part, the biggest change you hear | 5 |
| 3 bounce | none at 0; ratcheted repeats on more and more notes as it rises, clear but an ornament on the same pitches | 3 |
| 4 scale | changes which pitches sound but not the contour or rhythm; major to minor is subtle, whole and chrom are obvious | 3 |

## 3 · Subject

Five candidates, one per direction in `passes/01-subject/pass.json`; candidates and sketches in `passes/01-subject/v1…v5/`, notes in `passes/01-subject/notes.md`. Uniqueness submitted: `ready_for_pick` (every pair differs in pattern and language; subject overlap at most 0.13).

| candidate | pattern | drawing language | subject in one sentence | what each control moves | verdict |
| --- | --- | --- | --- | --- | --- |
| v1 | P14 Loom | engineering schematic | The last four bars woven as cloth: bins are warp threads, bars are rows, landed marbles are slabs on their thread | pegs: thread count · drop: slab heights · bounce: rebound cap position · scale: thread positions | candidate |
| v2 | P5 Field and figure | oscilloscope trace | Each note's odds as a bright stepped trace over a scope graticule, drops ticking in a strip | pegs: trace shape · drop: strip count · bounce: channel-2 trace scale · scale: pulse positions on the pitch axis | candidate |
| v3 | P12 Orrery | typeset diagram | A radial board as an orrery: hopper sun, peg-row orbits, bins as planets round the pitch circle | pegs: orbit count · drop: waiting-marble count · bounce: moon count · scale: planet positions | candidate |
| v4 | P13 Capture | orthographic elevation | The board itself in front elevation, bins cut as pipes to their pitch, the captured pile is what plays | pegs: row count · drop: gate aperture · bounce: rebound dimension · scale: floor heights | candidate |
| v5 | P3 Trace as subject (stretch) | survey plan | One marble's fall surveyed as a traverse through peg stations to a lot laid out by pitch | pegs: leg count · drop: chain pegs · bounce: rebound spur · scale: lot positions | candidate, weak fit |

Chosen: pending, the owner's pick.
