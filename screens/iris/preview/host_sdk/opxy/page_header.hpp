#pragma once
// Host-only stand-in for the Open-XY SDK's draw API: just enough to run a machine's display() and dump what it
// placed. NOT the SDK; names follow how toro and theseus call it.
#include "audio.hpp"
#include <cmath>
#include <cstdio>
namespace opxy {
typedef unsigned char u8;
namespace draw {
const i32 unit = 1024;
const u32 header_capacity = 8;
enum Paint { fill_and_stroke = 0 };
struct Point { i32 x, y; };
struct Turn { i32 c, s; };
inline i32 sine(i32 tenths) { return (i32)lround(1024.0 * std::sin(tenths * M_PI / 1800.0)); }
inline Turn rotation(i32 tenths) { return Turn{ sine(tenths + 900), sine(tenths) }; }
inline i32 clamp(i32 v, i32 lo, i32 hi) { return v < lo ? lo : v > hi ? hi : v; }
struct Input { i32 slots[8]; i32 elapsed; u32 note_serial; u32 held_notes; u32 reduced_motion; u32 shift_held; i32 shift_values[8]; };
template <int P, int PTS, int N, int T, int PAL> struct Frame {
    enum { point_count = PTS };
    struct Path { Point points[PTS > 0 ? PTS : 1]; u32 key; } paths[P > 0 ? P : 1];
    struct Node { i32 x, y, scale; u32 paint; Turn turn; bool shown; } nodes[N];
};
template <class F> void place(F& f, u32 n, i32 x, i32 y, i32 s, u32 paint, Paint) { auto& d = f.nodes[n]; d.x = x; d.y = y; d.scale = s; d.paint = paint; d.shown = true; d.turn = Turn{ 1024, 0 }; }
template <class F> void turn(F& f, u32 n, Turn t) { f.nodes[n].turn = t; }
template <class F> void hide(F& f, u32 n) { f.nodes[n].shown = false; }
struct PageHeader { u32 a[5]; void reset() {} };
inline void header_amount(char* o, u32, i32 q) { int v = (int)((q < 0 ? 0 : q) / 21474836.47 + 0.5); snprintf(o, 8, "%d%%", v); }
template <class F> void page_header(PageHeader&, const Input&, F&, const char* const*, char (*)[header_capacity], u32, const u8 (*)[4]) {}
}
}
#include <cstdio>
using opxy::draw::Input;
