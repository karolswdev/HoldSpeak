import XCTest
import Contracts
@testable import Providers

/// HSM-26-03 — the steering client over a stubbed network (URLProtocol, fully
/// offline). Proves the iPad speaks the Phase-87 consent spine: watch (peek),
/// arm (the grant or a typed refusal), steer (delivered or a first-class
/// refusal — a 409 is DATA, never a thrown toast), disarm, and the audit trail.
final class SteeringClientTests: XCTestCase {

    final class StubProtocol: URLProtocol {
        nonisolated(unsafe) static var routes: [String: (Int, Data)] = [:]
        nonisolated(unsafe) static var lastBody: Data?
        override class func canInit(with request: URLRequest) -> Bool { true }
        override class func canonicalRequest(for r: URLRequest) -> URLRequest { r }
        override func startLoading() {
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
        StubProtocol.lastBody = nil
    }

    private func client() -> HTTPDesktopClient {
        HTTPDesktopClient(config: .init(baseURL: URL(string: "http://desk.tailnet:8000")!, token: "t"),
                          session: stubbedSession())
    }

    private func route(_ path: String, _ status: Int, _ json: String) {
        StubProtocol.routes[path] = (status, Data(json.utf8))
    }

    func testPeekReturnsTheLivePane() async throws {
        route("/api/coders/claude:s1/peek", 200, #"""
        {"key":"claude:s1","agent":"claude","stale":false,"awaiting_response":true,
         "question":"merge?","updated_at":"2026-07-08T10:00:00Z",
         "grant":{"armed":true,"expires_in_seconds":840},
         "peek":{"status":"live","hash":"abc","lines":["$ make","ok"]}}
        """#)
        let peek = try await client().coderPeek(key: "claude:s1")
        XCTAssertEqual(peek.peek.status, "live")
        XCTAssertEqual(peek.peek.lines?.count, 2)
        XCTAssertTrue(peek.grant.armed)
        XCTAssertEqual(peek.grant.expiresInSeconds, 840)
    }

    func testArmReturnsTheGrant() async throws {
        route("/api/coders/claude:s1/arm", 200,
              #"{"status":"armed","key":"claude:s1","pane_id":"%5","expires_in_seconds":900}"#)
        let res = try await client().armCoder(key: "claude:s1")
        XCTAssertTrue(res.isArmed)
        XCTAssertEqual(res.paneId, "%5")
        XCTAssertEqual(res.expiresInSeconds, 900)
    }

    func testArmRefusalIsDataNotAnError() async throws {
        // A 409 stale-session refusal decodes into the result, never throws.
        route("/api/coders/claude:s1/arm", 409,
              #"{"status":"stale_session","detail":"registry record is 2700s old — a stale session cannot be armed"}"#)
        let res = try await client().armCoder(key: "claude:s1")
        XCTAssertFalse(res.isArmed)
        XCTAssertEqual(res.status, "stale_session")
        XCTAssertTrue(res.detail?.contains("stale session") == true)
    }

    func testDisarmIsIdempotentResult() async throws {
        route("/api/coders/claude:s1/disarm", 200,
              #"{"status":"disarmed","key":"claude:s1","was_armed":true}"#)
        let res = try await client().disarmCoder(key: "claude:s1")
        XCTAssertTrue(res.wasArmed)
    }

    func testSteerDeliversAndCarriesGrounding() async throws {
        route("/api/coders/claude:s1/steer", 200,
              #"{"status":"delivered","pane_id":"%5","submitted":false,"audit_id":7}"#)
        let refs = [RailsGroundingRef(repo: "holdspeak", project: "holdspeak", kind: "story", id: "HS-88-05")]
        let res = try await client().steerCoder(key: "claude:s1", text: "ship it", submit: false, grounding: refs)
        XCTAssertTrue(res.isDelivered)
        XCTAssertEqual(res.paneId, "%5")
        // The grounding rides the body as rails refs.
        let sent = String(decoding: StubProtocol.lastBody ?? Data(), as: UTF8.self)
        XCTAssertTrue(sent.contains("\"rails\""))
        XCTAssertTrue(sent.contains("HS-88-05"))
    }

    func testSteerRefusalRevokesAndReoffersARM() async throws {
        // The crown case: a recycled-pane steer refuses AND revokes — the shape
        // alone tells the surface to re-offer ARM.
        route("/api/coders/claude:s1/steer", 409,
              #"{"status":"pane_mismatch","revoked":true,"detail":"pane '%13' is not the armed '%5' — nothing was typed","audit_id":8}"#)
        let res = try await client().steerCoder(key: "claude:s1", text: "too late")
        XCTAssertFalse(res.isDelivered)
        XCTAssertEqual(res.status, "pane_mismatch")
        XCTAssertTrue(res.didRevoke)
    }

    func testAuditTrailDecodes() async throws {
        route("/api/coders/steering/audit", 200, #"""
        {"audit":[{"id":7,"ts":"2026-07-08T10:00:00Z","session_key":"claude:s1","agent":"claude",
         "pane_id":"%5","text_sha256":"abc","text_head":"ship it","grounding":["rails:story:HS-88-05"],
         "submit":false,"outcome":"delivered","detail":null}]}
        """#)
        let trail = try await client().steeringAudit(sessionKey: "claude:s1")
        XCTAssertEqual(trail.count, 1)
        XCTAssertEqual(trail[0].outcome, "delivered")
        XCTAssertEqual(trail[0].grounding, ["rails:story:HS-88-05"])
    }
}
