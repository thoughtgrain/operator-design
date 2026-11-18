import SwiftUI

/// The window: what to make on the left, the result on the right. Same split TurboMLX uses.
struct ContentView: View {
    @EnvironmentObject private var model: BenchModel

    var body: some View {
        NavigationSplitView {
            ControlPanel()
                .navigationSplitViewColumnWidth(min: 340, ideal: 420, max: 520)
        } detail: {
            OutputPanel()
        }
        .navigationTitle("sample-machine")
        .navigationSubtitle(subtitle)
        .toolbar {
            ToolbarItem(placement: .principal) {
                Picker("Stage", selection: $model.stage) {
                    ForEach(Stage.allCases) { stage in
                        Text(stage.rawValue).tag(stage)
                    }
                }
                .pickerStyle(.segmented)
                .labelsHidden()
                .help("Concept, then frames, then play")
            }
            ToolbarItemGroup(placement: .primaryAction) {
                Button {
                } label: {
                    Label("Show in Finder", systemImage: "folder")
                }
                .help("Show screens/sample-machine in Finder")

                if model.stage != .play {
                    Button {
                    } label: {
                        Label("Turn Down", systemImage: "trash")
                    }
                    .help("Turn this pass down")
                }

                primaryAction
            }
        }
    }

    private var subtitle: String {
        switch model.stage {
        case .concept: return "Concept · a generated picture, not a frame"
        case .frames: return model.variant.ready ? "Frame · drawn and linted" : "Frame · not ready to pick"
        case .play: return "Preview on this Mac · not the OP-XY"
        }
    }

    @ViewBuilder
    private var primaryAction: some View {
        switch model.stage {
        case .concept:
            Button("Approve Concept \(model.concept.id)") { model.stage = .frames }
                .buttonStyle(.borderedProminent)
        case .frames:
            Button("Pick Frame \(model.variant.id)") { model.stage = .play }
                .buttonStyle(.borderedProminent)
                .disabled(!model.variant.ready)
        case .play:
            Button("Write the Handoff") {}
                .buttonStyle(.borderedProminent)
        }
    }
}
