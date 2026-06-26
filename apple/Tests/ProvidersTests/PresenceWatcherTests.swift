import XCTest
@testable import Providers

/// HSM-15-09 — the proactive presence brain. Pure rising-edge + debounce + quiet/mute,
/// driven by a scripted `CompanionBoardState` stream (no network, fully deterministic).
final class PresenceWatcherTests: XCTestCase {

    // A waiting target = not stale + a non-empty question. A non-waiting one drops the question.
    private func waiting(_ agent: String, _ sid: String, _ q: String = "Migrate the schema now?") -> CompanionTarget {
        CompanionTarget(agent: agent, sessionID: sid, question: q, project: "acme/api")
    }
    private func idle(_ agent: String, _ sid: String) -> CompanionTarget {
        CompanionTarget(agent: agent, sessionID: sid, question: nil, project: "acme/api")
    }
    private func state(_ targets: [CompanionTarget]) -> CompanionBoardState {
        CompanionBoardState(awaiting: targets.contains { PresenceWatcher.isWaiting($0) }, targets: targets)
    }

    func testRisingEdgeFiresOnce() {
        var w = PresenceWatcher()
        let t0 = Date()
        // Frame 1: agent idle → no event.
        XCTAssertEqual(w.ingest(state([idle("claude", "s1")]), now: t0), [])
        // Frame 2: agent crosses into waiting → fires once.
        let e = w.ingest(state([waiting("claude", "s1")]), now: t0.addingTimeInterval(1))
        XCTAssertEqual(e.count, 1)
        XCTAssertEqual(e.first?.id, "claude/s1")
        XCTAssertEqual(e.first?.project, "acme/api")
        // Frame 3+4: still waiting → NO re-fire (no spam).
        XCTAssertEqual(w.ingest(state([waiting("claude", "s1")]), now: t0.addingTimeInterval(2)), [])
        XCTAssertEqual(w.ingest(state([waiting("claude", "s1")]), now: t0.addingTimeInterval(3)), [])
    }

    func testNewWaitingSessionIsARisingEdge() {
        var w = PresenceWatcher()
        let t0 = Date()
        XCTAssertEqual(w.ingest(state([waiting("claude", "s1")]), now: t0).count, 1)
        // A brand-new session appears already waiting → it wasn't present, so it's a rising edge.
        let e = w.ingest(state([waiting("claude", "s1"), waiting("codex", "s2")]), now: t0.addingTimeInterval(5))
        XCTAssertEqual(e.map(\.id), ["codex/s2"])
    }

    func testFallThenReRiseFiresAgainPastDebounce() {
        var w = PresenceWatcher(debounce: 10)
        let t0 = Date()
        XCTAssertEqual(w.ingest(state([waiting("claude", "s1")]), now: t0).count, 1)   // rise
        XCTAssertEqual(w.ingest(state([idle("claude", "s1")]), now: t0.addingTimeInterval(2)), [])  // fall
        // Re-rise WITHIN debounce → suppressed (flap protection).
        XCTAssertEqual(w.ingest(state([waiting("claude", "s1")]), now: t0.addingTimeInterval(5)), [])
        XCTAssertEqual(w.ingest(state([idle("claude", "s1")]), now: t0.addingTimeInterval(6)), [])
        // Re-rise PAST debounce → fires again (the agent asked a second time).
        XCTAssertEqual(w.ingest(state([waiting("claude", "s1")]), now: t0.addingTimeInterval(20)).count, 1)
    }

    func testQuietModeSuppressesButStillTracksEdges() {
        var w = PresenceWatcher(quiet: true)
        let t0 = Date()
        // Rises while quiet → nothing surfaces.
        XCTAssertEqual(w.ingest(state([waiting("claude", "s1")]), now: t0), [])
        // Leave quiet; the SAME ongoing wait must NOT replay (no backlog).
        w.quiet = false
        XCTAssertEqual(w.ingest(state([waiting("claude", "s1")]), now: t0.addingTimeInterval(1)), [])
        // A genuinely fresh rising edge after quiet ended DOES fire.
        let e = w.ingest(state([waiting("claude", "s1"), waiting("codex", "s2")]), now: t0.addingTimeInterval(2))
        XCTAssertEqual(e.map(\.id), ["codex/s2"])
    }

    func testPerAgentMuteNeverFires() {
        var w = PresenceWatcher(muted: ["claude/s1"])
        let t0 = Date()
        XCTAssertEqual(w.ingest(state([waiting("claude", "s1"), waiting("codex", "s2")]), now: t0).map(\.id), ["codex/s2"])
    }

    func testStaleOrEmptyQuestionIsNotWaiting() {
        var w = PresenceWatcher()
        let stale = CompanionTarget(agent: "claude", sessionID: "s1", question: "anything?", project: "x", stale: true)
        let blank = CompanionTarget(agent: "codex", sessionID: "s2", question: "   ", project: "x")
        XCTAssertEqual(w.ingest(state([stale, blank]), now: Date()), [])
    }

    func testForgetResetsTheEdgeMemory() {
        var w = PresenceWatcher(debounce: 1000)
        let t0 = Date()
        XCTAssertEqual(w.ingest(state([waiting("claude", "s1")]), now: t0).count, 1)
        // User answered → forget it; a later wait fires fresh despite the long debounce.
        w.forget("claude/s1")
        XCTAssertEqual(w.ingest(state([idle("claude", "s1")]), now: t0.addingTimeInterval(1)), [])
        XCTAssertEqual(w.ingest(state([waiting("claude", "s1")]), now: t0.addingTimeInterval(2)).count, 1)
    }
}
