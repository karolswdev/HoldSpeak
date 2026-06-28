import XCTest
import Contracts

/// HSM-18-01 — the dictation teleprompter's data decodes from the hub's REAL
/// `/api/dictation/dry-run` + `/api/dictation/readiness` JSON. The JSON below is the actual wire
/// shape produced by `_run_dictation_dry_run_text` (`holdspeak/web/routes/dictation/_helpers.py`)
/// and `api_dictation_readiness` (`.../pipeline.py`): `target` is `TargetProfile.to_dict()`
/// (`id`/`label`/`confidence`/`source`/`app_name`/`process_name`/`window_title`/`details`), NOT
/// the earlier guessed `app`/`window`/`process`/`profile`. snake_case -> camelCase via
/// `HoldSpeakContracts.decoder()`.
final class DictationClientTests: XCTestCase {

    // MARK: dry-run — the real `_run_dictation_dry_run_text` shape

    func testDryRunDecodesRealServerShape() throws {
        // A verbatim dry-run payload: `target` is the TargetProfile dict, `project` is an object,
        // `runtime_status`/`runtime_detail`/`blocks_count`/`suggestion_status`/`journal_id` ride
        // alongside the rewritten `final_text`. There is NO top-level `status`.
        let json = """
        {
          "project": {"name": "holdspeak", "root": "/Users/k/dev/holdspeak", "anchor": "git"},
          "target": {
            "id": "cursor", "label": "Cursor", "confidence": 0.78, "source": "hints",
            "app_name": "Cursor", "process_name": "Cursor", "window_title": "main.swift",
            "details": {"matched": "editor_app"}
          },
          "suggestion_status": "no_suggestion",
          "journal_id": 17,
          "learning": null,
          "runtime_status": "available",
          "runtime_detail": "mlx model present",
          "blocks_count": 2,
          "stages": [],
          "final_text": "Use Redis with a 24 hour TTL.",
          "total_elapsed_ms": 380.0,
          "warnings": ["model fallback"]
        }
        """.data(using: .utf8)!
        let dry = try HoldSpeakContracts.decoder().decode(DictationDryRun.self, from: json)
        XCTAssertEqual(dry.finalText, "Use Redis with a 24 hour TTL.")
        // target is the TargetProfile shape — app_name etc. populate now (they decoded to nil
        // against the old app/window/process model, the bug this audit fixed).
        XCTAssertEqual(dry.target?.id, "cursor")
        XCTAssertEqual(dry.target?.label, "Cursor")
        XCTAssertEqual(dry.target?.confidence, 0.78)
        XCTAssertEqual(dry.target?.source, "hints")
        XCTAssertEqual(dry.target?.appName, "Cursor")
        XCTAssertEqual(dry.target?.processName, "Cursor")
        XCTAssertEqual(dry.target?.windowTitle, "main.swift")
        XCTAssertEqual(dry.target?.details?["matched"], .string("editor_app"))
        XCTAssertEqual(dry.target?.displayLabel, "Cursor")     // the "-> Cursor" header
        // project is an object, not a string
        XCTAssertEqual(dry.project?.name, "holdspeak")
        XCTAssertEqual(dry.project?.root, "/Users/k/dev/holdspeak")
        XCTAssertEqual(dry.project?.anchor, "git")
        XCTAssertEqual(dry.runtimeStatus, "available")
        XCTAssertEqual(dry.runtimeDetail, "mlx model present")
        XCTAssertEqual(dry.blocksCount, 2)
        XCTAssertEqual(dry.suggestionStatus, "no_suggestion")
        XCTAssertEqual(dry.journalId, 17)
        XCTAssertEqual(dry.warnings, ["model fallback"])
        XCTAssertEqual(dry.totalElapsedMs, 380)
    }

