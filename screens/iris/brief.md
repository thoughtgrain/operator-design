# Iris · screen brief

Iris is named for the goddess of the rainbow, and for the coloured ring in the eye. The person asked for a new engine that morphs and overlaps four waveforms, with a rainbow as the starting idea for the screen, in grey.

## 0 · Screen or stock page?

- Subject in one sentence: four waveforms laid side by side like the bands of a rainbow, one lit where Morph sits and its neighbours bleeding in as Overlap opens.
- It earns a screen: there's one object the sound acts on (the four bands and the mix taken across them), and every control reshapes it.

## 1 · Intake

| | |
| --- | --- |
| Machine id | `iris` |
| Kind | synth |
| Category | engine |
| Colour | grey, confirmed by the owner (2026-11-17: "we don't want color"). The rainbow is a rainbow by its form (bands, arcs, order), never its hues, so no grayscale variant or colour role table is needed. |
| Sounds like | A single oscillator voice that scans from a pure sine through triangle and square to a bright saw. Open Overlap and the neighbouring waves sound together; add Spread and the four detune apart into a slow, shimmering chorus. |
| Controls | 6 (two pages, `"press": "page"`) |
| Control source | new (the DSP is written for this machine: `operators-xy/machines/iris/engine.cpp`) |

### 1A · Port map

No source to port from, so this is the control inventory of the DSP I wrote. Integer conversion as toro: each Q31 control word is taken as 0..32767 from its top 15 bits.

| control | what it does in the DSP | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| morph | centre of the mixing window across the four bands, 0 = sine, ⅓ = triangle, ⅔ = square, 1 = saw | page 1, encoder 1 | morph | linear 0..1 | percent | 0.3333 (triangle) | keep | band order is by harmonic content, so turning right always brightens |
| overlap | width of the window: 0 = a straight crossfade between the two nearest bands, 1 = all four sound, the far ones at a quarter weight | page 1, encoder 2 | overlap | linear 0..1 | percent | 0.25 | keep | weights are renormalised every block so the level holds |
| spread | detunes the four bands from each other, outer bands ±50 cents at 100 % | page 1, encoder 3 | spread | linear 0..1 | percent | 0 | keep | colouring, so it defaults off |
| tone | 2-pole low-pass that follows the note, 0.5 to 7.5 octaves above the fundamental, fixed Butterworth damping | page 1, encoder 4 | tone | linear 0..1 | percent | 0.7 | keep | key-tracked so it means "how many harmonics get through" at every pitch (my first fixed-frequency version went silent on high notes at 0); no resonance: the waves are the sound, the filter only tames them |
| skew | one breakpoint for the three shaped bands: phase-distorts the sine, leans the triangle toward a ramp, narrows the square to a pulse (50 % → 5 %); each band's resulting DC is subtracted exactly | page 2, encoder 1 (alt of morph) | skew | linear 0..1 | percent | 0 | keep | the saw has no breakpoint and stays a saw |
| phase | offsets each band's phase from the one before it, up to an eighth of a cycle each (quarter steps cancelled four equal bands' fundamental outright, −11 dB) | page 2, encoder 2 (alt of overlap) | phase | linear 0..1 | percent | 0 | keep | silent with Overlap closed on one band; with bands overlapping it cancels and reinforces harmonics |

Dropped on purpose: velocity (the XY applies it after the engine), an envelope and LFO (stock modules cover both), resonance (a resonant peak would fight Morph for what "brighter" means).

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/iris/definition.json` → 0 errors, 0 warnings, one note (two pages without 16 text slots: fine with the stock header; revisit in phase 4 if the screen draws its own header).

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | pass | more morph = further toward saw, more overlap/spread/tone/skew/phase = more of each |
| Header values in real units, ≤ ~5 chars | pass, with a note | all `percent` (≤ "100%", 4 chars). Spread could read in cents, but no display format shows cents; percent of the ±50 c maximum is the honest fallback |
| Defaults plainest useful; presets sound good (by ear) | pass / **pending device** | default is a clean triangle with a touch of its neighbours; presets by ear on hardware pending |
| Engine page holds only the sound's own parameters | pass | no envelope, LFO or mod amount |
| Page 1 holds what's played most | pass | morph, overlap, spread, tone; skew and phase are set-and-leave |
| Port parity | n/a | new machine |
| Saved sounds compatible | n/a | unreleased |
| `id` final | pass, until published | `iris`; it can still change before the first release |

### Captions

| # | label | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | morph | 0..1 | % | 33% | 0% / 50% / 100% | 51 | yes |
| 2 | overlap | 0..1 | % | 25% | 0% / 50% / 100% | 51 | yes |
| 3 | spread | 0..1 | % | 0% | 0% / 50% / 100% | 51 | yes |
| 4 | tone | 0..1 | % | 70% | 0% / 50% / 100% | 51 | yes |
| 5 | skew | 0..1 | % | 0% | 0% / 50% / 100% | 51 | yes |
| 6 | phase | 0..1 | % | 0% | 0% / 50% / 100% | 51 | yes |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: **pending device**.

Page 1 (played most): morph, overlap, spread, tone · Page 2: skew (under morph), phase (under overlap) · Repeated controls: none.

## 2 · Listen and rank

Scored from the DSP and the host render in `operators-xy/machines/iris/tests/` (I can't hear the device). **The person should confirm these by ear.**

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 morph | sine to saw: the biggest timbre change the voice has | 5 |
| 2 overlap | one band to all four at once: thickens and brightens, strongest away from the ends | 4 |
| 3 spread | static to a wide beating chorus; obvious from about 20 % | 4 |
| 4 tone | key-tracked low-pass from almost a sine to fully open, the same at every pitch | 4 |
| 5 skew | sine and triangle grow a sharp edge, square thins to a nasal pulse; small on the saw | 3 |
| 6 phase | hollows and fills harmonics, but only where bands overlap; inaudible on one band | 2 |
