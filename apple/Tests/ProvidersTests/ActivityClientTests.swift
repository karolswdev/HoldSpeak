import XCTest
import Contracts
@testable import Providers

/// Equilibrium 18-05 — the iPad activity-nudge client. Network stubbed via
/// `URLProtocol`; fully deterministic and offline (no real desktop). Proves: the
/// source-cited cards decode against `Nudge.to_dict()` (snake_case via the shared
/// decoder, no manual CodingKeys), the token rides as a Bearer header on every verb,
/// `selectNudge` posts a real JSON int `record_id`, `dismissNudge` hits the keyed
/// path, the briefing decodes (and `nil` when absent), and an HTTP error throws.
final class ActivityClientTests: XCTestCase {

    // MARK: stub (records body + auth + method + path)

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
            StubProtocol.lastBody = request.httpBody ?? request.bodySteamData()
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

    override func setUp() {
        super.setUp()
        StubProtocol.routes = [:]
        StubProtocol.lastAuth = nil
        StubProtocol.lastMethod = nil
        StubProtocol.lastPath = nil
        StubProtocol.lastBody = nil
    }

    private func client(token: String? = nil) -> HTTPDesktopClient {
        HTTPDesktopClient(config: .init(baseURL: URL(string: "http://desk.tailnet:8000")!, token: token),
                          session: stubbedSession())
    }

    // MARK: decode the source-cited cards

