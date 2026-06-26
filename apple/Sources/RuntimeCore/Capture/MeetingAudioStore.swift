import Foundation
import Providers

/// Where a meeting's full captured take is saved as a replayable WAV (HSM-14-17 follow-up).
///
/// The diarizer labels each segment with WHO spoke it, but the owner needs to *hear* a segment to
/// judge whether the label is right. So at `stop()` we persist the whole captured PCM16 take as one
/// WAV keyed by the meeting id; the meeting-detail view loads it and plays just one segment's slice
/// (`startTime…endTime`) on tap.
///
/// Layout: `…/Documents/meeting-audio/<meetingID>.wav`. Stable + derivable from the id alone, so the
/// detail view resolves the path without any extra persisted field. Best-effort by design — a write
/// failure must never break `stop()`/persist, and a missing file (older meetings recorded before this
/// landed) simply means no replay control, never a crash.
public struct MeetingAudioStore: Sendable {
    public let sampleRate: Int

    public init(sampleRate: Int = 16_000) {
        self.sampleRate = sampleRate
    }

    /// The directory holding per-meeting WAVs (created on demand). Documents so it survives relaunch.
    public static func directory() -> URL? {
        guard let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first
        else { return nil }
        let dir = docs.appendingPathComponent("meeting-audio", isDirectory: true)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir
    }

    /// The stable WAV path for a meeting id (whether or not the file exists yet).
    public static func audioURL(for meetingID: String) -> URL? {
        directory()?.appendingPathComponent("\(meetingID).wav")
    }

    /// True when a replayable take exists on disk for this meeting.
    public static func hasAudio(for meetingID: String) -> Bool {
        guard let u = audioURL(for: meetingID) else { return false }
        return FileManager.default.fileExists(atPath: u.path)
    }

    /// Write the full captured take for a meeting. Best-effort: returns the URL on success, `nil` on
    /// any failure (the caller must NOT let a write failure break stop/persist).
    @discardableResult
    public func save(_ samples: [Int16], for meetingID: String) -> URL? {
        guard !samples.isEmpty, let url = Self.audioURL(for: meetingID) else { return nil }
        let data = WavWriter.wavData(fromPCM16: samples, sampleRate: sampleRate)
        do { try data.write(to: url, options: .atomic); return url }
        catch { return nil }
    }
}
