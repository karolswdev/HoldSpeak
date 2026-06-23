import Foundation

/// HSM-14-18 — the "when does a live intelligence pass fire, and why" brain for real-time MIR on the
/// iPad. Pure + host-tested; no model, no UI. Two INDEPENDENT triggers (both user-configurable in the
/// real-time-intelligence setup screen):
///
///   • **Tack** — the user flagged a moment ⇒ fire immediately. The most useful and cheapest real-time
///     signal: intelligence on the thing you just chose to flag.
///   • **Cadence** — periodically over the growing transcript, deliberately SPARSE so a live pass never
///     fights Whisper + diarization on one chip: it fires only when BOTH enough *new* transcript has
///     accrued (`minNewSegments`) AND enough time has passed since the last pass (`minSecondsBetweenRuns`).
public struct LiveIntelCadence: Sendable, Equatable {
    public var tackTriggerEnabled: Bool
    public var cadenceEnabled: Bool
    public var minSecondsBetweenRuns: Double
    public var minNewSegments: Int

    public init(tackTriggerEnabled: Bool = true,
                cadenceEnabled: Bool = true,
                minSecondsBetweenRuns: Double = 25,
                minNewSegments: Int = 4) {
        self.tackTriggerEnabled = tackTriggerEnabled
        self.cadenceEnabled = cadenceEnabled
        self.minSecondsBetweenRuns = minSecondsBetweenRuns
        self.minNewSegments = minNewSegments
    }

    public enum Trigger: String, Sendable, Equatable { case tack, cadence }

    /// Whether a live intel pass should fire now, and why. A pending tack wins (immediate, user-driven).
    /// Otherwise the cadence fires only when BOTH floors are met (so it stays sparse). `nil` ⇒ don't run.
    public func decide(now: Double, lastRun: Double?, newSegmentsSinceLastRun: Int, tackPending: Bool) -> Trigger? {
        if tackTriggerEnabled, tackPending { return .tack }
        guard cadenceEnabled else { return nil }
        guard newSegmentsSinceLastRun >= minNewSegments else { return nil }
        if let last = lastRun, (now - last) < minSecondsBetweenRuns { return nil }   // too soon
        return .cadence
    }
}
