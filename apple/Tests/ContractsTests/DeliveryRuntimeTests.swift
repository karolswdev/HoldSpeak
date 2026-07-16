import XCTest
@testable import Contracts

/// HS-94-09 — the v2 Delivery Runtime contracts against golden fixtures.
///
/// The fixtures under `Fixtures/delivery_*.json` mirror the hub's ACTUAL wire
/// emissions (read_model / collector / node_link / attempts / dossiers), so a
/// field the hub adds, renames or drops fails HERE on the Swift surface. The
/// tolerance fixture pins the additive contract: unknown fields are ignored
/// and unknown enum raw values decode into a case carrying the raw string —
/// never a throw. A hygiene sweep mirrors the hub's §12/§13 rule: no fixture
/// string is ever a filesystem path.
final class DeliveryRuntimeTests: XCTestCase {

    private func fixtureURL(_ name: String) -> URL {
        URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()          // ContractsTests
            .appendingPathComponent("Fixtures")
            .appendingPathComponent(name)
    }

    private func fixtureData(_ name: String) throws -> Data {
        try Data(contentsOf: fixtureURL(name))
    }

    private func decode<T: Decodable>(_ type: T.Type, _ name: String) throws -> T {
        try HoldSpeakContracts.decoder().decode(type, from: fixtureData(name))
    }

    // MARK: - Snapshot (delivery_schema: 1)

    func testSnapshotFixtureDecodes() throws {
        let snap = try decode(DeliverySnapshot.self, "delivery_snapshot.json")
        XCTAssertEqual(snap.deliverySchema, 1)
        XCTAssertTrue(snap.revision.hasPrefix("rev_"))
        XCTAssertTrue(snap.cursor.hasPrefix("cur_"))   // opaque; never parsed
        XCTAssertEqual(snap.generatedAt, "2026-07-15T09:30:00Z")
        XCTAssertEqual(snap.sources.count, 2)

        let live = snap.sources[0]
        XCTAssertEqual(live.sourceId, "src_1b2c3d4e5f607182")
        XCTAssertEqual(live.nodeId, "node_9f8e7d6c5b4a3921")
        XCTAssertEqual(live.label, "holdspeak")
        XCTAssertEqual(live.status, .live)
        XCTAssertEqual(live.worktrees?.count, 2)
        XCTAssertEqual(live.worktrees?[0].worktreeId, "wt_0a1b2c3d4e5f6071")
        XCTAssertEqual(live.worktrees?[0].branch, "main")
        XCTAssertEqual(live.projects?.count, 1)
        XCTAssertNil(live.sessions)
        // Open-dictionary keys keep their WIRE spelling: `.convertFromSnakeCase`
        // rewrites struct property keys, not `[String: JSONValue]` entries.
        XCTAssertEqual(live.capabilities?.schemas?["feed_schema"], .number(1))
        XCTAssertEqual(live.capabilities?.schemas?["events_schema"], .number(2))
        XCTAssertEqual(live.capabilities?.disabled, [])

        let cold = snap.sources[1]
        XCTAssertEqual(cold.status, .unavailable)
        XCTAssertEqual(cold.detail, "not yet collected")
        XCTAssertNil(cold.nodeId)
        XCTAssertNil(cold.capabilities)
        // nil (not []) means never observed — the §13 distinction survives.
        XCTAssertNil(cold.projects)
    }

    // MARK: - Sources view (registry_schema: 1)

    func testSourcesViewFixtureDecodes() throws {
        let view = try decode(DeliverySourcesView.self, "delivery_sources.json")
        XCTAssertEqual(view.registrySchema, 1)
        XCTAssertEqual(view.sources.count, 2)
        let first = view.sources[0]
        XCTAssertEqual(first.fingerprint?.hasPrefix("sha256:"), true)
        XCTAssertEqual(first.status, .live)
        let second = view.sources[1]
        XCTAssertEqual(second.status, .stale)
        XCTAssertEqual(second.detail, "dw timed out")
        XCTAssertEqual(second.worktrees?.count, 1)
    }

    // MARK: - Nodes (nodes_schema: 1)

