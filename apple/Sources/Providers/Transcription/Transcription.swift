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
/// `<|endoftext|>` — which must never reach the coder (HSM-13-04 real-metal run caught
/// this). Pure + testable so the on-device transcriber can stay a thin adapter.
public enum WhisperText {
    /// Strip Whisper special tokens (`<|...|>`) and collapse the whitespace they leave.
    public static func clean(_ raw: String) -> String {
        let withoutTokens = raw.replacingOccurrences(
            of: "<\\|[^|]*\\|>", with: " ", options: .regularExpression)
        let collapsed = withoutTokens
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