    /// An "unknown" target (the `_profile("unknown", 0.0, ...)` path) with no usable name has no
    /// destination — the header shows nothing rather than the literal "unknown".
    func testDryRunUnknownTargetHasNoDestinationLabel() throws {
        let json = """
        {"final_text": "hi",
         "target": {"id": "unknown", "confidence": 0.0, "source": "none",
                    "app_name": null, "process_name": null, "window_title": null, "details": {}}}
        """.data(using: .utf8)!
        let dry = try HoldSpeakContracts.decoder().decode(DictationDryRun.self, from: json)
        XCTAssertEqual(dry.target?.id, "unknown")
        // no label, no app/window/process, and the id is "unknown" -> nothing to show.
        XCTAssertNil(dry.target?.displayLabel)
    }

    /// A disabled-pipeline dry-run returns no `target`/`blocks_count` extras; only `final_text` is
    /// guaranteed. It must still decode, not throw.
    func testDryRunToleratesMinimalPayload() throws {
        let json = #"{"final_text": "hello", "runtime_status": "disabled"}"#.data(using: .utf8)!
        let dry = try HoldSpeakContracts.decoder().decode(DictationDryRun.self, from: json)
        XCTAssertEqual(dry.finalText, "hello")
        XCTAssertEqual(dry.runtimeStatus, "disabled")
        XCTAssertNil(dry.target)
        XCTAssertNil(dry.project)
        XCTAssertNil(dry.target?.displayLabel)
    }

    // MARK: readiness — the real `api_dictation_readiness` shape

    func testReadinessDecodesRealServerShape() throws {
        // The real top-level: `ready` (the hub's verdict), `project`, `runtime` (model_exists lives
        // HERE, not top-level), and `target`. The earlier flat status/model_exists/runtime_status/
        // openai_compatible model decoded none of this.
        let json = """
        {
          "ready": true,
          "project": {"name": "holdspeak", "root": "/Users/k/dev/holdspeak", "anchor": "git"},
          "config": {"pipeline_enabled": true, "backend": "mlx"},
          "runtime": {
            "status": "available", "requested_backend": "mlx", "resolved_backend": "mlx",
            "detail": "model present", "model_exists": true
          },
          "target": {
            "id": "claude_code", "label": "Claude Code", "confidence": 0.92, "source": "hints",
            "app_name": "Terminal", "process_name": "claude", "window_title": null,
            "details": {"matched": "claude"}
          },
          "warnings": []
        }
        """.data(using: .utf8)!
        let r = try HoldSpeakContracts.decoder().decode(DictationReadiness.self, from: json)
        XCTAssertTrue(r.isReady)
        XCTAssertEqual(r.ready, true)
        XCTAssertEqual(r.project?.name, "holdspeak")
        XCTAssertEqual(r.runtime?.status, "available")
        XCTAssertEqual(r.runtime?.modelExists, true)
        XCTAssertEqual(r.runtime?.requestedBackend, "mlx")
        XCTAssertEqual(r.runtime?.resolvedBackend, "mlx")
        XCTAssertEqual(r.target?.id, "claude_code")
        XCTAssertEqual(r.target?.displayLabel, "Claude Code")
    }

    func testReadinessNotReadyWhenRuntimeUnavailable() throws {
        // ready:false + an unavailable runtime -> not ready, and isReady honors the hub verdict.
        let json = """
        {"ready": false, "project": null,
         "runtime": {"status": "missing_model", "model_exists": false}}
        """.data(using: .utf8)!
        let r = try HoldSpeakContracts.decoder().decode(DictationReadiness.self, from: json)
        XCTAssertFalse(r.isReady)
        XCTAssertEqual(r.runtime?.modelExists, false)
        XCTAssertNil(r.project)
    }

    /// With no `ready` field, isReady falls back to "the runtime is available".
    func testReadinessFallsBackToRuntimeStatusWhenNoVerdict() throws {
        let json = #"{"runtime": {"status": "available", "model_exists": true}}"#.data(using: .utf8)!
        let r = try HoldSpeakContracts.decoder().decode(DictationReadiness.self, from: json)
        XCTAssertNil(r.ready)
        XCTAssertTrue(r.isReady)
    }
}
