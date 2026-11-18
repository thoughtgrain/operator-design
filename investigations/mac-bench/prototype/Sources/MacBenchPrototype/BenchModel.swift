import SwiftUI

enum Stage: String, CaseIterable, Identifiable {
    case concept = "Concept"
    case frames = "Frames"
    case play = "Play"
    var id: String { rawValue }
}

enum Lens: String, CaseIterable, Identifiable {
    case vector = "Vector"
    case device = "Device"
    case armsLength = "Arm’s Length"
    case valueMap = "Value Map"
    var id: String { rawValue }

    var note: String {
        switch self {
        case .vector: return "The drawing as the Mac renders it, at 480 × 220."
        case .device: return "Rasterised and shown pixel for pixel."
        case .armsLength: return "Softened, as it reads from where you play."
        case .valueMap: return "Only the brightest grey survives."
        }
    }
}

struct Check: Identifiable {
    enum State: String { case pass, warn, fail, wait }
    let id = UUID()
    var state: State
    var text: String
}

/// One of the five generated pictures. Everything here is an invented stand-in drawn by code.
struct Concept: Identifiable {
    let id: Int
    var title: String
    var direction: String
    var path: Path
    var fill: Color? = nil
    var word: String? = nil
    var checks: [Check]
}

/// One of the five drawn frames, with how its trip through the pipeline went.
struct FrameVariant: Identifiable {
    let id: Int
    var title: String
    var caption: String
    var story: String
    var ready: Bool
    var path: Path
    var lineWidth: CGFloat = 1.5
    var dash: [CGFloat] = []
    var checks: [Check]
}

final class BenchModel: ObservableObject {
    @Published var stage: Stage = .concept
    @Published var conceptIndex = 0
    @Published var frameIndex = 0

    // Play: every control 0...1, snapped to the five drawn keyframes.
    @Published var values: [Double] = [0.5, 0.5, 0.25, 0.5]
    @Published var shiftValues: [Double] = [0.25, 0.75, 0.5, 0]
    @Published var holdsNote = false
    @Published var holdsShift = false
    @Published var lens: Lens = .vector

    @Published var subject = "[SUBJECT SENTENCE FROM THE BRIEF]"

    let concepts: [Concept] = [
        Concept(id: 1, title: "Opening arcs", direction: "The sound as a fan that opens. Depth sets how far.",
                path: Art.arcs(open: 0.5),
                checks: [.init(state: .pass, text: "body black"), .init(state: .pass, text: "greys"),
                         .init(state: .pass, text: "no lettering"), .init(state: .pass, text: "contours in budget")]),
        Concept(id: 2, title: "Receding lines", direction: "Distance as stacked horizons. Rate spreads them.",
                path: Art.horizon(),
                checks: [.init(state: .pass, text: "body black"), .init(state: .pass, text: "greys"),
                         .init(state: .pass, text: "no lettering"), .init(state: .warn, text: "contours near the limit")]),
        Concept(id: 3, title: "Ring of ticks", direction: "One ring whose teeth follow the tone.",
                path: Art.ticks(),
                checks: [.init(state: .pass, text: "body black"), .init(state: .pass, text: "greys"),
                         .init(state: .pass, text: "no lettering"), .init(state: .pass, text: "contours in budget")]),
        Concept(id: 4, title: "Stepped rise", direction: "A staircase that grows with the mix.",
                path: Art.terraces(), fill: Grey.step(2),
                checks: [.init(state: .pass, text: "body black"), .init(state: .warn, text: "flat fill, will be hatched"),
                         .init(state: .pass, text: "no lettering"), .init(state: .pass, text: "contours in budget")]),
        Concept(id: 5, title: "Four ribbons", direction: "Layered waves, one per control.",
                path: Art.wave(), word: "WAVE",
                checks: [.init(state: .pass, text: "body black"), .init(state: .pass, text: "greys"),
                         .init(state: .fail, text: "lettering found, cannot translate"), .init(state: .pass, text: "contours in budget")]),
    ]

