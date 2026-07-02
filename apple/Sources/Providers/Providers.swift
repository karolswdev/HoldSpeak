import Foundation
import Contracts

// Layer 3 — provider abstractions (charter Architecture). The Runtime Core
// depends on these protocols, never on a concrete engine. Method surfaces are
// intentionally minimal placeholders for Phase 1; each fills out in its phase:
// ITranscriber (Phase 3), ILLMProvider (Phase 5), IAudioCapture (Phase 2),
// IStorage (Phase 4), ISyncProvider (Phase 10).

public protocol IAudioCapture: Sendable {
    /// Begin capture; `onChunk` is called with 16 kHz mono PCM16 chunks as audio
    /// streams in. HSM-2-01/02.
    func start(onChunk: @escaping @Sendable (AudioChunk) -> Void) throws
    func stop() throws
}

public protocol ITranscriber: Sendable {
    /// Produce contract `Segment`s from captured audio (speaker-ready).
    func transcribe() async throws -> [Segment]
}

public protocol ILLMProvider: Sendable {
    /// Run a completion; structured-output binding lands in Phase 5.
    func complete(prompt: String) async throws -> String
}

/// HSM-14-09 — the vision seam: answer a prompt about an image. Same Mode A/B/C shape as
/// `ILLMProvider`: backed on-device by a local VLM (Gemma 4 — the small E4B variant — via
/// MLX-VLM on Apple Silicon) for the air-gapped case, or an OpenAI-compatible vision endpoint
/// (Modes B/C). The Runtime Core depends on this seam, never on a concrete model — so the VLM
/// is swappable (Gemma 4 E4B/12B, Qwen2.5-VL, Phi-4 MM). Used first as the ambiguity resolver
/// for the strokes-first sketch→Mermaid path (HSM-14-08), and for general image understanding
/// (whiteboard photos, pasted screenshots).
public protocol IVisionProvider: Sendable {
    /// Answer `prompt` about the PNG-encoded `image`. Fully local when Mode A.
    func describe(image: Data, prompt: String) async throws -> String
}

public protocol IStorage: Sendable {
    func saveMeeting(_ meeting: Meeting) throws
    func loadMeeting(id: String) throws -> Meeting?
    func saveArtifact(_ artifact: Artifact) throws
    func loadArtifacts(meetingId: String) throws -> [Artifact]
}

public protocol ISyncProvider: Sendable {
    /// Push a local change-set to the peer (desktop / homelab / Tailscale — the
    /// concrete transports are HSM-10-02). The Runtime Core depends on this seam,
    /// never on a transport.
    func push(_ changeSet: ChangeSet) async throws
    /// Pull the peer's change-set (its live entities + tombstones since last sync).
    func pull() async throws -> ChangeSet
}

public protocol IDesktopClient: Sendable {
    /// Probe the configured desktop/homelab peer (HSM-12-01). **Never throws** — an
    /// unreachable desktop is a first-class state, not an error, so the companion can
    /// render it and the device's on-device runtime is never blocked on the server.
    /// The Runtime Core depends on this seam, never on a concrete transport.
    func handshake() async -> DesktopConnection
    /// Honest egress descriptor for the badge (positioning canon: one badge, never a
    /// privacy novel). The companion talks to a LAN peer.
    var egressLabel: String { get }

    // MARK: Meetings remote control (HSM-12-02)
    // These DO throw on an unreachable/erroring peer — the view-model catches and
    // renders the unreachable state, keeping the on-device runtime unaffected.

    /// The server's meetings (`GET /api/meetings`).
    func listMeetings() async throws -> [MeetingSummary]
    /// The live runtime state (`GET /api/runtime/status`).
    func runtimeState() async throws -> RuntimeState
    /// Start a meeting on the desktop (`POST /api/meeting/start`), returning the
    /// resulting live state.
    func startMeeting(title: String?) async throws -> RuntimeState
    /// Stop the active meeting on the desktop (`POST /api/meeting/stop`), returning
    /// the resulting live state.
    func stopMeeting() async throws -> RuntimeState

    // MARK: Answer the coder (HSM-13-01)

    /// Deliver a dictated answer to the desktop (`POST /api/dictation/remote`). The
    /// desktop runs it through the rich dictation pipeline and delivers it into the
    /// coder; this returns the processed text + whether it was delivered.
    /// Deliver-on-command — the user pressed send; never autonomous.
    ///
    /// `target`: where the words land on the Mac. `.agent` (the default — keeps the
    /// "answer the coder" call sites byte-identical) routes into the waiting coder
    /// session; `.focused` (HSM-15-01) free-types into whatever Mac app is focused,
    /// no awaiting session required.
    func sendRemoteDictation(text: String, target: DictationTarget) async throws -> RemoteDictationResult

    // MARK: The Companion board (HSM-13-03)

