# Evidence — HS-74-01 — Run results persist as artifacts (hub)

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-74-run-story`)
- **Owner:** agent (Fable), owner-directed phase

## What changed

- **Schema v6** (`SCHEMA_VERSION = 6`): the artifacts table becomes
  owner-typed exactly the way proposals did in v5 — `meeting_id` is
  nullable and `origin IN ('meeting', 'run')`; a run-born artifact
  (origin `run`) carries NULL and its anchor is the capability lineage in
  `artifact_sources`. Upgrade = the standard SQLite rebuild (FKs
  suspended for the swap, ids verbatim, existing rows backfill
  `origin='meeting'`), riding the Phase-50 backup-then-apply path.
- **`record_artifact`** accepts an empty `meeting_id` (→ NULL +
  `origin='run'`); `artifact_id` stays required. Row reads are NULL-safe
  (`meeting_id` is `""` on every Python surface — never `None`).
  New `list_run_artifacts()` + factored `_sources_for`/`_artifact_summary`.
- **Sync**: `/api/sync/pull` gains the run-born lane (the second artifact
  loop); `_artifact_value` serializes `meeting_id` as a plain string
  (`""` for run-born — **the iPad's non-optional `meetingId: String`
  decode is unmoved; the wire shape is unchanged**); `_merge_artifacts`'
  "no meeting → skip" guard is replaced by real support (a pushed
  run-born artifact merges).
- **The three run routes persist**: a shared `_persist_run_artifact`
  (title `"<name>: <input head>"`, `artifact_type="run_output"`,
  `plugin_id="<kind>_run"`, status draft, the route's existing lineage
  `sources` — capability first) and every success response gains
  `artifact_id`. Persistence failure never eats a successful run (log +
  `artifact_id: null`). Workflow persists on BOTH paths (graph + prompt).

## Verification artifacts

- `tests/unit/test_run_artifacts.py` — **5 passed**:
  1. run-born `record_artifact` round-trips with lineage;
  2. empty `artifact_id` still refused;
  3. meeting-scoped listing unaffected (the two lanes don't bleed);
  4. the REAL route (stub engine): `POST /api/agents/{id}/run` →
     `artifact_id` in the response, the stored row carries body/lineage/
     title, and `/api/sync/pull` includes it with `meeting_id: ""` (a
     string on the wire, never null);
  5. **the v5→v6 upgrade**: a v5-facsimile DB rebuilds without losing a
     row (ids verbatim, backfilled origin), accepts a run-born row after,
     and a `.bak` landed BEFORE the migration (the Phase-50 contract).
- The two schema guards fired exactly as designed and were updated in
  this commit: the canonical snapshot (regenerated with the test's
  literal normalizer — the documented recipe) and the sync route stub
  (gains `list_run_artifacts`).
- Two more guards fired on the full sweep — the existing route tests pin
  the exact run-response dicts; they gain the popped `artifact_id`
  (asserted non-empty) in this commit.
- Full suite at ship: **3076 passed, 37 skipped, 0 failures** (3071 + the
  5 new).

## Acceptance criteria — re-checked

- [x] A run persists a REAL artifact in the one store, capability lineage
      attached; the response carries `artifact_id`.
- [x] The sync value shape is unchanged (string `meeting_id`); the pull
      carries run-born artifacts; a pushed run-born artifact merges.
- [x] Meeting-scoped read paths untouched.
- [x] The upgrade is the v5 precedent verbatim (backup, rebuild, ids kept).

## Deviations from plan

- The story said "loosen record_artifact for empty meeting_id"; the FK +
  NOT NULL constraint made that a REAL schema migration (v6). Done via
  the repo's own v5 recipe rather than an empty-string FK hack — the
  scaffold's status doc was written before the DDL was read; the schema
  work is the honest cost of the story.
