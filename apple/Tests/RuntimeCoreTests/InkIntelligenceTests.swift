import XCTest
import Contracts
@testable import Providers
@testable import RuntimeCore

/// HSM-8-06 — the magic pencil made "involved": a handwritten note promotes to a
/// schema-valid artifact proposal, and a hand-marked moment measurably changes what the
/// MIR routing extracts. Pure + on-device (no network).
final class InkIntelligenceTests: XCTestCase {

    private func seg(_ text: String, _ s: Double, _ e: Double) -> Segment {
        TranscribedSegment(text: text, startTime: s, endTime: e).asContractSegment()
    }

    // Mostly-product transcript with ONE lightly-incident segment (below threshold whole).
    private var transcript: Transcript {
        Transcript(meetingId: "m1", segments: [
            seg("user user user feature customer feedback roadmap", 0, 2),     // 0 product
            seg("priority value experience usability persona market", 2, 4),  // 1 product
            seg("there was an incident outage", 4, 6),                         // 2 incident (light)
            seg("user requirement adoption feedback user value", 6, 8),        // 3 product
        ], transcriptHash: "h")
    }

    // MARK: promote ink → artifact

    func testPromoteProducesASchemaValidDraftArtifact() {
        let a = InkPromoter.artifact(text: "Follow up with the vendor about pricing",
                                     type: .actionItems, meetingID: "m1", atSegment: 2, id: "ink-1")
        XCTAssertEqual(a.status, .draft)            // propose-and-confirm, never auto-committed
        XCTAssertEqual(a.artifactType, .actionItems)
        XCTAssertEqual(a.meetingId, "m1")
        XCTAssertEqual(a.bodyMarkdown, "Follow up with the vendor about pricing")
        XCTAssertEqual(a.sources.first?.sourceType, "handwriting")
        // It round-trips through the contract coder (schema-valid).
        let data = try! HoldSpeakContracts.encoder().encode(a)
        let back = try! HoldSpeakContracts.decoder().decode(Artifact.self, from: data)
        XCTAssertEqual(back.id, "ink-1")
        XCTAssertEqual(back.artifactType, .actionItems)
        XCTAssertEqual(back.status, .draft)
        XCTAssertEqual(back.bodyMarkdown, a.bodyMarkdown)
    }

    func testPromoteTitleIsTheFirstLine() {
        let a = InkPromoter.artifact(text: "Ship Friday\nand bump the cache TTL",
                                     type: .decisions, meetingID: "m1", id: "ink-2")
        XCTAssertEqual(a.title, "Ship Friday")
    }

    // MARK: marked moments weight extraction

    func testUnmarkedDoesNotSurfaceTheIncidentArtifact() {
        let types = InkEmphasis.routedTypes(profile: .product, transcript: transcript, marks: [])
        XCTAssertFalse(types.contains(.incidentTimeline), "below threshold, the light incident mention isn't routed")
    }

    func testAHandMarkedMomentSurfacesTheIncidentArtifact() {
        // The owner stars the incident moment (t=5, in segment 2) — it's now weighted.
        let types = InkEmphasis.routedTypes(profile: .product, transcript: transcript, marks: [5.0])
        XCTAssertTrue(types.contains(.incidentTimeline),
                      "a hand-flagged moment measurably changes what is extracted")
    }

    func testNoMarksLeavesScoresUnchanged() {
        let base = IntentScorer.score(transcript)
        XCTAssertEqual(InkEmphasis.emphasized(base, marks: [], in: transcript), base)
    }
}
