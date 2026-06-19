import Foundation
import Contracts
import Providers

/// HSM-7-01/03 — profile-driven artifact generation: the MIR routing decision in
/// front of the Phase-6 engine. Score the transcript's intents, route to an
/// artifact chain for the active profile, then generate. This is what makes Phase-6
/// generation profile-driven instead of one-size-fits-all.
public struct RoutedArtifactGenerator: Sendable {
    let engine: ArtifactGenerationEngine
    let router: MIRRouter

    public init(engine: ArtifactGenerationEngine, router: MIRRouter = MIRRouter()) {
        self.engine = engine
        self.router = router
    }

    public struct RoutedRun: Sendable {
        /// The routed artifact chain (the routing decision — deterministic).
        public let routedTypes: [ArtifactType]
        public let scores: IntentScores
        public let results: [(type: ArtifactType, result: Result<Artifact, Error>)]
        /// The artifacts that generated successfully.
        public var artifacts: [Artifact] { results.compactMap { try? $0.result.get() } }
    }

    /// Route + generate for an explicit profile.
    public func generate(from transcript: Transcript, profile: MIRProfile) async -> RoutedRun {
        let scores = IntentScorer.score(transcript)
        let types = router.route(profile: profile, scores: scores)
        let results = await engine.generate(types: types, from: transcript)
        return RoutedRun(routedTypes: types, scores: scores, results: results)
    }

    /// Route + generate using the meeting's carried profile (the HSM-7-03 seam).
    public func generate(from transcript: Transcript, for meeting: Meeting) async -> RoutedRun {
        await generate(from: transcript, profile: meeting.routingProfile)
    }
}

public extension Meeting {
    /// HSM-7-03 — the profile-selection seam: the routing profile rides on the
    /// `Meeting` per the Phase-0 contract (`mir_profile`). A host UI reads/writes
    /// `mirProfile`; the engine reads this, defaulting to `.balanced` when unset.
    var routingProfile: MIRProfile { mirProfile ?? .balanced }
}
