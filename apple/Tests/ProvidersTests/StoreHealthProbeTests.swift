import XCTest
import SQLite3
@testable import Providers

/// HSM-23-03 — the store-health probe the readiness panel renders. Every schema-
/// safety outcome (ok / missing / refused-newer / backup present) must come back as
/// a reportable state, never a throw.
final class StoreHealthProbeTests: XCTestCase {

    private func tempPath() -> String {
        NSTemporaryDirectory() + "hsm-health-\(UUID().uuidString).sqlite"
    }

    private func seedRawDB(at path: String, userVersion: Int32, _ script: String) throws {
        var db: OpaquePointer?
        XCTAssertEqual(sqlite3_open(path, &db), SQLITE_OK)
        defer { sqlite3_close(db) }
        XCTAssertEqual(sqlite3_exec(db, script, nil, nil, nil), SQLITE_OK)
        XCTAssertEqual(sqlite3_exec(db, "PRAGMA user_version=\(userVersion);", nil, nil, nil), SQLITE_OK)
    }

    func testMissingStoreIsAFreshInstallNotAFault() {
        let health = StoreHealthProbe.probe(path: tempPath())
        XCTAssertEqual(health.state, .missing)
        XCTAssertEqual(health.backupCount, 0)
    }

    func testHealthyStoreReportsSchemaAndIntegrity() throws {
        let path = tempPath()
        do { let db = try SQLiteStorage(path: path); db.close() }

        let health = StoreHealthProbe.probe(path: path)
        XCTAssertEqual(health.state, .ok(schema: SQLiteStorage.schemaVersion, integrityOK: true))
        XCTAssertEqual(health.backupCount, 0)
    }

    func testNewerStoreReportsTheRefusalWithBothVersions() throws {
        let path = tempPath()
        let future = SQLiteStorage.schemaVersion + 5
        try seedRawDB(at: path, userVersion: future, """
            CREATE TABLE meetings(id TEXT PRIMARY KEY, started_at TEXT, json TEXT,
              modified_at TEXT, deleted INTEGER NOT NULL DEFAULT 0);
            """)

        let health = StoreHealthProbe.probe(path: path)
        XCTAssertEqual(health.state,
                       .refusedNewer(stored: future, build: SQLiteStorage.schemaVersion))
        // The probe must not have healed/stamped anything: probing twice agrees.
        XCTAssertEqual(StoreHealthProbe.probe(path: path).state, health.state)
    }

    func testBackupSiblingsAreCounted() throws {
        let path = tempPath()
        // A v1 store: opening it (as the probe does) backs up then migrates —
        // the probe then reports the healthy state AND the backup it left.
        try seedRawDB(at: path, userVersion: 1, """
            CREATE TABLE meetings(id TEXT PRIMARY KEY, started_at TEXT, json TEXT);
            CREATE TABLE artifacts(id TEXT PRIMARY KEY, meeting_id TEXT, json TEXT);
            """)

        let health = StoreHealthProbe.probe(path: path)
        XCTAssertEqual(health.state, .ok(schema: SQLiteStorage.schemaVersion, integrityOK: true))
        XCTAssertEqual(health.backupCount, 1)
    }
}
