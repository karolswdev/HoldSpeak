# Evidence — HS-3-05: DIR-R-003 cold-start hard-cap

- **Phase:** 3 (Dictation Loop Closure)
- **Story:** HS-3-05
- **Captured at HEAD:** `d7cbf34` (pre-commit)
- **Date:** 2026-04-26

## What shipped

### Cold-start cap in `CountingRuntime` (`runtime_counters.py`)

- New constructor kwargs `warm_on_start: bool` and `cold_start_cap_ms: int | None`. When `warm_on_start=True`, `_cold_start_done` starts True so the cap check is skipped (the model is already warm).
- `classify()` now:
  1. If `_disabled` is set, raise `LLMRuntimeDisabledError` immediately — no inner call.
  2. Time the inner call with `time.perf_counter()`.
  3. If this is the first call (cold-start) and `cap_ms` is set and `elapsed > cap`, flip `_disabled=True`, set the session-level disabled flag, log a structured WARN, and raise `LLMRuntimeDisabledError`.
- New module exception `LLMRuntimeDisabledError` (subclass of `RuntimeError`) — caught by IntentRouter's existing `except Exception` handler so the pipeline falls back to a no-match warning rather than raising.

### Process-scoped session state

- Added `_SESSION_DISABLED` + `_SESSION_DISABLED_REASON` module-level state (locked under the same `_LOCK` as the counters).
- `_set_session_disabled(reason)` flips the flag from the wrapper.
- `get_session_status()` returns `{"llm_disabled_for_session": bool, "disabled_reason": str | None}` — read by doctor.
- `reset_counters()` zeros the disabled flag too (for test isolation).

### Wiring

- `build_runtime` in `runtime.py` gained a `cold_start_cap_ms: int | None = None` kwarg, threaded through to the wrapper.
- `_try_build_runtime` in `assembly.py` computes `cold_start_cap_ms = cfg.pipeline.max_total_latency_ms * 5` (DIR-R-003 multiplier) and passes it to the factory.

### Doctor

- `_check_dictation_runtime_counters` now reads `get_session_status()` alongside `get_counters()`. When `llm_disabled_for_session=True` the check status flips from PASS to WARN with a remediation hint pointing the user at restarting `holdspeak` or raising `max_total_latency_ms` / `warm_on_start: true`.

## Test output

### Targeted

```
$ uv run pytest tests/integration/test_dictation_cold_start_cap.py tests/unit/test_runtime_counters.py tests/unit/test_doctor_command.py --timeout=30 -v
... (output snipped)
2 + 15 + 26 = 43 passed
```

#### 6 new cold-start unit tests in `test_runtime_counters.py`

- `test_cold_start_under_cap_does_not_disable` — fast call stays clean.
- `test_cold_start_breach_disables_session_and_raises` — slow first call flips `_disabled`, raises `LLMRuntimeDisabledError`.
- `test_subsequent_classify_short_circuits_without_calling_inner` — after breach, `inner.classify_calls` stops advancing.
- `test_warm_on_start_skips_cold_start_cap` — `warm_on_start=True` bypasses the cap regardless of latency.
- `test_no_cap_means_no_disable_even_on_slow_first_call` — `cold_start_cap_ms=None` disables the check.
- `test_cold_start_failure_marks_done_but_not_disabled` — a *raising* first call counts as cold-start-done but doesn't trigger the cap-breach disable path (only slow successes count, not failures).

#### 2 new integration tests in `test_dictation_cold_start_cap.py`

- `test_pipeline_runs_after_cold_start_breach_without_raising` — slow stub runtime trips the cap on utterance #1; pipeline returns a non-empty `final_text` (intent-router's exception handler treats `LLMRuntimeDisabledError` as a no-match), session is now disabled, utterance #2 short-circuits without re-invoking `inner.classify`.
- `test_doctor_counters_warn_after_cold_start_breach` — `_check_dictation_runtime_counters` flips to WARN and includes the breach reason + a remediation `fix` field.

### Full regression

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
... (output snipped)
1007 passed, 13 skipped in 16.50s
```

Pass delta vs. HS-3-04 baseline (999 passed): **+8** (6 unit + 2
integration). 13 skipped is unchanged.

## Practical effect

If the user's first hotkey-press of a `holdspeak` session takes
more than `max_total_latency_ms × 5` (default 600ms × 5 = 3
seconds) to classify, the LLM stage gives up for that session:
subsequent utterances type cleanly via the lexical (no-LLM) path,
and `holdspeak doctor` shows a WARN line explaining what happened
with a one-line remediation. The disable is session-scoped, so a
fresh `holdspeak` launch retries.

This protects "useful" from a misconfigured Metal wheel (the
DIR-01 §12 risk #2 most-likely-real-world failure) or an
under-provisioned machine: dictation never hangs because the LLM
load went sideways.

## Deviations from story scope

- The wrapper logs the disable AND raises `LLMRuntimeDisabledError`,
  rather than "returning a short-circuit" sentinel. The exception
  flows through the IntentRouter's existing `except Exception`
  handler cleanly; `intent-router` warns and returns a no-match.
  This is functionally equivalent to a sentinel and avoids touching
  `IntentRouter` source.
- Did **not** add early-detection in `IntentRouter` (e.g., short-circuit
  out of the 2-attempt retry loop on `LLMRuntimeDisabledError`). After
  a breach, every utterance still goes through 2 wasteful wrapper
  calls that fail fast. Acceptable cost (the wrapper raises before
  invoking the inner runtime, so wall time is microseconds), and
  keeps `IntentRouter` untouched. If profiling later shows it
  matters, a one-line `if isinstance(exc, LLMRuntimeDisabledError):
  break` patch in `IntentRouter._classify_with_retries` is enough.
- Story's "warm-path runaway" was explicitly deferred — confirmed
  out-of-scope.

## Out-of-scope (deferred per story)

- Persistent disable across launches.
- User-visible UI signal — doctor output is sufficient.
- Warm-path runaway detection.
