import XCTest
import Contracts
import Providers
@testable import RuntimeCore

/// HSM-14 (Workbench v2) — host tests for the **Blueprints interpreter**: branches route,
/// forEach runs N times, while is bounded, data pulls + `{input}` substitution, the ordered
/// `ExecutionEvent` stream, and a model failure driving the per-node failure policy. Fakes for
/// `ILLMProvider` keep these model-free and instant.
final class BlueprintInterpreterTests: XCTestCase {

    // MARK: Fakes

    /// Records prompts; echoes a transform. Optionally fails the first `failTimes` calls.
    final class RecordingProvider: ILLMProvider, @unchecked Sendable {
        let transform: @Sendable (String) -> String
        private(set) var prompts: [String] = []
        private(set) var calls = 0
        private let failTimes: Int
        init(failTimes: Int = 0, transform: @escaping @Sendable (String) -> String = { "OUT(\($0))" }) {
            self.failTimes = failTimes; self.transform = transform
        }
        func complete(prompt: String) async throws -> String {
            prompts.append(prompt); calls += 1
            if calls <= failTimes { throw NSError(domain: "fake", code: 1) }
            return transform(prompt)
        }
    }
    final class DeadProvider: ILLMProvider, @unchecked Sendable {
        private(set) var calls = 0
        func complete(prompt: String) async throws -> String { calls += 1; throw NSError(domain: "dead", code: 9) }
    }

    private func noBackoff(_ retries: Int, _ p: FailurePolicy) -> RunPolicy {
        RunPolicy(maxRetries: retries, failurePolicy: p, backoff: { _ in })
    }

    /// Collect events synchronously from a run (the callback sink).
    private func collectEvents(_ interp: BlueprintInterpreter, _ bp: Blueprint, _ src: String) async -> ([ExecutionEvent], BlueprintRunResult) {
        let box = EventBox()
        let result = await interp.run(bp, sourceText: src) { box.append($0) }
        return (box.events, result)
    }
    final class EventBox: @unchecked Sendable {
        private(set) var events: [ExecutionEvent] = []
        func append(_ e: ExecutionEvent) { events.append(e) }
    }

    // MARK: - Branch routing (true)

    func testBranchTakesTruePathWhenConditionHolds() async {
        // entry → branch(contains "urgent") → true:sumT  false:sumF
        let bp = Blueprint(name: "b", entry: "e", nodes: [
            BPNode(id: "e", kind: .entry),
            BPNode(id: "br", kind: .branch(condition: .contains(keyword: "urgent"))),
            BPNode(id: "tn", kind: .summarize),
            BPNode(id: "fn", kind: .rewrite(tone: "calm")),
        ], execEdges: [
            BPExecEdge(from: BPExecPin(node: "e", name: "then"), to: "br"),
            BPExecEdge(from: BPExecPin(node: "br", name: "true"), to: "tn"),
            BPExecEdge(from: BPExecPin(node: "br", name: "false"), to: "fn"),
        ])
        let provider = RecordingProvider()
        let interp = BlueprintInterpreter(provider: provider)
        let (events, result) = await collectEvents(interp, bp, "this is URGENT now")

        XCTAssertNil(result.failure)
        XCTAssertTrue(result.pathTaken.contains("tn"))
        XCTAssertFalse(result.pathTaken.contains("fn"))
        XCTAssertTrue(events.contains(.branchTaken(id: "br", took: true)))
    }

    // MARK: - Branch routing (false)

    func testBranchTakesFalsePathWhenConditionFails() async {
        let bp = Blueprint(name: "b", entry: "e", nodes: [
            BPNode(id: "e", kind: .entry),
            BPNode(id: "br", kind: .branch(condition: .contains(keyword: "urgent"))),
            BPNode(id: "tn", kind: .summarize),
            BPNode(id: "fn", kind: .rewrite(tone: "calm")),
        ], execEdges: [
            BPExecEdge(from: BPExecPin(node: "e", name: "then"), to: "br"),
            BPExecEdge(from: BPExecPin(node: "br", name: "true"), to: "tn"),
            BPExecEdge(from: BPExecPin(node: "br", name: "false"), to: "fn"),
        ])
        let interp = BlueprintInterpreter(provider: RecordingProvider())
        let (events, result) = await collectEvents(interp, bp, "nothing pressing here")

        XCTAssertNil(result.failure)
        XCTAssertTrue(result.pathTaken.contains("fn"))
        XCTAssertFalse(result.pathTaken.contains("tn"))
        XCTAssertTrue(events.contains(.branchTaken(id: "br", took: false)))
    }

    // MARK: - forEach runs the body exactly N times

