import XCTest
import Contracts
import Providers
@testable import RuntimeCore

/// HSM-15-04 — the pure workflow runner over the linear `Workflow` model. Fakes for
/// `ILLMProvider` keep these host-tests model-free and instant (the injected backoff is a
/// no-op).
final class WorkflowRunnerTests: XCTestCase {

    // MARK: Fakes

    /// Records every prompt it's asked to complete; echoes a transform so threading is
    /// observable. Optionally fails the first `failTimes` calls (to drive retry/policy).
    final class RecordingProvider: ILLMProvider, @unchecked Sendable {
        let transform: @Sendable (String) -> String
        private(set) var prompts: [String] = []
        private(set) var calls = 0
        private let failTimes: Int
        private let error: Error

        init(failTimes: Int = 0,
             error: Error = NSError(domain: "fake", code: 1),
             transform: @escaping @Sendable (String) -> String = { "OUT(\($0))" }) {
            self.failTimes = failTimes
            self.error = error
            self.transform = transform
        }

        func complete(prompt: String) async throws -> String {
            prompts.append(prompt)
            calls += 1
            if calls <= failTimes { throw error }
            return transform(prompt)
        }
    }

    /// Always throws — an unreachable target.
    final class DeadProvider: ILLMProvider, @unchecked Sendable {
        private(set) var calls = 0
        func complete(prompt: String) async throws -> String {
            calls += 1
            throw NSError(domain: "unreachable", code: 42)
        }
    }

    private func noBackoffPolicy(maxRetries: Int, policy: FailurePolicy) -> RunPolicy {
        RunPolicy(maxRetries: maxRetries, failurePolicy: policy, backoff: { _ in })
    }

    // MARK: {input} substitution into the llmCall prompt

    func testCustomLLMCallSubstitutesInput() async {
        let provider = RecordingProvider()
        let runner = WorkflowRunner(provider: provider)
        let step = WorkflowStep.llmCall(name: "Q",
                                        prompt: "From {input}, list questions.",
                                        input: .meeting)
        let wf = Workflow(name: "c", source: .fullTranscript, steps: [step], output: .note)

        _ = await runner.run(wf, sourceText: "THE MEETING TEXT")

        XCTAssertEqual(provider.prompts.count, 1)
        XCTAssertEqual(provider.prompts.first, "From THE MEETING TEXT, list questions.",
                       "{input} is replaced with the resolved source text")
    }

    // MARK: input threading across steps

    func testInputThreadsAcrossSteps() async {
        // Two llmCalls bound to the previous step: step 2 must see step 1's output.
        let provider = RecordingProvider(transform: { _ in "STEP_OUT" })
        let runner = WorkflowRunner(provider: provider)
        let s1 = WorkflowStep.llmCall(name: "a", prompt: "first:{input}", input: .meeting)
        let s2 = WorkflowStep.llmCall(name: "b", prompt: "second:{input}", input: .previousStep)
        let wf = Workflow(name: "thread", source: .fullTranscript, steps: [s1, s2], output: .note)

        let result = await runner.run(wf, sourceText: "SRC")

        XCTAssertEqual(provider.prompts.first, "first:SRC")
        XCTAssertEqual(provider.prompts.last, "second:STEP_OUT",
                       "step 2 reads step 1's output, not the source")
        XCTAssertEqual(result.finalText, "STEP_OUT")
        XCTAssertTrue(result.didComplete)
    }

    func testFirstStepReadsSourceSubsequentReadPrevious() async {
        // summarize then rewrite — both model-backed, both read the threaded value.
        let provider = RecordingProvider(transform: { p in "TRANSFORMED(\(p.prefix(9)))" })
        let runner = WorkflowRunner(provider: provider)
        let wf = Workflow(name: "s", source: .fullTranscript,
                          steps: [.summarize, .rewrite(tone: "executive")], output: .note)

        let result = await runner.run(wf, sourceText: "RAW")

        XCTAssertEqual(result.steps.count, 2)
        XCTAssertTrue(provider.prompts[0].contains("RAW"), "summarize reads the source")
        XCTAssertTrue(provider.prompts[1].contains("executive"), "rewrite uses its tone template")
        XCTAssertTrue(provider.prompts[1].contains(result.steps[0].output),
                      "rewrite's prompt embeds summarize's output")
    }

    // MARK: keepIf is a pure filter (no model)

