import XCTest
import Contracts
@testable import Providers
@testable import RuntimeCore

/// HSM-17-04 — the answer-the-coder flow. Proves the payload assembly (typed +
/// dropped-context into one visible-grounding payload), the select-then-send
/// order against the exact session, the raw approve keystroke, and that a
/// failed select never sends (nothing autonomous, nothing silently lost).
final class CoderAnswerTests: XCTestCase {

    final class RecordingDesktop: IDesktopClient, @unchecked Sendable {
        var calls: [String] = []
        var selectError: Error?
        var sendError: Error?
        var lastText: String?
        var lastTarget: DictationTarget?
        var lastRaw: Bool?

        func handshake() async -> DesktopConnection { .init(reachable: true, runtimeReady: true, detail: "ready") }
        var egressLabel: String { "local + LAN → fake.desk" }
        func listMeetings() async throws -> [MeetingSummary] { [] }
        func runtimeState() async throws -> RuntimeState { RuntimeState(status: "ok") }
        func startMeeting(title: String?) async throws -> RuntimeState { RuntimeState(status: "ok", meetingActive: true) }
        func stopMeeting() async throws -> RuntimeState { RuntimeState(status: "ok") }
        func companionStatus() async throws -> CompanionBoardState { CompanionBoardState() }
        func dismissCompanionTarget(agent: String, sessionID: String) async throws {}
        func pinCompanionTarget(agent: String, sessionID: String, pinned: Bool) async throws {}

        func selectCompanionTarget(agent: String, sessionID: String) async throws {
            if let e = selectError { throw e }
            calls.append("select \(agent)/\(sessionID)")
        }
        func sendRemoteDictation(text: String, target: DictationTarget, raw: Bool) async throws -> RemoteDictationResult {
            if let e = sendError { throw e }
            calls.append("send")
            lastText = text; lastTarget = target; lastRaw = raw
            return RemoteDictationResult(success: true, finalText: text, delivered: true)
        }
    }

    enum TestError: Error { case boom }

    // MARK: compose

    func testComposePlainReplyIsUntouched() {
        XCTAssertEqual(CoderAnswer.compose(reply: "  ship it  "), "ship it")
    }

    func testComposeAttachesGroundingUnderACitedSeparator() {
        let payload = CoderAnswer.compose(
            reply: "Use the decision from the standup.",
            groundingTitle: "Q3 kickoff",
            grounding: "Decision: defer Guilds V1 to Q4."
        )
        XCTAssertEqual(
            payload,
            "Use the decision from the standup.\n\n---\nContext (from Q3 kickoff):\nDecision: defer Guilds V1 to Q4."
        )
    }

    func testComposeGroundingOnlyStillCarriesTheHeader() {
        let payload = CoderAnswer.compose(reply: "   ", groundingTitle: nil, grounding: "raw notes")
        XCTAssertEqual(payload, "Context:\nraw notes")
    }

    func testComposeEmptyGroundingIsDropped() {
        XCTAssertEqual(
            CoderAnswer.compose(reply: "go ahead", groundingTitle: "note", grounding: "  \n "),
            "go ahead"
        )
    }

    // MARK: send

    func testSendSelectsTheExactSessionThenDelivers() async throws {
        let desk = RecordingDesktop()

        let result = try await CoderAnswer.send(desk, agent: "claude", sessionID: "s-42", reply: "yes, and add tests")

        XCTAssertEqual(desk.calls, ["select claude/s-42", "send"])
        XCTAssertEqual(desk.lastText, "yes, and add tests")
        XCTAssertEqual(desk.lastTarget, .agent)
        XCTAssertEqual(desk.lastRaw, false)
        XCTAssertTrue(result.delivered)
    }

    func testSendCarriesGroundingInTheOnePayload() async throws {
        let desk = RecordingDesktop()

        _ = try await CoderAnswer.send(
            desk, agent: "codex", sessionID: "x1",
            reply: "answer from this", groundingTitle: "Pylon incident", grounding: "root cause: cert expiry"
        )

        XCTAssertEqual(desk.lastText, "answer from this\n\n---\nContext (from Pylon incident):\nroot cause: cert expiry")
    }

    func testFailedSelectNeverSends() async {
        let desk = RecordingDesktop()
        desk.selectError = TestError.boom

        do {
            _ = try await CoderAnswer.send(desk, agent: "claude", sessionID: "s1", reply: "hello")
            XCTFail("expected the select failure to throw")
        } catch {
            XCTAssertTrue(desk.calls.isEmpty)
            XCTAssertNil(desk.lastText)  // nothing was delivered
        }
    }

    func testSendFailureSurfaces() async {
        let desk = RecordingDesktop()
        desk.sendError = TestError.boom

        do {
            _ = try await CoderAnswer.send(desk, agent: "claude", sessionID: "s1", reply: "hello")
            XCTFail("expected the send failure to throw")
        } catch {
            XCTAssertEqual(desk.calls, ["select claude/s1"])  // honest partial trail
        }
    }

    // MARK: approve

    func testApproveSendsTheRawDialogKeystroke() async throws {
        let desk = RecordingDesktop()

        _ = try await CoderAnswer.approve(desk, agent: "claude", sessionID: "s-42")

        XCTAssertEqual(desk.calls, ["select claude/s-42", "send"])
        XCTAssertEqual(desk.lastText, "1")
        XCTAssertEqual(desk.lastRaw, true)  // the hub pipeline must not rewrite a keystroke
    }
}
