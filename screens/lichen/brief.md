# Lichen · screen brief

## 0 · Screen or stock page?

- Subject in one sentence: a colony of lichen growing across a lattice of scale degrees, spreading at its margin and dying back at its old centre, where each cell it newly takes is the note that plays.
- It earns a screen: the machine's rule is a spatial process on one object (the lattice and the colony on it), and every control changes what that colony does (how fast it spreads, how soon it dies, where new spores land, which pitches the lattice holds). The stock player page is 24 dots and binds no nodes, so this runs as a track-control synth on aux track 12 (SDK 1.9) with its own page on M1.

## 1 · Intake

| | |
| --- | --- |
| Machine id | `lichen` |
| Kind | synth + trackControl (SDK 1.9, aux track 12, unique) |
| Category | player |
| Colour | grey (default) |
| Concept | A growth automaton on a scale lattice: cells grow into neighbours and decay; new growth plays. |
| Sounds like | A melody that creeps outward from wherever it started, in short runs of steps and thirds, thickening as the colony spreads and thinning as its centre dies; it plays another track's instrument. Low decay builds long slow phrases that settle into one region of the lattice; high decay gives scattered flickering bursts. |
| Controls | 4: grow, decay, seed, scale (stock header) |
| Control source | new (the rule sketched below; no port) |

The page must show when the track is muted (mute is a track-control machine's bypass): the control code passes `muted` to the display in its `Overlay::display` words, and every subject candidate says what it does then.

### 1A · Definition (new machine; "source" is the rule)

The rule, as `passes/01-subject/sketch.py` models it: an isomorphic scale lattice of 12 columns × 6 rows, odd rows set half a cell right (a hex lattice). Right is the next scale degree, up-left one degree, up-right two (a third), so a cell's degree is `col − floor(row / 2) + 2·row` (degrees 0..19, about three octaves). Each cell has six neighbours. The clock is the project's 1/16; the colony starts from one spore at (6, 2).

| source control | range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| spread chance | 0..1 linear, 0.35 | 0 | grow | linear 0..1 | percent | 0.35 (35) | keep | each tick each living cell takes one free neighbour with this chance; at most 2 births a tick (they are the notes, so the rhythm can't flood the target track) |
| death chance | 0..1 linear, 0.2 | 1 | decay | linear 0..1 | percent | 0.2 (20) | keep | a living cell of age `a` dies with chance `decay · a / 8`, so old crust goes first and the colony hollows out; dead crust can't regrow for 5 ticks |
| spores per bar | 0, 1, 2, 3, 4, 6, 8 | 2 | seed | enum | enum | 1/6 (1) | keep | spores land on random empty cells on the bar's beats; at 0 a colony that dies out stays silent until a note on the target restarts it |
| scale | maj min dor phr lyd mix pent pmin | 3 | scale | enum | enum | 0 (maj) | keep | which semitones the degrees sit on; root follows the project key |
| birth cap | fixed 2 a tick | — | — | — | — | — | fixed | a polyphony and taste limit, not a knob |
| regrowth delay | fixed 5 ticks | — | — | — | — | — | fixed | it's what makes the dead centre visible as a ring; a knob would be a second decay |

Presets: **Crust** (defaults), **Bloom** (grow 70, decay 40, seed 2, pent), **Relic** (grow 15, decay 5, seed 1, dor).

Resources: `trackControl.stateBytes` 128 (72 cell ages as bytes, the RNG, the clock phase and the birth list), `savedBytes` 48 (the colony packed 4 bits a cell + start cell), `aux [12]`, `unique`. Voice resources are the minimal synth contract (its own track stays silent). `display` is the phase-1A placeholder (1 node, 1 palette entry); phase 4 sets it.

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/lichen/definition.json` → 0 errors, 1 warning (plus the trackControl note, answered above under Intake).

| warning | resolution |
| --- | --- |
| `engine-scope`: 'Decay' looks like an envelope/LFO control | Justified: it's the colony's death rate, part of the rule that picks notes, not an amplitude envelope. The OP-XY's envelope page acts on the target track's sound; nothing stock does what this does. The label stays because the concept names it. |

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | pass | grow: more spreading; decay: more dying; seed: more spores; scale: steps through the list (an enum, as meikyu's Scal) |
| Header values in real units, ≤ ~5 chars | pass / **pending device** | percents `0`..`100`, spore counts `0`..`8`, scale names ≤ 4 characters |
| Defaults plainest useful; presets sound good (by ear) | pass / **pending device** | defaults: a slow major colony from one spore; presets to confirm by ear |
| Engine page holds only the sound's own parameters | pass | all four are the rule's own; see the decay warning |
| Page 1 holds what's played most | pass | one page, four controls |
| Port parity: nothing silently lost | n/a | not a port; fixed rule settings listed above |
| Saved sounds compatible (if released) | n/a | unreleased |
| `id` final | pass | `lichen` |

### Captions

| # | label (≤ 8, lower) | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | grow | 0..100 | % | 35 | `0` / `50` / `100` | 38 px | yes |
| 2 | decay | 0..100 | % | 20 | `0` / `50` / `100` | 38 px | yes |
| 3 | seed | 0..8 | spores per bar | 1 | `0` / `3` / `8` | 13 px | yes |
| 4 | scale | 8 names | — | maj | `maj` / `lyd` / `pmin` | 38–51 px | yes (`pmin`/`pent` at 51 px are tight; **pending device**) |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device.

Page 1 (played most): grow, decay, seed, scale · Page 2: none.

## 2 · Listen and rank

Scored from the DSP, to confirm by ear.

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 grow | note density: at 0 the colony never spreads and only spores play (about one note a bar); at 100 two notes nearly every tick. The biggest change on the page | 5 |
| 2 decay | phrase life: at 0 the colony fills the lattice and then falls silent (nowhere left to grow); at 100 cells die within a few ticks and the melody comes in short scattered bursts | 4 |
| 3 seed | where phrases restart: subtle while the colony is alive (one new start a bar at the default), decisive when it dies out; at 8 the register jumps every half beat | 2 |
| 4 scale | harmony without changing rhythm: seven-note modes differ by one or two notes, the pentatonics clearly soften it | 3 |

## 3 · Subject

Five candidates, one per direction handed out for this pass. Pass record: `passes/01-subject/pass.json` (state `ready_for_pick`); candidates in `passes/01-subject/v1..v5/candidate.json`; sketches `passes/01-subject/v1..v5/rest.svg` (and `rest.png`), all generated by `passes/01-subject/sketch.py` from one colony model at the same tick; notes and a designer's ranking in `passes/01-subject/notes.md`.

| candidate | pattern | drawing language | subject in one sentence | verdict |
| --- | --- | --- | --- | --- |
| v1 | P12 Orrery | engineering schematic | the lattice's rows as orbits round a root sun, cells as planets, the colony a cluster that goes hollow as it dies | see notes |
| v2 | P13 Capture | oscilloscope trace | the colony's growth front as one bright closed trace on a graticule lattice, the dead centre an afterglow inside it | see notes |
| v3 | P14 Loom | typeset diagram | the last four ticks woven as cloth, one thread per scale degree, new growth capped bright | see notes |
| v4 | P5 Field and figure | orthographic elevation | a running-bond wall (one stone per cell) with the lichen as one lobed patch, cracked dead centre, growth strip at the foot | see notes |
| v5 | P2 Diagram + trace (stretch) | survey plan | plan of the lattice with the colony run as a traverse, beside a levelled profile of the pitches it played | weak fit, see notes |

Chosen: **pending the owner's pick.**
