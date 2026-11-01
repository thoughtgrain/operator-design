# Theseus · concepts, round 1 (stacked blocks)

Theseus is a DFAM-style drum voice from labyrinth: every note is a hit, the note's pitch picks the drum (low = kick, middle = toms and snare, high = hats and metal), and a hit LFO steps once per note, one cycle every 32 down to 2 hits (Rate). Header: decay punch cutoff fm / noise lfo rate tune.

I'm working in the house language from `library/toro-blocks/` (P10 Voice field): grey isometric blocks, built so every moving part is a translated node. For a drum machine the field's heartbeat is the hit, its geography is the zone, and its slow motion is the hit LFO. `concepts/blocks.py` draws all five from one small model of theseus (zone from note + tune, decay time 30 ms – 1.5 s with high drums shorter, the LFO as a triangle over the hit count). The board is `concepts/board-blocks.png`, with columns rest, kick, snare, hat, a bar's phrase, and everything at 100.

| | Design | The idea | Hit | Decay | LFO / Rate | Budget (worst frame) |
| --- | --- | --- | --- | --- | --- | --- |
| t1 | Kit towers | a riser of blocks; five drums stand in the middle row | the zone's tower punches up, stacked in blocks | how long it takes to fall | towers sway, stepping per hit | ~190 paths: fits |
| t2 | Step floor | a 16-step bed, four rows from kick to metal | the cell at this step, in its zone's row, jumps | how long the raised cells take to settle (a trail) | a wave across the bed, wavelength = Rate in hits | ~250: needs a 16 × 3 bed |
| t3 | Labyrinth | Theseus in the maze: a token walks the corridors | one step per hit; the walls near the zone breathe | how long the walls stay raised | the loop the token walks is the LFO cycle: 32 steps long down to 2 | ~250: fits if floor tiles are one node each |
| t4 | Crater | one slab of blocks | a crater punched where the zone lands, its rim ringing outward | how long the ring lasts | the slab tilts with the LFO | ~280: needs 12 × 6 |
| t5 | Hit stack | four lanes, kick to metal | a block lands on the zone's lane | how long the new block stays lit | the stacks fall when the LFO completes a cycle; the tick column counts down | ~50: lightest |

Every design: punch = how far a hit lifts or digs; cutoff = how bright a hit lights; fm = hits split and jag; noise = loose blocks thrown off a hit (more for high drums); tune = shifts which drum a note lands on.

Next: pick one; it goes through the protocol (definition from labyrinth's port, frames at 0/50/100, lint, perceptibility, prototype, video, handoff).

## Round 2: drums you can see

Round 1 read as abstract fields; Brian wanted it to look like drums. `concepts/drums.py` builds real drums from clean primitives: an ellipse for each head, a band for the shell with a darker right third, lugs and hoops as small blocks, cymbals as thin discs with lathe rings. No hand-drawn outlines, so the drawing stays crisp. Board: `concepts/board-drums.png`.

| | Design | What a hit does | Decay | LFO / Rate |
| --- | --- | --- | --- | --- |
| d1 | Kit (three-quarter view): kick facing us, two rack toms, snare, hi-hat | the struck drum's head dips and lights, rings spread across it; the kick's front head bulges; the hat lifts and tips | how many rings and how long they last | the kit sways one step per hit |
| d2 | Overhead kit: the same kit from above, every head a disc with its lugs | rings spread across the struck head; cymbals light and throw shimmer rings (fm) | rings | cymbals slide |
| d3 | One drum: theseus is one voice that becomes every drum | the single shell becomes the hit's drum (deep kick, tom, snare with wires, a cymbal for hats); five markers below light the zone | rings | — |
| d4 | Drum tower: shells stacked from kick at the base to hats on top | its tier lifts and lights | rings | the tower leans, more toward the top |
| d5 | Pads: a 4 × 4 drum-machine pad grid | its pad presses down and lights; fm splits the glow | how long the pad stays lit | a cursor steps across the pads, one cycle per Rate |

Every design keeps the round-1 mappings: punch = how far a hit moves, cutoff = how bright, fm = shimmer and split, noise = sizzle specks (more for high drums), tune = which drum a note lands on.

### d4, revision 2

Brian liked the tower and asked for two changes, so `concepts/d4_video.py` now does this:

- **Each tier is drawn as the drum it plays**, bottom to top:
  - the **kick** is the deepest, darkest shell, with a pale wrap stripe, claw hooks and a felt beater patch;
  - the **floor tom** is tall, with legs out to the sides;
  - the **snare** is a shallow, bright metal shell with many lugs, a strainer and its wires showing underneath;
  - the **rack tom** is medium depth, with a mount bracket;
  - the **hi-hat** is two cymbals on a clutch rod.
- **Only the drum that's hit moves, and only upward.** It rises fast and settles, never dipping below rest. The tiers above don't ride along, and there is no wobble or lean. The hit LFO now sets how high each hit jumps, and a hat hit lifts the top cymbal open.

The tiers step down in size so each head's front crescent shows, where its rings spread.
