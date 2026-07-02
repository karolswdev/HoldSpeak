import Foundation
import Contracts
import Providers

/// The Companion board at the Runtime-Core layer (HSM-13-03): surface the AI PI loop's
/// waiting coder sessions on the iPad and let the user pick *which* one an answer
/// targets, before sending. It depends on the `IDesktopClient` seam, never a transport,
/// and degrades honestly — an unreachable desktop is a `.failure` the view renders, not
/// a throw on the caller path (the same posture as `CompanionMeetings`).
///
/// Target selection is **server-side**: `select` makes a session the desktop's active
/// reply target, so the next answer (HSM-13-01/02 → `/api/dictation/remote`) delivers to
/// it with no silent client default. The board's job is to make that target visible and
/// changeable; the desktop holds the truth.
public struct CompanionBoard: Sendable {
    let client: IDesktopClient

    public init(client: IDesktopClient) {
        self.client = client
    }

    /// Load the current board (`GET /api/coders/status`).
    public func load() async -> Result<CompanionBoardState, Error> {
        await wrap { try await self.client.companionStatus() }
    }

    /// Make `target` the active reply target, then return the refreshed board so the
    /// selection is reflected from the desktop's truth (not assumed client-side).
    public func select(_ target: CompanionTarget) async -> Result<CompanionBoardState, Error> {
        await wrap {
            try await self.client.selectCompanionTarget(agent: target.agent, sessionID: target.sessionID)
            return try await self.client.companionStatus()
        }
    }

    /// Dismiss a waiting session (clears its captured question), then refresh.
    public func dismiss(_ target: CompanionTarget) async -> Result<CompanionBoardState, Error> {
        await wrap {
            try await self.client.dismissCompanionTarget(agent: target.agent, sessionID: target.sessionID)
            return try await self.client.companionStatus()
        }
    }

    /// Pin/unpin a waiting session (sticky target, never auto-expired), then refresh.
    public func pin(_ target: CompanionTarget, pinned: Bool) async -> Result<CompanionBoardState, Error> {
        await wrap {
            try await self.client.pinCompanionTarget(agent: target.agent, sessionID: target.sessionID, pinned: pinned)
            return try await self.client.companionStatus()
        }
    }

    /// Honest egress for the badge — the board talks to the paired LAN desktop.
    public var egressLabel: String { client.egressLabel }

    private func wrap<T>(_ op: () async throws -> T) async -> Result<T, Error> {
        do { return .success(try await op()) }
        catch { return .failure(error) }
    }
}
