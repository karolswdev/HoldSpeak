import XCTest
import Contracts
import Providers
@testable import RuntimeCore

/// HSM-6-01 — the artifact-generation engine seam. Drives the engine with a fake
/// `ILLMProvider`: a well-formed draft must bind to a schema-valid Phase-0
/// `Artifact`; malformed model output must surface as a recoverable failure, not
/// a crash; and every emitted artifact must be a propose-only `.draft`.
final class ArtifactGenerationEngineTests: XCTestCase {

    /// A fake ILLMProvider returning a preset sequence of responses (one per call).
    final class SequenceLLM: ILLMProvider, @unchecked Sendable {
        private let responses: [String]
        private var i = 0
        init(_ responses: [String]) { self.responses = responses }
        func complete(prompt: String) async throws -> String {
            defer { i += 1 }
            return responses[min(i, responses.count - 1)]
        }
    }

    private func transcript() -> Transcript {
        Transcript(
            meetingId: "m-42",
            segments: [
                Segment(text: "Let's ship on June 30.", speaker: "Ada", startTime: 0, endTime: 3),
                Segment(text: "Agreed, June 30 it is.", speaker: "Lin", startTime: 3, endTime: 6),
            ],
            transcriptHash: "sha256:deadbeef")
    }

    private let goodDraft = """
    {"title":"Ship date confirmed",
     "body_markdown":"The team **decided** to ship on June 30.",
     "structured_json":{"decision":"ship June 30","owner":"Ada"},
     "confidence":0.9}
    """

    // Well-formed model output → a schema-valid Artifact with engine-stamped fields.
    func testEmitsSchemaValidArtifact() async throws {
        let engine = ArtifactGenerationEngine(
            provider: SequenceLLM([goodDraft]),
            idGenerator: { "artifact-1" })
        let artifact = try await engine.generate(.decisions, from: transcript())

        // Engine-stamped provenance (not the model's to invent).
        XCTAssertEqual(artifact.id, "artifact-1")
        XCTAssertEqual(artifact.meetingId, "m-42")
        XCTAssertEqual(artifact.artifactType, .decisions)
        XCTAssertEqual(artifact.status, .draft)              // propose-only
        XCTAssertEqual(artifact.pluginId, "holdspeak.mobile.intelligence")
        XCTAssertEqual(artifact.sources, [ArtifactSource(sourceType: "transcript", sourceRef: "sha256:deadbeef")])

        // Model's contribution survived the bind.
        XCTAssertEqual(artifact.title, "Ship date confirmed")
        XCTAssertEqual(artifact.confidence, 0.9, accuracy: 0.0001)

        // Schema validity: it round-trips through the contract coder unchanged.
        let data = try HoldSpeakContracts.encoder().encode(artifact)
        let decoded = try HoldSpeakContracts.decoder().decode(Artifact.self, from: data)
        XCTAssertEqual(decoded, artifact)
    }

    // Malformed (prose, no JSON) output → a thrown, recoverable error, no crash.
    func testMalformedOutputIsRecoverable() async {
        let engine = ArtifactGenerationEngine(
            provider: SequenceLLM(["Sorry, I can't help with that."]),
            maxAttempts: 2)
        do {
            _ = try await engine.generate(.decisions, from: transcript())
            XCTFail("expected a parse failure")
        } catch {
            XCTAssertTrue(error is StructuredOutputError)   // recoverable, surfaced as an error
        }
    }

    // Batch: one type's malformed response must not sink the others.
    func testBatchIsResilientPerType() async {
        // maxAttempts:1 → type[0] consumes the good draft, type[1] the prose.
        let engine = ArtifactGenerationEngine(
            provider: SequenceLLM([goodDraft, "no json here"]),
            maxAttempts: 1,
            idGenerator: { "id" })
        let results = await engine.generate(types: [.decisions, .actionItems], from: transcript())

        XCTAssertEqual(results.count, 2)
        guard case .success(let ok) = results[0].result else { return XCTFail("decisions should succeed") }
        XCTAssertEqual(ok.artifactType, .decisions)
        guard case .failure = results[1].result else { return XCTFail("action_items should fail recoverably") }
    }

    // Propose-only: nothing the engine emits is ever accepted/executed.
    func testNeverAutoAccepts() async throws {
        let engine = ArtifactGenerationEngine(provider: SequenceLLM([goodDraft]))
        let artifact = try await engine.generate(.requirements, from: transcript())
        XCTAssertNotEqual(artifact.status, .accepted)
        XCTAssertEqual(artifact.status, .draft)
    }
}
