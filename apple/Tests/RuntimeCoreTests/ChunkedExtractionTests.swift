import XCTest
import Contracts
import Providers
@testable import RuntimeCore

/// HSM-8-07 + HSM-8-08 — long meetings never gamble on RAM. A memory-aware budget
/// (8-08) sizes the context to the device and decides when to chunk; chunked map-reduce
/// extraction (8-07) windows the transcript, extracts per window, and merges the results
/// so peak memory stays flat regardless of meeting length. Pure + deterministic.
final class ChunkedExtractionTests: XCTestCase {

    private let GiB = 1_073_741_824

    // MARK: OnDeviceBudget (HSM-8-08)

    func testBudgetReturnsCeilingWhenRAMIsAmple() {
        // ~8 GB headroom, 3.2 GB model, 2 GB margin → KV room ≈ 2.8 GB ≈ 18k tokens → ceiling.
        let t = OnDeviceBudget.contextTokens(
            availableBytes: 8 * GiB, modelBytes: 3_435_973_837, marginBytes: 2 * GiB)
        XCTAssertEqual(t, 16_384)
    }

    func testBudgetShrinksOnConstrainedDeviceAndNeverExceedsRAM() {
        let available = 5 * GiB
        let model = 3_435_973_837
        let margin = 768 * 1_048_576
        let t = OnDeviceBudget.contextTokens(availableBytes: available, modelBytes: model, marginBytes: margin)
        XCTAssertLessThan(t, 16_384)                 // can't afford the full ceiling
        XCTAssertGreaterThanOrEqual(t, 4_096)        // but still usable (floor)
        // The chosen context's estimated KV footprint never exceeds the affordable headroom.
        XCTAssertLessThanOrEqual(t * OnDeviceBudget.kvBytesPerToken, available - model - margin)
    }

    func testBudgetIsMonotonicInRAM() {
        let a = OnDeviceBudget.contextTokens(availableBytes: 5_000_000_000, modelBytes: 3_400_000_000, marginBytes: 500_000_000)
        let b = OnDeviceBudget.contextTokens(availableBytes: 6_000_000_000, modelBytes: 3_400_000_000, marginBytes: 500_000_000)
        XCTAssertLessThanOrEqual(a, b)
    }

    func testWindowReservesPromptAndOutput() {
        XCTAssertEqual(OnDeviceBudget.windowTokens(context: 16_384), 16_384 - 512 - 1_024)
    }

    func testNeedsChunkingThreshold() {
        XCTAssertFalse(OnDeviceBudget.needsChunking(transcriptTokens: 1_000, windowTokens: 2_000))
        XCTAssertTrue(OnDeviceBudget.needsChunking(transcriptTokens: 5_000, windowTokens: 2_000))
    }

    // MARK: windowing (HSM-8-07)

    private func seg(_ text: String, _ s: Double) -> Segment {
        Segment(text: text, speaker: "S", startTime: s, endTime: s + 1)
    }

    func testWindowsCoverAllSegmentsAndOverlap() {
        let segs = (0..<6).map { seg(String(repeating: "x", count: 12), Double($0)) }  // ~3 tokens each
        let windows = TranscriptWindowing.windows(segs, maxTokens: 6, overlap: 1)
        XCTAssertGreaterThan(windows.count, 1)
        // Every original segment appears in at least one window (coverage by start time).
        let covered = Set(windows.flatMap { $0 }.map { $0.startTime })
        XCTAssertEqual(covered, Set(segs.map { $0.startTime }))
        // Adjacent windows share the overlap segment.
        XCTAssertEqual(windows[0].last?.startTime, windows[1].first?.startTime)
    }

    func testOversizedSegmentIsKeptWholeNotDropped() {
        let big = seg(String(repeating: "y", count: 400), 0)   // ~100 tokens alone
        let small = seg(String(repeating: "z", count: 12), 1)  // ~3
        let windows = TranscriptWindowing.windows([big, small], maxTokens: 10, overlap: 0)
        XCTAssertTrue(windows.contains { $0.count == 1 && $0[0].startTime == 0 })
        XCTAssertEqual(Set(windows.flatMap { $0 }.map { $0.startTime }), [0, 1])
    }

    func testEmptyTranscriptYieldsNoWindows() {
        XCTAssertTrue(TranscriptWindowing.windows([], maxTokens: 10).isEmpty)
    }

    // MARK: merge (HSM-8-07)

    private func art(_ type: ArtifactType, _ body: String, _ conf: Double, id: String) -> Artifact {
        Artifact(id: id, meetingId: "m", artifactType: type, title: "t", bodyMarkdown: body,
                 structuredJson: .object([:]), confidence: conf, status: .draft,
                 pluginId: "p", pluginVersion: "0.1.0",
                 sources: [ArtifactSource(sourceType: "transcript", sourceRef: "h")])
    }

    func testDedupCollapsesCrossWindowDuplicatesKeepingHigherConfidence() {
        let merged = ArtifactMerge.dedup([
            art(.decisions, "Ship on Friday.", 0.4, id: "a"),
            art(.decisions, "ship on friday", 0.8, id: "b"),   // same item; punctuation/case differ
            art(.actionItems, "Email the vendor", 0.5, id: "c"),
        ])
        XCTAssertEqual(merged.count, 2)                        // the two decisions collapsed
        XCTAssertEqual(merged.first { $0.artifactType == .decisions }?.confidence, 0.8)  // stronger draft kept
    }

    func testDedupKeepsDifferentTypesSeparate() {
        let merged = ArtifactMerge.dedup([
            art(.decisions, "same body", 0.5, id: "a"),
            art(.actionItems, "same body", 0.5, id: "b"),
        ])
        XCTAssertEqual(merged.count, 2)
    }

    // MARK: ChunkedExtractor integration (HSM-8-07)

    /// A fake provider returning a constant valid draft — every window/type yields the
    /// same body, so we can prove cross-window collapse: N windows × M types → M artifacts.
    final class ConstantLLM: ILLMProvider, @unchecked Sendable {
        func complete(prompt: String) async throws -> String {
            #"{"title":"x","body_markdown":"constant body","confidence":0.5}"#
        }
    }

    func testChunkedExtractionWindowsThenMergesAcrossWindows() async {
        let segs = (0..<8).map { seg(String(repeating: "w", count: 20), Double($0)) }  // ~5 tokens each
        let transcript = Transcript(meetingId: "m", segments: segs, transcriptHash: "h")
        let engine = ArtifactGenerationEngine(provider: ConstantLLM())
        let extractor = ChunkedExtractor(engine: engine, windowTokens: 10, overlap: 1)

        XCTAssertTrue(extractor.shouldChunk(transcript))      // 8×5 = 40 tokens > 10
        var passes = 0
        let artifacts = await extractor.generate(
            types: [.decisions, .actionItems], from: transcript,
            onProgress: { _, total in passes = total })
        XCTAssertGreaterThan(passes, 1)                       // ran multiple windows
        XCTAssertEqual(artifacts.count, 2)                    // constant body ⇒ one per type
        XCTAssertEqual(Set(artifacts.map { $0.artifactType }), [.decisions, .actionItems])
        XCTAssertTrue(artifacts.allSatisfy { $0.status == .draft })   // propose-only preserved
    }

    func testShortTranscriptDoesNotChunk() {
        let transcript = Transcript(meetingId: "m", segments: [seg("short", 0)], transcriptHash: "h")
        let extractor = ChunkedExtractor(engine: ArtifactGenerationEngine(provider: ConstantLLM()), windowTokens: 2_000)
        XCTAssertFalse(extractor.shouldChunk(transcript))
    }
}
