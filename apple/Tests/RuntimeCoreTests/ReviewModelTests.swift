import XCTest
import Contracts
@testable import Providers
@testable import RuntimeCore

/// HSM-8-04 — the artifact-review view-model groups a meeting's proposals by type in the
/// active MIR profile's emphasis order, and approves/rejects on-device WITHOUT executing
/// anything (the charter non-goal: review + approve only).
final class ReviewModelTests: XCTestCase {

    final class FakeStore: IStorage, @unchecked Sendable {
        var savedArtifacts: [Artifact] = []
        var failSave = false
        func saveMeeting(_ m: Meeting) throws {}
        func loadMeeting(id: String) throws -> Meeting? { nil }
        func saveArtifact(_ a: Artifact) throws {
            if failSave { throw NSError(domain: "db", code: 1) }
            savedArtifacts.append(a)
        }
        func loadArtifacts(meetingId: String) throws -> [Artifact] { savedArtifacts.filter { $0.meetingId == meetingId } }
    }

    private func art(_ id: String, _ type: ArtifactType, status: ArtifactStatus = .draft) -> Artifact {
        Artifact(id: id, meetingId: "m1", artifactType: type, title: id, bodyMarkdown: "b",
                 structuredJson: .null, confidence: 0.7, status: status, pluginId: "p", pluginVersion: "v")
    }

    func testGroupsByType() {
        let m = ReviewModel(artifacts: [art("a1", .decisions), art("a2", .actionItems), art("a3", .decisions)])
        let groups = m.grouped(profile: .balanced)
        let decisions = groups.first { $0.type == .decisions }
        XCTAssertEqual(decisions?.items.map(\.id), ["a1", "a3"])
        XCTAssertEqual(groups.first { $0.type == .actionItems }?.items.count, 1)
    }

    func testProfileEmphasisOrdersTheGroups() {
        let m = ReviewModel(artifacts: [art("a1", .requirements), art("a2", .adr), art("a3", .actionItems)])
        // .architect emphasis is [adr, decisions, dependencyMap, requirements] — adr leads,
        // then requirements; actionItems (off-profile) sorts after the emphasis types.
        XCTAssertEqual(m.grouped(profile: .architect).map(\.type), [.adr, .requirements, .actionItems])
    }

    func testApproveFlipsToAcceptedPersistsAndNeverExecutes() throws {
        let store = FakeStore()
        let m = ReviewModel(artifacts: [art("a1", .decisions)], store: store)
        XCTAssertTrue(try m.approve("a1"))
        XCTAssertEqual(m.artifacts.first?.status, .accepted)
        XCTAssertEqual(store.savedArtifacts.map { $0.status }, [.accepted], "the approval persisted")
        // The only side effect is a persist — no execution path exists or was taken.
        XCTAssertEqual(store.savedArtifacts.count, 1)
    }

    func testRejectFlipsToRejected() throws {
        let store = FakeStore()
        let m = ReviewModel(artifacts: [art("a1", .actionItems)], store: store)
        XCTAssertTrue(try m.reject("a1"))
        XCTAssertEqual(m.artifacts.first?.status, .rejected)
        XCTAssertEqual(store.savedArtifacts.first?.status, .rejected)
    }

    func testApproveUnknownReturnsFalse() throws {
        let m = ReviewModel(artifacts: [art("a1", .decisions)])
        XCTAssertFalse(try m.approve("nope"))
    }

    func testPendingCountIgnoresDecided() {
        let m = ReviewModel(artifacts: [
            art("a1", .decisions, status: .draft),
            art("a2", .actionItems, status: .needsReview),
            art("a3", .requirements, status: .accepted),
        ])
        XCTAssertEqual(m.pendingCount, 2)
    }

    func testSaveFailurePropagates() {
        let store = FakeStore(); store.failSave = true
        let m = ReviewModel(artifacts: [art("a1", .decisions)], store: store)
        XCTAssertThrowsError(try m.approve("a1"))
    }

    func testEgressIsOnDevice() {
        XCTAssertEqual(ReviewModel(artifacts: []).egressLabel, "on-device · nothing leaves")
    }
}
