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
         "pane_id":"%5",
         "arm_commitment":"Arm pane %5 for 15 minutes",
         "grant":{"armed":true,"expires_in_seconds":840},
         "operation":{"effect_class":"terminal/type_text_and_keys","destination":"%5"},
         "policy":{"mode":"yolo","outcome":"allowed","reason_code":"registered_steering_posture_allowed","authority_basis":"control_posture","policy_version":"operation-policy/v2"},
         "peek":{"status":"live","hash":"abc","lines":["$ make","ok"]}}
        """#)
        let peek = try await client().coderPeek(key: "claude:s1")
        XCTAssertEqual(peek.peek.status, "live")
        XCTAssertEqual(peek.peek.lines?.count, 2)
        XCTAssertTrue(peek.grant.armed)
        XCTAssertEqual(peek.grant.expiresInSeconds, 840)
        XCTAssertEqual(peek.paneId, "%5")
        XCTAssertEqual(peek.armCommitment, "Arm pane %5 for 15 minutes")
        XCTAssertTrue(peek.policy?.usesControlPosture == true)
        XCTAssertEqual(peek.policy?.reasonCode, "registered_steering_posture_allowed")
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
              #"{"status":"delivered","pane_id":"%5","submitted":false,"audit_id":7,"policy":{"mode":"yolo","outcome":"allowed","authority_basis":"control_posture"},"receipt":{"id":"steering:7","source_ref":"coder_session:claude:s1","actual_destination":"%5","authority_basis":"control_posture","control_mode":"yolo","policy_version":"operation-policy/v2","effect_class":"terminal/type_text_and_keys","outcome":"delivered"}}"#)
        let refs = [RailsGroundingRef(repo: "holdspeak", project: "holdspeak", kind: "story", id: "HS-88-05")]
        let res = try await client().steerCoder(
            key: "claude:s1", text: "ship it", submit: false,
            expectedPaneId: "%5", grounding: refs
        )
        XCTAssertTrue(res.isDelivered)
        XCTAssertEqual(res.paneId, "%5")
        XCTAssertEqual(res.receipt?.id, "steering:7")
        XCTAssertTrue(res.policy?.usesControlPosture == true)
        // The grounding rides the body as rails refs.
        let sent = String(decoding: StubProtocol.lastBody ?? Data(), as: UTF8.self)
        XCTAssertTrue(sent.contains("\"rails\""))
        XCTAssertTrue(sent.contains("HS-88-05"))
        XCTAssertTrue(sent.contains("\"expected_pane_id\":\"%5\""))
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
         "submit":false,"outcome":"delivered","detail":null,
         "operation":{"effect_class":"terminal/type_text_and_keys","destination":"%5"},
         "policy_snapshot":{"mode":"yolo","authority_basis":"control_posture","policy_version":"operation-policy/v2"}}]}
        """#)
        let trail = try await client().steeringAudit(sessionKey: "claude:s1")
        XCTAssertEqual(trail.count, 1)
        XCTAssertEqual(trail[0].outcome, "delivered")
        XCTAssertEqual(trail[0].grounding, ["rails:story:HS-88-05"])
        XCTAssertEqual(trail[0].policySnapshot?.authorityBasis, "control_posture")
    }

    // MARK: - Phase-89/90 parity (the iPad catches up)

    func testKeysDeliverNamedAndLiteral() async throws {
        route("/api/coders/claude:s1/keys", 200,
              #"{"status":"delivered","pane_id":"%5","keys":"C-c"}"#)
        let res = try await client().coderKeys(
            key: "claude:s1", keys: [.interrupt, .literal("/find"), .down],
            expectedPaneId: "%5"
        )
        XCTAssertTrue(res.isDelivered)
        let sent = String(decoding: StubProtocol.lastBody ?? Data(), as: UTF8.self)
        XCTAssertTrue(sent.contains("\"C-c\""))       // a named key is a bare string
        XCTAssertTrue(sent.contains("\"literal\""))   // a literal run is an object
        XCTAssertTrue(sent.contains("/find"))
        XCTAssertTrue(sent.contains("\"expected_pane_id\":\"%5\""))
    }

    func testKeysRefusalIsData() async throws {
        // A recycled-pane keys refusal comes back 409 → SteerResult, revoking.
        route("/api/coders/claude:s1/keys", 409,
              #"{"status":"pane_mismatch","revoked":true,"detail":"recycled"}"#)
        let res = try await client().coderKeys(key: "claude:s1", keys: [.interrupt])
        XCTAssertFalse(res.isDelivered)
        XCTAssertTrue(res.didRevoke)
    }

    func testKeysToANodeRouteThroughTheRelayWithKeyInBody() async throws {
        route("/api/coders/relay/beta/keys", 200, #"{"status":"delivered","node":"beta","pane_id":"%5"}"#)
        let res = try await client().coderKeys(
            key: "pane:%5", keys: [.interrupt], expectedPaneId: "%5", node: "beta"
        )
        XCTAssertTrue(res.isDelivered)
        let sent = String(decoding: StubProtocol.lastBody ?? Data(), as: UTF8.self)
        XCTAssertTrue(sent.contains("\"key\""))        // the key rides the BODY on the relay
        XCTAssertTrue(sent.contains("pane:%5"))
        XCTAssertTrue(sent.contains("\"expected_pane_id\":\"%5\""))
    }

    func testDisarmToANodeRoutesThroughTheRelayWithKeyInBody() async throws {
        // Regression (HS-94-09 / the Phase-94 audit): disarm did NOT route to
        // the session's node, so a remote-armed grant survived a native
        // disarm. ONLY the relay route is stubbed here — hitting the local
        // `/api/coders/{key}/disarm` path would fail the request outright, so
        // a passing call proves the node-routed path was taken.
        route("/api/coders/relay/beta/disarm", 200,
              #"{"status":"disarmed","key":"pane:%5","was_armed":true,"node":"beta"}"#)
        let res = try await client().disarmCoder(key: "pane:%5", node: "beta")
        XCTAssertEqual(res.status, "disarmed")
        XCTAssertTrue(res.wasArmed)                    // the FAR grant is gone
        let sent = String(decoding: StubProtocol.lastBody ?? Data(), as: UTF8.self)
        XCTAssertTrue(sent.contains("\"key\""))        // the key rides the BODY on the relay
        XCTAssertTrue(sent.contains("pane:%5"))
    }

    func testDisarmWithoutANodeStaysOnTheLocalRoute() async throws {
        route("/api/coders/pane:%5/disarm", 200,
              #"{"status":"disarmed","key":"pane:%5","was_armed":false}"#)
        let res = try await client().disarmCoder(key: "pane:%5")
        XCTAssertEqual(res.status, "disarmed")
        XCTAssertFalse(res.wasArmed)
    }

    func testSteerToANodeRoutesThroughTheRelay() async throws {
        route("/api/coders/relay/beta/steer", 200, #"{"status":"delivered","node":"beta","pane_id":"%5"}"#)
        let res = try await client().steerCoder(key: "pane:%5", text: "hi", node: "beta")
        XCTAssertTrue(res.isDelivered)
        XCTAssertTrue(String(decoding: StubProtocol.lastBody ?? Data(), as: UTF8.self).contains("\"key\""))
    }

    func testPanesListDecodes() async throws {
        route("/api/coders/steering/panes", 200, #"""
        {"panes":[{"pane_id":"%3","session":"work","window":"0","command":"claude","title":"","active":true},
                  {"pane_id":"%7","session":"build","window":"1","command":"npm","title":"","active":false}]}
        """#)
        let panes = try await client().steeringPanes()
        XCTAssertEqual(panes.count, 2)
        XCTAssertEqual(panes[0].paneId, "%3")
        XCTAssertEqual(panes[0].command, "claude")
        XCTAssertEqual(panes[0].active, true)
    }

    func testNodesListDecodes() async throws {
        route("/api/coders/steering/nodes", 200, #"{"nodes":["beta","gamma"]}"#)
        let nodes = try await client().steeringNodes()
        XCTAssertEqual(nodes, ["beta", "gamma"])
    }

    func testKillDeliversAndRefusalIsData() async throws {
        route("/api/coders/pane:%5/kill", 200, #"{"status":"killed","pane_id":"%5","scope":"session"}"#)
        let killed = try await client().killCoder(key: "pane:%5", scope: "session")
        XCTAssertTrue(killed.isKilled)
        XCTAssertEqual(killed.scope, "session")

        route("/api/coders/pane:%5/kill", 409, #"{"status":"unarmed"}"#)
        let refused = try await client().killCoder(key: "pane:%5")
        XCTAssertFalse(refused.isKilled)
        XCTAssertEqual(refused.status, "unarmed")
    }

    func testSpawnReturnsThePaneKeyAndBadNameIsData() async throws {
        route("/api/coders/factory/spawn", 200, #"{"status":"spawned","session":"work","pane_id":"%9"}"#)
        let ok = try await client().spawnSession(name: "work", command: "bash")
        XCTAssertTrue(ok.isOk)
        XCTAssertEqual(ok.paneKey, "pane:%9")   // ready to attach

        route("/api/coders/factory/spawn", 409, #"{"status":"bad_name","detail":"no"}"#)
        let bad = try await client().spawnSession(name: "a b")
        XCTAssertFalse(bad.isOk)
        XCTAssertEqual(bad.status, "bad_name")
    }

    func testRenameRelabels() async throws {
        route("/api/coders/factory/rename", 200, #"{"status":"renamed","session":"shipped"}"#)
        let res = try await client().renameSession(target: "work", name: "shipped")
        XCTAssertTrue(res.isOk)
        XCTAssertEqual(res.session, "shipped")
    }
}
