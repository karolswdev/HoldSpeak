import Foundation
import Contracts
import Providers

/// The on-device meeting-capture loop (HSM-8-01) — the spine of the iPad flagship: press
/// Record, watch the transcript appear, stop to persist. It composes the Phase-2 capture,
/// the Phase-3 transcriber, and a meeting store behind seams; the view holds none of this
/// logic. Fully on-device — capture and transcription are the iPad's, nothing leaves.
///
/// Live transcript is **windowed** here, in **constant time regardless of meeting length**
/// (HSM-14-12). `tick()` re-transcribes only a bounded *active window* — the audio since the
/// last commit — never the whole take. Once that window grows past `commitThresholdSeconds`,
/// its settled front (every segment ending before an `overlapSeconds` guard, so an in-progress
/// sentence is never cut) is frozen into a **committed prefix** and the window advances. The
/// live transcript is always `committed prefix + active tail`: complete, monotonic, and cheap
/// to recompute at minute 40 just as at minute 1. Real per-segment timestamps from the
/// transcriber make the audio↔text boundary exact.
public final class MeetingCapture: @unchecked Sendable {
    private let capture: IAudioCapture
    private let makeTranscriber: @Sendable ([AudioChunk]) -> ITranscriber
    private let store: MeetingStore
    private let now: @Sendable () -> Date
    private let makeID: @Sendable () -> String

    /// HSM-14-17 — optional on-device speaker diarization. When injected (the opt-in setting is ON),
    /// `stop()` runs it over the final segments + the captured audio so each segment is labelled with
    /// who spoke it. When `nil` (OFF), `stop()` is byte-identical to its pre-diarization behaviour.
    /// Takes `(segments, pcm16Audio, sampleRate) -> labelledSegments`; runs on a background context.
    private let diarize: (@Sendable ([Segment], [Int16], Int) -> [Segment])?

    // HSM-14-12 — sliding-window tuning. Defaults are the production values; tests inject small
    // numbers (and a small `sampleRate`) to exercise commits without minutes of synthetic audio.
    private let sampleRate: Int
    private let commitThresholdSeconds: Double
    private let overlapSeconds: Double

    private let lock = NSLock()
    private var chunks: [AudioChunk] = []
    private var _state: CaptureState = .idle
    private var startedAt: Date?
    private var meetingID: String?
    private var lastGoodSegments: [Segment] = []   // last non-empty active-window tail (blank-pass fallback)
    private var _level: Float = 0                   // HSM-14 — smoothed mic amplitude for the live VU
    private var _capturedFrames: Int = 0            // diagnostic: total audio frames the callback delivered
    private var _peakLevel: Float = 0               // diagnostic: max raw rms seen this run (mic-health check)

    // HSM-14-12 — the committed prefix: the already-final transcript (absolute timestamps) and the
    // count of audio frames it represents. The active window is everything past `committedFrames`.
    private var committedSegments: [Segment] = []
    private var committedFrames: Int = 0

    public init(capture: IAudioCapture,
                store: MeetingStore,
                makeTranscriber: @escaping @Sendable ([AudioChunk]) -> ITranscriber,
                now: @escaping @Sendable () -> Date = { Date() },
                makeID: @escaping @Sendable () -> String = { UUID().uuidString },
                diarize: (@Sendable ([Segment], [Int16], Int) -> [Segment])? = nil,
                sampleRate: Int = 16_000,
                // The live active window re-transcribes EVERY tick, so its size is the live-latency
                // budget. 45s made each tick re-run Whisper over up to 45s of audio — seconds of work
                // per tick — so the live transcript fell badly behind the speaker (the final full pass
                // still caught everything). A ~10s window keeps each tick cheap so words appear live;
                // commits fire ~4x more often. ("Constant time" only needs a bound — not a large one.)
                commitThresholdSeconds: Double = 10,
                overlapSeconds: Double = 3) {
        self.capture = capture
        self.store = store
        self.makeTranscriber = makeTranscriber
        self.now = now
        self.makeID = makeID
        self.diarize = diarize
        self.sampleRate = sampleRate
        self.commitThresholdSeconds = commitThresholdSeconds
        self.overlapSeconds = overlapSeconds
    }

    /// HSM-14-12 invariant: the audio window handed to the transcriber on any tick never exceeds
    /// this many seconds — a commit fires at `commitThresholdSeconds`, and after it the window is
    /// reset to the `overlapSeconds` guard, so it can only grow back toward this ceiling. Per-tick
    /// transcription cost is therefore constant regardless of meeting length.
    public var maxActiveWindowSeconds: Double { commitThresholdSeconds + overlapSeconds }

