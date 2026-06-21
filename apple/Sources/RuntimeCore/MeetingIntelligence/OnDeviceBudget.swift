import Foundation
import Contracts

/// HSM-8-08 — OOM-safe on-device budgeting. The model's context window drives the
/// KV-cache, and the KV-cache is RAM on top of the resident weights. A hard-coded
/// context (the 16K from HSM-8-06) is a bet on the device; this makes it a number the
/// device vouches for: the largest context that leaves a conservative headroom over
/// the model + an estimated KV-cache, clamped to a usable floor and the model's
/// ceiling. Pure + deterministic — the host reads `contextTokens` to size the provider
/// and `needsChunking` to decide whether HSM-8-07's map-reduce kicks in. The increased-
/// memory entitlement is never *assumed*: without it the budget simply lands lower and
/// chunking carries the rest, so correctness is independent of the entitlement.
public enum OnDeviceBudget {

    /// Conservative KV-cache cost per context token (bytes) for a 4B-class GGUF.
    /// Qwen3-4B (GQA, fp16 KV) is ≈ 144 KB/token; we round UP so the estimate biases
    /// toward under-filling rather than an OOM — the entire point of this story.
    public static let kvBytesPerToken = 160_000

    /// The largest safe context (in tokens) for this device.
    /// - availableBytes: memory headroom the app may still draw on (e.g. iOS
    ///   `os_proc_available_memory()` — the bytes left before the jetsam limit), *before*
    ///   the model is resident.
    /// - modelBytes: the GGUF's on-disk size — a proxy for the weights about to load.
    /// - marginBytes: headroom to leave for activations, WhisperKit, the app, the OS.
    ///
    /// Clamped to `[floor, ceiling]`. For any device that can clear the floor's KV cost
    /// the result never exceeds `(availableBytes − modelBytes − marginBytes)` worth of
    /// tokens — it under-fills, it does not gamble.
    public static func contextTokens(
        availableBytes: Int, modelBytes: Int, marginBytes: Int,
        floor: Int = 4_096, ceiling: Int = 16_384
    ) -> Int {
        let forKV = availableBytes - modelBytes - marginBytes
        let affordable = max(0, forKV) / kvBytesPerToken
        return min(ceiling, max(floor, affordable))
    }

    /// How many of the context's tokens may hold transcript text in a *single* pass —
    /// the rest is reserved for the prompt scaffolding + the model's own output. A
    /// transcript longer than this must be chunked (HSM-8-07).
    public static func windowTokens(
        context: Int, promptOverhead: Int = 512, outputReserve: Int = 1_024
    ) -> Int {
        max(256, context - promptOverhead - outputReserve)
    }

    /// A rough token estimate for transcript text (≈ 4 chars/token, English-ish).
    /// Deliberately simple + deterministic; the safety margin absorbs the slop.
    public static func estimateTokens(_ text: String) -> Int { max(1, text.count / 4) }

    /// Total estimated transcript tokens across segments.
    public static func transcriptTokens(_ segments: [Segment]) -> Int {
        segments.reduce(0) { $0 + estimateTokens($1.text) }
    }

    /// Does this transcript need chunking under the chosen window budget? True when
    /// its text won't fit one window's worth of context, so HSM-8-07 windows it.
    public static func needsChunking(transcriptTokens: Int, windowTokens: Int) -> Bool {
        transcriptTokens > windowTokens
    }
}
