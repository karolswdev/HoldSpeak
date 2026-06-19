import Foundation
import CryptoKit
import Contracts
import Providers

/// HSM-6-02 — the five core artifact types HoldSpeak meetings must yield:
/// Action Items, Decisions, Risks, Requirements, Summaries.
///
/// Contract reality (Phase 0): only `ActionItem` has a dedicated typed contract +
/// schema. Decisions / Risks / Requirements are tagged-union `Artifact`s whose
/// type-specific fields live in the open `structured_json` blob (the Phase-0
/// design keeps these open in v0). A "Summary" has no `artifact_type` — its
/// contract home is `IntelSnapshot` (its own Phase-0 schema). So:
///
///   - Action Items → `Artifact(.actionItems)`, `structured_json` = a validated
///     `[ActionItem]` (the engine stamps the lifecycle fields the model can't).
///   - Decisions / Risks / Requirements → open-blob `Artifact`s produced through
///     the HSM-6-01 engine with per-type prompts.
///   - Summary → `IntelSnapshot` (summary + topics).
///
/// We do NOT invent a `summary` artifact type or per-type schemas the Phase-0
/// contract doesn't have (phase risk: a shape the contract can't hold is a
/// contract question, not a local hack).
public struct CoreArtifactGenerator: Sendable {

    /// The artifact-typed core types (Summary is `IntelSnapshot`, generated apart).
    public static let coreArtifactTypes: [ArtifactType] =
        [.actionItems, .decisions, .riskRegister, .requirements]

    let provider: ILLMProvider
    let pluginId: String
    let pluginVersion: String
    let maxAttempts: Int
    let now: @Sendable () -> Date

    public init(
        provider: ILLMProvider,
        pluginId: String = "holdspeak.mobile.intelligence",
        pluginVersion: String = HoldSpeakContracts.contractVersion,
        maxAttempts: Int = 3,
        now: @escaping @Sendable () -> Date = { Date() }
    ) {
        self.provider = provider
        self.pluginId = pluginId
        self.pluginVersion = pluginVersion
        self.maxAttempts = maxAttempts
        self.now = now
    }

    // MARK: Action Items (typed)

    /// What the model contributes for an action item — the lifecycle (id/status/
    /// review_state/created_at) is the engine's to stamp, never the model's.
    public struct ActionItemDraft: Decodable, Sendable, Equatable {
        public var task: String
        public var owner: String?
        public var due: String?
        public var sourceTimestamp: Double?
    }

    /// Generate the action-items artifact: `structured_json` is a schema-valid
    /// `[ActionItem]`. An empty transcript yields an empty list, not a fabricated
    /// one (the model is told to return `[]` when there are none).
    public func generateActionItems(from transcript: Transcript) async throws -> Artifact {
        let drafts = try await StructuredOutput.generate(
            [ActionItemDraft].self,
            prompt: CoreArtifactPrompts.actionItems(transcript),
            using: provider, maxAttempts: maxAttempts)
        let stamped = now()
        let items: [ActionItem] = drafts.map { d in
            ActionItem(
                task: d.task, owner: d.owner, due: d.due,
                id: Self.actionItemID(task: d.task, owner: d.owner),
                status: .pending, reviewState: .pending,
                sourceTimestamp: d.sourceTimestamp, createdAt: stamped)
        }
        let body = items.isEmpty
            ? "_No action items._"
            : items.map { "- [ ] \($0.task)" + ($0.owner.map { " (@\($0))" } ?? "") }.joined(separator: "\n")
        return Artifact(
            id: UUID().uuidString, meetingId: transcript.meetingId,
            artifactType: .actionItems, title: "Action Items", bodyMarkdown: body,
            structuredJson: try Self.jsonValue(items), confidence: 0.8,
            status: .draft, pluginId: pluginId, pluginVersion: pluginVersion,
            sources: [ArtifactSource(sourceType: "transcript", sourceRef: transcript.transcriptHash)])
    }

    // MARK: Decisions / Risks / Requirements (open-blob, via the HSM-6-01 engine)

    /// Generate one open-blob core artifact (`.decisions`, `.riskRegister`, or
    /// `.requirements`) using the HSM-6-01 engine with this type's prompt.
    public func generate(_ type: ArtifactType, from transcript: Transcript) async throws -> Artifact {
        precondition(Self.coreArtifactTypes.contains(type), "\(type) is not a core artifact type")
        if type == .actionItems { return try await generateActionItems(from: transcript) }
        let engine = ArtifactGenerationEngine(
            provider: provider, pluginId: pluginId, pluginVersion: pluginVersion,
            maxAttempts: maxAttempts,
            promptBuilder: { t, tr in CoreArtifactPrompts.prompt(for: t, tr) })
        return try await engine.generate(type, from: transcript)
    }

