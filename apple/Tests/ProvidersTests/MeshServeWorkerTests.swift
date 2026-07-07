import XCTest
import Contracts
@testable import Providers

/// HSM-25-01 — the Swift relay worker on the provider seam. Network stubbed
/// via `URLProtocol`; fully deterministic and offline (no real hub). Proves:
/// claim → execute on THIS device's provider → complete verbatim; node-side
/// failure → fail verbatim; hub outage → exponential backoff without dying;
/// cancel stops cleanly; the recursion guard refuses by name; the token rides
/// as Bearer and only there.
final class MeshServeWorkerTests: XCTestCase {

    // MARK: stub — request-scripted so one path can answer differently per call

    final class MeshStub: URLProtocol {
        /// Consumed front-to-back per matching path; a missing script entry →
        /// simulated network failure (the hub is down).
        nonisolated(unsafe) static var script: [(path: String, status: Int, body: String)] = []
        nonisolated(unsafe) static var requests: [(path: String, auth: String?, body: [String: Any])] = []

        override class func canInit(with request: URLRequest) -> Bool { true }
        override class func canonicalRequest(for r: URLRequest) -> URLRequest { r }

        override func startLoading() {
            let path = request.url?.path ?? ""
            var body: [String: Any] = [:]
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
                body = (try? JSONSerialization.jsonObject(with: data) as? [String: Any]) ?? [:]
            }
            MeshStub.requests.append((path, request.value(forHTTPHeaderField: "Authorization"), body))

