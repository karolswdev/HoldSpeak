import Foundation
import Contracts
import Providers

/// HSM-15-04 — **One runner for the mesh.** The Workbench draws a program (`Workflow`);
/// this makes it real. It walks the linear `Workflow.steps` in order, threads an
/// intermediate text value, executes the model-backed steps through an **injected**
/// `ILLMProvider` (so the host tests pass a fake and never load a model), runs the pure
/// transforms (`keepIf`) with no model, and enforces a per-run **failure policy** when a
/// provider call throws (retry → park, fall back to a second provider, or skip).
///
/// Pure RuntimeCore: no SwiftUI, no App types, no `RunQueueStore`. The "queue/park"
/// outcome is a *typed result the caller can enqueue* — the App layer owns the real queue.
/// The "dispatch to the Mac" mesh target is a stubbed seam (`unimplemented`) until the
/// desktop run-a-capability RPC (HSM-15-02) exists.

// MARK: - Failure policy

/// What the runner does when a model-backed step's provider call throws (an unreachable
/// endpoint, a dead on-device model, a transport error). The per-run default; a future
/// per-node override slots in here unchanged.
public enum FailurePolicy: String, Codable, Sendable, CaseIterable {
    /// Retry up to the configured bound (with backoff), then **park** the run so the
    /// caller can enqueue it as blocked and resume from this step later.
    case retryThenQueue
    /// Retry up to the bound, then swap to the injected **fallback** provider
    /// (the on-device model — the egress badge updates, it didn't leave after all).
    case fallbackOnDevice
    /// Retry up to the bound, then **skip** the step, carrying the resolved input through
    /// unchanged.
    case skip
}

/// Tunables for retry/backoff. **Injectable so tests never sleep**: the default `sleep`
/// closure is a no-op, and a test can assert the retry count without waiting.
public struct RunPolicy: Sendable {
    /// How many *additional* attempts after the first (0 = try once, never retry).
    public var maxRetries: Int
    /// The per-run default policy when a provider call throws.
    public var failurePolicy: FailurePolicy
    /// Sleep between attempts. `attempt` is 1-based (the retry index). Default: no sleep,
    /// so host tests are instant. A host can supply real `Task.sleep`-backed backoff.
    public var backoff: @Sendable (_ attempt: Int) async -> Void

    public init(maxRetries: Int = 2,
                failurePolicy: FailurePolicy = .retryThenQueue,
                backoff: @escaping @Sendable (_ attempt: Int) async -> Void = { _ in }) {
        self.maxRetries = maxRetries
        self.failurePolicy = failurePolicy
        self.backoff = backoff
    }
}

// MARK: - Run targets (the mesh seam)

/// Where a step runs. The on-device / endpoint paths both go through the injected
/// `ILLMProvider`; **`dispatchToMac` is the stubbed mesh seam** — building the desktop RPC
/// is later work (HSM-15-02). A step that resolves to `.dispatchToMac` and has no dispatch
/// handler wired throws `WorkflowRunError.dispatchUnimplemented`.
public enum RunTarget: String, Codable, Sendable, CaseIterable {
    case onDevice
    case endpoint
    case dispatchToMac
}

// MARK: - Result types

/// How a single step resolved.
public enum StepStatus: String, Codable, Sendable {
    case ok            // produced output
    case skipped       // failure policy `.skip` (or a step that does nothing)
    case fellBack      // failure policy `.fallbackOnDevice` — succeeded on the fallback
    case parked        // failure policy `.retryThenQueue` — exhausted retries, run parked here
    case failed        // unrecoverable (e.g. dispatch unimplemented, fallback also threw)
}

/// The outcome of one step in the walk — what ran, what it produced, how many attempts.
public struct StepOutcome: Sendable, Equatable {
    public var index: Int               // position in `workflow.steps`
    public var label: String            // the step's human label
    public var status: StepStatus
    public var input: String            // the resolved input fed to this step
    public var output: String           // the threaded output after this step
    public var attempts: Int            // provider attempts made (0 for pure/no-model steps)
    public var error: String?           // the last error description, if any

    public init(index: Int, label: String, status: StepStatus, input: String,
                output: String, attempts: Int, error: String? = nil) {
        self.index = index; self.label = label; self.status = status
        self.input = input; self.output = output; self.attempts = attempts; self.error = error
    }
}

/// Where a parked run resumes from — enough for the caller (the App's `RunQueueStore`) to
/// enqueue a `blocked` job and pick up later **without recomputing completed steps**.
public struct ParkedRun: Sendable, Equatable {
    public var workflowID: UUID
    public var resumeFromStep: Int      // the index of the step that parked
    public var carriedInput: String     // the resolved input that step never consumed
    public var reason: String           // the last error description

    public init(workflowID: UUID, resumeFromStep: Int, carriedInput: String, reason: String) {
        self.workflowID = workflowID; self.resumeFromStep = resumeFromStep
        self.carriedInput = carriedInput; self.reason = reason
    }
}

