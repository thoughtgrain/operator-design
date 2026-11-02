# Conductor · review (revision 2)

## Tools

| check | result |
| --- | --- |
| `lint_frame.py frames2/*/*.svg --two-page` | **0 errors, 0 warnings** across 99 frames |
| `perceptibility.py` M1 (`rev2/perc-m1.txt`) | 3 of 9 pass (key, prog, note response) |
| `perceptibility.py` M2 (`rev2/perc-m2.txt`) | 6 of 9 pass. Fails: role 2.05 % (floor 2.5), gate 0.16 % (1.2), note response 0.50 % (2.0) |
| `perceptibility.py` M3 (`rev2/perc-m3.txt`) | 6 of 9 pass. Fails: accent 0.50 % (0.8), tones on its 50 → 100 half, note response 0.48 % (2.0) |
| `perceptibility.py` M4 (`rev2/perc-m4.txt`) | 0 of 6 pass |
| device limits, asserted by `gen_frames2.py` on every frame | every node is one pool shape at uniform scale within (0, 2]; every paint comes from the 16-entry palette; no per-page static art |

## The decision this review is waiting on

The floors count pixels that change by at least one grey step. They were calibrated against the filled bodies of earlier screens. Revision 2 is outline only, by request (no grey fills unless showing depth). An outline that moves changes a fraction of the pixels a filled body does, so most controls fall under, while the contact sheets show each one changing clearly.

I see three options:

1. **Bigger travel.** Larger, heavier marks to make up the area. This works against the calm Brian asked for.
2. **A second floor for outline languages.** Set it in `tokens.json` and `constraints.md`, and confirm it against the contact sheets by eye. This changes the protocol, so it's Brian's call.
3. **Depth fills.** One dark fill tier only where a part sits in front of another, such as treads over risers or notches into the edge.

I recommend option 2, then re-running the four pages against the new floor.

Two protocol questions from revision 1 also still stand:
- **Two-state switches** (tones, mute) can't move on one half of their range.
- **Unordered enums** should be judged step by step.

## Craft (rest frames beside `library/loom-pages/` and `library/theseus-tower/` at 1:1)

| question | answer |
| --- | --- |
| One drawing language? | Yes: lines and outlines on a ground line on every page. M3 is the only page with depth, and it's modelled in 3D and projected through one camera. |
| Line weights? | Hairlines 1–1.2 px (ground lines, buses, ticks). Lines 1.5–1.6 px (arches, notches, treads, outlines). The subject is 2.2 px (the sounding arch, the note just hit). |
| One brightest element? | Yes. M1: the sounding arch. M2/M3: the note just hit. M4: the selected trace and pad. |
| Anything look like an icon? | No. The old circles and squares are gone; the shapes are arches, Vs, parallelograms, triangles and traces. |
| "Picture, not panel" (`craft.md`, 2026-11-02) | **Not met yet.** The resting pages still carry strips: M1's phrase line and groove, M2's lane index, M3's `5 arp` corner label, M4's register strip. The proposal is to fold them into the drawing or show them only while their encoder is touched. See `brief.md`. |

## Accessibility checklist

| item | evidence |
| --- | --- |
| Every frame viewed at 1:1 | `rev2/contact-m*.png` |
| Text ≥ 8 px, ≥ 10 px during play | All body text 10 px, titles 20 px |
| Text greys ≥ 4.5:1 | `#7D7D7D` 5.1:1 and up; nothing below |
| Non-text ≥ 3:1 | Meaningful lines ≥ `#646464` (3.55:1); ground lines `#4B4B4B` are context only |
| No part under ~3 px; no lines closer than 3 px | Lint is clean |
| No state by shade alone | Mostly. Shade-only exceptions: M2 vary (also smaller), M3 accent, M4 xpose (the lit octaves) |
| Each control differs at 0 / 50 / 100 | Clear by eye on the contact sheets; under the tool's floors as above |
| Nothing moves at rest; no flashing > 3×/s | Only the playhead and the note just hit change while playing |
| Reduced motion | Every ease jumps to its end state |
| Labels and captions | Widths measured with the device glyph table; the preview font differs. **Pending device** |
| No red | 16 grey paints |
| Device photos | **pending device** |

## Known limits of these frames

- **The music is a stand-in** (`gen_frames.py`'s `Song`, `Lane`, `Arp`), not `generator.h`.
- **M3 mode.** The vertical scale fits each frame's notes, and the stand-in's `order` mode uses a different pitch set. Mode therefore looks more different than it should. The fix is to lock the scale to the lane's range and correct `order`.
- **Text colour is fixed per slot on the device.** The selected lane's label goes to the one bright slot.
- **M4 track numbers** are two spaced text slots on the device. The previews place each digit where Univers would.
- **Stroke width under scale.** Arches, notches and risers assume a stroke keeps its width when a node scales. If the device scales stroke with the node, small arches thin and large ones thicken. **Pending device.**
