# HS-1-11 — Step 10: Full regression + DoD

- **Project:** holdspeak
- **Phase:** 1
- **Status:** done
- **Depends on:** HS-1-02..HS-1-09 (every shipping DIR-01 story)
- **Unblocks:** DIR-02 phase kickoff
- **Owner:** unassigned

## Problem

Per spec §14 Definition of Done + §11.2 Required Files, DIR-01 ships
when:

1. Every `DIR-*` requirement has passing verification evidence (or a
   documented gap with a clear DIR-02 punt).
2. The required evidence files exist and are non-empty.
3. The pipeline runs end-to-end on the reference Mac with the `mlx`
   `Qwen3-8B-MLX-4bit` primary; the `llama_cpp` Qwen2.5-3B-Q4_K_M
   path also runs end-to-end.
4. With `dictation.pipeline.enabled = false`, all baseline behavior
   is byte-identical to pre-DIR-01.
5. `holdspeak doctor` cleanly reports the new checks in both
   enabled and disabled states.
6. Phase summary lists known gaps and explicitly defers DIR-02
   items.

This story is the consolidating sweep: close the **one** small spec
gap that hasn't been covered yet (DIR-C-002, config-load validation
of stage IDs), run the full regression with per-area logs tee'd
into the evidence bundle, exercise `dictation dry-run` against the
real `Qwen3-8B-MLX-4bit` model on the reference Mac, run `holdspeak
doctor` with the pipeline enabled, and write the phase summary.

## Scope

- **In:**
  - `holdspeak/config.py` — `DictationConfigError` + a
    `__post_init__` on `DictationPipelineConfig` that rejects
    unknown stage IDs (DIR-C-002). Three new unit cases in
    `tests/unit/test_config.py::TestDictationPipelineValidation`.
  - `docs/evidence/phase-dir-01/<YYYYMMDD-HHMM>/` evidence bundle
    per spec §11.2. The required files (`00_manifest.md`,
    `01_env.txt`, `02_git_status.txt`, `03_traceability.md`, the
    `10_ut_*.log` per-area suite logs, `12_structured_output_validation.log`,
    `40_cli_checks.log`, `41_doctor_checks.log`, `60_logs_sample.txt`,
    `61_runtime_trace.txt`, `99_phase_summary.md`).
  - End-to-end model exercise: download `Qwen3-8B-MLX-4bit` to
    `~/Models/mlx/Qwen3-8B-MLX-4bit/`, write a sample global
    `~/.config/holdspeak/blocks.yaml`, flip
    `dictation.pipeline.enabled = true`, and run `uv run holdspeak
    dictation dry-run "<utterance>"`. Capture the stage-by-stage
    output into `61_runtime_trace.txt`.
  - `99_phase_summary.md` — green-state DIR-* matrix + the
    documented gaps with DIR-02 punts.
- **Out:**
  - DIR-O-002 LLM runtime counters (`model_loads`, `classify_calls`,
    `classify_failures`, `constrained_retries`) — deferred to
    DIR-02 with the rest of the observability surface. The
    DIR-O-001 per-run log line that HS-1-07 ships covers the
    "what happened" question for the live path; counters are a
    sustained-load concern, not a first-launch verification gate.
  - DIR-R-003 hard-cap enforcement on cold-start latency
    (max_total_latency_ms × 5) — the executor records
    `total_elapsed_ms`, the controller logs it, and the policy hook
    ships when there's a real latency baseline to tune against.
    No measurement gate per the 2026-04-25 amendment.
  - DIR-A-003 — referenced once in §10.2 but not defined in §9.3
    (spec typo; treated as a no-op). DIR-A-001 + DIR-DOC-001..003
    cover the CLI/doctor surface.
  - The `llama_cpp` Qwen2.5-3B-Q4_K_M end-to-end leg of phase exit
    criterion #3 — model is not installed on the reference Mac and
    DIR-01 explicitly commits to the `mlx` primary
    (2026-04-25 amendment). The `tests/integration/test_runtime_llama_cpp.py`
    harness is in place and skips cleanly; flipping it to active
    is a `holdspeak[dictation-llama]` install away.

## Acceptance criteria

- [x] DIR-C-002 enforced at config load time;
      `tests/unit/test_config.py::TestDictationPipelineValidation`
      covers default + accept-known + reject-unknown.
- [x] Full regression via `uv run pytest tests/ --timeout=30 -q`
      reports 907 passed, 12 skipped, 1 pre-existing hardware-only
      Whisper-loader fail. (Pass delta vs. HS-1-09: +3 new config
      validation cases + 1 mlx integration test now active.)
- [x] `~/Models/mlx/Qwen3-8B-MLX-4bit/` downloaded; `holdspeak
      dictation runtime status` reports `resolved backend: mlx`
      with `model: available`.