    func testActivityNudgesDecodeServerShapeWithCitations() async throws {
        StubProtocol.routes = ["/api/activity/nudges": (200, Data(#"""
        {"nudges":[
          {"key":"window:2026-06-27T12:00:00","kind":"window",
           "title":"You touched 4 things since noon","body":"github.com, jira",
           "score":0.91,"window_since":"2026-06-27T12:00:00","window_record_count":4,
           "extras":{"headline":"recent"},
           "citations":[
             {"record_id":42,"source_browser":"chrome","source_profile":"Default",
              "entity_type":"github_pull_request","entity_id":"7","domain":"github.com",
              "title":"Fix the thing","url":"https://github.com/x/y/pull/7",
              "last_seen_at":"2026-06-27T12:30:00Z","visit_count":3}
           ]},
          {"key":"record:99","kind":"record","title":"You were looking at a PR",
           "body":"github.com","score":0.5,"window_since":null,"window_record_count":0,
           "extras":{},"citations":[
             {"record_id":99,"source_browser":"firefox","source_profile":"dev",
              "entity_type":null,"entity_id":null,"domain":"example.com","title":null,
              "url":"https://example.com","last_seen_at":null,"visit_count":1}
           ]}
        ],"activity_enabled":true}
        """#.utf8))]

        let nudges = try await client(token: "tok").activityNudges()
        XCTAssertEqual(StubProtocol.lastMethod, "GET")
        XCTAssertEqual(StubProtocol.lastAuth, "Bearer tok")   // Bearer joined at call time
        XCTAssertEqual(nudges.count, 2)

        let window = nudges[0]
        XCTAssertEqual(window.key, "window:2026-06-27T12:00:00")
        XCTAssertEqual(window.kind, "window")
        XCTAssertEqual(window.score, 0.91, accuracy: 0.0001)
        XCTAssertEqual(window.windowRecordCount, 4)
        XCTAssertEqual(window.citations.count, 1)
        let cite = window.citations[0]
        XCTAssertEqual(cite.recordId, 42)                     // snake_case → camelCase, no CodingKeys
        XCTAssertEqual(cite.sourceBrowser, "chrome")
        XCTAssertEqual(cite.entityType, "github_pull_request")
        XCTAssertEqual(cite.visitCount, 3)
        XCTAssertEqual(cite.lastSeenAt, "2026-06-27T12:30:00Z")

        let record = nudges[1]                                // a sparse record card still decodes
        XCTAssertEqual(record.kind, "record")
        XCTAssertNil(record.windowSince)
        XCTAssertNil(record.citations[0].entityType)
        XCTAssertNil(record.citations[0].title)
        XCTAssertNil(record.citations[0].lastSeenAt)
    }

    func testActivityNudgesEmptyWhenTrackingOff() async throws {
        StubProtocol.routes = ["/api/activity/nudges": (200,
            Data(#"{"nudges":[],"activity_enabled":false}"#.utf8))]
        let nudges = try await client().activityNudges()
        XCTAssertTrue(nudges.isEmpty)
    }

    func testActivityNudgesHTTPErrorThrows() async {
        StubProtocol.routes = ["/api/activity/nudges": (500, Data())]
        do { _ = try await client().activityNudges(); XCTFail("expected throw") }
        catch HTTPDesktopClient.DesktopClientError.http(let code) { XCTAssertEqual(code, 500) }
        catch { XCTFail("wrong error: \(error)") }
    }

    // MARK: select — the "Dictate with this" grounding (record_id as a JSON int)

    func testSelectNudgePostsRealIntRecordId() async throws {
        StubProtocol.routes = ["/api/activity/nudges/select": (200, Data(#"{"selected":42}"#.utf8))]
        try await client(token: "tok").selectNudge(recordId: 42)
        XCTAssertEqual(StubProtocol.lastMethod, "POST")
        XCTAssertEqual(StubProtocol.lastPath, "/api/activity/nudges/select")
        XCTAssertEqual(StubProtocol.lastAuth, "Bearer tok")
        let body = try XCTUnwrap(StubProtocol.lastBody)
        let json = try XCTUnwrap(JSONSerialization.jsonObject(with: body) as? [String: Any])
        // Must be a JSON number, not the string "42" — the desktop does int(...).
        XCTAssertTrue(json["record_id"] is NSNumber)
        XCTAssertEqual(json["record_id"] as? Int, 42)
    }

    func testSelectNudgeUnknownIdThrows() async {
        StubProtocol.routes = ["/api/activity/nudges/select": (400,
            Data(#"{"error":"unknown record_id 999"}"#.utf8))]
        do { try await client().selectNudge(recordId: 999); XCTFail("expected throw") }
        catch HTTPDesktopClient.DesktopClientError.http(let code) { XCTAssertEqual(code, 400) }
        catch { XCTFail("wrong error: \(error)") }
    }

    // MARK: dismiss — keyed path

    func testDismissNudgeHitsKeyedPath() async throws {
        StubProtocol.routes = ["/api/activity/nudges/record:42/dismiss": (200,
            Data(#"{"dismissed":"record:42"}"#.utf8))]
        try await client(token: "tok").dismissNudge(id: "record:42")
        XCTAssertEqual(StubProtocol.lastMethod, "POST")
        XCTAssertEqual(StubProtocol.lastAuth, "Bearer tok")
        XCTAssertEqual(StubProtocol.lastPath, "/api/activity/nudges/record:42/dismiss")
    }

    // MARK: briefing — present and absent

    func testBriefingDecodesDigest() async throws {
        StubProtocol.routes = ["/api/activity/briefing": (200, Data(#"""
        {"briefing":{"id":7,"title":"Arch review","value":"## Context\n- decided X",
                     "updated_at":"2026-06-27T09:00:00Z"},
         "last_run":{"status":"success"}}
        """#.utf8))]
        let briefing = try await client(token: "tok").briefing()
        XCTAssertEqual(StubProtocol.lastAuth, "Bearer tok")
        let b = try XCTUnwrap(briefing)
        XCTAssertEqual(b.id, 7)
        XCTAssertEqual(b.title, "Arch review")
        XCTAssertTrue(b.value.contains("decided X"))
        XCTAssertEqual(b.updatedAt, "2026-06-27T09:00:00Z")
    }

    func testBriefingNilWhenAbsent() async throws {
        StubProtocol.routes = ["/api/activity/briefing": (200,
            Data(#"{"briefing":null,"last_run":null}"#.utf8))]
        let briefing = try await client().briefing()
        XCTAssertNil(briefing)   // the desk shows nothing rather than a fabricated digest
    }
}

private extension URLRequest {
    /// `URLProtocol` receives a streamed body for some posts; drain it so the test
    /// can assert on `record_id`'s JSON type regardless of how URLSession framed it.
    func bodySteamData() -> Data? {
        guard let stream = httpBodyStream else { return nil }
        stream.open()
        defer { stream.close() }
        var data = Data()
        let size = 4096
        let buffer = UnsafeMutablePointer<UInt8>.allocate(capacity: size)
        defer { buffer.deallocate() }
        while stream.hasBytesAvailable {
            let read = stream.read(buffer, maxLength: size)
            if read <= 0 { break }
            data.append(buffer, count: read)
        }
        return data.isEmpty ? nil : data
    }
}
