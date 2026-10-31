# Toro · screen brief

> Source: `thoughtgrain/labyrinth` → `opxy/machines/toro` (definition.json, engine.cpp, display.cpp, gen_panel.py), read 2026-10-31. Protocol: `opxy/protocol.md`.
> Status: phases 0–8 done for candidate A. Device checks pending (see `review.md`).

## 0 · Screen or stock page?

Screen. Toro has an obvious thing the sound acts on: a signal being folded, filtered and pushed. The current port already draws one (Taurus), so this run is a revision pass, not a blank page.

## 1 · Intake

| | |
| --- | --- |
| Machine id | `toro` |
| Kind | synth, sdk 1.7, `"press": "page"` |
| Sounds like | Two saw/triangle oscillators into a wavefolder, a resonant 2-pole low-pass and soft-clip drive. APHX gives each key its own drift that turns to chaos at the top. |
| Controls | 8, two pages |
| Control source | existing XY definition (`opxy/machines/toro/definition.json`), ported from the OP-1 plugin `toro/toro.c` |

### 1A · Port map

The XY definition already exists, so this records the port after the fact for the parity check.

| OP-1 control | OP-1 range / curve | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Blue SPRD | osc 2 at 1.0–1.5×, linear | 0 | spread | linear 1.0–1.5 | ratio | 0.06 | keep | |
| Green FOLD | 1–8× folder gain | 1 | fold | linear 0–1 | percent | 0.18 | keep | |
| White CUT | cutoff, squared | 2 | cutoff | linear 0–1 | percent | 0.55 | keep | squared response lives in the C++; the definition's linear mapping is for previews |
| Orange RES | resonance | 3 | res | linear 0–1 | percent | 0.24 | keep | |
| Blue page 2 SHAP | saw → triangle | 4 (alt on 0) | shape | linear 0–1 | percent | 0 | keep | |
| Green page 2 NOIS | noise into folder | 5 (alt on 1) | noise | linear 0–1 | percent | 0 | keep | |
| White page 2 DRIV (0–50 %) | 1–4× soft clip, full at 50 % | 6 (alt on 2) | drive | linear 0–1 | percent | 0 | **split** | now has its whole range |
| White page 2 APHX (50–100 %) | per-key drift over full drive | 7 (alt on 3) | aphx | linear 0–1 | percent | 0 | **split** | **no longer implies full drive**; see review |
| Velocity → APHX accent | deeper drift on hard notes | none | | | | | **drop** | the XY applies velocity after the engine |

Integer conversion: the port takes the top 15 bits of each Q31 word, so every knob curve matches the OP-1's 0..32767.

### 1B · Definition review

`lint_definition.py` → **0 errors, 0 warnings** (sdk 1.7, 8 parameters, two pages, 16 text slots).

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | pass | spread, fold, cutoff, res, noise, drive, aphx all rise; shape rises toward triangle, which is fine as long as the drawing makes "toward triangle" visible |
| Header values in real units, ≤ ~5 chars | pass | spread shows its ratio `1.xx`; the rest are amounts 0–100. Fold could show `1×`–`8×` as header text; optional |
| Defaults plainest useful; presets sound good | pass on defaults (noise, drive, aphx, shape at 0); **presets pending device** (by ear) | |
| Engine page holds only the sound's own parameters | pass | aphx is per-key drift built into the voice, not a stock-style LFO or mod amount |
| Page 1 holds what's played most | pass | spread, fold, cutoff, res are the OP-1's page 1 |
| Port parity | **flag** | On the OP-1, APHX sat on top of full drive. On the XY, aphx with drive at 0 is a cleaner sound than any OP-1 APHX setting. The `Labyrinth` preset (drive 0.8, aphx 1.0) is a little gentler than its OP-1 counterpart (full drive). Worth a line in the machine README, or set that preset's drive to 1.0 if parity matters more |
| Saved sounds compatible | n/a | not in the open-xy catalog yet; once it is, slot order and mappings freeze |
| `id` final | pass | `toro` |

### Captions

