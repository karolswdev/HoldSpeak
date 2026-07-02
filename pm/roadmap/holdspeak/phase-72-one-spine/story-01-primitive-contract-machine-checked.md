# HS-72-01 — The primitive contract, machine-checked

- **Status:** done
- **Priority:** HIGH (the keystone — every other cross-surface guarantee stands on it)
- **Depends on:** —
- **Evidence:** [evidence-story-01.md](./evidence-story-01.md)

## Goal

Turn the Primitive Framework's prose contract into a machine-checked one. One
set of JSON Schemas + golden fixtures for every kind that syncs, validated by
all three surfaces in their own test suites, so a field added (or renamed, or
retyped) on one surface fails a test on the others instead of drifting
silently. Today the four shapes per kind (Swift `Contracts`, Swift `App/`
records, Python `db/primitives.py`, TS `primitives.ts`) are reconciled only by
`THE_PRIMITIVE_FRAMEWORK.md` saying "byte-for-byte" and a `sync.py` comment
promising lockstep.

## Scope

- **In:** draft-2020-12 JSON Schemas under
  `pm/roadmap/holdspeak-mobile/contracts/schemas/` for the 10 sync kinds
  (`note`, `kb`, `agent`, `chain`, `workflow`, `directory`,
  `directory_membership`, `profile`, plus the existing `meeting`/`artifact`
  brought under the same envelope) **and** the `ChangeSet` wire envelope
  (`Synced<>.meta`, tombstones, snake_case wire casing per
  `SERIALIZATION-CONTRACT.md`). Golden fixtures per kind under
  `contracts/fixtures/`. Validators on all three surfaces. A CI-visible drift
  guard.
- **Out:** changing any shape (this story *locks* what ships today; shape
  fixes it uncovers become follow-ups); the `graph_json` field's semantics
  (reserved — HSM 22); presence/layout classes (never canonical by contract).

## Tasks

- [ ] Author the schemas from the shipped Python serialization (the hub is the
      canonical store), cross-checked against `Contracts/Primitives.swift` and
      `web/src/lib/primitives.ts`; every intentional per-surface deviation
      gets an explicit schema comment or is fixed here if trivially wrong.
- [ ] Extend `contracts/validate.py` to cover the new schemas + fixtures.
- [ ] Python: a pytest module that round-trips real repository rows through
      the wire shape (`/api/sync/pull` + the primitives routes) and validates
      every payload against the schemas.
- [ ] Swift: a test target that decodes every golden fixture into the
      `Contracts` type, re-encodes, and byte-compares (UTC-Z dates,
      snake_case) — proving the Swift coding path matches the schema without
      needing a JSON-Schema library on-device.
- [ ] Web: a build-time check (node script in `web/`) that validates the
      fixtures against `primitives.ts` shapes (compile-time assignment or
      ajv), wired into `npm run build` or a test script CI runs.
- [ ] The drift guard: a test that `sync.py`'s `SYNC_KINDS` == the schema
      set == the Swift `SyncKind` cases (extracted by script), replacing the
      lockstep comment.
- [ ] Prove the guard both ways: introduce a deliberate drift on one surface
      in a scratch commit, watch the other surfaces' checks fail, revert.

## Proof required

The validator run green on all three surfaces (pytest output, `swift test`
output, the web check output); the deliberate-drift run red (captured output);
the schemas + fixtures committed; `SERIALIZATION-CONTRACT.md` updated to point
at the schemas as the enforcement mechanism. Full suite green.

## Done

Shipped. 8 kind schemas + the ChangeSet envelope (all `x-sync-kind`-tagged)
with the shared golden fixture; three guards consume them (pytest over a REAL
`/api/sync/pull`, the Swift fixture round-trip via `HoldSpeakContracts`,
`validate.py` incl. the key-never-syncs negative). The three-way kind-set lock
(hub `SYNC_KINDS` == schemas == Swift `SyncKind`) replaces the lockstep
comment; the web check asserts `primitives.ts` never requires a field the
contract lacks. **Four real drifts caught and fixed/locked on the first
pass:** the hub emitted full values on tombstones (fixed — the contract says
a tombstone carries no payload); Swift required an `updated_at` the hub never
emits for 7 kinds (tolerant decoders added); `Agent.manual_context`/
`use_zone_context` are lossy through hub sync (schema-documented, follow-up);
`RuntimeProfile.baseURL` could never decode off the wire (explicit coding key).
Proofs: validate.py 20/20; contract+sync pytest 21 passed; `swift test` 394
passed / 0 failures; both deliberate-drift runs red then reverted; full python
suite 3051 passed, 38 skipped. See [evidence-story-01.md](./evidence-story-01.md).
