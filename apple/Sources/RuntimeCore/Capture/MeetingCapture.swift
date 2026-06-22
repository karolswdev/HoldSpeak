import Foundation
import Contracts
import Providers

/// The on-device meeting-capture loop (HSM-8-01) — the spine of the iPad flagship: press
/// Record, watch the transcript appear, stop to persist. It composes the Phase-2 capture,
/// the Phase-3 transcriber, and a meeting store behind seams; the view holds none of this
/// logic. Fully on-device — capture and transcription are the iPad's, nothing leaves.
///
/// Live transcript is **windowed** here: `tick()` re-transcribes the audio captured so
/// far, so the view updates as speech accumulates. A truly streaming transcriber is
/// HSM-3-02; this stays correct (and simple) on a short meeting until then.
public final class MeetingCapture: @unchecked Sendable {
    private let capture: IAudioCapture
    private let makeTranscriber: @Sendable ([AudioChunk]) -> ITranscriber
    private let store: MeetingStore
    private let now: @Sendable () -> Date
    private let makeID: @Sendable () -> String

    private let lock = NSLock()
    private var chunks: [AudioChunk] = []
    private var _state: CaptureState = .idle
    private var startedAt: Date?
    private var meetingID: String?
    private var lastGoodSegments: [Segment] = []   // last non-empty transcript (blank-pass fallback)
    private var _level: Float = 0                   // HSM-14 — smoothed mic amplitude for the live VU

    public init(capture: IAudioCapture,
                store: MeetingStore,
                makeTranscriber: @escaping @Sendable ([AudioChunk]) -> ITranscriber,
                now: @escaping @Sendable () -> Date = { Date() },
                makeID: @escaping @Sendable () -> String = { UUID().uuidString }) {
        self.capture = capture
        self.store = store
        self.makeTranscriber = makeTranscriber
        self.now = now
        self.makeID = makeID
    }

    public var state: CaptureState { locked { _state } }

    /// The id of the recording in progress (assigned at `start`), so a notebook
    /// (HSM-8-02) can bind notes to the meeting before it is persisted at `stop`.
    public var currentID: String? { locked { meetingID } }

    /// Capture stays local; the egress badge says so plainly.
    public var egressLabel: String { "on-device · nothing leaves" }

    /// HSM-14 — the live mic amplitude (0…~1), smoothed, updated on every captured buffer
    /// (~12×/s). Drives the audio-reactive waveform so the control plane visibly responds to
    /// sound the instant it arrives — no transcription round-trip needed.
    public var inputLevel: Float { locked { _level } }
    private func updateLevel(_ chunk: AudioChunk) {
        guard !chunk.samples.isEmpty else { return }
        var sum: Float = 0
        for s in chunk.samples { let f = Float(s) / 32768.0; sum += f * f }
        let rms = (sum / Float(chunk.samples.count)).squareRoot()
        locked { _level = Swift.max(rms, _level * 0.82) }   // fast attack, smooth decay
    }

    /// Begin a recording. Audio accumulates on-device; the live transcript starts empty.
    public func start() {
        locked { chunks.removeAll(); lastGoodSegments = []; _level = 0; startedAt = now(); meetingID = makeID(); _state = .recording(liveTranscript: "") }
        do {
            try capture.start { [weak self] chunk in
                guard let self else { return }
                self.locked { self.chunks.append(chunk) }
                self.updateLevel(chunk)
            }
        } catch {
            setState(.failed(String(describing: error)))
        }
    }

    /// Re-transcribe the audio captured so far and update the live transcript. The view
    /// drives this on a timer while recording; a no-op outside `.recording`. The last
    /// **non-empty** result is remembered, so a later blank pass can't lose the take.
    public func tick() async {
        guard case .recording = state else { return }
        let captured = locked { chunks }
        guard !captured.isEmpty else { return }
        let segments = (try? await makeTranscriber(captured).transcribe()) ?? []
        let text = segments.map(\.text).joined(separator: " ").trimmingCharacters(in: .whitespacesAndNewlines)
        locked {
            if !text.isEmpty { lastGoodSegments = segments }
            if case .recording = _state {
                // Don't flicker back to empty if this window came back blank.
                let shown = text.isEmpty ? lastGoodSegments.map(\.text).joined(separator: " ") : text
                _state = .recording(liveTranscript: shown)
            }
        }
    }

    /// Stop capture, transcribe the full take, persist the meeting, and return it. Lands
    /// in `.saved` (or `.failed`). The persisted meeting reopens intact via `load`.
    @discardableResult
    public func stop() async -> Meeting? {
        guard case .recording = state else { return nil }
        do { try capture.stop() }
        catch { setState(.failed(String(describing: error))); return nil }

        let captured = locked { chunks }
        let started = locked { startedAt } ?? now()
        let id = locked { meetingID } ?? makeID()
        let ended = now()

        // A single pass over a long buffer can come back blank (WhisperKit emits
        // [BLANK_AUDIO] for non-speech); when it does, keep the best live transcript
        // rather than persist nothing (HSM-8-04 real-metal run caught this).
        let finalSegs = (try? await makeTranscriber(captured).transcribe()) ?? []
        let finalText = finalSegs.map(\.text).joined(separator: " ").trimmingCharacters(in: .whitespacesAndNewlines)
        let segments = finalText.isEmpty ? locked { lastGoodSegments } : finalSegs
        let meeting = Meeting(
            id: id, startedAt: started, endedAt: ended,
            duration: ended.timeIntervalSince(started),
            title: nil, segments: segments,
            intelStatus: IntelStatus(state: "none"),
            micLabel: "On-device", remoteLabel: "")
        do {
            try store.save(meeting)
            setState(.saved(meeting))
            return meeting
        } catch {
            setState(.failed("save failed: \(error)"))
            return nil
        }
    }

    /// The recordings already on this device (for the meeting list).
    public func meetings() -> [Meeting] { (try? store.list()) ?? [] }

    /// Reopen a recording by id (the persistence round-trip the list relies on).
    public func reopen(id: String) -> Meeting? { try? store.load(id: id) }

    // MARK: - internals

    private func setState(_ s: CaptureState) { locked { _state = s } }
    private func locked<T>(_ body: () -> T) -> T { lock.lock(); defer { lock.unlock() }; return body() }
}

/// Where the capture loop reads + writes recordings. Narrower than `IStorage` (no
/// artifacts) and adds the list the meeting screen needs; the app adapts the Phase-4
/// `SQLiteStorage` to it.
public protocol MeetingStore: Sendable {
    func save(_ meeting: Meeting) throws
    func list() throws -> [Meeting]
    func load(id: String) throws -> Meeting?
}

/// The capture screen's state — drives Record/Stop and the live transcript view.
public enum CaptureState: Sendable, Equatable {
    case idle
    case recording(liveTranscript: String)
    case saved(Meeting)
    case failed(String)
}
