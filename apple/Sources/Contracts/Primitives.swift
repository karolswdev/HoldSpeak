import Foundation

/// The CANONICAL framework primitives (the unified PRIMITIVE FRAMEWORK).
///
/// Every primitive is first-class on desktop + iPad + web, authored anywhere, and
/// synced through the desktop hub (the canonical store). The iPad is a first-class
/// authoring port: things authored on the iPad are NOT `@AppStorage` locals that die
/// on the device — they are these canonical Codable objects, carried by `Synced<>`
/// (see Sync.swift) and reconciled last-write-by-`updatedAt`.
///
/// Wire rules (Coding.swift): snake_case JSON ⇄ camelCase Swift; instants are
/// ISO-8601 UTC `Z`. Identity is the stable `id`; the lastModified instant for sync
/// is `updatedAt`; deletes are tombstones (carried by the `Synced` envelope, not a
/// field here).
///
/// The desk's local `*Record` shapes (NoteRecord, AgentRecord, …) are derived
/// projections of these — they convert to/from the contract type so on-desk authoring
/// produces a real, sync-ready canonical object (`toContract` / `init(contract:)`).

// MARK: - Note (content / synced) — a first-class jotting

public struct Note: Codable, Equatable, Sendable, Identifiable {
    public var id: String
    public var title: String
    public var bodyMarkdown: String
    public var tags: [String]
    public var createdAt: Date
    public var updatedAt: Date

    public init(id: String, title: String, bodyMarkdown: String, tags: [String] = [],
                createdAt: Date, updatedAt: Date) {
        self.id = id
        self.title = title
        self.bodyMarkdown = bodyMarkdown
        self.tags = tags
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }
}

// MARK: - Directory (organization / synced) — a place primitives are filed (the iPad "zone")
//
// THE PRIMITIVE FRAMEWORK, wave 4 — "Zones ARE Directories". A desk zone is a Directory
// rendered spatially. The SPLIT is the whole point:
//
//   • Syncs (organization, THIS type): identity + nesting only — {id, name, parentId?}. The
//     `id` is the zone's stable `path` (e.g. "Atlas" or "Atlas/Q3"); `parentId` is the
//     parent path ("Atlas/Q3" → "Atlas", a top-level zone → nil). A directory + its
//     contents are the same on every surface.
//   • Per-device (layout, NEVER on the wire): the zone's geometry + paint — cx/cy/w/h,
//     color/border/fill/glow (the zone studio styling). A directory pulled from the hub
//     with no local geometry gets a sensible default placement on this device.
//
// Membership (which primitive is filed in which directory) is a SEPARATE synced edge —
// see `Membership` below. Geometry/paint is the zone's `ZoneRec` and stays local.
public struct Directory: Codable, Equatable, Sendable, Identifiable {
    public var id: String            // the zone's stable path ("Atlas", "Atlas/Q3")
    public var name: String          // the display name (the path's last segment)
    public var parentId: String?     // the parent directory's id (nil ⇒ a top-level zone)
    public var createdAt: Date
    public var updatedAt: Date

    public init(id: String, name: String, parentId: String? = nil,
                createdAt: Date, updatedAt: Date) {
        self.id = id
        self.name = name
        self.parentId = parentId
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }

    // HS-72-01 tolerant decode: the hub emits no updated_at for directories.
    private enum CodingKeys: String, CodingKey { case id, name, parentId, createdAt, updatedAt }
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(String.self, forKey: .id)
        name = try c.decode(String.self, forKey: .name)
        parentId = try c.decodeIfPresent(String.self, forKey: .parentId)
        createdAt = try c.decode(Date.self, forKey: .createdAt)
        updatedAt = try c.decodeIfPresent(Date.self, forKey: .updatedAt) ?? createdAt
    }
}