    /// The AI PI companion state (`GET /api/coders/status`): which coder sessions
    /// are waiting, which is the selected reply target, confidence + blockers.
    func companionStatus() async throws -> CompanionBoardState
    /// Make a waiting session the active reply target (`POST /api/coders/select`),
    /// so the next answer (HSM-13-01/02) delivers to it — no silent default.
    func selectCompanionTarget(agent: String, sessionID: String) async throws
    /// Clear a waiting session's captured question (`POST /api/coders/dismiss`).
    func dismissCompanionTarget(agent: String, sessionID: String) async throws
    /// Pin/unpin a waiting session as the sticky target (`POST /api/coders/pin`).
    func pinCompanionTarget(agent: String, sessionID: String, pinned: Bool) async throws

    // MARK: Run on the hub (HSM-15-xx — the Mesh "RUNS ON: your Mac")

    /// Run a synced Agent persona on the desktop hub's big model
    /// (`POST /api/agents/{id}/run` body `{input}`), returning the model's output.
    /// The card's `routableText` is the input; the work — and the egress — happens on
    /// the Mac, not on-device, so the result lands with a cloud/LAN egress badge.
    /// Throws on an unreachable hub or a 502 (no model loaded) — never silent.
    func runAgent(id: String, input: String) async throws -> HubRunResult
    /// Run a synced Chain (crew) on the desktop hub (`POST /api/chains/{id}/run` body
    /// `{input}` → `{output, steps}`), threading the input through each agent on the
    /// Mac. Returns the final output plus the per-step trail.
    func runChain(id: String, input: String) async throws -> HubRunResult
}

/// The desktop hub's response to running an Agent or Chain (`/api/agents/{id}/run`,
/// `/api/chains/{id}/run`). Decoded loosely — only `output` is load-bearing; `steps`
/// is the chain's per-agent trail when the hub returns it. Keys arrive snake_case.
public struct HubRunResult: Sendable, Equatable, Decodable {
    public var output: String
    public var steps: [String]?

    public init(output: String, steps: [String]? = nil) {
        self.output = output; self.steps = steps
    }
}

/// Where a remote dictation lands on the Mac (HSM-15-01). Maps to the desktop's
/// `target_mode` field on `POST /api/dictation/remote`.
public enum DictationTarget: String, Sendable, Equatable {
    /// Route into the waiting coder session (the "answer the coder" path, HSM-13). The
    /// historical default — keeps every prior call site byte-identical.
    case agent
    /// Free-type the processed text into whatever Mac app is focused, no awaiting coder
    /// session required (the flagship "dictate into your Mac" surface, HSM-15-01).
    case focused
}

/// Default-`.agent` convenience so the HSM-13 call sites (the coder composer, the probe)
/// stay byte-identical: they call `sendRemoteDictation(text:)` and route to the agent.
public extension IDesktopClient {
    func sendRemoteDictation(text: String) async throws -> RemoteDictationResult {
        try await sendRemoteDictation(text: text, target: .agent)
    }

    /// Default hub-run stubs so non-HTTP conformers (test fakes) keep compiling without
    /// claiming a capability they don't have. `HTTPDesktopClient` overrides both with
    /// the real routes; an unimplemented client honestly reports "unsupported".
    func runAgent(id: String, input: String) async throws -> HubRunResult {
        throw HubRunUnsupported.notImplemented
    }
    func runChain(id: String, input: String) async throws -> HubRunResult {
        throw HubRunUnsupported.notImplemented
    }
}

/// Thrown by the default hub-run stub when a client doesn't implement it.
public enum HubRunUnsupported: Error, Equatable { case notImplemented }

/// The desktop's response to a remote-dictation inject (HSM-13-01).
public struct RemoteDictationResult: Sendable, Equatable, Decodable {
    public var success: Bool
    public var finalText: String      // the pipeline-processed text (not raw transcript)
    public var delivered: Bool        // true if a desktop dictation target received it

    public init(success: Bool, finalText: String, delivered: Bool) {
        self.success = success; self.finalText = finalText; self.delivered = delivered
    }
}

/// One waiting coder session as the Companion board shows it (HSM-13-03) — a row in
/// the AI PI overview (`/api/coders/status` → `agent.sessions.items[]`). The board
/// makes the *selected* target unmistakable before any answer is sent.
public struct CompanionTarget: Sendable, Equatable, Identifiable {
    public var agent: String           // "claude" / "codex"
    public var sessionID: String
    public var question: String?       // the agent's last message — the ask
    public var project: String?        // repo/project name, for telling sessions apart
    public var selected: Bool          // the active reply target an answer would hit
    public var pinned: Bool            // sticky target, never auto-expired
    public var stale: Bool             // older than the freshness threshold
    public var confidence: String?     // delivery confidence ("high"/"medium"/…)

