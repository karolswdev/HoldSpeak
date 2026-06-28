import Foundation

// The aftercare digest contract (HS-49-01 / HSM client layer). Read-only "close
// the loop" rollup the desktop returns from `GET /api/meetings/{id}/aftercare`:
// what's still open (grouped by owner), what was decided, and a real diff vs the
// chronologically previous meeting. Plus the `POST .../aftercare/file-issue`
// result: an actuator *proposal* (proposed state) the user separately approves.
//
// Wire keys arrive snake_case and convert to these camelCase properties via the
// shared decoder (`HoldSpeakContracts.decoder()`, `.convertFromSnakeCase`) — so
// these types carry NO explicit CodingKeys for case conversion (matching
// Models.swift / Providers.swift conventions). Every nested field the digest can
// omit is optional, so the client tolerates the payload evolving and stays honest
// (an empty digest renders nothing).

/// A resolved "show me the moment" jump target — the transcript segment that
/// justifies a decision or open item (`resolve_provenance_segment`). `nil` on the
/// wire when the source had no usable timestamp (no fake jump is invented).
public struct AftercareProvenance: Codable, Equatable, Sendable {
    public var sourceTimestamp: Double?
    public var segmentIndex: Int?
    public var segmentStart: Double?
    public var speaker: String?
    public var textPreview: String?

    public init(sourceTimestamp: Double? = nil, segmentIndex: Int? = nil,
                segmentStart: Double? = nil, speaker: String? = nil, textPreview: String? = nil) {
        self.sourceTimestamp = sourceTimestamp
        self.segmentIndex = segmentIndex
        self.segmentStart = segmentStart
        self.speaker = speaker
        self.textPreview = textPreview
    }
}

/// One pending action item as the aftercare digest serializes it (an entry in an
/// owner group's `items`). `id` + `meetingId` are load-bearing for the file-issue
/// loop; everything else is best-effort.
public struct AftercareOpenItem: Codable, Equatable, Sendable {
    public var id: String
    public var task: String
    public var owner: String?
    public var due: String?
    public var reviewState: String?
    public var sourceTimestamp: Double?
    public var provenance: AftercareProvenance?
    public var meetingId: String?

    public init(id: String, task: String, owner: String? = nil, due: String? = nil,
                reviewState: String? = nil, sourceTimestamp: Double? = nil,
                provenance: AftercareProvenance? = nil, meetingId: String? = nil) {
        self.id = id
        self.task = task
        self.owner = owner
        self.due = due
        self.reviewState = reviewState
        self.sourceTimestamp = sourceTimestamp
        self.provenance = provenance
        self.meetingId = meetingId
    }
}

/// Open items for one owner — the `open_items.by_owner[]` grouping (named owners
/// A→Z, unassigned last, `owner == nil`).
public struct AftercareOwnerGroup: Codable, Equatable, Sendable {
    public var owner: String?
    public var count: Int
    public var items: [AftercareOpenItem]

    public init(owner: String? = nil, count: Int, items: [AftercareOpenItem] = []) {
        self.owner = owner
        self.count = count
        self.items = items
    }
}

/// The `open_items` block: a total plus the by-owner grouping.
public struct AftercareOpenItems: Codable, Equatable, Sendable {
    public var total: Int
    public var byOwner: [AftercareOwnerGroup]

    public init(total: Int, byOwner: [AftercareOwnerGroup] = []) {
        self.total = total
        self.byOwner = byOwner
    }
}

/// One decision captured for the meeting (deduped by normalized text). A
/// `provenance` is present only when the decision carried a real source timestamp.
public struct AftercareDecision: Codable, Equatable, Sendable {
    public var decision: String
    public var rationale: String?
    public var sourceTimestamp: Double?
    public var provenance: AftercareProvenance?

    public init(decision: String, rationale: String? = nil,
                sourceTimestamp: Double? = nil, provenance: AftercareProvenance? = nil) {
        self.decision = decision
        self.rationale = rationale
        self.sourceTimestamp = sourceTimestamp
        self.provenance = provenance
    }
}

/// The chronologically-previous meeting the diff is computed against.
public struct AftercarePreviousMeeting: Codable, Equatable, Sendable {
    public var id: String
    public var title: String?
    public var date: String?

    public init(id: String, title: String? = nil, date: String? = nil) {
        self.id = id
        self.title = title
        self.date = date
    }
}

/// An action item that has closed since the previous meeting (status done /
/// dismissed). A thin shape — the diff carries less than the live open-item.
public struct AftercareClosedAction: Codable, Equatable, Sendable {
    public var id: String
    public var task: String
    public var owner: String?
    public var status: String?
    public var meetingId: String?

    public init(id: String, task: String, owner: String? = nil,
                status: String? = nil, meetingId: String? = nil) {
        self.id = id
        self.task = task
        self.owner = owner
        self.status = status
        self.meetingId = meetingId
    }
}

