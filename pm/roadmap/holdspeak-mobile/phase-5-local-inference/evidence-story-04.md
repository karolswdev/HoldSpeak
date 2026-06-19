# Evidence — HSM-5-04 — Structured / JSON output

- **Shipped:** 2026-06-18
- **Commit:** Phase-5 partial bundle on `main` (see commit message)
- **Owner:** unassigned

## Files touched

- `apple/Sources/Providers/Inference/StructuredOutput.swift` — `extractJSON`
  (pulls JSON out of fenced / prose-wrapped model text), `decode<T>` (extract +
  decode through the contract `Codable`, which enforces the schema), and
  `generate<T>` (asks an `ILLMProvider`, decodes, bounded repair-retry on failure).
- `apple/Tests/ProvidersTests/InferenceTests.swift` — the extraction/decode/retry
  tests.

## Verification artifacts

`cd apple && swift test` → **24 tests, 0 failures**. Relevant:

```
testExtractJSONFromMessyText passed        # bare, prose-wrapped, and ```json fenced
testDecodeContractFromFencedOutput passed  # fenced model text -> Artifact(.decisions)
testRepairRetrySucceedsOnSecondAttempt passed  # garbage then valid -> decodes (attempt 2)
testRepairRetryExhausts passed             # all-garbage -> throws after the budget
```

## Acceptance criteria — re-checked

- [x] The provider can be asked for output conforming to a Phase-0 shape and the
  result validates — decoding into the contract `Codable` (e.g. `Artifact`)
  enforces enums + required fields, i.e. schema conformance in the Swift world.
- [x] On a validation failure a bounded repair/retry runs; persistent failure is
  surfaced honestly (throws), not a silent empty artifact.
- [x] The retry budget is explicit (`maxAttempts`).

## Deviations from plan

- Validation is via the contract `Codable` (which mirrors the HSM-0-02 JSON
  Schemas) rather than running a JSON-Schema validator in-app — the Swift type IS
  the schema enforcement on this side.
- Constrained decoding (grammar) "where the engine supports it" is an
  engine-specific optimization deferred to the HSM-5-02 engine impl; this
  validate-and-repair path is the engine-agnostic floor.

## Follow-ups

The real model producing this output is HSM-5-01/02 (engine pick + `ILLMProvider`
impl, device/dep); HSM-5-05 runs it for a 30-minute meeting on real hardware.
