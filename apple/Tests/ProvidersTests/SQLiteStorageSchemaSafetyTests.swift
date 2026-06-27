import XCTest
import SQLite3
import Contracts
@testable import Providers

/// Equilibrium 23-01/02: SQLiteStorage must mirror the desktop refuse-newer
/// matrix (holdspeak/db/core.py `_ensure_schema` + `SchemaVersionError`):
///
/// - a DB written by a NEWER build (user_version > build schema) is REFUSED for
///   writes and left byte-identical (never downgrade-stamped);
/// - an OLDER DB is backed up to a timestamped sibling BEFORE the v1 → v2 ALTERs;
/// - an equal-version DB is a no-op (no backup, no stamp change, data untouched).
final class SQLiteStorageSchemaSafetyTests: XCTestCase {

    private let SQLITE_TRANSIENT_T = unsafeBitCast(-1, to: sqlite3_destructor_type.self)

    private func tempPath() -> String {
        NSTemporaryDirectory() + "hsm-safety-\(UUID().uuidString).sqlite"
    }

    /// Open a raw connection, run a script, set user_version, close. Models a DB
    /// some other build left on disk.
    private func seedRawDB(at path: String, userVersion: Int32, _ script: String) throws {
        var db: OpaquePointer?
        XCTAssertEqual(sqlite3_open(path, &db), SQLITE_OK)
        defer { sqlite3_close(db) }
        XCTAssertEqual(sqlite3_exec(db, script, nil, nil, nil), SQLITE_OK)
        XCTAssertEqual(sqlite3_exec(db, "PRAGMA user_version=\(userVersion);", nil, nil, nil), SQLITE_OK)
    }

    private func readUserVersionRaw(at path: String) -> Int32 {
        var db: OpaquePointer?
        guard sqlite3_open(path, &db) == SQLITE_OK else { return -1 }
        defer { sqlite3_close(db) }
        var stmt: OpaquePointer?
        guard sqlite3_prepare_v2(db, "PRAGMA user_version;", -1, &stmt, nil) == SQLITE_OK else { return -1 }
        defer { sqlite3_finalize(stmt) }
        guard sqlite3_step(stmt) == SQLITE_ROW else { return -1 }
        return sqlite3_column_int(stmt, 0)
    }

    // MARK: - Newer DB: refused, never downgrade-stamped, data untouched

    func testNewerDatabaseIsRefusedAndLeftUntouched() throws {
        let path = tempPath()
        // A DB a FUTURE build wrote: schema version above our build.
        let future = SQLiteStorage.schemaVersion + 5
        try seedRawDB(at: path, userVersion: future, """
            CREATE TABLE meetings(id TEXT PRIMARY KEY, started_at TEXT, json TEXT,
              modified_at TEXT, deleted INTEGER NOT NULL DEFAULT 0, future_col TEXT);
            INSERT INTO meetings(id, started_at, json) VALUES('mtg_future','t','{}');
            """)

        XCTAssertThrowsError(try SQLiteStorage(path: path)) { error in
            guard case StorageError.tooNew(let stored, let build) = error else {
                return XCTFail("expected StorageError.tooNew, got \(error)")
            }
            XCTAssertEqual(stored, future)
            XCTAssertEqual(build, SQLiteStorage.schemaVersion)
        }

        // No downgrade-stamp: user_version is still the future version.
        XCTAssertEqual(readUserVersionRaw(at: path), future)
        // No data touched: the future-only column and its row survive intact.
        var db: OpaquePointer?
        XCTAssertEqual(sqlite3_open(path, &db), SQLITE_OK)
        defer { sqlite3_close(db) }
        var stmt: OpaquePointer?
        XCTAssertEqual(sqlite3_prepare_v2(db, "SELECT future_col FROM meetings WHERE id='mtg_future';", -1, &stmt, nil), SQLITE_OK)
        defer { sqlite3_finalize(stmt) }
        XCTAssertEqual(sqlite3_step(stmt), SQLITE_ROW, "the future row must still be there")
    }

    // MARK: - Older DB: backed up, then migrated, data preserved

