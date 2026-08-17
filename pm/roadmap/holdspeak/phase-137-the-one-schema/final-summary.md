# Phase 137 — The One Schema — Final Summary

**Status:** 4/4 done. Counsel recorded. Owner sitting pending.

## The mandate

The incremental schema-migration ceremony was friction with zero payoff.
HoldSpeak is single-user and unreleased; a 1061-line migration chain,
version-pin tests, a version-coupled snapshot, and a `SchemaVersionError`
that refused to open the owner's own database only ever earned their keep
upgrading strangers' old databases — and there are no strangers. Owner
ruling (2026-08-17): "conflate everything to an initial schema. I don't
need you to maintain something that's just used by me."

## The trigger: the v63 fork

The owner's real DB was schema v63 (133 tables); `main` was v61 (127).
The owner had run an unmerged branch (PR #461, automations) that added 7
tables the merged product lacks, while `main` shipped `scheduled_recordings`,
which the real DB lacks. The two forked — the classic parallel-branch
incremental-version collision — and the version gate refused to open the
owner's own DB on `main`. After the collapse, it opens again.

## What shipped

- **HS-137-01 — the reconcile engine** (`holdspeak/db/reconcile.py`).
  `reconcile_schema` brings any database to the canonical shape
  (`schema.py:SCHEMA_SQL`) on open: apply the `CREATE IF NOT EXISTS`
  shape, introspect each table against an in-memory reference and
  `ALTER ADD` any missing column, then run the data backfills only when
  the shape actually changed. Additive-only, idempotent, no version gate.
- **HS-137-02 — delete the ceremony.** `migrations.py` (1061 lines)
  removed; the doctor and `restore_database` no longer read a version
  integer.
- **HS-137-03 — the test reckoning.** ~19 migration-chain tests deleted;
  the schema-policy and doctor tests rewritten to assert shape, not
  version numbers; the canonical-snapshot shape guard kept.
- **HS-137-04 — prove, docs, close.** The real-DB proof (below), the
  ARCHITECTURE update, the counsel, this summary.

## Verification

- **The real-v63-DB proof (A6), on a COPY** (`scripts/verify_reconcile_real_db.py`,
  `evidence-story-04.md`): the owner's actual v63 database, opened through
  the app's normal path, raised no version refusal, kept all 133 tables
  and every sampled row count, gained `scheduled_recordings` (134 tables),
  and backed itself up before the shape change. **Zero data loss.** The
  original was never touched.
- **Two adversarial passes on the engine.** The second caught a BLOCKER:
  the migration-time backfills were running on every open, which would
  have resurrected every soft-deleted decision on each launch. Fixed at
  the root (backfills gated on shape change) plus belt-and-suspenders in
  `decisions.py` (soft-deleted rows skipped; the backfill UPDATE never
  sets `deleted`), with a regression test. Also folded: FTS shadow tables
  excluded from the reference diff; an ISO sentinel default for datetime
  columns in ALTER; a conditional pre-change backup (never on fresh
  creation); an atomic mutating phase.
- **Full suite green: 5917 passed, 0 real failures** (three concurrency
  failures confirmed pre-existing flakes, 2/2 serial → Candidate Z).

## Accepted caveats (owner may overrule at the sitting)

- **CHECK constraints** are not widened on existing tables (SQLite cannot
  without a rebuild); the live DB already carries the final values, so
  only a very old backup would differ.
- **Pre-v8 renames** (e.g. `agents`→`recipes`) are not replayed; a
  database from before those renames would orphan — not lose — the
  old-named tables. Accepted for a single-user, unreleased product.
- **The 7 experimental tables** from PR #461 stay as harmless orphans in
  the owner's DB until #461 is merged properly. Triaging the two stale
  zombie PRs (#461, #459) is separate follow-up work.

## Counsel

Verdict: **RATIFY-WITH-CONCERNS** (fresh Opus counsel). It confirmed the
collapse is complete (no production straggler still depends on
`migrations.py` / `SchemaVersionError` / the version integer), the blocker
is dead (soft-deleted rows are never touched; backfills gated on shape
change), the accepted caveats are correctly scoped for the owner's v63
DB, and — explicitly — the real-DB proof is **sufficient given the
structural additive-only guarantee** (the all-133-tables loss assertion
covers what the mostly-empty sampled tables do not). The docs accurately
describe the new reconcile. Five findings, none a merge blocker:

1. **(should-fix) Stale guidance comment** at `schema.py:7-9` ("bump this…
   four-way upgrade contract") — misleading after the collapse. **FIXED**
   in the close commit (the comment now says the stamp is informational
   and the reconcile is shape-based); the sibling SQL comment at
   `schema.py:17` fixed too.
2. **(note) `read_schema_version` is dead code** (zero callers) — LEDGERED
   for a future cleanup; harmless.
3. **(note) ARCHITECTURE.md iPad cross-reference** to "the four-way matrix
   described below" was stale. **FIXED** in the close commit.
4. **(note) The real-DB proof exercises mostly-empty tables** — tolerable
   by construction (additive-only + the all-tables loss assertion); a
   populated fixture would strengthen it. LEDGERED for the sitting.
5. **(note) SQL comment "Schema version for migrations"** cosmetic. FIXED
   with (1).

## The close

Pushed, PR'd, and merged on green CI per the house watch → read → merge
practice; the counsel's verdict is recorded above for the owner's
sitting. After this, the versioning tax is gone: edit the schema, and it
self-applies on open.
