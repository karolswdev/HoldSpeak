import XCTest
import Contracts
@testable import Providers
@testable import RuntimeCore

/// HSM-13-02 — the native voice-note composer at the Runtime-Core layer. Fake
/// capture / transcriber / desktop seams drive the state machine with no device:
/// capture → transcribe → review → deliver. The load-bearing assertion is the
/// owner's hard line — **nothing is delivered before an explicit `send()`**.
final class VoiceNoteComposerTests: XCTestCase {

    // A capture seam that emits canned chunks synchronously on start.
    final class EmittingCapture: IAudioCapture, @unchecked Sendable {
        let chunks: [AudioChunk]
        var started = 0
        var stopped = 0
        var throwOnStart = false
        init(_ chunks: [AudioChunk]) { self.chunks = chunks }
        func start(onChunk: @escaping @Sendable (AudioChunk) -> Void) throws {
            if throwOnStart { throw NSError(domain: "mic", code: 1) }
            started += 1
            for c in chunks { onChunk(c) }
        }
        func stop() throws { stopped += 1 }
    }

    // A transcriber that returns canned segments (or throws). Records the chunk count
    // it was built with, so we can prove the captured audio reached it.
    final class CannedTranscriber: ITranscriber, @unchecked Sendable {
        let segments: [Segment]
        let fail: Bool
        init(segments: [Segment], fail: Bool = false) { self.segments = segments; self.fail = fail }
        func transcribe() async throws -> [Segment] {
            if fail { throw NSError(domain: "whisper", code: 2) }
            return segments
        }
    }

    final class ChunkBox: @unchecked Sendable { var received: [AudioChunk] = [] }

    private func seg(_ text: String, _ s: Double, _ e: Double) -> Segment {
        TranscribedSegment(text: text, startTime: s, endTime: e).asContractSegment()
    }

    private func chunk(_ n: Int) -> AudioChunk { AudioChunk(samples: Array(repeating: 0, count: 8), sequence: n) }

    /// Build a composer wired to fakes; returns the composer + the fakes for asserts.
    private func make(
        chunks: [AudioChunk] = [],
        segments: [Segment] = [],
        transcribeFails: Bool = false,
        reachable: Bool = true
    ) -> (VoiceNoteComposer, EmittingCapture, CompanionMeetingsTests.FakeDesktop, ChunkBox) {
        let capture = EmittingCapture(chunks)
        let desktop = CompanionMeetingsTests.FakeDesktop(reachable: reachable)
        let box = ChunkBox()
        let composer = VoiceNoteComposer(
            capture: capture,
            client: desktop,
            makeTranscriber: { received in
                box.received = received
                return CannedTranscriber(segments: segments, fail: transcribeFails)
            }
        )
        return (composer, capture, desktop, box)
    }

    func testHappyPath_captureTranscribeReviewDeliver() async {
        let (composer, capture, desktop, box) = make(
            chunks: [chunk(0), chunk(1), chunk(2)],
            segments: [seg("ship it", 0, 1), seg("on friday", 1, 2)]
        )
        XCTAssertEqual(composer.state, .idle)

        composer.startRecording()
        XCTAssertEqual(composer.state, .recording)
        XCTAssertEqual(capture.started, 1)

        await composer.stopAndTranscribe()
        XCTAssertEqual(capture.stopped, 1)
        XCTAssertEqual(box.received.count, 3, "the captured chunks reached the transcriber")
        XCTAssertEqual(composer.state, .review(text: "ship it on friday"))
        XCTAssertTrue(desktop.remoteSent.isEmpty, "nothing delivered before send")

        let final = await composer.send()
        XCTAssertEqual(desktop.remoteSent, ["ship it on friday"])
        XCTAssertEqual(final, .delivered(RemoteDictationResult(success: true, finalText: "ship it on friday", delivered: true)))
        XCTAssertEqual(composer.state, final)
    }

    func testTranscriptionNeverAutoSends() async {
        let (composer, _, desktop, _) = make(chunks: [chunk(0)], segments: [seg("hello", 0, 1)])
        composer.startRecording()
        await composer.stopAndTranscribe()
        // Recognition landed in review and delivered NOTHING on its own.
        XCTAssertEqual(composer.state, .review(text: "hello"))
        XCTAssertTrue(desktop.remoteSent.isEmpty)
    }

    func testEditChangesTheDeliveredPayload() async {
        let (composer, _, desktop, _) = make(chunks: [chunk(0)], segments: [seg("raw recognition", 0, 1)])
        composer.startRecording()
        await composer.stopAndTranscribe()
        composer.editText("the corrected answer")
        XCTAssertEqual(composer.state, .review(text: "the corrected answer"))
        await composer.send()
        XCTAssertEqual(desktop.remoteSent, ["the corrected answer"], "the edited text is what ships")
    }

    func testEditOutsideReviewIsNoOp() async {
        let (composer, _, _, _) = make()
        composer.editText("nope")           // still idle
        XCTAssertEqual(composer.state, .idle)
    }

    func testTranscribeFailure_failsAndDeliversNothing() async {
        let (composer, _, desktop, _) = make(chunks: [chunk(0)], transcribeFails: true)
        composer.startRecording()
        await composer.stopAndTranscribe()
        if case .failed(let stage, _) = composer.state { XCTAssertEqual(stage, .transcribe) } else { XCTFail("expected transcribe failure") }
        XCTAssertTrue(desktop.remoteSent.isEmpty)
    }

    func testCaptureStartFailure_failsAtCapture() async {
        let (composer, capture, _, _) = make()
        capture.throwOnStart = true
        composer.startRecording()
        if case .failed(let stage, _) = composer.state { XCTAssertEqual(stage, .capture) } else { XCTFail("expected capture failure") }
    }

    func testDeliveryFailure_unreachableDesktop_failsAtDeliver() async {
        let (composer, _, _, _) = make(chunks: [chunk(0)], segments: [seg("answer", 0, 1)], reachable: false)
        composer.startRecording()
        await composer.stopAndTranscribe()
        XCTAssertEqual(composer.state, .review(text: "answer"))   // transcription is on-device, still works
        await composer.send()
        if case .failed(let stage, _) = composer.state { XCTAssertEqual(stage, .deliver) } else { XCTFail("expected deliver failure") }
    }

    func testEmptyRecognition_guardsTheSend() async {
        let (composer, _, desktop, _) = make(chunks: [chunk(0)], segments: [seg("   ", 0, 1)])
        composer.startRecording()
        await composer.stopAndTranscribe()
        XCTAssertEqual(composer.state, .review(text: ""))
        await composer.send()
        if case .failed(let stage, _) = composer.state { XCTAssertEqual(stage, .deliver) } else { XCTFail("expected guarded send") }
        XCTAssertTrue(desktop.remoteSent.isEmpty, "an empty note never reaches the coder")
    }

    func testSendFromIdleIsNoOp() async {
        let (composer, _, desktop, _) = make()
        let result = await composer.send()
        XCTAssertEqual(result, .idle)
        XCTAssertTrue(desktop.remoteSent.isEmpty)
    }

    func testEgressLabelMirrorsTheClient() {
        let (composer, _, _, _) = make()
        XCTAssertEqual(composer.egressLabel, "local + LAN → fake.desk")
    }
}