/// The typed result of a run: the final threaded text, every step's outcome, and any
/// parked/failed state the caller must act on.
public struct WorkflowRunResult: Sendable, Equatable {
    public var workflowID: UUID
    public var finalText: String
    public var steps: [StepOutcome]
    /// Set when the run parked (policy `.retryThenQueue` exhausted) — the caller enqueues it.
    public var parked: ParkedRun?
    /// Set when the run failed unrecoverably.
    public var failure: String?

    public init(workflowID: UUID, finalText: String, steps: [StepOutcome],
                parked: ParkedRun? = nil, failure: String? = nil) {
        self.workflowID = workflowID; self.finalText = finalText; self.steps = steps
        self.parked = parked; self.failure = failure
    }

    public var didComplete: Bool { parked == nil && failure == nil }
    public var didPark: Bool { parked != nil }
}

public enum WorkflowRunError: Error, Equatable {
    /// A step resolved to the `.dispatchToMac` mesh target but no dispatch handler is
    /// wired — the desktop run-a-capability RPC is HSM-15-02, not yet built.
    case dispatchUnimplemented
}

// MARK: - The runner

/// Walks a `Workflow` to a `WorkflowRunResult`. **Pure**: state lives on the call, not the
/// instance, so a single runner is reusable and `Sendable`.
public struct WorkflowRunner: Sendable {

    /// The provider that model-backed steps call (on-device or endpoint). Injected.
    private let provider: ILLMProvider
    /// The fallback provider used by `.fallbackOnDevice` (the on-device model). Injected;
    /// when `nil`, `.fallbackOnDevice` degrades to a failed step.
    private let fallback: ILLMProvider?
    private let policy: RunPolicy

    public init(provider: ILLMProvider, fallback: ILLMProvider? = nil, policy: RunPolicy = RunPolicy()) {
        self.provider = provider
        self.fallback = fallback
        self.policy = policy
    }

    /// Run `workflow` over `sourceText` (the resolved SOURCE text — the App supplies the
    /// transcript / tacked moments / selection; the runner stays source-agnostic).
    /// Optionally resume from `resumeFrom` with `seedInput` already threaded (so a parked
    /// run never recomputes completed steps).
    public func run(_ workflow: Workflow,
                    sourceText: String,
                    resumeFrom: Int = 0,
                    seedInput: String? = nil) async -> WorkflowRunResult {
        var threaded = seedInput ?? sourceText
        var outcomes: [StepOutcome] = []
        // The "head input" the first *executed* step reads: the cached/carried value on a
        // resume, else the workflow SOURCE. (Resume never recomputes earlier steps.)
        let headInput = seedInput ?? sourceText

        for index in workflow.steps.indices where index >= resumeFrom {
            let step = workflow.steps[index]
            // Input resolution: the head input for the first executed step (or a custom
            // node bound to `.meeting`, which always reads the SOURCE), the previous
            // output thereafter.
            let resolvedInput = resolveInput(for: step, index: index, resumeFrom: resumeFrom,
                                             threaded: threaded, sourceText: sourceText,
                                             headInput: headInput)

            // Pure transforms first — no model, no failure policy.
            if let pure = pureTransform(step, input: resolvedInput) {
                threaded = pure
                outcomes.append(StepOutcome(index: index, label: step.label, status: .ok,
                                            input: resolvedInput, output: pure, attempts: 0))
                continue
            }

            // Model-backed step: build the prompt, run it under the failure policy.
            let prompt = buildPrompt(for: step, input: resolvedInput)
            let attemptResult = await execute(prompt: prompt, target: .onDevice)

            switch attemptResult {
            case .success(let text, let attempts):
                threaded = text
                outcomes.append(StepOutcome(index: index, label: step.label, status: .ok,
                                            input: resolvedInput, output: text, attempts: attempts))

            case .failure(let lastError, let attempts):
                switch policy.failurePolicy {
                case .skip:
                    // Carry the input through unchanged.
                    outcomes.append(StepOutcome(index: index, label: step.label, status: .skipped,
                                                input: resolvedInput, output: resolvedInput,
                                                attempts: attempts, error: describe(lastError)))
                    // `threaded` stays as resolvedInput's source — keep the carried value.
                    threaded = resolvedInput

                case .fallbackOnDevice:
                    if let fb = fallback {
                        let fbResult = await attempt(prompt: prompt, on: fb)
                        switch fbResult {
                        case .success(let text, let fbAttempts):
                            threaded = text
                            outcomes.append(StepOutcome(index: index, label: step.label, status: .fellBack,
                                                        input: resolvedInput, output: text,
                                                        attempts: attempts + fbAttempts))
                        case .failure(let fbError, let fbAttempts):
                            outcomes.append(StepOutcome(index: index, label: step.label, status: .failed,
                                                        input: resolvedInput, output: resolvedInput,
                                                        attempts: attempts + fbAttempts,
                                                        error: describe(fbError)))
                            return WorkflowRunResult(workflowID: workflow.id, finalText: resolvedInput,
                                                     steps: outcomes, failure: describe(fbError))
                        }
                    } else {
                        outcomes.append(StepOutcome(index: index, label: step.label, status: .failed,
                                                    input: resolvedInput, output: resolvedInput,
                                                    attempts: attempts, error: "no fallback provider"))
                        return WorkflowRunResult(workflowID: workflow.id, finalText: resolvedInput,
                                                 steps: outcomes, failure: "no fallback provider")
                    }

                case .retryThenQueue:
                    // Park: the caller enqueues this as a blocked job and resumes from here.
                    let reason = describe(lastError)
                    outcomes.append(StepOutcome(index: index, label: step.label, status: .parked,
                                                input: resolvedInput, output: resolvedInput,
                                                attempts: attempts, error: reason))
                    let parked = ParkedRun(workflowID: workflow.id, resumeFromStep: index,
                                           carriedInput: resolvedInput, reason: reason)
                    return WorkflowRunResult(workflowID: workflow.id, finalText: resolvedInput,
                                             steps: outcomes, parked: parked)
                }
            }
        }

        return WorkflowRunResult(workflowID: workflow.id, finalText: threaded, steps: outcomes)
    }

