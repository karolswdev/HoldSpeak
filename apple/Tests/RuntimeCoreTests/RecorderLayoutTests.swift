import XCTest
import CoreGraphics
@testable import RuntimeCore

/// HSM-14-13 deliverable 1 — the recorder's snap/dock math + its persisted layout, host-tested.
final class RecorderLayoutTests: XCTestCase {
    private let viewport = CGSize(width: 800, height: 1200)

    func testDropNearBottomDocksBottom() {
        let d = RecorderSnap.dock(forCenter: CGPoint(x: 400, y: 1180), in: viewport)
        XCTAssertEqual(d, .bottom)
    }

    func testDropNearTopDocksTop() {
        let d = RecorderSnap.dock(forCenter: CGPoint(x: 400, y: 30), in: viewport)
        XCTAssertEqual(d, .top)
    }

    func testDropInTheMiddleFloats() {
        let d = RecorderSnap.dock(forCenter: CGPoint(x: 400, y: 600), in: viewport)
        XCTAssertEqual(d, .floating, "a drop far from any edge stays where the user left it")
    }

    func testNearestEdgeWinsAtTheBoundary() {
        // 120 from the top, 1080 from the bottom — past the 110 margin on both → floating.
        XCTAssertEqual(RecorderSnap.dock(forCenter: CGPoint(x: 400, y: 120), in: viewport), .floating)
        // 100 from the top → within margin, and the top is nearer → top.
        XCTAssertEqual(RecorderSnap.dock(forCenter: CGPoint(x: 400, y: 100), in: viewport), .top)
    }

    func testHomesSitAtTheirEdge() {
        let bottom = RecorderSnap.home(for: .bottom, in: viewport)
        XCTAssertEqual(bottom.x, 400, accuracy: 0.001)
        XCTAssertGreaterThan(bottom.y, 1100, "bottom home hugs the bottom edge")
        let top = RecorderSnap.home(for: .top, in: viewport)
        XCTAssertLessThan(top.y, 100, "top home hugs the top edge")
    }

    func testFloatingHomeUsesTheRememberedCenter() {
        let free = CGPoint(x: 220, y: 540)
        XCTAssertEqual(RecorderSnap.home(for: .floating, in: viewport, free: free), free)
        // ...and falls back to bottom-center when nothing has been remembered yet.
        let fallback = RecorderSnap.home(for: .floating, in: viewport, free: nil)
        XCTAssertEqual(fallback.x, 400, accuracy: 0.001)
    }

    func testClampKeepsTheRecorderOnScreen() {
        let off = RecorderSnap.clamp(CGPoint(x: -50, y: 99999), in: viewport, pad: 40)
        XCTAssertEqual(off.x, 40, accuracy: 0.001)
        XCTAssertEqual(off.y, viewport.height - 40, accuracy: 0.001)
        let inside = CGPoint(x: 400, y: 600)
        XCTAssertEqual(RecorderSnap.clamp(inside, in: viewport), inside, "a center already on-screen is untouched")
    }

    func testLayoutRoundTripsThroughCodable() throws {
        let layout = RecorderLayout(dock: .top, freeCenter: CGPoint(x: 120, y: 340), minimized: true)
        let data = try JSONEncoder().encode(layout)
        let back = try JSONDecoder().decode(RecorderLayout.self, from: data)
        XCTAssertEqual(back, layout, "dock + free center + minimized survive a persistence round-trip")
    }

    func testDefaultLayoutIsBottomDockedAndExpanded() {
        let l = RecorderLayout()
        XCTAssertEqual(l.dock, .bottom)
        XCTAssertFalse(l.minimized)
        XCTAssertNil(l.freeCenter)
    }
}
