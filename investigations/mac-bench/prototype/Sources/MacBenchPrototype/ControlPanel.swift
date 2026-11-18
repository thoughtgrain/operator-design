import SwiftUI

/// Left column: the settings for the current stage in a grouped form, and the engine with the
/// stage's main action pinned to the bottom.
struct ControlPanel: View {
    @EnvironmentObject private var model: BenchModel
    @State private var imageModel = "sensenova"
    @State private var drawingModel = "local"
    @State private var wantsClip = false

    var body: some View {
        Form {
            switch model.stage {
            case .concept: conceptSections
            case .frames: frameSections
            case .play: playSections
            }
        }
        .formStyle(.grouped)
        .safeAreaInset(edge: .bottom, spacing: 0) {
            VStack(spacing: 0) {
                Divider()
                footer
                    .padding(14)
            }
            .background(.bar)
        }
    }

    // MARK: Concept

    @ViewBuilder
    private var conceptSections: some View {
        Section {
            TextField("Subject", text: $model.subject, axis: .vertical)
                .lineLimit(3...6)
            LabeledContent("Added by the app") {
                Text("Grey on black. Line and hatching, no flat fills. No lettering or numbers. One subject, below the header band.")
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.trailing)
            }
        } header: {
            Text("Brief")
        } footer: {
            Text("The blocks are joined, in order, into one prompt.")
        }

        Section("Machine") {
            LabeledContent("Folder", value: "screens/sample-machine")
            LabeledContent("Header", value: "4 controls, from the definition")
            Toggle("Concept clip", isOn: $wantsClip)
        }
    }

    // MARK: Frames

    @ViewBuilder
    private var frameSections: some View {
        Section {
            FrameThumbnail(content: FrameView(layers: [Layer(path: Art.arcs(open: 0.5), color: Grey.step(6), width: 3)], soft: true),
                           isSelected: false)
                .accessibilityLabel("The approved concept: opening arcs")
            LabeledContent("Subject", value: "Five arcs fanning open from the bottom centre.")
            LabeledContent("Brightest", value: "The outermost arc.")
            LabeledContent("Keep", value: "Even spacing, the opening on the right.")
            LabeledContent("Drop", value: "The soft glow around each line.")
        } header: {
            Text("Approved Concept")
        } footer: {
            Text("Read once by the vision model. Positions come from the tracer.")
        }

        Section {
            LabeledContent("Trace the concept", value: "Arithmetic")
            LabeledContent("Interpret it", value: "Vision model")
            LabeledContent("Draw the body", value: "Code model")
            LabeledContent("Lint", value: "Arithmetic")
            LabeledContent("Compare with the concept", value: "Arithmetic")
            LabeledContent("Look again, if borderline", value: "Vision model")
        } header: {
            Text("Steps")
        } footer: {
            Text("Cheapest check first. A frame goes back to the model twice at most, then stops and asks you.")
        }
    }

    // MARK: Play

    @ViewBuilder
    private var playSections: some View {
        Section {
            ForEach(0..<4, id: \.self) { index in
                LabeledContent {
                    HStack(spacing: 10) {
                        Slider(value: binding(for: index), in: 0...1, step: 0.25)
                            .accessibilityLabel(model.controlTitles[index])
                        Text(model.controlValues[index])
                            .monospacedDigit()
                            .foregroundStyle(.secondary)
                            .frame(width: 40, alignment: .trailing)
                    }
                } label: {
                    Label {
                        Text(model.controlTitles[index])
                    } icon: {
                        EncoderCap(index: index, value: activeValues[index])
                    }
                }
            }
        } header: {
            Text("Encoders")
        } footer: {
            Text("Keyframes only: each encoder snaps between five drawn positions. Live easing needs a generator script beside the frames.")
        }

        Section {
            Toggle("A note", isOn: $model.holdsNote)
            Toggle("Shift", isOn: $model.holdsShift)
        } header: {
            Text("Hold")
        } footer: {
            Text("Shift swaps what the four header slots show. It never adds a row.")
        }

        Section("View") {
            Picker("Lens", selection: $model.lens) {
                ForEach(Lens.allCases) { lens in
                    Text(lens.rawValue).tag(lens)
                }
            }
            LabeledContent("MIDI controller", value: "[CONTROLLER NAME]")
        }
    }

    private var activeValues: [Double] { model.holdsShift ? model.shiftValues : model.values }

    private func binding(for index: Int) -> Binding<Double> {
        Binding(
            get: { activeValues[index] },
            set: { newValue in
                if model.holdsShift { model.shiftValues[index] = newValue } else { model.values[index] = newValue }
            }
        )
    }

    // MARK: Footer

    @ViewBuilder
    private var footer: some View {
        VStack(alignment: .leading, spacing: 8) {
            switch model.stage {
            case .concept:
                Picker("Image model", selection: $imageModel) {
                    Text("SenseNova-U1.5 · 16 GB RAM").tag("sensenova")
                    Text("Ming-Image · 24 GB RAM").tag("ming")
                }
                .labelsHidden()
                Text("Makes the five concept pictures, then unloads once one is approved.")
                    .font(.callout)
                    .foregroundStyle(.secondary)
                statusLine(detail: "11.8 GB · Apache 2.0")
                mainButton("Generate Five Concepts")
            case .frames:
                Picker("Drawing model", selection: $drawingModel) {
                    Text("Small code model · on this Mac").tag("local")
                    Text("A connected model").tag("connected")
                }
                .labelsHidden()
                Text("Draws the body only. The header is stamped from the definition and never generated.")
                    .font(.callout)
                    .foregroundStyle(.secondary)
                statusLine(detail: "about 1 GB")
                mainButton("Draw Five Frames")
            case .play:
                Text("The sweep video is these exact frames in order, encoded on the Mac. No model draws it.")
                    .font(.callout)
                    .foregroundStyle(.secondary)
                mainButton("Record a Sweep Video")
            }
        }
    }

    private func statusLine(detail: String) -> some View {
        HStack(spacing: 6) {
            Image(systemName: "checkmark.circle.fill")
                .foregroundStyle(.green)
            Text("Ready · in memory")
            Spacer()
            Text(detail)
                .foregroundStyle(.secondary)
        }
        .font(.callout)
    }

    private func mainButton(_ title: String) -> some View {
        Button {
        } label: {
            Text(title)
                .frame(maxWidth: .infinity)
        }
        .controlSize(.large)
        .keyboardShortcut(.return, modifiers: .command)
    }
}

/// A small encoder cap in its header column's grey, with a pointer that follows the value.
private struct EncoderCap: View {
    var index: Int
    var value: Double

    var body: some View {
        let cap = Grey.step([1, 3, 5, 7][index])
        let ink: Color = index < 2 ? .white : .black
        Circle()
            .fill(cap)
            .overlay(
                Capsule()
                    .fill(ink)
                    .frame(width: 2, height: 6)
                    .offset(y: -4)
                    .rotationEffect(.degrees(-135 + value * 270))
            )
            .frame(width: 18, height: 18)
            .accessibilityHidden(true)
    }
}
