import XCTest
import Contracts
@testable import Providers

/// HSM-5-06 — the OpenAI-compatible endpoint provider (Modes B/C). Network is
/// stubbed via `URLProtocol` so these run offline and deterministically: they
/// prove request shaping, response parsing, and error handling without a server.
final class EndpointProviderTests: XCTestCase {

    // A URLProtocol that answers from a script set per test — no real network.
    final class StubProtocol: URLProtocol {
        nonisolated(unsafe) static var handler: ((URLRequest) -> (Int, Data))?
        nonisolated(unsafe) static var lastBody: Data?
        nonisolated(unsafe) static var lastURL: URL?

        override class func canInit(with request: URLRequest) -> Bool { true }
        override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }
        override func startLoading() {
            StubProtocol.lastURL = request.url
            // URLProtocol strips httpBody into a stream for custom protocols; capture both.
            StubProtocol.lastBody = request.httpBody ?? request.httpBodyStream.map { stream in
                stream.open(); defer { stream.close() }
                var data = Data(); let n = 4096; var buf = [UInt8](repeating: 0, count: n)
                while stream.hasBytesAvailable {
                    let read = stream.read(&buf, maxLength: n)
                    if read <= 0 { break }
                    data.append(buf, count: read)
                }
                return data
            }
            let (status, body) = StubProtocol.handler?(request) ?? (500, Data())
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

    private func config() -> EndpointConfig {
        EndpointConfig(baseURL: URL(string: "http://192.168.1.43:8080/v1")!, model: "local")
    }

    func testCompletionParsesAssistantContent() async throws {
        StubProtocol.handler = { _ in
            let body = #"{"choices":[{"message":{"role":"assistant","content":"hello world"}}]}"#
            return (200, Data(body.utf8))
        }
        let provider = OpenAIEndpointProvider(config: config(), session: stubbedSession())
        let out = try await provider.complete(prompt: "hi")
        XCTAssertEqual(out, "hello world")
    }

    func testRequestShapeHitsChatCompletionsWithModelAndPrompt() async throws {
        StubProtocol.handler = { _ in (200, Data(#"{"choices":[{"message":{"content":"ok"}}]}"#.utf8)) }
        let provider = OpenAIEndpointProvider(config: config(), session: stubbedSession())
        _ = try await provider.complete(prompt: "summarize the meeting")

        XCTAssertEqual(StubProtocol.lastURL?.absoluteString,
                       "http://192.168.1.43:8080/v1/chat/completions")
        let body = try XCTUnwrap(StubProtocol.lastBody)
        let json = try XCTUnwrap(try JSONSerialization.jsonObject(with: body) as? [String: Any])
        XCTAssertEqual(json["model"] as? String, "local")
        XCTAssertEqual(json["stream"] as? Bool, false)
        let messages = try XCTUnwrap(json["messages"] as? [[String: Any]])
        XCTAssertEqual(messages.first?["role"] as? String, "user")
        XCTAssertEqual(messages.first?["content"] as? String, "summarize the meeting")
    }

    func testNon2xxThrowsHTTPError() async {
        StubProtocol.handler = { _ in (503, Data("overloaded".utf8)) }
        let provider = OpenAIEndpointProvider(config: config(), session: stubbedSession())
        do {
            _ = try await provider.complete(prompt: "x")
            XCTFail("expected http error")
        } catch let OpenAIEndpointProvider.ProviderError.http(status, body) {
            XCTAssertEqual(status, 503)
            XCTAssertTrue(body.contains("overloaded"))
        } catch { XCTFail("wrong error: \(error)") }
    }

    func testEmptyChoicesThrows() async {
        StubProtocol.handler = { _ in (200, Data(#"{"choices":[]}"#.utf8)) }
        let provider = OpenAIEndpointProvider(config: config(), session: stubbedSession())
        do {
            _ = try await provider.complete(prompt: "x")
            XCTFail("expected emptyCompletion")
        } catch OpenAIEndpointProvider.ProviderError.emptyCompletion {
            // expected
        } catch { XCTFail("wrong error: \(error)") }
    }

    func testBaseURLAlreadyIncludingRouteIsNotDoubled() {
        let cfg = EndpointConfig(
            baseURL: URL(string: "http://h:8080/v1/chat/completions")!, model: "m")
        let provider = OpenAIEndpointProvider(config: cfg)
        XCTAssertEqual(provider.chatCompletionsURL().absoluteString,
                       "http://h:8080/v1/chat/completions")
    }

    // The factory makes mode selection a setting (owner steer 2026-06-19).
    func testFactoryReturnsEndpointProviderForRemoteModes() throws {
        let p = try InferenceProviderFactory.make(mode: .homelab, endpoint: config())
        XCTAssertTrue(p is OpenAIEndpointProvider)
    }

    func testFactoryLocalUnavailableUntilEngineLands() {
        XCTAssertThrowsError(try InferenceProviderFactory.make(mode: .local)) {
            XCTAssertEqual($0 as? InferenceSettingsError, .localEngineUnavailable)
        }
    }

    func testFactoryEndpointModeRequiresConfig() {
        XCTAssertThrowsError(try InferenceProviderFactory.make(mode: .endpoint, endpoint: nil)) {
            XCTAssertEqual($0 as? InferenceSettingsError, .endpointNotConfigured)
        }
    }
}
