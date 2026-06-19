import XCTest
import Contracts
@testable import Providers

/// HSM-4-01 (SQLite store round-trips the Phase-0 contracts), HSM-4-02 (crash
/// recovery: committed survives, uncommitted rolls back, no corruption), HSM-4-03
/// (SCHEMA_VERSION = 1). All host-testable.
final class StorageTests: XCTestCase {

    struct Sample: Codable { let meeting: Meeting; let artifact: Artifact }

    private func fixture() throws -> Sample {
        var url = URL(fileURLWithPath: #filePath)
        for _ in 0..<4 { url.deleteLastPathComponent() }   // ...ProvidersTests/Tests/apple/<repo>
        url.appendPathComponent("pm/roadmap/holdspeak-mobile/contracts/fixtures/meeting-sample.json")
        return try HoldSpeakContracts.decoder().decode(Sample.self, from: Data(contentsOf: url))
    }

    private func tempPath() -> String {
        NSTemporaryDirectory() + "hsm-\(UUID().uuidString).sqlite"
    }

    func testMeetingRoundTripsThroughSQLite() throws {
        let s = try fixture()
        let db = try SQLiteStorage(path: tempPath()); defer { db.close() }
        try db.saveMeeting(s.meeting)
        XCTAssertEqual(try db.loadMeeting(id: s.meeting.id), s.meeting)   // exact contract back
        XCTAssertNil(try db.loadMeeting(id: "nope"))
    }

    func testArtifactStore() throws {
        let s = try fixture()
        let db = try SQLiteStorage(path: tempPath()); defer { db.close() }
        try db.saveArtifact(s.artifact)
        XCTAssertEqual(try db.loadArtifacts(meetingId: s.artifact.meetingId), [s.artifact])
        XCTAssertEqual(try db.loadArtifacts(meetingId: "other"), [])
    }

    func testSchemaVersionIsOne() throws {
        let db = try SQLiteStorage(path: tempPath()); defer { db.close() }
        XCTAssertEqual(try db.userVersion(), SQLiteStorage.schemaVersion)
        XCTAssertEqual(try db.userVersion(), 1)
    }

    /// Durability + no-corruption across an unclean shutdown: a committed write
    /// survives a connection that is abandoned WITHOUT close() (models a crash),
    /// and the reopened DB passes integrity_check.
    func testCrashRecoveryDurability() throws {
        let s = try fixture()
        let path = tempPath()
        do {
            let db = try SQLiteStorage(path: path)
            try db.saveMeeting(s.meeting)   // committed (autocommit); no open txn held
            // db goes out of scope unclosed -> models a crash after a committed write
        }
        let db2 = try SQLiteStorage(path: path); defer { db2.close() }
        XCTAssertEqual(try db2.loadMeeting(id: s.meeting.id), s.meeting)  // survived intact
        XCTAssertTrue(db2.integrityCheck())                               // not corrupt
    }

    /// Atomicity: an uncommitted write is rolled back (the mid-write half of crash
    /// safety — what a crash would discard).
    func testTransactionAtomicity() throws {
        let s = try fixture()
        let db = try SQLiteStorage(path: tempPath()); defer { db.close() }
        try db.saveMeeting(s.meeting)
        try db.begin()
        var pending = s.meeting
        pending.id = "mtg_pending"
        try db.saveMeeting(pending)
        try db.rollback()
        XCTAssertNotNil(try db.loadMeeting(id: s.meeting.id))   // committed kept
        XCTAssertNil(try db.loadMeeting(id: "mtg_pending"))     // uncommitted discarded
    }
}
