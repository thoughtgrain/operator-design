# Spool · screen brief

## 0 · Screen or stock page?

- Subject in one sentence: a short loop of tape with one cycle written on it, read back pass after pass while it wears, wobbles and saturates.
- It earns a screen: there is one object the sound acts on (the loop and what's written on it), and every control does something physical to it.

## 1 · Intake

| | |
| --- | --- |
| Machine id | `spool` |
| Kind | synth |
| Category | engine |
| Colour | grey (default) |
| Concept | A single-cycle wave written onto a short tape loop that wears with every pass; bias and wow colour it. |
| Sounds like | A bright single-cycle tone that, held, darkens pass by pass as its high partials wear off the tape, with soft dropouts opening where the oxide thins. Wow bends its pitch once per loop revolution; bias decides whether it saturates hard (under) or goes dull and quiet (over). |
| Controls | 4: wear, wow, length, bias (stock header) |
| Control source | new (the DSP is being written for this machine; the definition is drafted from that intent) |

### 1A · Definition (new machine)

No source platform, so the "port map" is the intended DSP, control by control.

| DSP quantity | range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| erosion per pass (high-partial loss + dropout growth) | 0..1, square law, 0 | 0 | wear | `power`, max 1, exponent 2 | `percent` | 0 | keep | Square law gives fine control where wear is slow (most musical range). Header shows the mapped value, so the knob's halfway reads `25` |
| wow depth (pitch deviation once per revolution, up to ±40 cents) | 0..1, linear, 0 | 1 | wow | `linear` 0..1 | `percent` | 0 | keep | Colouring control, defaults off |
| loop period (wear and wow advance once per revolution; one splice dip per revolution) | 0.05..2 s, exponential, 0.32 s | 2 | length | `exponential` 0.05..2 | `duration` | 0.5 (= 0.316 s) | keep | Real unit is time |
| record bias offset from optimum | −1 (under) .. +1 (over), linear, 0 | 3 | bias | `linear` −1..1 | `bipolar` | 0.5 (= 0) | keep | 0 is correct bias: neither clipping nor dulled |

Presets: `Fresh` (all defaults) and `Attic` (wear 0.62, wow 0.35, length 0.38, bias 0.3: a worn, slightly under-biased loop with audible wow).

`resources.display` is a placeholder (paths 1, points 64, nodes 24, palette 6, texts 0) until phase 4 sets it from the chosen subject. Several variants need more than one path (see their risks).

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/spool/definition.json` → **0 errors, 0 warnings**. Nothing to justify.

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | pass | more wear, more wow, a longer loop, more bias (under → over) |
| Header values in real units, ≤ ~5 chars | partly, **pending device** | `duration` for length; see captions: `316ms` doesn't fit, a header override to `0.32s` does in the fallback font |
| Defaults plainest useful; presets sound good (by ear) | pass by design, **pending ear** | defaults are a clean, correctly biased loop with no wear and no wow, i.e. the written cycle as is |
| Engine page holds only the sound's own parameters | pass | no envelope or LFO; wow is the tape's own transport, not a mod source |
| Page 1 holds what's played most | pass | one page |
| Port parity: nothing silently lost | n/a | new machine |
| Saved sounds compatible (if released) | n/a | not released |
| `id` final | pass | `spool` |

One design question for the owner: with wear at 0 the loop never wears, which is the plainest sound but makes history-based subjects (v3, v5) show identical passes at rest. I kept 0 as the rules ask; a small default (e.g. 0.2 → 4 % per pass) would be a deliberate departure and is the owner's call.

### Captions

| # | label | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | wear | 0..1 (power 2) | % | 0 | `0` / `25` / `100` | 38 px | yes |
| 2 | wow | 0..1 | % | 0 | `0` / `50` / `100` | 38 px | yes |
| 3 | length | 0.05..2 s (exp) | s | 0.5 | `50ms` / `316ms` / `2.0s` as `duration` might show them; proposed override `0.05s` / `0.32s` / `2.00s` | `316ms` 64 px est., 59 px rendered (no); `0.32s` 64 px est., 50 px rendered | no as `ms`; override borderline, **pending device** |
| 4 | bias | −1..1 | bipolar | 0.5 | `-100` / `0` / `+100` | 51 px | yes, tight |

Width estimate: characters × 0.64 × 20; rendered widths are in the preview's fallback font. Measured in Univers Next Pro Light: **pending device**. The sketches draw the proposed `0.32s` override.

Page 1: wear, wow, length, bias. No page 2.

## 2 · Listen and rank

Scored from the DSP, to confirm by ear. There's no audio render yet; scores come from what the model does across 0 → 100.

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 wear | Held, a bright cycle dulls toward a sine within a few passes at 100 and dropouts open; at 0 nothing changes. Dramatic, and it keeps working the longer a note sounds | 5 |
| 2 wow | Pitch sways once per revolution, up to ±40 cents; subtle below ~30, obvious above | 3 |
| 3 length | A soft splice dip once per revolution at any setting, and the pace of wear and wow; with wear and wow at 0 it's only the dip | 2 |
| 4 bias | Under: louder, harder clipping and grit; over: duller and ~2.5 dB quieter. Both ends clearly audible, centre is clean | 4 |

## 3 · Subject

Pass `passes/01-subject/` (state `ready_for_pick`, uniqueness checked). Directions were assigned before drawing; each variant has `candidate.json` and a rest sketch, all generated by `passes/01-subject/sketch.py`. Notes and a ranking are in `passes/01-subject/notes.md`.

| candidate | pattern | drawing language | subject in one sentence | verdict |
| --- | --- | --- | --- | --- |
| v1 | P2 Diagram + trace | typeset diagram | Labelled tape path (loop, rollers, heads) on the left, the cycle the play head reads on the right | owner's pick |
| v2 | P3 Trace as subject | orthographic elevation | The magnetised waveform bright along a strip of tape in front elevation, splices and a dimension line | owner's pick |
| v3 | P4 Stack in depth | survey plan | Passes of the loop as profiles stacked back in depth, now in front | owner's pick |
| v4 | P5 Field and figure | patent section | The record head's core in patent section on a perspective plane of tape, worn segments in a strip | owner's pick |
| v5 | P14 Loom (stretch) | hidden-line isometric | Each pass woven as a row of isometric slabs; wear shows as rows that stop matching | owner's pick |

The pick is the owner's; nothing is selected.
