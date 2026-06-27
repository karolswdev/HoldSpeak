import Foundation

// HSM equilibrium wave 3 — the iPad's propose→review→approve client contract.
// The desktop already SPLITS proposal generation from the human decision (the
// actuator audit the iPad currently collapses): `GET /api/meetings/{id}/proposals`
// is a pure read of `proposed`/decided proposals for review, and
// `POST /api/meetings/{id}/proposals/{pid}/decision` is the separate approve/reject
// gate. These types model exactly those two hub responses so the iPad can show the
// review queue and act on it without conflating the two steps.

/// One actuator proposal as the hub serializes it (`_proposal_to_dict` in
/// `holdspeak/web/routes/meetings.py`). snake_case wire keys map to camelCase via
/// the shared decoder's `.convertFromSnakeCase` (see `Coding.swift`); the timestamp
/// fields decode as ISO-8601 UTC `Z` and are optional because `decided_at` /
/// `executed_at` are `null` for an undecided proposal. Robust-decode posture: every
/// nullable wire field is optional so the review queue tolerates the payload evolving.
///
/// This is the review-side view; it intentionally mirrors (but does not depend on)
/// the existing `ActuatorProposal` so this wave's client slice lives entirely in
/// new files.
public struct MeetingProposal: Codable, Equatable, Sendable {
    public var id: String
    public var meetingId: String
    public var windowId: String?
    public var pluginId: String?
    public var pluginVersion: String?
    public var status: ActuatorStatus
    public var target: String
    public var action: String
    public var preview: String
    public var payload: JSONValue?
    public var reversible: Bool
    public var requiredCapabilities: [String]
    public var decidedBy: String?
    public var result: JSONValue?
    public var error: String?
    public var createdAt: Date?
    public var decidedAt: Date?
    public var executedAt: Date?

    public init(
        id: String, meetingId: String, windowId: String? = nil,
        pluginId: String? = nil, pluginVersion: String? = nil,
        status: ActuatorStatus, target: String, action: String, preview: String,
        payload: JSONValue? = nil, reversible: Bool, requiredCapabilities: [String] = [],
        decidedBy: String? = nil, result: JSONValue? = nil, error: String? = nil,
        createdAt: Date? = nil, decidedAt: Date? = nil, executedAt: Date? = nil
    ) {
        self.id = id
        self.meetingId = meetingId
        self.windowId = windowId
        self.pluginId = pluginId
        self.pluginVersion = pluginVersion
        self.status = status
        self.target = target
        self.action = action
        self.preview = preview
        self.payload = payload
        self.reversible = reversible
        self.requiredCapabilities = requiredCapabilities
        self.decidedBy = decidedBy
        self.result = result
        self.error = error
        self.createdAt = createdAt
        self.decidedAt = decidedAt
        self.executedAt = executedAt
    }
}

/// The list-proposals envelope: `{ "meeting_id": ..., "proposals": [...] }`.
public struct MeetingProposalsEnvelope: Codable, Equatable, Sendable {
    public var meetingId: String
    public var proposals: [MeetingProposal]

    public init(meetingId: String, proposals: [MeetingProposal]) {
        self.meetingId = meetingId
        self.proposals = proposals
    }
}

/// The decision route's response: `{ "success": ..., "proposal": {...} }` on a legal
/// approve/reject, or `{ "success": false, "error": ... }` on an illegal decision
/// (e.g. an already-executed proposal). `proposal` carries the transitioned record
/// (a slack approval may already be `executed`); `error` is the human reason.
public struct ProposalDecision: Codable, Equatable, Sendable {
    public var success: Bool
    public var proposal: MeetingProposal?
    public var error: String?

    public init(success: Bool, proposal: MeetingProposal? = nil, error: String? = nil) {
        self.success = success
        self.proposal = proposal
        self.error = error
    }
}
