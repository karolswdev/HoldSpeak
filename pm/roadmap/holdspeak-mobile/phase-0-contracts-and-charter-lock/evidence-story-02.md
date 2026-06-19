# Evidence — HSM-0-02 — JSON Schemas

- **Shipped:** 2026-06-18
- **Commit:** initial Phase-0 contracts bundle on `main` (see commit message)
- **Owner:** unassigned

## Files touched

- `contracts/schemas/segment.schema.json`, `action-item.schema.json`,
  `bookmark.schema.json`, `intel-snapshot.schema.json`, `artifact.schema.json`,
  `intel-job.schema.json`, `meeting.schema.json` — seven draft-2020-12 schemas
  with cross-file `$ref`s (meeting → segment/bookmark/intel-snapshot →
  action-item).
- `contracts/validate.py` — a `referencing`-registry validator: validates each
  fixture entity against its schema, enforces UTC-`Z` instants, and runs a
  negative check.

## Verification artifacts

`uv run --with jsonschema python pm/roadmap/holdspeak-mobile/contracts/validate.py`:

```
PASS  meeting: validates against its schema (0 errors)
PASS  artifact: validates against its schema (0 errors)
PASS  intel_job: validates against its schema (0 errors)
PASS  utc-z: all instants are UTC Z-terminated
PASS  negative: corrupted artifact rejected (2 error(s), as expected)
RESULT: ALL CHECKS PASSED
```

(Type-check is not validation; this is the validator actually executing against
the real-serialization fixture.)

## Acceptance criteria — re-checked

- [x] A schema exists for every core catalogued entity — seven schemas.
- [x] Each validates a real desktop payload with zero errors — meeting/artifact/
  intel_job pass; meeting transitively validates segment/bookmark/intel-snapshot/
  action-item via `$ref`.
- [x] Enum fields constrained; unknown values fail — proven by the negative case
  (bad `status` + missing `title` → 2 errors).
- [x] Optional vs. required explicit and matches desktop behavior — present-null
  vs. not-required-absent encoded per the serialization contract §4.
- [x] Cross-entity references resolve — the full nested Meeting validates.

## Deviations from plan

Added a UTC-`Z` enforcement check to the validator (HSM-0-05 owner decision) —
additive to the story's scope, recorded here.

## Follow-ups

HSM-0-04 broadens fixtures (parked entities, multiple MIR profiles) and adds a
parse→re-serialize round-trip assertion.
