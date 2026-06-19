import XCTest
import Contracts
import Providers
@testable import RuntimeCore

/// HSM-5-06 — live, opt-in integration of the full artifact path against a real
/// OpenAI-compatible endpoint. Skipped unless `HS_LIVE_ENDPOINT` is set (so CI and
/// the default `swift test` stay hermetic). Run it against the homelab box with:
///
///   HS_LIVE_ENDPOINT=http://192.168.1.43:8080/v1 HS_LIVE_MODEL=local \
///     swift test --filter LiveEndpointIntegrationTests
///
/// This is the host-side rehearsal of what the iPad does in Mode C: a transcript →
/// `OpenAIEndpointProvider` → `ArtifactGenerationEngine` → contract-shaped artifacts.
final class LiveEndpointIntegrationTests: XCTestCase {

    private func liveConfig() throws -> EndpointConfig {
        guard let raw = ProcessInfo.processInfo.environment["HS_LIVE_ENDPOINT"],
              let url = URL(string: raw) else {
            throw XCTSkip("set HS_LIVE_ENDPOINT to run the live endpoint integration")
        }
        let model = ProcessInfo.processInfo.environment["HS_LIVE_MODEL"] ?? "local"
        return EndpointConfig(baseURL: url, model: model, temperature: 0.2, timeout: 180)
    }

    /// A small but real meeting: two clear decisions and an action item, so the
    /// model has substance to extract (mirrors the desktop baseline shape).
    private func sampleTranscript() -> Transcript {
        let lines: [(String, String)] = [
            ("Alice", "Let's lock the API. I propose we standardize on the OpenAI-compatible endpoint for mobile inference."),
            ("Bob", "Agreed. We decided the iPad will default to the homelab endpoint rather than loading a local model."),
            ("Alice", "Bob, can you wire the endpoint config screen by Friday?"),
            ("Bob", "Yes, I'll own the endpoint settings UI and have it ready Friday."),
            ("Alice", "One risk: if the LAN is unreachable we need a local fallback so meetings don't stall."),
        ]
        var t = 0.0
        let segments = lines.map { pair -> Segment in
            defer { t += 5 }
            return Segment(text: pair.1, speaker: pair.0, startTime: t, endTime: t + 5)
        }
        return Transcript(meetingId: "live_mtg_001", segments: segments, transcriptHash: "live-hash")
    }

    func testLiveArtifactGenerationAgainstEndpoint() async throws {
        let config = try liveConfig()
        let provider = OpenAIEndpointProvider(config: config)
        let engine = ArtifactGenerationEngine(provider: provider)

        let types: [ArtifactType] = [.decisions, .actionItems, .requirements]
        let results = await engine.generate(types: types, from: sampleTranscript())

        var succeeded = 0
        for (type, result) in results {
            switch result {
            case .success(let artifact):
                succeeded += 1
                XCTAssertEqual(artifact.artifactType, type)
                XCTAssertEqual(artifact.status, .draft)          // propose-only
                XCTAssertFalse(artifact.title.isEmpty)
                print("✅ [\(type.rawValue)] \(artifact.title)\n\(artifact.bodyMarkdown)\n")
            case .failure(let error):
                print("⚠️  [\(type.rawValue)] failed: \(error)")
            }
        }
        XCTAssertGreaterThan(succeeded, 0, "expected at least one artifact from the live endpoint")
    }

    /// HSM-6-05 mechanism demonstration: score real endpoint-generated artifacts
    /// against a substance rubric, proving the parity verdict runs on live mobile
    /// output. NOT the formal Gate-5 — that needs the owner-signed baseline set +
    /// rubric (HSM-6-04 acceptance). This uses a rubric over the sample meeting's
    /// known facts to show the path end to end.
    func testLiveParityVerdictMechanism() async throws {
        let config = try liveConfig()
        let provider = OpenAIEndpointProvider(config: config)
        let engine = ArtifactGenerationEngine(provider: provider)

        let outcomes = await engine.generate(types: [.decisions, .actionItems], from: sampleTranscript())
        let artifacts = outcomes.compactMap { try? $0.result.get() }

        let rubric = ParityRubric(
            meetingId: "live_mtg_001",
            expectations: [
                .init(category: .artifact(.decisions),
                      mustCover: ["endpoint", "iPad", "homelab"]),
                .init(category: .artifact(.actionItems),
                      mustCover: ["Bob", "Friday", "endpoint"]),
            ],
            threshold: 0.8)

        let report = ParityScorer.score(artifacts: artifacts, summary: nil, rubric: rubric)
        print("📊 parity coverage \(String(format: "%.2f", report.overallCoverage)) (threshold \(report.threshold)) → \(report.passed ? "PASS" : "MISS")")
        for c in report.perCategory {
            print("   • \(c.category): \(c.covered)/\(c.total) covered; missing=\(c.missing)")
        }
        XCTAssertGreaterThan(report.overallCoverage, 0.0, "scorer ran on real mobile output")
    }
}
