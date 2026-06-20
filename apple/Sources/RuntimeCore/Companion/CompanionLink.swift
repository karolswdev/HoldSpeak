import Foundation
import Contracts
import Providers

/// HSM-12-01 — the Runtime-Core entry point to the desktop companion (charter
/// Amendment 1.1, Track M). Holds the `IDesktopClient` seam so the Runtime Core
/// depends on the *interface*, never a concrete transport, and gives the host one
/// thin thing to drive for "point this device at the server."
///
/// Deliberately minimal for HSM-12-01 — connect / health / egress only. The verb
/// surfaces (meetings remote control HSM-12-02; the remote-dictation inject HSM-13)
/// hang off this same seam in their stories.
///
/// **Offline-safe by construction:** `probe()` never throws and an unreachable
/// desktop is a returned state, so nothing the device does locally is ever gated on
/// the server being reachable (the "not a dumb terminal" principle, made structural).
public struct CompanionLink: Sendable {
    let client: IDesktopClient

    public init(client: IDesktopClient) {
        self.client = client
    }

    /// Probe the paired desktop. Never throws; returns the connection state to render.
    public func probe() async -> DesktopConnection {
        await client.handshake()
    }

    /// Honest egress descriptor for the badge (the companion talks to a LAN peer).
    public var egressLabel: String { client.egressLabel }
}
