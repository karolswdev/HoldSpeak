import XCTest
@testable import Contracts

/// HSM-24-01 — the `RuntimeProfile` contract, its sync envelope, the never-sync-the-key invariant,
/// and the legacy → profiles migration.
final class RuntimeProfileTests: XCTestCase {
    private let t = Date(timeIntervalSince1970: 1_700_000_000)

    private func sampleEndpoint() -> RuntimeProfile {
        RuntimeProfile(id: "p1", name: "OpenRouter", kind: .openAICompatible,
                       baseURL: "https://openrouter.ai/api/v1", model: "anthropic/claude-3.5",
                       contextLimit: 200_000, requiresKey: true, createdAt: t, updatedAt: t)
    }

    func testRoundTrip() throws {
        let p = sampleEndpoint()
        let data = try JSONEncoder().encode(p)
        let back = try JSONDecoder().decode(RuntimeProfile.self, from: data)
        XCTAssertEqual(p, back)
        XCTAssertEqual(back.egressHost, "openrouter.ai")
        XCTAssertFalse(back.isLocal)
    }

    func testOnDeviceEgressIsLocal() {
        let p = RuntimeProfile(id: "l", name: "This device", kind: .onDevice,
                               modelFile: "Qwen3-4B-Instruct-2507-Q4_K_M.gguf", createdAt: t, updatedAt: t)
        XCTAssertTrue(p.isLocal)
        XCTAssertNil(p.egressHost)   // on-device → no egress host → the badge stays "local"
    }

    func testChangeSetCarriesProfilesAndRoundTrips() throws {
        let cs = ChangeSet(profiles: [.live(sampleEndpoint(), id: "p1", kind: .profile, modifiedAt: t)])
        XCTAssertEqual(cs.count, 1)
        XCTAssertFalse(cs.isEmpty)
        let back = try JSONDecoder().decode(ChangeSet.self, from: try JSONEncoder().encode(cs))
        XCTAssertEqual(back.profiles.first?.value, sampleEndpoint())
    }

    /// A payload from a surface that doesn't know `profiles` yet (the hub pre-24-04) must still decode.
    func testChangeSetDecodesWhenProfilesAbsent() throws {
        let legacy = #"{"recipes":[],"meetings":[]}"#.data(using: .utf8)!
        let cs = try JSONDecoder().decode(ChangeSet.self, from: legacy)
        XCTAssertTrue(cs.profiles.isEmpty)
        XCTAssertTrue(cs.isEmpty)
    }

    /// THE security invariant: the profile shape can carry no key. There is no `apiKey` field, and a
    /// secret handed to the Keychain never appears in the synced bytes (proven by construction here).
    func testKeyNeverInThePayload() throws {
        let p = sampleEndpoint()   // requiresKey == true, but no key value lives on the shape
        let json = String(data: try JSONEncoder().encode(p), encoding: .utf8)!
        XCTAssertTrue(json.contains("requiresKey"))
        XCTAssertFalse(json.contains("apiKey"))
        XCTAssertFalse(json.lowercased().contains("sk-"))   // no API-key-shaped material can be present
        // And in a ChangeSet:
        let cs = ChangeSet(profiles: [.live(p, id: "p1", kind: .profile, modifiedAt: t)])
        let csJSON = String(data: try JSONEncoder().encode(cs), encoding: .utf8)!
        XCTAssertFalse(csJSON.contains("apiKey"))
    }

    func testMigrateLocalOnly() {
        let (profiles, active) = RuntimeProfileMigration.migrate(
            legacyModeIsLocal: true, endpointURL: "", endpointModel: "",
            localModelFile: "model.gguf", endpointHasKey: false, now: t)
        XCTAssertEqual(profiles.count, 1)
        XCTAssertEqual(active, RuntimeProfileMigration.localId)
        XCTAssertEqual(profiles.first?.kind, .onDevice)
        XCTAssertEqual(profiles.first?.modelFile, "model.gguf")
    }

    func testMigrateEndpointActive() {
        let (profiles, active) = RuntimeProfileMigration.migrate(
            legacyModeIsLocal: false, endpointURL: "https://api.openrouter.ai/v1",
            endpointModel: "gpt", localModelFile: "", endpointHasKey: true, now: t)
        XCTAssertEqual(profiles.count, 2)   // local is always seeded; endpoint added + active
        XCTAssertEqual(active, RuntimeProfileMigration.endpointId)
        let ep = profiles.first { $0.id == RuntimeProfileMigration.endpointId }
        XCTAssertEqual(ep?.kind, .openAICompatible)
        XCTAssertEqual(ep?.name, "api.openrouter.ai")
        XCTAssertTrue(ep?.requiresKey ?? false)
    }

    /// A configured endpoint is preserved as a profile even if the user was on local (active = local).
    func testMigrateLocalActiveButEndpointPreserved() {
        let (profiles, active) = RuntimeProfileMigration.migrate(
            legacyModeIsLocal: true, endpointURL: "https://x.test/v1", endpointModel: "m",
            localModelFile: "", endpointHasKey: false, now: t)
        XCTAssertEqual(profiles.count, 2)
        XCTAssertEqual(active, RuntimeProfileMigration.localId)
    }
}