    func testForEachRunsBodyExactlyNTimes() async {
        // entry → split(source) → forEach(over split) body: llm  completed: (nil)
        let bp = Blueprint(name: "fe", entry: "e", nodes: [
            BPNode(id: "e", kind: .entry),
            BPNode(id: "sp", kind: .splitIntoItems),
            BPNode(id: "fe", kind: .forEach),
            BPNode(id: "body", kind: .llm(name: "do", prompt: "process {input}")),
        ], execEdges: [
            BPExecEdge(from: BPExecPin(node: "e", name: "then"), to: "sp"),
            BPExecEdge(from: BPExecPin(node: "sp", name: "then"), to: "fe"),
            BPExecEdge(from: BPExecPin(node: "fe", name: "body"), to: "body"),
        ], dataEdges: [
            // split reads the source; forEach iterates split's collection; body reads forEach's item.
            BPDataEdge(from: BPDataPin(node: "sp", name: "out"), to: BPDataPin(node: "fe", name: "collection")),
            BPDataEdge(from: BPDataPin(node: "fe", name: "out"), to: BPDataPin(node: "body", name: "in")),
        ])
        let provider = RecordingProvider()
        let interp = BlueprintInterpreter(provider: provider)
        let source = "alpha\nbravo\ncharlie"   // 3 items
        let (events, result) = await collectEvents(interp, bp, source)

        XCTAssertNil(result.failure)
        // 3 loopIteration events for "fe".
        let iters = events.filter { if case .loopIteration(let id, _, _) = $0 { return id == "fe" }; return false }
        XCTAssertEqual(iters.count, 3)
        XCTAssertEqual(result.loopCounters["fe"], 3)
        // body executed exactly 3 times (3 provider calls).
        XCTAssertEqual(provider.calls, 3)
        // The {input} bound the loop item each pass (pull-based data resolution of forEach.out).
        XCTAssertEqual(provider.prompts, ["process alpha", "process bravo", "process charlie"])
    }

    // MARK: - while is bounded by maxIterations (never infinite)

    func testWhileLoopIsBoundedByMaxIterations() async {
        // A condition that is ALWAYS true (source is non-empty and never mutated) must still
        // terminate at maxIterations — proves the loop is bounded.
        let bp = Blueprint(name: "wl", entry: "e", nodes: [
            BPNode(id: "e", kind: .entry),
            BPNode(id: "wl", kind: .whileLoop(condition: .isNonEmpty, maxIterations: 4)),
            BPNode(id: "body", kind: .keepIf(keyword: "")),  // pure, no model, identity
        ], execEdges: [
            BPExecEdge(from: BPExecPin(node: "e", name: "then"), to: "wl"),
            BPExecEdge(from: BPExecPin(node: "wl", name: "body"), to: "body"),
        ])
        let interp = BlueprintInterpreter(provider: RecordingProvider())
        let (events, result) = await collectEvents(interp, bp, "always here")

        XCTAssertNil(result.failure)
        let iters = events.filter { if case .loopIteration(let id, _, _) = $0 { return id == "wl" }; return false }
        XCTAssertEqual(iters.count, 4, "while must stop at maxIterations")
        XCTAssertEqual(result.loopCounters["wl"], 4)
    }

    func testWhileLoopStopsWhenConditionFails() async {
        // isEmpty over a non-empty source is immediately false → zero body passes.
        let bp = Blueprint(name: "wl0", entry: "e", nodes: [
            BPNode(id: "e", kind: .entry),
            BPNode(id: "wl", kind: .whileLoop(condition: .isEmpty, maxIterations: 5)),
            BPNode(id: "body", kind: .summarize),
        ], execEdges: [
            BPExecEdge(from: BPExecPin(node: "e", name: "then"), to: "wl"),
            BPExecEdge(from: BPExecPin(node: "wl", name: "body"), to: "body"),
        ])
        let provider = RecordingProvider()
        let interp = BlueprintInterpreter(provider: provider)
        let (_, result) = await collectEvents(interp, bp, "non-empty")
        XCTAssertNil(result.failure)
        XCTAssertNil(result.loopCounters["wl"])    // never iterated
        XCTAssertEqual(provider.calls, 0)
    }

    // MARK: - Data resolution pulls the correct upstream value + {input} substitution

