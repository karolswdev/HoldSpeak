# HS-126-02 — Persist the brief

- **Project:** holdspeak
- **Phase:** 126
- **Status:** backlog
- **Depends on:** HS-126-01
- **Unblocks:** HS-126-03 through HS-126-08
- **Owner:** unassigned

## The thesis (the bar)

A generated brief is a local, inspectable receipt, not an ephemeral
summary. Persist its period, delivery state, disposition, and every cited
item so the desk, API, and MCP surface read one durable truth.

### What changes

1. Add `monday_briefs` with `id`, `period_start`, `period_end`, `headline`,
   `generated_at`, `spoken`, and `disposition`.
2. Add `monday_brief_items` with `id`, `brief_id`, `section`, `source_ref`,
   `text`, `detail`, and `priority`.
3. Add keys, foreign-key relationships, and the period uniqueness constraint
   required by generation idempotency.
4. Bump the schema and update the checked-in schema contract.

## Acceptance criteria

1. A brief and its ordered, sectioned items round-trip through SQLite.
2. Item rows cannot refer to a nonexistent brief.
3. The schema prevents duplicate briefs for one generation period.
4. `spoken` and `disposition` can be updated without changing brief content.
5. The schema version and schema snapshot agree.

## Test plan

- Migration: open an existing database and verify the schema bump applies.
- Repository: insert, read, and update a brief with items.
- Constraint: duplicate period and orphan-item inserts fail cleanly.
- Run the focused schema and persistence test selection with `uv run pytest -q`.
