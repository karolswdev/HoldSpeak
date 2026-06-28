import Foundation

// HSM-18-01 — the dictation teleprompter's data: the hub's dry-run preview (what WOULD be typed,
// and where) and a readiness snapshot. Decoded with HoldSpeakContracts.decoder()
// (.convertFromSnakeCase), so the snake_case wire (final_text, total_elapsed_ms) maps to these
// camelCase properties automatically. Lenient (most fields optional) so a hub shape drift degrades
// gracefully on the teleprompter rather than throwing.

/// Where a dry-run says the dictation would land (the detected target profile / focused app).
///
/// This is the wire shape of `TargetProfile.to_dict()` in `holdspeak/target_profile.py`:
/// `{id, label, confidence, source, app_name, process_name, window_title, details}`. The hub
/// returns this object verbatim under `target` on both `/api/dictation/dry-run` and
/// `/api/dictation/readiness`. snake_case (`app_name`, `process_name`, `window_title`) maps to
/// these camelCase properties via `.convertFromSnakeCase` — no hand-written `CodingKeys`. Every
/// field is optional so a sparse / drifted hub payload still decodes.
public struct DryRunTarget: Codable, Sendable, Equatable {
    /// Stable profile id ("cursor", "claude_code", "browser", "unknown", ...).
    public var id: String?
    /// Human label the desk header renders ("Cursor", "Claude Code", ...).
    public var label: String?
    public var confidence: Double?
    /// How the profile was resolved ("explicit" | "hints" | "none" | ...).
    public var source: String?
    public var appName: String?
    public var processName: String?
    public var windowTitle: String?
    /// Free-form server extras (e.g. `{"matched": "codex"}`); kept as a typed blob so an
    /// evolving payload still decodes.
    public var details: [String: JSONValue]?

    public init(id: String? = nil, label: String? = nil, confidence: Double? = nil,
                source: String? = nil, appName: String? = nil, processName: String? = nil,
                windowTitle: String? = nil, details: [String: JSONValue]? = nil) {
        self.id = id
        self.label = label
        self.confidence = confidence
        self.source = source
        self.appName = appName
        self.processName = processName
        self.windowTitle = windowTitle
        self.details = details
    }

    /// The best human label for the destination column header ("→ Cursor"), or nil if unknown.
    /// Prefers the hub's own `label`, then the app/window/process names; an "unknown" id is
    /// treated as no destination so the teleprompter shows nothing rather than "unknown".
    public var displayLabel: String? {
        for candidate in [label, appName, windowTitle, processName] {
            if let c = candidate?.trimmingCharacters(in: .whitespaces), !c.isEmpty { return c }
        }
        if let id = id?.trimmingCharacters(in: .whitespaces),
           !id.isEmpty, id.lowercased() != "unknown" {
            return id
        }
        return nil
    }
}

/// The detected project context the hub attaches to a dry-run / readiness payload
/// (`{name, root, anchor}` from `detect_project_for_cwd`). `null` when no project is detected.
public struct DictationProject: Codable, Sendable, Equatable {
    public var name: String?
    public var root: String?
    public var anchor: String?

    public init(name: String? = nil, root: String? = nil, anchor: String? = nil) {
        self.name = name
        self.root = root
        self.anchor = anchor
    }
}

/// The result of `POST /api/dictation/dry-run`: the routed + rewritten text the pipeline would
/// produce, plus where it would go, so the user sees the receipt before a keystroke leaves the app.
///
/// Mirrors `_run_dictation_dry_run_text` in
/// `holdspeak/web/routes/dictation/_helpers.py`: `final_text` is the only always-present field;
/// `target` is a `DryRunTarget` (the `TargetProfile.to_dict()` shape, NOT app/window/process),
/// `project` is an object (`{name, root, anchor}`), `runtime_status`/`runtime_detail` describe the
/// runtime, `blocks_count` counts the loaded blocks, and `warnings` is a list of strings. There is
/// no top-level `status` field — that was a model guess; the runtime state lives in
/// `runtimeStatus`. All but `finalText` are optional so a drifted / disabled-pipeline payload
/// still decodes.
public struct DictationDryRun: Codable, Sendable, Equatable {
    public var finalText: String
    public var target: DryRunTarget?
    public var warnings: [String]?
    public var totalElapsedMs: Double?
    public var runtimeStatus: String?
    public var runtimeDetail: String?
    public var blocksCount: Int?
    public var project: DictationProject?
    /// The deterministic doc-suggestion outcome ("stored" | "no_suggestion" | "dismissed" | ...).
    public var suggestionStatus: String?
    /// The journal row id this dry-run wrote (when journaling is on), for the in-the-moment fix.
    public var journalId: Int?

    public init(finalText: String, target: DryRunTarget? = nil, warnings: [String]? = nil,
                totalElapsedMs: Double? = nil, runtimeStatus: String? = nil,
                runtimeDetail: String? = nil, blocksCount: Int? = nil,
                project: DictationProject? = nil, suggestionStatus: String? = nil,
                journalId: Int? = nil) {
        self.finalText = finalText
        self.target = target
        self.warnings = warnings
        self.totalElapsedMs = totalElapsedMs
        self.runtimeStatus = runtimeStatus
        self.runtimeDetail = runtimeDetail
        self.blocksCount = blocksCount
        self.project = project
        self.suggestionStatus = suggestionStatus
        self.journalId = journalId
    }
}

/// The runtime sub-object of the readiness snapshot (`runtime` in the real payload). Carries the
/// availability `status` ("available" | "missing_model" | "unavailable" | "disabled"), whether a
/// local model file exists, and the requested/resolved backend.
public struct DictationRuntimeReadiness: Codable, Sendable, Equatable {
    public var status: String?
    public var modelExists: Bool?
    public var requestedBackend: String?
    public var resolvedBackend: String?
    public var detail: String?

    public init(status: String? = nil, modelExists: Bool? = nil, requestedBackend: String? = nil,
                resolvedBackend: String? = nil, detail: String? = nil) {
        self.status = status
        self.modelExists = modelExists
        self.requestedBackend = requestedBackend
        self.resolvedBackend = resolvedBackend
        self.detail = detail
    }
}

/// A readiness snapshot for the dictate screen's status strip (`GET /api/dictation/readiness`).
///
/// Mirrors `api_dictation_readiness` in `holdspeak/web/routes/dictation/pipeline.py`: the
/// top-level keys are `ready` (the hub's own readiness verdict), `project`, `runtime`, and
/// `target` (the `DryRunTarget` / `TargetProfile.to_dict()` shape). The earlier model invented a
/// flat `status`/`model_exists`/`runtime_status`/`openai_compatible` — none of those are
/// top-level; `model_exists` lives under `runtime`. All optional so a partial payload still
/// decodes.
public struct DictationReadiness: Codable, Sendable, Equatable {
    /// The hub's own readiness verdict (pipeline enabled + project + valid blocks + runtime).
    public var ready: Bool?
    public var project: DictationProject?
    public var runtime: DictationRuntimeReadiness?
    public var target: DryRunTarget?

    public init(ready: Bool? = nil, project: DictationProject? = nil,
                runtime: DictationRuntimeReadiness? = nil, target: DryRunTarget? = nil) {
        self.ready = ready
        self.project = project
        self.runtime = runtime
        self.target = target
    }

    /// True when the snapshot reports a usable runtime. Trusts the hub's `ready` verdict first,
    /// then falls back to "the runtime is available" (model present or endpoint reachable).
    public var isReady: Bool {
        if let ready { return ready }
        return runtime?.status?.lowercased() == "available"
    }
}
