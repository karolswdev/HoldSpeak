import XCTest
import Contracts
@testable import RuntimeCore

/// HS-72-09 — the desk records embed the canonical contracts.
///
/// Four proofs:
///  1. Round-trip — each record encodes → decodes to an equal value (the new nested shape).
///  2. Legacy migration — the OLD flat `@AppStorage` JSON shapes (hand-written fixtures,
///     matching the deleted structs' Codable shapes exactly) still decode; contract
///     timestamps get populated at decode time.
///  3. Fidelity — `synced(at:)` PRESERVES the embedded contract (tags, createdAt,
///     memberIds, tools, graphJson, a meeting-born artifact's identity…) and bumps ONLY
///     updatedAt — the loss class the old `toContract(now:)` bridges had.
///  4. Golden fixture — the hub's canonical wire values wrap into records and round-trip.
final class DeskRecordsTests: XCTestCase {

    private let t0 = Date(timeIntervalSince1970: 1_700_000_000)   // a stable past instant
    private let t1 = Date(timeIntervalSince1970: 1_700_000_600)

    private func roundTrip<T: Codable & Equatable>(_ value: T, _ label: String) throws -> T {
        let data = try JSONEncoder().encode(value)
        let back = try JSONDecoder().decode(T.self, from: data)
        XCTAssertEqual(back, value, "\(label) must round-trip the new nested shape")
        return back
    }

    // MARK: - 1. round-trip (the new nested shape)

    func testNoteRecordRoundTrip() throws {
        var rec = NoteRecord(contract: Note(id: "n1", title: "Ship it", bodyMarkdown: "the desk syncs",
                                            tags: ["golden"], createdAt: t0, updatedAt: t1), path: "Atlas")
        rec.title = "Ship it now"   // compatibility setter writes into the contract
        let back = try roundTrip(rec, "NoteRecord")
        XCTAssertEqual(back.contract.title, "Ship it now")
        XCTAssertEqual(back.contract.tags, ["golden"])
        XCTAssertEqual(back.contract.createdAt, t0)
        XCTAssertEqual(back.path, "Atlas")
    }

    func testKBRecordRoundTrip() throws {
        let rec = KBRecord(contract: KB(id: "k1", name: "Architecture", memberIds: ["note:n1"],
                                        createdAt: t0, updatedAt: t1), path: "Atlas")
        let back = try roundTrip(rec, "KBRecord")
        XCTAssertEqual(back.contract.memberIds, ["note:n1"])
        XCTAssertEqual(back.items, 1)
    }

    func testOutputRecordRoundTrip() throws {
        let prov = RunProvenance(sourceCardId: "m1", sourceCardTitle: "Q3 kickoff",
                                 viaId: "a1", viaName: "Scout", viaKind: "agent")
        let rec = OutputRecord(id: "o1", title: "Summary", body: "ship it", source: "Q3 kickoff",
                               lens: "Summary", path: "Atlas", provenance: prov)
        let back = try roundTrip(rec, "OutputRecord")
        XCTAssertEqual(back.lens, "Summary")
        XCTAssertEqual(back.source, "Q3 kickoff")
        XCTAssertEqual(back.provenance, prov)
        XCTAssertEqual(back.lineageLine, "from Q3 kickoff · via Scout")
        XCTAssertEqual(back.path, "Atlas")
    }

    func testWorkflowRecordRoundTrip() throws {
        let rec = WorkflowRecord(contract: WorkflowDefinition(id: "w1", name: "Risks",
                                                              prompt: "List the risks",
                                                              graphJson: .object(["v": .string("1")]),
                                                              createdAt: t0, updatedAt: t1))
        let back = try roundTrip(rec, "WorkflowRecord")
        XCTAssertEqual(back.prompt, "List the risks")
        XCTAssertEqual(back.contract.graphJson, .object(["v": .string("1")]))
    }

