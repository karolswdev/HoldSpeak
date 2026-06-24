import Foundation
import Contracts
import Providers

/// HSM-14 (Workbench v2) — **the Blueprints interpreter**. Walks the `Blueprint`'s exec
/// graph from `entry`, following exec edges and evaluating the control-flow family (branch /
/// forEach / whileLoop / sequence / merge). Model nodes call the **injected `ILLMProvider`**
/// (a fake in tests); data-in pins resolve **pull-based** (memoized per run). It threads an
/// `ExecutionContext` (active node, per-node status, the path taken, loop counters) and emits
/// a stream of `Codable` `ExecutionEvent`s so a UI OR the mesh can watch the run live.
///
/// Control-flow superset of `WorkflowRunner` (the linear runner), ADDITIVE — neither touches
/// the other. Reuses `FailurePolicy`/`RunPolicy` from `WorkflowRunner.swift`.
///
/// Every loop is **bounded** (forEach by collection size, while by `maxIterations`, and a
/// global `maxSteps` guards against an exec cycle) — the interpreter never hangs.

// MARK: - Execution events (the live-trace contract — Codable, mesh-rideable)

/// A node's lifecycle state during a run.
public enum BPNodeStatus: String, Codable, Sendable, Equatable {
    case pending, running, done, skipped, failed
}

/// A small, ordered, `Codable` event. The interpreter emits these as it walks; a UI renders
/// them and the same stream can ride the mesh to "whoever is watching".
public enum ExecutionEvent: Codable, Sendable, Equatable {
    case runStarted(blueprint: UUID)
    case nodeEntered(id: BPNodeID)
    case nodeStatus(id: BPNodeID, status: BPNodeStatus)
    case branchTaken(id: BPNodeID, took: Bool)               // true = "true" exec-out, false = "false"
    case loopIteration(id: BPNodeID, index: Int, count: Int?) // count nil for while (unknown ahead)
    case nodeProduced(id: BPNodeID, preview: String)          // a short preview of the node's value
    case runFinished(summary: String)
    case runFailed(message: String)
}

// MARK: - Execution context (threaded run state)

/// The mutable run state the interpreter threads. Captures the active node(s), per-node
/// status, the path taken (in fire order), and per-loop iteration counters — everything a
/// live canvas or the mesh needs to render the run.
public struct ExecutionContext: Sendable {
    public private(set) var activeNodes: [BPNodeID] = []          // currently running (stack-ish)
    public private(set) var status: [BPNodeID: BPNodeStatus] = [:]
    public private(set) var pathTaken: [BPNodeID] = []           // every node entered, in order
    public private(set) var loopCounters: [BPNodeID: Int] = [:]   // node id → iterations run
    public var stepsTaken: Int = 0                               // global bound guard

    public init() {}

    mutating func enter(_ id: BPNodeID) {
        activeNodes.append(id)
        pathTaken.append(id)
        status[id] = .running
        stepsTaken += 1
    }
    mutating func leave(_ id: BPNodeID, _ s: BPNodeStatus) {
        status[id] = s
        if let i = activeNodes.lastIndex(of: id) { activeNodes.remove(at: i) }
    }
    mutating func markPending(_ id: BPNodeID) { if status[id] == nil { status[id] = .pending } }
    mutating func bumpLoop(_ id: BPNodeID) -> Int {
        let n = (loopCounters[id] ?? 0) + 1; loopCounters[id] = n; return n
    }
}

// MARK: - Run result

public struct BlueprintRunResult: Sendable, Equatable {
    public var blueprintID: UUID
    public var finalText: String
    public var pathTaken: [BPNodeID]
    public var status: [BPNodeID: BPNodeStatus]
    public var loopCounters: [BPNodeID: Int]
    public var failure: String?

    public init(blueprintID: UUID, finalText: String, pathTaken: [BPNodeID],
                status: [BPNodeID: BPNodeStatus], loopCounters: [BPNodeID: Int], failure: String? = nil) {
        self.blueprintID = blueprintID; self.finalText = finalText; self.pathTaken = pathTaken
        self.status = status; self.loopCounters = loopCounters; self.failure = failure
    }
    public var didComplete: Bool { failure == nil }
}

