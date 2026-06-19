import Foundation
import Contracts
import RuntimeCore
import Providers

/// Layer 4 — platform hosts (iPad/iPhone apps). The only UI-bearing layer; it
/// presents the Runtime Core and never owns business logic. Placeholder for
/// Phase 1 (no SwiftUI yet, so the package builds + tests on macOS); the real
/// SwiftUI hosts land in Phases 8 (iPad) and 9 (iPhone).
public enum Hosts {
    public static let layer = "hosts"
    public static let runtimeLayer = RuntimeCore.layer
}
