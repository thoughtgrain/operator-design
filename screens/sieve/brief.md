# Sieve · screen brief

## 0 · Screen or stock page?

- Subject in one sentence: the sieve itself, a mesh that the input's harmonic series falls onto, with only the multiples it keeps getting through. (Five readings of it are in the subject pass below.)
- Not the stock page: the machine has one object it acts on (the input's harmonic series) and one rule (keep every Nth multiple), and every control does something to that picture.

## 1 · Intake

| | |
| --- | --- |
| Machine id | `sieve` |
| Kind | effect (SDK 1.7: its own send page, 4 parameters, stock header, no shift row) |
| Category | effect |
| Colour | grey (default) |
| Concept | A harmonic sieve: a comb filter tuned to the input's fundamental keeps only chosen multiples, shaken to let others through. |
| Sounds like | A pitch tracker follows the input's fundamental and a bank of comb resonances sits on the harmonics it keeps, so a bass line through the sieve at 2nd comes out an octave up and glassy, at 3rd a twelfth up and hollow. Shake lets rejected harmonics flicker through at random, so a held note rattles and sparkles instead of ringing pure. |
| Controls | 4: mesh, shake, keep, mix |
| Control source | new (the DSP is being written alongside this brief) |

### 1A · Definition (new machine, no port)

Source is the DSP as specified, not a port; every control is new.

| DSP control | range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| harmonic step N (keep k where k mod N = 0) | 1..8, stepped | 0 | mesh | enum `all, 2nd … 8th` | enum | 0.1429 (2nd) | keep | Clockwise keeps fewer harmonics, like a higher mesh number on a real sieve (finer). Default 2nd, not `all`: at `all` the sieve keeps everything and is only a pitched comb, so 2nd (octave up) is the plainest setting that sounds like this machine. |
| leak probability of rejected harmonics | 0..1, linear | 1 | shake | linear 0..1 | percent | 0 | keep | Colouring, so it defaults off. |
| comb ring time (feedback decay to −60 dB) | 10 ms .. 2 s, exponential | 2 | keep | exponential 0.01..2.0 | duration | 0.4 (83 ms) | keep | Ring time is heard in seconds; exponential so the useful short end gets travel. |
| wet/dry | 0..1, linear | 3 | mix | linear 0..1 | percent | 1.0 | keep | 100 % on a send, where the dry signal is already in the track. |
| pitch tracker sensitivity / fallback pitch | — | — | — | — | — | — | drop | Fixed in the DSP (tracks 30 Hz–2 kHz, holds the last pitch through silence); four knobs are better spent on the sound. A shift row could expose a tracking mode later if it earns it. |

Presets: **Octave** (defaults: 2nd, no shake, 83 ms, 100 %) and **Rattle** (3rd, shake 55 %, ~400 ms, 80 %).

`resources.display` is a placeholder (1 path × 64 points, 32 nodes, 0 texts, 6 palette) until phase 4.

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/sieve/definition.json` → 0 errors, 0 warnings (two notes: effects have no browser preview yet, so the page is checked on a device; effect resources aren't reviewed beyond structure).

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | yes | mesh: the step N rises (finer); shake: leak rises; keep: ring time rises; mix: wet share rises |
| Header values in real units, ≤ ~5 chars | partly | `2nd`, `0`–`100`, durations; `141ms` is 5 characters and estimates over the column (see Captions) |
| Defaults plainest useful; presets sound good (by ear) | yes on paper, **pending ear** | Shake off, mix 100 %, mesh 2nd; presets not yet heard |
| Engine page holds only the sound's own parameters | yes | No envelope or LFO |
| Page 1 holds what's played most | yes | One page |
| Port parity | n/a | New machine; the tracker settings dropped on purpose (above) |
| Saved sounds compatible | n/a | Unreleased |
| `id` final | yes | `sieve` |

### Captions

| # | label | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | mesh | all .. 8th | step | 2nd | `all` / `5th` / `8th` | 38 | yes |
| 2 | shake | 0 .. 100 | % | 0 | `0` / `50` / `100` | 38 | yes |
| 3 | keep | 10 ms .. 2 s | s | 83 ms | `10ms` / `141ms` / `2.0s` | 51 / 64 / 51 | no at mid-range: `100ms`–`999ms` estimate 64 px, **pending device** (measure the stock duration format in the real font; fallback is a header text override in `0.14s` style) |
| 4 | mix | 0 .. 100 | % | 100 | `0` / `50` / `100` | 38 | yes |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device.

Page 1: mesh, shake, keep, mix. No page 2, no shift row.

## 2 · Listen and rank

Scored from the DSP, to confirm by ear.

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 mesh | Jumps the heard pitch up by octaves, twelfths and beyond while thinning the tone from full to a few glassy partials; the biggest change on the machine | 5 |
| 2 shake | Nothing at 0, a faint shimmer by 30, a busy rattle of flickering partials by 100 | 3 |
| 3 keep | Short plucky colour at 10 ms to a long singing drone at 2 s that outlasts the input | 4 |
| 4 mix | On a send the dry path is already in the track, so it mostly sets how much the sieve dominates; clear but not dramatic | 3 |

## 3 · Subject

Pass record: `passes/01-subject/pass.json` (five directions, uniqueness checked: ready for pick). Sketches: `passes/01-subject/v1..v5/rest.svg`, notes and a ranking in `passes/01-subject/notes.md`.

| candidate | pattern | drawing language | subject in one sentence | what each control moves | verdict |
| --- | --- | --- | --- | --- | --- |
| v1 | P1 Section drawing | orthographic elevation | A riddle seen side-on: the harmonics fall as rods onto its mesh plate, and only rods over a hole drop through. | mesh: holes (count) · shake: riddle slides (position) · keep: passed rod length (position) · mix: bypass gate (rotation) | open |
| v2 | P2 Diagram + trace | survey plan | A surveyed plan of the sieve with sixteen numbered stations beside a long-section profile of the output spectrum. | mesh: open stations (count) · shake: lattice slides (position) · keep: peak width (shape) · mix: dry profile lifts (position) | open |
| v3 | P3 Trace as subject | patent section | Fig. 1: the sieved wave emerging from a hatched wall and ringing out between dashed envelope lines. | mesh: trace period (shape) · shake: chaff grains (count) · keep: envelope lines (shape) · mix: dry trace (scale) | open |
| v4 | P4 Stack in depth | hidden-line isometric | An exploded column of eight round test sieves, the tray at the current mesh lit and holding the kept harmonics as grains. | mesh: lit tray (position) · shake: stack slides (position) · keep: heap height (shape) · mix: feed spout (rotation) | open |
| v5 | P11 Instrument stack (stretch) | star atlas | An atlas plate of a constellation drawn as an organ rank, the kept partials the bright named stars at the pipe mouths. | mesh: named stars (count) · shake: proper-motion drift (position) · keep: kept magnitude (scale) · mix: unsieved magnitude (scale) | open |

Chosen: the owner's pick (not made here).