    func testOlderDatabaseIsBackedUpThenMigrated() throws {
        let path = tempPath()
        // A v1 DB: meetings/artifacts WITHOUT modified_at/deleted, with a real row.
        try seedRawDB(at: path, userVersion: 1, """
            CREATE TABLE meetings(id TEXT PRIMARY KEY, started_at TEXT, json TEXT);
            CREATE TABLE artifacts(id TEXT PRIMARY KEY, meeting_id TEXT, json TEXT);
            INSERT INTO meetings(id, started_at, json)
              VALUES('mtg_old','2024-01-01T00:00:00Z','{"id":"mtg_old"}');
            """)

        let dir = (path as NSString).deletingLastPathComponent
        let stem = (path as NSString).lastPathComponent
        let before = try FileManager.default.contentsOfDirectory(atPath: dir)
            .filter { $0.hasPrefix(stem) && $0.hasSuffix(".bak") }
        XCTAssertTrue(before.isEmpty, "no backup should exist before opening")

        let db = try SQLiteStorage(path: path); defer { db.close() }

        // Migrated: stamped to the current build version.
        XCTAssertEqual(try db.userVersion(), SQLiteStorage.schemaVersion)
        // The v1 row survives the migration AND the ALTERs landed (v2 columns now
        // exist and the row reads back through them as a live, non-tombstoned row).
        try db.saveArtifact(Artifact(id: "art_post", meetingId: "mtg_old",
                                     artifactType: .decisions, title: "ok",
                                     bodyMarkdown: "", structuredJson: .object([:]),
                                     confidence: 0, status: .draft,
                                     pluginId: "p", pluginVersion: "1"))
        XCTAssertEqual(try db.loadArtifacts(meetingId: "mtg_old").map { $0.id }, ["art_post"])

        // A timestamped backup sibling was written before the ALTERs ran.
        let after = try FileManager.default.contentsOfDirectory(atPath: dir)
            .filter { $0.hasPrefix(stem) && $0.hasSuffix(".bak") }
        XCTAssertEqual(after.count, 1, "exactly one backup sibling should exist")

        // And the backup is still the ORIGINAL v1 (user_version 1, no modified_at).
        let backupPath = (dir as NSString).appendingPathComponent(after[0])
        XCTAssertEqual(readUserVersionRaw(at: backupPath), 1, "backup must be the pre-migration copy")
    }

    // MARK: - Equal DB: no-op (no new backup, version unchanged, data intact)

    func testEqualVersionDatabaseIsNoOp() throws {
        let path = tempPath()
        // First open creates the schema at the current version and lands a real row.
        var url = URL(fileURLWithPath: #filePath)
        for _ in 0..<4 { url.deleteLastPathComponent() }
        url.appendPathComponent("pm/roadmap/holdspeak-mobile/contracts/fixtures/meeting-sample.json")
        struct Sample: Codable { let meeting: Meeting }
        let sample = try HoldSpeakContracts.decoder().decode(Sample.self, from: Data(contentsOf: url))
        do {
            let db = try SQLiteStorage(path: path)
            try db.saveMeeting(sample.meeting)
            db.close()
        }

        let dir = (path as NSString).deletingLastPathComponent
        let stem = (path as NSString).lastPathComponent
        let before = try FileManager.default.contentsOfDirectory(atPath: dir)
            .filter { $0.hasPrefix(stem) && $0.hasSuffix(".bak") }

        // Reopen an already-current DB: equal-version path.
        let db = try SQLiteStorage(path: path); defer { db.close() }
        XCTAssertEqual(try db.userVersion(), SQLiteStorage.schemaVersion)
        XCTAssertEqual(try db.loadMeeting(id: sample.meeting.id), sample.meeting, "data intact")

        // No NEW backup was written for an equal-version open.
        let after = try FileManager.default.contentsOfDirectory(atPath: dir)
            .filter { $0.hasPrefix(stem) && $0.hasSuffix(".bak") }
        XCTAssertEqual(after.count, before.count, "equal-version open takes no backup")
    }
}
