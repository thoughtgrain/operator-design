# Pendula · screen brief

## 0 · Screen or stock page?

- Subject in one sentence: a row of pendulums of slowly different lengths, each playing its note as it crosses the centre, drifting out of phase and back.
- Not the stock page: there's one physical object the rule acts on, and every control changes it (how long they hang, how many, how far they swing, which notes they play). A player on aux track 12 has no stock page that draws anything anyway.

## 1 · Intake

| | |
| --- | --- |
| Machine id | `pendula` |
| Kind | synth + trackControl (`machine.json`: sdk 1.9; `resources.trackControl` with `aux: [12]`, `unique: true`) |
| Category | player |
| Colour | grey (default) |
| Concept | A pendulum wave: pendulums of slowly different lengths each play a note as they cross the centre, drifting in and out of phase. |
| Sounds like | A cluster of notes released together that unravels into rippling arpeggios, ripples, then chords again as the pendulums realign. Pendulum *i* makes K + *i* half-swings per cycle (K = 16), each crossing of the centre sends one note to the target track. |
| Controls | 4: length, count, swing, scale (stock header) |
| Control source | new (the source is the DSP I'm writing) |
| Mute | Mute is the bypass. The control code passes `muted` to the display through `Overlay::display`; every candidate says how its drawing shows it (`muted` in each `candidate.json`). |

### 1A · Definition (new machine)

| source control | range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| period of the longest pendulum | 0.4–4 s, exponential, 1.2 s | 0 | Length | exponential 0.4..4 | duration | 0.4771 | keep | Named for what rises: a longer pendulum, a longer period. Every other pendulum keeps its ratio K/(K + i), so the realign cycle is K × period (19 s at default). |
| pendulums | 3–16, linear, 8 | 1 | Count | linear 3..16 | ratio | 0.3846 | keep | Integer steps; the drawing eases each pendulum in. |
| swing amplitude | 0–100 %, linear, 60 % | 2 | Swing | linear 0..1 | percent | 0.6 | keep | Sets velocity (speed through centre ∝ amplitude) and shortens the gate slightly at the top. 0 % still plays, softly. |
| scale | 6 choices, pent | 3 | Scale | enum pent, major, minor, dor, hira, chrom | enum | 0 (pent) | keep | Longest pendulum takes the root; each shorter one the next degree up. |

Dropped: tempo sync (the run is free, like the real apparatus; the start lines up with the transport), a "drift" (K) control: K is fixed at 16 so the four controls stay what's played. Revisit if the owner wants cycle length on a knob.

Presets: **Wave** (defaults) and **Long drift** (2.5 s, 12 pendulums, 40 % swing, minor).

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/pendula/definition.json` → **0 errors, 0 warnings**, one note (the trackControl reminder to show mute, answered above). `resources.display` is still the 1A placeholder; phase 4 sets it.

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | yes | length (longer period), count (more), swing (wider), scale (enum, order runs sparse to dense: pent → chrom) |
| Header values in real units, ≤ ~5 chars | yes, one pending | seconds, a count, a percentage, a scale name; the 5-letter scale names need measuring (Captions) |
| Defaults plainest useful; presets sound good (by ear) | yes / pending ear | pentatonic, eight pendulums, never dissonant at default; by ear pending |
| Engine page holds only the sound's own parameters | yes | no envelope or LFO; the target track's own engine shapes the notes |
| Page 1 holds what's played most | yes | one page |
| Port parity | n/a | new machine |
| Saved sounds compatible | n/a | not released |
| `id` final | yes | `pendula` |

### Captions

| # | label (≤ 8, lower) | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | length | 0.4–4 | s | 1.2 s | `0.4s` / `1.3s` / `4.0s` (stock duration format) | 51 px | yes, pending the stock format |
| 2 | count | 3–16 | — | 8 | `3` / `10` / `16` | 26 px | yes |
| 3 | swing | 0–100 | % | 60 | `0` / `50` / `100` | 38 px | yes |
| 4 | scale | 6 names | — | pent | `pent` / `dor` / `chrom` (also `major`, `minor`, `hira`) | 51–64 px | `pent`, `dor`, `hira` yes; `major`, `minor`, `chrom` est. 64 px: **pending device** (enum values may draw smaller, as in meikyu's header) |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device.

## 2 · Listen and rank

Scored from the DSP, to confirm by ear.

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 length | Ten times slower from 0 to 100: the note rate and the speed of the drift both follow it. Dramatic. | 5 |
| 2 count | 3 to 16 voices: density and pitch range (pentatonic: under an octave to over three). Big. | 4 |
| 3 swing | Velocity of every note, plus slightly shorter gates near 100. Clear, but the pattern stays the same. | 3 |
| 4 scale | Changes the pitch set, not the rhythm; pent → chrom is a big colour change, neighbours are subtle. | 3 |

## 3 · Subject

Five candidates from the directions in `passes/01-subject/pass.json`; sketches and per-control sentences in `passes/01-subject/v1…v5/`. Uniqueness: `design_pass_submit` → ready_for_pick. Rest everywhere is the moment before release: transport stopped, every bob held at the same release point, no notes.

| candidate | pattern | drawing language | subject in one sentence | what each control moves | verdict |
| --- | --- | --- | --- | --- | --- |
| v1 | P13 Capture | typeset diagram | Every pendulum from one pivot on nested swing arcs; the plumb line is the gate that captures a crossing bob. | length: arc radius (scale) · count: arcs · swing: opening angle θ (rotation) · scale: pitch-class polygon | see notes.md |
| v2 | P14 Loom | orthographic elevation | Front elevation; strings run on into a woven cloth where each crossing of the last four beats is a slab. | length: drop (position) · count: threads · swing: bob lift + slab height · scale: thread spacing by interval | see notes.md |
| v3 | P5 Field and figure | survey plan | Overhead plan: row along a datum, a release board holding every bob on one line, scale ruler as the strip. | length: lane span · count: lanes · swing: bob symbol size · scale: strip ticks | see notes.md |
| v4 | P12 Orrery | patent section | Conical pendulums on one spindle, orbits as an orrery, the section plane A–A as the gate. | length: cone drop (scale) · count: orbits · swing: cone angle · scale: base dial ticks | see notes.md |
| v5 | P6 Figures (stretch) | hidden-line isometric | A swing set with a block rider per seat whose feet strike a tuned bar at the bottom. | length: chain drop · count: riders · swing: hold-back angle · scale: bar lengths | see notes.md |

Chosen: **the owner's pick** (pending).
