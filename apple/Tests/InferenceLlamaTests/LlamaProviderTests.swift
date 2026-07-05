import XCTest
import Contracts
import Providers
import RuntimeCore
@testable import InferenceLlama

/// HSM-5-02 — the on-device (Mode A) engine proof. Opt-in via `HS_GGUF_PATH` (a
/// local `.gguf`) so the default suite stays fast and model-free; the target itself
/// still builds llama.cpp, proving the engine integrates behind `ILLMProvider`.
///
///   HS_GGUF_PATH=/path/to/model.gguf swift test --filter LlamaProviderTests
///
/// This is the host (macOS Metal) rehearsal of Mode A; the iPad on-device run is the
/// same `LlamaProvider` behind the same seam (device launch gated separately).
final class LlamaProviderTests: XCTestCase {

    private func modelPath() throws -> String {
        guard let p = ProcessInfo.processInfo.environment["HS_GGUF_PATH"], !p.isEmpty else {
            throw XCTSkip("set HS_GGUF_PATH to a local .gguf to run the Mode-A engine proof")
        }
        return p
    }

    func testLoadsGGUFAndCompletes() async throws {
        let path = try modelPath()
        let provider = try LlamaProvider(modelPath: path, maxTokenCount: 512)
        let out = try await provider.complete(prompt: "Reply with exactly one word: PONG")
        print("📦 Mode-A completion: \(out)")
        XCTAssertFalse(out.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
                       "expected a non-empty completion from the local GGUF")
    }

    /// Full Mode A: transcript → LlamaProvider → ArtifactGenerationEngine →
    /// contract-shaped artifacts, fully local (no network).
    func testModeAArtifactGenerationFullyLocal() async throws {
        let path = try modelPath()
        let provider = try LlamaProvider(modelPath: path, maxTokenCount: 1024)
        let engine = ArtifactGenerationEngine(provider: provider)

        let segments = [
            Segment(text: "We decided to ship the iPad client with on-device inference as a fallback.",
                    speaker: "Alice", startTime: 0, endTime: 5),
            Segment(text: "Action item: Bob will benchmark the 8B model on the iPad by Friday.",
                    speaker: "Alice", startTime: 5, endTime: 10),
        ]
        let transcript = Transcript(meetingId: "modea_001", segments: segments, transcriptHash: "modea-hash")

        let results = await engine.generate(types: [.decisions, .actionItems], from: transcript)
        let artifacts = results.compactMap { try? $0.result.get() }
        for a in artifacts { print("✅ [\(a.artifactType.rawValue)] \(a.title)\n\(a.bodyMarkdown)") }

        XCTAssertGreaterThan(artifacts.count, 0, "expected at least one artifact from the local model")
        XCTAssertTrue(artifacts.allSatisfy { $0.status == .draft })   // propose-only
    }

    // MARK: - model-free locks (no GGUF needed)

    /// The on-device sampling default is the faithful-extraction preset, not
    /// LLM.swift's hot chat default (temp 0.8 / topK 40). This is the single
    /// highest-leverage on-device quality knob — lock its values.
    func testExtractionSamplingPresetValues() {
        let s = LlamaSampling.extraction
        XCTAssertEqual(s.temp, 0.4, "extraction runs faithful, not hot (LLM.swift default is 0.8)")
        XCTAssertEqual(s.topP, 0.8)
        XCTAssertEqual(s.topK, 20, "Qwen3 non-thinking guidance")
        XCTAssertEqual(s.repeatPenalty, 1.1, "gentle — transcripts legitimately repeat terms")
    }

    /// A downloaded/imported model is prompted in ITS family's template, not a
    /// one-size ChatML — verified by filename, no model load.
    func testAutoTemplatePicksTheModelFamily() {
        // Just assert distinct templates resolve per family (Template isn't
        // Equatable, so compare stop sequences / identity via a smoke check that
        // the picker doesn't collapse everyone to ChatML).
        let qwen = LlamaProvider.autoTemplate(for: "Qwen3-4B-Instruct-2507-Q5_K_M.gguf")
        let llama = LlamaProvider.autoTemplate(for: "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf")
        let gemma = LlamaProvider.autoTemplate(for: "gemma-3n-E4B-it-Q4_K_M.gguf")
        // Llama-3 uses the eot header format; Qwen/Gemma do not.
        XCTAssertEqual(llama.stopSequence, "<|eot_id|>", "Llama-3 gets its header template")
        XCTAssertNotEqual(qwen.stopSequence, "<|eot_id|>", "Qwen is ChatML, not Llama-3")
        XCTAssertNotEqual(gemma.stopSequence, "<|eot_id|>", "Gemma is its own template")
    }
}
