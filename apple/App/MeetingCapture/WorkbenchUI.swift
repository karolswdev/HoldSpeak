import SwiftUI
import Foundation

// HSM-14-19 "The Desk" decomposition: THE WORKBENCH — the visual intelligence builder (HSM-14-15 linear
// node-graph + HSM-14-16 Blueprints canvas + inspectors + seeded providers), the app-within-the-app.
// Lifted verbatim out of MeetingCaptureApp.swift. The pure engine (Workflow/WorkflowRunner/Blueprint/
// BlueprintInterpreter) lives in RuntimeCore/Workbench/; this is its UI. Same module — all resolves.

// MARK: - Workbench (user-defined intelligence builder)

/// The library of saved user-defined workflows, persisted to UserDefaults. The builder edits a
/// working copy and saves here; a meeting runs any saved workflow.
@MainActor final class WorkflowStore: ObservableObject {
    static let shared = WorkflowStore()
    @Published var saved: [Workflow] = []
    private let d = UserDefaults.standard
    private let key = "hs.workflows.v1"
    private init() {
        if let data = d.data(forKey: key), let ws = try? JSONDecoder().decode([Workflow].self, from: data) { saved = ws }
    }
    func save(_ w: Workflow) {
        if let i = saved.firstIndex(where: { $0.id == w.id }) { saved[i] = w } else { saved.insert(w, at: 0) }
        persist()
    }
    func delete(_ id: UUID) { saved.removeAll { $0.id == id }; persist() }
    private func persist() { if let data = try? JSONEncoder().encode(saved) { d.set(data, forKey: key) } }
}

// MARK: - HSM-22-01 — the desk workflow library (Save writes what the desk syncs)

/// Upserts a lowered workflow into the DESK's record store — the exact
/// `@AppStorage`-backed keys `DeskDioramaStage` owns (`hs.diorama.workflows` +
/// the `hs.diorama.synctimes` LWW stamp) with the exact same coders, so the next
/// `DeskSyncDriver` pass pushes the graph to the hub like every other primitive.
/// The Workbench and the desk stage are never alive at once (both are classic-home
/// destinations), so the direct defaults write cannot race the stage's persistence.
@MainActor enum DeskWorkflowLibrary {
    static func upsert(_ record: WorkflowRecord) {
        let defaults = UserDefaults.standard

        var records: [WorkflowRecord] = []
        if let s = defaults.string(forKey: "hs.diorama.workflows"), let data = s.data(using: .utf8),
           let existing = try? JSONDecoder().decode([WorkflowRecord].self, from: data) {
            records = existing
        }
        if let i = records.firstIndex(where: { $0.id == record.id }) { records[i] = record }
        else { records.append(record) }
        if let data = try? JSONEncoder().encode(records), let s = String(data: data, encoding: .utf8) {
            defaults.set(s, forKey: "hs.diorama.workflows")
        }

        // Stamp modified-now (iso8601 — persistSyncMaps' coder) so LWW pushes it.
        let enc = JSONEncoder(); enc.dateEncodingStrategy = .iso8601
        let dec = JSONDecoder(); dec.dateDecodingStrategy = .iso8601
        var times: [String: Date] = [:]
        if let s = defaults.string(forKey: "hs.diorama.synctimes"), let data = s.data(using: .utf8),
           let existing = try? dec.decode([String: Date].self, from: data) {
            times = existing
        }
        times[record.id] = Date()
        if let data = try? enc.encode(times), let s = String(data: data, encoding: .utf8) {
            defaults.set(s, forKey: "hs.diorama.synctimes")
        }
    }
}

// MARK: - Workbench: the visual language (HSM-14-15)
//
// A node-based dataflow canvas. Typed primitives — "Transcription", "Decisions", "LLM call",
// "Slack" — are draggable objects you wire output→input. Each cable is colored by the data type
// flowing through it (signal = cobalt, text = amber, findings = green), so the program reads at a
// glance. This is the builder the owner asked for: a meta-language for composing intelligence,
// not a config form. Run lights the graph up — signal pulses travel the cables.

/// The typed value that travels along a cable.
private enum PortType: Equatable {
    case signal, text, findings
    var color: Color {
        switch self { case .signal: return Sig.local; case .text: return Sig.accent; case .findings: return Sig.ok }
    }
    var label: String {
        switch self { case .signal: return "signal"; case .text: return "text"; case .findings: return "findings" }
    }
}

private enum NodeCat: String { case source = "SOURCE", intel = "INTELLIGENCE", transform = "TRANSFORM", output = "OUTPUT" }

/// A primitive in the language — the vocabulary the user composes from.
private enum NodeKind: String, CaseIterable, Identifiable {
    case transcription, tacked, selection
    case decisions, actions, risks, questions, requirements
    case llm, summarize, rewrite, filter
    case note, board, slack, diagram
    var id: String { rawValue }

    var cat: NodeCat {
        switch self {
        case .transcription, .tacked, .selection: return .source
        case .decisions, .actions, .risks, .questions, .requirements: return .intel
        case .llm, .summarize, .rewrite, .filter: return .transform
        case .note, .board, .slack, .diagram: return .output
        }
    }
    var title: String {
        switch self {
        case .transcription: return "Transcription"; case .tacked: return "Tacked moments"; case .selection: return "Selection"
        case .decisions: return "Decisions"; case .actions: return "Action items"; case .risks: return "Risks"
        case .questions: return "Questions"; case .requirements: return "Requirements"
        case .llm: return "LLM call"; case .summarize: return "Summarize"; case .rewrite: return "Rewrite"; case .filter: return "Filter"
        case .note: return "Note"; case .board: return "Artifacts"; case .slack: return "Slack"; case .diagram: return "Diagram"
        }
    }
    var glyph: String {
        switch self {
        case .transcription: return "waveform"; case .tacked: return "pin.fill"; case .selection: return "selection.pin.in.out"
        case .decisions: return "checkmark.seal.fill"; case .actions: return "checklist"; case .risks: return "exclamationmark.triangle.fill"
        case .questions: return "questionmark.bubble.fill"; case .requirements: return "list.bullet.rectangle.fill"
        case .llm: return "terminal.fill"; case .summarize: return "text.append"; case .rewrite: return "pencil.and.outline"; case .filter: return "line.3.horizontal.decrease.circle"
        case .note: return "note.text"; case .board: return "rectangle.stack.fill"; case .slack: return "paperplane.fill"; case .diagram: return "flowchart"
        }
    }
    var inputs: [PortType] {
        switch cat {
        case .source: return []
        case .intel: return [.signal]
        case .transform: return [.text]
        case .output: return self == .board ? [.findings] : [.text]
        }
    }
    var outputs: [PortType] {
        switch cat {
        case .source: return [.signal]
        case .intel: return [.findings]
        case .transform: return [.text]
        case .output: return []
        }
    }
    var isEgress: Bool { self == .slack }
    /// Whether running this node calls a language model (so it needs a target + a failure policy).
    var usesModel: Bool { cat == .intel || self == .llm || self == .summarize || self == .rewrite }
    var accent: Color {
        switch cat {
        case .source: return Sig.local
        case .intel: return Sig.ok
        case .transform: return Sig.accent
        case .output: return isEgress ? Sig.accent : Sig.local
        }
    }
    var grad: LinearGradient {
        switch cat {
        case .source: return Sig.localGradient
        case .intel: return LinearGradient(colors: [Color(hex: 0x6FE3AE), Sig.ok], startPoint: .topLeading, endPoint: .bottomTrailing)
        case .transform: return Sig.accentGradient
        case .output: return isEgress ? Sig.accentGradient : Sig.localGradient
        }
    }
    /// One tight line describing what the primitive does — shown in the inspector (teaches the language).
    var blurb: String {
        switch self {
        case .transcription: return "The full meeting transcript."
        case .tacked: return "Only the moments you tacked."
        case .selection: return "A passage you selected."
        case .decisions: return "Pulls the decisions made."
        case .actions: return "Pulls action items + owners."
        case .risks: return "Surfaces risks raised."
        case .questions: return "Open questions left unanswered."
        case .requirements: return "Stated requirements + constraints."
        case .llm: return "Your prompt, your model. {input} is the wired input."
        case .summarize: return "Condenses the input to its essence."
        case .rewrite: return "Rewrites the input in a tone."
        case .filter: return "Keeps only lines matching a keyword."
        case .note: return "Saves the result as one note."
        case .board: return "Files findings to the review board."
        case .slack: return "Drafts a Slack message (you approve)."
        case .diagram: return "Renders the result as a Mermaid diagram."
        }
    }
}

/// A placed primitive on the canvas.
/// Which model a model-backed node prefers to run on. `auto` follows the app's Settings; the others
/// pin the node to a target regardless of the global default.
private enum ModelPref: String, CaseIterable, Identifiable {
    case auto, onDevice, endpoint, desktop
    var id: String { rawValue }
    var label: String { switch self { case .auto: return "Auto"; case .onDevice: return "On-device"; case .endpoint: return "Endpoint"; case .desktop: return "Your Mac" } }
    var glyph: String { switch self { case .auto: return "wand.and.stars"; case .onDevice: return "ipad"; case .endpoint: return "network"; case .desktop: return "desktopcomputer" } }
    var hint: String {
        switch self {
        case .auto: return "Follows Settings."
        case .onDevice: return "Always the on-device model. No network."
        case .endpoint: return "Always your configured endpoint."
        case .desktop: return "Runs on your paired desktop."
        }
    }
    /// The runner's per-step target for this pin (HSM-15-02). `auto` = nil (the run default).
    var runTarget: RunTarget? {
        switch self {
        case .auto: return nil
        case .onDevice: return .onDevice
        case .endpoint: return .endpoint
        case .desktop: return .dispatchToMac
        }
    }
}

/// What a run does when a node's chosen model can't be reached.
// `FailurePolicy` (retryThenQueue / fallbackOnDevice / skip) is defined once in RuntimeCore
// (`Workbench/WorkflowRunner.swift`) — the node inspector's policy IS the runner's policy. The app
// only adds the UI facets here, so there is a single source of truth.
extension FailurePolicy: Identifiable {
    public var id: String { rawValue }
    var label: String {
        switch self {
        case .retryThenQueue: return "Retry, then queue"
        case .fallbackOnDevice: return "Fall back on-device"
        case .skip: return "Skip the step"
        }
    }
    var glyph: String {
        switch self {
        case .retryThenQueue: return "clock.arrow.circlepath"
        case .fallbackOnDevice: return "ipad.and.arrow.forward"
        case .skip: return "arrow.turn.down.right"
        }
    }
    var hint: String {
        switch self {
        case .retryThenQueue: return "Retry a few times, then hold the run in the queue and resume when reachable."
        case .fallbackOnDevice: return "If the endpoint is down, run this step on the on-device model instead."
        case .skip: return "Drop this step and carry the input straight through."
        }
    }
}

/// HSM-14-15 — how a node is doing in the *current* run. Drives the canvas glow (idle → working
/// pulse → settled done, or red on fail/park). Mirrors the runner's `StepStatus` but is a UI concern.
private enum NodeRunState { case idle, working, done, failed, parked }

private struct GraphNode: Identifiable {
    let id: UUID
    var kind: NodeKind
    var pos: CGPoint
    var prompt: String = ""
    var tone: String = "Executive"
    var keyword: String = "risk"
    var modelPref: ModelPref = .auto
    var onFail: FailurePolicy = .retryThenQueue
    /// Live run state — set by the runner as it walks the lowered workflow (HSM-14-15).
    var runState: NodeRunState = .idle
    init(_ kind: NodeKind, _ pos: CGPoint) { self.id = UUID(); self.kind = kind; self.pos = pos }
    var title: String { kind.title }
    var subtitle: String? {
        switch kind {
        case .llm:
            let p = prompt.trimmingCharacters(in: .whitespacesAndNewlines)
            return p.isEmpty ? "tap to write a prompt" : "\u{201C}\(p.prefix(28))\(p.count > 28 ? "\u{2026}" : "")\u{201D}"
        case .rewrite: return "tone \u{00B7} \(tone.lowercased())"
        case .filter: return "keep \u{00B7} \(keyword)"
        default: return nil
        }
    }
}

private struct PortRef: Hashable { let node: UUID; let isInput: Bool; let index: Int }
private struct GraphEdge: Identifiable { let id = UUID(); var from: PortRef; var to: PortRef }

private enum GraphGeom {
    static let nodeW: CGFloat = 198
    static let nodeH: CGFloat = 72
    static let canvas = CGSize(width: 2600, height: 1800)
}

private func cablePath(_ a: CGPoint, _ b: CGPoint) -> Path {
    var p = Path()
    let dx = max(46, abs(b.x - a.x) * 0.45)
    p.move(to: a)
    p.addCurve(to: b, control1: CGPoint(x: a.x + dx, y: a.y), control2: CGPoint(x: b.x - dx, y: b.y))
    return p
}
private func cablePoint(_ a: CGPoint, _ b: CGPoint, _ t: CGFloat) -> CGPoint {
    let dx = max(46, abs(b.x - a.x) * 0.45)
    let c1 = CGPoint(x: a.x + dx, y: a.y), c2 = CGPoint(x: b.x - dx, y: b.y)
    let m = 1 - t
    return CGPoint(x: m*m*m*a.x + 3*m*m*t*c1.x + 3*m*t*t*c2.x + t*t*t*b.x,
                   y: m*m*m*a.y + 3*m*m*t*c1.y + 3*m*t*t*c2.y + t*t*t*b.y)
}