            guard let i = MeshStub.script.firstIndex(where: { $0.path == path }) else {
                client?.urlProtocol(self, didFailWithError: URLError(.cannotConnectToHost))
                return
            }
            let entry = MeshStub.script.remove(at: i)
            let resp = HTTPURLResponse(url: request.url!, statusCode: entry.status,
                                       httpVersion: nil, headerFields: nil)!
            client?.urlProtocol(self, didReceive: resp, cacheStoragePolicy: .notAllowed)
            client?.urlProtocol(self, didLoad: Data(entry.body.utf8))
            client?.urlProtocolDidFinishLoading(self)
        }
        override func stopLoading() {}
    }

    override func setUp() {
        super.setUp()
        MeshStub.script = []
        MeshStub.requests = []
    }

    private func client(token: String? = "s3cret") -> HTTPDesktopClient {
        let cfg = URLSessionConfiguration.ephemeral
        cfg.protocolClasses = [MeshStub.self]
        return HTTPDesktopClient(
            config: .init(baseURL: URL(string: "http://hub.local:8765")!, token: token),
            session: URLSession(configuration: cfg))
    }

    private struct EchoProvider: ILLMProvider {
        var answer = "The mesh is a set of your own machines."
        var thrown: String?
        func complete(prompt: String) async throws -> String {
            if let thrown { throw MeshServeRefusal(thrown) }
            return answer
        }
    }

    private static let jobJSON = """
    {"job": {"id": "relay_1", "node": "phone-edge", "task_kind": "llm",
             "system_prompt": "Be brief.", "user_prompt": "What is the mesh?",
             "temperature": 0.2, "max_tokens": 400, "model_hint": "gemma4",
             "status": "running", "deadline_at": "2026-07-07T12:02:00"}}
    """
    private static let idleJSON = #"{"job": null}"#

    /// Drive `run()` deterministically: injected sleep records its delays and
    /// cancels the loop after `stopAfterSleeps` naps, so no test ever waits.
    private func serve(
        worker sleepsToStop: Int, client: HTTPDesktopClient,
        provider: EchoProvider = EchoProvider(),
        makeProvider: (@Sendable () async throws -> any ILLMProvider)? = nil
    ) async -> (sleeps: [Double], stats: MeshServeWorker.Stats) {
        let recorder = SleepRecorder(stopAfter: sleepsToStop)
        let worker = MeshServeWorker(
            node: "phone-edge", client: client,
            makeProvider: makeProvider ?? { provider },
            sleep: { await recorder.record($0) },
            log: { _ in })
        let task = Task { await worker.run() }
        await recorder.arm(task)
        await task.value
        return (await recorder.delays, await worker.stats)
    }

    private actor SleepRecorder {
        var delays: [Double] = []
        private let stopAfter: Int
        private var task: Task<Void, Never>?
        init(stopAfter: Int) { self.stopAfter = stopAfter }
        func arm(_ t: Task<Void, Never>) { task = t }
        func record(_ seconds: Double) {
            delays.append(seconds)
            if delays.count >= stopAfter { task?.cancel() }
        }
    }

    // MARK: the loop

    func testClaimExecuteCompleteVerbatim() async throws {
        MeshStub.script = [
            ("/api/mesh/relay/claim", 200, Self.jobJSON),
            ("/api/mesh/relay/relay_1/complete", 200, "{}"),
            ("/api/mesh/relay/claim", 200, Self.idleJSON),
        ]
        let (_, stats) = await serve(worker: 1, client: client())

        let complete = MeshStub.requests.first { $0.path.hasSuffix("/complete") }
        XCTAssertEqual(complete?.body["result"] as? String,
                       "The mesh is a set of your own machines.")
        XCTAssertEqual(stats.jobsServed, 1)
        // the claim body names THIS node, and the token rides as Bearer
        let claim = try XCTUnwrap(MeshStub.requests.first)
        XCTAssertEqual(claim.body["node"] as? String, "phone-edge")
        XCTAssertEqual(claim.auth, "Bearer s3cret")
    }

    func testProviderFailurePostsFailVerbatim() async {
        MeshStub.script = [
            ("/api/mesh/relay/claim", 200, Self.jobJSON),
            ("/api/mesh/relay/relay_1/fail", 200, "{}"),
            ("/api/mesh/relay/claim", 200, Self.idleJSON),
        ]
        let (_, stats) = await serve(
            worker: 1, client: client(), provider: EchoProvider(thrown: "no model loaded"))

        let fail = MeshStub.requests.first { $0.path.hasSuffix("/fail") }
        XCTAssertEqual(fail?.body["error"] as? String, "no model loaded")
        XCTAssertEqual(stats.jobsServed, 0)
    }

    func testRecursionGuardFailsTheJobByName() async {
        MeshStub.script = [
            ("/api/mesh/relay/claim", 200, Self.jobJSON),
            ("/api/mesh/relay/relay_1/fail", 200, "{}"),
            ("/api/mesh/relay/claim", 200, Self.idleJSON),
        ]
        let refusal = "this device's profile runs elsewhere — serving needs an on-device model or an endpoint"
        _ = await serve(worker: 1, client: client(),
                        makeProvider: { throw MeshServeRefusal(refusal) })

        let fail = MeshStub.requests.first { $0.path.hasSuffix("/fail") }
        XCTAssertEqual(fail?.body["error"] as? String, refusal)
    }

    func testEmptyAnswerFailsByNameInsteadOfDangling() async {
        MeshStub.script = [
            ("/api/mesh/relay/claim", 200, Self.jobJSON),
            ("/api/mesh/relay/relay_1/fail", 200, "{}"),
            ("/api/mesh/relay/claim", 200, Self.idleJSON),
        ]
        _ = await serve(worker: 1, client: client(), provider: EchoProvider(answer: "  "))

        let fail = MeshStub.requests.first { $0.path.hasSuffix("/fail") }
        XCTAssertEqual(fail?.body["error"] as? String, "the provider returned an empty answer")
    }

    func testHubOutageBacksOffExponentially() async {
        // no script at all → every claim fails as network-down
        let (sleeps, _) = await serve(worker: 3, client: client())
        XCTAssertEqual(sleeps, [1.0, 2.0, 4.0])
    }

    func testIdleCadenceIsJitteredAroundThePollInterval() async {
        MeshStub.script = [
            ("/api/mesh/relay/claim", 200, Self.idleJSON),
            ("/api/mesh/relay/claim", 200, Self.idleJSON),
        ]
        let (sleeps, _) = await serve(worker: 2, client: client())
        for s in sleeps {
            XCTAssertGreaterThanOrEqual(s, 3.0 * 0.8)
            XCTAssertLessThanOrEqual(s, 3.0 * 1.2)
        }
        // idle posts nothing — the two claims are the only requests
        XCTAssertEqual(MeshStub.requests.count, 2)
        XCTAssertTrue(MeshStub.requests.allSatisfy { $0.path == "/api/mesh/relay/claim" })
    }

    func testLateCompletionIsLoggedNeverRetried() async {
        MeshStub.script = [
            ("/api/mesh/relay/claim", 200, Self.jobJSON),
            ("/api/mesh/relay/relay_1/complete", 409, #"{"error": "job is not completable"}"#),
            ("/api/mesh/relay/claim", 200, Self.idleJSON),
        ]
        let (_, stats) = await serve(worker: 1, client: client())
        XCTAssertEqual(stats.jobsServed, 0)
        XCTAssertEqual(stats.lastOutcome, "late/unreported relay_1")
        // exactly one completion attempt — a slow worker learns the truth
        let completes = MeshStub.requests.filter { $0.path.hasSuffix("/complete") }
        XCTAssertEqual(completes.count, 1)
    }
}
