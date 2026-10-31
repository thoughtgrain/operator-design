# Toro · screen brief

> Source: `thoughtgrain/labyrinth` → `opxy/machines/toro` (definition.json, engine.cpp, display.cpp, gen_panel.py), read 2026-10-31. Protocol: `opxy/protocol.md`.
> Status: **revision 3**, phases 3–8 redone after the craft review (2026-10-31). Passes lint, the perceptibility gate and the side-by-side craft review. Device checks pending (see `review.md`).

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

**Chosen:** A, Taurus revised (2026-10-31). Phase 2 scores confirmed as written.

### Revision 3 · what changed and why

Revision 2 passed every gate and still looked childish. Side by side with labyrinth's first Taurus chart and MNMD at 1:1, the gap was craft, not function:

- **It mixed languages.** A flat cartoon moon, a sunburst nebula, a fan of meteor wedges, bullseye shock rings and a nested "target" disk.
- **Lines thickened into wedges** under the zoom.
- **It lost the chart's authenticity:** no grid, no labels.

So `opxy/craft.md` now sets the rules: one drawing language, three line weights that never thicken, one brightest element, no icons, and a side-by-side review before phase 7. Revision 3 redraws everything as a **star-atlas page**:

- **Restored:** your original grid, labels and figure, now completely static.
- **Cutoff:** an atlas detail inset with a leader line to Aldebaran, instead of moving the whole camera.
- **Fold:** moves to the Milky Way, drawn as isophote contours.
- **Drive:** plotted meteor trails.
- **The Moon:** an outline on a dotted ephemeris track.

Drawing language: **star atlas** (Tirion and Bečvář conventions). References: labyrinth `opxy/docs/toro_rest.png`, MNMD's MD KIT and FM STAT for line weight and restraint.

## 4 · Map and budget

| # | score | channel | part (nodes) | travel 0 → 100 | what the player sees | gate (need → got) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 spread | 4 | position | the Moon: body, phase, limb (38–47) | slides 142 px along its dotted ephemeris track | the Moon pulls away as the oscillators detune | 1.6 → 3.36 % |
| 2 fold | 5 | **shape** + shade | Milky Way isophote contours, 3 mutable outlines (0–2) | edges fold 1× → 8× (wavefolded sine), inner contours brighten as the band thickens | a soft irregular band frays into folded edges | 2.5 → 3.02 % |
| 3 cutoff | 5 | scale | the magnifier on Aldebaran: star, core, spikes, 2 neighbours (29–31, 36–37) | star radius 1.8 → 27 px; neighbours move out of the window | moving in on Aldebaran: a point becomes the star's disk | 2.5 → 3.45 % |
| 4 res | 3 | count + shade | Airy rings round the magnified star (32–35) | 1 → 4 rings, fading outward | the star rings | 1.2 → 1.35 % |
| 5 shape | 3 | shape (stepped) | Moon phase (8 phase nodes) | crescent → full | saw → triangle: sharp crescent → round | 1.2 → 1.37 % |
| 6 noise | 2 | count | faint stars (64–228) | 40 → 165 | the sky fills | 0.8 → 1.59 % |
| 7 drive | 3 | count + shade | plotted Taurid trails (48–63) | 2 → 16 trails, brighter | more meteors traced back to the radiant | 1.2 → 1.30 % |
| 8 aphx | 2→5 | position | faint stars | drift 0 → 6–26 px on the engine's curve | stars wander off their places | 0.8 → 0.98 % |
| note | | shade + scale | figure lines (20–28), Aldebaran, magnified star and spikes, one trail, Milky Way core contour, twinkle | 0.2 s brighten | the bull lights for a beat on every note | 2.0 → 2.01 % |

```json
"display": {"stateBytes": 180, "stateAlignment": 4,
            "paths": 3, "points": 64, "nodes": 229, "texts": 16, "palette": 16}
```

| case (prototype model, 60 fps, 16ths at 120 BPM) | changed nodes / frame |
| --- | --- |
| at rest | 0 |
| playing, each control held at 100 | avg 8.3–9.6 · peak 16–19 |
| turning aphx (every visible star drifts) | avg ~34 · peak ~55 for the ease; batch it (handoff.md) |

**Confirm on the host** with `display()` before submitting.

### Earlier revisions (superseded, in git history)

- **Revision 2** (`8a66b56`): a fixed chart with a full-screen camera on Aldebaran, and the sky drawn as icons. It passed the gates and failed the craft review.
- **Revision 1** (`c4aa8e9`): the chart itself changed with the controls, and it failed the perceptibility gate on five controls.