    public var state: CaptureState { locked { _state } }

    /// The id of the recording in progress (assigned at `start`), so a notebook
    /// (HSM-8-02) can bind notes to the meeting before it is persisted at `stop`.
    public var currentID: String? { locked { meetingID } }

    /// Capture stays local; the egress badge says so plainly.
    public var egressLabel: String { "on device" }

    /// HSM-14 — the live mic amplitude (0…~1), smoothed, updated on every captured buffer
    /// (~12×/s). Drives the audio-reactive waveform so the control plane visibly responds to
    /// sound the instant it arrives — no transcription round-trip needed.
    public var inputLevel: Float { locked { _level } }
    /// Diagnostics for the device mic-health readout: total frames the callback delivered, and the
    /// loudest raw RMS seen this run. `capturedFrames == 0` ⇒ no audio is reaching us at all.
    public var capturedFrames: Int { locked { _capturedFrames } }
    public var peakLevel: Float { locked { _peakLevel } }
    private func updateLevel(_ chunk: AudioChunk) {
        guard !chunk.samples.isEmpty else { return }
        var sum: Float = 0
        for s in chunk.samples { let f = Float(s) / 32768.0; sum += f * f }
        let rms = (sum / Float(chunk.samples.count)).squareRoot()
        // Speech RMS is small (~0.01–0.08); without gain the meter barely twitches. Lift it into a
        // usable range, then instant-attack / fast-decay so the widget visibly tracks your voice.
        let gained = Swift.min(1, rms * 4.5)
        locked {
            _level = Swift.max(gained, _level * 0.74)
            _capturedFrames += chunk.samples.count
            if rms > _peakLevel { _peakLevel = rms }
        }
    }

