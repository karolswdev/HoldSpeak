import Foundation

// HSM-25-01 — the Apple twin of `holdspeak mesh serve` (desktop HS-85-03):
// claim on a jittered ~3s cadence (every poll stamps this node's liveness
// hub-side — polling IS liveness), execute each llm job on THIS device's OWN
// provider, post the outcome verbatim. Hub outages back off exponentially
// without dying; cancellation lets the in-flight job finish. Serving is
// consent: the caller starts the loop, and stopping it reads offline hub-side
// within the liveness window — nothing to clean up.

/// The recursion guard's named refusal (the desktop walk's design find,
/// mirrored): a device whose active profile runs elsewhere must not serve —
/// "executing" would relay onward instead of running anything. The app-side
/// provider factory throws this; the worker fails the job with it, verbatim.
public struct MeshServeRefusal: Error, Equatable, CustomStringConvertible, Sendable {
    public let reason: String
    public init(_ reason: String) { self.reason = reason }
    public var description: String { reason }
}

public actor MeshServeWorker {
    /// The serving surface's honest state line: how many runs this session,
    /// and the last outcome (25-02 renders it — no prose beyond this).
    public struct Stats: Equatable, Sendable {
        public var jobsServed = 0
        public var lastOutcome = ""
        public init() {}
    }

    private let node: String
    private let client: HTTPDesktopClient
    private let makeProvider: @Sendable () async throws -> any ILLMProvider
    private let pollInterval: Double
    private let sleep: @Sendable (Double) async -> Void
    private let log: @Sendable (String) -> Void

    // THIS device's own resolution — built lazily on the first job, reused.
    private var provider: (any ILLMProvider)?
    public private(set) var stats = Stats()

    public init(
        node: String,
        client: HTTPDesktopClient,
        makeProvider: @escaping @Sendable () async throws -> any ILLMProvider,
        pollInterval: Double = 3.0,
        sleep: @escaping @Sendable (Double) async -> Void = {
            try? await Task.sleep(nanoseconds: UInt64($0 * 1_000_000_000))
        },
        log: @escaping @Sendable (String) -> Void = { print($0) }
    ) {
        self.node = node
        self.client = client
        self.makeProvider = makeProvider
        self.pollInterval = pollInterval
        self.sleep = sleep
        self.log = log
    }

    /// The serve loop; runs until the surrounding Task is cancelled. An
    /// in-flight job always finishes — cancellation is honored between polls,
    /// so a claimed run is never abandoned by this side.
    public func run() async {
        var backoff = 1.0
        while !Task.isCancelled {
            do {
                if let job = try await client.claimMeshRelay(node: node) {
                    backoff = 1.0
                    await handle(job)
                    continue // more work may be queued — claim again right away
                }
                backoff = 1.0
                await sleep(pollInterval * Double.random(in: 0.8...1.2))
            } catch {
                // Silence and outage are different answers: an unreachable hub
                // backs off (1s → 30s cap, reset on success) without dying.
                log("mesh serve: hub unreachable: \(error)")
                await sleep(backoff)
                backoff = min(30, backoff * 2)
            }
        }
        log("node \(node) stopped serving the mesh")
    }

    private func handle(_ job: MeshRelayJob) async {
        log("job \(job.id) CLAIMED for node \(node)")
        let started = Date()
        do {
            let kind = job.taskKind ?? "llm"
            guard kind == "llm" else {
                throw MeshServeRefusal("unsupported task kind '\(kind)'")
            }
            let provider = try await engine()
            let system = job.systemPrompt ?? ""
            let user = job.userPrompt ?? ""
            // The fold: `complete(prompt:)` is the whole provider seam in v1 —
            // system + user ride as one prompt (the recorded phase limit; the
            // job's temperature/max_tokens are honored when the seam grows).
            let prompt = system.isEmpty ? user : system + "\n\n" + user
            let result = try await provider.complete(prompt: prompt)
            guard !result.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
                // the hub refuses an empty result; fail by name instead of
                // letting the job dangle to its deadline
                throw MeshServeRefusal("the provider returned an empty answer")
            }
            do {
                try await client.completeMeshRelay(jobID: job.id, result: result)
                stats.jobsServed += 1
                stats.lastOutcome = "completed \(job.id)"
                let secs = Date().timeIntervalSince(started)
                log("job \(job.id) COMPLETED on node \(node) in "
                    + String(format: "%.1f", secs) + "s (\(result.count) chars)")
            } catch {
                // e.g. .http(409): the answer arrived after the deadline — the
                // hub already failed the job by name; a slow worker learns the
                // truth and never retries.
                stats.lastOutcome = "late/unreported \(job.id)"
                log("mesh serve: could not report completion for \(job.id): \(error)")
            }
        } catch {
            let text = (error as? MeshServeRefusal)?.reason ?? String(describing: error)
            stats.lastOutcome = "failed \(job.id)"
            do { try await client.failMeshRelay(jobID: job.id, error: text) }
            catch { log("mesh serve: could not report failure for \(job.id): \(error)") }
            log("job \(job.id) FAILED on node \(node): \(text)")
        }
    }

    private func engine() async throws -> any ILLMProvider {
        if let provider { return provider }
        let built = try await makeProvider()
        provider = built
        return built
    }
}
