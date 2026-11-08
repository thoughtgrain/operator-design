# Lathe · v3 cleanup and interaction study

Owner's pick: pass 02 v3, the lacquer coat under a microscope at grazing light. This is a cleanup of that pick plus a study of what each control does to it. It's not a new generative pass, so it's one design, not five. Everything comes from `build.py` (one camera, one model); `python3 screens/lathe/frames/build.py --sheets` regenerates every frame, `before-after.png`, `contact.png` and `sweep.gif`.

## What changed, and why

v3 read as lacquer, but at 1:1 it also read as a retro perspective grid: about 25 evenly spaced lines converging on a vanishing point, flat lines with no wall between them, and a field that ran out to the frame edges. I changed these things:

- **Fewer, physical grooves.** At the default there's the newest groove plus four earlier turns, not 12+ lips. Each turn is a real V groove now. Light comes in low from the right, so the groove's left wall is the lit one. I draw that wall as a dark body (`#323232`) between its lit lip (Line, `#7D7D7D`) and its floor (hairline). The other wall, the lands between grooves and the uncut lacquer stay black. Because the lines come in pairs with wide black lands between them, they don't add up to a grid.
- **A gentler camera.** I steepened the tilt (56° down, far/near pitch ~0.9 instead of ~0.55), so the turns stay close to parallel and lean slightly toward the newest groove. Nothing sweeps to a horizon any more. The camera's principal point sits on the newest groove, so it stands upright and is where the eye lands.
- **A believable microscope field.** Depth of field: each lip dims in three runs as it recedes (`#7D7D7D` → `#646464` → `#4B4B4B` hairline), and the walls and floors stop short of the far end. A round field stop is centred below the frame and cut off by its edges, so the far ends of the outer turns follow its arc (clearest at groove 100). The near cut face is the anchor: a lit top edge with a V notch under every groove, black coat below. The uncut lacquer edge fades out on the left before x = 30.
- **The newest groove is the one bright line.** Its lit lip is the only `#CDCDCD` element, at Subject weight. To its left is uncut lacquer (black, because the cutter hasn't reached it), and the turns cut earlier sit to its right, toward the rim.
- **The rim** is just outside the last turn: a dim receding edge, and the coat falling away over it in the cut face.
- Housekeeping: no text below the header. No grey-fill states (the only fills are the wall bodies, which are real surfaces, the wear grains, which are real particles, and nothing that signals on/off). The body is 92–93 % black in every frame. Nothing reaches above y = 43, and nothing touches the frame edges (content spans x 30–455). The header shows lathe's titles and stock-format values, with amounts and no %: `1.00 / 0 / 0 / 0` at rest, and 0.50 / 1.41 / 4.00, 0 / 50 / 100, 0 / 35 / 100 and 0 / 25 / 100 across the control frames, following the definition's mappings.

## What an effect page can react to on the device

Only the controls. Nothing else on an effect page changes on its own, and this screen only moves when a knob turns.

- open-xy `docs/display.md` (staging, 6b2d113), "Effect pages (SDK 1.7)": *"Its input's `slots` hold all eight of its controls, `track` is the send (14 or 15), and two fields follow the note activity: `shift`, 1 while Shift is held on an effect with a shift row, and `choices`, each shift control's choice."* lathe has no shift row, so `shift` and `choices` are always 0 for it.
- Same file, "Note activity (SDK 1.1)": *"Non-instrument tracks report zero."* A send track gets no note serial, no held notes and no note-offs.
- There's no audio signal or level in the display input at all, so I didn't draw a meter. The amp envelope (`display.md`, "Amp envelope (SDK 1.10)") is for *"a synth's page or a sample engine's own screen"* only. Transport, tempo and `muted` are in the track-control `control()` input (`docs/api.md`, "Track control"), not in the display input.
- `elapsed` is in every display input, but `ux.md` (Principles) says *"Calm by default. An idle screen is still; motion answers a note, a press or a turn."* So there's nothing to animate with it except a turn's own ease. The optional `display_parameter_reset(state, slot)` callback (when a parameter is reset to its default) is a turn too: that control eases back.

So there's no `motion.gif`. `sweep.gif` (1:1, 165 frames) turns each control slowly from 0 to 100 in turn, holds, and snaps back to the default. It's a stand-in for the 0.15–0.2 s ease the device would run on each step.

## Interactions

Each control has its own channel on its own part. Scores are from the brief's phase 2.

| control | score | channel · part | 0 → 100 at 1:1 | what the player sees |
| --- | --- | --- | --- | --- |
| cut | 4 | shape · the newest groove (nodes 0, 1) | lateral swing 2.2 → ~19 px at the near end; the largest single-point move is 16.1 px, which clears the 16 px shape floor | at 0.50 the newest groove is almost straight; at 1.00 it swings gently; at 4.00 it swings wide and its crests flatten into plateaus (tanh limit), saturation you can see. The lit wall body follows the swing |
| groove | 3 | count + position · earlier turns 5–7 and the rim | 4 → 7 turns; the rim steps ~41 px per turn and leaves the field at 100 | further in toward the label means more turns already cut beside the newest one, and the rim bevel steps out to the right until, at 100, the field is all grooves out to the field stop. Turns arrive at groove 25, 58 and 92 |
| wear | 3 | count · 27 marks on the earlier turns | 0 → 27 items (5 long scratches, 15 grains, 7 short scratches) | first, long stylus-skate scratches across the earlier turns (they arrive first, so the first half of the knob reads), then grains and short scratches on the lands. Every land mark stays ≥ 3 px clear of the groove edges. The newest groove and its land never wear |
| rumble | 2 | position · two ghosts of the newest lip (nodes 2, 3) | ghost offsets 0 → 13 px and 0 → 26 px, trailing left | the lit lip smears into a double exposure, which is what a microscope image of a rumbling platter does. At 0 the ghosts are parked; at 25 (knob 50) they sit 5 and 10 px off; at 100, 13 and 26 px. The nearer ghost is `#7D7D7D`, the farther `#646464`, so the lip stays brightest |

Choices worth flagging:

- **groove isn't "spacing tightening and walls steepening".** In this drawing, tightening the pitch moves every earlier turn on every frame of a turn, and the earlier turns are static outlines, so walls can't re-steepen without re-keying paths, and only four paths exist. Counting turns uses the same nodes, which appear in place and never move, so a groove turn costs nothing between steps. It also tells the physical story honestly: the further in the cutter is, the more turns already lie beside it. The trade-off is that it doesn't draw *why* inner grooves sound duller, which is the recorded wavelength getting shorter. Open question below.
- **rumble isn't a heave or a tilt.** The v3 ±3° turn was under the 30° rotation floor and read as nothing. A heave of the groove lines needs every turn re-keyed (static outlines can't bend), and whole-field drift is ~45 nodes per frame for a still result that just looks shifted. Ghosting the lip is 2 nodes, it's perceptible, and it doesn't share a channel with cut: cut changes the lip's shape, rumble moves the ghosts' positions, and their shapes just follow the lip.
- **The ghosts are one-sided** so they never meet the first earlier turn, even at cut 4.00 + rumble 100. I checked that combination together with groove 100 and wear 100 (x2 render): clear everywhere, ≥ 6 px between the newest wall and turn 1 at the widest swing.

