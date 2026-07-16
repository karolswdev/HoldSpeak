import Foundation

// HS-94-09 — the v2 Delivery Runtime contracts, as Swift models the native
// Desk decodes. These MIRROR the hub's ACTUAL wire emissions, not the contract
// prose (PLATFORM-CONTRACT §3 identity / §4 records made concrete):
//
// - `delivery_schema: 1` snapshot   — holdspeak/delivery/read_model.py +
//                                     collector._wire_row
// - `registry_schema: 1` sources    — collector.sources_view / registry.to_wire
// - `nodes_schema: 1` nodes         — node_link.NodeLinkState.nodes_view
// - `attempts_schema: 1` attempts   — db/delivery_attempts.WorkAttempt.to_wire
// - `dossier_schema: 1` /
//   `phase_dossier_schema: 1`       — delivery/dossiers.DossierService
// - the typed refusal envelope      — web/routes/delivery_dossiers._refusal_response
//
// ADDITIVE tolerance is binding (§4.4 / the fixture-parity acceptance):
// unknown fields are ignored (plain Codable), and every closed vocabulary
// decodes an unrecognized raw value into a case CARRYING the raw string —
// a new server word never throws on an old client.
//
// snake_case on the wire converts to camelCase via HoldSpeakContracts.decoder().
// Instants ride as String (the hub emits ISO-Z), never a fragile Date decode.
// §12/§13: no field in these shapes ever carries a filesystem path — the
// fixture tests mirror that hygiene rule on the Swift side.

// MARK: - Tolerant vocabularies

/// Per-source freshness (read_model.SOURCE_STATUSES).
public enum DeliverySourceStatus: Codable, Equatable, Sendable {
    case live, stale, offline, incompatible, unauthorized, unavailable
    /// A raw value this client does not know yet — kept, never thrown.
    case unknown(String)

    public init(rawValue raw: String) {
        switch raw {
        case "live": self = .live
        case "stale": self = .stale
        case "offline": self = .offline
        case "incompatible": self = .incompatible
        case "unauthorized": self = .unauthorized
        case "unavailable": self = .unavailable
        default: self = .unknown(raw)
        }
    }

    public var rawValue: String {
        switch self {
        case .live: return "live"
        case .stale: return "stale"
        case .offline: return "offline"
        case .incompatible: return "incompatible"
        case .unauthorized: return "unauthorized"
        case .unavailable: return "unavailable"
        case .unknown(let raw): return raw
        }
    }

    public init(from decoder: Decoder) throws {
        self.init(rawValue: try decoder.singleValueContainer().decode(String.self))
    }
    public func encode(to encoder: Encoder) throws {
        var c = encoder.singleValueContainer(); try c.encode(rawValue)
    }
}

/// Node liveness (node_link: live → stale after 15 s → offline after 30 s;
/// legacy-direct rows are honestly `unknown`).
public enum NodeLiveness: Codable, Equatable, Sendable {
    case live, stale, offline, unknown
    /// A raw value this client does not know yet — kept, never thrown.
    case unrecognized(String)

    public init(rawValue raw: String) {
        switch raw {
        case "live": self = .live
        case "stale": self = .stale
        case "offline": self = .offline
        case "unknown": self = .unknown
        default: self = .unrecognized(raw)
        }
    }

    public var rawValue: String {
        switch self {
        case .live: return "live"
        case .stale: return "stale"
        case .offline: return "offline"
        case .unknown: return "unknown"
        case .unrecognized(let raw): return raw
        }
    }

    public init(from decoder: Decoder) throws {
        self.init(rawValue: try decoder.singleValueContainer().decode(String.self))
    }
    public func encode(to encoder: Encoder) throws {
        var c = encoder.singleValueContainer(); try c.encode(rawValue)
    }
}

/// Attempt association provenance (db/delivery_attempts.ASSOCIATION_KINDS).
public enum AttemptAssociationKind: Codable, Equatable, Sendable {
    case launch, riderClaim, manual, contract, heuristic
    /// A raw value this client does not know yet — kept, never thrown.
    case unknown(String)

    public init(rawValue raw: String) {
        switch raw {
        case "launch": self = .launch
        case "rider_claim": self = .riderClaim
        case "manual": self = .manual
        case "contract": self = .contract
        case "heuristic": self = .heuristic
        default: self = .unknown(raw)
        }
    }

    public var rawValue: String {
        switch self {
        case .launch: return "launch"
        case .riderClaim: return "rider_claim"
        case .manual: return "manual"
        case .contract: return "contract"
        case .heuristic: return "heuristic"
        case .unknown(let raw): return raw
        }
    }

