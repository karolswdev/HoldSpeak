import XCTest
import Contracts
@testable import Providers
@testable import RuntimeCore

/// HSM-14-12 — constant-time live transcription. The capture loop must re-transcribe only a
/// bounded *active window* (not the whole take), commit its settled front, and still present a
/// complete, monotonic live transcript. These tests drive that with a fake timestamped
/// transcriber and a capture whose chunk N carries sample value N, so the output text is tied to
/// **absolute** audio position — any loss or duplication across a commit boundary shows up as a
/// wrong word sequence. Tuned tiny (`sampleRate: 1` ⇒ 1 frame = 1 s) so commits fire cheaply.
final class SlidingWindowTests: XCTestCase {

    /// Chunk N carries sample value N (one frame each). Lets the transcriber emit position-tied text.
    final class IndexedCapture: IAudioCapture, @unchecked Sendable {
        private var cb: (@Sendable (AudioChunk) -> Void)?
        private var seq = 0
        var started = 0, stopped = 0
        func start(onChunk f: @escaping @Sendable (AudioChunk) -> Void) throws { started += 1; cb = f }
        func stop() throws { stopped += 1 }
        func emit(_ n: Int) { for _ in 0..<n { cb?(AudioChunk(samples: [Int16(seq)], sequence: seq)); seq += 1 } }
    }

    /// Shared across the per-tick transcribers: records the largest window ever transcribed and
    /// can force blank passes (the non-speech `[BLANK_AUDIO]` case) on windows above a frame count.
    final class Recorder: @unchecked Sendable {
        private let lock = NSLock()
        private(set) var maxFrames = 0
        var blankAbove: Int? = nil
        func note(_ f: Int) { lock.lock(); maxFrames = max(maxFrames, f); lock.unlock() }
    }

    /// One 1-second segment per window frame: text `w<absolute value>`, timestamps **window-relative**
    /// (exactly what WhisperKit returns for the slice it was handed).
    final class WindowTranscriber: ITranscriber, @unchecked Sendable {
        let chunks: [AudioChunk]; let rec: Recorder
        init(_ c: [AudioChunk], _ r: Recorder) { chunks = c; rec = r }
        func transcribe() async throws -> [Segment] {
            let values = chunks.flatMap { $0.samples }
            rec.note(values.count)
            if let cap = rec.blankAbove, values.count > cap { return [] }
            return values.enumerated().map { j, v in
                TranscribedSegment(text: "w\(v)", startTime: Double(j), endTime: Double(j + 1)).asContractSegment()
            }
        }
    }

    final class MemStore: MeetingStore, @unchecked Sendable {
        var saved: [String: Meeting] = [:]; var order: [String] = []
        func save(_ m: Meeting) throws { if saved[m.id] == nil { order.append(m.id) }; saved[m.id] = m }
        func list() throws -> [Meeting] { order.compactMap { saved[$0] } }
        func load(id: String) throws -> Meeting? { saved[id] }
    }

    private func make(_ cap: IndexedCapture, _ rec: Recorder, _ store: MemStore = MemStore()) -> MeetingCapture {
        let date = Date(timeIntervalSince1970: 1_000_000)
        return MeetingCapture(capture: cap, store: store,
                              makeTranscriber: { WindowTranscriber($0, rec) },
                              now: { date }, makeID: { "m-1" },
                              sampleRate: 1, commitThresholdSeconds: 4, overlapSeconds: 2)
    }

    private func words(_ s: String) -> [String] { s.split(separator: " ").map(String.init) }

    // Acceptance #1 + #3 + the commit-math criterion in one trace: as a long meeting accumulates,
    // (a) the audio handed to the transcriber per tick never exceeds the bound, while
    // (b) the live transcript is, at EVERY tick, exactly the full meeting in order — which can only
    //     hold if `committedFrames` advances by precisely the committed segments' end time (a gap
    //     would drop a word, an under-advance would repeat one).
    func testActiveWindowStaysBoundedWhileTranscriptStaysComplete() async {
        let cap = IndexedCapture(); let rec = Recorder(); let mc = make(cap, rec)
        mc.start()
        var prev = 0
        for i in 0..<24 {
            cap.emit(1)
            await mc.tick()
            guard case .recording(let live) = mc.state else { return XCTFail("expected recording at tick \(i)") }
            let w = words(live)
            XCTAssertEqual(w, (0...i).map { "w\($0)" }, "tick \(i): the full meeting, in order, no gap or repeat at the seam")
            XCTAssertGreaterThanOrEqual(w.count, prev, "the live transcript only grows")
            prev = w.count
        }
        XCTAssertLessThanOrEqual(Double(rec.maxFrames), mc.maxActiveWindowSeconds,
                                 "per-tick audio never exceeds the bound (constant cost regardless of length)")
        XCTAssertLessThan(rec.maxFrames, 24, "and far below the 24-frame full-meeting cost windowing replaces")
        XCTAssertLessThanOrEqual(Double(mc.bufferedFrames), mc.maxActiveWindowSeconds,
                                 "captured PCM itself is pruned with the committed prefix")
    }

    // Acceptance #2 + #5: the persisted meeting = committed prefix + a final pass over the bounded
    // tail, reconstructing the whole transcript with absolute, monotonic timestamps and no seam.
    func testStopAssemblesCommittedPrefixAndTailWithNoSeam() async {
        let cap = IndexedCapture(); let rec = Recorder(); let store = MemStore(); let mc = make(cap, rec, store)
        mc.start()
        for _ in 0..<12 { cap.emit(1); await mc.tick() }   // several commits happen along the way
        let meeting = await mc.stop()
        XCTAssertEqual(meeting?.segments.map(\.text), (0..<12).map { "w\($0)" },
                       "saved transcript is the complete meeting — not worse than a full pass")
        XCTAssertEqual(meeting?.segments.map(\.startTime), (0..<12).map(Double.init),
                       "timestamps are absolute and monotonic across the committed/tail boundary")
        XCTAssertEqual(mc.reopen(id: "m-1")?.segments.count, 12, "and it round-trips through the store")
    }

    // Acceptance: a blank window (non-speech) never loses the take and never commits.
    func testBlankWindowHoldsTheTakeAndCommitsNothing() async {
        let cap = IndexedCapture(); let rec = Recorder(); let mc = make(cap, rec)
        mc.start()
        for _ in 0..<7 { cap.emit(1); await mc.tick() }    // a committed prefix + a live tail
        guard case .recording(let good) = mc.state else { return XCTFail("expected recording") }
        XCTAssertEqual(words(good), (0..<7).map { "w\($0)" })

        rec.blankAbove = 0                                  // the next window comes back entirely blank
        cap.emit(1); await mc.tick()
        guard case .recording(let afterBlank) = mc.state else { return XCTFail("expected recording") }
        XCTAssertEqual(words(afterBlank), (0..<7).map { "w\($0)" },
                       "a blank pass holds the last good transcript and commits nothing")
    }
}