## Node plan and redraw

| node(s) | part | kind | driven by |
| --- | --- | --- | --- |
| 0 | newest groove, lit lip (`#CDCDCD`, 2 px ribbon) | mutable outline, 64 points | cut (key changes when its points change) |
| 1 | newest groove, lit wall (fill `#323232`, hairline `#7D7D7D` edge) | mutable outline, 64 points | cut |
| 2, 3 | rumble ghosts of the lip (2.5 px, `#646464`, `#7D7D7D`) | mutable outline, 64 points | position: rumble; shape follows cut; parked at rumble 0 |
| 4–20 | earlier turns 5, 6, 7: wall, notch/land, lip runs, floor runs (7 + 6 + 4 nodes after field clipping) | static shape, shown or parked | groove |
| 21–26 | rim at 4, 5, 6 turns: receding edge + fall (2 each) | static shape, shown or parked | groove |
| 27–53 | wear marks | static shape, shown or parked | wear |

Proposed `resources.display` (not yet written to `definition.json`, which still has the phase-1A placeholder): `paths 4`, `points 64`, `nodes 54`, `texts 0`, `palette 6` (`#CDCDCD #969696 #7D7D7D #646464 #4B4B4B #323232`), `stateBytes` ≈ 24 (four eased control values plus targets; settle it in the handoff). Everything else is unbound static artwork: turns 1–4, their notches, the uncut edge, and the default rim's land.