- [x] `holdspeak dictation dry-run "<text>"` runs the full pipeline
      end-to-end against the real model, prints stage-by-stage
      output, and captures the trace into
      `61_runtime_trace.txt`.
- [x] `holdspeak doctor` with `dictation.pipeline.enabled = true`
      shows `[PASS] LLM runtime: ...` and
      `[PASS] Structured-output compilation: ...` lines (captured
      in `41_doctor_checks.log`).
- [x] Disabled-state byte-identical guarantee re-verified:
      `tests/unit/test_controller.py::test_dictation_disabled_path_is_byte_identical_and_does_not_build_pipeline`
      stays green.
- [x] Evidence bundle at `docs/evidence/phase-dir-01/<YYYYMMDD-HHMM>/`
      contains every spec §11.2 file (or an entry in the manifest
      explaining why a file is intentionally absent — only DIR-O-002
      counters and DIR-R-003 hard-cap are deferred).
- [x] `99_phase_summary.md` lists the green DIR-* matrix and the
      DIR-02 punts.

## Test plan

- **Unit:** `uv run pytest tests/ --timeout=30 -q` (full sweep).
- **Per-area logs:** `uv run pytest -v tests/unit/<area>.py | tee
  docs/evidence/phase-dir-01/<ts>/10_ut_<area>.log` for each
  per-area file required by spec §11.2.
- **AT (CLI + doctor):** `uv run holdspeak dictation …` and `uv run
  holdspeak doctor` invocations with output redirected into the
  bundle.
- **MT (manual trace):** the `61_runtime_trace.txt` capture from
  the real-model dry-run.

## Bugs found and fixed during the DoD sweep

- **`runtime_mlx.py` did not expand `~` in the model path.** The
  `mlx_lm.load(...)` call received the raw `~/Models/mlx/...` string
  and tried to interpret it as an HF repo id. Fixed by passing the
  expanded `Path` for filesystem-style values; bare repo ids
  (`namespace/repo_name`) still go through unmodified.
- **`runtime_mlx.py` was bound to a removed `outlines` API.** The
  original implementation imported
  `outlines.processors.JSONLogitsProcessor`, which was renamed +
  redesigned in `outlines>=1.0` (now `OutlinesLogitsProcessor`,
  driven by `outlines.Generator(model, output_type=JsonSchema(...))`).
  Refactored `MlxRuntime.classify` to use the current
  `outlines.from_mlxlm(model, tokenizer)` +
  `Generator(omodel, output_type=JsonSchema(schema_dict))` shape;
  the test seam moved from `processor_factory + generate_fn` to a
  single `generator_factory(model, tokenizer, schema_dict) ->
  callable(prompt, max_tokens) -> str` callable. Test file
  updated; `tests/integration/test_runtime_mlx.py` is now active
  on the reference Mac and passes against the real
  `Qwen3-8B-MLX-4bit`.
- **Sample `blocks.yaml`** authored for the e2e originally used
  `mode: append` with `{raw_text}` inside the template, which
  duplicated the input text. Fixed in the user's file by switching
  to `mode: replace` (the template already encodes the full final
  text). The spec's §8.2 example has the same shape — flagging
  it here as a documentation tightening for DIR-02 (no code
  change; current `_apply_mode` is correct per the spec letter).

## Notes / open questions

- **Why DIR-O-002 isn't a phase blocker.** DIR-O-002 calls for
  runtime counters (`model_loads`, `classify_calls`,
  `classify_failures`, `constrained_retries`). The DIR-O-001
  per-run log line that HS-1-07 emits already answers the
  "did the pipeline behave?" question for first-launch
  verification; counters become valuable when there's real load to
  observe. Adding them now would be speculative scaffolding (the
  user-direction memory: bank on chosen behavior, don't pre-build
  measurement that nothing will look at). Punted to DIR-02 with
  the rest of the sustained-observability surface.
- **Why DIR-R-003 isn't a phase blocker.** The hard-cap on
  cold-start latency requires a baseline to tune against. The
  2026-04-25 amendment explicitly removed the pre-shipping
  measurement gate; layering a hard kill on `total_elapsed_ms`
  before the user has felt the real latency would be the same
  speculative scaffolding under a different name. The executor
  exposes `total_elapsed_ms` and the controller logs it, so the
  policy lands trivially in DIR-02 once there's a perception
  signal to tune to.
- **Why the `llama_cpp` end-to-end leg isn't in the bundle.** The
  reference Mac runs the `mlx` primary per the 2026-04-25 model
  decision. The `llama_cpp` Qwen2.5-3B-Q4_K_M path has full
  unit-level coverage (`tests/unit/test_dictation_runtime.py` +
  `tests/unit/test_dictation_grammars.py`) and an
  integration harness (`tests/integration/test_runtime_llama_cpp.py`)
  that skips cleanly without the extra. A future commit can flip
  the harness to active by installing `holdspeak[dictation-llama]`
  + downloading the GGUF; no DIR-01 code change needed.
