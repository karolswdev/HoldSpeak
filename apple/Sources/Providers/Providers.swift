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
}

/// A meeting as the desktop's `GET /api/meetings` summarizes it (HSM-12-02). Decoded
/// loosely — only `id` is required — so the client tolerates the server's payload
/// evolving. Keys arrive snake_case and convert via the shared decoder.
public struct MeetingSummary: Sendable, Equatable, Decodable, Identifiable {
    public var id: String
    public var title: String?
    public var startedAt: Date?
    public var endedAt: Date?
    public var durationSeconds: Double?
    public var segmentCount: Int?
    public var actionItemCount: Int?
    public var intelStatus: String?

    public init(id: String, title: String? = nil, startedAt: Date? = nil, endedAt: Date? = nil,
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
