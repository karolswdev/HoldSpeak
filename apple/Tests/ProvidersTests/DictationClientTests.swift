import XCTest
import Contracts

/// HSM-18-01 — the dictation teleprompter's data decodes from the hub's real `/api/dictation/dry-run`
/// + `/api/dictation/readiness` JSON (snake_case wire -> camelCase via HoldSpeakContracts.decoder()).
final class DictationClientTests: XCTestCase {

    func testDryRunDecodesFinalTextAndDestination() throws {
        let json = """
        {
          "final_text": "Use Redis with a 24 hour TTL.",
          "target": { "app": "Cursor", "confidence": 0.91 },
          "warnings": ["model fallback"],
          "total_elapsed_ms": 380,
          "status": "ok",
          "blocks_count": 2,
          "project": "holdspeak"
        }
        """.data(using: .utf8)!
        let dry = try HoldSpeakContracts.decoder().decode(DictationDryRun.self, from: json)
        XCTAssertEqual(dry.finalText, "Use Redis with a 24 hour TTL.")
        XCTAssertEqual(dry.target?.label, "Cursor")          // the destination column header "-> Cursor"
        XCTAssertEqual(dry.target?.confidence, 0.91)
        XCTAssertEqual(dry.warnings, ["model fallback"])
        XCTAssertEqual(dry.totalElapsedMs, 380)
        XCTAssertEqual(dry.blocksCount, 2)
    }

    func testDryRunToleratesMissingOptionalFields() throws {
        // a minimal hub response (only final_text) must still decode, not throw
        let json = #"{"final_text": "hello"}"#.data(using: .utf8)!
        let dry = try HoldSpeakContracts.decoder().decode(DictationDryRun.self, from: json)
        XCTAssertEqual(dry.finalText, "hello")
        XCTAssertNil(dry.target)
        XCTAssertNil(dry.target?.label)
    }

    func testReadinessDecodesAndReportsReady() throws {
        let json = """
        { "status": "ready", "model_exists": true, "runtime_status": "ok", "openai_compatible": false }
        """.data(using: .utf8)!
        let r = try HoldSpeakContracts.decoder().decode(DictationReadiness.self, from: json)
        XCTAssertTrue(r.isReady)
        XCTAssertEqual(r.modelExists, true)
        XCTAssertEqual(r.runtimeStatus, "ok")
    }

    func testReadinessNotReadyWhenNoModelAndNoEndpoint() throws {
        let json = #"{"status": "incomplete", "model_exists": false, "openai_compatible": false}"#.data(using: .utf8)!
        let r = try HoldSpeakContracts.decoder().decode(DictationReadiness.self, from: json)
        XCTAssertFalse(r.isReady)
    }
}
