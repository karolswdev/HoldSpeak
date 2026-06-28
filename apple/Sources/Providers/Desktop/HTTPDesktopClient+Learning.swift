import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import Contracts

// HSM client layer — the dictation learning loop, READ side (Phase 19-06). Two
// read-only verbs over the desktop hub's existing HTTP API:
//
//   - journalEntries(limit:source:)  GET /api/dictation/journal          → JournalResponse
//   - learningDigest(window:)        GET /api/dictation/learning-digest  → LearningDigest
//
// Read-only by design: the iPad does NOT journal on-device and does NOT write
// corrections here — that's Phase 9. The hub's POST/DELETE/correct routes are not
// surfaced on this seam.
//
// New extension file by design (the equilibrium-wave conflict rule): no edits to
// HTTPDesktopClient.swift or any shared file. Reuses `self.config` (baseURL + Bearer
// token) and the same request/decode posture as the rest of the client — a non-2xx
// throws `DesktopClientError.http`; a decode miss throws `.malformed`.
extension HTTPDesktopClient {

    /// `GET /api/dictation/journal?limit=&source=` → the dictation journal newest-first
    /// plus the local-only trust facts (enabled / retention / true count). Pure read,
    /// no side effects. On a bare server (no durable journal) `items` is empty and
    /// `count` is 0 — never an error. A non-2xx throws `.http(code)`.
    ///
    /// - Parameters:
    ///   - limit: max entries to return (hub default 200).
    ///   - source: filter to "dictation" or "dry_run"; anything else the hub treats as
    ///             "no filter". `nil` returns all sources.
    public func journalEntries(limit: Int = 200, source: String? = nil) async throws -> JournalResponse {
        var query = "limit=\(limit)"
        if let source, !source.isEmpty {
            let encoded = source.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? source
            query += "&source=\(encoded)"
        }
        let data = try await sendLearning(makeLearningRequest(path: "api/dictation/journal?\(query)"))
        do { return try HoldSpeakContracts.decoder().decode(JournalResponse.self, from: data) }
        catch { throw DesktopClientError.malformed }
    }

    /// `GET /api/dictation/learning-digest?window=` → the windowed "what HoldSpeak
    /// learned" digest (corrections made, dictations corrected, by-kind/block/target
    /// breakdowns, per-correction whole-journal reach). Pure read. The hub coerces an
    /// unknown window to "week", so this always decodes to a digest on a 2xx; a non-2xx
    /// throws `.http(code)`.
    ///
    /// - Parameter window: "week" (last 7 days) or "all".
    public func learningDigest(window: String = "week") async throws -> LearningDigest {
        let encoded = window.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? window
        let data = try await sendLearning(makeLearningRequest(path: "api/dictation/learning-digest?window=\(encoded)"))
        do { return try HoldSpeakContracts.decoder().decode(LearningDigest.self, from: data) }
        catch { throw DesktopClientError.malformed }
    }

    // MARK: - internals (private to this extension — no dependency on the seam's own
    //         private helpers, per the conflict rule; the request shape mirrors
    //         HTTPDesktopClient.makeRequest / send exactly).

    /// Run a request, throwing `DesktopClientError.http` on a non-2xx so the verbs
    /// surface a real failure the view-model can render.
    private func sendLearning(_ request: URLRequest) async throws -> Data {
        let (data, response) = try await session.data(for: request)
        if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            throw DesktopClientError.http(http.statusCode)
        }
        return data
    }

    private func makeLearningRequest(path: String) -> URLRequest {
        let base = config.baseURL.absoluteString.hasSuffix("/")
            ? String(config.baseURL.absoluteString.dropLast()) : config.baseURL.absoluteString
        var request = URLRequest(url: URL(string: "\(base)/\(path)") ?? config.baseURL)
        request.httpMethod = "GET"
        request.timeoutInterval = config.timeout
        if let token = config.token, !token.isEmpty {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        return request
    }
}
