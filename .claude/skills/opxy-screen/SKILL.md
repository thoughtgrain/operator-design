---
name: opxy-screen
description: Design or revise the screen an OP-XY machine draws with the open-xy SDK — subject, control mapping, node budget, 480x220 SVG frames, contact sheet, motion spec and display.cpp handoff. Use for any OP-XY machine screen, header layout or screen review.
---

# OP-XY machine screen

You're running the protocol in `opxy/protocol.md`. Read `opxy/constraints.md` and `opxy/patterns.md` before drawing anything; `opxy/accessibility.md` before review. Outputs go in `screens/<machine-id>/`.

## Steps

1. **Gate 0.** Decide screen vs stock page. If there's no single object the sound acts on, recommend the stock page and stop.
2. **Brief.** Copy `opxy/templates/brief.md`. Fill intake (labels ≤ 8 chars lower case, captions estimated at chars × 0.64 × 20 against 53 px), then rank each control's audible effect 1–5. If you can't hear the machine, ask the person for the ranking rather than inventing it.
3. **Subject.** Propose 2–3 candidates tied to patterns. **Ask the person to choose** unless they already have.
4. **Map + budget.** One channel per control, travel scaled to score with a visible floor, no on/off-only controls. Declare the `display` block. Rest = 0 changed nodes; heaviest playing ≈ 20 average.
5. **Frames.** Start from `opxy/templates/frame.svg`. Draw `rest`, `playing`, and `c<N>-000/050/100` per control. Generate frames from one script when there are many, so they stay consistent; never hand-patch a single frame out of sync with the brief.
6. **Lint.** `python3 opxy/tools/lint_frame.py screens/<id>/frames/*.svg` (`--two-page` for 5–8 controls, `--own-header` if covering the header). Fix every error; fix or justify every warning in `review.md`.
7. **Contact sheet.** `python3 opxy/tools/contact_sheet.py screens/<id>/frames --out screens/<id>/contact.svg --png`, then look at the PNG at 1:1. If any control's three frames look alike, go back to step 4.
8. **Motion, review, handoff.** Write `motion.md`, `review.md` (checklist from `accessibility.md`), `handoff.md` per protocol phase 8.

## Hard rules

- 480 × 220, grey only, never red. Univers Next Pro Light, ≥ 8 px.
- Bound mutable outlines: `M L… Z`, `fill="none"`, distinct points ≥ 1/8 px apart, closing edge ≥ 1/4 px, no turn within 2.5° of straight back, ≤ 64 points, one subpath.
- Lines are closed ribbons. Parts that meet share an outline or pivot.
- Nothing moves at rest. Eases settle in 0.15–0.2 s. Reduced motion jumps.
- Don't copy stock artwork or other machines' drawings.
- Device-only checks (caption widths in the real font, rasterization, redraw on hardware, photos) are **pending device** until someone does them. Never mark them done.
- open-xy `docs/display.md` and `docs/ux.md` override this repo if they disagree.