@MainActor private final class PatchModel: ObservableObject {
    @Published var nodes: [GraphNode] = []
    @Published var edges: [GraphEdge] = []
    @Published var selected: UUID?
    @Published var pending: (from: PortRef, point: CGPoint)?
    @Published var running = false
    /// The edges whose cable should pulse RIGHT NOW — the outgoing cables of the working node, so the
    /// signal visibly travels the wire the run is on (HSM-14-15). Empty ⇒ no pulse.
    @Published var activeEdges: Set<UUID> = []
    var dragOrigin: [UUID: CGPoint] = [:]

    func node(_ id: UUID) -> GraphNode? { nodes.first { $0.id == id } }
    func idx(_ id: UUID) -> Int? { nodes.firstIndex { $0.id == id } }

    func portCenter(_ ref: PortRef) -> CGPoint? {
        guard let n = node(ref.node) else { return nil }
        let arr = ref.isInput ? n.kind.inputs : n.kind.outputs
        guard ref.index < arr.count else { return nil }
        let x = ref.isInput ? n.pos.x - GraphGeom.nodeW/2 : n.pos.x + GraphGeom.nodeW/2
        let top = n.pos.y - GraphGeom.nodeH/2
        return CGPoint(x: x, y: top + GraphGeom.nodeH * CGFloat(ref.index + 1) / CGFloat(arr.count + 1))
    }
    func portType(_ ref: PortRef) -> PortType? {
        guard let n = node(ref.node) else { return nil }
        let arr = ref.isInput ? n.kind.inputs : n.kind.outputs
        return ref.index < arr.count ? arr[ref.index] : nil
    }
    func move(_ id: UUID, to p: CGPoint) {
        guard let i = idx(id) else { return }
        nodes[i].pos = CGPoint(x: min(max(p.x, GraphGeom.nodeW/2), GraphGeom.canvas.width - GraphGeom.nodeW/2),
                               y: min(max(p.y, GraphGeom.nodeH/2 + 6), GraphGeom.canvas.height - GraphGeom.nodeH/2))
    }
    private func compatible(_ out: PortType, _ inp: PortType) -> Bool {
        if out == inp { return true }
        switch (out, inp) { case (.signal, .text), (.findings, .text): return true; default: return false }
    }
    func endWire(at p: CGPoint) {
        defer { pending = nil }
        guard let pend = pending, let outType = portType(pend.from) else { return }
        var best: (PortRef, CGFloat)?
        for n in nodes where n.id != pend.from.node {
            for i in n.kind.inputs.indices {
                let ref = PortRef(node: n.id, isInput: true, index: i)
                guard let c = portCenter(ref), let it = portType(ref), compatible(outType, it) else { continue }
                let d = hypot(c.x - p.x, c.y - p.y)
                if d < 46, best == nil || d < best!.1 { best = (ref, d) }
            }
        }
        if let (ref, _) = best {
            edges.removeAll { $0.to == ref }            // one cable per input
            edges.append(GraphEdge(from: pend.from, to: ref))
            tactile(.medium)
        }
    }
    func addNode(_ kind: NodeKind, at p: CGPoint) { let n = GraphNode(kind, p); nodes.append(n); selected = n.id }
    func remove(_ id: UUID) {
        edges.removeAll { $0.from.node == id || $0.to.node == id }
        nodes.removeAll { $0.id == id }
        if selected == id { selected = nil }
    }

    // MARK: - HSM-14-15 — lower the graph to a runnable `Workflow`

    /// The result of lowering the canvas graph to the runner's linear model: the `Workflow` the
    /// engine executes, PLUS the canvas node id for each step (and the source/output node ids), so the
    /// run can light the right node + cable as each `StepOutcome` lands.
    struct LoweredGraph {
        var workflow: Workflow
        var sourceNode: UUID
        var stepNodes: [UUID]        // one per `workflow.steps[i]`
        var stepTargets: [RunTarget?] = []  // the node inspector's pin, per step (HSM-15-02)
        var outputNode: UUID?
    }

    /// Walk the **primary** source→…→output chain in wire order and produce an ordered `Workflow`.
    ///
    /// v1 LIMITATION — the runnable model is a LINEAR pipeline (Workflow.steps), so this follows the
    /// MAIN PATH only: it starts at the first source node, and at each node follows its FIRST wired
    /// outgoing edge. If the graph branches (a source fanning out to two chains, like the seeded
    /// Decisions + LLM split) only the first branch runs; the other outputs are ignored. A full DAG
    /// engine is deliberately out of scope — see WorkflowRunner.swift's "Pure linear" note.
    func lowerToWorkflow(name: String = "Canvas run") -> LoweredGraph? {
        guard let src = nodes.first(where: { $0.kind.cat == .source }) else { return nil }
        let source: WorkflowSource = {
            switch src.kind {
            case .tacked: return .tackedMoments
            case .selection: return .selection
            default: return .fullTranscript
            }
        }()

        var steps: [WorkflowStep] = []
        var stepNodes: [UUID] = []
        var stepTargets: [RunTarget?] = []
        var outputNode: UUID?
        var output: WorkflowOutput = .artifacts

        // Follow the first outgoing edge from a node to the next node it feeds.
        func next(after id: UUID) -> GraphNode? {
            let outgoing = edges.filter { $0.from.node == id }
            guard let edge = outgoing.first else { return nil }
            return node(edge.to.node)
        }

        var current = next(after: src.id)
        var guardCount = 0
        while let n = current, guardCount < nodes.count + 2 {
            guardCount += 1
            switch n.kind.cat {
            case .source:
                // A second source in the chain is meaningless to the linear model — stop.
                current = nil
            case .intel, .transform:
                if let step = step(for: n) {
                    steps.append(step)
                    stepNodes.append(n.id)
                    stepTargets.append(n.modelPref.runTarget)
                }
                current = next(after: n.id)
            case .output:
                output = workflowOutput(for: n.kind)
                outputNode = n.id
                current = nil
            }
        }
        guard !steps.isEmpty else { return nil }
        let wf = Workflow(name: name, source: source, steps: steps, output: output)
        return LoweredGraph(workflow: wf, sourceNode: src.id, stepNodes: stepNodes,
                            stepTargets: stepTargets, outputNode: outputNode)
    }

    /// Map a single node to its `WorkflowStep`. Intel nodes lower to `.extract(type)`; the transforms
    /// lower to their direct counterparts; the custom LLM node carries the user's prompt.
    private func step(for n: GraphNode) -> WorkflowStep? {
        switch n.kind {
        case .decisions:    return .extract(.decisions)
        case .actions:      return .extract(.actionItems)
        case .risks:        return .extract(.riskRegister)
        case .questions:    return .lens(.balanced)        // "open questions" — surface via a lens
        case .requirements: return .extract(.requirements)
        case .summarize:    return .summarize
        case .rewrite:      return .rewrite(tone: n.tone)
        case .filter:       return .keepIf(n.keyword)
        case .llm:
            let p = n.prompt.trimmingCharacters(in: .whitespacesAndNewlines)
            // A custom node with no prompt still runs — substitute the input straight through.
            return .llmCall(name: n.kind.title, prompt: p.isEmpty ? "{input}" : p, input: .previousStep)
        default:            return nil
        }
    }

    private func workflowOutput(for kind: NodeKind) -> WorkflowOutput {
        switch kind { case .slack: return .slack; case .note: return .note; default: return .artifacts }
    }

    // MARK: - HSM-22-01 — lower the canvas to a travelling `Blueprint` (graph_json)

    /// A stable id for THIS canvas session, so re-saving after an edit updates the same
    /// synced workflow instead of minting a sibling every save.
    let deskWorkflowID = UUID().uuidString.lowercased()

    /// Walk the same primary source→…→output chain `lowerToWorkflow` runs, but produce
    /// the syncable `Blueprint` — the graph_json wire the hub's linearizer parses.
    /// Linear by construction (exactly the subset the hub runs); each model-op node
    /// carries the inspector's `failure_policy` + `runs_on` so the provenance travels.
    func lowerToBlueprint() -> Blueprint? {
        guard let src = nodes.first(where: { $0.kind.cat == .source }) else { return nil }
        var bpNodes: [BPNode] = [BPNode(id: "entry", kind: .entry),
                                 BPNode(id: "source", kind: .source)]
        var execEdges = [BPExecEdge(from: BPExecPin(node: "entry", name: "then"), to: "source")]
        var prev: BPNodeID = "source"
        var titles: [String] = []

        func next(after id: UUID) -> GraphNode? {
            guard let edge = edges.first(where: { $0.from.node == id }) else { return nil }
            return node(edge.to.node)
        }

        var current = next(after: src.id)
        var index = 0
        var guardCount = 0
        while let n = current, guardCount < nodes.count + 2 {
            guardCount += 1
            switch n.kind.cat {
            case .source:
                current = nil
            case .intel, .transform:
                if let kind = bpKind(for: n) {
                    index += 1
                    let id = "n\(index)"
                    bpNodes.append(BPNode(
                        id: id, kind: kind,
                        failurePolicy: kind.isModelOp ? n.onFail : nil,
                        runsOn: kind.isModelOp ? BPRunsOn(rawValue: n.modelPref.rawValue) : nil))
                    execEdges.append(BPExecEdge(from: BPExecPin(node: prev, name: "then"), to: id))
                    prev = id
                    titles.append(n.kind.title)
                }
                current = next(after: n.id)
            case .output:
                current = nil
            }
        }
        guard index > 0 else { return nil }   // nothing runnable wired yet
        bpNodes.append(BPNode(id: "out", kind: .output))
        execEdges.append(BPExecEdge(from: BPExecPin(node: prev, name: "then"), to: "out"))
        let name = "Canvas · " + titles.prefix(3).joined(separator: " → ")
        return Blueprint(name: name, entry: "entry", nodes: bpNodes, execEdges: execEdges)
    }

    /// The canvas vocabulary → the Blueprint vocabulary. `questions` has no curated
    /// Blueprint node; it lowers to its intent (an open-questions llm call).
    private func bpKind(for n: GraphNode) -> BPNodeKind? {
        switch n.kind {
        case .decisions:    return .extract(.decisions)
        case .actions:      return .extract(.actionItems)
        case .risks:        return .extract(.riskRegister)
        case .requirements: return .extract(.requirements)
        case .questions:    return .llm(name: "Open questions",
                                        prompt: "From {input}, list the sharpest open questions a reviewer should ask. One per line.")
        case .summarize:    return .summarize
        case .rewrite:      return .rewrite(tone: n.tone)
        case .filter:       return .keepIf(keyword: n.keyword)
        case .llm:
            let p = n.prompt.trimmingCharacters(in: .whitespacesAndNewlines)
            return .llm(name: n.kind.title, prompt: p.isEmpty ? "{input}" : p)
        default:            return nil
        }
    }

    // MARK: Run-state drivers (set by the canvas run loop)

    func setRunState(_ id: UUID, _ s: NodeRunState) { if let i = idx(id) { nodes[i].runState = s } }
    func clearRun() {
        for i in nodes.indices { nodes[i].runState = .idle }
        activeEdges.removeAll()
    }
    /// Pulse the outgoing cables of `id` (the node currently working).
    func activateOutgoing(of id: UUID) {
        activeEdges = Set(edges.filter { $0.from.node == id }.map(\.id))
    }
}

/// HSM-14-15 — a seeded **fake** `ILLMProvider` for the demo + the Simulator, where no GGUF is loaded.
/// Real runs use `InferenceConfigStore.shared.makeProvider(...)` (on-device by default — the iPad is a
/// full peer); this exists so the canvas run is demonstrable WITHOUT a model. It returns short, canned
/// text keyed off the prompt, with a small delay so the working-state pulse is visible.
private struct SeededFakeProvider: ILLMProvider {
    let stepDelay: Duration
    init(stepDelay: Duration = .milliseconds(650)) { self.stepDelay = stepDelay }
    func complete(prompt: String) async throws -> String {
        try? await Task.sleep(for: stepDelay)
        let p = prompt.lowercased()
        if p.contains("decision") { return "Decision: ship the v1 canvas runner.\nDecision: keep the model swappable behind ILLMProvider." }
        if p.contains("action") { return "[ ] Wire Run → WorkflowRunner — owner: mobile\n[ ] Drive the Queue HUD from StepOutcome — owner: mobile" }
        if p.contains("risk") || p.contains("question") { return "Risk: a branching graph only runs its main path in v1.\nQuestion: when do we need a real DAG engine?" }
        if p.contains("requirement") { return "Req: the run must reflect REAL runner state, not a faked animation." }
        if p.contains("summar") { return "The Workbench now executes: the canvas lowers to a Workflow and the runner walks it live." }
        if p.contains("rewrite") { return "We shipped on-device workflow execution; the canvas and queue now reflect the real run." }
        return "Open question: which step should own the egress badge when the output is Slack?"
    }
}

