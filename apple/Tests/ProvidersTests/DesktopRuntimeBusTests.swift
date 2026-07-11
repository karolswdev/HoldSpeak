import XCTest
@testable import Providers

final class DesktopRuntimeBusTests: XCTestCase {
    func testNativeWebSocketUsesBearerHeaderAndCleanURL() throws {
        let secret = "token with / characters"
        let client = HTTPDesktopClient(config: .init(
            baseURL: URL(string: "https://hub.example.test:8443")!, token: secret
        ))
        let request = client.runtimeWebSocketRequest()
        XCTAssertEqual(request.url?.absoluteString, "wss://hub.example.test:8443/ws")
        XCTAssertFalse(request.url?.absoluteString.contains(secret) ?? true)
        XCTAssertEqual(request.value(forHTTPHeaderField: "Authorization"), "Bearer \(secret)")
        XCTAssertEqual(request.value(forHTTPHeaderField: "Sec-WebSocket-Protocol"), "holdspeak.v1")
    }

    func testReconnectBackoffIsBounded() {
        XCTAssertEqual(DesktopRuntimeBus.reconnectDelay(attempt: 0), .milliseconds(500))
        XCTAssertEqual(DesktopRuntimeBus.reconnectDelay(attempt: 3), .seconds(4))
        XCTAssertEqual(DesktopRuntimeBus.reconnectDelay(attempt: 99), .seconds(12))
    }
}
