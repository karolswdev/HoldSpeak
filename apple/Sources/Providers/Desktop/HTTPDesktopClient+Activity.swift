import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import Contracts

// Equilibrium 18-05 — the iPad's activity-nudge client. Until now the device never
// called any `/api/activity/*` route, so the desktop's source-cited pre-briefing
// nudges (and the "Dictate with this" grounding) were absent on mobile. This
// extension closes that gap against the shapes in `holdspeak/web/routes/activity/`:
//
//   GET  /api/activity/nudges               → the cited cards (nudges.py)
//   POST /api/activity/nudges/select        → park a record id for the next dictation
//   POST /api/activity/nudges/{id}/dismiss  → persist a dismissal
//   GET  /api/activity/briefing             → the project digest, when one exists
//
// Self-contained off the internal `config` (the file-private request helpers on the
// base type are not reachable here): each request joins the Bearer token at call
// time and never logs or echoes it (the Phase-61 credential discipline). Decoding
// uses the shared `.convertFromSnakeCase` decoder so the contract types carry no
// hand-written `CodingKeys` for the snake_case mapping.
extension HTTPDesktopClient {

    // MARK: - Activity nudges (Phase 53 → mobile)

    /// `GET /api/activity/nudges` → the top source-cited nudges. Returns `[]` when
    /// activity tracking is off (the desktop engine gates that); a non-2xx throws
    /// `DesktopClientError.http` so the desk surfaces an honest failure.
    public func activityNudges(projectId: String? = nil, limit: Int = 3) async throws -> [ActivityNudge] {
        var path = "api/activity/nudges?limit=\(limit)"
        if let projectId, !projectId.isEmpty,
           let escaped = projectId.addingPercentEncoding(withAllowedCharacters: .urlQueryValueAllowed) {
            path += "&project_id=\(escaped)"
        }
        let data = try await activitySend(activityRequest(path: path))
        do { return try HoldSpeakContracts.decoder().decode(NudgesEnvelope.self, from: data).nudges }
        catch { throw DesktopClientError.malformed }
    }

    /// `POST /api/activity/nudges/select` body `{record_id}` — parks the chosen
    /// record id so the next dictation folds that activity record into its rewrite
    /// context (the "Dictate with this" grounding). `record_id` MUST ride as a JSON
    /// int: the desktop does `int(body.get("record_id"))` and 400s an unknown id.
    public func selectNudge(recordId: Int) async throws {
        _ = try await activitySend(activityJSONRequest(path: "api/activity/nudges/select",
                                                       body: ["record_id": recordId]))
    }

    /// `POST /api/activity/nudges/{id}/dismiss` — persist a dismissal so the same
    /// nudge does not return. `id` is the deterministic `ActivityNudge.key`
    /// (e.g. `record:42` / `window:<iso>`), URL-escaped for the path.
    public func dismissNudge(id: String) async throws {
        let escaped = id.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? id
        _ = try await activitySend(activityRequest(path: "api/activity/nudges/\(escaped)/dismiss",
                                                   method: "POST"))
    }

    /// `GET /api/activity/briefing` → the most-recent project briefing, or `nil` when
    /// the desktop has none (the iPad shows nothing rather than a fabricated digest).
    public func briefing() async throws -> ActivityBriefing? {
        let data = try await activitySend(activityRequest(path: "api/activity/briefing"))
        do { return try HoldSpeakContracts.decoder().decode(BriefingEnvelope.self, from: data).briefing }
        catch { throw DesktopClientError.malformed }
    }

    // MARK: - internals (self-contained; do not touch HTTPDesktopClient.swift)

    struct NudgesEnvelope: Decodable {
        var nudges: [ActivityNudge]
        var activityEnabled: Bool?
    }

    /// The briefing route nests the digest under `briefing` (nullable) alongside a
    /// `last_run` status row the mobile surface does not yet render.
    struct BriefingEnvelope: Decodable {
        var briefing: ActivityBriefing?
    }

    /// Run a request off the internal session, throwing `DesktopClientError.http` on
    /// a non-2xx so the verb methods surface a real failure.
    private func activitySend(_ request: URLRequest) async throws -> Data {
        let (data, response) = try await session.data(for: request)
        if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            throw DesktopClientError.http(http.statusCode)
        }
        return data
    }

    /// A GET/POST with no body, joining the Bearer token off `config` at call time.
    private func activityRequest(path: String, method: String = "GET") -> URLRequest {
        var request = URLRequest(url: activityURL(path: path))
        request.httpMethod = method
        request.timeoutInterval = config.timeout
        if let token = config.token, !token.isEmpty {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        return request
    }

    /// A POST with a JSON body (a real int for `record_id`), Bearer joined off
    /// `config` at call time.
    private func activityJSONRequest(path: String, body: [String: Any]) -> URLRequest {
        var request = URLRequest(url: activityURL(path: path))
        request.httpMethod = "POST"
        request.timeoutInterval = config.timeout
        if let token = config.token, !token.isEmpty {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        return request
    }

    private func activityURL(path: String) -> URL {
        let base = config.baseURL.absoluteString.hasSuffix("/")
            ? String(config.baseURL.absoluteString.dropLast()) : config.baseURL.absoluteString
        return URL(string: "\(base)/\(path)") ?? config.baseURL
    }
}

private extension CharacterSet {
    /// Query-value-safe set: alphanumerics plus the unreserved marks, so a value with
    /// `&`/`=`/`/` is escaped rather than splitting the query.
    static let urlQueryValueAllowed: CharacterSet = {
        var set = CharacterSet.alphanumerics
        set.insert(charactersIn: "-._~")
        return set
    }()
}
