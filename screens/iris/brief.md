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

## 3 · Subject

Five candidates, one per direction from `design_pass_start`, drawn by five parallel `opxy-designer` agents. Pass record: `passes/01-subject/pass.json` (submitted 0 problems; every pair differs in angle and language, subject overlap ≤ 0.16; body pixels differ 10.8–25.4 % pairwise at 1:1, measured from Playwright renders since rsvg-convert isn't installed). Side by side: `passes/01-subject/sheet.png`.

| candidate | angle | drawing language | subject in one sentence | verdict |
| --- | --- | --- | --- | --- |
| v1 | one detail at large scale | exploded view, hidden-line 3D | the mixed wave as a block's cut edge, its four wave laminations slid off along a pin | crowded to the right; the mix isn't large |
| v2 | the object in the name | single-weight contour | a rainbow of four bands over a horizon, each band its waveform bent along its cone of light, the morph band lit | **chosen** |
| v3 | the mechanism | hatched mass | an iris diaphragm over a sliding plate engraved with the four waves; what shows through is what sounds | strong idea; the housing outweighs the lit wave |
| v4 | the material, close | edge-lit silhouette | four wave trains crossing one water surface | reads as a terrain plot |
| v5 | one scene | detailed line art | a prism splits one beam into four wave rays; a slit on a rail picks which pass | jaws leave the frame at the extremes; busy at the prism |

Chosen: **v2, the rainbow**, picked by the owner on 2026-11-17. It's the machine's name drawn literally, it reads at once at 1:1, and every control has its own part. Grey only (owner's decision), so it's a rainbow by its form.

Angle: the object in the name. Pattern: none. Language: single-weight contour, every line a 1.5 px closed ribbon projected from one 3D model (four cones of light round the anti-solar point, one camera at the horizon); the lit band is the one brightest element. Reference: `library/theseus-tower`.

| control | what moves |
| --- | --- |
| morph | the light moves across the bands, sine (outer) to saw (inner); the band under the window is lit, the others set by their mix weight |
| overlap | the neighbouring bands' cone angles pull toward the lit band, from four arcs standing apart to arcs crowding one radius with their waves crossing |
| spread | each band takes its own cycle count round the bow, so waves that line up radially at 0 drift out of step along the arc |
| tone | the drawn waves lose their corners: sharp at 100, smooth humps at 0 |
| skew | the square's teeth narrow to pulses, the triangle leans into a ramp, the sine bunches; the saw arc doesn't change |
| phase | each band's wave slides along the arc against the band outside it, so aligned crests shear into a diagonal (up to an eighth of a cycle per band, matching the engine) |

Carried into the frames pass from v2's risks: the target-ring look when waves are smooth (overlap 0, tone low), the saw band faint at rest, the lit band getting shorter as morph rises, and a device question: each band's wave at up to 64 points per mutable outline, four outlines in all.

## 4 · Map and budget

### The structural decision

v2 draws every band as a long wave ribbon, and that doesn't fit the device. A ribbon of N centreline points is a 2N-point outline, the device reshapes at most 4 outlines of at most 64 points each, and one band at 11 cycles needs a few hundred points. Four live bands are out of reach, so I split the drawing by what it shows:

- **The four bands are the components, drawn in grey as fixed shapes.** Each band is a chain of one-cycle nodes, one node per wave cycle, authored once per band at its own size and placed along its arc by `display()` with a translation and a turn. Moving the band (overlap), stretching its cycles (spread) or sliding it along the arc (phase) is a move, a turn and a uniform scale, never a reshape.
- **The one bright line is the mix**: the actual output wave, the window-weighted sum of the four bands, run through Tone's filter, riding at the radius Morph sets. It's drawn with the four mutable outlines, a quarter of the arc each (32 centreline points per outline, so about 10 per cycle). Every control that changes the sound's shape (morph, overlap, tone, skew, phase, and spread's beating along the arc) changes this line for real, because it's computed from the same maths as the engine.

That makes the picture honest in a way v2 wasn't: the grey bands are what goes in and the bright line is what comes out. Morph slides the bright line inward across the bow from the sine band to the saw band, and its shape follows.

The bow is a true semicircle: the sun on the horizon behind the viewer (a sunset bow, the tallest a rainbow gets), seen by a camera looking straight at the anti-solar point. It's still one 3D model through one camera (`craft.md`), and the circular arcs let display() place cycles by angle with no perspective stretch to fake. v2's 13° sun splayed the feet; this fixes that and the device cost together.

| # | control | score | channel | part (node) | travel 0 → 100 | what the player sees |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | morph | 5 | position + shape | mix line (nodes 0–3) | radius from the outer (sine) band to the inner (saw), 3 band spacings (≥ 36 px), shape sine → saw | the bright line walks inward across the bow and sharpens from a smooth swell to a ramp |
| 2 | overlap | 4 | position | grey band chains | neighbours' radii pulled toward the bright line, up to 80 % of the way; the mix line takes their shapes in | the bow tightens round the bright line; at 100 the four bands crowd it and their waves cross |
| 3 | spread | 4 | scale + shape | band cycle nodes; mix line | band i's cycle length × (1 + 0.12 (i − 1.5)) (scale 0.82–1.18 at the outer bands); the mix line's amplitude beats along the arc | the bands' crests fall out of radial line, and the bright line swells and thins round the bow |
| 4 | tone | 4 | shape (two parts) | mix line; band chains (raw ↔ rounded) | the mix's drawn bandwidth from 1.4 to 11 harmonics; the band cut sweeps outward: saw rounded below 65 %, square below 45 %, triangle below 20 %, the sine never | the bright line's corners round off, and band by band from the inside the teeth melt into smooth humps |
| 5 | skew | 3 | shape | mix line only | breakpoint 50 % → 5 % on the sine, triangle and square parts of the mix | the bright line leans; on the square it narrows to spikes. The grey bands don't lean: they're fixed one-cycle nodes on the device |
| 6 | phase | 2 | position | band cycle nodes; mix line | band i slides i/8 of a cycle along its arc (the saw, 3/8) | the bands' crests shear into a diagonal; the bright line hollows where bands overlap |

Tone needed its second part. The first frames passed every number but one: Tone scored 0.94 % against a 1.6 % floor. On the default triangle mix there's almost nothing above the fundamental for a low-pass to take, and a line at about 10 points per cycle can't draw past the 5th harmonic anyway. So the drawn bandwidth is fitted to what the line resolves (0.5–3.5 octaves, written in `gen_frames.py`), and the bands carry the rest. They run from plain (outside) to bright (inside), so a low-pass is drawn as what it does to that order: the inner bands lose their corners first. The cut bands drop one grey step and switch to a pre-drawn rounded chain. The first try (darkening cut bands with no change of shape) passed at 2.28 % but the three Tone frames still looked alike on the contact sheet, so I replaced it with the change of shape.

Note response: while notes are held, the mix line travels along the arc (its phase advances, a rewrite of the 4 outlines per frame) and steps up from `#AFAFAF` to `#CDCDCD`. On hold ended it settles in 0.15–0.2 s and stops. At rest nothing moves.

```json
"display": {"stateBytes": 60, "stateAlignment": 4,
            "paths": 4, "points": 64, "nodes": 140, "texts": 16, "palette": 5}
```

Nodes: 0–3 the mix outlines (mutable outlines are always the first nodes), 4–11 the two-page header bar, then 4 bands × 16 raw cycle nodes and 4 × 16 rounded ones (64 + 64; 16 covers the densest band at full spread, the rest park hidden): 140. The ground mask and the horizon are static art, not nodes: they never move, and a bound black mask would take its palette entry's paint. Palette: the mix (rest, held) and three band greys, 5 entries. stateBytes 60 (`sizeof(DisplayState)`: the header's 20, six eased controls, travel, speed, the path key, a flag). Texts: the 16 `page_header.hpp` takes for two pages. Palette: the mix (lit, held), three band greys by mix weight, the horizon grey, black.

