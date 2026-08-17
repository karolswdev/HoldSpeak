# HS-137-03 — The test reckoning

- **Project:** holdspeak
- **Phase:** 137
- **Status:** done
- **Depends on:** HS-137-01
- **Unblocks:** HS-137-04
- **Owner:** unassigned

## Problem

~15 tests exercise the deleted migration chain (fake an old-version DB,
assert it upgrades). They test machinery that no longer exists. And a few
assert version NUMBERS that should assert SHAPE. Reckon with them.

## Scope

### In

- **DELETE** the migration-chain tests (they test `run_migrations`
  replaying a specific version step — gone):
  `test_db.py::test_a_v58_database_upgrades_additively`,
  `test_decision_record_service.py::test_schema_migrates_v40_to_v43` and
  `::test_schema_migrates_v42_decision_record_tombstones`,
  `test_monday_brief_service.py::test_schema_migrates_v39_to_v40`,
  `test_decision_commitments.py::test_v38_database_gains_commitments_table`,
  `test_migration_v59_mesh_workers.py` (whole file),
  `test_kernel_cancelled_schema.py` (whole file),
  `test_projection_schema.py` (whole file, if it only tests the v45
  step — confirm),
  `test_speech_side_door_admission.py::test_schema_v57_upgrades_publication_claim_before_installing_triggers`,
  `test_memory_index.py::test_v31_migration_backfills_existing_rows`,
  `test_db_actuator_origin.py::test_v4_upgrade_retypes_desk_rows`,
  `test_recipe_pinned_context.py::test_v6_facsimile_upgrade_adds_the_columns`
  and `::test_v7_agents_table_renames_to_recipes`,
  `test_run_artifacts.py::test_v5_to_v6_upgrade_rebuilds_without_losing_rows`,
  `test_db_steering_audit.py::test_v11_*` and `::test_v21_*`.
  **Verify each is migration-chain-only before deleting** (grep the test
  body); if a file has non-migration tests too, delete only the
  migration test, not the file.
- **REWRITE** `test_db_schema_policy.py` (the four-way fresh/current/
  older/newer policy) → test the reconcile: fresh DB works, reconcile is
  idempotent on a current DB, a "newer"-stamped DB opens (no refusal), a
  missing table/column self-heals, orphan tables survive.
- **REWRITE** `test_doctor_config_honesty.py:47-58` for the new doctor
  output (no version comparison).
- **REWRITE** `test_decision_records.py` (integration, lines ~55-60/230/
  343) to drop the version-stamp setup while keeping the domain
  assertions (CRUD/FTS/supersession).
- **KEEP** `test_db.py::test_fresh_schema_matches_canonical_snapshot` and
  `tests/fixtures/db_schema_canonical.txt` — the shape guard survives.
- **LEAVE ALONE** the unrelated `*_SCHEMA_VERSION` payload/protocol tests
  (`test_ask_runner_migration.py`, `test_hs13103_remaining_obligations.py`,
  `test_projection_stager.py`, the service-level `*_runner_migration.py`
  files) — they are not the DB schema system.

### Out

- Production code (HS-137-01/02).

## Acceptance criteria

- [ ] Every migration-chain test is deleted (or its migration case
  removed), verified by grep for `read_schema_version(` / `stamp`-old-
  version setup returning clean in kept tests.
- [ ] `test_db_schema_policy.py` asserts reconcile behavior (idempotent,
  self-heal, newer-opens, orphan-safe), not version comparison.
- [ ] The canonical-snapshot shape test still passes.
- [ ] `uv run pytest -q tests/ -k "db or schema or doctor or decision or
  migration"` is green (no references to the deleted symbols).

## Test plan

- The `-k` run above, read before flipping. The orchestrator runs the
  full suite.
