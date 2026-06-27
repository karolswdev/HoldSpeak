import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import Contracts

// HSM equilibrium wave 3 — the propose→review→approve client slice. The iPad today
// collapses "generate a proposal" and "approve it"; the desktop already keeps them
// apart (actuator audit). These two methods give the iPad the SPLIT:
//
//   • `meetingProposals(meetingId:)` — a pure read of the proposals queued for
//     review (`GET /api/meetings/{id}/proposals`). No side effect.
//   • `decideProposal(meetingId:proposalId:approved:)` — the separate human gate
//     (`POST /api/meetings/{id}/proposals/{pid}/decision`). Approving only flips DB
//     state for most targets; a `slack` target executes immediately (the hub's
//     consent model) — either way the transitioned proposal rides back.
//
// New file by design: no edit to HTTPDesktopClient.swift / IDesktopClient (siblings
// add their own methods on the same type). The request/decode style is copied from
// HTTPDesktopClient.swift (Bearer auth, shared decoder, throw on non-2xx) but built
// inline here so it depends on no private helper.
extension HTTPDesktopClient {

    // MARK: - Proposals: review (HSM equilibrium wave 3)

    /// `GET /api/meetings/{meetingId}/proposals` → the review queue. A pure read —
    /// viewing a proposal performs no side effect on the hub. Throws
    /// `DesktopClientError.http` on a non-2xx (e.g. 404 unknown meeting) and
    /// `.malformed` if the envelope can't be decoded.
    public func meetingProposals(meetingId: String) async throws -> [MeetingProposal] {
        let request = proposalsRequest(
            path: "api/meetings/\(escape(meetingId))/proposals", method: "GET")
        let data = try await proposalsSend(request)
        do {
            return try HoldSpeakContracts.decoder()
                .decode(MeetingProposalsEnvelope.self, from: data).proposals
        } catch {
            throw DesktopClientError.malformed
        }
    }

    /// `POST /api/meetings/{meetingId}/proposals/{proposalId}/decision` with body
    /// `{ "decision": "approved"|"rejected" }`. `approved` maps to the hub's two legal
    /// strings; the route rejects anything else. Returns the decision envelope
    /// (`success` + the transitioned `proposal`, or `error` on an illegal transition
    /// such as deciding an already-executed proposal). A non-2xx (404 unknown
    /// proposal, 400 illegal decision) throws `DesktopClientError.http`.
    public func decideProposal(
        meetingId: String, proposalId: String, approved: Bool
    ) async throws -> ProposalDecision {
        let body = ["decision": approved ? "approved" : "rejected"]
        let request = proposalsRequest(
            path: "api/meetings/\(escape(meetingId))/proposals/\(escape(proposalId))/decision",
            method: "POST", jsonBody: body)
        let data = try await proposalsSend(request)
        do {
            return try HoldSpeakContracts.decoder().decode(ProposalDecision.self, from: data)
        } catch {
            throw DesktopClientError.malformed
        }
    }

    // MARK: - internals (self-contained; no dependency on private helpers)

    /// Percent-encode a path segment so an id with reserved characters can't break
    /// the URL. Falls back to the raw value if encoding somehow fails.
    private func escape(_ segment: String) -> String {
        segment.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? segment
    }

    /// Run a request against the hub, throwing `DesktopClientError.http` on a non-2xx
    /// so the review view-model can render an honest failure (mirrors the
    /// `send(_:)` discipline in HTTPDesktopClient.swift).
    private func proposalsSend(_ request: URLRequest) async throws -> Data {
        let (data, response) = try await session.data(for: request)
        if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            throw DesktopClientError.http(http.statusCode)
        }
        return data
    }

    /// Build a Bearer-authed request the same way HTTPDesktopClient does, but inline
    /// (no private-helper dependency). Trims a trailing slash off the base, attaches
    /// the token when present, and JSON-encodes a string body for the decision POST.
    private func proposalsRequest(
        path: String, method: String, jsonBody: [String: String]? = nil
    ) -> URLRequest {
        let absolute = config.baseURL.absoluteString
        let base = absolute.hasSuffix("/") ? String(absolute.dropLast()) : absolute
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
