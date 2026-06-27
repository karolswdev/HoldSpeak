import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import Contracts

// HSM client layer — Meeting Aftercare (HS-49 surface over the desktop's existing
// HTTP API). Two read/close-the-loop verbs on the desktop client seam:
//
//   - aftercare(meetingId:)            GET  /api/meetings/{id}/aftercare
//   - fileAftercareIssue(...)          POST /api/meetings/{id}/aftercare/file-issue
//
// New extension file by design (the equilibrium-wave conflict rule): no edits to
// HTTPDesktopClient.swift or the shared seam. Reuses `self.config` (baseURL +
// Bearer token) and the same request/decode posture as the rest of the client —
// a non-2xx throws `DesktopClientError.http`; a decode miss throws `.malformed`.
extension HTTPDesktopClient {

    /// `GET /api/meetings/{id}/aftercare` → the read-only aftercare digest: what's
    /// still open (by owner), what was decided, and the real diff vs the previous
    /// meeting. Pure read, no side effects. `Aftercare.isEmpty` is the caller's cue
    /// to stay quiet. A non-2xx (e.g. 404 unknown meeting) throws `.http(code)`.
    public func aftercare(meetingId: String) async throws -> Aftercare {
        let encoded = meetingId.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? meetingId
        let data = try await sendAftercare(makeAftercareRequest(path: "api/meetings/\(encoded)/aftercare"))
        do { return try HoldSpeakContracts.decoder().decode(Aftercare.self, from: data) }
        catch { throw DesktopClientError.malformed }
    }

    /// `POST /api/meetings/{id}/aftercare/file-issue` body `{action_item_id, repo}` →
    /// an actuator *proposal* (proposed state) plus its human preview. Nothing leaves
    /// the machine here: filing only records a proposal that the user must separately
    /// approve (and actuators must be enabled). The route requires the target `repo`
    /// ("owner/name") and that the action item already be `accepted`, so a 400 here
    /// throws `.http(400)` and the caller surfaces the honest reason.
    @discardableResult
    public func fileAftercareIssue(
        meetingId: String, actionItemId: String, repo: String
    ) async throws -> AftercareFileIssueResult {
        let encoded = meetingId.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? meetingId
        let request = makeAftercareRequest(
            path: "api/meetings/\(encoded)/aftercare/file-issue",
            method: "POST",
            jsonBody: ["action_item_id": actionItemId, "repo": repo])
        let data = try await sendAftercare(request)
        do { return try HoldSpeakContracts.decoder().decode(AftercareFileIssueResult.self, from: data) }
        catch { throw DesktopClientError.malformed }
    }

    // MARK: - internals (private to this extension — no dependency on the seam's
    //         own private helpers, per the conflict rule; the request shape mirrors
    //         HTTPDesktopClient.makeRequest / send exactly).

    /// Run a request, throwing `DesktopClientError.http` on a non-2xx so the verbs
    /// surface a real failure the view-model can render.
    private func sendAftercare(_ request: URLRequest) async throws -> Data {
        let (data, response) = try await session.data(for: request)
        if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            throw DesktopClientError.http(http.statusCode)
        }
        return data
    }

    private func makeAftercareRequest(
        path: String, method: String = "GET", jsonBody: [String: String]? = nil
    ) -> URLRequest {
        let base = config.baseURL.absoluteString.hasSuffix("/")
            ? String(config.baseURL.absoluteString.dropLast()) : config.baseURL.absoluteString
        var request = URLRequest(url: URL(string: "\(base)/\(path)") ?? config.baseURL)
        request.httpMethod = method
        request.timeoutInterval = config.timeout
        if let token = config.token, !token.isEmpty {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        if let jsonBody {
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try? JSONSerialization.data(withJSONObject: jsonBody)
        }
        return request
    }
}