/// The canvas — a pannable, pinch-zoomable dot-grid graph with draggable typed nodes and
/// type-colored cables. This is the Workbench.
private struct GraphCanvasView: View {
    @Environment(\.dismiss) private var dismiss
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @StateObject private var model = PatchModel()
    @State private var pan: CGSize = .zero
    @State private var panStart: CGSize = .zero
    @State private var zoom: CGFloat = 1
    @State private var zoomStart: CGFloat = 1
    @State private var inspect: GraphNode?
    @State private var spin = false
    @State private var runTask: Task<Void, Never>?
    @State private var saved = false          // HSM-22-01 — the Save button's settle beat

    var body: some View {
        ZStack {
            Sig.bgGradient.ignoresSafeArea()
            Circle().fill(Sig.accent.opacity(0.12)).frame(width: 460).blur(radius: 150).offset(x: 170, y: -340).ignoresSafeArea()
            graphArea
            VStack(spacing: 0) { header; Spacer(minLength: 0); palette }
        }
        .toolbar(.hidden, for: .navigationBar).tint(Sig.accent)
        .onAppear {
            spin = true
            if model.nodes.isEmpty { seed() }
            #if targetEnvironment(simulator)
            let env = ProcessInfo.processInfo.environment
            if env["HS_DEMO_WB_RUN"] == "1" { model.running = true }
            if env["HS_DEMO_WB_EDIT"] == "1" { inspect = model.nodes.first { $0.kind == .llm } }
            if env["HS_DEMO_WB_RUNTIME"] == "1" { inspect = model.nodes.first { $0.kind == .decisions } }
            // HSM-14-15 — kick off a REAL run with the seeded fake provider so the canvas + Queue HUD
            // show live execution without a loaded model. Open the queue so the HUD is visible.
            if env["HS_DEMO_WB_EXEC"] == "1" {
                RunQueueStore.shared.expanded = true
                startRun()
            }
            // HSM-22-01 screenshot/proof affordance — the same save path the tap runs.
            if env["HS_DEMO_WB_SAVE"] == "1" {
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.8) { saveToDesk() }
            }
            // HSM-15-02 — pin the first model-op node to the paired desktop and run:
            // the SAME startRun the tap runs; with HS_DESKTOP_HOST set (a live local
            // hub) the pinned step genuinely dispatches over /api/ask.
            if env["HS_DEMO_WB_MESH"] == "1" {
                if let i = model.nodes.firstIndex(where: { $0.kind.cat == .intel }) {
                    model.nodes[i].modelPref = .desktop
                }
                RunQueueStore.shared.expanded = true
                startRun()
            }
            #endif
        }
        .sheet(item: $inspect) { n in
            NodeInspectorSheet(model: model, nodeID: n.id).presentationDetents([.height(380), .large])
        }
    }

    // The signal flows left→right; the viewport opens centered on the seeded graph.
    private var graphArea: some View {
        GeometryReader { geo in
            ZStack {
                DotGrid()
                edgeLayer
                nodeLayer
                portHandles
            }
            .frame(width: GraphGeom.canvas.width, height: GraphGeom.canvas.height)
            .coordinateSpace(name: "graph")
            .scaleEffect(zoom)
            .offset(pan)
            .frame(width: geo.size.width, height: geo.size.height)
            .contentShape(Rectangle())
            .gesture(panGesture)
            .simultaneousGesture(zoomGesture)
            .clipped()
        }
    }

    private var header: some View {
        HStack(spacing: 11) {
            Button { tactile(); dismiss() } label: {
                Image(systemName: "chevron.left").font(.system(size: 16, weight: .heavy)).foregroundStyle(Sig.text)
                    .frame(width: 40, height: 40).background(.ultraThinMaterial, in: Circle())
                    .overlay(Circle().strokeBorder(Sig.topHairline, lineWidth: 1))
            }.buttonStyle(PressableCard())
            ZStack {
                Circle().fill(Sig.accent.opacity(0.45)).frame(width: 32, height: 32).blur(radius: 13)
                pixelAsset("crystal", size: 38, fallback: "cube.transparent.fill", tint: .black)
                    .rotationEffect(.degrees(spin ? 360 : 0))
                    .animation(reduceMotion ? nil : .linear(duration: 16).repeatForever(autoreverses: false), value: spin)
            }
            VStack(alignment: .leading, spacing: 1) {
                Text("WORKBENCH").font(.system(size: 9, weight: .heavy)).tracking(1.7).foregroundStyle(Sig.accent)
                Text("Wire up intelligence").font(.system(size: 19, weight: .heavy)).foregroundStyle(Sig.text).lineLimit(1)
            }
            Spacer(minLength: 6)
            saveButton
            runButton
        }
        .padding(.horizontal, 16).padding(.top, 12).padding(.bottom, 14)
        .background(LinearGradient(colors: [Sig.bg, Sig.bg.opacity(0)], startPoint: .top, endPoint: .bottom).ignoresSafeArea(edges: .top))
    }

    // HSM-22-01 — the graph travels: Save lowers the canvas to the canonical
    // graph_json `WorkflowRecord` on the DESK, where the next sync pass ports it to
    // the hub like every other primitive.
    private var saveButton: some View {
        Button {
            tactile(.medium)
            saveToDesk()
        } label: {
            HStack(spacing: 6) {
                Image(systemName: saved ? "checkmark" : "square.and.arrow.down")
                    .font(.system(size: 12, weight: .black))
                Text(saved ? "Saved" : "Save").font(.system(size: 14, weight: .heavy))
            }
            .foregroundStyle(saved ? Sig.ok : Sig.text)
            .padding(.horizontal, 14).padding(.vertical, 10)
            .background(.ultraThinMaterial, in: Capsule())
            .overlay(Capsule().strokeBorder(
                saved ? AnyShapeStyle(Sig.ok.opacity(0.5)) : AnyShapeStyle(Sig.topHairline),
                lineWidth: 1))
        }.buttonStyle(PressableCard())
    }

    private func saveToDesk() {
        guard let blueprint = model.lowerToBlueprint() else {
            print("[Workbench] save: nothing runnable wired source→… yet")
            tactile(.heavy); return
        }
        guard let definition = try? blueprint.workflowDefinition(id: model.deskWorkflowID) else {
            print("[Workbench] save: graph_json lowering failed for '\(blueprint.name)'")
            tactile(.heavy); return
        }
        DeskWorkflowLibrary.upsert(WorkflowRecord(contract: definition))
        print("[Workbench] save: '\(definition.name)' → desk workflow \(definition.id) (graph_json aboard)")
        withAnimation(.spring(response: 0.4, dampingFraction: 0.8)) { saved = true }
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.2) {
            withAnimation { saved = false }
        }
    }

    private var runButton: some View {
        Button {
            tactile(.medium)
            if model.running { stopRun() } else { startRun() }
        } label: {
            HStack(spacing: 6) {
                Image(systemName: model.running ? "stop.fill" : "play.fill").font(.system(size: 12, weight: .black))
                Text(model.running ? "Running" : "Run").font(.system(size: 14, weight: .heavy))
            }
            .foregroundStyle(.black)
            .padding(.horizontal, 16).padding(.vertical, 10)
            .background(Sig.accentGradient, in: Capsule())
            .shadow(color: Sig.accent.opacity(model.running ? 0.65 : 0.3), radius: model.running ? 13 : 6)
        }.buttonStyle(PressableCard())
    }

    private var edgeLayer: some View {
        TimelineView(.animation(paused: !model.running)) { tl in
            Canvas { ctx, _ in
                let t = tl.date.timeIntervalSinceReferenceDate
                for e in model.edges {
                    guard let a = model.portCenter(e.from), let b = model.portCenter(e.to), let ty = model.portType(e.from) else { continue }
                    let path = cablePath(a, b)
                    ctx.drawLayer { l in
                        l.addFilter(.blur(radius: 7))
                        l.stroke(path, with: .color(ty.color.opacity(0.5)), style: StrokeStyle(lineWidth: 6, lineCap: .round))
                    }
                    ctx.stroke(path, with: .color(ty.color.opacity(0.92)), style: StrokeStyle(lineWidth: 2.4, lineCap: .round))
                    // Only the WORKING node's outgoing cables pulse — so the signal visibly travels the
                    // wire the run is on right now (HSM-14-15), not every cable at once.
                    if model.running && model.activeEdges.contains(e.id) {
                        let phase = CGFloat((t * 0.8).truncatingRemainder(dividingBy: 1))
                        let p = cablePoint(a, b, phase)
                        ctx.drawLayer { l in l.addFilter(.blur(radius: 5)); l.fill(Path(ellipseIn: CGRect(x: p.x-6, y: p.y-6, width: 12, height: 12)), with: .color(ty.color)) }
                        ctx.fill(Path(ellipseIn: CGRect(x: p.x-3, y: p.y-3, width: 6, height: 6)), with: .color(.white))
                    }
                }
                if let pend = model.pending, let a = model.portCenter(pend.from), let ty = model.portType(pend.from) {
                    ctx.stroke(cablePath(a, pend.point), with: .color(ty.color.opacity(0.85)),
                               style: StrokeStyle(lineWidth: 2.4, lineCap: .round, dash: [7, 6]))
                    ctx.fill(Path(ellipseIn: CGRect(x: pend.point.x-5, y: pend.point.y-5, width: 10, height: 10)), with: .color(ty.color))
                }
            }
            .frame(width: GraphGeom.canvas.width, height: GraphGeom.canvas.height)
        }
        .allowsHitTesting(false)
    }

    private var nodeLayer: some View {
        ForEach(model.nodes) { n in
            NodeCardView(node: n, selected: model.selected == n.id,
                         onDelete: { withAnimation(.spring(response: 0.4, dampingFraction: 0.8)) { model.remove(n.id) }; tactile() })
                .position(n.pos)
                .gesture(
                    DragGesture(coordinateSpace: .named("graph"))
                        .onChanged { v in
                            if model.dragOrigin[n.id] == nil { model.dragOrigin[n.id] = n.pos; model.selected = n.id }
                            let o = model.dragOrigin[n.id]!
                            model.move(n.id, to: CGPoint(x: o.x + v.translation.width, y: o.y + v.translation.height))
                        }
                        .onEnded { _ in model.dragOrigin[n.id] = nil; tactile() }
                )
                .onTapGesture { tactile(); model.selected = n.id; inspect = n }
        }
    }

    // Invisible grab targets over each output port — drag one to pull a cable to an input.
    private var portHandles: some View {
        ForEach(model.nodes) { n in
            ForEach(Array(n.kind.outputs.enumerated()), id: \.offset) { i, _ in
                let ref = PortRef(node: n.id, isInput: false, index: i)
                if let c = model.portCenter(ref) {
                    Circle().fill(Color.white.opacity(0.001)).frame(width: 42, height: 42).contentShape(Circle())
                        .position(c)
                        .gesture(
                            DragGesture(coordinateSpace: .named("graph"))
                                .onChanged { v in model.pending = (ref, v.location) }
                                .onEnded { v in model.endWire(at: v.location) }
                        )
                }
            }
        }
    }

    private var palette: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 9) {
                ForEach(NodeKind.allCases) { paletteChip($0) }
            }.padding(.horizontal, 18).padding(.vertical, 13)
        }
        .background(.ultraThinMaterial)
        .overlay(LinearGradient(colors: [Sig.accent.opacity(0.45), .clear], startPoint: .top, endPoint: .bottom).frame(height: 1.5), alignment: .top)
    }

    private func paletteChip(_ k: NodeKind) -> some View {
        Button {
            tactile()
            withAnimation(.spring(response: 0.42, dampingFraction: 0.78)) {
                let c = CGPoint(x: GraphGeom.canvas.width/2 - pan.width/zoom + CGFloat.random(in: -44...44),
                                y: GraphGeom.canvas.height/2 - pan.height/zoom + CGFloat.random(in: -34...34))
                model.addNode(k, at: c)
            }
        } label: {
            HStack(spacing: 7) {
                Image(systemName: k.glyph).font(.system(size: 12, weight: .bold))
                Text(k.title).font(.system(size: 13, weight: .heavy))
                Image(systemName: "plus").font(.system(size: 9, weight: .black)).opacity(0.65)
            }
            .foregroundStyle(k == .llm ? .black : k.accent)
            .padding(.horizontal, 13).padding(.vertical, 9)
            .background(k == .llm ? AnyShapeStyle(Sig.accentGradient) : AnyShapeStyle(k.accent.opacity(0.14)), in: Capsule())
            .overlay { if k != .llm { Capsule().strokeBorder(k.accent.opacity(0.35), lineWidth: 1) } }
        }.buttonStyle(PressableCard())
    }

    private var panGesture: some Gesture {
        DragGesture()
            .onChanged { v in pan = CGSize(width: panStart.width + v.translation.width, height: panStart.height + v.translation.height) }
            .onEnded { _ in panStart = pan }
    }
    private var zoomGesture: some Gesture {
        MagnificationGesture()
            .onChanged { m in zoom = min(1.6, max(0.55, zoomStart * m)) }
            .onEnded { _ in zoomStart = zoom }
    }

    // A useful starting program: Transcription fans out to a Decisions lens and a custom LLM call;
    // findings file to the board, the LLM draft becomes a note.
    private func seed() {
        let cx = GraphGeom.canvas.width/2, cy = GraphGeom.canvas.height/2
        let src = GraphNode(.transcription, CGPoint(x: cx - 360, y: cy - 30))
        let dec = GraphNode(.decisions, CGPoint(x: cx - 20, y: cy - 150))
        var llm = GraphNode(.llm, CGPoint(x: cx - 20, y: cy + 80))
        llm.prompt = "From {input}, list the sharpest risks as pointed questions a reviewer should ask. One per line, no preamble."
        let board = GraphNode(.board, CGPoint(x: cx + 330, y: cy - 150))
        let note = GraphNode(.note, CGPoint(x: cx + 330, y: cy + 80))
        model.nodes = [src, dec, llm, board, note]
        func o(_ n: GraphNode, _ i: Int) -> PortRef { PortRef(node: n.id, isInput: false, index: i) }
        func ip(_ n: GraphNode, _ i: Int) -> PortRef { PortRef(node: n.id, isInput: true, index: i) }
        model.edges = [
            GraphEdge(from: o(src, 0), to: ip(dec, 0)),
            GraphEdge(from: o(src, 0), to: ip(llm, 0)),
            GraphEdge(from: o(dec, 0), to: ip(board, 0)),
            GraphEdge(from: o(llm, 0), to: ip(note, 0)),
        ]
    }

    // MARK: - HSM-14-15 — execute the graph through the real WorkflowRunner

    private func stopRun() {
        runTask?.cancel(); runTask = nil
        withAnimation(.easeInOut(duration: 0.3)) { model.running = false }
        model.clearRun()
    }

    /// Lower the canvas to a `Workflow`, build a provider, and run it through `WorkflowRunner`. The
    /// canvas node glow + cable pulse and the app-wide Queue HUD are driven from the REAL per-step
    /// `StepOutcome`s — only the provider is faked (no GGUF in the Simulator).
    private func startRun() {
        guard let lowered = model.lowerToWorkflow() else {
            tactile(.heavy); return   // nothing wired source→…→output yet
        }
        model.clearRun()
        withAnimation(.easeInOut(duration: 0.3)) { model.running = true }
        model.setRunState(lowered.sourceNode, .done)

        runTask = Task { await run(lowered) }
    }

    /// The run loop. We execute step-by-step (one `WorkflowRunner` call per step over the threaded
    /// text) so the UI can light each node + push a `QueuedJob` as it goes — same engine, same failure
    /// policy, just stepped so the run is *visible*. The provider work stays off the main actor.
    private func run(_ lowered: PatchModel.LoweredGraph) async {
        let queue = RunQueueStore.shared
        let runName = lowered.workflow.name
        // The seeded source text the runner reads (the App is source-agnostic; this stands in for the
        // resolved transcript / tacked moments / selection in the demo).
        let sourceText = "Standup transcript: we decided to ship the v1 canvas runner. "
            + "Action: wire Run to WorkflowRunner. Risk: branching graphs only run their main path. "
            + "Open question: when do we need a real DAG engine?"

        // The provider: REAL on-device/endpoint unless the model is absent — then the seeded fake so
        // the run is demonstrable. In the Simulator there is never a GGUF, so we use the fake.
        let provider: ILLMProvider = makeRunProvider()
        // The mesh dispatch (HSM-15-02): a node pinned to "Your Mac" runs its prompt on the
        // paired peer over the hub's ask route. No paired peer → nil, and the step rides its
        // IF-UNREACHABLE policy exactly like an unreachable endpoint.
        var dispatch: MeshDispatch?
        if let client = await DictatePeerStore.shared.client() {
            dispatch = { (prompt: String) async throws -> String in
                let result = try await client.runStep(prompt: prompt)
                guard let out = result.output, !out.isEmpty else {
                    throw HTTPDesktopClient.DesktopClientError.malformed
                }
                return out
            }
        }
        let runner = WorkflowRunner(provider: provider, dispatch: dispatch,
                                    policy: RunPolicy(maxRetries: 1, failurePolicy: .skip))
        let peerName = await DictatePeerStore.shared.displayName

        var threaded = sourceText
        for (i, step) in lowered.workflow.steps.enumerated() {
            if Task.isCancelled { break }
            let nodeID = lowered.stepNodes[i]
            // The job's target label states the STEP's resolved pin (HSM-15-02 — the
            // app-wide default only when the node is unpinned), settled to where it
            // ACTUALLY ran once the outcome lands.
            let stepTarget = i < lowered.stepTargets.count ? lowered.stepTargets[i] : nil
            let target = targetLabel(stepTarget, peerName: peerName)

            // Light the node + its outgoing cable; push a WORKING job.
            model.setRunState(nodeID, .working)
            model.activateOutgoing(of: nodeID)
            // The job's REAL id (a fresh UUID here never matched the inserted job's
            // self-generated id, so rows stayed "working" forever — found in the
            // HSM-15-02 build; the settle below now actually lands).
            let queued = QueuedJob(runName, model.node(nodeID)?.title ?? step.label,
                                   target: target, status: .working, progress: 0.4)
            let jobID = queued.id
            withAnimation(.spring(response: 0.4, dampingFraction: 0.85)) {
                queue.jobs.insert(queued, at: 0)
            }
            tactile(.light)

            // A single-step workflow over the threaded value — REAL runner execution.
            let single = Workflow(name: runName, source: lowered.workflow.source, steps: [step],
                                  output: lowered.workflow.output)
            let result = await runner.run(single, sourceText: threaded, targets: [stepTarget])

            if Task.isCancelled { break }
            let outcome = result.steps.first
            threaded = result.finalText

            // Settle the node + the job from the REAL StepStatus.
            let status: NodeRunState
            let job: JobStatus
            switch outcome?.status {
            case .ok, .fellBack: status = .done; job = .done
            case .skipped:       status = .done; job = .done
            case .parked:        status = .parked; job = .blocked
            default:             status = .failed; job = .failed
            }
            withAnimation(.spring(response: 0.45, dampingFraction: 0.8)) {
                model.setRunState(nodeID, status)
                if let qi = queue.jobs.firstIndex(where: { $0.id == jobID }) {
                    queue.jobs[qi].status = job
                    queue.jobs[qi].progress = 1
                    queue.jobs[qi].note = outcome?.error
                    // Settle the label to where the step ACTUALLY ran (a fallback
                    // means it never left — the badge updates, HSM-15-02 honesty).
                    if let ran = outcome?.ranOn {
                        queue.jobs[qi].target = targetLabel(ran, peerName: peerName)
                    }
                }
            }
            // Hand the pulse to the next node's cables (or clear at the end).
            model.activeEdges.removeAll()
        }

        // The OUTPUT node settles last — the result landed where the graph sends it.
        if !Task.isCancelled, let out = lowered.outputNode {
            withAnimation(.spring(response: 0.45, dampingFraction: 0.8)) { model.setRunState(out, .done) }
        }
        if !Task.isCancelled {
            withAnimation(.easeInOut(duration: 0.4)) { model.running = false }
        }
        runTask = nil
    }

    /// The provider for a real run: on-device / endpoint via Settings, falling back to the seeded fake
    /// when no model is available (always, in the Simulator). Keeps model work off the main actor at
    /// the call site (the runner awaits it on a background `Task`).
    private func makeRunProvider() -> ILLMProvider {
        let cfg = InferenceConfigStore.shared
        #if targetEnvironment(simulator)
        return SeededFakeProvider()   // no GGUF in the Simulator — the run is still real, the model is faked
        #else
        if let p = try? cfg.makeProvider(localModelPath: MeetingReviewState.localGGUF(), context: 16_384) {
            return p
        }
        return SeededFakeProvider()
        #endif
    }

    /// The HUD job's target words for a step's pin (HSM-15-02). An unpinned step
    /// (`nil`) states the app-wide default — the pre-mesh behaviour, now scoped to
    /// exactly the steps that actually follow it.
    private func targetLabel(_ target: RunTarget?, peerName: String) -> String {
        switch target {
        case .dispatchToMac: return peerName
        case .onDevice:      return "On-device"
        case .endpoint:      return "Endpoint"
        case nil:            return InferenceConfigStore.shared.isLocal ? "On-device" : "Endpoint"
        }
    }
}

