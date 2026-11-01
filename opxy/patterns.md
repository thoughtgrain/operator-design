# Patterns

A pattern is a way to compose a machine's screen: what the subject is, where it sits, which visual channels the controls drive, and what it costs in nodes. They're descriptions, not assets. I never trace another machine's drawing; I borrow the idea and draw my own subject.

Every pattern lives under the same rules in `constraints.md`. The point of this file is to skip the blank-canvas phase and start from something that's already known to work on 480 × 220 grey.

## The visual-channel table

Before any pattern, this is the menu. Each control gets **one primary channel**, and no two controls share one, because if two knobs both make the thing bigger the player can't tell which did what.

| Channel | How the frame does it | Redraw cost | Reads well for | Watch out |
| --- | --- | --- | --- | --- |
| **Rotation** | `turn` / `sweep(value, half)` on a node around its origin | 1 node | pitch-ish, angle, tension, strike force | Rotating parts that touch others need a shared pivot |
| **Position** | `place` x/y | 1 node | balance, mix, offset, travel, delay time | Keep travel ≥ ~12 px across the range so the quietest control still visibly moves |
| **Uniform scale** | `scale` ≤ 2 | 1 node | size, level, room, density | No non-uniform scale. Scale stroke widths too, so check thin lines at the low end |
| **Shape** | Mutable outline, ≤ 64 points, new `key` per change | Whole path on change | timbre, waveshape, resonance, harmonics | Only up to 4 paths. Points ≥ 1/8 px apart, no near-reversals |
| **Shade** | `shade` to another palette entry | 1 node | activity, which part is engaged, depth | Never the only signal for a small difference. Fade through greys, don't jump |
| **Count** | `hide` / `place` a set of nodes | 1 node per toggled part | voices, steps, partials, grains | Step in with an ease so the control isn't an on/off change |
| **Text** | text slot or header value | 1 slot | modes, enums, codes | Header already shows values; use body text only for named states (a vowel, a model) |

Proportion rule from ux.md: the channel's travel scales with how much the control changes the sound, with a generous floor. I score each control's audible impact 1–5 in the brief and use that score to size its travel. The floors are numbers, not taste: `constraints.md` → Perceptible change lists them per channel (position ≥ 24 px, rotation ≥ 30°, scale ≥ 1.6×, count ≥ 12, shape ≥ 16 px), and `perceptibility.py` checks the result. Shade on its own never clears a floor.

## Gate 0: stock page

Not every machine needs its own screen. If a machine is an effect or utility where the stock page already tells the player everything (four values, no single object the sound acts on), I keep the stock page and spend the effort on sound. Found Motive's kit does this for several of its machines. A custom screen has to meet "one subject, every control reads"; a screen that can't is worse than the stock one.

Pick stock when: no physical or diagrammatic subject exists, the controls are independent utility settings, or the CPU budget is already tight.

---

## P1 · Section drawing

**The idea.** Draw the part that makes the sound as if cut open, like a patent drawing: the membrane, the striker, the reed, the spring, the tube. Controls move physical parts of that object. MNMD's MD KIT is the reference: each drum machine gets its own drawing and every control moves it.

**Layout.** Subject centred in the body (y 38–210), roughly 200–280 px wide so strokes stay ≥ 2 px and there's air around it. Motion marks (short arcs either side) show vibration while notes are held.

**Channel fit.** Rotation for strikers and arms (strike force, angle), shape for the vibrating surface (one mutable outline), position for dampers or pickups, count for marks.

**Budget.** Typically 1–2 paths, 8–20 nodes, 4–6 palette entries. The vibrating surface is the expensive part; keep its key tied to the control, and animate held notes by moving or scaling nodes rather than re-keying the path every frame.

**Pitfalls.** Thin parts drawn as single strokes must be closed ribbons. A striker and its pivot must share an origin or they drift apart on the device.

## P2 · Diagram + trace

**The idea.** Split the body: structure on the left (operators and their routing, a vowel chart, a keyboard with chord tones marked), the output waveform on the right. The left says *how* the sound is built, the right says *what it sounds like*. MNMD's FM STAT, VO-6 and DPRO-DENS use this.

**Layout.** Left zone x 0–240, right zone x 240–480, which lines up with encoder columns 1–2 and 3–4. When the controls split the same way (structure on knobs 1–2, tone on 3–4) the screen and the hands agree.

**Channel fit.** Structure: shade (which operator is active), scale (operator level), thickness of routing ribbons (depth). Trace: shape.

