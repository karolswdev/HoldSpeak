# MIR-01 traceability matrix

**Captured:** 2026-04-26 00:37 UTC
**Git:** c603638 (HS-2-10: MIR doctor checks + failure-isolation integration test)
**Bundle:** `docs/evidence/phase-mir-01/20260426-0037/`

Every requirement from spec §7.2 mapped to the evidence artifact that
demonstrates it. Methods follow the spec's UT/IT/AT/MT/LG taxonomy.

## Functional requirements

| Req | Method | Evidence | Notes |
|---|---|---|---|
| MIR-F-001 | UT | `10_ut_router.log` (`test_build_intent_windows_*`, `test_score_windows_works_end_to_end_with_build_intent_windows`) | Rolling-window builder with deterministic boundaries |
| MIR-F-002 | UT | `10_ut_router.log` (`test_score_window_supports_multi_label_above_threshold_mir_f_002`) | Multi-label scoring per window |
| MIR-F-003 | UT | `10_ut_router.log` (`test_available_profiles_include_balanced_and_domain_profiles`) | 5 supported intents in `SUPPORTED_INTENTS` |
| MIR-F-004 | UT | `10_ut_router.log` (`test_score_window_supports_multi_label_above_threshold_mir_f_002`) | Multiple intents above threshold in same window |
| MIR-F-005 | UT | `10_ut_router.log` (`test_select_active_intents_uses_threshold_and_hysteresis`, `test_iter_intent_transitions_hysteresis_suppresses_oscillation_mir_f_005`) | Hysteresis suppresses oscillation |
| MIR-F-006 | UT | `10_ut_router.log` (`test_preview_route_uses_scores_when_no_override`, `test_preview_route_honors_override_intents_and_profile_chain`) | Deterministic plugin chain selection |
| MIR-F-007 | IT | `20_it_routing.log` (`test_intent_override_put_invokes_callback_with_intent_list` in 40_api_checks.log; CLI `holdspeak intel route --override`) | Manual override changes routing |
| MIR-F-008 | UT | `10_ut_router.log` (`test_dispatch_window_idempotency_dedups_second_dispatch_mir_f_008`) | Per-`(meeting,window,plugin,hash)` dedup |
| MIR-F-009 | IT | `20_it_routing.log` (`test_pipeline_rerun_dedupes_via_host_idempotency_cache`); `20_it_synthesis.log` (`test_synthesis_dedupes_identical_outputs_across_overlapping_windows`) | Overlapping windows do not duplicate artifacts |
| MIR-F-010 | IT | `20_it_synthesis.log` (`test_process_meeting_state_synthesizes_when_flag_set`) | Synthesis on finalization merges per-window outputs |
| MIR-F-011 | IT | `20_it_synthesis.log` (`test_synthesize_and_persist_writes_artifacts_with_lineage`) | Synthesis preserves source-window references |
| MIR-F-012 | IT | `20_it_fallback.log` (`test_failing_plugin_does_not_block_chain_siblings_mir_r_004`); also `test_pipeline_keeps_running_when_every_other_plugin_explodes` | Graceful degrade — pipeline returns instead of raising |

## Data + persistence requirements

| Req | Method | Evidence | Notes |
|---|---|---|---|
| MIR-D-001 | AT | `30_db_checks.txt` (`test_record_and_list_intent_windows`, `test_record_intent_window_round_trips_typed_score`) | `intent_windows` schema with temporal bounds |
| MIR-D-002 | AT | `30_db_checks.txt` (`test_record_and_list_intent_windows` round-trips intent_scores) | `intent_window_scores` per-label rows |
| MIR-D-003 | AT | `30_db_checks.txt` (`test_record_and_list_plugin_runs`, `test_record_plugin_run_round_trips_typed_record`) | `plugin_runs` table with status |
| MIR-D-004 | AT | `30_db_checks.txt` (`test_record_and_list_artifacts_with_lineage`, `test_record_artifact_with_lineage_packs_window_and_plugin_run_sources`) | `artifacts` + `artifact_sources` lineage |
| MIR-D-005 | MT | `31_migration_checks.txt` (re-run construction PASS) | Idempotent `CREATE TABLE IF NOT EXISTS` migrations + version 10 |
| MIR-D-006 | IT | `30_db_checks.txt` (`test_back_compat_meeting_without_intent_data_loads_clean_mir_d_006`) | Empty-meeting reads return [] safely |