    func testNodesFixtureDecodes() throws {
        let view = try decode(DeliveryNodesView.self, "delivery_nodes.json")
        XCTAssertEqual(view.nodesSchema, 1)
        XCTAssertEqual(view.nodes.count, 3)

        let live = view.nodes[0]
        XCTAssertEqual(live.name, "intel-43")
        XCTAssertEqual(live.nodeId, "node_9f8e7d6c5b4a3921")
        XCTAssertEqual(live.kind, "node-link")
        XCTAssertEqual(live.status, .live)
        XCTAssertEqual(live.commandsEnabled, true)
        XCTAssertEqual(live.capabilities, ["delivery.source", "coder.steering"])
        XCTAssertEqual(live.cursor, 42)
        XCTAssertEqual(live.clockSkewSeconds, -0.412)

        let stale = view.nodes[1]
        XCTAssertEqual(stale.status, .stale)
        XCTAssertEqual(stale.commandsEnabled, false)
        XCTAssertEqual(stale.compat, "capability_missing")
        XCTAssertNil(stale.clockSkewSeconds)

        // Legacy env-table rows are labeled and honestly unknown.
        let legacy = view.nodes[2]
        XCTAssertEqual(legacy.kind, "legacy-direct")
        XCTAssertEqual(legacy.status, .unknown)
        XCTAssertNil(legacy.nodeId)
        XCTAssertEqual(legacy.compat, "legacy-direct")
    }

    // MARK: - Work attempts (attempts_schema: 1)

    func testAttemptsFixtureDecodes() throws {
        let view = try decode(WorkAttemptsView.self, "delivery_attempts.json")
        XCTAssertEqual(view.attemptsSchema, 1)
        XCTAssertEqual(view.attempts.count, 3)

        let rider = view.attempts[0]
        XCTAssertEqual(rider.attemptId, "att_5f6e7d8c9b0a1122")
        XCTAssertEqual(rider.storyRef.sourceId, "src_1b2c3d4e5f607182")
        XCTAssertEqual(rider.storyRef.project, "holdspeak")
        XCTAssertEqual(rider.storyRef.storyId, "HS-94-09")
        XCTAssertEqual(rider.association?.kind, .riderClaim)
        XCTAssertEqual(rider.association?.claimedBy, "rider:claude")
        XCTAssertEqual(rider.exact, true)
        XCTAssertEqual(rider.state, .working)
        XCTAssertEqual(rider.state?.isTerminal, false)
        XCTAssertEqual(rider.targetId, "%12")
        XCTAssertEqual(rider.history?.count, 4)
        XCTAssertNil(rider.history?[0].from)             // creation event
        XCTAssertEqual(rider.history?[0].to, "starting")
        XCTAssertEqual(rider.history?[0].reason, "created:rider_claim")
        XCTAssertEqual(rider.history?[3].to, "working")

        let heuristic = view.attempts[1]
        XCTAssertEqual(heuristic.association?.kind, .heuristic)
        XCTAssertEqual(heuristic.exact, false)           // never exact
        XCTAssertEqual(heuristic.state, .idle)
        XCTAssertNil(heuristic.association?.claimedAt)

        let tomb = view.attempts[2]
        XCTAssertEqual(tomb.association?.kind, .manual)
        XCTAssertEqual(tomb.state, .abandoned)
        XCTAssertEqual(tomb.state?.isTerminal, true)
        XCTAssertEqual(tomb.endedAt, "2026-07-14T10:00:05Z")
        // Resilience recorded, not erased: unknown → abandoned in history.
        XCTAssertEqual(tomb.history?[1].to, "unknown")
        XCTAssertEqual(tomb.history?[1].reason, "node_offline")
        XCTAssertEqual(tomb.history?[2].reason, "stale_timeout")
    }

    // MARK: - Story dossier (dossier_schema: 1)