    func testDataResolutionPullsUpstreamValueAndSubstitutesInput() async {
        // entry → llmA(reads source) → llmB(reads llmA via a data wire).
        let bp = Blueprint(name: "dr", entry: "e", nodes: [
            BPNode(id: "e", kind: .entry),
            BPNode(id: "a", kind: .llm(name: "A", prompt: "A:{input}")),
            BPNode(id: "b", kind: .llm(name: "B", prompt: "B:{input}")),
        ], execEdges: [
            BPExecEdge(from: BPExecPin(node: "e", name: "then"), to: "a"),
            BPExecEdge(from: BPExecPin(node: "a", name: "then"), to: "b"),
        ], dataEdges: [
            BPDataEdge(from: BPDataPin(node: "a", name: "out"), to: BPDataPin(node: "b", name: "in")),
        ])
        let provider = RecordingProvider(transform: { "<\($0)>" })
        let interp = BlueprintInterpreter(provider: provider)
        let (_, result) = await collectEvents(interp, bp, "SRC")

        XCTAssertNil(result.failure)
        // A read the source: "A:SRC". B pulled A's produced value "<A:SRC>": "B:<A:SRC>".
        XCTAssertEqual(provider.prompts.count, 2)
        XCTAssertEqual(provider.prompts[0], "A:SRC")
        XCTAssertEqual(provider.prompts[1], "B:<A:SRC>")
        XCTAssertEqual(result.finalText, "<B:<A:SRC>>")
    }

    // MARK: - The ordered ExecutionEvent stream (the live-trace contract)

    func testExecutionEventStreamEmitsExpectedOrderedSequence() async {
        // A small branching + (no-model) graph so ordering is deterministic without provider noise.
        // entry → branch(contains "go") → true: keepIf("a") → output
        let bp = Blueprint(name: "ord", entry: "e", nodes: [
            BPNode(id: "e", kind: .entry),
            BPNode(id: "br", kind: .branch(condition: .contains(keyword: "go"))),
            BPNode(id: "k", kind: .keepIf(keyword: "x")),
            BPNode(id: "o", kind: .output),
            BPNode(id: "f", kind: .summarize),    // false path, never taken
        ], execEdges: [
            BPExecEdge(from: BPExecPin(node: "e", name: "then"), to: "br"),
            BPExecEdge(from: BPExecPin(node: "br", name: "true"), to: "k"),
            BPExecEdge(from: BPExecPin(node: "br", name: "false"), to: "f"),
            BPExecEdge(from: BPExecPin(node: "k", name: "then"), to: "o"),
        ], dataEdges: [
            BPDataEdge(from: BPDataPin(node: "k", name: "out"), to: BPDataPin(node: "o", name: "in")),
        ])
        let interp = BlueprintInterpreter(provider: RecordingProvider())
        // keepIf("x") keeps only the one line containing "x" → "fox" so the preview is unambiguous.
        let (events, result) = await collectEvents(interp, bp, "go\nfox\nbeta")
        XCTAssertNil(result.failure)

        let expected: [ExecutionEvent] = [
            .runStarted(blueprint: bp.id),
            .nodeEntered(id: "e"),
            .nodeStatus(id: "e", status: .running),
            .nodeStatus(id: "e", status: .done),
            .nodeEntered(id: "br"),
            .nodeStatus(id: "br", status: .running),
            .branchTaken(id: "br", took: true),
            .nodeStatus(id: "br", status: .done),
            .nodeEntered(id: "k"),
            .nodeStatus(id: "k", status: .running),
            .nodeProduced(id: "k", preview: "fox"),
            .nodeStatus(id: "k", status: .done),
            .nodeEntered(id: "o"),
            .nodeStatus(id: "o", status: .running),
            .nodeProduced(id: "o", preview: "fox"),
            .nodeStatus(id: "o", status: .done),
            .runFinished(summary: "ran 4 node(s)"),
        ]
        XCTAssertEqual(events, expected)
    }

    // MARK: - AsyncStream surface yields the same events

    func testAsyncStreamSurfaceYieldsEvents() async {
        let bp = Blueprint(name: "as", entry: "e", nodes: [
            BPNode(id: "e", kind: .entry),
            BPNode(id: "s", kind: .summarize),
        ], execEdges: [
            BPExecEdge(from: BPExecPin(node: "e", name: "then"), to: "s"),
        ])
        let interp = BlueprintInterpreter(provider: RecordingProvider())
        var got: [ExecutionEvent] = []
        for await ev in interp.events(bp, sourceText: "x") { got.append(ev) }
        XCTAssertEqual(got.first, .runStarted(blueprint: bp.id))
        XCTAssertTrue(got.contains(.nodeEntered(id: "s")))
        if case .runFinished = got.last { } else { XCTFail("stream must finish with runFinished") }
    }

    // MARK: - Failure policy: skip carries input, fallback recovers, retryThenQueue fails (no crash)

