# Rain · screen brief

## 0 · Screen or stock page?

- Subject in one sentence: a roof of pitched tiles in the rain, where each tile course is a note, each drop that lands plays the course it hits, the wind pushes the drops across the courses, and the gutter holds the last notes to replay them.
- Not the stock page: rain is a track-control player (SDK 1.9, aux track 12), and the stock player page is 24 on/off dots that bind no nodes. There is one scene the rule acts on (the roof), and every control changes something in it (how many drops, how many courses, where the wind sends them, how full the gutter is).

## 1 · Intake

| | |
| --- | --- |
| Machine id | `rain` |
| Kind | synth + `resources.trackControl` (SDK 1.9, aux track 12, unique) |
| Category | player |
| Colour | grey (default) |
| Concept | Raindrops on a roof of pitched tiles: drops fall at a rate, gusts push them across, puddles repeat the last notes. |
| Sounds like | Rain has no sound of its own: it plays another track. At low rate it's a sparse, irregular drip of notes from a scale; turned up it becomes a dense patter, and a strong gust turns the scatter into runs that walk up or down the tiles. A full puddle makes the last few notes come back as uneven echoes, so phrases repeat and then dissolve. |
| Controls | 4: rate, roof, gust, puddle |
| Control source | new (the source is the control code I'm writing: a Poisson drop clock, a scale-quantised pitch walk over the roof's span, and a short note memory for the puddle) |
| Mute | Mute is the machine's bypass (`ux.md`, Aux tracks): the page must show it. `control::Input.muted` goes to the display through `Overlay::display`; every candidate says what its muted state looks like |

### 1A · Port map (new machine: the player's own controls)