/// A dim graph-paper dot grid — the canvas's "this is a workspace" texture.
private struct DotGrid: View {
    var body: some View {
        Canvas { ctx, size in
            let step: CGFloat = 34, r: CGFloat = 1.3
            var y: CGFloat = step
            while y < size.height {
                var x: CGFloat = step
                while x < size.width {
                    ctx.fill(Path(ellipseIn: CGRect(x: x-r, y: y-r, width: r*2, height: r*2)), with: .color(.white.opacity(0.05)))
                    x += step
                }
                y += step
            }
        }
        .frame(width: GraphGeom.canvas.width, height: GraphGeom.canvas.height)
        .allowsHitTesting(false)
    }
}

/// One node on the canvas: a Signal card with a typed glyph, a title, and colored I/O ports.
private struct NodeCardView: View {
    let node: GraphNode
    let selected: Bool
    let onDelete: () -> Void
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var pulse = false
    private var k: NodeKind { node.kind }

    // HSM-14-15 — the live run color for this node (nil ⇒ idle, no run treatment).
    private var runColor: Color? {
        switch node.runState {
        case .idle:    return nil
        case .working: return Sig.accent
        case .done:    return Sig.ok
        case .parked:  return Sig.warn
        case .failed:  return Sig.bad
        }
    }
    private var isWorking: Bool { node.runState == .working }

    var body: some View {
        HStack(spacing: 11) {
            GlyphChip(system: k.glyph, gradient: k.grad, size: 40)
            VStack(alignment: .leading, spacing: 2) {
                Text(node.title).font(.system(size: 15, weight: .bold)).foregroundStyle(Sig.text).lineLimit(1)
                if let s = node.subtitle {
                    Text(s).font(.system(size: 10.5, weight: .medium)).foregroundStyle(k == .llm ? Sig.accent : Sig.faint).lineLimit(1)
                } else {
                    Text(k.cat.rawValue).font(.system(size: 8.5, weight: .heavy)).tracking(1).foregroundStyle(Sig.faint)
                }
            }
            Spacer(minLength: 2)
        }
        .padding(.horizontal, 13)
        .frame(width: GraphGeom.nodeW, height: GraphGeom.nodeH)
        .signalCard(Sig.s1, radius: 17)
        .overlay(RoundedRectangle(cornerRadius: 17, style: .continuous)
            .strokeBorder(borderStyle, lineWidth: runColor != nil ? 2.4 : (selected ? 2 : 1)))
        .overlay(ports)
        .overlay(alignment: .topLeading) { runPip }
        .overlay(alignment: .topTrailing) {
            if selected {
                Button { onDelete() } label: {
                    Image(systemName: "xmark.circle.fill").font(.system(size: 19))
                        .symbolRenderingMode(.palette).foregroundStyle(Sig.muted, Sig.s3)
                }.offset(x: 9, y: -9)
            }
        }
        .scaleEffect(isWorking && pulse && !reduceMotion ? 1.035 : 1)
        .shadow(color: runColor?.opacity(isWorking ? 0.6 : 0.4) ?? (selected ? k.accent.opacity(0.3) : .clear),
                radius: runColor != nil ? (isWorking ? 18 : 12) : (selected ? 12 : 0))
        .animation(.easeInOut(duration: 0.5).repeatForever(autoreverses: true), value: pulse)
        .onAppear { pulse = true }
    }

    private var borderStyle: AnyShapeStyle {
        if let c = runColor { return AnyShapeStyle(c) }
        return selected ? AnyShapeStyle(k.accent) : AnyShapeStyle(Sig.topHairline)
    }

    // A small status pip in the corner while/after a run touches this node.
    @ViewBuilder private var runPip: some View {
        if let c = runColor {
            Image(systemName: isWorking ? "bolt.fill"
                  : (node.runState == .done ? "checkmark"
                     : (node.runState == .parked ? "pause.fill" : "xmark")))
                .font(.system(size: 9, weight: .black)).foregroundStyle(.black)
                .frame(width: 19, height: 19).background(c, in: Circle())
                .overlay(Circle().stroke(Sig.bg, lineWidth: 2))
                .offset(x: -7, y: -7)
        }
    }

    private var ports: some View {
        ZStack {
            ForEach(Array(k.inputs.enumerated()), id: \.offset) { i, ty in
                portDot(ty).position(x: 0, y: portY(true, i))
            }
            ForEach(Array(k.outputs.enumerated()), id: \.offset) { i, ty in
                portDot(ty).position(x: GraphGeom.nodeW, y: portY(false, i))
            }
        }
        .frame(width: GraphGeom.nodeW, height: GraphGeom.nodeH)
    }
    private func portY(_ input: Bool, _ i: Int) -> CGFloat {
        let count = input ? k.inputs.count : k.outputs.count
        return GraphGeom.nodeH * CGFloat(i + 1) / CGFloat(count + 1)
    }
    private func portDot(_ ty: PortType) -> some View {
        Circle().fill(ty.color).frame(width: 13, height: 13)
            .overlay(Circle().stroke(Sig.bg, lineWidth: 2.5))
            .shadow(color: ty.color.opacity(0.7), radius: 4)
    }
}

/// The node inspector — tap a node to open it. Configurable nodes (LLM call, Rewrite, Filter) get a
/// real editor; every node shows what it does and its typed I/O (so the language is legible).
private struct NodeInspectorSheet: View {
    @ObservedObject var model: PatchModel
    let nodeID: UUID
    @Environment(\.dismiss) private var dismiss
    @State private var prompt = ""
    @State private var tone = "Executive"
    @State private var keyword = "risk"
    @State private var modelPref: ModelPref = .auto
    @State private var onFail: FailurePolicy = .retryThenQueue
    private let tones = ["Executive", "Plain", "Friendly", "Technical", "Terse"]

