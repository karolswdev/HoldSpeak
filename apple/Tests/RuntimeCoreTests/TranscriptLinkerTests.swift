import XCTest
import Contracts
@testable import Providers
@testable import RuntimeCore

/// HSM-8-03 — a note/mark anchors on the transcript moment (a `Segment` start time), not
/// rendered text, so it resolves to the same segment across re-render; bidirectional; and
/// a link made before a transcript exists degrades gracefully.
final class TranscriptLinkerTests: XCTestCase {

    final class MemLinkStore: LinkStore, @unchecked Sendable {
        var blobs: [String: Data] = [:]
        var failSave = false
        func saveLinks(_ data: Data, meetingID: String) throws {
            if failSave { throw NSError(domain: "db", code: 1) }
            blobs[meetingID] = data
        }
        func loadLinks(meetingID: String) throws -> Data? { blobs[meetingID] }
    }

    private func seg(_ s: Double, _ e: Double) -> Segment {
        TranscribedSegment(text: "w", startTime: s, endTime: e).asContractSegment()
    }
    /// Segments: [0] 0–2, [1] 2–5, [2] 5–8.
    private var segments: [Segment] { [(0.0, 2.0), (2.0, 5.0), (5.0, 8.0)].map { seg($0.0, $0.1) } }

    private func linker(_ store: MemLinkStore = MemLinkStore()) -> TranscriptLinker {
        TranscriptLinker(store: store, meetingID: "m1")
    }

    func testResolvesToContainingSegment() {
        XCTAssertEqual(TranscriptLinker.segmentIndex(for: 3.2, in: segments), 1)
        XCTAssertEqual(TranscriptLinker.segmentIndex(for: 6.0, in: segments), 2)
        XCTAssertEqual(TranscriptLinker.segmentIndex(for: 0.5, in: segments), 0)
    }

    func testStableAcrossReRender() throws {
        let store = MemLinkStore()
        try linker(store).linkNote(page: 1, at: 3.2)
        // A fresh linker over the same store + the same segments resolves the same way.
        let l = linker(store)
        let link = l.links()[0]
        XCTAssertEqual(l.resolve(link, in: segments), 1)
        XCTAssertEqual(l.resolve(link, in: segments), 1, "re-render resolves identically")
    }

    func testNearestWhenPastTheEnd() {
        XCTAssertEqual(TranscriptLinker.segmentIndex(for: 100.0, in: segments), 2, "a mark past the end snaps to the nearest")
    }

    func testBidirectionalFromMomentToNotes() throws {
        let l = linker()
        try l.linkNote(page: 0, at: 0.5)   // segment 0
        try l.linkNote(page: 1, at: 3.2)   // segment 1
        try l.markMoment(at: 4.0)          // segment 1
        XCTAssertEqual(l.links(atSegmentIndex: 1, in: segments).map(\.page), [1, nil])
        XCTAssertEqual(l.links(atSegmentIndex: 0, in: segments).map(\.page), [0])
        XCTAssertTrue(l.links(atSegmentIndex: 2, in: segments).isEmpty)
    }

    func testNoTranscriptDegradesGracefully() throws {
        let l = linker()
        try l.markMoment(at: 0.0)          // made before any transcript exists
        XCTAssertEqual(l.links().count, 1)
        XCTAssertNil(l.resolve(l.links()[0], in: []), "no transcript → resolves nil, never crashes")
    }

    func testMarkVsNoteLink() throws {
        let l = linker()
        try l.markMoment(at: 1.0, label: "decision")
        try l.linkNote(page: 2, at: 3.0)
        XCTAssertTrue(l.links()[0].isMark)
        XCTAssertEqual(l.links()[0].label, "decision")
        XCTAssertFalse(l.links()[1].isMark)
        XCTAssertEqual(l.links()[1].page, 2)
    }

    func testPersistsAndReloads() throws {
        let store = MemLinkStore()
        try linker(store).markMoment(at: 3.2, label: "★")
        XCTAssertEqual(linker(store).links(), [TranscriptLink(anchorTime: 3.2, page: nil, label: "★")])
    }

    func testSaveFailurePropagates() {
        let store = MemLinkStore(); store.failSave = true
        XCTAssertThrowsError(try linker(store).markMoment(at: 1.0))
    }
}