public enum BlueprintRunError: Error, Equatable {
    case validation(String)        // the blueprint failed static validation
    case stepBudgetExceeded(Int)   // the global exec-step bound tripped (cycle guard)
    case modelFailed(String)       // a model op failed unrecoverably under its policy
}

// MARK: - The interpreter

/// Interprets a `Blueprint`. **Pure**: all run state lives on the call (an `ExecutionContext`
/// + a per-run data memo), so one interpreter instance is reusable and `Sendable`.
public struct BlueprintInterpreter: Sendable {

    private let provider: ILLMProvider
    private let fallback: ILLMProvider?
    private let policy: RunPolicy
    /// Hard global bound on exec steps — guards against an exec cycle the static validator
    /// can't see (a `merge` wired back into an earlier node). Generous; only trips on a true loop.
    private let maxSteps: Int

    public init(provider: ILLMProvider, fallback: ILLMProvider? = nil,
                policy: RunPolicy = RunPolicy(), maxSteps: Int = 10_000) {
        self.provider = provider; self.fallback = fallback
        self.policy = policy; self.maxSteps = maxSteps
    }

    /// Run `blueprint` over `sourceText` (the resolved SOURCE — the App supplies it). Returns
    /// the result AND streams every `ExecutionEvent` via `onEvent`. (A callback sink — the
    /// caller can forward to an `AsyncStream` continuation for a UI, or onto the mesh. See the
    /// `events(...)` convenience below for a ready-made `AsyncStream`.)
    @discardableResult
    public func run(_ blueprint: Blueprint,
                    sourceText: String,
                    onEvent: @Sendable (ExecutionEvent) -> Void = { _ in }) async -> BlueprintRunResult {

        if let v = blueprint.validate() {
            onEvent(.runStarted(blueprint: blueprint.id))
            onEvent(.runFailed(message: v.description))
            return BlueprintRunResult(blueprintID: blueprint.id, finalText: sourceText,
                                      pathTaken: [], status: [:], loopCounters: [:],
                                      failure: v.description)
        }

        var ctx = ExecutionContext()
        // Pull-based data memo: a node id → its produced scalar value, computed once per run.
        // `loopItem` overlays the current forEach item for nodes inside a body subgraph.
        var memo = DataMemo(blueprint: blueprint, sourceText: sourceText)

        onEvent(.runStarted(blueprint: blueprint.id))
        for n in blueprint.nodes { ctx.markPending(n.id) }

        do {
            try await walk(from: blueprint.entry, blueprint: blueprint,
                           ctx: &ctx, memo: &memo, onEvent: onEvent)
        } catch let err as BlueprintRunError {
            let msg = describe(err)
            onEvent(.runFailed(message: msg))
            return BlueprintRunResult(blueprintID: blueprint.id, finalText: memo.lastProduced,
                                      pathTaken: ctx.pathTaken, status: ctx.status,
                                      loopCounters: ctx.loopCounters, failure: msg)
        } catch {
            let msg = String(describing: error)
            onEvent(.runFailed(message: msg))
            return BlueprintRunResult(blueprintID: blueprint.id, finalText: memo.lastProduced,
                                      pathTaken: ctx.pathTaken, status: ctx.status,
                                      loopCounters: ctx.loopCounters, failure: msg)
        }

        let summary = "ran \(ctx.pathTaken.count) node(s)"
        onEvent(.runFinished(summary: summary))
        return BlueprintRunResult(blueprintID: blueprint.id, finalText: memo.lastProduced,
                                  pathTaken: ctx.pathTaken, status: ctx.status,
                                  loopCounters: ctx.loopCounters)
    }

    // MARK: The exec walk

