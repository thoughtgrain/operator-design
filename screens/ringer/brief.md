# Ringer · screen brief

## 0 · Screen or stock page?

- Subject in one sentence: a ring of bells being rung in changes, where every control moves the bells, their order, or the rhythm they strike in.
- Not the stock page: a player as a track-control synth has no stock picture of its rule, and the rule (bells exchanging places, one change per row) is a physical, drawable thing.

## 1 · Intake

| | |
| --- | --- |
| Machine id | `ringer` |
| Kind | synth + trackControl (`machine.json`: `kind: synth`, `sdk: 1.9`; `resources.trackControl` on aux track 12, unique) |
| Category | player |
| Colour | grey (default) |
| Concept | Change ringing: a set of bells permuted by a method, one change per row, at a steady pace. |
| Sounds like | A ring of tuned notes (a descending major scale, treble highest) played as a steady stream on the target track, the order shifting every row so a familiar scale keeps turning into new phrases. Handstroke and backstroke rows alternate; with the gap open the stream breathes every second row, as tower bells do. |
| Controls | 4: bells, method, pace, stroke (stock header) |
| Control source | new |
| Mute | Mute is the bypass (ux.md, Aux tracks): the control passes `muted` to the display through `Overlay::display`, and every candidate says how its page shows it. |

### 1A · Port map (new machine: the source is the DSP I'm writing)

| source control | source range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| stage (number of bells) | 4..12, integer, 6 | 0 | bells | linear 4..12 | ratio | 0.25 (6, minor) | keep | DSP rounds to the nearest whole bell; the stages are minimus to maximus |
| method | 6 methods, ordered by how far the bells stray from plain hunting | 1 | method | enum `hunt bob gran sted kent camb` | enum | 0.2 (plain bob) | keep | Odd methods (grandsire, stedman) on an even stage ring with the tenor covering, as towers do |
| pace | blows per beat, 0.5..8, exponential, 2 | 2 | pace | exponential 0.5..8 | ratio | 0.5 (2 a beat) | keep | Tempo-synced to the OP-XY clock; clockwise is faster |
| handstroke gap | 0..1 blow, linear, 0 | 3 | stroke | linear 0..1 | percent | 0 (even stream) | keep | 100 % is the traditional open handstroke lead of one whole blow |
| scale / root | follows the target track's key | none | | | | | drop | The bells take the project scale; a fifth control would mean two pages for a setting the OP-XY already has |
| call (bob / single) | per lead | none | | | | | drop | Calls are touches; v1 rings plain courses. Could return as a key press later |

Integer conversion: none (new machine, Q31 control positions read directly).

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/ringer/definition.json` → 0 errors, 0 warnings (one note: show the muted state, answered in every candidate's risks).

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | pass | more bells; methods in order of complexity (hunt → camb); more blows a beat; a wider gap |
| Header values in real units, ≤ ~5 chars | pass, pending device | `6`, `bob`, `2.0`, `0%`: bell count, method name, blows per beat, gap as % of a blow |
| Defaults plainest useful; presets sound good (by ear) | pass, pending ear | Plain bob minor, even stream, 2 a beat: the first thing a band rings. Presets: plain bob minor, grandsire triples (open), cambridge major (open) |
| Engine page holds only the sound's own parameters | pass | four rule parameters; no envelope or LFO |
| Page 1 holds what's played most | pass | one page |
| Port parity: nothing silently lost | pass | new machine; scale and calls dropped with reasons above |
| Saved sounds compatible (if released) | n/a | not released |
| `id` final | pass | `ringer` |

### Captions

| # | label (≤ 8, lower) | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | bells | 4..12 | bells | 6 | `4` / `8` / `12` | 26 | yes |
| 2 | method | 6 methods | name | bob | `hunt` / `sted` / `camb` | 51 | yes, barely |
| 3 | pace | 0.5..8 | blows a beat | 2.0 | `0.5` / `2.0` / `8.0` | 38 | yes |
| 4 | stroke | 0..100 | % of a blow | 0 | `0%` / `50%` / `100%` | 51 | yes, barely |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device (the ratio display's exact digits are the SDK's).

Page 1: all four. No page 2.

## 2 · Listen and rank

Scored from the DSP, to confirm by ear.

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 bells | 4 to 12 notes a row: the range of the ring triples and every row lengthens; a strong change | 4 |
| 2 method | the same notes in a different order; plain hunt to Cambridge is clear over a lead, not on one note | 3 |
| 3 pace | 0.5 to 8 blows a beat, sixteen times the note rate; the loudest thing on the page | 5 |
| 4 stroke | up to one blow's pause every second row: a lilt, plain at slow pace, soft at fast | 2 |

## 3 · Subject

Five candidates from `passes/01-subject/` (pass record `pass.json`, state `ready_for_pick`). Sketches: `passes/01-subject/v1…v5/rest.svg`, all from `sketch.py`, all at defaults (plain bob minor).

| candidate | pattern | drawing language | subject in one sentence | what each control moves | verdict |
| --- | --- | --- | --- | --- | --- |
| v1 | P12 Orrery | patent section | Each bell a sectioned profile on its own orbit; its angle is its place in the change | bells: count of orbits · method: position on orbits · pace: count of rim graduations · stroke: rotation, a gap sector | owner's pick |
| v2 | P13 Capture | hidden-line isometric | The bells in their frame, each turned to how far it has swung: place in the change is where it is in its swing | bells: count of pits filled · method: rotation of each bell · pace: position of sallies · stroke: position of sliders | owner's pick |
| v3 | P14 Loom | star atlas | The method as a star chart: changes are parallels, places meridians, the treble's path the constellation line | bells: count of meridians · method: shape of the constellation · pace: count of parallels · stroke: position, whole pulls pair up | owner's pick |
| v4 | P5 Field and figure | engineering schematic | One bell in elevation turned to the angle it's rung to, over a chamber floor, the whole pull in the strip | bells: count of ticks · method: position (tick heights) · pace: rotation of the bell · stroke: position, gap in the strip | owner's pick |
| v5 | P4 Stack in depth (stretch) | oscilloscope trace | Each change as the pitch staircase it sends, the four before it stacked back as sweeps | bells: count of steps · method: shape of the front trace · pace: position, depth step · stroke: position, lead-in | owner's pick |

Chosen: pending the owner's pick (the designer's ranking is in `passes/01-subject/notes.md`).
