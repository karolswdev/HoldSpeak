import Foundation

// HSM-26-02 — the DeskOS belt + the presence-class steering/rails shapes,
// as Swift models the diorama decodes. These MIRROR the desktop contracts
// written down in HSM-26-01 (pm/roadmap/holdspeak-mobile/contracts/schemas/):
// the belt renders from GET /api/missioncontrol/state; the steering + rails
// surfaces from the Phase-87/88 routes. "Inherits, never redesigns" — a
// Swift field maps 1:1 to a contract row; nothing is invented here.
//
// snake_case on the wire converts to camelCase via HoldSpeakContracts.decoder().
// Instants ride as String (the presence routes emit ISO-Z but tolerate the
// registry's own stamps), never a fragile Date decode.

// MARK: - The belt (GET /api/missioncontrol/state)

public struct BeltState: Codable, Equatable, Sendable {
    public var repos: [BeltRepo]
    public init(repos: [BeltRepo]) { self.repos = repos }
}

public struct BeltRepo: Codable, Equatable, Sendable {
    public var name: String
    public var path: String?
    public var status: String            // live | compatibility | unavailable | unreachable
    public var detail: String?
    public var feed: BeltFeed?
    public init(name: String, path: String? = nil, status: String,
                detail: String? = nil, feed: BeltFeed? = nil) {
        self.name = name; self.path = path; self.status = status
        self.detail = detail; self.feed = feed
    }
}

public struct BeltFeed: Codable, Equatable, Sendable {
    public var projects: [BeltProject]
    public init(projects: [BeltProject]) { self.projects = projects }
}

public struct BeltProject: Codable, Equatable, Sendable {
    public var slug: String
    public var prefix: String?
    public var currentPhase: BeltPhase?
    public var nextStory: BeltStoryRef?
    public var phases: [BeltPhase]?
    public var stories: [BeltStory]
    public var warnings: Int?
    public init(slug: String, prefix: String? = nil, currentPhase: BeltPhase? = nil,
                nextStory: BeltStoryRef? = nil, phases: [BeltPhase]? = nil,
                stories: [BeltStory] = [], warnings: Int? = nil) {
        self.slug = slug; self.prefix = prefix; self.currentPhase = currentPhase
        self.nextStory = nextStory; self.phases = phases; self.stories = stories
        self.warnings = warnings
    }
}

public struct BeltPhase: Codable, Equatable, Sendable {
    public var number: Int
    public var title: String?
    public var status: String            // open | closed
    public var storiesDone: Int?
    public var storiesTotal: Int?
    public init(number: Int, title: String? = nil, status: String,
                storiesDone: Int? = nil, storiesTotal: Int? = nil) {
        self.number = number; self.title = title; self.status = status
        self.storiesDone = storiesDone; self.storiesTotal = storiesTotal
    }
}

public struct BeltStoryRef: Codable, Equatable, Sendable {
    public var storyId: String
    public var title: String?
    public var status: String?
    public init(storyId: String, title: String? = nil, status: String? = nil) {
        self.storyId = storyId; self.title = title; self.status = status
    }
}

public struct BeltStory: Codable, Equatable, Sendable {
    public var storyId: String
    public var title: String?
    public var status: String
    public var phase: Int?
    public var evidenceExists: Bool?
    public init(storyId: String, title: String? = nil, status: String,
                phase: Int? = nil, evidenceExists: Bool? = nil) {
        self.storyId = storyId; self.title = title; self.status = status
        self.phase = phase; self.evidenceExists = evidenceExists
    }
}

// MARK: - Presence: steering (Phase 87)

public struct CoderSteeringOperation: Codable, Equatable, Sendable {
    public var effectClass: String?
    public var destination: String?
    public var consequence: String?
}

public struct CoderSteeringPolicy: Codable, Equatable, Sendable {
    public var mode: String?
    public var source: String?
    public var policyVersion: String?
    public var outcome: String?
    public var reasonCode: String?
    public var authorityBasis: String?
    public var nextState: String?
    public var requiresGrant: Bool?

    public var usesControlPosture: Bool {
        outcome == "allowed" && authorityBasis == "control_posture"
    }
}

public struct CoderSteeringCommitment: Codable, Equatable, Sendable {
    public var effect: String?
    public var destination: String?
    public var authorityBasis: String?
    public var nextState: String?
    public var receipt: String?
}

public struct CoderSteeringReceipt: Codable, Equatable, Sendable {
    public var id: String
    public var sourceRef: String?
    public var actualDestination: String?
    public var authorityBasis: String?
    public var controlMode: String?
    public var policyVersion: String?
    public var effectClass: String?
    public var outcome: String?
}

public struct CoderSessionPeek: Codable, Equatable, Sendable {
    public var key: String
    public var agent: String
    public var stale: Bool
    public var awaitingResponse: Bool
    public var question: String?
    public var updatedAt: String?
    public var paneId: String?
    public var operation: CoderSteeringOperation?
    public var policy: CoderSteeringPolicy?
    public var commitment: CoderSteeringCommitment?
    public var armCommitment: String?
    public var grant: Grant
    public var peek: Peek

