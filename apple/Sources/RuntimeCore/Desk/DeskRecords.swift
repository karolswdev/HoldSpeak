import Foundation
import Contracts

// HS-72-09 — ONE SPINE: the iPad desk records EMBED the canonical `Contracts` types
// instead of hand-mirroring them. Each record is `{ contract, per-device extras }`:
// the embedded contract IS the storage (nothing is re-derived on push), the extras
// (layout `path`, zone geometry/paint, the KB item count) never cross the wire.
//
// Why this fixes a real class of bugs: the old `toContract(now:)` bridges REBUILT the
// contract from the flat fields on every push, stamping `createdAt = now` (creation
// time never stable) and hardcoding whatever the flat record didn't carry (`Note.tags`
// wiped, `KB.memberIds` wiped, a meeting-born `Artifact`'s meetingId/type/confidence/
// status/sources replaced, `WorkflowDefinition.graphJson` dropped, `Agent.tools`
// dropped, every record's timestamps re-minted). With the contract embedded, `synced(at:)`
// bumps ONLY `updatedAt` and everything else rides through untouched.
//
// Codable is dual-shape for device-data migration: these records persist as
// `@AppStorage` JSON arrays on real devices (hs.diorama.notes/.agents/…), so the OLD
// flat shape (`{id, title, body, path}`) must keep decoding. Legacy rows build a fresh
// contract with `createdAt = updatedAt =` decode-time. The NEW shape nests the
// contract: `{contract: {…}, path: …}`.
//
// SwiftUI-free on purpose (Foundation + Contracts only) so `swift test` covers them;
// the gen script flattens Sources + App into one module, so App call sites keep
// compiling via the compatibility computed properties (get+set → `$record.field`
// bindings still work).

// MARK: - RunProvenance — where a generated output came from

// LINEAGE — records the input card an output was made from (id + human title) and what
// produced it (the agent/chain that ran). Carried into the synced `Artifact.sources`,
// so web reads the same provenance the iPad shows.
public struct RunProvenance: Codable, Equatable, Sendable {
    public var sourceCardId: String      // the routed primitive's id (the input)
    public var sourceCardTitle: String   // its human title (what the lineage line names)
    public var viaId: String             // the agent/chain id that produced this
    public var viaName: String           // its name ("Scout", a crew name)
    public var viaKind: String           // "agent" | "chain"

    public init(sourceCardId: String, sourceCardTitle: String, viaId: String, viaName: String, viaKind: String) {
        self.sourceCardId = sourceCardId; self.sourceCardTitle = sourceCardTitle
        self.viaId = viaId; self.viaName = viaName; self.viaKind = viaKind
    }

    // A tasteful one-line summary for the card: "from <source card> · via Scout".
    public var line: String {
        let from = sourceCardTitle.trimmingCharacters(in: .whitespacesAndNewlines)
        let via = viaName.trimmingCharacters(in: .whitespacesAndNewlines)
        if from.isEmpty && via.isEmpty { return "" }
        if via.isEmpty { return "from \(from)" }
        if from.isEmpty { return "via \(via)" }
        return "from \(from) · via \(via)"
    }
}

// MARK: - NoteRecord — a first-class jotting (embeds `Note`)

public struct NoteRecord: Codable, Identifiable, Equatable, Sendable {
    public var contract: Note      // THE contract fields — single source
    public var path: String        // per-device layout; never on the wire

    public var id: String { contract.id }
    // Compatibility spellings so App call sites keep compiling:
    public var title: String { get { contract.title } set { contract.title = newValue } }
    public var body: String { get { contract.bodyMarkdown } set { contract.bodyMarkdown = newValue } }

    public init(contract n: Note, path: String = "") {
        self.contract = n; self.path = path
    }
    public init(id: String, title: String, body: String, path: String) {
        let now = Date()
        self.contract = Note(id: id, title: title, bodyMarkdown: body, tags: [],
                             createdAt: now, updatedAt: now)
        self.path = path
    }

