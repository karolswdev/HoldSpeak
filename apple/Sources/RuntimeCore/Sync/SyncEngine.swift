import Foundation
import Contracts
import Providers

/// HSM-10-01 — the sync engine (Runtime Core, Layer 2).
///
/// Produces a `ChangeSet` from the local store and applies a `ChangeSet` back to
/// it, both expressed in Phase-0 contract entities. It depends only on the
/// `ISyncStore` + `ISyncProvider` seams — never a concrete transport — so the same
/// engine drives desktop / homelab / Tailscale once those land (HSM-10-02).
///
/// Conflict resolution (idempotent round-trip, last-writer policy) is HSM-10-03;
/// this story establishes the object model and the produce/apply machinery. `apply`
/// validates every payload against the Phase-0 contract (encode→decode through the
/// shared coder, which is the schema) **before** it touches the store.
public struct SyncEngine: Sendable {

    public init() {}

    public enum SyncError: Error, Equatable {
        case tombstoneMissingMetadata
        case liveRecordMissingPayload(kind: SyncKind, id: String)
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
        let meetingTombs = tombs.filter { $0.kind == .meeting }
            .map { Synced<Meeting>(meta: $0, value: nil) }
        let artifactTombs = tombs.filter { $0.kind == .artifact }
            .map { Synced<Artifact>(meta: $0, value: nil) }
        return ChangeSet(meetings: meetings + meetingTombs, artifacts: artifacts + artifactTombs)
    }

    /// Apply a change-set to the store: live records upserted with their carried
    /// `lastModified`; tombstones soft-deleted. Every live payload is validated
    /// against the Phase-0 contract before any write.
    public func apply(_ changeSet: ChangeSet, to store: ISyncStore) throws {
        // Validate first — nothing touches the store until every payload is schema-valid.
        for rec in changeSet.meetings where !rec.meta.deleted {
            guard let v = rec.value else { throw SyncError.liveRecordMissingPayload(kind: .meeting, id: rec.meta.id) }
            try validate(v)
        }
        for rec in changeSet.artifacts where !rec.meta.deleted {
            guard let v = rec.value else { throw SyncError.liveRecordMissingPayload(kind: .artifact, id: rec.meta.id) }
            try validate(v)
        }

        for rec in changeSet.meetings {
            if rec.meta.deleted { try store.deleteMeeting(id: rec.meta.id, at: rec.meta.lastModified) }
            else { try store.saveMeeting(rec.value!, modifiedAt: rec.meta.lastModified) }
        }
        for rec in changeSet.artifacts {
            if rec.meta.deleted { try store.deleteArtifact(id: rec.meta.id, at: rec.meta.lastModified) }
            else { try store.saveArtifact(rec.value!, modifiedAt: rec.meta.lastModified) }
        }
    }

    /// Drive one round-trip through a provider: push the local snapshot, pull the
    /// peer's change-set, and apply it locally. (Bidirectional conflict policy is
    /// HSM-10-03; here the pulled set is applied as-is.)
    public func sync(local store: ISyncStore, via provider: ISyncProvider) async throws {
        try await provider.push(snapshot(of: store))
        let incoming = try await provider.pull()
        try apply(incoming, to: store)
    }

    /// Schema validation: round-trip the value through the contract coder. A value
    /// the contract can't hold throws here, before the store is touched.
    private func validate<T: Codable>(_ value: T) throws {
        let data = try HoldSpeakContracts.encoder().encode(value)
        _ = try HoldSpeakContracts.decoder().decode(T.self, from: data)
    }
}