// MARK: - Membership (organization / synced) — a primitive's home directory edge
//
// The synced classification edge: which primitive is filed in which directory. Identity is
// the `primitiveId` (a primitive has at most one home directory), so the edge LWW-resolves
// per primitive like any other synced record. `directoryId` is the Directory's id (a zone
// path); an empty string means "filed at root" (the desk's home level). On the desk this
// is the union of the `filed` map (meetings/games) and each output/note/kb record's `path`.
//
// NOTE: membership was previously treated as per-device layout (`path`). It is ORGANIZATION
// and now rides the wire so filing a card on one surface files it on every surface.
public struct Membership: Codable, Equatable, Sendable, Identifiable {
    public var primitiveId: String   // the filed primitive's desk id ("note:…", "m:…", "out:…")
    public var directoryId: String   // the Directory id (zone path); "" ⇒ root
    public var updatedAt: Date

    public var id: String { primitiveId }

    public init(primitiveId: String, directoryId: String, updatedAt: Date) {
        self.primitiveId = primitiveId
        self.directoryId = directoryId
        self.updatedAt = updatedAt
    }

    // HS-72-01 tolerant decode: the hub emits created_at/last_modified but no
    // updated_at for membership edges — fall back created_at, then distantPast
    // (the Synced meta's last_modified stays the LWW key either way).
    // `CodingKeys` (property-only) keeps the synthesized encode; the decode
    // reads the extra created_at through its own key set.
    private enum CodingKeys: String, CodingKey { case primitiveId, directoryId, updatedAt }
    private enum LenientKeys: String, CodingKey { case primitiveId, directoryId, createdAt, updatedAt }
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: LenientKeys.self)
        primitiveId = try c.decode(String.self, forKey: .primitiveId)
        directoryId = try c.decode(String.self, forKey: .directoryId)
        updatedAt = try c.decodeIfPresent(Date.self, forKey: .updatedAt)
            ?? c.decodeIfPresent(Date.self, forKey: .createdAt)
            ?? .distantPast
    }
}

// MARK: - KB (organization / synced) — a named container of member primitive refs

public struct KB: Codable, Equatable, Sendable, Identifiable {
    public var id: String
    public var name: String
    public var memberIds: [String]   // primitive ids filed in this KB (Membership is the synced edge)
    public var createdAt: Date
    public var updatedAt: Date

    public init(id: String, name: String, memberIds: [String] = [],
                createdAt: Date, updatedAt: Date) {
        self.id = id
        self.name = name
        self.memberIds = memberIds
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }

    // HS-72-01 tolerant decode: the hub's canonical KB emission carries NO
    // updated_at (KBRecord has none) — the LWW key is the Synced meta's
    // last_modified. Default updatedAt to createdAt instead of failing the
    // whole ChangeSet decode. Encoding stays synthesized (all keys out).
    private enum CodingKeys: String, CodingKey { case id, name, memberIds, createdAt, updatedAt }
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(String.self, forKey: .id)
        name = try c.decode(String.self, forKey: .name)
        memberIds = try c.decodeIfPresent([String].self, forKey: .memberIds) ?? []
        createdAt = try c.decode(Date.self, forKey: .createdAt)
        updatedAt = try c.decodeIfPresent(Date.self, forKey: .updatedAt) ?? createdAt
    }
}

// MARK: - Recipe (capability / synced) — a persona you build and route cards through

public struct Recipe: Codable, Equatable, Sendable, Identifiable {
    public var id: String
    public var name: String
    public var avatar: String            // an avatar id (drives glyph + hue on the desk)
    public var role: String              // a one-line tagline
    public var systemPrompt: String      // how it behaves
    public var userTemplate: String      // what to ask — "{input}" is replaced at run time
    public var tools: [String]           // capability refs (connector/workflow ids); [] today
    public var kbId: String?             // grounded in this KB when set
    public var manualContext: String     // always-on pinned context
    public var useZoneContext: Bool      // also feed the current zone's meetings (per-device hint)
    public var profileId: String?        // Phase 24 — the RuntimeProfile this agent runs on (nil = active default)
    public var createdAt: Date
    public var updatedAt: Date

