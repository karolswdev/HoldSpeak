import Foundation

/// On-device speaker diarization — the matching/clustering half (the model-free, host-testable part).
/// Mirrors the desktop's `holdspeak/speaker_intel.py`: a speaker is a 256-dim L2-normalised voice
/// embedding (from the Core ML `VoiceEncoder`); a new utterance embedding is matched by **cosine
/// similarity** against known speakers, and either folds into the best match above a threshold
/// (refining its profile by an exponential moving average) or starts a new speaker. Same maths as the
/// desktop, so identities stay compatible across devices.
///
/// HSM-14-17. Pure value logic — no Core ML, no audio — so it unit-tests deterministically.

public struct SpeakerProfile: Identifiable, Equatable, Sendable {
    public let id: String
    public var name: String
    public var embedding: [Float]   // L2-normalised, 256-dim
    public var sampleCount: Int

    public init(id: String, name: String, embedding: [Float], sampleCount: Int = 1) {
        self.id = id
        self.name = name
        self.embedding = embedding
        self.sampleCount = sampleCount
    }

    /// Refine the profile with a new embedding (EMA), then re-normalise — exactly the desktop's
    /// `SpeakerEmbedding.update` (default `alpha = 0.3`).
    mutating func fold(_ e: [Float], alpha: Float) {
        guard embedding.count == e.count else { return }
        for i in embedding.indices { embedding[i] = (1 - alpha) * embedding[i] + alpha * e[i] }
        embedding = SpeakerMath.normalized(embedding)
        sampleCount += 1
    }
}

public enum SpeakerMath {
    public static func cosine(_ a: [Float], _ b: [Float]) -> Float {
        guard a.count == b.count, !a.isEmpty else { return 0 }
        var dot: Float = 0, na: Float = 0, nb: Float = 0
        for i in a.indices { dot += a[i] * b[i]; na += a[i] * a[i]; nb += b[i] * b[i] }
        let denom = (na.squareRoot()) * (nb.squareRoot())
        return denom == 0 ? 0 : dot / denom
    }

    public static func normalized(_ v: [Float]) -> [Float] {
        var n: Float = 0
        for x in v { n += x * x }
        n = n.squareRoot()
        guard n > 0 else { return v }
        return v.map { $0 / n }
    }
}

/// Online speaker assignment. Not thread-safe by itself — drive it from the capture loop's serial
/// context (or wrap it). Relative labels ("Speaker 1/2/…") per run; cross-meeting identity (seeding
/// known speakers) is a later layer that just pre-loads `speakers`.
public final class SpeakerMatcher {
    /// Cosine match threshold (the desktop's `SIMILARITY_THRESHOLD`). Above ⇒ same speaker.
    public var threshold: Float
    /// EMA weight for refining a matched profile.
    public var alpha: Float
    public private(set) var speakers: [SpeakerProfile] = []
    private var counter = 0

    public init(threshold: Float = 0.75, alpha: Float = 0.3, known: [SpeakerProfile] = []) {
        self.threshold = threshold
        self.alpha = alpha
        self.speakers = known
        self.counter = known.count
    }

    /// Assign an utterance embedding to a speaker — folding into the best match above `threshold`, else
    /// creating a new speaker. Returns the resolved profile (id + display name).
    @discardableResult
    public func assign(_ raw: [Float]) -> SpeakerProfile {
        let e = SpeakerMath.normalized(raw)
        var best: (idx: Int, sim: Float)?
        for (i, s) in speakers.enumerated() {
            let sim = SpeakerMath.cosine(s.embedding, e)
            if sim >= threshold, best == nil || sim > best!.sim { best = (i, sim) }
        }
        if let b = best {
            speakers[b.idx].fold(e, alpha: alpha)
            return speakers[b.idx]
        }
        counter += 1
        let p = SpeakerProfile(id: "spk-\(counter)", name: "Speaker \(counter)", embedding: e)
        speakers.append(p)
        return p
    }

    /// Best matching speaker for an embedding without mutating (for read-only labelling).
    public func match(_ raw: [Float]) -> SpeakerProfile? {
        let e = SpeakerMath.normalized(raw)
        var best: (idx: Int, sim: Float)?
        for (i, s) in speakers.enumerated() {
            let sim = SpeakerMath.cosine(s.embedding, e)
            if sim >= threshold, best == nil || sim > best!.sim { best = (i, sim) }
        }
        return best.map { speakers[$0.idx] }
    }

    public func rename(_ id: String, to name: String) {
        if let i = speakers.firstIndex(where: { $0.id == id }) { speakers[i].name = name }
    }
}
