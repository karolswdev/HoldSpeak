import Foundation
import Contracts

/// What a transcription engine (WhisperKit) yields for one window/chunk, before
/// mapping to the Phase-0 `Segment` contract. HSM-3-04.
public struct TranscribedSegment: Equatable, Sendable {
    public var text: String
    public var startTime: Double   // seconds since meeting start
    public var endTime: Double

    public init(text: String, startTime: Double, endTime: Double) {
        self.text = text
        self.startTime = startTime
        self.endTime = endTime
    }

    /// Map to the Phase-0 `Segment` — speaker-ready: real timing + a **reserved
    /// speaker slot** (`speakerId` stays nil until diarization assigns identity).
    /// `speaker` is the display label.
    public func asContractSegment(speaker: String = "Speaker 1") -> Segment {
        Segment(text: text, speaker: speaker, speakerId: nil,
                startTime: startTime, endTime: endTime,
                isBookmarked: false, deviceId: nil)
    }
}

/// On-device Whisper model variants (charter §"Local model strategy"). HSM-3-01.
public enum WhisperModel: String, Sendable, CaseIterable {
    case base, small, medium, large
}

/// Cleaning Whisper output into deliverable prose. A WhisperKit segment's raw `text`
/// carries control tokens — `<|startoftranscript|>`, `<|en|>`, `<|0.00|>` timestamps,
/// `<|endoftext|>` (HSM-13-04 real-metal run) — and non-speech markers like
/// `[BLANK_AUDIO]` / `[MUSIC]` / `[INAUDIBLE]` it emits for silence or music (HSM-8-04
/// real-metal run, recording a meeting off a speaker). Neither belongs in a transcript.
/// Pure + testable so the on-device transcriber can stay a thin adapter.
public enum WhisperText {
    /// Strip Whisper special tokens (`<|...|>`) + all-caps bracketed non-speech markers
    /// (`[BLANK_AUDIO]`, `[MUSIC]`, …) and collapse the whitespace they leave. A take
    /// that is entirely non-speech cleans to `""` (the caller then keeps the last good
    /// transcript instead of saving a blank marker).
    public static func clean(_ raw: String) -> String {
        let stripped = raw
            .replacingOccurrences(of: "<\\|[^|]*\\|>", with: " ", options: .regularExpression)
            .replacingOccurrences(of: "\\[[A-Z][A-Z0-9 _]*\\]", with: " ", options: .regularExpression)
        let collapsed = stripped
            .split(whereSeparator: { $0 == " " || $0 == "\n" || $0 == "\t" })
            .joined(separator: " ")
        return collapsed.trimmingCharacters(in: .whitespacesAndNewlines)
    }
}

public enum DeviceClass: Sendable { case iPhone, iPad }

public enum WhisperModelPolicy {
    /// iPhone -> Base, iPad -> Small, per the charter's per-device defaults.
    public static func defaultModel(for device: DeviceClass) -> WhisperModel {
        switch device {
        case .iPhone: return .base
        case .iPad: return .small
        }
    }
}

/// The config a transcriber is built with. `language` is "auto" by default
/// (Whisper's per-utterance detection); resolve it via `normalizedLanguage()`.
/// HSM-3-01/03.
public struct TranscriberConfig: Sendable {
    public var language: String?
    public var model: WhisperModel

    public init(language: String? = "auto", model: WhisperModel) {
        self.language = language
        self.model = model
    }

    /// The Whisper language code, or nil for auto; throws on an unknown value.
    public func normalizedLanguage() throws -> String? {
        try WhisperLanguage.normalize(language)
    }
}
