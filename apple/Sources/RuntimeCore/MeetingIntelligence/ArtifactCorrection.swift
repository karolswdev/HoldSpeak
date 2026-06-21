import Foundation
import Contracts
import Providers

/// HSM-14-07 — voice-driven correction, fully on-device. The user rejects an artifact the
/// local model produced and says (out loud, transcribed by WhisperKit) what's wrong with it;
/// that spoken feedback is fused with the ORIGINAL output and routed back to the same local
/// model to regenerate a corrected version — grounded in the transcript, propose-and-confirm.
/// Pure prompt + a thin corrector over the existing engine, so it's host-testable + model-free.
public enum ArtifactCorrection {

    /// The regeneration prompt: give the model the artifact it previously produced + the
    /// user's correction, and ask for a corrected artifact of the SAME type, faithful to the
    /// transcript.
    public static func prompt(
        type: ArtifactType, original: Artifact, correction: String, transcript: Transcript
    ) -> String {
        let body = transcript.segments.map { "\($0.speaker): \($0.text)" }.joined(separator: "\n")
        let original = original.bodyMarkdown.isEmpty ? original.title : original.bodyMarkdown
        return """
        You are HoldSpeak's meeting-intelligence engine. You previously produced this
        "\(type.rawValue)" artifact for this meeting:

        \(original)

        The user reviewed it and said, in their own words, what is WRONG with it and how to
        fix it:

        "\(correction.trimmingCharacters(in: .whitespacesAndNewlines))"

        Produce a CORRECTED "\(type.rawValue)" artifact that fixes EXACTLY what the user
        flagged, while staying faithful to the transcript below. Do not repeat the mistake.

        Return ONLY a JSON object with these keys:
          "title": a short headline,
          "body_markdown": the corrected artifact written as Markdown,
          "structured_json": an object with the type-specific fields,
          "confidence": a number 0.0–1.0.

        Transcript:
        \(body)
        """
    }

    /// Regenerate `original` addressing the user's spoken `correction`, grounded in
    /// `transcript`, over the given provider. Returns a NEW `.draft` proposal of the same
    /// type, stamped with a `voice_correction` source (propose-and-confirm — the user
    /// approves the corrected version; nothing is auto-committed).
    public static func corrected(
        original: Artifact, correction: String, transcript: Transcript,
        provider: ILLMProvider, maxAttempts: Int = 2,
        idGenerator: @escaping @Sendable () -> String = { UUID().uuidString }
    ) async throws -> Artifact {
        let captured = original
        let pb: ArtifactGenerationEngine.PromptBuilder = { type, t in
            prompt(type: type, original: captured, correction: correction, transcript: t)
        }
        let engine = ArtifactGenerationEngine(
            provider: provider, maxAttempts: maxAttempts, promptBuilder: pb, idGenerator: idGenerator)
        var fixed = try await engine.generate(original.artifactType, from: transcript)
        // Provenance: this draft came from a voice correction of the original.
        fixed.sources.append(ArtifactSource(sourceType: "voice_correction",
                                            sourceRef: String(correction.prefix(140))))
        return fixed
    }
}
