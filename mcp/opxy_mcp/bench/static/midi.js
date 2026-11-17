// Web MIDI in, nothing out. Chrome and Edge have it (on 127.0.0.1 it counts as a secure context); Safari and
// Firefox without the add-on don't, and the bench says so instead of failing quietly.
//
// Events: "cc" {channel, cc, value, input}, "noteon" {channel, note, velocity}, "noteoff" {channel, note},
//         "panic" (all notes off / all sound off), "ports" {names}.

export class Midi extends EventTarget {
  constructor() {
    super();
    this.access = null;
  }

  get supported() {
    return typeof navigator.requestMIDIAccess === "function";
  }

  get names() {
    return this.access ? [...this.access.inputs.values()].map((i) => i.name || "MIDI input") : [];
  }

  async connect() {
    if (!this.supported) throw new Error("This browser has no Web MIDI. Chrome or Edge do; the on-screen knobs work everywhere.");
    if (!this.access) {
      this.access = await navigator.requestMIDIAccess({ sysex: false });
      this.access.addEventListener("statechange", () => this.hook());
    }
    this.hook();
    return this.names;
  }

  hook() {
    for (const input of this.access.inputs.values()) {
      input.onmidimessage = (e) => this.receive(e.data, input.name);
    }
    this.emit("ports", { names: this.names });
  }

  emit(type, detail) {
    this.dispatchEvent(new CustomEvent(type, { detail }));
  }

  receive(data, input) {
    if (!data || data.length < 2) return;
    const [status, a, b = 0] = data;
    const kind = status & 0xf0;
    const channel = (status & 0x0f) + 1;
    if (kind === 0xb0) {
      if (a === 120 || a === 123) return this.emit("panic", { channel });
      return this.emit("cc", { channel, cc: a, value: b, input });
    }
    if (kind === 0x90 && b > 0) return this.emit("noteon", { channel, note: a, velocity: b });
    if (kind === 0x80 || kind === 0x90) return this.emit("noteoff", { channel, note: a });
  }
}

// A relative encoder sends steps, not positions: 1..63 up, 65..127 down (two's complement, the common form).
export function relativeStep(value) {
  if (value === 0 || value === 64) return 0;
  return value < 64 ? value : value - 128;
}