**Budget.** The trace is one mutable path (≤ 64 points). Re-key it when a control changes, not on time. If it must scroll while playing, translate the node instead of rewriting points.

**Pitfalls.** A 64-point trace across 200 px is ~3 px per point, fine for a smooth wave, coarse for noise. A noisy trace with near-vertical zigzags is exactly where near-reversal faults show up: give each tooth a small flat top.

## P3 · Trace as subject

**The idea.** The waveform *is* the object. Draw it big, bright, and let controls reshape it: pulse width, stepping (bit depth), sub-octave layers in grey underneath. MNMD's SID-6581 and SWAVE-PULSE.

**Layout.** One bright trace across most of the body, secondary layers in `#646464`–`#7D7D7D` below or behind it.

**Channel fit.** Shape for the main trace, count/position for layers, shade for which layer is engaged.

**Budget.** 1–3 paths. Cheap at rest; on note, animate amplitude with node scale rather than re-keying.

**Pitfalls.** Easy to drift into "oscilloscope", which says nothing new. Each control must change the drawing in a way you can see at 0/50/100; if a control doesn't move the trace, it needs another channel or another pattern.

## P4 · Stack in depth

**The idea.** A set of things the sound moves through (wavetable frames, presets, delay taps) drawn as offset layers receding diagonally. The current one is bright, the rest grey. MNMD's DPRO-WAVE.

**Channel fit.** Position along the stack for scan position, shade for "current", shape only on the current layer.

**Budget.** One mutable path for the current layer; the other layers are static artwork that only change shade. Very cheap to animate.

**Pitfalls.** Layer spacing ≥ ~6 px or it turns into hatching. Cap visible layers at 5–6.

## P5 · Field and figure

**The idea.** A ground plane or field (a receding mesh, a horizon, a floor) with one figure on it, plus a thin activity strip along the bottom edge (steps, notes, grains). The reference screen in `reference/` is this pattern: a face-like outline floating over a mesh, with a step strip under it.

**Layout.** Field fills the body behind everything at a low grey (`#323232`–`#4B4B4B`). Figure centred, bright. Strip in y ~196–212.

**Channel fit.** Figure: shape and scale. Field: position (scroll, tilt) or nothing at all. Strip: count and shade.

**Budget.** The field must be static artwork or it eats the redraw budget. If the field moves, move one parent-equivalent set of a few nodes, never re-key it.

**Pitfalls.** Meshes converge toward the horizon, which is where line spacing drops below 3 px. Fade or stop the mesh before it gets that dense.

## P6 · Figures

**The idea.** Characters or creatures that perform the sound: singers whose mouths open with formants, a hand strumming. Found Motive's Choir (singers) is the reference. Works when the sound has an obvious performer.

**Channel fit.** Shape for mouths/bodies (mutable outlines), rotation for limbs, count for how many perform (voices), position for spread.

**Budget.** Watch the count: eight figures × 4 nodes each is 32 nodes before anything moves. Animate only the parts a note or control actually changes.

**Pitfalls.** Figures invite idle animation (breathing, blinking). Idle stays still.

## P7 · Column affinity

**The idea.** Not a subject but a layout discipline I apply on top of the others when it fits: place the part a control drives in or near that control's 120 px column. The header already labels columns at x `120i`, so a part that sits under its label needs no extra legend.

**When.** Machines with four parallel things (four operators, four voices, four partials). Skip it when it would break the single subject into a dashboard.

## P9 · One-bit ink

**The idea.** A chunky hero figure drawn like 1-bit print: hard 2 px white outlines on everything, tone made from ordered (Bayer) dither instead of grey values, and a scatter of small sound-glyphs around it (a waveform, sparkles, squiggles, dither swatches). It sits between figure and symbol: a character you recognise at a glance, built from flat blocky planes. I picked this up from a screen the toro owner pointed at in round 9; toro's `concepts/ink1bit.py` is my first study in it.

**Why it works at 1:1.** Dither is pixel-exact, so nothing smears the way thin grey anti-aliased edges do on the real panel. Five tones (black, 25 %, 50 %, 75 %, white) are plenty, and they read as texture rather than as a grey ramp, which gives the screen its printed, hand-made feel.

**Channel fit.**

- The figure carries the big controls: shape (horns, posture) and the dither level of its main planes, which is a tone channel.
- The glyphs carry the small ones, one control per glyph, so each control has an obvious place to look. In toro the waveform glyph is shape, the sparkles are noise, the squiggles are fold, and the dither swatches slipping out of place are aphx.

