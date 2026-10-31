---
name: opxy-screen
description: Design or revise the screen an OP-XY machine draws with the open-xy SDK, including building and reviewing its definition.json from a port (OP-1 plugin or other source) — subject, control mapping, node budget, 480x220 SVG frames, contact sheet, motion spec and display.cpp handoff. Use for any OP-XY machine screen, port definition, header layout or screen review.
---

# OP-XY machine screen

You're running the protocol in `opxy/protocol.md`. Read `opxy/constraints.md` and `opxy/patterns.md` before drawing anything; `opxy/accessibility.md` before review. Outputs go in `screens/<machine-id>/`.

## Steps

1. **Gate 0.** Decide screen vs stock page. If there's no single object the sound acts on, recommend the stock page and stop.
2. **Brief.** Copy `opxy/templates/brief.md` and fill intake. Note where the controls come from.
3. **Definition from the port (1A)**, when there's no XY `definition.json` yet: read the source engine's code (not its manual), inventory every control including shared knobs and hidden modes, give each a fate (keep / split / merge / drop with a reason), keep the source's ranges and curves, pick real-unit display formats, lay out pages (page 1 = played most, one alternate per position, no filler), clean defaults, carry presets. Write the port map into the brief and the draft to `screens/<id>/definition.json`, leaving `resources.display` as a placeholder.
4. **Definition review (1B):** run `python3 opxy/tools/lint_definition.py <definition.json>`. Fix errors; resolve or justify each warning in the brief; give every row of the review table a verdict. By-ear and device checks stay **pending device**.
5. **Captions and ranking.** Captions from the reviewed definition (labels ≤ 8 chars lower case, values estimated at chars × 0.64 × 20 against 53 px). Rank each control's audible effect 1–5. If you can't hear the machine, score from the DSP and ask the person to confirm.
6. **Subject.** Propose 2–3 candidates tied to patterns. When revising an existing screen, score it against the protocol as candidate A. **Ask the person to choose** unless they already have.
7. **Map + budget.** One channel per control, travel scaled to score with a visible floor, no on/off-only controls. Fill `resources.display` and re-run `lint_definition.py`. Rest = 0 changed nodes; heaviest playing ≈ 20 average.
8. **Frames.** Start from `opxy/templates/frame.svg`. Draw `rest`, `playing`, and `c<N>-000/050/100` per control. Generate frames from one script when there are many, so they stay consistent; never hand-patch a single frame out of sync with the brief.
9. **Lint.** `python3 opxy/tools/lint_frame.py screens/<id>/frames/*.svg` (`--two-page` for 5–8 controls, `--own-header` if covering the header). Fix every error; fix or justify every warning in `review.md`.
10. **Contact sheet.** `python3 opxy/tools/contact_sheet.py screens/<id>/frames --out screens/<id>/contact.svg --png`, then look at the PNG at 1:1. If any control's three frames look alike, go back to step 7.
11. **Motion, review, handoff.** Write `motion.md`, `review.md` (checklist from `accessibility.md`), `handoff.md` per protocol phase 8.

## Hard rules

- 480 × 220, grey only, never red. Univers Next Pro Light, ≥ 8 px.
- Bound mutable outlines: `M L… Z`, `fill="none"`, distinct points ≥ 1/8 px apart, closing edge ≥ 1/4 px, no turn within 2.5° of straight back, ≤ 64 points, one subpath.
- Lines are closed ribbons. Parts that meet share an outline or pivot.
- Nothing moves at rest. Eases settle in 0.15–0.2 s. Reduced motion jumps.
- Don't copy stock artwork or other machines' drawings.
- Device-only checks (caption widths in the real font, rasterization, redraw on hardware, photos) are **pending device** until someone does them. Never mark them done.
- open-xy `docs/display.md` and `docs/ux.md` override this repo if they disagree.
