import XCTest
import Contracts
@testable import Providers

/// HSM equilibrium wave 3 — the propose→review→approve client slice. A decode
/// round-trip over a realistic hub payload (`_proposal_to_dict` in
/// `holdspeak/web/routes/meetings.py`) plus a stubbed drive of the two client
/// methods, proving the route paths, the Bearer header, the decision body shape,
/// and that the responses decode into MeetingProposal / ProposalDecision.
/// Fully offline (URLProtocol stub) — no real desktop.
final class ProposalsClientTests: XCTestCase {

    // MARK: stub (mirrors DesktopClientTests' StubProtocol; records last request)

    final class StubProtocol: URLProtocol {
        nonisolated(unsafe) static var routes: [String: (Int, Data)] = [:]
        nonisolated(unsafe) static var lastAuth: String??
        nonisolated(unsafe) static var lastMethod: String?
        nonisolated(unsafe) static var lastPath: String?
        nonisolated(unsafe) static var lastBody: Data?
        override class func canInit(with request: URLRequest) -> Bool { true }
        override class func canonicalRequest(for r: URLRequest) -> URLRequest { r }
        override func startLoading() {
            StubProtocol.lastAuth = request.value(forHTTPHeaderField: "Authorization")
            StubProtocol.lastMethod = request.httpMethod
            StubProtocol.lastPath = request.url?.path
            // URLProtocol strips httpBody into httpBodyStream; read it back.
            if let stream = request.httpBodyStream {
                stream.open()
                var data = Data()
                let bufSize = 1024
                let buf = UnsafeMutablePointer<UInt8>.allocate(capacity: bufSize)
                while stream.hasBytesAvailable {
                    let read = stream.read(buf, maxLength: bufSize)
                    if read <= 0 { break }
                    data.append(buf, count: read)
                }
                buf.deallocate()
                stream.close()
                StubProtocol.lastBody = data
            } else {
                StubProtocol.lastBody = request.httpBody
            }
            let path = request.url?.path ?? ""
            guard let (status, body) = StubProtocol.routes[path] else {
                client?.urlProtocol(self, didFailWithError: URLError(.cannotConnectToHost))
                return
            }
            let resp = HTTPURLResponse(url: request.url!, statusCode: status, httpVersion: nil, headerFields: nil)!
            client?.urlProtocol(self, didReceive: resp, cacheStoragePolicy: .notAllowed)
            client?.urlProtocol(self, didLoad: body)
            client?.urlProtocolDidFinishLoading(self)
        }
        override func stopLoading() {}
    }

    private func stubbedSession() -> URLSession {
        let cfg = URLSessionConfiguration.ephemeral
        cfg.protocolClasses = [StubProtocol.self]
        return URLSession(configuration: cfg)
    }

    private func client(token: String? = "t0ken") -> HTTPDesktopClient {
        HTTPDesktopClient(config: .init(baseURL: URL(string: "http://desk.tailnet:8000")!, token: token),
                          session: stubbedSession())
    }

    override func setUp() {
        super.setUp()
        StubProtocol.routes = [:]
        StubProtocol.lastAuth = nil
        StubProtocol.lastMethod = nil
        StubProtocol.lastPath = nil
        StubProtocol.lastBody = nil
    }