    // sync-ready envelope (carried by ChangeSet.notes) — bumps ONLY updatedAt;
    // createdAt/tags/every other contract field ride through untouched.
    public func synced(at: Date = Date()) -> Synced<Note> {
        var c = contract; c.updatedAt = at
        return .live(c, id: c.id, kind: .note, modifiedAt: at)
    }

    // Codable: the new nested shape, plus the legacy flat @AppStorage shape.
    private enum CodingKeys: String, CodingKey { case contract, path }
    private enum LegacyKeys: String, CodingKey { case id, title, body, path }
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        if let k = try c.decodeIfPresent(Note.self, forKey: .contract) {
            contract = k
            path = try c.decodeIfPresent(String.self, forKey: .path) ?? ""
        } else {
            let l = try decoder.container(keyedBy: LegacyKeys.self)
            let now = Date()
            contract = Note(id: try l.decode(String.self, forKey: .id),
                            title: try l.decode(String.self, forKey: .title),
                            bodyMarkdown: try l.decode(String.self, forKey: .body),
                            tags: [], createdAt: now, updatedAt: now)
            path = try l.decodeIfPresent(String.self, forKey: .path) ?? ""
        }
    }
    public func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(contract, forKey: .contract)
        try c.encode(path, forKey: .path)
    }
}

// MARK: - KBRecord — a knowledge base (embeds `KB`)

public struct KBRecord: Codable, Identifiable, Equatable, Sendable {
    public var contract: KB        // THE contract fields — single source
    public var path: String        // per-device layout; never on the wire
    public var items: Int          // the desk-side routed-card count; `memberIds` is the synced truth

    public var id: String { contract.id }
    public var name: String { get { contract.name } set { contract.name = newValue } }

    public init(contract k: KB, path: String = "") {
        self.contract = k; self.path = path; self.items = k.memberIds.count
    }
    public init(id: String, name: String, path: String, items: Int) {
        let now = Date()
        self.contract = KB(id: id, name: name, memberIds: [], createdAt: now, updatedAt: now)
        self.path = path; self.items = items
    }

    public func synced(at: Date = Date()) -> Synced<KB> {
        var c = contract; c.updatedAt = at   // memberIds/createdAt preserved (the old bridge wiped members)
        return .live(c, id: c.id, kind: .kb, modifiedAt: at)
    }

    private enum CodingKeys: String, CodingKey { case contract, path, items }
    private enum LegacyKeys: String, CodingKey { case id, name, path, items }
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        if let k = try c.decodeIfPresent(KB.self, forKey: .contract) {
            contract = k
            path = try c.decodeIfPresent(String.self, forKey: .path) ?? ""
            items = try c.decodeIfPresent(Int.self, forKey: .items) ?? k.memberIds.count
        } else {
            let l = try decoder.container(keyedBy: LegacyKeys.self)
            let now = Date()
            contract = KB(id: try l.decode(String.self, forKey: .id),
                          name: try l.decode(String.self, forKey: .name),
                          memberIds: [], createdAt: now, updatedAt: now)
            path = try l.decodeIfPresent(String.self, forKey: .path) ?? ""
            items = try l.decodeIfPresent(Int.self, forKey: .items) ?? 0
        }
    }
    public func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(contract, forKey: .contract)
        try c.encode(path, forKey: .path)
        try c.encode(items, forKey: .items)
    }
}

// MARK: - OutputRecord — a generated output (embeds `Artifact`)

// A generated output — the result of routing a primitive through the AI core. The desk's
// lens/source/provenance live INSIDE the contract (`structuredJson` + `sources`), exactly
// where the wire carries them, so a hub-authored artifact's meetingId/type/confidence/
// status/sources survive an iPad edit + push (the old bridge rebuilt and lost them).
public struct OutputRecord: Codable, Identifiable, Equatable, Sendable {
    public var contract: Artifact  // THE contract fields — single source
    public var path: String        // per-device layout; never on the wire

    public var id: String { contract.id }
    public var title: String { get { contract.title } set { contract.title = newValue } }
    public var body: String { get { contract.bodyMarkdown } set { contract.bodyMarkdown = newValue } }

