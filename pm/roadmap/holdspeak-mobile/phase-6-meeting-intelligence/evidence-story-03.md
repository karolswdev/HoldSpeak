# Evidence — HSM-6-03 — ADR Candidates

- **Shipped:** 2026-06-19
- **Commit:** Phase-6 HSM-6-03 on `main` (see commit message)
- **Owner:** unassigned

## What shipped

ADR (Architecture Decision Record) Candidates as an open-blob `Artifact(.adr)` on
the HSM-6-01 seam: `CoreArtifactGenerator.generateADRCandidates(from:)` drives the
model with an ADR-intent prompt (a candidate ties to a decision with architectural
weight, referencing its context) and binds the result into a schema-valid
`Artifact`. Each candidate carries a `source_timestamp` to the decision moment;
the artifact carries a transcript `ArtifactSource`. Propose-only (`.draft`); no
architectural decision → empty `candidates`, never fabricated.

**Scope split:** the original story was "ADR Candidates + Follow-ups". Follow-ups
is split to **HSM-6-06 (blocked)** — `artifact_type` is a closed cross-runtime enum
with no follow-up type, so it needs a contract decision touching the desktop +
schema + both runtimes + fixtures (owner: ship ADR now, defer Follow-ups).

## Files touched

- `apple/Sources/RuntimeCore/MeetingIntelligence/CoreArtifacts.swift` —
  `generateADRCandidates(from:)` + `CoreArtifactPrompts.adrCandidates`.
- `apple/Tests/RuntimeCoreTests/ADRCandidatesTests.swift` — the two tests.
- Story docs: story-03 rescoped to ADR + done; `story-06-followups.md` created
  (HSM-6-06, blocked).

## Verification

`cd apple && swift test` — **35/35 green** (33 prior + 2 new), layer guard green.

```
ADRCandidatesTests
  testADRCandidatesValidate   passed   (Artifact(.adr) round-trips; candidate present;
                                        source_timestamp = the decision moment; transcript source)
  testADRDoesNotFabricate     passed   (no architectural decision → empty candidates)
Executed 35 tests, with 0 failures
```

## Notes

- Substance, not wording: the test asserts a candidate is present and tied to the
  transcript moment, never the model's phrasing.
- Real-model substance/parity is HSM-6-04's job; this proves shape + presence +
  no-fabrication on the seam.
