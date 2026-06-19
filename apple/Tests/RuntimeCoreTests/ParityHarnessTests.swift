import XCTest
import Contracts
@testable import RuntimeCore

/// HSM-6-04 — the parity baseline harness. The scorer is a pure function over
/// fixed inputs: substance coverage, phrasing-tolerant, identical across reruns.
final class ParityHarnessTests: XCTestCase {

    private func artifact(_ type: ArtifactType, title: String, body: String) -> Artifact {
        Artifact(id: "x", meetingId: "m", artifactType: type, title: title, bodyMarkdown: body,
                 structuredJson: .object([:]), confidence: 0.8, status: .draft,
                 pluginId: "p", pluginVersion: "1",
                 sources: [ArtifactSource(sourceType: "transcript", sourceRef: "h")])
    }

    private func rubric(threshold: Double) -> ParityRubric {
        ParityRubric(meetingId: "m", expectations: [
            .init(category: .artifact(.decisions), mustCover: ["ship the API Friday", "freeze the schema"]),
            .init(category: .summary, mustCover: ["vendor key expires"]),
        ], threshold: threshold)
    }

    // Phrasing-tolerant coverage + per-category attribution.
    func testPerCategoryCoverageIsPhrasingTolerant() {
        let artifacts = [artifact(.decisions, title: "Decisions",
            body: "The team decided to **ship the API** on Friday. We will not freeze anything yet.")]
        let summary = IntelSnapshot(timestamp: 0, topics: ["release"], actionItems: [],
            summary: "The vendor key expires next week, so we moved fast.")

        let report = ParityScorer.score(artifacts: artifacts, summary: summary, rubric: rubric(threshold: 0.6))

        let decisions = report.perCategory.first { $0.category == .artifact(.decisions) }!
        XCTAssertEqual(decisions.covered, 1)                 // "ship the API Friday" matched despite markdown/order
        XCTAssertEqual(decisions.total, 2)
        XCTAssertEqual(decisions.missing, ["freeze the schema"])  // not covered (no "schema")

        let summaryScore = report.perCategory.first { $0.category == .summary }!
        XCTAssertEqual(summaryScore.covered, 1)              // summary text covers it

        XCTAssertEqual(report.overallCoverage, 2.0 / 3.0, accuracy: 0.0001)  // 2 of 3 facts
        XCTAssertTrue(report.passed)                          // >= 0.6
    }

    // Pure + deterministic: identical verdict across reruns (the gate isn't a vibe).
    func testScorerIsDeterministic() {
        let artifacts = [artifact(.decisions, title: "D", body: "ship the API Friday")]
        let summary = IntelSnapshot(timestamp: 0, topics: [], actionItems: [], summary: "nothing notable")
        let r = rubric(threshold: 0.5)
        XCTAssertEqual(ParityScorer.score(artifacts: artifacts, summary: summary, rubric: r),
                       ParityScorer.score(artifacts: artifacts, summary: summary, rubric: r))
    }

    // Threshold verdict + a clean miss attributed to its category.
    func testThresholdFailsAndAttributes() {
        let artifacts = [artifact(.decisions, title: "D", body: "we discussed lunch")]
        let summary = IntelSnapshot(timestamp: 0, topics: [], actionItems: [], summary: "lunch was good")
        let report = ParityScorer.score(artifacts: artifacts, summary: summary, rubric: rubric(threshold: 0.6))
        XCTAssertEqual(report.overallCoverage, 0.0, accuracy: 0.0001)  // nothing covered
        XCTAssertFalse(report.passed)
        // The gap is per-category, not one opaque score.
        XCTAssertEqual(report.perCategory.first { $0.category == .summary }!.missing, ["vendor key expires"])
    }
}
