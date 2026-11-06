# Vapor · screen brief

## 0 · Screen or stock page?

- Subject in one sentence: a breathy voice is a pulse of air shaped by a tube into a vowel, so the screen is that shaping: the tube, the vowel it makes, or the wave that comes out (five candidates in section 3; the pick is the owner's).
- Not the stock page: there is one object every control acts on (the vocal tract and its vowel), and every control changes it in a way that can be drawn.

## 1 · Intake

| | |
| --- | --- |
| Machine id | `vapor` |
| Kind | synth |
| Category | engine |
| Colour | grey (default) |
| Concept | A breathy formant voice: a glottal pulse through a throat tube and vowel formants, gliding between vowels. |
| Sounds like | A soft sung vowel with air in it, from a hushed whisper to a clear pulsed tone. Each note opens out of a closed "oo" into its vowel, so phrases sound sung rather than switched on. |
| Controls | 4: vowel, breath, throat, glide (stock header) |
| Control source | new (the DSP I'm writing; no port) |

DSP sketch the definition is written against: a Rosenberg-style glottal pulse at the note's pitch, mixed with aspiration noise gated by the pulse's open phase (breath sets the mix); three parallel two-pole formant resonators (F1-F3) whose centre frequencies come from a vowel table, all divided by the throat ratio (a longer tract lowers every formant); each note starts its formants at /u/ (or at the last vowel sung, legato) and slides to the target vowel with a one-pole glide of the set time, which also smooths vowel changes while a note sounds.

### 1A · Port map

New machine, so "source" is the DSP above.

| source control | source range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| vowel position | 9 points on the u-o-a-e-i path (vowels and the midpoints between them) | 0 | vowel | enum `u uo o oa a ae e ei i` | enum | 0.5 (`a`) | keep | Stepped on purpose: the glide control smooths every step, so the knob picks targets and glide decides how the voice travels between them |
| aspiration mix | 0..1 linear, noise vs pulse | 1 | breath | linear 0..1 | percent | 0.25 | keep | Not zero by default; see review |
| tract length ratio | 0.75..1.5 linear (formants ÷ ratio) | 2 | throat | linear 0.75..1.5 | ratio | 0.3333 (1.00) | keep | 1.00 = 17.5 cm adult tract; clockwise is a longer throat and lower formants |
| formant glide time | 5 ms..2 s, exponential | 3 | glide | exponential 0.005..2.0 | duration | 0.4147 (60 ms) | keep | Time from the onset vowel (or the last one) to the target |

Integer conversion: none; no source platform.

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/vapor/definition.json` → 0 errors, 0 warnings.

| warning | resolution |
| --- | --- |
| none | `breath` isn't caught by the colouring pattern but is the one judgement call: see the defaults row |

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | yes | vowel walks u → i (rising F2), breath rises, throat lengthens (ratio rises), glide time rises |
| Header values in real units, ≤ ~5 chars | partly | `a`, `25`, `1.00` fit; glide's `100ms` estimates at 64 px, over the 53 px column, for 100-999 ms (0.50 to ~0.88 of its travel): **pending device** measurement in Univers Next Pro Light |
| Defaults plainest useful; presets sound good (by ear) | yes, one departure | breath defaults to 25 %, not 0: vapor *is* a breathy voice and 0 is a bare buzzing pulse, which is the coloured end for this engine, not the clean one. Presets: **pending by ear** |
| Engine page holds only the sound's own parameters | yes | glide is a formant slide inside the voice, not an envelope; the OP-XY's envelope still shapes level |
| Page 1 holds what's played most | yes | one page |
| Port parity: nothing silently lost | n/a | new machine |
| Saved sounds compatible (if released) | n/a | unreleased |
| `id` final | yes | `vapor` |

### Captions

| # | label (≤ 8, lower) | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | vowel | u … i (9 steps) | enum | 0.5 | `u` / `a` / `i` (widest `uo`, `oa`, `ae`, `ei`) | 26 px | yes |
| 2 | breath | 0 … 100 | % | 0.25 | `0` / `50` / `100` | 38 px | yes |
| 3 | throat | 0.75 … 1.50 | ratio | 0.3333 | `0.75` / `1.13` / `1.50` | 51 px | yes, just |
| 4 | glide | 5 ms … 2 s | duration | 0.4147 | `5ms` / `100ms` / `2.0s` (format per device) | 64 px at `100ms` | no in the 100-999 ms band, **pending device** |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device.

Page 1 (played most): all four · Page 2: none · Repeated controls: none.

## 2 · Listen and rank

Scored from the DSP, to confirm by ear.

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 vowel | F1/F2 sweep through five vowels; the most obvious change the voice has | 5 |
| 2 breath | pure pulse to near-whisper; loudness of the noise and loss of pitch clarity, strong across the whole range | 4 |
| 3 throat | child-small to giant-large voice; every formant moves by an octave across the range | 4 |
| 4 glide | at 5 ms each note simply starts on its vowel; from ~50 ms an audible "w"-like onset, at 2 s a slow diphthong. Only heard at note starts and vowel moves | 3 |

## 3 · Subject

Five candidates, one per direction from the pass record `passes/01-subject/pass.json` (each in `passes/01-subject/vN/candidate.json`, sketched in `vN/rest.svg` by `passes/01-subject/sketch.py`). Uniqueness: `design_pass_submit` → `ready_for_pick`.

| candidate | pattern | drawing language | subject in one sentence | what each control moves | verdict |
| --- | --- | --- | --- | --- | --- |
| v1 | P15 Cell field | typeset diagram | A field of square cells laid over the vowel chart, where a bright clump of lit cells sits on the sung vowel and grey breath hangs round it. | vowel: clump position · breath: grey haze count · throat: clump size (count) · glide: trail of cells from u | open |
| v2 | P1 Section drawing | orthographic elevation | The throat drawn in elevation as a segmented acoustic tube from glottis to lips, its sections widening and narrowing into the shape of the vowel. | vowel: tube profile (shape) · breath: turbulence streaks (count) · throat: tube scale · glide: ghost profiles (count) | open |
| v3 | P2 Diagram + trace | survey plan | A survey split in two: the vowel quadrilateral plotted as a parcel with five stations and a traverse to the sung vowel, and the spectral profile as a long section. | vowel: station position + peaks (shape) · breath: noise ground line (position) · throat: plan scale · glide: chainage ticks (count) | open |
| v4 | P3 Trace as subject | patent section | The pressure wave at the lips as a patent figure, four glottal periods ringing with the vowel, early ones still gliding out of a closed u, aspiration traced beneath. | vowel: ringing (shape) · breath: aspiration trace (shape) · throat: trace scale · glide: ghost periods (count) | open |
| v5 | P11 Instrument stack (stretch) | hidden-line isometric | Five vowel resonators stacked on a throat neck, the sung vowel's chamber solid, breath rising off the top in rings. | vowel: which chamber is solid (shade + position) · breath: rings (count) · throat: neck length (position) · glide: lit chambers (count) | open; stretch reads as a poor fit |

Chosen: pending, the owner's pick.
