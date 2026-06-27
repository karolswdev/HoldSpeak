import Foundation

// EQ-W3 (iOS artifacts) — the read-side contract for a meeting's synthesized
// artifacts, modelled faithfully against `GET /api/meetings/{id}/artifacts` in
// holdspeak/web/routes/meetings.py. The audit finding this fixes: the iPad render
// currently drops `confidence` and `sources` (the provenance the desk should
// show), so this type carries them as first-class fields.
//
// Wire keys arrive snake_case; these camelCase properties map via the shared
// decoder's `.convertFromSnakeCase` strategy (HoldSpeakContracts.decoder()),
// matching the no-explicit-CodingKeys convention of `ArtifactSource` in Models.swift.
//
// INTEGRATOR NOTE — overlap with `Contracts/Models.swift::Artifact`:
//   `Artifact` already exists and also carries `confidence` (non-optional Double)
//   and `sources: [ArtifactSource]`. This `MeetingArtifact` is a deliberately
//   leaner, decode-tolerant read model for the artifacts route: `artifactType`
//   and `status` stay `String` (not the `ArtifactType`/`ArtifactStatus` enums) so
//   a future wire value never fails the whole decode, `confidence` is `Double?`
//   per the slice spec, and the lineage rows use a local
//   `MeetingArtifactSource`. If the integrator prefers the richer `Artifact`,
//   collapse these two — but keep the optional `confidence` + the source list so
//   the iPad render can finally show provenance.

/// One lineage row for a synthesized artifact. On the wire each `sources` entry is
/// `{"source_type": ..., "source_ref": ...}` (see `ArtifactSummary.sources` in
/// holdspeak/db/models.py — a `list[dict[str, str]]`). Decodes via the shared
/// `.convertFromSnakeCase` decoder (sourceType ← source_type).
public struct MeetingArtifactSource: Codable, Equatable, Sendable {
    public var sourceType: String
    public var sourceRef: String

    public init(sourceType: String, sourceRef: String) {
        self.sourceType = sourceType
        self.sourceRef = sourceRef
    }
}

/// A synthesized meeting artifact as returned by `GET /api/meetings/{id}/artifacts`.
/// Carries the type/title/body/status the iPad already shows AND the `confidence`
/// + `sources` provenance it currently drops. Decode is tolerant: `artifactType`
/// and `status` are raw wire strings, and `confidence` is optional.
public struct MeetingArtifact: Codable, Equatable, Sendable {
    public var id: String
    public var meetingId: String
    /// Raw wire string (e.g. "action_items", "decisions"); matches `ArtifactType`
    /// raw values but kept as `String` so an unknown type never fails the decode.
    public var artifactType: String
    public var title: String
    public var bodyMarkdown: String
    /// Type-specific structured payload (open shape). Kept as `JSONValue` so the
    /// read model tolerates any plugin output.
    public var structuredJson: JSONValue?
    /// Synthesis confidence (0...1). Optional per the slice spec; the route always
    /// sends a float today, but the iPad render must tolerate its absence.
    public var confidence: Double?
    /// Raw wire string (e.g. "draft", "needs_review", "accepted", "rejected").
    public var status: String
    public var pluginId: String?
    public var pluginVersion: String?
    /// The provenance list — `(source_type, source_ref)` lineage rows.
    public var sources: [MeetingArtifactSource]
    public var createdAt: Date?
    public var updatedAt: Date?

    public init(
        id: String, meetingId: String, artifactType: String,
        title: String, bodyMarkdown: String, structuredJson: JSONValue? = nil,
        confidence: Double? = nil, status: String, pluginId: String? = nil,
        pluginVersion: String? = nil, sources: [MeetingArtifactSource] = [],
        createdAt: Date? = nil, updatedAt: Date? = nil
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
    }
}

/// The envelope `GET /api/meetings/{id}/artifacts` returns: `{meeting_id, artifacts}`.
public struct MeetingArtifactsEnvelope: Codable, Equatable, Sendable {
    public var meetingId: String
    public var artifacts: [MeetingArtifact]

    public init(meetingId: String, artifacts: [MeetingArtifact]) {
        self.meetingId = meetingId
        self.artifacts = artifacts
    }
}
