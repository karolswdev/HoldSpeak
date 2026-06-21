import XCTest
import Contracts
import Providers
@testable import RuntimeCore

/// HSM-14-07 — voice-driven on-device correction. The prompt must fuse the original output +
/// the user's spoken correction + the transcript; the corrector must return a same-type
/// `.draft` with voice provenance. Pure + model-free.
final class ArtifactCorrectionTests: XCTestCase {

    private func art(_ type: ArtifactType, _ title: String, _ body: String) -> Artifact {
        Artifact(id: "orig", meetingId: "m", artifactType: type, title: title, bodyMarkdown: body,
                 structuredJson: .object([:]), confidence: 0.6, status: .draft,
                 pluginId: "holdspeak.mobile.intelligence", pluginVersion: "0.1.0",
                 sources: [ArtifactSource(sourceType: "transcript", sourceRef: "h")])
    }
    private var transcript: Transcript {
        Transcript(meetingId: "m", segments: [
            Segment(text: "We ship on Friday the 14th.", speaker: "Ada", startTime: 0, endTime: 3),
        ], transcriptHash: "h")
    }

    func testPromptFusesOriginalCorrectionAndTranscript() {
        let original = art(.decisions, "Ship Friday", "Decision: ship on Friday.")
        let p = ArtifactCorrection.prompt(
            type: .decisions, original: original,
            correction: "You missed the date — it's Friday the 14th.", transcript: transcript)
        XCTAssertTrue(p.contains("decisions"))
        XCTAssertTrue(p.contains("Decision: ship on Friday."))      // the original output
        XCTAssertTrue(p.contains("Friday the 14th"))                // the spoken correction
        XCTAssertTrue(p.contains("We ship on Friday the 14th."))    // grounded in the transcript
    }

    /// A fake provider that returns a corrected draft (as if the model fixed the date).
    final class FixLLM: ILLMProvider, @unchecked Sendable {
        func complete(prompt: String) async throws -> String {
            #"{"title":"Ship Friday the 14th","body_markdown":"Decision: ship on **Friday the 14th**.","confidence":0.9}"#
        }
    }

    func testCorrectedProducesSameTypeDraftWithVoiceProvenance() async throws {
        let original = art(.decisions, "Ship Friday", "Decision: ship on Friday.")
        let fixed = try await ArtifactCorrection.corrected(
            original: original, correction: "it's Friday the 14th", transcript: transcript,
            provider: FixLLM(), idGenerator: { "fixed-1" })
        XCTAssertEqual(fixed.id, "fixed-1")
        XCTAssertEqual(fixed.artifactType, .decisions)                  // same type
        XCTAssertEqual(fixed.status, .draft)                            // propose-and-confirm
        XCTAssertTrue(fixed.bodyMarkdown.contains("Friday the 14th"))   // the model's fix
        XCTAssertTrue(fixed.sources.contains { $0.sourceType == "voice_correction" })  // provenance
    }
}
