import XCTest
import Contracts
@testable import Providers

/// HSM-22-04 — the workflow hub-run client: the graph run's envelope (object
/// steps + the honest `warning`) decodes off the REAL route shape, Bearer rides,
/// non-2xx throws. Mirrors SetupStatusClientTests' stub posture.
final class WorkflowRunClientTests: XCTestCase {

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

    // The REAL route shape (workflows.py api_run_workflow): a graph run with the
    // per-node object trail — the shape `HubRunResult` (string steps) cannot carry.
    private let runJSON = #"""
    {
      "workflow_id": "wf-1",
      "output": "risk: the demo",
      "provider": "local",
      "steps": [
        {"node_id": "n1", "kind": "summarize", "provider": "local",
         "failure_policy": null, "runs_on": "auto", "status": "ok"},
        {"node_id": "n2", "kind": "keep_if", "provider": null,
         "failure_policy": "skip", "runs_on": "onDevice", "status": "ok"}
      ],
      "sources": [{"source_type": "workflow", "source_ref": "wf-1"}],
      "artifact_id": "art_123",
      "result_ref": "artifact:art_123",
      "invocation_id": "invocation_1",
      "correlation_id": "invocation_1",
      "invocation": {
        "id": "invocation_1", "correlation_id": "invocation_1",
        "definition_ref": "workflow:wf-1", "initiator": "owner",
        "grounding_refs": ["note:n1"], "requested_placement": "this_machine",
        "input_snapshot": {"input": "the meeting"}, "state": "succeeded",
        "result_ref": "artifact:art_123", "error": null,
        "created_at": "2026-07-11T12:00:00Z", "updated_at": "2026-07-11T12:00:01Z",
        "completed_at": "2026-07-11T12:00:01Z",
        "attempts": [{
          "id": "attempt_1", "invocation_id": "invocation_1", "attempt_index": 1,
          "destination": "this_machine", "provider": "local", "state": "succeeded",
          "error": null, "result_ref": "artifact:art_123",
          "started_at": "2026-07-11T12:00:00Z", "completed_at": "2026-07-11T12:00:01Z"
        }]
      }
    }
    """#

    func testDecodesTheGraphRunEnvelope() async throws {
        StubProtocol.routes = ["/api/workflows/wf-1/run": (200, Data(runJSON.utf8))]
        let result = try await client(token: "tok").runWorkflow(id: "wf-1", input: "the meeting")
        XCTAssertEqual(StubProtocol.lastAuth, "Bearer tok")
        // The input rode as JSON.
        let sent = try JSONSerialization.jsonObject(with: StubProtocol.lastBody ?? Data()) as? [String: Any]
        XCTAssertEqual(sent?["input"] as? String, "the meeting")

        XCTAssertEqual(result.output, "risk: the demo")
        XCTAssertEqual(result.provider, "local")
        XCTAssertEqual(result.artifactId, "art_123")
        XCTAssertEqual(result.resultRef, "artifact:art_123")
        XCTAssertEqual(result.invocationId, "invocation_1")
        XCTAssertEqual(result.invocation?.definitionRef, "workflow:wf-1")
        XCTAssertEqual(result.invocation?.attempts.first?.destination, "this_machine")
        XCTAssertNil(result.warning)
        XCTAssertEqual(result.steps?.count, 2)
        XCTAssertEqual(result.steps?[0].nodeId, "n1")
        XCTAssertEqual(result.steps?[0].kind, "summarize")
        XCTAssertEqual(result.steps?[1].failurePolicy, "skip")
        XCTAssertEqual(result.steps?[1].runsOn, "onDevice")
    }

    func testLegacyWarningStillDecodes() async throws {
        // Backward compatibility with a pre-HS-92-06 hub that lowered graphs.
        let body = #"{"workflow_id": "wf-1", "output": "OUT", "provider": "local", "warning": "control-flow nodes present; prompt fallback ran", "artifact_id": "art_9"}"#
        StubProtocol.routes = ["/api/workflows/wf-1/run": (200, Data(body.utf8))]
        let result = try await client().runWorkflow(id: "wf-1", input: "x")
        XCTAssertEqual(result.output, "OUT")
        XCTAssertNil(result.steps)
        XCTAssertTrue(result.warning?.contains("control-flow") == true)
    }

    func testNon2xxThrows() async {
        StubProtocol.routes = ["/api/workflows/wf-1/run": (502, Data())]
        do { _ = try await client().runWorkflow(id: "wf-1", input: "x"); XCTFail("expected throw") }
        catch let HTTPDesktopClient.DesktopClientError.http(code) { XCTAssertEqual(code, 502) }
        catch { XCTFail("wrong error: \(error)") }
    }
}
