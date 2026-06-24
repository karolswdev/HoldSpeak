import Foundation
import Contracts

/// HSM-14 (Workbench v2) — **the Blueprints model**. Where the linear `Workflow`
/// (still shipped, still driven by `WorkflowRunner`) reads strictly top-to-bottom, a
/// `Blueprint` is the richer **graph**: an Unreal-Blueprints-style two-wire program with
/// real control flow (branches, loops, sequences) and typed data plumbing.
///
/// This file is the PURE, `Codable` DATA MODEL. The `BlueprintInterpreter` (sibling file)
/// is the execution engine. Both are additive — they do not touch `Workflow`/`WorkflowRunner`.
///
/// Two wire kinds (the whole point):
///  - **exec edges** carry *control flow* — the ORDER nodes fire in. Each node has one
///    exec-in and zero-or-more *named* exec-outs (`then`, `true`/`false`, `body`/`completed`…).
///  - **data edges** carry *values* — typed. A node's data-out connects to a downstream
///    node's data-in and is resolved **pull-based** (a data-in pulls its upstream's value,
///    memoized per run).
///
/// Everything is `Codable` so a Blueprint (and the live `ExecutionEvent` trace) can ride the
/// App canvas AND the mesh transport ("whoever is watching").

// MARK: - Pins & ports (the wire vocabulary)

/// The kinds of value a data pin carries. Deliberately tiny but real: the engine threads
/// `text`, builds/consumes `collection`s (forEach), and evaluates `bool` conditions.
/// (Design note: we keep this a closed enum rather than a generic type system — the simplest
/// thing that supports the shipped node set and is type-checkable.)
public enum BPDataType: String, Codable, Sendable, Equatable, CaseIterable {
    case text          // a single string (the threaded model value)
    case collection    // an ordered list of strings (forEach iterates these)
    case bool          // a condition result
}

/// A reference to one named exec-out on a node. (Exec-in is implicit — every node has one.)
public struct BPExecPin: Codable, Sendable, Equatable, Hashable {
    public var node: BPNodeID
    public var name: String     // "then" / "true" / "false" / "body" / "completed" / "0".."n"
    public init(node: BPNodeID, name: String) { self.node = node; self.name = name }
}

/// A reference to one named data pin (in OR out) on a node.
public struct BPDataPin: Codable, Sendable, Equatable, Hashable {
    public var node: BPNodeID
    public var name: String     // "in" / "value" / "out" / "item" …
    public init(node: BPNodeID, name: String) { self.node = node; self.name = name }
}

public typealias BPNodeID = String

// MARK: - Edges

/// A control-flow wire: when `from` (a named exec-out) fires, control proceeds to `to`'s
/// exec-in.
public struct BPExecEdge: Codable, Sendable, Equatable, Hashable {
    public var from: BPExecPin   // a node's named exec-out
    public var to: BPNodeID      // the downstream node's (implicit) exec-in
    public init(from: BPExecPin, to: BPNodeID) { self.from = from; self.to = to }
}

/// A data wire: `to` (a data-in) pulls its value from `from` (a data-out). Type-checked.
public struct BPDataEdge: Codable, Sendable, Equatable, Hashable {
    public var from: BPDataPin   // a node's data-out
    public var to: BPDataPin     // a node's data-in
    public init(from: BPDataPin, to: BPDataPin) { self.from = from; self.to = to }
}

// MARK: - Conditions

/// A small, pure condition evaluated over a resolved `text`/`collection` input. Real but
/// minimal — enough for branch/while to be meaningful without a full expression language.
public enum BPCondition: Codable, Sendable, Equatable {
    case contains(keyword: String)   // text (case-insensitive) contains the keyword
    case isEmpty                     // the resolved input is empty / whitespace-only
    case isNonEmpty                  // the resolved input has content
    case countAtLeast(Int)           // collection (or non-empty lines) count >= n

    /// Evaluate against a resolved value. `text` is the scalar form; `lines` the split form
    /// the engine passes so `countAtLeast` counts items, not characters.
    public func evaluate(text: String, lines: [String]) -> Bool {
        switch self {
        case .contains(let kw):
            guard !kw.isEmpty else { return false }
            return text.lowercased().contains(kw.lowercased())
        case .isEmpty:
            return text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        case .isNonEmpty:
            return !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        case .countAtLeast(let n):
            return lines.count >= n
        }
    }
}

// MARK: - Node kinds

/// What a node does. Focused but real: a source of input, model ops (custom `llm` + curated
/// extract/summarize/rewrite reusing the `Workflow` vocabulary), pure transforms, the
/// control-flow family, and a sink.
///
/// Control-flow nodes name their exec-outs (the interpreter follows them):
///  - `branch`  → "true" / "false"
///  - `forEach` → "body" (per item) then "completed"
///  - `whileLoop` → "body" (per pass, bounded) then "completed"
///  - `sequence(n)` → "0","1",…,"n-1" in order
///  - others (entry/source/model/transform/merge) → "then"
public enum BPNodeKind: Codable, Sendable, Equatable {
    case entry                                            // exec-out: "then". The run's start.
    case source                                           // provides the run input text. exec-out "then".
    // Model ops — call the injected ILLMProvider.
    case llm(name: String, prompt: String)                // CUSTOM: {input} substitution. exec-out "then".
    case extract(ArtifactType)                            // curated. exec-out "then".
    case summarize                                        // exec-out "then".
    case rewrite(tone: String)                            // exec-out "then".
    // Pure transforms — no model.
    case keepIf(keyword: String)                          // keep lines mentioning keyword. exec-out "then".
    case splitIntoItems                                   // text → collection (one item per non-empty line). exec-out "then".
    // Control flow.
    case branch(condition: BPCondition)                   // exec-outs "true"/"false".
    case forEach                                          // data-in "collection"; exec-outs "body","completed".
    case whileLoop(condition: BPCondition, maxIterations: Int)  // bounded. exec-outs "body","completed".
    case sequence(count: Int)                             // exec-outs "0".."count-1" in order, then "then".
    case merge                                            // join branches back. exec-out "then".
    case output                                           // sink. exec-out "then" (usually none).