    public init(id: String, name: String, avatar: String, role: String,
                systemPrompt: String, userTemplate: String, tools: [String] = [],
                kbId: String? = nil, manualContext: String = "", useZoneContext: Bool = false,
                profileId: String? = nil, createdAt: Date, updatedAt: Date) {
        self.id = id
        self.name = name
        self.avatar = avatar
        self.role = role
        self.systemPrompt = systemPrompt
        self.userTemplate = userTemplate
        self.tools = tools
        self.kbId = kbId
        self.manualContext = manualContext
        self.useZoneContext = useZoneContext
        self.profileId = profileId
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }

    // HS-72-01 tolerant decode, updated HS-77-01: the hub persists and emits
    // manual_context/use_zone_context since schema v7 (the Phase-72 loss
    // ended); updated_at still never rides the hub's agent emission. Defaults
    // keep decoding pre-v7 hubs.
    private enum CodingKeys: String, CodingKey {
        case id, name, avatar, role, systemPrompt, userTemplate, tools, kbId
        case manualContext, useZoneContext, profileId, createdAt, updatedAt
    }
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(String.self, forKey: .id)
        name = try c.decode(String.self, forKey: .name)
        avatar = try c.decodeIfPresent(String.self, forKey: .avatar) ?? ""
        role = try c.decodeIfPresent(String.self, forKey: .role) ?? ""
        systemPrompt = try c.decodeIfPresent(String.self, forKey: .systemPrompt) ?? ""
        userTemplate = try c.decodeIfPresent(String.self, forKey: .userTemplate) ?? ""
        tools = try c.decodeIfPresent([String].self, forKey: .tools) ?? []
        kbId = try c.decodeIfPresent(String.self, forKey: .kbId)
        manualContext = try c.decodeIfPresent(String.self, forKey: .manualContext) ?? ""
        useZoneContext = try c.decodeIfPresent(Bool.self, forKey: .useZoneContext) ?? false
        profileId = try c.decodeIfPresent(String.self, forKey: .profileId)
        createdAt = try c.decode(Date.self, forKey: .createdAt)
        updatedAt = try c.decodeIfPresent(Date.self, forKey: .updatedAt) ?? createdAt
    }
}

// MARK: - Chain (capability / synced) — an ordered chain of recipes

public struct Chain: Codable, Equatable, Sendable, Identifiable {
    public var id: String
    public var name: String
    public var steps: [String]          // ordered Recipe ids
    public var createdAt: Date
    public var updatedAt: Date

    public init(id: String, name: String, steps: [String] = [],
                createdAt: Date, updatedAt: Date) {
        self.id = id
        self.name = name
        self.steps = steps
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }

    // HS-72-01 tolerant decode: the hub emits no updated_at for chains.
    private enum CodingKeys: String, CodingKey { case id, name, steps, createdAt, updatedAt }
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(String.self, forKey: .id)
        name = try c.decode(String.self, forKey: .name)
        steps = try c.decodeIfPresent([String].self, forKey: .steps) ?? []
        createdAt = try c.decode(Date.self, forKey: .createdAt)
        updatedAt = try c.decodeIfPresent(Date.self, forKey: .updatedAt) ?? createdAt
    }
}

// MARK: - RuntimeProfile (capability / synced) — a named "where intelligence runs" target (Phase 24)

/// A named, reusable inference target: on-device, or any OpenAI-compatible endpoint. The app keeps a
/// LIST of these plus one active; an `Recipe` may point at one (`Recipe.profileId`).
///
/// **Security invariant (load-bearing):** the API key is NEVER a field here and NEVER syncs. It lives
/// in the device Keychain (or, on the hub, its secrets), referenced by `id`, and is joined to an
/// `EndpointConfig` only at request time. Only the SHAPE below crosses the wire.
public struct RuntimeProfile: Codable, Equatable, Sendable, Identifiable {
    public enum Kind: String, Codable, Sendable { case onDevice, openAICompatible }
    public var id: String
    public var name: String
    public var kind: Kind
    public var modelFile: String        // onDevice: the .gguf filename ("" = first installed)
    public var baseURL: String          // openAICompatible: the OpenAI-compatible root
    public var model: String            // openAICompatible: the served model id
    public var contextLimit: Int        // usable window (on-device computed at run time; endpoint declared)
    public var requiresKey: Bool        // openAICompatible: a key is expected in the Keychain (never here)
    public var createdAt: Date
    public var updatedAt: Date