    /// Follow control flow from `nodeID`. Each node: enter → execute its kind → follow the
    /// chosen exec-out(s). Loops recurse into their body subgraph, bounded.
    private func walk(from nodeID: BPNodeID,
                      blueprint: Blueprint,
                      ctx: inout ExecutionContext,
                      memo: inout DataMemo,
                      onEvent: @Sendable (ExecutionEvent) -> Void) async throws {
        var current: BPNodeID? = nodeID

        while let id = current {
            if ctx.stepsTaken >= maxSteps { throw BlueprintRunError.stepBudgetExceeded(maxSteps) }
            guard let node = blueprint.node(id) else { return }  // dangling: stop this strand

            ctx.enter(id)
            onEvent(.nodeEntered(id: id))
            onEvent(.nodeStatus(id: id, status: .running))

            switch node.kind {

            case .entry, .source, .merge:
                // Pass-through control. Source/merge produce no model value of their own; the
                // run input is resolved on demand by downstream data-ins.
                ctx.leave(id, .done)
                onEvent(.nodeStatus(id: id, status: .done))
                current = blueprint.execTarget(from: node.exec("then"))

            case .llm, .extract, .summarize, .rewrite:
                // Model op: resolve its data-in (pull-based), build the prompt, run under policy.
                let input = memo.resolveInput(into: node.dataIn(), node: node)
                let prompt = buildPrompt(for: node.kind, input: input)
                let outcome = await runModel(prompt: prompt, node: node, carried: input)
                switch outcome {
                case .produced(let text):
                    memo.set(id, text)
                    ctx.leave(id, .done)
                    onEvent(.nodeProduced(id: id, preview: preview(text)))
                    onEvent(.nodeStatus(id: id, status: .done))
                    current = blueprint.execTarget(from: node.exec("then"))
                case .skipped(let carried):
                    memo.set(id, carried)
                    ctx.leave(id, .skipped)
                    onEvent(.nodeStatus(id: id, status: .skipped))
                    current = blueprint.execTarget(from: node.exec("then"))
                case .failed(let reason):
                    ctx.leave(id, .failed)
                    onEvent(.nodeStatus(id: id, status: .failed))
                    throw BlueprintRunError.modelFailed(reason)
                }

            case .keepIf(let keyword):
                let input = memo.resolveInput(into: node.dataIn(), node: node)
                let kept = keepIf(input, keyword: keyword)
                memo.set(id, kept)
                ctx.leave(id, .done)
                onEvent(.nodeProduced(id: id, preview: preview(kept)))
                onEvent(.nodeStatus(id: id, status: .done))
                current = blueprint.execTarget(from: node.exec("then"))

            case .splitIntoItems:
                let input = memo.resolveInput(into: node.dataIn(), node: node)
                let items = splitIntoItems(input)
                memo.setCollection(id, items)
                memo.set(id, items.joined(separator: "\n"))
                ctx.leave(id, .done)
                onEvent(.nodeProduced(id: id, preview: preview("\(items.count) item(s)")))
                onEvent(.nodeStatus(id: id, status: .done))
                current = blueprint.execTarget(from: node.exec("then"))

            case .branch(let condition):
                let input = memo.resolveInput(into: node.dataIn(), node: node)
                let took = condition.evaluate(text: input, lines: nonEmptyLines(input))
                ctx.leave(id, .done)
                onEvent(.branchTaken(id: id, took: took))
                onEvent(.nodeStatus(id: id, status: .done))
                current = blueprint.execTarget(from: node.exec(took ? "true" : "false"))

            case .sequence:
                // Run each numbered exec-out subgraph in order, then continue via "then".
                ctx.leave(id, .done)
                onEvent(.nodeStatus(id: id, status: .done))
                for name in node.kind.execOutNames where name != "then" {
                    if let target = blueprint.execTarget(from: node.exec(name)) {
                        try await walk(from: target, blueprint: blueprint, ctx: &ctx,
                                       memo: &memo, onEvent: onEvent)
                    }
                }
                current = blueprint.execTarget(from: node.exec("then"))

            case .forEach:
                // Pull the collection data-in; run the "body" subgraph once per item, binding
                // the item as this node's data-out (memoized). Bounded by the collection size.
                let items = memo.resolveCollection(into: node.dataIn("collection"), node: node)
                ctx.leave(id, .done)
                onEvent(.nodeStatus(id: id, status: .done))
                let bodyEntry = blueprint.execTarget(from: node.exec("body"))
                for (i, item) in items.enumerated() {
                    let n = ctx.bumpLoop(id)
                    onEvent(.loopIteration(id: id, index: i, count: items.count))
                    memo.bindLoopItem(id, item)         // forEach's data-out = current item
                    if let bodyEntry {
                        try await walk(from: bodyEntry, blueprint: blueprint, ctx: &ctx,
                                       memo: &memo, onEvent: onEvent)
                    }
                    _ = n
                }
                memo.clearLoopItem(id)
                current = blueprint.execTarget(from: node.exec("completed"))

            case .whileLoop(let condition, let maxIterations):
                // Re-evaluate the condition over the data-in each pass; run "body" up to the
                // bound. ALWAYS bounded — never an infinite loop.
                let bound = max(0, maxIterations)
                ctx.leave(id, .done)
                onEvent(.nodeStatus(id: id, status: .done))
                let bodyEntry = blueprint.execTarget(from: node.exec("body"))
                var iter = 0
                while iter < bound {
                    let input = memo.resolveInput(into: node.dataIn(), node: node)
                    let holds = condition.evaluate(text: input, lines: nonEmptyLines(input))
                    if !holds { break }
                    let n = ctx.bumpLoop(id)
                    onEvent(.loopIteration(id: id, index: iter, count: nil))
                    if let bodyEntry {
                        try await walk(from: bodyEntry, blueprint: blueprint, ctx: &ctx,
                                       memo: &memo, onEvent: onEvent)
                    }
                    iter += 1
                    _ = n
                }
                current = blueprint.execTarget(from: node.exec("completed"))

            case .output:
                // Sink: capture the resolved value as the run's final text.
                let input = memo.resolveInput(into: node.dataIn(), node: node)
                memo.set(id, input)
                memo.markFinal(input)
                ctx.leave(id, .done)
                onEvent(.nodeProduced(id: id, preview: preview(input)))
                onEvent(.nodeStatus(id: id, status: .done))
                current = blueprint.execTarget(from: node.exec("then"))   // usually nil
            }
        }
    }

