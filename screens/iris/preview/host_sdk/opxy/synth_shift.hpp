#pragma once
// Host-only stand-in for opxy/synth_shift.hpp (SDK 1.13): held, line, values. NOT the SDK.
#include "page_header.hpp"
namespace opxy { namespace draw {
struct ShiftRow { bool held; u32 line; i32 values[8]; };
inline ShiftRow shift_row(const Input& in) { ShiftRow r; r.held = in.shift_held != 0; r.line = 0; for (int i = 0; i < 8; ++i) r.values[i] = in.shift_values[i]; return r; }
} }
