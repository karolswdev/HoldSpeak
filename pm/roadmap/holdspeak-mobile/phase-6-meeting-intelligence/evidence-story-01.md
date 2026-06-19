# Evidence — HSM-6-01 — The artifact-generation engine

- **Shipped:** 2026-06-19
- **Commit:** Phase-6 HSM-6-01 on `main` (see commit message)
- **Owner:** unassigned

## Files touched

- `apple/Sources/RuntimeCore/MeetingIntelligence/ArtifactGenerationEngine.swift` —
  the Runtime-Core (Layer 2) engine: takes a Phase-0 `Transcript` + an injected
  `ILLMProvider`, prompts the model, decodes its output via the Phase-5
  `StructuredOutput` bridge into an `ArtifactDraft`, and binds that into a full
  Phase-0 `Artifact` (stamping id / meetingId / type / plugin identity / a
  transcript `ArtifactSource`). Propose-only: every artifact is `.draft`.
- `apple/Sources/Contracts/Models.swift` — added public memberwise inits to
  `Artifact`, `ArtifactSource`, and `Transcript` (the structs were construct-only
  via decoding; the engine + tests need to build them) — the same "add inits as
  later phases need" pattern HSM-3-04 set.
- `apple/Package.swift` — `RuntimeCore` now depends on `Providers` (for the
  injected `ILLMProvider`/`StructuredOutput` ports) + a new `RuntimeCoreTests`
  target.
- `apple/Tests/RuntimeCoreTests/ArtifactGenerationEngineTests.swift` — the seam
  tests (fake `ILLMProvider`).

## Verification artifacts

`cd apple && swift test` — **28/28 green** (24 prior + 4 new), layer guard green
(`Contracts`/`RuntimeCore`/`Providers` import no SwiftUI/UIKit/WebKit):

```
Test Suite 'ArtifactGenerationEngineTests' ...
  testBatchIsResilientPerType       passed
  testEmitsSchemaValidArtifact      passed
  testMalformedOutputIsRecoverable  passed
  testNeverAutoAccepts              passed
Executed 28 tests, with 0 failures
core layers are UI-free ✓
```

## Acceptance criteria — re-checked

- [x] Runtime-Core (Layer 2), no UI dependency — layer guard green.
- [x] Injected `ILLMProvider` + Phase-0 `Transcript`; no concrete provider assumed.
- [x] Emits a schema-valid Phase-0 `Artifact` — `testEmitsSchemaValidArtifact`
  round-trips the emitted artifact through the contract coder unchanged.
- [x] Malformed model output → recoverable error, not a crash —
  `testMalformedOutputIsRecoverable`; `testBatchIsResilientPerType` proves one bad
  type does not sink the others.
- [x] No execute/connector/autonomy path — propose-only `.draft`
  (`testNeverAutoAccepts`).

## Design notes

- **The model contributes only the intelligence.** It returns an `ArtifactDraft`
  (title, body, type-specific `structured_json`, confidence); the engine owns the
  discriminator (`artifact_type`), identity, and provenance. This keeps the model's
  job small and reliable and the contract binding the engine's responsibility.
- **Generic seam, concrete types later.** A `PromptBuilder` is injected (default: a
  generic schema-hinted prompt); HSM-6-02 (five core types) and HSM-6-03 (ADR
  Candidates + Follow-ups) supply the per-type prompts/parsers on top of this seam.
- **Substance is HSM-6-04's job.** This story judges shape/validity only (per the
  story's own note); the parity baseline harness measures quality.

## Deviations / open questions

- **`RuntimeCore` → `Providers` dependency.** The injected port protocols
  (`ILLMProvider`, `StructuredOutput`) live in the `Providers` target (per the
  README/Package layer note), so RuntimeCore depends on Providers. **Risk to flag
  at Phase 3:** when `HSM-3-01` adds the WhisperKit SPM dependency to the
  `Providers` target, RuntimeCore (and its tests) would transitively link a model
  engine. **Trigger/mitigation:** at Phase 3, isolate the heavy adapter deps (e.g.
  split a dependency-free `ProviderInterfaces` target, or keep WhisperKit behind a
  sub-target) so the domain never links an inference/transcription engine. Recorded
  in the phase status "Decisions deferred".
- Integration against a real homelab/endpoint provider (story Test plan
  "Integration") is deferred to the HSM-6-04 parity harness, which runs the engine
  against a real `ILLMProvider` and judges substance.
