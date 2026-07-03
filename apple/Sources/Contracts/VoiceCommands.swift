import Foundation

// HSM-18-02 — the voice command macro contracts, modelled against
// `holdspeak/config.py` (`MacrosConfig` / `VoiceMacro` / `VoiceMacroAction`) as they
// ride `GET/PUT /api/settings` under `dictation.macros`, and the board's
// `POST /api/commands/test` response (holdspeak/web/routes/system.py).
//
// Wire keys are snake_case via the shared `HoldSpeakContracts.decoder()`; these
// types carry no hand-written CodingKeys.

/// One deterministic action: a `kind` (`open_url` | `launch_app` | `shell` |
/// `type_text`) + that kind's single `payload`. Raw wire strings so an unknown
/// future kind never fails the decode; the hub validates on write.
public struct VoiceMacroActionSpec: Codable, Equatable, Sendable {
    public var kind: String
    public var payload: String

    public init(kind: String, payload: String) {
        self.kind = kind
        self.payload = payload
    }

    /// The one plain-language line of exactly what this fires — kept in lockstep
    /// with `VoiceMacroAction.preview()` in `holdspeak/config.py` (design §10:
    /// the card, the editor, and any audit read identically).
    public var preview: String {
        switch kind {
        case "open_url": return "opens \(payload)"
        case "launch_app": return "launches \(payload)"
        case "shell": return "runs: \(payload)"
        case "type_text": return "types: \(payload)"
        default: return payload
        }
    }
}

/// One configured macro: the spoken `keyword` → its action.
public struct VoiceMacroSpec: Codable, Equatable, Sendable {
    public var keyword: String
    public var action: VoiceMacroActionSpec

    public init(keyword: String, action: VoiceMacroActionSpec) {
        self.keyword = keyword
        self.action = action
    }
}

/// The `dictation.macros` settings block. Off by default hub-side; the board
/// reads and writes exactly this shape through `/api/settings`.
public struct VoiceMacroSettings: Codable, Equatable, Sendable {
    public var enabled: Bool
    public var items: [VoiceMacroSpec]

    public init(enabled: Bool = false, items: [VoiceMacroSpec] = []) {
        self.enabled = enabled
        self.items = items
    }
}

/// `POST /api/commands/test` — the board's verify-one-action result. `tested`
/// is false for `type_text` (nothing to run; it types into the focused app),
/// `output` carries a shell action's captured output when the hub returns one.
public struct VoiceMacroTestResult: Codable, Equatable, Sendable {
    public var ok: Bool
    public var tested: Bool?
    public var preview: String?
    public var note: String?
    public var output: String?
    public var error: String?

    public init(ok: Bool, tested: Bool? = nil, preview: String? = nil,
                note: String? = nil, output: String? = nil, error: String? = nil) {
        self.ok = ok
        self.tested = tested
        self.preview = preview
        self.note = note
        self.output = output
        self.error = error
    }
}
