# HS-159-01 - The watch graduation: WatchSpec@1 lands, legacy keeps breathing

- **Project:** holdspeak
- **Phase:** 159
- **Status:** done
- **Depends on:** -
- **Unblocks:** HS-159-02
- **Owner:** unassigned

## Problem

`connector_watches` (schema.py:2295) holds typed Watch identity,
query_json, snapshot baseline, error and enabled state — the SRS
graduates it to `WatchSpec@1` (§9.3) rather than birthing a parallel
root (AD-PRJ-010). The setup needs its own durable tables (§9.1) and
the rule/evaluation/effect contracts need homes (§9.4). Every
existing Watch and its attached Reactions MUST keep running.

## Scope

- **In:** (a) ADDITIVE columns on `connector_watches` per §9.3:
  `schema_version, project_id, intent, provider_connection_id,
  subject_kind, trigger_kind, trigger_json, mode, state, revision,
  baseline_state, test_state, test_result_json, last_test_at,
  next_evaluation_at, last_evaluated_at` — keep `query_json` as
  subject scope/query and `snapshot_json` as baseline cache; existing
  IDs untouched. Migration-as-backfill: existing rows become
  `schema_version='WatchSpec@1'`, `intent='Legacy automation watch'`,
  project_id NULL, trigger from the embedded
  refresh_interval_minutes, state from enabled. (b) New tables §9.1:
  `project_setup_sessions`, `project_setup_answers` (append-only,
  UNIQUE(session_id, question_id, revision)),
  `watch_setup_proposals`, `watch_provider_connections` (NO
  credential material — PROV-004). (c) §9.4: `watch_rules`
  (UNIQUE(watch_id, ordinal)), `watch_evaluations`
  (UNIQUE(watch_id, watch_revision, source_revision)),
  `watch_effects` (idempotency_key UNIQUE). (d) `project_sources`
  (§5.4) — the Project↔`watch:<id>` binding that stores semantic
  role/materiality and NEVER copies query/cadence/baseline
  (DOM-013). (e) Repo helpers; canonical snapshot regen per the
  recorded gotcha; SCHEMA_VERSION bump.
- **Out:** any service behavior change (02/03); provider adapters;
  evaluation logic.

## Acceptance criteria

- [ ] A pre-159 DB (and a COPY of the real DB) reconciles: every existing connector_watch row backfilled to WatchSpec@1 with its ID, query_json, snapshot_json, error history, and attached connector_reactions intact; repeated reconcile idempotent.
- [ ] Legacy compat pinned BEFORE the change: characterization tests over ReactionService.refresh_due_watches/preview/diff paths green before and after the graduation.
- [ ] All new tables carry the SRS's uniqueness/idempotency constraints; named-column INSERTs only; snapshot diff confined to new lines.
- [ ] project_sources enforces DOM-013 by shape (no query/cadence/baseline columns exist to copy into).

## Test plan

- **Unit:** `tests/unit/test_watch_graduation_schema.py` (fresh + legacy fixture + real-DB copy; backfill truth table); ReactionService characterization pins; snapshot + positional-INSERT fences.

## What shipped

- Schema v68: `connector_watches` +16 §9.3 columns (query_json and
  snapshot_json untouched); 8 new tables — setup sessions/answers/
  proposals, provider connections (no credential columns),
  rules/evaluations/effects with the SRS's uniqueness, and
  `project_sources` (DOM-013 by shape: no query/cadence/baseline
  columns exist to copy into); 9 indexes; named columns throughout.
- The backfill lives in `reconcile.py:_backfill_watch_graduation`
  (inside `_apply_data_backfills`): rows with empty schema_version
  graduate to WatchSpec@1 / 'Legacy automation watch' / poll trigger
  lifted from query_json.refresh_interval_minutes / state from
  enabled / yolo / revision 1. Second reconcile is a no-op.
- LEGACY PINNED FIRST: 31 characterization tests over
  ReactionService's watch paths (create/list/preview/refresh cycle/
  due cadence/diff semantics/reaction routing) — green before AND
  after the graduation.
- Repo helpers in `holdspeak/db/automations.py` (where
  connector_watches access already lived); nothing calls the new
  ones yet.
- REAL-DB PROOF RUN BY THE ORCHESTRATOR (the worker only authored
  it): the owner's actual DB copied to tmp, reconciled — watch IDs,
  row counts, and attached reactions intact; backfill truth verified;
  second pass no-op. `1 passed in 0.68s`. Scoped set:
  154 passed, 2 skipped (the CI-skip legs) under isolated HOME.

## Notes / open questions

- The real-DB test copies via shutil.copy2 and opens ONLY the copy — the one lawful un-isolated pytest invocation, verified by code read before running.