**Budget.** Dither only lives in things that never move. A node is one path of ≤ 64 points, so a dithered plane (hundreds of 1 px marks) can't be a node, can't be hidden and can't change tone. Split the screen: the still parts as static artwork, run-length `<rect>`s in white (toro's body is ~1,850 at 1 px, ~430 at 2 px cells); the parts that move or change as flat palette greys with a 2 px white outline, matched to the dither density they stand in for. Toro's `screens/toro/gen_ink.py` is the worked example.

**Pitfalls.**

- Dither at 50 % next to a 2 px outline can read as a grey blur. Leave a 1 px black gutter inside every outline.
- White-on-white: when a control drives a plane toward white, features drawn in white (eyes, highlights) disappear. Cap the plane at 75 %, or invert the feature to black.
- Ornaments multiply. Every glyph must be a control; if it isn't, cut it.
- Don't copy the reference's figure or composition. The pattern is the language (outline, dither, glyphs), not that drawing.

## P10 · Voice field

**The idea.** A field of identical simple parts (isometric columns, tiles, bars) whose geometry is computed from a small model of the machine's own signal path. Every control becomes an operation on the field that does to its shape what the control does to the sound: a second oscillator becomes a second wave across it, a folder folds its heights, a filter decides how much fine detail survives, a clip flattens its peaks. Notes act on the field where the key lands. Toro's stacked blocks (`library/toro-blocks/`) is the worked example.

**Why it works.** The mapping explains itself, so nothing on screen needs a label. It's also abstract enough that drawing quality never becomes the question, which is where figurative subjects kept failing. Toro went through nine rounds of bulls before landing here.

**Channel fit.** Shape (heights) carries the big controls; shade on a row or band carries one control at most; count and position come from the note. One control can also act on the whole field's form rather than its heights: in toro, fold rolls the field up into a drum, because a folder folds the signal back on itself.

**Budget.**

- **Build every part from translated pieces.** An isometric column is three nodes (top, left face, right face). Make the faces fixed-length pillars that move with the top, so height changes are pure translation: no mutable outlines, no static art.
- **Draw back to front.** Each pillar's overhang is then hidden by the columns in front of it. Two black skirt nodes, drawn last, hide the front row's.
- **Snap to whole pixels.** Edges stay crisp, and a part only redraws when it really moves.
- **Check the count.** Seventy columns is 210 nodes; keep the grid at 70–75 columns with the 8-node two-page header.
- **Mix solid and wireframe.** Give parts two looks from the palette, solid faces or a hidden-line wireframe (black fill, grey edge), and swap a part's palette instead of reshaping it. Toro hollows the quiet part of the wave (the lowest 35% of the voice's range) plus a fixed seeded scatter of about a quarter of the rest, so the wireframe reads as texture everywhere and still moves with the sound. Decide it on the voice's own value, before note lifts, so notes don't flicker parts between looks; keep struck and lit parts solid. Wireframes must keep their black fill: see-through wireframes turn a dense field into a tangle at 1:1. It costs two palette entries and no extra redraw.
- **Pillars or slabs.** Floor-length pillars (with black skirts drawn last) make heights read as solid columns, but they pin the field to the floor. If a control should lift, bend or roll the field, use short slabs: toro's fold wraps the field round a drum, which pillars can't follow because a node never tilts. Slide each upright block to its point on the curve, push it out along the normal by its height, and shrink the relief as it wraps so the curve reads before the texture.

**Pitfalls.**

- **Field-wide motion is expensive.** A note that moves the whole field (a roll, a ripple) changes far more than ~20 nodes a frame. Make it a decision with the owner, and write down the fallbacks.
- **Hairline seams between faces.** Use same-colour strokes (~0.3 px) and check them on the device.
- **Shade can't be the only signal.** Don't let a control's whole effect be a shade change; put it on geometry too.
- **Nodes slide, they never tilt.** Anything that should rotate (a roll, a curl, a flap) is faked by moving upright parts along the curve. What failed for toro's roll, so you don't repeat it: flat tiles wound into a spiral read as floating slats ("lilies"); curling the *front* edge back paints the lifted rows over everything, because the fixed draw order puts them last; a hinged flap with floor-length pillars reads as a slab. What worked: slabs, a curve that keeps back rows drawn first, and relief flattened as the field wraps. Watch for leftover masks too: the skirts that hid pillar overhang cut into the drum until they were hidden.

## P11 · Instrument stack

