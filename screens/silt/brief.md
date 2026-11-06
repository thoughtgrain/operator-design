# Silt · screen brief

## 0 · Screen or stock page?

- Subject in one sentence: a bank of additive partials that lie settled like sediment, which each note stirs up (the high partials lift furthest) and which then sink back at the settling rate.
- A custom screen earns its place: there is one thing the sound acts on (the partials and how high they hang), and all four controls change it.

## 1 · Intake

| | |
| --- | --- |
| Machine id | `silt` |
| Kind | synth |
| Category | engine |
| Colour | grey (default) |
| Concept | Additive partials that settle like sediment: stirring lifts the high partials, which then sink back at a settling rate. |
| Sounds like | A dull, round additive tone at rest that brightens on every note as the upper partials are stirred up, then darkens again as they sink. Short settle sounds like a plucked brightness; long settle leaves a slow, glassy fall. |
| Controls | 4: settle, layers, stir, grain (stock header) |
| Control source | new |

### 1A · Port map (new machine: the source is the DSP being written)

| source control | source range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| settling time constant | 0.1–10 s, exponential, 1.0 s | 0 | settle | exponential 0.1..10 | duration | 0.5 (1.0 s) | new | time for lifted partials to sink back to their bed level (one time constant) |
| partial count | 2–64, stepped, 16 | 1 | layers | enum 2,4,8,12,16,24,32,48,64 | enum | 0.5 (16) | new | stepped so the count and the CPU cost are predictable |
| stir depth | 0–1, linear, 0.35 | 2 | stir | linear 0..1 | percent | 0.35 | new | how far a note lifts each partial above its bed; lift grows with partial number |
| grain | 0–1, linear, 0 | 3 | grain | linear 0..1 | percent | 0 | new | fixed seeded detune per partial up to ±4 % (inharmonic, coarse); defaults off as a colouring control |

No integer conversion: values come straight from the SDK's Q31 positions through the mappings above.

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/silt/definition.json` → 0 errors, 0 warnings. `resources.display` is a placeholder (1 path × 64 points, 64 nodes, 8 palette entries) until phase 4.

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | pass | settle time, partial count, stir depth and grain coarseness all rise clockwise |
| Header values in real units, ≤ ~5 chars | pass, pending device | `1.0s`, `16`, `35`, `0`; settle's short end may print as `100ms` (5 chars, ~64 px est.), pending the device font |
| Defaults plainest useful; presets sound good (by ear) | pass, pending device | grain off; stir at 35 so a note audibly brightens; presets Still (defaults) and Flood (slow, 48 partials, heavy stir, some grain) |
| Engine page holds only the sound's own parameters | pass | settle is the sound's own spectral motion, not the amp envelope; the stock envelope still shapes level |
| Page 1 holds what's played most | pass | one page, four controls |
| Port parity: nothing silently lost | n/a | new machine |
| Saved sounds compatible (if released) | n/a | not released |
| `id` final | pass | `silt` |

### Captions

| # | label (≤ 8, lower) | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | settle | 0.1–10 | s | 1.0 s | `0.1s` / `1.0s` / `10s` | 51 px | yes (pending device; `100ms` would be 64 px) |
| 2 | layers | 2–64 | partials | 16 | `2` / `16` / `64` | 26 px | yes |
| 3 | stir | 0–100 | % | 35 | `0` / `50` / `100` | 38 px | yes |
| 4 | grain | 0–100 | % | 0 | `0` / `50` / `100` | 38 px | yes |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device.

Page 1 (played most): settle, layers, stir, grain · Page 2: none.

## 2 · Listen and rank

Scored from the DSP, to confirm by ear.

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 settle | from a quick flick of brightness on each note to a slow 10 s darkening; dramatic on repeated or held notes | 4 |
| 2 layers | 2 partials is hollow and nearly sine, 64 is full and buzzy; most of the change sits at the low end (2 → 12) | 4 |
| 3 stir | from no brightening at all to a bright, buzzy lift on every note; the main timbre control | 5 |
| 4 grain | partials pulled off harmonic: beating and a metallic edge, subtle below ~30 | 3 |

## 3 · Subject

Five candidates from `passes/01-subject/pass.json` (state `ready_for_pick`, every pair unique). Each has `candidate.json` and a rest sketch `rest.svg` beside it; `passes/01-subject/notes.md` ranks them. The pick is the owner's.

| candidate | pattern | drawing language | subject in one sentence | what each control moves | verdict |
| --- | --- | --- | --- | --- | --- |
| v1 | P2 Diagram + trace | oscilloscope trace | A dual-channel scope: the partial spectrum and its decay slope on the left graticule, the summed output waveform on the right. | settle rotation (dB decay line), layers count (spectrum lines), stir shape (output trace), grain position (lines slide off harmonic ticks) | owner's pick |
| v2 | P3 Trace as subject | typeset diagram | The stirred wave printed big as a textbook figure, its component partials drawn small beneath it hanging in a band that sinks toward a stippled silt bed. | settle position (band depth), layers count (component curves), stir shape (main wave), grain scale (stipple dots) | owner's pick |
| v3 | P4 Stack in depth | orthographic elevation | Octave bands of partials as flat plates in elevation, stepping back from the fundamental on the ground line, the upper plates lifted off their dashed settled positions. | settle position along stack (bright plate), layers count (plates), stir position (vertical lift), grain shape (bright plate's top edge) | owner's pick |
| v4 | P5 Field and figure | survey plan | A survey plan of a settling basin: a bright silt plume over a contoured bed, its deposit lens on the flow line, one chainage station per partial. | settle scale (plume), layers count (stations), stir shape (plume edge), grain position (deposit lens) | owner's pick |
| v5 | P11 Instrument stack (stretch) | patent section | A glass settling column cut open like a patent figure, partial strata stacked to a bright interface, a hinged stirring arm and suspended grains above. | settle position (interface), layers count (strata), stir rotation (arm), grain scale (particles) | owner's pick; stretch doesn't honestly fit P11 |
