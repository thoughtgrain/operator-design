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

Proportion rule from ux.md: the channel's travel scales with how much the control changes the sound, with a generous floor. I score each control's audible impact 1–5 in the brief and use that score to size its travel.

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
