import XCTest
import Contracts
@testable import RuntimeCore

/// HSM-22-01 — the graph_json wire, golden-pinned across the language boundary.
///
/// These tests ENCODE real `Blueprint`s through the canonical coder and compare them
/// to the committed fixtures (`contracts/fixtures/blueprint-linear-sample.json` +
/// `blueprint-branching-sample.json`). The hub's pytest
/// (`tests/unit/test_blueprint_graph_conformance.py`) feeds the SAME fixture bytes
/// into `workflow_graph.linearize()` — so the Swift encoder and the Python parser can
/// never drift apart silently.
///
/// Regenerate after a deliberate model change:
///   HS_REGEN_BLUEPRINT_FIXTURES=1 swift test --filter BlueprintWireTests
final class BlueprintWireTests: XCTestCase {

    // MARK: the canonical graphs

    /// Linear: entry → llm → extract(decisions) → keepIf → output, with the per-node
    /// provenance a real inspector sets (failure_policy + runs_on) — every field the
    /// hub's `GraphNode` carries.
    private func linearBlueprint() -> Blueprint {
        let nodes = [
            BPNode(id: "e1", kind: .entry),
            BPNode(id: "ask", kind: .llm(name: "LLM call", prompt: "From {input}, list the risks. One per line."),
                   failurePolicy: .fallbackOnDevice, runsOn: .endpoint),
            BPNode(id: "dec", kind: .extract(.decisions), failurePolicy: .skip, runsOn: .onDevice),
            BPNode(id: "keep", kind: .keepIf(keyword: "risk")),
            BPNode(id: "out", kind: .output),
        ]
        return Blueprint(id: UUID(uuidString: "AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE")!,
                         name: "Golden linear",
                         entry: "e1",
                         nodes: nodes,
                         execEdges: [
                            BPExecEdge(from: BPExecPin(node: "e1", name: "then"), to: "ask"),
                            BPExecEdge(from: BPExecPin(node: "ask", name: "then"), to: "dec"),
                            BPExecEdge(from: BPExecPin(node: "dec", name: "then"), to: "keep"),
                            BPExecEdge(from: BPExecPin(node: "keep", name: "then"), to: "out"),
                         ])
    }

    /// Branching: entry → branch → {true: summarize, false: rewrite}. The hub must
    /// REFUSE this honestly — the fixture pins the refusal side of the contract.
    private func branchingBlueprint() -> Blueprint {
        let nodes = [
            BPNode(id: "e1", kind: .entry),
            BPNode(id: "br", kind: .branch(condition: .contains(keyword: "risk"))),
            BPNode(id: "a", kind: .summarize),
            BPNode(id: "b", kind: .rewrite(tone: "Executive")),
        ]
        return Blueprint(id: UUID(uuidString: "99999999-8888-7777-6666-555555555555")!,
                         name: "Golden branching",
                         entry: "e1",
                         nodes: nodes,
                         execEdges: [
                            BPExecEdge(from: BPExecPin(node: "e1", name: "then"), to: "br"),
                            BPExecEdge(from: BPExecPin(node: "br", name: "true"), to: "a"),
                            BPExecEdge(from: BPExecPin(node: "br", name: "false"), to: "b"),
                         ])
    }

    // MARK: fixture plumbing (repo-relative via #filePath, the HS-72-01 pattern)

    private func fixturesDir() -> URL {
        URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()  // RuntimeCoreTests
            .deletingLastPathComponent()  // Tests
            .deletingLastPathComponent()  // apple
            .deletingLastPathComponent()  // repo root
            .appendingPathComponent("pm/roadmap/holdspeak-mobile/contracts/fixtures")
    }

