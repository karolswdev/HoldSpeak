import Foundation
import Contracts
import Providers

/// HSM-10 — the one-call sync operation the host UI drives ("Sync now").
///
/// Ties the pieces together: snapshot the local store, durably **record** the
/// outbound change-set to the offline queue, **flush** the queue to the peer, then
/// **pull + apply** the peer's change-set (conflict-resolved). It is offline-safe by
/// construction — `syncNow` never throws on an unreachable peer; it reports
/// `reachedPeer = false` with the snapshot safely queued for the next attempt, so
/// sync is never on the capture/review path.
///
/// This is the mobile-side orchestration the continuity gate (HSM-10-04) exercises
/// live on hardware; here it's host-proven against a fake peer.
public struct SyncCoordinator: Sendable {
    let store: ISyncStore
    let provider: ISyncProvider
    let queue: SyncQueue
    let engine: SyncEngine

    public init(store: ISyncStore, provider: ISyncProvider, queue: SyncQueue,
                engine: SyncEngine = SyncEngine()) {
        self.store = store
        self.provider = provider
        self.queue = queue
        self.engine = engine
    }

    public struct Outcome: Sendable, Equatable {
        /// Queued change-sets successfully pushed this pass.
        public var pushed: Int
        /// Change-sets still queued afterward (peer was down for some/all).
        public var pendingAfter: Int
        /// Records applied from the peer's pull.
        public var applied: Int
        /// Concurrent conflicts surfaced on apply (kept local; never silently dropped).
        public var conflicts: [SyncEngine.Conflict]
        /// Whether the peer answered the pull this pass.
        public var reachedPeer: Bool
    }

    /// Run one sync pass. Durable-first: the local snapshot is queued before any
    /// network, so nothing is lost if the peer is down or the app dies mid-sync.
    @discardableResult
    public func syncNow() async throws -> Outcome {
        // 1. Record the outbound snapshot durably (offline-safe).
        try queue.enqueueNext(try engine.snapshot(of: store))

        // 2. Flush the queue to the peer (never throws; leaves the rest if down).
        let pushed = await queue.flush(through: provider)
        let pendingAfter = (try? queue.count()) ?? 0

        // 3. Pull + apply if the peer is reachable.
        do {
            let incoming = try await provider.pull()
            let report = try engine.apply(incoming, to: store)
            return Outcome(pushed: pushed, pendingAfter: pendingAfter,
                           applied: report.applied, conflicts: report.conflicts, reachedPeer: true)
        } catch {
            // Peer unreachable on pull — the snapshot is safely queued for later.
            return Outcome(pushed: pushed, pendingAfter: pendingAfter,
                           applied: 0, conflicts: [], reachedPeer: false)
        }
    }
}
