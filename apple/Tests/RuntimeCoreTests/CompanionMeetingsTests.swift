import XCTest
import Contracts
@testable import Providers
@testable import RuntimeCore

/// HSM-12-02 — meetings remote control at the Runtime-Core layer. A scriptable fake
/// `IDesktopClient` drives the view-model with no network; proves list/start/stop/
/// live-state flow AND that an unreachable desktop degrades to a `.failure` result
/// (never a throw on the caller path).
final class CompanionMeetingsTests: XCTestCase {

    final class FakeDesktop: IDesktopClient, @unchecked Sendable {
        struct Down: Error {}
        var meetings: [MeetingSummary]
        var state: RuntimeState
        var reachable: Bool
        var started: [String?] = []
        var stopped = 0
        var remoteSent: [String] = []
        init(meetings: [MeetingSummary] = [], state: RuntimeState = RuntimeState(status: "ok"), reachable: Bool = true) {
            self.meetings = meetings; self.state = state; self.reachable = reachable
        }
        func handshake() async -> DesktopConnection { .init(reachable: reachable, runtimeReady: reachable, detail: "") }
        var egressLabel: String { "local + LAN → fake.desk" }
        func listMeetings() async throws -> [MeetingSummary] { if !reachable { throw Down() }; return meetings }
        func runtimeState() async throws -> RuntimeState { if !reachable { throw Down() }; return state }
        func startMeeting(title: String?) async throws -> RuntimeState {
            if !reachable { throw Down() }
            started.append(title); state = RuntimeState(status: "ok", meetingActive: true, meetingId: "m-new"); return state
        }
        func stopMeeting() async throws -> RuntimeState {
            if !reachable { throw Down() }
            stopped += 1; state = RuntimeState(status: "ok", meetingActive: false); return state
        }
        func sendRemoteDictation(text: String) async throws -> RemoteDictationResult {
            if !reachable { throw Down() }
            remoteSent.append(text)
            return RemoteDictationResult(success: true, finalText: text, delivered: true)
        }
    }

    func testListsMeetings() async {
        let fake = FakeDesktop(meetings: [MeetingSummary(id: "m1", title: "Arch review"),
                                          MeetingSummary(id: "m2", title: "Standup")])
        let result = await CompanionMeetings(client: fake).meetings()
        guard case .success(let m) = result else { return XCTFail("expected success") }
        XCTAssertEqual(m.map(\.id), ["m1", "m2"])
    }

    func testStartReflectsLiveState() async {
        let fake = FakeDesktop()
        let result = await CompanionMeetings(client: fake).start(title: "Kickoff")
        guard case .success(let s) = result else { return XCTFail("expected success") }
        XCTAssertTrue(s.meetingActive)
        XCTAssertEqual(s.meetingId, "m-new")
        XCTAssertEqual(fake.started, ["Kickoff"])
    }

    func testStopReflectsIdle() async {
        let fake = FakeDesktop(state: RuntimeState(status: "ok", meetingActive: true, meetingId: "m1"))
        let result = await CompanionMeetings(client: fake).stop()
        guard case .success(let s) = result else { return XCTFail("expected success") }
        XCTAssertFalse(s.meetingActive)
        XCTAssertEqual(fake.stopped, 1)
    }

    /// The load-bearing graceful-degradation guarantee: an unreachable desktop is a
    /// `.failure` result, NOT a thrown error on the caller path.
    func testUnreachableDegradesToFailureResult() async {
        let vm = CompanionMeetings(client: FakeDesktop(reachable: false))
        if case .success = await vm.meetings() { XCTFail("expected failure when unreachable") }
        if case .success = await vm.start() { XCTFail("expected failure when unreachable") }
        if case .success = await vm.liveState() { XCTFail("expected failure when unreachable") }
        // No assertion needed beyond "didn't throw" — reaching here proves it.
    }
}