    private func assertMatchesFixture(_ blueprint: Blueprint, _ filename: String,
                                      file: StaticString = #filePath, line: UInt = #line) throws {
        let url = fixturesDir().appendingPathComponent(filename)
        let encoded = try blueprint.graphJSONData()
        if ProcessInfo.processInfo.environment["HS_REGEN_BLUEPRINT_FIXTURES"] == "1" {
            try (String(data: encoded, encoding: .utf8)! + "\n").data(using: .utf8)!
                .write(to: url)
            return
        }
        let committed = try Data(contentsOf: url)
        // Compare parsed JSON (whitespace-tolerant), then the exact bytes minus the
        // trailing newline (sortedKeys makes the encoding deterministic).
        let lhs = try JSONSerialization.jsonObject(with: encoded) as? NSDictionary
        let rhs = try JSONSerialization.jsonObject(with: committed) as? NSDictionary
        XCTAssertEqual(lhs, rhs, "\(filename) drifted from the Swift encoder — regenerate deliberately (HS_REGEN_BLUEPRINT_FIXTURES=1) and re-run the hub conformance pytest", file: file, line: line)
        XCTAssertEqual(String(data: encoded, encoding: .utf8)!.trimmingCharacters(in: .newlines),
                       String(data: committed, encoding: .utf8)!.trimmingCharacters(in: .newlines),
                       file: file, line: line)
    }

    // MARK: the pins

    func testLinearBlueprintMatchesTheGoldenFixture() throws {
        try assertMatchesFixture(linearBlueprint(), "blueprint-linear-sample.json")
    }

    func testBranchingBlueprintMatchesTheGoldenFixture() throws {
        try assertMatchesFixture(branchingBlueprint(), "blueprint-branching-sample.json")
    }

    func testWireShapeIsTheHubContract() throws {
        // The load-bearing key shapes, asserted on the raw wire so a coder-strategy
        // regression is named, not just "fixtures differ".
        let wire = String(data: try linearBlueprint().graphJSONData(), encoding: .utf8)!
        XCTAssertTrue(wire.contains("\"exec_edges\""), "snake_case keys must reach the wire")
        XCTAssertTrue(wire.contains("\"data_edges\""))
        XCTAssertTrue(wire.contains("\"failure_policy\" : \"fallbackOnDevice\""),
                      "enum RAW VALUES ride unconverted (the hub's _FAILURE_POLICIES)")
        XCTAssertTrue(wire.contains("\"runs_on\" : \"endpoint\""),
                      "the new BPNode.runsOn reaches the wire as runs_on")
        XCTAssertTrue(wire.contains("\"runs_on\" : \"onDevice\""),
                      "camelCase RAW value survives (the hub's _RUN_TARGETS)")
        XCTAssertTrue(wire.contains("\"_0\" : \"decisions\""),
                      "extract's unlabeled associated value is the _0 shape the hub parses")
        let branching = String(data: try branchingBlueprint().graphJSONData(), encoding: .utf8)!
        XCTAssertTrue(branching.contains("\"branch\""))
        XCTAssertTrue(branching.contains("\"keyword\" : \"risk\""))
    }

    func testGraphJSONValueRoundTripsIntoWorkflowDefinition() throws {
        // The lowering lands in the synced contract: graphJson carries the graph and
        // the whole definition round-trips through the canonical coder unchanged.
        let definition = try linearBlueprint().workflowDefinition(prompt: "fallback: {input}",
                                                                  createdAt: Date(timeIntervalSince1970: 1_700_000_000),
                                                                  updatedAt: Date(timeIntervalSince1970: 1_700_000_000))
        XCTAssertEqual(definition.name, "Golden linear")
        XCTAssertNotNil(definition.graphJson)
        let coder = (HoldSpeakContracts.encoder(), HoldSpeakContracts.decoder())
        let decoded = try coder.1.decode(WorkflowDefinition.self, from: coder.0.encode(definition))
        XCTAssertEqual(decoded, definition, "graphJson must survive the contract coder byte-faithful")
    }

    func testRunsOnAbsentStaysAbsentOnTheWire() throws {
        // nil runsOn/failurePolicy must OMIT the keys (inherit-the-default is the
        // absence of the key, the hub's None/unset path — never an explicit null).
        var bp = linearBlueprint()
        bp.nodes = [BPNode(id: "e1", kind: .entry), BPNode(id: "out", kind: .output)]
        bp.execEdges = [BPExecEdge(from: BPExecPin(node: "e1", name: "then"), to: "out")]
        let wire = String(data: try bp.graphJSONData(), encoding: .utf8)!
        XCTAssertFalse(wire.contains("runs_on"))
        XCTAssertFalse(wire.contains("failure_policy"))
    }
}