    func testStoryDossierFixtureDecodes() throws {
        let dossier = try decode(StoryDossier.self, "delivery_story_dossier.json")
        XCTAssertEqual(dossier.dossierSchema, 1)
        XCTAssertEqual(dossier.bundleId, "bundle-3c4d5e6f708192a3")
        XCTAssertEqual(dossier.bundleChanged, false)
        XCTAssertEqual(dossier.freshness, .live)
        XCTAssertEqual(dossier.storyId, "HS-94-05")
        XCTAssertEqual(dossier.phase, 94)
        XCTAssertEqual(dossier.status, "done")
        XCTAssertNotNil(dossier.sourceRevision?.headSha)
        XCTAssertNotNil(dossier.sourceRevision?.indexTree)
        XCTAssertEqual(dossier.summary?.assets, 2)
        XCTAssertEqual(dossier.summary?.passingCaptures, 1)
        XCTAssertEqual(dossier.summary?.failingCaptures, 1)
        XCTAssertEqual(dossier.members?.count, 5)

        let roles = Set((dossier.members ?? []).compactMap { $0.role })
        XCTAssertTrue(roles.isSuperset(of: ["story_markdown", "evidence_markdown", "phase_status", "asset"]))
        for member in dossier.members ?? [] {
            XCTAssertEqual(member.assetId?.hasPrefix("a-"), true)
            XCTAssertEqual(member.sha256?.hasPrefix("sha256:"), true)
            XCTAssertNotNil(member.mediaType)
            XCTAssertNotNil(member.bytes)
        }

        // Captured runs carry an explicit pass/fail, never inferred client-side.
        XCTAssertEqual(dossier.capturedRuns?.count, 2)
        XCTAssertEqual(dossier.capturedRuns?[0].passed, true)
        XCTAssertEqual(dossier.capturedRuns?[0].exitCode, 0)
        XCTAssertEqual(dossier.capturedRuns?[1].passed, false)
        XCTAssertEqual(dossier.capturedRuns?[1].exitCode, 1)

        // The trace points into members by asset id.
        let memberIds = Set((dossier.members ?? []).compactMap { $0.assetId })
        XCTAssertTrue(memberIds.contains(dossier.trace?.storyAssetId ?? ""))
        XCTAssertTrue(memberIds.contains(dossier.trace?.evidenceAssetId ?? ""))
        XCTAssertTrue(memberIds.contains(dossier.trace?.phaseStatusAssetId ?? ""))
        XCTAssertNil(dossier.trace?.finalSummaryAssetId)

        // Inline docs: sanitized Markdown as text with a typed state.
        XCTAssertEqual(dossier.story?.state, "ready")
        XCTAssertEqual(dossier.story?.assetId, dossier.trace?.storyAssetId)
        XCTAssertTrue(dossier.story?.markdown?.contains("HS-94-05") == true)
        XCTAssertEqual(dossier.evidence?.count, 1)
        XCTAssertEqual(dossier.evidence?[0].state, "ready")
    }

    // MARK: - Phase dossier (phase_dossier_schema: 1)

    func testPhaseDossierFixtureDecodes() throws {
        let phase = try decode(PhaseDossier.self, "delivery_phase_dossier.json")
        XCTAssertEqual(phase.phaseDossierSchema, 1)
        XCTAssertEqual(phase.phase, 94)
        XCTAssertEqual(phase.title, "Delivery Runtime")
        XCTAssertEqual(phase.storiesDone, 8)
        XCTAssertEqual(phase.storiesTotal, 10)
        XCTAssertEqual(phase.stories.count, 2)

        let ready = phase.stories[0]
        XCTAssertEqual(ready.state, "ready")
        XCTAssertEqual(ready.title, "Evidence dossiers and safe assets")
        XCTAssertEqual(ready.freshness, .cached)
        XCTAssertEqual(ready.trace?.finalSummaryAssetId, "a-6f708192a3b4c5d6")
        // Metadata only on this surface: no inline doc bodies load.
        XCTAssertNil(ready.story)
        XCTAssertNil(ready.evidence)

        // A refused row stays a visible stub, never silently dropped.
        let stub = phase.stories[1]
        XCTAssertEqual(stub.storyId, "HS-94-10")
        XCTAssertEqual(stub.state, "not_found")
        XCTAssertNil(stub.bundleId)

        XCTAssertEqual(phase.finalSummary?.assetId, "a-6f708192a3b4c5d6")
        XCTAssertEqual(phase.finalSummary?.bundleId, "bundle-3c4d5e6f708192a3")
    }

    // MARK: - The typed refusal envelope

    func testRefusalFixtureDecodesAndPreservesTheManifest() throws {
        let refusal = try decode(DeliveryRefusal.self, "delivery_refusal.json")
        XCTAssertEqual(refusal.refusal, .bundleChanged)
        XCTAssertTrue(refusal.detail?.contains("re-fetch") == true)
        // §13: bundle_changed preserves the cached manifest metadata.
        XCTAssertEqual(refusal.manifest?.bundleChanged, true)
        XCTAssertEqual(refusal.manifest?.liveBundleId, "bundle-99887766554433aa")
        XCTAssertEqual(refusal.manifest?.members?.count, 1)
        XCTAssertEqual(refusal.manifest?.freshness, .cached)
    }

