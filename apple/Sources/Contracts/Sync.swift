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
    case recipe
    case chain
    case workflow
    case profile        // a runtime/connectivity target (Phase 24); SHAPE only — the API key never syncs
    case model          // a model MANIFEST (HSM-16-08): availability only — the binary NEVER syncs
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
    public var recipes: [Synced<Recipe>]
    public var chains: [Synced<Chain>]
    public var workflows: [Synced<WorkflowDefinition>]
    public var profiles: [Synced<RuntimeProfile>]   // runtime targets — SHAPE only (key never synced)
    public var models: [Synced<ModelManifest>]      // model MANIFESTS only — the binary never syncs

    public init(meetings: [Synced<Meeting>] = [], artifacts: [Synced<Artifact>] = [],
                notes: [Synced<Note>] = [], kbs: [Synced<KB>] = [],
                directories: [Synced<Directory>] = [], directoryMemberships: [Synced<Membership>] = [],
                recipes: [Synced<Recipe>] = [], chains: [Synced<Chain>] = [],
                workflows: [Synced<WorkflowDefinition>] = [], profiles: [Synced<RuntimeProfile>] = [],
                models: [Synced<ModelManifest>] = []) {
        self.meetings = meetings
        self.artifacts = artifacts
        self.notes = notes
        self.kbs = kbs
        self.directories = directories
        self.directoryMemberships = directoryMemberships
        self.recipes = recipes
        self.chains = chains
        self.workflows = workflows
        self.profiles = profiles
        self.models = models
    }

    /// Records the tolerant decode below could not read (a novel enum value, a
    /// malformed payload). Never encoded; surfaced so a sync pass can report
    /// "n skipped" instead of silently pretending completeness. One bad record
    /// must never fail the whole ChangeSet again (the 2026-07-06 saga: a single
    /// `run_output` artifact took down every pull for four builds).
    public var undecodedRecords: Int = 0

    // Decode tolerantly, on two axes:
    // - any array absent from the payload defaults to [] (a surface that doesn't yet
    //   know a kind sends a subset, and the others must still decode);
    // - within an array, a record that fails to decode is skipped and COUNTED
    //   (`undecodedRecords`), never allowed to fail the set.
    // (Encoding stays synthesized: all keys out; the counter is not a CodingKey.)
    private enum CodingKeys: String, CodingKey {
        case meetings, artifacts, notes, kbs, directories, directoryMemberships, recipes, chains, workflows, profiles, models
    }
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        var dropped = 0
        func lossy<V: Codable & Equatable & Sendable>(
            _ type: V.Type, _ key: CodingKeys
        ) -> [Synced<V>] {
            guard var arr = try? c.nestedUnkeyedContainer(forKey: key) else { return [] }
            var out: [Synced<V>] = []
            while !arr.isAtEnd {
                if let rec = try? arr.decode(Synced<V>.self) {
                    out.append(rec)
                } else {
                    // A failed decode does not advance the container — consume the
                    // element as an opaque JSONValue to move past it.
                    _ = try? arr.decode(JSONValue.self)
                    dropped += 1
                }
            }
            return out
        }
        meetings = lossy(Meeting.self, .meetings)
        artifacts = lossy(Artifact.self, .artifacts)
        notes = lossy(Note.self, .notes)
        kbs = lossy(KB.self, .kbs)
        directories = lossy(Directory.self, .directories)
        directoryMemberships = lossy(Membership.self, .directoryMemberships)
        recipes = lossy(Recipe.self, .recipes)
        chains = lossy(Chain.self, .chains)
        workflows = lossy(WorkflowDefinition.self, .workflows)
        profiles = lossy(RuntimeProfile.self, .profiles)
        models = lossy(ModelManifest.self, .models)
        undecodedRecords = dropped
    }

    public var isEmpty: Bool {
        meetings.isEmpty && artifacts.isEmpty && notes.isEmpty && kbs.isEmpty
            && directories.isEmpty && directoryMemberships.isEmpty
            && recipes.isEmpty && chains.isEmpty && workflows.isEmpty && profiles.isEmpty
            && models.isEmpty
    }
    public var count: Int {
        meetings.count + artifacts.count + notes.count + kbs.count
            + directories.count + directoryMemberships.count
            + recipes.count + chains.count + workflows.count + profiles.count + models.count
    }
}
