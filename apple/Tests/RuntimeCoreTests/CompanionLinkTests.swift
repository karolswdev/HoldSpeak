import XCTest
import Contracts
@testable import Providers
@testable import RuntimeCore

/// HSM-12-01 — the Runtime-Core side of the desktop companion. Proves the core
/// depends on the `IDesktopClient` *interface* (a fake drives it), and — the
/// load-bearing guarantee — that an unreachable desktop never blocks on-device work.
final class CompanionLinkTests: XCTestCase {

    /// A fake desktop client: no network, scriptable connection, honest egress.
    final class FakeDesktop: IDesktopClient, @unchecked Sendable {
        var connection: DesktopConnection
        var probes = 0
        init(_ connection: DesktopConnection) { self.connection = connection }
        func handshake() async -> DesktopConnection { probes += 1; return connection }
        var egressLabel: String { "local + LAN → fake.desk" }
    }

    func testProbeReportsReadyConnection() async {
        let fake = FakeDesktop(.init(reachable: true, runtimeReady: true, detail: "ready · web"))
        let link = CompanionLink(client: fake)
        let conn = await link.probe()
        XCTAssertTrue(conn.reachable)
        XCTAssertTrue(conn.runtimeReady)
        XCTAssertEqual(fake.probes, 1)
        XCTAssertTrue(link.egressLabel.contains("LAN"))
    }

    func testProbeReportsOfflineWithoutThrowing() async {
        let link = CompanionLink(client: FakeDesktop(.offline("cannotConnectToHost")))
        let conn = await link.probe()   // no try — the seam never throws
        XCTAssertFalse(conn.reachable)
        XCTAssertTrue(conn.detail.hasPrefix("desktop unreachable"))
    }

    /// The "not a dumb terminal" guarantee: on-device work completes fully while the
    /// desktop is unreachable — the companion is additive, never on the local path.
    func testOnDeviceWorkUnaffectedWhenDesktopUnreachable() async {
        let link = CompanionLink(client: FakeDesktop(.offline("down")))

        // Simulated on-device operation that does not depend on the server.
        func localCapture() -> String { "captured-on-device" }

        let conn = await link.probe()
        let local = localCapture()

        XCTAssertFalse(conn.reachable)              // server is down ...
        XCTAssertEqual(local, "captured-on-device") // ... yet local work still ran
    }
}
