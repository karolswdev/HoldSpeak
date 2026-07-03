import XCTest
@testable import Contracts

// HSM-21-01 — the one egress grammar. These lock the exact badge words and the
// honest tint split (anything that leaves the device must not wear the local
// treatment) so no surface can drift back to a hand-built posture.
final class EgressScopeTests: XCTestCase {

    func testLabelsAreTheCanonicalGrammar() {
        XCTAssertEqual(EgressScope.local.label, "On device")
        XCTAssertEqual(EgressScope.mixed("your desktop").label, "Local + your desktop")
        XCTAssertEqual(EgressScope.cloud("slack").label, "Cloud · slack")
    }

    func testSymbolsPerPosture() {
        XCTAssertEqual(EgressScope.local.symbolName, "lock.fill")
        XCTAssertEqual(EgressScope.mixed("x").symbolName, "desktopcomputer")
        XCTAssertEqual(EgressScope.cloud("x").symbolName, "arrow.up.forward.app.fill")
    }

    func testTintSplitIsHonest() {
        // The load-bearing rule: mixed and cloud NEVER map to the local tint.
        XCTAssertEqual(EgressScope.local.tintKey, "local")
        XCTAssertEqual(EgressScope.mixed("your desktop").tintKey, "leaves")
        XCTAssertEqual(EgressScope.cloud("slack").tintKey, "leaves")
        XCTAssertFalse(EgressScope.local.leavesDevice)
        XCTAssertTrue(EgressScope.mixed("m").leavesDevice)
        XCTAssertTrue(EgressScope.cloud("c").leavesDevice)
    }
}
