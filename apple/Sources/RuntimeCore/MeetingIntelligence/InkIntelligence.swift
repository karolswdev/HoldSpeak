import Foundation
import Contracts
import Providers

/// Ink into intelligence (HSM-8-06) — the magic pencil made a first-class input, not a
/// parallel scratchpad. Two pure, on-device pieces the app drives:
///   • `InkPromoter` turns a recognized handwritten note (or a marked moment) into a
///     schema-valid Phase-0 `Artifact` proposal (propose-and-confirm; the user approves).
///   • `InkEmphasis` lets the HSM-8-03 marked moments **weight what the model extracts**:
///     the intents found in hand-flagged segments are boosted, so a user-marked moment
///     measurably changes the routed artifact chain vs. the same transcript unmarked.
/// All deterministic + model-free (the air-gapped gate forbids any network path).

public enum InkPromoter {
    /// Build an `Artifact` proposal from handwritten/recognized text. Status `.draft` —
    /// the user confirms it in review; nothing is auto-committed (charter non-goal).
    public static func artifact(
        text: String, type: ArtifactType, meetingID: String,
        atSegment: Int? = nil, id: String, now: Date = Date()
    ) -> Artifact {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        let title = String((trimmed.split(separator: "\n").first.map(String.init) ?? trimmed).prefix(80))
        var structured: [String: JSONValue] = ["source": .string("handwriting")]
        if let s = atSegment { structured["segment"] = .number(Double(s)) }
        return Artifact(
            id: id, meetingId: meetingID, artifactType: type,
            title: title.isEmpty ? "Handwritten note" : title,
            bodyMarkdown: trimmed,
            structuredJson: .object(structured),
            confidence: 0.5, status: .draft,
            pluginId: "holdspeak.mobile.ink", pluginVersion: HoldSpeakContracts.contractVersion,
            sources: [ArtifactSource(sourceType: "handwriting", sourceRef: "notebook")],
            createdAt: now, updatedAt: now)
    }
}

public enum InkEmphasis {
    /// Boost the intents found in the segments a user hand-marked (HSM-8-03), so the
    /// router weights what they flagged. Pure: the same marks always boost the same way.
    public static func emphasized(
        _ base: IntentScores, marks: [Double], in transcript: Transcript, boost: Double = 0.2
    ) -> IntentScores {
        guard !marks.isEmpty else { return base }
        var scores = base.scores
        for mark in marks {
            guard let i = TranscriptLinker.segmentIndex(for: mark, in: transcript.segments) else { continue }
            let local = IntentScorer.score(text: transcript.segments[i].text)
            for (intent, value) in local.scores where value > 0 {
                scores[intent, default: 0] += boost   // flagged by hand → extra weight
            }
        }
        return IntentScores(scores)
    }

    /// The routed artifact chain for a profile, with the marked moments weighting it —
    /// the convenience the app uses so a hand-flagged meeting extracts what was flagged.
    public static func routedTypes(
        profile: MIRProfile, transcript: Transcript, marks: [Double],
        router: MIRRouter = MIRRouter()
    ) -> [ArtifactType] {
        let scores = emphasized(IntentScorer.score(transcript), marks: marks, in: transcript)
        return router.route(profile: profile, scores: scores)
    }
}