    // MARK: - Additive tolerance (unknown fields + unknown enum raw values)

    private struct ToleranceFixture: Decodable {
        var snapshot: DeliverySnapshot
        var node: NodePresence
        var attempt: WorkAttempt
        var dossier: StoryDossier
        var refusal: DeliveryRefusal
    }

    func testUnknownFieldsAndEnumValuesNeverThrow() throws {
        let f = try decode(ToleranceFixture.self, "delivery_tolerance.json")

        // Unknown enum raw values decode into the case carrying the raw string.
        XCTAssertEqual(f.snapshot.sources[0].status, .unknown("quarantined"))
        XCTAssertEqual(f.node.status, .unrecognized("hibernating"))
        XCTAssertEqual(f.attempt.association?.kind, .unknown("delegated"))
        XCTAssertEqual(f.attempt.state, .unrecognized("paused"))
        XCTAssertEqual(f.attempt.state?.isTerminal, false)
        XCTAssertEqual(f.dossier.freshness, .unknown("prefetched"))
        XCTAssertEqual(f.refusal.refusal, .unknown("rate_limited"))

        // The known fields still land despite the unknown neighbors
        // (extra top-level, nested, and array-element fields are ignored).
        XCTAssertEqual(f.snapshot.deliverySchema, 1)
        XCTAssertEqual(f.snapshot.sources[0].worktrees?[0].worktreeId, "wt_ffffffffffffffff")
        XCTAssertEqual(f.node.name, "future-node")
        XCTAssertEqual(f.node.cursor, 3)
        XCTAssertEqual(f.attempt.storyRef.storyId, "HS-99-01")
        XCTAssertEqual(f.attempt.history?.count, 1)
        XCTAssertEqual(f.dossier.members?[0].role, "hologram")
        XCTAssertEqual(f.dossier.summary?.assets, 0)
    }

    func testUnknownEnumRoundTripsItsRawValue() throws {
        // What decoded tolerant must re-encode byte-honest, not blank.
        let status = DeliverySourceStatus(rawValue: "quarantined")
        let data = try HoldSpeakContracts.encoder().encode([status])
        XCTAssertEqual(String(decoding: data, as: UTF8.self), #"["quarantined"]"#)
    }

    // MARK: - Fixture hygiene (the §12/§13 mirror)

    /// No wire field ever carries a filesystem path: nothing decodes a string
    /// that is an absolute path, a home-relative path, or a Windows drive
    /// path. Mirrors the hub's rule that paths are server-side only.
    func testNoFixtureFieldIsAFilesystemPath() throws {
        let fixturesDir = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .appendingPathComponent("Fixtures")
        let names = try FileManager.default
            .contentsOfDirectory(atPath: fixturesDir.path)
            .filter { $0.hasPrefix("delivery_") && $0.hasSuffix(".json") }
        XCTAssertEqual(names.count, 8, "expected every delivery fixture to be swept")
        for name in names {
            let doc = try JSONSerialization.jsonObject(with: fixtureData(name))
            assertNoPaths(in: doc, fixture: name)
        }
    }

    private func assertNoPaths(in value: Any, fixture: String) {
        switch value {
        case let text as String:
            XCTAssertFalse(text.hasPrefix("/"),
                           "\(fixture): absolute path on the wire: \(text)")
            XCTAssertFalse(text.hasPrefix("~"),
                           "\(fixture): home path on the wire: \(text)")
            XCTAssertFalse(text.contains("/Users/") || text.contains("/home/"),
                           "\(fixture): user path on the wire: \(text)")
            XCTAssertFalse(text.contains(":\\"),
                           "\(fixture): drive path on the wire: \(text)")
        case let dict as [String: Any]:
            for (key, nested) in dict {
                XCTAssertNotEqual(key, "path",
                                  "\(fixture): a 'path' field crossed the wire")
                assertNoPaths(in: nested, fixture: fixture)
            }
        case let array as [Any]:
            for nested in array { assertNoPaths(in: nested, fixture: fixture) }
        default:
            break
        }
    }
}
