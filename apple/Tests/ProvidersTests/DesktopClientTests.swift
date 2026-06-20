import XCTest
import Contracts
@testable import Providers

/// HSM-12-01 — the desktop client seam + pairing. Network stubbed via `URLProtocol`;
/// fully deterministic and offline (no real desktop). Proves: pairing → handshake
/// against /health + /api/runtime/status, an honest egress label, the token rides as
/// a Bearer header, and an unreachable peer fails soft (never throws → `.offline`).
final class DesktopClientTests: XCTestCase {

    // MARK: stub

    final class StubProtocol: URLProtocol {
        /// path -> (status, body). A missing path → network failure (simulated down).
        nonisolated(unsafe) static var routes: [String: (Int, Data)] = [:]
        nonisolated(unsafe) static var lastAuth: String??
        nonisolated(unsafe) static var failEverything = false
        override class func canInit(with request: URLRequest) -> Bool { true }
        override class func canonicalRequest(for r: URLRequest) -> URLRequest { r }
        override func startLoading() {
            StubProtocol.lastAuth = request.value(forHTTPHeaderField: "Authorization")
            let path = request.url?.path ?? ""
            if StubProtocol.failEverything || StubProtocol.routes[path] == nil {
                client?.urlProtocol(self, didFailWithError: URLError(.cannotConnectToHost))
                return
            }
            let (status, body) = StubProtocol.routes[path]!
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
        StubProtocol.failEverything = false
    }

    private func client(token: String? = nil) -> HTTPDesktopClient {
        HTTPDesktopClient(config: .init(baseURL: URL(string: "http://desk.tailnet:8000")!, token: token),
                          session: stubbedSession())
    }

    private func runtimeStatus(_ json: String) -> Data { Data(json.utf8) }

    // MARK: pairing

    func testPeerBuildsConfigFromHostPortToken() throws {
        let peer = DesktopPeer(host: "desk.tailnet", port: 8000, token: "t0ken")
        let config = try XCTUnwrap(HTTPDesktopClient.Config(peer: peer))
        XCTAssertEqual(config.baseURL.absoluteString, "http://desk.tailnet:8000")
        XCTAssertEqual(config.token, "t0ken")
    }

    func testMalformedPeerYieldsNoConfig() {
        // An empty host has no valid URL → no config (the client then stays offline).
        XCTAssertNil(HTTPDesktopClient.Config(peer: DesktopPeer(host: "", port: 0)))
    }

    // MARK: handshake — reachable

    func testHandshakeReachableAndRuntimeReady() async {
        StubProtocol.routes = [
            "/health": (200, Data(#"{"status":"ok"}"#.utf8)),
            "/api/runtime/status": (200, runtimeStatus(#"{"status":"ok","mode":"web","meeting_active":false}"#)),
        ]
        let conn = await client().handshake()
        XCTAssertTrue(conn.reachable)
        XCTAssertTrue(conn.runtimeReady)
        XCTAssertTrue(conn.detail.contains("web"))   // summary surfaces the mode
    }

    func testHandshakeSurfacesActiveMeeting() async {
        StubProtocol.routes = [
            "/health": (200, Data(#"{"status":"ok"}"#.utf8)),
            "/api/runtime/status": (200, runtimeStatus(#"{"status":"ok","mode":"web","meeting_active":true}"#)),
        ]
        let conn = await client().handshake()
        XCTAssertTrue(conn.runtimeReady)
        XCTAssertEqual(conn.detail, "meeting active")
    }

    func testHandshakeReachableButRuntimeStatusUnavailable() async {
        StubProtocol.routes = [
            "/health": (200, Data(#"{"status":"ok"}"#.utf8)),
            "/api/runtime/status": (500, Data()),
        ]
        let conn = await client().handshake()
        XCTAssertTrue(conn.reachable)        // health passed
        XCTAssertFalse(conn.runtimeReady)    // status did not
        XCTAssertEqual(conn.detail, "runtime status unavailable")
    }

    // MARK: handshake — offline (fail soft, never throw)

    func testHandshakeUnreachableFailsSoft() async {
        StubProtocol.failEverything = true   // peer down
        let conn = await client().handshake()   // must NOT throw — no try
        XCTAssertFalse(conn.reachable)
        XCTAssertFalse(conn.runtimeReady)
        XCTAssertTrue(conn.detail.hasPrefix("desktop unreachable"))
    }

    func testHandshakeBadHealthStatusIsOffline() async {
        StubProtocol.routes = ["/health": (404, Data())]
        let conn = await client().handshake()
        XCTAssertFalse(conn.reachable)
        XCTAssertTrue(conn.detail.contains("404"))
    }

    // MARK: egress + token

    func testEgressLabelIsHonest() {
        let label = client().egressLabel
        XCTAssertTrue(label.contains("LAN"))
        XCTAssertTrue(label.contains("desk.tailnet"))
    }

    func testTokenRidesAsBearerAndIsNotInEgress() async {
        StubProtocol.routes = [
            "/health": (200, Data(#"{"status":"ok"}"#.utf8)),
            "/api/runtime/status": (200, runtimeStatus(#"{"status":"ok"}"#)),
        ]
        let c = client(token: "s3cret")
        _ = await c.handshake()
        XCTAssertEqual(StubProtocol.lastAuth, "Bearer s3cret")   // joined at call time
        XCTAssertFalse(c.egressLabel.contains("s3cret"))         // never leaked to the badge
    }
}
