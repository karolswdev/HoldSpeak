# Phase 6 — Meeting Intelligence — final summary

**Closed:** 2026-06-19 (Gate 5 met). Track G of the Council Implementation Charter.

## Charter gate — PASSED

**Gate 5: parity with the desktop quality baseline.** The HSM-6-04 parity harness,
run over a fixed baseline meeting with real mobile generation, reports **mean
coverage 0.92 over 3 runs against a pre-fixed 0.8 threshold (3/3 runs pass)** —
mobile meeting intelligence is at parity with the desktop quality baseline on the
agreed substance. See [`evidence-story-05.md`](./evidence-story-05.md). Threshold
fixed before the run; gaps filed honestly, not hidden; bar not moved to pass.

## What shipped

| Story | Outcome |
|---|---|
| HSM-6-01 | Artifact-generation engine seam (`ArtifactGenerationEngine`): transcript + injected `ILLMProvider` → schema-valid Phase-0 `Artifact`; propose-only; prose-robust. |
| HSM-6-02 | The five core artifact types (Action Items typed to `[ActionItem]`; Decisions/Risks/Requirements open-blob; Summary → `IntelSnapshot`). |
| HSM-6-03 | ADR Candidates (`Artifact(.adr)`); never fabricated. |
| HSM-6-04 | The parity baseline harness (`ParityRubric`/`ParityScorer`/`ParityReport`) — deterministic substance-coverage scoring. |
| HSM-6-05 | **Gate-5 verdict: PASS (0.92 ≥ 0.8).** |

`swift test` green throughout (38/38 at HSM-6-04; the Gate-5 verdict is an opt-in
live test against a real endpoint).

## Deferred / carried forward

- **HSM-6-06 (Follow-ups)** stays **blocked** on a cross-runtime `follow_up`
  artifact-type contract decision (needs desktop + schema + both runtimes +
  fixtures). It is not required for Gate 5 and is the owner's call.
- **On-device / fully-local execution proof.** The Gate-5 verdict is artifact-quality
  parity, measured on the mobile stack against a real Mode-B/C endpoint. Executing
  the same stack on the iPad is carried by **HSM-5-06** (built + signed + installed
  on the iPad Air M4; on-device launch pending the device unlock) and **HSM-5-02**
  (fully-local Mode A, the on-device GGUF). These are execution-location proofs, not
  re-measurements of quality.

## Decisions of record

- Parity is judged on substance (presence/type/coverage), never exact strings —
  generation is non-deterministic; scoring is not (HSM-6-04).
- The parity rubric + 0.8 threshold + verdict were owner-delegated to the agent
  ("for gate five, I trust your call", 2026-06-19) and fixed before measuring.
