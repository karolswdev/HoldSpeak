import XCTest
import Contracts
import Providers
@testable import RuntimeCore

/// A LIVE proof (skipped unless `RUN_LIVE_ENDPOINT=1`): runs the real iPad `WorkflowRunner`
/// against a REAL LAN model endpoint via `OpenAIEndpointProvider` — NO fake provider. Proves the
/// Workbench execution path actually calls a model and threads real output. Endpoint is
/// configurable via env so it can target the clean Mac llama-server (.28) or any OpenAI-compatible box.
final class LiveEndpointRunnerTests: XCTestCase {
    func testWorkflowRunsAgainstRealEndpoint() async throws {
        let env = ProcessInfo.processInfo.environment
        try XCTSkipUnless(env["RUN_LIVE_ENDPOINT"] == "1", "set RUN_LIVE_ENDPOINT=1 to run the live proof")

        let urlStr = env["LIVE_ENDPOINT_URL"] ?? "http://192.168.1.43:8080"
        let model = env["LIVE_ENDPOINT_MODEL"] ?? "Qwythos-9B-Claude-Mythos-5-1M-Q6_K.gguf"
        let config = EndpointConfig(baseURL: URL(string: urlStr)!, model: model,
                                    apiKey: nil, temperature: 0.2, timeout: 120)
        let provider = OpenAIEndpointProvider(config: config)

        // A real transcript (the PI-204 incident) as the workflow SOURCE.
        let transcript = """
        Wei: api.prod went down at 14:02 — clients got 5xx, the TLS cert had expired.
        Priya: cert-manager should have rotated it. The ACME HTTP-01 solver path was blocked by the PI-198 network policy change, so renewal failed silently.
        Wei: and our only alert was edge 5xx — nothing watched cert expiry headroom.
        Priya: let's add a 14-day expiry-headroom alert. I'll take that.
        Wei: I'll add a synthetic ACME-path test in CI so a network policy change can't silently break renewal again.
        Me: I'll write the runbook break-glass procedure and the postmortem.
        """

        // A real user-built workflow: SOURCE -> a custom LLM call -> note. This is what the
        // canvas lowers to; here we run it directly through the runner with a REAL provider.
        let workflow = Workflow(
            name: "Risks as questions",
            source: .fullTranscript,
            steps: [.llmCall(
                name: "Risks as questions",
                prompt: "From the following meeting notes, list the top 3 risks as pointed questions a reviewer should ask. One per line, no preamble.\n\n{input}",
                input: .meeting)],
            output: .note)

        let runner = WorkflowRunner(provider: provider)
        let result = await runner.run(workflow, sourceText: transcript)

        print("=== LIVE iPad WorkflowRunner @ \(urlStr) (\(model)) ===")
        for s in result.steps {
            print("[step] \(s.label) — status=\(s.status) attempts=\(s.attempts)")
        }
        print("--- finalText ---")
        print(result.finalText)
        print("--- end ---")

        XCTAssertNil(result.failure, "the run should not fail outright")
        XCTAssertFalse(result.finalText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
                       "the real model must return non-empty text")
    }
}
