# Tilt · screen brief

## 0 · Screen or stock page?

- Subject in one sentence: the sound's spectrum with one band held in focus, crisp, while everything outside it goes soft and the whole thing tilts about that band.
- Not the stock page: there's one thing the sound acts on (the spectrum, split into in-focus and out-of-focus), and all four controls change it (where the focus sits, how it slopes, how soft the rest is, how much of it you hear).
- An effect page gets no audio and no notes (`constraints.md`, Which machines draw a screen: `slots`, `track`, `shift`, `choices`). So every drawing is the settings applied to a fixed test chart (a harmonic source with three formants and three hits in time), not the live signal, and the screen moves only on a turn.

## 1 · Intake

| | |
| --- | --- |
| Machine id | `tilt` |
| Kind | effect (SDK 1.7 send page; `machine.json`) |
| Category | effect |
| Colour | grey (default) |
| Concept | Tilt-shift for sound: a spectral tilt with a blur that smears everything outside a focal band. |
| Sounds like | A one-octave band around the focus passes untouched while the rest of the spectrum is smeared, in frequency (partials melt into a wash) and a little in time (transients outside the band soften into swells), so the band seems to sit in front of a blurred background. A tilt filter pivoting on the focus darkens or brightens everything around it. |
| Controls | 4: focus, tilt, blur, mix (one page, stock header) |
| Control source | new (no source engine; "source" is the DSP sketched in `passes/01-subject/sketch.py`: flat-topped band window ±0.5 oct, log-frequency Gaussian smear outside it, ±6 dB/oct tilt about the focus) |

### 1A · Definition (new machine)

No port, so the port map is the new machine's own controls.

| control | range / curve | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| focus | 100 Hz – 8 kHz, ISO third-octave centres | 0 | focus | enum, 20 labels | enum | 0.5263 (1k) | keep | Enum so the header shows real frequencies (`1.2k`, `6.3k`); the DSP glides between centres so the steps don't click |
| tilt | −6 … +6 dB/oct about the focus | 1 | tilt | linear −6..6 | bipolar | 0.5 (flat) | keep | Clockwise brightens (the high side rises) |
| blur | smear width 0 … 0.64 oct, time smear 0 … ~80 ms | 2 | blur | linear 0..1 | percent | 0.4 | keep | The effect itself, so it doesn't default to 0 (at 0 with tilt flat the machine does nothing) |
| mix | dry … wet | 3 | mix | linear 0..1 | percent | 1.0 | keep | A send effect, so wet by default |
| band width | fixed ±0.5 oct | — | — | — | — | — | drop | Considered as a shift-row enum (`narrow`, `oct`, `wide`); left out because it doesn't earn a place yet. Revisit if focus alone feels too coarse by ear |

Presets: `Miniature` (the defaults: 1k in focus, flat, blur 40 %, wet) and `Haze` (focus 500, tilt −2 dB/oct, blur 85 %, mix 70 %).

`resources.display` is a placeholder (paths 1, points 64, nodes 64, texts 0, palette 8); phase 4 sets it from the chosen subject.

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/tilt/definition.json` → 0 errors, 0 warnings, 2 notes (effects have no browser preview yet; effect resources not reviewed beyond structure). Nothing to justify.

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | yes | focus rises in Hz, tilt rises toward brighter, blur and mix rise in amount |
| Header values in real units, ≤ ~5 chars | yes, one pending | focus in Hz (`1.2k` is the widest, 4 chars); blur and mix are amounts, so percent is their unit. tilt's `bipolar` caption is **pending device**: if it shows the mapped value it reads `-6`…`+6` (dB/oct); if it shows −100…+100 it's still direction-correct but not a unit, and a `header[1]` override (`+3dB`, 4 chars) would fix it |
| Defaults plainest useful; presets sound good (by ear) | defaults yes; presets **pending ear** | Defaults are the gentlest setting that does something (flat tilt, mild blur). Preset sound unconfirmed until the DSP runs |
| Engine page holds only the sound's own parameters | yes | No envelope or LFO |
| Page 1 holds what's played most | yes | One page |
| Port parity | n/a | New machine; the only thing left out (band width) is listed above |
| Saved sounds compatible | n/a | Unreleased |
| `id` final | yes | `tilt` |

### Captions

| # | label | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | focus | 100 Hz – 8 kHz | Hz (enum) | 1k | `100` / `1k` / `8k` (widest `1.2k`, `6.3k`) | 38 / 26 / 26 (51) | yes |
| 2 | tilt | −6 … +6 | dB/oct (bipolar) | 0 | `-6` / `0` / `+6` (or `-100` / `0` / `+100`) | 26 / 13 / 26 (51) | yes |
| 3 | blur | 0 – 100 | % | 40 | `0` / `50` / `100` | 13 / 26 / 38 | yes |
| 4 | mix | 0 – 100 | % | 100 | `0` / `50` / `100` | 13 / 26 / 38 | yes |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device.

Page 1 (played most): focus, tilt, blur, mix · Page 2: none · Shift row: none.

## 2 · Listen and rank

Scored from the DSP, to confirm by ear (the effect isn't built yet; scores come from the model in `sketch.py`, on a full-range source).

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 | focus: moves which octave stays clear; obvious with blur up, subtle at blur 0 and tilt flat (then it only moves the tilt's pivot) | 3 |
| 2 | tilt: ±6 dB/oct is ±24 dB at four octaves from the focus, from dark and boomy to thin and bright across the turn | 5 |
| 3 | blur: from transparent to a wash where only the band keeps its partials and its attacks | 4 |
| 4 | mix: blends dry and wet; at the default (tilt flat, blur 40 %) wet is close to dry, so it's audible mainly once blur or tilt are up | 2 |

## 3 · Subject

Five candidates, one per direction from the pass (`passes/01-subject/pass.json`, state `ready_for_pick`). Sketches: `passes/01-subject/v1…v5/rest.svg` (all 0 lint errors), notes in `passes/01-subject/notes.md`.

| candidate | pattern | drawing language | subject in one sentence | what each control moves | verdict |
| --- | --- | --- | --- | --- | --- |
| v1 | P3 Trace as subject | typeset diagram | One bright spectrum line on a log-frequency axis, crisp and jagged in the focal band, smoothed outside it | focus: position of the crisp span; tilt: rotation of the line about the focus; blur: shape (smoothing outside); mix: position of a dry ghost line | open |
| v2 | P4 Stack in depth | orthographic elevation | Six octave bands as cards receding in elevation, the focus card crisp and bright, the others soft with an echoed outline | focus: which card is crisp; tilt: card heights; blur: echo lift and flattening; mix: stack spacing | open |
| v3 | P10 Voice field | survey plan | A frequency × time plot of square markers, a sharp surveyed strip at the focus, the rest smeared even | focus: strip position; tilt: marker size ramp; blur: evening-out down time; mix: count of wet markers | open |
| v4 | P15 Cell field | patent section | A block of cells cut like a patent section: solid crisp cells in the band, cross-hatched smeared runs outside | focus: solid column position; tilt: hatch density ramp; blur: run length; mix: count of dry cells | open |
| v5 | P13 Capture (stretch) | hidden-line isometric | A tilt-shift miniature: fins on a base, a glass plane of focus capturing the fins inside its depth of field as solid | focus: plane position; tilt: base slope (fin heights); blur: ghost set-back; mix: plain scale on the base edge | open |

Chosen: … (the owner's pick).
