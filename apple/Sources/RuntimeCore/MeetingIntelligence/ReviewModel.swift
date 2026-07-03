import Foundation
import Contracts
import Providers

/// The artifact-review surface at the Runtime-Core layer (HSM-8-04) — the iPad meeting
/// workflow's last beat. A recorded meeting yields Phase-6 artifacts (decisions / action
/// items / risks / requirements / …) as **proposals**; this groups them by type in the
/// active MIR profile's emphasis order, and lets the user **review + approve** on-device.
///
/// Approve flips a draft to `.accepted` and persists it — it **never executes** anything
/// (the charter non-goal: no connector/action runs here; that's a later platform).
public final class ReviewModel: @unchecked Sendable {
    private let lock = NSLock()
    private var _artifacts: [Artifact]
    private let store: IStorage?
    private let now: @Sendable () -> Date

    public init(artifacts: [Artifact], store: IStorage? = nil, now: @escaping @Sendable () -> Date = { Date() }) {
        self._artifacts = artifacts
        self.store = store
        self.now = now
    }

    public var artifacts: [Artifact] { locked { _artifacts } }

    /// Proposals still awaiting a decision (draft / needs-review).
    public var pendingCount: Int { artifacts.filter { $0.status == .draft || $0.status == .needsReview }.count }

    /// Capture + intelligence are on-device; the badge says so (positioning canon — one
    /// badge, no privacy prose).
    public var egressLabel: String { "on device" }

    /// Artifacts grouped by type, ordered by the MIR profile's emphasis first, then any
    /// remaining types. Empty groups are omitted — the review reflects the profile.
    public func grouped(profile: MIRProfile = .balanced) -> [ArtifactGroup] {
        let present = Dictionary(grouping: artifacts, by: { $0.artifactType })
        let emphasis = MIRRouter.baseEmphasis[profile] ?? []
        var orderedTypes = emphasis.filter { present[$0] != nil }
        for t in ArtifactType.allCases where present[t] != nil && !orderedTypes.contains(t) {
            orderedTypes.append(t)
        }
        return orderedTypes.map { ArtifactGroup(type: $0, items: present[$0] ?? []) }
    }

    /// Approve a proposal: `.accepted` + persisted. Review-and-approve only — nothing runs.
    @discardableResult public func approve(_ id: String) throws -> Bool { try setStatus(id, .accepted) }
    /// Reject a proposal: `.rejected` + persisted.
    @discardableResult public func reject(_ id: String) throws -> Bool { try setStatus(id, .rejected) }

    private func setStatus(_ id: String, _ status: ArtifactStatus) throws -> Bool {
        let updated: Artifact? = locked {
            guard let i = _artifacts.firstIndex(where: { $0.id == id }) else { return nil }
            _artifacts[i].status = status
            _artifacts[i].updatedAt = now()
            return _artifacts[i]
        }
        guard let artifact = updated else { return false }
        try store?.saveArtifact(artifact)
        return true
    }

    private func locked<T>(_ body: () -> T) -> T { lock.lock(); defer { lock.unlock() }; return body() }
}

/// A type's artifacts in the review surface (one section).
public struct ArtifactGroup: Sendable, Equatable {
    public var type: ArtifactType
    public var items: [Artifact]
    public init(type: ArtifactType, items: [Artifact]) { self.type = type; self.items = items }
}
