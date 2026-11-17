//! opxy-raster: an OP-XY frame (SVG) to PNG, the same way on every machine.
//!
//! The command line is the subset of rsvg-convert that opxy's Python tools already call, so it drops in
//! wherever they look for a renderer:
//!
//!     opxy-raster -w 480 -h 220 -b black -o frame.png frame.svg
//!
//! Why it exists: rsvg-convert is a system package (librsvg) that isn't always there, and without a renderer
//! the pass uniqueness check, perceptibility and render_frame can't run. resvg is pure Rust, needs no system
//! libraries, and draws the same pixels on macOS, Linux and Windows, so golden-image tests can pin it.
//!
//! With --luma it writes brightness instead of a PNG: a binary PGM (P5) of 0..255 per pixel, computed exactly as
//! opxy/tools/perceptibility.py's PNG decoder does (Rec. 709 weights in integers, alpha over black). The checks
//! then read the pixels in one slice instead of decoding a PNG in pure Python, which was most of their time.
//!
//!     opxy-raster --luma -w 480 -h 220 -b black -o frame.pgm frame.svg
//!
//! Exit codes: 0 ok, 1 the SVG couldn't be read or drawn, 2 usage.

use std::path::PathBuf;
use std::process::ExitCode;

use resvg::{tiny_skia, usvg};

const USAGE: &str = "usage: opxy-raster [-w WIDTH] [-h HEIGHT] [-b COLOUR] -o OUT.png IN.svg\n\
                     \n\
                     -w, --width       output width in px (default: the SVG's own)\n\
                     -h, --height      output height in px (default: the SVG's own)\n\
                     -b, --background  black, white, none or #RRGGBB (default: none)\n\
                     -o, --output      PNG to write (PGM with --luma)\n\
                     --luma            write brightness 0..255 as binary PGM instead of a PNG\n\
                     -V, --version     print the version";

struct Args {
    width: Option<u32>,
    height: Option<u32>,
    background: Option<tiny_skia::Color>,
    luma: bool,
    output: PathBuf,
    input: PathBuf,
}

fn colour(s: &str) -> Result<Option<tiny_skia::Color>, String> {
    let rgb = |r, g, b| Ok(Some(tiny_skia::Color::from_rgba8(r, g, b, 255)));
    match s.to_ascii_lowercase().as_str() {
        "none" | "transparent" => Ok(None),
        "black" => rgb(0, 0, 0),
        "white" => rgb(255, 255, 255),
        hex if hex.len() == 7 && hex.starts_with('#') => {
            let n = u32::from_str_radix(&hex[1..], 16).map_err(|_| format!("not a colour: {s}"))?;
            rgb((n >> 16) as u8, (n >> 8) as u8, n as u8)
        }
        _ => Err(format!("background is black, white, none or #RRGGBB, not {s}")),
    }
}

fn parse(argv: &[String]) -> Result<Args, String> {
    let (mut width, mut height, mut background, mut output, mut input) = (None, None, None, None, None);
    let mut luma = false;
    let mut it = argv.iter();
    while let Some(a) = it.next() {
        let mut value = |name: &str| it.next().cloned().ok_or_else(|| format!("{name} needs a value"));
        match a.as_str() {
            "-w" | "--width" => width = Some(value(a)?.parse::<u32>().map_err(|_| "width is a whole number")?),
            "-h" | "--height" => height = Some(value(a)?.parse::<u32>().map_err(|_| "height is a whole number")?),
            "-b" | "--background" | "--background-color" => background = colour(&value(a)?)?,
            "-o" | "--output" => output = Some(PathBuf::from(value(a)?)),
            "--luma" => luma = true,
            s if s.starts_with('-') && s.len() > 1 => return Err(format!("unknown option {s}")),
            s => {
                if input.replace(PathBuf::from(s)).is_some() {
                    return Err("one input SVG at a time".into());
                }
            }
        }
    }
    if width == Some(0) || height == Some(0) {
        return Err("width and height must be above 0".into());
    }
    Ok(Args {
        width,
        height,
        background,
        luma,
        output: output.ok_or("-o OUT.png is required")?,
        input: input.ok_or("an input SVG is required")?,
    })
}

