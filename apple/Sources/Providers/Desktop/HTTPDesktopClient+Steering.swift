import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import Contracts

// HSM-26-03 — the consent spine on the wire (Phase 87). The iPad attaches to a
// live session (peek, read-only), consumes the Hub's policy decision, and
// steers it (voice-first, audited). Secure/Normal may arm a bounded grant;
// YOLO binds the expected registered pane id without an arm prompt. Refusals are
// first-class DATA, not errors: an unarmed or recycled-pane steer comes back as
// a typed SteerResult (a 409 body), so the surface re-offers ARM from the shape
// alone — never a thrown toast. Own request helpers (the +Ask precedent).

/// Arm's outcome: the grant on success, or a typed refusal (stale session /
/// no pane / the pane cannot prove itself). A loose Provider-layer result so
/// both the 200 and the 409 body decode into one thing the surface reads.
public struct CoderArmResult: Codable, Equatable, Sendable {
    public var status: String            // "armed" | stale_session | no_pane | pane_gone | ...
    public var key: String?
    public var paneId: String?
    public var expiresInSeconds: Int?
    public var detail: String?
    public var isArmed: Bool { status == "armed" }
    public init(status: String, key: String? = nil, paneId: String? = nil,
                expiresInSeconds: Int? = nil, detail: String? = nil) {
        self.status = status; self.key = key; self.paneId = paneId
        self.expiresInSeconds = expiresInSeconds; self.detail = detail
    }
}

public struct CoderDisarmResult: Codable, Equatable, Sendable {
    public var status: String
    public var key: String
    public var wasArmed: Bool
}

// --- Phase-89/90 parity (the iPad catches up to the web desk) ---------------

/// A key in a `/keys` sequence: a NAMED tmux key (`C-c`, `Up`, `Escape`) or a
/// LITERAL run. Matches the hub's body — a bare string for a named key, a
/// `{ "literal": "…" }` object for a literal.
public enum SteerKey: Equatable, Sendable {
    case named(String)
    case literal(String)
    var wire: Any {
        switch self {
        case .named(let k): return k
        case .literal(let t): return ["literal": t]
        }
    }
    public static let interrupt = SteerKey.named("C-c")
    public static let escape = SteerKey.named("Escape")
    public static let enter = SteerKey.named("Enter")
    public static let up = SteerKey.named("Up")
    public static let down = SteerKey.named("Down")
    public static let left = SteerKey.named("Left")
    public static let right = SteerKey.named("Right")
}

/// A tmux pane from `GET /api/coders/steering/panes` — attach to ANY of them.
public struct PaneInfo: Codable, Equatable, Sendable {
    // No explicit CodingKeys: the shared decoder converts snake_case
    // (pane_id → paneId), matching the CoderArmResult precedent.
    public var paneId: String
    public var session: String
    public var window: String?
    public var command: String?
    public var title: String?
    public var active: Bool?
    public init(paneId: String, session: String, window: String? = nil,
                command: String? = nil, title: String? = nil, active: Bool? = nil) {
        self.paneId = paneId; self.session = session; self.window = window
        self.command = command; self.title = title; self.active = active
    }
}

/// The outcome of ending a pane/session (`POST /{key}/kill`). A refusal is
/// DATA (a 409 body): an unarmed or recycled-pane kill decodes here, and a
/// revoking refusal sets `revoked` so the surface re-offers ARM.
public struct CoderKillResult: Codable, Equatable, Sendable {
    public var status: String            // "killed" | unarmed | pane_mismatch | pane_gone | ...
    public var paneId: String?
    public var scope: String?
    public var revoked: Bool?
    public var detail: String?
    public var isKilled: Bool { status == "killed" }
    public var didRevoke: Bool { revoked == true }
}

/// The outcome of a factory create/label act (`POST /factory/{spawn,rename}`).
/// A bad name / duplicate is DATA (a 409 body).
public struct FactoryResult: Codable, Equatable, Sendable {
    public var status: String            // "spawned" | "renamed" | bad_name | exists | ...
    public var session: String?
    public var paneId: String?
    public var detail: String?
    public var isOk: Bool { status == "spawned" || status == "renamed" }
    /// The `pane:%N` key of a just-spawned session, ready to attach to.
    public var paneKey: String? { paneId.map { "pane:\($0)" } }
}

extension HTTPDesktopClient {

    /// `GET /api/coders/{key}/peek` — the read-only window into a session's pane.
    /// Watching is free: no grant, no keystroke. `lastHash` rides the content
    /// gate (an unchanged pane answers `not_modified`, no body).
    public func coderPeek(key: String, lines: Int = 200, lastHash: String? = nil, node: String? = nil) async throws -> CoderSessionPeek {
        var path: String
        if let n = node, !n.isEmpty {
            path = "api/coders/relay/\(encoded(n))/peek?key=\(encoded(key))&lines=\(lines)"
        } else {
            path = "api/coders/\(encoded(key))/peek?lines=\(lines)"
        }
        if let h = lastHash, !h.isEmpty { path += "&last_hash=\(encoded(h))" }
        let data = try await sendSteer(makeSteerRequest(path: path, method: "GET"))
        guard let peek = try? HoldSpeakContracts.decoder().decode(CoderSessionPeek.self, from: data) else {
            throw DesktopClientError.malformed
        }
        return peek
    }

