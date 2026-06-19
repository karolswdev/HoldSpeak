import Foundation
import Contracts

/// HSM-7-01/02 — the MIR routing decision, ported into the Runtime Core (Layer 2).
///
/// Desktop MIR-01 is a full web-runtime feature (rolling windows, hysteresis, a
/// plugin host, synthesis, DB lineage). The mobile port keeps only the **routing
/// decision** the Track-H gate needs: from `(active profile, per-window intent
/// scores)` choose an ordered set of artifact types to emphasize, and feed that to
/// the Phase-6 `ArtifactGenerationEngine`. It is **deterministic** (MIR-F-006: same
/// input + profile → same chain) and model-free — intent scoring is the desktop
/// lexical signal, not the LLM — so the gate is reproducible.
///
/// Intent vocabulary is MIR-01's verbatim five (MIR-F-003): architecture, delivery,
/// product, incident, comms. Parked (desktop-fidelity follow-ups): windowing,
/// hysteresis, transition events, synthesis, lineage persistence, per-window
/// profile override (v1 is one profile per meeting).

/// Per-window (here: whole-transcript) multi-label intent scores, normalized 0…1.
public struct IntentScores: Sendable, Equatable {
    public var scores: [MIRIntent: Double]
    public init(_ scores: [MIRIntent: Double]) { self.scores = scores }

    public func score(_ intent: MIRIntent) -> Double { scores[intent] ?? 0 }

    /// Intents at/above `threshold`, strongest first; ties broken by raw value so
    /// the order is deterministic.
    public func above(_ threshold: Double) -> [MIRIntent] {
        MIRIntent.allCases
            .filter { score($0) >= threshold && score($0) > 0 }
            .sorted { a, b in
                let (sa, sb) = (score(a), score(b))
                return sa == sb ? a.rawValue < b.rawValue : sa > sb
            }
    }
}

/// Deterministic lexical intent scoring (the desktop signal extractor's shape):
/// count per-intent keyword hits in the transcript, normalize by total hits.
public enum IntentScorer {
    static let lexicons: [MIRIntent: [String]] = [
        .architecture: ["architecture", "design", "api", "schema", "interface", "coupling",
                        "scalability", "tradeoff", "adr", "pattern", "service", "module",
                        "dependency", "abstraction", "contract"],
        .delivery: ["deadline", "milestone", "sprint", "ship", "release", "timeline",
                    "estimate", "blocker", "deliver", "schedule", "due", "velocity",
                    "backlog", "scope creep"],
        .product: ["user", "users", "customer", "feature", "requirement", "roadmap",
                   "persona", "market", "priority", "feedback", "adoption", "value",
                   "experience", "usability"],
        .incident: ["incident", "outage", "postmortem", "root cause", "severity",
                    "rollback", "alert", "downtime", "mitigation", "runbook", "on-call",
                    "failure", "regression", "sev"],
        .comms: ["announce", "stakeholder", "update", "communicate", "notify", "summary",
                 "email", "newsletter", "broadcast", "memo", "report"],
    ]

    public static func score(_ transcript: Transcript) -> IntentScores {
        score(text: transcript.segments.map(\.text).joined(separator: " "))
    }

    public static func score(text: String) -> IntentScores {
        let hay = text.lowercased()
        var hits: [MIRIntent: Int] = [:]
        var total = 0
        for (intent, words) in lexicons {
            var n = 0
            for w in words { n += occurrences(of: w, in: hay) }
            hits[intent] = n
            total += n
        }
        guard total > 0 else { return IntentScores([:]) }
        var scores: [MIRIntent: Double] = [:]
        for (intent, n) in hits where n > 0 { scores[intent] = Double(n) / Double(total) }
        return IntentScores(scores)
    }

    /// Count non-overlapping occurrences of `needle` in `hay` (both lowercased).
    static func occurrences(of needle: String, in hay: String) -> Int {
        guard !needle.isEmpty else { return 0 }
        var count = 0
        var range = hay.startIndex..<hay.endIndex
        while let found = hay.range(of: needle, range: range) {
            count += 1
            range = found.upperBound..<hay.endIndex
        }
        return count
    }
}

/// Routes `(profile, intent scores)` → an ordered, de-duplicated set of artifact
/// types for the Phase-6 engine to generate. The profile sets the base emphasis;
/// off-profile intents that score above threshold add their signature artifact
/// (so a "balanced" meeting that's really an incident still surfaces an incident
/// timeline). Pure + deterministic.
public struct MIRRouter: Sendable {
    public let threshold: Double
    public init(threshold: Double = 0.15) { self.threshold = threshold }

    /// Each profile's base emphasis — distinct from Balanced's (HSM-7-02 gate).
    public static let baseEmphasis: [MIRProfile: [ArtifactType]] = [
        .balanced:  [.decisions, .actionItems, .riskRegister, .requirements],
        .architect: [.adr, .decisions, .dependencyMap, .requirements],
        .delivery:  [.milestonePlan, .actionItems, .riskRegister, .decisions],
        .product:   [.requirements, .customerSignals, .scopeReview, .decisions],
        .incident:  [.incidentTimeline, .runbookDelta, .riskRegister, .actionItems],
    ]

    /// The profile's "home" intent (its base already covers it, so we don't re-add it).
    static let homeIntent: [MIRProfile: MIRIntent] = [
        .architect: .architecture, .delivery: .delivery,
        .product: .product, .incident: .incident,
    ]

    /// The signature artifact an above-threshold off-profile intent contributes.
    static let intentSignature: [MIRIntent: ArtifactType] = [
        .architecture: .adr, .delivery: .milestonePlan, .product: .customerSignals,
        .incident: .incidentTimeline, .comms: .stakeholderUpdate,
    ]

    public func emphasis(for profile: MIRProfile) -> [ArtifactType] {
        Self.baseEmphasis[profile] ?? Self.baseEmphasis[.balanced]!
    }

    /// The routed artifact chain for this profile + scores.
    public func route(profile: MIRProfile, scores: IntentScores) -> [ArtifactType] {
        var chain = emphasis(for: profile)
        let home = Self.homeIntent[profile]
        for intent in scores.above(threshold) where intent != home {
            if let sig = Self.intentSignature[intent], !chain.contains(sig) {
                chain.append(sig)
            }
        }
        return chain
    }
}