Redraw (changed nodes per frame):

- **At rest: 0.** There's no live input, so nothing changes until a knob turns.
- **cut turning:** 2 per eased frame (nodes 0, 1 re-keyed), or 4 when rumble is up and the ghosts follow. That's four 64-point paths, the most expensive case, and it lasts only for the 0.15–0.2 s ease after each detent.
- **groove turning:** 0 between steps; 6–11 on the frame a turn arrives (its 4–7 nodes plus a rim swap of 2 + 2).
- **wear turning:** 1 node per mark crossing its threshold, at most ~3 in one frame on a fast spin.
- **rumble turning:** 2 per eased frame (translations only, no re-key).
- **Heaviest:** cut and rumble eased in the same frame is 4 re-keyed paths; the peak is a groove step at 11. Well under ~20, and it drops back to 0 within 0.2 s of the last detent.

## Checks

- `python3 opxy/tools/lint_frame.py screens/lathe/frames/*.svg --paths 4` on rest + 12 control frames: **0 errors, 0 warnings**, no `text-in-drawing`, 54 nodes, max 64 points, every mutable outline 64 points. I ran it with `--paths 4` because `definition.json` still declares `paths 0`.
- Judged at 1:1 (`rest.png`, `contact.png`, `before-after.png`).
- `perceptibility.py` (scores 4, 3, 3, 2; header bottom 20). The frames were staged as `c<N>-000/050/100` copies, then removed:

| control | need | 0→100 | 0→50 | 50→100 | span | |
| --- | --- | --- | --- | --- | --- | --- |
| cut | 1.60 | 2.30 | 1.26 | 1.93 | 129 | ok |
| groove | 1.20 | 2.08 | 1.35 | 1.16 | 129 | ok |
| wear | 1.20 | 1.29 | 0.51 | 0.78 | 162 | ok |
| rumble | 0.80 | 0.85 | 0.87 | 1.45 | 122 | ok (thin margin) |

No note response row: an effect page gets no notes, so there's no `playing` frame.

## Pending

- **Device:** everything. There's no browser preview for effect pages, so check on an OP-XY: the 2.5 px ghosts and the `#323232` wall fills on the real panel, the wear grains (5–7 px) at arm's length, the cost of re-keying four 64-point paths during a cut turn, and whether `4.00` fits its column in Univers Next Pro Light.
- **rumble's margin is thin** (0.85 against 0.80). If the device makes the ghosts read fainter than the preview, widen the offsets rather than lower the score.
- **The groove channel's honesty** (open question): is "more turns beside it" enough, or should groove also shorten the newest groove's wavelength? That's the real cause of inner-groove loss, but it would put a second control on the newest groove's shape, next to cut.
- **`definition.json` `resources.display`** still needs the numbers above (phase 4), then a rerun of `lint_definition.py` and of the frame lint with `--definition`.
- `motion.md`, `review.md` and `handoff.md` aren't written yet.