    /// `POST /api/coders/{key}/arm` — earn the grant. 200 → armed; 409 → a typed
    /// refusal (both decode into CoderArmResult). Pins the pane's %N and starts
    /// the countdown.
    public func armCoder(key: String, ttlSeconds: Int? = nil, node: String? = nil) async throws -> CoderArmResult {
        let (path, keyInBody) = steerVerb(node: node, key: key, verb: "arm")
        var body: [String: Any] = ttlSeconds.map { ["ttl_seconds": $0] } ?? [:]
        if keyInBody { body["key"] = key }
        let data = try await sendSteerAllowing409(makeSteerRequest(path: path, method: "POST", jsonBody: body))
        guard let res = try? HoldSpeakContracts.decoder().decode(CoderArmResult.self, from: data) else {
            throw DesktopClientError.malformed
        }
        return res
    }

    /// `POST /api/coders/{key}/disarm` — one tap, immediate, idempotent. A
    /// `node` routes through the relay (`POST /api/coders/relay/{node}/disarm`,
    /// key in the BODY) exactly like the other verbs — the Phase-94 audit
    /// found the local-only route left a remote-armed grant alive after a
    /// native disarm; the disarm MUST land on the session's own node.
    public func disarmCoder(key: String, node: String? = nil) async throws -> CoderDisarmResult {
        let (path, keyInBody) = steerVerb(node: node, key: key, verb: "disarm")
        var body: [String: Any] = [:]
        if keyInBody { body["key"] = key }
        let data = try await sendSteer(makeSteerRequest(path: path, method: "POST", jsonBody: body))
        guard let res = try? HoldSpeakContracts.decoder().decode(CoderDisarmResult.self, from: data) else {
            throw DesktopClientError.malformed
        }
        return res
    }

    /// `POST /api/coders/{key}/steer` — deliver one steer through the chokepoint.
    /// 200 → delivered; 409 → a typed refusal (both decode into SteerResult). A
    /// revoking refusal (recycled pane / expiry) sets `revoked` so the surface
    /// re-offers ARM.
    public func steerCoder(key: String, text: String, submit: Bool = true,
                           expectedPaneId: String? = nil,
                           grounding: [RailsGroundingRef]? = nil, node: String? = nil) async throws -> SteerResult {
        let (path, keyInBody) = steerVerb(node: node, key: key, verb: "steer")
        var body: [String: Any] = ["text": text, "submit": submit]
        if keyInBody { body["key"] = key }
        if let expectedPaneId, !expectedPaneId.isEmpty {
            body["expected_pane_id"] = expectedPaneId
        }
        if let g = grounding, !g.isEmpty {
            body["grounding"] = ["rails": g.map { ["repo": $0.repo, "project": $0.project, "kind": $0.kind, "id": $0.id] }]
        }
        let data = try await sendSteerAllowing409(makeSteerRequest(path: path, method: "POST", jsonBody: body))
        guard let res = try? HoldSpeakContracts.decoder().decode(SteerResult.self, from: data) else {
            throw DesktopClientError.malformed
        }
        return res
    }

    /// `GET /api/coders/steering/audit` — the steer trail (hash + head only).
    public func steeringAudit(sessionKey: String? = nil, limit: Int = 50) async throws -> [SteeringAuditEntry] {
        var path = "api/coders/steering/audit?limit=\(limit)"
        if let k = sessionKey, !k.isEmpty { path += "&session_key=\(encoded(k))" }
        let data = try await sendSteer(makeSteerRequest(path: path, method: "GET"))
        guard let dto = try? HoldSpeakContracts.decoder().decode(AuditDTO.self, from: data) else {
            throw DesktopClientError.malformed
        }
        return dto.audit ?? []
    }

    struct AuditDTO: Decodable { var audit: [SteeringAuditEntry]? }

    // MARK: - Phase-89/90 parity

    /// `POST /api/coders/{key}/keys` — full key control (HS-89-01). Send real
    /// keys (`.interrupt`, arrows, `.escape`) through the chokepoint. 200 →
    /// delivered; 409 → a typed refusal (a revoking one re-offers ARM). A
    /// `node` routes through the relay (HS-89-03).
    public func coderKeys(key: String, keys: [SteerKey],
                          expectedPaneId: String? = nil,
                          node: String? = nil) async throws -> SteerResult {
        let (path, keyInBody) = steerVerb(node: node, key: key, verb: "keys")
        var body: [String: Any] = ["keys": keys.map { $0.wire }]
        if keyInBody { body["key"] = key }
        if let expectedPaneId, !expectedPaneId.isEmpty {
            body["expected_pane_id"] = expectedPaneId
        }
        let data = try await sendSteerAllowing409(makeSteerRequest(path: path, method: "POST", jsonBody: body))
        guard let res = try? HoldSpeakContracts.decoder().decode(SteerResult.self, from: data) else {
            throw DesktopClientError.malformed
        }
        return res
    }

