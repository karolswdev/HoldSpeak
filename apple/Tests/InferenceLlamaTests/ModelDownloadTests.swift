import XCTest
import Contracts
import Providers
@testable import InferenceLlama

/// HSM-5-03 — the Hugging Face download path, end to end. Opt-in (`HS_HF_DOWNLOAD=1`)
/// because it pulls a real (small) model over the network; the default suite stays
/// offline. Proves: catalog artifact → downloader → ModelStore (resolvable path) →
/// LlamaProvider loads it → completes.
final class ModelDownloadTests: XCTestCase {

    // A small real model so the proof is fast (~0.6 GB), distinct from the catalog
    // tiers (which are 3B/8B/12B).
    private let tinyArtifact = ModelArtifact(
        tier: .fourB, displayName: "TinyLlama 1.1B Chat (Q4_K_M)",
        huggingFaceRepo: "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
        quantization: "Q4_K_M", fileName: "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")

    func testDownloadThenLoadAndComplete() async throws {
        guard ProcessInfo.processInfo.environment["HS_HF_DOWNLOAD"] == "1" else {
            throw XCTSkip("set HS_HF_DOWNLOAD=1 to run the real Hugging Face download proof")
        }
        let dir = URL(fileURLWithPath: NSTemporaryDirectory())
            .appendingPathComponent("hsm-dl-\(UUID().uuidString)", isDirectory: true)
        let store = ModelStore(root: dir)
        defer { try? FileManager.default.removeItem(at: dir) }

        let downloader = ModelDownloader()
        let url = try await downloader.download(tinyArtifact, into: store) { p in
            if Int(p * 100) % 25 == 0 { print(String(format: "download %.0f%%", p * 100)) }
        }

        // Resolvable through the store under the catalogued filename.
        XCTAssertEqual(url.lastPathComponent, tinyArtifact.fileName)
        XCTAssertTrue(store.isInstalled(tinyArtifact))

        // And the engine can load + complete from it.
        let provider = try LlamaProvider(modelPath: url.path, maxTokenCount: 256)
        let out = try await provider.complete(prompt: "Reply with exactly one word: PONG")
        print("📥 downloaded-model completion: \(out)")
        XCTAssertFalse(out.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
    }
}