fn render(args: &Args) -> Result<(), String> {
    let data = std::fs::read(&args.input).map_err(|e| format!("can't read {}: {e}", args.input.display()))?;
    let mut opt = usvg::Options::default();
    opt.resources_dir = args.input.parent().map(|p| p.to_path_buf());
    // The device font (UniversNextPro-Light) is rarely installed, so header text falls back to a system face,
    // the same as rsvg-convert. Widths are approximate either way; the frames say so.
    opt.fontdb_mut().load_system_fonts();
    // usvg's last resort is the generic serif; the device face is a grotesk, so a missing face should land on
    // a sans like it does under rsvg-convert. Point both generics at the first sans that's installed.
    let db = opt.fontdb_mut();
    let sans = ["Helvetica Neue", "Helvetica", "Arial", "Liberation Sans", "DejaVu Sans", "FreeSans"]
        .into_iter()
        .find(|name| db.faces().any(|f| f.families.iter().any(|(n, _)| n == name)));
    if let Some(name) = sans {
        db.set_serif_family(name);
        db.set_sans_serif_family(name);
    }
    let tree = usvg::Tree::from_data(&data, &opt).map_err(|e| format!("{}: {e}", args.input.display()))?;

    let size = tree.size();
    let w = args.width.unwrap_or_else(|| size.width().ceil() as u32);
    let h = args.height.unwrap_or_else(|| size.height().ceil() as u32);
    let mut pixmap = tiny_skia::Pixmap::new(w, h).ok_or("output size is too large")?;
    if let Some(bg) = args.background {
        pixmap.fill(bg);
    }
    // Like rsvg-convert with both -w and -h: fit each axis. Frames are 480 x 220, so 1:1 and 2x keep the aspect.
    let transform = tiny_skia::Transform::from_scale(w as f32 / size.width(), h as f32 / size.height());
    resvg::render(&tree, transform, &mut pixmap.as_mut());
    if args.luma {
        let mut out = format!("P5\n{w} {h}\n255\n").into_bytes();
        out.extend(luma(&pixmap));
        return std::fs::write(&args.output, out).map_err(|e| format!("can't write {}: {e}", args.output.display()));
    }
    pixmap.save_png(&args.output).map_err(|e| format!("can't write {}: {e}", args.output.display()))
}

/// Brightness per pixel, byte for byte what perceptibility.decode_png makes of this pixmap saved as a PNG:
/// the PNG holds demultiplied RGBA, then v = (2126 r + 7152 g + 722 b) / 10000 and v * a / 255, both floored.
fn luma(pixmap: &tiny_skia::Pixmap) -> Vec<u8> {
    pixmap
        .pixels()
        .iter()
        .map(|p| {
            let c = p.demultiply();
            let v = (2126 * c.red() as u32 + 7152 * c.green() as u32 + 722 * c.blue() as u32) / 10000;
            (v * c.alpha() as u32 / 255) as u8
        })
        .collect()
}

fn main() -> ExitCode {
    let argv: Vec<String> = std::env::args().skip(1).collect();
    if argv.iter().any(|a| a == "-V" || a == "--version") {
        println!("opxy-raster {} (resvg)", env!("CARGO_PKG_VERSION"));
        return ExitCode::SUCCESS;
    }
    if argv.is_empty() || argv.iter().any(|a| a == "--help") {
        eprintln!("{USAGE}");
        return ExitCode::from(2);
    }
    let args = match parse(&argv) {
        Ok(a) => a,
        Err(e) => {
            eprintln!("opxy-raster: {e}\n\n{USAGE}");
            return ExitCode::from(2);
        }
    };
    match render(&args) {
        Ok(()) => ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("opxy-raster: {e}");
            ExitCode::from(1)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn argv(s: &str) -> Vec<String> {
        s.split_whitespace().map(String::from).collect()
    }

    #[test]
    fn parses_the_rsvg_subset() {
        let a = parse(&argv("-w 480 -h 220 -b black -o out.png in.svg")).unwrap();
        assert_eq!((a.width, a.height), (Some(480), Some(220)));
        assert!(a.background.is_some());
        assert_eq!(a.input, PathBuf::from("in.svg"));
    }

    #[test]
    fn rejects_what_it_cannot_do() {
        assert!(parse(&argv("-o out.png")).is_err());
        assert!(parse(&argv("in.svg")).is_err());
        assert!(parse(&argv("-w 0 -o o.png in.svg")).is_err());
        assert!(parse(&argv("-b red -o o.png in.svg")).is_err());
        assert!(parse(&argv("--zoom 2 -o o.png in.svg")).is_err());
    }

    #[test]
    fn luma_matches_the_python_formula() {
        let mut pm = tiny_skia::Pixmap::new(3, 1).unwrap();
        pm.pixels_mut()[0] = tiny_skia::ColorU8::from_rgba(0xCD, 0xCD, 0xCD, 255).premultiply();
        pm.pixels_mut()[1] = tiny_skia::ColorU8::from_rgba(10, 200, 30, 255).premultiply();
        pm.pixels_mut()[2] = tiny_skia::ColorU8::from_rgba(255, 255, 255, 128).premultiply();
        // (2126*205 + 7152*205 + 722*205) / 10000 = 205; (2126*10 + 7152*200 + 722*30) / 10000 = 147
        assert_eq!(luma(&pm), vec![205, 147, 128]);
        assert!(parse(&argv("--luma -o o.pgm in.svg")).unwrap().luma);
    }

    #[test]
    fn hex_background() {
        let c = colour("#323232").unwrap().unwrap();
        assert_eq!(c.to_color_u8().red(), 0x32);
    }
}
