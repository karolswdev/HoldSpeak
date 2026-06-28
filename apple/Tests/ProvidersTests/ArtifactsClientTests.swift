import XCTest
@testable import Contracts

// EQ-W3 (iOS artifacts) — decode round-trip for the `GET /api/meetings/{id}/artifacts`
// response. The load-bearing assertions: `confidence` and `sources` decode (the two
// fields the iPad render currently drops), plus the type/title/body/status the
// SwiftUI screen already shows. The JSON literal mirrors the exact shape
// holdspeak/web/routes/meetings.py::api_get_meeting_artifacts returns.
//
// METAL-READINESS (EQ-W6 audit): the `created_at`/`updated_at` literals use the REAL
// wire shape — the route emits `artifact.created_at.isoformat()` where the value was
// loaded via `datetime.fromisoformat(...)` from a DB string written by
// `datetime.now().isoformat()`: naive/local, microseconds, NO `Z`. The contract
// decoded these as `Date` via the shared `.iso8601` strategy, which THROWS on a
// zone-less string — failing the whole artifact decode on real metal. Now carried as
// raw `String?`.
final class ArtifactsClientTests: XCTestCase {

    private static let envelopeJSON = """
    {
      "meeting_id": "mtg-2026-06-27-a",
      "artifacts": [
        {
          "id": "art-001",
          "meeting_id": "mtg-2026-06-27-a",
          "artifact_type": "decisions",
          "title": "Decisions",
          "body_markdown": "## Decisions\\n- Ship EQ-W3 client slices in parallel worktrees.",
          "structured_json": {"decisions": ["ship the equilibrium wave"]},
          "confidence": 0.82,
          "status": "needs_review",
          "plugin_id": "decisions.core",
          "plugin_version": "1.0.0",
          "sources": [
            {"source_type": "intent_window", "source_ref": "win-7"},
            {"source_type": "plugin_run", "source_ref": "run-42"}
          ],
          "created_at": "2026-06-27T10:00:00.123456",
          "updated_at": "2026-06-27T10:05:00.654321"
        }
      ]
    }
    """

    func testDecodesEnvelopeWithConfidenceAndSources() throws {
        let data = Data(Self.envelopeJSON.utf8)
        let envelope = try HoldSpeakContracts.decoder()
            .decode(MeetingArtifactsEnvelope.self, from: data)

        XCTAssertEqual(envelope.meetingId, "mtg-2026-06-27-a")
        XCTAssertEqual(envelope.artifacts.count, 1)

        let artifact = try XCTUnwrap(envelope.artifacts.first)
        XCTAssertEqual(artifact.id, "art-001")
        XCTAssertEqual(artifact.meetingId, "mtg-2026-06-27-a")
        XCTAssertEqual(artifact.artifactType, "decisions")
        XCTAssertEqual(artifact.title, "Decisions")
        XCTAssertTrue(artifact.bodyMarkdown.contains("Ship EQ-W3"))
        XCTAssertEqual(artifact.status, "needs_review")
        XCTAssertEqual(artifact.pluginId, "decisions.core")

        // The audit fix — confidence decodes (and is the right value).
        XCTAssertEqual(try XCTUnwrap(artifact.confidence), 0.82, accuracy: 0.0001)

        // The audit fix — the provenance list decodes with snake_case keys mapped.
        XCTAssertEqual(artifact.sources.count, 2)
        XCTAssertEqual(artifact.sources[0].sourceType, "intent_window")
        XCTAssertEqual(artifact.sources[0].sourceRef, "win-7")
        XCTAssertEqual(artifact.sources[1].sourceType, "plugin_run")
        XCTAssertEqual(artifact.sources[1].sourceRef, "run-42")

        // Real naive/no-`Z` timestamps carried verbatim (they threw as `Date` before).
        XCTAssertEqual(artifact.createdAt, "2026-06-27T10:00:00.123456")
        XCTAssertEqual(artifact.updatedAt, "2026-06-27T10:05:00.654321")
    }

    /// `confidence` is `Double?` per the slice spec: an artifact without it still
    /// decodes (the iPad render must tolerate its absence), and `sources` defaults
    /// to empty when omitted is NOT allowed by the route — but a present-empty list
    /// decodes cleanly.
    func testConfidenceIsOptionalAndEmptySourcesDecode() throws {
        let json = """
        {
          "meeting_id": "m1",
          "artifacts": [
            {
              "id": "a1",
              "meeting_id": "m1",
              "artifact_type": "action_items",
              "title": "Action Items",
              "body_markdown": "- do the thing",
              "structured_json": {},
              "confidence": null,
              "status": "draft",
              "plugin_id": "action_items.core",
              "plugin_version": "1.0.0",
              "sources": [],
              "created_at": "2026-06-27T11:00:00.000000",
              "updated_at": "2026-06-27T11:00:00.000000"
            }
          ]
        }
        """
        let envelope = try HoldSpeakContracts.decoder()
            .decode(MeetingArtifactsEnvelope.self, from: Data(json.utf8))
        let artifact = try XCTUnwrap(envelope.artifacts.first)
        XCTAssertNil(artifact.confidence)
        XCTAssertTrue(artifact.sources.isEmpty)
        XCTAssertEqual(artifact.artifactType, "action_items")
    }
}
