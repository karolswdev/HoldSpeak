import Foundation
import SQLite3
import Contracts

// SQLite wants its TRANSIENT destructor so it copies bound text immediately.
private let SQLITE_TRANSIENT = unsafeBitCast(-1, to: sqlite3_destructor_type.self)

public enum StorageError: Error, Equatable {
    case open(String), exec(String), prepare(String)
}

/// SQLite-backed `IStorage` + `ISyncStore` (HSM-4-01, HSM-10-01). Greenfield, WAL
/// for crash safety. Each entity is stored as its Phase-0 contract JSON in a keyed
/// row, so what comes back is exactly the contract.
///
/// Schema v2 (HSM-10-01) adds per-row `modified_at` (UTC `Z`) and a `deleted`
/// soft-delete flag (tombstones) so a sync change-set can be produced from and
/// applied to the store. `json` is nullable now: a tombstone row carries no payload.
///
/// Note: there is intentionally NO `deinit` close — abandoning an instance models a
/// crash (the crash-recovery test). Call `close()` for clean shutdown.
public final class SQLiteStorage: IStorage, ISyncStore, @unchecked Sendable {
    public static let schemaVersion: Int32 = 2

    private var db: OpaquePointer?
    private let encoder = HoldSpeakContracts.encoder()
    private let decoder = HoldSpeakContracts.decoder()

    public init(path: String) throws {
        let flags = SQLITE_OPEN_READWRITE | SQLITE_OPEN_CREATE | SQLITE_OPEN_FULLMUTEX
        guard sqlite3_open_v2(path, &db, flags, nil) == SQLITE_OK else {
            throw StorageError.open(lastError)
        }
        try exec("PRAGMA journal_mode=WAL;")
        try exec("PRAGMA foreign_keys=ON;")
        try exec("""
            CREATE TABLE IF NOT EXISTS meetings(
              id TEXT PRIMARY KEY, started_at TEXT, json TEXT,
              modified_at TEXT, deleted INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS artifacts(
              id TEXT PRIMARY KEY, meeting_id TEXT, json TEXT,
              modified_at TEXT, deleted INTEGER NOT NULL DEFAULT 0);
            CREATE INDEX IF NOT EXISTS idx_artifacts_meeting ON artifacts(meeting_id);
            """)
        try migrateIfNeeded()
        try exec("PRAGMA user_version=\(Self.schemaVersion);")
    }

    /// v1 → v2: a pre-existing v1 DB lacks `modified_at`/`deleted`. Add them
    /// (guarded — ignore "duplicate column"). Greenfield, so this is the only step.
    private func migrateIfNeeded() throws {
        guard (try? userVersion()) ?? 0 < 2 else { return }
        for sql in [
            "ALTER TABLE meetings ADD COLUMN modified_at TEXT;",
            "ALTER TABLE meetings ADD COLUMN deleted INTEGER NOT NULL DEFAULT 0;",
            "ALTER TABLE artifacts ADD COLUMN modified_at TEXT;",
            "ALTER TABLE artifacts ADD COLUMN deleted INTEGER NOT NULL DEFAULT 0;",
        ] {
            _ = sqlite3_exec(db, sql, nil, nil, nil)   // duplicate-column is benign
        }
    }

    public func close() {
        if let db { sqlite3_close(db) }
        db = nil
    }

    // MARK: - IStorage

    public func saveMeeting(_ meeting: Meeting) throws { try saveMeeting(meeting, modifiedAt: Date()) }

    public func loadMeeting(id: String) throws -> Meeting? {
        guard let json = try queryOne("SELECT json FROM meetings WHERE id=? AND deleted=0;", [id])
        else { return nil }
        return try decoder.decode(Meeting.self, from: Data(json.utf8))
    }

    public func saveArtifact(_ artifact: Artifact) throws { try saveArtifact(artifact, modifiedAt: Date()) }

    public func loadArtifacts(meetingId: String) throws -> [Artifact] {
        try queryAll("SELECT json FROM artifacts WHERE meeting_id=? AND deleted=0 ORDER BY id;", [meetingId])
            .map { try decoder.decode(Artifact.self, from: Data($0.utf8)) }
    }

    // MARK: - ISyncStore (HSM-10-01)

    public func saveMeeting(_ meeting: Meeting, modifiedAt: Date) throws {
        try run("""
            INSERT INTO meetings(id, started_at, json, modified_at, deleted) VALUES(?,?,?,?,0)
            ON CONFLICT(id) DO UPDATE SET started_at=excluded.started_at, json=excluded.json,
              modified_at=excluded.modified_at, deleted=0;
            """, [meeting.id, isoString(meeting.startedAt), try jsonString(meeting), isoString(modifiedAt)])
    }

    public func saveArtifact(_ artifact: Artifact, modifiedAt: Date) throws {
        try run("""
            INSERT INTO artifacts(id, meeting_id, json, modified_at, deleted) VALUES(?,?,?,?,0)
            ON CONFLICT(id) DO UPDATE SET meeting_id=excluded.meeting_id, json=excluded.json,
              modified_at=excluded.modified_at, deleted=0;
            """, [artifact.id, artifact.meetingId, try jsonString(artifact), isoString(modifiedAt)])
    }

    public func deleteMeeting(id: String, at: Date) throws {
        try run("""
            INSERT INTO meetings(id, started_at, json, modified_at, deleted) VALUES(?,NULL,NULL,?,1)
            ON CONFLICT(id) DO UPDATE SET json=NULL, modified_at=excluded.modified_at, deleted=1;
            """, [id, isoString(at)])
    }

