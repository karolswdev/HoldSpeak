# Phase 31 — Database Decomposition

**Status:** in-progress (opened 2026-06-02). 4/5 stories shipped.

**Last updated:** 2026-06-02 (HS-31-04 done — 18-version migration ladder squashed to one
canonical schema; `SCHEMA_VERSION` reset to 1; `core.py` 1224→666; fresh-build `sqlite_master`
proven identical to the pre-squash v18 schema (snapshot test committed); dev DB dropped &
recreated. Suite green at 2063. HS-31-05 closeout next.).

## Goal

Break the 5,481-line `holdspeak/db.py` monolith into cohesive per-domain
repository classes and a separated migration ladder, with **zero behavior
change** at each step. `db.py` is now the persistence layer for every feature
in the product — meetings, deferred intel, activity intelligence, plugin/artifact
synthesis, projects — and it has grown into a single `MeetingDatabase` class with
~131 methods, ~28 tables, ~215 raw `execute()` calls, and a single 581-line
`_apply_schema()` (`db.py:857-1438`) where the same tables (`speakers`,
`intent_windows`) are created 2-3× across initial schema and migrations. It is
the module most likely to rot first and is the scariest to touch while it is one
file; this phase makes it navigable and safely modifiable without changing a
single caller.

## Scope

**Posture: greenfield / aggressive.** There is exactly one user (the author) and
one dev DB. We are **not** protecting external callers or old on-disk databases —
so we take the clean end state, not the compatibility-preserving one. The
*query semantics* stay identical (the win is separation, not behavior change), but
the *call shape* and the migration history are free to change.

### In

- Introduce a `holdspeak/db/` package with a shared connection/transaction helper
  and per-domain repositories:
  - `MeetingRepository` — meetings, segments, speakers, topics, bookmarks,
    action_items, meeting_tags, meeting_projects.
  - `IntelRepository` — intel_jobs, intel_job_attempts, intel_snapshots.
  - `ActivityRepository` — activity_records/annotations/domain_rules/
    enrichment_connectors/import_checkpoints/meeting_candidates/privacy_settings/
    project_rules.
  - `PluginArtifactRepository` — plugin_runs, plugin_run_jobs, artifacts,
    artifact_sources, intent_windows, intent_window_scores.
  - `ProjectRepository` — projects, project_detection_log, connector_runs.
- A thin `Database` container owns the one connection and exposes the repos as
  attributes (`db.meetings.save(...)`, `db.intel.claim(...)`). **Update all call
  sites** to use it. **Delete the 131-method `MeetingDatabase` god-surface** — do
  not keep it as a delegating facade (that just relocates the god object).
- **Squash the migration ladder.** Collapse the 18-version `_apply_schema()` into
  a single canonical `CREATE TABLE` set that builds the current (v18-equivalent)
  schema in one shot; delete the historical version steps and the duplicate
  `CREATE TABLE`s. Reset `SCHEMA_VERSION` to 1 (fresh history). The author's one
  dev DB gets a one-shot rebuild (export-what-matters / recreate, or just drop) —
  no in-place upgrade path is preserved.

### Out

- Query-semantics changes: the SQL each method runs stays equivalent — this is
  separation + a schema squash, not a behavior or data-model redesign. No new
  tables/columns beyond removing the now-redundant migration scaffolding.
- Introducing an ORM or query builder. Stays raw `sqlite3`.
- Async/threadpool offload of sync DB calls (settled in Phase 26; out of scope).

## Exit criteria (evidence required)

- [ ] Domain methods live in repository classes; a thin `Database` container owns
      the connection and exposes the repos; the 131-method `MeetingDatabase`
      god-class is **deleted**, with line-count before/after recorded.
- [ ] All call sites use the new repo API; `grep` shows no remaining
      `MeetingDatabase` usage. Query semantics preserved — proven by
      `tests/unit/test_db.py` (rewritten to the repo API) + the full suite green.
- [ ] The migration ladder is **squashed** to a single canonical schema build;
      `_apply_schema()`'s 18-version ladder and duplicate `CREATE TABLE`s are gone;
      `SCHEMA_VERSION` reset to 1. A fresh build produces the current
      (v18-equivalent) schema — proven by a `sqlite_master` dump diff against a
      pre-refactor fresh build being empty.
- [ ] The author's dev DB is rebuilt cleanly (note in evidence what was preserved
      vs. dropped).
