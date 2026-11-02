# Constraints

The hard numbers I design against. Every line points at its source so I can re-check it when the SDK moves. If this file and open-xy disagree, open-xy is right and this file is stale.

Sources, pinned to what I read on 2026-11-02:

- **[display]** open-xy `docs/display.md` on `staging` (598e121, 2026-11-01)
- **[ux]** open-xy `docs/ux.md` on `staging` (same)
- **[api]** open-xy `docs/api.md` on `staging` (same)
- **[tmpl]** open-xy `sdk/platform/opxy-1.2.1/screen.svg`
- **[pr260]** open-xy [PR #260](https://github.com/etcetc000/open-xy/pull/260), "design principles, screen budget and device pitfalls": **open, not reviewed or merged**. I keep its rules as house rules because they match what I've seen on the device, but they aren't SDK law yet. If it merges, these become [display]/[ux]; if it changes or closes, I revisit them.
- **[te]** teenage.engineering/products/op-xy
- **[house]** my own rule, for this repo's identity; open-xy doesn't require it

## Canvas

| Rule | Value | Source |
| --- | --- | --- |
| Drawable screen | **480 × 220 px**, black | [tmpl], [ux] |
| Panel spec | TE lists the panel as 480 × 222. I design to the SDK's 220 because that's what machines draw into. | [te] |
| Stock header | y 0–20: a stepped grey bar, eight 60 × 20 steps; four titles (10 px) over four values (20 px) | [tmpl] |
| Machine artwork | Starts below y = 20. Covering the top 20 px hides the stock header (then I draw my own). | [display] |
| Two-page header | Occupies y 0–38. Keep other artwork below ~38. | [ux] |
| Control columns | Four, 120 px wide. Titles at x `5 + 120i`, values at x `65 + 120i`. | [ux] |
| Coordinate range | Nodes/texts may sit at x −64..640, y −64..320 (Q10). Hidden parks at (640, 320). | [display] |

## Colour

Grey is the default here, on purpose. The OP-XY's own screens are grey, and the point of this repo is that a machine looks like part of that instrument. open-xy itself now allows colour (optional guidance in [ux], and a developer-authored grayscale variant or automatic conversion in [display]), so colour is a legal choice; it's just not the default. Colour is an **override**, and it lives in the harness's MCP config, not in a conversation: the server only accepts colour when its config sets `OPXY_COLOUR=allow` (`python3 mcp/setup.py <client> --colour`). Each harness (Claude Code, Claude Desktop, Codex, LM Studio, Ollama) opts in separately, so a person decides it once, in a file, and no agent can switch it on by asking. The repo's own `.mcp.json` leaves it off.

| Rule | Value | Source |
| --- | --- | --- |
| Default palette | Grey only. Up to 16 palette entries per machine. | [house], [display] |
| Colour override | Off unless the harness's MCP config sets `OPXY_COLOUR=allow`. Then frames may use colour (`lint_frame.py --colour`), and the brief records why this machine uses it | [house] |
| Colour needs a grayscale design | With the override, the machine also ships `panel.grayscale.svg.fragment` (`"graphics": {"grayscale": …}`, `"sdk": "1.5"`), designed as carefully as the colour one, never left to automatic conversion. Same bound IDs, element types, origins, fill-vs-none and outline topology; every paint grey | [house], [display] |
| Colour roles | Two to four accent hues, each with a role (an oscillator, a parameter group, a signal path), kept the same across pages, presets and animation; a role table in the brief: role, colour, its grey, and one more cue that isn't colour | [ux] |
| Colour is never the only cue | The grayscale version must read on its own, so every hue difference also has a shape, label, position or outline difference | [ux] |
| Red | Stock uses bright red for recording and parameter locks. I never use red in machine art, colour override or not, so red keeps its meaning. | [te], [house] |
| Header greys | Bar steps `#000000 #323232 #4B4B4B #646464 #7D7D7D #969696 #AFAFAF #CDCDCD` | [tmpl] |
| Header text | `#CBCBCB` on the dark half, `#000000` on the light half | [tmpl], [ux] |
| Inactive page row | Titles `#5A5A5A`, values `#707070` | [ux] |
| Meaning of grey | Grey is inactive, bright is active | [ux] |

## Type

| Rule | Value | Source |
| --- | --- | --- |
| Device font | Univers Next Pro Light (`font-family="UniversNextPro-Light"`) | [ux], [tmpl] |
| Header sizes | Titles 10 px; values 20 px edited, 13 px inactive | [ux] |
| Minimum | Nothing under ~8 px | [ux] |
| Labels | One or two words, ≤ 8 characters, lower case | [ux] |
| Header values | Real units, ≤ ~5 characters. A 20 px value has ~53 px before the next column; `5.5mm` needs 64. Measure in the device font, don't count characters. | [ux] |
| Text slots | 0–32, ≤ 23 characters each; more than 4 needs `"sdk": "1.3"`, more than 16 `"sdk": "1.7"` | [display] |
| Header text override | `header[i]` replaces the stock value at position `i` (≤ ~5 characters); an empty string keeps the stock value | [display] |
| Text at rest | A layout must read at unit scale; scaling text is momentary decoration | [ux] |

## Frame budget (what `definition.json` declares)

| Field | Limit | Source |
| --- | --- | --- |
| `paths` (mutable outlines) | 0–4; they are nodes `0..paths-1` | [display] |
| `points` per outline | 2–64 | [display] |
| `nodes` | `paths`..512; more than 256 need `"sdk": "1.8"` | [display] |
| `texts` | 0..32; more than 4 need 1.3, more than 16 need 1.7 | [display] |
| `palette` | 1–16 | [display] |
| Node scale | Uniform only, positive, ≤ 2 | [display] |
| Node turn | Unit vector; `sweep(value, half)` up to ±1800 tenths of a degree | [display] |
| Redraw | ~**20 changed nodes per frame** on average while notes sound, low peak, at every setting including the heaviest; **zero at rest**. open-xy's CPU profiling leaves graphics out, so this cost only shows on the device | [pr260]; [ux] for still at rest |
| Path keys | Change a path's `key` only when its points change. A key that includes time redraws the whole path every frame. | [display]; time-in-key: [pr260] |
| Moving fills | Expensive. Allowed where they earn it; check heavy ones on the device. | [pr260] |

## Drawing on the device (preview won't show these)

| Rule | Value | Source |
| --- | --- | --- |
| Outlines enclose area | A line is a thin closed ribbon, never a stroke traced out and back | [display] |
| Near-reversal | Treat a turn within ~2.5° of straight back as a fault; give sharp tips a small flat end | [display] (turns straight back); 2.5°: [pr260] |
| Point spacing | Neighbouring points ≥ 1/8 px apart (both edges of a ribbon too) | [pr260] |
| Closing edge | Last→first edge ≥ 1/4 px; start the outline where both edges are long | [pr260] |
| Fills | Only elements authored with a fill ever fill; mutable outlines always draw hollow | [display] |
| Subpaths | Every `path`, bound or not: one subpath, ≤ 64 points | [pr260] |
| Touching parts | Parts that meet share one outline or the same pivot/transform | [pr260] |
| Bound path shape | Exactly `M`, `points − 1` × `L`, `Z`; no fill; every point distinct | [display] |
| Bound transforms | `matrix(1 0 0 1 x y)` or none | [display] |
| Mutable outline extent | Points within ±64 px of the node's origin (place the node, author points relative to it) | [display] |
| Numbers | ≤ 4 fractional digits, no exponent notation | [display] |
| Paint | Explicit fill and stroke on every leaf; no group style inheritance, no browser-only features | [display] |
| IDs | `<prefix>_node_<i>`, `<prefix>_text_<i>`, `<prefix>_palette_<i>` (palette entries parked off screen) | [display] |

## Legibility at 1:1

| Rule | Value | Source |
| --- | --- | --- |
| Judge size | Look at every frame at 480 × 220, not enlarged | [ux] (review at native size) |
| Small parts | Avoid parts under ~3–4 px | [pr260] |
| Hatching | Avoid lines closer than ~3 px | [pr260] |
| Grey-only differences | Don't show a difference only with a slightly dimmer grey | [pr260] |

## Perceptible change

This one is mine, not open-xy's. PR #260's ux.md asks that a control visibly change the screen and says "too subtle reads as broken", but gives no number (and isn't merged yet). These floors make it testable. They live in `tokens.json` → `perceptibility`, and `tools/perceptibility.py` measures them on 1:1 renders.

| Rule | Value |
| --- | --- |
| What counts as changed | A pixel in the body (below the header) whose brightness moves by ≥ 24/255, about one stock grey step |
| Area changed, 0 → 100, by audible score | score 1: 0.5 % · 2: 0.8 % · 3: 1.2 % · 4: 1.6 % · 5: 2.5 % of the body (the body is ~87,000 px, so 2.5 % is ~2,200 px) |
| Each half (0 → 50, 50 → 100) | ≥ 40 % of the full-range floor, so a control doesn't do all its work at one end |
| Spread of the change | Its bounding box spans ≥ 40 px, so a big change in one tiny spot doesn't pass |
| Note response (rest → playing) | ≥ 2 % of the body, spanning ≥ 40 px |

Design-time floors per channel, the travel a control needs before it has a chance of passing:

| Channel | Floor over the full range |
| --- | --- |
| Position | ≥ 24 px |
| Rotation | ≥ 30° |
| Scale | ≥ 1.6× |
| Shade | ≥ 3 grey steps, and never alone |
| Count | ≥ 12 items, or doubling |
| Shape | some point moves ≥ 16 px |
| Note flare | ≥ 1.4× scale or ≥ 2 grey steps on top of a position or scale change |

## Motion

| Rule | Value | Source |
| --- | --- | --- |
| Idle | Still. Motion answers a note, press or turn. | [ux] |
| Ease | Exponential ease-out, settles in 0.15–0.2 s | [ux] |
| Reduced motion / track change | Jump to the end state | [ux] |
| Note animation | Animate while notes are held, then release; a fixed-length animation stops while a long note still sounds | [display] |
| Note serial | Counts per track, not per key; several note starts between frames can merge into one | [display] |
| Note activity | `held_notes`, `note_off_serial` and `NoteTracker` (`hold_started`, `hold_ended`, `note_released`) follow stock's note gate, not the sound: no promise the sound has ended at a note-off. The first frame after a reset or track change emits no events | [display] |
| Display reset | `display_reset` runs when the page is selected and when its track changes, so a short entrance animation there is allowed; continuing on the same page and track doesn't reset | [display] |
| No on/off controls | Every control eases through its range visually; none is only an on/off change in the drawing | [pr260] |

## Which machines draw a screen

| Machine | Own screen | What it gets | Source |
| --- | --- | --- | --- |
| Synth | Its engine page, any SDK | The display input below | [display] |
| Effect | Its send page, from SDK 1.7 (replaces stock's FX page on M1 of the send) | `slots` with all eight controls, `track` 14 or 15, `shift` and the shift row's `choices`. **No browser preview yet**, so design from stills and check on a device | [api], [display] |
| Sample engine | Over the sampler's page, from SDK 1.8, when it forks the sampler (`"base": "sampler"`) | The sample overview: 96 min/max bins over the whole sample, the outer markers, reverse, and `assigned`/`loaded` states (say how to load one when nothing's assigned; show nothing stale while it loads). It gives up stock's trim controls on that page, so start/end and loop need the engine's own controls | [api], [display] |
| Drum kit | SDK 1.8 | `shift`, the selected key's `model`, and `choices` (model group, place in group, choke group) whether or not Shift is held; a press always switches the key's first four and last four controls | [display], [ux] |
| Player, sequencer, function | Not yet: their pages need bound nodes the stock player page doesn't give | | [house] |

## Definition (`definition.json`)

Source **[api]**: open-xy `docs/api.md` § Definition, Own screen and Effect pages, on `staging`.

| Rule | Value | Source |
| --- | --- | --- |
| Top-level fields | Exactly `schema` (1), `id`, `name`, `parameters`, `presets`, `resources`, optional `press`; an effect may add `shift` | [api] |
| `id` | Lowercase letter then letters/digits/_, ≤ 15. Presets store it, so it never changes once published | [api] |
| Parameter count | Synth 4–8; sample/effect 1–8 | [api] |
| Parameter fields | `id`, `label`, `default`, `mapping`, `display`; synth alternates (index ≥ 4) also `control` 0..3 | [api] |
| Labels | ≤ 8 letters, digits or spaces; shown lower case | [api] |
| Values | Defaults and preset values in [0, 1]; presets hold exactly the declared controls, ≤ 64 presets | [api] |
| Mappings | `linear` (increasing), `anchors` (3–256 increasing), `power` (exponent ≠ 1), `exponential` (0 < min ≤ max), `enum` (2–256 unique labels ≤ 15 chars) | [api] |
| Display formats | `ratio`, `percent`, `bipolar`, `duration`, `semitones`, `enum`, `division` (division maps linear 0..1) | [api] |
| Two pages | `"press": "page"`: synth or effect, 5–8 parameters, ≤ 1 alternate per position. Synth: 8 parameters need sdk 1.3, 5–7 need sdk 1.4. Effect: sdk 1.7 | [api] |
| Effect shift row | `"shift"`: 1–4 enum controls chosen with Shift + encoders (sdk 1.7); all choices together ≤ 1,048,576 combinations; with a shift row, Shift no longer gives fine steps | [api] |
| Text slots | > 4 need sdk 1.3; > 16 need sdk 1.7 | [api] |
| Voice capacity | 1–256; 8 covers one track (stock plays ≤ 8 notes per track) | [api] |
| Saved sounds | Order and mapping changes affect saved sounds; a new slot at 0 must sound as before | [api], [ux] |

## Controls

| Rule | Value | Source |
| --- | --- | --- |
| Direction | Clockwise makes the shown number rise; name the control for what rises | [ux] |
| Count | ≤ 4 uses the stock header; 5–8 uses two pages (`"press": "page"`) via `page_header.hpp` | [ux] |
| Scope | The engine page holds the sound's own parameters, not another envelope/LFO/mod amount | [ux] |
