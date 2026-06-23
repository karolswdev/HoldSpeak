import Foundation
import Contracts
import Providers

/// HSM-14-17 — on-device speaker diarization, wired end to end: take the captured meeting audio and
/// the produced `[Segment]`, and label each segment with WHO spoke it. This is the orchestration
/// half (the matcher + the Core ML embedder are the proven pieces); it mirrors resemblyzer's
/// `VoiceEncoder.embed_utterance`:
///
///   1. slice each segment's audio out of the take (by its `startTime`/`endTime`),
///   2. convert PCM16 → float [-1, 1],
///   3. **volume-normalise to −30 dBFS** (resemblyzer's `preprocess_wav` does the same — the
///      embeddings only match the desktop after this gain),
///   4. split into 25 440-sample partials (the model's input window; zero-pad the short last one),
///   5. embed each partial via the Core ML model,
///   6. **average the partial embeddings and L2-normalise** (resemblyzer's utterance embedding),
///   7. `SpeakerMatcher.assign` → fold into the best speaker above threshold, else a new one.
///
/// ONE `SpeakerMatcher` is reused across the whole meeting so "Speaker 1/2/…" stay consistent.
///
/// The DSP-free maths (dBFS gain, partial slicing, mean+normalise) is pure and host-tested; the only
/// non-portable part is the Core ML embedder, injected behind `AudioEmbedding`.

/// The injected embedder seam: one 25 440-sample float partial → a 256-dim embedding. The Core ML
/// `AudioEmbedder` (Providers) conforms on device; tests inject a deterministic stub.
public protocol AudioEmbedding: Sendable {
    func embed(partial: [Float]) throws -> [Float]
}

#if canImport(CoreML)
extension AudioEmbedder: AudioEmbedding {}
#endif

/// The pure (no Core ML, no model) maths of the diarize pipeline — host-testable in full.
public enum DiarizeMath {
    public static let partialSamples = audioEmbedPartialSamples   // 25_440
    public static let targetDBFS: Float = -30

    /// PCM16 slice for a segment, as float [-1, 1]. Clamps the window to the buffer.
    public static func floatSlice(_ audio: [Int16], start: Double, end: Double, sampleRate: Int) -> [Float] {
        guard sampleRate > 0, end > start, !audio.isEmpty else { return [] }
        let lo = Swift.max(0, Int(start * Double(sampleRate)))
        let hi = Swift.min(audio.count, Int(end * Double(sampleRate)))
        guard hi > lo else { return [] }
        return audio[lo..<hi].map { Float($0) / 32768.0 }
    }

    /// dBFS of a float signal (`20·log10(rms)`), or `nil` if silent (rms == 0) — caller skips.
    public static func dBFS(_ x: [Float]) -> Float? {
        guard !x.isEmpty else { return nil }
        var sum: Float = 0
        for s in x { sum += s * s }
        let rms = (sum / Float(x.count)).squareRoot()
        guard rms > 0 else { return nil }
        return 20 * log10(rms)
    }

    /// The gain (linear multiplier) that lifts `x` to −30 dBFS — `nil` if `x` is silent (skip it).
    /// Matches resemblyzer's `normalize_volume(..., target_dBFS=-30, increase_only=False)`.
    public static func normGain(_ x: [Float]) -> Float? {
        guard let db = dBFS(x) else { return nil }
        return pow(10, (targetDBFS - db) / 20)
    }

    /// Volume-normalise to −30 dBFS; returns `nil` for a silent slice (no embedding worth making).
    public static func volumeNormalized(_ x: [Float]) -> [Float]? {
        guard let g = normGain(x) else { return nil }
        return x.map { $0 * g }
    }