    public func deleteArtifact(id: String, at: Date) throws {
        try run("""
            INSERT INTO artifacts(id, meeting_id, json, modified_at, deleted) VALUES(?,NULL,NULL,?,1)
            ON CONFLICT(id) DO UPDATE SET json=NULL, modified_at=excluded.modified_at, deleted=1;
            """, [id, isoString(at)])
    }

    public func allMeetings() throws -> [(meeting: Meeting, modifiedAt: Date)] {
        try queryRows("SELECT json, modified_at FROM meetings WHERE deleted=0 ORDER BY id;", [], 2)
            .map { (try decoder.decode(Meeting.self, from: Data(($0[0] ?? "").utf8)), parseDate($0[1])) }
    }

    public func allArtifacts() throws -> [(artifact: Artifact, modifiedAt: Date)] {
        try queryRows("SELECT json, modified_at FROM artifacts WHERE deleted=0 ORDER BY id;", [], 2)
            .map { (try decoder.decode(Artifact.self, from: Data(($0[0] ?? "").utf8)), parseDate($0[1])) }
    }

    public func tombstones() throws -> [SyncMetadata] {
        let m = try queryRows("SELECT id, modified_at FROM meetings WHERE deleted=1 ORDER BY id;", [], 2)
            .map { SyncMetadata(id: $0[0] ?? "", kind: .meeting, lastModified: parseDate($0[1]), deleted: true) }
        let a = try queryRows("SELECT id, modified_at FROM artifacts WHERE deleted=1 ORDER BY id;", [], 2)
            .map { SyncMetadata(id: $0[0] ?? "", kind: .artifact, lastModified: parseDate($0[1]), deleted: true) }
        return m + a
    }

    // MARK: - Transactions (for the crash-recovery test + batch writes)

    public func begin() throws { try exec("BEGIN;") }
    public func commit() throws { try exec("COMMIT;") }
    public func rollback() throws { try exec("ROLLBACK;") }

    // MARK: - Integrity / version

    public func integrityCheck() -> Bool {
        (try? queryOne("PRAGMA integrity_check;", [])) == "ok"
    }

    public func userVersion() throws -> Int32 {
        Int32(try queryOne("PRAGMA user_version;", []).flatMap { Int($0) } ?? -1)
    }

    // MARK: - Low-level helpers

    private var lastError: String { String(cString: sqlite3_errmsg(db)) }

    private func jsonString<T: Encodable>(_ value: T) throws -> String {
        String(data: try encoder.encode(value), encoding: .utf8)!
    }

    private func isoString(_ date: Date) -> String {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime]
        return f.string(from: date)
    }

    private func parseDate(_ s: String?) -> Date {
        guard let s else { return Date(timeIntervalSince1970: 0) }
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime]
        return f.date(from: s) ?? Date(timeIntervalSince1970: 0)
    }

    private func exec(_ sql: String) throws {
        if sqlite3_exec(db, sql, nil, nil, nil) != SQLITE_OK { throw StorageError.exec(lastError) }
    }

    /// Prepared write with nullable text binds (nil → SQL NULL).
    private func run(_ sql: String, _ binds: [String?]) throws {
        var stmt: OpaquePointer?
        guard sqlite3_prepare_v2(db, sql, -1, &stmt, nil) == SQLITE_OK else { throw StorageError.prepare(lastError) }
        defer { sqlite3_finalize(stmt) }
        bind(stmt, binds)
        guard sqlite3_step(stmt) == SQLITE_DONE else { throw StorageError.exec(lastError) }
    }

    private func bind(_ stmt: OpaquePointer?, _ binds: [String?]) {
        for (i, v) in binds.enumerated() {
            if let v { sqlite3_bind_text(stmt, Int32(i + 1), v, -1, SQLITE_TRANSIENT) }
            else { sqlite3_bind_null(stmt, Int32(i + 1)) }
        }
    }

    private func queryOne(_ sql: String, _ bind: [String]) throws -> String? {
        var stmt: OpaquePointer?
        guard sqlite3_prepare_v2(db, sql, -1, &stmt, nil) == SQLITE_OK else { throw StorageError.prepare(lastError) }
        defer { sqlite3_finalize(stmt) }
        for (i, v) in bind.enumerated() { sqlite3_bind_text(stmt, Int32(i + 1), v, -1, SQLITE_TRANSIENT) }
        guard sqlite3_step(stmt) == SQLITE_ROW, let c = sqlite3_column_text(stmt, 0) else { return nil }
        return String(cString: c)
    }

    private func queryAll(_ sql: String, _ bind: [String]) throws -> [String] {
        try queryRows(sql, bind, 1).compactMap { $0[0] }
    }

    /// Run a query returning `columns` text columns per row (nil for NULL cells).
    private func queryRows(_ sql: String, _ binds: [String], _ columns: Int32) throws -> [[String?]] {
        var stmt: OpaquePointer?
        guard sqlite3_prepare_v2(db, sql, -1, &stmt, nil) == SQLITE_OK else { throw StorageError.prepare(lastError) }
        defer { sqlite3_finalize(stmt) }
        for (i, v) in binds.enumerated() { sqlite3_bind_text(stmt, Int32(i + 1), v, -1, SQLITE_TRANSIENT) }
        var out: [[String?]] = []
        while sqlite3_step(stmt) == SQLITE_ROW {
            var row: [String?] = []
            for c in 0..<columns {
                if let t = sqlite3_column_text(stmt, c) { row.append(String(cString: t)) } else { row.append(nil) }
            }
            out.append(row)
        }
        return out
    }
}
