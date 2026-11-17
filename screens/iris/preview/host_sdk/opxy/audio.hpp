#pragma once
// Host-only stand-in for the Open-XY SDK's audio types, enough to compile an engine's tests here. NOT the SDK.
namespace opxy {
typedef int i32; typedef unsigned u32; typedef long long i64;
const unsigned block_frames = 64;
typedef i32* Output; typedef const i32* Parameters; typedef const u32* Pitch;
}
