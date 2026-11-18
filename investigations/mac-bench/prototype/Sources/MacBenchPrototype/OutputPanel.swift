import SwiftUI

/// Right column: the selected item at actual size on a neutral stage, its description and checks,
/// and the strip of five underneath.
struct OutputPanel: View {
    @EnvironmentObject private var model: BenchModel
    @Environment(\.colorScheme) private var colorScheme

    var body: some View {
        VStack(spacing: 0) {
            stage
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            Divider()
            infoBar
            Divider()
            strip
        }
        .background(colorScheme == .dark ? Color(white: 0.1) : Color(white: 0.82))
    }

    // MARK: Stage

    private var stage: some View {
        currentFrame
            .lens(model.stage == .play ? model.lens : .vector)
            .overlay(Rectangle().strokeBorder(Color.white.opacity(0.08)))
            .accessibilityElement()
            .accessibilityLabel(stageLabel)
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .overlay(alignment: .bottomTrailing) {
                Text("Actual Size · 100%")
                    .font(.callout)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)
                    .background(.regularMaterial, in: Capsule())
                    .padding(12)
            }
    }

    private var currentFrame: FrameView {
        switch model.stage {
        case .concept: return conceptFrame(model.concept)
        case .frames: return variantFrame(model.variant)
        case .play: return FrameView(layers: model.playLayers(), header: model.header)
        }
    }

    private func conceptFrame(_ concept: Concept) -> FrameView {
        FrameView(layers: [Layer(path: concept.path, color: Grey.step(6), width: 3, fill: concept.fill)],
                  soft: true, word: concept.word)
    }

    private func variantFrame(_ variant: FrameVariant) -> FrameView {
        FrameView(layers: [Layer(path: variant.path, width: variant.lineWidth, dash: variant.dash)])
    }

    private var stageLabel: String {
        switch model.stage {
        case .concept: return "Generated concept \(model.concept.id): \(model.concept.title), at 480 by 220 with the stock header"
        case .frames: return "Drawn frame \(model.variant.id): \(model.variant.title), at 480 by 220 with the stock header"
        case .play: return "The picked frame: five arcs that open as depth rises, under the stock header"
        }
    }

    // MARK: Info

    private var infoBar: some View {
        VStack(alignment: .leading, spacing: 8) {
            (Text(infoTitle + ". ").bold() + Text(infoSentence))
                .frame(maxWidth: .infinity, alignment: .leading)
            HStack(spacing: 6) {
                ForEach(infoChecks) { check in
                    CheckChip(check: check)
                }
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
        .background(Color(nsColor: .windowBackgroundColor))
    }

    private var infoTitle: String {
        switch model.stage {
        case .concept: return model.concept.title
        case .frames: return model.variant.title
        case .play: return "Even fan"
        }
    }

    private var infoSentence: String {
        switch model.stage {
        case .concept: return model.concept.direction
        case .frames: return model.variant.story
        case .play: return model.lens.note
        }
    }

    private var infoChecks: [Check] {
        switch model.stage {
        case .concept: return model.concept.checks
        case .frames: return model.variant.checks
        case .play:
            return [Check(state: .pass, text: "lint, every keyframe"), Check(state: .pass, text: "body black, 40 % floor"),
                    Check(state: .wait, text: "photo of the real screen")]
        }
    }

    // MARK: Strip

    private var strip: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .firstTextBaseline, spacing: 6) {
                Text(stripTitle).font(.headline)
                Text(stripCount).font(.caption).foregroundStyle(.secondary)
            }
            .padding(.horizontal, 16)
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(alignment: .top, spacing: 8) {
                    switch model.stage {
                    case .concept:
                        ForEach(Array(model.concepts.enumerated()), id: \.element.id) { index, concept in
                            thumbnail(conceptFrame(concept), isSelected: index == model.conceptIndex,
                                      label: "Concept \(concept.id): \(concept.title)") { model.conceptIndex = index }
                        }
                    case .frames:
                        ForEach(Array(model.variants.enumerated()), id: \.element.id) { index, variant in
                            VStack(alignment: .leading, spacing: 4) {
                                thumbnail(variantFrame(variant), isSelected: index == model.frameIndex,
                                          label: "Frame \(variant.id): \(variant.title), \(variant.caption)") { model.frameIndex = index }
                                Text(variant.caption).font(.caption).foregroundStyle(.secondary)
                            }
                        }
                    case .play:
                        ForEach(Array(BenchModel.keyframes.enumerated()), id: \.offset) { index, depth in
                            thumbnail(FrameView(layers: model.playLayers(depth: depth), header: model.header),
                                      isSelected: depth == model.values[1],
                                      label: "Depth keyframe \(index + 1) of 5") { model.values[1] = depth }
                        }
                    }
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 2)
            }
        }
        .padding(.vertical, 10)
        .background(Color(nsColor: .windowBackgroundColor))
    }

    private var stripTitle: String {
        switch model.stage {
        case .concept: return "Concepts"
        case .frames: return "Frames"
        case .play: return "Keyframes"
        }
    }

    private var stripCount: String { model.stage == .play ? "5 · depth" : "5" }

    private func thumbnail(_ frame: FrameView, isSelected: Bool, label: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            FrameThumbnail(content: frame, isSelected: isSelected)
        }
        .buttonStyle(.plain)
        .accessibilityLabel(label)
        .accessibilityAddTraits(isSelected ? .isSelected : [])
    }
}

/// A check result. The word carries the state; the fill only reinforces it.
private struct CheckChip: View {
    var check: Check

    var body: some View {
        Text("\(check.state.rawValue) · \(check.text)")
            .font(.caption)
            .foregroundStyle(check.state == .fail ? Color.black : (check.state == .wait ? Color.secondary : Color.primary))
            .padding(.horizontal, 7)
            .padding(.vertical, 2)
            .background(fillColor, in: RoundedRectangle(cornerRadius: 5))
            .overlay(RoundedRectangle(cornerRadius: 5).strokeBorder(borderColor))
    }

    private var fillColor: Color {
        switch check.state {
        case .pass: return Color.primary.opacity(0.1)
        case .fail: return Color.orange
        case .warn, .wait: return Color.clear
        }
    }

    private var borderColor: Color {
        switch check.state {
        case .warn: return Color.primary
        case .wait: return Color.secondary.opacity(0.5)
        case .pass, .fail: return Color.clear
        }
    }
}

private extension View {
    /// The bench's lenses, approximated with stock effects for the prototype.
    @ViewBuilder
    func lens(_ lens: Lens) -> some View {
        switch lens {
        case .vector, .device: self
        case .armsLength: self.blur(radius: 1.4)
        case .valueMap: self.contrast(9).brightness(-0.25)
        }
    }
}
