import Foundation

// HSM-23-03 — the store-health probe behind the readiness panel. The Wave-4 schema
// safety (refuse-newer + backup-then-apply) lives in `SQLiteStorage` but had zero UI
// surface; this probe turns it into one reportable value. It opens the SAME open
// path the app uses (so a refused-newer store reports exactly what the app hit —
// and an older store migrates behind its backup, exactly as the app open would),
// reads integrity + schema, and closes.

/// What the readiness panel states about the on-device store.
public struct StoreHealth: Equatable, Sendable {
    public enum State: Equatable, Sendable {
        /// Open succeeded: the stamped schema version + PRAGMA integrity_check.
        case ok(schema: Int32, integrityOK: Bool)
        /// No store file yet (created on first save) — a fresh install, not a fault.
        case missing
        /// The refuse-newer guard fired: a newer build wrote this DB; left untouched.
        case refusedNewer(stored: Int32, build: Int32)
        /// Any other open failure, carried verbatim.
        case failed(String)
    }

    public var state: State
    /// Timestamped `.bak` siblings next to the store (backup-then-apply artifacts).
    public var backupCount: Int

    public init(state: State, backupCount: Int) {
        self.state = state
        self.backupCount = backupCount
    }
}

public enum StoreHealthProbe {
    /// Probe the store at `path`. Never throws — every outcome is a reportable state.
    public static func probe(path: String) -> StoreHealth {
        let backups = backupCount(path: path)
        guard FileManager.default.fileExists(atPath: path) else {
            return StoreHealth(state: .missing, backupCount: backups)
        }
        do {
            let storage = try SQLiteStorage(path: path)
            defer { storage.close() }
            let schema = (try? storage.userVersion()) ?? -1
            return StoreHealth(state: .ok(schema: schema, integrityOK: storage.integrityCheck()),
                               backupCount: backupCount(path: path))
        } catch StorageError.tooNew(let stored, let build) {
            return StoreHealth(state: .refusedNewer(stored: stored, build: build),
                               backupCount: backups)
        } catch {
            return StoreHealth(state: .failed(String(describing: error)),
                               backupCount: backups)
        }
    }

    /// Count the `<file>.<timestamp>.bak` siblings `backupBeforeMigrate` writes.
    private static func backupCount(path: String) -> Int {
        let dir = (path as NSString).deletingLastPathComponent
        let stem = (path as NSString).lastPathComponent
        let names = (try? FileManager.default.contentsOfDirectory(atPath: dir)) ?? []
        return names.filter { $0.hasPrefix(stem + ".") && $0.hasSuffix(".bak") }.count
    }
}