    // MARK: Model execution under the failure policy

    private enum ModelOutcome { case produced(String), skipped(String), failed(String) }

    private func runModel(prompt: String, node: BPNode, carried: String) async -> ModelOutcome {
        let effective = node.failurePolicy ?? policy.failurePolicy
        let primary = await attempt(prompt: prompt, on: provider)
        switch primary {
        case .success(let text):
            return .produced(text)
        case .failure(let err):
            switch effective {
            case .skip:
                // `.skip` carries the resolved input through unchanged (the step did nothing).
                return .skipped(carried)
            case .fallbackOnDevice:
                guard let fb = fallback else { return .failed("no fallback provider") }
                let r = await attempt(prompt: prompt, on: fb)
                switch r {
                case .success(let text): return .produced(text)
                case .failure(let e):    return .failed(describeError(e))
                }
            case .retryThenQueue:
                // No queue in the interpreter (the App owns parking); treat as a hard failure
                // so the policy difference is observable in tests.
                return .failed(describeError(err))
            }
        }
    }

    private enum Attempt { case success(String), failure(Error) }

    /// Bounded retry loop against a provider; injectable backoff (no sleep in tests).
    private func attempt(prompt: String, on provider: ILLMProvider) async -> Attempt {
        var lastError: Error = NSError(domain: "blueprint", code: -1)
        let totalTries = max(1, policy.maxRetries + 1)
        for tryIndex in 0..<totalTries {
            do { return .success(try await provider.complete(prompt: prompt)) }
            catch {
                lastError = error
                if tryIndex < totalTries - 1 { await policy.backoff(tryIndex + 1) }
            }
        }
        return .failure(lastError)
    }

    // MARK: Prompts & pure transforms (mirrors WorkflowRunner's templates)

    private func buildPrompt(for kind: BPNodeKind, input: String) -> String {
        switch kind {
        case .llm(_, let prompt):
            return prompt.replacingOccurrences(of: "{input}", with: input)
        case .summarize:
            return "Summarize the following into a tight, faithful summary. No preamble, just the summary.\n\n\(input)"
        case .rewrite(let tone):
            return "Rewrite the following text in a \(tone) tone, preserving every fact and detail. Return only the rewritten text.\n\n\(input)"
        case .extract(let type):
            return "From the following, extract the \(type.rawValue.replacingOccurrences(of: "_", with: " ")). Return only that artifact, no preamble.\n\n\(input)"
        default:
            return input
        }
    }

    private func keepIf(_ input: String, keyword: String) -> String {
        let needle = keyword.lowercased()
        guard !needle.isEmpty else { return input }
        return input.split(separator: "\n", omittingEmptySubsequences: false)
            .filter { $0.lowercased().contains(needle) }
            .joined(separator: "\n")
    }

    private func splitIntoItems(_ input: String) -> [String] { nonEmptyLines(input) }

