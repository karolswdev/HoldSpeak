import Foundation
import Contracts
import Providers

/// HSM-8-07 — chunked map-reduce extraction for long meetings. Windows a transcript
/// into budget-bounded, segment-aligned, overlapping chunks (so a decision spanning a
/// boundary is captured), extracts per window over the existing engine, then merges the
/// per-window artifacts into one deduplicated set. Peak context stays FLAT with meeting
/// length — a 2-hour transcript uses the same per-pass context as a 20-minute one — so
/// we never grow the window to fit and never gamble on RAM (HSM-8-08 sizes the budget).
/// All on-device (the air-gapped gate forbids any network path).

public enum TranscriptWindowing {
    /// Segment-aligned windows, each ≤ `maxTokens` of transcript text, with `overlap`
    /// segments shared between neighbours. Never splits a segment. A single segment that
    /// already exceeds `maxTokens` is kept whole in its own window rather than dropped —
    /// correctness over the budget for the pathological case (the budget has slack for it).
    public static func windows(
        _ segments: [Segment], maxTokens: Int, overlap: Int = 1,
        estimate: (String) -> Int = OnDeviceBudget.estimateTokens
    ) -> [[Segment]] {
        guard !segments.isEmpty else { return [] }
        let safeOverlap = max(0, overlap)
        var windows: [[Segment]] = []
        var start = 0
        while start < segments.count {
            var window: [Segment] = []
            var tokens = 0
            var end = start
            while end < segments.count {
                let t = estimate(segments[end].text)
                if !window.isEmpty && tokens + t > maxTokens { break }   // full — but never empty
                window.append(segments[end]); tokens += t; end += 1
            }
            windows.append(window)
            if end >= segments.count { break }
            start = max(start + 1, end - safeOverlap)                    // share `overlap`; always progress
        }
        return windows
    }
}

public enum ArtifactMerge {
    /// Merge per-window artifacts into one set: keep one per (type + normalized body),
    /// preferring the higher-confidence copy. Order-stable by first appearance — so a
    /// decision found in three overlapping windows surfaces once, not three times.
    public static func dedup(_ artifacts: [Artifact]) -> [Artifact] {
        var indexByKey: [String: Int] = [:]
        var out: [Artifact] = []
        for a in artifacts {
            let body = a.bodyMarkdown.isEmpty ? a.title : a.bodyMarkdown
            let key = "\(a.artifactType.rawValue)\u{1}\(normalize(body))"
            if let idx = indexByKey[key] {
                if a.confidence > out[idx].confidence { out[idx] = a }   // keep the stronger draft
            } else {
                indexByKey[key] = out.count
                out.append(a)
            }
        }
        return out
    }

    /// Whitespace/punctuation/case-insensitive normalization so trivially-different
    /// restatements of the same item collapse.
    static func normalize(_ s: String) -> String {
        s.lowercased()
            .split(whereSeparator: { $0.isWhitespace || $0.isPunctuation })
            .joined(separator: " ")
    }
}

/// Drives the engine over windows and merges. The caller opens the provider ONCE at the
/// windowed budget (HSM-8-08), so peak context is one window's worth regardless of how
/// long the meeting ran — the OOM guard made structural.
public struct ChunkedExtractor: Sendable {
    let engine: ArtifactGenerationEngine
    let windowTokens: Int
    let overlap: Int

    public init(engine: ArtifactGenerationEngine, windowTokens: Int, overlap: Int = 1) {
        self.engine = engine
        self.windowTokens = windowTokens
        self.overlap = overlap
    }

    /// Whether `transcript` needs windowing (else the caller uses the single fast pass).
    public func shouldChunk(_ transcript: Transcript) -> Bool {
        OnDeviceBudget.needsChunking(
            transcriptTokens: OnDeviceBudget.transcriptTokens(transcript.segments),
            windowTokens: windowTokens)
    }

    /// Map-reduce: extract `types` over each window, merge into one deduped set. Each
    /// window's artifacts keep a `#w<i>` provenance suffix on the transcript hash so the
    /// source window is traceable. `onProgress(windowIndex, windowCount)` lets the host
    /// stream the passes rather than show a dead spinner.
    public func generate(
        types: [ArtifactType], from transcript: Transcript,
        onProgress: ((Int, Int) -> Void)? = nil
    ) async -> [Artifact] {
        let windows = TranscriptWindowing.windows(
            transcript.segments, maxTokens: windowTokens, overlap: overlap)
        guard !windows.isEmpty else { return [] }
        var all: [Artifact] = []
        for (idx, window) in windows.enumerated() {
            onProgress?(idx, windows.count)
            let sub = Transcript(meetingId: transcript.meetingId, segments: window,
                                 transcriptHash: "\(transcript.transcriptHash)#w\(idx)")
            for outcome in await engine.generate(types: types, from: sub) {
                if case .success(let a) = outcome.result { all.append(a) }   // failures drop, others survive
            }
        }
        return ArtifactMerge.dedup(all)
    }
}
