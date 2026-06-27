import Foundation

// HSM-18-01 — the dictation teleprompter's data: the hub's dry-run preview (what WOULD be typed,
// and where) and a readiness snapshot. Decoded with HoldSpeakContracts.decoder()
// (.convertFromSnakeCase), so the snake_case wire (final_text, total_elapsed_ms) maps to these
// camelCase properties automatically. Lenient (most fields optional) so a hub shape drift degrades
// gracefully on the teleprompter rather than throwing.

/// Where a dry-run says the dictation would land (the detected target profile / focused app).
public struct DryRunTarget: Codable, Sendable, Equatable {
    public var app: String?
    public var window: String?
    public var process: String?
    public var profile: String?
    public var confidence: Double?

    /// The best human label for the destination column header ("→ Cursor"), or nil if unknown.
    public var label: String? {
        for candidate in [app, window, process, profile] {
            if let c = candidate?.trimmingCharacters(in: .whitespaces), !c.isEmpty { return c }
        }
        return nil
    }
}

/// The result of `POST /api/dictation/dry-run`: the routed + rewritten text the pipeline would
/// produce, plus where it would go, so the user sees the receipt before a keystroke leaves the app.
public struct DictationDryRun: Codable, Sendable, Equatable {
    public var finalText: String
    public var target: DryRunTarget?
    public var warnings: [String]?
    public var totalElapsedMs: Double?
    public var status: String?
    public var blocksCount: Int?
    public var project: String?

    public init(finalText: String, target: DryRunTarget? = nil, warnings: [String]? = nil,
                totalElapsedMs: Double? = nil, status: String? = nil, blocksCount: Int? = nil,
                project: String? = nil) {
        self.finalText = finalText
        self.target = target
        self.warnings = warnings
        self.totalElapsedMs = totalElapsedMs
        self.status = status
        self.blocksCount = blocksCount
        self.project = project
    }
}

/// A lean readiness snapshot for the dictate screen's status strip (`GET /api/dictation/readiness`).
public struct DictationReadiness: Codable, Sendable, Equatable {
    public var status: String?
    public var modelExists: Bool?
    public var runtimeStatus: String?
    public var openaiCompatible: Bool?
    public var project: String?

    /// True when the snapshot reports a usable runtime (a model present or an endpoint reachable).
    public var isReady: Bool {
        if let s = status?.lowercased(), s == "ready" || s == "ok" { return true }
        return (modelExists ?? false) || (openaiCompatible ?? false)
    }
}