    private var node: GraphNode? { model.node(nodeID) }

    var body: some View {
        VStack(spacing: 0) {
            grabber
            if let n = node {
                headerBar(n)
                ScrollView {
                    VStack(alignment: .leading, spacing: 16) {
                        ioRow(n)
                        editor(n)
                        if n.kind.usesModel { runtimeSection(n) }
                        Color.clear.frame(height: 12)
                    }
                    .padding(.horizontal, 20).padding(.top, 6)
                }
            }
        }
        .presentationDetents([.height(440), .large])
        .presentationDragIndicator(.hidden)
        .presentationCornerRadius(30)
        .presentationBackground {
            ZStack {
                Sig.bgGradient
                Circle().fill((node?.kind.accent ?? Sig.accent).opacity(0.16)).frame(width: 360).blur(radius: 130)
                    .offset(x: 120, y: -260)
            }
            .ignoresSafeArea()
        }
        .onAppear { if let n = node { prompt = n.prompt; tone = n.tone; keyword = n.keyword; modelPref = n.modelPref; onFail = n.onFail } }
    }

    private var grabber: some View {
        Capsule().fill(Sig.faint.opacity(0.55)).frame(width: 40, height: 5)
            .padding(.top, 9).padding(.bottom, 4)
    }

    // A designed header — the node's glyph + identity on the left, a real "Done" pill on the right.
    private func headerBar(_ n: GraphNode) -> some View {
        HStack(spacing: 13) {
            GlyphChip(system: n.kind.glyph, gradient: n.kind.grad, size: 46)
            VStack(alignment: .leading, spacing: 2) {
                Text(n.kind.cat.rawValue).font(.system(size: 9, weight: .heavy)).tracking(1.4).foregroundStyle(n.kind.accent)
                Text(n.title).font(.system(size: 22, weight: .heavy)).foregroundStyle(Sig.text)
            }
            Spacer()
            Button { tactile(.medium); commit(); dismiss() } label: {
                Text("Done").font(.system(size: 14, weight: .heavy)).foregroundStyle(.black)
                    .padding(.horizontal, 18).padding(.vertical, 10)
                    .background(Sig.accentGradient, in: Capsule())
                    .shadow(color: Sig.accent.opacity(0.35), radius: 7, y: 3)
            }.buttonStyle(PressableCard())
        }
        .padding(.horizontal, 20).padding(.top, 6).padding(.bottom, 14)
    }

    private func ioRow(_ n: GraphNode) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(n.kind.blurb).font(.system(size: 13, weight: .medium)).foregroundStyle(Sig.muted)
            HStack(spacing: 8) {
                if n.kind.inputs.isEmpty { tinyTag("starts here") }
                ForEach(Array(n.kind.inputs.enumerated()), id: \.offset) { _, t in typePill(t) }
                if !n.kind.inputs.isEmpty && !n.kind.outputs.isEmpty {
                    Image(systemName: "arrow.right").font(.system(size: 10, weight: .black)).foregroundStyle(Sig.faint)
                }
                ForEach(Array(n.kind.outputs.enumerated()), id: \.offset) { _, t in typePill(t) }
                if n.kind.outputs.isEmpty { tinyTag("ends here") }
            }
        }
        .padding(14).frame(maxWidth: .infinity, alignment: .leading).signalCard(Sig.s1, radius: 16)
    }
    private func tinyTag(_ s: String) -> some View {
        Text(s).font(.system(size: 11, weight: .bold)).foregroundStyle(Sig.faint)
            .padding(.horizontal, 10).padding(.vertical, 6).background(Sig.s3, in: Capsule())
    }
    private func typePill(_ t: PortType) -> some View {
        HStack(spacing: 6) {
            Circle().fill(t.color).frame(width: 8, height: 8)
            Text(t.label).font(.system(size: 11, weight: .bold)).foregroundStyle(Sig.text)
        }
        .padding(.horizontal, 10).padding(.vertical, 6)
        .background(t.color.opacity(0.12), in: Capsule())
        .overlay(Capsule().strokeBorder(t.color.opacity(0.3), lineWidth: 1))
    }

    @ViewBuilder private func editor(_ n: GraphNode) -> some View {
        switch n.kind {
        case .llm:
            section("PROMPT") {
                ZStack(alignment: .topLeading) {
                    if prompt.isEmpty {
                        Text("What should the model do? Use {input}.")
                            .font(.system(size: 14)).foregroundStyle(Sig.faint).padding(.horizontal, 9).padding(.vertical, 12)
                    }
                    TextEditor(text: $prompt).font(.system(size: 14)).foregroundStyle(Sig.text)
                        .scrollContentBackground(.hidden).frame(minHeight: 130).padding(5)
                }
                .background(Sig.s2, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
                .overlay(RoundedRectangle(cornerRadius: 14).strokeBorder(Sig.topHairline, lineWidth: 1))
                .overlay(alignment: .bottomTrailing) { VoiceFillMic(text: $prompt, tint: Sig.accent, size: 28).padding(9) }
                Button { prompt += (prompt.isEmpty ? "" : " ") + "{input}" } label: {
                    Label("Insert {input}", systemImage: "curlybraces").font(.system(size: 12, weight: .bold))
                        .foregroundStyle(Sig.accent).padding(.horizontal, 12).padding(.vertical, 7)
                        .background(Sig.accent.opacity(0.12), in: Capsule())
                }.buttonStyle(PressableCard())
            }
        case .rewrite:
            section("TONE") { chipRow(tones.map { ($0, $0, "") }, selected: tone) { tone = $0 } }
        case .filter:
            section("KEEP LINES CONTAINING") {
                TextField("keyword", text: $keyword).font(.system(size: 15, weight: .semibold)).foregroundStyle(Sig.text)
                    .padding(14).background(Sig.s2, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
                    .overlay(RoundedRectangle(cornerRadius: 14).strokeBorder(Sig.topHairline, lineWidth: 1))
                    .autocorrectionDisabled().textInputAutocapitalization(.never)
            }
        default:
            EmptyView()
        }
    }

    // The runtime contract for a model-backed node: where it runs, and what happens if that's down.
    private func runtimeSection(_ n: GraphNode) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            section("RUNS ON") {
                chipRow(ModelPref.allCases.map { ($0.rawValue, $0.label, $0.glyph) }, selected: modelPref.rawValue) {
                    if let p = ModelPref(rawValue: $0) { modelPref = p }
                }
                Text(modelPref.hint).font(.system(size: 12, weight: .medium)).foregroundStyle(Sig.faint)
            }
            section("IF UNREACHABLE") {
                chipRow(FailurePolicy.allCases.map { ($0.rawValue, $0.label, $0.glyph) }, selected: onFail.rawValue) {
                    if let p = FailurePolicy(rawValue: $0) { onFail = p }
                }
                Text(onFail.hint).font(.system(size: 12, weight: .medium)).foregroundStyle(Sig.faint)
            }
        }
        .padding(15).frame(maxWidth: .infinity, alignment: .leading).signalCard(Sig.s1, radius: 16)
        .overlay(RoundedRectangle(cornerRadius: 16).strokeBorder(Sig.accent.opacity(0.16), lineWidth: 1))
    }

    @ViewBuilder private func section<C: View>(_ title: String, @ViewBuilder _ content: () -> C) -> some View {
        VStack(alignment: .leading, spacing: 9) {
            Text(title).font(.system(size: 10, weight: .heavy)).tracking(1.2).foregroundStyle(Sig.faint)
            content()
        }
    }

    // A horizontal row of selectable chips: (id, label, sf-glyph). Glyph optional ("").
    private func chipRow(_ options: [(String, String, String)], selected: String, _ pick: @escaping (String) -> Void) -> some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(options, id: \.0) { opt in
                    let on = opt.0 == selected
                    Button { tactile(); withAnimation(.spring(response: 0.3, dampingFraction: 0.8)) { pick(opt.0) } } label: {
                        HStack(spacing: 6) {
                            if !opt.2.isEmpty { Image(systemName: opt.2).font(.system(size: 11, weight: .bold)) }
                            Text(opt.1).font(.system(size: 13, weight: .heavy))
                        }
                        .foregroundStyle(on ? .black : Sig.muted)
                        .padding(.horizontal, 13).padding(.vertical, 9)
                        .background(on ? AnyShapeStyle(Sig.accentGradient) : AnyShapeStyle(Sig.s2), in: Capsule())
                        .overlay { if !on { Capsule().strokeBorder(Sig.topHairline, lineWidth: 1) } }
                    }.buttonStyle(PressableCard())
                }
            }.padding(.bottom, 1)
        }
    }

    private func commit() {
        guard let i = model.idx(nodeID) else { return }
        model.nodes[i].prompt = prompt
        model.nodes[i].tone = tone
        model.nodes[i].keyword = keyword
        model.nodes[i].modelPref = modelPref
        model.nodes[i].onFail = onFail
    }
}

/// The Workbench: a node-based visual language for composing intelligence. Hosts the graph canvas.
/// HSM-14-16 — this is now the Blueprints canvas (v2): a real two-wire (exec + typed data) visual
/// programming editor that lowers to `Blueprint` and runs through `BlueprintInterpreter` live.
struct WorkbenchView: View {
    // v2 (BlueprintCanvasView) is mid-build + demo-gated; the home uses the working v1 until v2 is
    // finished and device-walked. (Recording-first: paused the canvas to fix the core.)
    var body: some View { GraphCanvasView() }
}

// MARK: - HSM-14-16 — the Blueprints canvas (Workbench v2)
//
// A draw.io-grade visual programming editor on top of the shipped `Blueprint`/`BlueprintInterpreter`
// engine. TWO wire kinds, Unreal-Blueprints style:
//   • EXEC pins (white, arrow) — control flow. Every node has one exec-in + named exec-outs.
//   • DATA pins (colored circles, one per `BPDataType`) — typed values; connections are type-checked.
// Drag an exec-out → an exec-in to make a white exec wire; a data-out → a data-in to make a colored
// data wire (rejected with a haptic + flash if the `BPDataType`s don't match). Run lowers the canvas
// to a `Blueprint`, runs it through `BlueprintInterpreter`, and drives the canvas LIVE off the real
// `ExecutionEvent` stream: the active node ignites, statuses recolor, branches light the taken path
// and dim the other, for-each shows a live n/total, a glowing token travels the active exec wire.

// MARK: Blueprints palette vocabulary

/// One palette entry: a `BPNodeKind` template + its presentation. Grouped into the five rails the
/// owner asked for (Sources · Intelligence · Control flow · Transforms · Outputs).
private enum BPPaletteItem: String, CaseIterable, Identifiable {
    case source
    case llm, extractDecisions, extractActions, summarize, rewrite
    case branch, forEach, whileLoop, sequence, merge
    case keepIf, splitIntoItems
    case output
    var id: String { rawValue }

    enum Group: String, CaseIterable { case sources = "SOURCES", intel = "INTELLIGENCE", control = "CONTROL FLOW", transforms = "TRANSFORMS", outputs = "OUTPUTS" }

    var group: Group {
        switch self {
        case .source:                                   return .sources
        case .llm, .extractDecisions, .extractActions, .summarize, .rewrite: return .intel
        case .branch, .forEach, .whileLoop, .sequence, .merge:               return .control
        case .keepIf, .splitIntoItems:                  return .transforms
        case .output:                                   return .outputs
        }
    }

    /// A fresh model kind for this palette item (with sensible defaults the inspector can edit).
    func makeKind() -> BPNodeKind {
        switch self {
        case .source:           return .source
        case .llm:              return .llm(name: "LLM call", prompt: "From {input}, list the sharpest open questions a reviewer should ask. One per line.")
        case .extractDecisions: return .extract(.decisions)
        case .extractActions:   return .extract(.actionItems)
        case .summarize:        return .summarize
        case .rewrite:          return .rewrite(tone: "Executive")
        case .branch:           return .branch(condition: .contains(keyword: "risk"))
        case .forEach:          return .forEach
        case .whileLoop:        return .whileLoop(condition: .isNonEmpty, maxIterations: 3)
        case .sequence:         return .sequence(count: 2)
        case .merge:            return .merge
        case .keepIf:           return .keepIf(keyword: "risk")
        case .splitIntoItems:   return .splitIntoItems
        case .output:           return .output
        }
    }

    var title: String {
        switch self {
        case .source: return "Source"; case .llm: return "LLM call"
        case .extractDecisions: return "Decisions"; case .extractActions: return "Action items"
        case .summarize: return "Summarize"; case .rewrite: return "Rewrite"
        case .branch: return "Branch"; case .forEach: return "For-each"; case .whileLoop: return "While"
        case .sequence: return "Sequence"; case .merge: return "Merge"
        case .keepIf: return "Keep if"; case .splitIntoItems: return "Split items"; case .output: return "Output"
        }
    }
    var glyph: String {
        switch self {
        case .source: return "waveform"; case .llm: return "terminal.fill"
        case .extractDecisions: return "checkmark.seal.fill"; case .extractActions: return "checklist"
        case .summarize: return "text.append"; case .rewrite: return "pencil.and.outline"
        case .branch: return "arrow.triangle.branch"; case .forEach: return "repeat"; case .whileLoop: return "arrow.2.circlepath"
        case .sequence: return "list.number"; case .merge: return "arrow.triangle.merge"
        case .keepIf: return "line.3.horizontal.decrease.circle"; case .splitIntoItems: return "square.split.2x1"; case .output: return "tray.full.fill"
        }
    }
}