    // MARK: Input resolution

    private func resolveInput(for step: WorkflowStep, index: Int, resumeFrom: Int,
                              threaded: String, sourceText: String, headInput: String) -> String {
        // A custom `llmCall` honours its declared input binding. `.meeting` ALWAYS reads the
        // workflow SOURCE (even on a resume); `.previousStep` reads the head input for the
        // first executed step, else the threaded value.
        if case .llmCall(_, _, let input) = step {
            switch input {
            case .meeting:      return sourceText
            case .previousStep: return (index == resumeFrom) ? headInput : threaded
            }
        }
        // Curated steps read the head input for the first executed step, else the threaded value.
        return (index == resumeFrom) ? headInput : threaded
    }

    // MARK: Pure transforms (no model)

    /// `keepIf(keyword)` keeps the lines that mention the keyword (case-insensitive). A
    /// PURE text filter — no model. Returns `nil` for model-backed steps.
    private func pureTransform(_ step: WorkflowStep, input: String) -> String? {
        guard case .keepIf(let keyword) = step else { return nil }
        let needle = keyword.lowercased()
        guard !needle.isEmpty else { return input }
        let kept = input
            .split(separator: "\n", omittingEmptySubsequences: false)
            .filter { $0.lowercased().contains(needle) }
        return kept.joined(separator: "\n")
    }

    // MARK: Prompt templates

    /// The built-in prompt for a model-backed step. The custom `llmCall` substitutes
    /// `{input}` into the user's prompt; the curated steps use shipped templates.
    private func buildPrompt(for step: WorkflowStep, input: String) -> String {
        switch step {
        case .llmCall(_, let prompt, _):
            // `{input}` substitution — the user's prompt is wired into the pipeline.
            return prompt.replacingOccurrences(of: "{input}", with: input)
        case .summarize:
            return "Summarize the following into a tight, faithful summary. "
                + "No preamble, just the summary.\n\n\(input)"
        case .rewrite(let tone):
            return "Rewrite the following text in a \(tone) tone, preserving every fact "
                + "and detail. Return only the rewritten text.\n\n\(input)"
        case .lens(let profile):
            return "Read the following through a \(profile.rawValue) lens. Surface what "
                + "matters most from that perspective.\n\n\(input)"
        case .extract(let type):
            return "From the following, extract the \(type.rawValue.replacingOccurrences(of: "_", with: " ")). "
                + "Return only that artifact, no preamble.\n\n\(input)"
        case .keepIf:
            // Pure — never reaches here, but keep the switch total.
            return input
        }
    }

    // MARK: Provider execution + retry

    private enum AttemptResult {
        case success(text: String, attempts: Int)
        case failure(error: Error, attempts: Int)
    }

    /// Run a prompt against a target. On-device / endpoint go through the injected
    /// provider; `.dispatchToMac` is the stubbed mesh seam (HSM-15-02).
    private func execute(prompt: String, target: RunTarget) async -> AttemptResult {
        switch target {
        case .onDevice, .endpoint:
            return await attempt(prompt: prompt, on: provider)
        case .dispatchToMac:
            // Seam: the desktop run-a-capability RPC is not built yet.
            return .failure(error: WorkflowRunError.dispatchUnimplemented, attempts: 0)
        }
    }

    /// One bounded retry loop against a provider. Backoff is injectable (no sleep in tests).
    private func attempt(prompt: String, on provider: ILLMProvider) async -> AttemptResult {
        var attempts = 0
        var lastError: Error = WorkflowRunError.dispatchUnimplemented
        let totalTries = max(1, policy.maxRetries + 1)
        for tryIndex in 0..<totalTries {
            attempts += 1
            do {
                let text = try await provider.complete(prompt: prompt)
                return .success(text: text, attempts: attempts)
            } catch {
                lastError = error
                if tryIndex < totalTries - 1 {
                    await policy.backoff(tryIndex + 1)
                }
            }
        }
        return .failure(error: lastError, attempts: attempts)
    }

    private func describe(_ error: Error) -> String { String(describing: error) }
}
