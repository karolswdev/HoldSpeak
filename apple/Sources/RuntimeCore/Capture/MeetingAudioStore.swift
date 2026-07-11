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

/// Append-only, crash-recoverable PCM journal for a live Meeting (HS-92-04).
///
/// Audio is written before the capture callback returns. Every five seconds the
/// file is synchronized and a tiny manifest is atomically replaced; recovery
/// trusts only `durableFrames`, so a kill can lose at most one checkpoint window
/// and can never manufacture or duplicate frames. Finalization streams the PCM
/// into a WAV rather than assembling the full take in memory.
public final class MeetingAudioJournal: @unchecked Sendable {
    public struct Recovery: Codable, Equatable, Sendable {
        public var meetingID: String
        public var sampleRate: Int
        public var durableFrames: Int
        public var status: String
        public var updatedAt: Date
    }

    private let lock = NSLock()
    private let meetingID: String
    private let sampleRate: Int
    private let checkpointFrames: Int
    private let pcmURL: URL
    private let manifestURL: URL
    private var handle: FileHandle?
    private var writtenFrames = 0
    private var durableFrames = 0
    private var _lastError: String?

    public var lastError: String? { lock.lock(); defer { lock.unlock() }; return _lastError }

    public init?(meetingID: String, sampleRate: Int = 16_000,
                 checkpointSeconds: Double = 5) {
        guard let dir = MeetingAudioStore.directory() else { return nil }
        self.meetingID = meetingID
        self.sampleRate = sampleRate
        self.checkpointFrames = max(1, Int(Double(sampleRate) * checkpointSeconds))
        self.pcmURL = dir.appendingPathComponent("\(meetingID).pcm16.partial")
        self.manifestURL = dir.appendingPathComponent("\(meetingID).capture.json")
        do {
            FileManager.default.createFile(atPath: pcmURL.path, contents: nil)
            self.handle = try FileHandle(forWritingTo: pcmURL)
            try writeManifest(status: "recording")
        } catch { return nil }
    }

    public func append(_ samples: [Int16]) {
        guard !samples.isEmpty else { return }
        lock.lock(); defer { lock.unlock() }
        guard let handle, _lastError == nil else { return }
        do {
            let little = samples.map { $0.littleEndian }
            let data = little.withUnsafeBytes { Data($0) }
            try handle.write(contentsOf: data)
            writtenFrames += samples.count
            if writtenFrames - durableFrames >= checkpointFrames {
                try checkpointLocked(status: "recording")
            }
        } catch { _lastError = String(describing: error) }
    }

    public func checkpoint() {
        lock.lock(); defer { lock.unlock() }
        do { try checkpointLocked(status: "recording") }
        catch { _lastError = String(describing: error) }
    }

    @discardableResult
    public func finalize() -> URL? {
        lock.lock(); defer { lock.unlock() }
        guard _lastError == nil, let handle,
              let finalURL = MeetingAudioStore.audioURL(for: meetingID) else { return nil }
        do {
            try checkpointLocked(status: "finalizing")
            try handle.close()
            self.handle = nil
            let temp = finalURL.appendingPathExtension("tmp")
            FileManager.default.createFile(atPath: temp.path, contents: nil)
            let output = try FileHandle(forWritingTo: temp)
            try output.write(contentsOf: Self.wavHeader(frames: durableFrames, sampleRate: sampleRate))
            let input = try FileHandle(forReadingFrom: pcmURL)
            var remaining = durableFrames * MemoryLayout<Int16>.size
            while remaining > 0 {
                let data = try input.read(upToCount: min(256 * 1024, remaining)) ?? Data()
                if data.isEmpty { break }
                try output.write(contentsOf: data)
                remaining -= data.count
            }
            try input.close()
            guard remaining == 0 else { throw CocoaError(.fileReadCorruptFile) }
            try output.synchronize()
            try output.close()
            _ = try? FileManager.default.removeItem(at: finalURL)
            try FileManager.default.moveItem(at: temp, to: finalURL)
            try writeManifest(status: "finalized")
            try? FileManager.default.removeItem(at: pcmURL)
            try? FileManager.default.removeItem(at: manifestURL)
            return finalURL
        } catch {
            _lastError = String(describing: error)
            try? writeManifest(status: "recoverable")
            return nil
        }
    }

