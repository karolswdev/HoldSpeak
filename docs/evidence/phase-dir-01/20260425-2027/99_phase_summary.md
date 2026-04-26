# DIR-01 Phase Summary

**Phase:** Dictation Intent Routing
**Status:** complete
**Closing commit:** see `02_git_status.txt`
**Reference Mac:** Apple Silicon, macOS 26 (Darwin 25.2.0)

## What shipped

The DIR-01 phase delivers a real-time, on-device, LLM-driven
transcript enrichment pipeline for the voice-typing path, behind a
single config flag (`dictation.pipeline.enabled = false` by
default — DIR-C-001).

Surface area:

- **Contracts** (HS-1-02) — `Utterance`, `IntentTag`, `StageResult`,
  `Transducer` Protocol; `kind="transducer"` accepted by the
  plugin-registry contract.
- **Pipeline executor** (HS-1-03) — ordered, error-isolating
  in-process executor with per-stage timing, ring buffer for the
  last N runs (DIR-F-009), and an I/O-free `on_run` callback seam
  the controller uses for DIR-O-001 logging.
- **Pluggable LLM runtime** (HS-1-04) — `LLMRuntime` Protocol with
  two concrete backends (`mlx-lm` with `Qwen3-8B-MLX-4bit` on
  Apple Silicon, `llama-cpp-python` with
  `Qwen2.5-3B-Instruct-Q4_K_M` cross-platform), `auto`-resolution
  with deterministic test seams, lazy backend imports, and a
  shared `StructuredOutputSchema` compiler emitting GBNF
  (`llama_cpp`) and outlines-style JSON-schema (`mlx`) from the
  same `BlockSet`.
- **Block-config loader** (HS-1-05) — YAML schema with
  `safe_load` (DIR-S-001), strict template shape validation
  (DIR-S-002 — only `{name}` and `{a.b.c}` placeholders),
  project-replace-global semantics (DIR-F-008), and the
  `LoadedBlocks → BlockSet` bridge to the constraint compiler.
- **Built-in stages** (HS-1-06) — `IntentRouter` (`requires_llm=True`)
  with one-retry-then-no-match (DIR-F-004) and full-taxonomy
  union scoring (DIR-F-005); `KbEnricher` (`requires_llm=False`,
  no runtime arg per DIR-R-004) with custom dict-only template
  resolver (no `str.format` reachable) gated on `matched + threshold`
  (DIR-F-006) and DIR-F-007 unresolved-placeholder skip.
- **Controller wiring** (HS-1-07) — pipeline plumbed between
  `text_processor.process` and `typer.type_text` in
  `_on_hotkey_release`. Disabled-state byte-identical guarantee
  enforced by lazy-import discipline; build failures sticky for
  the controller lifetime (recovery seam:
  `apply_runtime_config()`); DIR-O-001 structured log line emitted
  controller-side so the executor stays I/O-free.
- **CLI** (HS-1-08) — `holdspeak dictation` with five
  subcommands (`dry-run`, `blocks ls/show/validate`,
  `runtime status`); usable without an LLM backend installed
  (no-LLM `dry-run` runs with `intent-router` skipped, so block
  authors can validate YAML on machines without
  `mlx-lm`/`llama-cpp-python`). Pipeline assembly lifted into
  `plugins/dictation/assembly.py` so the controller, CLI, and
  doctor share one builder.
- **Doctor** (HS-1-09) — two new checks
  (`LLM runtime`, `Structured-output compilation`) honoring
  DIR-DOC-003 (never `FAIL`, even when DIR-01 is disabled).
- **DoD sweep** (HS-1-11) — config-load validation of stage IDs
  (DIR-C-002), evidence bundle, real-model end-to-end exercise
  on the reference Mac.

## Test posture at close

- Full sweep: 906 passed, 13 skipped, 1 pre-existing hardware-only
  Whisper-loader fail in `tests/e2e/test_metal.py` (recorded as the
  baseline since HS-1-03; unrelated to DIR-01).
- Per-area logs in `10_ut_*.log`, `12_*`, `40_*`, `41_*`.
- Real-model dry-run + doctor run on Apple Silicon with
  `Qwen3-8B-MLX-4bit` resident: see `61_runtime_trace.txt`.

## Phase exit criteria — verdict

| Criterion | Status |
|---|---|
| Every DIR-* requirement has passing verification (or documented gap) | **green** (see `03_traceability.md`) |
| Evidence bundle non-empty per spec §11.2 | **green** (this folder) |
| End-to-end on the reference Mac with `mlx` + `Qwen3-8B-MLX-4bit` | **green** (`61_runtime_trace.txt`) |
| Disabled-state byte-identical | **green** (`tests/unit/test_controller.py::test_dictation_disabled_path_is_byte_identical_and_does_not_build_pipeline`) |
| Doctor reports the new checks cleanly in both states | **green** (`41_doctor_checks.log` + `61_runtime_trace.txt`) |
| Phase summary lists known gaps + DIR-02 punts | this document |

## Deferred to DIR-02

1. **DIR-R-003 cold-start hard-cap.** The executor exposes
   `total_elapsed_ms` and the controller logs it. The hard kill on
   `max_total_latency_ms × 5` ships once a perception baseline
   exists. No measurement gate per the 2026-04-25 amendment.
2. **DIR-O-002 runtime counters** (`model_loads`, `classify_calls`,
   `classify_failures`, `constrained_retries`). DIR-O-001 per-run
   line covers first-launch verification; counters are a
   sustained-load concern.
3. **`llama_cpp` end-to-end leg.** Reference Mac runs the `mlx`
   primary per the 2026-04-25 model decision. Unit + integration
   harnesses are in place; flipping the integration test to active
   is a `holdspeak[dictation-llama]` install + GGUF download away.
4. **Project-context plumbing into the dictation `Utterance`.**
   `utt.project = None` for now; `kb-enricher` skips on missing
   `{project.*}` placeholders gracefully (DIR-F-007).
5. **Multi-utterance state**, **cloud router fallback**,
   **shared model file with `intel.py`**, **web block editor** —
   all explicitly out-of-scope per spec §3.2.

## Decision log (key)

- 2026-04-25 — Pipeline off by default (DIR-C-001). Owner: agent.
- 2026-04-25 — Two pluggable backends behind `LLMRuntime`. Owner:
  agent + user.
- 2026-04-25 — `mlx` primary `Qwen3-8B-MLX-4bit`. Owner: user.
- 2026-04-25 — Constrained decoding: GBNF (`llama_cpp`) +
  outlines-style (`mlx`) emitted from the same `BlockSet`.
- 2026-04-25 — No pre-shipping measurement; DIR-01 banks on the
  chosen models and ships on perception alone. (Drops HS-1-01 +
  HS-1-10.)
