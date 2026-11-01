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
