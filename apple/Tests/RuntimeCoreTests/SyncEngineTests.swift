import XCTest
import Contracts
import Providers
@testable import RuntimeCore

/// HSM-10-01 — the sync object model + engine. Host-testable end to end: a
/// change-set is produced from a seeded Phase-4 store and applied to an empty one
/// (directly and across a JSON "wire" via a fake provider), proving the Runtime
/// Core depends only on the `ISyncProvider`/`ISyncStore` seams.
final class SyncEngineTests: XCTestCase {

    struct Sample: Codable { let meeting: Meeting; let artifact: Artifact }

    private func fixture() throws -> Sample {
        var url = URL(fileURLWithPath: #filePath)
        for _ in 0..<4 { url.deleteLastPathComponent() }
        url.appendPathComponent("pm/roadmap/holdspeak-mobile/contracts/fixtures/meeting-sample.json")
        return try HoldSpeakContracts.decoder().decode(Sample.self, from: Data(contentsOf: url))
    }

    private func tempStore() throws -> SQLiteStorage {
        try SQLiteStorage(path: NSTemporaryDirectory() + "hsm-sync-\(UUID().uuidString).sqlite")
    }

    private let t0 = Date(timeIntervalSince1970: 1_700_000_000)   // whole seconds (ISO precision)

    /// A transport-free `ISyncProvider` that relays a change-set through real JSON —
    /// so push/pull exercises the wire encoding + schema-validating decode.
    final class JSONRelayProvider: ISyncProvider, @unchecked Sendable {
        private var stored = Data()
        func push(_ changeSet: ChangeSet) async throws {
            stored = try HoldSpeakContracts.encoder().encode(changeSet)
        }
        func pull() async throws -> ChangeSet {
            guard !stored.isEmpty else { return ChangeSet() }
            return try HoldSpeakContracts.decoder().decode(ChangeSet.self, from: stored)
        }
    }

    func testSnapshotApplyRoundTrip() throws {
        let s = try fixture()
        let a = try tempStore(); defer { a.close() }
        let b = try tempStore(); defer { b.close() }
        try a.saveMeeting(s.meeting, modifiedAt: t0)
        try a.saveArtifact(s.artifact, modifiedAt: t0)

        let engine = SyncEngine()
        try engine.apply(engine.snapshot(of: a), to: b)

        XCTAssertEqual(try b.loadMeeting(id: s.meeting.id), s.meeting)          // exact contract
        XCTAssertEqual(try b.loadArtifacts(meetingId: s.artifact.meetingId), [s.artifact])
        // last-modified is carried, not restamped.
        XCTAssertEqual(try b.allMeetings().first?.modifiedAt, t0)
    }

    func testRoundTripAcrossJSONProvider() async throws {
        let s = try fixture()
        let source = try tempStore(); defer { source.close() }
        let dest = try tempStore(); defer { dest.close() }
        try source.saveMeeting(s.meeting, modifiedAt: t0)
        try source.saveArtifact(s.artifact, modifiedAt: t0)

        let engine = SyncEngine()
        let relay = JSONRelayProvider()
        try await relay.push(engine.snapshot(of: source))      // source -> wire
        try engine.apply(try await relay.pull(), to: dest)     // wire -> dest

        XCTAssertEqual(try dest.loadMeeting(id: s.meeting.id), s.meeting)
        XCTAssertEqual(try dest.loadArtifacts(meetingId: s.artifact.meetingId), [s.artifact])
    }

    func testSyncFlowDependsOnlyOnProviderSeam() async throws {
        let s = try fixture()
        let store = try tempStore(); defer { store.close() }
        try store.saveMeeting(s.meeting, modifiedAt: t0)

        let engine = SyncEngine()
        // sync() pushes the local snapshot then applies whatever pull returns; with
        // a loopback relay that's the same set → store is unchanged + intact.
        try await engine.sync(local: store, via: JSONRelayProvider())
        XCTAssertEqual(try store.loadMeeting(id: s.meeting.id), s.meeting)
    }

    func testTombstonePropagatesDelete() throws {
        let s = try fixture()
        let a = try tempStore(); defer { a.close() }
        let b = try tempStore(); defer { b.close() }
        let engine = SyncEngine()

        try a.saveMeeting(s.meeting, modifiedAt: t0)
        try engine.apply(engine.snapshot(of: a), to: b)
        XCTAssertNotNil(try b.loadMeeting(id: s.meeting.id))

        try a.deleteMeeting(id: s.meeting.id, at: t0.addingTimeInterval(60))
        try engine.apply(engine.snapshot(of: a), to: b)

        XCTAssertNil(try b.loadMeeting(id: s.meeting.id))                       // gone
        XCTAssertEqual(try b.tombstones().map(\.id), [s.meeting.id])            // tombstone recorded
    }

    func testApplyIsIdempotent() throws {
        let s = try fixture()
        let a = try tempStore(); defer { a.close() }
        let b = try tempStore(); defer { b.close() }
        try a.saveMeeting(s.meeting, modifiedAt: t0)
        try a.saveArtifact(s.artifact, modifiedAt: t0)

        let engine = SyncEngine()
        let cs = try engine.snapshot(of: a)
        try engine.apply(cs, to: b)
        try engine.apply(cs, to: b)                                            // twice → no change

        XCTAssertEqual(try b.allMeetings().count, 1)
        XCTAssertEqual(try b.loadArtifacts(meetingId: s.artifact.meetingId), [s.artifact])
    }

    func testMalformedRecordSkippedAtWire() throws {
        // A live meeting record missing the required `id` — schema-invalid. The
        // safety property is unchanged: it must never reach the store. The
        // MECHANISM changed with the tolerant ChangeSet decode (the 2026-07-06
        // saga): the bad record is skipped and counted, not allowed to fail the
        // whole set (which is what turned one bad row into "Offline · queued").
        let bad = #"""
        {"meetings":[{"meta":{"id":"m1","kind":"meeting","last_modified":"2026-01-01T00:00:00Z","deleted":false},
         "value":{"started_at":"2026-01-01T00:00:00Z","tags":[],"segments":[],"bookmarks":[],
                  "intel_status":"none","mic_label":"m","remote_label":"r","devices":[]}}],"artifacts":[]}
        """#
        let set = try HoldSpeakContracts.decoder().decode(ChangeSet.self, from: Data(bad.utf8))
        XCTAssertEqual(set.meetings.count, 0)      // never reaches the store
        XCTAssertEqual(set.undecodedRecords, 1)    // and the skip is visible, not silent
    }
}
