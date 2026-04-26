# DIR-* requirement → evidence traceability

| Requirement | Method | Evidence | Status |
|---|---|---|---|
| DIR-F-001 | UT | `10_ut_pipeline.log` (`test_run_executes_stages_in_order`) | green |
| DIR-F-002 | UT | `10_ut_pipeline.log` (`test_run_when_disabled_returns_short_circuited_passthrough`) | green |
| DIR-F-003 | UT | `10_ut_pipeline.log` (stage exception → original text + warning) | green |
| DIR-F-004 | UT | `10_ut_router.log` (parse-failure / unknown block id retry then no-match) | green |
| DIR-F-005 | UT | `10_ut_router.log` (taxonomy union: `metadata.taxonomy_size`) | green |
| DIR-F-006 | UT | `10_ut_enricher.log` (per-block + default threshold gating) | green |
| DIR-F-007 | UT | `10_ut_enricher.log` (unresolved placeholder skip + warning; `_no_unresolved_braces_ever_typed_smoke`) | green |
| DIR-F-008 | UT | `10_ut_blocks.log` (project file fully replaces global) | green |
| DIR-F-009 | UT | `10_ut_pipeline.log` (`recent_runs` ring buffer) | green |
| DIR-F-010 | AT | `40_cli_checks.log` (`test_dry_run_prints_each_stage_when_runtime_loaded`) + `61_runtime_trace.txt` (real model) | green |
| DIR-F-011 | UT | `10_ut_runtime.log` + `40_cli_checks.log` (`llm_enabled=False` → router skipped, kb-enricher still runs) | green |
| DIR-D-001 | UT | `10_ut_blocks.log` (`version: 1` schema check) | green |
| DIR-D-002 | UT | `10_ut_blocks.log` (malformed YAML → `BlockConfigError` with file + path) | green |
| DIR-D-003 | n/a | No DB schema changes; ring buffer is in-memory (DIR-F-009) | green |
| DIR-A-001 | AT | `40_cli_checks.log` (every CLI subcommand happy + sad path) | green |
| DIR-A-003 | n/a | Spec typo — undefined in §9.3; DIR-A-001 + DIR-DOC-001..003 cover the surface | n/a |
| DIR-C-001 | UT | `10_ut_runtime.log` (`test_default_dictation_pipeline_disabled`) + `tests/unit/test_controller.py::test_dictation_disabled_path_is_byte_identical_and_does_not_build_pipeline` | green |
| DIR-C-002 | UT | `10_ut_config.log` (`TestDictationPipelineValidation::test_unknown_stage_id_rejected`) | green |
| DIR-DOC-001 | AT | `41_doctor_checks.log` (`test_dictation_runtime_check_*`) + `61_runtime_trace.txt` (real `holdspeak doctor` output) | green |
| DIR-DOC-002 | AT | `41_doctor_checks.log` (`test_dictation_compile_check_*`) + `61_runtime_trace.txt` | green |
| DIR-DOC-003 | AT | `41_doctor_checks.log` (`test_dictation_*_check_pass_when_pipeline_disabled` returns PASS) | green |
| DIR-R-001 | MT | `61_runtime_trace.txt` (real-model dry-run; perception is the user's call) | green |
| DIR-R-003 | n/a | **Deferred to DIR-02.** Executor exposes `total_elapsed_ms`; controller logs it. No measurement gate per 2026-04-25 amendment — the hard kill ships when there's a real latency baseline. | deferred |
| DIR-R-004 | UT | `10_ut_enricher.log` (`test_kb_enricher_constructor_takes_no_runtime`; `requires_llm == False`) | green |
| DIR-O-001 | LG | `60_logs_sample.txt` (controller-side `dictation_pipeline_run` structured log line; verified by `tests/unit/test_controller.py::test_dictation_enabled_runs_pipeline_and_types_final_text`) | green |
| DIR-O-002 | n/a | **Deferred to DIR-02.** Counters (`model_loads`, `classify_calls`, `classify_failures`, `constrained_retries`) are a sustained-load concern; DIR-O-001 per-run line covers first-launch verification. | deferred |
| DIR-S-001 | UT | `10_ut_security.log` (PyYAML safe_load rejects `!!python/object`) | green |
| DIR-S-002 | UT | `10_ut_security.log` (templates rejected on format specs / conversions / method calls / item access / arithmetic) | green |
| DIR-S-003 | MT | `61_runtime_trace.txt` (no network calls observed during the real-model dry-run; `runtime_mlx.py` and `runtime_llama_cpp.py` make no `urllib`/`socket`/`requests` calls) | green |
