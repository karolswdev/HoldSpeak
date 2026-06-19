import XCTest
import Contracts
import Providers
@testable import RuntimeCore

/// HSM-10 — the one-call sync orchestration. Host-tested against a toggleable fake
/// peer + a real SQLite store + a temp queue. Deterministic, offline-safe.
final class SyncCoordinatorTests: XCTestCase {

    struct Sample: Codable { let meeting: Meeting; let artifact: Artifact }
    private func fixture() throws -> Sample {
        var url = URL(fileURLWithPath: #filePath)
        for _ in 0..<4 { url.deleteLastPathComponent() }
        url.appendPathComponent("pm/roadmap/holdspeak-mobile/contracts/fixtures/meeting-sample.json")
        return try HoldSpeakContracts.decoder().decode(Sample.self, from: Data(contentsOf: url))
    }
    private func tempStore() throws -> SQLiteStorage {
        try SQLiteStorage(path: NSTemporaryDirectory() + "hsm-co-\(UUID().uuidString).sqlite")
    }
    private func tempQueue() -> SyncQueue {
        SyncQueue(directory: URL(fileURLWithPath: NSTemporaryDirectory())
            .appendingPathComponent("hsm-coq-\(UUID().uuidString)", isDirectory: true))
    }
    private let t0 = Date(timeIntervalSince1970: 1_700_000_000)

    /// A peer that can be toggled down, records pushes, and serves a configured pull.
    final class FakePeer: ISyncProvider, @unchecked Sendable {
        struct Down: Error {}
        var up: Bool = true
        var received: [ChangeSet] = []
        var pullResult = ChangeSet()
        func push(_ changeSet: ChangeSet) async throws {
            if !up { throw Down() }
            received.append(changeSet)
        }
        func pull() async throws -> ChangeSet {
            if !up { throw Down() }
            return pullResult
        }
    }

    func testSyncNowPushesAndAppliesWhenReachable() async throws {
        let s = try fixture()
        let store = try tempStore(); defer { store.close() }
        try store.saveMeeting(s.meeting, modifiedAt: t0)

        let peer = FakePeer()
        // The peer offers a fresh artifact to pull back.
        peer.pullResult = ChangeSet(artifacts: [.live(s.artifact, id: s.artifact.id, kind: .artifact, modifiedAt: t0)])

        let coord = SyncCoordinator(store: store, provider: peer, queue: tempQueue())
        let outcome = try await coord.syncNow()

        XCTAssertTrue(outcome.reachedPeer)
        XCTAssertEqual(outcome.pushed, 1)               // the local snapshot flushed
        XCTAssertEqual(outcome.pendingAfter, 0)         // queue drained
        XCTAssertEqual(outcome.applied, 1)              // pulled artifact applied
        XCTAssertFalse(peer.received.isEmpty)           // peer got our snapshot
        XCTAssertEqual(try store.loadArtifacts(meetingId: s.artifact.meetingId), [s.artifact])
    }

    func testSyncNowIsOfflineSafe() async throws {
        let s = try fixture()
        let store = try tempStore(); defer { store.close() }
        try store.saveMeeting(s.meeting, modifiedAt: t0)

        let peer = FakePeer(); peer.up = false
        let coord = SyncCoordinator(store: store, provider: peer, queue: tempQueue())

        let outcome = try await coord.syncNow()         // must not throw
        XCTAssertFalse(outcome.reachedPeer)
        XCTAssertEqual(outcome.pushed, 0)
        XCTAssertEqual(outcome.pendingAfter, 1)         // snapshot safely queued
        XCTAssertEqual(outcome.applied, 0)
    }

    func testQueuedSnapshotsResumeWhenPeerReturns() async throws {
        let s = try fixture()
        let store = try tempStore(); defer { store.close() }
        try store.saveMeeting(s.meeting, modifiedAt: t0)

        let peer = FakePeer(); peer.up = false
        let queue = tempQueue()
        let coord = SyncCoordinator(store: store, provider: peer, queue: queue)

        _ = try await coord.syncNow()                   // offline → queued
        _ = try await coord.syncNow()                   // offline again → 2 queued
        XCTAssertEqual(try queue.count(), 2)

        peer.up = true
        let outcome = try await coord.syncNow()         // back online → flush all (incl. this pass's)
        XCTAssertTrue(outcome.reachedPeer)
        XCTAssertEqual(outcome.pendingAfter, 0)
        XCTAssertEqual(peer.received.count, 3)          // all three snapshots delivered
    }
}
