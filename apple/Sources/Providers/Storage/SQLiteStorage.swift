import Foundation
import SQLite3
import Contracts

// SQLite wants its TRANSIENT destructor so it copies bound text immediately.
private let SQLITE_TRANSIENT = unsafeBitCast(-1, to: sqlite3_destructor_type.self)

public enum StorageError: Error, Equatable {
    case open(String), exec(String), prepare(String)
}

/// SQLite-backed `IStorage` (HSM-4-01). Greenfield: ships at `SCHEMA_VERSION = 1`,
/// WAL mode for crash safety. Each entity is stored as its Phase-0 contract JSON
/// in a keyed row, so what comes back is exactly the contract (the round-trip is
/// the Swift Codable layer the tests already trust).
///
/// Note: there is intentionally NO `deinit` close — abandoning an instance models
/// a crash (used by the crash-recovery test). Call `close()` for clean shutdown.
public final class SQLiteStorage: IStorage, @unchecked Sendable {
    public static let schemaVersion: Int32 = 1

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
              id TEXT PRIMARY KEY, started_at TEXT, json TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS artifacts(
              id TEXT PRIMARY KEY, meeting_id TEXT, json TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS idx_artifacts_meeting ON artifacts(meeting_id);
            """)
        try exec("PRAGMA user_version=\(Self.schemaVersion);")
    }

    public func close() {
        if let db { sqlite3_close(db) }
        db = nil
    }

    // MARK: - IStorage

    public func saveMeeting(_ meeting: Meeting) throws {
        let json = try jsonString(meeting)
        try upsert("meetings", ["id", "started_at", "json"],
                   [meeting.id, isoString(meeting.startedAt), json])
    }

    public func loadMeeting(id: String) throws -> Meeting? {
        guard let json = try queryOne("SELECT json FROM meetings WHERE id=?;", [id]) else { return nil }
        return try decoder.decode(Meeting.self, from: Data(json.utf8))
    }

    public func saveArtifact(_ artifact: Artifact) throws {
        let json = try jsonString(artifact)
        try upsert("artifacts", ["id", "meeting_id", "json"],
                   [artifact.id, artifact.meetingId, json])
    }

    public func loadArtifacts(meetingId: String) throws -> [Artifact] {
        try queryAll("SELECT json FROM artifacts WHERE meeting_id=? ORDER BY id;", [meetingId])
            .map { try decoder.decode(Artifact.self, from: Data($0.utf8)) }
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

    private func exec(_ sql: String) throws {
        if sqlite3_exec(db, sql, nil, nil, nil) != SQLITE_OK { throw StorageError.exec(lastError) }
    }

    private func upsert(_ table: String, _ columns: [String], _ values: [String]) throws {
        let cols = columns.joined(separator: ",")
        let placeholders = values.map { _ in "?" }.joined(separator: ",")
        let sql = "INSERT OR REPLACE INTO \(table)(\(cols)) VALUES(\(placeholders));"
        var stmt: OpaquePointer?
        guard sqlite3_prepare_v2(db, sql, -1, &stmt, nil) == SQLITE_OK else { throw StorageError.prepare(lastError) }
        defer { sqlite3_finalize(stmt) }
        for (i, v) in values.enumerated() {
            sqlite3_bind_text(stmt, Int32(i + 1), v, -1, SQLITE_TRANSIENT)
        }
        guard sqlite3_step(stmt) == SQLITE_DONE else { throw StorageError.exec(lastError) }
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
        var stmt: OpaquePointer?
        guard sqlite3_prepare_v2(db, sql, -1, &stmt, nil) == SQLITE_OK else { throw StorageError.prepare(lastError) }
        defer { sqlite3_finalize(stmt) }
        for (i, v) in bind.enumerated() { sqlite3_bind_text(stmt, Int32(i + 1), v, -1, SQLITE_TRANSIENT) }
        var out: [String] = []
        while sqlite3_step(stmt) == SQLITE_ROW {
            if let c = sqlite3_column_text(stmt, 0) { out.append(String(cString: c)) }
        }
        return out
    }
}
