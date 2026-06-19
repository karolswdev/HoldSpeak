# Evidence — HSM-0-04 — Conformance fixtures

- **Shipped:** 2026-06-18
- **Commit:** Phase-0 close bundle on `main` (see commit message)
- **Owner:** unassigned

## Files touched

- `contracts/fixtures/meeting-sample.json` — golden Meeting + Artifact + IntelJob
  (HSM-0-01/02), UTC-`Z` normalized.
- `contracts/fixtures/mir-and-actuator-sample.json` — golden ActuatorProposal +
  two IntentWindows (balanced + architect), from real `holdspeak/db/models.py`
  dataclasses via `asdict`.
- `contracts/schemas/actuator-proposal.schema.json`,
  `contracts/schemas/intent-window.schema.json` — schemas for the two
  contract-relevant "beyond-charter" keep entities (now 9 schemas total).
- `contracts/validate.py` — extended: validates the new entities, a canonical
  round-trip/stability check over both fixture files, a MIR-profile-distinctness
  assertion, and the UTC-`Z` sweep now covers both fixtures.

## Verification artifacts

`uv run --with jsonschema python pm/roadmap/holdspeak-mobile/contracts/validate.py`:

```
PASS  meeting / artifact / intel_job: validate (0 errors)
PASS  actuator_proposal: validates against its schema (0 errors)
PASS  intent_window[balanced]: validates against its schema (0 errors)
PASS  intent_window[architect]: validates against its schema (0 errors)
PASS  utc-z: all instants are UTC Z-terminated
PASS  round-trip: fixtures are canonical / stable
PASS  mir-profile: distinct profiles carried (balanced vs architect)
PASS  negative: corrupted artifact rejected (2 error(s), as expected)
RESULT: ALL CHECKS PASSED
```

## Acceptance criteria — re-checked

- [x] Golden fixture per canonical entity + a full nested Meeting; the MIR-profile
  dimension is exercised by the balanced/architect intent windows.
- [x] Every fixture validates against the schema set — validator green.
- [x] Fixtures derived from real desktop dataclasses (`to_dict`/`asdict`), not
  hand-invented.
- [x] The validator is one documented command both runtimes can run.
- [x] Round-trip stability asserted (canonical JSON; the typed Swift-Codable
  round-trip is Phase 1's job, noted in the validator).

## Deviations from plan

Dictation-journal fixture/schema deferred (the "keep-lightweight" entity) — filed
as a follow-up; the two highest-value beyond-charter entities (actuator proposal,
intent window) are covered.

## Follow-ups

Phase 1 adds the typed Swift `Codable` round-trip over these same fixtures
(HSM-1-02). Per-`artifact_type` `structured_json` sub-schemas remain open/additive.
