import SwiftUI

/// The Settings window (⌘,): a stock tabbed settings scene.
struct SettingsView: View {
    var body: some View {
        TabView {
            EngineSettings()
                .tabItem { Label("Engines", systemImage: "cpu") }
            placeholder("MIDI settings go here.")
                .tabItem { Label("MIDI", systemImage: "pianokeys") }
            placeholder("Folder settings go here.")
                .tabItem { Label("Folders", systemImage: "folder") }
        }
        .frame(width: 620, height: 520)
    }

    private func placeholder(_ text: String) -> some View {
        Text(text)
            .foregroundStyle(.secondary)
            .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

private struct EngineSettings: View {
    @AppStorage("drawingEngine") private var engine = "local"

    var body: some View {
        Form {
            Section {
                Picker("Frames are drawn by", selection: $engine) {
                    Text("This Mac").tag("local")
                    Text("A connected model").tag("connected")
                }
                .pickerStyle(.radioGroup)
            } footer: {
                Text(engine == "local"
                     ? "Keyframes from a small code model. Works offline; encoders snap between drawn positions."
                     : "A generator script from a hosted model. Needs a connection; encoders move live and eased.")
            }

            Section {
                row("Concept stills", "SenseNova-U1.5", "11.8 GB · needs 16 GB", "Downloaded")
                row("Concept clips", "LTX-2.3, 4-bit", "28.5 GB · needs 32 GB", "Not downloaded")
                row("Interpret", "[VISION MODEL TO CHOOSE]", "[SIZE]", "To decide")
                row("Draw", "Small code model", "about 1 GB", "To build")
                row("Trace, lint, compare", "Built in", "No model", "Ready")
                row("Header and video", "Built in", "No model", "Ready")
            } header: {
                Text("On this Mac")
            } footer: {
                Text("The image model unloads once a concept is approved, so the other two fit together on a 16 GB Mac. Not on a Mac? The Python bench and the MCP tools work as before and write the same files.")
            }
        }
        .formStyle(.grouped)
    }

    private func row(_ step: String, _ runsOn: String, _ detail: String, _ state: String) -> some View {
        LabeledContent {
            Text(state)
        } label: {
            Text(step)
            Text("\(runsOn) · \(detail)")
        }
    }
}
