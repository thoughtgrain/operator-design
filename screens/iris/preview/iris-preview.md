# Iris · preview

**Audio: simulated (engine code run on a computer, not a device recording).**

`iris-preview.mp4` is 480 × 220 at 1:1, 30 fps and 27.2 s long. `iris-preview-2x.mp4` is a 960 × 440 copy for sharing, scaled nearest-neighbour. The same label is in both files' metadata (`comment`).

## How I made it

One score drives the picture and the sound, so every change you see is a change you hear.

- **Picture.** This is iris's real `display()` from `operators-xy/machines/iris/display.cpp`, run on a computer over the score by `display_host.cpp`. The nodes it places are drawn with the authored geometry from `panel.svg.fragment`. `host_sdk/` is my own small stand-in for the SDK's draw API, not the SDK, so this shows what the device code places, not how the OP-XY rasterises it. The header is a preview drawing in a fallback font.
- **Sound.** This is iris's real `engine.cpp`, run block by block over the same score by `../audio/render.cpp`. A plain envelope stands in for the OP-XY's envelope page: 6 ms attack, full sustain, 250 ms release. The device's envelope, filter, effects, mixer and output stage aren't in it, so this is how the engine code sounds on a computer, not how an OP-XY sounds. I normalised it to peak at −3 dBFS and saved it as `../audio/iris-preview.wav`.

Rebuild with `python3 make_preview.py`. It needs g++, node with Playwright, ffmpeg, and the operators-xy checkout at the path at the top of the script.

## Score

| time (s) | what happens | what you hear |
| --- | --- | --- |
| 0.0–1.5 | rest at the defaults (morph 33, overlap 25, spread 0, tone 70) | silence. Nothing moves: the mix outlines are written once and not again |
| 1.5–4.5 | four held notes (0.55 s each) | a triangle with a little sine and square; the bright line brightens and travels along the arc while each note is held |
| 4.5–5.1 | hold ended | the release tail; the line slows and settles |
| 5.1–17.9 | morph, overlap, spread, tone, each turned default → 0 → 100 → default over 3.2 s while an A minor pentatonic phrase plays (0.32 s notes every 0.4 s) | sine → saw; one band → all four; still → beating; dark → open |
| 17.9–18.6 | page press: page 2 (skew and phase move to the top row) | silence |
| 18.6–25.0 | skew, then phase, turned the same way | the wave leans and the square pulses; the overlapped bands hollow |
| 25.0–25.7 | page press back to page 1 | — |
| 25.7–27.2 | rest | the last release, then silence; the screen is still |

## Watched at 1:1

- **Rest:** still, as required, with 0 mix rewrites after the first frame.
- **Each control:** visibly reshapes the bow while it turns and stops when it stops. Nothing alternates bright and dark faster than the notes, and the notes are at most 2.5 a second.
- **Page press:** in this preview it's a swap of the header's rows. On the device, `page_header.hpp` animates the press over 0.15 s, which this stand-in doesn't draw.
- **Still pending a device:** how it looks and redraws on the real screen. Someone needs to film the device.