    func testKeepIfFiltersLinesAndCallsNoProvider() async {
        let provider = RecordingProvider()
        let runner = WorkflowRunner(provider: provider)
        let wf = Workflow(name: "f", source: .fullTranscript,
                          steps: [.keepIf("risk")], output: .artifacts)
        let src = "line about budget\na RISK we flagged\nanother line\nrisk register"

        let result = await runner.run(wf, sourceText: src)

        XCTAssertEqual(provider.calls, 0, "keepIf is pure — no provider call")
        XCTAssertEqual(result.finalText, "a RISK we flagged\nrisk register",
                       "only lines mentioning the keyword survive, case-insensitive")
        XCTAssertEqual(result.steps.first?.attempts, 0)
        XCTAssertEqual(result.steps.first?.status, .ok)
    }

    // MARK: step ordering

    func testStepOrderingIsPreserved() async {
        let provider = RecordingProvider(transform: { _ in "X" })
        let runner = WorkflowRunner(provider: provider)
        let wf = Workflow(name: "o", source: .fullTranscript,
                          steps: [.summarize, .keepIf("X"), .rewrite(tone: "plain")],
                          output: .note)

        let result = await runner.run(wf, sourceText: "src")

        XCTAssertEqual(result.steps.map(\.index), [0, 1, 2])
        XCTAssertEqual(result.steps.map(\.label),
                       ["Summarize", "Keep if · X", "Rewrite · plain"])
    }

    // MARK: retry-then-park

    func testRetryThenParkAfterExhaustingRetries() async {
        let dead = DeadProvider()
        let runner = WorkflowRunner(provider: dead,
                                    policy: noBackoffPolicy(maxRetries: 2, policy: .retryThenQueue))
        let wf = Workflow(name: "p", source: .fullTranscript, steps: [.summarize], output: .note)

        let result = await runner.run(wf, sourceText: "SRC")

        XCTAssertEqual(dead.calls, 3, "1 try + 2 retries")
        XCTAssertTrue(result.didPark)
        XCTAssertEqual(result.parked?.resumeFromStep, 0)
        XCTAssertEqual(result.parked?.carriedInput, "SRC")
        XCTAssertEqual(result.steps.first?.status, .parked)
        XCTAssertEqual(result.steps.first?.attempts, 3)
    }

    func testParkResumesFromCachedStepWithoutRecompute() async {
        // A parked run resumes at the parked step with its carried input; earlier steps
        // are NOT recomputed (we feed resumeFrom + seedInput).
        let provider = RecordingProvider(transform: { _ in "RESUMED" })
        let runner = WorkflowRunner(provider: provider)
        let wf = Workflow(name: "r", source: .fullTranscript,
                          steps: [.summarize, .rewrite(tone: "x")], output: .note)

        let result = await runner.run(wf, sourceText: "ORIGINAL",
                                      resumeFrom: 1, seedInput: "CACHED_STEP0_OUTPUT")

        XCTAssertEqual(provider.calls, 1, "only step 1 ran — step 0 was cached")
        XCTAssertEqual(result.steps.map(\.index), [1], "resumed at the parked step")
        XCTAssertTrue(provider.prompts.first!.contains("CACHED_STEP0_OUTPUT"),
                      "the resumed step consumes the carried/cached input")
    }

    // MARK: fallback to a second provider

    func testFallbackOnDeviceUsesSecondProvider() async {
        let primary = DeadProvider()                                   // unreachable endpoint
        let fallback = RecordingProvider(transform: { _ in "ON_DEVICE_RESULT" })
        let runner = WorkflowRunner(provider: primary, fallback: fallback,
                                    policy: noBackoffPolicy(maxRetries: 1, policy: .fallbackOnDevice))
        let wf = Workflow(name: "fb", source: .fullTranscript, steps: [.summarize], output: .note)

        let result = await runner.run(wf, sourceText: "SRC")

        XCTAssertEqual(primary.calls, 2, "1 try + 1 retry on the primary, then it gave up")
        XCTAssertEqual(fallback.calls, 1, "the fallback ran once and succeeded")
        XCTAssertTrue(result.didComplete)
        XCTAssertEqual(result.finalText, "ON_DEVICE_RESULT")
        XCTAssertEqual(result.steps.first?.status, .fellBack)
    }

    func testSkipPolicyCarriesInputThrough() async {
        let dead = DeadProvider()
        let runner = WorkflowRunner(provider: dead,
                                    policy: noBackoffPolicy(maxRetries: 0, policy: .skip))
        let wf = Workflow(name: "sk", source: .fullTranscript, steps: [.summarize], output: .note)

        let result = await runner.run(wf, sourceText: "CARRY_ME")

        XCTAssertEqual(dead.calls, 1, "one try, no retries")
        XCTAssertTrue(result.didComplete)
        XCTAssertEqual(result.finalText, "CARRY_ME", "skip carries the input through unchanged")
        XCTAssertEqual(result.steps.first?.status, .skipped)
    }
}