    func testAgentRecordRoundTrip() throws {
        let rec = AgentRecord(contract: Agent(id: "a1", name: "Scout", avatar: "p1", role: "digs",
                                              systemPrompt: "research", userTemplate: "{input}",
                                              tools: ["wf1"], kbId: "kb1", manualContext: "pinned",
                                              useZoneContext: true, profileId: "profile.local",
                                              createdAt: t0, updatedAt: t1))
        let back = try roundTrip(rec, "AgentRecord")
        XCTAssertEqual(back.kb, "kb1")
        XCTAssertEqual(back.profileId, "profile.local")
        XCTAssertEqual(back.contract.tools, ["wf1"])
    }

    func testChainRecordRoundTrip() throws {
        let rec = ChainRecord(contract: Chain(id: "c1", name: "Refine", steps: ["a1", "a2"],
                                              createdAt: t0, updatedAt: t1))
        let back = try roundTrip(rec, "ChainRecord")
        XCTAssertEqual(back.steps, ["a1", "a2"])
    }

    func testZoneRecRoundTrip() throws {
        let rec = ZoneRec(path: "Atlas/Q3", color: 5, cx: 0.7, cy: 0.6, w: 180, h: 120,
                          borderW: 2, borderStyle: 1, fillStyle: 3, fillOpacity: 0.2, glow: true, hex: 0xFF00FF)
        let back = try roundTrip(rec, "ZoneRec")
        XCTAssertEqual(back.path, "Atlas/Q3")
        XCTAssertEqual(back.contract.name, "Q3")
        XCTAssertEqual(back.contract.parentId, "Atlas")
        XCTAssertEqual(back.glow, true)
        XCTAssertEqual(back.hex, 0xFF00FF)
    }

    // MARK: - 2. legacy migration (the OLD flat @AppStorage shapes keep decoding)

    private func decodeLegacy<T: Decodable>(_ json: String, as type: T.Type) throws -> T {
        try JSONDecoder().decode(T.self, from: Data(json.utf8))
    }

    func testLegacyNoteDecodes() throws {
        // OLD shape: struct NoteRecord { var id, title, body, path: String } (synthesized Codable)
        let rec = try decodeLegacy(
            #"{"id":"n1","title":"Ship it","body":"the desk syncs","path":"Atlas"}"#,
            as: NoteRecord.self)
        XCTAssertEqual(rec.id, "n1")
        XCTAssertEqual(rec.title, "Ship it")
        XCTAssertEqual(rec.body, "the desk syncs")
        XCTAssertEqual(rec.path, "Atlas")
        XCTAssertEqual(rec.contract.createdAt, rec.contract.updatedAt)   // populated at decode time
        XCTAssertGreaterThan(rec.contract.createdAt, .distantPast)
    }

    func testLegacyKBDecodes() throws {
        // OLD shape: struct KBRecord { var id, name, path: String; var items: Int }
        let rec = try decodeLegacy(
            #"{"id":"k1","name":"Architecture","path":"","items":7}"#,
            as: KBRecord.self)
        XCTAssertEqual(rec.name, "Architecture")
        XCTAssertEqual(rec.items, 7)
        XCTAssertEqual(rec.contract.memberIds, [])
        XCTAssertEqual(rec.contract.createdAt, rec.contract.updatedAt)
    }

