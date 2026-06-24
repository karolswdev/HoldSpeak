import Foundation
import Contracts
import Providers

/// HSM-14-18 — the live-intel runner: the iPad's intelligence runs **during** the meeting, not
/// only at review. The desktop already does this (`meeting_session/intel_analysis.py` fires a
/// streaming intel pass repeatedly over the partial transcript); this is its on-device peer.
///
/// Composition, not new machinery: [`LiveIntelCadence`] decides *when* a pass fires (tack now /
/// cadence when sparse-floors are met), `MIRRouter` decides *what* to extract for the active
/// profile, and the Phase-6 `ArtifactGenerationEngine` does the extraction. The runner threads
/// them over a **bounded context window** so a live pass on one chip never fights Whisper +
/// diarization (the story's resource reality — don't firehose).
///
/// Pure RuntimeCore: no SwiftUI, no `RunQueueStore`, no device types. The provider is **injected
/// as a factory**, not a single instance — production opens a FRESH provider per inference (a
/// reused llama context accumulates KV and starves/crashes the 2nd+ call; the post-meeting
/// `generate()` loop already learned this the hard way). Host tests pass a counting fake factory
/// and never load a model.
///
/// An `actor`: a live pass takes seconds, and cadence/tack can fire again mid-pass — the actor
/// serializes state and an `inFlight` guard drops overlapping ticks rather than stacking model
/// work. Propose-only: every artifact is a `.draft`, exactly as at review.
public actor LiveIntelRunner {

    /// Tunables, all surfaced in the real-time-intelligence setup screen (the next slice).
    public struct Config: Sendable, Equatable {
        /// The when-to-fire brain. Tack + cadence toggle/tune independently.
        public var cadence: LiveIntelCadence
        /// The lens a live pass routes through (the meeting's MIR profile).
        public var profile: MIRProfile
        /// Analyze only the trailing `windowSeconds` of transcript, so per-pass cost stays bounded
        /// no matter how long the meeting runs. `<= 0` ⇒ the whole partial transcript (desktop-style).
        public var windowSeconds: Double
        /// Cap the artifact types a single live pass extracts (cheap + responsive). `<= 0` ⇒ no cap
        /// (the full routed chain, as at review). A live cadence wants a tight few; review wants all.
        public var maxTypesPerPass: Int

        public init(cadence: LiveIntelCadence = LiveIntelCadence(),
                    profile: MIRProfile = .balanced,
                    windowSeconds: Double = 90,
                    maxTypesPerPass: Int = 2) {
            self.cadence = cadence
            self.profile = profile
            self.windowSeconds = windowSeconds
            self.maxTypesPerPass = maxTypesPerPass
        }
    }

    /// One live pass's outcome — what fired it, what it looked at, what it routed, what it produced.
    /// The UI lights the tacked-card "thinking" state from the trigger and materializes `artifacts`.
    public struct LivePass: Sendable {
        public let trigger: LiveIntelCadence.Trigger
        /// How many segments the analyzed window held (≤ the live transcript; bounded by `windowSeconds`).
        public let analyzedSegments: Int
        /// The MIR-routed types this pass asked for (the deterministic routing decision).
        public let routedTypes: [ArtifactType]
        /// The `.draft` artifacts that generated successfully this pass (a failed type is simply absent).
        public let artifacts: [Artifact]
        public let firedAt: Double
    }

    private let meetingID: String
    private var config: Config
    private let makeProvider: @Sendable () throws -> ILLMProvider
    private let router: MIRRouter
    private let maxAttempts: Int
    private let now: @Sendable () -> Double
    private let idGenerator: @Sendable () -> String

    // Running state (actor-isolated).
    private var lastRun: Double?
    private var consumedSegmentCount: Int = 0
    private var inFlight = false

    public init(meetingID: String,
                config: Config,
                makeProvider: @escaping @Sendable () throws -> ILLMProvider,
                router: MIRRouter = MIRRouter(),
                maxAttempts: Int = 2,
                now: @escaping @Sendable () -> Double = { Date().timeIntervalSince1970 },
                idGenerator: @escaping @Sendable () -> String = { UUID().uuidString }) {
        self.meetingID = meetingID
        self.config = config
        self.makeProvider = makeProvider
        self.router = router
        self.maxAttempts = maxAttempts
        self.now = now
        self.idGenerator = idGenerator
    }

    /// Live-tune the cadence/profile/window from the setup screen without losing the run's clocks.
    public func update(_ config: Config) { self.config = config }

    /// Offer the runner the current live transcript + whether a tack is pending. If the cadence says
    /// fire, it runs ONE MIR-routed pass over the bounded window and returns it; otherwise `nil`.
    /// Overlapping ticks while a pass is in flight are dropped (the live pass owns the model).
    public func tick(segments: [Segment], tackPending: Bool) async -> LivePass? {
        let newSinceLastRun = max(0, segments.count - consumedSegmentCount)
        guard !inFlight,
              let trigger = config.cadence.decide(now: now(),
                                                  lastRun: lastRun,
                                                  newSegmentsSinceLastRun: newSinceLastRun,
                                                  tackPending: tackPending)
        else { return nil }

        inFlight = true
        defer { inFlight = false }

        let window = Self.trailingWindow(segments, lastSeconds: config.windowSeconds)
        let transcript = Transcript(meetingId: meetingID,
                                    segments: window,
                                    transcriptHash: "live-\(consumedSegmentCount)-\(segments.count)")

        let scores = IntentScorer.score(transcript)
        var types = router.route(profile: config.profile, scores: scores)
        if config.maxTypesPerPass > 0 { types = Array(types.prefix(config.maxTypesPerPass)) }

        // A FRESH provider + engine per type — a clean model context every inference (see the class
        // doc). A type that throws (unreachable endpoint, bad parse) is dropped from this pass, never
        // crashing the others or the run — exactly the post-meeting engine's per-type resilience.
        var artifacts: [Artifact] = []
        for type in types {
            guard let provider = try? makeProvider() else { continue }
            let engine = ArtifactGenerationEngine(provider: provider,
                                                  maxAttempts: maxAttempts,
                                                  idGenerator: idGenerator)
            if let artifact = try? await engine.generate(type, from: transcript) {
                artifacts.append(artifact)
            }
        }

        // Advance the clocks AFTER the pass: cadence's "new segments since last run" and the
        // min-interval both reset off this moment, so the next cadence pass needs fresh transcript.
        let firedAt = now()
        lastRun = firedAt
        consumedSegmentCount = segments.count

        return LivePass(trigger: trigger,
                        analyzedSegments: window.count,
                        routedTypes: types,
                        artifacts: artifacts,
                        firedAt: firedAt)
    }

    /// The trailing-context selector: the last `lastSeconds` of transcript (by segment end time),
    /// which is the most useful real-time signal — the live cadence and a just-tacked moment both
    /// live at the growing end. `lastSeconds <= 0` ⇒ the whole transcript; an empty trailing slice
    /// (clock skew / all segments older than the cutoff) falls back to the whole transcript rather
    /// than analyzing nothing.
    static func trailingWindow(_ segments: [Segment], lastSeconds: Double) -> [Segment] {
        guard lastSeconds > 0, let last = segments.last else { return segments }
        let cutoff = last.endTime - lastSeconds
        let windowed = segments.filter { $0.endTime >= cutoff }
        return windowed.isEmpty ? segments : windowed
    }
}