    func testModelFailureSkipPolicyCarriesInput() async {
        let bp = Blueprint(name: "skip", entry: "e", nodes: [
            BPNode(id: "e", kind: .entry),
            BPNode(id: "m", kind: .llm(name: "m", prompt: "{input}"), failurePolicy: .skip),
            BPNode(id: "o", kind: .output),
        ], execEdges: [
            BPExecEdge(from: BPExecPin(node: "e", name: "then"), to: "m"),
            BPExecEdge(from: BPExecPin(node: "m", name: "then"), to: "o"),
        ], dataEdges: [
            BPDataEdge(from: BPDataPin(node: "m", name: "out"), to: BPDataPin(node: "o", name: "in")),
        ])
        let interp = BlueprintInterpreter(provider: DeadProvider(), policy: noBackoff(1, .skip))
        let (events, result) = await collectEvents(interp, bp, "CARRY ME")
        XCTAssertNil(result.failure, "skip must not crash or fail the run")
        XCTAssertEqual(result.status["m"], .skipped)
        XCTAssertTrue(events.contains(.nodeStatus(id: "m", status: .skipped)))
        XCTAssertEqual(result.finalText, "CARRY ME")   // carried through
    }

    func testModelFailureFallbackPolicyRecovers() async {
        let dead = DeadProvider()
        let fb = RecordingProvider(transform: { "FB(\($0))" })
        let bp = Blueprint(name: "fb", entry: "e", nodes: [
            BPNode(id: "e", kind: .entry),
            BPNode(id: "m", kind: .summarize, failurePolicy: .fallbackOnDevice),
        ], execEdges: [
            BPExecEdge(from: BPExecPin(node: "e", name: "then"), to: "m"),
        ])
        let interp = BlueprintInterpreter(provider: dead, fallback: fb, policy: noBackoff(0, .fallbackOnDevice))
        let (_, result) = await collectEvents(interp, bp, "src")
        XCTAssertNil(result.failure)
        XCTAssertEqual(result.status["m"], .done)
        XCTAssertGreaterThan(dead.calls, 0)
        XCTAssertGreaterThan(fb.calls, 0)
    }

    func testModelFailureRetriesThenFailsWithoutCrash() async {
        let dead = DeadProvider()
        let bp = Blueprint(name: "q", entry: "e", nodes: [
            BPNode(id: "e", kind: .entry),
            BPNode(id: "m", kind: .summarize, failurePolicy: .retryThenQueue),
        ], execEdges: [
            BPExecEdge(from: BPExecPin(node: "e", name: "then"), to: "m"),
        ])
        let interp = BlueprintInterpreter(provider: dead, policy: noBackoff(2, .retryThenQueue))
        let (events, result) = await collectEvents(interp, bp, "src")
        XCTAssertNotNil(result.failure, "exhausted retries surface as a failed run, not a crash")
        XCTAssertEqual(dead.calls, 3, "1 try + 2 retries")
        XCTAssertEqual(result.status["m"], .failed)
        if case .runFailed? = events.last { } else { XCTFail("run must end with runFailed") }
    }

    // MARK: - Validation rejects a data-type mismatch

    func testValidationRejectsDataTypeMismatch() async {
        // splitIntoItems (collection out) wired into summarize (text in) → mismatch.
        let bp = Blueprint(name: "bad", entry: "e", nodes: [
            BPNode(id: "e", kind: .entry),
            BPNode(id: "sp", kind: .splitIntoItems),
            BPNode(id: "s", kind: .summarize),
        ], execEdges: [
            BPExecEdge(from: BPExecPin(node: "e", name: "then"), to: "sp"),
            BPExecEdge(from: BPExecPin(node: "sp", name: "then"), to: "s"),
        ], dataEdges: [
            BPDataEdge(from: BPDataPin(node: "sp", name: "out"), to: BPDataPin(node: "s", name: "in")),
        ])
        XCTAssertNotNil(bp.validate())
        let interp = BlueprintInterpreter(provider: RecordingProvider())
        let (events, result) = await collectEvents(interp, bp, "x")
        XCTAssertNotNil(result.failure)
        if case .runFailed? = events.last { } else { XCTFail("invalid blueprint must runFailed") }
    }

    // MARK: - Codable round-trip (mesh-rideable)

    func testBlueprintAndEventsAreCodable() throws {
        let bp = Blueprint(name: "cod", entry: "e", nodes: [
            BPNode(id: "e", kind: .entry),
            BPNode(id: "br", kind: .branch(condition: .countAtLeast(2))),
        ], execEdges: [BPExecEdge(from: BPExecPin(node: "e", name: "then"), to: "br")])
        let bpData = try JSONEncoder().encode(bp)
        XCTAssertEqual(try JSONDecoder().decode(Blueprint.self, from: bpData), bp)

        let evts: [ExecutionEvent] = [
            .runStarted(blueprint: bp.id),
            .loopIteration(id: "fe", index: 1, count: 3),
            .branchTaken(id: "br", took: false),
            .runFinished(summary: "ok"),
        ]
        let evData = try JSONEncoder().encode(evts)
        XCTAssertEqual(try JSONDecoder().decode([ExecutionEvent].self, from: evData), evts)
    }
}
