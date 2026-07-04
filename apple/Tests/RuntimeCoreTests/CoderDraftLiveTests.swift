import XCTest
import Contracts
@testable import Providers
@testable import RuntimeCore

/// HSM-17-05 — the OPT-IN live endpoint draft proof. Skipped unless
/// `HS_LIVE_DRAFT_ENDPOINT` names an OpenAI-compatible base URL (e.g. the
/// LAN llama.cpp). Mirrors the Python suite's opt-in e2e posture: CI never
/// runs it; a human proves the real wire locally and records the output.
final class CoderDraftLiveTests: XCTestCase {

    func testLiveEndpointDraftsAGroundedAnswer() async throws {
        guard let base = ProcessInfo.processInfo.environment["HS_LIVE_DRAFT_ENDPOINT"],
              let url = URL(string: base) else {
            throw XCTSkip("set HS_LIVE_DRAFT_ENDPOINT to run the live endpoint draft proof")
        }
        let model = ProcessInfo.processInfo.environment["HS_LIVE_DRAFT_MODEL"] ?? "local-model"
        let provider = OpenAIEndpointProvider(config: .init(baseURL: url, model: model, apiKey: nil))

        let draft = try await CoderAnswer.draft(
            provider,
            agent: "claude",
            question: "Should the sync queue retry failed pushes automatically, or surface them for manual retry?",
            groundingTitle: "Mesh queue design",
            grounding: "Decision: the mesh queue is durable-first; failed pushes stay queued and the failure policy is per-workflow (retry-then-queue / fallback / skip)."
        )

        print("LIVE DRAFT >>> \(draft)")
        XCTAssertFalse(draft.isEmpty)
        XCTAssertGreaterThan(draft.count, 20)
    }
}
