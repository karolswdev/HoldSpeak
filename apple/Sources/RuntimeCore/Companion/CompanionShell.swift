import Foundation
import Contracts
import Providers

/// The unified Companion shell at the Runtime-Core layer (HSM-12-03). The "not a dumb
/// terminal" principle, made structural: the shell composes the iPad's **own on-device
/// runtime** and the **server it is pointed at** into one state, so the views can show
/// both at once — the device is enriched by pairing, never reduced to a remote.
///
/// All business logic lives here (the views hold none): probe the desktop, list its
/// meetings, and carry the local runtime summary alongside. An unreachable desktop is a
/// calm `localOnly` mode — the on-device runtime is always present and never blocked.
public struct CompanionShell: Sendable {
    let link: CompanionLink
    let meetings: CompanionMeetings
    /// The iPad's own runtime summary (capabilities + local meetings), supplied by the
    /// app from the on-device stack. A closure so the Core depends on no device API.
    let localProvider: @Sendable () async -> LocalRuntimeSummary

    public init(link: CompanionLink, meetings: CompanionMeetings,
                localProvider: @escaping @Sendable () async -> LocalRuntimeSummary) {
        self.link = link
        self.meetings = meetings
        self.localProvider = localProvider
    }

    /// Load the whole shell state in one pass: the on-device summary (always), plus the
    /// server view when reachable. A reachable handshake whose meetings call then fails
    /// degrades to `localOnly` — honest, never a half-rendered server.
    public func load() async -> CompanionShellState {
        let local = await localProvider()
        let connection = await link.probe()

        var serverMeetings: [MeetingSummary] = []
        var serverReachable = connection.reachable
        if connection.reachable {
            switch await meetings.meetings() {
            case .success(let m): serverMeetings = m
            case .failure: serverReachable = false
            }
        }

        return CompanionShellState(
            connection: connection,
            serverReachable: serverReachable,
            serverMeetings: serverMeetings,
            local: local,
            mode: serverReachable ? .connected : .localOnly
        )
    }

    /// Honest egress for the badge — the shell talks to the paired LAN desktop.
    public var egressLabel: String { link.egressLabel }
}

/// The iPad's on-device runtime as the shell presents it — a first-class peer of the
/// server, not a placeholder. `capabilities` are the always-on local powers (capture,
/// Whisper, local inference); `meetings` are recordings that live on the device.
public struct LocalRuntimeSummary: Sendable, Equatable {
    public var ready: Bool
    public var capabilities: [String]
    public var meetings: [MeetingSummary]

    public init(ready: Bool, capabilities: [String] = [], meetings: [MeetingSummary] = []) {
        self.ready = ready
        self.capabilities = capabilities
        self.meetings = meetings
    }
}

/// Whether the shell is showing both faces or just the device's own.
public enum ShellMode: Sendable, Equatable { case connected, localOnly }

/// One composed snapshot the shell renders: the device's own runtime alongside the
/// server view. `localOnly` means the desktop is unreachable — the on-device runtime
/// still stands, fully.
public struct CompanionShellState: Sendable, Equatable {
    public var connection: DesktopConnection
    public var serverReachable: Bool
    public var serverMeetings: [MeetingSummary]
    public var local: LocalRuntimeSummary
    public var mode: ShellMode

    public init(connection: DesktopConnection, serverReachable: Bool,
                serverMeetings: [MeetingSummary], local: LocalRuntimeSummary, mode: ShellMode) {
        self.connection = connection
        self.serverReachable = serverReachable
        self.serverMeetings = serverMeetings
        self.local = local
        self.mode = mode
    }
}
