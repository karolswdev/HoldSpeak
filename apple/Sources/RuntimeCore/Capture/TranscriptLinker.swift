import Foundation
import Contracts

/// Transcript linking (HSM-8-03) — a note (or a one-gesture "mark this moment") remembers
/// *when* it was taken, anchored on the **transcript moment**, not on rendered text that
/// re-flows. The anchor is a `Segment` start time (the Phase-0 contract's stable timing),
/// so a link resolves to the same segment across re-render and sync. Bidirectional: from
/// a note you reach its moment, and from a moment you reach the notes taken there.
///
/// A link made before any transcript exists degrades gracefully — it's stored and simply
/// resolves to `nil` until segments arrive (no crash, no dangling pointer).
public struct TranscriptLink: Codable, Equatable, Sendable {
    /// The transcript moment, as a segment start time (seconds). Stable across re-render.
    public var anchorTime: Double
    /// The notebook page taken at this moment; `nil` for a bare "mark this moment".
    public var page: Int?
    /// Optional label for a mark (e.g. "decision", "★").
    public var label: String?

    public init(anchorTime: Double, page: Int? = nil, label: String? = nil) {
        self.anchorTime = anchorTime
        self.page = page
        self.label = label
    }

    /// A mark (no note page) — the raw material HSM-8-06 weaves into the intelligence.
    public var isMark: Bool { page == nil }
}

public final class TranscriptLinker: @unchecked Sendable {
    private let store: LinkStore
    private let meetingID: String
    private let lock = NSLock()
    private var _links: [TranscriptLink]

    public init(store: LinkStore, meetingID: String) {
        self.store = store
        self.meetingID = meetingID
        if let blob = try? store.loadLinks(meetingID: meetingID) ?? nil,
           let decoded = try? JSONDecoder().decode([TranscriptLink].self, from: blob) {
            _links = decoded
        } else {
            _links = []
        }
    }

    public func links() -> [TranscriptLink] { lock.lock(); defer { lock.unlock() }; return _links }

    /// Add a link and persist. The caller passes the active transcript time at the moment
    /// the note/mark was made (0 is fine when no transcript yet — it resolves to nil).
    public func add(_ link: TranscriptLink) throws {
        let snapshot: [TranscriptLink] = { lock.lock(); defer { lock.unlock() }; _links.append(link); return _links }()
        try store.saveLinks(try JSONEncoder().encode(snapshot), meetingID: meetingID)
    }

    /// A one-gesture flag at the current moment, no note attached.
    public func markMoment(at time: Double, label: String? = nil) throws {
        try add(TranscriptLink(anchorTime: time, page: nil, label: label))
    }

    /// Anchor a notebook page to the current moment.
    public func linkNote(page: Int, at time: Double) throws {
        try add(TranscriptLink(anchorTime: time, page: page))
    }

    /// The transcript segment a link points to — the segment whose window contains the
    /// anchor, else the nearest by start time, else `nil` (no transcript = graceful).
    public func resolve(_ link: TranscriptLink, in segments: [Segment]) -> Int? {
        Self.segmentIndex(for: link.anchorTime, in: segments)
    }

    /// Bidirectional: the links anchored within the segment at `index`.
    public func links(atSegmentIndex index: Int, in segments: [Segment]) -> [TranscriptLink] {
        links().filter { Self.segmentIndex(for: $0.anchorTime, in: segments) == index }
    }

    /// Pure resolution — the segment whose `[startTime, endTime]` contains `time`, else the
    /// nearest by `startTime`. `nil` when there are no segments. Stable across re-render
    /// because it keys on the contract's segment timing, never on text offsets.
    public static func segmentIndex(for time: Double, in segments: [Segment]) -> Int? {
        guard !segments.isEmpty else { return nil }
        if let exact = segments.firstIndex(where: { time >= $0.startTime && time <= $0.endTime }) {
            return exact
        }
        return segments.indices.min(by: {
            abs(segments[$0].startTime - time) < abs(segments[$1].startTime - time)
        })
    }
}

/// Where a meeting's transcript links are read + written (a meeting-keyed blob). The app
/// backs this with the app container; the view never touches files directly.
public protocol LinkStore: Sendable {
    func saveLinks(_ data: Data, meetingID: String) throws
    func loadLinks(meetingID: String) throws -> Data?
}
