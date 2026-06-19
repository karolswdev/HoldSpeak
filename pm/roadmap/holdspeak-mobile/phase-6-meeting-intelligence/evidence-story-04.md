# Evidence — HSM-6-04 — The parity baseline harness

- **Shipped:** 2026-06-19
- **Commit:** Phase-6 HSM-6-04 on `main` (see commit message)
- **Owner:** unassigned

## What shipped

A deterministic, phrasing-tolerant **substance-coverage** scorer that operationally
defines "parity with the desktop quality baseline" (the Track-G gate) — so the gate
is measurable, not a vibe.

- `ParityCategory` — `.artifact(ArtifactType)` or `.summary` (the summary lives in
  `IntelSnapshot`, kept honest with HSM-6-02).
- `ParityRubric` — per-category `mustCover` key facts + a pass `threshold`.
- `ParityScorer.score(artifacts:summary:rubric:)` — a **pure function**: for each
  fact, every significant token (lowercased, ≥3 chars) must appear in that
  category's mobile text (artifact title+body+flattened `structured_json`, or the
  snapshot summary+topics). Tolerant of phrasing/markdown/case/order.
- `ParityReport` — per-category `covered`/`total`/`missing` + overall coverage
  (fact-weighted) + `passed` vs threshold.

**Owner-agreed parity definition (default):** baseline-meeting set = the **Phase-67
dogfood transcripts**; threshold = **0.8 overall coverage, reported per-type**.

## Files touched

- `apple/Sources/RuntimeCore/MeetingIntelligence/ParityHarness.swift`
- `apple/Tests/RuntimeCoreTests/ParityHarnessTests.swift`

## Verification

`cd apple && swift test` — **38/38 green** (35 prior + 3 new), layer guard green.

```
ParityHarnessTests
  testPerCategoryCoverageIsPhrasingTolerant  passed  (markdown/order-tolerant match; per-category covered/missing)
  testScorerIsDeterministic                  passed  (run twice → identical report; the gate isn't a vibe)
  testThresholdFailsAndAttributes            passed  (verdict + the gap attributed to its category)
Executed 38 tests, with 0 failures
```

## Scope boundary — what HSM-6-05 still owns (and its gate)

This story delivers the **harness + the parity definition**. The **live verdict**
— capture the desktop baseline artifacts on the dogfood set, run *mobile* generation
over the same inputs, score, record pass/fail — is **HSM-6-05**, and it is **gated**:

- The mobile side needs a real `ILLMProvider` to generate artifacts to score — that
  is the **device/dep-gated inference engine (Phase 5, HSM-5-01/02)**. There is no
  on-device model yet, so a true mobile-vs-desktop parity verdict cannot run.
- The desktop baseline capture needs the desktop intel pipeline (a real model;
  the `.43` homelab LLM per repo convention).

So Phase 6's **intelligence is complete and host-proven**; the **quality gate
verdict awaits the on-device engine**. Recorded honestly rather than fake-closed.
