# Drill · screen brief

## 0 · Screen or stock page?

- Subject in one sentence: a toothed wheel, turned by the oscillator at a set ratio, whose teeth a follower reads, so the read phase steps forward tooth by tooth and bends the wave.

## 1 · Intake

| | |
| --- | --- |
| Machine id | `drill` |
| Kind | synth |
| Category | engine |
| Colour | grey (default) |
| Concept | Phase distortion driven by a gear train: the read phase is bent by a toothed wheel whose ratio and wear shape the timbre. |
| Sounds like | A sine at bite 0 that grows a stepped, buzzy edge as bite rises, its formant-like peak sweeping with ratio the way a CZ resonance sweep does. Few sharp teeth give a coarse, gritty grind; many teeth or heavy wear smooth it back toward a rounder, darker tone. |
| Controls | 4: ratio, teeth, wear, bite (stock header) |
| Control source | new |

The DSP the scores below are taken from (also in `passes/01-subject/sketch.py`): the wheel turns `ratio` times per oscillator cycle (`w = ratio · phase`); its teeth step that turn (`s = (floor(w·T) + edge(frac(w·T), wear)) / T`); bite mixes the read toward the steps (`p = w + bite · (s − w)`); out is `sin(2π p) · (1 − phase)`, a CZ-style window that keeps the note's pitch whatever the ratio.

### 1A · Port map

New machine; no source to port. The definition is drafted from the DSP above.

| source control | source range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| wheel turns per cycle | 0.5–8, log | 0 | ratio | exponential 0.5–8 | ratio | 0.5 (2.00) | keep | 2.00 is the plainest useful setting: one clear resonant hump pair, no beating |
| teeth on the wheel | 3–24, integer | 1 | teeth | enum "3".."24" | enum | 0.15 (6) | keep | 0.15 sits inside index 3 under either rounding or flooring of the enum |
| tooth wear (edge rounding + unevenness) | 0–1, linear | 2 | wear | linear 0–1 | percent | 0 | keep | colouring control, so it defaults off |
| follower depth | 0–1, linear | 3 | bite | linear 0–1 | percent | 0.35 | keep | 0 is a pure windowed sine; 35 % is audibly the machine without being harsh |

Presets: `Clean` (the defaults) and `Grind` (ratio 1.00, teeth 4, wear 40 %, bite 80 %).

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/drill/definition.json` → 0 errors, 0 warnings. `resources.display` is a placeholder until phase 4.

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | yes | ratio, teeth, wear and bite each rise with the number shown |
| Header values in real units, ≤ ~5 chars | yes, pending device | `2.00`, `6`, `0%`, `35%`; the device's `ratio` format for values over 1 needs checking in the font |
| Defaults plainest useful; presets sound good (by ear) | pending device | defaults chosen from the DSP; presets not heard yet |
| Engine page holds only the sound's own parameters | yes | no envelope, LFO or mod amount |
| Page 1 holds what's played most | yes | one page |
| Port parity: nothing silently lost | n/a | new machine |
| Saved sounds compatible (if released) | n/a | unreleased |
| `id` final | yes | `drill` |

### Captions

| # | label (≤ 8, lower) | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | ratio | 0.5–8 | ratio | 2.00 | 0.50 / 2.00 / 8.00 | 4 × 12.8 = 51 | yes, just |
| 2 | teeth | 3–24 | count | 6 | 3 / 14 / 24 | 2 × 12.8 = 26 | yes |
| 3 | wear | 0–100 | % | 0% | 0% / 50% / 100% | 4 × 12.8 = 51 | yes, just |
| 4 | bite | 0–100 | % | 35% | 0% / 50% / 100% | 4 × 12.8 = 51 | yes, just |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device.

Page 1 (played most): ratio, teeth, wear, bite · Page 2: none · Repeated controls: none.

## 2 · Listen and rank

Scored from the DSP, to confirm by ear.

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 | ratio: sweeps the windowed peak from below the fundamental to the 8th partial, the classic resonant PD sweep; the biggest change in the machine | 5 |
| 2 | teeth: 3 teeth is a coarse stepped grind, 24 so fine the steps nearly vanish; strong at the low end, flattening past ~14 | 4 |
| 3 | wear: rounds each step edge and lowers the top harmonics, a darkening rather than a new sound; plain at bite 0 | 3 |
| 4 | bite: pure sine at 0 to a hard staircase read at 100, bright and buzzy; as dramatic as ratio | 5 |

## 3 · Subject

Five candidates from `passes/01-subject/pass.json` (state `ready_for_pick`); sketches at `passes/01-subject/v*/rest.svg`, notes in `passes/01-subject/notes.md`.

| candidate | pattern | drawing language | subject in one sentence | what each control moves | verdict |
| --- | --- | --- | --- | --- | --- |
| v1 | P1 Section drawing | typeset diagram | The wheel itself as a labelled figure: a big driver rim turning it, a follower riding its teeth | ratio: driver size/position · teeth: wheel outline · wear: follower tip shape · bite: follower rotation | candidate |
| v2 | P2 Diagram + trace | orthographic elevation | Gear pair in elevation left, bent output wave right | ratio: driver size/position · teeth: wheel outline + tick count · wear: trace corners · bite: trace bend | candidate |
| v3 | P3 Trace as subject | survey plan | The output wave as a proposed alignment bent off the dashed existing one, stations per tooth | ratio: chainage position · teeth: station count · wear: alignment corners · bite: offset from existing | candidate |
| v4 | P4 Stack in depth | patent section | The rim unrolled into sectioned strips, one per turn, stacked in depth with a pawl biting the front | ratio: back-strip stagger · teeth: front strip outline · wear: back strips' shape · bite: pawl position | candidate |
| v5 | P12 Orrery (stretch) | hidden-line isometric | An epicyclic train: sun driver, carrier, bright planet wheel in a toothed ring | ratio: planet scale · teeth: ring outline · wear: planet outline · bite: planet position on the arm | candidate, weak fit |

Chosen: pending, the owner's pick.
