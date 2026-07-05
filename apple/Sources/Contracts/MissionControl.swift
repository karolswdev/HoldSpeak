import Foundation

// HSM-25-01 — the iOS model of the mission-control substrate the
// backend relays (its Phase 82: /api/missioncontrol/state|sessions|
// events). These mirror the frozen Delivery Workbench documents —
// `feed_schema` 1 and `sessions_schema` 1 — as the backend bridge
// re-emits them. snake_case wire keys decode via `.convertFromSnakeCase`
// (Coding.swift); every optional matches a field that may be absent
// (a repo whose status is not "live" carries no `feed`). The
// ContractsTests round-trip literal backend JSON through these, so
// the test IS the drift guard against the FastAPI shapes.

/// One repo's mission-control status, as relayed by
/// `/api/missioncontrol/state`. `status` is "live" | "compatibility"
/// | "unavailable"; only a live repo carries a `feed`.
public struct MCRepoState: Codable, Equatable, Sendable {
    public var name: String
    public var path: String
    public var status: String
    public var detail: String?
    public var feed: MCFeed?

    public var isLive: Bool { status == "live" }

    public init(name: String, path: String, status: String,
                detail: String? = nil, feed: MCFeed? = nil) {
        self.name = name
        self.path = path
        self.status = status
        self.detail = detail
        self.feed = feed
    }
}

/// The state endpoint's envelope: one entry per configured rails repo.
public struct MCStatePayload: Codable, Equatable, Sendable {
    public var repos: [MCRepoState]
    public var error: String?

    public init(repos: [MCRepoState], error: String? = nil) {
        self.repos = repos
        self.error = error
    }
}

/// The frozen Delivery Workbench feed (`feed_schema` 1).
public struct MCFeed: Codable, Equatable, Sendable {
    public var feedSchema: Int
    public var projects: [MCProject]

    public init(feedSchema: Int, projects: [MCProject]) {
        self.feedSchema = feedSchema
        self.projects = projects
    }
}

public struct MCPhase: Codable, Equatable, Sendable {
    public var number: Int
    public var title: String
    public var status: String            // "open" | "closed"
    public var storiesDone: Int
    public var storiesTotal: Int

    public init(number: Int, title: String, status: String,
                storiesDone: Int, storiesTotal: Int) {
        self.number = number
        self.title = title
        self.status = status
        self.storiesDone = storiesDone
        self.storiesTotal = storiesTotal
    }
}

public struct MCNextStory: Codable, Equatable, Sendable {
    public var storyId: String
    public var title: String
    public var status: String

    public init(storyId: String, title: String, status: String) {
        self.storyId = storyId
        self.title = title
        self.status = status
    }
}

public struct MCStory: Codable, Equatable, Sendable {
    public var storyId: String
    public var title: String
    public var status: String
    public var phase: Int
    public var evidenceExists: Bool

    public init(storyId: String, title: String, status: String,
                phase: Int, evidenceExists: Bool) {
        self.storyId = storyId
        self.title = title
        self.status = status
        self.phase = phase
        self.evidenceExists = evidenceExists
    }
}

public struct MCProject: Codable, Equatable, Sendable {
    public var slug: String
    public var prefix: String
    public var currentPhase: MCPhase?
    public var nextStory: MCNextStory?
    public var phases: [MCPhase]
    public var stories: [MCStory]
    public var warnings: Int

    public init(slug: String, prefix: String, currentPhase: MCPhase? = nil,
                nextStory: MCNextStory? = nil, phases: [MCPhase],
                stories: [MCStory], warnings: Int) {
        self.slug = slug
        self.prefix = prefix
        self.currentPhase = currentPhase
        self.nextStory = nextStory
        self.phases = phases
        self.stories = stories
        self.warnings = warnings
    }
}

// -- sessions -------------------------------------------------------

/// The sessions endpoint envelope. The bridge relays the DW
/// correlation document under `sessions` when the registry is live;
/// otherwise `status` is "compatibility" | "unavailable" with a
/// `detail`.
public struct MCSessionsPayload: Codable, Equatable, Sendable {
    public var status: String
    public var detail: String?
    public var sessions: MCSessionsDoc?

    public var isLive: Bool { status == "live" }

    public init(status: String, detail: String? = nil,
                sessions: MCSessionsDoc? = nil) {
        self.status = status
        self.detail = detail
        self.sessions = sessions
    }
}

