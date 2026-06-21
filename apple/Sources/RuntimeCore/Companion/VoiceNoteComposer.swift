import Foundation
import Contracts
import Providers

/// Composing a voice-note answer to the coder (HSM-13-02): record on the iPad,
/// transcribe **on-device**, review/edit the recognized text, then deliver it
/// through the HSM-13-01 inject path. The iPad "stands its own ground" here — the
/// capture and transcription are the device's; only the resulting dictation payload
/// leaves, to the paired server.
///
/// The one rule the owner drew a hard line on: **nothing is delivered before an
/// explicit `send()`**. `stopAndTranscribe()` always lands in `.review`; it never
/// auto-sends from recognition. The rich-pipeline transform happens server-side
/// (HSM-13-01) — this stays thin: capture → recognize → review → post.
public enum VoiceNoteState: Sendable, Equatable {
    case idle
    case recording
    case transcribing
    /// Recognized (and freely editable) text, awaiting an explicit send.
    case review(text: String)
    case delivering(text: String)
    case delivered(RemoteDictationResult)
    case failed(stage: VoiceNoteStage, reason: String)
}

/// Which leg failed, so the UI can say something honest ("couldn't reach the
/// desktop" vs "transcription failed") rather than a generic error.
public enum VoiceNoteStage: Sendable, Equatable { case capture, transcribe, deliver }

public final class VoiceNoteComposer: @unchecked Sendable {
    private let capture: IAudioCapture
    private let client: IDesktopClient
    /// Build an on-device transcriber bound to the captured audio. A factory (not a
    /// pre-built `ITranscriber`) because `ITranscriber.transcribe()` reads audio it
    /// was constructed with — the live path hands it the accumulated chunks; the
    /// MLX/Whisper single-executor-thread discipline lives inside that transcriber,
    /// not here (we never spin a second transcription path).
    private let makeTranscriber: @Sendable ([AudioChunk]) -> ITranscriber

    private let lock = NSLock()
    private var chunks: [AudioChunk] = []
    private var _state: VoiceNoteState = .idle

    public init(capture: IAudioCapture,
                client: IDesktopClient,
                makeTranscriber: @escaping @Sendable ([AudioChunk]) -> ITranscriber) {
        self.capture = capture
        self.client = client
        self.makeTranscriber = makeTranscriber
    }

    /// The current composition state. Safe to read from any thread.
    public var state: VoiceNoteState { locked { _state } }

    /// Honest egress for the badge: capture stays on-device; only the dictation
    /// payload travels to the paired server (positioning canon — one badge, no
    /// privacy novel). Mirrors the desktop client's label.
    public var egressLabel: String { client.egressLabel }

    /// Begin capture. Audio accumulates on-device; nothing leaves yet.
    public func startRecording() {
        locked { chunks.removeAll(); _state = .recording }
        do {
            try capture.start { [weak self] chunk in
                guard let self else { return }
                self.locked { self.chunks.append(chunk) }
            }
        } catch {
            setState(.failed(stage: .capture, reason: String(describing: error)))
        }
    }

    /// Stop capture and transcribe the captured audio on-device. Always lands in
    /// `.review` (or `.failed`) — it **never** delivers.
    public func stopAndTranscribe() async {
        guard case .recording = state else { return }
        do { try capture.stop() }
        catch {
            setState(.failed(stage: .capture, reason: String(describing: error)))
            return
        }
        setState(.transcribing)
        let captured = locked { chunks }
        do {
            let segments = try await makeTranscriber(captured).transcribe()
            let text = segments.map(\.text).joined(separator: " ")
                .trimmingCharacters(in: .whitespacesAndNewlines)
            setState(.review(text: text))
        } catch {
            setState(.failed(stage: .transcribe, reason: String(describing: error)))
        }
    }

    /// Edit the recognized text before sending. A no-op outside `.review` (you can
    /// only edit something that's been recognized and is awaiting send).
    public func editText(_ text: String) {
        locked { if case .review = _state { _state = .review(text: text) } }
    }

    /// Deliver the reviewed text through the HSM-13-01 inject path. The user pressed
    /// send — deliver-on-command, never autonomous. A no-op unless in `.review`.
    @discardableResult
    public func send() async -> VoiceNoteState {
        guard case .review(let text) = state else { return state }
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else {
            setState(.failed(stage: .deliver, reason: "nothing to send"))
            return state
        }
        setState(.delivering(text: trimmed))
        do {
            setState(.delivered(try await client.sendRemoteDictation(text: trimmed)))
        } catch {
            setState(.failed(stage: .deliver, reason: String(describing: error)))
        }
        return state
    }

    // MARK: - internals

    private func setState(_ s: VoiceNoteState) { locked { _state = s } }

    private func locked<T>(_ body: () -> T) -> T {
        lock.lock(); defer { lock.unlock() }
        return body()
    }
}