    public init(from decoder: Decoder) throws {
        self.init(rawValue: try decoder.singleValueContainer().decode(String.self))
    }
    public func encode(to encoder: Encoder) throws {
        var c = encoder.singleValueContainer(); try c.encode(rawValue)
    }
}

/// Attempt states (db/delivery_attempts.ATTEMPT_STATES — the honest machine).
public enum AttemptState: Codable, Equatable, Sendable {
    case starting, working, waiting, idle, ended, abandoned, unknown
    /// A raw value this client does not know yet — kept, never thrown.
    case unrecognized(String)

    public init(rawValue raw: String) {
        switch raw {
        case "starting": self = .starting
        case "working": self = .working
        case "waiting": self = .waiting
        case "idle": self = .idle
        case "ended": self = .ended
        case "abandoned": self = .abandoned
        case "unknown": self = .unknown
        default: self = .unrecognized(raw)
        }
    }

    public var rawValue: String {
        switch self {
        case .starting: return "starting"
        case .working: return "working"
        case .waiting: return "waiting"
        case .idle: return "idle"
        case .ended: return "ended"
        case .abandoned: return "abandoned"
        case .unknown: return "unknown"
        case .unrecognized(let raw): return raw
        }
    }

    /// Terminal tombstones (db TERMINAL_STATES) — never resurrected.
    public var isTerminal: Bool {
        self == .ended || self == .abandoned
    }

    public init(from decoder: Decoder) throws {
        self.init(rawValue: try decoder.singleValueContainer().decode(String.self))
    }
    public func encode(to encoder: Encoder) throws {
        var c = encoder.singleValueContainer(); try c.encode(rawValue)
    }
}

/// Manifest-view freshness (dossiers.ManifestView.freshness).
public enum DossierFreshness: Codable, Equatable, Sendable {
    case live, cached, unavailable
    /// A raw value this client does not know yet — kept, never thrown.
    case unknown(String)

    public init(rawValue raw: String) {
        switch raw {
        case "live": self = .live
        case "cached": self = .cached
        case "unavailable": self = .unavailable
        default: self = .unknown(raw)
        }
    }

    public var rawValue: String {
        switch self {
        case .live: return "live"
        case .cached: return "cached"
        case .unavailable: return "unavailable"
        case .unknown(let raw): return raw
        }
    }

    public init(from decoder: Decoder) throws {
        self.init(rawValue: try decoder.singleValueContainer().decode(String.self))
    }
    public func encode(to encoder: Encoder) throws {
        var c = encoder.singleValueContainer(); try c.encode(rawValue)
    }
}

/// dw's typed refusal codes as the hub maps them (dossiers.REFUSAL_HTTP).
public enum DeliveryRefusalCode: Codable, Equatable, Sendable {
    case notFound, notInManifest, outsideRoot, symlink, absent, oversize
    case bundleChanged, hashMismatch, unavailable, incompatible
    /// A raw value this client does not know yet — kept, never thrown.
    case unknown(String)

    public init(rawValue raw: String) {
        switch raw {
        case "not_found": self = .notFound
        case "not_in_manifest": self = .notInManifest
        case "outside_root": self = .outsideRoot
        case "symlink": self = .symlink
        case "absent": self = .absent
        case "oversize": self = .oversize
        case "bundle_changed": self = .bundleChanged
        case "hash_mismatch": self = .hashMismatch
        case "unavailable": self = .unavailable
        case "incompatible": self = .incompatible
        default: self = .unknown(raw)
        }
    }

    public var rawValue: String {
        switch self {
        case .notFound: return "not_found"
        case .notInManifest: return "not_in_manifest"
        case .outsideRoot: return "outside_root"
        case .symlink: return "symlink"
        case .absent: return "absent"
        case .oversize: return "oversize"
        case .bundleChanged: return "bundle_changed"
        case .hashMismatch: return "hash_mismatch"
        case .unavailable: return "unavailable"
        case .incompatible: return "incompatible"
        case .unknown(let raw): return raw
        }
    }

    public init(from decoder: Decoder) throws {
        self.init(rawValue: try decoder.singleValueContainer().decode(String.self))
    }
    public func encode(to encoder: Encoder) throws {
        var c = encoder.singleValueContainer(); try c.encode(rawValue)
    }
}

// MARK: - Snapshot (GET /api/delivery/snapshot — delivery_schema: 1)

/// One worktree of a registered source — opaque ID + display branch only;
/// the server-side path never crosses the wire (§12/§13).
public struct WorktreeRef: Codable, Equatable, Sendable {
    public var worktreeId: String
    public var branch: String?
    public init(worktreeId: String, branch: String? = nil) {
        self.worktreeId = worktreeId; self.branch = branch
    }
}

