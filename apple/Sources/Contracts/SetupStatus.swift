import Foundation

// HSM-21-04 — the hub's posture snapshot (`GET /api/setup/status`, HS-42-01), the
// slice the ambient trust chip needs. Wire keys arrive snake_case and convert via the
// shared decoder (`.convertFromSnakeCase`); every field is optional (robust-decode
// posture — the route carries more than the chip reads, and the payload evolves).

/// One row from the hub's canonical destination/operation trust registry.
public struct TrustDestination: Codable, Equatable, Sendable {
    public var id: String?
    public var name: String?
    public var operation: String?
    public var enabled: Bool?
    public var destination: String?
    public var boundary: String?
    public var dataClass: String?
    public var authorityBasis: String?
    public var backgroundAbility: String?
    public var revokeAction: String?
    public var lastReceipt: String?

    public init(id: String? = nil, name: String? = nil, operation: String? = nil,
                enabled: Bool? = nil,
                destination: String? = nil, boundary: String? = nil,
                dataClass: String? = nil, authorityBasis: String? = nil,
                backgroundAbility: String? = nil, revokeAction: String? = nil,
                lastReceipt: String? = nil) {
        self.id = id; self.name = name; self.operation = operation; self.enabled = enabled
        self.destination = destination; self.boundary = boundary
        self.dataClass = dataClass; self.authorityBasis = authorityBasis
        self.backgroundAbility = backgroundAbility; self.revokeAction = revokeAction
        self.lastReceipt = lastReceipt
    }
}

/// The `trust` block: what can leave the machine right now, from config (display only).
public struct SetupTrust: Codable, Equatable, Sendable {
    /// The web bind address ("127.0.0.1" loopback, or an off-loopback bind).
    public var webBind: String?
    /// Whether a web auth token is set (off-loopback without one is the danger posture).
    public var authTokenSet: Bool?
    /// "none" | "configured" | "possible" — whether a transcript can leave.
    public var transcriptEgress: String?
    /// Whether actuators (external writes, still per-action approved) are enabled.
    public var actuatorsEnabled: Bool?
    public var destinations: [TrustDestination]?
    public var summary: String?

    public init(webBind: String? = nil, authTokenSet: Bool? = nil,
                transcriptEgress: String? = nil, actuatorsEnabled: Bool? = nil,
                destinations: [TrustDestination]? = nil, summary: String? = nil) {
        self.webBind = webBind
        self.authTokenSet = authTokenSet
        self.transcriptEgress = transcriptEgress
        self.actuatorsEnabled = actuatorsEnabled
        self.destinations = destinations
        self.summary = summary
    }
}

/// One doctor check off the hub's `sections` block (HSM-23-03 — the readiness panel
/// reads the whole doctor, not just the trust slice). Wire: `{id, label, status,
/// detail, fix}`; `status` is "pass" | "warn" | "fail" | "unknown" (setup_status.py
/// `_section_from_check`). Every field optional (robust-decode posture).
public struct SetupSection: Codable, Equatable, Sendable {
    public var id: String?
    public var label: String?
    public var status: String?
    public var detail: String?

    public init(id: String? = nil, label: String? = nil,
                status: String? = nil, detail: String? = nil) {
        self.id = id
        self.label = label
        self.status = status
        self.detail = detail
    }
}

/// The setup-status envelope (`presence`/`primary_action` are not carried).
public struct SetupStatus: Codable, Equatable, Sendable {
    public var version: String?
    /// "ready" | "needs_attention" | "blocked" — the doctor rollup.
    public var overall: String?
    public var firstRun: Bool?
    public var trust: SetupTrust?
    /// The hub's per-check doctor sections (HSM-23-03; absent on older hubs).
    public var sections: [SetupSection]?

    public init(version: String? = nil, overall: String? = nil,
                firstRun: Bool? = nil, trust: SetupTrust? = nil,
                sections: [SetupSection]? = nil) {
        self.version = version
        self.overall = overall
        self.firstRun = firstRun
        self.trust = trust
        self.sections = sections
    }

    /// The four-posture mapping the web chip uses (`trust-view.js trustPosture`) — the
    /// SAME order, so both surfaces state the same truth:
    /// attention (off-loopback, no token) → writes (actuators on) → endpoint
    /// (a transcript can leave) → local.
    public var posture: TrustPosture {
        let t = trust ?? SetupTrust()
        let bind = (t.webBind ?? "127.0.0.1")
        let loopback = bind.isEmpty || bind == "127.0.0.1" || bind == "localhost" || bind == "::1"
        if !loopback && !(t.authTokenSet ?? false) { return .attention }
        if t.actuatorsEnabled ?? false { return .writesNeedApproval }
        if let egress = t.transcriptEgress, egress != "none" { return .configuredEndpoint }
        return .localOnly
    }
}

/// The chip's four postures, one label each (labels, never sentences).
public enum TrustPosture: Equatable, Sendable {
    case attention
    case writesNeedApproval
    case configuredEndpoint
    case localOnly

    public var label: String {
        switch self {
        case .attention: return "Needs attention"
        case .writesNeedApproval: return "Writes need approval"
        case .configuredEndpoint: return "Configured endpoint"
        case .localOnly: return "Local only"
        }
    }
}
