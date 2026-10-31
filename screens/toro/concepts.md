# Toro · reset: five concepts (phase 3)

2026-10-31. The Taurus atlas (revision 3) is set aside, not deleted; it's in git history and stays a fallback. Each concept below names its drawing language and a reference (`opxy/craft.md`), maps all eight controls to distinct channels, and notes what it costs on the device.

Toro's sound, for reference: two saw/triangle oscillators (spread sets osc 2's ratio, 1.0–1.5) → wavefolder (1–8×) with noise into it → resonant low-pass → soft-clip drive. Aphx gives each key its own drift, gentle then chaotic. Scores: spread 4, fold 5, cutoff 5, res 3, shape 3, noise 2, drive 3, aphx 2→5.

---

## 1 · The bull drawn by its own spectrum

**Language:** a mathematical plate. A single contour line, graph-paper hairlines, small figure numbers. **Reference:** MNMD FM STAT for restraint.

The bull's silhouette is drawn as a Fourier series, one closed line. The low-pass filter does to the drawing what it does to the sound.

| Control | What the player sees |
| --- | --- |
| cutoff | how many harmonics draw the bull: a smooth blob at 0, a detailed bull with horns and hooves at 100 |
| res | ringing along the outline at the cutoff harmonic, the way a resonant filter rings on an edge |
| fold | the outline's radius is wavefolded: edges fold back on themselves |
| spread | a second, fainter outline drawn at osc 2's ratio, separating from the first |
| shape | corners sharpen (saw) or round off (triangle) |
| drive | the silhouette presses against a frame and flattens there, which is soft clipping made visible |
| noise | stippled dots inside the silhouette |
| aphx | the line wavers per key, steady then trembling |
| note | the outline brightens and briefly gains harmonics, then settles |

**Why it fits:** every control is the DSP itself, drawn on the bull. **Cost:** 2 mutable outlines (64 points each), ~60 nodes. **Risk:** a 64-point Fourier bull needs careful simplification to still read as a bull at low cutoff.

## 2 · Patent drawing of the mechanical bull

**Language:** a patent section drawing: numbered parts, leader lines, section hatching kept sparse. **Reference:** MNMD MD KIT. **Lineage:** the OP-1 toro was a robot bull on a hydraulic ram.

The bucking saddle sits on a shaft driven by two cams. A cam turns rotation into motion, so it's a mechanical oscillator, and its profile is a waveform.

| Control | What the player sees |
| --- | --- |
| spread | cam 2's lobe count against cam 1's (the ratio) |
| fold | the cam profile folds: more lobes, sharper reversals |
| shape | the profile's slope: saw-like ramps or triangle-like symmetry |
| cutoff | the hydraulic damper's valve opens, so the piston's stroke lengthens |
| res | the return spring: coil tension, and how long it bounces after a note |
| drive | a pressure gauge's needle swings toward red-line (drawn grey) |
| noise | grit and sand on the base plate |
| aphx | worn bearings: parts tilt off-axis, steady to wobbling |
| note | the saddle bucks: cams turn, piston strokes, spring rebounds |

**Why it fits:** oscillators as cams; the note is a physical event with a big, readable motion. **Cost:** 1–2 mutable outlines for the cam profiles, ~50 nodes. **Risk:** the most parts of any concept; needs discipline to stay one clear subject.

## 3 · Harmonograph

**Language:** a Victorian scientific instrument engraving, with the trace it draws. **Reference:** 19th-century instrument plates; MNMD SID-6581 for the bold trace.

Two pendulums (two oscillators) move a pen over paper. Holding a note draws; releasing lifts the pen.

| Control | What the player sees |
| --- | --- |
| spread | the pendulums' frequency ratio: an ellipse at 1:1, a 3:2 figure at a fifth |
| fold | the pen reflects at the paper's edge, folding the figure back on itself |
| cutoff | damping: how far the figure spirals inward before it fades |
| res | coupling between the pendulums: the figure beats and rings |
| shape | the swing's waveform: sharp turns (saw) or round loops (triangle) |
| drive | the figure pushes past a margin and flattens against it |
| noise | ink speckle along the line |
| aphx | per-key detune: the figure precesses and smears |
| note | held: the pen draws the trace; released: it lifts and the trace stays until the next note |

**Why it fits:** literally two oscillators drawing, and "animate while notes are held" is the instrument's own behaviour. **Cost:** 2 mutable outlines (the trace in two halves), ~30 nodes. **Risk:** no bull; it's toro's sound, not toro's name.

## 4 · Rock-art survey of an aurochs

**Language:** an archaeological tracing of cave art: dotted outlines, rock-relief contour lines, a survey grid, scale bar and site labels. **Reference:** survey plates of Palaeolithic art (the oldest bulls anyone drew).

An aurochs traced from a cave wall, documented the way archaeologists record it.

| Control | What the player sees |
| --- | --- |
| cutoff | a lamp's pool of light: closed shows a small lit patch, open reveals the whole wall and the animal |
| res | the lamp's edge sharpens into bright bands |
| fold | the rock relief: contour lines of the wall fold into ridges |
| spread | a second animal painted over the first (a palimpsest), offset by osc 2's ratio |
| shape | the outline's technique: incised (sharp, dotted) to painted (soft, continuous) |
| drive | pigment: hatching density inside the animal |
| noise | calcite speckle on the wall |
| aphx | hand tremor in the traced lines |
| note | the lamp flickers up, then settles |

**Why it fits:** deeply bull-native and nothing else on the OP-XY looks like it. Cutoff as light is very readable. **Cost:** 2 mutable outlines (relief contours), lamp as scaled nodes, ~80 nodes. **Risk:** hatching and stipple must respect the ≥ 3 px spacing rule.

## 5 · Anatomical plate of the bull's skull

**Language:** a natural-history engraving: the skull in side view, fine outlines, a few hatch lines, figure letters. **Reference:** encyclopedia anatomy plates; theseus's helmet, so the two screens sit together.

| Control | What the player sees |
| --- | --- |
| cutoff | the jaw opens, like a mouth opening a filter |
| res | breath rings from the nostrils, tighter and brighter |
| fold | the horns curl and twist further, folding back on themselves |
| spread | the horns spread apart (two horns, two oscillators) |
| shape | horn tips: sharp (saw) to blunt (triangle) |
| drive | vapour from the nostrils thickens |
| noise | stipple on the bone |
| aphx | the skull tilts and drifts off its axis |
| note | a snort: vapour puffs and the jaw snaps a little wider, then settles |

**Why it fits:** clearly a bull, mature and quiet, and pairs with theseus. **Cost:** 2 mutable outlines (horns), ~40 nodes. **Risk:** jaw and horns are close together; spread and fold both act on the horns, so they need clearly different motions (apart vs curl).

---

## Choosing

Concepts 1 and 3 are the most faithful to the sound; 2, 4 and 5 are the most bull. My order, by how well each control reads and how distinct it would look on the OP-XY: **1, 2, 4, 5, 3**.
