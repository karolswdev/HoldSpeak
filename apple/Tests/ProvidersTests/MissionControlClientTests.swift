import XCTest
import Contracts
@testable import Providers

/// HSM-25-01 — the iOS mission-control client. Network stubbed via
/// `URLProtocol`; deterministic and offline. The JSON literals below
/// are the frozen backend shapes (its Phase 82:
/// /api/missioncontrol/state|sessions|events); decoding them here is
/// the drift guard against the FastAPI contract. Proves: the feed,
/// correlation, and events decode (snake_case via the shared decoder,
/// no manual CodingKeys); the owner Bearer token rides every request;
/// compatibility/unavailable statuses decode without a `feed`; and an
/// HTTP error throws `DesktopClientError.http`.
final class MissionControlClientTests: XCTestCase {

    final class StubProtocol: URLProtocol {
        nonisolated(unsafe) static var routes: [String: (Int, Data)] = [:]
        nonisolated(unsafe) static var lastAuth: String??
        nonisolated(unsafe) static var lastPath: String?
        override class func canInit(with request: URLRequest) -> Bool { true }
        override class func canonicalRequest(for r: URLRequest) -> URLRequest { r }
        override func startLoading() {
            StubProtocol.lastAuth = request.value(forHTTPHeaderField: "Authorization")
            StubProtocol.lastPath = request.url?.path
            let path = request.url?.path ?? ""
            guard let (status, body) = StubProtocol.routes[path] else {
                client?.urlProtocol(self, didFailWithError: URLError(.cannotConnectToHost))
                return
            }
            let resp = HTTPURLResponse(url: request.url!, statusCode: status,
                                       httpVersion: nil, headerFields: nil)!
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
        StubProtocol.lastPath = nil
    }

    private func client(token: String? = nil) -> HTTPDesktopClient {
        HTTPDesktopClient(config: .init(baseURL: URL(string: "http://desk.tailnet:8000")!,
                                        token: token),
                          session: stubbedSession())
    }

    private func route(_ path: String, _ json: String, status: Int = 200) {
        StubProtocol.routes[path] = (status, Data(json.utf8))
    }

    // MARK: the frozen shapes

    private let liveState = """
    {"repos": [{"name": "delivery-workbench", "path": "/repos/dw",
      "status": "live", "feed": {"feed_schema": 1, "projects": [
        {"slug": "work-log-automation", "prefix": "WLA",
         "current_phase": {"number": 14, "title": "The Absorption",
           "status": "open", "stories_done": 6, "stories_total": 7},
         "next_story": {"story_id": "WLA-14-07", "title": "Prove it",
           "status": "backlog"},
         "phases": [{"number": 13, "title": "Mission control",
           "status": "closed", "stories_done": 6, "stories_total": 6}],
         "stories": [{"story_id": "WLA-14-06", "title": "Seven locks",
           "status": "done", "phase": 14, "evidence_exists": true}],
         "warnings": 1}]}}]}
    """

    private let liveSessions = """
    {"status": "live", "sessions": {"sessions_schema": 1,
      "registry": "ok", "sessions": [
        {"key": "claude:s1", "agent": "claude", "correlation": "on_story",
         "stories": [{"story_id": "WLA-14-07"}], "awaiting_response": true,
         "stale": false, "tmux": {"session": "gate"}}]}}
    """

    private let liveEvents = """
    {"repos": [{"name": "delivery-workbench", "path": "/repos/dw",
      "status": "live", "events": [
        {"ts": "2026-07-04T21:00:00Z", "event": "gate_refusal",
         "story": "WLA-14-07", "detail": {"rule": "story-evidence"}}]}]}
    """

    // MARK: state

    func testStateDecodesTheLiveFeed() async throws {
        route("/api/missioncontrol/state", liveState)
        let payload = try await client(token: "t").missionControlState()
        let repo = try XCTUnwrap(payload.repos.first)
        XCTAssertTrue(repo.isLive)
        let project = try XCTUnwrap(repo.feed?.projects.first)
        XCTAssertEqual(project.slug, "work-log-automation")
        XCTAssertEqual(project.currentPhase?.number, 14)
        XCTAssertEqual(project.currentPhase?.storiesDone, 6)
        XCTAssertEqual(project.nextStory?.storyId, "WLA-14-07")
        XCTAssertEqual(project.stories.first?.evidenceExists, true)
        XCTAssertEqual(project.warnings, 1)
    }

    func testStateCompatibilityHasNoFeed() async throws {
        route("/api/missioncontrol/state", """
        {"repos": [{"name": "dw", "path": "/x", "status": "compatibility",
          "detail": "feed_schema 2 is not the schema this desk was proven against (1)"}]}
        """)
        let repo = try await client().missionControlState().repos.first
        XCTAssertEqual(repo?.status, "compatibility")
        XCTAssertFalse(repo?.isLive ?? true)
        XCTAssertNil(repo?.feed)
        XCTAssertTrue(repo?.detail?.contains("proven against") ?? false)
    }

    // MARK: sessions

    func testSessionsDecodeCorrelation() async throws {
        route("/api/missioncontrol/sessions", liveSessions)
        let payload = try await client(token: "t").missionControlSessions()
        XCTAssertTrue(payload.isLive)
        let session = try XCTUnwrap(payload.sessions?.sessions.first)
        XCTAssertEqual(session.correlation, "on_story")
        XCTAssertEqual(session.stories.first?.storyId, "WLA-14-07")
        XCTAssertTrue(session.awaitingResponse)
        XCTAssertEqual(session.tmux?.session, "gate")
    }

    func testSessionsUnavailableDecodesWithoutDoc() async throws {
        route("/api/missioncontrol/sessions",
              #"{"status": "unavailable", "detail": "no rails repo configured"}"#)
        let payload = try await client().missionControlSessions()
        XCTAssertEqual(payload.status, "unavailable")
        XCTAssertNil(payload.sessions)
    }

    // MARK: events

    func testEventsDecodeWithFreeFormDetail() async throws {
        route("/api/missioncontrol/events", liveEvents)
        let payload = try await client(token: "t").missionControlEvents()
        let event = try XCTUnwrap(payload.repos.first?.events?.first)
        XCTAssertEqual(event.event, "gate_refusal")
        XCTAssertEqual(event.story, "WLA-14-07")
        XCTAssertEqual(event.detail?["rule"], .string("story-evidence"))
    }

    // MARK: auth + failure

    func testOwnerTokenRidesEveryRequest() async throws {
        route("/api/missioncontrol/state", liveState)
        _ = try await client(token: "owner-secret").missionControlState()
        XCTAssertEqual(StubProtocol.lastAuth, "Bearer owner-secret")
        XCTAssertEqual(StubProtocol.lastPath, "/api/missioncontrol/state")
    }

    func testNoTokenSendsNoAuthHeader() async throws {
        route("/api/missioncontrol/state", liveState)
        _ = try await client(token: nil).missionControlState()
        XCTAssertEqual(StubProtocol.lastAuth, .some(nil))
    }

    func testOwnerOnlyRejectionThrowsHTTP() async throws {
        route("/api/missioncontrol/state", "{}", status: 403)
        do {
            _ = try await client(token: "wrong").missionControlState()
            XCTFail("a 403 must throw so the conveyor can render 'pair with the owner'")
        } catch let error as HTTPDesktopClient.DesktopClientError {
            XCTAssertEqual(error, .http(403))
        }
    }
}
