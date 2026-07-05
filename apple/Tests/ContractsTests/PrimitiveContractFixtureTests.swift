import XCTest
@testable import Contracts

/// HS-72-01 — the primitive contract, machine-checked (Phase 72, One Spine).
///
/// Decodes the shared golden fixture — the HUB's canonical wire emissions —
/// through the canonical coder (`HoldSpeakContracts`), so a field the hub adds,
/// renames or drops fails HERE, on the Swift surface, instead of drifting. The
/// same fixture is validated against the JSON Schemas by the hub's pytest
/// (`tests/unit/test_primitive_contract.py`) and `contracts/validate.py`.
///
/// Fixture: `pm/roadmap/holdspeak-mobile/contracts/fixtures/primitives-sample.json`,
/// read via `#filePath` (tests run in-place in the repo; no bundle plumbing).
final class PrimitiveContractFixtureTests: XCTestCase {

    /// The whole golden fixture, decoded in one shot with the canonical decoder.
    private struct Fixture: Codable, Equatable {
        var note: Note
        var kb: KB
        var recipe: Recipe
        var chain: Chain
        var workflow: WorkflowDefinition
        var directory: Directory
        var directoryMembership: Membership
        var profile: RuntimeProfile
        var changeset: ChangeSet
    }

    private func fixtureData() throws -> Data {
        // …/apple/Tests/ContractsTests/PrimitiveContractFixtureTests.swift → repo root
        let root = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()  // ContractsTests
            .deletingLastPathComponent()  // Tests
            .deletingLastPathComponent()  // apple
            .deletingLastPathComponent()  // repo root
        let url = root
            .appendingPathComponent("pm/roadmap/holdspeak-mobile/contracts/fixtures")
            .appendingPathComponent("primitives-sample.json")
        return try Data(contentsOf: url)
    }

    private func decodedFixture() throws -> Fixture {
        try HoldSpeakContracts.decoder().decode(Fixture.self, from: fixtureData())
    }

    // MARK: every hub emission decodes

    func testGoldenFixtureDecodesEveryKind() throws {
        let f = try decodedFixture()
        XCTAssertEqual(f.note.id, "note-golden-1")
        XCTAssertEqual(f.note.tags, ["golden", "contract"])
        XCTAssertEqual(f.kb.memberIds, ["note-golden-1"])
        XCTAssertEqual(f.recipe.kbId, "kb-golden-1")
        XCTAssertNil(f.recipe.profileId)
        // Phase 77: the hub persists + re-emits the pinned context — the wire
        // fields must REACH the properties, not just decode tolerantly (HSM-23-04).
        XCTAssertEqual(f.recipe.manualContext, "Always consider the Q3 launch.")
        XCTAssertTrue(f.recipe.useZoneContext)
        XCTAssertEqual(f.chain.steps, ["agent-golden-1"])
        XCTAssertEqual(f.workflow.prompt, "Draft a stakeholder update")
        XCTAssertEqual(f.directory.parentId, "Atlas")
        XCTAssertEqual(f.directoryMembership.primitiveId, "note-golden-1")
        XCTAssertEqual(f.profile.kind, .openAICompatible)
        // The latent baseURL key bug: wire base_url must reach the property.
        XCTAssertEqual(f.profile.baseURL, "http://192.168.1.43:8080/v1")
    }

    func testHubEmissionsWithoutUpdatedAtDecodeTolerantly() throws {
        // The hub emits NO updated_at for kb/agent/chain/workflow/directory/
        // membership/profile — updatedAt must default (createdAt) instead of
        // failing the whole ChangeSet decode.
        let f = try decodedFixture()
        for (name, created, updated) in [
            ("kb", f.kb.createdAt, f.kb.updatedAt),
            ("recipe", f.recipe.createdAt, f.recipe.updatedAt),
            ("chain", f.chain.createdAt, f.chain.updatedAt),
            ("workflow", f.workflow.createdAt, f.workflow.updatedAt),
            ("directory", f.directory.createdAt, f.directory.updatedAt),
        ] {
            XCTAssertEqual(updated, created, "\(name).updatedAt should default to createdAt")
        }
    }

    // MARK: round-trip stability

    func testEveryKindRoundTripsThroughTheCanonicalCoder() throws {
        let f = try decodedFixture()
        let enc = HoldSpeakContracts.encoder()
        let dec = HoldSpeakContracts.decoder()
        XCTAssertEqual(try dec.decode(Note.self, from: enc.encode(f.note)), f.note)
        XCTAssertEqual(try dec.decode(KB.self, from: enc.encode(f.kb)), f.kb)
        XCTAssertEqual(try dec.decode(Recipe.self, from: enc.encode(f.recipe)), f.recipe)
        XCTAssertEqual(try dec.decode(Chain.self, from: enc.encode(f.chain)), f.chain)
        XCTAssertEqual(try dec.decode(WorkflowDefinition.self, from: enc.encode(f.workflow)), f.workflow)
        XCTAssertEqual(try dec.decode(Directory.self, from: enc.encode(f.directory)), f.directory)
        XCTAssertEqual(try dec.decode(Membership.self, from: enc.encode(f.directoryMembership)), f.directoryMembership)
        XCTAssertEqual(try dec.decode(RuntimeProfile.self, from: enc.encode(f.profile)), f.profile)
        XCTAssertEqual(try dec.decode(ChangeSet.self, from: enc.encode(f.changeset)), f.changeset)
    }

    func testEncodedWireIsSnakeCase() throws {
        let f = try decodedFixture()
        let note = String(data: try HoldSpeakContracts.encoder().encode(f.note), encoding: .utf8)!
        XCTAssertTrue(note.contains("\"body_markdown\""))
        XCTAssertTrue(note.contains("\"created_at\""))
        let profile = String(data: try HoldSpeakContracts.encoder().encode(f.profile), encoding: .utf8)!
        XCTAssertTrue(profile.contains("\"base_url\""))
        XCTAssertFalse(profile.contains("api_key"), "the key NEVER syncs")
    }

    // MARK: the envelope

    func testChangeSetEnvelopeCarriesLiveAndTombstone() throws {
        let f = try decodedFixture()
        XCTAssertEqual(f.changeset.notes.count, 2)
        let live = f.changeset.notes[0]
        XCTAssertFalse(live.meta.deleted)
        XCTAssertEqual(live.value?.id, "note-golden-1")
        let tomb = f.changeset.notes[1]
        XCTAssertTrue(tomb.meta.deleted)
        XCTAssertNil(tomb.value, "a tombstone carries no payload")
        XCTAssertEqual(f.changeset.profiles.count, 1)
        XCTAssertEqual(f.changeset.directoryMemberships.count, 1)
        // Buckets absent from the fixture decode to [] (the tolerant decode).
        XCTAssertTrue(f.changeset.meetings.isEmpty)
    }
}