    // The desk metadata rides in `structuredJson` (so it survives sync); a meeting-born
    // artifact (no desk metadata) falls back to its type/meeting exactly as before.
    public var lens: String {
        get {
            if case let .object(o) = contract.structuredJson, case let .string(s)? = o["lens"] { return s }
            return contract.artifactType.rawValue
        }
        set { setStructured("lens", .string(newValue)) }
    }
    public var source: String {
        get {
            if case let .object(o) = contract.structuredJson, case let .string(s)? = o["source"] { return s }
            return contract.meetingId.isEmpty ? "synced" : "meeting"
        }
        set {
            setStructured("source", .string(newValue))
            if provenance == nil { contract.sources = [ArtifactSource(sourceType: "desk", sourceRef: newValue)] }
        }
    }
    // Provenance — populated when this output came from a routed run (agent/chain). nil for
    // direct lens routes / live captures / harvested scores (their `source` is the lineage).
    // Rides BOTH in `sources` (the canonical provenance array web reads) and in
    // `structuredJson` (so the typed `RunProvenance` can be rebuilt after a round-trip).
    public var provenance: RunProvenance? {
        get {
            guard case let .object(o) = contract.structuredJson, case let .object(p)? = o["provenance"],
                  case let .string(scid)? = p["source_card_id"], case let .string(sct)? = p["source_card_title"],
                  case let .string(vid)? = p["via_id"], case let .string(vn)? = p["via_name"],
                  case let .string(vk)? = p["via_kind"] else { return nil }
            return RunProvenance(sourceCardId: scid, sourceCardTitle: sct, viaId: vid, viaName: vn, viaKind: vk)
        }
        set {
            if let p = newValue {
                setStructured("provenance", .object([
                    "source_card_id": .string(p.sourceCardId),
                    "source_card_title": .string(p.sourceCardTitle),
                    "via_id": .string(p.viaId),
                    "via_name": .string(p.viaName),
                    "via_kind": .string(p.viaKind),
                ]))
                contract.sources = [
                    ArtifactSource(sourceType: "card", sourceRef: p.sourceCardTitle),
                    ArtifactSource(sourceType: p.viaKind, sourceRef: p.viaName),
                ]
            } else {
                setStructured("provenance", nil)
                contract.sources = [ArtifactSource(sourceType: "desk", sourceRef: source)]
            }
        }
    }

    // The lineage line shown on the printed/kept card + the Output pull-out. Prefers the rich
    // run provenance ("from <card> · via Scout"); falls back to the legacy `from <source>`.
    public var lineageLine: String {
        if let p = provenance, !p.line.isEmpty { return p.line }
        return source.isEmpty ? "" : "from \(source)"
    }

    private mutating func setStructured(_ key: String, _ value: JSONValue?) {
        var o: [String: JSONValue] = [:]
        if case let .object(existing) = contract.structuredJson { o = existing }
        o[key] = value
        contract.structuredJson = .object(o)
    }

    public init(contract a: Artifact, path: String = "") {
        self.contract = a; self.path = path
    }
    // A fresh desk-authored artifact: no parent meeting, the iPad desk is its plugin
    // source, and the lens/source/provenance ride in `structuredJson`/`sources`.
    public init(id: String, title: String, body: String, source: String, lens: String, path: String,
                provenance: RunProvenance? = nil) {
        let now = Date()
        var sources: [ArtifactSource] = [ArtifactSource(sourceType: "desk", sourceRef: source)]
        var structured: [String: JSONValue] = ["lens": .string(lens), "source": .string(source)]
        if let p = provenance {
            sources = [
                ArtifactSource(sourceType: "card", sourceRef: p.sourceCardTitle),
                ArtifactSource(sourceType: p.viaKind, sourceRef: p.viaName),
            ]
            structured["provenance"] = .object([
                "source_card_id": .string(p.sourceCardId),
                "source_card_title": .string(p.sourceCardTitle),
                "via_id": .string(p.viaId),
                "via_name": .string(p.viaName),
                "via_kind": .string(p.viaKind),
            ])
        }
        self.contract = Artifact(id: id, meetingId: "", artifactType: .pluginOutput, title: title,
                                 bodyMarkdown: body, structuredJson: .object(structured),
                                 confidence: 1.0, status: .draft, pluginId: "ipad.desk", pluginVersion: "0",
                                 sources: sources, createdAt: now, updatedAt: now,
                                 // Every desk-minted card is a run's output — say so
                                 // explicitly (v6) instead of leaving the wire to infer
                                 // it from the empty meeting anchor.
                                 origin: "run")
        self.path = path
    }

