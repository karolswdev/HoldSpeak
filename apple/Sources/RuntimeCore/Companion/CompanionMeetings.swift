import Foundation
import Contracts
import Providers

/// HSM-12-02 — the Runtime-Core view-model for meetings remote control: from the
/// phone/iPad, list the server's meetings and start/stop one, reflecting the live
/// runtime state. It drives the `IDesktopClient` seam, so the core depends on the
/// interface, not a transport, and stays UI-free (the SwiftUI screens in HSM-12-03
/// render these results).
///
/// Every call returns a `Result` rather than throwing, so an unreachable/erroring
/// desktop is a rendered outcome — the companion degrades gracefully and the
/// on-device runtime is never gated on the server (the "not a dumb terminal"
/// principle).
public struct CompanionMeetings: Sendable {
    let client: IDesktopClient

    public init(client: IDesktopClient) {
        self.client = client
    }

    /// List the server's meetings (newest-first as the server returns them).
    public func meetings() async -> Result<[MeetingSummary], Error> {
        await wrap { try await client.listMeetings() }
    }

    /// The live runtime state (is a meeting active, which one, runtime up).
    public func liveState() async -> Result<RuntimeState, Error> {
        await wrap { try await client.runtimeState() }
    }

    /// Start a meeting on the desktop, returning the resulting live state.
    public func start(title: String? = nil) async -> Result<RuntimeState, Error> {
        await wrap { try await client.startMeeting(title: title) }
    }

    /// Stop the active meeting on the desktop, returning the resulting live state.
    public func stop() async -> Result<RuntimeState, Error> {
        await wrap { try await client.stopMeeting() }
    }

    public var egressLabel: String { client.egressLabel }

    private func wrap<T>(_ op: () async throws -> T) async -> Result<T, Error> {
        do { return .success(try await op()) }
        catch { return .failure(error) }
    }
}