    public init(agent: String, sessionID: String, question: String? = nil, project: String? = nil,
                selected: Bool = false, pinned: Bool = false, stale: Bool = false, confidence: String? = nil) {
        self.agent = agent; self.sessionID = sessionID; self.question = question; self.project = project
        self.selected = selected; self.pinned = pinned; self.stale = stale; self.confidence = confidence
    }

    public var id: String { "\(agent)/\(sessionID)" }
}

/// The Companion board's view of the AI PI loop (HSM-13-03), decoded from
/// `GET /api/coders/status`. Honest by construction: an empty `targets` with
/// `awaiting == false` means *nothing is waiting* — never a manufactured target.
public struct CompanionBoardState: Sendable, Equatable {
    public var readyForReply: Bool     // the desktop can deliver an answer right now
    public var blockers: [String]      // why not, if not (e.g. "no_agent_waiting")
    public var awaiting: Bool          // at least one coder is waiting on a reply
    public var targets: [CompanionTarget]

    public init(readyForReply: Bool = false, blockers: [String] = [],
                awaiting: Bool = false, targets: [CompanionTarget] = []) {
        self.readyForReply = readyForReply; self.blockers = blockers
        self.awaiting = awaiting; self.targets = targets
    }

    /// The target an answer would currently land in (the selected one, else the first
    /// waiting session). `nil` when nothing is waiting.
    public var activeTarget: CompanionTarget? {
        targets.first(where: { $0.selected }) ?? targets.first
    }
}

/// A meeting as the desktop's `GET /api/meetings` summarizes it (HSM-12-02). Decoded
/// loosely — only `id` is required — so the client tolerates the server's payload
/// evolving. Keys arrive snake_case and convert via the shared decoder.
///
/// METAL-READINESS: `startedAt`/`endedAt` are RAW ISO STRINGS, not `Date`. The hub
/// emits `m.started_at.isoformat()` where `started_at` is a *naive/local/microsecond*
/// `datetime.now()` with NO `Z` and NO offset (e.g. `2026-06-27T18:08:21.337333`).
/// The shared decoder's `.iso8601` strategy REQUIRES a timezone and rejects fractional
/// seconds, so a `Date?` here throws on a present-but-naive value (`decodeIfPresent`
/// only skips null/absent, not malformed) — failing the WHOLE `listMeetings()` /
/// `searchMeetings()` decode on the live archive. Carried as `String?` to match the
/// rest of the session contracts (MeetingProposal / MeetingArtifact / Aftercare) and
/// stay format-safe; no consumer parses these as instants today.
public struct MeetingSummary: Sendable, Equatable, Decodable, Identifiable {
    public var id: String
    public var title: String?
    public var startedAt: String?
    public var endedAt: String?
    public var durationSeconds: Double?
    public var segmentCount: Int?
    public var actionItemCount: Int?
    public var intelStatus: String?

    public init(id: String, title: String? = nil, startedAt: String? = nil, endedAt: String? = nil,
                durationSeconds: Double? = nil, segmentCount: Int? = nil,
                actionItemCount: Int? = nil, intelStatus: String? = nil) {
        self.id = id; self.title = title; self.startedAt = startedAt; self.endedAt = endedAt
        self.durationSeconds = durationSeconds; self.segmentCount = segmentCount
        self.actionItemCount = actionItemCount; self.intelStatus = intelStatus
    }
}

/// The desktop's live runtime state (`GET /api/runtime/status`), HSM-12-02.
public struct RuntimeState: Sendable, Equatable {
    public var status: String          // "ok" when the runtime is up
    public var mode: String?           // e.g. "web"
    public var meetingActive: Bool
    public var meetingId: String?

    public init(status: String, mode: String? = nil, meetingActive: Bool = false, meetingId: String? = nil) {
        self.status = status; self.mode = mode; self.meetingActive = meetingActive; self.meetingId = meetingId
    }
}

/// The sync-facing view of the local store (HSM-10-01): modified-time tracking and
/// soft-delete tombstones on top of the Phase-4 store, so a change-set can be
/// produced from and applied to it. Kept separate from `IStorage` so the base CRUD
/// surface stays lean.
public protocol ISyncStore: Sendable {
    func saveMeeting(_ meeting: Meeting, modifiedAt: Date) throws
    func saveArtifact(_ artifact: Artifact, modifiedAt: Date) throws
    /// Soft-delete: record a tombstone (`deleted=1`) so the delete can propagate.
    func deleteMeeting(id: String, at: Date) throws
    func deleteArtifact(id: String, at: Date) throws
    /// Live (non-tombstoned) entities with their last-modified instant.
    func allMeetings() throws -> [(meeting: Meeting, modifiedAt: Date)]
    func allArtifacts() throws -> [(artifact: Artifact, modifiedAt: Date)]
    /// Tombstones (propagated deletes) for both kinds.
    func tombstones() throws -> [SyncMetadata]
}
