import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import Contracts

// EQ-W3 (iOS artifacts) — the read client for a meeting's synthesized artifacts.
// Additive extension on `HTTPDesktopClient`; lives in its own file so this slice
// never touches the shared client (siblings + the integrator add their own verbs).
//
// Why this exists: the iPad currently renders meeting artifacts WITHOUT their
// `confidence` or `sources` (the provenance the desk should show). This method
// returns `[MeetingArtifact]`, which carries both — so the SwiftUI screen the
// integrator builds can finally show how confident the synthesis was and what it
// was grounded in.

extension HTTPDesktopClient {

    /// `GET /api/meetings/{meetingId}/artifacts` → the meeting's synthesized
    /// artifacts (each with `confidence` + `sources` provenance). Reuses
    /// `self.config` (baseURL + Bearer token + timeout); a non-2xx throws
    /// `DesktopClientError.http`, a shape mismatch throws `.malformed`, so the
    /// view-model surfaces an honest failure rather than a silently empty list.
    public func meetingArtifacts(meetingId: String) async throws -> [MeetingArtifact] {
        let request = artifactsRequest(meetingId: meetingId)

        let (data, response) = try await session.data(for: request)
        if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            throw DesktopClientError.http(http.statusCode)
        }
        do {
            return try HoldSpeakContracts.decoder()
                .decode(MeetingArtifactsEnvelope.self, from: data)
                .artifacts
        } catch {
            throw DesktopClientError.malformed
        }
    }

    /// Build the artifacts GET request inline (no dependency on the shared client's
    /// private helpers, per the no-shared-edits rule), mirroring the Bearer-auth
    /// request pattern in HTTPDesktopClient.swift. `meetingId` is path-escaped so an
    /// id with reserved characters never produces a junk URL.
    private func artifactsRequest(meetingId: String) -> URLRequest {
        let absolute = config.baseURL.absoluteString
        let base = absolute.hasSuffix("/") ? String(absolute.dropLast()) : absolute
        let escapedID = meetingId.addingPercentEncoding(
            withAllowedCharacters: .urlPathAllowed) ?? meetingId
        let url = URL(string: "\(base)/api/meetings/\(escapedID)/artifacts") ?? config.baseURL

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.timeoutInterval = config.timeout
        if let token = config.token, !token.isEmpty {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        return request
    }
}