/// The look of a `BPNodeKind` on the canvas — its accent + gradient, keyed off the five families.
private enum BPNodeStyle {
    static func family(_ kind: BPNodeKind) -> BPPaletteItem.Group {
        switch kind {
        case .entry, .source:                       return .sources
        case .llm, .extract, .summarize, .rewrite:  return .intel
        case .branch, .forEach, .whileLoop, .sequence, .merge: return .control
        case .keepIf, .splitIntoItems:              return .transforms
        case .output:                               return .outputs
        }
    }
    static func accent(_ kind: BPNodeKind) -> Color {
        switch family(kind) {
        case .sources:    return Sig.local
        case .intel:      return Sig.ok
        case .control:    return Color(hex: 0xC08BFF)   // a distinct violet for control flow
        case .transforms: return Sig.accent
        case .outputs:    return Sig.warn
        }
    }
    static func gradient(_ kind: BPNodeKind) -> LinearGradient {
        let a = accent(kind)
        return LinearGradient(colors: [a.opacity(0.85), a], startPoint: .topLeading, endPoint: .bottomTrailing)
    }
    static func glyph(_ kind: BPNodeKind) -> String {
        switch kind {
        case .entry:        return "play.fill"
        case .source:       return "waveform"
        case .llm:          return "terminal.fill"
        case .extract:      return "checkmark.seal.fill"
        case .summarize:    return "text.append"
        case .rewrite:      return "pencil.and.outline"
        case .branch:       return "arrow.triangle.branch"
        case .forEach:      return "repeat"
        case .whileLoop:    return "arrow.2.circlepath"
        case .sequence:     return "list.number"
        case .merge:        return "arrow.triangle.merge"
        case .keepIf:       return "line.3.horizontal.decrease.circle"
        case .splitIntoItems: return "square.split.2x1"
        case .output:       return "tray.full.fill"
        }
    }
    static func title(_ kind: BPNodeKind) -> String {
        switch kind {
        case .entry:                 return "Start"
        case .source:                return "Source"
        case .llm(let n, _):         return n
        case .extract(let t):        return artifactTypeLabel(t)
        case .summarize:             return "Summarize"
        case .rewrite(let tone):     return "Rewrite"
        case .branch:                return "Branch"
        case .forEach:               return "For-each"
        case .whileLoop:             return "While"
        case .sequence:              return "Sequence"
        case .merge:                 return "Merge"
        case .keepIf:                return "Keep if"
        case .splitIntoItems:        return "Split items"
        case .output:                return "Output"
        }
    }
    static func subtitle(_ kind: BPNodeKind) -> String? {
        switch kind {
        case .llm(_, let p):
            let t = p.trimmingCharacters(in: .whitespacesAndNewlines)
            return t.isEmpty ? "tap to write a prompt" : "\u{201C}\(t.prefix(30))\(t.count > 30 ? "\u{2026}" : "")\u{201D}"
        case .branch(let c):     return conditionLabel(c)
        case .whileLoop(let c, let n): return "\(conditionLabel(c)) · ≤\(n)"
        case .rewrite(let tone): return "tone · \(tone.lowercased())"
        case .keepIf(let kw):    return "keep · \(kw)"
        case .sequence(let n):   return "\(n) branches"
        default:                 return nil
        }
    }
    static func conditionLabel(_ c: BPCondition) -> String {
        switch c {
        case .contains(let kw): return "contains \u{201C}\(kw)\u{201D}"
        case .isEmpty:          return "is empty"
        case .isNonEmpty:       return "has content"
        case .countAtLeast(let n): return "count ≥ \(n)"
        }
    }
}

private extension BPDataType {
    var color: Color {
        switch self { case .text: return Sig.accent; case .collection: return Sig.local; case .bool: return Color(hex: 0xC08BFF) }
    }
    var label: String { rawValue }
}

// MARK: Canvas geometry + pin model

private enum BPGeom {
    static let nodeW: CGFloat = 210
    static let rowH: CGFloat = 26          // height of one pin row
    static let headerH: CGFloat = 52
    static let canvas = CGSize(width: 3200, height: 2200)
}

/// A reference to one pin on a placed node, for hit-testing + cable endpoints.
private struct BPPinRef: Equatable {
    enum Kind: Equatable { case execIn, execOut(String), dataIn(String), dataOut }
    let node: BPNodeID
    let kind: Kind
    var isOutput: Bool { switch kind { case .execOut, .dataOut: return true; default: return false } }
    var isExec: Bool { switch kind { case .execIn, .execOut: return true; default: return false } }
}

/// The placed node: the engine `BPNode` + a canvas position. The model is the source of truth for
/// pin layout (so geometry + the lowered `Blueprint` never disagree).
private struct BPPlaced: Identifiable, Equatable {
    var node: BPNode
    var pos: CGPoint
    var id: BPNodeID { node.id }

    /// The data-in pin names this node exposes (left side, below the exec-in).
    var dataInNames: [String] {
        switch node.kind {
        case .entry, .source:   return []
        case .forEach:          return ["collection"]
        default:                return node.kind.dataInType != nil ? ["in"] : []
        }
    }
    /// Whether this node exposes a data-out (right side).
    var hasDataOut: Bool { node.kind.dataOutType != nil }
    var execOutNames: [String] { node.kind.execOutNames }

    /// Total card height = header + the taller of (exec-outs, data rows).
    var height: CGFloat {
        let rightRows = execOutNames.count + (hasDataOut ? 1 : 0)
        let leftRows = 1 + dataInNames.count                       // exec-in + data-ins
        return BPGeom.headerH + CGFloat(max(rightRows, leftRows, 1)) * BPGeom.rowH + 8
    }
}

// MARK: The canvas model — graph + wiring + lowering + live run state

@MainActor private final class BPCanvasModel: ObservableObject {
    @Published var placed: [BPPlaced] = []
    @Published var execEdges: [BPExecEdge] = []
    @Published var dataEdges: [BPDataEdge] = []
    @Published var selected: BPNodeID?
    @Published var entry: BPNodeID = "entry"

    // In-flight wire drag: the source pin + the live cursor point (canvas space).
    @Published var pending: (from: BPPinRef, point: CGPoint)?
    // A brief red flash + location when a bad (type-mismatched / illegal) connection is rejected.
    @Published var rejection: (point: CGPoint, t: Date)?

    // Live-run state (driven by ExecutionEvents).
    @Published var running = false
    @Published var status: [BPNodeID: BPNodeStatus] = [:]
    @Published var activeNode: BPNodeID?
    @Published var litExecEdges: Set<Int> = []           // indices into execEdges that are "taken"
    @Published var tokenEdge: Int?                        // exec edge the glowing token is travelling
    @Published var branchTaken: [BPNodeID: Bool] = [:]    // a branch node → which exec-out fired
    @Published var loopCounter: [BPNodeID: (Int, Int?)] = [:]  // forEach/while → (index, total?)
    @Published var finished = false

    var dragOrigin: [BPNodeID: CGPoint] = [:]

    func placed(_ id: BPNodeID) -> BPPlaced? { placed.first { $0.id == id } }
    func idx(_ id: BPNodeID) -> Int? { placed.firstIndex { $0.id == id } }

    // MARK: Pin geometry — the model owns it so the lowered graph + the canvas agree.

    /// The center of a pin in canvas coordinates. Exec-in is row 0 on the left; data-ins follow.
    /// On the right, exec-outs come first, then the data-out.
    func pinCenter(_ ref: BPPinRef) -> CGPoint? {
        guard let p = placed(ref.node) else { return nil }
        let left = p.pos.x - BPGeom.nodeW / 2
        let right = p.pos.x + BPGeom.nodeW / 2
        let top = p.pos.y - p.height / 2
        func rowY(_ i: Int) -> CGFloat { top + BPGeom.headerH + BPGeom.rowH * (CGFloat(i) + 0.5) }
        switch ref.kind {
        case .execIn:
            return CGPoint(x: left, y: rowY(0))
        case .dataIn(let name):
            guard let di = p.dataInNames.firstIndex(of: name) else { return nil }
            return CGPoint(x: left, y: rowY(1 + di))
        case .execOut(let name):
            guard let oi = p.execOutNames.firstIndex(of: name) else { return nil }
            return CGPoint(x: right, y: rowY(oi))
        case .dataOut:
            guard p.hasDataOut else { return nil }
            return CGPoint(x: right, y: rowY(p.execOutNames.count))
        }
    }

    /// Enumerate every pin on every node, with its center — for the draggable hit targets + dots.
    func allPins() -> [(BPPinRef, CGPoint)] {
        var out: [(BPPinRef, CGPoint)] = []
        for p in placed {
            let refs: [BPPinRef.Kind] =
                [.execIn]
                + p.dataInNames.map { .dataIn($0) }
                + p.execOutNames.map { .execOut($0) }
                + (p.hasDataOut ? [.dataOut] : [])
            for k in refs {
                let r = BPPinRef(node: p.id, kind: k)
                if let c = pinCenter(r) { out.append((r, c)) }
            }
        }
        return out
    }

    func move(_ id: BPNodeID, to point: CGPoint) {
        guard let i = idx(id) else { return }
        let x = min(max(point.x, BPGeom.nodeW/2 + 8), BPGeom.canvas.width - BPGeom.nodeW/2 - 8)
        let h = placed[i].height
        let y = min(max(point.y, h/2 + 8), BPGeom.canvas.height - h/2 - 8)
        placed[i].pos = CGPoint(x: x, y: y)
    }

    // MARK: Wiring — start at an output pin, drop near a compatible input pin.

    func beginWire(from ref: BPPinRef, at point: CGPoint) { pending = (ref, point) }
    func dragWire(to point: CGPoint) { pending?.point = point }

    /// Finish a wire. Snaps to the nearest input pin of the matching wire family within reach.
    /// EXEC-out → exec-in makes a white exec edge. DATA-out → data-in makes a colored data edge,
    /// TYPE-CHECKED: a mismatch (or any illegal pairing) is rejected with a haptic + a red flash.
    func endWire(at point: CGPoint) {
        defer { pending = nil }
        guard let pend = pending else { return }
        let from = pend.from
        guard from.isOutput else { reject(at: point); return }

        // Find the nearest compatible-family INPUT pin within snap distance.
        var best: (BPPinRef, CGFloat)?
        for (ref, c) in allPins() where !ref.isOutput && ref.node != from.node && ref.isExec == from.isExec {
            let d = hypot(c.x - point.x, c.y - point.y)
            if d < 52, best == nil || d < best!.1 { best = (ref, d) }
        }
        guard let (target, _) = best else { reject(at: point); return }

        if from.isExec {
            connectExec(from: from, to: target)
        } else {
            connectData(from: from, to: target, at: point)
        }
    }

    private func connectExec(from: BPPinRef, to: BPPinRef) {
        guard case .execOut(let name) = from.kind, case .execIn = to.kind else { return }
        let pin = BPExecPin(node: from.node, name: name)
        execEdges.removeAll { $0.from == pin }           // one wire per exec-out
        execEdges.append(BPExecEdge(from: pin, to: to.node))
        tactile(.medium)
    }

    private func connectData(from: BPPinRef, to: BPPinRef, at point: CGPoint) {
        guard case .dataOut = from.kind, case .dataIn(let inName) = to.kind,
              let fromNode = placed(from.node)?.node, let toNode = placed(to.node)?.node,
              let outT = fromNode.kind.dataOutType, let inT = toNode.kind.dataInType else { reject(at: point); return }
        // TYPE CHECK — the heart of the data-wire contract. A collection-out into a text-in (etc.)
        // is refused; no silent bad wires.
        guard outT == inT else { reject(at: point); return }
        let toPin = BPDataPin(node: to.node, name: inName)
        dataEdges.removeAll { $0.to == toPin }           // one wire per data-in
        dataEdges.append(BPDataEdge(from: BPDataPin(node: from.node, name: "out"), to: toPin))
        tactile(.medium)
    }

    private func reject(at point: CGPoint) {
        rejection = (point, Date())
        tactile(.heavy)
    }

    // MARK: Add / remove nodes

    private var counter = 0
    func addNode(_ item: BPPaletteItem, at point: CGPoint) {
        counter += 1
        let id = "\(item.rawValue)-\(counter)"
        var node = BPNode(id: id, kind: item.makeKind())
        node.failurePolicy = .skip
        placed.append(BPPlaced(node: node, pos: point))
        selected = id
    }

    func remove(_ id: BPNodeID) {
        guard id != entry else { tactile(.heavy); return }   // never delete the start
        execEdges.removeAll { $0.from.node == id || $0.to == id }
        dataEdges.removeAll { $0.from.node == id || $0.to.node == id }
        placed.removeAll { $0.id == id }
        if selected == id { selected = nil }
    }

    /// Mutate a node's kind in place (the inspector commits through here).
    func update(_ id: BPNodeID, _ transform: (inout BPNode) -> Void) {
        guard let i = idx(id) else { return }
        transform(&placed[i].node)
    }

