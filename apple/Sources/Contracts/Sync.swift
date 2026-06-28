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
    // content
    case meeting
    case artifact
    case note
    // organization
    case kb
    case directory      // the iPad "zone": identity + nesting (geometry/paint stays local)
    case membership = "directory_membership"   // a primitive's home-directory edge; wire kind matches the hub
    // capability
    case agent
    case chain
    case workflow
    case profile        // a runtime/connectivity target (Phase 24); SHAPE only — the API key never syncs
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
/// Action-Items artifact). The store-backed sync set spans the framework primitives:
/// Meetings + Artifacts + Notes (content), KBs (organization), and Agents + Chains +
/// Workflows (capability). Games are LOCAL-ONLY and never appear here; per-device
/// layout (x/y) is not synced either.
public struct ChangeSet: Codable, Equatable, Sendable {
    public var meetings: [Synced<Meeting>]
    public var artifacts: [Synced<Artifact>]
    public var notes: [Synced<Note>]
    public var kbs: [Synced<KB>]
    public var directories: [Synced<Directory>]   // the iPad zone's identity + nesting
    public var directoryMemberships: [Synced<Membership>]  // primitive → home-directory edges
    public var agents: [Synced<Agent>]
    public var chains: [Synced<Chain>]
    public var workflows: [Synced<WorkflowDefinition>]
    public var profiles: [Synced<RuntimeProfile>]   // runtime targets — SHAPE only (key never synced)

    public init(meetings: [Synced<Meeting>] = [], artifacts: [Synced<Artifact>] = [],
                notes: [Synced<Note>] = [], kbs: [Synced<KB>] = [],
                directories: [Synced<Directory>] = [], directoryMemberships: [Synced<Membership>] = [],
                agents: [Synced<Agent>] = [], chains: [Synced<Chain>] = [],
                workflows: [Synced<WorkflowDefinition>] = [], profiles: [Synced<RuntimeProfile>] = []) {
        self.meetings = meetings
        self.artifacts = artifacts
        self.notes = notes
        self.kbs = kbs
        self.directories = directories
        self.directoryMemberships = directoryMemberships
        self.agents = agents
        self.chains = chains
        self.workflows = workflows
        self.profiles = profiles
    }

    // Decode tolerantly: any array absent from the payload defaults to []. A surface that doesn't yet
    // know a kind (e.g. the hub before it learns `profiles`) sends a subset, and the others must still
    // decode — the whole point of cross-surface equilibrium. (Encoding stays synthesized: all keys out.)
    private enum CodingKeys: String, CodingKey {
        case meetings, artifacts, notes, kbs, directories, directoryMemberships, agents, chains, workflows, profiles
    }
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        meetings = try c.decodeIfPresent([Synced<Meeting>].self, forKey: .meetings) ?? []
        artifacts = try c.decodeIfPresent([Synced<Artifact>].self, forKey: .artifacts) ?? []
        notes = try c.decodeIfPresent([Synced<Note>].self, forKey: .notes) ?? []
        kbs = try c.decodeIfPresent([Synced<KB>].self, forKey: .kbs) ?? []
        directories = try c.decodeIfPresent([Synced<Directory>].self, forKey: .directories) ?? []
        directoryMemberships = try c.decodeIfPresent([Synced<Membership>].self, forKey: .directoryMemberships) ?? []
        agents = try c.decodeIfPresent([Synced<Agent>].self, forKey: .agents) ?? []
        chains = try c.decodeIfPresent([Synced<Chain>].self, forKey: .chains) ?? []
        workflows = try c.decodeIfPresent([Synced<WorkflowDefinition>].self, forKey: .workflows) ?? []
        profiles = try c.decodeIfPresent([Synced<RuntimeProfile>].self, forKey: .profiles) ?? []
    }

    public var isEmpty: Bool {
        meetings.isEmpty && artifacts.isEmpty && notes.isEmpty && kbs.isEmpty
            && directories.isEmpty && directoryMemberships.isEmpty
            && agents.isEmpty && chains.isEmpty && workflows.isEmpty && profiles.isEmpty
    }
    public var count: Int {
        meetings.count + artifacts.count + notes.count + kbs.count
            + directories.count + directoryMemberships.count
            + agents.count + chains.count + workflows.count + profiles.count
    }
}
