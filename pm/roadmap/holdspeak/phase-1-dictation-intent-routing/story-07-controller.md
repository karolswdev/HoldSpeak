# HS-1-07 — Step 6: Controller wiring

- **Project:** holdspeak
- **Phase:** 1
- **Status:** done
- **Depends on:** HS-1-02 (contracts), HS-1-03 (pipeline executor), HS-1-04 (LLM runtime), HS-1-05 (blocks loader), HS-1-06 (built-in stages)
- **Unblocks:** HS-1-08 (CLI dry-run shares the same builder), HS-1-09 (doctor surfaces what the controller resolves), HS-1-11 (DoD)
- **Owner:** unassigned

## Problem

DIR-01 §6.1 + §6.3 + §12.7 call for the `DictationPipeline` to be
invoked in `holdspeak/controller.py` between
`text_processor.process` and `typer.type_text`. The previous five
stories shipped every component the controller needs (executor,
runtime factory, blocks loader, both built-in stages); this story
assembles them and turns the live voice-typing path into a real
pipeline call — gated by `dictation.pipeline.enabled` (DIR-C-001),
which defaults to `False`.

The hard rule is the **byte-identical disabled path** (phase exit
criterion #4 / spec §14): with `dictation.pipeline.enabled = false`,
the typer MUST receive exactly what `text_processor.process`
returned, no dictation modules MAY be imported, and no observable
side effect of the dictation feature MAY appear. The wiring is the
first DIR-01 commit that touches user-visible behavior, so the
guard has to be airtight.

When enabled, the controller MUST:

- Build the runtime via `runtime.build_runtime(**runtime_kwargs)`.
- Load blocks via `resolve_blocks(global, project_root)`.
- Build `IntentRouter(runtime, blocks)` + `KbEnricher(blocks)` once
  per controller (singletons per process per spec §7.1's "no
  per-utterance reinstantiation").
- Wrap them in `DictationPipeline([...], enabled=True,
  llm_enabled=True, on_run=<emit DIR-O-001 log line>)`.
- Pass an `Utterance(raw_text=processed, audio_duration_s,
  transcribed_at, project=None)` through `pipeline.run(utt)` and
  type `result.final_text`.

`project=None` is the DIR-01 default — `ProjectContext` plumbing for
dictation is a DIR-02 concern; HS-1-07 does not wire
`project_detector` into the dictation path. `kb-enricher` already
handles a `None` project gracefully (returns the input text + a
warning when any `{project.*}` placeholder is referenced).

Cold-start failures (model file missing, runtime extra not
installed, blocks YAML malformed) MUST NOT crash the live typing
path. The controller falls back to the original
`text_processor.process` text and logs the failure once; the
disabled-state typing behavior is the safe fallback.

## Scope

- **In:**
  - `holdspeak/controller.py`:
    - New `_dictation_pipeline` instance attribute (lazy; `None`
      until first utterance with `pipeline.enabled = true`).
    - New `_dictation_pipeline_failed` flag — once a build attempt
      raises, the controller stops retrying for the lifetime of the
      controller (or until `apply_runtime_config` is called).
    - New private builder method (`_build_dictation_pipeline`)
      lazy-imports the dictation modules and returns the
      `DictationPipeline` (or `None` on disabled / build failure).
    - New `_maybe_run_dictation_pipeline(text, *, audio_duration_s,
      transcribed_at)` invoked between `text_processor.process` and
      `typer.type_text` inside `_on_hotkey_release.transcribe_and_type`.
      Returns the (possibly enriched) text. On any unexpected
      exception, returns the input text unchanged (defense in depth
      on top of the pipeline executor's own error isolation).
    - `apply_runtime_config()` invalidates the cached pipeline so
      config edits to `dictation.*` take effect on the next utterance.
    - DIR-O-001 emitter in `_emit_pipeline_run` callback —
      structured log line containing stage IDs, per-stage
      `elapsed_ms`, intent tag, warnings.
  - `tests/unit/test_controller.py` — new cases:
    - `test_dictation_disabled_path_is_byte_identical_and_no_pipeline_imported`
      — with default config (`pipeline.enabled = false`), typer
      receives `text_processor.process` output verbatim and the
      `holdspeak.plugins.dictation.pipeline` module is **not**
      present in `sys.modules` after the utterance.
    - `test_dictation_enabled_runs_pipeline_and_types_final_text`
      — monkeypatch the builder to inject a fake pipeline whose
      `run()` returns a `PipelineRun` with `final_text=
      "ENRICHED"`; assert typer receives `"ENRICHED"`.
    - `test_dictation_pipeline_build_failure_falls_back_to_processed_text`
      — builder raises; typer receives the original
      `text_processor.process` output; controller logs but does not
      retry (within the same controller lifetime).
    - `test_dictation_pipeline_run_exception_falls_back_to_processed_text`
      — fake pipeline's `run()` raises; typer receives the original
      processed text.
    - `test_apply_runtime_config_invalidates_dictation_pipeline`
      — first utterance builds the pipeline; `apply_runtime_config()`
      drops the cache; next utterance triggers a rebuild.
- **Out:**
  - CLI `holdspeak dictation dry-run` (HS-1-08).
  - Doctor checks `LLM runtime` / `Structured-output compilation`
    (HS-1-09).
  - `web_server.py` read-only API for the latest pipeline run
    (DIR-01 §6.3 #4 — deferred to HS-1-11 / HS-1-08 follow-up; not
    required for the live-typing path).
  - Plumbing `ProjectContext` from `project_detector` into the
    dictation `Utterance` — DIR-02. `utt.project = None` for now;
    `kb-enricher` already DIR-F-007-skips on missing
    `{project.*}` placeholders.
  - `max_total_latency_ms` enforcement (DIR-R-003) — exposed by the
    executor as `total_elapsed_ms`, but the policy hook is
    intentionally deferred (no real-world data yet to justify a
    hard kill on the live path).

## Acceptance criteria

- [x] `holdspeak/controller.py` invokes the dictation pipeline
      between `text_processor.process` and `typer.type_text` when
      `dictation.pipeline.enabled = true`, and is a no-op
      (importing nothing from `holdspeak.plugins.dictation`) when
      `pipeline.enabled = false`.
- [x] Disabled-state byte-identical test passes
      (`test_dictation_disabled_path_is_byte_identical_and_no_pipeline_imported`).
- [x] Enabled-state happy-path test passes
      (`test_dictation_enabled_runs_pipeline_and_types_final_text`).
- [x] Build-failure fallback test passes
      (`test_dictation_pipeline_build_failure_falls_back_to_processed_text`).
- [x] Run-time exception fallback test passes
      (`test_dictation_pipeline_run_exception_falls_back_to_processed_text`).
- [x] Cache-invalidation test passes
      (`test_apply_runtime_config_invalidates_dictation_pipeline`).
- [x] DIR-O-001 emitter writes a single structured log line per
      run (stage_ids, elapsed_ms map, intent.matched + block_id,
      warnings count, total_elapsed_ms). Verified by inspecting the
      record list captured in
      `test_dictation_enabled_runs_pipeline_and_types_final_text`.
- [x] `uv run pytest -q tests/unit/test_controller.py` → all green.
- [x] Full regression: 882 passed, 13 skipped, 1 pre-existing
      hardware-only Whisper-loader fail in
      `tests/e2e/test_metal.py::TestWhisperTranscription::test_model_loads`.

## Test plan

- **Unit:** `tests/unit/test_controller.py` — the five new cases
  above, plus the four pre-existing controller cases stay green.
- **Regression:** `uv run pytest -q tests/`.
- **Manual:** None (HS-1-08 CLI + HS-1-11 DoD cover the manual
  end-to-end path against a real model).

## Notes / open questions

- Lazy-import discipline matters for the byte-identical guarantee:
  the builder method imports
  `holdspeak.plugins.dictation.{pipeline,runtime,blocks,builtin.*}`
  inside the function body, never at module top. The disabled
  test asserts `'holdspeak.plugins.dictation.pipeline' not in
  sys.modules` after a full utterance round-trip.
- Build failures are sticky for the controller's lifetime, not the
  process's: if `apply_runtime_config()` runs (e.g. user toggles
  the feature in settings), the cache + failure flag are both
  cleared and the next utterance retries the build. This is the
  natural recovery seam.
- `Utterance.project = None` is the DIR-01 default. `kb-enricher`'s
  resolver treats unresolved `{project.*}` as a no-op (DIR-F-007),
  so a block authored for a project that uses `{project.name}`
  simply skips injection until DIR-02 wires the context through.
- The `on_run` callback emits a structured `logging` line at INFO.
  Keeping it controller-side (not executor-side) preserves the
  HS-1-03 invariant that the executor is I/O-free, and lets
  HS-1-11 swap the destination (e.g. JSON file sink) without
  touching the pipeline.
- `max_total_latency_ms` enforcement (DIR-R-003) remains deferred:
  the executor records `total_elapsed_ms`, the controller logs it,
  and a future story can layer a hard kill once we have a real
  latency baseline. No measurement gate per the 2026-04-25
  amendment, so we don't pre-build the policy.
