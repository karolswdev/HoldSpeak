import XCTest
import Contracts
import Providers
@testable import RuntimeCore

/// HSM-6-02 — the five core artifact types. Substance checks (presence/coverage),
/// never exact-string assertions: the model phrases differently every run.
final class CoreArtifactsTests: XCTestCase {

    final class StubLLM: ILLMProvider, @unchecked Sendable {
        let byKeyword: [String: String]
        let fallback: String
        init(byKeyword: [String: String] = [:], fallback: String = "[]") {
            self.byKeyword = byKeyword; self.fallback = fallback
        }
        func complete(prompt: String) async throws -> String {
            for (kw, resp) in byKeyword where prompt.contains(kw) { return resp }
            return fallback
        }
    }

    private let fixedDate = Date(timeIntervalSince1970: 1_700_000_000)

    private func transcript() -> Transcript {
        Transcript(
            meetingId: "m-7",
            segments: [
                Segment(text: "We will ship the API on Friday.", speaker: "Ada", startTime: 10, endTime: 13),
                Segment(text: "Risk: the vendor key expires next week.", speaker: "Lin", startTime: 13, endTime: 17),
            ],
            transcriptHash: "sha256:cafe")
    }

    private func gen(_ stub: StubLLM) -> CoreArtifactGenerator {
        let date = fixedDate   // capture the value, not self, for the @Sendable clock
        return CoreArtifactGenerator(provider: stub, now: { date })
    }

    // Action items: structured_json validates as [ActionItem]; lifecycle stamped.
    func testActionItemsAreTypedAndStamped() async throws {
        let stub = StubLLM(byKeyword: ["ACTION ITEMS":
            #"[{"task":"Ship the API","owner":"Ada","due":"Friday","source_timestamp":10}]"#])
        let artifact = try await gen(stub).generateActionItems(from: transcript())

        XCTAssertEqual(artifact.artifactType, .actionItems)
        XCTAssertEqual(artifact.status, .draft)
        // structured_json round-trips back to the typed contract with zero errors.
        let data = try HoldSpeakContracts.encoder().encode(artifact.structuredJson)
        let items = try HoldSpeakContracts.decoder().decode([ActionItem].self, from: data)
        XCTAssertEqual(items.count, 1)
        XCTAssertEqual(items[0].task, "Ship the API")        // substance: the committed task
        XCTAssertEqual(items[0].status, .pending)            // engine-stamped lifecycle
        XCTAssertEqual(items[0].reviewState, .pending)
        XCTAssertEqual(items[0].sourceTimestamp, 10)         // provenance to the transcript moment
        XCTAssertEqual(items[0].id, CoreArtifactGenerator.actionItemID(task: "Ship the API", owner: "Ada"))
    }

    // Empty input → empty set, never a hallucinated one.
    func testNoInstancesYieldsEmptySet() async throws {
        let artifact = try await gen(StubLLM(fallback: "[]")).generateActionItems(from: transcript())
        let data = try HoldSpeakContracts.encoder().encode(artifact.structuredJson)
        let items = try HoldSpeakContracts.decoder().decode([ActionItem].self, from: data)
        XCTAssertTrue(items.isEmpty)
    }

    // Decisions/Risks/Requirements: schema-valid Artifact envelope with the right type.
    func testOpenBlobCoreTypesValidate() async throws {
        let resp = #"{"title":"Decisions","body_markdown":"- Ship Friday","structured_json":{"items":[{"decision":"Ship the API Friday"}]},"confidence":0.7}"#
        for type in [ArtifactType.decisions, .riskRegister, .requirements] {
            let artifact = try await gen(StubLLM(fallback: resp)).generate(type, from: transcript())
            XCTAssertEqual(artifact.artifactType, type)
            XCTAssertEqual(artifact.status, .draft)
            XCTAssertEqual(artifact.sources.first?.sourceRef, "sha256:cafe")  // provenance
            // The envelope round-trips through the contract coder unchanged.
            let data = try HoldSpeakContracts.encoder().encode(artifact)
            XCTAssertEqual(try HoldSpeakContracts.decoder().decode(Artifact.self, from: data), artifact)
        }
    }

    // Summary → IntelSnapshot (the contract home; no fake `summary` artifact type).
    func testSummaryIsIntelSnapshot() async throws {
        let stub = StubLLM(byKeyword: ["Summarize":
            #"{"summary":"The team agreed to ship the API Friday.","topics":["release","vendor key"]}"#])
        let snap = try await gen(stub).generateSummary(from: transcript())
        XCTAssertFalse(snap.summary.isEmpty)
        XCTAssertEqual(snap.topics, ["release", "vendor key"])
        XCTAssertEqual(snap.timestamp, fixedDate.timeIntervalSince1970, accuracy: 0.001)
        // Schema-valid against the IntelSnapshot contract.
        let data = try HoldSpeakContracts.encoder().encode(snap)
        XCTAssertEqual(try HoldSpeakContracts.decoder().decode(IntelSnapshot.self, from: data), snap)
    }

    // The non-core-type guard holds (only the four are core artifact types).
    func testCoreArtifactTypeSet() {
        XCTAssertEqual(CoreArtifactGenerator.coreArtifactTypes,
                       [.actionItems, .decisions, .riskRegister, .requirements])
    }
}