/// One Delivery Source row. Covers BOTH emissions: the snapshot row
/// (collector._wire_row — capabilities/projects/sessions) and the registry
/// view row (sources_view — fingerprint). Fields absent on one surface stay
/// nil on the other; that asymmetry is the wire's, not an invention here.
public struct DeliverySource: Codable, Equatable, Sendable {
    public var sourceId: String
    public var nodeId: String?
    public var label: String?
    /// Registry view only: "sha256:…" over credential-free clone identity.
    public var fingerprint: String?
    public var status: DeliverySourceStatus?
    public var detail: String?
    public var observedAt: String?
    /// Snapshot row only. Open-dictionary keys keep their wire spelling
    /// ("feed_schema" stays "feed_schema" inside `schemas`) — the decoder's
    /// key strategy rewrites struct property keys, not `[String: JSONValue]`
    /// entries (pinned by DeliveryRuntimeTests).
    public var capabilities: DeliveryCapabilities?
    public var worktrees: [WorktreeRef]?
    /// nil (not []) means never observed; [] is a known-empty source (§13).
    public var projects: [JSONValue]?
    public var sessions: [JSONValue]?

    public init(sourceId: String, nodeId: String? = nil, label: String? = nil,
                fingerprint: String? = nil, status: DeliverySourceStatus? = nil,
                detail: String? = nil, observedAt: String? = nil,
                capabilities: DeliveryCapabilities? = nil,
                worktrees: [WorktreeRef]? = nil,
                projects: [JSONValue]? = nil, sessions: [JSONValue]? = nil) {
        self.sourceId = sourceId; self.nodeId = nodeId; self.label = label
        self.fingerprint = fingerprint; self.status = status; self.detail = detail
        self.observedAt = observedAt; self.capabilities = capabilities
        self.worktrees = worktrees; self.projects = projects; self.sessions = sessions
    }
}

/// The dw capability report the collector retains per source.
public struct DeliveryCapabilities: Codable, Equatable, Sendable {
    public var schemas: [String: JSONValue]?
    public var statuses: [JSONValue]?
    public var verbs: [JSONValue]?
    public var features: [String: JSONValue]?
    public var disabled: [String]?
}

/// The coherent read model: ONE revision over every collection it carries,
/// ONE opaque replayable cursor (clients compare + hand back, never parse).
public struct DeliverySnapshot: Codable, Equatable, Sendable {
    public var deliverySchema: Int
    public var revision: String
    public var cursor: String
    public var generatedAt: String?
    public var sources: [DeliverySource]
}

/// GET /api/delivery/sources — registry + freshness (registry_schema: 1).
public struct DeliverySourcesView: Codable, Equatable, Sendable {
    public var registrySchema: Int
    public var sources: [DeliverySource]
}

// MARK: - Nodes (GET /api/delivery/nodes — nodes_schema: 1)

/// One node row: labels, opaque IDs, typed liveness, last-seen — no tokens,
/// no URLs, no paths. Legacy env-table steering nodes appear labeled
/// `legacy-direct` with honest `unknown` liveness.
public struct NodePresence: Codable, Equatable, Sendable {
    public var name: String
    public var nodeId: String?
    public var kind: String?             // node-link | legacy-direct
    public var status: NodeLiveness
    public var lastSeen: String?
    public var instanceId: String?
    public var capabilities: [String]?
    public var commandsEnabled: Bool?
    public var compat: String?           // protocol_mismatch | capability_missing | legacy-direct
    public var cursor: Int?
    public var clockSkewSeconds: Double?
}

public struct DeliveryNodesView: Codable, Equatable, Sendable {
    public var nodesSchema: Int
    public var nodes: [NodePresence]
}

// MARK: - Work attempts (GET /api/delivery/attempts — attempts_schema: 1)

/// The immutable Story binding an attempt undertakes (§4.2).
public struct DeliveryStoryRef: Codable, Equatable, Sendable {
    public var sourceId: String
    public var project: String
    public var storyId: String
    public init(sourceId: String, project: String, storyId: String) {
        self.sourceId = sourceId; self.project = project; self.storyId = storyId
    }
}

/// Explicit provenance: WHO bound this attempt, HOW, and WHEN. A
/// `heuristic` kind is never exact — ambiguity stays visible data.
public struct AttemptAssociation: Codable, Equatable, Sendable {
    public var kind: AttemptAssociationKind?
    public var claimedBy: String?
    public var claimedAt: String?
}

/// One replayable transition ("from" is null on the creation event).
public struct AttemptTransition: Codable, Equatable, Sendable {
    public var from: String?
    public var to: String
    public var reason: String?
    public var occurredAt: String?
}

