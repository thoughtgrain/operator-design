# Relay · screen brief

## 0 · Screen or stock page?

- Subject in one sentence: the bucket chain itself, with a test note passing down it and coming round again, so the player sees how many buckets it has, which of them leak, how unevenly they're clocked and how often the note recirculates.
- Not the stock page: there is one thing the sound acts on (the chain), and every control changes it.

## 1 · Intake

| | |
| --- | --- |
| Machine id | `relay` |
| Kind | effect |
| Category | effect |
| Colour | grey (default) |
| Concept | A bucket-brigade delay with failing stages: some buckets leak, the clock wanders, feedback recirculates. |
| Sounds like | A dark, slightly grainy analogue delay: from flanger-short slap to a 1 s echo, the repeats softening each pass. Turned up, the repeats lose level and pieces as buckets leak, and warble in pitch as the clock wanders. |
| Controls | 4: stages, leak, clock, feedback (stock header; no shift row) |
| Control source | new (source is the DSP to be written) |

No shift row: a chip-type or clock-noise enum was considered and doesn't earn its place; four continuous controls cover the concept.

Effect pages get their controls (`slots`), `track` and `shift`, not the audio or notes, so whatever the screen shows of a signal is a notional test note through the chain, not what's playing. No browser preview for effect pages yet: design from stills, check on a device.

### 1A · Port map (new machine: source is the DSP)

| source control | source range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bucket count | 100..10000 stages at a nominal 0.1 ms per stage, log | 0 | stages | exponential 0.01..1.0 s | duration | 0.5 (1000 stages, 100 ms) | keep | Header shows the delay time the stage count makes; the screen shows the count |
| leak | 0..1: share of buckets failing (seeded) and how much charge each loses per tick | 1 | leak | linear 0..1 | percent | 0 | keep | Degrading, so off by default |
| clock wander | 0..1 semitone peak pitch deviation from a slow random clock drift | 2 | clock | linear 0..1 | semitones | 0 | keep | Degrading, so off by default; label is fixed by the brief, the value says what rises (wander, in st) |
| feedback | 0..1 of the output back to the input; the chain's own insertion loss (~1 dB a pass) keeps 100 % from running away | 3 | feedback | linear 0..1 | percent | 0.35 | keep | Plain useful echo: three audible repeats |

Integer conversion: none (new machine).

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/relay/definition.json` → 0 errors, 0 warnings (2 notes: effects have no browser preview yet; effect resources not reviewed beyond structure). `resources.display` is a placeholder until phase 4.

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | yes, one caveat | stages, leak, feedback rise as named. `clock` names the clock, not the wander; the semitone value makes clear what rises. If the owner may rename, `wander` is clearer |
| Header values in real units, ≤ ~5 chars | partly | `100ms` and other three-digit ms values are 5 characters, est. 64 px, over the 53 px column (it overlaps `leak` in the preview font). Pending device measurement; fallback is a header text override in seconds (`0.10`) or a range that keeps ms to two digits |
| Defaults plainest useful; presets sound good (by ear) | yes / pending ear | leak and clock 0, feedback 35 %, 100 ms. Presets `Clean` and `Tired` to confirm by ear |
| Engine page holds only the sound's own parameters | yes | all four are the delay's own |
| Page 1 holds what's played most | yes | one page |
| Port parity: nothing silently lost | n/a | new machine |
| Saved sounds compatible (if released) | n/a | unreleased |
| `id` final | yes | `relay` |

### Captions

| # | label (≤ 8, lower) | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | stages | 10 ms .. 1 s (100..10000 stages) | duration | 0.5 | `10ms` / `100ms` / `1.0s` | 51 / 64 / 51 | no at mid range (pending device) |
| 2 | leak | 0..100 | percent | 0 | `0` / `50` / `100` | 13 / 26 / 38 | yes |
| 3 | clock | 0..1 st | semitones | 0 | `0.00` / `0.50` / `1.00` | 51 | yes, just |
| 4 | feedback | 0..100 | percent | 35 | `0` / `50` / `100` | 13 / 26 / 38 | yes |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device. `feedback` is 8 characters, the label limit.

Page 1 (played most): all four · Page 2: none · Repeated controls: none.

## 2 · Listen and rank

Scored from the DSP, to confirm by ear.

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 stages | delay time 10 ms → 1 s: comb/flange colour through slapback to a clear echo; the biggest change in what the effect is | 5 |
| 2 leak | repeats lose level and highs and break up into grit as failing buckets drop charge; obvious from ~30 %, subtle below | 4 |
| 3 clock | pitch warble of the repeats, chorus-like at low settings to seasick at 1 st; quieter than leak, and only on the wet signal | 3 |
| 4 feedback | from one repeat to a long recirculating tail near self-oscillation; dramatic at the top | 4 |

## 3 · Subject

Pass record: `passes/01-subject/pass.json` (state `ready_for_pick`), candidates in `passes/01-subject/v1..v5/candidate.json`, sketches `rest.svg`/`rest.png` from `passes/01-subject/sketch.py`, notes in `passes/01-subject/notes.md`.

| candidate | pattern | drawing language | subject in one sentence | what each control moves | verdict |
| --- | --- | --- | --- | --- | --- |
| v1 | P4 Stack in depth | oscilloscope trace | Each trip round the chain is one scope sweep, stacked back in depth, newest bright in front | stages: burst position on every sweep · leak: shape of the front trace · clock: back layers shear sideways · feedback: number of layers | owner's pick |
| v2 | P10 Voice field | typeset diagram | The chain coiled into a printed spiral of bucket bars, each turn one recirculation | stages: bars per turn · leak: failing bars sink · clock: bar spacing and lump drift · feedback: number of turns | owner's pick |
| v3 | P15 Cell field | orthographic elevation | A wall of bucket compartments face on, held charge as how full and bright each stands | stages: spacing of runs · leak: compartments drained · clock: run length · feedback: density of lit runs | owner's pick |
| v4 | P1 Section drawing | survey plan | The charge channel cut lengthwise as a surveyor's long-section of wells and pools, chainage in stages, return leg beneath | stages: number of wells · leak: pool-surface profile · clock: gate/well pitch · feedback: grade line height | owner's pick |
| v5 | P11 Instrument stack (stretch) | patent section | A patent drawing of a cascade of tipping buckets with a return riser | stages: number of buckets · leak: drops and sinking levels · clock: bucket tilt · feedback: riser water column | owner's pick |

Chosen: pending, the owner's call.
