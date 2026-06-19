# Evidence — HSM-6-02 — The five core artifact types

- **Shipped:** 2026-06-19
- **Commit:** Phase-6 HSM-6-02 on `main` (see commit message)
- **Owner:** unassigned

## What shipped

The five core types meetings must yield, each mapped to the contract that can
actually hold it:

| Logical type | Contract home | Validation |
|---|---|---|
| Action Items | `Artifact(.actionItems)`, `structured_json` = `[ActionItem]` | decodes to the typed `ActionItem` contract |
| Decisions | `Artifact(.decisions)` (open `structured_json`) | `Artifact` envelope round-trips |
| Risks | `Artifact(.riskRegister)` (open) | `Artifact` envelope round-trips |
| Requirements | `Artifact(.requirements)` (open) | `Artifact` envelope round-trips |
| Summary | `IntelSnapshot` (summary + topics) | `IntelSnapshot` contract round-trips |

**Contract-honest mapping (decision):** Phase 0 gives only `ActionItem` a typed
contract + schema; Decisions/Risks/Requirements are tagged-union `Artifact`s with
open `structured_json` (Phase-0 design), and there is **no `summary` artifact
type** — a summary's contract home is `IntelSnapshot` (its own schema). We did not
invent a `summary` artifact type or per-type schemas the contract lacks (phase
risk: a shape the contract can't hold is a contract question, not a local hack).

## Files touched

- `apple/Sources/RuntimeCore/MeetingIntelligence/CoreArtifacts.swift` —
  `CoreArtifactGenerator` (the typed ActionItems path + `IntelSnapshot` summary;
  Decisions/Risks/Requirements run through the HSM-6-01 engine with per-type
  prompts) + `CoreArtifactPrompts` (desktop-intent prompts, every one mandating
  "[] / empty when none").
- `apple/Sources/Contracts/Models.swift` — public inits for `ActionItem` and
  `IntelSnapshot` (construct-only before).
- `apple/Sources/Providers/Inference/StructuredOutput.swift` — **bug fix surfaced
  by this story:** `extractJSON` grabbed the first inner object of an array
  (`[{…}]` → `{…}`), so a `[ActionItem]` response failed to decode. It now extracts
  whichever structure (`{` or `[`) opens first. Safe for the existing object cases
  (Phase-5 `InferenceTests` still green).
- `apple/Tests/RuntimeCoreTests/CoreArtifactsTests.swift` — the per-type tests.

## Verification

`cd apple && swift test` — **33/33 green** (28 prior + 5 new), layer guard green.

```
CoreArtifactsTests
  testActionItemsAreTypedAndStamped  passed   (structured_json decodes to [ActionItem];
                                                id = sha256(task:owner)[:12]; lifecycle stamped)
  testNoInstancesYieldsEmptySet      passed   (empty input → [], not hallucinated)
  testOpenBlobCoreTypesValidate      passed   (decisions/risks/requirements envelopes round-trip)
  testSummaryIsIntelSnapshot         passed   (Summary → schema-valid IntelSnapshot)
  testCoreArtifactTypeSet            passed
Executed 33 tests, with 0 failures
```

## Notes

- **Substance, not wording.** Tests assert the task/topics actually present are
  captured (and the engine-stamped lifecycle/provenance), never the model's exact
  phrasing — per the story note and repo convention for non-deterministic intel.
- **Action items are the only typed core type**; the engine builds each
  `ActionItem` from a model draft (task/owner/due/source_timestamp) and stamps the
  lifecycle the model can't author (id, `status=pending`, `review_state=pending`,
  `created_at`), matching the desktop's content-addressed id.
- Real-model substance/parity is HSM-6-04's job; this story proves shape +
  presence on the seam.
