import Foundation

// HSM-21-04 — the hub's posture snapshot (`GET /api/setup/status`, HS-42-01), the
// slice the ambient trust chip needs. Wire keys arrive snake_case and convert via the
// shared decoder (`.convertFromSnakeCase`); every field is optional (robust-decode
// posture — the route carries more than the chip reads, and the payload evolves).

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

    public init(webBind: String? = nil, authTokenSet: Bool? = nil,
                transcriptEgress: String? = nil, actuatorsEnabled: Bool? = nil) {
        self.webBind = webBind
        self.authTokenSet = authTokenSet
        self.transcriptEgress = transcriptEgress
        self.actuatorsEnabled = actuatorsEnabled
    }
}

/// The setup-status envelope (the chip's slice; `sections`/`presence` are not carried).
public struct SetupStatus: Codable, Equatable, Sendable {
    public var version: String?
    /// "ready" | "attention" | … — the doctor rollup.
    public var overall: String?
    public var firstRun: Bool?
    public var trust: SetupTrust?

    public init(version: String? = nil, overall: String? = nil,
                firstRun: Bool? = nil, trust: SetupTrust? = nil) {
        self.version = version
        self.overall = overall
        self.firstRun = firstRun
        self.trust = trust
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
