import XCTest
@testable import Providers

/// HSM-2-02 / HSM-2-03: the platform-agnostic core of the audio engine — the
/// chunk stream + bounded accumulator + the 16 kHz WAV export — plus an
/// end-to-end pipeline driven by a fake capture (the live AVAudioEngine service
/// is iOS-only and device-verified).
final class AudioTests: XCTestCase {

    // A test double for IAudioCapture: emits preset chunks synchronously.
    final class FakeAudioCapture: IAudioCapture, @unchecked Sendable {
        let chunks: [AudioChunk]
        init(_ chunks: [AudioChunk]) { self.chunks = chunks }
        func start(onChunk: @escaping @Sendable (AudioChunk) -> Void) throws {
            for c in chunks { onChunk(c) }
        }
        func stop() throws {}
    }

    func testWavHeaderIs16kMonoPCM16() {
        let samples = [Int16](repeating: 0, count: 8_000)   // 0.5 s @ 16 kHz
        let wav = WavWriter.wavData(fromPCM16: samples)

        XCTAssertEqual(wav.count, 44 + 8_000 * 2)           // header + PCM bytes
        XCTAssertEqual(String(data: wav[0..<4], encoding: .ascii), "RIFF")
        XCTAssertEqual(String(data: wav[8..<12], encoding: .ascii), "WAVE")
        XCTAssertEqual(String(data: wav[36..<40], encoding: .ascii), "data")

        func u16(_ o: Int) -> Int { Int(wav[o]) | Int(wav[o + 1]) << 8 }
        func u32(_ o: Int) -> Int { u16(o) | u16(o + 2) << 16 }
        XCTAssertEqual(u16(20), 1)        // PCM
        XCTAssertEqual(u16(22), 1)        // mono
        XCTAssertEqual(u32(24), 16_000)   // sample rate
        XCTAssertEqual(u16(34), 16)       // bits/sample
        XCTAssertEqual(u32(40), 8_000 * 2) // data length
    }

    func testAccumulatorIsBoundedAndCountsDrops() {
        let acc = AudioAccumulator(maxFrames: 1_000)
        acc.append(AudioChunk(samples: [Int16](repeating: 1, count: 800), sequence: 1))
        acc.append(AudioChunk(samples: [Int16](repeating: 2, count: 800), sequence: 2))
        // 1600 appended, cap 1000 -> 600 oldest dropped, 1000 retained.
        XCTAssertEqual(acc.totalFrames, 1_600)
        XCTAssertEqual(acc.retainedFrames, 1_000)
        XCTAssertEqual(acc.droppedFrames, 600)
    }

    func testCaptureToWavPipeline() throws {
        let acc = AudioAccumulator(maxFrames: 16_000 * 60)
        let capture = FakeAudioCapture([
            AudioChunk(samples: Array(repeating: 100, count: 1_600), sequence: 1),
            AudioChunk(samples: Array(repeating: -100, count: 1_600), sequence: 2),
        ])

        try capture.start { acc.append($0) }
        try capture.stop()

        XCTAssertEqual(acc.totalFrames, 3_200)
        let wav = WavWriter.wavData(fromPCM16: acc.drain())
        XCTAssertEqual(wav.count, 44 + 3_200 * 2)            // a valid WAV came out the far end
        XCTAssertEqual(acc.retainedFrames, 0)               // drained
    }
}
