# Screen design protocol

How I go from a machine's sound and parameters to a screen design that's ready for someone to implement in `display.cpp`. Each phase has an output and a gate. I don't start the next phase until the gate passes, because the expensive mistakes (wrong subject, blown node budget) are cheap to catch early and painful to catch on hardware.

Everything lands in `screens/<machine-id>/`:

```
screens/<machine-id>/
├── brief.md          ← phases 1–4, from templates/brief.md
├── frames/           ← phase 5: rest.svg, playing.svg, c<N>-000.svg, c<N>-050.svg, c<N>-100.svg
├── contact.svg       ← phase 5: tools/contact_sheet.py output (+ contact.png if rsvg-convert exists)
├── motion.md         ← phase 6
├── review.md         ← phase 7
└── handoff.md        ← phase 8
```

## Phase 0 · Does it earn a screen?

Read the sound. Ask: is there one object or scene this sound acts on? If not, it gets the stock page (see Gate 0 in `patterns.md`) and the protocol ends here with a one-line note in `brief.md`.

**Gate:** I can name the subject in one sentence, or I've decided on the stock page.

## Phase 1 · Intake

Fill in the top of `brief.md`: machine id, kind (synth, effect), what it sounds like in two sentences, and every parameter with range, real unit, default, and the header caption it will show.

Why the captions now: they're the first thing that breaks. ux.md caps labels at 8 characters and values at about 5, measured in Univers Next Pro Light. If `dew point` doesn't fit, I find out before I've drawn anything.

**Gate:** every label ≤ 8 characters, lower case; every value caption estimated to fit its column (see the width note in `accessibility.md`); 1–8 parameters, with page 1 holding what's played most if there are more than 4.

## Phase 2 · Listen and rank

For each control, judge its audible effect across 0 → 100 (by ear in the preview, or by level/band energy) and score it 1–5. This score sizes the control's visual travel in phase 4.

Why: ux.md asks that a control be seen as much as heard. A quiet control with a huge visual swing lies to the player; a loud one with a tiny mark leaves them guessing.

**Gate:** every control has a score and a one-line reason ("cutoff sweep, dramatic: 5"; "drift, subtle until 70: 2").

## Phase 3 · Subject

Write two or three candidate subjects, each in one sentence, each tied to a pattern from `patterns.md` (section drawing, diagram + trace, figure...). For each, sketch in words what every control does to it. Pick one and say why.

This is where I stop and ask if the person hasn't already chosen. The subject is the biggest creative decision and the hardest to change later.

**Gate:** one subject, one pattern, and a sentence per control saying what moves. Reject any candidate where a control has nothing to move, or where the screen reads as a dashboard of meters.

## Phase 4 · Map and budget

Fill the mapping table in `brief.md`:

| control | score | channel | part | travel at 0 → 100 | what the player sees |
| --- | --- | --- | --- | --- | --- |

Rules:

- One primary channel per control, no two controls on the same channel of the same part.
- Travel scales with the score, floor of ~12 px movement or ~20° rotation or a two-step shade change, whichever applies, so score-1 controls still visibly move.
- No control is only an on/off change in the drawing.

Then the budget: declare `paths`, `points`, `nodes`, `texts`, `palette`, and estimate changed nodes per frame at rest (must be 0), playing at defaults, and playing at the heaviest setting (target ~20 average).

**Gate:** budget fits `constraints.md`, rest cost is 0, heaviest playing estimate ≤ ~20 average with a stated peak.

## Phase 5 · Frames

Draw the frames as SVG at exactly 480 × 220, starting from `templates/frame.svg`. Required set:

- `rest.svg`: all controls at default, no notes
- `playing.svg`: defaults, notes held, mid-animation
- `c<N>-000.svg`, `c<N>-050.svg`, `c<N>-100.svg` for each control N, others at default

Authoring rules for frames (they're meant to become `panel.svg.fragment`, so I author them that way from the start):

- Bound parts get device IDs (`<id>_node_<i>`), mutable outlines are `M L… Z` with no fill and distinct points.
- Every leaf has explicit `fill`, `stroke`, `stroke-width`. No group styles, no gradients, filters, masks, `<use>`, CSS.
- Lines are closed ribbons, not strokes traced back.
- Text uses `font-family="UniversNextPro-Light"`. Previews will fall back to another font locally, so I treat rendered widths as approximate.

Run the linter on every frame, then build the contact sheet:

```sh
python3 opxy/tools/lint_frame.py screens/<id>/frames/*.svg
python3 opxy/tools/contact_sheet.py screens/<id>/frames --out screens/<id>/contact.svg
```

**Gate:** zero lint errors; warnings either fixed or explained in `review.md`; every control visibly different across its three frames on the contact sheet at 1:1.

## Phase 6 · Motion

Write `motion.md`: for each trigger (turn per control, note on, held, hold ended, page press) what moves, from what to what, over how long, and the reduced-motion end state. Use the vocabulary at the end of `patterns.md`.

**Gate:** nothing moves at rest; every ease settles in 0.15–0.2 s; held-note motion lasts as long as notes are held; reduced motion and track change jump to the end state.

## Phase 7 · Review

Copy `checklists` from `accessibility.md` and the "before you submit" items from ux.md into `review.md` and answer each one with evidence (a frame name, a number). Anything only provable on hardware is marked **pending device**, never ticked.

**Gate:** every item answered; nothing ticked that wasn't checked.

## Phase 8 · Handoff

Write `handoff.md` for whoever implements it in the machine's repo:

- The `display` block for `definition.json` with the numbers from phase 4.
- Node index map: node `i` → part → which input drives it → channel.
- Palette map: entry `i` → hex → used for.
- Text slot map, if any.
- What `DisplayState` needs (NoteTracker, eased values, page header).
- Path key policy: which control changes each path's key.
- Open device checks: the pending items from phase 7.

**Gate:** someone who hasn't read the brief can implement `display.cpp` from `handoff.md` and the frames alone.

---

## Revisions

When a design changes after handoff, I update the brief's mapping table first, re-run phases 4–8 for what changed, and note the change at the top of `handoff.md` with a date. Frames get regenerated, not hand-patched, so the contact sheet always matches the brief.
