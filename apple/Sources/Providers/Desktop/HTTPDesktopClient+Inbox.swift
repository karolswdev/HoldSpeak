import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import Contracts

// HSM-15-03 — the mesh inbox client: one poll over everything in flight on the
// hub + everything pending the human nod. The Queue HUD merges these beside the
// on-device jobs; approving from the HUD rides the EXISTING decision routes
// (meeting proposals via HTTPDesktopClient+Proposals; desk-origin ones via
// `decideDeskProposal` below). New extension file by design (the conflict rule).

/// One in-flight hub job (deferred intel / MIR plugin run). Robust decode.
public struct MeshInboxJob: Codable, Equatable, Sendable, Identifiable {
    public var id: String
    public var kind: String?        // "intel" | "plugin"
    public var label: String?
    public var status: String?      // "queued" | "running"
    public var meetingId: String?
    public var attempts: Int?

    public init(id: String, kind: String? = nil, label: String? = nil,
                status: String? = nil, meetingId: String? = nil, attempts: Int? = nil) {
        self.id = id; self.kind = kind; self.label = label
        self.status = status; self.meetingId = meetingId; self.attempts = attempts
    }
}

/// One proposal awaiting the nod. `origin` + `target` pick the decision route;
/// the payload NEVER rides (the hub keeps the parity source of truth).
public struct MeshInboxProposal: Codable, Equatable, Sendable, Identifiable {
    public var id: String
    public var origin: String?      // "meeting" | "desk"
    public var meetingId: String?   // nil for desk-origin
    public var target: String?      // "slack" | "github" | "webhook" | …
    public var action: String?
    public var preview: String?
    public var status: String?
    public var createdAt: String?   // ISO string — the timestamps rule (never Date)
    public var commitment: MeshProposalCommitment?

    public init(id: String, origin: String? = nil, meetingId: String? = nil,
                target: String? = nil, action: String? = nil, preview: String? = nil,
                status: String? = nil, createdAt: String? = nil,
                commitment: MeshProposalCommitment? = nil) {
        self.id = id; self.origin = origin; self.meetingId = meetingId
        self.target = target; self.action = action; self.preview = preview
        self.status = status; self.createdAt = createdAt; self.commitment = commitment
    }
}

public struct MeshProposalCommitment: Codable, Equatable, Sendable {
    public var approve: String?
    public var reject: String?
    public init(approve: String? = nil, reject: String? = nil) {
        self.approve = approve; self.reject = reject
    }
}

public struct MeshInboxCounts: Codable, Equatable, Sendable {
    public var queued: Int?
    public var running: Int?
    public var failed: Int?
    public var pendingApprovals: Int?

    public init(queued: Int? = nil, running: Int? = nil,
                failed: Int? = nil, pendingApprovals: Int? = nil) {
        self.queued = queued; self.running = running
        self.failed = failed; self.pendingApprovals = pendingApprovals
    }
}

/// The whole envelope `GET /api/mesh/inbox` answers with.
public struct MeshInbox: Codable, Equatable, Sendable {
    public var jobs: [MeshInboxJob]?
    public var proposals: [MeshInboxProposal]?
    public var counts: MeshInboxCounts?

    public init(jobs: [MeshInboxJob]? = nil, proposals: [MeshInboxProposal]? = nil,
                counts: MeshInboxCounts? = nil) {
        self.jobs = jobs; self.proposals = proposals; self.counts = counts
    }
}

/// A desk-origin decision's answer. Deliberately NOT `ProposalDecision`: its
/// `MeetingProposal` requires a `meeting_id`, and a desk proposal's is null on
/// the wire — the strict decode would throw on a SUCCESSFUL decision. The HUD
/// only needs success/error (it re-polls the inbox for fresh state).
public struct DeskProposalDecision: Codable, Equatable, Sendable {
    public var success: Bool
    public var error: String?

    public init(success: Bool, error: String? = nil) {
        self.success = success
        self.error = error
    }
}

extension HTTPDesktopClient {

    /// `GET /api/mesh/inbox` → the hub's in-flight jobs + pending approvals.
    /// A pure read; non-2xx throws `DesktopClientError.http`.
    public func meshInbox() async throws -> MeshInbox {
        let data = try await inboxSend(inboxRequest(path: "api/mesh/inbox", method: "GET"))
        do { return try HoldSpeakContracts.decoder().decode(MeshInbox.self, from: data) }
        catch { throw DesktopClientError.malformed }
    }

    /// The desk-origin twin of `decideProposal` (which owns the meeting-origin
    /// route). The hub serves one LITERAL route per connector, so the target is
    /// switched here (an unknown target is refused client-side — it could only
    /// 404). Approving a `slack` desk proposal executes immediately through the
    /// hub's guarded executor; `decided_by` names this surface in the audit trail.
    public func decideDeskProposal(
        target: String, proposalId: String, approved: Bool
    ) async throws -> DeskProposalDecision {
        let path: String
        switch target {
        case "slack":
            path = "api/desk/actuators/slack/\(inboxEscape(proposalId))/decision"
        case "webhook":
            path = "api/desk/actuators/webhook/\(inboxEscape(proposalId))/decision"
        case "github":
            path = "api/desk/actuators/github/\(inboxEscape(proposalId))/decision"
        default:
            throw DesktopClientError.malformed
        }
        let body = ["decision": approved ? "approved" : "rejected",
                    "decided_by": "ipad-companion"]
        let request = inboxRequest(path: path, method: "POST", jsonBody: body)
        let data = try await inboxSend(request)
        do { return try HoldSpeakContracts.decoder().decode(DeskProposalDecision.self, from: data) }
        catch { throw DesktopClientError.malformed }
    }

    // MARK: - internals (private to this extension, per the conflict rule)

    private func inboxEscape(_ segment: String) -> String {
        segment.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? segment
    }

    private func inboxSend(_ request: URLRequest) async throws -> Data {
        let (data, response) = try await session.data(for: request)
        if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            throw DesktopClientError.http(http.statusCode)
        }
        return data
    }

    private func inboxRequest(
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