    public func synced(at: Date = Date()) -> Synced<Artifact> {
        var c = contract
        c.updatedAt = at
        if c.createdAt == nil { c.createdAt = at }   // Artifact timestamps are optional on a draft
        return .live(c, id: c.id, kind: .artifact, modifiedAt: at)
    }

    private enum CodingKeys: String, CodingKey { case contract, path }
    private enum LegacyKeys: String, CodingKey { case id, title, body, source, lens, path, provenance }
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        if let k = try c.decodeIfPresent(Artifact.self, forKey: .contract) {
            contract = k
            path = try c.decodeIfPresent(String.self, forKey: .path) ?? ""
        } else {
            let l = try decoder.container(keyedBy: LegacyKeys.self)
            self = OutputRecord(id: try l.decode(String.self, forKey: .id),
                                title: try l.decode(String.self, forKey: .title),
                                body: try l.decode(String.self, forKey: .body),
                                source: try l.decode(String.self, forKey: .source),
                                lens: try l.decode(String.self, forKey: .lens),
                                path: try l.decodeIfPresent(String.self, forKey: .path) ?? "",
                                provenance: try l.decodeIfPresent(RunProvenance.self, forKey: .provenance))
        }
    }
    public func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(contract, forKey: .contract)
        try c.encode(path, forKey: .path)
    }
}

// MARK: - WorkflowRecord — a saved Ask (embeds `WorkflowDefinition`)

public struct WorkflowRecord: Codable, Identifiable, Equatable, Sendable {
    public var contract: WorkflowDefinition   // THE contract fields — single source

    public var id: String { contract.id }
    public var name: String { get { contract.name } set { contract.name = newValue } }
    // The desk's v0 carrier is the saved-Ask `prompt`; a graph-only workflow (no prompt)
    // reads as an empty prompt — but its `graphJson` now SURVIVES an iPad push (the old
    // bridge dropped it on every round-trip).
    public var prompt: String { get { contract.prompt ?? "" } set { contract.prompt = newValue } }

    public init(contract w: WorkflowDefinition) {
        self.contract = w
    }
    public init(id: String, name: String, prompt: String) {
        let now = Date()
        self.contract = WorkflowDefinition(id: id, name: name, prompt: prompt,
                                           createdAt: now, updatedAt: now)
    }

    public func synced(at: Date = Date()) -> Synced<WorkflowDefinition> {
        var c = contract; c.updatedAt = at
        return .live(c, id: c.id, kind: .workflow, modifiedAt: at)
    }

    private enum CodingKeys: String, CodingKey { case contract }
    private enum LegacyKeys: String, CodingKey { case id, name, prompt }
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        if let k = try c.decodeIfPresent(WorkflowDefinition.self, forKey: .contract) {
            contract = k
        } else {
            let l = try decoder.container(keyedBy: LegacyKeys.self)
            let now = Date()
            contract = WorkflowDefinition(id: try l.decode(String.self, forKey: .id),
                                          name: try l.decode(String.self, forKey: .name),
                                          prompt: try l.decode(String.self, forKey: .prompt),
                                          createdAt: now, updatedAt: now)
        }
    }
    public func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(contract, forKey: .contract)
    }
}

// MARK: - AgentRecord — a tailored persona (embeds `Agent`)

public struct AgentRecord: Codable, Identifiable, Equatable, Sendable {
    public var contract: Agent   // THE contract fields — single source

