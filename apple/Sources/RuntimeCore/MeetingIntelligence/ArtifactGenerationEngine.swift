import Foundation
import Contracts
import Providers

/// HSM-6-01 — the artifact-generation engine (Runtime Core, Layer 2).
///
/// Turns a finished `Transcript` plus an injected `ILLMProvider` into Phase-0
/// `Artifact` records. This is the generic seam every artifact type lives on
/// (HSM-6-02 the five core types, HSM-6-03 ADR Candidates + Follow-ups): it owns
/// the drive-the-model → bind-to-contract machinery; the concrete prompts/parsers
/// are layered on via the injected `PromptBuilder`.
///
/// The model contributes only the *intelligence* (an `ArtifactDraft`: title, body,
/// type-specific JSON, confidence). The engine stamps the non-model fields (id,
/// meetingId, type, plugin identity, sources) and binds the result into a full
/// `Artifact`. Robust to the model returning prose instead of clean JSON: a parse
/// failure surfaces as a recoverable `.failure`, never a crash.
///
/// Propose-only (charter Propose→Review→Approve→Execute): every emitted artifact
/// is a `.draft` proposal. No code path here executes an action or calls a
/// connector — generation proposes, the human approves, an executor (elsewhere)
/// acts.
public struct ArtifactGenerationEngine: Sendable {

    /// The model's contribution — decoded from its (possibly messy) text via
    /// `StructuredOutput`. Type-agnostic on purpose: the discriminator and
    /// provenance are the engine's to stamp, not the model's to invent.
    public struct ArtifactDraft: Decodable, Sendable, Equatable {
        public var title: String
        public var bodyMarkdown: String
        public var structuredJson: JSONValue
        public var confidence: Double

        enum CodingKeys: String, CodingKey {
            case title, bodyMarkdown, structuredJson, confidence
        }

        public init(from decoder: Decoder) throws {
            let c = try decoder.container(keyedBy: CodingKeys.self)
            title = try c.decode(String.self, forKey: .title)
            bodyMarkdown = try c.decodeIfPresent(String.self, forKey: .bodyMarkdown) ?? ""
            structuredJson = try c.decodeIfPresent(JSONValue.self, forKey: .structuredJson) ?? .object([:])
            // Models are unreliable about emitting a confidence; default mid.
            confidence = try c.decodeIfPresent(Double.self, forKey: .confidence) ?? 0.5
        }

        public init(title: String, bodyMarkdown: String = "",
                    structuredJson: JSONValue = .object([:]), confidence: Double = 0.5) {
            self.title = title
            self.bodyMarkdown = bodyMarkdown
            self.structuredJson = structuredJson
            self.confidence = confidence
        }
    }

    /// Builds the per-type prompt from the transcript. HSM-6-02/03 inject the
    /// concrete, type-specific prompts; the default is a generic, schema-hinted
    /// instruction sufficient to exercise the seam.
    public typealias PromptBuilder = @Sendable (ArtifactType, Transcript) -> String

    let provider: ILLMProvider
    let pluginId: String
    let pluginVersion: String
    let maxAttempts: Int
    let promptBuilder: PromptBuilder
    let idGenerator: @Sendable () -> String

    public init(
        provider: ILLMProvider,
        pluginId: String = "holdspeak.mobile.intelligence",
        pluginVersion: String = HoldSpeakContracts.contractVersion,
        maxAttempts: Int = 3,
        promptBuilder: @escaping PromptBuilder = ArtifactGenerationEngine.defaultPrompt,
        idGenerator: @escaping @Sendable () -> String = { UUID().uuidString }
    ) {
        self.provider = provider
        self.pluginId = pluginId
        self.pluginVersion = pluginVersion
        self.maxAttempts = maxAttempts
        self.promptBuilder = promptBuilder
        self.idGenerator = idGenerator
    }

    /// Generate one artifact of `type` from `transcript`. Throws only for a
    /// genuinely unrecoverable provider/parse failure; callers that want
    /// per-type resilience should use ``generate(types:from:)``.
    public func generate(_ type: ArtifactType, from transcript: Transcript) async throws -> Artifact {
        let prompt = promptBuilder(type, transcript)
        let draft = try await StructuredOutput.generate(
            ArtifactDraft.self, prompt: prompt, using: provider, maxAttempts: maxAttempts)
        return bind(draft, type: type, transcript: transcript)
    }

    /// Generate several artifact types in one pass. Each type's outcome is
    /// independent — a malformed response for one type yields a `.failure` for
    /// that type without sinking the others (charter robustness).
    public func generate(
        types: [ArtifactType], from transcript: Transcript
    ) async -> [(type: ArtifactType, result: Result<Artifact, Error>)] {
        var out: [(type: ArtifactType, result: Result<Artifact, Error>)] = []
        for type in types {
            do { out.append((type, .success(try await generate(type, from: transcript)))) }
            catch { out.append((type, .failure(error))) }
        }
        return out
    }

    /// Stamp the engine-owned fields onto the model's draft, producing a complete
    /// Phase-0 `Artifact` proposal (`status == .draft`).
    func bind(_ draft: ArtifactDraft, type: ArtifactType, transcript: Transcript) -> Artifact {
        Artifact(
            id: idGenerator(),
            meetingId: transcript.meetingId,
            artifactType: type,
            title: draft.title,
            bodyMarkdown: draft.bodyMarkdown,
            structuredJson: draft.structuredJson,
            confidence: draft.confidence,
            status: .draft,                       // propose-only; never .accepted here
            pluginId: pluginId,
            pluginVersion: pluginVersion,
            sources: [ArtifactSource(sourceType: "transcript", sourceRef: transcript.transcriptHash)]
        )
    }

    /// A generic, schema-hinted prompt. Concrete per-type prompts arrive in
    /// HSM-6-02/03; this is enough to drive any `ILLMProvider` through the seam.
    public static func defaultPrompt(_ type: ArtifactType, _ transcript: Transcript) -> String {
        let body = transcript.segments
            .map { "\($0.speaker): \($0.text)" }
            .joined(separator: "\n")
        return """
        You are HoldSpeak's meeting-intelligence engine. From the transcript below,
        produce a single "\(type.rawValue)" artifact.

        Return ONLY a JSON object with these keys:
          "title": a short headline,
          "body_markdown": the artifact written as Markdown,
          "structured_json": an object with the type-specific fields,
          "confidence": a number 0.0–1.0.

        Transcript:
        \(body)
        """
    }
}
