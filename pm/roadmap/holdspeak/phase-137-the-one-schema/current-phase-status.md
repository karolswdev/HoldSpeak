# Phase 137 — The One Schema

**Status:** in progress (3/4).

**Last updated:** 2026-08-17.

## Owner mandate

The incremental schema-versioning ceremony is friction with zero payoff:
HoldSpeak is single-user and unreleased, yet every phase pays a tax to a
migration chain built to upgrade strangers' old databases through every
historical version — strangers who do not exist. Owner ruling
(2026-08-17): **"conflate everything to an initial schema. I don't need
you to maintain something that's just used by me."** Kill the migration
ceremony; replace it with one declarative, self-reconciling schema.

## The trigger: the v63 fork

The owner's real DB (`~/.local/share/holdspeak/holdspeak.db`) is schema
v63 with 133 tables; `main` is v61 with 127. The owner had run the
`agent/automation-reaction-engine` branch (PR #461) locally, which added
7 tables (`connector_reactions`, `connector_watches`,
`reaction_event_projections`, `service_events`, `resourceful_dispatches`,
`resourceful_policies`, `mesh_offer_reservations`) the merged product
lacks; meanwhile `main` shipped `scheduled_recordings`, which the real DB
lacks. The two forked — the classic parallel-branch incremental-version
collision — and the version gate now refuses to open the owner's own DB
on `main` (v61 < v63 → `SchemaVersionError`). The collapse fixes this:
after it, the real DB opens on `main` again.

## Target end state

One declarative schema (`holdspeak/db/schema.py:SCHEMA_SQL`, already the
full `CREATE TABLE IF NOT EXISTS` shape). On DB open, `reconcile_schema`
brings any DB to that shape idempotently: apply `SCHEMA_SQL` (creates
missing tables/indexes/triggers), then introspect each table and
`ALTER TABLE ADD COLUMN` any missing column, then run the idempotent
seeds/backfills. No version integer gating anything, no
`SchemaVersionError`, no `migrations.py` chain, no per-change version
bump, no version-pin tests, no version-coupled snapshot. Edit the schema;
it self-applies on open.

## Invariants (each carries a test)

- **A1 — additive only.** The reconcile CREATEs missing tables and
  ALTERs-in missing columns. It NEVER drops a table, drops a column, or
  deletes a row. Orphan tables (the 7 experimental ones) survive
  untouched.
- **A2 — idempotent.** Running the reconcile on an already-current DB is
  a no-op (no errors, no spurious ALTERs).
- **A3 — self-heals shape.** A DB missing a table gains it on open; a DB
  missing a column gains it on open.
- **A4 — ALTER-safe defaults.** A column whose CREATE default is a
  function (`datetime('now')`) is added via ALTER with a constant
  default (existing rows have no value anyway); new INSERTs still get the
  function default from the table definition.
- **A5 — no version gate.** Opening a DB never fails on a version
  mismatch; a "newer" DB (like the owner's v63) opens without ceremony.
- **A6 — real data preserved.** The owner's real v63 DB, opened under the
  reconcile (on a COPY, for proof), keeps all 133 tables and all rows,
  and gains `scheduled_recordings`.

**Accepted caveat:** SQLite cannot widen a CHECK constraint on an
existing table without a rebuild; the reconcile does not attempt it. The
live DB already carries the final CHECK values (it passed those
migrations historically); only a very old backup would differ — accepted
per the single-user, unreleased posture.

## Canon

`docs/internal/CONSTITUTION.md` — the kernel is a ledger/flight recorder,
policy stays trivial-yes (the ledger-not-gate ruling). This phase is
pure friction removal; it changes no user-facing behavior beyond the hub
opening the owner's own database again.

## Story status

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-137-01 | The declarative reconcile + open path | done | [story-01](./story-01-reconcile-engine.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-137-02 | Delete the ceremony | done | [story-02](./story-02-delete-ceremony.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-137-03 | The test reckoning | done | [story-03](./story-03-test-reckoning.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-137-04 | Prove on the real DB, docs, close | backlog | [story-04](./story-04-prove-docs-close.md) | — |

## Stories

1. **HS-137-01 — The declarative reconcile + open path.** Write
   `reconcile_schema(conn)`; replace `_ensure_schema`'s version-gated
   flow (`core.py:162-185`) with an unconditional reconcile; delete
   `SchemaVersionError`; carry `_apply_seeds_and_backfills` in. A1–A5
   with tests.
2. **HS-137-02 — Delete the ceremony.** Remove `holdspeak/db/migrations.py`
   (1061 lines); clean `db/__init__.py` exports; rewrite the doctor's DB
   check and `restore_database`'s probe to not depend on the version
   integer.
3. **HS-137-03 — The test reckoning.** Delete the ~15 migration-chain
   tests; rewrite `test_db_schema_policy.py` and
   `test_doctor_config_honesty.py`; keep the canonical-snapshot shape
   test; add reconcile tests (missing-column, missing-table, idempotent,
   orphan-safe). Leave the unrelated `*_SCHEMA_VERSION` payload/protocol
   tests alone.
4. **HS-137-04 — Prove on the real DB, docs, close.** Open a COPY of the
   owner's real v63 DB under the reconcile and assert A6 (133 tables + all
   rows survive, `scheduled_recordings` gained); update ARCHITECTURE
   (the reconcile replaces migrations); the counsel; the final summary.

## Out of scope

- Merging PR #461 (automations) or #459 (people-ledger) — separate
  triage. The 7 experimental tables stay orphans until #461 lands
  properly.
- Any change to table shapes or product behavior — this is friction
  removal only.

## Where we are

The collapse is done and green (HS-137-01/02/03, bundled). The migration
ceremony is gone: `reconcile_schema` (`holdspeak/db/reconcile.py`) brings
any DB to the canonical shape on open — apply `SCHEMA_SQL`, ALTER-in
missing columns (ISO sentinel for datetime defaults), and run the data
backfills ONLY when the shape actually changed (a clean open is a true
no-op). `migrations.py` (1061 lines) is deleted; `SchemaVersionError` and
the version gate are gone; the doctor and `restore_database` no longer
read a version integer; ~19 migration-chain tests removed and the policy/
doctor tests rewritten to assert shape.

An adversarial pass on the engine caught a real blocker before it shipped
— the migration-time backfills were running on every open, which would
have resurrected every soft-deleted decision on each launch; fixed at the
root (backfills gated on shape change) and belt-and-suspenders in
`decisions.py` (soft-deleted rows are never touched), with a regression
test. A conditional pre-change backup restores the old safety net without
backing up fresh creations.

Full suite green: 5917 passed, 0 real failures (three concurrency
failures confirmed pre-existing flakes, 2/2 serial → Candidate Z).
HS-137-04 (prove on a copy of the real v63 DB, docs, counsel, close) is
next.