    // MARK: Lower the canvas to the engine `Blueprint`

    func lower(name: String = "Blueprint run") -> Blueprint {
        Blueprint(id: blueprintID, name: name, entry: entry,
                  nodes: placed.map(\.node), execEdges: execEdges, dataEdges: dataEdges)
    }
    /// A stable id so a re-run streams `runStarted(blueprint:)` for the same graph.
    let blueprintID = UUID()

    // MARK: Live-run drivers (set by the event consumer)

    func resetRun() {
        status.removeAll(); activeNode = nil; litExecEdges.removeAll(); tokenEdge = nil
        branchTaken.removeAll(); loopCounter.removeAll(); finished = false
    }

    /// Light the exec edge whose `from` pin matches (node, outName) — the path control just took.
    func lightExec(from node: BPNodeID, out name: String) {
        let pin = BPExecPin(node: node, name: name)
        if let i = execEdges.firstIndex(where: { $0.from == pin }) {
            litExecEdges.insert(i)
            tokenEdge = i
        }
    }
}

/// HSM-14-16 — a seeded fake `ILLMProvider` for the Blueprints canvas in the Simulator / when no GGUF
/// is loaded. Returns short, branch-relevant canned text with a small delay so the live trace is
/// watchable. Real device runs use `InferenceConfigStore.makeProvider(...)`.
private struct BPSeededProvider: ILLMProvider {
    var stepDelay: Duration = .milliseconds(520)
    func complete(prompt: String) async throws -> String {
        try? await Task.sleep(for: stepDelay)
        let p = prompt.lowercased()
        if p.contains("decision") { return "Decision: ship the Blueprints canvas.\nDecision: keep the model behind ILLMProvider." }
        if p.contains("action")   { return "[ ] Wire Run to BlueprintInterpreter — owner: mobile\n[ ] Drive the live trace off ExecutionEvent" }
        if p.contains("question") { return "Open question: when do we need a real diamond merge?\nQuestion: should loops fan out on the mesh?" }
        if p.contains("summar")   { return "The Workbench is a real visual program: exec + typed data wires, control flow, a live trace." }
        if p.contains("rewrite")  { return "We shipped the Blueprints canvas; runs reflect the real interpreter, branch and loop included." }
        return "Risk: a branch only lights the taken path.\nRisk: loops must stay bounded."
    }
}

// MARK: The Blueprints canvas view

private struct BlueprintCanvasView: View {
    @Environment(\.dismiss) private var dismiss
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @StateObject private var model = BPCanvasModel()
    @State private var pan: CGSize = .zero
    @State private var panStart: CGSize = .zero
    @State private var zoom: CGFloat = 0.82
    @State private var zoomStart: CGFloat = 0.82
    @State private var inspect: BPNodeID?
    @State private var spin = false
    @State private var runTask: Task<Void, Never>?
    @State private var flourish = false

    var body: some View {
        ZStack {
            Sig.bgGradient.ignoresSafeArea()
            Circle().fill(Sig.accent.opacity(0.10)).frame(width: 480).blur(radius: 160).offset(x: 170, y: -360).ignoresSafeArea()
            Circle().fill(Color(hex: 0xC08BFF).opacity(0.08)).frame(width: 420).blur(radius: 160).offset(x: -200, y: 260).ignoresSafeArea()
            graphArea
            VStack(spacing: 0) { header; Spacer(minLength: 0); palette }
            if flourish { completionFlourish.transition(.opacity).allowsHitTesting(false) }
        }
        .toolbar(.hidden, for: .navigationBar).tint(Sig.accent)
        .onAppear {
            spin = true
            if model.placed.isEmpty { seed() }
            #if targetEnvironment(simulator)
            let env = ProcessInfo.processInfo.environment
            if env["HS_DEMO_BP_EDIT"] == "1" { inspect = model.placed.first { if case .llm = $0.node.kind { return true }; return false }?.id }
            if env["HS_DEMO_BP_RUN"] == "1" { startRun() }
            #endif
        }
        .sheet(item: Binding(get: { inspect.map(BPSheetID.init) }, set: { inspect = $0?.id })) { s in
            BPNodeInspector(model: model, nodeID: s.id)
        }
        .topBack { dismiss() }
    }

    // A wrapper so a String id is `Identifiable` for `.sheet(item:)`.
    private struct BPSheetID: Identifiable { let id: BPNodeID }

    private var graphArea: some View {
        GeometryReader { geo in
            ZStack {
                BPDotGrid()
                edgeLayer
                nodeLayer
                pinHandles
                rejectionFlash
            }
            .frame(width: BPGeom.canvas.width, height: BPGeom.canvas.height)
            .coordinateSpace(name: "bp")
            .scaleEffect(zoom)
            .offset(pan)
            .frame(width: geo.size.width, height: geo.size.height)
            .contentShape(Rectangle())
            .gesture(panGesture)
            .simultaneousGesture(zoomGesture)
            .clipped()
        }
    }

    private var header: some View {
        HStack(spacing: 11) {
            Spacer().frame(width: 64)   // clear the topBack chip
            ZStack {
                Circle().fill(Sig.accent.opacity(0.4)).frame(width: 30, height: 30).blur(radius: 13)
                pixelAsset("crystal", size: 34, fallback: "point.3.connected.trianglepath.dotted", tint: Sig.accent)
                    .rotationEffect(.degrees(spin ? 360 : 0))
                    .animation(reduceMotion ? nil : .linear(duration: 18).repeatForever(autoreverses: false), value: spin)
            }
            VStack(alignment: .leading, spacing: 1) {
                Text("BLUEPRINTS").font(.system(size: 9, weight: .heavy)).tracking(1.8).foregroundStyle(Sig.accent)
                Text("Compose intelligence").font(.system(size: 18, weight: .heavy)).foregroundStyle(Sig.text).lineLimit(1)
            }
            Spacer(minLength: 6)
            runButton
        }
        .padding(.horizontal, 16).padding(.top, 12).padding(.bottom, 14)
        .background(LinearGradient(colors: [Sig.bg, Sig.bg.opacity(0)], startPoint: .top, endPoint: .bottom).ignoresSafeArea(edges: .top))
    }

    private var runButton: some View {
        Button {
            tactile(.medium)
            if model.running { stopRun() } else { startRun() }
        } label: {
            HStack(spacing: 6) {
                Image(systemName: model.running ? "stop.fill" : "play.fill").font(.system(size: 12, weight: .black))
                Text(model.running ? "Running" : "Run").font(.system(size: 14, weight: .heavy))
            }
            .foregroundStyle(.black)
            .padding(.horizontal, 16).padding(.vertical, 10)
            .background(Sig.accentGradient, in: Capsule())
            .shadow(color: Sig.accent.opacity(model.running ? 0.65 : 0.3), radius: model.running ? 14 : 6)
        }.buttonStyle(PressableCard())
    }

    // MARK: Edge layer — bezier cables, white for exec, colored for data, with a travelling token.

    private var edgeLayer: some View {
        TimelineView(.animation(paused: !model.running)) { tl in
            Canvas { ctx, _ in
                let t = tl.date.timeIntervalSinceReferenceDate
                // Data wires (colored) under the exec wires.
                for e in model.dataEdges {
                    guard let a = model.pinCenter(BPPinRef(node: e.from.node, kind: .dataOut)),
                          let b = model.pinCenter(BPPinRef(node: e.to.node, kind: .dataIn(e.to.name))),
                          let ty = model.placed(e.from.node)?.node.kind.dataOutType else { continue }
                    let path = cablePath(a, b)
                    ctx.drawLayer { l in l.addFilter(.blur(radius: 6)); l.stroke(path, with: .color(ty.color.opacity(0.45)), style: StrokeStyle(lineWidth: 5, lineCap: .round)) }
                    ctx.stroke(path, with: .color(ty.color.opacity(0.9)), style: StrokeStyle(lineWidth: 2.2, lineCap: .round, dash: [1, 6]))
                }
                // Exec wires (white). Taken edges glow; the token rides the active one.
                for (i, e) in model.execEdges.enumerated() {
                    guard let a = model.pinCenter(BPPinRef(node: e.from.node, kind: .execOut(e.from.name))),
                          let b = model.pinCenter(BPPinRef(node: e.to, kind: .execIn)) else { continue }
                    let path = cablePath(a, b)
                    let lit = model.litExecEdges.contains(i)
                    let baseColor: Color = lit ? Sig.accent : .white
                    let dim = (model.running && !lit && model.tokenEdge != nil) ? 0.16 : (lit ? 0.95 : 0.6)
                    if lit { ctx.drawLayer { l in l.addFilter(.blur(radius: 8)); l.stroke(path, with: .color(Sig.accent.opacity(0.55)), style: StrokeStyle(lineWidth: 7, lineCap: .round)) } }
                    ctx.stroke(path, with: .color(baseColor.opacity(dim)), style: StrokeStyle(lineWidth: lit ? 3 : 2.2, lineCap: .round))
                    drawArrowHead(ctx: ctx, at: b, from: a, color: baseColor.opacity(dim))
                    if model.running && model.tokenEdge == i {
                        let phase = CGFloat((t * 1.1).truncatingRemainder(dividingBy: 1))
                        let p = cablePoint(a, b, phase)
                        ctx.drawLayer { l in l.addFilter(.blur(radius: 6)); l.fill(Path(ellipseIn: CGRect(x: p.x-7, y: p.y-7, width: 14, height: 14)), with: .color(Sig.accent)) }
                        ctx.fill(Path(ellipseIn: CGRect(x: p.x-3.5, y: p.y-3.5, width: 7, height: 7)), with: .color(.white))
                    }
                }
                // The in-flight wire being dragged.
                if let pend = model.pending, let a = model.pinCenter(pend.from) {
                    let col: Color = pend.from.isExec ? .white : (model.placed(pend.from.node)?.node.kind.dataOutType?.color ?? Sig.accent)
                    ctx.stroke(cablePath(a, pend.point), with: .color(col.opacity(0.85)),
                               style: StrokeStyle(lineWidth: 2.4, lineCap: .round, dash: [7, 6]))
                    ctx.fill(Path(ellipseIn: CGRect(x: pend.point.x-5, y: pend.point.y-5, width: 10, height: 10)), with: .color(col))
                }
            }
            .frame(width: BPGeom.canvas.width, height: BPGeom.canvas.height)
        }
        .allowsHitTesting(false)
    }

    private func drawArrowHead(ctx: GraphicsContext, at b: CGPoint, from a: CGPoint, color: Color) {
        let ang = atan2(0, b.x - a.x)   // cables enter horizontally
        let size: CGFloat = 7
        var tri = Path()
        tri.move(to: b)
        tri.addLine(to: CGPoint(x: b.x - size*cos(ang - 0.5), y: b.y - size*sin(ang - 0.5)))
        tri.addLine(to: CGPoint(x: b.x - size*cos(ang + 0.5), y: b.y - size*sin(ang + 0.5)))
        tri.closeSubpath()
        ctx.fill(tri, with: .color(color))
    }

    private var nodeLayer: some View {
        ForEach(model.placed) { p in
            BPNodeCard(placed: p,
                       selected: model.selected == p.id,
                       status: model.status[p.id],
                       active: model.activeNode == p.id,
                       branch: model.branchTaken[p.id],
                       loop: model.loopCounter[p.id],
                       onDelete: { withAnimation(.spring(response: 0.4, dampingFraction: 0.8)) { model.remove(p.id) }; tactile() })
                .position(p.pos)
                .gesture(
                    DragGesture(coordinateSpace: .named("bp"))
                        .onChanged { v in
                            if model.dragOrigin[p.id] == nil { model.dragOrigin[p.id] = p.pos; model.selected = p.id }
                            let o = model.dragOrigin[p.id]!
                            model.move(p.id, to: CGPoint(x: o.x + v.translation.width, y: o.y + v.translation.height))
                        }
                        .onEnded { _ in model.dragOrigin[p.id] = nil; tactile() }
                )
                .onTapGesture { tactile(); model.selected = p.id; inspect = p.id }
        }
    }

    // Invisible grab targets over each OUTPUT pin — drag to pull a wire to an input.
    private var pinHandles: some View {
        ForEach(Array(model.allPins().enumerated()), id: \.offset) { _, entry in
            let (ref, c) = entry
            if ref.isOutput {
                Circle().fill(Color.white.opacity(0.001)).frame(width: 44, height: 44).contentShape(Circle())
                    .position(c)
                    .gesture(
                        DragGesture(coordinateSpace: .named("bp"))
                            .onChanged { v in model.beginWire(from: ref, at: v.location); model.dragWire(to: v.location) }
                            .onEnded { v in model.endWire(at: v.location) }
                    )
            }
        }
    }

    @ViewBuilder private var rejectionFlash: some View {
        if let r = model.rejection {
            BPRejectBadge(at: r.point, stamp: r.t)
        }
    }

