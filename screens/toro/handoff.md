# Toro · handoff (revision 3)

For implementing the TAURUS atlas screen in `thoughtgrain/labyrinth` → `opxy/machines/toro`. The frames are the target poses, and `prototype.html` is the moving reference, built from the same model. `gen_frames.py` holds the exact geometry and maths, so port from it rather than measuring pictures.

## What changes in the machine

| File | Change |
| --- | --- |
| `gen_panel.py` | Static artwork, from `gen_frames.static_back()`, `labels()` and `inset_frame()`: the grid (3 declination arcs, 6 hour lines, 1 px `#323232` filled ribbons), Pleiades, the Moon's dashed ephemeris track, the radiant symbol, labels (10 px `#7D7D7D`, `TAURUS` 12 px `#AFAFAF`), black halos behind chart stars, and the magnifier (black window, rim, 4 reticle ticks, leader to Aldebaran, "α Tau"). Nodes as in the map below. Remove the old field scatter, Milky Way scatter, sky band, comets and Pleiades ring. Header cover path gets `stroke="none"`. Greys limited to the stock ramp. |
| `display.cpp` | Rewrite the drawing per this handoff and `motion.md`. No camera: the chart is fixed. |
| `display.h` | New `DisplayState` (below). |
| `definition.json` | `resources.display` → the block below. Parameters unchanged. |

## Display block

```json
"display": {"stateBytes": 180, "stateAlignment": 4,
            "paths": 3, "points": 64, "nodes": 229, "texts": 16, "palette": 16}
```

## Node map

| Nodes | Part | Driven by | Channel |
| --- | --- | --- | --- |
| 0–2 | Milky Way contours: outer, mid, core (mutable, 64 points, node at (440, 102), points within ±64) | fold, note | shape `w = (half·(1 + lump) + fold(g·sin(…))·amp·(c+1)/3)·taper`, `g = 1 + 7·fold`, `amp = 0.6 + 17·fold^1.4`; shrink to fit ±63.5, never clamp points. Shades `#323232`, `(2 + 1.5·fold)/7`, `(3 + 2·fold + note)/7` |
| 3–10 | header bar | `page_header.hpp` | stock |
| 11–19 | chart stars (ald, g1–g4, β, ζ, back, tail) | note (Aldebaran only) | Aldebaran 1.3× on a note |
| 20–28 | figure lines | note | shade `(3 + 3·flash)/7` |
| 29 | magnified star | cutoff, note | scale: radius `1.8 + 25·cutoff` (+12 % on a note); author r 30 |
| 30 | its bright core | cutoff | radius `max(1.6, 0.78·r)` |
| 31 | its diffraction spikes (drawn under the disk) | cutoff, note | length `min(38, r + 9 + 7·flash)` |
| 32–35 | Airy rings | res, cutoff, note | ring i: brightness `clamp(4·res − i + 0.25)`, shade `(1 + 3.5·b·(1 − 0.12i))/7`; radius `r + 5 + 5.5i`; hidden past the window |
| 36, 37 | neighbour stars in the window | cutoff | offset × `(1 + 3.5·cutoff²)`; hidden outside the window |
| 38 | Moon body (`#323232`) | spread | x `170 + 142·spread`, y 63 |
| 39 | Moon limb (`#AFAFAF` annulus) | spread | same position |
| 40–47 | Moon phases (lit 0.1 → 1.0, `#646464`) | shape, spread | show `round(7·shape)`; cusps end at ±78° |
| 48–63 | meteor trails | drive, note | show `2 + round(14·drive)`; shade `(3 + 2·drive)/7`; a note lights one in fixed rotation |
| 64–228 | faint stars | noise, aphx, held | show `40 + round(125·noise)` in fixed order; drift `kink·(6 + 20·h₁)` along `360°·h₂`, `kink = 0.4a + 0.6a³` |

## Palette

Entries 0–7: the stock ramp `#000000 #323232 #4B4B4B #646464 #7D7D7D #969696 #AFAFAF #CDCDCD`. 8–15 spare.

## DisplayState (estimate 180 bytes)

`PageHeader` 20 · `NoteTracker` 16 · serial and note age 8 · eased controls 32 · contour key 8 · faint-star lit bits 21 plus 3 twinkle timers 6 · drift cursor 4 · trail rotation 4 · seed and clock 8 · padding. Set `stateBytes` to `sizeof(DisplayState)`.

## Path key policy

The contours re-key when fold's detent value changes, never on time. A note only changes their shade.

## Open device checks

Photos (rest, playing, heaviest) · caption `1.25` in the device font · host `display()` redraw, including while turning aphx · `sdk.py test` preview frames · CPU readout · presets by ear.
