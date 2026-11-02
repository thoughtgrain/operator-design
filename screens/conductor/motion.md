# Conductor · motion (revision 2)

These rules apply to every page:
- Every ease is exponential ease-out and settles in 0.2 s.
- Reduced motion, a track change and a page change all jump to the end state.
- Nothing moves while the sequencer is stopped and no knob is turning.

`rev2/conductor-pages.mp4` shows all of this at 120 BPM.

## M1 · song

| trigger | what moves | time |
| --- | --- | --- |
| step | the groove tick under the playhead goes bright; the phrase-line playhead steps | instant |
| chord change | the next arch becomes the bright one; the sounding triangle and its label swap; the plate title changes | instant (a restyle) |
| turn key | triangles, labels and arches slide along the line to their new pitch classes | 0.2 s per click |
| turn scale | degrees whose pitch class changes slide one tick | 0.2 s |
| turn prog | arches change: each one eases from its old span to its new one (scale + position) | 0.2 s |
| turn dens / cmplx | kicks appear, or move off the beat, in the groove | 0.2 s |
| turn hrate | separators slide to their new bars | 0.2 s |
| turn swing | offbeat ticks slide late | 0.2 s |
| turn evolve | candidate triangles scale | 0.2 s |
| freeze | candidate triangles return to their resting size; `frozen` appears | 0.2 s |

## M2 · lanes

| trigger | what moves | time |
| --- | --- | --- |
| step | the playhead steps; the notch under it goes bright | instant |
| turn lane | the page changes lane (title, notches, ticks) | instant |
| turn oct | the edge and its notches rise or fall | 0.2 s |
| turn vel | notches scale | 0.2 s |
| turn gate | gate ticks slide along the edge | 0.2 s |
| turn dens / vary / lock | notches appear, shrink, or move to their new steps | 0.2 s |

## M3 · lane

| trigger | what moves | time |
| --- | --- | --- |
| step | the playhead steps; the tread under it goes bright | instant |
| chord change | treads move to the new chord's pitches; risers re-length | 0.2 s |
| turn any arp control | treads move to their new steps and pitches; risers follow | 0.2 s |

## M4 · route

| trigger | what moves | time |
| --- | --- | --- |
| turn to | the trace slides to the new bus, with hops appearing and disappearing as it passes buses | 0.2 s per click |
| mute | the trace slides back behind the names; a strike crosses the name | 0.2 s |
| unmute | the trace slides back out | 0.2 s |
| turn low / high | the caps slide; octave segments change shade as a cap passes them | 0.2 s |
| turn xpose | lit octave segments shift | 0.2 s |

## Flashing

At 16ths and 180 BPM the bright tread or notch moves on 12 times a second. That's a moving mark, not a flash of one element. Each element lights once per pass, so nothing exceeds WCAG 2.3.1's three flashes a second.
