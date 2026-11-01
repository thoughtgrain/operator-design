// Renders theseus's real engine (labyrinth opxy/machines/theseus/engine.cpp) to raw mono float32 at 44.1 kHz,
// one voice per hit, for the d4 tower video's soundtrack.
// stdin:  "blocks N" then N lines of 8 control values (0..1, header order), then "hits M" and M lines "block hz".
// stdout: float32 samples. Build: g++ -O2 -std=c++17 -I<open-xy>/sdk/include -I<theseus> render.cpp
#include "engine.cpp"
#include <cstdio>
#include <vector>

int main()
{
    long nb; if (std::scanf(" blocks %ld", &nb) != 1) return 1;
    std::vector<opxy::i32> params(nb * 8);
    for (long b = 0; b < nb; b++)
        for (int k = 0; k < 8; k++) { double x; std::scanf("%lf", &x); params[b * 8 + k] = static_cast<opxy::i32>(x * 2147483647.0); }
    long nh; std::scanf(" hits %ld", &nh);
    std::vector<long> hb(nh); std::vector<double> hz(nh);
    for (long i = 0; i < nh; i++) std::scanf("%ld %lf", &hb[i], &hz[i]);
    const int V = 8;                                     // voices, oldest stolen first
    theseus::Shared shared{};
    theseus::Voice voice[V]{}; double vhz[V] = {0}; long vstart[V]; bool on[V] = {false};
    for (int k = 0; k < V; k++) { theseus::initialize(voice[k], shared, 1); vstart[k] = -1; }
    long next = 0;
    opxy::i32 out[64]; opxy::u32 pitch[64]; float mix[64];
    for (long b = 0; b < nb; b++) {
        while (next < nh && hb[next] <= b) {
            int pick = 0;
            for (int k = 1; k < V; k++) if (!on[k] || (on[pick] && vstart[k] < vstart[pick])) { if (!on[k]) { pick = k; break; } pick = k; }
            for (int k = 0; k < V; k++) if (!on[k]) { pick = k; break; }
            theseus::start(voice[pick], shared, 1); vhz[pick] = hz[next]; vstart[pick] = b; on[pick] = true; next++;
        }
        for (int n = 0; n < 64; n++) mix[n] = 0;
        for (int k = 0; k < V; k++) {
            if (!on[k]) continue;
            for (int n = 0; n < 64; n++) pitch[n] = static_cast<opxy::u32>(vhz[k] / 44100.0 * 4294967296.0);
            theseus::render(voice[k], shared, 1, out, &params[b * 8], pitch);
            for (int n = 0; n < 64; n++) mix[n] += out[n] / 2147483648.0f;
            if (b - vstart[k] > 44100 * 3 / 64) on[k] = false;   // a hit is done after 3 s
        }
        std::fwrite(mix, sizeof(float), 64, stdout);
    }
    return 0;
}
