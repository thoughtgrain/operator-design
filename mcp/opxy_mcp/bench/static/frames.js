// One 480 × 220 frame on the page, drawn one of three ways, never scaled:
//   vector  the browser draws the SVG (on a high-DPI screen that's sharper than the panel can be)
//   device  rasterised to exactly 480 × 220 and shown pixel for pixel (image-rendering: pixelated)
//   arm     downsampled 4× and softened: what's left is what reads from arm's length
// plus a value map (only the brightest grey kept) and a meter: body black against craft.md's 40 % floor.
// Sources load latest-wins, so a knob turned fast never shows an old frame after a newer one.

export const W = 480, H = 220;
const BLACK_FLOOR = 40;   // craft.md, Composition: at least 40 % of the body stays black
const BLACK_LUMA = 10;    // below this a pixel counts as black ground
const BRIGHT_LUMA = 190;  // #CDCDCD is 205, #AFAFAF is 175: the brightest grey class sits above this

const luma = (d, i) => 0.2126 * d[i] + 0.7152 * d[i + 1] + 0.0722 * d[i + 2];

function measure(data, top) {
  const d = data.data;
  let black = 0, body = 0, bright = 0;
  for (let y = top; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const l = luma(d, (y * W + x) * 4);
      body++;
      if (l < BLACK_LUMA) black++;
      if (l >= BRIGHT_LUMA) bright++;
    }
  }
  return { blackPct: (100 * black) / body, brightPx: bright };
}

export class FrameView {
  constructor({ alt = "", headerBottom = 20, meter = true } = {}) {
    this.el = document.createElement("div");
    this.el.className = "frame";
    this.img = new Image(W, H);
    this.img.alt = alt;
    this.img.decoding = "async";
    this.canvas = document.createElement("canvas");
    this.canvas.width = W;
    this.canvas.height = H;
    this.canvas.setAttribute("role", "img");
    this.canvas.setAttribute("aria-label", alt);
    this.canvas.hidden = true;
    this.busy = Object.assign(document.createElement("span"), { className: "busy" });
    this.busy.setAttribute("aria-hidden", "true");
    this.el.append(this.img, this.canvas, this.busy);
    this.meter = meter ? Object.assign(document.createElement("p"), { className: "meter" }) : null;
    this.top = headerBottom;
    this.mode = "vector";
    this.valueMap = false;
    this.src = null;
    this.loaded = null;   // the Image that last finished loading
    this.seq = 0;
  }

  setAlt(alt) {
    this.img.alt = alt;
    this.canvas.setAttribute("aria-label", alt);
  }

  missing(text) {
    this.src = null;
    this.loaded = null;
    this.img.hidden = true;
    this.canvas.hidden = true;
    let m = this.el.querySelector(".missing");
    if (!m) {
      m = Object.assign(document.createElement("div"), { className: "missing" });
      this.el.append(m);
    }
    m.textContent = text;
    if (this.meter) this.meter.textContent = "";
  }

  // Resolves true when this source is the one on screen, false when a newer one replaced it first.
  async setSource(src) {
    if (!src) {
      this.missing("not drawn yet");
      return true;
    }
    if (src === this.src && this.loaded) return true;
    const seq = ++this.seq;
    this.src = src;
    this.el.dataset.busy = "1";
    const next = new Image(W, H);
    next.src = src;
    try {
      await next.decode();
    } catch {
      if (seq === this.seq) {
        this.el.dataset.busy = "0";
        this.missing("couldn't draw this frame");
      }
      return false;
    }
    if (seq !== this.seq) return false;
    this.el.dataset.busy = "0";
    this.el.querySelector(".missing")?.remove();
    this.loaded = next;
    this.img.src = src;
    this.draw();
    return true;
  }

  setLens(mode, valueMap) {
    this.mode = mode;
    this.valueMap = valueMap;
    if (this.loaded) this.draw();
  }

  draw() {
    const img = this.loaded;
    if (!img) return;
    const ctx = this.canvas.getContext("2d", { willReadFrequently: true });
    ctx.imageSmoothingEnabled = true;
    ctx.filter = "none";
    ctx.fillStyle = "#000";
    ctx.fillRect(0, 0, W, H);
    ctx.drawImage(img, 0, 0, W, H);
    const raw = ctx.getImageData(0, 0, W, H);
    if (this.meter) this.writeMeter(measure(raw, this.top));

    const raster = this.mode !== "vector" || this.valueMap;
    this.img.hidden = raster;
    this.canvas.hidden = !raster;
    if (!raster) return;

    if (this.mode === "arm") {
      const small = document.createElement("canvas");
      small.width = W / 4;
      small.height = Math.round(H / 4);
      const s = small.getContext("2d");
      s.imageSmoothingQuality = "high";
      s.drawImage(this.canvas, 0, 0, small.width, small.height);
      ctx.fillRect(0, 0, W, H);
      ctx.filter = "blur(0.7px)";
      ctx.drawImage(small, 0, 0, W, H);
      ctx.filter = "none";
    }
    if (this.valueMap) {
      const data = ctx.getImageData(0, 0, W, H);
      const d = data.data;
      for (let i = 0; i < d.length; i += 4) {
        const l = luma(d, i);
        const v = l >= BRIGHT_LUMA ? 255 : l * 0.16;
        d[i] = d[i + 1] = d[i + 2] = v;
      }
      ctx.putImageData(data, 0, 0);
    }
  }

  writeMeter({ blackPct, brightPx }) {
    const under = blackPct < BLACK_FLOOR;
    this.meter.innerHTML = "";
    const black = document.createElement("span");
    black.innerHTML = `body black <b>${blackPct.toFixed(0)} %</b>`;
    if (under) {
      black.className = "under";
      black.title = `Under the ${BLACK_FLOOR} % floor in craft.md (Composition)`;
    }
    const bright = document.createElement("span");
    bright.innerHTML = `brightest grey <b>${brightPx} px</b>`;
    bright.title = "Pixels in the brightest grey class (#CDCDCD). Turn on the value map to see where they are.";
    this.meter.append(black, bright);
  }
}
