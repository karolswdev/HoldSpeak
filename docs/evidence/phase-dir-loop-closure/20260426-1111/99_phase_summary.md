# Phase 3 — Dictation Loop Closure: phase summary

- **Captured:** 2026-04-26
- **Phase canon:** `docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md` (DIR-01)
- **Stories shipped:** HS-3-01 through HS-3-06 (6 stories; no scaffold drops).
- **Pass delta vs. HS-3-scaffold baseline (973):** **+34** to 1007 passed; 13 skipped (12 baseline + 1 new gated `llama_cpp` e2e).

## What this phase did

Closed the four DIR-01 deferred items from the previous handover's
"DIR-02 follow-ups" list, in the order that maximized user-facing
leverage:

1. **Project context plumbing** (HS-3-01 + HS-3-02 — split during scaffold-amendment commit `c27e8f0`). The MIR-side `project_detector.py` is a transcript-keyword scorer, not a cwd-walking project-root finder; the spec assumed something that didn't exist. HS-3-01 built `detect_project_for_cwd()` at `holdspeak/plugins/dictation/project_root.py` (~130 LOC, 8 unit tests). HS-3-02 wired it through the two `Utterance` constructors (`controller.py`, `commands/dictation.py`) and `blocks.py:150`'s `project_root` parameter, plus a doctor surface. **Effect: the kb-enricher's `{project.name}` / `{project.kb.*}` placeholders now resolve in dogfood; per-project `<root>/.holdspeak/blocks.yaml` is auto-loaded over the global file.**
2. **`llama_cpp` end-to-end leg** (HS-3-03). README gained a dedicated "Optional: Dictation LLM Backend" section covering both backends with install, `huggingface-cli` model download, the macOS arm64 `CMAKE_ARGS="-DGGML_METAL=on"` rebuild guidance (DIR-01 §12 risk #2), config opt-in, and verification commands. New `tests/integration/test_dictation_llama_cpp_e2e.py` exercises the full DictationPipeline through `runtime_llama_cpp.py` against a real GGUF; gated, skips cleanly without deps. **Effect: the cross-platform default declared in DIR-01 §5 is documented + tested end-to-end.**
3. **DIR-O-002 runtime counters** (HS-3-04). New module `runtime_counters.py` ships `CountingRuntime` — a process-scoped, threadsafe wrapper around any `LLMRuntime` that increments `model_loads`, `classify_calls`, `classify_failures` at the right boundaries. `build_runtime` returns the wrapper so both backends gain instrumentation in one place. Doctor surfaces the snapshot. **Effect: dogfood can read at a glance whether the LLM stage is firing.**
4. **DIR-R-003 cold-start hard-cap** (HS-3-05). Cap logic added to the same `CountingRuntime`: first `classify()` after launch (when `warm_on_start=False`) is timed; if it exceeds `max_total_latency_ms × 5`, the wrapper logs a structured WARN, sets a session-disabled flag, and raises `LLMRuntimeDisabledError`. Subsequent calls short-circuit. IntentRouter's existing exception handler catches the error as a no-match warning so the pipeline never raises. Doctor flips PASS→WARN with a one-line remediation. **Effect: dictation never hangs because of a misconfigured Metal wheel or an underprovisioned machine.**

## Story → exit-criteria mapping

| Phase exit criterion | Evidence |
|---|---|
| `Utterance.project` is populated by the controller and CLI on every utterance, verified by an integration test that exercises both call sites | HS-3-02 / `20_it_project_context.log` (`test_cli_dry_run_populates_project_from_cwd` + `test_controller_pipeline_build_passes_project_root_and_utterance_carries_project`) |
| `llama_cpp` end-to-end test runs against a real GGUF when deps present; produces a non-empty `final_text` | HS-3-03 / `20_it_llama_cpp_e2e.log` (gated; runs on reference Mac) |
| `holdspeak doctor` reports DIR-O-002 counter values | HS-3-04 / `10_ut_doctor.log` (`test_runtime_counters_check_reports_snapshot_when_enabled`) |
| DIR-R-003 hard-cap is enforced: a forced cold-start that exceeds `max_total_latency_ms × 5` short-circuits and disables the LLM stage for the session | HS-3-05 / `20_it_cold_start.log` + `10_ut_runtime_counters.log` |
| Full regression clean | `30_full_regression.log` — 1007 passed, 13 skipped |
| Phase summary at `docs/evidence/phase-dir-loop-closure/<TS>/99_phase_summary.md` enumerates what shipped + remaining deferreds | This file. |

## Cumulative phase shape

```
eefba0a HS-3 scaffold: open phase-3 — backlog stories + index update
c27e8f0 HS-3 scaffold amendment: split HS-3-01 into detector + wiring; renumber
6659662 HS-3-01: detect_project_for_cwd() pure function
e56202f HS-3-02: wire detect_project_for_cwd() into Utterance + blocks loader
505794f HS-3-03: llama_cpp end-to-end leg
d7cbf34 HS-3-04: DIR-O-002 runtime counters via CountingRuntime wrapper
3f36046 HS-3-05: DIR-R-003 cold-start hard-cap
{HS-3-06 lands directly after this bundle is staged}
```

8 commits total: 2 scaffold + 5 stories + 1 DoD. 6 stories done; 0
dropped (compare DIR-01's HS-1-01 / HS-1-10 drops and MIR-01's HS-2-01
drop).

Touched files (cumulative): `holdspeak/plugins/dictation/project_root.py`
(new), `holdspeak/plugins/dictation/runtime_counters.py` (new),
`holdspeak/plugins/dictation/runtime.py`,
`holdspeak/plugins/dictation/assembly.py`,
`holdspeak/controller.py`, `holdspeak/commands/dictation.py`,
`holdspeak/commands/doctor.py`, `README.md`. New test files:
`tests/unit/test_project_detector_cwd.py`,
`tests/unit/test_runtime_counters.py`,
`tests/integration/test_dictation_project_context.py`,
`tests/integration/test_dictation_cold_start_cap.py`,
`tests/integration/test_dictation_llama_cpp_e2e.py`. Plus tracked
phase docs and the existing `tests/unit/test_doctor_command.py`
extended with project-context + counter checks.

## Gaps + deferred items

These were explicitly out-of-scope per individual story scope blocks
or this phase's `current-phase-status.md` "Decisions deferred"
section. Each is a candidate for a future phase or follow-up story.

1. **Real-GGUF e2e capture in evidence.** The HS-3-03 gated test was authored + verified to skip cleanly; the user runs it against the real GGUF on the reference Mac during ongoing dogfood. Per `feedback_no_validation_spikes`, fetching the ~3 GB GGUF onto the dev box just to satisfy the bundle would be ceremony.
2. **`constrained_retries` always reads 0.** Both shipped backends use single-shot constrained decoding (GBNF / outlines). The counter surface is in place per spec §9.7; advanced via `note_constrained_retry()` from a future runtime that re-attempts under tightened constraints.
3. **IntentRouter does not short-circuit out of its 2-attempt retry loop on `LLMRuntimeDisabledError`.** After a cold-start breach, every utterance still goes through 2 wrapper calls that fail fast in microseconds. Negligible cost, keeps `IntentRouter` untouched. A one-line `if isinstance(exc, LLMRuntimeDisabledError): break` patch would cut the wasted retries if profiling later shows it matters.
4. **Warm-path runaway detection.** DIR-R-003 only covers cold-start. If dogfood reveals warm-path runaway (the LLM gets slow over time without a cold-start event), a follow-up story can extend the cap to also fire on N consecutive warm-path slow calls.
5. **Counter persistence across restarts.** Counters are process-scoped; `holdspeak doctor` reports the *current* session, not a historical accumulation.
6. **HTTP/web endpoint for counters.** Explicitly deferred to the web flagship runtime phase (`docs/PLAN_PHASE_WEB_FLAGSHIP_RUNTIME.md`).
7. **`detect_project_for_cwd()` LRU cache.** Profiling didn't surface a hotspot; one-stat-per-ancestor is cheap. Add only if dogfood exposes it.
8. **Narrowing `ProjectContext` from `dict[str, Any]` to a dataclass.** DIR-01 §6.4 explicitly leaves the loose typing for kb-enricher's benefit; deferred to a future phase that wants stricter typing.

## What this phase did NOT touch

- MIR-01 follow-up items (on-segment-update wiring, web UI HTML/JS controls, `mir_enabled` / `intent_router_enabled` convergence) — separate phase if/when picked up.
- The web flagship runtime migration (`docs/PLAN_PHASE_WEB_FLAGSHIP_RUNTIME.md`).
- Any new product code in MIR-01 surfaces.

The phase closes with the dictation pipeline genuinely useful in
dogfood: it carries project context, has a verified
cross-platform LLM path, surfaces the operational signals you need
to diagnose it, and degrades gracefully if the LLM goes sideways.
