import XCTest
import Contracts
@testable import Providers

/// HSM-15-02 — the per-step mesh dispatch client: `runStep` rides the hub's ask
/// route (`POST /api/ask`) with an EMPTY context (the runner already resolved the
/// step's input into the prompt), decodes the output + the run's honest egress,
/// Bearer rides, non-2xx throws. Mirrors WorkflowRunClientTests' stub posture.
final class AskClientTests: XCTestCase {

    final class StubProtocol: URLProtocol {
        nonisolated(unsafe) static var routes: [String: (Int, Data)] = [:]
        nonisolated(unsafe) static var lastAuth: String??
        nonisolated(unsafe) static var lastBody: Data?
        override class func canInit(with request: URLRequest) -> Bool { true }
        override class func canonicalRequest(for r: URLRequest) -> URLRequest { r }
        override func startLoading() {
            StubProtocol.lastAuth = request.value(forHTTPHeaderField: "Authorization")
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
        StubProtocol.lastBody = nil
    }

    // The REAL route shape (primitives/ask.py api_ask): output + provider + the
    // run's honest egress + the model name.
    private let askJSON = #"""
    {
      "output": "MAC OUT",
      "lens": "Workbench",
      "provider": "cloud",
      "profile_id": null,
      "egress": {"scope": "cloud", "host": "192.168.1.43"},
      "model": "Qwen3.5-9B-Q6_K",
      "context_ids": [],
      "context_titles": []
    }
    """#

    func testRunStepPostsThePromptAndDecodesTheHonestEgress() async throws {
        StubProtocol.routes = ["/api/ask": (200, Data(askJSON.utf8))]
        let result = try await client(token: "tok").runStep(prompt: "Summarize: SRC")
        XCTAssertEqual(StubProtocol.lastAuth, "Bearer tok")

        let sent = try JSONSerialization.jsonObject(with: StubProtocol.lastBody ?? Data()) as? [String: Any]
        XCTAssertEqual(sent?["prompt"] as? String, "Summarize: SRC")
        XCTAssertEqual(sent?["lens"] as? String, "Workbench")
        XCTAssertEqual((sent?["context"] as? [Any])?.isEmpty, true,
                       "a dispatched step grounds nothing extra — the prompt IS the step")

        XCTAssertEqual(result.output, "MAC OUT")
        XCTAssertEqual(result.provider, "cloud")
        XCTAssertEqual(result.model, "Qwen3.5-9B-Q6_K")
        XCTAssertEqual(result.egress?.scope, "cloud")
        XCTAssertEqual(result.egress?.host, "192.168.1.43")
    }

    func testLocalRunDecodesWithoutHost() async throws {
        let body = #"{"output": "OUT", "provider": "local", "egress": {"scope": "local"}, "model": "Foo-9B"}"#
        StubProtocol.routes = ["/api/ask": (200, Data(body.utf8))]
        let result = try await client().runStep(prompt: "x")
        XCTAssertEqual(result.egress?.scope, "local")
        XCTAssertNil(result.egress?.host)
        XCTAssertEqual(result.model, "Foo-9B")
    }

    func testNon2xxThrows() async {
        StubProtocol.routes = ["/api/ask": (502, Data())]
        do { _ = try await client().runStep(prompt: "x"); XCTFail("expected throw") }
        catch let HTTPDesktopClient.DesktopClientError.http(code) { XCTAssertEqual(code, 502) }
        catch { XCTFail("wrong error: \(error)") }
    }
}
