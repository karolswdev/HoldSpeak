import XCTest
import Contracts
@testable import Providers
@testable import RuntimeCore

/// HSM-8-01 — the on-device meeting-capture loop. Fake capture / transcriber / store
/// drive the record → live transcript → persist → reopen flow with no device: the live
/// transcript grows as audio accumulates, and a stopped meeting reopens intact.
final class MeetingCaptureTests: XCTestCase {

    // Capture that emits chunks on demand, so a test can grow the buffer between ticks.
    final class PushCapture: IAudioCapture, @unchecked Sendable {
        private var onChunk: (@Sendable (AudioChunk) -> Void)?
        var started = 0, stopped = 0, throwOnStart = false
        private var seq = 0
        func start(onChunk cb: @escaping @Sendable (AudioChunk) -> Void) throws {
            if throwOnStart { throw NSError(domain: "mic", code: 1) }
            started += 1; onChunk = cb
        }
        func stop() throws { stopped += 1 }
        func emit(_ n: Int) { for _ in 0..<n { onChunk?(AudioChunk(samples: [0], sequence: seq)); seq += 1 } }
    }

    // Yields one "wN" segment per captured chunk — so the transcript reflects the buffer.
    final class CountTranscriber: ITranscriber, @unchecked Sendable {
        let count: Int
        init(count: Int) { self.count = count }
        func transcribe() async throws -> [Segment] {
            (0..<count).map { TranscribedSegment(text: "w\($0)", startTime: Double($0), endTime: Double($0 + 1)).asContractSegment() }
        }
    }

    final class MemStore: MeetingStore, @unchecked Sendable {
        var saved: [String: Meeting] = [:]
        var order: [String] = []
        var failSave = false
        func save(_ m: Meeting) throws {
            if failSave { throw NSError(domain: "db", code: 1) }
            if saved[m.id] == nil { order.append(m.id) }
            saved[m.id] = m
        }
        func list() throws -> [Meeting] { order.compactMap { saved[$0] } }
        func load(id: String) throws -> Meeting? { saved[id] }
    }

    private let fixedDate = Date(timeIntervalSince1970: 1_000_000)

    private func make(_ capture: PushCapture, _ store: MemStore) -> MeetingCapture {
        let date = fixedDate   // copy so the @Sendable closure captures no self
        return MeetingCapture(capture: capture, store: store,
                              makeTranscriber: { CountTranscriber(count: $0.count) },
                              now: { date }, makeID: { "m-1" })
    }

    func testLiveTranscriptGrowsAsSpeechAccumulates() async {
        let cap = PushCapture(); let mc = make(cap, MemStore())
        mc.start()
        XCTAssertEqual(mc.state, .recording(liveTranscript: ""))
        XCTAssertEqual(cap.started, 1)

        cap.emit(2)
        await mc.tick()
        XCTAssertEqual(mc.state, .recording(liveTranscript: "w0 w1"))

        cap.emit(2)
        await mc.tick()
        XCTAssertEqual(mc.state, .recording(liveTranscript: "w0 w1 w2 w3"), "transcript grows with the audio")
    }

    func testStopPersistsAndReopensIntact() async {
        let cap = PushCapture(); let store = MemStore(); let mc = make(cap, store)
        mc.start()
        cap.emit(3)
        let meeting = await mc.stop()

        XCTAssertEqual(cap.stopped, 1)
        guard let meeting else { return XCTFail("expected a saved meeting") }
        XCTAssertEqual(meeting.id, "m-1")
        XCTAssertEqual(meeting.segments.map(\.text), ["w0", "w1", "w2"])
        XCTAssertEqual(meeting.startedAt, fixedDate)
        if case .saved(let s) = mc.state { XCTAssertEqual(s, meeting) } else { XCTFail("expected saved state") }
        // Persisted: it shows in the list AND reopens byte-for-byte.
        XCTAssertEqual(mc.meetings().map(\.id), ["m-1"])
        XCTAssertEqual(mc.reopen(id: "m-1"), meeting)
    }

    func testReopenSurvivesAFreshViewModel() async {
        let store = MemStore()
        // Record + stop on one view-model...
        let cap = PushCapture()
        let recorder = make(cap, store)
        recorder.start(); cap.emit(2); _ = await recorder.stop()
        // ...a brand-new view-model over the SAME store still reopens it (reopen-intact).
        let fresh = make(PushCapture(), store)
        XCTAssertEqual(fresh.reopen(id: "m-1")?.segments.count, 2)
        XCTAssertEqual(fresh.meetings().count, 1)
    }

    func testCaptureStartFailureFails() {
        let cap = PushCapture(); cap.throwOnStart = true
        let mc = make(cap, MemStore())
        mc.start()
        if case .failed = mc.state {} else { XCTFail("expected failed on mic error") }
    }

    func testMeetingIsDurableBeforeCaptureAcceptsAudio() {
        let cap = PushCapture(); let store = MemStore(); let mc = make(cap, store)
        mc.start()
        XCTAssertEqual(cap.started, 1)
        XCTAssertEqual(store.saved["m-1"]?.endedAt, nil)
        XCTAssertEqual(store.saved["m-1"]?.captureStatus, "recording")
        XCTAssertEqual(store.saved["m-1"]?.provenance, "native")
    }

    func testSaveFailureFails() async {
        let cap = PushCapture(); let store = MemStore(); store.failSave = true
        let mc = make(cap, store)
        mc.start(); cap.emit(1)
        _ = await mc.stop()
        if case .failed = mc.state {} else { XCTFail("expected failed on save error") }
    }

    func testStopFallsBackToLastGoodWhenFinalPassBlanks() async {
        // The transcriber yields good text on a short buffer but blanks once it's long
        // (>= 5 chunks) — exactly the on-device [BLANK_AUDIO] symptom. Stop must keep the
        // last good live transcript, not persist the blank.
        let date = fixedDate
        let cap = PushCapture(); let store = MemStore()
        let mc = MeetingCapture(
            capture: cap, store: store,
            makeTranscriber: { CountTranscriber(count: $0.count >= 5 ? 0 : $0.count) },
            now: { date }, makeID: { "m-1" })
        mc.start()
        cap.emit(2); await mc.tick()
        XCTAssertEqual(mc.state, .recording(liveTranscript: "w0 w1"))
        cap.emit(4)                              // now 6 chunks → the final pass blanks
        let meeting = await mc.stop()
        XCTAssertEqual(meeting?.segments.map(\.text), ["w0", "w1"], "blank final pass keeps the last good transcript")
    }

    func testLiveTranscriptDoesNotFlickerToBlank() async {
        let date = fixedDate
        let cap = PushCapture(); let store = MemStore()
        let mc = MeetingCapture(
            capture: cap, store: store,
            makeTranscriber: { CountTranscriber(count: $0.count >= 5 ? 0 : $0.count) },
            now: { date }, makeID: { "m-1" })
        mc.start()
        cap.emit(2); await mc.tick()             // "w0 w1"
        cap.emit(4); await mc.tick()             // blank window → keep showing the last good
        XCTAssertEqual(mc.state, .recording(liveTranscript: "w0 w1"))
    }

    func testTickIsNoOpWhenIdle() async {
        let mc = make(PushCapture(), MemStore())
        await mc.tick()
        XCTAssertEqual(mc.state, .idle)
    }

    func testEgressIsOnDevice() {
        XCTAssertEqual(make(PushCapture(), MemStore()).egressLabel, "on device")
    }
}
