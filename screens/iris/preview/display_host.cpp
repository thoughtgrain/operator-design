// Runs iris's real display() (operators-xy machines/iris/display.cpp) over a score and dumps every frame's nodes.
// Built against host_sdk/, a host stand-in for the SDK's draw API (not the SDK), so the preview shows what the
// device code places. stdin: "frames N", N lines "s0 s1 s2 s3 s4 s5 held shift" (controls 0..1 in definition order: the page,
// then the Shift row; held and shift 0/1), 30 fps.
// stdout: one line per frame: 140 nodes "x y scale paint cos sin shown", then the 4 outlines' 64 points.
#include "display.cpp"
#include <cstdio>
int main()
{
    long nf; if (std::scanf(" frames %ld", &nf) != 1) return 1;
    static iris::DisplayState st; static iris::Frame fr; iris::display_reset(st);
    Input in = {}; in.elapsed = 34;                                   /* 1/30 s, Q10 */
    for (long f = 0; f < nf; f++) {
        double v[6]; int held, shift;
        for (int k = 0; k < 6; k++) if (std::scanf("%lf", &v[k]) != 1) return 1;
        if (std::scanf("%d %d", &held, &shift) != 2) return 1;
        for (int k = 0; k < 6; k++) { const int q = v[k] >= 1 ? 2147483647 : (int)(v[k] * 2147483647.0); if (k < 4) in.slots[k] = q; else in.shift_values[k - 4] = q; }
        in.shift_held = shift;
        in.held_notes = held; if (held) in.note_serial++;
        iris::display(st, in, fr);
        for (int n = 0; n < 140; n++) { auto& d = fr.nodes[n]; std::printf("%d %d %d %u %d %d %d ", d.x, d.y, d.scale, d.paint, d.turn.c, d.turn.s, d.shown ? 1 : 0); }
        for (int q = 0; q < 4; q++) for (int k = 0; k < 64; k++) std::printf("%d %d ", fr.paths[q].points[k].x, fr.paths[q].points[k].y);
        std::printf("%u\n", fr.paths[0].key);
    }
    return 0;
}
