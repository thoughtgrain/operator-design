# Rain · subject pass 03 · notes

The owner's window: the whole screen is the pane, drops land on it, cling, gather, and a heavy one lets go and runs down, sweeping up what's below it and leaving a clear trail. All five come from `sketch.py` and one pane model: **a note is a drop landing** (rain's control code is a drop clock, so the landing is the event the player hears; a breakaway only happens when beads have gathered, which is the puddle's echo, so each bead a run swallows is a note played again). **Pitch is height on the glass** (higher on the pane, higher note), so **roof** is the height of the band drops land in: one line at 0 st, most of the pane at 36. **Gust** slants each landing (a short streak just before the drop arrives) and pushes runs sideways. **Puddle** is how much the glass holds before a bead lets go: bigger heavy beads, longer runs, more beads swept up and replayed. Rest frames are at the defaults (rate 1.0, roof 12, gust 0, puddle 0); the clips use gust +20 so the drift shows. Every bead is a sagging spherical cap projected through one camera per variant. All five lint at 0 errors and 0 warnings (no `text-in-drawing`), are ≥ 90 % black, and were judged at 1:1 from `vN/rest.png`. Uniqueness: `ready_for_pick`, every pair differs in angle and language, and the highest subject overlap is 0.14.

Each `vN/motion.gif` is 480 × 220, 20 fps, 4.8 s: seven drops land in the first 3 s (two of them on the heaviest bead at their height so it lets go), runs finish, and the last 0.5 s is still (0 changed elements). The changed-element counts below are SVG leaves changed per frame, a stand-in for nodes, not a device measurement.

**v1 · the trails (bold closed outlines).** The pane face on and wide. A band of small beads in bold outline, and the lanes heavy beads wiped on the way down, each a closed outline with the beads it dropped strung inside.
Strong: the trails are the truest trace of what the glass did, they read as rain on a window instantly, and motion is cheap (1.2 changed elements a frame on average, peak 5). Weak: at 1:1 the band of small rings can read as bubbles, and the brightest thing at rest is a small bead, not the trace.

**v2 · the cut edge (cutaway section).** The pane at an angle, cut at its right edge: the glass's thickness as a hatched section, and the heavy bead on the cut in profile with its meniscus, swelling with puddle.
Strong: the most physical "what each knob does to a real window", and the profile bead is a real, surprising subject. Motion is calm (3.0 a frame, peak 9). Weak: the section reads as a thin post at 1:1, the subject sits at the edge while the bead field takes the middle, and gust is foreshortened.

**v3 · the gathered drops (exploded view).** The heaviest bead with the drops it gathered pulled back off the glass along the line they came in on. Each floats over its landing height with a leader back to it. A new drop enters bright on the right and the oldest leaves.
Strong: it's the only one that shows the puddle's memory and pitch together, and the newest part answers each note. Weak: the leaders, contact rings and slides edge toward a node graph, the flattened drops can look like balloons, and the background beads tell a separate story. Peak cost grows with puddle (all parts shift on a note; peak 24 here).

**v4 · one heavy bead (single-weight contour).** Close on one bead about to go, its surface in level contours sagging to its heavy lower edge. Neighbours and an old wiped lane are cut by the frame. In the clip it lets go and leaves the frame.
Strong: the calmest and most authored at 1:1, with one clear subject that only this machine would have, and the breakaway is a strong, physical note answer. Weak: nested contours flirt with the target rule, the subject is gone after it runs (an empty lane until a new bead gathers), and hierarchy rests on grey steps alone.

**v5 · rain on the glass (hatched mass).** Close, literal: every bead and run is a 45° hatched mass (water is see-through), with the lower meniscus rim lit. The newest rim is the brightest.
Strong: it looks most like water on a window, the hatching follows the craft rule exactly, and the heavy runs with their hatched lanes are the owner's picture. Weak: it's the costliest in motion (12.5 a frame on average, peak 46, every hatch line a node), small hatched beads near striped balls, and its layout is close to v1's.

## Ranking (designer's, not the pick)

1. v4: the one I'd put beside theseus-tower. A single subject at large scale, calm, unmistakably a heavy drop on glass, and its breakaway is the note made visible. It needs a rule for what holds the eye after the bead has gone.
2. v5: the owner's sentence drawn literally: drops gathering into heavy masses that run and leave lanes. It needs a cheaper hatching for moving drops.
3. v1: the clearest whole window and the cheapest motion. It's less authored than v4 and v5.
4. v2: the most physical idea, but the section strip and the edge subject don't read well enough at 1:1 yet.
5. v3: it explains the most and reads the least. It's at risk of looking like a diagram.
