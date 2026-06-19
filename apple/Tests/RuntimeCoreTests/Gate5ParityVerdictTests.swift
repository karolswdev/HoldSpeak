import XCTest
import Contracts
import Providers
@testable import RuntimeCore

/// HSM-6-05 — the Gate-5 parity verdict.
///
/// Runs the HSM-6-04 parity harness over a fixed baseline meeting with **real**
/// mobile generation (the Runtime Core artifact engine driving a real model via the
/// charter Mode-B/C endpoint provider), and records the verdict against a rubric
/// whose threshold is fixed up front (0.8) — no post-hoc tuning to pass.
///
/// The rubric is the owner-delegated parity bar (owner: "for gate five, I trust
/// your call", 2026-06-19): per category, the substantive facts a good desktop
/// artifact set covers for this meeting, grounded in the transcript (HSM-6-04's
/// operational definition of "the desktop baseline"). Scoring is deterministic;
/// generation is not, so the verdict runs N iterations and reports the spread.
///
/// Opt-in (`HS_LIVE_ENDPOINT`), so the default suite stays hermetic:
///   HS_LIVE_ENDPOINT=http://192.168.1.13:8081/v1 HS_LIVE_MODEL=local \
///     swift test --filter Gate5ParityVerdictTests
final class Gate5ParityVerdictTests: XCTestCase {

    private func liveConfig() throws -> EndpointConfig {
        guard let raw = ProcessInfo.processInfo.environment["HS_LIVE_ENDPOINT"],
              let url = URL(string: raw) else {
            throw XCTSkip("set HS_LIVE_ENDPOINT to run the Gate-5 parity verdict")
        }
        let model = ProcessInfo.processInfo.environment["HS_LIVE_MODEL"] ?? "local"
        return EndpointConfig(baseURL: url, model: model, temperature: 0.2, timeout: 240)
    }

    /// The fixed Gate-5 baseline meeting: an architecture/planning standup with
    /// clear decisions, owned actions, a risk, and a requirement — the substance a
    /// desktop run would extract.
    private func baselineMeeting() -> Transcript {
        let lines: [(String, String)] = [
            ("Priya", "Today we're deciding the mobile inference architecture for the iPad client."),
            ("Marco", "I propose we standardize on an OpenAI-compatible endpoint as the default, with on-device GGUF as a fallback."),
            ("Priya", "Agreed. Decision: the iPad defaults to the homelab endpoint, and we keep local inference as a user setting."),
            ("Marco", "We also decided to use llama.cpp with Q4_K_M models for the on-device path."),
            ("Priya", "Action item: Marco will implement the endpoint provider and the mode setting by next Tuesday."),
            ("Sara", "Action item: I'll write the parity harness and define the coverage rubric before we ship."),
            ("Marco", "Risk: if the LAN endpoint is unreachable, meetings stall — we need a graceful local fallback."),
            ("Priya", "Requirement: artifact generation must produce contract-shaped JSON that validates against the Phase-0 schemas."),
            ("Sara", "One more requirement: the runtime must never act autonomously — propose, then a human approves."),
        ]
        var t = 0.0
        let segments = lines.map { pair -> Segment in
            defer { t += 8 }
            return Segment(text: pair.1, speaker: pair.0, startTime: t, endTime: t + 8)
        }
        return Transcript(meetingId: "gate5_baseline_001", segments: segments,
                          transcriptHash: "gate5-baseline-hash")
    }

    /// The parity rubric — the fixed bar. Threshold 0.8, set before any run.
    private func rubric() -> ParityRubric {
        ParityRubric(
            meetingId: "gate5_baseline_001",
            expectations: [
                .init(category: .artifact(.decisions),
                      mustCover: ["endpoint", "homelab", "local", "llama"]),
                .init(category: .artifact(.actionItems),
                      mustCover: ["Marco", "provider", "Sara", "rubric"]),
                .init(category: .artifact(.riskRegister),
                      mustCover: ["LAN", "fallback"]),
                .init(category: .artifact(.requirements),
                      mustCover: ["contract", "JSON", "approves"]),
            ],
            threshold: 0.8)
    }

    func testGate5ParityVerdict() async throws {
        let config = try liveConfig()
        let provider = OpenAIEndpointProvider(config: config)
        let engine = ArtifactGenerationEngine(provider: provider)
        let r = rubric()
        let types: [ArtifactType] = [.decisions, .actionItems, .riskRegister, .requirements]

        let iterations = 3
        var coverages: [Double] = []
        var passes = 0

        print("=== HSM-6-05 Gate-5 parity verdict (threshold \(r.threshold)) ===")
        print("model=\(config.model) endpoint=\(config.baseURL.absoluteString) iterations=\(iterations)")

        for i in 1...iterations {
            let outcomes = await engine.generate(types: types, from: baselineMeeting())
            let artifacts = outcomes.compactMap { try? $0.result.get() }
            let report = ParityScorer.score(artifacts: artifacts, summary: nil, rubric: r)
            coverages.append(report.overallCoverage)
            if report.passed { passes += 1 }
            print(String(format: "run %d: overall %.2f → %@", i, report.overallCoverage,
                         report.passed ? "PASS" : "MISS"))
            for c in report.perCategory {
                print(String(format: "   %@: %d/%d%@", "\(c.category)", c.covered, c.total,
                             c.missing.isEmpty ? "" : " missing=\(c.missing)"))
            }
        }

        let mean = coverages.reduce(0, +) / Double(coverages.count)
        print(String(format: "VERDICT: mean coverage %.2f over %d runs; %d/%d runs >= threshold",
                     mean, iterations, passes, iterations))

        // The recorded verdict: mean coverage meets the pre-fixed bar.
        XCTAssertGreaterThanOrEqual(mean, r.threshold,
            "Gate-5: mean parity coverage \(mean) below threshold \(r.threshold) — file as a finding, do not lower the bar")
    }
}