**The idea.** When the machine plays something people already know by sight (a drum kit), draw that, simply: the instrument's parts as clean geometric primitives (ellipses for heads and cymbals, bands for shells, short strokes for lugs) in a line drawing, arranged so every part the sound can select has its own place. Theseus stacks its kit into a tower, kick at the base to hi-hat on top (`library/theseus-tower/`).

**Why it works.**

- **Recognition is free.** Nobody needs a legend for which drum is which.
- **Clean primitives keep it crisp.** Ellipses, bands and short strokes avoid the hand-drawn outlines that failed for toro's bulls.
- **Lines keep overlaps legible.** A line drawing (black shapes with grey outlines) keeps overlapping parts readable where solid fills merge them.

**Channel fit.** Position for the hit (only the struck part moves, only upward), shade for the hit's brightness (only the struck part fills), count for decay (rings), and the secondary parts for the rest (cymbals rock, a floor that doubles as a clock).

**Budget.** One part moves per hit, so the redraw cost is that part's nodes. Build each part from a handful of nodes (shell, head, rim, lug strip), not one per detail.

**Pitfalls.**

- **Solid fills everywhere.** They make neighbouring parts run together; Brian's note on the first version.
- **Moving everything.** A hit that wobbles the whole instrument reads as noise; move only what played.
- **Floors and shadows out of perspective.** Put them in the same projection as the heads.

## P12 · Orrery

**The idea.** A machine whose state is a set of things in a cycle (a register's steps, voices, patterns) drawn as a solar system: a sun, concentric orbits, planets that orbit. Each planet stands for one item; it fills when its item is active and flashes when it sounds. A sequence shows as links running along an orbit from planet to planet. Meikyu's player page (`library/meikyu-orrery/`) is the worked example.

**Why it works.** Orbits read as cycles without a legend, motion is constant but calm (everything turns at one rate), and a parameter can change the population (how many planets are out) rather than a dial.

**Build it in 3D.** Model the sun as a sphere and the orbits as evenly spaced circles in one plane, put one camera on it, and project. Order by distance to the camera; split orbit lines at the sun's depth so they wrap it. Size from depth. (`opxy/craft.md`, Think in 3D.)

**Budget.**

- **One node per planet look.** A planet is one path (≤ 64 points, all loops wound one way so a fill covers the disc); its kind sets how many variants it needs (wireframe 3 for spin, rocky 2 for tumble, smooth and banded 1). Fill and flash are palette swaps.
- **Links are mutable outlines.** Four at most: the live one plus three fading. Draw them on the orbit itself, in the direction the planets travel.
- **Count it.** Write a `device_parts()` that tallies the nodes on every build and keep it under the limit with headroom.

**Pitfalls.**

- **2D ellipses bent by hand** don't wrap the sun and bunch up near it. Model it.
- **A ring around a point on the screen's edge is half off-screen.** Accept it or move the centre; no camera angle fixes it.
- **Too many planets for the orbits.** Guarantee spacing only for the ones that carry meaning; let the rest step out of view while they would touch.
- **Links across the whole screen.** Keep links within one orbit and one phrase; when the sequence changes orbit, flash the planet instead.
- **Players can't do this yet.** Today's player page is 24 on/off dots; this needs bound nodes. Say so up front.

## P8 · Headers

- **Stock header (≤ 4 controls).** Do nothing; artwork starts below y 20.
- **Two pages (5–8 controls).** Use `page_header.hpp`; reserve y 0–38. Page 1 is what's played most. Repeat a page-1 control on page 2 where there's no alternate; never add filler.
- **Own header.** Only when the header itself needs to show something stock can't. Cover y 0–20 and rebuild it with nodes and text slots; this uses every text slot, so budget for it.

---

## Motion vocabulary

These are the motions I reach for, all short, decelerating, and answered by the player:

| Motion | Triggered by | How | Notes |
| --- | --- | --- | --- |
| Settle | turn | ease the driven part to its new pose over 0.15–0.2 s | Reduced motion: jump |
| Strike | note on | a part kicks then settles (striker, membrane) | Restart on each note serial |
| Sustain | held notes | motion marks or a gentle oscillation while `held` | Runs as long as notes are held, then releases |
| Release | hold ended | ease back to rest | Same 0.15–0.2 s |
| Page grow | encoder press | edited row grows to 20 px and onto the bar | `page_header.hpp` does this |

Nothing moves at rest. If a screen looks dead when idle, the subject is too weak, not the motion too little.
