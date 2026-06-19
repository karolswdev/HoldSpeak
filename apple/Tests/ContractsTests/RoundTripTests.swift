import XCTest
@testable import Contracts

/// HSM-1-02: the Swift Contracts types decode the Phase-0 golden conformance
/// fixtures and round-trip through Swift Codable. The fixtures are the single
/// canonical set under pm/roadmap/holdspeak-mobile/contracts/fixtures — the same
/// payloads the Python-side validator checks, so both runtimes test one source.
final class RoundTripTests: XCTestCase {

    // Wrappers matching the fixture files' top-level keys.
    struct MeetingSample: Codable {
        let meeting: Meeting
        let artifact: Artifact
        let intelJob: IntelJob
    }
    struct MirSample: Codable {
        let actuatorProposal: ActuatorProposal
        let intentWindowBalanced: IntentWindow
        let intentWindowArchitect: IntentWindow
    }

    /// Repo-root-relative path to the Phase-0 fixtures, anchored on this file.
    private func fixturesDir() -> URL {
        var url = URL(fileURLWithPath: #filePath)
        for _ in 0..<4 { url.deleteLastPathComponent() }  // ...ContractsTests/Tests/apple/<repo>
        return url.appendingPathComponent("pm/roadmap/holdspeak-mobile/contracts/fixtures")
    }

    private func load(_ name: String) throws -> Data {
        try Data(contentsOf: fixturesDir().appendingPathComponent(name))
    }

    func testDecodeMeetingSample() throws {
        let s = try HoldSpeakContracts.decoder().decode(
            MeetingSample.self, from: load("meeting-sample.json"))

        XCTAssertEqual(s.meeting.id, "mtg_001")
        XCTAssertEqual(s.meeting.segments.count, 1)
        XCTAssertEqual(s.meeting.segments.first?.speaker, "Karol")
        XCTAssertEqual(s.meeting.intelStatus.state, "ready")          // nested intel_status
        XCTAssertNil(s.meeting.mirProfile)                            // not a Meeting field
        XCTAssertEqual(s.meeting.intel?.actionItems.first?.status, .pending)
        XCTAssertEqual(s.meeting.intel?.actionItems.first?.id.count, 12)  // content-hash id

        XCTAssertEqual(s.artifact.artifactType, .decisions)          // tagged-union discriminator
        XCTAssertEqual(s.artifact.status, .draft)
        XCTAssertNil(s.artifact.createdAt)                           // draft omits it

        XCTAssertEqual(s.intelJob.status, "ready")
        XCTAssertEqual(s.intelJob.attempts, 1)
    }

    func testMeetingRoundTripsThroughSwiftCodable() throws {
        let dec = HoldSpeakContracts.decoder()
        let enc = HoldSpeakContracts.encoder()
        let original = try dec.decode(MeetingSample.self, from: load("meeting-sample.json"))

        // encode -> decode -> equal: the typed round-trip the contract promises.
        let reencoded = try enc.encode(original.meeting)
        let again = try dec.decode(Meeting.self, from: reencoded)
        XCTAssertEqual(original.meeting, again)

        let artAgain = try dec.decode(Artifact.self, from: enc.encode(original.artifact))
        XCTAssertEqual(original.artifact, artAgain)
    }

    func testInstantsEncodeAsUTCZ() throws {
        let s = try HoldSpeakContracts.decoder().decode(
            MeetingSample.self, from: load("meeting-sample.json"))
        let json = String(data: try HoldSpeakContracts.encoder().encode(s.meeting), encoding: .utf8)!
        XCTAssertTrue(json.contains("\"started_at\":\"2026-06-18T09:00:00Z\""),
                      "instants must encode as UTC Z (contract §2)")
    }

    func testMIRProfileDimension() throws {
        let s = try HoldSpeakContracts.decoder().decode(
            MirSample.self, from: load("mir-and-actuator-sample.json"))
        XCTAssertEqual(s.intentWindowBalanced.profile, .balanced)
        XCTAssertEqual(s.intentWindowArchitect.profile, .architect)
        XCTAssertNotEqual(s.intentWindowBalanced.profile, s.intentWindowArchitect.profile)
        XCTAssertEqual(s.intentWindowBalanced.activeIntents, [.architecture])
    }

    func testActuatorProposal() throws {
        let s = try HoldSpeakContracts.decoder().decode(
            MirSample.self, from: load("mir-and-actuator-sample.json"))
        XCTAssertEqual(s.actuatorProposal.status, .proposed)
        XCTAssertEqual(s.actuatorProposal.target, "github")
        XCTAssertEqual(s.actuatorProposal.requiredCapabilities, ["github:write"])
        XCTAssertFalse(s.actuatorProposal.reversible)
    }
}
