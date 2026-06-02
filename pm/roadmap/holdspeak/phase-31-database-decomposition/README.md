# Phase 31 — Database Decomposition

**Status:** in-progress (opened 2026-06-02; HS-31-01 first).

Phase 31 breaks the `holdspeak/db.py` monolith (5,481 lines — one `MeetingDatabase`
class with ~131 methods, ~28 tables, ~215 raw `execute()` calls, and a single
581-line `_apply_schema()` carrying an 18-version migration ladder) into cohesive
per-domain repository classes behind a thin `Database` container, and **squashes**
the migration ladder to one canonical schema. Query semantics are preserved; the
god-class and the migration history are not.

**Posture: greenfield/aggressive** — one user (the author), one dev DB, destructive
changes are fine. So unlike Phase 26's compat-preserving decomposition, this phase
**deletes** the `MeetingDatabase` god-class (call sites move to `db.meetings.*`)
rather than keeping a delegating facade, and **squashes** the migration ladder
rather than preserving an upgrade path. Same "one beast per phase, existing suite
is the regression gate" discipline, applied to the module that backs *every*
feature (meetings, intel, activity, plugins, artifacts, projects).

## Where to look first

- `current-phase-status.md` — goal, scope, exit criteria, story table, risks.
- `../phase-26-web-runtime-decomposition/` — the precedent: a behavior-preserving
  monolith split with a route-inventory diff per story. This phase mirrors its shape.
- `../../../holdspeak/db.py` — the monolith being decomposed.
- `../../../tests/unit/test_db.py` — the 1,617-line regression gate this phase leans on.

## Phase boundaries

This phase owns the **structure** of the persistence layer: repository extraction,
deleting the god-class, updating call sites to the `db.*` container, and squashing
the migration ladder to one canonical schema. It does **not** redesign the data
model, add tables/columns beyond removing redundant scaffolding, alter query
semantics, or introduce an ORM. Call sites change (by design — the god-class is
deleted), but the SQL each repository runs is the same SQL it ran before.

Async/threadpool offload of sync SQLite calls is explicitly out (already answered
"document, no offload" in Phase 26's `audit-sync-db-async.md`).
