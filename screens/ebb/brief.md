# Ebb · screen brief

## 0 · Screen or stock page?

- Subject in one sentence: the tide itself, a water level that rises and falls over a scale's steps on a slow period, picking the register from its height and throwing foam (grace notes) at each turn.
- Not the stock page: a player on aux track 12 has no stock page that binds nodes, and the rule has one obvious physical subject (a tide) whose every part is a control.

## 1 · Intake

| | |
| --- | --- |
| Machine id | `ebb` |
| Kind | synth + `resources.trackControl` (SDK 1.9, aux track 12, unique; `machine.json` sdk 1.9) |
| Category | player |
| Colour | grey (default) |
| Concept | Notes rise and fall with a tide over a scale: the tide's height picks the register, foam scatters grace notes at the turn. |
| Sounds like | A slow melodic swell that climbs and falls through the target track's register on a scale, like water up and down a flight of steps. At the top and bottom of each tide, foam adds quick neighbour-note flurries before it turns. |
| Controls | 4: tide, period, foam, scale (stock header) |
| Control source | new (the DSP is the control code written for this machine) |
| Mute | Mute is the machine's bypass (ux.md, Aux tracks). The control code passes `control::Input.muted` to the display through `Overlay::display`, and every subject candidate says how its page shows it, by a channel other than shade alone. |

### 1A · Port map

New machine, no source platform. "Source" is the control code: `pitch(t) = mean + tide/2 · sin(2π t / period)`, quantised to the scale, emitted on the target track's step clock; within ±1/8 period of each turn, foam is the probability that a step adds one or two grace notes a scale step either side.

| source control | range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tide (range of the swing) | 0–36 st, linear, 12 st | 0 | tide | linear 0..36 | semitones | 0.3333 (12 st) | keep | Peak-to-peak span around the mean register; clockwise widens the swing. 12 st (an octave) is the plainest audible tide. |
| period (one full tide) | 1–32 s, exponential, 8 s | 1 | period | exponential 1..32 | duration | 0.6 (8.0 s) | keep | Exponential so the musically useful 2–12 s sits mid-range. |
| foam (grace-note chance at the turn) | 0–100 %, linear, 0 % | 2 | foam | linear 0..1 | percent | 0 | keep | Colouring control, defaults off. |
| scale | 7 modes, enum, maj | 3 | scale | enum maj, min, dor, phr, lyd, pent, hira | enum | 0 (maj) | keep | Labels ≤ 4 characters so they fit the 20 px value. Whole-tone was dropped: "whole" needs ~64 px. |

Integer conversion: none; values are the SDK's [0, 1] control positions.

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/ebb/definition.json` → 0 errors, 1 warning (plus the trackControl note).

| warning | resolution |
| --- | --- |
| `voiceCapacity 1; stock plays up to 8 notes per track` | Justified. Ebb runs on aux track 12, which the SDK keeps silent: it makes no sound of its own, so it needs no voices beyond the one slot a synth must declare. Its notes go to the target track, whose own engine has its own voice capacity. |
| (note) trackControl on aux 12: show the muted state | Each subject candidate in `passes/01-subject/` says how its page shows mute; the chosen one carries it to motion.md and handoff.md. |

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | pass | tide: a wider swing; period: a longer tide; foam: more grace notes; scale steps through the list (enum, no rise). |
| Header values in real units, ≤ ~5 chars | pass, widths pending device | semitones, seconds, percent, mode names; see Captions. |
| Defaults plainest useful; presets sound good (by ear) | pass by design, ear pending device | Slack: a one-octave tide over 8 s in major, no foam. Spring: 30 st, 4 s, 45 % foam, lydian. |
| Engine page holds only the sound's own parameters | pass | All four are the rule's own; no envelope or LFO. M4's shared LFO isn't claimed (no `sharedLfo`). |
| Page 1 holds what's played most | pass | One page. |
| Port parity: nothing silently lost | pass | New machine; whole-tone mode dropped for caption width, noted above. |
| Saved sounds compatible (if released) | n/a | Unreleased. |
| `id` final | yes | `ebb`. |

### Captions

| # | label (≤ 8, lower) | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | tide | 0–36 | st | 12 | 0 / 18 / 36 | 26 px | yes |
| 2 | period | 1–32 | s | 8.0 s | 1.0s / 5.7s / 32s | 51 px ("5.7s"); "32.0s" would be 64 px | yes if the duration format drops the decimal over 10 s; **pending device** |
| 3 | foam | 0–100 | % | 0 | 0 / 50 / 100 | 38 px | yes |
| 4 | scale | 7 modes | — | maj | maj / phr / hira | 51 px ("pent", "hira") | yes, tight |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device.

Page 1 (played most): tide, period, foam, scale · Page 2: none · Repeated controls: none.

## 2 · Listen and rank

Scored from the DSP, to confirm by ear.

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 tide | From one repeated note (0 st) to a three-octave swing; the register sweep is the machine's main gesture. | 5 |
| 2 period | From a fast warble (1 s) to a contour that takes 32 s to come round; changes the music's whole pace. | 4 |
| 3 foam | Nothing at 0; flurries of grace notes only near the turns, so it's heard twice a period, not continuously. | 3 |
| 4 scale | Every note's interval changes, the contour doesn't; clear to the ear but the shape stays. | 3 |

## 3 · Subject

Pass `passes/01-subject/` (state `ready_for_pick`; five directions, uniqueness checked). Sketches: `passes/01-subject/v1…v5/rest.svg`, generated by `sketch.py`. Notes and a ranking: `passes/01-subject/notes.md`.

| candidate | pattern | drawing language | subject in one sentence | what each control moves | verdict |
| --- | --- | --- | --- | --- | --- |
| v1 | P13 Capture | orthographic elevation | A stepped sea wall in elevation, one tread per scale degree; the water level is the capture line and the highest tread it covers plays. | tide: hw/lw marks spread · period: swell wavelength · foam: spray count · scale: tread profile | for the owner |
| v2 | P14 Loom | survey plan | Four rows of tide woven as weft over sixteen chainage lines, newest at the front. | tide: weft swing · period: weft wavelength · foam: hollow grace slabs · scale: corner scale bar + terracing | for the owner |
| v3 | P5 Field and figure | patent section | Fig. 1: a float in section on a receding sea, its graduated spar sliding past a fixed index. | tide: stop collars spread · period: sea wavelength · foam: spray count · scale: spar graduations | for the owner |
| v4 | P12 Orrery | hidden-line isometric | The moon drawing the sea into a spheroid round a hidden earth, pitch classes as beads on a ring. | tide: spheroid length · period: orbit radius · foam: spray off the tips · scale: beads filled | for the owner |
| v5 | P10 Voice field (stretch) | star atlas | A star chart where every degree at every moment is a star sized by how near the tide passes. | tide: band swing · period: band wavelength · foam: scatter at turns · scale: row spacing | for the owner |

Chosen: pending, the owner's pick.
