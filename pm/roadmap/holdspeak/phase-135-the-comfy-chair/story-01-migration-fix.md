# HS-135-01 — The hub opens its own desk

- **Project:** holdspeak
- **Phase:** 135
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-135-13
- **Owner:** unassigned

## Problem

The owner's real DB (schema 59) fails the 59→60 migration:
`sqlite3.OperationalError: no such column: node_id` during
`run_migrations` → `conn.executescript(SCHEMA_SQL)`
(`holdspeak/db/migrations.py:29`). The hub errors on next real start
against current main. Surfaced during Phase 134 (ledgered there; DB
verified unharmed — pristine backup at
`~/.local/share/holdspeak/holdspeak.db.20260816-162131.bak`). Likely
the Phase-132 v60 schema meeting an older mesh-table shape.

## Scope

### In

- Reproduce against a COPY of the owner's backup (NEVER the live file;
  isolated HOME always): copy the .bak into a temp HOME's expected
  path and run the migration.
- Root-cause the failing statement (which CREATE/INDEX/trigger
  references `node_id` against which old-shape table) and fix the
  migration path so schema-59 databases with the older mesh shape
  reach 60 clean (add the missing column-alter step, guard the index
  creation, or stage the mesh-table rebuild — whatever the truth
  requires).
- A regression test that constructs a schema-59 DB with the OLD mesh
  shape (derive the old shape from git history of the schema, not
  guesswork) and proves the migration reaches 60 with data intact.
- Verify the hub boots on the migrated copy (a boot smoke in the
  test or evidence).

### Out

- Any schema v61 changes; touching the owner's live DB (the owner runs
  their own migration after merge); migration framework redesign.

## Acceptance criteria

- [ ] The failing statement is named in the story evidence with the
  old-shape table definition that triggers it.
- [ ] A copy of the real backup migrates 59→60 clean; row counts of
  key tables unchanged (evidence shows before/after counts).
- [ ] The regression test fails on the old code and passes on the fix.
- [ ] Full migration-related focused tests green.

## Test plan

- `HOME=$(mktemp -d) uv run pytest -q tests/unit -k "migrat or schema" --tb=short`
  plus the new test; the real-backup-copy migration run captured in
  evidence (unsandboxed step run by the orchestrator if LAN/home
  access is needed — coordinate before SHIP).
