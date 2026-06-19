import Foundation
import Contracts

/// HSM-10-02 — offline tolerance for sync. A disk-backed FIFO of change-sets the
/// app records locally; flushing pushes them to a peer and drops each on success.
/// Sync is **never on the capture/review path**: you record a change-set instantly
/// (a local file write), and `flush` resumes opportunistically when a peer is
/// reachable. If the peer is down, the queue is left intact and the app is
/// unaffected — `flush` swallows transport errors rather than propagating them.
public struct SyncQueue: Sendable {
    public let directory: URL

    public init(directory: URL) { self.directory = directory }

    public static func defaultDirectory() throws -> URL {
        let base = try FileManager.default.url(
            for: .applicationSupportDirectory, in: .userDomainMask, appropriateFor: nil, create: true)
        let dir = base.appendingPathComponent("HoldSpeak/sync-queue", isDirectory: true)
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir
    }

    private func ensure() throws {
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
    }

    /// Record a change-set to the queue. `seq` is a zero-padded monotonic ordinal so
    /// the lexical filename order is FIFO order (caller supplies it — e.g. a counter
    /// or a timestamp — keeping this type free of clock/RNG).
    @discardableResult
    public func enqueue(_ changeSet: ChangeSet, seq: Int) throws -> URL {
        try ensure()
        let name = String(format: "%012d.json", seq)
        let url = directory.appendingPathComponent(name)
        try HoldSpeakContracts.encoder().encode(changeSet).write(to: url)
        return url
    }

    /// Enqueue with a monotonic seq derived from the current contents
    /// (max-existing + 1) — stays clock/RNG-free and keeps FIFO order even across
    /// partial flushes (a removed-then-readded item never reuses a live index).
    @discardableResult
    public func enqueueNext(_ changeSet: ChangeSet) throws -> URL {
        let next = (try pending().compactMap { Int($0.deletingPathExtension().lastPathComponent) }.max() ?? -1) + 1
        return try enqueue(changeSet, seq: next)
    }

    /// Queued change-sets in FIFO order.
    public func pending() throws -> [URL] {
        try ensure()
        return try FileManager.default
            .contentsOfDirectory(at: directory, includingPropertiesForKeys: nil)
            .filter { $0.pathExtension == "json" }
            .sorted { $0.lastPathComponent < $1.lastPathComponent }
    }

    public func count() throws -> Int { try pending().count }

    /// Push every queued change-set to the peer, dropping each on success. On the
    /// first transport failure it **stops and leaves the rest queued** (offline →
    /// resume later) and does NOT throw. Returns how many were flushed.
    @discardableResult
    public func flush(through provider: ISyncProvider) async -> Int {
        guard let urls = try? pending() else { return 0 }
        var flushed = 0
        for url in urls {
            guard
                let data = try? Data(contentsOf: url),
                let changeSet = try? HoldSpeakContracts.decoder().decode(ChangeSet.self, from: data)
            else {
                try? FileManager.default.removeItem(at: url)   // unreadable/corrupt → drop, keep going
                continue
            }
            do {
                try await provider.push(changeSet)
                try? FileManager.default.removeItem(at: url)
                flushed += 1
            } catch {
                break   // peer unreachable — stop, keep the rest, resume later
            }
        }
        return flushed
    }
}
