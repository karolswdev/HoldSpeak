import Foundation
import Contracts
import Providers

/// HSM-10-01/03 — the sync engine (Runtime Core, Layer 2).
///
/// Produces a `ChangeSet` from the local store and applies one back, both in
/// Phase-0 contract entities, over the `ISyncStore` + `ISyncProvider` seams (never
/// a concrete transport). `apply` validates every payload against the contract
/// before any write, and resolves conflicts (HSM-10-03).
///
/// ## Conflict policy (HSM-10-03)
/// Per record, comparing the incoming `last_modified` to the local one:
/// - **incoming newer** → apply it (a live record upserts; a tombstone deletes).
///   This also handles tombstone-vs-live by recency: a newer tombstone deletes; a
///   newer live record resurrects, but an **older** live record never resurrects a
///   newer tombstone (no zombie re-creates).
/// - **incoming older** → skip (keep the newer local edit).
/// - **same timestamp, same content (or both tombstones)** → no-op → the round-trip
///   is **idempotent**.
/// - **same timestamp, divergent** (both live but different, or delete-vs-edit) →
///   a genuine concurrent conflict: keep the local copy and **surface it in the
///   report** rather than silently dropping either side (non-destructive). The host
///   resolves surfaced conflicts; nothing is lost silently.
public struct SyncEngine: Sendable {

    public init() {}

    public enum SyncError: Error, Equatable {
        case liveRecordMissingPayload(kind: SyncKind, id: String)
    }

    /// One surfaced concurrent conflict (kept local; incoming not silently dropped).
    public struct Conflict: Sendable, Equatable {
        public let kind: SyncKind
        public let id: String
    }

    public struct ApplyReport: Sendable, Equatable {
        public var applied: Int = 0
        public var skipped: Int = 0
        public var conflicts: [Conflict] = []
        public var changed: Bool { applied > 0 }
    }

    /// The full local state as a change-set: live entities + tombstones.
    public func snapshot(of store: ISyncStore) throws -> ChangeSet {
        let meetings = try store.allMeetings().map {
            Synced<Meeting>.live($0.meeting, id: $0.meeting.id, kind: .meeting, modifiedAt: $0.modifiedAt)
        }
        let artifacts = try store.allArtifacts().map {
            Synced<Artifact>.live($0.artifact, id: $0.artifact.id, kind: .artifact, modifiedAt: $0.modifiedAt)
        }
        let tombs = try store.tombstones()
        let meetingTombs = tombs.filter { $0.kind == .meeting }.map { Synced<Meeting>(meta: $0, value: nil) }
        let artifactTombs = tombs.filter { $0.kind == .artifact }.map { Synced<Artifact>(meta: $0, value: nil) }
        return ChangeSet(meetings: meetings + meetingTombs, artifacts: artifacts + artifactTombs)
    }

    private enum Action { case apply, skip, conflict }

    /// The conflict decision for one record against its local counterpart.
    private func decide(incomingTime: Date, incomingDeleted: Bool,
                        localTime: Date?, localDeleted: Bool, contentEqual: Bool) -> Action {
        guard let localTime else { return .apply }            // brand new
        if incomingTime > localTime { return .apply }         // newer wins (incl. resurrect / delete)
        if incomingTime < localTime { return .skip }          // local is newer
        if incomingDeleted == localDeleted {                  // same timestamp…
            return incomingDeleted ? .skip : (contentEqual ? .skip : .conflict)
        }
        return .conflict                                      // delete-vs-edit at the same time
    }

    /// Apply a change-set with the conflict policy above. Validates every live
    /// payload against the contract before any write; returns a report (applied /
    /// skipped / surfaced conflicts).
    @discardableResult
    public func apply(_ changeSet: ChangeSet, to store: ISyncStore) throws -> ApplyReport {
        for rec in changeSet.meetings where !rec.meta.deleted {
            guard let v = rec.value else { throw SyncError.liveRecordMissingPayload(kind: .meeting, id: rec.meta.id) }
            try validate(v)
        }
        for rec in changeSet.artifacts where !rec.meta.deleted {
            guard let v = rec.value else { throw SyncError.liveRecordMissingPayload(kind: .artifact, id: rec.meta.id) }
            try validate(v)
        }

        var report = ApplyReport()

        let liveMeetings = Dictionary(uniqueKeysWithValues: try store.allMeetings().map { ($0.meeting.id, $0) })
        let liveArtifacts = Dictionary(uniqueKeysWithValues: try store.allArtifacts().map { ($0.artifact.id, $0) })
        let tombs = try store.tombstones()
        let meetingTombs = Dictionary(uniqueKeysWithValues: tombs.filter { $0.kind == .meeting }.map { ($0.id, $0.lastModified) })
        let artifactTombs = Dictionary(uniqueKeysWithValues: tombs.filter { $0.kind == .artifact }.map { ($0.id, $0.lastModified) })

        for rec in changeSet.meetings {
            let live = liveMeetings[rec.meta.id]
            let localTime = live?.modifiedAt ?? meetingTombs[rec.meta.id]
            let localDeleted = live == nil && meetingTombs[rec.meta.id] != nil
            let contentEqual = (live != nil && rec.value != nil) ? (live!.meeting == rec.value!) : false
            switch decide(incomingTime: rec.meta.lastModified, incomingDeleted: rec.meta.deleted,
                          localTime: localTime, localDeleted: localDeleted, contentEqual: contentEqual) {
            case .apply:
                if rec.meta.deleted { try store.deleteMeeting(id: rec.meta.id, at: rec.meta.lastModified) }
                else { try store.saveMeeting(rec.value!, modifiedAt: rec.meta.lastModified) }
                report.applied += 1
            case .skip: report.skipped += 1
            case .conflict: report.conflicts.append(.init(kind: .meeting, id: rec.meta.id))
            }
        }

        for rec in changeSet.artifacts {
            let live = liveArtifacts[rec.meta.id]
            let localTime = live?.modifiedAt ?? artifactTombs[rec.meta.id]
            let localDeleted = live == nil && artifactTombs[rec.meta.id] != nil
            let contentEqual = (live != nil && rec.value != nil) ? (live!.artifact == rec.value!) : false
            switch decide(incomingTime: rec.meta.lastModified, incomingDeleted: rec.meta.deleted,
                          localTime: localTime, localDeleted: localDeleted, contentEqual: contentEqual) {
            case .apply:
                if rec.meta.deleted { try store.deleteArtifact(id: rec.meta.id, at: rec.meta.lastModified) }
                else { try store.saveArtifact(rec.value!, modifiedAt: rec.meta.lastModified) }
                report.applied += 1
            case .skip: report.skipped += 1
            case .conflict: report.conflicts.append(.init(kind: .artifact, id: rec.meta.id))
            }
        }

        return report
    }

    /// Drive one round-trip through a provider: push the local snapshot, pull the
    /// peer's change-set, and apply it locally (conflict-resolved).
    @discardableResult
    public func sync(local store: ISyncStore, via provider: ISyncProvider) async throws -> ApplyReport {
        try await provider.push(snapshot(of: store))
        let incoming = try await provider.pull()
        return try apply(incoming, to: store)
    }

    /// Schema validation: round-trip the value through the contract coder.
    private func validate<T: Codable>(_ value: T) throws {
        let data = try HoldSpeakContracts.encoder().encode(value)
        _ = try HoldSpeakContracts.decoder().decode(T.self, from: data)
    }
}