    /// `GET /api/coders/steering/panes` — every tmux pane on the machine
    /// (HS-89-02). Watch any free; arm one by its `pane:%N` key to steer it.
    public func steeringPanes() async throws -> [PaneInfo] {
        let data = try await sendSteer(makeSteerRequest(path: "api/coders/steering/panes", method: "GET"))
        guard let dto = try? HoldSpeakContracts.decoder().decode(PanesDTO.self, from: data) else {
            throw DesktopClientError.malformed
        }
        return dto.panes ?? []
    }

    /// `GET /api/coders/steering/nodes` — the configured steering nodes, NAMES
    /// ONLY (HS-90-02). Empty means "this Mac only".
    public func steeringNodes() async throws -> [String] {
        let data = try await sendSteer(makeSteerRequest(path: "api/coders/steering/nodes", method: "GET"))
        guard let dto = try? HoldSpeakContracts.decoder().decode(NodesDTO.self, from: data) else {
            throw DesktopClientError.malformed
        }
        return dto.nodes ?? []
    }

    /// `POST /api/coders/{key}/kill` — end the armed pane (`scope: "pane"`) or
    /// its session (`scope: "session"`) (HS-90-01). The ultimate manipulation,
    /// gated like a steer; a refusal is DATA. Local only, like the web desk.
    public func killCoder(key: String, scope: String = "pane") async throws -> CoderKillResult {
        let data = try await sendSteerAllowing409(makeSteerRequest(path: "api/coders/\(encoded(key))/kill", method: "POST", jsonBody: ["scope": scope]))
        guard let res = try? HoldSpeakContracts.decoder().decode(CoderKillResult.self, from: data) else {
            throw DesktopClientError.malformed
        }
        return res
    }

    /// `POST /api/coders/factory/spawn` — create a detached session (HS-90-01).
    /// The name is validated hub-side; a bad name is a 409 `bad_name`. On
    /// success `paneKey` is the `pane:%N` to attach to.
    public func spawnSession(name: String, command: String? = nil) async throws -> FactoryResult {
        var body: [String: Any] = ["name": name]
        if let c = command, !c.isEmpty { body["command"] = c }
        let data = try await sendSteerAllowing409(makeSteerRequest(path: "api/coders/factory/spawn", method: "POST", jsonBody: body))
        guard let res = try? HoldSpeakContracts.decoder().decode(FactoryResult.self, from: data) else {
            throw DesktopClientError.malformed
        }
        return res
    }

    /// `POST /api/coders/factory/rename` — relabel a session (HS-90-01).
    public func renameSession(target: String, name: String) async throws -> FactoryResult {
        let data = try await sendSteerAllowing409(makeSteerRequest(path: "api/coders/factory/rename", method: "POST", jsonBody: ["target": target, "name": name]))
        guard let res = try? HoldSpeakContracts.decoder().decode(FactoryResult.self, from: data) else {
            throw DesktopClientError.malformed
        }
        return res
    }

    struct PanesDTO: Decodable { var panes: [PaneInfo]? }
    struct NodesDTO: Decodable { var nodes: [String]? }

    // MARK: - internals

    /// Node-aware path (HS-89-03 / HS-90-02): a targeted node routes through
    /// the relay with the key in the BODY; "this Mac" hits the pane's own
    /// route with the key in the PATH.
    private func steerVerb(node: String?, key: String, verb: String) -> (path: String, keyInBody: Bool) {
        if let n = node, !n.isEmpty {
            return ("api/coders/relay/\(encoded(n))/\(verb)", true)
        }
        return ("api/coders/\(encoded(key))/\(verb)", false)
    }

    private func encoded(_ s: String) -> String {
        s.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? s
    }

    private func sendSteer(_ request: URLRequest) async throws -> Data {
        let (data, response) = try await session.data(for: request)
        if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            throw DesktopClientError.http(http.statusCode)
        }
        return data
    }

    /// Like `sendSteer`, but a 409 is DATA (a typed refusal), not an error —
    /// the consent grammar: an unarmed/recycled steer is a first-class result.
    private func sendSteerAllowing409(_ request: URLRequest) async throws -> Data {
        let (data, response) = try await session.data(for: request)
        if let http = response as? HTTPURLResponse,
           !(200...299).contains(http.statusCode), http.statusCode != 409 {
            throw DesktopClientError.http(http.statusCode)
        }
        return data
    }

    private func makeSteerRequest(path: String, method: String, jsonBody: [String: Any]? = nil) -> URLRequest {
        let base = config.baseURL.absoluteString.hasSuffix("/")
            ? String(config.baseURL.absoluteString.dropLast()) : config.baseURL.absoluteString
        var request = URLRequest(url: URL(string: "\(base)/\(path)") ?? config.baseURL)
        request.httpMethod = method
        request.timeoutInterval = config.timeout
        if let token = config.token, !token.isEmpty {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        if let body = jsonBody {
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        }
        return request
    }
}
