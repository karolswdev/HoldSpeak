# HS-130-10 — Inherited ledger triage (2026-08-09)

Full isolated-HOME backend suite on phase-130 HEAD == pre-phase baseline, **byte-identical failing set** across all 9 stories (zero regressions, zero inherited failures touched).

- **repaired-by-130:** 1 (`test_api_surface` — the DecisionRecord rename's manifest drift, regenerated at close per Sol's counsel)
- **newly-caused:** 0 (every story shipped at zero net regression vs baseline)
- **131-owned (sync contract):** 7
- **still-inherited (re-ledgered):** 94 across 35 test files (was 95; `test_api_surface` reclassified repaired-by-130)

## 131-owned — route to Phase 131 (sync registry + deployment revisions)

These fail on the sync/kind/changeset contract that Phase 131's one sync registry (buckets/maps/serializers) and admission-captured deployment revision resolve. They are Candidate Z's sync-contract slice; do NOT re-count them under a general debt phase.

- `tests/integration/test_primitive_framework_sync.py::test_ipad_synced_graph_workflow_runs_on_the_hub`
- `tests/integration/test_web_companion_slack.py::test_source_identity_must_be_a_known_qualified_kind`
- `tests/unit/test_primitive_contract.py::TestHubEmissionsValidate::test_pull_body_validates_against_changeset_envelope`
- `tests/unit/test_primitive_contract.py::TestKindSetCannotDrift::test_schemas_cover_exactly_sync_kinds`
- `tests/unit/test_primitive_contract.py::TestKindSetCannotDrift::test_swift_sync_kind_matches_hub`
- `tests/unit/test_web_routes_sync.py::test_pull_serializes_meetings_and_artifacts`
- `tests/unit/test_web_routes_sync.py::test_push_live_merges_meeting_and_keeps_audit_inbox`

## still-inherited — re-ledgered to a dedicated remediation phase (Phase 118–128 integration debt)

Unrelated to placement/execution truth; grouped by test file with a named provisional home. Owner rules the remediation-phase scope at the sitting (this is the surviving body of Candidate Z after the 131 slice is removed).

| Test file | Count | Family / provisional home |
|---|---|---|
| `test_workbench_walk` | 14 | Workbench e2e harness (Phase 122 walk) — remediation phase |
| `test_web_server` | 13 | Web server routes — remediation phase |
| `test_intel_streaming` | 9 | Meeting intel streaming (Phase 124/125) — remediation phase |
| `test_web_companion_slack` | 6 | Companion Slack (Phase 119) — remediation phase |
| `test_history_slack_surfaces` | 4 | History Slack — remediation phase |
| `test_web_dictation_cockpit` | 4 | Dictation/other surface — remediation phase |
| `test_web_dictation_correction_ritual` | 4 | Dictation/other surface — remediation phase |
| `test_live_bus` | 3 | Live bus (Phase 123) — remediation phase |
| `test_decision_records` | 3 | Decision records integration (now DecisionRecord) — remediation phase |
| `test_web_history_import_ui` | 3 | History import — remediation phase |
| `test_cadence_agent` | 2 | Cadence agent — remediation phase |
| `test_web_companion_github` | 2 | Companion GitHub — remediation phase |
| `test_web_companion_webhook` | 2 | Companion webhook — remediation phase |
| `test_web_dictation_journal` | 2 | Dictation/other surface — remediation phase |
| `test_web_dictation_learning_digest` | 2 | Dictation/other surface — remediation phase |
| `test_web_history_archive` | 2 | History archive — remediation phase |
| `test_actuator_presence_broadcasts` | 1 | Actuator/presence bus — remediation phase |
| `test_dictation_journal_replay` | 1 | Dictation journal replay — remediation phase |
| `test_dictation_moment_of_truth` | 1 | Dictation moment — remediation phase |
| `test_meeting_conflict_recovery` | 1 | Meeting sync conflict (ConflictError NameError, crud.py:161) — remediation phase |
| `test_rails_observer_live` | 1 | Rails observer live/.43 — remediation phase (needs metal) |
| `test_web_dictation_blocks_api` | 1 | Dictation/other surface — remediation phase |
| `test_web_dictation_corrections_api` | 1 | Dictation/other surface — remediation phase |
| `test_web_dictation_readiness_api` | 1 | Dictation/other surface — remediation phase |
| `test_web_dictation_settings_api` | 1 | Dictation/other surface — remediation phase |
| `test_web_dictation_trust_signals` | 1 | Dictation/other surface — remediation phase |
| `test_web_dry_run_api` | 1 | Dictation dry-run API — remediation phase |
| `test_web_project_kb_api` | 1 | Project KB API — remediation phase |
| `test_induction_integration_43` | 1 | Induction .43 — remediation phase (needs metal) |
| `test_mesh_dispatch` | 1 | KNOWN FLAKE (passes on rerun) — quarantine candidate |
| `test_db` | 1 | DB — remediation phase |
| `test_decision_commitments` | 1 | Decision commitments — remediation phase |
| `test_interior_canon_guard` | 1 | CSS left-rail canon guard — remediation phase |
| `test_product_copy` | 1 | Product-copy drift guard — remediation phase |
| `test_web_vocabulary_guard` | 1 | Web prose dash guard — remediation phase |

## Close addendum (2026-08-09, Sol counsel)

`test_api_surface` was originally listed still-inherited; Sol's close counsel showed it is 130-caused drift (the DecisionRecord rename added `/api/decision-records` routes without regenerating `docs/api-surface.json`). Regenerated via `scripts/gen_api_surface.py` (436 routes) and reclassified **repaired-by-130**. No other reclassification.
