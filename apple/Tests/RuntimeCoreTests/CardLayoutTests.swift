import XCTest
import CoreGraphics
@testable import RuntimeCore

/// HSM-14-13 deliverables 3–4 — card resize clamp + the tidy grid, host-tested.
final class CardLayoutTests: XCTestCase {
    private let viewport = CGSize(width: 800, height: 1200)
    private let pinFloor: CGFloat = 200

    func testClampWidthHoldsTheReadableRange() {
        XCTAssertEqual(CardSize.clampWidth(40), CardSize.minWidth, "too-narrow clamps up")
        XCTAssertEqual(CardSize.clampWidth(9999), CardSize.maxWidth, "too-wide clamps down")
        XCTAssertEqual(CardSize.clampWidth(200), 200, accuracy: 0.001, "an in-range width is untouched")
    }

    func testTidyEmptyIsEmpty() {
        XCTAssertTrue(WorkspaceTidy.layout(count: 0, in: viewport, pinFloor: pinFloor).isEmpty)
    }

    func testTidyPlacesEveryCardBelowTheStreamAndOnScreen() {
        let pts = WorkspaceTidy.layout(count: 7, in: viewport, pinFloor: pinFloor)
        XCTAssertEqual(pts.count, 7)
        for p in pts {
            XCTAssertGreaterThan(p.y, pinFloor, "every tidied card sits below the streaming strip")
            XCTAssertGreaterThanOrEqual(p.x, 0)
            XCTAssertLessThanOrEqual(p.x, viewport.width)
        }
    }

    func testTidyFlowsIntoRows() {
        // 174-wide cards + 16 gap in 800 wide → 4 columns; card 5 starts a second, lower row.
        let pts = WorkspaceTidy.layout(count: 6, in: viewport, pinFloor: pinFloor)
        XCTAssertEqual(pts[0].y, pts[3].y, accuracy: 0.001, "first four share a row")
        XCTAssertGreaterThan(pts[4].y, pts[0].y, "the fifth card wraps to a lower row")
    }

    func testTidyCentersEachRow() {
        // A single card is centered horizontally.
        let one = WorkspaceTidy.layout(count: 1, in: viewport, pinFloor: pinFloor)
        XCTAssertEqual(one[0].x, viewport.width / 2, accuracy: 0.5, "one card centers on the surface")
    }
}
