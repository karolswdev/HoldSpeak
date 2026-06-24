import Foundation

// HSM-15-09 — the proactive layer. Dictation is push (you → agent); presence is the
// pull (agent → you). This is the pure brain of it: feed it successive
// `CompanionBoardState` snapshots (from polling `companionStatus()`) and it emits a
// "newly waiting" event ONCE per rising edge — the instant a session crosses into
// awaiting-on-you. No view, no timer, no network here, so it unit-tests with a scripted
// status stream. Honest + non-autonomous: it only ever *surfaces* a transition; it
// never answers for you, and quiet-mode / per-agent mute suppress the surfacing.

/// One agent transition the watcher decided is worth surfacing — a session that just
/// crossed from "not waiting" to "waiting on you" (a rising edge), already past the
/// quiet-mode + mute gates.
public struct PresenceEvent: Sendable, Equatable, Identifiable {
    public var agent: String           // "claude" / "codex"
    public var sessionID: String
    public var question: String?       // the ask — surfaced as a tight quote, never prose
    public var project: String?        // repo, for telling sessions apart
    public var at: Date                // when the rising edge was detected

    public init(agent: String, sessionID: String, question: String? = nil,
                project: String? = nil, at: Date = Date()) {
        self.agent = agent; self.sessionID = sessionID
        self.question = question; self.project = project; self.at = at
    }

    /// Stable across the same session (so a re-fire of the *same* wait dedupes cleanly).
    public var id: String { "\(agent)/\(sessionID)" }

    /// The target this event would answer — so the nudge's "Answer" reuses the desk's spine.
    public var target: CompanionTarget {
        CompanionTarget(agent: agent, sessionID: sessionID, question: question, project: project, selected: true)
    }
}

/// The pure rising-edge + debounce + quiet/mute brain. Drive it by calling `ingest`
/// with each fresh `companionStatus()` snapshot; it returns the events to surface for
/// THIS snapshot (usually 0, occasionally 1+). Value-semantic and Sendable — the caller
/// holds one instance and mutates it on its own actor.
///
/// Rules:
///  - **Rising edge:** a session that is "waiting" now and was NOT waiting in the last
///    snapshot fires once. A session that stays waiting across snapshots does NOT re-fire
///    (no repeat-spam). A brand-new waiting session appearing is, by definition, a rising
///    edge (it wasn't present, so it wasn't waiting).
///  - **Fall + re-rise:** if a session stops waiting and later waits again, that's a NEW
///    rising edge and fires again (the agent asked a second question).
///  - **Debounce:** a session that just fired won't re-fire within `debounce` even if it
///    momentarily drops and re-rises (flap protection across poll jitter).
///  - **Quiet mode:** while `quiet`, nothing fires (focus-safe); transitions are still
///    tracked so leaving quiet-mode doesn't replay a backlog — only fresh rising edges
///    after quiet ends surface.
///  - **Per-agent mute:** a muted `id` ("agent/session") never fires.
public struct PresenceWatcher: Sendable {
    /// Suppress all surfacing (focus / "do not disturb"). Transitions are still tracked.
    public var quiet: Bool
    /// Per-target mutes, keyed by `PresenceEvent.id` ("agent/sessionID").
    public var muted: Set<String>
    /// Minimum gap before the same session may fire again (flap protection).
    public var debounce: TimeInterval

    /// Which sessions were "waiting" in the previous snapshot (the edge memory).
    private var waitingLast: Set<String> = []
    /// Last fire time per session id — the debounce ledger.
    private var lastFired: [String: Date] = [:]

    public init(quiet: Bool = false, muted: Set<String> = [], debounce: TimeInterval = 20) {
        self.quiet = quiet; self.muted = muted; self.debounce = debounce
    }

    /// Whether a target is "waiting on you" — the same definition the Agent Desk uses:
    /// not stale, and carrying a non-empty question (the ask). Shared so the HUD lane,
    /// the desk, and the watcher never disagree on what "waiting" means.
    public static func isWaiting(_ t: CompanionTarget) -> Bool {
        !t.stale && (t.question?.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty == false)
    }

    /// Feed one fresh status snapshot; get back the rising-edge events to surface now.
    /// Mutates the edge memory + debounce ledger. `now` is injectable for tests.
    public mutating func ingest(_ state: CompanionBoardState, now: Date = Date()) -> [PresenceEvent] {
        let waitingNow = Set(state.targets.filter { Self.isWaiting($0) }.map { $0.id })
        // Rising edges: waiting now, not waiting in the previous snapshot.
        let risen = waitingNow.subtracting(waitingLast)

        var events: [PresenceEvent] = []
        if !quiet {
            for t in state.targets where Self.isWaiting(t) && risen.contains(t.id) {
                if muted.contains(t.id) { continue }
                if let prev = lastFired[t.id], now.timeIntervalSince(prev) < debounce { continue }
                lastFired[t.id] = now
                events.append(PresenceEvent(agent: t.agent, sessionID: t.sessionID,
                                            question: t.question, project: t.project, at: now))
            }
        }
        // Always advance the edge memory — even in quiet mode — so leaving quiet doesn't
        // replay a backlog (only genuinely fresh rising edges after quiet ends will fire).
        waitingLast = waitingNow
        return events
    }

    /// Forget a session entirely (e.g. after the user answered/dismissed it) so its NEXT
    /// wait is treated as a fresh rising edge.
    public mutating func forget(_ id: String) {
        waitingLast.remove(id)
        lastFired.removeValue(forKey: id)
    }
}
