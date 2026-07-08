import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import Contracts

// HSM-26-03 — the consent spine on the wire (Phase 87). The iPad attaches to a
// live session (peek, read-only), arms it (a grant that pins the pane's %N and
// counts down), and steers it (voice-first, audited). The refusals are
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

extension HTTPDesktopClient {

    /// `GET /api/coders/{key}/peek` — the read-only window into a session's pane.
    /// Watching is free: no grant, no keystroke. `lastHash` rides the content
    /// gate (an unchanged pane answers `not_modified`, no body).
    public func coderPeek(key: String, lines: Int = 200, lastHash: String? = nil) async throws -> CoderSessionPeek {
        var path = "api/coders/\(encoded(key))/peek?lines=\(lines)"
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
    public func armCoder(key: String, ttlSeconds: Int? = nil) async throws -> CoderArmResult {
        let body: [String: Any] = ttlSeconds.map { ["ttl_seconds": $0] } ?? [:]
        let data = try await sendSteerAllowing409(makeSteerRequest(path: "api/coders/\(encoded(key))/arm", method: "POST", jsonBody: body))
        guard let res = try? HoldSpeakContracts.decoder().decode(CoderArmResult.self, from: data) else {
            throw DesktopClientError.malformed
        }
        return res
    }

    /// `POST /api/coders/{key}/disarm` — one tap, immediate, idempotent.
    public func disarmCoder(key: String) async throws -> CoderDisarmResult {
        let data = try await sendSteer(makeSteerRequest(path: "api/coders/\(encoded(key))/disarm", method: "POST", jsonBody: [:]))
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
                           grounding: [RailsGroundingRef]? = nil) async throws -> SteerResult {
        var body: [String: Any] = ["text": text, "submit": submit]
        if let g = grounding, !g.isEmpty {
            body["grounding"] = ["rails": g.map { ["repo": $0.repo, "project": $0.project, "kind": $0.kind, "id": $0.id] }]
        }
        let data = try await sendSteerAllowing409(makeSteerRequest(path: "api/coders/\(encoded(key))/steer", method: "POST", jsonBody: body))
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

    // MARK: - internals

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
