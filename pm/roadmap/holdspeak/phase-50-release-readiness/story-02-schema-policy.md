# HS-50-02 — Safe-by-default schema policy

- **Project:** holdspeak
- **Phase:** 50
- **Status:** backlog
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
- [ ] `_ensure_schema` implements the four-way matrix; the silent data-loss path is
      closed (no destructive action without a backup; newer DB refused untouched).
- [ ] The fresh-install path (empty/absent DB) is byte-identical to today.
- [ ] Behavior-preserving for the common case (stored == version is a no-op); the
      `reset_database()` / temp-DB test idiom still works.
- [ ] Tests cover fresh / equal / older / newer; full relevant suite green.

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