## API + UX requirements

| Req | Method | Evidence | Notes |
|---|---|---|---|
| MIR-A-000 | AT | `40_api_checks.log` (timeline + plugin-runs + artifacts endpoints all green via `TestClient`) | Web is the flagship surface for new MIR-01 functionality |
| MIR-A-001 | AT | `40_api_checks.log` (`test_intent_timeline_endpoint_returns_windows_and_transitions`) | `GET /api/meetings/{id}/intent-timeline` |
| MIR-A-002 | AT | `40_api_checks.log` (`test_plugin_runs_endpoint_returns_persisted_runs`) | `GET /api/meetings/{id}/plugin-runs` |
| MIR-A-003 | MT | `41_cli_checks.log` (`test_run_intel_command_route_dry_run_emits_route_json`, `--help` shows `--route-dry-run`) | `holdspeak intel route --route-dry-run` |
| MIR-A-004 | MT | `41_cli_checks.log` (`test_run_intel_command_reroute_persists_intent_window`, `--help` shows `--reroute`) | `holdspeak intel route --reroute` with `--profile` override |
| MIR-A-005 | AT | `40_api_checks.log` (timeline payload includes `intent_scores` per label) | Confidence values in API payload |
| MIR-A-006 | IT | `40_api_checks.log` (`test_intent_*_invokes_callback_*` cases for control / profile / override / preview) | Web controls reach `on_*` callbacks with the right shape |
| MIR-A-007 | MT | `99_phase_summary.md` (no new TUI work blocked phase exit) | TUI may lag, MUST NOT block |
| MIR-A-008 | MT | `99_phase_summary.md` (story-08 evidence emphasizes the API as flagship; CLI subcommand additions explicitly deferred) | Docs lead with web flows |

## Reliability + performance

| Req | Method | Evidence | Notes |
|---|---|---|---|
| MIR-R-001 | MT | `50_perf.txt` (lexical scorer median 0.0096ms over 100 windows; 300ms gate trivially met) | Routing-per-window SHOULD ≤ 300ms median |
| MIR-R-002 | IT | `10_ut_router.log` (`test_plugin_host_metrics_count_success_error_timeout_and_deduped`); `holdspeak/plugins/host.py::execute` uses ThreadPoolExecutor + `future.result(timeout=...)` | Per-plugin timeout enforced |
| MIR-R-003 | IT | `10_ut_router.log` (`test_plugin_host_register_and_execute_success` covers `execution_mode='deferred'` queueing — see `tests/unit/test_plugin_host.py`) | Heavy plugins enqueue via `_is_deferred_plugin` |
| MIR-R-004 | IT | `20_it_fallback.log` (all 3 cases) | One plugin failure does not block others |
| MIR-R-005 | IT | `20_it_routing.log` (`test_meeting_session_stop_*` 3 cases all pass with `@pytest.mark.timeout(15)`) | Stop persists partial progress without deadlock |

## Observability + safety

| Req | Method | Evidence | Notes |
|---|---|---|---|
| MIR-O-001 | LG | `60_logs_sample.txt` (start + finish events both carry `meeting_id`/`window_id`/`plugin_id`/`intent_set`) | Structured log fields present |
| MIR-O-002 | LG | `61_metrics_sample.txt` (`router counters: {'routed_windows': 2, 'dropped_windows': 0}` after two dispatches) | Router counters increment |
| MIR-O-003 | LG | `61_metrics_sample.txt` (`host metrics: {'runs_total': 10, 'success': 4, 'error': 2, 'deduped': 4, ...}` after two dispatches) | Host counters per status |
| MIR-S-001 | UT | `10_ut_security.log` (`test_capability_mismatch_blocks_plugin_execution`) | Capability checks gate execution |
| MIR-S-002 | UT | `10_ut_security.log` (`test_actuator_plugins_blocked_by_default`) | Actuators disabled by default |
| MIR-S-003 | LG | `60_logs_sample.txt` (`'api_key' appears in redacted_keys, never in context_keys`) | Logs avoid raw secret values |

## Outcome

Every `MIR-*` requirement has a passing artifact in this bundle. No
items are flagged as failed or deferred. Phase exit conditions in spec
§11 (Definition of Done) are satisfied (see `99_phase_summary.md`).