/// One bounded undertaking of one primary Story (§4.2): opaque IDs only,
/// explicit provenance, honest states, replayable history.
public struct WorkAttempt: Codable, Equatable, Sendable {
    public var attemptId: String
    public var storyRef: DeliveryStoryRef
    public var nodeId: String?
    public var worktreeId: String?
    public var sessionId: String?
    public var targetId: String?
    public var association: AttemptAssociation?
    public var exact: Bool?
    public var state: AttemptState?
    public var startedAt: String?
    public var updatedAt: String?
    public var endedAt: String?
    public var history: [AttemptTransition]?
}

public struct WorkAttemptsView: Codable, Equatable, Sendable {
    public var attemptsSchema: Int
    public var attempts: [WorkAttempt]
}

// MARK: - Evidence dossiers (dossier_schema: 1 / phase_dossier_schema: 1)

/// One manifest member as the wire sees it: identity + typed metadata.
/// The manifest's server-side `path` field NEVER leaves the hub (§13).
public struct EvidenceMember: Codable, Equatable, Sendable {
    public var assetId: String?
    public var role: String?             // story_markdown | evidence_markdown | phase_status | final_summary | asset
    public var label: String?
    public var mediaType: String?
    public var bytes: Int?
    public var sha256: String?
    /// Phase-dossier final-summary reference rides its bundle along.
    public var bundleId: String?
}

/// One captured run parsed from the evidence Markdown; `passed` is explicit.
public struct CapturedRun: Codable, Equatable, Sendable {
    public var timestamp: String?
    public var command: String?
    public var exitCode: Int?
    public var passed: Bool?
}

/// The bundle's revision anchor: hashes only, never a repo path.
public struct SourceRevision: Codable, Equatable, Sendable {
    public var headSha: String?
    public var indexTree: String?
}

/// The dw manifest summary (open counts; tolerant of additions).
public struct DossierSummary: Codable, Equatable, Sendable {
    public var assets: Int?
    public var passingCaptures: Int?
    public var failingCaptures: Int?
}

/// Trace pointers into `members` by asset id.
public struct DossierTrace: Codable, Equatable, Sendable {
    public var storyAssetId: String?
    public var evidenceAssetId: String?
    public var phaseStatusAssetId: String?
    public var finalSummaryAssetId: String?
}

/// One inline document body: sanitized Markdown as TEXT, or a typed
/// unavailability state ("ready" | a refusal code) with a nil body.
public struct DossierDoc: Codable, Equatable, Sendable {
    public var assetId: String?
    public var state: String?
    public var markdown: String?
}

/// The story dossier (manifest wire + honesty markers + inline docs).
/// Also the shape of the `manifest` a bundle_changed/hash_mismatch refusal
/// preserves, and of a phase dossier's per-story rows (where a refused row
/// carries only storyId/title/status/state) — hence the broad optionality.
public struct StoryDossier: Codable, Equatable, Sendable {
    public var dossierSchema: Int?
    public var bundleId: String?
    public var bundleChanged: Bool?
    public var liveBundleId: String?
    public var freshness: DossierFreshness?
    public var detail: String?
    public var sourceId: String?
    public var project: String?
    public var storyId: String?
    public var phase: Int?
    public var status: String?
    /// Phase-dossier row extras: the story's title and row state
    /// ("ready" | a refusal code).
    public var title: String?
    public var state: String?
    public var sourceRevision: SourceRevision?
    public var summary: DossierSummary?
    public var members: [EvidenceMember]?
    public var capturedRuns: [CapturedRun]?
    public var trace: DossierTrace?
    public var story: DossierDoc?
    public var evidence: [DossierDoc]?
}

/// The phase's story dossiers grouped, metadata only — assets stream later.
public struct PhaseDossier: Codable, Equatable, Sendable {
    public var phaseDossierSchema: Int
    public var sourceId: String?
    public var project: String?
    public var phase: Int?
    public var title: String?
    public var status: String?
    public var storiesDone: Int?
    public var storiesTotal: Int?
    public var stories: [StoryDossier]
    public var finalSummary: EvidenceMember?
}

// MARK: - The typed refusal envelope

/// A dossier/asset refusal as the hub answers it (404/409/413/503 body):
/// `refusal` is the typed code, `detail` is classified (no paths, no argv,
/// no stderr), and a bundle_changed/hash_mismatch refusal PRESERVES the
/// cached manifest metadata (§13 — never silently re-pointed).
public struct DeliveryRefusal: Codable, Equatable, Sendable {
    public var refusal: DeliveryRefusalCode
    public var detail: String?
    public var manifest: StoryDossier?
    public init(refusal: DeliveryRefusalCode, detail: String? = nil,
                manifest: StoryDossier? = nil) {
        self.refusal = refusal; self.detail = detail; self.manifest = manifest
    }
}