    public var id: String { contract.id }
    public var name: String { get { contract.name } set { contract.name = newValue } }
    public var avatar: String { get { contract.avatar } set { contract.avatar = newValue } }
    public var role: String { get { contract.role } set { contract.role = newValue } }
    public var systemPrompt: String { get { contract.systemPrompt } set { contract.systemPrompt = newValue } }
    public var userTemplate: String { get { contract.userTemplate } set { contract.userTemplate = newValue } }
    public var manualContext: String { get { contract.manualContext } set { contract.manualContext = newValue } }
    public var useZoneContext: Bool { get { contract.useZoneContext } set { contract.useZoneContext = newValue } }
    // The desk's `kb` is a KB *name* today; it rides as `kbId` ("" ⇔ nil on the contract).
    public var kb: String {
        get { contract.kbId ?? "" }
        set { contract.kbId = newValue.isEmpty ? nil : newValue }
    }
    // Phase 24 — the RuntimeProfile this agent runs on ("" ⇔ nil = active default).
    public var profileId: String {
        get { contract.profileId ?? "" }
        set { contract.profileId = newValue.isEmpty ? nil : newValue }
    }

    public init(contract a: Agent) {
        self.contract = a
    }
    public init(id: String, name: String, avatar: String, role: String, systemPrompt: String,
                userTemplate: String, manualContext: String, useZoneContext: Bool, kb: String,
                profileId: String = "") {
        let now = Date()
        self.contract = Agent(id: id, name: name, avatar: avatar, role: role,
                              systemPrompt: systemPrompt, userTemplate: userTemplate, tools: [],
                              kbId: kb.isEmpty ? nil : kb, manualContext: manualContext,
                              useZoneContext: useZoneContext,
                              profileId: profileId.isEmpty ? nil : profileId,
                              createdAt: now, updatedAt: now)
    }

    // sync-ready envelope (carried by ChangeSet.agents) — createdAt/tools preserved.
    public func synced(at: Date = Date()) -> Synced<Agent> {
        var c = contract; c.updatedAt = at
        return .live(c, id: c.id, kind: .agent, modifiedAt: at)
    }

    // Legacy decode stays tolerant: persisted agents predate `profileId` (and earlier
    // fields), so absent keys default rather than fail — a missing field must never
    // wipe a user's saved agents.
    private enum CodingKeys: String, CodingKey { case contract }
    private enum LegacyKeys: String, CodingKey {
        case id, name, avatar, role, systemPrompt, userTemplate, manualContext, useZoneContext, kb, profileId
    }
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        if let k = try c.decodeIfPresent(Agent.self, forKey: .contract) {
            contract = k
        } else {
            let l = try decoder.container(keyedBy: LegacyKeys.self)
            self = AgentRecord(
                id: try l.decode(String.self, forKey: .id),
                name: try l.decode(String.self, forKey: .name),
                avatar: try l.decode(String.self, forKey: .avatar),
                role: try l.decode(String.self, forKey: .role),
                systemPrompt: try l.decode(String.self, forKey: .systemPrompt),
                userTemplate: try l.decode(String.self, forKey: .userTemplate),
                manualContext: try l.decodeIfPresent(String.self, forKey: .manualContext) ?? "",
                useZoneContext: try l.decodeIfPresent(Bool.self, forKey: .useZoneContext) ?? false,
                kb: try l.decodeIfPresent(String.self, forKey: .kb) ?? "",
                profileId: try l.decodeIfPresent(String.self, forKey: .profileId) ?? "")
        }
    }
    public func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(contract, forKey: .contract)
    }
}

// MARK: - ChainRecord — an ordered crew of agents (embeds `Chain`)

public struct ChainRecord: Codable, Identifiable, Equatable, Sendable {
    public var contract: Chain   // THE contract fields — single source

    public var id: String { contract.id }
    public var name: String { get { contract.name } set { contract.name = newValue } }
    public var steps: [String] { get { contract.steps } set { contract.steps = newValue } }

    public static func blank() -> ChainRecord { ChainRecord(id: UUID().uuidString, name: "", steps: []) }

