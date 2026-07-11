import XCTest
@testable import RuntimeCore

/// HSM-15-12 — the pure assembler: ordering, provenance headers, budget
/// refusal, the KB honesty marker. The picker UI is sim-shot, not unit-tested;
/// THIS is the seam every run target calls, so its shape is locked here.
final class ContextEnvelopeTests: XCTestCase {

    func testBlocksRenderProvenanceHeadersInSelectionOrder() throws {
        let blocks: [ContextEnvelope.Block] = [
            .init(kind: .meeting, title: "Q3 kickoff", day: "2026-07-01", body: "We ship."),
            .init(kind: .artifact, title: "Decisions", detail: "Q3 kickoff", body: "- Ship it."),
            .init(kind: .note, title: "Scratch", body: "Remember the manifest."),
        ]
        let text = try ContextEnvelope.assemble(blocks).get()
        let expected = """
        [MEETING: Q3 kickoff — 2026-07-01]
        We ship.

        [ARTIFACT: Decisions — Q3 kickoff]
        - Ship it.

        [NOTE: Scratch]
        Remember the manifest.
        """
        XCTAssertEqual(text, expected)
    }

    func testOverBudgetRefusesInsteadOfTrimming() {
        let big = ContextEnvelope.Block(
            kind: .meeting, title: "Deep dive",
            body: String(repeating: "transcript ", count: 2_000))
        let result = ContextEnvelope.assemble([big], budgetTokens: 100)
        guard case .failure(.overBudget(let needed, let budget)) = result else {
            return XCTFail("an over-budget selection must refuse, not trim")
        }
        XCTAssertEqual(budget, 100)
        XCTAssertGreaterThan(needed, budget)
        // The gauge and the refusal use the SAME estimator.
        XCTAssertEqual(needed, ContextEnvelope.estimateTokens([big]))
    }

    func testWithinBudgetPasses() {
        let small = ContextEnvelope.Block(kind: .meeting, title: "Standup", body: "Short.")
        XCTAssertEqual(
            try? ContextEnvelope.assemble([small], budgetTokens: 1_000).get(),
            "[MEETING: Standup]\nShort."
        )
    }

    func testKBBlockCarriesContentOrTheHonestMarker() {
        let hydrated = ContextEnvelope.kbBlock(name: "Mesh", content: "Peers pair by token.")
        XCTAssertEqual(hydrated.rendered, "[KB: Mesh]\nPeers pair by token.")

        let empty = ContextEnvelope.kbBlock(name: "Mesh", content: nil)
        XCTAssertEqual(empty.rendered, "[KB: Mesh — not hydrated on this device]")
    }

    func testSelectionMapsToHubWireRefs() {
        let sel = GroundingSelection(meetings: [
            .init(id: "m1", title: "Kickoff", includeTranscript: true, artifactIds: ["a1", "a2"]),
            .init(id: "m2", title: "Retro", artifactIds: ["a3"]),
        ], resources: [
            .init(ref: "note:n1", kind: "Note", title: "Scratch"),
            .init(ref: "project:p1", kind: "Project", title: "Launch"),
        ])
        XCTAssertEqual(sel.hubMeetingIds, ["m1", "m2"])
        XCTAssertEqual(sel.hubArtifactIds, ["a1", "a2", "a3"])
        XCTAssertEqual(sel.hubExpand, "full")   // any transcript toggle upgrades the expand
        XCTAssertEqual(sel.hubRefs, ["note:n1", "project:p1"])
        XCTAssertEqual(sel.summaryLabel, "2 meetings · 3 artifacts · 2 objects")

        let digestOnly = GroundingSelection(meetings: [.init(id: "m1", title: "Kickoff")])
        XCTAssertEqual(digestOnly.hubExpand, "summary")
        XCTAssertEqual(digestOnly.summaryLabel, "1 meeting")
        XCTAssertTrue(GroundingSelection().isEmpty)
    }

    func testLegacySelectionWithoutResourcesStillDecodes() throws {
        let legacy = Data(#"{"meetings":[]}"#.utf8)
        let decoded = try JSONDecoder().decode(GroundingSelection.self, from: legacy)
        XCTAssertEqual(decoded.resources, [])
        XCTAssertTrue(decoded.isEmpty)
    }

    func testEmptySelectionEstimatesZero() {
        XCTAssertEqual(ContextEnvelope.estimateTokens([]), 0)
    }
}

private extension ContextEnvelope.Block {
    /// Meeting sugar mirroring the picker's construction.
    init(kind: ContextEnvelope.Block.Kind, title: String, day: String, body: String) {
        self.init(kind: kind, title: title, detail: day, body: body)
    }
}
