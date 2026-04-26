# HS-3-04 — DIR-O-002 runtime counters

- **Project:** holdspeak
- **Phase:** 3
- **Status:** done
- **Depends on:** HS-3-03 (`llama_cpp` leg verified so counters can be exercised on both backends)
- **Unblocks:** dogfood-friendly observability of the LLM stage
- **Owner:** unassigned

## Problem

DIR-01 §9.7 (`DIR-O-002`) calls for the LLM runtime to emit
`model_loads`, `classify_calls`, `classify_failures`, and
`constrained_retries` counters. The runtime modules
(`runtime_mlx.py`, `runtime_llama_cpp.py`) don't currently track
them, and `holdspeak doctor` doesn't surface them. Without these,
there's no quick way to tell whether the LLM stage is even being
exercised in dogfood — a cardinal "is this thing actually doing
anything" signal.

## Scope

- **In:**
  - Add a small counter object (process-scoped, threadsafe) to the LLM runtime layer — either at the `LLMRuntime` Protocol level via a wrapper or in each concrete runtime, whichever keeps the implementation under ~50 lines.
  - Increment counters at the appropriate call sites: load (`model_loads`), each `classify` invocation (`classify_calls`), exception raising or constrained-output failure (`classify_failures`), and re-attempt under the GBNF/regex constraint path (`constrained_retries`).
  - Surface the counter snapshot in `holdspeak doctor` under a new sub-check (or extend the existing "LLM runtime" check from `DIR-DOC-001`).
  - Unit tests for the counter object (increment, snapshot semantics).
  - Integration test asserting that one classify call increments `classify_calls` by 1.
- **Out:**
  - Persistence of counters across restarts.
  - HTTP/web endpoint for counters — explicitly deferred to the web flagship runtime phase (per phase decisions).
  - Per-stage timing histograms — DIR-O-001 territory, separate concern.

## Acceptance criteria

- [x] Module-level `get_counters()` returns `{model_loads, classify_calls, classify_failures, constrained_retries}` as ints (`holdspeak/plugins/dictation/runtime_counters.py`).
- [x] `holdspeak doctor` prints the counter snapshot under "LLM runtime counters" check (PASS-only — observability, not health).
- [x] 9 unit tests for the counter module + wrapper pass: initial-zero snapshot, first-load advances `model_loads` (subsequent loads do not), classify advances calls, failure advances failures + re-raises, `note_constrained_retry`, `reset_counters`, attribute delegation, info delegation, build_runtime end-to-end wraps with CountingRuntime.
- [x] An integration-style test (`test_build_runtime_wraps_with_counting_and_classify_advances`) forces one classify call through `build_runtime` with stub factories and asserts `classify_calls == 1` (and `model_loads == 1`).
- [x] Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py` → 999 passed, 13 skipped (delta +11 vs. HS-3-03 baseline 988: 9 counter unit + 2 doctor unit).

## Test plan

- **Unit:** `tests/unit/test_runtime_counters.py` — counter object semantics.
- **Integration:** test that one `classify` invocation through a mocked runtime advances counters.
- **Regression:** the documented full-suite command.

## Notes / open questions

- Counter storage: a module-level dict guarded by a `threading.Lock` is sufficient. No need for `multiprocessing` or `prometheus_client`.
- Doctor surface: keep it terse — one line per counter, in the existing DIR-01 doctor section.
