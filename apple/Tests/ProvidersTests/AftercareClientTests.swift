import XCTest
import Contracts
@testable import Providers

/// HSM Aftercare client layer — decode round-trips + the client verbs over a stubbed
/// network (URLProtocol, fully offline). Proves the digest from
/// `GET /api/meetings/{id}/aftercare` decodes faithfully (open_items.by_owner,
/// decisions, since_last_meeting, is_empty) and the `POST .../file-issue` envelope
/// decodes to a proposal + preview. Mirrors DesktopClientTests' stub posture.
final class AftercareClientTests: XCTestCase {

    // MARK: stub (same shape as DesktopClientTests.StubProtocol)

    final class StubProtocol: URLProtocol {
        nonisolated(unsafe) static var routes: [String: (Int, Data)] = [:]
        nonisolated(unsafe) static var lastAuth: String??
        nonisolated(unsafe) static var lastMethod: String?
        nonisolated(unsafe) static var lastBody: Data?
        override class func canInit(with request: URLRequest) -> Bool { true }
        override class func canonicalRequest(for r: URLRequest) -> URLRequest { r }
        override func startLoading() {
            StubProtocol.lastAuth = request.value(forHTTPHeaderField: "Authorization")
            StubProtocol.lastMethod = request.httpMethod
            StubProtocol.lastBody = request.httpBody
                ?? request.httpBodyStream.map { stream -> Data in
                    stream.open(); defer { stream.close() }
                    var data = Data(); var buf = [UInt8](repeating: 0, count: 4096)
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

    private func stubbedSession() -> URLSession {
        let cfg = URLSessionConfiguration.ephemeral
        cfg.protocolClasses = [StubProtocol.self]
        return URLSession(configuration: cfg)
    }

    override func setUp() {
        super.setUp()
        StubProtocol.routes = [:]
        StubProtocol.lastAuth = nil
        StubProtocol.lastMethod = nil
        StubProtocol.lastBody = nil
    }

    private func client(token: String? = nil) -> HTTPDesktopClient {
        HTTPDesktopClient(config: .init(baseURL: URL(string: "http://desk.tailnet:8000")!, token: token),
                          session: stubbedSession())
    }

    // A realistic, fully-populated digest (the shape compute_meeting_aftercare emits).
    private let digestJSON = #"""
    {
      "meeting_id": "m1",
      "meeting_title": "Arch review",
      "meeting_date": "2026-06-20T10:00:00+00:00",
      "open_items": {
        "total": 3,
        "by_owner": [
          {
            "owner": "Karol",
            "count": 2,
            "items": [
              {"id": "a1", "task": "Wire the sync transport", "owner": "Karol",
               "due": "2026-06-25", "review_state": "accepted", "source_timestamp": 12.5,
               "provenance": {"source_timestamp": 12.5, "segment_index": 4, "segment_start": 11.0,
                              "speaker": "Karol", "text_preview": "let's wire the transport next"},
               "meeting_id": "m1"},
              {"id": "a2", "task": "Draft the contract", "owner": "Karol",
               "due": null, "review_state": "pending", "source_timestamp": null,
               "provenance": null, "meeting_id": "m1"}
            ]
          },
          {
            "owner": null,
            "count": 1,
            "items": [
              {"id": "a3", "task": "Book the room", "owner": null, "due": null,
               "review_state": "pending", "source_timestamp": null, "provenance": null,
               "meeting_id": "m1"}
            ]
          }
        ]
      },
      "decisions": [
        {"decision": "Ship the iPad companion", "rationale": "Track M gate achieved",
         "source_timestamp": 30.0,
         "provenance": {"source_timestamp": 30.0, "segment_index": 9, "segment_start": 29.5,
                        "speaker": "Karol", "text_preview": "we ship the companion"}},
        {"decision": "Defer Windows", "rationale": null, "source_timestamp": null, "provenance": null}
      ],
      "since_last_meeting": {
        "previous_meeting": {"id": "m0", "title": "Kickoff", "date": "2026-06-19T09:00:00+00:00"},
        "new_decisions": [
          {"decision": "Ship the iPad companion", "rationale": "Track M gate achieved",
           "source_timestamp": 30.0, "provenance": null}
        ],
        "new_actions": [
          {"id": "a1", "task": "Wire the sync transport", "owner": "Karol", "due": "2026-06-25",
           "review_state": "accepted", "source_timestamp": 12.5, "provenance": null, "meeting_id": "m1"}
        ],
        "closed_actions": [
          {"id": "a0", "task": "Pick the engine", "owner": "Karol", "status": "done", "meeting_id": "m0"}
        ],
        "changed": true
      },
      "is_empty": false,
      "slack_configured": true
    }
    """#

    // MARK: digest decode round-trip (direct + through the client)

    func testAftercareDigestDecodesFaithfully() throws {
        let digest = try HoldSpeakContracts.decoder().decode(Aftercare.self, from: Data(digestJSON.utf8))

        XCTAssertEqual(digest.meetingId, "m1")
        XCTAssertEqual(digest.meetingTitle, "Arch review")
        XCTAssertFalse(digest.isEmpty)
        XCTAssertEqual(digest.slackConfigured, true)

        // open_items.by_owner — named owner first, unassigned (nil) last.
        XCTAssertEqual(digest.openItems.total, 3)
        XCTAssertEqual(digest.openItems.byOwner.count, 2)
        let karol = digest.openItems.byOwner[0]
        XCTAssertEqual(karol.owner, "Karol")
        XCTAssertEqual(karol.count, 2)
        XCTAssertEqual(karol.items.first?.id, "a1")
        XCTAssertEqual(karol.items.first?.reviewState, "accepted")
        XCTAssertEqual(karol.items.first?.provenance?.segmentIndex, 4)
        XCTAssertEqual(karol.items.first?.provenance?.textPreview, "let's wire the transport next")
        XCTAssertNil(digest.openItems.byOwner[1].owner)   // unassigned group

        // decisions
        XCTAssertEqual(digest.decisions.count, 2)
        XCTAssertEqual(digest.decisions[0].decision, "Ship the iPad companion")
        XCTAssertEqual(digest.decisions[0].rationale, "Track M gate achieved")
        XCTAssertNil(digest.decisions[1].rationale)

        // since_last_meeting diff
        let since = try XCTUnwrap(digest.sinceLastMeeting)
        XCTAssertTrue(since.changed)
        XCTAssertEqual(since.previousMeeting?.id, "m0")
        XCTAssertEqual(since.previousMeeting?.title, "Kickoff")
        XCTAssertEqual(since.newDecisions.count, 1)
        XCTAssertEqual(since.newActions.first?.id, "a1")
        XCTAssertEqual(since.closedActions.first?.status, "done")
    }

    func testEmptyDigestDecodes() throws {
        let json = #"""
        {"meeting_id": "m9", "meeting_title": null, "meeting_date": "2026-06-20T10:00:00+00:00",
         "open_items": {"total": 0, "by_owner": []}, "decisions": [],
         "since_last_meeting": null, "is_empty": true, "slack_configured": false}
        """#
        let digest = try HoldSpeakContracts.decoder().decode(Aftercare.self, from: Data(json.utf8))
        XCTAssertTrue(digest.isEmpty)
        XCTAssertEqual(digest.openItems.total, 0)
        XCTAssertTrue(digest.openItems.byOwner.isEmpty)
        XCTAssertNil(digest.sinceLastMeeting)            // no prior meeting → no delta invented
        XCTAssertEqual(digest.slackConfigured, false)
    }

    func testAftercareClientGETsAndDecodes() async throws {
        StubProtocol.routes = ["/api/meetings/m1/aftercare": (200, Data(digestJSON.utf8))]
        let digest = try await client(token: "tok").aftercare(meetingId: "m1")
        XCTAssertEqual(StubProtocol.lastMethod, "GET")
        XCTAssertEqual(StubProtocol.lastAuth, "Bearer tok")   // Bearer token rides
        XCTAssertEqual(digest.meetingId, "m1")
        XCTAssertEqual(digest.openItems.byOwner.first?.items.first?.task, "Wire the sync transport")
    }

    func testAftercare404Throws() async {
        StubProtocol.routes = ["/api/meetings/nope/aftercare": (404, Data(#"{"error":"Meeting not found"}"#.utf8))]
        do { _ = try await client().aftercare(meetingId: "nope"); XCTFail("expected throw") }
        catch HTTPDesktopClient.DesktopClientError.http(let code) { XCTAssertEqual(code, 404) }
        catch { XCTFail("wrong error: \(error)") }
    }

    // MARK: file-issue

    func testFileAftercareIssuePostsAndDecodesProposal() async throws {
        let body = #"""
        {"success": true,
         "proposal": {
            "id": "p1", "meeting_id": "m1", "window_id": "m1:aftercare",
            "plugin_id": "github_issue", "plugin_version": "1.0.0", "status": "proposed",
            "target": "octo/repo", "action": "create_issue",
            "preview": "Open issue in octo/repo: Wire the sync transport",
            "reversible": false, "required_capabilities": ["github:issues:write"],
            "decided_by": null, "error": null,
            "created_at": "2026-06-27T12:00:00+00:00", "decided_at": null, "executed_at": null}}
        """#
        StubProtocol.routes = ["/api/meetings/m1/aftercare/file-issue": (200, Data(body.utf8))]

        let result = try await client(token: "tok").fileAftercareIssue(
            meetingId: "m1", actionItemId: "a1", repo: "octo/repo")

        XCTAssertEqual(StubProtocol.lastMethod, "POST")
        XCTAssertEqual(StubProtocol.lastAuth, "Bearer tok")
        // The body carries both the action item id and the target repo verbatim.
        let sent = try XCTUnwrap(StubProtocol.lastBody)
        let obj = try XCTUnwrap(try JSONSerialization.jsonObject(with: sent) as? [String: Any])
        XCTAssertEqual(obj["action_item_id"] as? String, "a1")
        XCTAssertEqual(obj["repo"] as? String, "octo/repo")

        XCTAssertTrue(result.success)
        let proposal = try XCTUnwrap(result.proposal)
        XCTAssertEqual(proposal.id, "p1")
        XCTAssertEqual(proposal.status, "proposed")            // proposed only — nothing sent
        XCTAssertEqual(proposal.target, "octo/repo")
        XCTAssertEqual(proposal.preview, "Open issue in octo/repo: Wire the sync transport")
        XCTAssertEqual(proposal.requiredCapabilities, ["github:issues:write"])
        XCTAssertNotNil(proposal.createdAt)                    // ISO date decodes
        XCTAssertNil(proposal.executedAt)
    }

    func testFileAftercareIssueErrorEnvelopeDecodesOn400() throws {
        // The route returns {"success": false, "error": "..."} with a 4xx for a
        // non-accepted item; decode the envelope shape directly.
        let body = #"{"success": false, "error": "Only an accepted action item can be filed as an issue"}"#
        let result = try HoldSpeakContracts.decoder().decode(
            AftercareFileIssueResult.self, from: Data(body.utf8))
        XCTAssertFalse(result.success)
        XCTAssertNil(result.proposal)
        XCTAssertEqual(result.error, "Only an accepted action item can be filed as an issue")
    }

    func testFileAftercareIssue400Throws() async {
        StubProtocol.routes = ["/api/meetings/m1/aftercare/file-issue":
            (400, Data(#"{"success":false,"error":"A target repo (owner/name) is required"}"#.utf8))]
        do {
            _ = try await client().fileAftercareIssue(meetingId: "m1", actionItemId: "a1", repo: "x")
            XCTFail("expected throw")
        } catch HTTPDesktopClient.DesktopClientError.http(let code) { XCTAssertEqual(code, 400) }
        catch { XCTFail("wrong error: \(error)") }
    }
}