| # | label | range | unit | default | caption 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | spread | 1.0–1.5 | ratio | 0.06 | `1.00` / `1.25` / `1.50` | 51 | yes, tight |
| 2 | fold | 1–8× | amount | 0.18 | `0` / `50` / `100` | 38 | yes |
| 3 | cutoff | 0–1, squared | amount | 0.55 | `0` / `50` / `100` | 38 | yes |
| 4 | res | 0–1 | amount | 0.24 | `0` / `50` / `100` | 38 | yes |
| 5 | shape | saw → tri | amount | 0 | `0` / `50` / `100` | 38 | yes |
| 6 | noise | 0–1 | amount | 0 | `0` / `50` / `100` | 38 | yes |
| 7 | drive | 1–4× clip | amount | 0 | `0` / `50` / `100` | 38 | yes |
| 8 | aphx | 0–1, cubic top | amount | 0 | `0` / `50` / `100` | 38 | yes |

Width: characters × 0.64 × 20. Measured in Univers Next Pro Light: **pending device**. `1.25` at an estimated 51 px is the one to measure first.

Page 1 (played most): spread, fold, cutoff, res · Page 2: shape, noise, drive, aphx · Repeated controls: none.

Labels are all ≤ 8 characters. display.cpp passes them capitalised; `page_header` lowercases them, so the header is correct.

## 2 · Listen and rank

Scored from the DSP and labyrinth's README, not by ear. **Confirm or correct these by ear** before phase 4, since they size every control's visual travel.

| # | audible effect across 0 → 100 | score |
| --- | --- | --- |
| 1 spread | unison → osc 2 up to a fifth; beating, then an interval | 4 |
| 2 fold | 1× → 8× folder gain; clean to buzzy, harmonically rich. The machine's signature | 5 |
| 3 cutoff | closed to open, squared response so most change is in the top half | 5 |
| 4 res | resonant peak; audible from ~40, whistly at the top | 3 |
| 5 shape | saw → triangle; darker, softer, folds differently | 3 |
| 6 noise | noise into the folder; grit, then hiss | 2 |
| 7 drive | 1× → 4× soft clip; louder, denser, compressed | 3 |
| 8 aphx | per-key drift: subtle below 50, falls apart in the top quarter | 2 → 5 (curve) |

## 3 · Subject

### The current design, scored against the protocol

Taurus is a strong subject: points and hairlines on black suit the screen, and Cutoff as Aldebaran's magnitude and Spread as the horn stars both read well. It falls short on the rules that matter most for a player learning by turning:

| Rule | Where it misses |
| --- | --- |
| Every control reads at 0/50/100 without playing | **Fold** (score 5) only shows as a brief sky turn on a note; turning it with no note changes nothing. **Noise** only shows while notes are held. **Aphx** only changes comet odds. **Res** shows mainly as spin on notes. |
| No on/off-only controls | **Drive** shows a wash only above 60 and nothing below. Aldebaran's spikes appear at 30 and its halo at 60, but the magnitude scales smoothly, so Cutoff passes. |
| Seen as much as heard | Fold, the loudest control, has the least visual travel at rest. |
| Idle is still | A comet crosses the idle sky about every 9 s. |
| Short, decelerating motion | The sky eases back by 1/12 per frame (frame-rate dependent, well past 0.2 s). The Pleiades keep spinning up to ~2.5 s with high Res. |
| ~20 changed nodes per frame | **Estimated over.** A note turns the whole sky, moving ~9 stars, 8 joins, the Pleiades (7 + ring), Aldebaran (3) and up to 8 comet nodes, plus 12 twinkles while held. At steady 16ths the sky never settles, so roughly 40–50 changed nodes per frame. Needs measuring with `display()` on the host. |
| Parts ≥ 3–4 px, text ≥ 10 px read in play | The field stars are 1–2 px (decorative, acceptable). "Pleiades", the Greek letters and the RA/Dec line are small, low-contrast grey text. |

### Candidates

