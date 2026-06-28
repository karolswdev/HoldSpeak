# CAD-1-01 — Cadence models + SQLite migrations

- **Program:** cadence-engine · **Phase:** 1 · **Status:** done — **leads the phase.**
  Built + tested (`tests/integration/test_cadence_store.py`, 9 green; schema snapshot regenerated;
  77 db/doctor tests green). Off by default / inert.
- **Depends on:** nothing. **Unblocks:** every other Phase-1 story.

## Problem

There is no persistence for loops/next-actions/nudges/policies. They need first-class tables
(chart decision §3.1: source-projected entities, not views) following the repo's storage pattern.

## The design

Reuse the storage pattern verified in the seam map:

1. **Schema.** Append `CREATE TABLE IF NOT EXISTS` blocks to `SCHEMA_SQL`
   (`holdspeak/db/core.py:142–806`) for `cadence_loops`, `cadence_evidence_refs`,
   `cadence_next_actions`, `cadence_nudges`, `cadence_policies` (full DDL in the rough design §10,
   with `status`/`priority`/`severity` as TEXT, timestamps as TEXT ISO-8601, `stale_score REAL`,
   FKs `ON DELETE CASCADE` to `cadence_loops`). Add indexes: `cadence_loops(status, snoozed_until)`,
   `cadence_loops(source_type, source_id)` **UNIQUE** (the idempotency key for projection).
2. **Bump `SCHEMA_VERSION = 2 → 3`** (`core.py:39`). The existing version bump path backs up +
   re-applies (`core.py:850–891`); the schema-snapshot test must be regenerated
   ([[reference_schema_snapshot_regen]] — use the identical regex, don't hand-edit).
3. **Repository.** New `holdspeak/db/cadence.py` → `class CadenceRepository(BaseRepository)`
   (`db/base.py`: `__init__(self, connection, container)`, JSON helpers provided). Methods:
   `upsert_loop(...)` (INSERT…ON CONFLICT(source_type,source_id) DO UPDATE — preserving
   status/snoozed_until/nudge_count when already user-decided), `get_loop`, `list_loops(status=…)`,
   `set_status(id, status)`, `snooze(id, until)`, `bump_nudge(id, at)`, plus `add_evidence`,
   `add_next_action`, `record_nudge`, `get_policy`/`upsert_policy`. Register in
   `Database.__init__` (`core.py:816`) as `self.cadence = CadenceRepository(self._connection, self)`
   and re-export in `holdspeak/db/__init__.py`.
4. **Models.** `holdspeak/cadence/models.py` — `@dataclass` (frozen where natural) for `OpenLoop`,
   `EvidenceRef`, `NextBestAction`, `Nudge`, `CadencePolicy`, with `Literal` enums per the design
   §4. Pure data; no I/O. The repository converts rows↔dataclasses.

## Scope

- **In:** the 5 tables + indexes, the version bump + snapshot regen, `CadenceRepository`, the
  dataclasses, registration/export.
- **Out:** the collector (1-02), scoring (1-03), the tick (1-04), any reads of meetings/proposals.

## Proof / acceptance

- `Database` opens on a fresh DB and on an existing v2 DB (backup-then-migrate path) without error.
- `CadenceRepository.upsert_loop` is idempotent: two upserts of the same `source_type:source_id`
  yield one row; the second preserves a prior `status="killed"` / `snoozed_until`.
- The schema-snapshot test passes after regeneration.

## Test plan

`tests/unit/test_cadence_models.py` (dataclass round-trips), `tests/integration/test_cadence_store.py`
(real DB: create tables, upsert idempotency, killed-survives-recollection, evidence/next-action FKs
cascade on loop delete). `uv run pytest -q tests/integration/test_cadence_store.py`.
