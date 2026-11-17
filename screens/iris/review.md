# Iris · review

Evidence is a frame name in `frames/`, a number, or a tool result. **Pending device** means only an OP-XY can settle it and nobody has done that yet.

## Craft review (opxy/craft.md)

I put the rest frame beside `library/theseus-tower` at 1:1.

| Question | Answer |
| --- | --- |
| Every element drawn in the named language (single-weight contour, projected from one model)? | Yes. Bands, the mix and the horizon are all closed ribbons projected from one model: a sunset bow, every band a circle about one centre on the horizon |
| Line weights match the table at every setting? | Mostly. Horizon 1.2 px (hairline), bands 1.5 px (line), the mix 2.5 px (subject). On the device a band cycle scales with its radius and Spread, so in the worst corner (the saw band pulled out by Overlap 100 and stretched by Spread 100) it reaches about 1.35×, ~2 px: still under the subject weight, and the mix stays the brightest and heaviest line. If it reads as too heavy on hardware, pre-draw a thinner chain for the inner bands |
| Exactly one brightest element? | Yes. The mix line, `#AFAFAF` at rest and `#CDCDCD` held. The brightest band is `#969696` |
| Anything look like an icon? | No. The risk was a target, and the cycle density rising inward (11 → 16) keeps it from reading as one |
| Text or numbers outside the header? Any state shown as a grey fill? | No and no. Nothing is filled; a band Tone has cut changes shape (rounded) as well as dropping a grey step |
| Could this screen belong to a different machine? | No. The four bands are iris's four waveforms in order, and the bright line is iris's own output computed from the engine's maths |
| Sits in the same set as the reference? | Yes, at 1:1: a calm single subject in grey line, black all round |

One thing I watched: at 1:1 the square band can read as battlements at the crown. It's the true shape of the wave, and the rounded chain takes over when Tone closes, so I kept it.

## Tools

- `lint_definition.py definition.json`: 0 errors, 0 warnings.
- `lint_frame.py frames/*.svg --definition definition.json`: 21 frames (with `shift.svg`), 0 errors, 0 warnings (after revision 03) (this includes mutable outlines within ±64 px of their origin).
- `perceptibility.py --scores 5,4,4,4,3,2`: **pass** on the design frames (table in `brief.md` §5) and on `display()`'s own output run on the host (§5, Frames against the device code). Frames were rendered at 1:1 with Playwright, because rsvg-convert isn't installed here.

## Accessibility checklist (opxy/accessibility.md)

- [x] Every frame viewed at 1:1 (480 × 220) on `contact.png`
- [x] Text ≥ 8 px everywhere, ≥ 10 px for anything read during play: header text only, stock sizes (10 / 20 / 13 px)
- [x] Text greys ≥ 4.5:1 on their background: stock header, apart from the stock inactive row
- [x] Meaningful non-text parts ≥ 3:1: bands `#646464` (3.55:1) to `#969696` (7.1:1), mix `#AFAFAF` (9.6:1). The horizon `#4B4B4B` is ground by design
- [x] No part under ~3 px; no repeated lines closer than ~3 px: since revision 03 the bands are 10 px apart and their crests interlock on purpose (the owner asked for overlap). They cross at an angle rather than running parallel, and a ring out of the blend is a near-plain arc 10 px from its neighbour. The ripple (0.8 px) is a shape on a 1.5 px line, not a part of its own
- [x] No state or control effect shown by shade alone: a band's mix weight shows as grey *and* as the mix line's shape and the bands' radii; Tone's cut is a change of shape
- [x] Each control visibly different at 0 / 50 / 100 on the contact sheet, and `perceptibility.py` passes
- [x] Visual travel matches the audible score: morph (5) has the largest change at 10.2 %, phase (2) is above its floor without being the loudest. Phase is visually large for a score of 2 (7.2 %), because sliding a wave even a little moves a lot of pixels. I'm keeping it, because it's what phase does to the inputs
- [x] Nothing moves at rest; nothing flashes: the only colour change is the mix line's single step on hold, and no faster than notes are played
- [x] Reduced-motion end states differ by more than shade: they're the same drawings as the settled frames
- [x] Labels ≤ 8 characters, lower case. Value captions: **pending device** (the estimate is ≤ 51 px against 53)
- [x] No red anywhere in the machine artwork
- [ ] Device photos at rest, playing and the heaviest setting: **pending device**

## Before you submit (open-xy ux.md)

- [x] The page holds what's played most (morph, overlap, spread, tone); skew and phase are on the Shift row, and Shift replaces the header's contents rather than adding a row (`frames/shift.svg`)
- [x] Defaults are the plainest useful sound (triangle, a little of its neighbours, no spread). Presets by ear: **pending device**
- [x] Controls are named for what rises clockwise
- [x] The engine page holds only the sound's own parameters
- [x] The screen shows every control, and every control changes the screen
- [ ] Redraw budget measured on the device (4 mutable outlines × 64 points rewritten per frame while held): **pending device**
- [ ] CPU on the device: **pending device**. Host checks: `tests/sound.cpp` passes against a stand-in for the SDK header; `sdk.py test` hasn't been run against the real SDK yet

## Revision 03 (2026-11-17)

Rings 10 px apart and interlocking, the ends off the bottom edge, and rings in the blend sliding onto the bright line and swelling. Craft answers unchanged: one language, one brightest element (the mix line), no text in the drawing. `panel.svg.fragment` is under the 64 KiB preview cap (62,972 bytes). The version before this revision wasn't (107 KB), and I missed it then.
