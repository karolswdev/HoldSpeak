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
    /// Windows, each ≤ `maxTokens` of transcript text, with `overlap` segments shared
    /// between neighbours. An oversized segment is FIRST split internally (HSM-11-07) — at
    /// sentence boundaries, then words, then a hard char-slice — so the windows are
    /// genuinely bounded even when the on-device transcriber emits the whole meeting as one
    /// giant segment (today's reality until realtime segmentation). This is what makes the
    /// per-pass memory actually flat regardless of meeting length.
    public static func windows(
        _ segments: [Segment], maxTokens: Int, overlap: Int = 1,
        estimate: (String) -> Int = OnDeviceBudget.estimateTokens
    ) -> [[Segment]] {
        let prepared = splitOversized(segments, maxTokens: maxTokens, estimate: estimate)
        guard !prepared.isEmpty else { return [] }
        let safeOverlap = max(0, overlap)
        var windows: [[Segment]] = []
        var start = 0
        while start < prepared.count {
            var window: [Segment] = []
            var tokens = 0
            var end = start
            while end < prepared.count {
                let t = estimate(prepared[end].text)
                if !window.isEmpty && tokens + t > maxTokens { break }   // full — but never empty
                window.append(prepared[end]); tokens += t; end += 1
            }
            windows.append(window)
            if end >= prepared.count { break }
            start = max(start + 1, end - safeOverlap)                    // share `overlap`; always progress
        }
        return windows
    }

    /// Replace any segment whose text exceeds `maxTokens` with sentence-aligned
    /// sub-segments (each ≤ `maxTokens`); segments within budget pass through untouched.
    /// Sub-segments interpolate their start/end across the parent's span by character
    /// offset, so transcript anchoring stays monotonic and the first keeps the parent's
    /// start. This is the fix that lets chunking bound memory for a single giant segment.
    public static func splitOversized(
        _ segments: [Segment], maxTokens: Int,
        estimate: (String) -> Int = OnDeviceBudget.estimateTokens
    ) -> [Segment] {
        var out: [Segment] = []
        for seg in segments {
            guard estimate(seg.text) > maxTokens else { out.append(seg); continue }
            let pieces = splitText(seg.text, maxTokens: maxTokens, estimate: estimate)
            guard pieces.count > 1 else { out.append(seg); continue }   // unsplittable → keep whole
            let span = seg.endTime - seg.startTime
            let totalChars = max(1, pieces.reduce(0) { $0 + $1.count })
            var consumed = 0
            for piece in pieces {
                let s = seg.startTime + span * Double(consumed) / Double(totalChars)
                consumed += piece.count
                let e = seg.startTime + span * Double(consumed) / Double(totalChars)
                out.append(Segment(text: piece, speaker: seg.speaker, speakerId: seg.speakerId,
                                   startTime: s, endTime: e,
                                   isBookmarked: seg.isBookmarked, deviceId: seg.deviceId))
            }
        }
        return out
    }

    /// Split a too-long string into pieces each ≤ `maxTokens`, preferring sentence/space
    /// boundaries and falling back to a hard char cut for a runaway unbroken span. The
    /// original text is preserved exactly (slices, then trimmed per piece).
    static func splitText(
        _ text: String, maxTokens: Int, estimate: (String) -> Int
    ) -> [String] {
        guard estimate(text) > maxTokens else { return [text] }
        let maxChars = max(1, maxTokens * 4)               // estimate() is chars/4
        let chars = Array(text)
        var pieces: [String] = []
        var start = 0
        while start < chars.count {
            let hardEnd = min(start + maxChars, chars.count)
            var end = hardEnd
            if hardEnd < chars.count, let b = lastBoundary(chars, from: start, to: hardEnd) { end = b }
            if end <= start { end = hardEnd }              // no boundary → hard cut; always progress
            let piece = String(chars[start..<end]).trimmingCharacters(in: .whitespacesAndNewlines)
            if !piece.isEmpty { pieces.append(piece) }
            start = end
        }
        return pieces.isEmpty ? [text] : pieces
    }

    /// The latest index in `(start, end]` that ends a sentence (`.!?`/newline) or, failing
    /// that, a word (space/tab) — so a cut lands on a clean boundary when one exists.
    private static func lastBoundary(_ chars: [Character], from start: Int, to end: Int) -> Int? {
        var spaceBoundary: Int? = nil
        var i = end - 1
        while i > start {
            let c = chars[i]
            if c == "." || c == "!" || c == "?" || c == "\n" { return i + 1 }   // latest sentence end
            if (c == " " || c == "\t"), spaceBoundary == nil { spaceBoundary = i + 1 }
            i -= 1
        }
        return spaceBoundary
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
