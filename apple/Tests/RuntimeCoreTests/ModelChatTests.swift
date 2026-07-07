import XCTest
import Contracts
@testable import RuntimeCore

/// HSM-15-13 — the synthesized model persona: id/name/profile mapping is the seam
/// (the chat surface itself is sim-shot, not unit-tested).
final class ModelChatTests: XCTestCase {

    private func manifest(node: String = "desktop", name: String = "Qwen3.5-9B-UD-Q6_K_XL") -> ModelManifest {
        ModelManifest(id: "\(node):intel", node: node, name: name,
                      capabilities: ["language"], createdAt: .distantPast, updatedAt: .distantPast)
    }

    func testPersonaWearsTheModelAndPinsTheProfile() {
        let p = ModelChat.persona(manifest: manifest(), profileId: "desktop:Qwen3.5-9B-UD-Q6_K_XL")
        XCTAssertEqual(p.id, "modelchat:desktop:Qwen3.5-9B-UD-Q6_K_XL")
        XCTAssertEqual(p.name, "Qwen3.5-9B-UD-Q6_K_XL")
        XCTAssertEqual(p.role, "your desktop")
        XCTAssertEqual(p.profileId, "desktop:Qwen3.5-9B-UD-Q6_K_XL")
        // No standing context — grounding belongs to the conversation (15-12).
        XCTAssertEqual(p.systemPrompt, "")
        XCTAssertEqual(p.manualContext, "")
        XCTAssertFalse(p.useZoneContext)
        XCTAssertEqual(p.kb, "")
    }

    func testThreadsAreNodeScoped() {
        XCTAssertNotEqual(
            ModelChat.persona(manifest: manifest(node: "desktop"), profileId: "x").id,
            ModelChat.persona(manifest: manifest(node: "iPad"), profileId: "x").id
        )
        XCTAssertEqual(ModelChat.nodeLabel("iPad"), "iPad")
    }

    func testIsModelChatDiscriminates() {
        XCTAssertTrue(ModelChat.isModelChat("modelchat:desktop:Qwen"))
        XCTAssertFalse(ModelChat.isModelChat("seed1"))
    }
}
