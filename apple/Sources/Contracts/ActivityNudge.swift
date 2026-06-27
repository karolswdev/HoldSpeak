import Foundation

// Equilibrium 18-05 — the iPad's model of the desktop's source-cited pre-briefing
// nudges (HoldSpeak Phase 53). Mirrors `Nudge.to_dict()` / `NudgeCitation.to_dict()`
// in `holdspeak/activity_nudges.py` exactly: snake_case wire keys decode to these
// camelCase properties via `.convertFromSnakeCase` (Coding.swift) — no manual
// `CodingKeys`. Every optional matches a `None`-able Python field so a sparse card
// still decodes (the codebase's robust-decode posture).

/// A source citation for a nudge — names where the cited record came from, so the
/// "Dictate with this" grounding is honest about its source (never fabricated).
public struct NudgeCitation: Codable, Equatable, Sendable {
    public var recordId: Int
    public var sourceBrowser: String
    public var sourceProfile: String
    public var entityType: String?
    public var entityId: String?
    public var domain: String
    public var title: String?
    public var url: String
    /// ISO-8601 instant kept as a wire string: it is `None`-able server-side, and
    /// holding the raw string avoids coupling the decoder's date strategy to a field
    /// the UI only displays.
    public var lastSeenAt: String?
    public var visitCount: Int

    public init(recordId: Int, sourceBrowser: String, sourceProfile: String,
                entityType: String? = nil, entityId: String? = nil, domain: String,
                title: String? = nil, url: String, lastSeenAt: String? = nil,
                visitCount: Int) {
        self.recordId = recordId
        self.sourceBrowser = sourceBrowser
        self.sourceProfile = sourceProfile
        self.entityType = entityType
        self.entityId = entityId
        self.domain = domain
        self.title = title
        self.url = url
        self.lastSeenAt = lastSeenAt
        self.visitCount = visitCount
    }
}

/// A single source-cited pre-briefing nudge. The `key` is the deterministic id the
/// dismiss route takes (e.g. `record:42` / `window:<iso>`); a `record`-kind nudge's
/// first citation's `recordId` is what `selectNudge` parks for the next dictation.
public struct ActivityNudge: Codable, Equatable, Sendable {
    public var key: String
    public var kind: String   // "window" | "record"
    public var title: String
    public var body: String
    public var score: Double
    public var citations: [NudgeCitation]
    public var windowSince: String?
    public var windowRecordCount: Int
    /// Free-form server extras; kept as a typed blob so an evolving payload still
    /// decodes. Defaults empty when the key is absent.
    public var extras: [String: JSONValue]

    public init(key: String, kind: String, title: String, body: String, score: Double,
                citations: [NudgeCitation], windowSince: String? = nil,
                windowRecordCount: Int = 0, extras: [String: JSONValue] = [:]) {
        self.key = key
        self.kind = kind
        self.title = title
        self.body = body
        self.score = score
        self.citations = citations
        self.windowSince = windowSince
        self.windowRecordCount = windowRecordCount
        self.extras = extras
    }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        self.key = try c.decode(String.self, forKey: .key)
        self.kind = try c.decode(String.self, forKey: .kind)
        self.title = try c.decode(String.self, forKey: .title)
        self.body = try c.decode(String.self, forKey: .body)
        self.score = try c.decodeIfPresent(Double.self, forKey: .score) ?? 0
        self.citations = try c.decodeIfPresent([NudgeCitation].self, forKey: .citations) ?? []
        self.windowSince = try c.decodeIfPresent(String.self, forKey: .windowSince)
        self.windowRecordCount = try c.decodeIfPresent(Int.self, forKey: .windowRecordCount) ?? 0
        self.extras = try c.decodeIfPresent([String: JSONValue].self, forKey: .extras) ?? [:]
    }
}

/// The desktop's project briefing surface (`GET /api/activity/briefing`): the most
/// recent `meeting_context_briefing` annotation (markdown in `value`) when one
/// exists, else `nil` — the iPad shows nothing rather than a fabricated digest.
public struct ActivityBriefing: Codable, Equatable, Sendable {
    public var id: Int
    public var title: String?
    public var value: String
    public var updatedAt: String?

    public init(id: Int, title: String? = nil, value: String, updatedAt: String? = nil) {
        self.id = id
        self.title = title
        self.value = value
        self.updatedAt = updatedAt
    }
}
