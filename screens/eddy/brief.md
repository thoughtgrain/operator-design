# Eddy · screen brief

## 0 · Screen or stock page?

- Subject in one sentence: a rotating horn throwing sound round a cabinet, its rotor speed blown about by turbulence; the screen is that rotor and what its turning does to the sound (which drawing of it is the subject pass's open question, `passes/01-subject/`).
- Not stock: there is one physical object the whole sound comes from (the rotor), and every control acts on it (speed, irregular speed, horn reach / doppler, how much of it reaches the output).

## 1 · Intake

| | |
| --- | --- |
| Machine id | `eddy` |
| Kind | effect (send page, SDK 1.7) |
| Category | effect |
| Colour | grey (default) |
| Concept | A rotating speaker drowned in turbulence: spin sets the rotor, flutter adds eddies to its speed, depth sets the doppler. |
| Sounds like | A rotary speaker on the send: a slow chorale swirl at the default that speeds to a tremolo warble, the pitch wobbling with the horn's doppler. Flutter makes the rotor's speed gust and stall, so the swirl loses its even pulse and turns seasick. |
| Controls | 4: spin, flutter, depth, mix (stock header) |
| Control source | new (definition drafted here from the DSP being written: `definition.json`, `machine.json`) |

### 1A · Port map

New machine; "source" is the DSP as designed.

| source control | source range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rotor rate | 0.4–7 Hz, exponential, 0.82 Hz | 0 | spin | exponential 0.4..7 | ratio (Hz) | 0.25 (= 0.82 Hz) | keep | Chorale ~0.8 Hz at the default, tremolo ~6–7 Hz at the top; exponential so the slow end gets the travel |
| rate turbulence | 0–1, linear, 0 | 1 | flutter | linear 0..1 | percent | 0 | keep | Filtered-noise modulation of the rotor rate (gusts of up to ±60 % at 100); colouring, so off by default |
| doppler depth | 0–1, linear, 0.5 | 2 | depth | linear 0..1 | percent | 0.5 | keep | Horn radius: sets the delay-line excursion (pitch) and the AM depth together |
| wet/dry | 0–1, linear, 1 | 3 | mix | linear 0..1 | percent | 1 | keep | A send effect: 100 % wet by default, so the send level is the mix; lower for a partly dry return |
| drum rotor | fixed ratio 0.85 × horn, slower inertia | — | — | — | — | — | drop | Not a control: the drum follows the horn at a fixed ratio, as in the cabinets it imitates |
| chorale/tremolo switch | — | — | — | — | — | — | drop | Spin's continuous range covers both; a shift-row enum (`slow`/`fast` with ramp) was considered and left out because it would duplicate spin and the shift row costs Shift's fine steps |

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/eddy/definition.json` → 0 errors, 1 warning.

| warning | resolution |
| --- | --- |
| clean-defaults: `depth` reads like a colouring control but defaults to 0.5 | Justified. Depth is the effect itself, not an extra colour on top: at 0 the rotor makes no doppler and no amplitude swirl, so the default sound would be a dry return. Flutter, the actual degrading control, defaults to 0. |

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | pass | spin (rate), flutter (turbulence), depth (doppler), mix (wet) all rise clockwise |
| Header values in real units, ≤ ~5 chars | pass, pending device | spin shows Hz as a ratio (0.40–7.00, 4 chars); the rest are percent over true 0..1 ranges |
| Defaults plainest useful; presets sound good (by ear) | pending device | Chorale at 0.82 Hz, no flutter, half depth, full wet; presets Chorale and Gale unheard |
| Engine page holds only the sound's own parameters | pass | No envelope or LFO; flutter is the sound's own rotor turbulence, not a stock modulation |
| Page 1 holds what's played most | pass | One page, four controls |
| Port parity: nothing silently lost | pass | New machine; the dropped drum ratio and speed switch are listed above |
| Saved sounds compatible (if released) | n/a | Unreleased |
| `id` final | pass | `eddy` |

### Captions

| # | label (≤ 8, lower) | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | spin | 0.4–7 | Hz | 0.82 | 0.40 / 1.67 / 7.00 | 51 | yes, just (pending device) |
| 2 | flutter | 0–100 | % | 0 | 0 / 50 / 100 | 38 | yes |
| 3 | depth | 0–100 | % | 50 | 0 / 50 / 100 | 38 | yes |
| 4 | mix | 0–100 | % | 100 | 0 / 50 / 100 | 38 | yes |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device.

Page 1 (played most): spin, flutter, depth, mix · Page 2: none · Repeated controls: none

## 2 · Listen and rank

Scored from the DSP, to confirm by ear.

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 | spin: slow chorale swirl to fast tremolo warble, the most obvious change the machine makes | 5 |
| 2 | flutter: from an even pulse to gusting, stalling speed; subtle under ~30 %, obvious above, and quieter at very low spin | 3 |
| 3 | depth: from no movement (dry-sounding) to a deep pitch wobble and strong amplitude swirl | 4 |
| 4 | mix: on a send, wet/dry of the return; clear but it changes level and blend more than character | 3 |

## 3 · Subject

Pass record: `passes/01-subject/pass.json` (state `ready_for_pick`). Sketches: `passes/01-subject/v1…v5/rest.svg`, all from `passes/01-subject/sketch.py`; notes and a ranking in `passes/01-subject/notes.md`.

| candidate | pattern | drawing language | subject in one sentence | what each control moves | verdict |
| --- | --- | --- | --- | --- | --- |
| v1 | P1 Section drawing | oscilloscope trace | The horn chamber cut through in plan and drawn by a scope beam: the twin horn is one bright trace on a graticule, its phosphor trail fading behind each mouth. | spin: trail arc 20–280°; flutter: trail ripples; depth: horn length 2.4×; mix: ghost horns 0–4 | owner's pick |
| v2 | P2 Diagram + trace | typeset diagram | Signal-path diagram (input, rotor, eddy line, dry/wet vane) beside the output trace of a tone the doppler squeezes. | spin: rotor ticks 3–24; flutter: eddy line shape; depth: trace FM; mix: vane 90° | owner's pick |
| v3 | P3 Trace as subject | orthographic elevation | The horn mouth's path through time as a helix in elevation, front half-turns bright and back as hidden lines, projected from an end view. | spin: helix pitch 1–12 turns; flutter: uneven pitch; depth: radius 18–58 px; mix: crossfade point 374 px | owner's pick |
| v4 | P4 Stack in depth | survey plan | Survey sheets of the rotor, one per past revolution, stacked back in time; the front sheet maps the throw as contours. | spin: bearing advance 25–165° per sheet; flutter: sheets out of register; depth: lobe 3×; mix: sheets 2–5 | owner's pick |
| v5 | P12 Orrery (stretch) | patent section | The cabinet cut open as a patent section: horn and drum rotor on two orbits about one shaft, louvred walls, numerals on leaders. | spin: phantom horn positions 1–13; flutter: drum orbit ripples; depth: horn orbit 2×; mix: louvres 10–70° | owner's pick |

The pick is the owner's; not chosen here.
