import XCTest
import Contracts
@testable import Providers

/// HSM-10-02 — the HTTP sync transport + offline queue. Network stubbed via
/// `URLProtocol`; the queue uses temp dirs. All offline + deterministic.
final class SyncTransportTests: XCTestCase {

    // MARK: stubs

    final class SyncStubProtocol: URLProtocol {
        nonisolated(unsafe) static var handler: ((URLRequest) -> (Int, Data))?
        nonisolated(unsafe) static var lastMethod: String?
        nonisolated(unsafe) static var lastURL: URL?
        nonisolated(unsafe) static var lastBody: Data?
        override class func canInit(with request: URLRequest) -> Bool { true }
        override class func canonicalRequest(for r: URLRequest) -> URLRequest { r }
        override func startLoading() {
            SyncStubProtocol.lastMethod = request.httpMethod
            SyncStubProtocol.lastURL = request.url
            SyncStubProtocol.lastBody = request.httpBody ?? request.httpBodyStream.map { s in
                s.open(); defer { s.close() }
                var d = Data(); var buf = [UInt8](repeating: 0, count: 4096)
                while s.hasBytesAvailable { let n = s.read(&buf, maxLength: 4096); if n <= 0 { break }; d.append(buf, count: n) }
                return d
            }
            let (status, body) = SyncStubProtocol.handler?(request) ?? (500, Data())
            let resp = HTTPURLResponse(url: request.url!, statusCode: status, httpVersion: nil, headerFields: nil)!
            client?.urlProtocol(self, didReceive: resp, cacheStoragePolicy: .notAllowed)
            client?.urlProtocol(self, didLoad: body)
            client?.urlProtocolDidFinishLoading(self)
        }
        override func stopLoading() {}
    }

    private func stubbedSession() -> URLSession {
        let cfg = URLSessionConfiguration.ephemeral
        cfg.protocolClasses = [SyncStubProtocol.self]
        return URLSession(configuration: cfg)
    }

    private func provider(_ session: URLSession) -> HTTPSyncProvider {
        HTTPSyncProvider(config: .init(baseURL: URL(string: "http://desk.tailnet:8000")!), session: session)
    }

    private func sampleChangeSet() -> ChangeSet {
        ChangeSet(meetings: [.tombstone(id: "m1", kind: .meeting, at: Date(timeIntervalSince1970: 1))])
    }

    // Fake providers for queue tests.
    final class OKProvider: ISyncProvider, @unchecked Sendable {
        var pushed = 0
        func push(_ changeSet: ChangeSet) async throws { pushed += 1 }
        func pull() async throws -> ChangeSet { ChangeSet() }
    }
    final class UnreachableProvider: ISyncProvider, @unchecked Sendable {
        struct Down: Error {}
        func push(_ changeSet: ChangeSet) async throws { throw Down() }
        func pull() async throws -> ChangeSet { throw Down() }
    }
    final class FailAfterProvider: ISyncProvider, @unchecked Sendable {
        struct Down: Error {}
        let limit: Int; var pushed = 0
        init(limit: Int) { self.limit = limit }
        func push(_ changeSet: ChangeSet) async throws {
            if pushed >= limit { throw Down() }; pushed += 1
        }
        func pull() async throws -> ChangeSet { ChangeSet() }
    }

    // MARK: HTTPSyncProvider

    func testPushPostsChangeSetToSyncEndpoint() async throws {
        SyncStubProtocol.handler = { _ in (200, Data()) }
        try await provider(stubbedSession()).push(sampleChangeSet())
        XCTAssertEqual(SyncStubProtocol.lastMethod, "POST")
        XCTAssertEqual(SyncStubProtocol.lastURL?.absoluteString, "http://desk.tailnet:8000/api/sync/push")
        let body = try XCTUnwrap(SyncStubProtocol.lastBody)
        let decoded = try HoldSpeakContracts.decoder().decode(ChangeSet.self, from: body)
        XCTAssertEqual(decoded.meetings.first?.meta.id, "m1")
        XCTAssertTrue(decoded.meetings.first?.meta.deleted == true)
    }

    func testPullDecodesChangeSet() async throws {
        SyncStubProtocol.handler = { _ in
            (200, try! HoldSpeakContracts.encoder().encode(
                ChangeSet(artifacts: [.tombstone(id: "a1", kind: .artifact, at: Date(timeIntervalSince1970: 2))])))
        }
        let cs = try await provider(stubbedSession()).pull()
        XCTAssertEqual(SyncStubProtocol.lastURL?.absoluteString, "http://desk.tailnet:8000/api/sync/pull")
        XCTAssertEqual(cs.artifacts.first?.meta.id, "a1")
    }

    func testPushNon2xxThrows() async {
        SyncStubProtocol.handler = { _ in (503, Data()) }
        do { try await provider(stubbedSession()).push(sampleChangeSet()); XCTFail("expected error") }
        catch HTTPSyncProvider.SyncTransportError.http(let s) { XCTAssertEqual(s, 503) }
        catch { XCTFail("wrong error: \(error)") }
    }

    func testEgressLabelIsHonest() {
        XCTAssertTrue(provider(stubbedSession()).egressLabel.contains("LAN"))
        XCTAssertTrue(provider(stubbedSession()).egressLabel.contains("desk.tailnet"))
    }

    // MARK: SyncQueue offline tolerance

    private func tempQueue() -> SyncQueue {
        SyncQueue(directory: URL(fileURLWithPath: NSTemporaryDirectory())
            .appendingPathComponent("hsm-q-\(UUID().uuidString)", isDirectory: true))
    }

    func testEnqueuePreservesFIFOOrder() throws {
        let q = tempQueue()
        try q.enqueue(sampleChangeSet(), seq: 0)
        try q.enqueue(sampleChangeSet(), seq: 1)
        try q.enqueue(sampleChangeSet(), seq: 2)
        XCTAssertEqual(try q.pending().map(\.lastPathComponent),
                       ["000000000000.json", "000000000001.json", "000000000002.json"])
    }

    func testFlushDrainsWhenPeerReachable() async throws {
        let q = tempQueue()
        for i in 0..<3 { try q.enqueue(sampleChangeSet(), seq: i) }
        let ok = OKProvider()
        let n = await q.flush(through: ok)
        XCTAssertEqual(n, 3)
        XCTAssertEqual(ok.pushed, 3)
        XCTAssertEqual(try q.count(), 0)
    }

    func testFlushKeepsQueueWhenPeerUnreachable() async throws {
        let q = tempQueue()
        for i in 0..<3 { try q.enqueue(sampleChangeSet(), seq: i) }
        let n = await q.flush(through: UnreachableProvider())   // must not throw
        XCTAssertEqual(n, 0)
        XCTAssertEqual(try q.count(), 3)   // intact → resume later
    }

    func testFlushIsPartialAndResumable() async throws {
        let q = tempQueue()
        for i in 0..<3 { try q.enqueue(sampleChangeSet(), seq: i) }
        let n = await q.flush(through: FailAfterProvider(limit: 2))
        XCTAssertEqual(n, 2)
        XCTAssertEqual(try q.count(), 1)   // the rest stays queued
    }
}
