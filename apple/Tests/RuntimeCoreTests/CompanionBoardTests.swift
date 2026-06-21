import XCTest
import Contracts
@testable import Providers
@testable import RuntimeCore

/// HSM-13-03 — the Companion board view-model. A scriptable fake `IDesktopClient`
/// drives it with no network: targets render, select/dismiss/pin update the desktop's
/// truth and the refreshed board reflects it, and an unreachable desktop degrades to a
/// `.failure` (never a throw on the caller path, never a faked target).
final class CompanionBoardTests: XCTestCase {

    private func target(_ agent: String, _ sid: String, question: String, selected: Bool = false,
                        pinned: Bool = false, stale: Bool = false) -> CompanionTarget {
        CompanionTarget(agent: agent, sessionID: sid, question: question, project: "repo",
                        selected: selected, pinned: pinned, stale: stale, confidence: "high")
    }

    private func desktop(_ targets: [CompanionTarget], reachable: Bool = true) -> CompanionMeetingsTests.FakeDesktop {
        let d = CompanionMeetingsTests.FakeDesktop(reachable: reachable)
        d.board = CompanionBoardState(readyForReply: !targets.isEmpty, blockers: targets.isEmpty ? ["no_agent_waiting"] : [],
                                      awaiting: !targets.isEmpty, targets: targets)
        return d
    }

    func testLoadsWaitingTargets() async {
        let d = desktop([target("claude", "s1", question: "Redis or Postgres?", selected: true),
                         target("codex", "s2", question: "Rename the module?")])
        let result = await CompanionBoard(client: d).load()
        guard case .success(let state) = result else { return XCTFail("expected success") }
        XCTAssertEqual(state.targets.map(\.sessionID), ["s1", "s2"])
        XCTAssertEqual(state.activeTarget?.sessionID, "s1")
        XCTAssertTrue(state.awaiting)
        XCTAssertEqual(state.targets[0].question, "Redis or Postgres?")
    }

    func testSelectMakesTheTargetActive() async {
        let d = desktop([target("claude", "s1", question: "Q1", selected: true),
                         target("codex", "s2", question: "Q2")])
        let board = CompanionBoard(client: d)
        let result = await board.select(target("codex", "s2", question: "Q2"))
        guard case .success(let state) = result else { return XCTFail("expected success") }
        XCTAssertEqual(d.selected.map(\.1), ["s2"], "the select hit the desktop")
        XCTAssertEqual(state.activeTarget?.sessionID, "s2", "the refreshed board reflects the new target")
        XCTAssertFalse(state.targets.first(where: { $0.sessionID == "s1" })!.selected)
    }

    func testPinAndUnpin() async {
        let d = desktop([target("claude", "s1", question: "Q1")])
        let board = CompanionBoard(client: d)
        _ = await board.pin(target("claude", "s1", question: "Q1"), pinned: true)
        XCTAssertEqual(d.pinnedCalls.map(\.2), [true])
        let result = await board.pin(target("claude", "s1", question: "Q1"), pinned: false)
        guard case .success(let state) = result else { return XCTFail("expected success") }
        XCTAssertEqual(d.pinnedCalls.map(\.2), [true, false])
        XCTAssertFalse(state.targets[0].pinned)
    }

    func testDismissRemovesTheTarget() async {
        let d = desktop([target("claude", "s1", question: "Q1"),
                         target("codex", "s2", question: "Q2")])
        let result = await CompanionBoard(client: d).dismiss(target("claude", "s1", question: "Q1"))
        guard case .success(let state) = result else { return XCTFail("expected success") }
        XCTAssertEqual(d.dismissed.map(\.1), ["s1"])
        XCTAssertEqual(state.targets.map(\.sessionID), ["s2"])
    }

    func testEmptyBoardIsHonest_neverManufacturesATarget() async {
        let d = desktop([])
        let result = await CompanionBoard(client: d).load()
        guard case .success(let state) = result else { return XCTFail("expected success") }
        XCTAssertTrue(state.targets.isEmpty)
        XCTAssertFalse(state.awaiting)
        XCTAssertNil(state.activeTarget)
        XCTAssertEqual(state.blockers, ["no_agent_waiting"])
    }

    func testUnreachableDesktopDegradesToFailure() async {
        let d = desktop([target("claude", "s1", question: "Q1")], reachable: false)
        let board = CompanionBoard(client: d)
        if case .success = await board.load() { XCTFail("expected failure on load") }
        if case .success = await board.select(target("claude", "s1", question: "Q1")) { XCTFail("expected failure on select") }
    }

    func testEgressLabelMirrorsTheClient() {
        XCTAssertEqual(CompanionBoard(client: desktop([])).egressLabel, "local + LAN → fake.desk")
    }
}
