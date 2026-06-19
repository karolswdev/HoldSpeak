import Foundation

/// HSM-10-01 — the sync object model.
///
/// Cross-device continuity syncs the **Phase-0 contract entities themselves**
/// (Meetings, Artifacts), never a parallel sync schema that could drift from them.
/// The sync metadata a transport needs — a stable id, a last-modified instant, and
/// a tombstone for deletes — rides in a thin contract-layer *envelope* (`Synced`)
/// whose payload is the unmodified entity. So the wire carries the real contract
/// object plus its sync header; the entity structs stay pure.
///
/// (Contract addition, HSM-10-01 → escalated to the serialization contract per the
/// story's note — additive, not a side field on each entity.)

public enum SyncKind: String, Codable, Sendable, CaseIterable {
    case meeting
    case artifact
}

/// The sync header for one entity: which entity, when it last changed, and whether
/// this is a tombstone (a propagated delete). Instants are UTC `Z` per the contract.
public struct SyncMetadata: Codable, Equatable, Sendable {
    public var id: String
    public var kind: SyncKind
    public var lastModified: Date
    public var deleted: Bool

    public init(id: String, kind: SyncKind, lastModified: Date, deleted: Bool = false) {
        self.id = id
        self.kind = kind
        self.lastModified = lastModified
        self.deleted = deleted
    }
}

/// An entity wrapped with its sync header. `value` is the real Phase-0 contract
/// object; it is `nil` exactly when `meta.deleted` (a tombstone carries no payload).
public struct Synced<Value: Codable & Equatable & Sendable>: Codable, Equatable, Sendable {
    public var meta: SyncMetadata
    public var value: Value?

    public init(meta: SyncMetadata, value: Value?) {
        self.meta = meta
        self.value = value
    }

    /// A live (non-tombstone) record.
    public static func live(_ value: Value, id: String, kind: SyncKind, modifiedAt: Date) -> Synced<Value> {
        Synced(meta: SyncMetadata(id: id, kind: kind, lastModified: modifiedAt, deleted: false), value: value)
    }

    /// A tombstone (a propagated delete).
    public static func tombstone(id: String, kind: SyncKind, at: Date) -> Synced<Value> {
        Synced(meta: SyncMetadata(id: id, kind: kind, lastModified: at, deleted: true), value: nil)
    }
}

/// A set of changes to push or pull: the syncable contract entities, each as a
/// `Synced` envelope. Actions are not a top-level store entity (they live inside an
/// Action-Items artifact), so the store-backed sync set is Meetings + Artifacts.
public struct ChangeSet: Codable, Equatable, Sendable {
    public var meetings: [Synced<Meeting>]
    public var artifacts: [Synced<Artifact>]

    public init(meetings: [Synced<Meeting>] = [], artifacts: [Synced<Artifact>] = []) {
        self.meetings = meetings
        self.artifacts = artifacts
    }

    public var isEmpty: Bool { meetings.isEmpty && artifacts.isEmpty }
    public var count: Int { meetings.count + artifacts.count }
}
