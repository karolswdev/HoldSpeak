import XCTest
@testable import RuntimeCore

final class LiveIntelCadenceTests: XCTestCase {
    func testTackFiresImmediatelyRegardlessOfCadence() {
        let c = LiveIntelCadence(minSecondsBetweenRuns: 60, minNewSegments: 10)
        // Tack wins even with no new segments and a recent run.
        XCTAssertEqual(c.decide(now: 100, lastRun: 99, newSegmentsSinceLastRun: 0, tackPending: true), .tack)
    }

    func testTackSuppressedWhenTackTriggerOff() {
        let c = LiveIntelCadence(tackTriggerEnabled: false, cadenceEnabled: false)
        XCTAssertNil(c.decide(now: 100, lastRun: nil, newSegmentsSinceLastRun: 99, tackPending: true))
    }

    func testCadenceFiresWhenSegmentsAndTimeFloorsMet() {
        let c = LiveIntelCadence(minSecondsBetweenRuns: 25, minNewSegments: 4)
        XCTAssertEqual(c.decide(now: 130, lastRun: 100, newSegmentsSinceLastRun: 5, tackPending: false), .cadence)
    }

    func testFirstCadenceFiresOnceEnoughSegmentsAccrue() {
        let c = LiveIntelCadence(minNewSegments: 4)
        XCTAssertEqual(c.decide(now: 40, lastRun: nil, newSegmentsSinceLastRun: 4, tackPending: false), .cadence)
        XCTAssertNil(c.decide(now: 40, lastRun: nil, newSegmentsSinceLastRun: 3, tackPending: false))   // not enough yet
    }

    func testCadenceHeldWhenTooSoon() {
        let c = LiveIntelCadence(minSecondsBetweenRuns: 25, minNewSegments: 4)
        // Enough new segments, but only 10s since the last run.
        XCTAssertNil(c.decide(now: 110, lastRun: 100, newSegmentsSinceLastRun: 8, tackPending: false))
    }

    func testCadenceDisabledNeverFiresCadenceButTackStillWorks() {
        let c = LiveIntelCadence(tackTriggerEnabled: true, cadenceEnabled: false)
        XCTAssertNil(c.decide(now: 999, lastRun: nil, newSegmentsSinceLastRun: 100, tackPending: false))
        XCTAssertEqual(c.decide(now: 999, lastRun: nil, newSegmentsSinceLastRun: 100, tackPending: true), .tack)
    }
}