    func testLegacyOutputDecodes() throws {
        // OLD shape: struct OutputRecord { var id, title, body, source, lens, path: String;
        //                                  var provenance: RunProvenance? }
        let rec = try decodeLegacy(#"""
            {"id":"o1","title":"Scout · reply","body":"three facts","source":"Scout","lens":"Agent",
             "path":"Atlas","provenance":{"sourceCardId":"m1","sourceCardTitle":"Q3 kickoff",
             "viaId":"a1","viaName":"Scout","viaKind":"agent"}}
            """#, as: OutputRecord.self)
        XCTAssertEqual(rec.title, "Scout · reply")
        XCTAssertEqual(rec.source, "Scout")
        XCTAssertEqual(rec.lens, "Agent")
        XCTAssertEqual(rec.provenance?.viaName, "Scout")
        XCTAssertEqual(rec.contract.meetingId, "")
        XCTAssertEqual(rec.contract.artifactType, .pluginOutput)
        XCTAssertEqual(rec.contract.pluginId, "ipad.desk")
        XCTAssertNotNil(rec.contract.createdAt)

        // and one without provenance (nil is how the old rows mostly look)
        let plain = try decodeLegacy(
            #"{"id":"o2","title":"Standup notes","body":"review the dock","source":"Standup","lens":"Note","path":""}"#,
            as: OutputRecord.self)
        XCTAssertNil(plain.provenance)
        XCTAssertEqual(plain.lineageLine, "from Standup")
    }

    func testLegacyWorkflowDecodes() throws {
        // OLD shape: struct WorkflowRecord { var id, name, prompt: String }
        let rec = try decodeLegacy(
            #"{"id":"w1","name":"Risks","prompt":"List the risks"}"#,
            as: WorkflowRecord.self)
        XCTAssertEqual(rec.name, "Risks")
        XCTAssertEqual(rec.prompt, "List the risks")
        XCTAssertEqual(rec.contract.createdAt, rec.contract.updatedAt)
    }

    func testLegacyAgentDecodes() throws {
        // OLD shape (tolerant decode): {id,name,avatar,role,systemPrompt,userTemplate,
        //  manualContext?,useZoneContext?,kb?,profileId?} — early rows predate the optionals.
        let early = try decodeLegacy(
            #"{"id":"a1","name":"Scout","avatar":"p1","role":"digs","systemPrompt":"research","userTemplate":"{input}"}"#,
            as: AgentRecord.self)
        XCTAssertEqual(early.name, "Scout")
        XCTAssertEqual(early.manualContext, "")
        XCTAssertFalse(early.useZoneContext)
        XCTAssertEqual(early.kb, "")
        XCTAssertEqual(early.profileId, "")

        let full = try decodeLegacy(#"""
            {"id":"a2","name":"Sage","avatar":"p3","role":"plans","systemPrompt":"plan","userTemplate":"{input}",
             "manualContext":"three engineers","useZoneContext":true,"kb":"Architecture","profileId":"profile.local"}
            """#, as: AgentRecord.self)
        XCTAssertEqual(full.kb, "Architecture")
        XCTAssertEqual(full.contract.kbId, "Architecture")
        XCTAssertEqual(full.profileId, "profile.local")
        XCTAssertTrue(full.useZoneContext)
        XCTAssertEqual(full.contract.createdAt, full.contract.updatedAt)
    }

    func testLegacyChainDecodes() throws {
        // OLD shape: struct ChainRecord { var id, name: String; var steps: [String] }
        let rec = try decodeLegacy(
            #"{"id":"c1","name":"Refine","steps":["seed1","seed3"]}"#,
            as: ChainRecord.self)
        XCTAssertEqual(rec.steps, ["seed1", "seed3"])
        XCTAssertEqual(rec.contract.createdAt, rec.contract.updatedAt)
    }

    func testLegacyZoneDecodes() throws {
        // The old ZoneRec was CSV-persisted (never Codable), but the flat shape the old
        // struct WOULD have had decodes too — style fields optional, as on-device.
        let rec = try decodeLegacy(
            #"{"path":"Atlas/Q3","color":2,"cx":0.4,"cy":0.5,"w":200,"h":130,"glow":true}"#,
            as: ZoneRec.self)
        XCTAssertEqual(rec.path, "Atlas/Q3")
        XCTAssertEqual(rec.contract.name, "Q3")
        XCTAssertEqual(rec.contract.parentId, "Atlas")
        XCTAssertEqual(rec.color, 2)
        XCTAssertTrue(rec.glow)
        XCTAssertEqual(rec.borderW, 1.5)   // absent style keys default to the old look
        XCTAssertEqual(rec.contract.createdAt, rec.contract.updatedAt)
    }

    // MARK: - 3. fidelity — synced(at:) preserves the contract, bumps only updatedAt

    func testSyncedPreservesNoteTagsAndCreatedAt() throws {
        // THE bug the old bridge had: toContract stamped createdAt = now and tags = [] on
        // every push, so creation time was never stable and hub/web tags were wiped.
        let note = Note(id: "n1", title: "Golden", bodyMarkdown: "body",
                        tags: ["golden", "contract"], createdAt: t0, updatedAt: t0)
        let env = NoteRecord(contract: note, path: "Atlas").synced(at: t1)
        XCTAssertEqual(env.value?.tags, ["golden", "contract"], "tags must survive an iPad push")
        XCTAssertEqual(env.value?.createdAt, t0, "createdAt must stay the creation instant")
        XCTAssertEqual(env.value?.updatedAt, t1, "updatedAt is the only bumped field")
        XCTAssertEqual(env.meta.lastModified, t1)
        XCTAssertEqual(env.meta.kind, .note)
    }

    func testSyncedPreservesKBMembersAgentToolsChainAndWorkflowGraph() throws {
        // The same loss class across the other bridges, fixed by construction.
        let kb = KBRecord(contract: KB(id: "k1", name: "KB", memberIds: ["note:n1"],
                                       createdAt: t0, updatedAt: t0)).synced(at: t1)
        XCTAssertEqual(kb.value?.memberIds, ["note:n1"], "memberIds must survive (old bridge sent [])")
        XCTAssertEqual(kb.value?.createdAt, t0)

        let agent = AgentRecord(contract: Agent(id: "a1", name: "Scout", avatar: "p1", role: "digs",
                                                systemPrompt: "s", userTemplate: "{input}", tools: ["wf1"],
                                                createdAt: t0, updatedAt: t0)).synced(at: t1)
        XCTAssertEqual(agent.value?.tools, ["wf1"], "tools must survive (old bridge sent [])")
        XCTAssertEqual(agent.value?.createdAt, t0)

        let chain = ChainRecord(contract: Chain(id: "c1", name: "Refine", steps: ["a1"],
                                                createdAt: t0, updatedAt: t0)).synced(at: t1)
        XCTAssertEqual(chain.value?.createdAt, t0)

        let wf = WorkflowRecord(contract: WorkflowDefinition(id: "w1", name: "W", prompt: nil,
                                                             graphJson: .object(["n": .number(1)]),
                                                             createdAt: t0, updatedAt: t0)).synced(at: t1)
        XCTAssertEqual(wf.value?.graphJson, .object(["n": .number(1)]), "graphJson must survive (old bridge dropped it)")
        XCTAssertEqual(wf.value?.createdAt, t0)
        XCTAssertEqual(wf.value?.updatedAt, t1)
    }

    func testSyncedPreservesMeetingBornArtifactIdentity() throws {
        // A hub/meeting-born artifact edited on the iPad must keep its meeting linkage,
        // type, confidence, status and sources (the old bridge rebuilt it as a fresh
        // desk plugin_output draft).
        let art = Artifact(id: "art1", meetingId: "m42", artifactType: .decisions, title: "Decisions",
                           bodyMarkdown: "b", structuredJson: .object([:]), confidence: 0.83,
                           status: .accepted, pluginId: "core.summary", pluginVersion: "3",
                           sources: [ArtifactSource(sourceType: "meeting", sourceRef: "m42")],
                           createdAt: t0, updatedAt: t0)
        var rec = OutputRecord(contract: art, path: "Atlas")
        rec.body = "edited on the iPad"
        let env = rec.synced(at: t1)
        XCTAssertEqual(env.value?.meetingId, "m42")
        XCTAssertEqual(env.value?.artifactType, .decisions)
        XCTAssertEqual(env.value?.confidence, 0.83)
        XCTAssertEqual(env.value?.status, .accepted)
        XCTAssertEqual(env.value?.pluginId, "core.summary")
        XCTAssertEqual(env.value?.sources, [ArtifactSource(sourceType: "meeting", sourceRef: "m42")])
        XCTAssertEqual(env.value?.createdAt, t0)
        XCTAssertEqual(env.value?.updatedAt, t1)
        XCTAssertEqual(env.value?.bodyMarkdown, "edited on the iPad")
    }

    func testSyncedPreservesDirectoryCreatedAtAndStripsGeometry() throws {
        let dir = Directory(id: "Atlas/Q3", name: "Q3", parentId: "Atlas", createdAt: t0, updatedAt: t0)
        var zone = ZoneRec(directory: dir, index: 4)
        zone.glow = true; zone.w = 300   // local paint/geometry — must never reach the wire
        let env = zone.synced(at: t1)
        XCTAssertEqual(env.value, Directory(id: "Atlas/Q3", name: "Q3", parentId: "Atlas",
                                            createdAt: t0, updatedAt: t1))
        XCTAssertEqual(env.meta.kind, .directory)
    }

    // MARK: - 4. the golden fixture wraps into records and round-trips

    private struct GoldenFixture: Decodable {
        var note: Note
        var kb: KB
        var agent: Agent
        var chain: Chain
        var workflow: WorkflowDefinition
        var directory: Directory
    }

    private func goldenFixture() throws -> GoldenFixture {
        // …/apple/Tests/RuntimeCoreTests/DeskRecordsTests.swift → repo root
        let root = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()  // RuntimeCoreTests
            .deletingLastPathComponent()  // Tests
            .deletingLastPathComponent()  // apple
            .deletingLastPathComponent()  // repo root
        let url = root
            .appendingPathComponent("pm/roadmap/holdspeak-mobile/contracts/fixtures")
            .appendingPathComponent("primitives-sample.json")
        return try HoldSpeakContracts.decoder().decode(GoldenFixture.self, from: Data(contentsOf: url))
    }

    func testGoldenFixtureWrapsAndRoundTrips() throws {
        let f = try goldenFixture()

        let note = try roundTrip(NoteRecord(contract: f.note, path: "Atlas"), "golden NoteRecord")
        XCTAssertEqual(note.title, "Golden note")
        XCTAssertEqual(note.contract.tags, ["golden", "contract"])

        let kb = try roundTrip(KBRecord(contract: f.kb), "golden KBRecord")
        XCTAssertEqual(kb.contract.memberIds, ["note-golden-1"])
        XCTAssertEqual(kb.items, 1)

        let agent = try roundTrip(AgentRecord(contract: f.agent), "golden AgentRecord")
        XCTAssertEqual(agent.kb, "kb-golden-1")
        XCTAssertEqual(agent.profileId, "")

        let chain = try roundTrip(ChainRecord(contract: f.chain), "golden ChainRecord")
        XCTAssertEqual(chain.steps, ["agent-golden-1"])

        let wf = try roundTrip(WorkflowRecord(contract: f.workflow), "golden WorkflowRecord")
        XCTAssertEqual(wf.prompt, "Draft a stakeholder update")
        XCTAssertNotNil(wf.contract.graphJson)

        let zone = try roundTrip(ZoneRec(directory: f.directory, index: 0), "golden ZoneRec")
        XCTAssertEqual(zone.path, "Atlas/Q3")
        XCTAssertEqual(zone.contract.parentId, "Atlas")

        // and the wrapped contracts push back out through the canonical wire coder intact
        let pushed = try HoldSpeakContracts.encoder().encode(note.synced(at: t1))
        let landed = try HoldSpeakContracts.decoder().decode(Synced<Note>.self, from: pushed)
        XCTAssertEqual(landed.value?.tags, ["golden", "contract"])
        XCTAssertEqual(landed.value?.createdAt, f.note.createdAt)
        XCTAssertEqual(landed.value?.updatedAt, t1)
    }
}
