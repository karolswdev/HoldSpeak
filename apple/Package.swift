// swift-tools-version: 6.0
// HoldSpeak Mobile Runtime — the four-layer Swift package (charter Architecture).
// Layer rule: Contracts / RuntimeCore / Providers must NOT depend on SwiftUI,
// UIKit, or WebView. Hosts (Layer 4) is the only UI-bearing layer.
import PackageDescription

let package = Package(
    name: "HoldSpeakMobile",
    platforms: [
        // Provisional floor; revisit at Phase 5 — if Core ML wins (MLState KV
        // cache) the iOS floor moves to 18 (PROGRAM-RISKS P6).
        .macOS(.v14), .iOS(.v17),
    ],
    products: [
        .library(name: "Contracts", targets: ["Contracts"]),
        .library(name: "RuntimeCore", targets: ["RuntimeCore"]),
        .library(name: "Providers", targets: ["Providers"]),
    ],
    targets: [
        // Layer 1 — language-neutral schema as Swift types. Foundation only.
        .target(name: "Contracts"),
        // Layer 2 — meeting/artifact/MIR engines, persistence, sync. No UI.
        // Depends on Providers for the injected port protocols (ILLMProvider etc.).
        .target(name: "RuntimeCore", dependencies: ["Contracts", "Providers"]),
        // Layer 3 — provider protocols (transcriber/LLM/audio/storage/sync).
        .target(name: "Providers", dependencies: ["Contracts"]),
        // Layer 4 — platform hosts (iPad/iPhone apps). The only UI layer.
        .target(name: "Hosts", dependencies: ["RuntimeCore", "Providers", "Contracts"]),
        .testTarget(name: "ContractsTests", dependencies: ["Contracts"]),
        .testTarget(name: "RuntimeCoreTests", dependencies: ["RuntimeCore", "Providers", "Contracts"]),
        .testTarget(name: "ProvidersTests", dependencies: ["Providers", "Contracts"]),
    ]
)
