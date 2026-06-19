# Evidence — HSM-7-01 — Port the MIR routing engine

- **Shipped:** 2026-06-19 · **Branch:** `holdspeak-mobile/phase-7-mir-port`

## Files
- `apple/Sources/RuntimeCore/MeetingIntelligence/MIRRouter.swift` — `IntentScorer`
  (deterministic lexical scoring of MIR-01's five intents), `IntentScores`,
  `MIRRouter` (`route(profile:scores:) -> [ArtifactType]`).
- `apple/Sources/RuntimeCore/MeetingIntelligence/RoutedArtifactGenerator.swift` —
  scores intents → routes → drives the Phase-6 `ArtifactGenerationEngine`.

## Verification (`swift test`, RuntimeCoreTests/MIRRouterTests)
- `testIntentScorerDetectsDominantIntent` — architecture/incident text scores its intent top; empty → no scores.
- `testRouteIsDeterministic` — same (profile, scores) → identical chain (MIR-F-006).
- `testOffProfileIntentAddsItsSignatureArtifact` — an above-threshold off-profile intent appends its signature artifact (MIR-F-004 multi-intent reaches generation).
- `testHomeIntentNotDuplicated` — a profile's home intent doesn't double-add.
- Full suite **69 / 6 skipped / 0 failures**.

## Notes
Ported only the routing **decision** (profile + scores → emphasis), model-free
(lexical, not the LLM) so the gate is reproducible. Parked desktop-fidelity:
windows/hysteresis/transitions/synthesis/lineage (Decisions deferred).
