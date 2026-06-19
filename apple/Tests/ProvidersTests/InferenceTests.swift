import XCTest
import Contracts
@testable import Providers

/// HSM-5-03 (per-device LLM model policy) + HSM-5-04 (structured-output plumbing:
/// extract JSON from messy model text, decode through the contract, bounded
/// repair-retry). Host-testable; the engine pick + 30-min local gate are device.
final class InferenceTests: XCTestCase {

    // A fake ILLMProvider returning a preset sequence of responses.
    final class SequenceLLM: ILLMProvider, @unchecked Sendable {
        private let responses: [String]
        private var i = 0
        init(_ responses: [String]) { self.responses = responses }
        func complete(prompt: String) async throws -> String {
            defer { i += 1 }
            return responses[min(i, responses.count - 1)]
        }
    }

    private let validArtifact = """
    {"id":"a1","meeting_id":"m1","artifact_type":"decisions","title":"t",
     "body_markdown":"b","structured_json":{},"confidence":0.8,"status":"draft",
     "plugin_id":"p","plugin_version":"1","sources":[]}
    """

    func testPerDeviceModelDefaults() {
        XCTAssertEqual(InferenceModelPolicy.defaultModel(for: .iPhone), .fourB)   // charter
        XCTAssertEqual(InferenceModelPolicy.defaultModel(for: .iPad), .eightB)
    }

    func test12BPlusOnlyWhenPluggedIn() {
        XCTAssertFalse(InferenceModelPolicy.isAllowed(.twelveBPlus, pluggedIn: false))
        XCTAssertTrue(InferenceModelPolicy.isAllowed(.twelveBPlus, pluggedIn: true))
        XCTAssertTrue(InferenceModelPolicy.isAllowed(.fourB, pluggedIn: false))   // small always ok
        XCTAssertTrue(InferenceModelPolicy.isAllowed(.eightB, pluggedIn: false))
    }

    func testExtractJSONFromMessyText() {
        XCTAssertEqual(StructuredOutput.extractJSON(from: #"{"a":1}"#), #"{"a":1}"#)
        XCTAssertEqual(StructuredOutput.extractJSON(from: "Sure! {\"a\":1} done"), #"{"a":1}"#)
        XCTAssertEqual(StructuredOutput.extractJSON(from: "```json\n{\"a\":1}\n```"), #"{"a":1}"#)
        XCTAssertNil(StructuredOutput.extractJSON(from: "no json here"))
    }

    func testDecodeContractFromFencedOutput() throws {
        let fenced = "Here you go:\n```json\n\(validArtifact)\n```"
        let artifact = try StructuredOutput.decode(Artifact.self, from: fenced)
        XCTAssertEqual(artifact.artifactType, .decisions)
        XCTAssertEqual(artifact.status, .draft)
    }

    func testRepairRetrySucceedsOnSecondAttempt() async throws {
        let llm = SequenceLLM(["sorry, here's some prose with no json", validArtifact])
        let artifact = try await StructuredOutput.generate(Artifact.self,
                                                           prompt: "extract decisions",
                                                           using: llm, maxAttempts: 3)
        XCTAssertEqual(artifact.artifactType, .decisions)
    }

    func testRepairRetryExhausts() async {
        let llm = SequenceLLM(["nope", "still nope", "nope again"])
        do {
            _ = try await StructuredOutput.generate(Artifact.self, prompt: "x", using: llm, maxAttempts: 3)
            XCTFail("expected exhaustion")
        } catch {
            // expected: noJSON / exhausted
        }
    }
}
