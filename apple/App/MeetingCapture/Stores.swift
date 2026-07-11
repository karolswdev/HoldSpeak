import Foundation
import WhisperKit

// HSM-14-19 — "The Desk" decomposition: the infrastructure adapters (persistence + on-device
// transcription) lifted verbatim out of MeetingCaptureApp.swift. These back the RuntimeCore seams
// (NotebookStore / MeetingStore / LinkStore / ITranscriber); the views never touch them directly.
// Behaviour unchanged — a move, not a rewrite. Same module, so the protocols/types resolve without imports.

final class InMemoryNotebookStore: NotebookStore, @unchecked Sendable {
    private var blobs: [String: Data] = [:]
    func saveNotebook(_ data: Data, meetingID: String) throws { blobs[meetingID] = data }
    func loadNotebook(meetingID: String) throws -> Data? { blobs[meetingID] }
}

// MARK: - On-device transcription (WhisperKit behind ITranscriber)

final class WhisperKitTranscriber: ITranscriber, @unchecked Sendable {
    private let chunks: [AudioChunk]
    private let model: String
    init(chunks: [AudioChunk], model: String) { self.chunks = chunks; self.model = model }

    /// HSM-18-03 — the user's chosen transcription language as WhisperKit decode options.
    /// The key/normalize logic lives in `WhisperLanguage.configuredCode()` (the ONE
    /// resolver every call site shares — the answer app and the speak harness wire the
    /// same way). "auto"/unknown -> `nil` = per-utterance detection, byte-identical.
    static func decodeOptions() -> DecodingOptions {
        var opts = DecodingOptions()
        opts.language = WhisperLanguage.configuredCode()
        return opts
    }

    // The WhisperKit model is LOADED ONCE and reused. Previously every call constructed a fresh
    // `WhisperKit(...)`, which reloads the CoreML model from disk (seconds) — so live ticks
    // compounded into a frozen-feeling control plane. Cached in a lock-guarded static (WhisperKit
    // isn't Sendable, so it never crosses an isolation boundary — created + used in this method).
    private static let cacheLock = NSLock()
    nonisolated(unsafe) private static var modelCache: [String: WhisperKit] = [:]
    private static func cachedModel(_ k: String) -> WhisperKit? { cacheLock.lock(); defer { cacheLock.unlock() }; return modelCache[k] }
    private static func cacheModel(_ k: String, _ m: WhisperKit) { cacheLock.lock(); modelCache[k] = m; cacheLock.unlock() }

    func transcribe() async throws -> [Segment] {
        let samples = chunks.flatMap { $0.samples }
        guard samples.count >= 16_000 / 4 else { return [] }
        let floats = samples.map { Float($0) / 32768.0 }
        let whisper: WhisperKit
        if let cached = Self.cachedModel(model) {
            whisper = cached
        } else {
            whisper = try await WhisperKit(WhisperKitConfig(model: model))
            Self.cacheModel(model, whisper)
        }
        let results = try await whisper.transcribe(audioArray: floats, decodeOptions: Self.decodeOptions())
        // Preserve WhisperKit's real per-segment timestamps (relative to this window) instead of
        // collapsing to one zero-timestamp segment — the sliding-window commit (HSM-14-12) needs
        // them to know exactly which audio a committed segment covers. `WhisperText.clean` runs
        // per segment; all-non-speech segments drop out, so a blank window still cleans to [].
        let segs = results.flatMap { $0.segments }.compactMap { seg -> Segment? in
            let text = WhisperText.clean(seg.text)
            guard !text.isEmpty else { return nil }
            return TranscribedSegment(text: text, startTime: Double(seg.start), endTime: Double(seg.end)).asContractSegment()
        }
        return segs
    }
}

// MARK: - SQLite-backed MeetingStore (Phase-4 persistence)

/// Adapts the Phase-4 `SQLiteStorage` to the capture loop's `MeetingStore`, most-recent
/// first. Falls back to an in-memory store if the DB can't open, so the app still runs.
final class SQLiteMeetingStore: MeetingStore, @unchecked Sendable {
    private let storage: SQLiteStorage
    init() throws {
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        storage = try SQLiteStorage(path: docs.appendingPathComponent("meetings.sqlite").path)
    }
    func save(_ meeting: Meeting) throws { try storage.saveMeeting(meeting) }
    func save(_ meeting: Meeting, modifiedAt: Date) throws {
        try storage.saveMeeting(meeting, modifiedAt: modifiedAt)
    }
    func delete(id: String, at: Date) throws { try storage.deleteMeeting(id: id, at: at) }
    func load(id: String) throws -> Meeting? { try storage.loadMeeting(id: id) }
    func list() throws -> [Meeting] {
        try storage.allMeetings().sorted { $0.modifiedAt > $1.modifiedAt }.map(\.meeting)
    }
}

// MARK: - Notebook persistence (HSM-8-02) — a meeting-keyed blob behind the seam

/// Backs the `NotebookStore` seam with one JSON blob per meeting in the app container.
/// The view never touches files — it goes through the `Notebook` view-model.
final class FileNotebookStore: NotebookStore, @unchecked Sendable {
    private let dir: URL
    init() {
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        dir = docs.appendingPathComponent("notebooks", isDirectory: true)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
    }
    private func url(_ id: String) -> URL { dir.appendingPathComponent("\(id).json") }
    func saveNotebook(_ data: Data, meetingID: String) throws { try data.write(to: url(meetingID), options: .atomic) }
    func loadNotebook(meetingID: String) throws -> Data? {
        let u = url(meetingID)
        return FileManager.default.fileExists(atPath: u.path) ? try Data(contentsOf: u) : nil
    }
}

/// File-backed `LinkStore` (HSM-8-03) — a meeting-keyed JSON blob of transcript links.
final class FileLinkStore: LinkStore, @unchecked Sendable {
    private let dir: URL
    init() {
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        dir = docs.appendingPathComponent("links", isDirectory: true)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
    }
    private func url(_ id: String) -> URL { dir.appendingPathComponent("\(id).json") }
    func saveLinks(_ data: Data, meetingID: String) throws { try data.write(to: url(meetingID), options: .atomic) }
    func loadLinks(meetingID: String) throws -> Data? {
        let u = url(meetingID)
        return FileManager.default.fileExists(atPath: u.path) ? try Data(contentsOf: u) : nil
    }
}
