import SwiftUI

/// The stock header greys from opxy/constraints.md, darkest to lightest.
enum Grey {
    private static let values: [Double] = [0x00, 0x32, 0x4B, 0x64, 0x7D, 0x96, 0xAF, 0xCD]
    static func step(_ index: Int) -> Color {
        Color(white: values[min(max(index, 0), values.count - 1)] / 255)
    }
    static let headerText = Color(white: 0xCB / 255)
}

struct HeaderSlot {
    var title: String
    var value: String

    static let sample = [
        HeaderSlot(title: "rate", value: "0.5"), HeaderSlot(title: "depth", value: "12"),
        HeaderSlot(title: "tone", value: "lp"), HeaderSlot(title: "mix", value: "40"),
    ]
}

struct Layer {
    var path: Path
    var color: Color = Grey.step(7)
    var width: CGFloat = 1.5
    var dash: [CGFloat] = []
    var fill: Color? = nil
}

/// One 480 × 220 frame: a body drawn from layers, and the stock header stamped on top.
/// The header is never part of the drawing; the app composes it from the machine's definition.
struct FrameView: View {
    var layers: [Layer]
    var header: [HeaderSlot] = HeaderSlot.sample
    /// A generated concept is a soft picture, not a drawing: blur the body, never the header.
    var soft = false
    var word: String? = nil

    var body: some View {
        ZStack(alignment: .topLeading) {
            Color.black
            Canvas { context, _ in
                for layer in layers {
                    if let fill = layer.fill { context.fill(layer.path, with: .color(fill)) }
                    context.stroke(layer.path, with: .color(layer.color),
                                   style: StrokeStyle(lineWidth: layer.width, dash: layer.dash))
                }
                if let word {
                    context.draw(Text(word).font(.system(size: 30, weight: .semibold)).foregroundColor(Grey.step(7)),
                                 at: CGPoint(x: 240, y: 64))
                }
            }
            .blur(radius: soft ? 1.1 : 0)
            Canvas { context, _ in
                for index in 0..<8 {
                    context.fill(Path(CGRect(x: CGFloat(index) * 60, y: 0, width: 60, height: 20)),
                                 with: .color(Grey.step(index)))
                }
                for (index, slot) in header.prefix(4).enumerated() {
                    let ink = index < 2 ? Grey.headerText : Color.black
                    let x = CGFloat(index) * 120
                    context.draw(Text(slot.title).font(.system(size: 10, weight: .light)).foregroundColor(ink),
                                 at: CGPoint(x: x + 5, y: 13), anchor: .bottomLeading)
                    context.draw(Text(slot.value).font(.system(size: 20, weight: .light)).foregroundColor(ink),
                                 at: CGPoint(x: x + 65, y: 22), anchor: .bottomLeading)
                }
            }
        }
        .frame(width: 480, height: 220)
        .clipped()
    }
}

/// A frame at 30 % for the strip. Thumbnails are for finding a frame, never for judging one.
struct FrameThumbnail: View {
    var content: FrameView
    var isSelected: Bool

    var body: some View {
        content
            .scaleEffect(0.3, anchor: .topLeading)
            .frame(width: 144, height: 66, alignment: .topLeading)
            .clipShape(RoundedRectangle(cornerRadius: 6))
            .overlay(RoundedRectangle(cornerRadius: 6).strokeBorder(isSelected ? Color.primary : Color.clear, lineWidth: 2))
    }
}

/// Stand-in artwork, drawn by code. None of it is a real machine's screen.
enum Art {
    static func addArc(to path: inout Path, radius: Double, open: Double, wide: Double) {
        for step in 0...24 {
            let angle = Double.pi * (1 - (Double(step) / 24) * (0.55 + 0.45 * open))
            let point = CGPoint(x: 240 + radius * wide * cos(angle), y: 208 - radius * sin(angle))
            if step == 0 { path.move(to: point) } else { path.addLine(to: point) }
        }
    }

    static func arcs(open: Double, step: Double = 24, wide: Double = 1.25) -> Path {
        var path = Path()
        var radius = 36.0
        while radius <= 156 {
            addArc(to: &path, radius: radius, open: open, wide: wide)
            radius += step
        }
        return path
    }

    static func horizon() -> Path {
        var path = Path()
        for index in 0..<9 {
            let y = 96 + Double(index * index) * 1.45
            let half = 60 + Double(index) * 22 * 0.8
            path.move(to: CGPoint(x: 240 - half, y: y))
            path.addLine(to: CGPoint(x: 240 + half, y: y))
        }
        return path
    }

    static func ticks() -> Path {
        var path = Path()
        for index in 0..<36 {
            let angle = Double(index) / 36 * Double.pi * 2
            let outer = 58 + 26 * (0.5 + 0.5 * sin(angle * 3 + 3))
            path.move(to: CGPoint(x: 240 + 57 * cos(angle), y: 126 + 44 * sin(angle)))
            path.addLine(to: CGPoint(x: 240 + outer * 1.3 * cos(angle), y: 126 + outer * sin(angle)))
        }
        return path
    }

    static func terraces() -> Path {
        var path = Path()
        var y = 200.0
        path.move(to: CGPoint(x: 70, y: y))
        for index in 0...10 {
            let x = 70 + Double(index) * 34
            path.addLine(to: CGPoint(x: x, y: y))
            y = max(50, y - (6 + Double(index % 3) * 8 * 0.9))
            path.addLine(to: CGPoint(x: x, y: y))
        }
        path.addLine(to: CGPoint(x: 410, y: 200))
        path.closeSubpath()
        return path
    }

    static func wave() -> Path {
        var path = Path()
        for row in 0..<4 {
            var x = 40.0
            var isFirst = true
            while x <= 440 {
                let y = 110 + Double(row) * 22 + sin(x / (26 + Double(row) * 6) + 2.5) * 13
                let point = CGPoint(x: x, y: y)
                if isFirst { path.move(to: point); isFirst = false } else { path.addLine(to: point) }
                x += 8
            }
        }
        return path
    }
}
