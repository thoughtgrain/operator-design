# Theseus (drum tower) · audit

| | |
| --- | --- |
| Audited | 2026-10-31, against tokens `source.ref`: pull/260 (docs/design-guidelines), read 2026-10-31 |
| Author | Brian Hinton (thoughtgrain); confirmed his to share: yes, asked for it on the reference list |
| Licence | MIT (labyrinth's OP-XY ports) |
| Material | `frames/` (26: rest, playing, each control at 0/50/100), `theseus-tower.mp4` with simulated engine audio (engine code run on a computer, not a device recording) |
| **Verdict** | **meets, with notes** |

## Results

| Check | Result | Evidence |
| --- | --- | --- |
| Artwork (`lint_frame.py`) | 0 errors in all 26 frames | warnings: the SDK header zone; parts under 3 px (sparks, lugs) |
| Perceptibility | pass on all eight controls and the note | table below |
| Contact sheet, by eye | one subject; grey only; the played drum is the brightest thing on every playing frame | `contact.png` |
| Motion | idle still; only struck drums move, only upward, settling in ~0.3 s; hats rock ~0.5 s | video |
| Sound | the video's soundtrack is theseus's engine.cpp playing the same score, simulated on a computer; how the device sounds is pending | `screens/theseus/audio/` |

### Perceptibility

Measured at one moment of play (kick, snare, high tom, hat and low tom struck within 330 ms). Control scores: decay 4, punch 4, cutoff 4, fm 4, noise 3, lfo 3, rate 1 (silent at the default LFO depth of 0), tune 3.

```
control        score  need %  0→100 %  0→50 %  50→100 %  span
decay              4    1.60     9.75    9.71      5.15   178  ok
punch              4    1.60     9.93    7.55      7.57   204  ok
cutoff             4    1.60     3.26    1.66      1.60   122  ok
fm                 4    1.60     3.43    1.01      3.97   284  ok
noise              3    1.20     2.18    1.13      1.13   253  ok
lfo                3    1.20     4.91    2.44      2.42   203  ok
rate               1    0.50     0.73    0.37      0.82   191  ok
tune               3    1.20    14.93   13.99     11.98   178  ok
note response      —    2.00    13.62       —         —   204  ok
pass
```

## Notes

- **Not yet fitted to the device.** This entry is the design. The drawing is generated per frame as plain SVG, not yet as the fixed set of nodes `display.cpp` moves.
- **Expected node budget.** Each tier's lugs and rings must become a handful of nodes per drum, and the floor clock's dashes up to 32 nodes; the redraw cost per hit should stay near one tier's nodes.
- **Next step.** The design goes through `opxy/protocol.md` (definition, fragment, budget) before it ships.
- **Device pending.**
