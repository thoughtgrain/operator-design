
### Motion: what moves, and why

Idle is still (ux.md), so every change below is caused by a note or a control. The bull is a character, which invites breathing and blinking; I'm not doing that. The note is the heartbeat.

| Element | On a note | With a control | How it's done on the device |
| --- | --- | --- | --- |
| Head (horns, ears, face) | wobbles side to side on its neck: ±7 px at the horn tips, 2.2 Hz, decaying over ~0.5 s, the neck fixed | spread scales the horns from their roots; cutoff opens the eyes | the head is one node group; the wobble is a skew of that group, so it's a few node transforms, not re-keyed paths. Horn scale is a mutable outline on each horn |
| Eyes | flash wide (white, black pupil) for the first 150 ms | cutoff 0 → dead black, default → the reference's square glint, 100 → wide open | three pre-dithered artwork states, shown by cutoff; the flash shows the wide state |
| Steam | flares one puff further for ~0.6 s | drive brings it out of the nostrils puff by puff; nothing at 0 | a chain of static puffs, each a node, revealed in order along the plume by drive; the flare reveals one more |
| Tail tuft | flicks up and against the wobble | — | one node, two transforms |
| Bar glyphs (both) | pulse taller with the note's envelope, then settle | shape morphs the envelope saw → triangle | bars are 1 px-wide nodes scaled in y; cheap |
| Dither swatches | shimmer: the slip jumps a step | aphx slips them per key, with a torn scanline | pre-dithered swatches translated by node; the scanline is one bar node |
| Burst beside the muzzle | — | res grows it and adds rays | one mutable outline |
| Squiggles | — | fold adds them, one per quarter turn, and tightens their wave | mutable outlines, hidden until fold wakes them |
| Sparkles and grain | — | noise adds sparkles and lone pixels | a small pool of nodes shown by count; the grain is one static artwork layer per noise step |
| Legs, hooves, body | nothing | nothing | the planted stance is the point; moving it would break the drawing |

Budget check: a note moves the head group (1 transform), the tuft (1), the eyes (1 swap), one steam puff (1 show) and ~30 glyph bars (scaled). The bars are the cost; if ~20 changed nodes per frame is the limit, I pulse only the big glyph (18 bars) and leave the small one static. Everything else is under ten nodes.

`i2-trace/note.gif` is a 0.9 s note at 2×, with drive at 30 so the flare shows.