    public init(contract c: Chain) {
        self.contract = c
    }
    public init(id: String, name: String, steps: [String]) {
        let now = Date()
        self.contract = Chain(id: id, name: name, steps: steps, createdAt: now, updatedAt: now)
    }

    public func synced(at: Date = Date()) -> Synced<Chain> {
        var c = contract; c.updatedAt = at
        return .live(c, id: c.id, kind: .chain, modifiedAt: at)
    }

    private enum CodingKeys: String, CodingKey { case contract }
    private enum LegacyKeys: String, CodingKey { case id, name, steps }
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        if let k = try c.decodeIfPresent(Chain.self, forKey: .contract) {
            contract = k
        } else {
            let l = try decoder.container(keyedBy: LegacyKeys.self)
            let now = Date()
            contract = Chain(id: try l.decode(String.self, forKey: .id),
                             name: try l.decode(String.self, forKey: .name),
                             steps: try l.decode([String].self, forKey: .steps),
                             createdAt: now, updatedAt: now)
        }
    }
    public func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(contract, forKey: .contract)
    }
}

// MARK: - ZoneRec — a desk zone (embeds `Directory`; geometry/paint stays local)

// A zone is a resizable, free-placed AREA: a path (recursion), a colour, a unit-centre
// (cx,cy) and a size (w,h in points). THE SPLIT: only identity + nesting (the embedded
// `Directory`) cross the wire; geometry (cx/cy/w/h) + paint (color/border/fill/glow)
// are PER-DEVICE layout and deliberately never enter the contract. Its SwiftUI `tint`
// lives in an App-side extension (this type stays SwiftUI-free).
public struct ZoneRec: Codable, Equatable, Sendable {
    public var contract: Directory   // identity + nesting — the only part that syncs
    public var color: Int
    public var cx: Double
    public var cy: Double
    public var w: Double
    public var h: Double
    // style (all optional, default to the old look): a zone is paintable
    public var borderW: Double = 1.5
    public var borderStyle: Int = 0    // 0 solid · 1 dashed · 2 dotted
    public var fillStyle: Int = 0      // 0 gradient · 1 solid · 2 hatch · 3 dots · 4 grid
    public var fillOpacity: Double = 0.12
    public var glow: Bool = false
    public var hex: Int = 0            // 0 ⇒ use the palette colour; else a fully custom colour

    // The zone's stable slash-nested path IS the directory id; setting it re-derives
    // the directory's name + parentId (rename = a new path = a new id).
    public var path: String {
        get { contract.id }
        set {
            contract.id = newValue
            contract.name = newValue.split(separator: "/").last.map(String.init) ?? newValue
            contract.parentId = ZoneRec.parentId(forPath: newValue)
        }
    }

    public static func directoryId(forPath path: String) -> String { path }
    public static func parentId(forPath path: String) -> String? {
        var c = path.split(separator: "/").map(String.init)
        if !c.isEmpty { c.removeLast() }
        let p = c.joined(separator: "/")
        return p.isEmpty ? nil : p
    }

    public init(path: String, color: Int, cx: Double, cy: Double, w: Double, h: Double,
                borderW: Double = 1.5, borderStyle: Int = 0, fillStyle: Int = 0,
                fillOpacity: Double = 0.12, glow: Bool = false, hex: Int = 0) {
        let now = Date()
        self.contract = Directory(id: ZoneRec.directoryId(forPath: path),
                                  name: path.split(separator: "/").last.map(String.init) ?? path,
                                  parentId: ZoneRec.parentId(forPath: path),
                                  createdAt: now, updatedAt: now)
        self.color = color; self.cx = cx; self.cy = cy; self.w = w; self.h = h
        self.borderW = borderW; self.borderStyle = borderStyle; self.fillStyle = fillStyle
        self.fillOpacity = fillOpacity; self.glow = glow; self.hex = hex
    }

