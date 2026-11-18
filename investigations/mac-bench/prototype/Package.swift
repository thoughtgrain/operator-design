// swift-tools-version: 5.9
import PackageDescription

// A look-and-feel prototype of the Mac bench: stock SwiftUI controls and stub data, no models and no engine.
// Run it with `swift run` from this folder, or open Package.swift in Xcode and press Run.
let package = Package(
    name: "MacBenchPrototype",
    platforms: [.macOS(.v14)],
    targets: [
        .executableTarget(name: "MacBenchPrototype", path: "Sources/MacBenchPrototype")
    ]
)
