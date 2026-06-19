import XCTest
import Contracts
import Providers
@testable import RuntimeCore

/// HSM-10-03 — the conflict policy + idempotent round-trip, over a real SQLite
/// store. Host-testable + deterministic (fixed whole-second timestamps).
final class SyncConflictTests: XCTestCase {

    struct Sample: Codable { let meeting: Meeting; let artifact: Artifact }
    private func fixture() throws -> Sample {
        var url = URL(fileURLWithPath: #filePath)
        for _ in 0..<4 { url.deleteLastPathComponent() }
        url.appendPathComponent("pm/roadmap/holdspeak-mobile/contracts/fixtures/meeting-sample.json")
        return try HoldSpeakContracts.decoder().decode(Sample.self, from: Data(contentsOf: url))
    }
    private func tempStore() throws -> SQLiteStorage {
        try SQLiteStorage(path: NSTemporaryDirectory() + "hsm-cf-\(UUID().uuidString).sqlite")
    }
    private let t0 = Date(timeIntervalSince1970: 1_700_000_000)
    private var t1: Date { t0.addingTimeInterval(60) }
    private var t2: Date { t0.addingTimeInterval(120) }

    private func meeting(_ title: String) throws -> Meeting {
        var m = try fixture().meeting
        m.title = title
        return m
    }
    private func live(_ m: Meeting, at t: Date) -> ChangeSet {
        ChangeSet(meetings: [.live(m, id: m.id, kind: .meeting, modifiedAt: t)])
    }

    func testRoundTripIsIdempotent() throws {
        let s = try fixture()
        let a = try tempStore(); defer { a.close() }
        let b = try tempStore(); defer { b.close() }
        try a.saveMeeting(s.meeting, modifiedAt: t0)
        try a.saveArtifact(s.artifact, modifiedAt: t0)
        let engine = SyncEngine()
        let cs = try engine.snapshot(of: a)

        let first = try engine.apply(cs, to: b)
        XCTAssertEqual(first.applied, 2)

        let second = try engine.apply(cs, to: b)        // sync twice → no change
        XCTAssertEqual(second.applied, 0)
        XCTAssertFalse(second.changed)
        XCTAssertEqual(second.skipped, 2)
        XCTAssertEqual(try b.allMeetings().count, 1)
    }

    func testNewerWinsAndOlderIsSkipped() throws {
        let b = try tempStore(); defer { b.close() }
        let engine = SyncEngine()
        let m = try meeting("X")
        try b.saveMeeting(m, modifiedAt: t1)

        var newer = m; newer.title = "Y"
        XCTAssertEqual(try engine.apply(live(newer, at: t2), to: b).applied, 1)   // newer wins
        XCTAssertEqual(try b.loadMeeting(id: m.id)?.title, "Y")

        var older = m; older.title = "Z"
        let r = try engine.apply(live(older, at: t0), to: b)                      // older skipped
        XCTAssertEqual(r.skipped, 1)
        XCTAssertEqual(try b.loadMeeting(id: m.id)?.title, "Y")
    }

    func testConcurrentDivergenceSurfacedNonDestructively() throws {
        let b = try tempStore(); defer { b.close() }
        let engine = SyncEngine()
        let local = try meeting("LOCAL")
        try b.saveMeeting(local, modifiedAt: t0)

        var incoming = local; incoming.title = "REMOTE"        // same id + time, diverged
        let r = try engine.apply(live(incoming, at: t0), to: b)

        XCTAssertEqual(r.conflicts, [.init(kind: .meeting, id: local.id)])   // surfaced, not silent
        XCTAssertEqual(r.applied, 0)
        XCTAssertEqual(try b.loadMeeting(id: local.id)?.title, "LOCAL")      // local kept
    }

    func testTombstoneDoesNotResurrectOlderEdit() throws {
        let b = try tempStore(); defer { b.close() }
        let engine = SyncEngine()
        let m = try meeting("X")
        try b.saveMeeting(m, modifiedAt: t0)
        try b.deleteMeeting(id: m.id, at: t1)                  // tombstone at t1
        XCTAssertNil(try b.loadMeeting(id: m.id))

        // An older live re-create must NOT resurrect over a newer tombstone.
        let skip = try engine.apply(live(m, at: t0), to: b)
        XCTAssertEqual(skip.skipped, 1)
        XCTAssertNil(try b.loadMeeting(id: m.id))

        // A newer live re-create does resurrect.
        var revived = m; revived.title = "BACK"
        XCTAssertEqual(try engine.apply(live(revived, at: t2), to: b).applied, 1)
        XCTAssertEqual(try b.loadMeeting(id: m.id)?.title, "BACK")
    }
}