| case | changed nodes / frame |
| --- | --- |
| at rest | 0 |
| playing, defaults | 4 (the mix outlines) |
| playing, heaviest (spread 100: the mix beats, so its outlines change every frame anyway) | avg 4 · peak 4. Turning a knob moves up to 64 band nodes, but only during the turn. |

The redraw risk is the outline rewrite, not the count: 4 × 64 points every frame while held. It's **pending device**; if it's too heavy, the travel can step every second frame.

## 5 · Frames

Frames pass 02 (`passes/02-frames/`): five rest-frame variants of the rainbow from `frame_directions` (off-axis low, full-bleed elevation, centred hero with a density gradient, low-horizon section, three-quarter column-affine), each drawn by its own `opxy-designer` agent to section 4's structure. All five lint clean; every pair differs by 9.3–11.9 % of body pixels at 1:1 (floor 4 %). **v3, the centred bow, picked by the owner on 2026-11-17**: the calmest of the five, with black all round, and the cycle count rising inward (11, 13, 14, 16) so the wavelength on screen halves from the sine band to the saw band, the way a real bow's wavelengths order. That density is what stops four nested arcs reading as a target.

The set is generated by `gen_frames.py` (from v3's generator, with the fixes in section 4) into `frames/`: rest, playing, and c1–c6 at 000/050/100.

- `lint_frame.py frames/*.svg --two-page --definition definition.json`: 0 errors, 0 warnings, 20 frames.
- `perceptibility.py` (scores 5, 4, 4, 4, 3, 2), from Playwright 1:1 renders because rsvg-convert isn't installed here:

| control | need % | 0→100 % | 0→50 % | 50→100 % | span | |
| --- | --- | --- | --- | --- | --- | --- |
| morph | 2.50 | 10.22 | 10.89 | 10.54 | 321 | ok |
| overlap | 1.60 | 7.73 | 8.12 | 6.58 | 319 | ok |
| spread | 1.60 | 8.94 | 8.13 | 8.03 | 316 | ok |
| tone | 1.60 | 3.90 | 2.24 | 1.77 | 290 | ok |
| skew | 1.20 | 2.42 | 1.98 | 1.96 | 290 | ok |
| phase | 0.80 | 7.18 | 5.36 | 6.20 | 290 | ok |
| note response | 2.00 | 3.23 | | | 292 | ok |

- Band greys start at `#646464` (3.55:1), not `#4B4B4B`: a band out of the mix is still one of the four inputs, so it's a meaningful part and needs ≥ 3:1 (`accessibility.md`). It also fixed the faint saw band every frame designer flagged.
- Contact sheet: `contact.svg` / `contact.png`. Looked at 1:1: every control's three frames read differently (Tone only after the change described in section 4).

### Frames against the device code

`display.cpp` exists in operators-xy, so I ran it on the host against a small stand-in for the SDK's draw API, rendered the nodes it placed with the authored geometry from `panel.svg.fragment`, and compared that to these frames at 1:1. That's a check of the maths, not of the SDK.

- The first comparison caught a lie in the frames: the design generator leaned the grey bands with Skew, and the device can't, because the bands are fixed one-cycle nodes. I regenerated the frames with the bands unskewed; Skew still passes on the mix line alone (2.42 % against 1.2 %).
- After that, the device output differs from the frames by 0.2–1 % of the body for most controls (antialiasing at the edges), 2–3.4 % at Overlap 100 and Spread 50–100 (the device scales whole cycles, so a band pulled to a larger radius or stretched by Spread gets slightly taller waves and a slightly heavier line, up to about 1.35× and ~2 px in the worst corner), and 3.8 % on `playing` (a different moment of the same motion).
- `perceptibility.py` on the device renders: **pass**. Morph 10.20, overlap 7.69, spread 9.37, tone 3.96, skew 2.44, phase 7.31, note response 2.59.
- At rest the mix outlines are written once and never again; while held they rewrite every frame.
