import AppKit
import SwiftUI

/// `swift run` starts a bare executable with no bundle, so the app has to ask to be a regular,
/// frontmost app itself. Xcode's Run does the same thing through the scheme.
final class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
    }
}

@main
struct MacBenchApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate
    @StateObject private var model = BenchModel()

    var body: some Scene {
        WindowGroup("sample-machine") {
            ContentView()
                .environmentObject(model)
                .frame(minWidth: 980, minHeight: 640)
        }
        .defaultSize(width: 1280, height: 800)

        Settings {
            SettingsView()
        }
    }
}
