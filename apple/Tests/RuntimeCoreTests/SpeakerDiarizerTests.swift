import XCTest
@testable import RuntimeCore
import Contracts

/// HSM-14-17 — host tests for the pure diarize pipeline maths (no Core ML, no device) plus the
/// end-to-end orchestration through a deterministic stub embedder.
final class SpeakerDiarizerTests: XCTestCase {

    // MARK: float slicing

    func testFloatSliceWindowsAndScales() {
        // 16 kHz: 1s = 16000 samples. Slice [0.5, 1.0) -> samples 8000..<16000.
        let audio = (0..<16_000).map { Int16($0 % 100) }
        let s = DiarizeMath.floatSlice(audio, start: 0.5, end: 1.0, sampleRate: 16_000)
        XCTAssertEqual(s.count, 8_000)
        XCTAssertEqual(s.first!, Float(8_000 % 100) / 32768.0, accuracy: 1e-9)
    }

    func testFloatSliceClampsAndRejectsEmpty() {
        let audio = [Int16](repeating: 1000, count: 1_000)
        XCTAssertEqual(DiarizeMath.floatSlice(audio, start: 0, end: 10, sampleRate: 16_000).count, 1_000) // clamped to buffer
        XCTAssertTrue(DiarizeMath.floatSlice(audio, start: 1, end: 0, sampleRate: 16_000).isEmpty)        // end<=start
        XCTAssertTrue(DiarizeMath.floatSlice([], start: 0, end: 1, sampleRate: 16_000).isEmpty)
    }

    // MARK: dBFS + normalize gain (resemblyzer's -30 dBFS preprocess)

    func testDBFSAndSilence() {
        XCTAssertNil(DiarizeMath.dBFS([0, 0, 0]))                 // silent -> nil
        // rms 0.1 -> 20*log10(0.1) = -20 dBFS
        let db = DiarizeMath.dBFS([Float](repeating: 0.1, count: 100))
        XCTAssertEqual(db!, -20, accuracy: 1e-4)
    }

    func testNormGainLiftsToMinus30dBFS() {
        // Signal at -20 dBFS; gain should bring it to -30 dBFS, i.e. multiply by 10^((-30+20)/20)=0.3162.
        let x = [Float](repeating: 0.1, count: 100)
        let g = DiarizeMath.normGain(x)!
        XCTAssertEqual(g, pow(10, -10.0/20.0), accuracy: 1e-5)
        let normed = DiarizeMath.volumeNormalized(x)!
        XCTAssertEqual(DiarizeMath.dBFS(normed)!, -30, accuracy: 1e-3)
    }

    func testVolumeNormalizedSilentIsNil() {
        XCTAssertNil(DiarizeMath.volumeNormalized([Float](repeating: 0, count: 50)))
    }

    // MARK: partials (zero-pad the short last one; always >= 1)

    func testPartialsExactAndPadded() {
        let n = DiarizeMath.partialSamples
        // 1.5 partials -> 2 partials, the second zero-padded.
        let x = [Float](repeating: 0.5, count: n + n / 2)
        let parts = DiarizeMath.partials(x)
        XCTAssertEqual(parts.count, 2)
        XCTAssertTrue(parts.allSatisfy { $0.count == n })
        // last partial: first n/2 are signal, rest zero.
        XCTAssertEqual(parts[1][n / 2], 0)
        XCTAssertEqual(parts[1][0], 0.5)
    }

    func testPartialsShortInputIsOnePadded() {
        let parts = DiarizeMath.partials([Float](repeating: 1, count: 10))
        XCTAssertEqual(parts.count, 1)
        XCTAssertEqual(parts[0].count, DiarizeMath.partialSamples)
    }

    func testPartialsEmptyIsEmpty() {
        XCTAssertTrue(DiarizeMath.partials([]).isEmpty)
    }

    // MARK: mean embedding (L2-normed mean of partials)

    func testMeanEmbeddingIsL2NormedMean() {
        let e = DiarizeMath.meanEmbedding([[3, 0, 0], [0, 0, 0]])!
        // mean = [1.5, 0, 0] -> normalised [1, 0, 0]
        XCTAssertEqual(e, [1, 0, 0])
    }

    // MARK: end-to-end through a stub embedder

    /// A stub that returns one of two fixed orthogonal embeddings based on the partial's mean sign —
    /// so two differently-signed utterances must separate into two speakers.
    struct SignEmbedder: AudioEmbedding {
        func embed(partial: [Float]) throws -> [Float] {
            let mean = partial.reduce(0, +) / Float(max(1, partial.count))
            return mean >= 0 ? [1, 0, 0, 0] : [0, 1, 0, 0]
        }
    }

    func testDiarizeSeparatesTwoSpeakersAndLabels() {
        let n = 16_000
        // segment A: 0.0–1.0s positive; segment B: 1.0–2.0s negative; segment C: 2.0–3.0s positive (==A).
        var audio = [Int16](repeating: 0, count: 3 * n)
        for i in 0..<n { audio[i] = 4000 }                 // A: positive
        for i in n..<(2*n) { audio[i] = -4000 }            // B: negative
        for i in (2*n)..<(3*n) { audio[i] = 4000 }         // C: positive
        let segs = [
            Segment(text: "a", speaker: "Speaker", startTime: 0, endTime: 1),
            Segment(text: "b", speaker: "Speaker", startTime: 1, endTime: 2),
            Segment(text: "c", speaker: "Speaker", startTime: 2, endTime: 3),
        ]
        let d = SpeakerDiarizer(embedder: SignEmbedder())
        let out = d.diarize(segs, audio: audio, sampleRate: 16_000)
        XCTAssertEqual(out.count, 3)
        XCTAssertEqual(out[0].speaker, "Speaker 1")
        XCTAssertEqual(out[1].speaker, "Speaker 2")
        XCTAssertEqual(out[2].speaker, "Speaker 1")        // C folds back into A
        XCTAssertNotNil(out[0].speakerId)
        XCTAssertEqual(out[0].speakerId, out[2].speakerId)
        XCTAssertNotEqual(out[0].speakerId, out[1].speakerId)
        XCTAssertEqual(d.speakers.count, 2)
    }

    func testDiarizeSkipsSilentSegmentKeepingLabel() {
        let segs = [Segment(text: "x", speaker: "Original", startTime: 0, endTime: 1)]
        let audio = [Int16](repeating: 0, count: 16_000)   // silent
        let out = SpeakerDiarizer(embedder: SignEmbedder()).diarize(segs, audio: audio, sampleRate: 16_000)
        XCTAssertEqual(out[0].speaker, "Original")          // untouched
    }
}