    // MARK: Summary (IntelSnapshot)

    struct SummaryDraft: Decodable { var summary: String; var topics: [String]? }

    /// Generate the meeting summary as an `IntelSnapshot` (the contract home for a
    /// summary). Action items on the snapshot are left empty here — they are their
    /// own artifact (`generateActionItems`); this avoids double-sourcing them.
    public func generateSummary(from transcript: Transcript) async throws -> IntelSnapshot {
        let draft = try await StructuredOutput.generate(
            SummaryDraft.self, prompt: CoreArtifactPrompts.summary(transcript),
            using: provider, maxAttempts: maxAttempts)
        return IntelSnapshot(
            timestamp: now().timeIntervalSince1970,
            topics: draft.topics ?? [], actionItems: [], summary: draft.summary)
    }

    // MARK: helpers

    /// Mirror the desktop's content-addressed id: `sha256(task:owner)[:12]`
    /// (action-item.schema.json), so the same item dedupes across runs.
    static func actionItemID(task: String, owner: String?) -> String {
        let digest = SHA256.hash(data: Data("\(task):\(owner ?? "")".utf8))
        let hex = digest.map { String(format: "%02x", $0) }.joined()
        return String(hex.prefix(12))
    }

    /// Encode an `Encodable` to a contract `JSONValue` (wire-shape, snake_case).
    static func jsonValue<T: Encodable>(_ value: T) throws -> JSONValue {
        let data = try HoldSpeakContracts.encoder().encode(value)
        return try HoldSpeakContracts.decoder().decode(JSONValue.self, from: data)
    }
}

/// Per-type prompts kept close to the desktop's extraction intent so Phase-6
/// parity (HSM-6-04) compares like with like. The "[]/empty when none" rule is
/// explicit in every prompt — it is what stops hallucinated artifacts.
public enum CoreArtifactPrompts {

    static func transcriptText(_ t: Transcript) -> String {
        t.segments.map { "[\(Int($0.startTime))s] \($0.speaker): \($0.text)" }.joined(separator: "\n")
    }

    public static func actionItems(_ t: Transcript) -> String {
        """
        Extract the ACTION ITEMS from the meeting transcript below. An action item
        is a concrete task someone committed to. Return ONLY a JSON array; each
        element is {"task": string, "owner": string|null, "due": string|null,
        "source_timestamp": number|null} where source_timestamp is the second mark
        in the transcript that justifies it. If there are NO action items, return [].

        Transcript:
        \(transcriptText(t))
        """
    }

    public static func summary(_ t: Transcript) -> String {
        """
        Summarize the meeting transcript below. Return ONLY a JSON object:
        {"summary": string (2-4 sentences), "topics": array of short topic strings}.

        Transcript:
        \(transcriptText(t))
        """
    }

    /// The open-blob types: the engine decodes title/body/structured_json/confidence.
    public static func prompt(for type: ArtifactType, _ t: Transcript) -> String {
        let (noun, guidance): (String, String)
        switch type {
        case .decisions:
            (noun, guidance) = ("DECISIONS",
                "a decision is a choice the group settled on. structured_json: {\"items\": [{\"decision\": string, \"rationale\": string|null, \"source_timestamp\": number|null}]}")
        case .riskRegister:
            (noun, guidance) = ("RISKS",
                "a risk is something that could threaten the work. structured_json: {\"items\": [{\"risk\": string, \"severity\": \"low\"|\"medium\"|\"high\"|null, \"source_timestamp\": number|null}]}")
        case .requirements:
            (noun, guidance) = ("REQUIREMENTS",
                "a requirement is something the solution must satisfy. structured_json: {\"items\": [{\"requirement\": string, \"source_timestamp\": number|null}]}")
        default:
            (noun, guidance) = (type.rawValue.uppercased(), "structured_json: {\"items\": []}")
        }
        return """
        Extract the \(noun) from the meeting transcript below — \(guidance).
        Return ONLY a JSON object {"title": string, "body_markdown": string,
        "structured_json": object, "confidence": number 0-1}. If there are none,
        return an empty "items" array — never invent one.

        Transcript:
        \(transcriptText(t))
        """
    }
}
