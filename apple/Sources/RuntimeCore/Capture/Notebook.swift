import Foundation

/// The handwritten-notes notebook at the Runtime-Core layer (HSM-8-02). The iPad's
/// differentiator — PencilKit ink that lives alongside the live transcript and persists
/// with the meeting. The Core stays UIKit-free: a page is the **serialized drawing**
/// (`PKDrawing.dataRepresentation()` is `Data`), so this layer round-trips `[Data]`
/// through a store seam and the view owns the actual canvas.
///
/// Persistence goes through `NotebookStore` (a meeting-keyed blob), never direct file
/// access from the view — the acceptance's hard rule.
public final class Notebook: @unchecked Sendable {
    private let store: NotebookStore
    private let meetingID: String

    public init(store: NotebookStore, meetingID: String) {
        self.store = store
        self.meetingID = meetingID
    }

    /// Persist the notebook's pages (one serialized `PKDrawing` per page) with the
    /// meeting. Encoded as a single versioned blob so multi-page round-trips intact.
    public func save(pages: [Data]) throws {
        let blob = try JSONEncoder().encode(NotebookPages(pages: pages))
        try store.saveNotebook(blob, meetingID: meetingID)
    }

    /// Reload the saved pages, or `[]` when this meeting has no notebook yet. A corrupt
    /// blob decodes to `[]` rather than throwing — a meeting's notes never block reopen.
    public func reload() -> [Data] {
        guard let blob = try? store.loadNotebook(meetingID: meetingID) ?? nil else { return [] }
        return (try? JSONDecoder().decode(NotebookPages.self, from: blob))?.pages ?? []
    }
}

/// Where a meeting's notebook blob is read + written. The app backs this with the
/// Phase-4 store / app container; the view-model + view never touch files directly.
public protocol NotebookStore: Sendable {
    func saveNotebook(_ data: Data, meetingID: String) throws
    func loadNotebook(meetingID: String) throws -> Data?
}

/// The on-disk shape of a notebook — a list of serialized PencilKit pages. Versioned so
/// the persistence model (PKDrawing blob today) can evolve without breaking old notes.
public struct NotebookPages: Codable, Equatable, Sendable {
    public var version: Int
    public var pages: [Data]

    public init(pages: [Data], version: Int = 1) {
        self.version = version
        self.pages = pages
    }
}