    private var palette: some View {
        VStack(spacing: 0) {
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 14) {
                    ForEach(BPPaletteItem.Group.allCases, id: \.self) { g in paletteGroup(g) }
                }.padding(.horizontal, 18).padding(.vertical, 13)
            }
        }
        .background(.ultraThinMaterial)
        .overlay(LinearGradient(colors: [Sig.accent.opacity(0.4), .clear], startPoint: .top, endPoint: .bottom).frame(height: 1.5), alignment: .top)
    }

    private func paletteGroup(_ g: BPPaletteItem.Group) -> some View {
        VStack(alignment: .leading, spacing: 7) {
            Text(g.rawValue).font(.system(size: 8.5, weight: .heavy)).tracking(1.3).foregroundStyle(Sig.faint)
            HStack(spacing: 8) {
                ForEach(BPPaletteItem.allCases.filter { $0.group == g }) { paletteChip($0) }
            }
        }
    }

    private func paletteChip(_ item: BPPaletteItem) -> some View {
        let accent = BPNodeStyle.accent(item.makeKind())
        return Button {
            tactile()
            withAnimation(.spring(response: 0.42, dampingFraction: 0.78)) {
                let c = CGPoint(x: BPGeom.canvas.width/2 - pan.width/zoom + CGFloat.random(in: -50...50),
                                y: BPGeom.canvas.height/2 - pan.height/zoom + CGFloat.random(in: -40...40))
                model.addNode(item, at: c)
            }
        } label: {
            HStack(spacing: 6) {
                Image(systemName: item.glyph).font(.system(size: 11, weight: .bold))
                Text(item.title).font(.system(size: 12.5, weight: .heavy))
                Image(systemName: "plus").font(.system(size: 8, weight: .black)).opacity(0.6)
            }
            .foregroundStyle(accent)
            .padding(.horizontal, 11).padding(.vertical, 8)
            .background(accent.opacity(0.13), in: Capsule())
            .overlay(Capsule().strokeBorder(accent.opacity(0.35), lineWidth: 1))
        }.buttonStyle(PressableCard())
    }

    private var completionFlourish: some View {
        VStack {
            Spacer()
            HStack(spacing: 9) {
                Image(systemName: "checkmark.seal.fill").font(.system(size: 16, weight: .bold)).foregroundStyle(Sig.ok)
                Text("Run complete").font(.system(size: 15, weight: .heavy)).foregroundStyle(Sig.text)
            }
            .padding(.horizontal, 18).padding(.vertical, 12)
            .background(.ultraThinMaterial, in: Capsule())
            .overlay(Capsule().strokeBorder(Sig.ok.opacity(0.4), lineWidth: 1))
            .shadow(color: Sig.ok.opacity(0.4), radius: 16)
            Spacer().frame(height: 150)
        }
    }

    private var panGesture: some Gesture {
        DragGesture()
            .onChanged { v in pan = CGSize(width: panStart.width + v.translation.width, height: panStart.height + v.translation.height) }
            .onEnded { _ in panStart = pan }
    }
    private var zoomGesture: some Gesture {
        MagnificationGesture()
            .onChanged { m in zoom = min(1.5, max(0.5, zoomStart * m)) }
            .onEnded { _ in zoomStart = zoom }
    }

    // MARK: The seed — a believable starter Blueprint with real control flow.
    //
    // Source → split into items → For-each (body: keep-if "risk" → an LLM rewrite of the item),
    // completed → Branch (contains "decision") → true: extract Decisions → Output; false: Summarize → Output.
    // Demonstrates a loop AND a branch with two output paths.
    private func seed() {
        let cx = BPGeom.canvas.width/2, cy = BPGeom.canvas.height/2
        func n(_ id: String, _ k: BPNodeKind, _ x: CGFloat, _ y: CGFloat, _ fp: FailurePolicy? = nil) -> BPPlaced {
            var node = BPNode(id: id, kind: k); node.failurePolicy = fp ?? .skip
            return BPPlaced(node: node, pos: CGPoint(x: cx + x, y: cy + y))
        }
        let entry  = n("entry",  .entry,                       -780, -40)
        let source = n("source", .source,                      -560, -40)
        let split  = n("split",  .splitIntoItems,              -330, -40)
        let each   = n("each",   .forEach,                     -110, -40)
        let keep   = n("keep",   .keepIf(keyword: "risk"),      80,  120)
        let rwrite = n("rewrite",.rewrite(tone: "Executive"),  330,  120)
        let branch = n("branch", .branch(condition: .contains(keyword: "decision")), 170, -180)
        let dec    = n("dec",    .extract(.decisions),          440, -260)
        let summ   = n("summ",   .summarize,                    440, -90)
        let outA   = n("outA",   .output,                       720, -260)
        let outB   = n("outB",   .output,                       720, -90)
        model.placed = [entry, source, split, each, keep, rwrite, branch, dec, summ, outA, outB]
        model.entry = "entry"

        func ex(_ from: String, _ out: String, _ to: String) -> BPExecEdge {
            BPExecEdge(from: BPExecPin(node: from, name: out), to: to)
        }
        func da(_ from: String, _ to: String, _ inName: String = "in") -> BPDataEdge {
            BPDataEdge(from: BPDataPin(node: from, name: "out"), to: BPDataPin(node: to, name: inName))
        }
        model.execEdges = [
            ex("entry", "then", "source"),
            ex("source", "then", "split"),
            ex("split", "then", "each"),
            ex("each", "body", "keep"),
            ex("keep", "then", "rewrite"),
            ex("each", "completed", "branch"),
            ex("branch", "true", "dec"),
            ex("branch", "false", "summ"),
            ex("dec", "then", "outA"),
            ex("summ", "then", "outB"),
        ]
        model.dataEdges = [
            da("split", "each", "collection"),    // collection → forEach
            da("each", "keep"),                     // current item → keep-if (text)
            da("keep", "rewrite"),                  // text → rewrite
            da("dec", "outA"),
            da("summ", "outB"),
        ]
    }

    // MARK: Run — lower → interpret → drive the canvas off the ExecutionEvent stream.

    private func stopRun() {
        runTask?.cancel(); runTask = nil
        withAnimation(.easeInOut(duration: 0.3)) { model.running = false }
        model.resetRun()
    }

    private func startRun() {
        runTask?.cancel()
        model.resetRun()
        withAnimation(.easeInOut(duration: 0.3)) { model.running = true }
        flourish = false
        let blueprint = model.lower()
        let sourceText = "Standup transcript. Decision: ship the Blueprints canvas. "
            + "Risk: branching graphs only light the taken path. Action: wire Run to the interpreter. "
            + "Risk: loops must stay bounded. Open question: do we need a true diamond merge?"
        let provider = makeRunProvider()
        runTask = Task { await consume(blueprint: blueprint, sourceText: sourceText, provider: provider) }
    }

    /// Subscribe to the interpreter's `ExecutionEvent` AsyncStream and animate the canvas live.
    /// Every animation below is driven by a REAL event (not a scripted timeline):
    ///   • nodeEntered   → set the active node (ignite/scale) + light the exec wire that reached it
    ///   • nodeStatus    → recolor the node (running / done / skipped / failed)
    ///   • branchTaken   → record which exec-out fired (the card shows ✓/✗) + light that path, dim the other
    ///   • loopIteration → update the For-each card's live n/total counter
    ///   • runFinished   → completion flourish + haptic
    private func consume(blueprint: Blueprint, sourceText: String, provider: ILLMProvider) async {
        let queue = RunQueueStore.shared
        let runName = "Blueprint run"
        let target = InferenceConfigStore.shared.isLocal ? "On-device" : "Endpoint"
        let interp = BlueprintInterpreter(provider: provider, policy: RunPolicy(maxRetries: 1, failurePolicy: .skip))

        for await ev in interp.events(blueprint, sourceText: sourceText) {
            if Task.isCancelled { break }
            switch ev {
            case .runStarted:
                break
            case .nodeEntered(let id):
                withAnimation(.spring(response: 0.35, dampingFraction: 0.7)) {
                    model.activeNode = id
                    model.status[id] = .running
                }
                // Light the exec wire that just reached this node (the path taken).
                if let edgeIdx = model.execEdges.firstIndex(where: { $0.to == id && model.status[$0.from.node] != nil }) {
                    withAnimation(.easeInOut(duration: 0.25)) {
                        model.litExecEdges.insert(edgeIdx); model.tokenEdge = edgeIdx
                    }
                }
                tactile(.light)
                if let node = model.placed(id)?.node, node.kind.isModelOp {
                    withAnimation(.spring(response: 0.4, dampingFraction: 0.85)) {
                        queue.jobs.insert(QueuedJob(runName, BPNodeStyle.title(node.kind), target: target, status: .working, progress: 0.4), at: 0)
                    }
                }
            case .nodeStatus(let id, let s):
                withAnimation(.spring(response: 0.4, dampingFraction: 0.8)) { model.status[id] = s }
                if s != .running, model.activeNode == id { model.activeNode = nil }
                if s == .done || s == .skipped || s == .failed {
                    if let qi = queue.jobs.firstIndex(where: { $0.step == BPNodeStyle.title(model.placed(id)?.node.kind ?? .merge) && $0.status == .working }) {
                        queue.jobs[qi].status = (s == .failed ? .failed : .done); queue.jobs[qi].progress = 1
                    }
                }
            case .branchTaken(let id, let took):
                withAnimation(.spring(response: 0.4, dampingFraction: 0.8)) {
                    model.branchTaken[id] = took
                    model.lightExec(from: id, out: took ? "true" : "false")
                }
                tactile(.medium)
            case .loopIteration(let id, let index, let count):
                withAnimation(.spring(response: 0.3, dampingFraction: 0.8)) { model.loopCounter[id] = (index + 1, count) }
                tactile(.light)
            case .nodeProduced:
                break
            case .runFinished:
                withAnimation(.easeInOut(duration: 0.4)) { model.running = false; model.tokenEdge = nil; model.finished = true; flourish = true }
                tactile(.heavy)
                runTask = nil
                Task { try? await Task.sleep(for: .seconds(2)); await MainActor.run { withAnimation { flourish = false } } }
            case .runFailed(let msg):
                withAnimation(.easeInOut(duration: 0.4)) { model.running = false; model.tokenEdge = nil }
                _ = msg
                tactile(.heavy)
                runTask = nil
            }
        }
    }

    private func makeRunProvider() -> ILLMProvider {
        #if targetEnvironment(simulator)
        return BPSeededProvider()
        #else
        if let p = try? InferenceConfigStore.shared.makeProvider(localModelPath: MeetingReviewState.localGGUF(), context: 16_384) { return p }
        return BPSeededProvider()
        #endif
    }
}

/// A dim graph-paper dot grid for the Blueprints canvas.
private struct BPDotGrid: View {
    var body: some View {
        Canvas { ctx, size in
            let step: CGFloat = 36, r: CGFloat = 1.3
            var y: CGFloat = step
            while y < size.height {
                var x: CGFloat = step
                while x < size.width {
                    ctx.fill(Path(ellipseIn: CGRect(x: x-r, y: y-r, width: r*2, height: r*2)), with: .color(.white.opacity(0.045)))
                    x += step
                }
                y += step
            }
        }
        .frame(width: BPGeom.canvas.width, height: BPGeom.canvas.height)
        .allowsHitTesting(false)
    }
}

/// A short-lived red flash where a bad connection was refused (type mismatch / illegal pairing).
private struct BPRejectBadge: View {
    let at: CGPoint
    let stamp: Date
    @State private var show = false
    var body: some View {
        Group {
            if show {
                HStack(spacing: 5) {
                    Image(systemName: "xmark.octagon.fill").font(.system(size: 12, weight: .bold))
                    Text("type mismatch").font(.system(size: 11, weight: .heavy))
                }
                .foregroundStyle(.white)
                .padding(.horizontal, 11).padding(.vertical, 7)
                .background(Sig.bad, in: Capsule())
                .shadow(color: Sig.bad.opacity(0.6), radius: 10)
                .position(at)
                .transition(.scale.combined(with: .opacity))
            }
        }
        .onChange(of: stamp) { _, _ in flash() }
        .onAppear { flash() }
    }
    private func flash() {
        withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) { show = true }
        Task { try? await Task.sleep(for: .milliseconds(1100)); await MainActor.run { withAnimation { show = false } } }
    }
}

// Minimal leaf views to keep the mid-build v2 canvas compiling (it's demo-gated only). They get
// fully built when the Blueprints canvas resumes — recording-first paused that work.
private struct BPNodeCard: View {
    let placed: BPPlaced
    let selected: Bool
    let status: BPNodeStatus?
    let active: Bool
    let branch: Bool?
    let loop: (Int, Int?)?
    let onDelete: () -> Void
    var body: some View {
        Text(String("\(placed.node.kind)".prefix(18)))
            .font(.system(size: 13, weight: .bold)).foregroundStyle(Sig.text)
            .padding(12).frame(width: 168, height: 60)
            .signalCard(Sig.s1, radius: 16)
            .overlay(RoundedRectangle(cornerRadius: 16, style: .continuous)
                .strokeBorder(selected || active ? AnyShapeStyle(Sig.accent) : AnyShapeStyle(Sig.topHairline),
                              lineWidth: selected || active ? 2 : 1))
    }
}
private struct BPNodeInspector: View {
    @ObservedObject var model: BPCanvasModel
    let nodeID: BPNodeID
    @Environment(\.dismiss) private var dismiss
    var body: some View {
        VStack(spacing: 14) {
            Text("Node").font(.system(size: 18, weight: .heavy)).foregroundStyle(Sig.text)
            Button("Done") { dismiss() }.tint(Sig.accent)
        }.padding(24).presentationDetents([.medium])
    }
}
