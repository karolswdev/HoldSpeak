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
}

// MARK: - Agent (capability / synced) — a persona you build and route cards through

public struct Agent: Codable, Equatable, Sendable, Identifiable {
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
    public var createdAt: Date
    public var updatedAt: Date

    public init(id: String, name: String, avatar: String, role: String,
                systemPrompt: String, userTemplate: String, tools: [String] = [],
                kbId: String? = nil, manualContext: String = "", useZoneContext: Bool = false,
                createdAt: Date, updatedAt: Date) {
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
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }
}

// MARK: - Chain (capability / synced) — an ordered crew of agents

public struct Chain: Codable, Equatable, Sendable, Identifiable {
    public var id: String
    public var name: String
    public var steps: [String]          // ordered Agent ids
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
// one-directional + lossy by design: a Workbench `Workflow` serializes its graph into this type's
// `graphJson` to travel, and the desk's saved-Ask carries `prompt`. A receiving surface rehydrates
// a runnable `Workflow` from `graphJson` when (and only when) it has the engine. Until the
// graph-bridge lands, `prompt` (the saved-Ask) is the v0 carrier and `graphJson` is reserved.
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
}
