# DIR-01 evidence bundle

**Phase:** DIR-01 (Dictation Intent Routing)
**Captured:** 2026-04-25
**Reference Mac:** arm64 macOS 26.2
**Commit:** 56618f342c29834d18e6be674a9ab5a95bde03d9
**Branch:** main

## File index

- `00_manifest.md` (this file)
- `01_env.txt` — host `uname -a`, macOS version, Python + uv versions.
- `02_git_status.txt` — working tree state + HEAD commit at capture.
- `03_traceability.md` — every DIR-* requirement → evidence line + status.
- `10_ut_pipeline.log` — `pytest -v tests/unit/test_dictation_pipeline.py`.
- `10_ut_router.log` — `pytest -v tests/unit/test_dictation_intent_router.py`.
- `10_ut_enricher.log` — `pytest -v tests/unit/test_dictation_kb_enricher.py`.
- `10_ut_blocks.log` — `pytest -v tests/unit/test_dictation_blocks.py`.
- `10_ut_runtime.log` — `pytest -v tests/unit/test_dictation_runtime.py`.
- `10_ut_config.log` — `pytest -v tests/unit/test_config.py -k Dictation`.
- `10_ut_security.log` — security-tagged subset of the blocks suite (YAML safe_load + template shape rejection).
- `12_structured_output_validation.log` — `pytest -v tests/unit/test_dictation_grammars.py` (GBNF + outlines compile + cross-backend equivalence).
- `40_cli_checks.log` — `pytest -v tests/unit/test_dictation_cli.py` (every CLI subcommand happy + sad path, including the no-LLM dry-run fallback).
- `41_doctor_checks.log` — `pytest -v tests/unit/test_doctor_command.py -k dictation` (DIR-DOC-001..003).
- `60_logs_sample.txt` — sample of the DIR-O-001 `dictation_pipeline_run` structured log line emitted by the controller's `on_run` callback.
- `61_runtime_trace.txt` — `holdspeak dictation runtime status` + `holdspeak dictation dry-run` against the real `Qwen3-8B-MLX-4bit` model on the reference Mac, plus `holdspeak doctor` with `pipeline.enabled = true`.
- `99_phase_summary.md` — DIR-01 closing summary, deferred items, DIR-02 punts.

## Deferred (with rationale)

- **DIR-R-003** — cold-start hard-cap on `max_total_latency_ms × 5`. Executor exposes `total_elapsed_ms`; controller logs it. Hard kill ships once a perception baseline exists (no measurement gate per the 2026-04-25 amendment).
- **DIR-O-002** — runtime counters (`model_loads`, `classify_calls`, `classify_failures`, `constrained_retries`). DIR-O-001 per-run line covers first-launch verification; counters are a sustained-load concern, deferred to DIR-02.
- **`llama_cpp` end-to-end leg** — reference Mac runs the `mlx` primary per the 2026-04-25 model decision. Unit + integration harnesses are in place; flipping the integration test to active is a `holdspeak[dictation-llama]` install + GGUF download away.