| source control | source range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| drop rate (mean drops per beat, Poisson spacing) | 0.25..8 per beat, exponential, 1.0 | 1 | rate | exponential 0.25..8 | ratio | 0.4 (1.0 per beat) | keep | Exponential so each quarter of the knob roughly doubles density. Shown as drops per beat |
| roof span (pitch range the tile courses cover, scale-quantised) | 0..36 st, linear, 12 | 2 | roof | linear 0..36 | semitones | 0.3333 (12 st) | keep | 0 = a flat roof: every drop the same note. Courses are the scale's notes inside the span |
| gust (pitch-walk bias: drops pushed across the courses) | −1..+1, linear, 0 | 3 | gust | linear −1..1 | bipolar | 0.5 (0) | keep | 0 = still air, drops land at random; + pushes them up the roof (rising runs), − down |
| puddle (chance a drop replays from the last-notes memory, and that memory's depth) | 0..1, linear, 0 | 4 | puddle | linear 0..1 | percent | 0 | keep | 0 = dry: nothing repeats, the plainest setting |
| scale / root | — | — | — | — | — | — | drop | The target track's key and the project scale cover this; four controls are the concept's four |
| note length, velocity | — | — | — | — | — | — | drop | Fixed short gate, velocity from a light random spread; the target track's envelope shapes the sound |

Integer conversion: none (new machine, float control code).

`trackControl`: `stateBytes 256` (drop clock, walk position, puddle memory of 16 notes), `savedBytes 64` (the puddle memory survives a pattern switch), `aux [12]`, `unique true`. `resources.display` is the placeholder (`stateBytes 4, nodes 1, palette 1`) until phase 4. Voice resources are nominal: the track is silent.

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/rain/definition.json` → 0 errors, 0 warnings (one note: show the muted state, which is carried in the intake row above). Nothing to justify.

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | pass | rate (drops per beat), roof (span), gust (push, bipolar: clockwise pushes up the roof), puddle (repeat amount) all rise clockwise |
| Header values in real units, ≤ ~5 chars | pass, with a note | rate in drops per beat (ratio), roof in semitones, gust bipolar −100..+100, puddle percent. `ratio`'s rounding (1.0 vs 1.00) and `+100` need measuring in the device font |
| Defaults plainest useful; presets sound good (by ear) | pass by design, **pending ear** | One drop a beat over an octave, still air, dry gutter. Presets Drizzle (defaults), Squall (4 a beat, 2 octaves, gusty, a little puddle), Eaves (slow drip, narrow, deep puddle) |
| Engine page holds only the sound's own parameters | pass | No envelope or LFO; all four are the rule's own |
| Page 1 holds what's played most | pass | One page, four controls |
| Port parity: nothing silently lost | pass | New machine; dropped scale/root and note length listed above |
| Saved sounds compatible (if released) | n/a | Unreleased |
| `id` final | pass | `rain` |

### Captions

| # | label (≤ 8, lower) | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | rate | 0.25..8, exponential | drops per beat (ratio) | 0.4 | 0.25 / 1.41 / 8.00 | 4 × 12.8 = 51 px | yes, tight |
| 2 | roof | 0..36 | semitones | 0.3333 | 0 / 18 / 36 | 2 × 12.8 = 26 px (`+36`: 38 px) | yes |
| 3 | gust | −1..+1 | bipolar | 0.5 | −100 / 0 / +100 | 4 × 12.8 = 51 px | yes, tight |
| 4 | puddle | 0..1 | percent | 0 | 0 / 50 / 100 | 38 px | yes |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device (rate's `0.25`/`8.00` and gust's `−100`).

Page 1 (played most): rate, roof, gust, puddle · Page 2: none · Repeated controls: none.

## 2 · Listen and rank

Scored from the DSP, to confirm by ear. (Rain's "DSP" is its control code: scores judge how much the played notes change across 0 → 100.)

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 rate | A drop every four beats to eight a beat: from sparse drip to a dense patter, the biggest change in how much is played | 5 |
| 2 roof | One repeated note at 0 st to a three-octave scatter at 36: the melody's whole range; clear from about 3 st up | 4 |
| 3 gust | Still air at 0 (random landing); toward ±100 the scatter turns into rising or falling runs. Audible as direction more than as density | 3 |
| 4 puddle | Nothing at 0; from ~30 phrases start coming back; at 100 most notes are replays and the line loops before it dissolves | 3 |

## 3 · Subject

Five candidates, one per direction in `passes/01-subject/pass.json` (state `ready_for_pick`, every pair differs in pattern and language, subject overlap ≤ 0.14). Sketches: `passes/01-subject/v1…v5/rest.svg`, generator `passes/01-subject/sketch.py`, notes in `passes/01-subject/notes.md`.

| candidate | pattern | drawing language | subject in one sentence | what each control moves | verdict |
| --- | --- | --- | --- | --- | --- |
| v1 | P12 Orrery | survey plan | A round pavilion roof surveyed from above: tile courses are orbits round the finial, drops sit on their course like planets, the gutter is the puddle's orbit | rate: drop count · roof: ring count · gust: drops turn round the finial · puddle: beads on the gutter | candidate |
| v2 | P13 Capture | patent section | A mono-pitch roof in patent section: the course that catches a drop plays it, the gutter's water level is how much replays | rate: streak count · roof: pitch angle · gust: streak slant · puddle: water level | candidate |
| v3 | P14 Loom | hidden-line isometric | The roof is the loom: tile columns are warp threads, each bar weaves a row at the eave and older bars climb to the ridge; struck tiles stand as slabs | rate: slabs per row · roof: thread count · gust: row shear · puddle: solid (repeated) columns | candidate |
| v4 | P5 Field and figure | star atlas | The rain as a meteor shower on a star chart: the roof is a constellation of course stars, drops are trails back to a radiant the gust slides along the sky | rate: trail count · roof: ridge star height · gust: radiant position · puddle: open cluster | candidate |
| v5 | P9 One-bit ink (stretch) | engineering schematic | A gable roof in one-bit ink with dithered courses, wired schematic-style to rain, wind and puddle glyphs | rate: streak count · roof: gable pitch · gust: wind strokes and lean · puddle: plane scale | doesn't fit (a picture of the setting, not the rule) |

Chosen: pending the owner's pick.
