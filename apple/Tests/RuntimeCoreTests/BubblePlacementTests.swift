import XCTest
import CoreGraphics
@testable import RuntimeCore

/// HSM-14-13 deliverable 2 — the free-place-vs-tack drop decision, host-tested.
final class BubblePlacementTests: XCTestCase {
    private let pinFloor: CGFloat = 200
    private let tackZone = CGRect(x: 280, y: 900, width: 240, height: 56)   // bottom-center target

    func testDropOnTackZoneTacks() {
        XCTAssertEqual(BubblePlacement.decide(at: CGPoint(x: 400, y: 920), pinFloor: pinFloor, tackZone: tackZone), .tack)
    }

    func testDropBelowTheStreamIsLoose() {
        // Below pinFloor, outside the tack zone → just placed, no marked moment.
        XCTAssertEqual(BubblePlacement.decide(at: CGPoint(x: 120, y: 600), pinFloor: pinFloor, tackZone: tackZone), .loose)
    }

    func testDropBackInTheStreamSnapsBack() {
        XCTAssertEqual(BubblePlacement.decide(at: CGPoint(x: 200, y: 80), pinFloor: pinFloor, tackZone: tackZone), .snapBack)
    }

    func testTackZoneWinsEvenAboveThePinFloor() {
        // A tack zone could sit anywhere; a drop inside it tacks regardless of the floor.
        let highZone = CGRect(x: 280, y: 40, width: 240, height: 56)
        XCTAssertEqual(BubblePlacement.decide(at: CGPoint(x: 400, y: 60), pinFloor: pinFloor, tackZone: highZone), .tack)
    }

    func testPlainPlacementIsTheDefaultBelowTheFold() {
        // The whole point of deliverable 2: most of the surface is free placement, not tacking.
        for x in stride(from: 40.0, through: 760.0, by: 120) {
            let drop = BubblePlacement.decide(at: CGPoint(x: x, y: 500), pinFloor: pinFloor, tackZone: tackZone)
            XCTAssertEqual(drop, .loose, "a plain drop at x=\(x) below the stream is loose, not tacked")
        }
    }
}
