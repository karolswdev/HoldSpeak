# HS-25-04 — LLM Runtime Thread-Safety Made Explicit

- **Project:** holdspeak
- **Phase:** 25
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-25-07
- **Owner:** unassigned

## Problem

The dictation LLM runtimes (`runtime_mlx.py`, `runtime_llama_cpp.py`) are not
thread-safe — MLX has global device state and a llama.cpp context can be
corrupted by concurrent decoding. Today the only thing preventing concurrent
`classify`/`rewrite` calls is `controller._transcription_lock`
(`controller.py:88`, used at `:160`), an *undocumented* invariant living in a
different module. If that serialization ever changes (e.g. a second audio
source, or the Phase 26 web refactor), the runtimes can crash silently.

## Scope

### In

- Confirm the actual contention surface: enumerate every caller of
  `runtime.classify` / `runtime.rewrite` and whether they share the controller
  lock.
- Make the single-flight contract explicit at the runtime layer — either an
  internal mutex around inference in the runtime classes, or a documented,
  asserted single-flight guarantee if the controller genuinely owns it for all
  call paths.
- Document the chosen contract in the runtime modules so the Phase 26 refactor
  and future audio sources can't break it unknowingly.

### Out

- Making inference genuinely *parallel* (not a goal; serialization is fine).
- Changing the transcription `_transcription_lock` semantics (HS-25-05 touches
  transcription, not the LLM runtimes).

## Acceptance criteria

- [x] `tests/unit/test_runtime_counters_concurrency.py` spawns 8 concurrent
      `classify` (and mixed `classify`/`rewrite`) calls through one
      `CountingRuntime` and asserts the inner runtime sees `max_in_flight == 1`.
- [x] Concurrency contract documented: `CountingRuntime` docstring + the `_serialized`
      decorator, and a "NOT thread-safe → reached only via CountingRuntime" note
      on `MlxRuntime` and `LlamaCppRuntime`.
- [x] A mutex was added at the `CountingRuntime` chokepoint (the wrapper
      `build_runtime` always applies). Single-thread cost is one uncontended
      `RLock` acquire per call (negligible); existing counters/dictation tests
      pass unchanged.
- [x] Controller's prior implicit reliance annotated (`controller.py` —
      transcription lock noted as defense-in-depth, no longer the sole guarantee).

## Test plan

- Unit: `uv run pytest -q tests/ -k "runtime and (concurren or thread or lock)"`
  — drive concurrent calls with threads against a fake runtime that detects
  re-entrancy.
- Integration: `uv run pytest -q tests/ -k dictation` stays green.
- Manual: n/a (covered by tests + HS-25-07 dogfood).

## Notes / open questions

- Prefer the lightest correct option. If the controller already serializes every
  real call path, a documented assertion + test may beat adding a second lock —
  decide from the enumerated contention surface, not by default.
- Watch for deadlock if both the controller lock and a runtime lock are held.

## Closeout

Shipped 2026-05-31. See [evidence-story-04.md](./evidence-story-04.md).

Contention surface enumerated: production `classify`/`rewrite` callers are
`intent_router.py` + `project_rewriter.py`, both flowing through `CountingRuntime`
(which `build_runtime` always wraps), driven from the controller's transcription
thread. Rather than rely on the controller lock (an external, implicit guarantee
that a future caller — dry-run, a second audio source — could bypass), the lock
was placed at the `CountingRuntime` chokepoint so single-flight is intrinsic to
the runtime. Lock ordering is safe: the per-instance call lock is always outer,
the module-level counter `_LOCK` inner; nothing acquires them in reverse.
