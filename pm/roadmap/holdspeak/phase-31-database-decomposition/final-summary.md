# Phase 31 — Database Decomposition — Final Summary

**Status: DONE (frozen 2026-06-02).** 5/5 stories shipped. This file is immutable; reopen
work in a new phase.

## Goal (met)

Break the 5,481-line `holdspeak/db.py` god-object — one `MeetingDatabase` class with ~88
methods, ~28 tables, and a 581-line `_apply_schema` carrying an 18-version migration ladder —
into cohesive per-domain repositories and a single canonical schema, behavior-preserving,
greenfield-aggressive (delete, don't wrap). **Met.**

## Result

`holdspeak/db.py` → the `holdspeak/db/` package:

| File | Role | Lines |
|---|---|---|
| `core.py` | `Database` container — connection, schema, singleton (4 methods) | 665 |
| `activity.py` | `ActivityRepository` — local activity-intelligence ledger | 1553 |
| `meetings.py` | `MeetingRepository` — meetings/segments/speakers/bookmarks/action-items/intel snapshots | 890 |
| `plugins.py` | `PluginArtifactRepository` — intent windows, plugin runs/jobs, artifacts | 814 |
| `projects.py` | `ProjectRepository` — projects, associations, detection log | 463 |
| `intel.py` | `IntelRepository` — deferred-intel jobs/attempts queue | 394 |
| `models.py` | 18 dataclasses + validation constants (shared; kills the import cycle) | 345 |
| `base.py` | `BaseRepository` — connection factory, container back-ref, `_json_*` | 49 |
| `__init__.py` | re-exports the full public surface | 17 |
| **total** | | **5,190** |

The package total is *smaller* than the original single file (5,481) — the migration-ladder
squash removed more than the per-file scaffolding added. The god-class is gone in substance
and name (`MeetingDatabase` → `Database`, zero refs in code).

## Exit criteria — all met

- [x] Domain methods live in repositories; a thin `Database` container owns the connection and
      exposes them; the 88-method god-class is deleted (665-line container, 4 methods).
- [x] All call sites use the repo API; `grep -r MeetingDatabase` in code returns nothing; query
      semantics preserved — `tests/unit/test_db.py` (rewritten to the repo API) + full suite green.
- [x] Migration ladder squashed to one canonical schema build; `SCHEMA_VERSION` reset to 1;
      fresh-build `sqlite_master` byte-identical to the pre-squash v18 schema (79 objects),
      pinned by a committed snapshot test.
- [x] Duplicate `CREATE TABLE`s removed (they lived only in the deleted ladder).
- [x] Author's dev DB rebuilt cleanly (dropped from v18, recreated at v1).
- [x] `uv run pytest -q --ignore=tests/e2e/test_metal.py` green throughout — ended at **2063 passed, 14 skipped**.

## Stories

| ID | Story | Evidence |
|---|---|---|
| HS-31-01 | Repository seam + `MeetingRepository` (pilot) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-31-02 | `IntelRepository` (deferred-intel queue) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-31-03 | Plugin/Project/Activity repos + retire the god-class | [evidence-story-03.md](./evidence-story-03.md) |
| HS-31-04 | Squash the migration ladder | [evidence-story-04.md](./evidence-story-04.md) |
| HS-31-05 | Closeout (this summary) | — |

## Key decisions

- **Greenfield/aggressive:** deleted the god-class (no compat facade), squashed migrations
  (no upgrade path), rebuilt the dev DB. Per the operator's standing posture.
- **`models.py` for shared dataclasses** — established in HS-31-01, it permanently removes the
  repo↔container import cycle.
- **Container back-reference (`self._db`)** for the handful of cross-domain calls (intel
  requeue → meeting; activity rule → project). Repos are `Repo(connection, container)`.
- **`intel_snapshots` belongs to `MeetingRepository`** (embedded in `MeetingState`), so
  `IntelRepository` is the jobs/attempts queue only.
- **AST extraction with a coverage assertion** for HS-31-03 (helpers were scattered) — every
  method must land in exactly one category or the extractor fails.
- **Schema honesty via a committed snapshot** rather than a reconstructed version ladder.

## Handoff

`db.py` is no longer a liability. The data layer is navigable and each domain is independently
modifiable. The next foundation work is **Phase 32** (foundation hardening & doc truth):
class-ify `web_runtime.py`, invert the meeting→web coupling, converge audio ownership, add the
ungated CI core-path smoke test, extract a route error helper, and reconcile stale non-PMO docs.