    public static func recoverable() -> [Recovery] {
        guard let dir = MeetingAudioStore.directory(),
              let urls = try? FileManager.default.contentsOfDirectory(
                at: dir, includingPropertiesForKeys: nil
              ) else { return [] }
        let decoder = JSONDecoder(); decoder.dateDecodingStrategy = .iso8601
        return urls.filter { $0.lastPathComponent.hasSuffix(".capture.json") }
            .compactMap { try? decoder.decode(Recovery.self, from: Data(contentsOf: $0)) }
            .filter { $0.status != "finalized" }
            .sorted { $0.updatedAt > $1.updatedAt }
    }

    /// Finalize exactly the fsynced prefix after relaunch. Bytes beyond the
    /// manifest checkpoint are intentionally ignored (bounded-loss contract).
    @discardableResult
    public static func recover(meetingID: String) -> URL? {
        guard let dir = MeetingAudioStore.directory() else { return nil }
        let manifest = dir.appendingPathComponent("\(meetingID).capture.json")
        let pcm = dir.appendingPathComponent("\(meetingID).pcm16.partial")
        guard let final = MeetingAudioStore.audioURL(for: meetingID),
              let data = try? Data(contentsOf: manifest) else { return nil }
        let decoder = JSONDecoder(); decoder.dateDecodingStrategy = .iso8601
        guard let recovery = try? decoder.decode(Recovery.self, from: data),
              recovery.durableFrames > 0,
              (try? finalizePCM(pcmURL: pcm, finalURL: final,
                                frames: recovery.durableFrames,
                                sampleRate: recovery.sampleRate)) != nil
        else { return nil }
        try? FileManager.default.removeItem(at: pcm)
        try? FileManager.default.removeItem(at: manifest)
        return final
    }

    public static func discard(meetingID: String) {
        guard let dir = MeetingAudioStore.directory() else { return }
        for name in ["\(meetingID).capture.json", "\(meetingID).pcm16.partial",
                     "\(meetingID).wav"] {
            try? FileManager.default.removeItem(at: dir.appendingPathComponent(name))
        }
    }

    private func checkpointLocked(status: String) throws {
        guard let handle else { throw CocoaError(.fileNoSuchFile) }
        try handle.synchronize()
        durableFrames = writtenFrames
        try writeManifest(status: status)
    }

    private func writeManifest(status: String) throws {
        let value = Recovery(meetingID: meetingID, sampleRate: sampleRate,
                             durableFrames: durableFrames, status: status,
                             updatedAt: Date())
        let encoder = JSONEncoder(); encoder.dateEncodingStrategy = .iso8601
        try encoder.encode(value).write(to: manifestURL, options: .atomic)
    }

    private static func wavHeader(frames: Int, sampleRate: Int) -> Data {
        var data = Data()
        func ascii(_ s: String) { data.append(contentsOf: s.utf8) }
        func u16(_ n: UInt16) { var v = n.littleEndian; data.append(Data(bytes: &v, count: 2)) }
        func u32(_ n: UInt32) { var v = n.littleEndian; data.append(Data(bytes: &v, count: 4)) }
        let pcmBytes = UInt32(clamping: frames * MemoryLayout<Int16>.size)
        ascii("RIFF"); u32(36 &+ pcmBytes); ascii("WAVE")
        ascii("fmt "); u32(16); u16(1); u16(1); u32(UInt32(sampleRate))
        u32(UInt32(sampleRate * 2)); u16(2); u16(16)
        ascii("data"); u32(pcmBytes)
        return data
    }

    private static func finalizePCM(pcmURL: URL, finalURL: URL,
                                    frames: Int, sampleRate: Int) throws {
        let temp = finalURL.appendingPathExtension("tmp")
        FileManager.default.createFile(atPath: temp.path, contents: nil)
        let output = try FileHandle(forWritingTo: temp)
        try output.write(contentsOf: wavHeader(frames: frames, sampleRate: sampleRate))
        let input = try FileHandle(forReadingFrom: pcmURL)
        var remaining = frames * MemoryLayout<Int16>.size
        while remaining > 0 {
            let data = try input.read(upToCount: min(256 * 1024, remaining)) ?? Data()
            if data.isEmpty { break }
            try output.write(contentsOf: data)
            remaining -= data.count
        }
        try input.close()
        guard remaining == 0 else { throw CocoaError(.fileReadCorruptFile) }
        try output.synchronize(); try output.close()
        try? FileManager.default.removeItem(at: finalURL)
        try FileManager.default.moveItem(at: temp, to: finalURL)
    }
}
