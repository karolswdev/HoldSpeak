import XCTest
import Contracts
@testable import Providers
@testable import RuntimeCore

/// HSM-12-03 — the unified Companion shell view-model. Composes the desktop seam
/// (HSM-12-01/02) with the iPad's own on-device runtime summary, and proves the
/// "not a dumb terminal" principle structurally: the device is **always present**,
/// and an unreachable desktop is a calm `localOnly` mode, never a blocked app.
final class CompanionShellTests: XCTestCase {

    private let localSummary = LocalRuntimeSummary(
        ready: true,
        capabilities: ["On-device capture", "Whisper transcription", "Local inference"],
        meetings: [MeetingSummary(id: "local-1", title: "Standup (on-device)")]
    )

    private func shell(_ desktop: IDesktopClient) -> CompanionShell {
        let summary = localSummary   // copy the value so the @Sendable closure captures no self
        return CompanionShell(link: CompanionLink(client: desktop),
                              meetings: CompanionMeetings(client: desktop),
                              localProvider: { summary })
    }

    func testConnectedShowsBothFaces() async {
        let d = CompanionMeetingsTests.FakeDesktop(
            meetings: [MeetingSummary(id: "m1", title: "Arch review"),
                       MeetingSummary(id: "m2", title: "Standup")],
            reachable: true)
        let state = await shell(d).load()
        XCTAssertEqual(state.mode, .connected)
        XCTAssertTrue(state.serverReachable)
        XCTAssertEqual(state.serverMeetings.map(\.id), ["m1", "m2"])
        // The device is a first-class peer, not hidden when paired.
        XCTAssertTrue(state.local.ready)
        XCTAssertEqual(state.local.meetings.map(\.id), ["local-1"])
        XCTAssertFalse(state.local.capabilities.isEmpty)
    }

    func testUnreachableIsLocalOnlyButDeviceStandsItsGround() async {
        let d = CompanionMeetingsTests.FakeDesktop(reachable: false)
        let state = await shell(d).load()
        XCTAssertEqual(state.mode, .localOnly)
        XCTAssertFalse(state.serverReachable)
        XCTAssertFalse(state.connection.reachable)
        XCTAssertTrue(state.serverMeetings.isEmpty)
        // The on-device runtime is fully present even with the desktop down.
        XCTAssertTrue(state.local.ready)
        XCTAssertEqual(state.local.capabilities.count, 3)
        XCTAssertEqual(state.local.meetings.map(\.id), ["local-1"])
    }

    func testReachableButMeetingsFailDegradesToLocalOnly() async {
        let state = await shell(ReachableBrokenDesktop()).load()
        XCTAssertEqual(state.mode, .localOnly, "a reachable handshake whose meetings fail is honestly localOnly")
        XCTAssertFalse(state.serverReachable)
        XCTAssertTrue(state.serverMeetings.isEmpty)
        XCTAssertTrue(state.local.ready)   // device still stands
    }

    func testEgressMirrorsTheClient() {
        XCTAssertEqual(shell(CompanionMeetingsTests.FakeDesktop()).egressLabel, "local + LAN → fake.desk")
    }

    // A desktop whose health is fine but whose meetings call throws — the shell must
    // degrade to localOnly rather than render a half-empty server.
    private final class ReachableBrokenDesktop: IDesktopClient, @unchecked Sendable {
        struct Boom: Error {}
        func handshake() async -> DesktopConnection { .init(reachable: true, runtimeReady: true, detail: "ready") }
        var egressLabel: String { "local + LAN → broken.desk" }
        func listMeetings() async throws -> [MeetingSummary] { throw Boom() }
        func runtimeState() async throws -> RuntimeState { throw Boom() }
        func startMeeting(title: String?) async throws -> RuntimeState { throw Boom() }
        func stopMeeting() async throws -> RuntimeState { throw Boom() }
        func sendRemoteDictation(text: String, target: DictationTarget) async throws -> RemoteDictationResult { throw Boom() }
        func companionStatus() async throws -> CompanionBoardState { throw Boom() }
        func selectCompanionTarget(agent: String, sessionID: String) async throws { throw Boom() }
        func dismissCompanionTarget(agent: String, sessionID: String) async throws { throw Boom() }
        func pinCompanionTarget(agent: String, sessionID: String, pinned: Bool) async throws { throw Boom() }
    }
}
