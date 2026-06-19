import XCTest
import Contracts
import Providers
@testable import RuntimeCore

/// HSM-6-03 (ADR half) — ADR Candidates as an open-blob `Artifact(.adr)`. Substance
/// checks (an architectural decision is captured; none is invented), not strings.
/// (Follow-ups are deferred — the contract has no follow-up `artifact_type`; HSM-6-06.)
final class ADRCandidatesTests: XCTestCase {

    final class FixedLLM: ILLMProvider, @unchecked Sendable {
        let response: String
        init(_ response: String) { self.response = response }
        func complete(prompt: String) async throws -> String { response }
    }

    struct ADRPayload: Decodable { let candidates: [ADRCandidate] }
    struct ADRCandidate: Decodable { let title: String; let sourceTimestamp: Double? }

    private func transcript(_ segments: [Segment]) -> Transcript {
        Transcript(meetingId: "m-adr", segments: segments, transcriptHash: "sha256:arch")
    }

    private func payload(_ artifact: Artifact) throws -> ADRPayload {
        let data = try HoldSpeakContracts.encoder().encode(artifact.structuredJson)
        return try HoldSpeakContracts.decoder().decode(ADRPayload.self, from: data)
    }

    // An architecture-review transcript → a schema-valid ADR artifact with provenance.
    func testADRCandidatesValidate() async throws {
        let resp = #"""
        {"title":"ADR: adopt event sourcing","body_markdown":"## Context\nWe debated state.",
         "structured_json":{"candidates":[{"title":"Adopt event sourcing","context":"audit needs",
         "decision":"use an append-only event log","consequences":"replay cost","source_timestamp":42}]},
         "confidence":0.8}
        """#
        let gen = CoreArtifactGenerator(provider: FixedLLM(resp))
        let artifact = try await gen.generateADRCandidates(from: transcript([
            Segment(text: "Should we use an event log for state?", speaker: "Ada", startTime: 40, endTime: 44),
            Segment(text: "Yes, append-only; we need the audit trail.", speaker: "Lin", startTime: 44, endTime: 48),
        ]))

        XCTAssertEqual(artifact.artifactType, .adr)
        XCTAssertEqual(artifact.status, .draft)                          // propose-only
        XCTAssertEqual(artifact.sources.first?.sourceRef, "sha256:arch") // provenance to the transcript

        let p = try payload(artifact)
        XCTAssertEqual(p.candidates.count, 1)                            // substance: a candidate present
        XCTAssertEqual(p.candidates[0].sourceTimestamp, 42)             // tied to the decision moment

        // The envelope round-trips through the contract coder unchanged.
        let data = try HoldSpeakContracts.encoder().encode(artifact)
        XCTAssertEqual(try HoldSpeakContracts.decoder().decode(Artifact.self, from: data), artifact)
    }

    // No architectural decision → no candidate (never fabricated).
    func testADRDoesNotFabricate() async throws {
        let resp = #"{"title":"ADR Candidates","body_markdown":"None.","structured_json":{"candidates":[]},"confidence":0.2}"#
        let gen = CoreArtifactGenerator(provider: FixedLLM(resp))
        let artifact = try await gen.generateADRCandidates(from: transcript([
            Segment(text: "Let's grab lunch at noon.", speaker: "Ada", startTime: 0, endTime: 2),
        ]))
        XCTAssertEqual(artifact.artifactType, .adr)
        XCTAssertTrue(try payload(artifact).candidates.isEmpty)
    }
}