/// The real diff vs the previous meeting (`since_last_meeting`). `nil` on the wire
/// when there is no prior meeting at all (no delta is invented).
public struct AftercareSinceLastMeeting: Codable, Equatable, Sendable {
    public var previousMeeting: AftercarePreviousMeeting?
    public var newDecisions: [AftercareDecision]
    public var newActions: [AftercareOpenItem]
    public var closedActions: [AftercareClosedAction]
    public var changed: Bool

    public init(previousMeeting: AftercarePreviousMeeting? = nil,
                newDecisions: [AftercareDecision] = [], newActions: [AftercareOpenItem] = [],
                closedActions: [AftercareClosedAction] = [], changed: Bool = false) {
        self.previousMeeting = previousMeeting
        self.newDecisions = newDecisions
        self.newActions = newActions
        self.closedActions = closedActions
        self.changed = changed
    }
}

/// The full aftercare digest (`GET /api/meetings/{id}/aftercare`). `isEmpty` is the
/// caller's cue to stay quiet (nothing open, decided, or changed). `slackConfigured`
/// gates the Send-to-Slack affordance (HS-61-02) — a bool only, never the webhook URL.
public struct Aftercare: Codable, Equatable, Sendable {
    public var meetingId: String
    public var meetingTitle: String?
    public var meetingDate: String?
    public var openItems: AftercareOpenItems
    public var decisions: [AftercareDecision]
    public var sinceLastMeeting: AftercareSinceLastMeeting?
    public var isEmpty: Bool
    public var slackConfigured: Bool?

    public init(meetingId: String, meetingTitle: String? = nil, meetingDate: String? = nil,
                openItems: AftercareOpenItems, decisions: [AftercareDecision] = [],
                sinceLastMeeting: AftercareSinceLastMeeting? = nil,
                isEmpty: Bool = false, slackConfigured: Bool? = nil) {
        self.meetingId = meetingId
        self.meetingTitle = meetingTitle
        self.meetingDate = meetingDate
        self.openItems = openItems
        self.decisions = decisions
        self.sinceLastMeeting = sinceLastMeeting
        self.isEmpty = isEmpty
        self.slackConfigured = slackConfigured
    }
}

/// The actuator proposal returned by `POST .../aftercare/file-issue` (the
/// `proposal` block of `{"success": true, "proposal": {...}}`). A *proposed* GitHub
/// issue — nothing leaves the machine until it is separately approved + actuators
/// are enabled. Decoded loosely; the `preview` is the human-readable summary the
/// approval surface shows (never the machine payload's secrets).
///
/// METAL-READINESS (EQ-W6 audit): this is `_proposal_to_dict` in
/// holdspeak/web/routes/meetings.py — the same serializer Proposals use, so the
/// timestamp fields are RAW ISO STRINGS, not `Date`. The hub re-emits them with
/// `datetime.now().isoformat()` (naive/local/microsecond, NO `Z`, e.g.
/// `2026-06-27T18:08:21.337333`), which the shared decoder's `.iso8601` strategy
/// would reject — failing the whole file-issue decode on real metal. Carried as
/// `String?` to match the contract's "Timestamps are ISO strings" and stay format-safe.
public struct AftercareIssueProposal: Codable, Equatable, Sendable {
    public var id: String
    public var meetingId: String?
    public var windowId: String?
    public var pluginId: String?
    public var pluginVersion: String?
    public var status: String?
    public var target: String?
    public var action: String?
    public var preview: String?
    public var reversible: Bool?
    public var requiredCapabilities: [String]?
    public var decidedBy: String?
    public var error: String?
    /// Raw ISO wire strings (naive/local, no `Z`); see the type doc. Never `Date`.
    public var createdAt: String?
    public var decidedAt: String?
    public var executedAt: String?

    public init(id: String, meetingId: String? = nil, windowId: String? = nil,
                pluginId: String? = nil, pluginVersion: String? = nil, status: String? = nil,
                target: String? = nil, action: String? = nil, preview: String? = nil,
                reversible: Bool? = nil, requiredCapabilities: [String]? = nil,
                decidedBy: String? = nil, error: String? = nil,
                createdAt: String? = nil, decidedAt: String? = nil, executedAt: String? = nil) {
        self.id = id
        self.meetingId = meetingId
        self.windowId = windowId
        self.pluginId = pluginId
        self.pluginVersion = pluginVersion
        self.status = status
        self.target = target
        self.action = action
        self.preview = preview
        self.reversible = reversible
        self.requiredCapabilities = requiredCapabilities
        self.decidedBy = decidedBy
        self.error = error
        self.createdAt = createdAt
        self.decidedAt = decidedAt
        self.executedAt = executedAt
    }
}

/// The full `POST .../aftercare/file-issue` envelope: `{"success", "proposal"?, "error"?}`.
/// A 400/404 from the route returns `{"success": false, "error": "..."}` (no proposal).
public struct AftercareFileIssueResult: Codable, Equatable, Sendable {
    public var success: Bool
    public var proposal: AftercareIssueProposal?
    public var error: String?

    public init(success: Bool, proposal: AftercareIssueProposal? = nil, error: String? = nil) {
        self.success = success
        self.proposal = proposal
        self.error = error
    }
}
