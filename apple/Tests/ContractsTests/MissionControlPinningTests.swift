import XCTest
import Contracts

/// HSM-25-02/03 — the belt's live-layer decision kernel, pure and
/// host-hermetic. Mirrors the web workbench's server-side rule
/// (`mission_control_live_layer`, WLA-15-02): `on_story` pins to its
/// story id; ambiguous never guesses a pin (unknown beats guessed);
/// everything else lands off-belt honestly.
final class MissionControlPinningTests: XCTestCase {

    private func session(_ key: String, _ correlation: String,
                          stories: [String] = [],
                          awaiting: Bool = false, stale: Bool = false) -> MCSession {
        MCSession(key: key, agent: "claude", correlation: correlation,
                   stories: stories.map { MCSessionStory(storyId: $0) },
                   awaitingResponse: awaiting, stale: stale, tmux: nil)
    }

    func testOnStoryPinsToItsStory() {
        let (pins, offBelt) = pinMissionControlSessions([
            session("a", "on_story", stories: ["DM-1-02"]),
        ])
        XCTAssertEqual(pins["DM-1-02"]?.map(\.key), ["a"])
        XCTAssertTrue(offBelt.isEmpty)
    }

    func testOnStoryWithMultipleStoriesPinsToEach() {
        let (pins, _) = pinMissionControlSessions([
            session("d", "on_story", stories: ["DM-1-02", "DM-2-01"]),
        ])
        XCTAssertEqual(Set(pins.keys), ["DM-1-02", "DM-2-01"])
    }

    func testAmbiguousNeverGuessesAPin() {
        let (pins, offBelt) = pinMissionControlSessions([
            session("b", "ambiguous", stories: ["X-1", "X-2"]),
        ])
        XCTAssertTrue(pins.isEmpty, "ambiguous must never pin — unknown beats guessed")
        XCTAssertEqual(offBelt.map(\.key), ["b"])
    }

    func testOtherCorrelationsStayOffBelt() {
        let (pins, offBelt) = pinMissionControlSessions([
            session("c", "off_rails"),
            session("e", "idle_on_rails"),
            session("f", "unreadable"),
        ])
        XCTAssertTrue(pins.isEmpty)
        XCTAssertEqual(offBelt.map(\.key), ["c", "e", "f"])
    }

    func testMultipleSessionsCanPinToTheSameStory() {
        let (pins, _) = pinMissionControlSessions([
            session("a", "on_story", stories: ["S-1"]),
            session("d", "on_story", stories: ["S-1"]),
        ])
        XCTAssertEqual(pins["S-1"]?.map(\.key), ["a", "d"])
    }

    func testStaleAndAwaitingFlagsSurviveThePin() {
        let (pins, _) = pinMissionControlSessions([
            session("a", "on_story", stories: ["S-1"], awaiting: true, stale: false),
        ])
        XCTAssertEqual(pins["S-1"]?.first?.awaitingResponse, true)
        XCTAssertEqual(pins["S-1"]?.first?.stale, false)
    }

    func testOnStoryWithNoStoriesFallsOffBelt() {
        // A malformed/degenerate on_story with an empty stories array
        // must not silently vanish — it stays visible off-belt.
        let (pins, offBelt) = pinMissionControlSessions([
            session("g", "on_story", stories: []),
        ])
        XCTAssertTrue(pins.isEmpty)
        XCTAssertEqual(offBelt.map(\.key), ["g"])
    }
}
