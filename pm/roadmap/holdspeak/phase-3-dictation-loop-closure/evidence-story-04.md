# Evidence — HS-3-04: DIR-O-002 runtime counters

- **Phase:** 3 (Dictation Loop Closure)
- **Story:** HS-3-04
- **Captured at HEAD:** `505794f` (pre-commit)
- **Date:** 2026-04-26

## What shipped

### Counter module (`holdspeak/plugins/dictation/runtime_counters.py`)

- Process-scoped, threadsafe counter state for the four DIR-O-002 fields: `model_loads`, `classify_calls`, `classify_failures`, `constrained_retries`.
- Module-level singleton guarded by `threading.Lock`. `get_counters()` returns an int snapshot; `reset_counters()` zeros for test isolation; `note_constrained_retry()` is the public knob a future runtime would call when re-attempting under tightened structured-output constraints.
- `CountingRuntime` wraps any `LLMRuntime`-shaped object and increments counters at the right boundaries:
  - First successful `load()` → `model_loads += 1` (subsequent calls no-op the counter).
  - Every `classify()` → `classify_calls += 1`; an exception out of `inner.classify()` advances `classify_failures` before re-raising.
  - `__getattr__` delegates unknown attributes to the inner runtime so introspection (e.g. `rt.kwargs` on test stubs) keeps working through the wrapper.

### Wiring (`holdspeak/plugins/dictation/runtime.py`)

- `build_runtime()` now returns `CountingRuntime(inner)` instead of the raw inner. Both backends (`mlx`, `llama_cpp`) get counters for free without needing to know about them. The counter wrap is a one-line addition at the bottom of `build_runtime`.

### Doctor (`holdspeak/commands/doctor.py`)

- New `_check_dictation_runtime_counters(config)` returning a `DoctorCheck`:
  - PASS with `"disabled"` detail when `dictation.pipeline.enabled is False`.
  - PASS with `"model_loads=N classify_calls=N classify_failures=N constrained_retries=N"` otherwise.
- Inserted at the end of the dictation block in `collect_doctor_checks()` (after constraint compile) so the section reads: `Project context → LLM runtime → Structured-output compilation → LLM runtime counters`.

## Test output

### Targeted

```
$ uv run pytest tests/unit/test_runtime_counters.py tests/unit/test_doctor_command.py --timeout=30 -q
..................................                                       [100%]
34 passed in 0.25s
```

The 9 counter tests cover initial state, load increments (single-shot), classify increments, failure path, `note_constrained_retry`, reset, attribute delegation, info delegation, and end-to-end via `build_runtime`. The 2 new doctor tests cover the disabled-skip path and the snapshot-reporting path.

### Discovered + fixed: pre-existing test breakage

After wrapping `build_runtime`'s output in `CountingRuntime`, two
existing tests in `tests/unit/test_dictation_runtime.py` failed
because they introspected `.kwargs` on the returned runtime and the
wrapper didn't expose it:

```
FAILED tests/unit/test_dictation_runtime.py::test_build_runtime_passes_mlx_kwargs
FAILED tests/unit/test_dictation_runtime.py::test_build_runtime_passes_llama_kwargs
```

Fix: added `__getattr__` to `CountingRuntime` so unknown attributes
delegate to the inner runtime. This is the right semantics anyway —
the wrapper is meant to be transparent. Re-run: both tests pass.
Documented inline in the wrapper class.

### Full regression

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
... (output snipped)
999 passed, 13 skipped in 15.77s
```

Pass delta vs. HS-3-03 baseline (988 passed): **+11** (9 counter
unit + 2 doctor unit). 13 skipped is unchanged.

## On `constrained_retries`

Both shipped runtimes (`runtime_mlx.py`, `runtime_llama_cpp.py`) use
single-shot constrained decoding (outlines for MLX, GBNF for
llama_cpp). Neither has a retry path today, so
`constrained_retries` will read 0 in dogfood. This is intentional:
the counter surface is in place per spec §9.7 so a future runtime
(or LLM-driven repair pass) can advance it without coupling to the
counter module's internals — it just calls
`note_constrained_retry()`.

## Practical effect

`holdspeak doctor` now reports a one-line LLM-counter line. In
dogfood: launch `holdspeak`, hold the hotkey once, then re-run
`doctor` — `classify_calls` should be ≥ 1 (assuming the LLM stage
actually fired; if it stayed 0, that's a signal the pipeline isn't
exercising the runtime, which is exactly the diagnostic this
counter is for).

## Deviations from story scope

- The story stub said the counter object lives "either at the
  `LLMRuntime` Protocol level via a wrapper or in each concrete
  runtime, whichever keeps the implementation under ~50 lines."
  Picked the wrapper. Concrete runtimes need zero changes; counter
  module is ~120 lines including docstrings, ~50 LOC of actual code.
- `__getattr__` delegation was not in the story stub but emerged
  necessary for backward compat with existing runtime tests. Pure
  win — the wrapper is now genuinely transparent.

## Out-of-scope (deferred per story)

- Counter persistence across restarts.
- HTTP/web endpoint for counters — explicitly deferred to the web
  flagship runtime phase.
- Per-stage timing histograms (DIR-O-001 territory, separate concern).
