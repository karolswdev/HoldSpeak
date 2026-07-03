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
        XCTAssertEqual(s.artifact.origin, "meeting")                 // v6, explicit on the wire
        XCTAssertFalse(s.artifact.isRunBorn)

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

    /// HSM-18-07: `origin` ("meeting" | "run", v6) decodes when present and the
    /// run-born derivation matches the hub's own (`plugins.py`: no meeting
    /// anchor ⇒ run-born) when the wire omits it — an older hub, a client push.
    func testArtifactOriginDecodesAndDerivesRunBorn() throws {
        let dec = HoldSpeakContracts.decoder()

        func artifactJSON(meetingId: String, origin: String?) -> Data {
            var fields = [
                "\"id\":\"a1\"", "\"meeting_id\":\"\(meetingId)\"",
                "\"artifact_type\":\"plugin_output\"", "\"title\":\"t\"",
                "\"body_markdown\":\"b\"", "\"structured_json\":{}",
                "\"confidence\":0.5", "\"status\":\"draft\"",
                "\"plugin_id\":\"p\"", "\"plugin_version\":\"1\"", "\"sources\":[]",
            ]
            if let origin { fields.append("\"origin\":\"\(origin)\"") }
            return Data("{\(fields.joined(separator: ","))}".utf8)
        }

        // Explicit on the wire — the hub always emits it now.
        let run = try dec.decode(Artifact.self, from: artifactJSON(meetingId: "", origin: "run"))
        XCTAssertEqual(run.origin, "run")
        XCTAssertTrue(run.isRunBorn)

        let anchored = try dec.decode(Artifact.self, from: artifactJSON(meetingId: "m1", origin: "meeting"))
        XCTAssertFalse(anchored.isRunBorn)

        // Absent — tolerated, derived from the meeting anchor.
        let bareRun = try dec.decode(Artifact.self, from: artifactJSON(meetingId: "", origin: nil))
        XCTAssertNil(bareRun.origin)
        XCTAssertTrue(bareRun.isRunBorn)

        let bareAnchored = try dec.decode(Artifact.self, from: artifactJSON(meetingId: "m1", origin: nil))
        XCTAssertFalse(bareAnchored.isRunBorn)

        // An unknown raw value never fails the decode (tolerant String?).
        let odd = try dec.decode(Artifact.self, from: artifactJSON(meetingId: "m1", origin: "weird"))
        XCTAssertEqual(odd.origin, "weird")
        XCTAssertFalse(odd.isRunBorn)
    }

    /// LIVE SYNC (THE PRIMITIVE FRAMEWORK, wave 2): a full-kind `ChangeSet` — the exact
    /// payload the desk's snapshot pushes to `/api/sync/push` — round-trips byte-stable
    /// through the contract coder across all seven kinds, snake_case on the wire, with a
    /// tombstone carrying no value. This is the wire contract the desk-backed store builds.
    func testFullKindChangeSetRoundTrips() throws {
        let enc = HoldSpeakContracts.encoder()
        let dec = HoldSpeakContracts.decoder()
        let now = Date(timeIntervalSince1970: 1_700_000_000)

        let cs = ChangeSet(
            artifacts: [Synced<Artifact>.live(
                Artifact(id: "a1", meetingId: "", artifactType: .pluginOutput, title: "Out",
                         bodyMarkdown: "body", structuredJson: .object(["lens": .string("Agent")]),
                         confidence: 1, status: .draft, pluginId: "ipad.desk", pluginVersion: "0",
                         sources: [], createdAt: now, updatedAt: now),
                id: "a1", kind: .artifact, modifiedAt: now)],
            notes: [Synced<Note>.live(Note(id: "n1", title: "T", bodyMarkdown: "B", tags: ["x"],
                                           createdAt: now, updatedAt: now), id: "n1", kind: .note, modifiedAt: now),
                    Synced<Note>.tombstone(id: "n2", kind: .note, at: now)],
            kbs: [Synced<KB>.live(KB(id: "k1", name: "Knowledge", memberIds: ["n1"], createdAt: now, updatedAt: now),
                                  id: "k1", kind: .kb, modifiedAt: now)],
            agents: [Synced<Agent>.live(Agent(id: "ag1", name: "Scout", avatar: "p1", role: "r",
                                              systemPrompt: "sp", userTemplate: "{input}", createdAt: now, updatedAt: now),
                                        id: "ag1", kind: .agent, modifiedAt: now)],
            chains: [Synced<Chain>.live(Chain(id: "c1", name: "Crew", steps: ["ag1"], createdAt: now, updatedAt: now),
                                        id: "c1", kind: .chain, modifiedAt: now)],
            workflows: [Synced<WorkflowDefinition>.live(
                WorkflowDefinition(id: "w1", name: "Saved Ask", prompt: "do x", createdAt: now, updatedAt: now),
                id: "w1", kind: .workflow, modifiedAt: now)])

        let data = try enc.encode(cs)
        let json = String(data: data, encoding: .utf8)!
        XCTAssertTrue(json.contains("body_markdown"))   // snake_case on the wire
        XCTAssertTrue(json.contains("last_modified"))   // the envelope's one-truth instant
        XCTAssertTrue(json.contains("\"deleted\":true"))// the tombstone

        let back = try dec.decode(ChangeSet.self, from: data)
        XCTAssertEqual(back, cs)                         // byte-stable round-trip
        XCTAssertEqual(back.count, 7)
        XCTAssertNil(back.notes.first { $0.meta.id == "n2" }?.value)   // tombstone carries no payload
        XCTAssertEqual(back.agents.first?.value?.name, "Scout")
    }

    /// WAVE 4 (the Directory): a `ChangeSet` carrying directories (the iPad zone's identity +
    /// nesting) + membership edges round-trips byte-stable through the contract coder. The
    /// directory shape is identity-only (no geometry/paint keys on the wire); `parent_id` carries
    /// the nesting; a membership edge maps a primitive to its home directory; deletes are
    /// tombstones with no payload.
    func testDirectoryAndMembershipRoundTrip() throws {
        let enc = HoldSpeakContracts.encoder()
        let dec = HoldSpeakContracts.decoder()
        let now = Date(timeIntervalSince1970: 1_700_000_000)

        let cs = ChangeSet(
            directories: [
                Synced<Directory>.live(Directory(id: "Atlas", name: "Atlas", parentId: nil,
                                                 createdAt: now, updatedAt: now),
                                       id: "Atlas", kind: .directory, modifiedAt: now),
                Synced<Directory>.live(Directory(id: "Atlas/Q3", name: "Q3", parentId: "Atlas",
                                                 createdAt: now, updatedAt: now),
                                       id: "Atlas/Q3", kind: .directory, modifiedAt: now),
                Synced<Directory>.tombstone(id: "Old", kind: .directory, at: now)],
            directoryMemberships: [
                Synced<Membership>.live(Membership(primitiveId: "note:n1", directoryId: "Atlas", updatedAt: now),
                                        id: "note:n1", kind: .membership, modifiedAt: now)])

        let data = try enc.encode(cs)
        let json = String(data: data, encoding: .utf8)!
        XCTAssertTrue(json.contains("parent_id"))        // nesting, snake_case on the wire
        XCTAssertTrue(json.contains("directory_id"))     // the membership edge
        XCTAssertTrue(json.contains("primitive_id"))
        XCTAssertFalse(json.contains("\"cx\""))          // geometry NEVER crosses the wire
        XCTAssertFalse(json.contains("glow"))            // paint NEVER crosses the wire

        let back = try dec.decode(ChangeSet.self, from: data)
        XCTAssertEqual(back, cs)                          // byte-stable round-trip
        XCTAssertEqual(back.count, 4)                     // 3 directories + 1 membership
        XCTAssertEqual(back.directories.first { $0.meta.id == "Atlas/Q3" }?.value?.parentId, "Atlas")
        XCTAssertNil(back.directories.first { $0.meta.id == "Atlas" }?.value?.parentId)
        XCTAssertNil(back.directories.first { $0.meta.id == "Old" }?.value)   // tombstone, no payload
        XCTAssertEqual(back.directoryMemberships.first?.value?.directoryId, "Atlas")
    }
}
