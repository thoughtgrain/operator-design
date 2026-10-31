# opxy · machine screen design

How I design the screen an OP-XY machine draws through the [open-xy SDK](https://github.com/etcetc000/open-xy): from the sound and its parameters to frames, a motion spec and a handoff someone can implement in `display.cpp`.

The device rules come from open-xy. What this module adds is the process: choosing a subject, mapping each control to something you can see in proportion to what you hear, staying inside the redraw budget, and catching device faults while the design is still cheap to change.

## Reading order

1. **[constraints.md](constraints.md)** — the numbers: 480 × 220, greys, type, frame limits, device drawing faults. Every line links to its source.
2. **[protocol.md](protocol.md)** — the phases (0 screen-or-stock, 1 intake, 2 rank, 3 subject, 4 map + budget, 5 frames, 6 motion, 7 review, 8 handoff), each with an output and a gate.
3. **[patterns.md](patterns.md)** — the visual-channel table and the composition patterns (section drawing, diagram + trace, trace as subject, stack in depth, field and figure, figures, column affinity, headers).
4. **[accessibility.md](accessibility.md)** — contrast for every grey, sizes, single-cue rules, motion, caption widths, and the review checklist.
5. **[reference/](reference/)** — annotated screens and links to MNMD, Found Motive and the core machines.

## Files

| Path | What it is |
| --- | --- |
| `tokens.json` | The numbers as data. Tools read it; update it with `constraints.md`. |
| `templates/brief.md` | Phases 0–4 as a fill-in document |
| `templates/frame.svg` | 480 × 220 starter with a preview-only stock header and the authoring rules in a comment |
| `tools/lint_frame.py` | Checks frames against device rules: canvas, grey-only/no red, explicit paint, one subpath ≤ 64 points, closed ribbons, point spacing, closing edge, near-reversal turns, bound-id topology and transforms, number format, text size/font/length, header zone, small parts |
| `tools/contact_sheet.py` | Tiles `rest`, `playing` and `c<N>-000/050/100` frames into a 1:1 contact sheet (SVG, PNG with `--png`) |

## Quick start

```sh
mkdir -p screens/<id>/frames
cp opxy/templates/brief.md screens/<id>/brief.md
cp opxy/templates/frame.svg screens/<id>/frames/rest.svg

python3 opxy/tools/lint_frame.py screens/<id>/frames/*.svg          # add --two-page for 5–8 controls
python3 opxy/tools/contact_sheet.py screens/<id>/frames --out screens/<id>/contact.svg --png
```

Tools are stdlib Python 3.10+. `--png` uses `rsvg-convert` if it's installed. The device font (Univers Next Pro Light) is licensed, so local previews render text in a fallback; caption widths stay "pending device" until measured in the real font.

## What the linter can't tell you

It reads static SVG. It can't count changed nodes per frame (run `display()` on the host for that, per ux.md), can't hear whether travel matches the sound, and can't see what the device rasterizer does. Clean lint means "ready for `sdk.py test` and a device photo", nothing more.
