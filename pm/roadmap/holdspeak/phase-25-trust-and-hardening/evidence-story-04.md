# Evidence — HS-25-04 — LLM Runtime Thread-Safety Made Explicit

- **Shipped:** 2026-05-31
- **Commit:** (pending — same commit as this evidence file)
- **Owner:** Claude (agent)

## What shipped

Inference serialization is now intrinsic to the runtime instead of relying on
the controller's transcription lock. `CountingRuntime` — which `build_runtime`
always wraps every concrete adapter in (`runtime.py:198`) — serializes `load`,
`classify`, and `rewrite` on a per-instance `RLock`, so the non-thread-safe MLX
/ llama.cpp adapters are only ever driven by one thread at a time.

## Contention surface (enumerated before changing anything)

- Production callers of `classify`/`rewrite`: `builtin/intent_router.py:159` and
  `builtin/project_rewriter.py`, both via the runtime handed to the stages by
  `assembly.py`, which is always a `CountingRuntime` (`build_runtime`).
- Driven from the controller's transcription thread under `_transcription_lock`
  — so no *live* bug today, but the guarantee was implicit and external, and a
  future caller (dry-run, a second audio source) could bypass it.

## Files touched

- `holdspeak/plugins/dictation/runtime_counters.py` — `_serialized` decorator +
  per-instance `self._call_lock = threading.RLock()`; `load`/`classify`/`rewrite`
  decorated; docstring documents the contract. `import functools`.
- `holdspeak/plugins/dictation/runtime_mlx.py`,
  `holdspeak/plugins/dictation/runtime_llama_cpp.py` — class docstrings note
  "NOT thread-safe; reached only through CountingRuntime."
- `holdspeak/controller.py` — annotated the transcription lock as defense in
  depth (runtime now self-serializes).
- `tests/unit/test_runtime_counters_concurrency.py` — **new**, 2 cases.

## Verification artifacts

```
$ uv run pytest -q tests/unit/test_runtime_counters_concurrency.py \
    tests/unit/test_runtime_counters.py
17 passed
  (concurrent classify: inner.max_in_flight == 1 across 8 threads;
   mixed classify+rewrite: max_in_flight == 1)

$ uv run ruff check holdspeak/plugins/dictation/runtime_counters.py \
    holdspeak/plugins/dictation/runtime_mlx.py \
    holdspeak/plugins/dictation/runtime_llama_cpp.py holdspeak/controller.py \
    tests/unit/test_runtime_counters_concurrency.py
All checks passed!

$ uv run pytest -q --ignore=tests/e2e/test_metal.py
9 failed, 1856 passed, 13 skipped
  (+2 vs the HS-25-03 baseline; the 9 are the same pre-existing failures —
   stale _built bundle + missing Safari fixture.)
```

## Acceptance criteria — re-checked

- [x] Concurrent calls serialized (`max_in_flight == 1`) — concurrency test.
- [x] Concurrency contract documented (CountingRuntime + both adapters).
- [x] Single-thread cost is one uncontended `RLock` acquire/call; existing tests
      unchanged.
- [x] Controller's prior reliance annotated.

## Deviations from plan

Lock placed at the `CountingRuntime` chokepoint (one location, always present)
rather than in each adapter — lighter and equally correct since every production
path goes through it. Lock ordering verified safe (call lock outer, counter
`_LOCK` inner; never reversed).

## Follow-ups

None.