    public init(id: String, name: String, kind: Kind, modelFile: String = "", baseURL: String = "",
                model: String = "", contextLimit: Int = 16_384, requiresKey: Bool = false,
                createdAt: Date, updatedAt: Date) {
        self.id = id; self.name = name; self.kind = kind; self.modelFile = modelFile
        self.baseURL = baseURL; self.model = model; self.contextLimit = contextLimit
        self.requiresKey = requiresKey; self.createdAt = createdAt; self.updatedAt = updatedAt
    }

    // HS-72-01 tolerant decode: the hub emits no updated_at for profiles. The
    // API key is NEVER a field here — decoding ignores unknown keys, and the
    // schema (profile.schema.json) rejects any key-shaped field on the wire.
    private enum CodingKeys: String, CodingKey {
        case id, name, kind, modelFile, baseURL = "baseUrl", model, contextLimit, requiresKey
        case createdAt, updatedAt
    }
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(String.self, forKey: .id)
        name = try c.decode(String.self, forKey: .name)
        kind = try c.decode(Kind.self, forKey: .kind)
        modelFile = try c.decodeIfPresent(String.self, forKey: .modelFile) ?? ""
        baseURL = try c.decodeIfPresent(String.self, forKey: .baseURL) ?? ""
        model = try c.decodeIfPresent(String.self, forKey: .model) ?? ""
        contextLimit = try c.decodeIfPresent(Int.self, forKey: .contextLimit) ?? 16_384
        requiresKey = try c.decodeIfPresent(Bool.self, forKey: .requiresKey) ?? false
        createdAt = try c.decode(Date.self, forKey: .createdAt)
        updatedAt = try c.decodeIfPresent(Date.self, forKey: .updatedAt) ?? createdAt
    }

    public var isLocal: Bool { kind == .onDevice }
    /// The endpoint host for the egress badge (nil when on-device → "local").
    public var egressHost: String? { kind == .openAICompatible ? URL(string: baseURL)?.host : nil }
}

/// A model MANIFEST (capability/synced, HSM-16-08): "this node has this model, with these
/// capabilities." The manifest is the ONLY thing that crosses the mesh — the model binary
/// never does (it stays device-local; the schema's additionalProperties:false makes any
/// path/url/bytes-shaped field a validation failure). This is how a surface knows what
/// "run it on your desktop" would actually run.
public struct ModelManifest: Codable, Equatable, Sendable, Identifiable {
    public var id: String               // "<node>:<file-or-model-id>" — rows from different nodes never collide
    public var node: String             // the device holding it ("desktop", "iPad", "iPhone")
    public var name: String             // the human/model name ("Qwen3.5-9B-Instruct-Q6_K")
    public var capabilities: [String]   // e.g. ["language"], ["speech"]
    public var createdAt: Date
    public var updatedAt: Date

    public init(id: String, node: String, name: String, capabilities: [String] = ["language"],
                createdAt: Date, updatedAt: Date) {
        self.id = id; self.node = node; self.name = name; self.capabilities = capabilities
        self.createdAt = createdAt; self.updatedAt = updatedAt
    }

    private enum CodingKeys: String, CodingKey { case id, node, name, capabilities, createdAt, updatedAt }
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(String.self, forKey: .id)
        node = try c.decodeIfPresent(String.self, forKey: .node) ?? ""
        name = try c.decode(String.self, forKey: .name)
        capabilities = try c.decodeIfPresent([String].self, forKey: .capabilities) ?? []
        createdAt = try c.decodeIfPresent(Date.self, forKey: .createdAt) ?? .distantPast
        updatedAt = try c.decodeIfPresent(Date.self, forKey: .updatedAt) ?? .distantPast
    }
}

