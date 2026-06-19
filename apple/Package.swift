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
        // Mode A engine adapter (HSM-5-02). Kept a SEPARATE product so the native
        // llama.cpp engine links ONLY where it's used (Hosts), never into the
        // domain (Contracts/RuntimeCore) — the Phase-6 "ProviderInterfaces" concern.
        .library(name: "InferenceLlama", targets: ["InferenceLlama"]),
    ],
    dependencies: [
        // llama.cpp behind Swift (bundles the engine + Metal; macOS/iOS). The
        // HSM-5-01 pick; reversible because it sits behind `ILLMProvider`.
        .package(url: "https://github.com/eastriverlee/LLM.swift", from: "2.0.0"),
    ],
    targets: [
        // Layer 1 — language-neutral schema as Swift types. Foundation only.
        .target(name: "Contracts"),
        // Layer 2 — meeting/artifact/MIR engines, persistence, sync. No UI.
        // Depends on Providers for the injected port protocols (ILLMProvider etc.).
        .target(name: "RuntimeCore", dependencies: ["Contracts", "Providers"]),
        // Layer 3 — provider protocols (transcriber/LLM/audio/storage/sync).
        .target(name: "Providers", dependencies: ["Contracts"]),
        // Layer 3 (engine adapter) — the llama.cpp-backed `ILLMProvider` (Mode A).
        // Depends on the native engine; the domain does not depend on this target.
        .target(name: "InferenceLlama",
                 dependencies: ["Providers", "Contracts", .product(name: "LLM", package: "LLM.swift")]),
        // Layer 4 — platform hosts (iPad/iPhone apps). The only UI layer.
        .target(name: "Hosts", dependencies: ["RuntimeCore", "Providers", "Contracts"]),
        .testTarget(name: "ContractsTests", dependencies: ["Contracts"]),
        .testTarget(name: "RuntimeCoreTests", dependencies: ["RuntimeCore", "Providers", "Contracts"]),
        .testTarget(name: "ProvidersTests", dependencies: ["Providers", "Contracts"]),
        .testTarget(name: "InferenceLlamaTests",
                    dependencies: ["InferenceLlama", "RuntimeCore", "Providers", "Contracts"]),
    ]
)
