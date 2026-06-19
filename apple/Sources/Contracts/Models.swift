import Foundation

// The canonical entity types (charter Layer 1), generated against the Phase-0
// JSON Schemas + serialization contract. snake_case wire keys map to these
// camelCase properties via the decoder/encoder key strategy (see Coding.swift);
// instants are UTC-Z `Date`s, intra-meeting offsets are `Double` seconds.

public struct Segment: Codable, Equatable, Sendable {
    public var text: String
    public var speaker: String
    public var speakerId: String?
    public var startTime: Double
    public var endTime: Double
    public var isBookmarked: Bool
    public var deviceId: String?

    // Public memberwise init so RuntimeCore/Providers (other modules) can build a
    // Segment — e.g. the Phase-3 transcription mapping. (Synthesized memberwise
    // inits are internal; cross-module construction needs this.)
    public init(text: String, speaker: String, speakerId: String? = nil,
                startTime: Double, endTime: Double,
                isBookmarked: Bool = false, deviceId: String? = nil) {
        self.text = text
        self.speaker = speaker
        self.speakerId = speakerId
        self.startTime = startTime
        self.endTime = endTime
        self.isBookmarked = isBookmarked
        self.deviceId = deviceId
    }
}

public struct Bookmark: Codable, Equatable, Sendable {
    public var timestamp: Double
    public var label: String
    public var createdAt: Date
}

public struct ActionItem: Codable, Equatable, Sendable {
    public var task: String
    public var owner: String?
    public var due: String?
    public var id: String
    public var status: ActionStatus
    public var reviewState: ReviewState
    public var reviewedAt: Date?
    public var sourceTimestamp: Double?
    public var createdAt: Date
    public var completedAt: Date?
}

public struct IntelSnapshot: Codable, Equatable, Sendable {
    public var timestamp: Double
    public var topics: [String]
    public var actionItems: [ActionItem]
    public var summary: String
}

/// `intel_status` serializes nested (NOT the flat in-memory string) — contract §1.
public struct IntelStatus: Codable, Equatable, Sendable {
    public var state: String
    public var detail: String?
    public var requestedAt: Date?
    public var completedAt: Date?
}

public struct Meeting: Codable, Equatable, Sendable {
    public var id: String
    public var startedAt: Date
    public var endedAt: Date?
    public var duration: Double?
    public var formattedDuration: String?
    public var title: String?
    public var tags: [String]
    public var segments: [Segment]
    public var bookmarks: [Bookmark]
    public var intel: IntelSnapshot?
    public var intelStatus: IntelStatus
    public var micLabel: String
    public var remoteLabel: String
    public var webUrl: String?
    public var devices: [JSONValue]
    // mir_profile is NOT a desktop Meeting field; HSM-7-03 adds it as a contract
    // addition (Phase 7). Reserved here, absent on the wire today.
    public var mirProfile: MIRProfile?
}

public struct ArtifactSource: Codable, Equatable, Sendable {
    public var sourceType: String
    public var sourceRef: String

    public init(sourceType: String, sourceRef: String) {
        self.sourceType = sourceType
        self.sourceRef = sourceRef
    }
}

/// A synthesized artifact — the tagged union (contract §5): `artifactType` is the
/// discriminator, `structuredJson` the type-specific (open) payload.
public struct Artifact: Codable, Equatable, Sendable {
    public var id: String
    public var meetingId: String
    public var artifactType: ArtifactType
    public var title: String
    public var bodyMarkdown: String
    public var structuredJson: JSONValue
    public var confidence: Double
    public var status: ArtifactStatus
    public var pluginId: String
    public var pluginVersion: String
    public var sources: [ArtifactSource]
    public var createdAt: Date?   // present on persisted ArtifactSummary, absent on a draft
    public var updatedAt: Date?
    // Reserved optional egress scope (contract §8); unpopulated in v0.
    public var egress: JSONValue?

    public init(
        id: String, meetingId: String, artifactType: ArtifactType,
        title: String, bodyMarkdown: String, structuredJson: JSONValue,
        confidence: Double, status: ArtifactStatus, pluginId: String,
        pluginVersion: String, sources: [ArtifactSource] = [],
        createdAt: Date? = nil, updatedAt: Date? = nil, egress: JSONValue? = nil
    ) {
        self.id = id
        self.meetingId = meetingId
        self.artifactType = artifactType
        self.title = title
        self.bodyMarkdown = bodyMarkdown
        self.structuredJson = structuredJson
        self.confidence = confidence
        self.status = status
        self.pluginId = pluginId
        self.pluginVersion = pluginVersion
        self.sources = sources
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.egress = egress
    }
}

public struct IntelJob: Codable, Equatable, Sendable {
    public var meetingId: String
    public var status: String
    public var transcriptHash: String
    public var requestedAt: Date
    public var updatedAt: Date
    public var attempts: Int
    public var lastError: String?
    public var meetingTitle: String?
    public var startedAt: Date?
    public var intelStatusDetail: String?
}

public struct ActuatorProposal: Codable, Equatable, Sendable {
    public var id: String
    public var meetingId: String
    public var windowId: String
    public var pluginId: String
    public var pluginVersion: String
    public var idempotencyKey: String
    public var status: ActuatorStatus
    public var target: String
    public var action: String
    public var preview: String
    public var payload: JSONValue
    public var reversible: Bool
    public var requiredCapabilities: [String]
    public var decidedBy: String?
    public var result: JSONValue?
    public var error: String?
    public var createdAt: Date
    public var decidedAt: Date?
    public var executedAt: Date?
    public var updatedAt: Date
}

/// The MIR intent window — where the meeting routing `profile` is actually
/// persisted per-meeting (a `Meeting` does not carry it).
public struct IntentWindow: Codable, Equatable, Sendable {
    public var meetingId: String
    public var windowId: String
    public var startSeconds: Double
    public var endSeconds: Double
    public var transcriptHash: String
    public var transcriptExcerpt: String
    public var profile: MIRProfile
    public var threshold: Double
    public var activeIntents: [MIRIntent]
    public var intentScores: [String: Double]
    public var overrideIntents: [String]
    public var tags: [String]
    public var metadata: JSONValue
    public var createdAt: Date
    public var updatedAt: Date
}

/// A transcript as a thin wrapper over its segments (contract §7) — for sync
/// addressing without the whole Meeting.
public struct Transcript: Codable, Equatable, Sendable {
    public var meetingId: String
    public var segments: [Segment]
    public var transcriptHash: String

    public init(meetingId: String, segments: [Segment], transcriptHash: String) {
        self.meetingId = meetingId
        self.segments = segments
        self.transcriptHash = transcriptHash
    }
}