    /// Slice a (normalised) utterance into fixed 25 440-sample partials.
    ///
    /// When the utterance is **shorter than one partial**, we DO NOT zero-pad the tail with silence —
    /// a partial that is mostly silence embeds to near-random, which is exactly what spawned a fresh
    /// speaker per short fragment (the over-split). Instead we **tile (repeat) the voiced audio** to
    /// fill the 25 440-sample window, so the single partial is all voice. (The diarizer already
    /// refuses anything below `minDurationSeconds` ≈ 1 s, so this only ever tiles ≥1 s of real
    /// speech.) Multi-partial utterances (≥1.6 s) keep the original windowing: a short trailing
    /// remainder there is averaged in with full voiced partials, so zero-padding it is harmless.
    public static func partials(_ x: [Float]) -> [[Float]] {
        guard !x.isEmpty else { return [] }
        // Sub-partial utterance: tile the voiced samples to fill exactly one window (no silence).
        if x.count < partialSamples {
            var p = [Float](); p.reserveCapacity(partialSamples)
            while p.count < partialSamples {
                p.append(contentsOf: x.prefix(partialSamples - p.count))
            }
            return [p]
        }
        var out: [[Float]] = []
        var i = 0
        while i < x.count {
            let hi = Swift.min(i + partialSamples, x.count)
            var p = Array(x[i..<hi])
            if p.count < partialSamples { p.append(contentsOf: repeatElement(0, count: partialSamples - p.count)) }
            out.append(p)
            i += partialSamples
        }
        return out
    }

    /// Resemblyzer's utterance embedding: the L2-normalised mean of the per-partial embeddings.
    public static func meanEmbedding(_ embeddings: [[Float]]) -> [Float]? {
        guard let first = embeddings.first, !first.isEmpty else { return nil }
        var acc = [Float](repeating: 0, count: first.count)
        for e in embeddings where e.count == acc.count {
            for i in acc.indices { acc[i] += e[i] }
        }
        for i in acc.indices { acc[i] /= Float(embeddings.count) }
        return SpeakerMath.normalized(acc)
    }
}

/// Global agglomerative clustering — the OFFLINE diarization pass (the owner's insight): instead of
/// greedily assigning each segment in order against a database still filling up (which judges early
/// segments against an empty/immature set and over-splits), collect EVERY segment embedding first and
/// cluster the whole set together. Each embedding starts as its own cluster; repeatedly merge the two
/// clusters whose mean embeddings are most similar, while that similarity ≥ `threshold`. Order-
/// independent: it can MERGE speakers the online pass wrongly split, and converges on the true speaker
/// count. Returns a cluster label per input (0-based, ordered by first appearance, so the earliest
/// voice is Speaker 1). O(n³) worst case; n = embedded segments per meeting (small).
public enum SpeakerClustering {
    public static func cluster(_ embeddings: [[Float]], threshold: Float) -> [Int] {
        let n = embeddings.count
        guard n > 0 else { return [] }
        var members: [[Int]] = (0..<n).map { [$0] }
        var centroids: [[Float]] = embeddings.map { SpeakerMath.normalized($0) }
        while members.count > 1 {
            var best: (a: Int, b: Int, sim: Float)?
            for a in 0..<members.count {
                for b in (a + 1)..<members.count {
                    let s = SpeakerMath.cosine(centroids[a], centroids[b])
                    if best == nil || s > best!.sim { best = (a, b, s) }
                }
            }
            guard let m = best, m.sim >= threshold else { break }     // nothing close enough left
            members[m.a].append(contentsOf: members[m.b])
            centroids[m.a] = mean(members[m.a].map { embeddings[$0] })
            members.remove(at: m.b); centroids.remove(at: m.b)
        }
        var label = [Int](repeating: 0, count: n)
        let ordered = members.sorted { ($0.min() ?? 0) < ($1.min() ?? 0) }   // earliest-spoken = Speaker 1
        for (newId, group) in ordered.enumerated() { for p in group { label[p] = newId } }
        return label
    }

    static func mean(_ es: [[Float]]) -> [Float] {
        guard let first = es.first else { return [] }
        var acc = [Float](repeating: 0, count: first.count)
        for e in es where e.count == acc.count { for i in acc.indices { acc[i] += e[i] } }
        for i in acc.indices { acc[i] /= Float(es.count) }
        return SpeakerMath.normalized(acc)
    }
}