    public struct Grant: Codable, Equatable, Sendable {
        public var armed: Bool
        public var expiresInSeconds: Int?
        public init(armed: Bool, expiresInSeconds: Int? = nil) {
            self.armed = armed; self.expiresInSeconds = expiresInSeconds
        }
    }

    public struct Peek: Codable, Equatable, Sendable {
        public var status: String        // live | not_modified | pane_gone | tmux_absent | no_pane | error
        public var hash: String?
        public var lines: [String]?
        public var detail: String?
        public init(status: String, hash: String? = nil,
                    lines: [String]? = nil, detail: String? = nil) {
            self.status = status; self.hash = hash; self.lines = lines; self.detail = detail
        }
    }

    public init(key: String, agent: String, stale: Bool, awaitingResponse: Bool,
                question: String? = nil, updatedAt: String? = nil,
                grant: Grant, peek: Peek, paneId: String? = nil,
                operation: CoderSteeringOperation? = nil,
                policy: CoderSteeringPolicy? = nil,
                commitment: CoderSteeringCommitment? = nil,
                armCommitment: String? = nil) {
        self.key = key; self.agent = agent; self.stale = stale
        self.awaitingResponse = awaitingResponse; self.question = question
        self.updatedAt = updatedAt; self.grant = grant; self.peek = peek
        self.paneId = paneId; self.operation = operation; self.policy = policy
        self.commitment = commitment; self.armCommitment = armCommitment
    }
}

public struct ArmingGrant: Codable, Equatable, Sendable {
    public var status: String            // "armed"
    public var key: String
    public var paneId: String
    public var expiresInSeconds: Int
    public init(status: String, key: String, paneId: String, expiresInSeconds: Int) {
        self.status = status; self.key = key; self.paneId = paneId
        self.expiresInSeconds = expiresInSeconds
    }
}

public struct SteerResult: Codable, Equatable, Sendable {
    public var status: String            // delivered + the typed refusals
    public var paneId: String?
    public var submitted: Bool?
    public var auditId: Int?
    public var revoked: Bool?
    public var detail: String?
    public var operation: CoderSteeringOperation?
    public var policy: CoderSteeringPolicy?
    public var receipt: CoderSteeringReceipt?
    public init(status: String, paneId: String? = nil, submitted: Bool? = nil,
                auditId: Int? = nil, revoked: Bool? = nil, detail: String? = nil,
                operation: CoderSteeringOperation? = nil,
                policy: CoderSteeringPolicy? = nil,
                receipt: CoderSteeringReceipt? = nil) {
        self.status = status; self.paneId = paneId; self.submitted = submitted
        self.auditId = auditId; self.revoked = revoked; self.detail = detail
        self.operation = operation; self.policy = policy; self.receipt = receipt
    }

    /// The consent grammar the surface reads from the shape alone: a
    /// revoking refusal (recycled pane / expiry) means re-offer ARM.
    public var isDelivered: Bool { status == "delivered" }
    public var didRevoke: Bool { revoked == true }
}

public struct SteeringAuditEntry: Codable, Equatable, Sendable {
    public var id: Int
    public var ts: String
    public var sessionKey: String
    public var agent: String
    public var paneId: String?
    public var textSha256: String
    public var textHead: String
    public var grounding: [String]
    public var submit: Bool
    public var outcome: String
    public var detail: String?
    public var operation: CoderSteeringOperation?
    public var policySnapshot: CoderSteeringPolicy?
    public init(id: Int, ts: String, sessionKey: String, agent: String,
                paneId: String? = nil, textSha256: String, textHead: String,
                grounding: [String] = [], submit: Bool, outcome: String,
                detail: String? = nil, operation: CoderSteeringOperation? = nil,
                policySnapshot: CoderSteeringPolicy? = nil) {
        self.id = id; self.ts = ts; self.sessionKey = sessionKey; self.agent = agent
        self.paneId = paneId; self.textSha256 = textSha256; self.textHead = textHead
        self.grounding = grounding; self.submit = submit; self.outcome = outcome
        self.detail = detail; self.operation = operation
        self.policySnapshot = policySnapshot
    }
}

// MARK: - Presence: rails (Phase 88)

public struct RailsGroundingRef: Codable, Equatable, Sendable {
    public var repo: String
    public var project: String
    public var kind: String              // phase | story | evidence | roadmap
    public var id: String
    public init(repo: String, project: String, kind: String, id: String) {
        self.repo = repo; self.project = project; self.kind = kind; self.id = id
    }
}

public struct RailsJournalEntry: Codable, Equatable, Sendable {
    public var id: String
    public var title: String
    public var bodyMarkdown: String
    public var createdAt: String?
    public init(id: String, title: String, bodyMarkdown: String, createdAt: String? = nil) {
        self.id = id; self.title = title; self.bodyMarkdown = bodyMarkdown
        self.createdAt = createdAt
    }
}