    private func nonEmptyLines(_ input: String) -> [String] {
        input.split(separator: "\n", omittingEmptySubsequences: false)
            .map { $0.trimmingCharacters(in: .whitespaces) }
            .filter { !$0.isEmpty }
    }

    private func preview(_ s: String) -> String {
        let flat = s.replacingOccurrences(of: "\n", with: " ")
        return flat.count <= 80 ? flat : String(flat.prefix(80)) + "…"
    }

    private func describeError(_ e: Error) -> String { String(describing: e) }
    private func describe(_ e: BlueprintRunError) -> String {
        switch e {
        case .validation(let m):        return "validation: \(m)"
        case .stepBudgetExceeded(let n): return "step budget exceeded (\(n))"
        case .modelFailed(let m):       return "model failed: \(m)"
        }
    }
}

// MARK: - AsyncStream convenience

public extension BlueprintInterpreter {
    /// Run and surface events as an `AsyncStream<ExecutionEvent>` — the shape a SwiftUI canvas
    /// or a mesh transport subscribes to. The run executes in a detached child task; the stream
    /// finishes when the run does.
    func events(_ blueprint: Blueprint, sourceText: String) -> AsyncStream<ExecutionEvent> {
        AsyncStream { continuation in
            let task = Task {
                _ = await self.run(blueprint, sourceText: sourceText) { ev in
                    continuation.yield(ev)
                }
                continuation.finish()
            }
            continuation.onTermination = { _ in task.cancel() }
        }
    }
}

// MARK: - Pull-based data resolution

/// The per-run data memo. Resolves a node's data-in by pulling the connected data-out's value
/// (memoized), overlaying the active forEach loop item where one is bound. Pure value type.
struct DataMemo: Sendable {
    let blueprint: Blueprint
    let sourceText: String
    private var produced: [BPNodeID: String] = [:]
    private var collections: [BPNodeID: [String]] = [:]
    private var loopItems: [BPNodeID: String] = [:]
    /// The most recent meaningful value produced — the run's "final text" if no output sink ran.
    private(set) var lastProduced: String
    private var finalText: String?

    init(blueprint: Blueprint, sourceText: String) {
        self.blueprint = blueprint
        self.sourceText = sourceText
        self.lastProduced = sourceText
    }

    mutating func set(_ id: BPNodeID, _ value: String) {
        produced[id] = value
        if !value.isEmpty { lastProduced = value }
    }
    mutating func setCollection(_ id: BPNodeID, _ items: [String]) { collections[id] = items }
    mutating func bindLoopItem(_ id: BPNodeID, _ item: String) { loopItems[id] = item; produced[id] = item }
    mutating func clearLoopItem(_ id: BPNodeID) { loopItems[id] = nil }
    mutating func markFinal(_ value: String) { finalText = value; lastProduced = value }

    /// Resolve the scalar (`text`) value feeding `pin`. Pull the connected data-out; if none is
    /// wired, fall back to the SOURCE text (so a node with an exec wire but no data wire still
    /// sees the run input — the common "linear" shape). A forEach item overlays its node's out.
    func resolveInput(into pin: BPDataPin, node: BPNode) -> String {
        if let src = blueprint.dataSource(into: pin) {
            return value(of: src)
        }
        // Unwired data-in: default to the run source (keeps simple graphs working).
        return sourceText
    }

    /// Resolve a `collection` value feeding `pin` (forEach's "collection" data-in).
    func resolveCollection(into pin: BPDataPin, node: BPNode) -> [String] {
        guard let src = blueprint.dataSource(into: pin) else { return [] }
        if let items = collections[src.node] { return items }
        // A text-out wired into a collection-in: split it into lines (graceful coercion).
        return value(of: src).split(separator: "\n", omittingEmptySubsequences: true)
            .map { $0.trimmingCharacters(in: .whitespaces) }.filter { !$0.isEmpty }
    }

    /// The value at a data-out pin: a bound loop item wins, else the node's produced value,
    /// else (for source/entry) the run source, else "".
    private func value(of pin: BPDataPin) -> String {
        if let item = loopItems[pin.node] { return item }
        if let v = produced[pin.node] { return v }
        if let node = blueprint.node(pin.node) {
            switch node.kind {
            case .source, .entry: return sourceText
            default: break
            }
        }
        return ""
    }
}
