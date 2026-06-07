# HS-50-02 — Safe-by-default schema policy

- **Project:** holdspeak
- **Phase:** 50
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-50-03, HS-50-04, HS-50-07
- **Owner:** unassigned

## Problem
`holdspeak/db/core.py:_ensure_schema` (l.625-636) rebuilds the schema via
`_apply_schema` -> `SCHEMA_SQL` `executescript` (l.638-658) whenever the stored
version is below `SCHEMA_VERSION` (l.28). There is no backup and no
newer-than-known guard. The next schema bump silently destroys an existing user's
data. This is the heart of the phase.

## Scope
- **In:** make `_ensure_schema` safe by default, with an explicit matrix:
  - **fresh / empty DB** -> create at the current `SCHEMA_VERSION` (exactly as
    today; the fresh-install path is untouched).
  - **stored == SCHEMA_VERSION** -> no-op.
  - **stored < SCHEMA_VERSION** -> back up first (HS-50-03), then apply; never a
    bare rebuild that loses data without a backup.
  - **stored > SCHEMA_VERSION** -> refuse with a clear error (this build is older
    than the DB); do not downgrade-rebuild, do not touch the data.
- **Out:** the backup mechanism itself (HS-50-03 provides it; this story calls it);
  doctor surfacing (HS-50-04); a historical migration ladder (none deployed — this
  is the forward contract).

## Acceptance criteria
- [x] `_ensure_schema` implements the four-way matrix; the silent data-loss path is
      closed (no destructive action without a backup; newer DB refused untouched).
      (`db/core.py` `_ensure_schema` + `_read_schema_version` + `SchemaVersionError`)
- [x] The fresh-install path (empty/absent DB) is byte-identical to today.
      (same `_apply_schema(conn)`, no backup; full suite green)
- [x] Behavior-preserving for the common case (stored == version is a no-op); the
      `reset_database()` / temp-DB test idiom still works.
- [x] Tests cover fresh / equal / older / newer; full relevant suite green.
      (`tests/unit/test_db_schema_policy.py`; 2436 passed)

## Note on the framing (verified against the live tree)
`SCHEMA_SQL` is fully additive today (all `CREATE TABLE IF NOT EXISTS`, no
`DROP`/`DELETE`), so the current `executescript` does not literally drop tables.
The real unguarded holes were: a newer DB silently run by an older build, and no
backup before any future migration. Both are closed. See
[evidence-story-02.md](./evidence-story-02.md).

## Test plan
- Unit/integration: open a fresh DB (created at version); open at-version (no-op);
  open an older-version DB (backup taken, schema applied, no data lost where the
  schema is additive); open a newer-version DB (raises a clear error, file
  untouched). `uv run pytest -q -k "schema or db or database or migrat"`.

## Notes / open questions
- Bump `SCHEMA_VERSION` in a test fixture (not the real constant) to simulate
  older/newer without a real schema change, or stamp the `schema_version` table
  directly.
- Decide the refusal type (a dedicated exception) so callers + doctor can render it
  cleanly.
