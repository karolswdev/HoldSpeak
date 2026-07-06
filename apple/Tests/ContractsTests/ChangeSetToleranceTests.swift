import XCTest
@testable import Contracts

/// The 2026-07-06 connect-saga regression pins (defect #3): a single novel
/// artifact type on the wire (`run_output`) made the whole `/api/sync/pull`
/// ChangeSet undecodable, so every build since 1 showed "Offline · queued".
/// Two guarantees, tested separately:
/// 1. `run_output` is a KNOWN type now — those records decode whole.
/// 2. A type the app has never heard of drops THAT record, counted in
///    `undecodedRecords`, and the rest of the set survives.
final class ChangeSetToleranceTests: XCTestCase {

    private func changeSetJSON(artifactType: String) -> Data {
        """
        {
          "artifacts": [
            {
              "meta": {"id": "art_bad", "kind": "artifact",
                       "last_modified": "2026-07-06T12:00:00Z", "deleted": false},
              "value": {
                "id": "art_bad", "meeting_id": "", "artifact_type": "\(artifactType)",
                "title": "Recipe run", "body_markdown": "output text",
                "structured_json": {}, "confidence": 1.0, "status": "draft",
                "plugin_id": "recipe_run", "plugin_version": "1", "sources": [],
                "origin": "run"
              }
            },
            {
              "meta": {"id": "art_good", "kind": "artifact",
                       "last_modified": "2026-07-06T12:00:00Z", "deleted": false},
              "value": {
                "id": "art_good", "meeting_id": "mtg_001", "artifact_type": "decisions",
                "title": "Decisions", "body_markdown": "- ship it",
                "structured_json": {}, "confidence": 0.9, "status": "draft",
                "plugin_id": "core", "plugin_version": "1", "sources": []
              }
            }
          ],
          "notes": [
            {
              "meta": {"id": "n1", "kind": "note",
                       "last_modified": "2026-07-06T12:00:00Z", "deleted": false},
              "value": {"id": "n1", "title": "Survives", "body_markdown": "",
                        "tags": [], "created_at": "2026-07-06T12:00:00Z",
                        "updated_at": "2026-07-06T12:00:00Z"}
            }
          ]
        }
        """.data(using: .utf8)!
    }

    func testRunOutputIsAKnownArtifactType() throws {
        let set = try HoldSpeakContracts.decoder().decode(
            ChangeSet.self, from: changeSetJSON(artifactType: "run_output"))
        XCTAssertEqual(set.artifacts.count, 2)
        XCTAssertEqual(set.artifacts.first?.value?.artifactType, .runOutput)
        XCTAssertTrue(set.artifacts.first?.value?.isRunBorn ?? false)
        XCTAssertEqual(set.undecodedRecords, 0)
    }

    func testANovelTypeDropsOneRecordNotTheWholeSet() throws {
        let set = try HoldSpeakContracts.decoder().decode(
            ChangeSet.self, from: changeSetJSON(artifactType: "time_travel_log"))
        // The bad record is skipped and COUNTED; its siblings all land.
        XCTAssertEqual(set.artifacts.count, 1)
        XCTAssertEqual(set.artifacts.first?.value?.id, "art_good")
        XCTAssertEqual(set.notes.count, 1)
        XCTAssertEqual(set.undecodedRecords, 1)
    }

    func testCleanSetsReportZeroUndecoded() throws {
        let set = try HoldSpeakContracts.decoder().decode(
            ChangeSet.self, from: Data("{}".utf8))
        XCTAssertTrue(set.isEmpty)
        XCTAssertEqual(set.undecodedRecords, 0)
    }
}