- [ ] `uv run pytest -q --ignore=tests/e2e/test_metal.py` is green throughout.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-31-01 | Repository seam + `MeetingRepository` (pilot pattern) | done | [story-01-meeting-repository.md](./story-01-meeting-repository.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-31-02 | `IntelRepository` extract | done | [story-02-intel-repository.md](./story-02-intel-repository.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-31-03 | `ActivityRepository` + `PluginArtifactRepository` + `ProjectRepository` + delete god-class | done | [story-03-activity-plugin-repos.md](./story-03-activity-plugin-repos.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-31-04 | Squash the migration ladder | done | [story-04-migration-framework.md](./story-04-migration-framework.md) | [evidence-story-04.md](./evidence-story-04.md) |
| HS-31-05 | Decomposition closeout (size + schema-parity evidence) | not-started | [story-05-decomposition-closeout.md](./story-05-decomposition-closeout.md) | — |

## Where we are

Opened 2026-06-02 as a fast-follow once the engineering review flagged `db.py`
as the single largest structural liability in the repo. Phase 26 already proved
the playbook on `web_server.py` (5,658 → 523 lines, behavior-preserving); this
phase reuses it.

**HS-31-01 is done.** `holdspeak/db.py` is now the `holdspeak/db/` package:
`models.py` (18 dataclasses + constants), `base.py` (`BaseRepository` + shared
`_json_*`), `meetings.py` (`MeetingRepository` — meetings/segments/speakers/topics/
bookmarks/action-items + intel snapshots, moved verbatim), and `core.py` (the
`MeetingDatabase` container, 5481 → 4311 lines, still holding the un-migrated
domains). 53 production + 112 test call sites moved to `db.meetings.*`; the
god-class no longer has the moved methods (test-pinned). `__init__.py` re-exports
the full public surface, so `from holdspeak.db import X` is unchanged. Suite green
at 2062; the package is ruff-clean. The seam every later story copies now exists.

**HS-31-02 is done.** `IntelRepository` (`holdspeak/db/intel.py`, 394 lines) owns the
deferred-intel queue: the 11 `*_intel_job*` / `update_meeting_intel_status` methods moved
verbatim; `core.py` dropped to 3934. The one cross-domain call (`requeue_intel_job` →
`get_meeting`) established the **container back-reference** pattern: repos receive the
container as `self._db`, so `requeue` calls `self._db.meetings.get_meeting(...)`. 19
production + 32 test call sites moved to `db.intel.*`; 7 fake doubles got an `intel`
self-property. Suite green at 2062; ruff-clean.

**HS-31-03 is done.** The last three domains are extracted — `PluginArtifactRepository`
(`plugins.py`, 814), `ProjectRepository` (`projects.py`, 463), `ActivityRepository`
(`activity.py`, 1553) — via AST extraction (scattered helpers) with a coverage assertion.
`core.py` is now a **1224-line container** (from 5481, −78%): connection, schema, the
singleton, nothing else. The god-class was then **renamed `MeetingDatabase → Database`**
(145 refs across 41 files; zero in code, no alias). The one inter-repo call (activity→project)
uses `self._db.projects`. ~469 call sites moved; 11 fakes got repo self-properties. Suite
green at 2062; ruff-clean.

**HS-31-04 is done.** The 18-version migration ladder (~558 lines of dead-for-fresh-builds
code in `_apply_schema`) is deleted; the schema is built from the single canonical `SCHEMA_SQL`.
`SCHEMA_VERSION` reset 18→1; `core.py` 1224→666. A fresh build's `sqlite_master` is byte-identical
to the pre-squash v18 schema (79 objects) — pinned by `tests/fixtures/db_schema_canonical.txt` +
`test_fresh_schema_matches_canonical_snapshot`. Duplicate `CREATE TABLE`s (only in the ladder)
are gone. Dev DB dropped & recreated at v1. Suite green at 2063.

Next: **HS-31-05** — closeout: confirm exit criteria, final size/parity evidence, `final-summary.md`.

## Pickup order

1. HS-31-01 — establish the repository + shared-connection pattern on the
   meetings cluster; this is the load-bearing pilot.
2. HS-31-02..03 — migrate one domain per story (one PR each), facade delegating.
3. HS-31-04 — once methods are domain-grouped, extract the migration ladder and
   collapse duplicate table definitions.
4. HS-31-05 — size + schema-parity evidence + closeout / `final-summary.md`.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| A method changes query behavior subtly during a move (param order, default, return shape) | Medium | Move the SQL verbatim; `test_db.py` (rewritten to the repo API) + full suite as the gate | Any DB test fails on logic, not just an import rename |
| Migration squash changes the resulting schema vs. today | Medium | Diff `sqlite_master` from a fresh build before/after; require empty diff. (No upgrade path to preserve — greenfield) | The fresh-build schema dump differs from the pre-refactor baseline |
| Call-site churn (deleting the god-class touches many files) misses a usage | Medium | `grep -r MeetingDatabase` + the full suite must show zero remaining usage; lean on tests, not caution | An import/attr error surfaces after the god-class is removed |
| Repos sharing one connection introduce transaction/locking regressions | Medium | One owned connection on the `Database` container; repos receive it, never open their own; preserve existing `with conn:` boundaries | A test exposes a partial-write or "database is locked" not present before |
| Hidden coupling via late imports (`from .meeting_session import ...` inside methods) breaks on move | Low | Keep the late-import where it guards a cycle; pin with an import test | A circular import appears when a method moves to a repo module |

## Decisions made (this phase)

- 2026-06-02 — Split out as its own phase (not folded into Phase 32 hardening) —
  `db.py` is a Phase-26-scale beast and deserves an isolated blast radius — user.
- 2026-06-02 — **Greenfield/aggressive posture** — no users but the author, one
  dev DB, "destructive is fine." So: delete the `MeetingDatabase` god-class
  (update call sites to a clean repo API) rather than keep a compat facade; and
  **squash** the migration ladder to one canonical schema rather than preserve an
  upgrade path — user.

- 2026-06-02 (HS-31-01) — **Package layout resolved:** `holdspeak/db/` with
  `models.py` (shared dataclasses, kills the import cycle for all repos), `base.py`,
  one module per domain, and `core.py` as the container. `__init__.py` re-exports
  the full public surface so no caller import changes.
- 2026-06-02 (HS-31-01) — **`intel_snapshots` belongs to `MeetingRepository`,** not
  `IntelRepository`: it is embedded in `MeetingState` save/load, not queue state. So
  HS-31-02's `IntelRepository` scope narrows to the jobs/attempts queue.
- 2026-06-02 (HS-31-02) — **Container back-reference for cross-domain calls.** Repos are
  constructed `Repo(self._connection, self)` and reach siblings via `self._db.<repo>`.
  Chosen over threading specific sibling repos per constructor — simpler as cross-domain
  calls multiply in HS-31-03. Coupling is repo→container (the composition root), acceptable.

## Decisions deferred
- Exact dev-DB rebuild handling (drop & recreate vs. export-then-recreate) —
  trigger: HS-31-04 — default: whatever is least effort; the data is the author's
  own and reproducible.
