import XCTest
import Contracts
@testable import Providers

/// HSM-18-02 — the iPad CommandsBoard client. Network stubbed via `URLProtocol`;
/// fully deterministic and offline. Proves: the `dictation.macros` block decodes
/// out of the full settings payload (and defaults off/empty on an older hub),
/// the PUT sends ONLY the deep-merge macros slice, the test route round-trips
/// (incl. the `type_text` preview-only case), and an HTTP error throws.
final class CommandsClientTests: XCTestCase {

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
            if let stream = request.httpBodyStream {
                stream.open(); defer { stream.close() }
                var data = Data()
                let buf = UnsafeMutablePointer<UInt8>.allocate(capacity: 1024)
                defer { buf.deallocate() }
                while stream.hasBytesAvailable {
                    let n = stream.read(buf, maxLength: 1024)
                    if n <= 0 { break }
                    data.append(buf, count: n)
                }
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

    override func setUp() {
        super.setUp()
        StubProtocol.routes = [:]
        StubProtocol.lastAuth = nil
        StubProtocol.lastBody = nil
    }

    private func client(token: String? = nil) -> HTTPDesktopClient {
        HTTPDesktopClient(config: .init(baseURL: URL(string: "http://desk.tailnet:8000")!, token: token),
                          session: stubbedSession())
    }

    func testMacroSettingsDecodeOutOfTheFullSettingsPayload() async throws {
        // The settings route returns the WHOLE config; only dictation.macros is ours.
        StubProtocol.routes = ["/api/settings": (200, Data(#"""
        {"hotkey":{"key":"alt_r"},
         "dictation":{"pipeline":{"enabled":true},
                      "macros":{"enabled":true,
                                "items":[{"keyword":"standup",
                                          "action":{"kind":"type_text","payload":"## Standup"}},
                                         {"keyword":"logs",
                                          "action":{"kind":"shell","payload":"tail -f /tmp/x.log"}}]}},
         "_runtime_status":{"counters":{}}}
        """#.utf8))]
        let settings = try await client(token: "tok").macroSettings()
        XCTAssertEqual(StubProtocol.lastAuth, "Bearer tok")
        XCTAssertTrue(settings.enabled)
        XCTAssertEqual(settings.items.count, 2)
        XCTAssertEqual(settings.items[0].keyword, "standup")
        XCTAssertEqual(settings.items[0].action.preview, "types: ## Standup")
        XCTAssertEqual(settings.items[1].action.preview, "runs: tail -f /tmp/x.log")
    }

    func testOlderHubWithoutMacrosDecodesAsDefaultOff() async throws {
        StubProtocol.routes = ["/api/settings": (200, Data(#"{"hotkey":{"key":"alt_r"}}"#.utf8))]
        let settings = try await client().macroSettings()
        XCTAssertFalse(settings.enabled)
        XCTAssertTrue(settings.items.isEmpty)
    }

    func testUpdateSendsOnlyTheMacrosSlice() async throws {
        StubProtocol.routes = ["/api/settings": (200, Data(#"{"success":true}"#.utf8))]
        try await client().updateMacroSettings(VoiceMacroSettings(
            enabled: true,
            items: [VoiceMacroSpec(keyword: "standup",
                                   action: VoiceMacroActionSpec(kind: "type_text", payload: "## Standup"))]))
        XCTAssertEqual(StubProtocol.lastMethod, "PUT")
        let body = try XCTUnwrap(JSONSerialization.jsonObject(
            with: XCTUnwrap(StubProtocol.lastBody)) as? [String: Any])
        XCTAssertEqual(Array(body.keys), ["dictation"])   // the deep-merge slice, nothing else
        let macros = try XCTUnwrap((body["dictation"] as? [String: Any])?["macros"] as? [String: Any])
        XCTAssertEqual(macros["enabled"] as? Bool, true)
        let items = try XCTUnwrap(macros["items"] as? [[String: Any]])
        XCTAssertEqual(items.count, 1)
        XCTAssertEqual(items[0]["keyword"] as? String, "standup")
    }

    func testTestMacroRoundTripsAndTypeTextIsPreviewOnly() async throws {
        StubProtocol.routes = ["/api/commands/test": (200, Data(#"""
        {"ok":true,"tested":false,"preview":"types: ## Standup","note":"types into the focused app"}
        """#.utf8))]
        let result = try await client().testMacro(kind: "type_text", payload: "## Standup")
        XCTAssertTrue(result.ok)
        XCTAssertEqual(result.tested, false)
        XCTAssertEqual(result.preview, "types: ## Standup")
        let body = try XCTUnwrap(JSONSerialization.jsonObject(
            with: XCTUnwrap(StubProtocol.lastBody)) as? [String: Any])
        XCTAssertEqual(body["kind"] as? String, "type_text")
    }

    func testHTTPErrorThrows() async {
        StubProtocol.routes = ["/api/settings": (500, Data())]
        do { _ = try await client().macroSettings(); XCTFail("expected throw") }
        catch HTTPDesktopClient.DesktopClientError.http(let code) { XCTAssertEqual(code, 500) }
        catch { XCTFail("wrong error: \(error)") }
    }
}
