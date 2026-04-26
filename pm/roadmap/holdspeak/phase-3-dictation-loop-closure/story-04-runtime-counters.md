# HS-3-04 — DIR-O-002 runtime counters

- **Project:** holdspeak
- **Phase:** 3
- **Status:** backlog
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

- [ ] LLM runtime exposes a `counters()` snapshot returning `{model_loads, classify_calls, classify_failures, constrained_retries}` as ints.
- [ ] `holdspeak doctor` prints the counter snapshot when an LLM backend is configured.
- [ ] Unit tests for the counter object pass.
- [ ] An integration test forcing one classify call asserts `classify_calls` increments by 1.
- [ ] Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py` PASS.

## Test plan

- **Unit:** `tests/unit/test_runtime_counters.py` — counter object semantics.
- **Integration:** test that one `classify` invocation through a mocked runtime advances counters.
- **Regression:** the documented full-suite command.

## Notes / open questions

- Counter storage: a module-level dict guarded by a `threading.Lock` is sufficient. No need for `multiprocessing` or `prometheus_client`.
- Doctor surface: keep it terse — one line per counter, in the existing DIR-01 doctor section.
