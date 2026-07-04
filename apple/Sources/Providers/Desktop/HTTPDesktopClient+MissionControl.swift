import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import Contracts

// HSM-25-01 — the client extension for the backend's mission-control
// endpoints (its Phase 82: /api/missioncontrol/state|sessions|events).
// Same idiom as +Activity: self-contained request/send helpers that
// join the owner Bearer token off `config` at call time (the
// Phase-61 credential discipline — the token is never logged or
// echoed). A non-2xx throws `DesktopClientError.http` so the
// conveyor renders an honest failure; the owner-only 401/403 is a
// first-class rendered state upstream, not a crash.

extension HTTPDesktopClient {

    /// `GET /api/missioncontrol/state` → per-repo roadmap feed.
    public func missionControlState() async throws -> MCStatePayload {
        let data = try await mcSend(mcRequest(path: "api/missioncontrol/state"))
        do { return try HoldSpeakContracts.decoder().decode(MCStatePayload.self, from: data) }
        catch { throw DesktopClientError.malformed }
    }

    /// `GET /api/missioncontrol/sessions` → the correlation document.
    public func missionControlSessions() async throws -> MCSessionsPayload {
        let data = try await mcSend(mcRequest(path: "api/missioncontrol/sessions"))
        do { return try HoldSpeakContracts.decoder().decode(MCSessionsPayload.self, from: data) }
        catch { throw DesktopClientError.malformed }
    }

    /// `GET /api/missioncontrol/events?tail=N` → recent rail events.
    public func missionControlEvents(tail: Int = 20) async throws -> MCEventsPayload {
        let data = try await mcSend(mcRequest(path: "api/missioncontrol/events?tail=\(tail)"))
        do { return try HoldSpeakContracts.decoder().decode(MCEventsPayload.self, from: data) }
        catch { throw DesktopClientError.malformed }
    }

    // -- helpers (mirrors +Activity; core send/makeRequest are file-private) --

    private func mcSend(_ request: URLRequest) async throws -> Data {
        let (data, response) = try await session.data(for: request)
        if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            throw DesktopClientError.http(http.statusCode)
        }
        return data
    }

    private func mcRequest(path: String, method: String = "GET") -> URLRequest {
        var request = URLRequest(url: mcURL(path: path))
        request.httpMethod = method
        request.timeoutInterval = config.timeout
        if let token = config.token, !token.isEmpty {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        return request
    }

    private func mcURL(path: String) -> URL {
        let base = config.baseURL.absoluteString.hasSuffix("/")
            ? String(config.baseURL.absoluteString.dropLast())
            : config.baseURL.absoluteString
        return URL(string: "\(base)/\(path)") ?? config.baseURL
    }
}