    let variants: [FrameVariant] = [
        FrameVariant(id: 1, title: "Even fan", caption: "Ready", story: "Drawn on the first try.", ready: true,
                     path: Art.arcs(open: 0.5),
                     checks: [.init(state: .pass, text: "lint"), .init(state: .pass, text: "matches the concept"),
                              .init(state: .pass, text: "no second look needed")]),
        FrameVariant(id: 2, title: "Wide open", caption: "Ready",
                     story: "Sent back once: the arcs had closed into rings. Reopened on the right.", ready: true,
                     path: Art.arcs(open: 1),
                     checks: [.init(state: .pass, text: "lint"), .init(state: .warn, text: "match was borderline"),
                              .init(state: .pass, text: "second look, one round")]),
        FrameVariant(id: 3, title: "Dense fan", caption: "Needs you",
                     story: "Still over budget after two rounds, so it stopped. Edit it, or leave it out of the pick.", ready: false,
                     path: Art.arcs(open: 0.5, step: 10), lineWidth: 1,
                     checks: [.init(state: .fail, text: "lint: over node budget"), .init(state: .wait, text: "match not run"),
                              .init(state: .wait, text: "second look not run")]),
        FrameVariant(id: 4, title: "Narrow fan", caption: "Ready",
                     story: "Narrower than the concept and dashed. It passes, and the difference is yours to judge.", ready: true,
                     path: Art.arcs(open: 0.05, wide: 0.8), dash: [3, 5],
                     checks: [.init(state: .pass, text: "lint"), .init(state: .warn, text: "drifted from the concept"),
                              .init(state: .pass, text: "second look, two rounds")]),
        FrameVariant(id: 5, title: "Fifth direction", caption: "Drawing…",
                     story: "The header is already in place. The body arrives when the model finishes.", ready: false,
                     path: Path(),
                     checks: [.init(state: .wait, text: "lint"), .init(state: .wait, text: "match"),
                              .init(state: .wait, text: "second look")]),
    ]

    var concept: Concept { concepts[conceptIndex] }
    var variant: FrameVariant { variants[frameIndex] }

    // MARK: Play

    static let keyframes: [Double] = [0, 0.25, 0.5, 0.75, 1]
    private static let tones = ["lp", "lp", "bp", "hp", "hp"]

    private func keyframeIndex(_ value: Double) -> Int { Int((value * 4).rounded()) }

    var controlTitles: [String] {
        holdsShift ? ["shape", "drift", "fold", "bias"] : ["rate", "depth", "tone", "mix"]
    }

    var controlValues: [String] {
        if holdsShift { return shiftValues.map { String(Int(($0 * 100).rounded())) } }
        return [
            String(format: "%.2f", values[0]),
            String(Int((values[1] * 24).rounded())),
            Self.tones[keyframeIndex(values[2])],
            String(Int((values[3] * 100).rounded())),
        ]
    }

    /// Shift swaps what the four header slots show; it never adds a row.
    var header: [HeaderSlot] {
        zip(controlTitles, controlValues).map { HeaderSlot(title: $0, value: $1) }
    }

    func playLayers(depth: Double? = nil) -> [Layer] {
        let depth = depth ?? values[1]
        let wide = 0.95 + values[0] * 0.6
        let width = 1 + Double(keyframeIndex(values[2])) * 0.5
        var inner = Path()
        for radius in [36.0, 60, 84, 108] { Art.addArc(to: &inner, radius: radius, open: depth, wide: wide) }
        var outer = Path()
        Art.addArc(to: &outer, radius: 132 + depth * 24, open: depth, wide: wide)
        return [
            Layer(path: inner, color: Grey.step(2 + keyframeIndex(values[3])), width: width),
            Layer(path: outer, color: holdsNote ? Grey.step(7) : Grey.step(5), width: width),
        ]
    }
}