/// Drives the pipeline over a meeting as a TWO-PHASE OFFLINE pass: (1) embed every ≥`minDuration`
/// segment, (2) globally cluster the full embedding set, (3) label segments by cluster (short segments
/// inherit a neighbour). This is the post-capture quality pass — every segment is judged against the
/// complete speaker set, not a database that's still filling up.
public final class SpeakerDiarizer: @unchecked Sendable {
    private let embedder: AudioEmbedding

    /// The cosine merge threshold for the global clustering (the desktop's `SIMILARITY_THRESHOLD`).
    /// Higher ⇒ more speakers (stricter); lower ⇒ fewer (more merging). Tunable; default 0.75.
    public var threshold: Float

    /// Mirrors the desktop's `MIN_AUDIO_DURATION = 1.0 s`. Segments shorter than this aren't embedded
    /// (a sub-second slice embeds near-random); they **inherit the nearest labelled segment's speaker**.
    public let minDurationSeconds: Double

    private var _speakers: [SpeakerProfile] = []

    public init(embedder: AudioEmbedding, threshold: Float = 0.75, alpha: Float = 0.3,
                minDurationSeconds: Double = 1.0) {
        self.embedder = embedder
        self.threshold = threshold
        self.minDurationSeconds = minDurationSeconds
    }

    public func diarize(_ segments: [Segment], audio: [Int16], sampleRate: Int) -> [Segment] {
        var out = segments

        // Phase 1 — embed every ≥ minDuration segment (order-independent; just collect them).
        var embeddedIdx: [Int] = []
        var embeddings: [[Float]] = []
        for idx in out.indices {
            let seg = out[idx]
            guard (seg.endTime - seg.startTime) >= minDurationSeconds else { continue }
            let raw = DiarizeMath.floatSlice(audio, start: seg.startTime, end: seg.endTime, sampleRate: sampleRate)
            guard let normed = DiarizeMath.volumeNormalized(raw) else { continue }
            let parts = DiarizeMath.partials(normed)
            guard !parts.isEmpty else { continue }
            var embs: [[Float]] = []
            embs.reserveCapacity(parts.count)
            for p in parts { if let e = try? embedder.embed(partial: p) { embs.append(e) } }
            guard let utterance = DiarizeMath.meanEmbedding(embs) else { continue }
            embeddedIdx.append(idx); embeddings.append(utterance)
        }
        guard !embeddings.isEmpty else { return out }

        // Phase 2 — cluster the FULL set globally (the quality pass).
        let labels = SpeakerClustering.cluster(embeddings, threshold: threshold)
        let clusterCount = (labels.max() ?? -1) + 1

        // Build one SpeakerProfile per cluster from its members' mean embedding (mature centroid).
        _speakers = (0..<clusterCount).map { c in
            let members = labels.indices.filter { labels[$0] == c }
            let centroid = DiarizeMath.meanEmbedding(members.map { embeddings[$0] }) ?? embeddings[members[0]]
            return SpeakerProfile(id: "spk-\(c + 1)", name: "Speaker \(c + 1)",
                                  embedding: centroid, sampleCount: members.count)
        }

        // Phase 3 — label embedded segments by their cluster; short/skipped ones inherit the running speaker.
        var lastSpeaker: (name: String, id: String?)?
        var pos = 0
        for idx in out.indices {
            if pos < embeddedIdx.count, embeddedIdx[pos] == idx {
                let p = _speakers[labels[pos]]
                out[idx].speaker = p.name; out[idx].speakerId = p.id
                lastSpeaker = (p.name, p.id)
                pos += 1
            } else if let last = lastSpeaker {
                out[idx].speaker = last.name; out[idx].speakerId = last.id
            }
        }
        return out
    }

    /// The speakers discovered this meeting (for later rename / cross-meeting identity).
    public var speakers: [SpeakerProfile] { _speakers }
}
