import XCTest
import Contracts
@testable import Providers

/// HSM-15-03 — the mesh inbox client: the envelope decodes off the REAL route
/// shape (jobs + proposals + counts, no payload on any proposal), Bearer rides,
/// the desk-origin decision posts to the right route with `decided_by`, and a
/// non-2xx throws. Mirrors AskClientTests' stub posture.
final class MeshInboxClientTests: XCTestCase {

    final class StubProtocol: URLProtocol {
        nonisolated(unsafe) static var routes: [String: (Int, Data)] = [:]
        nonisolated(unsafe) static var lastAuth: String??
        nonisolated(unsafe) static var lastPath: String?
        nonisolated(unsafe) static var lastBody: Data?
        override class func canInit(with request: URLRequest) -> Bool { true }
        override class func canonicalRequest(for r: URLRequest) -> URLRequest { r }
        override func startLoading() {
            StubProtocol.lastAuth = request.value(forHTTPHeaderField: "Authorization")
            StubProtocol.lastPath = request.url?.path
            StubProtocol.lastBody = request.httpBody ?? request.httpBodyStream.map { stream in
                stream.open(); defer { stream.close() }
                var data = Data(); var buf = [UInt8](repeating: 0, count: 1024)
                while stream.hasBytesAvailable {
                    let n = stream.read(&buf, maxLength: buf.count)
                    if n <= 0 { break }
                    data.append(buf, count: n)
                }
                return data
            }
            let path = request.url?.path ?? ""
            guard let (status, body) = StubProtocol.routes[path] else {
                client?.urlProtocol(self, didFailWithError: URLError(.cannotConnectToHost)); return
            }
            let resp = HTTPURLResponse(url: request.url!, statusCode: status, httpVersion: nil, headerFields: nil)!
            client?.urlProtocol(self, didReceive: resp, cacheStoragePolicy: .notAllowed)
            client?.urlProtocol(self, didLoad: body)
            client?.urlProtocolDidFinishLoading(self)
        }
        override func stopLoading() {}
    }

    private func client(token: String? = nil) -> HTTPDesktopClient {
        let cfg = URLSessionConfiguration.ephemeral
        cfg.protocolClasses = [StubProtocol.self]
        return HTTPDesktopClient(config: .init(baseURL: URL(string: "http://desk.tailnet:8000")!, token: token),
                                 session: URLSession(configuration: cfg))
    }

    override func setUp() {
        super.setUp()
        StubProtocol.routes = [:]
        StubProtocol.lastAuth = nil
        StubProtocol.lastPath = nil
        StubProtocol.lastBody = nil
    }

    // The REAL route shape (routes/mesh.py api_mesh_inbox).
    private let inboxJSON = #"""
    {
      "jobs": [
        {"kind": "intel", "id": "intelq:m1", "label": "Q3 kickoff",
         "status": "queued", "meeting_id": "m1", "attempts": 0},
        {"kind": "plugin", "id": "pj1", "label": "risk_register",
         "status": "queued", "meeting_id": "m1", "attempts": 1}
      ],
      "proposals": [
        {"id": "prop-m", "origin": "meeting", "meeting_id": "m1",
         "target": "github", "action": "create_issue",
         "preview": "Open a follow-up issue", "status": "proposed",
         "created_at": "2026-07-05T10:00:00"},
        {"id": "prop-d", "origin": "desk", "meeting_id": null,
         "target": "slack", "action": "send_message",
         "preview": "Digest → #eng-updates", "status": "proposed",
         "operation": {"effect_class": "slack/post_message",
                       "destination": "slack:sha256:fixed",
                       "consequence": "execute_now"},
         "policy_snapshot": {"mode": "neutral", "source": "config",
                             "policy_version": "operation-policy/v2",
                             "outcome": "authorization_required",
                             "reason_code": "per_action_authorization_required",
                             "authority_basis": "per_action_required",
                             "next_state": "awaiting_authorization"},
         "created_at": "2026-07-05T10:01:00"}
      ],
      "counts": {"queued": 2, "running": 0, "failed": 1, "pending_approvals": 2}
    }
    """#

    func testInboxDecodesJobsProposalsAndCounts() async throws {
        StubProtocol.routes = ["/api/mesh/inbox": (200, Data(inboxJSON.utf8))]
        let inbox = try await client(token: "tok").meshInbox()
        XCTAssertEqual(StubProtocol.lastAuth, "Bearer tok")

        XCTAssertEqual(inbox.jobs?.count, 2)
        XCTAssertEqual(inbox.jobs?[0].kind, "intel")
        XCTAssertEqual(inbox.jobs?[0].label, "Q3 kickoff")
        XCTAssertEqual(inbox.jobs?[0].meetingId, "m1")
        XCTAssertEqual(inbox.jobs?[1].attempts, 1)

        XCTAssertEqual(inbox.proposals?.count, 2)
        let desk = inbox.proposals?[1]
        XCTAssertEqual(desk?.origin, "desk")
        XCTAssertNil(desk?.meetingId)
        XCTAssertEqual(desk?.target, "slack")
        XCTAssertEqual(desk?.preview, "Digest → #eng-updates")
        XCTAssertEqual(desk?.operation?.effectClass, "slack/post_message")
        XCTAssertEqual(desk?.operation?.destination, "slack:sha256:fixed")
        XCTAssertEqual(desk?.policySnapshot?.mode, "neutral")
        XCTAssertEqual(desk?.policySnapshot?.policyVersion, "operation-policy/v2")
        XCTAssertEqual(desk?.policySnapshot?.nextState, "awaiting_authorization")

        XCTAssertEqual(inbox.counts?.pendingApprovals, 2)
        XCTAssertEqual(inbox.counts?.failed, 1)
    }

    func testDeskDecisionPostsTheRightRouteAndActor() async throws {
        // The REAL desk decision envelope carries the full proposal dict with
        // meeting_id null — the tolerant DeskProposalDecision decode must not
        // choke on it (the strict MeetingProposal decode would).
        let decisionJSON = #"""
        {"success": true, "proposal": {"id": "prop-d", "meeting_id": null,
         "origin": "desk", "status": "approved", "target": "slack",
         "action": "send_message", "preview": "Digest → #eng-updates"}}
        """#
        StubProtocol.routes = ["/api/desk/actuators/slack/prop-d/decision": (200, Data(decisionJSON.utf8))]
        let decision = try await client(token: "tok").decideDeskProposal(
            target: "slack", proposalId: "prop-d", approved: true)
        XCTAssertTrue(decision.success)
        XCTAssertEqual(StubProtocol.lastPath, "/api/desk/actuators/slack/prop-d/decision")
        let sent = try JSONSerialization.jsonObject(with: StubProtocol.lastBody ?? Data()) as? [String: String]
        XCTAssertEqual(sent?["decision"], "approved")
        XCTAssertEqual(sent?["decided_by"], "ipad-companion",
                       "an iPad decision must name this surface in the audit trail")
    }

    func testNon2xxThrows() async {
        StubProtocol.routes = ["/api/mesh/inbox": (503, Data())]
        do { _ = try await client().meshInbox(); XCTFail("expected throw") }
        catch let HTTPDesktopClient.DesktopClientError.http(code) { XCTAssertEqual(code, 503) }
        catch { XCTFail("wrong error: \(error)") }
    }
}
