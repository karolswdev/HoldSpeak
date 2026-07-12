import XCTest
import Contracts
@testable import Providers

final class ProjectionClientTests: XCTestCase {
    final class StubProtocol: URLProtocol {
        nonisolated(unsafe) static var status = 200
        nonisolated(unsafe) static var body = Data()
        nonisolated(unsafe) static var lastRequest: URLRequest?
        nonisolated(unsafe) static var lastBody: Data?
        override class func canInit(with request: URLRequest) -> Bool { true }
        override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }
        override func startLoading() {
            Self.lastRequest = request
            if let stream = request.httpBodyStream {
                stream.open()
                var data = Data()
                let buffer = UnsafeMutablePointer<UInt8>.allocate(capacity: 1024)
                defer { buffer.deallocate(); stream.close() }
                while stream.hasBytesAvailable {
                    let count = stream.read(buffer, maxLength: 1024)
                    if count <= 0 { break }
                    data.append(buffer, count: count)
                }
                Self.lastBody = data
            } else {
                Self.lastBody = request.httpBody
            }
            let response = HTTPURLResponse(
                url: request.url!, statusCode: Self.status, httpVersion: nil, headerFields: nil
            )!
            client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
            client?.urlProtocol(self, didLoad: Self.body)
            client?.urlProtocolDidFinishLoading(self)
        }
        override func stopLoading() {}
    }

    private func client() -> HTTPDesktopClient {
        let config = URLSessionConfiguration.ephemeral
        config.protocolClasses = [StubProtocol.self]
        return HTTPDesktopClient(
            config: .init(baseURL: URL(string: "http://desk.local:8000")!, token: "tok"),
            session: URLSession(configuration: config)
        )
    }

    func testProjectionEnvelopeDecodesSharedSemanticsAndPagination() async throws {
        StubProtocol.body = Data(#"""
        {"projections":[{"id":"p1","projection_kind":"attention",
          "subject_ref":"meeting:m1","subject_label":"Daily return",
          "title":"Meeting capture needs recovery","summary":"Open the Meeting.",
          "reason_code":"capture_recoverable","decision_kind":"recovery",
          "attention_state":"needs_attention","actual_destination":"this_machine",
          "authority_basis":"explicit_capture","attempt":null,"outcome":"recoverable",
          "timestamp":"2026-07-11T01:00:00Z","correlation_id":"meeting:m1",
          "source_kind":"meeting","source_id":"m1","source_api":"/api/meetings/m1",
          "detail_url":"/history?meeting=m1","control_mode":"yolo",
          "policy_version":"operation-policy/v2","effect_class":"slack/post_message",
          "severity":"error","dismissed":false}],
         "counts":{"needs_attention":1,"receipts":0},
         "subject_counts":{"meeting:m1":{"needs_attention":1,"receipts":0}},
         "page":{"offset":0,"limit":50,"total":1,"has_more":false}}
        """#.utf8)
        let result = try await client().deskProjections()
        XCTAssertEqual(result.projections.first?.subjectRef, "meeting:m1")
        XCTAssertEqual(result.projections.first?.actualDestination, "this_machine")
        XCTAssertEqual(result.projections.first?.attentionState, "needs_attention")
        XCTAssertEqual(result.projections.first?.controlMode, "yolo")
        XCTAssertEqual(result.projections.first?.policyVersion, "operation-policy/v2")
        XCTAssertEqual(result.projections.first?.effectClass, "slack/post_message")
        XCTAssertEqual(result.page.total, 1)
        XCTAssertEqual(StubProtocol.lastRequest?.value(forHTTPHeaderField: "Authorization"), "Bearer tok")
    }

    func testDismissUsesPresentationRouteWithoutSubjectPayload() async throws {
        StubProtocol.body = Data(#"{"success":true}"#.utf8)
        try await client().updateProjectionPresentation(id: "meeting:m1:recoverable", action: "dismiss")
        XCTAssertEqual(
            StubProtocol.lastRequest?.url?.path,
            "/api/desk/projections/meeting:m1:recoverable/presentation"
        )
        let json = try JSONSerialization.jsonObject(
            with: StubProtocol.lastBody ?? Data()
        ) as? [String: String]
        XCTAssertEqual(json, ["action": "dismiss"])
    }
}
