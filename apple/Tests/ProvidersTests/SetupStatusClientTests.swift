import XCTest
import Contracts
@testable import Providers

/// HSM-21-04 — the setup-status client + the four-posture mapping the trust chip
/// renders. The mapping MUST match web/src/scripts/trust-view.js `trustPosture`
/// (attention → writes → endpoint → local, in that precedence) so both surfaces
/// state the same truth. Mirrors AftercareClientTests' stub posture.
final class SetupStatusClientTests: XCTestCase {

    final class StubProtocol: URLProtocol {
        nonisolated(unsafe) static var routes: [String: (Int, Data)] = [:]
        nonisolated(unsafe) static var lastAuth: String??
        nonisolated(unsafe) static var lastMethod: String?
        override class func canInit(with request: URLRequest) -> Bool { true }
        override class func canonicalRequest(for r: URLRequest) -> URLRequest { r }
        override func startLoading() {
            StubProtocol.lastAuth = request.value(forHTTPHeaderField: "Authorization")
            StubProtocol.lastMethod = request.httpMethod
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
    }

    private func client(token: String? = nil) -> HTTPDesktopClient {
        HTTPDesktopClient(config: .init(baseURL: URL(string: "http://desk.tailnet:8000")!, token: token),
                          session: stubbedSession())
    }

    // The real route's shape (build_setup_status): snake_case, more fields than we read.
    private let statusJSON = #"""
    {
      "version": "0.3.1",
      "overall": "ready",
      "first_run": false,
      "primary_action": {"kind": "none"},
      "sections": [
        {"id": "microphone", "label": "Microphone", "status": "pass", "detail": "Input device found", "fix": null},
        {"id": "whisper-model", "label": "Whisper model", "status": "warn", "detail": "Not downloaded", "fix": "holdspeak setup"}
      ],
      "trust": {
        "web_bind": "0.0.0.0",
        "auth_token_set": true,
        "transcript_egress": "possible",
        "egress_detail": "Auto: local first.",
        "configured_endpoints": ["http://192.168.1.43:8080/v1"],
        "actuators_enabled": false,
        "webhook_allowed_hosts": []
      },
      "presence": {"enabled": false, "available": true, "tier": "hud"}
    }
    """#

    func testDecodesTheChipSliceAndSendsBearer() async throws {
        StubProtocol.routes = ["/api/setup/status": (200, Data(statusJSON.utf8))]
        let status = try await client(token: "tok").setupStatus()
        XCTAssertEqual(StubProtocol.lastMethod, "GET")
        XCTAssertEqual(StubProtocol.lastAuth, "Bearer tok")
        XCTAssertEqual(status.overall, "ready")
        XCTAssertEqual(status.firstRun, false)
        XCTAssertEqual(status.trust?.webBind, "0.0.0.0")
        XCTAssertEqual(status.trust?.authTokenSet, true)
        XCTAssertEqual(status.trust?.transcriptEgress, "possible")
        XCTAssertEqual(status.trust?.actuatorsEnabled, false)
        // HSM-23-03 — the doctor sections reach the readiness panel (real
        // `_section_from_check` shape: id/label/status/detail, status vocab
        // pass|warn|fail|unknown; `fix` is not carried).
        XCTAssertEqual(status.sections?.count, 2)
        XCTAssertEqual(status.sections?[0].id, "microphone")
        XCTAssertEqual(status.sections?[0].label, "Microphone")
        XCTAssertEqual(status.sections?[0].status, "pass")
        XCTAssertEqual(status.sections?[0].detail, "Input device found")
        XCTAssertEqual(status.sections?[1].status, "warn")
    }

    func testMissingSectionsDecodeAsNil() throws {
        // An older hub without a sections block must not fail the decode.
        let bare = #"{"version": "0.3.0", "overall": "ready"}"#
        let status = try HoldSpeakContracts.decoder().decode(SetupStatus.self, from: Data(bare.utf8))
        XCTAssertNil(status.sections)
        XCTAssertEqual(status.overall, "ready")
    }

    func testNon2xxThrows() async {
        StubProtocol.routes = ["/api/setup/status": (500, Data())]
        do { _ = try await client().setupStatus(); XCTFail("expected throw") }
        catch let HTTPDesktopClient.DesktopClientError.http(code) { XCTAssertEqual(code, 500) }
        catch { XCTFail("wrong error: \(error)") }
    }

    // MARK: the four-posture precedence (must mirror trust-view.js trustPosture)

    private func status(bind: String = "127.0.0.1", token: Bool = false,
                        egress: String = "none", actuators: Bool = false) -> SetupStatus {
        SetupStatus(trust: SetupTrust(webBind: bind, authTokenSet: token,
                                      transcriptEgress: egress, actuatorsEnabled: actuators))
    }

    func testPosturePrecedenceMatchesTheWebChip() {
        XCTAssertEqual(status(bind: "0.0.0.0", token: false).posture, .attention)
        // A token heals the off-loopback bind; actuators then lead.
        XCTAssertEqual(status(bind: "0.0.0.0", token: true, actuators: true).posture, .writesNeedApproval)
        XCTAssertEqual(status(egress: "possible").posture, .configuredEndpoint)
        XCTAssertEqual(status(egress: "configured").posture, .configuredEndpoint)
        XCTAssertEqual(status().posture, .localOnly)
        // Attention outranks everything (the web chip's order).
        XCTAssertEqual(status(bind: "0.0.0.0", token: false, egress: "configured",
                              actuators: true).posture, .attention)
        // Writes outrank the endpoint posture.
        XCTAssertEqual(status(egress: "configured", actuators: true).posture, .writesNeedApproval)
        // A missing trust block is the calm default, never a scare.
        XCTAssertEqual(SetupStatus().posture, .localOnly)
    }

    func testPostureLabelsAreTheChipWords() {
        XCTAssertEqual(TrustPosture.attention.label, "Needs attention")
        XCTAssertEqual(TrustPosture.writesNeedApproval.label, "Writes need approval")
        XCTAssertEqual(TrustPosture.configuredEndpoint.label, "Configured endpoint")
        XCTAssertEqual(TrustPosture.localOnly.label, "Local only")
    }
}
