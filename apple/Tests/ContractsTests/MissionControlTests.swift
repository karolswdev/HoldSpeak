import XCTest
@testable import Contracts

/// HSM-26-02: the DeskOS-belt + presence models decode the REAL Phase-87/88
/// wire shapes. The steering/rails samples are the SAME fixtures the Python
/// validator (`contracts/validate.py`) and the desktop fidelity test
/// (`test_steering_contracts_fidelity.py`) check — one source, three runners.
/// "Inherits, never redesigns": if the iPad cannot decode the real shape, it
/// fails here, not on glass.
final class MissionControlTests: XCTestCase {

    private func fixturesDir() -> URL {
        var url = URL(fileURLWithPath: #filePath)
        for _ in 0..<4 { url.deleteLastPathComponent() }
        return url.appendingPathComponent("pm/roadmap/holdspeak-mobile/contracts/fixtures")
    }

    private func decode<T: Decodable>(_ type: T.Type, from json: String) throws -> T {
        try HoldSpeakContracts.decoder().decode(T.self, from: Data(json.utf8))
    }

    // The steering + rails fixture, keyed like the on-disk sample.
    private struct SteeringSample: Decodable {
        let coderSessionPeek: CoderSessionPeek
        let coderSessionPeekNotModified: CoderSessionPeek
        let armingGrant: ArmingGrant
        let steerResultDelivered: SteerResult
        let steerResultRefused: SteerResult
        let steeringAuditEntry: SteeringAuditEntry
        let railsGroundingRef: RailsGroundingRef
        let railsJournalEntry: RailsJournalEntry
    }

    func testTheSteeringAndRailsFixtureDecodes() throws {
        let data = try Data(contentsOf: fixturesDir().appendingPathComponent("steering-and-rails-sample.json"))
        let sample = try HoldSpeakContracts.decoder().decode(SteeringSample.self, from: data)

        // Peek: the honest envelope + the content-hash gate.
        XCTAssertTrue(sample.coderSessionPeek.awaitingResponse)
        XCTAssertEqual(sample.coderSessionPeek.peek.status, "live")
        XCTAssertEqual(sample.coderSessionPeek.peek.lines?.count, 2)
        XCTAssertEqual(sample.coderSessionPeekNotModified.peek.status, "not_modified")
        XCTAssertFalse(sample.coderSessionPeekNotModified.grant.armed)

        // Grant: the pinned pane + the countdown.
        XCTAssertEqual(sample.armingGrant.paneId, "%5")
        XCTAssertEqual(sample.armingGrant.expiresInSeconds, 900)

        // Steer result: the consent grammar the surface reads from the shape.
        XCTAssertTrue(sample.steerResultDelivered.isDelivered)
        XCTAssertEqual(sample.steerResultRefused.status, "pane_mismatch")
        XCTAssertTrue(sample.steerResultRefused.didRevoke)  // re-offer ARM

        // Audit: the receipt (hash + head, never full text) + the refs.
        XCTAssertEqual(sample.steeringAuditEntry.outcome, "delivered")
        XCTAssertEqual(sample.steeringAuditEntry.grounding, ["rails:story:HS-88-05"])
        XCTAssertTrue(sample.steeringAuditEntry.ts.hasSuffix("Z"))  // §2: UTC-Z

        // Rails: the receipt ref + the journal note.
        XCTAssertEqual(sample.railsGroundingRef.kind, "story")
        XCTAssertEqual(sample.railsGroundingRef.id, "HS-88-05")
        XCTAssertTrue(sample.railsJournalEntry.bodyMarkdown.contains("rail event"))
    }

    func testBeltStateDecodesFromTheStateFeedShape() throws {
        // The real GET /api/missioncontrol/state shape (one live repo, its
        // current phase and stories, an awaiting-session-free feed).
        let json = """
        {
          "repos": [
            {
              "name": "delivery-workbench",
              "path": "/repos/dw",
              "status": "live",
              "feed": {
                "projects": [
                  {
                    "slug": "work-log-automation",
                    "prefix": "WLA",
                    "current_phase": {
                      "number": 16, "status": "closed",
                      "stories_done": 4, "stories_total": 4,
                      "title": "The flagship tree"
                    },
                    "next_story": null,
                    "stories": [
                      { "story_id": "WLA-16-01", "title": "First", "status": "done", "phase": 16, "evidence_exists": true }
                    ],
                    "warnings": 1
                  }
                ]
              }
            },
            { "name": "holdspeak", "path": "/repos/hs", "status": "unavailable", "detail": "no dw" }
          ]
        }
        """
        let state = try decode(BeltState.self, from: json)
        XCTAssertEqual(state.repos.count, 2)
        let live = state.repos[0]
        XCTAssertEqual(live.status, "live")
        let project = live.feed?.projects.first
        XCTAssertEqual(project?.slug, "work-log-automation")
        XCTAssertEqual(project?.currentPhase?.number, 16)
        XCTAssertEqual(project?.currentPhase?.storiesTotal, 4)   // stories_total → storiesTotal
        XCTAssertEqual(project?.stories.first?.storyId, "WLA-16-01")
        XCTAssertEqual(project?.stories.first?.evidenceExists, true)
        XCTAssertNil(project?.nextStory)
        // An unavailable repo carries its honest state, no feed.
        XCTAssertEqual(state.repos[1].status, "unavailable")
        XCTAssertNil(state.repos[1].feed)
    }

    func testARailsRefRoundTripsToTheWire() throws {
        let ref = RailsGroundingRef(repo: "holdspeak", project: "holdspeak", kind: "story", id: "HS-88-05")
        let data = try HoldSpeakContracts.encoder().encode(ref)
        let wire = String(decoding: data, as: UTF8.self)
        XCTAssertTrue(wire.contains("\"kind\":\"story\""))
        let back = try HoldSpeakContracts.decoder().decode(RailsGroundingRef.self, from: data)
        XCTAssertEqual(back, ref)
    }
}