    /// Begin a recording. Audio accumulates on-device; the live transcript starts empty.
    public func start() {
        locked { chunks.removeAll(); lastGoodSegments = []; committedSegments = []; committedFrames = 0; _level = 0; _capturedFrames = 0; _peakLevel = 0; startedAt = now(); meetingID = makeID(); _state = .recording(liveTranscript: "") }
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

    /// Re-transcribe only the bounded **active window** (HSM-14-12) and update the live
    /// transcript to `committed prefix + active tail`. The view drives this on a timer while
    /// recording; a no-op outside `.recording`. Two invariants the legacy take relied on are
    /// kept: a blank window never loses the take (the last good tail is held), and the live
    /// transcript only grows. The window's settled front is committed once it passes
    /// `commitThresholdSeconds`, so the per-tick cost stays constant on a long meeting.
    public func tick() async {
        guard case .recording = state else { return }
        let (captured, fromFrame) = locked { (chunks, committedFrames) }
        guard !captured.isEmpty else { return }
        let window = Self.windowChunks(captured, fromFrame: fromFrame)
        guard !window.chunks.isEmpty else { return }
        let windowSegs = (try? await makeTranscriber(window.chunks).transcribe()) ?? []
        locked {
            guard case .recording = _state else { return }
            var tail: [Segment]
            if windowSegs.isEmpty {
                tail = lastGoodSegments                       // blank window → hold the last good tail, never commit
            } else {
                tail = windowSegs
                let windowDuration = Double(window.frames) / Double(sampleRate)
                if windowDuration > commitThresholdSeconds {
                    let cutoff = windowDuration - overlapSeconds   // keep the in-progress sentence in the tail
                    let commitCount = windowSegs.prefix { $0.endTime < cutoff }.count
                    if commitCount > 0 {
                        let base = Double(committedFrames) / Double(sampleRate)
                        committedSegments.append(contentsOf: windowSegs[..<commitCount].map { Self.shifted($0, by: base) })
                        committedFrames += Int((windowSegs[commitCount - 1].endTime * Double(sampleRate)).rounded())
                        tail = Array(windowSegs[commitCount...])
                    }
                }
                lastGoodSegments = tail
            }
            let text = (committedSegments + tail).map(\.text).joined(separator: " ")
                .trimmingCharacters(in: .whitespacesAndNewlines)
            _state = .recording(liveTranscript: text)
        }
    }

    /// Stop capture, transcribe the full take, persist the meeting, and return it. Lands
    /// in `.saved` (or `.failed`). The persisted meeting reopens intact via `load`.
    @discardableResult
    public func stop() async -> Meeting? {
        guard case .recording = state else { return nil }
        do { try capture.stop() }
        catch { setState(.failed(String(describing: error))); return nil }

        let (captured, prefix, fromFrame, lastGood) =
            locked { (chunks, committedSegments, committedFrames, lastGoodSegments) }
        let started = locked { startedAt } ?? now()
        let id = locked { meetingID } ?? makeID()
        let ended = now()

        // The persisted transcript is never worse than the old full-pass result (HSM-14-12).
        // Short meeting (nothing committed): the legacy single authoritative pass with a
        // blank-pass fallback (a buffer of non-speech comes back blank — keep the last good
        // transcript rather than persist nothing; HSM-8-04 caught this). Long meeting: the
        // frozen committed prefix + one final pass over the bounded tail, so a 40-minute take
        // costs the same to finish as a 1-minute one.
        let segments: [Segment]
        if prefix.isEmpty {
            let finalSegs = (try? await makeTranscriber(captured).transcribe()) ?? []
            let finalText = finalSegs.map(\.text).joined(separator: " ").trimmingCharacters(in: .whitespacesAndNewlines)
            segments = finalText.isEmpty ? lastGood : finalSegs
        } else {
            let window = Self.windowChunks(captured, fromFrame: fromFrame)
            let tailSegs = (try? await makeTranscriber(window.chunks).transcribe()) ?? []
            let base = Double(fromFrame) / Double(sampleRate)
            let raw = tailSegs.isEmpty ? lastGood : tailSegs
            segments = prefix + raw.map { Self.shifted($0, by: base) }
        }

        // HSM-14-17 — on-device speaker diarization (opt-in). With the diarizer injected, label the
        // final segments by who spoke each, over the full captured take's PCM16. Off the main thread
        // (model inference); when no diarizer is injected this whole block is skipped (byte-identical).
        let pcm = captured.flatMap { $0.samples }
        var labelled = segments
        if let diarize, !segments.isEmpty {
            let sr = sampleRate
            labelled = await Task.detached(priority: .userInitiated) {
                diarize(segments, pcm, sr)
            }.value
        }

        let meeting = Meeting(
            id: id, startedAt: started, endedAt: ended,
            duration: ended.timeIntervalSince(started),
            title: nil, segments: labelled,
            intelStatus: IntelStatus(state: "none"),
            micLabel: "On-device", remoteLabel: "")

        // Persist the full captured take as a replayable WAV keyed by the meeting id, so the detail
        // view can play back any one segment to judge its speaker label. Best-effort: a write failure
        // here must never break stop/persist, so this is fire-and-forget with no error propagation.
        MeetingAudioStore(sampleRate: sampleRate).save(pcm, for: id)

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

    /// The active window (HSM-14-12): the chunks carrying audio from frame `fromFrame` onward.
    /// Frame-accurate — a chunk straddling the boundary is sliced so the window starts exactly at
    /// the committed frame (commit advances by a segment end time × sample rate, which need not
    /// land on a chunk boundary). `fromFrame == 0` returns the chunks untouched (no copy), which
    /// keeps the short-meeting path byte-for-byte the pre-HSM-14-12 behavior.
    static func windowChunks(_ all: [AudioChunk], fromFrame start: Int) -> (chunks: [AudioChunk], frames: Int) {
        guard start > 0 else { return (all, all.reduce(0) { $0 + $1.frameCount }) }
        var consumed = 0
        var out: [AudioChunk] = []
        for c in all {
            let end = consumed + c.frameCount
            if end <= start { consumed = end; continue }      // fully committed — drop it
            if consumed >= start {
                out.append(c)                                  // wholly inside the window
            } else {
                let off = start - consumed                     // boundary chunk — keep its tail
                out.append(AudioChunk(samples: Array(c.samples[off...]), sequence: c.sequence))
            }
            consumed = end
        }
        return (out, out.reduce(0) { $0 + $1.frameCount })
    }

    /// A copy of `s` with its window-relative timestamps shifted to absolute meeting time.
    static func shifted(_ s: Segment, by base: Double) -> Segment {
        Segment(text: s.text, speaker: s.speaker, speakerId: s.speakerId,
                startTime: s.startTime + base, endTime: s.endTime + base,
                isBookmarked: s.isBookmarked, deviceId: s.deviceId)
    }
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