    // INVERSE BRIDGE — build a ZoneRec from an incoming `Directory` with DEFAULT geometry
    // (the directory carried none). `index` spreads fresh zones across the canvas so a
    // batch of pulled directories don't stack on one spot. The directory (its timestamps
    // included) is embedded as-is — nothing re-minted.
    public init(directory d: Directory, index: Int = 0) {
        self.contract = d
        self.color = index
        // a tidy default grid placement; the user can re-arrange + paint locally afterward
        let col = index % 3, row = (index / 3) % 3
        self.cx = 0.27 + 0.23 * Double(col)
        self.cy = 0.20 + 0.18 * Double(row)
        self.w = 168
        self.h = 104
    }

    public func synced(at: Date = Date()) -> Synced<Directory> {
        var c = contract; c.updatedAt = at   // createdAt preserved; geometry/paint never leaves
        return .live(c, id: c.id, kind: .directory, modifiedAt: at)
    }

    // Zones persist as CSV on-device (hs.diorama.zones), so no legacy JSON exists in the
    // wild — but the flat shape decodes anyway (the shape the old struct would have had).
    private enum CodingKeys: String, CodingKey {
        case contract, color, cx, cy, w, h, borderW, borderStyle, fillStyle, fillOpacity, glow, hex
    }
    private enum LegacyKeys: String, CodingKey {
        case path, color, cx, cy, w, h, borderW, borderStyle, fillStyle, fillOpacity, glow, hex
    }
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        if let k = try c.decodeIfPresent(Directory.self, forKey: .contract) {
            contract = k
            color = try c.decodeIfPresent(Int.self, forKey: .color) ?? 0
            cx = try c.decodeIfPresent(Double.self, forKey: .cx) ?? 0.5
            cy = try c.decodeIfPresent(Double.self, forKey: .cy) ?? 0.5
            w = try c.decodeIfPresent(Double.self, forKey: .w) ?? 168
            h = try c.decodeIfPresent(Double.self, forKey: .h) ?? 104
            borderW = try c.decodeIfPresent(Double.self, forKey: .borderW) ?? 1.5
            borderStyle = try c.decodeIfPresent(Int.self, forKey: .borderStyle) ?? 0
            fillStyle = try c.decodeIfPresent(Int.self, forKey: .fillStyle) ?? 0
            fillOpacity = try c.decodeIfPresent(Double.self, forKey: .fillOpacity) ?? 0.12
            glow = try c.decodeIfPresent(Bool.self, forKey: .glow) ?? false
            hex = try c.decodeIfPresent(Int.self, forKey: .hex) ?? 0
        } else {
            let l = try decoder.container(keyedBy: LegacyKeys.self)
            self = ZoneRec(path: try l.decode(String.self, forKey: .path),
                           color: try l.decode(Int.self, forKey: .color),
                           cx: try l.decode(Double.self, forKey: .cx),
                           cy: try l.decode(Double.self, forKey: .cy),
                           w: try l.decode(Double.self, forKey: .w),
                           h: try l.decode(Double.self, forKey: .h),
                           borderW: try l.decodeIfPresent(Double.self, forKey: .borderW) ?? 1.5,
                           borderStyle: try l.decodeIfPresent(Int.self, forKey: .borderStyle) ?? 0,
                           fillStyle: try l.decodeIfPresent(Int.self, forKey: .fillStyle) ?? 0,
                           fillOpacity: try l.decodeIfPresent(Double.self, forKey: .fillOpacity) ?? 0.12,
                           glow: try l.decodeIfPresent(Bool.self, forKey: .glow) ?? false,
                           hex: try l.decodeIfPresent(Int.self, forKey: .hex) ?? 0)
        }
    }
    public func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(contract, forKey: .contract)
        try c.encode(color, forKey: .color)
        try c.encode(cx, forKey: .cx)
        try c.encode(cy, forKey: .cy)
        try c.encode(w, forKey: .w)
        try c.encode(h, forKey: .h)
        try c.encode(borderW, forKey: .borderW)
        try c.encode(borderStyle, forKey: .borderStyle)
        try c.encode(fillStyle, forKey: .fillStyle)
        try c.encode(fillOpacity, forKey: .fillOpacity)
        try c.encode(glow, forKey: .glow)
        try c.encode(hex, forKey: .hex)
    }
}
