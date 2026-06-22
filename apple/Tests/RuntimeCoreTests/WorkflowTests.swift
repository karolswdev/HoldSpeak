import XCTest
import Contracts
@testable import RuntimeCore

/// HSM-14 Workbench — the user-defined workflow model (the engine the visual builder binds to).
final class WorkflowTests: XCTestCase {

    func testPlanReadsTopToBottom() {
        let w = Workflow(name: "x", source: .fullTranscript,
                         steps: [.lens(.delivery), .summarize], output: .artifacts)
        XCTAssertEqual(w.plan, "Full transcript  →  Lens · Delivery  →  Summarize  →  Artifact cards")
    }

    func testRunnableRequiresAStep() {
        XCTAssertFalse(Workflow(name: "empty", source: .fullTranscript, steps: [], output: .note).isRunnable)
        XCTAssertTrue(Workflow(name: "ok", source: .fullTranscript, steps: [.summarize], output: .note).isRunnable)
    }

    func testProducedTypesFromExtractAndLensDeduped() {
        // delivery lens emphasis + an explicit extract that overlaps → de-duplicated, order kept.
        let lensTypes = MIRRouter.baseEmphasis[.delivery] ?? []
        let w = Workflow(name: "x", source: .fullTranscript,
                         steps: [.lens(.delivery), .extract(.decisions)], output: .artifacts)
        let produced = w.producedTypes(default: [.requirements])
        XCTAssertTrue(produced.contains(.decisions))
        XCTAssertEqual(Set(produced).count, produced.count, "no duplicate types")
        for t in lensTypes { XCTAssertTrue(produced.contains(t), "lens emphasis \(t) is included") }
    }

    func testProducedTypesFallsBackWhenNoExtractOrLens() {
        let w = Workflow(name: "x", source: .fullTranscript, steps: [.summarize], output: .note)
        XCTAssertEqual(w.producedTypes(default: [.requirements]), [.requirements])
    }

    func testEgressFlagOnlyForSlack() {
        XCTAssertTrue(WorkflowOutput.slack.isEgress)
        XCTAssertFalse(WorkflowOutput.artifacts.isEgress)
        XCTAssertFalse(WorkflowOutput.note.isEgress)
    }

    func testCodableRoundTripIncludingAssociatedValueSteps() throws {
        let w = Workflow(name: "Exec → Slack", source: .tackedMoments,
                         steps: [.extract(.riskRegister), .rewrite(tone: "executive"), .keepIf("budget")],
                         output: .slack)
        let data = try JSONEncoder().encode(w)
        let back = try JSONDecoder().decode(Workflow.self, from: data)
        XCTAssertEqual(back, w, "name, source, every step (with its associated value), and output survive")
    }

    func testPresetsAreRunnableAndRoundTrip() throws {
        XCTAssertFalse(WorkflowPresets.all.isEmpty)
        for w in WorkflowPresets.all {
            XCTAssertTrue(w.isRunnable, "\(w.name) has at least one step")
            let back = try JSONDecoder().decode(Workflow.self, from: try JSONEncoder().encode(w))
            XCTAssertEqual(back, w)
        }
    }
}