public struct MCSessionsDoc: Codable, Equatable, Sendable {
    public var sessionsSchema: Int
    public var registry: String
    public var sessions: [MCSession]

    public init(sessionsSchema: Int, registry: String, sessions: [MCSession]) {
        self.sessionsSchema = sessionsSchema
        self.registry = registry
        self.sessions = sessions
    }
}

public struct MCSessionStory: Codable, Equatable, Sendable {
    public var storyId: String
    public init(storyId: String) { self.storyId = storyId }
}

public struct MCTmux: Codable, Equatable, Sendable {
    public var session: String?
    public init(session: String? = nil) { self.session = session }
}

public struct MCSession: Codable, Equatable, Sendable {
    public var key: String
    public var agent: String
    public var correlation: String       // on_story | ambiguous | idle_on_rails | off_rails | unreadable
    public var stories: [MCSessionStory]
    public var awaitingResponse: Bool
    public var stale: Bool
    public var tmux: MCTmux?

    public init(key: String, agent: String, correlation: String,
                stories: [MCSessionStory], awaitingResponse: Bool,
                stale: Bool, tmux: MCTmux? = nil) {
        self.key = key
        self.agent = agent
        self.correlation = correlation
        self.stories = stories
        self.awaitingResponse = awaitingResponse
        self.stale = stale
        self.tmux = tmux
    }
}

// -- events ---------------------------------------------------------

public struct MCRepoEvents: Codable, Equatable, Sendable {
    public var name: String
    public var path: String
    public var status: String
    public var detail: String?
    public var events: [MCEvent]?

    public init(name: String, path: String, status: String,
                detail: String? = nil, events: [MCEvent]? = nil) {
        self.name = name
        self.path = path
        self.status = status
        self.detail = detail
        self.events = events
    }
}

public struct MCEventsPayload: Codable, Equatable, Sendable {
    public var repos: [MCRepoEvents]
    public var error: String?

    public init(repos: [MCRepoEvents], error: String? = nil) {
        self.repos = repos
        self.error = error
    }
}

/// One rail event. `detail` is a small free-form map (rule ids, exit
/// codes) kept as `JSONValue` so a new detail key never breaks decode
/// — the codebase's robust-decode posture.
public struct MCEvent: Codable, Equatable, Sendable {
    public var ts: String
    public var event: String
    public var story: String?
    public var detail: [String: JSONValue]?

    public init(ts: String, event: String, story: String? = nil,
                detail: [String: JSONValue]? = nil) {
        self.ts = ts
        self.event = event
        self.story = story
        self.detail = detail
    }
}

// -- the live-layer pinning kernel (HSM-25-02/03) --------------------

/// The belt's live-layer decision, pure and testable: `on_story`
/// sessions pin to their story ids; every other correlation outcome
/// (ambiguous included — unknown beats guessed) stays off the belt.
/// Mirrors the web workbench's server-side kernel
/// (`mission_control_live_layer` in `dw_pmo/workbench.py`,
/// WLA-15-02) so both clients make the same call from the same
/// correlation document.
/// One rail-event ticker line: `gate_refusal` carries its rule id
/// verbatim — the rails' words, not the app's. Pure and testable;
/// mirrors the web workbench's `mcEvents` renderer (WLA-15-02).
public func formatMCEvent(_ event: MCEvent) -> String {
    let time = event.ts.contains("T")
        ? String(event.ts.split(separator: "T").last ?? "").replacingOccurrences(of: "Z", with: "")
        : event.ts
    let detail = (event.detail ?? [:])
        .compactMap { key, value -> String? in
            switch value {
            case .string(let s): return "\(key)=\(s)"
            case .number(let n): return "\(key)=\(n)"
            case .bool(let b): return "\(key)=\(b)"
            case .null, .array, .object: return nil
            }
        }
        .sorted()
        .joined(separator: " ")
    return [time, event.event, event.story, detail.isEmpty ? nil : detail]
        .compactMap { $0 }
        .joined(separator: "  ")
}

public func pinMissionControlSessions(
    _ sessions: [MCSession]
) -> (pins: [String: [MCSession]], offBelt: [MCSession]) {
    var pins: [String: [MCSession]] = [:]
    var offBelt: [MCSession] = []
    for session in sessions {
        if session.correlation == "on_story", !session.stories.isEmpty {
            for story in session.stories {
                pins[story.storyId, default: []].append(session)
            }
        } else {
            offBelt.append(session)
        }
    }
    return (pins, offBelt)
}
