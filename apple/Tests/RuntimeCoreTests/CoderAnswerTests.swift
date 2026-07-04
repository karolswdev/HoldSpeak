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

// MARK: - HSM-17-05: the AI draft

extension CoderAnswerTests {

    final class ScriptedLLM: ILLMProvider, @unchecked Sendable {
        var prompts: [String] = []
        var response = "Use the event-sourced approach; snapshots hourly."
        var error: Error?
        func complete(prompt: String) async throws -> String {
            if let e = error { throw e }
            prompts.append(prompt)
            return "  \(response)\n"
        }
    }

    func testDraftPromptCarriesRoleQuestionAndTask() {
        let prompt = CoderAnswer.draftPrompt(agent: "claude", question: "Tabs or spaces for the generated files?")

        XCTAssertTrue(prompt.hasPrefix("[ROLE]"))
        XCTAssertTrue(prompt.contains("[QUESTION FROM CLAUDE]\nTabs or spaces for the generated files?"))
        XCTAssertTrue(prompt.hasSuffix("[TASK]\nDraft the user's reply."))
        XCTAssertFalse(prompt.contains("[CONTEXT"))  // no grounding -> no context block
    }

    func testDraftPromptGroundingRidesAsCitedContext() {
        let prompt = CoderAnswer.draftPrompt(
            agent: "codex", question: "Which store do we use?",
            groundingTitle: "ADR 12", grounding: "Decision: SQLite, single writer."
        )

        XCTAssertTrue(prompt.contains("[CONTEXT — ADR 12]\nDecision: SQLite, single writer."))
        XCTAssertTrue(prompt.contains("[QUESTION FROM CODEX]"))
    }

    func testDraftPromptBoundsRunawayGrounding() {
        let prompt = CoderAnswer.draftPrompt(
            agent: "claude", question: "q",
            grounding: String(repeating: "x", count: 20_000)
        )
        XCTAssertLessThan(prompt.count, 8_000)
    }

    func testDraftCallsTheProviderOnceAndTrims() async throws {
        let llm = ScriptedLLM()

        let draft = try await CoderAnswer.draft(llm, agent: "claude", question: "Proceed?")

        XCTAssertEqual(draft, "Use the event-sourced approach; snapshots hourly.")
        XCTAssertEqual(llm.prompts.count, 1)
    }

    func testDraftNeverTouchesTheDesktopClient() async throws {
        // The non-negotiable: drafting composes, only a human approve injects.
        // The draft API cannot reach a client by construction — this pins the
        // provider as its only collaborator.
        let llm = ScriptedLLM()
        let desk = RecordingDesktop()

        _ = try await CoderAnswer.draft(llm, agent: "claude", question: "Send it?")

        XCTAssertTrue(desk.calls.isEmpty)
        XCTAssertNil(desk.lastText)
    }

    func testDraftFailureSurfaces() async {
        let llm = ScriptedLLM()
        llm.error = TestError.boom

        do {
            _ = try await CoderAnswer.draft(llm, agent: "claude", question: "q")
            XCTFail("expected the provider failure to throw")
        } catch { /* honest error, composer keeps the human's text */ }
    }
}