| | Pattern | What each control moves | Verdict |
| --- | --- | --- | --- |
| **A · Taurus, revised** | P5 field + figure | spread: horn stars out (kept) · **fold: the ecliptic, one mutable outline across the chart, folds back on itself 1→8 times** · cutoff: Aldebaran's magnitude (kept) · res: Pleiades tighten and the ring brightens at rest, short spin on a note · shape: horn line bends (kept) · **noise: more field stars come out**, twinkle while held · **drive: the Milky Way band widens and steps up through greys** · **aphx: a standing comet whose tail kinks more as aphx rises**, plus launches on notes only | Recommended. Keeps what works and the screen's identity. Fold gets the strongest channel (shape) and draws exactly what a wavefolder does. The sky turn is retired, which is where most of the redraw cost came from. |
| **B · The bull, rebuilt** | P1/P6 figure | the OP-1 rig in grey ribbons: horns spread, plate folds, eyes for cutoff, lasso for res | Continuity with the OP-1 plugin, but the README already tried and dropped it. It's figure-heavy on nodes, and the original art is mine to reuse but was drawn for 320 × 160 colour. |
| **C · Fold diagram + trace** | P2 diagram + trace | left: a wave hitting two mirrors that fold it (fold, shape, noise); right: the output trace (cutoff, res, drive) | The clearest teacher of what toro does, and cheap. It loses the character, and it looks like every other synth. |

**Chosen:** A, Taurus revised (chosen 2026-10-31). Scores in phase 2 confirmed as written.

## 4 · Map and budget

| # | score | channel | part (node) | travel 0 → 100 | what the player sees |
| --- | --- | --- | --- | --- | --- |
| 1 spread | 4 | position | β, ζ (17, 18) + their joins | β +44 px out, −8 px up; ζ +44 px out, +2 px down | the horns open |
| 2 fold | 5 | **shape** | ecliptic, mutable outlines (0, 1) | an arch (1×) → 8 folds across 432 px | the ecliptic folds back on itself, like the wave does |
| 3 cutoff | 5 | scale + shade | Aldebaran spike, core, halo (10–12) | core 0.5 → 1.9×, spike 0.3 → 1.5×, `#4B4B4B` → `#CDCDCD` | the eye star goes from a point to a blaze |
| 4 res | 3 | scale + shade | Pleiades (30–36), ring (37–44) | cluster 1.0 → 0.6×, ring `#323232` → `#7D7D7D` | the cluster pulls tight and its ring lights |
| 5 shape | 3 | position | β, ζ (17, 18) | both tips lift 22 px | the horns curl up |
| 6 noise | 2 | count | field stars (53–64) | 2 → 12 stars out | the sky fills with stars |
| 7 drive | 3 | position + shade | Milky Way, 3 lines (65–67) | lines spread 0 → ±12 px, `#323232` → `#7D7D7D` | the band widens and brightens |
| 8 aphx | 2→5 | rotation + scale + shade | standing comet (45–48) | tail 42 → 84 px, kinks 0 → ±35°, following the engine's gentle-then-wild curve | the comet's tail goes from straight to tangled |

Spread and shape share the horn stars but on different axes (out vs up); the contact sheet shows they stay distinct.

```json
"display": {"stateBytes": 156, "stateAlignment": 4,
            "paths": 2, "points": 64, "nodes": 68, "texts": 16, "palette": 16}
```

Unchanged from the current port: 2 paths (now used for the ecliptic instead of parked), 68 nodes, all 16 text slots for the two-page header. `stateBytes` will change with the new state (handoff.md lists it); re-run `lint_definition.py` after.

| case | changed nodes / frame |
| --- | --- |
| at rest | **0** (no idle comet, no twinkle without notes, nothing easing) |
| turning a control | the nodes on that control's row above, for 0.15–0.2 s; fold re-keys 2 paths once per detent |
| playing, defaults, 16ths at 120 BPM | avg ~12 · peak ~19 (Aldebaran 3, ecliptic shade 2, Pleiades 7, ≤ 3 twinkles) |
| playing, heaviest (noise, res, aphx 100) | avg ~17 · peak ~22 (adds 2 comets × 2 nodes; twinkle capped at 3 changes per frame) |

Estimates from the motion spec; **measure on the host** with `display()` before submitting.