/// Pure mapping from the legacy single inference config (one mode + one endpoint) to a profile list
/// plus the active id. Deterministic (takes `now`) so the one-time app migration is testable. No key
/// flows through here — `endpointHasKey` only signals the caller to move the key into the Keychain.
public enum RuntimeProfileMigration {
    public static let localId = "profile.local"
    public static let endpointId = "profile.endpoint"

    public static func migrate(legacyModeIsLocal: Bool, endpointURL: String, endpointModel: String,
                               localModelFile: String, endpointHasKey: Bool, now: Date)
        -> (profiles: [RuntimeProfile], activeId: String) {
        var profiles: [RuntimeProfile] = [
            RuntimeProfile(id: localId, name: "This device", kind: .onDevice,
                           modelFile: localModelFile, createdAt: now, updatedAt: now)
        ]
        let url = endpointURL.trimmingCharacters(in: .whitespaces)
        if !url.isEmpty {
            let host = URL(string: url)?.host ?? "endpoint"
            profiles.append(RuntimeProfile(id: endpointId, name: host, kind: .openAICompatible,
                                           baseURL: url, model: endpointModel, requiresKey: endpointHasKey,
                                           createdAt: now, updatedAt: now))
        }
        let activeId = (!legacyModeIsLocal && !url.isEmpty) ? endpointId : localId
        return (profiles, activeId)
    }
}

// MARK: - WorkflowDefinition (capability / synced) — a saved Ask or graph
//
// RECONCILIATION (THE PRIMITIVE FRAMEWORK, tab 1) — two DISTINCT, deliberately-separate types:
//
//   • `Contracts.WorkflowDefinition` (THIS type) is the **synced wire contract** — the durable,
//     last-write-wins shape that ports between surfaces (desk ⇄ hub ⇄ web). Minimal + Codable +
//     Sendable: {id, name, prompt? | graphJson?, createdAt, updatedAt}. The wire `kind` is
//     `workflow` (see `SyncKind.workflow`) — DO NOT rename it; the snake_case payload key is fixed.
//
//   • `RuntimeCore.Workbench.Workflow` (in Sources/RuntimeCore/Workbench/Workflow.swift) is the
//     **executable engine model** — the richer Blueprints pipeline (source + typed steps + output)
//     the on-device runner actually runs. It is NOT synced as-is.
//
// They are kept apart ON PURPOSE so the contract layer never depends on the engine. The bridge is
// one-directional + lossy by design: a Workbench graph lowers into this type's `graphJson` to
// travel (HSM-22-01: `Blueprint.graphJSONValue()` through the canonical coder — the exact shape
// the hub's `workflow_graph.linearize()` parses, golden-pinned by `contracts/fixtures/`
// `blueprint-*.json`), and the desk's saved-Ask carries `prompt` (also the hub's honest
// fallback when it must refuse a non-linear graph). A receiving surface rehydrates a runnable
// graph from `graphJson` when (and only when) it has the engine.
public struct WorkflowDefinition: Codable, Equatable, Sendable, Identifiable {
    public var id: String
    public var name: String
    public var prompt: String?          // a saved Ask
    public var graphJson: JSONValue?    // OR a Workbench graph (reserved)
    public var createdAt: Date
    public var updatedAt: Date

    public init(id: String, name: String, prompt: String? = nil, graphJson: JSONValue? = nil,
                createdAt: Date, updatedAt: Date) {
        self.id = id
        self.name = name
        self.prompt = prompt
        self.graphJson = graphJson
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }

    // HS-72-01 tolerant decode: the hub emits no updated_at for workflows.
    private enum CodingKeys: String, CodingKey { case id, name, prompt, graphJson, createdAt, updatedAt }
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(String.self, forKey: .id)
        name = try c.decode(String.self, forKey: .name)
        prompt = try c.decodeIfPresent(String.self, forKey: .prompt)
        graphJson = try c.decodeIfPresent(JSONValue.self, forKey: .graphJson)
        createdAt = try c.decode(Date.self, forKey: .createdAt)
        updatedAt = try c.decodeIfPresent(Date.self, forKey: .updatedAt) ?? createdAt
    }
}
