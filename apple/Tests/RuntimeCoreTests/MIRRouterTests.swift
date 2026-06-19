import XCTest
import Contracts
import Providers
@testable import RuntimeCore

/// HSM-7-01..04 — the MIR routing port. All host-testable + deterministic (the
/// routing decision is model-free; the gate measures artifact-type set differences,
/// which depend only on the router).
final class MIRRouterTests: XCTestCase {

    // A fake provider so generation succeeds for any routed type — the gate measures
    // the routed TYPE SET, not model output.
    final class StubLLM: ILLMProvider, @unchecked Sendable {
        func complete(prompt: String) async throws -> String {
            #"{"title":"t","body_markdown":"b","structured_json":{},"confidence":0.5}"#
        }
    }

    struct Sample: Codable { let meeting: Meeting; let artifact: Artifact }
    private func fixtureMeeting() throws -> Meeting {
        var url = URL(fileURLWithPath: #filePath)
        for _ in 0..<4 { url.deleteLastPathComponent() }
        url.appendPathComponent("pm/roadmap/holdspeak-mobile/contracts/fixtures/meeting-sample.json")
        return try HoldSpeakContracts.decoder().decode(Sample.self, from: Data(contentsOf: url)).meeting
    }

    private func transcript(_ lines: [String]) -> Transcript {
        var t = 0.0
        let segs = lines.map { line -> Segment in
            defer { t += 5 }
            return Segment(text: line, speaker: "S", startTime: t, endTime: t + 5)
        }
        return Transcript(meetingId: "mir_001", segments: segs, transcriptHash: "h")
    }

    // MARK: - HSM-7-01: intent scoring

    func testIntentScorerDetectsDominantIntent() {
        let arch = IntentScorer.score(text: "Let's discuss the API design, the schema, the service interface and the dependency tradeoffs.")
        XCTAssertEqual(arch.above(0.15).first, .architecture)

        let inc = IntentScorer.score(text: "We had an outage; severity high, the postmortem found the root cause, we did a rollback and updated the runbook.")
        XCTAssertEqual(inc.above(0.15).first, .incident)

        XCTAssertTrue(IntentScorer.score(text: "hello there").scores.isEmpty)
    }

    // MARK: - HSM-7-02: five profiles, distinct emphasis

    func testEveryProfileExistsAndDiffersFromBalanced() {
        let balanced = Set(MIRRouter.baseEmphasis[.balanced]!)
        for profile in MIRProfile.allCases {
            XCTAssertNotNil(MIRRouter.baseEmphasis[profile], "\(profile) has no emphasis")
            if profile != .balanced {
                XCTAssertNotEqual(Set(MIRRouter.baseEmphasis[profile]!), balanced,
                                  "\(profile) emphasis must differ from balanced")
            }
        }
        XCTAssertEqual(MIRProfile.allCases.count, 5)   // charter five
    }

    // MARK: - HSM-7-01: deterministic routing + score-driven additions

    func testRouteIsDeterministic() {
        let scores = IntentScorer.score(text: "incident outage severity rollback runbook")
        let r = MIRRouter()
        XCTAssertEqual(r.route(profile: .balanced, scores: scores),
                       r.route(profile: .balanced, scores: scores))
    }

    func testOffProfileIntentAddsItsSignatureArtifact() {
        // A "balanced" meeting that is really an incident picks up the incident timeline.
        let scores = IntentScorer.score(text: "outage outage incident severity postmortem rollback runbook downtime mitigation alert")
        let chain = MIRRouter().route(profile: .balanced, scores: scores)
        XCTAssertTrue(chain.contains(.incidentTimeline), "off-profile incident should add its signature")
        XCTAssertTrue(chain.starts(with: MIRRouter.baseEmphasis[.balanced]!), "base emphasis preserved first")
    }

    func testHomeIntentNotDuplicated() {
        let scores = IntentScorer.score(text: "architecture design api schema service module dependency pattern")
        let chain = MIRRouter().route(profile: .architect, scores: scores)
        XCTAssertEqual(chain.filter { $0 == .adr }.count, 1, "architect's home intent must not double-add adr")
    }

    // MARK: - HSM-7-03: profile seam on Meeting

    func testProfileSeamRoundTripsOnMeeting() throws {
        var meeting = try fixtureMeeting()
        meeting.mirProfile = .architect
        let data = try HoldSpeakContracts.encoder().encode(meeting)
        let back = try HoldSpeakContracts.decoder().decode(Meeting.self, from: data)
        XCTAssertEqual(back.mirProfile, .architect)
        XCTAssertEqual(back.routingProfile, .architect)

        meeting.mirProfile = nil
        XCTAssertEqual(meeting.routingProfile, .balanced)   // safe default
    }

    // MARK: - HSM-7-04: the gate — profile measurably changes extraction

    func testGateProfileChangesExtraction() async {
        // One identical input; everything constant except the profile.
        let input = transcript([
            "We need to lock the API design and the service schema and the module dependencies.",
            "There was also an incident: an outage with high severity; we did a rollback and a postmortem.",
            "And the customer feedback on the feature roadmap matters for the user requirements.",
        ])
        let gen = RoutedArtifactGenerator(engine: ArtifactGenerationEngine(provider: StubLLM()))

        let control = await gen.generate(from: input, profile: .balanced)
        let treatment = await gen.generate(from: input, profile: .architect)

        let controlTypes = Set(control.artifacts.map(\.artifactType))
        let treatmentTypes = Set(treatment.artifacts.map(\.artifactType))
        let delta = controlTypes.symmetricDifference(treatmentTypes)

        print("HSM-7-04 gate: balanced=\(controlTypes.map(\.rawValue).sorted()) "
            + "architect=\(treatmentTypes.map(\.rawValue).sorted()) delta=\(delta.map(\.rawValue).sorted())")

        XCTAssertFalse(delta.isEmpty, "switching profile must measurably change the artifact set")
        XCTAssertGreaterThan(control.artifacts.count, 0)
        XCTAssertGreaterThan(treatment.artifacts.count, 0)
    }
}