    // A realistic GET /api/meetings/{id}/proposals envelope: one undecided slack
    // proposal (null decided_at/executed_at/decided_by/result/error) — the exact
    // shape `_proposal_to_dict` serializes.
    private let proposalsJSON = #"""
    {
      "meeting_id": "m-42",
      "proposals": [
        {
          "id": "p-1",
          "meeting_id": "m-42",
          "window_id": "w-7",
          "plugin_id": "slack_export",
          "plugin_version": "1.0.0",
          "status": "proposed",
          "target": "slack",
          "action": "send_message",
          "preview": "Posting the meeting digest to #standup",
          "payload": {"channel": "#standup", "blocks": 3},
          "reversible": false,
          "required_capabilities": ["network.slack"],
          "decided_by": null,
          "result": null,
          "error": null,
          "created_at": "2026-06-27T14:03:11Z",
          "decided_at": null,
          "executed_at": null
        }
      ]
    }
    """#

    // MARK: decode round-trip

    func testProposalsEnvelopeDecodes() throws {
        let env = try HoldSpeakContracts.decoder()
            .decode(MeetingProposalsEnvelope.self, from: Data(proposalsJSON.utf8))
        XCTAssertEqual(env.meetingId, "m-42")
        XCTAssertEqual(env.proposals.count, 1)

        let p = try XCTUnwrap(env.proposals.first)
        XCTAssertEqual(p.id, "p-1")
        XCTAssertEqual(p.meetingId, "m-42")
        XCTAssertEqual(p.windowId, "w-7")
        XCTAssertEqual(p.pluginId, "slack_export")
        XCTAssertEqual(p.status, .proposed)
        XCTAssertEqual(p.target, "slack")
        XCTAssertEqual(p.action, "send_message")
        XCTAssertEqual(p.preview, "Posting the meeting digest to #standup")
        XCTAssertFalse(p.reversible)
        XCTAssertEqual(p.requiredCapabilities, ["network.slack"])
        XCTAssertNil(p.decidedBy)
        XCTAssertNil(p.decidedAt)
        XCTAssertNil(p.executedAt)
        XCTAssertNotNil(p.createdAt)               // ISO-8601 Z decoded
        XCTAssertEqual(p.payload, .object(["channel": .string("#standup"),
                                           "blocks": .number(3)]))
    }

    func testDecisionEnvelopeDecodes() throws {
        // An approved slack proposal executes immediately → comes back `executed`.
        let json = #"""
        {
          "success": true,
          "proposal": {
            "id": "p-1",
            "meeting_id": "m-42",
            "window_id": "w-7",
            "plugin_id": "slack_export",
            "plugin_version": "1.0.0",
            "status": "executed",
            "target": "slack",
            "action": "send_message",
            "preview": "Posting the meeting digest to #standup",
            "payload": {"channel": "#standup"},
            "reversible": false,
            "required_capabilities": ["network.slack"],
            "decided_by": "ipad-user",
            "result": {"ok": true},
            "error": null,
            "created_at": "2026-06-27T14:03:11Z",
            "decided_at": "2026-06-27T14:05:00Z",
            "executed_at": "2026-06-27T14:05:01Z"
          }
        }
        """#
        let decision = try HoldSpeakContracts.decoder()
            .decode(ProposalDecision.self, from: Data(json.utf8))
        XCTAssertTrue(decision.success)
        XCTAssertNil(decision.error)
        let p = try XCTUnwrap(decision.proposal)
        XCTAssertEqual(p.status, .executed)
        XCTAssertEqual(p.decidedBy, "ipad-user")
        XCTAssertNotNil(p.decidedAt)
        XCTAssertNotNil(p.executedAt)
        XCTAssertEqual(p.result, .object(["ok": .bool(true)]))
    }

    func testIllegalDecisionEnvelopeDecodes() throws {
        // The hub returns success:false + error on an illegal transition.
        let json = #"{"success": false, "error": "proposal already executed"}"#
        let decision = try HoldSpeakContracts.decoder()
            .decode(ProposalDecision.self, from: Data(json.utf8))
        XCTAssertFalse(decision.success)
        XCTAssertNil(decision.proposal)
        XCTAssertEqual(decision.error, "proposal already executed")
    }

    // MARK: stubbed client drive — route paths, Bearer, decision body

    func testMeetingProposalsHitsRouteWithBearer() async throws {
        StubProtocol.routes = ["/api/meetings/m-42/proposals": (200, Data(proposalsJSON.utf8))]
        let proposals = try await client().meetingProposals(meetingId: "m-42")
        XCTAssertEqual(proposals.count, 1)
        XCTAssertEqual(proposals.first?.id, "p-1")
        XCTAssertEqual(StubProtocol.lastMethod, "GET")
        XCTAssertEqual(StubProtocol.lastPath, "/api/meetings/m-42/proposals")
        XCTAssertEqual(StubProtocol.lastAuth, "Bearer t0ken")
    }

    func testDecideProposalPostsApprovedDecision() async throws {
        let okJSON = #"""
        {"success": true, "proposal": {
          "id": "p-1", "meeting_id": "m-42", "window_id": null,
          "plugin_id": "slack_export", "plugin_version": "1.0.0",
          "status": "approved", "target": "slack", "action": "send_message",
          "preview": "x", "payload": null, "reversible": false,
          "required_capabilities": [], "decided_by": "ipad-user",
          "result": null, "error": null, "created_at": "2026-06-27T14:03:11Z",
          "decided_at": "2026-06-27T14:05:00Z", "executed_at": null
        }}
        """#
        StubProtocol.routes = [
            "/api/meetings/m-42/proposals/p-1/decision": (200, Data(okJSON.utf8))
        ]
        let decision = try await client().decideProposal(
            meetingId: "m-42", proposalId: "p-1", approved: true)
        XCTAssertTrue(decision.success)
        XCTAssertEqual(decision.proposal?.status, .approved)
        XCTAssertEqual(StubProtocol.lastMethod, "POST")
        XCTAssertEqual(StubProtocol.lastPath, "/api/meetings/m-42/proposals/p-1/decision")

        // The body must carry decision:"approved" (approved=true → the hub string).
        let body = try XCTUnwrap(StubProtocol.lastBody)
        let obj = try XCTUnwrap(JSONSerialization.jsonObject(with: body) as? [String: String])
        XCTAssertEqual(obj["decision"], "approved")
    }

    func testDecideProposalRejectMapsToRejectedString() async throws {
        let okJSON = #"""
        {"success": true, "proposal": {
          "id": "p-1", "meeting_id": "m-42", "window_id": null,
          "plugin_id": "slack_export", "plugin_version": "1.0.0",
          "status": "rejected", "target": "slack", "action": "send_message",
          "preview": "x", "payload": null, "reversible": false,
          "required_capabilities": [], "decided_by": "ipad-user",
          "result": null, "error": null, "created_at": "2026-06-27T14:03:11Z",
          "decided_at": "2026-06-27T14:05:00Z", "executed_at": null
        }}
        """#
        StubProtocol.routes = [
            "/api/meetings/m-42/proposals/p-1/decision": (200, Data(okJSON.utf8))
        ]
        _ = try await client().decideProposal(meetingId: "m-42", proposalId: "p-1", approved: false)
        let body = try XCTUnwrap(StubProtocol.lastBody)
        let obj = try XCTUnwrap(JSONSerialization.jsonObject(with: body) as? [String: String])
        XCTAssertEqual(obj["decision"], "rejected")
    }

    func testNon2xxThrowsHTTPError() async {
        StubProtocol.routes = ["/api/meetings/nope/proposals": (404, Data())]
        do {
            _ = try await client().meetingProposals(meetingId: "nope")
            XCTFail("expected a thrown HTTP error on 404")
        } catch let HTTPDesktopClient.DesktopClientError.http(code) {
            XCTAssertEqual(code, 404)
        } catch {
            XCTFail("expected DesktopClientError.http, got \(error)")
        }
    }
}
