import XCTest
@testable import RuntimeCore

/// HSM-8-02 — the notebook view-model round-trips PencilKit pages through the store seam:
/// strokes (as serialized `Data`) persist with the meeting and reload intact, multi-page,
/// keyed per meeting. No UIKit — the Core works in serialized drawings.
final class NotebookTests: XCTestCase {

    final class MemNotebookStore: NotebookStore, @unchecked Sendable {
        var blobs: [String: Data] = [:]
        var failSave = false
        func saveNotebook(_ data: Data, meetingID: String) throws {
            if failSave { throw NSError(domain: "db", code: 1) }
            blobs[meetingID] = data
        }
        func loadNotebook(meetingID: String) throws -> Data? { blobs[meetingID] }
    }

    private func page(_ s: String) -> Data { Data(s.utf8) }

    func testPagesRoundTripIntact() throws {
        let store = MemNotebookStore()
        try Notebook(store: store, meetingID: "m1").save(pages: [page("stroke-A"), page("stroke-B")])
        // A fresh notebook over the same store reloads the exact pages.
        let pages = Notebook(store: store, meetingID: "m1").reload()
        XCTAssertEqual(pages, [page("stroke-A"), page("stroke-B")])
    }

    func testEmptyMeetingHasNoNotebook() {
        XCTAssertEqual(Notebook(store: MemNotebookStore(), meetingID: "m1").reload(), [])
    }

    func testNotebooksAreKeyedPerMeeting() throws {
        let store = MemNotebookStore()
        try Notebook(store: store, meetingID: "m1").save(pages: [page("A")])
        try Notebook(store: store, meetingID: "m2").save(pages: [page("B"), page("C")])
        XCTAssertEqual(Notebook(store: store, meetingID: "m1").reload(), [page("A")])
        XCTAssertEqual(Notebook(store: store, meetingID: "m2").reload(), [page("B"), page("C")])
    }

    func testSaveOverwritesThePreviousNotebook() throws {
        let store = MemNotebookStore()
        let nb = Notebook(store: store, meetingID: "m1")
        try nb.save(pages: [page("v1")])
        try nb.save(pages: [page("v2"), page("v2b")])
        XCTAssertEqual(nb.reload(), [page("v2"), page("v2b")])
    }

    func testCorruptBlobReloadsEmptyNeverThrows() {
        let store = MemNotebookStore()
        store.blobs["m1"] = Data("not a notebook".utf8)
        XCTAssertEqual(Notebook(store: store, meetingID: "m1").reload(), [], "a corrupt notebook never blocks reopen")
    }

    func testSaveFailurePropagates() {
        let store = MemNotebookStore(); store.failSave = true
        XCTAssertThrowsError(try Notebook(store: store, meetingID: "m1").save(pages: [page("x")]))
    }
}
