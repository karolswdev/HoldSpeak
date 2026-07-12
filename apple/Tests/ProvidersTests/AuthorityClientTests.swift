import XCTest
import Contracts
@testable import Providers

final class AuthorityClientTests: XCTestCase {
    final class StubProtocol: URLProtocol {
        nonisolated(unsafe) static var body = Data()
        nonisolated(unsafe) static var lastRequest: URLRequest?

        override class func canInit(with request: URLRequest) -> Bool { true }
        override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }

        override func startLoading() {
            Self.lastRequest = request
            let response = HTTPURLResponse(
                url: request.url!, statusCode: 200, httpVersion: nil, headerFields: nil
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

    func testAuthorityPolicyDecodesTheSharedVersionedPosture() async throws {
        StubProtocol.body = Data(#"""
        {"control_mode":"yolo","control_mode_label":"YOLO",
         "control_mode_description":"Runs eligible configured work without HoldSpeak approval prompts.",
         "policy_version":"operation-policy/v2","source":"config",
         "applies_to":"future_operations_only",
         "precedence":["hard_invariants","control_mode"],
         "hard_invariants":["destination_binding","payload_binding"],
         "supported_families":["external_write"],
         "unsupported_family_behavior":"refused"}
        """#.utf8)

        let policy = try await client().authorityPolicy()
        XCTAssertEqual(policy.controlMode, "yolo")
        XCTAssertEqual(policy.controlModeLabel, "YOLO")
        XCTAssertEqual(policy.policyVersion, "operation-policy/v2")
        XCTAssertEqual(policy.appliesTo, "future_operations_only")
        XCTAssertEqual(policy.unsupportedFamilyBehavior, "refused")
        XCTAssertEqual(StubProtocol.lastRequest?.url?.path, "/api/authority/policy")
        XCTAssertEqual(
            StubProtocol.lastRequest?.value(forHTTPHeaderField: "Authorization"),
            "Bearer tok"
        )
    }
}