    /// The named exec-outs this kind exposes, in declaration order.
    public var execOutNames: [String] {
        switch self {
        case .branch:               return ["true", "false"]
        case .forEach, .whileLoop:  return ["body", "completed"]
        case .sequence(let n):      return (0..<max(0, n)).map(String.init) + ["then"]
        case .output:               return []
        default:                    return ["then"]
        }
    }

    /// The data-OUT type this kind produces (what downstream data-ins can pull), if any.
    public var dataOutType: BPDataType? {
        switch self {
        case .entry, .merge, .output, .branch, .whileLoop: return nil
        case .splitIntoItems:                              return .collection
        case .forEach:                                     return .text   // the current item, bound during "body"
        default:                                           return .text   // source / model ops / keepIf / sequence
        }
    }

    /// The data-IN type this kind expects on its primary data-in (`"in"`/`"collection"`), if any.
    public var dataInType: BPDataType? {
        switch self {
        case .entry, .source:           return nil
        case .forEach:                  return .collection
        case .branch, .whileLoop:       return .text     // condition reads its resolved text input
        default:                        return .text
        }
    }

    public var isModelOp: Bool {
        switch self { case .llm, .extract, .summarize, .rewrite: return true; default: return false }
    }
}

/// One node in the Blueprint graph.
public struct BPNode: Codable, Sendable, Equatable, Identifiable {
    public var id: BPNodeID
    public var kind: BPNodeKind
    /// Per-node failure policy override (reuses `WorkflowRunner`'s `FailurePolicy`). `nil`
    /// inherits the run's default. Only meaningful on model ops.
    public var failurePolicy: FailurePolicy?

    public init(id: BPNodeID, kind: BPNodeKind, failurePolicy: FailurePolicy? = nil) {
        self.id = id; self.kind = kind; self.failurePolicy = failurePolicy
    }

    /// A data-out pin reference for this node (name "out").
    public func out(_ name: String = "out") -> BPDataPin { BPDataPin(node: id, name: name) }
    /// A data-in pin reference (name "in" by default).
    public func dataIn(_ name: String = "in") -> BPDataPin { BPDataPin(node: id, name: name) }
    /// A named exec-out pin reference.
    public func exec(_ name: String = "then") -> BPExecPin { BPExecPin(node: id, name: name) }
}

// MARK: - The Blueprint

/// A complete graph program: nodes + the two wire sets + the entry node.
public struct Blueprint: Codable, Sendable, Equatable, Identifiable {
    public var id: UUID
    public var name: String
    public var entry: BPNodeID
    public var nodes: [BPNode]
    public var execEdges: [BPExecEdge]
    public var dataEdges: [BPDataEdge]

    public init(id: UUID = UUID(), name: String, entry: BPNodeID,
                nodes: [BPNode], execEdges: [BPExecEdge] = [], dataEdges: [BPDataEdge] = []) {
        self.id = id; self.name = name; self.entry = entry
        self.nodes = nodes; self.execEdges = execEdges; self.dataEdges = dataEdges
    }

    public func node(_ id: BPNodeID) -> BPNode? { nodes.first { $0.id == id } }

    /// The node reached by following the named exec-out `pin` (nil if the wire is unconnected).
    public func execTarget(from pin: BPExecPin) -> BPNodeID? {
        execEdges.first { $0.from == pin }?.to
    }

    /// The data-out feeding `pin` (a data-in), nil if unconnected.
    public func dataSource(into pin: BPDataPin) -> BPDataPin? {
        dataEdges.first { $0.to == pin }?.from
    }

    // MARK: Validation (type-check the data edges)

    public enum ValidationError: Error, Equatable, CustomStringConvertible {
        case missingEntry(BPNodeID)
        case danglingEdgeNode(BPNodeID)
        case typeMismatch(from: BPDataPin, out: BPDataType, to: BPDataPin, expected: BPDataType)

        public var description: String {
            switch self {
            case .missingEntry(let id):           return "entry node '\(id)' not found"
            case .danglingEdgeNode(let id):       return "edge references unknown node '\(id)'"
            case .typeMismatch(let f, let o, let t, let e):
                return "data type mismatch: \(f.node).\(f.name) is \(o.rawValue) but \(t.node).\(t.name) expects \(e.rawValue)"
            }
        }
    }

    /// Static, model-only validation (no provider). Catches a missing entry, dangling edge
    /// endpoints, and **data-type mismatches** (a `collection`-out wired into a `text`-in).
    public func validate() -> ValidationError? {
        let ids = Set(nodes.map(\.id))
        guard ids.contains(entry) else { return .missingEntry(entry) }
        for e in execEdges {
            if !ids.contains(e.from.node) { return .danglingEdgeNode(e.from.node) }
            if !ids.contains(e.to)        { return .danglingEdgeNode(e.to) }
        }
        for e in dataEdges {
            guard let fromNode = node(e.from.node) else { return .danglingEdgeNode(e.from.node) }
            guard let toNode   = node(e.to.node)   else { return .danglingEdgeNode(e.to.node) }
            if let outT = fromNode.kind.dataOutType, let inT = toNode.kind.dataInType, outT != inT {
                return .typeMismatch(from: e.from, out: outT, to: e.to, expected: inT)
            }
        }
        return nil
    }
}
