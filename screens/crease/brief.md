# Crease · screen brief

## 0 · Screen or stock page?

- Subject in one sentence: the track's signal as a strip of paper pushed past its edges and folded back on itself, the folds placed by symmetry and softened by the paper.
- It earns a screen: a wavefolder has one thing it acts on (the signal's shape) and one mechanism (the fold), and all four controls change that fold in ways you can draw. Which picture of it is the subject pass's question (`passes/01-subject/`).

## 1 · Intake

| | |
| --- | --- |
| Machine id | `crease` |
| Kind | effect (SDK 1.7: draws its own send page, stock header, no shift row) |
| Category | effect |
| Colour | grey (default) |
| Sounds like | A wavefolder for any track: quiet input passes clean, louder input is pushed past the paper's edge and folds back, piling up bright odd harmonics that sweep as the level moves. Sym tips the fold so even harmonics come in; paper rounds the creases so the top end softens. |
| Controls | 4: crease, sym, paper, mix |
| Control source | new (definition drafted here; "source" is the DSP below) |

Shift row: none. A fold-shape enum (triangle / sine / Lockhart) was considered, but paper already blends sharp to soft continuously, and a shift row costs Shift's fine steps (`constraints.md`, Effect shift row). It doesn't earn its place yet.

### 1A · Definition (new machine)

The DSP the definition is written against: `y = fold(crease · x + 0.6 · sym, paper)`, `out = mix · y + (1 − mix) · x`, where `fold` reflects into ±1 with a triangle fold blended toward `sin(π/2 · u)` by paper. The same model draws the sketches (`passes/01-subject/sketch.py`).

| source control | range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fold gain | ×1 … ×8, exponential | 0 | Crease | exponential 1..8 | ratio | 0.3333 (×2.00) | keep | ×1 is unity: nothing folds. ×2 is one clean fold, the plainest setting that still sounds like the effect |
| bias | −1 … +1, linear | 1 | Sym | linear −1..1 | bipolar | 0.5 (0) | keep | 0 is symmetric (odd harmonics only) |
| fold softness | 0 … 1, linear | 2 | Paper | linear 0..1 | percent | 0.4 (40) | keep | 0 a sharp triangle crease, 100 a sine fold |
| dry/wet | 0 … 1, linear | 3 | Mix | linear 0..1 | percent | 1.0 (100) | keep | a send effect returns wet by default |

Presets: Plain (the defaults), Origami (×5.1, sym +0.24, paper 12: many sharp folds, a little even harmonic), Tissue (×3.1, sym 0, paper 85, mix 60: soft and half dry).

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/crease/definition.json` → 0 errors, 0 warnings, 2 notes (effects have no browser preview yet; effect resources only checked for structure). Nothing to justify.

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | pass | more crease, more sym (toward +), more paper (softer), more mix (wetter) |
| Header values in real units, ≤ ~5 chars | pass | `2.00` ratio, bipolar sym, percents; widths below |
| Defaults plainest useful; presets sound good (by ear) | pass, **pending device** | crease defaults to ×2, not ×1: ×1 is a bypass, and the effect page's plainest useful sound is one fold. Presets by ear pending |
| Engine page holds only the sound's own parameters | pass | four fold parameters, no envelope or LFO |
| Page 1 holds what's played most | pass | one page |
| Port parity: nothing silently lost | n/a | new machine |
| Saved sounds compatible (if released) | n/a | unreleased |
| `id` final | pass | `crease` |

### Captions

| # | label (≤ 8, lower) | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | crease | ×1 … ×8 | ratio | 0.3333 | `1.00` / `2.83` / `8.00` | 51 | yes, tight |
| 2 | sym | −1 … +1 | bipolar | 0.5 | `-100` / `0` / `+100` | 51 | yes, tight |
| 3 | paper | 0 … 100 | % | 0.4 | `0` / `50` / `100` | 38 | yes |
| 4 | mix | 0 … 100 | % | 1.0 | `0` / `50` / `100` | 38 | yes |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device. How `bipolar` renders (±100 or ±1.00) is the SDK's; four characters either way.

Page 1 (played most): all four · Page 2: none · Repeated controls: none.

## 2 · Listen and rank

Scored from the DSP, to confirm by ear.

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 crease | clean at ×1 to seven-odd folds at ×8, a sweep from sine to a bright buzzy stack of harmonics: the effect itself | 5 |
| 2 sym | silent at ×1; past one fold it brings in even harmonics and moves where the folds land, a clear timbre shift either side of centre | 3 |
| 3 paper | sharp to soft corners: the upper harmonics roll off, audible but a tone change, not a character change | 2 |
| 4 mix | dry to folded; strong at high crease, moderate at the ×2 default | 3 |

## 3 · Subject

Pass 01 is open with five directions (`passes/01-subject/pass.json`, `notes.md`). The pick is the owner's.

| candidate | pattern | drawing language | subject in one sentence | verdict |
| --- | --- | --- | --- | --- |
| v1 | P4 Stack in depth | patent section | the strip folded into plies, a patent figure of the stack, the wave inked on the top ply | open |
| v2 | P10 Voice field | hidden-line isometric | a slab field whose heights are the fold surface, creases as lit ridges | open |
| v3 | P15 Cell field | star atlas | the harmonics as a band of square cells across an atlas plate | open |
| v4 | P1 Section drawing | engineering schematic | a folding press in section, the web festooned between two roller banks | open |
| v5 | P9 One-bit ink (stretch) | oscilloscope trace | a one-bit paper streamer folded into the output wave on a scope graticule | open |

Chosen: pending the owner's pick.
