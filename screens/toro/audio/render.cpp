// Renders toro's real engine (labyrinth opxy/machines/toro/engine.cpp) to raw mono float32 at 44.1 kHz.
// toro has no amplitude envelope of its own (the OP-XY's comes after), so this applies a plain one per note:
// 6 ms attack, full sustain, 280 ms release, which is roughly an OP-XY patch set to "organ".
// stdin:  "blocks N", N lines of 8 control values (0..1, header order), "notes M", M lines "start_block end_block hz".
// stdout: float32 samples.
#include "engine.cpp"
#include <cmath>
#include <cstdio>
#include <vector>

int main()
{
    long nb; if (std::scanf(" blocks %ld", &nb) != 1) return 1;
    std::vector<opxy::i32> params(nb * 8);
    for (long b = 0; b < nb; b++)
        for (int k = 0; k < 8; k++) { double x; if (std::scanf("%lf", &x) != 1) return 1; params[b * 8 + k] = static_cast<opxy::i32>(x * 2147483647.0); }
    long nn; if (std::scanf(" notes %ld", &nn) != 1) return 1;
    std::vector<long> b0(nn), b1(nn); std::vector<double> hz(nn);
    for (long i = 0; i < nn; i++) if (std::scanf("%ld %ld %lf", &b0[i], &b1[i], &hz[i]) != 3) return 1;
    const int V = 8;
    toro::Shared shared{};
    toro::Voice voice[V]{}; long note_of[V]; double level[V];
    for (int k = 0; k < V; k++) { toro::initialize(voice[k], shared, 1); note_of[k] = -1; level[k] = 0; }
    const double att = 1.0 / (0.006 * 44100), rel = std::exp(-1.0 / (0.28 * 44100 / 4.6));
    long next = 0;
    opxy::i32 out[64]; opxy::u32 pitch[64]; float mix[64];
    for (long b = 0; b < nb; b++) {
        while (next < nn && b0[next] <= b) {
            int pick = -1;
            for (int k = 0; k < V; k++) if (note_of[k] < 0) { pick = k; break; }
            if (pick < 0) { pick = 0; for (int k = 1; k < V; k++) if (level[k] < level[pick]) pick = k; }
            toro::start(voice[pick], shared, 1); note_of[pick] = next; level[pick] = 0; next++;
        }
        for (int n = 0; n < 64; n++) mix[n] = 0;
        for (int k = 0; k < V; k++) {
            if (note_of[k] < 0) continue;
            const long i = note_of[k];
            for (int n = 0; n < 64; n++) pitch[n] = static_cast<opxy::u32>(hz[i] / 44100.0 * 4294967296.0);
            toro::render(voice[k], shared, 1, out, &params[b * 8], pitch);
            const bool held = b < b1[i];
            for (int n = 0; n < 64; n++) {
                level[k] = held ? (level[k] + att > 1 ? 1 : level[k] + att) : level[k] * rel;
                mix[n] += static_cast<float>(out[n] / 2147483648.0 * level[k]);
            }
            if (!held && level[k] < 1e-4) note_of[k] = -1;
        }
        std::fwrite(mix, sizeof(float), 64, stdout);
    }
    return 0;
}
