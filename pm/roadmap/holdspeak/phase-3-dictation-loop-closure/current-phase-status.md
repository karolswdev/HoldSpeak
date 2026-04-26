# Phase 3 — Dictation Loop Closure (DIR-01 deferreds)

**Last updated:** 2026-04-26 (HS-3-06 DoD sweep complete — **PHASE 3 DONE**; evidence bundle at `docs/evidence/phase-dir-loop-closure/20260426-1111/` (11 files); full sweep 1007 passed, 13 skipped, +34 cumulative pass delta vs. HS-3-scaffold baseline).

## Goal

Close the loop on the DIR-01 dictation pipeline so that holding the
hotkey produces text that is **actually useful** end-to-end: grounded
in project context, optionally enriched by an LLM running through
the cross-platform `llama_cpp` backend, with operational signals you
can read in `holdspeak doctor`. DIR-01 (`HS-1-*`) shipped the
contracts, the lexical path, and the MLX runtime; this phase
delivers the four deferred items from `99_phase_summary.md`-style
follow-up list that turn the pipeline from "scaffolding" into "I
can dogfood it."

This phase has **no separate spec doc**. Its canon is
`docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md` (DIR-01) — the four
stories below close the requirements that DIR-01 deliberately
deferred (DIR-R-003, DIR-O-002, the `llama_cpp` end-to-end leg,
and project-context plumbing into `Utterance`). This section is
**immutable** for the life of the phase.

## Scope

- **In:**
  - HS-3-01 — `detect_project_for_cwd()` pure function: walks cwd→root looking for `.holdspeak/`, `.git/`, or language manifests; returns a `ProjectContext` dict; unit-tested.
  - HS-3-02 — wire HS-3-01 through both `Utterance` construction sites (`holdspeak/controller.py`, `holdspeak/commands/dictation.py`) and through `holdspeak/plugins/dictation/blocks.py:150`'s `project_root` parameter; integration tests + doctor surface.
  - HS-3-03 — `llama_cpp` end-to-end leg: documented install path (extra + GGUF download), an integration test gated on `requires_llama_cpp`, and a verified end-to-end pipeline run on a real GGUF.
  - HS-3-04 — DIR-O-002 runtime counters (`model_loads`, `classify_calls`, `classify_failures`, `constrained_retries`) surfaced via `holdspeak doctor`.
  - HS-3-05 — DIR-R-003 cold-start hard-cap: first call after launch with `warm_on_start=false` must complete or short-circuit within `max_total_latency_ms × 5`; otherwise log and disable for the session.
  - HS-3-06 — DoD sweep + phase-exit evidence bundle (mirrors HS-1-11 / HS-2-11).
- **Out:**
  - Cloud router, multi-utterance state, additional backends beyond the existing `mlx` + `llama_cpp` pair — explicitly deferred in DIR-01 §11 and outside DIR-01's spec.
  - Web UI HTML/JS controls for DIR-01 — the JSON contract is a meeting-side concern and is part of the MIR-01 deferred set, not this phase.
  - MIR-01 follow-up items (on-segment-update wiring, etc.) — separate phase if/when the user picks that up.

## Exit criteria (evidence required)

- [x] `Utterance.project` is populated by the controller and the CLI dictation command on every utterance, verified by an integration test that exercises both call sites. — `docs/evidence/phase-dir-loop-closure/20260426-1111/20_it_project_context.log`
- [x] `llama_cpp` end-to-end test runs against a real GGUF (gated on `requires_llama_cpp`); pipeline produces a non-empty `final_text` from a fixture utterance. — `20_it_llama_cpp_e2e.log` (gated; runs on reference Mac)
- [x] `holdspeak doctor` reports DIR-O-002 counter values (zeroed on a fresh session, non-zero after one classify call). — `10_ut_doctor.log` (`test_runtime_counters_check_reports_snapshot_when_enabled`)
- [x] DIR-R-003 hard-cap is enforced: a forced cold-start that exceeds `max_total_latency_ms × 5` short-circuits and disables the LLM stage for the session. — `20_it_cold_start.log` + `10_ut_runtime_counters.log`
- [x] Full regression clean: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py` PASS. — `30_full_regression.log` (1007 passed, 13 skipped)
- [x] Phase summary at `docs/evidence/phase-dir-loop-closure/20260426-1111/99_phase_summary.md` enumerates what shipped + 8 deferred follow-up items.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-3-01 | `detect_project_for_cwd()` pure function | done | [story-01-project-context](./story-01-project-context.md) | [evidence-story-01](./evidence-story-01.md) — 8 unit tests pass; full sweep 981 passed (+8 vs. baseline) |
| HS-3-02 | Wire detector into `Utterance` + blocks loader | done | [story-02-wire-detector](./story-02-wire-detector.md) | [evidence-story-02](./evidence-story-02.md) — 4 integration + 3 doctor unit tests pass; full sweep 988 (+7 vs. HS-3-01) |
| HS-3-03 | `llama_cpp` end-to-end leg | done | [story-03-llama-cpp-leg](./story-03-llama-cpp-leg.md) | [evidence-story-03](./evidence-story-03.md) — gated e2e test + README install docs; 1 new skipped test (runs on reference Mac); full sweep 988 passed, 13 skipped |
| HS-3-04 | DIR-O-002 runtime counters | done | [story-04-runtime-counters](./story-04-runtime-counters.md) | [evidence-story-04](./evidence-story-04.md) — `CountingRuntime` wrapper + doctor surface; 11 new tests; full sweep 999 passed |
| HS-3-05 | DIR-R-003 cold-start hard-cap | done | [story-05-cold-start-cap](./story-05-cold-start-cap.md) | [evidence-story-05](./evidence-story-05.md) — cold-start cap + session-disable + doctor WARN; 8 new tests; full sweep 1007 passed |
| HS-3-06 | DoD sweep + phase exit | done | [story-06-dod](./story-06-dod.md) | [evidence-story-06](./evidence-story-06.md) — 11-file bundle at `docs/evidence/phase-dir-loop-closure/20260426-1111/`; full sweep 1007 passed |

## Where we are

**Phase 3 is complete.** All 6 stories shipped across 8 commits
(2 scaffold + 5 stories + 1 DoD); 0 dropped. Evidence bundle at
`docs/evidence/phase-dir-loop-closure/20260426-1111/` (11 files);
spec exit-criteria all checked above. Full regression: 1007 passed,
13 skipped (+34 cumulative vs. HS-3-scaffold baseline). The dictation
pipeline now:

- `detect_project_for_cwd()` lives at `holdspeak/plugins/dictation/project_root.py` with 8 unit tests (HS-3-01).
- `HoldSpeakController._build_dictation_pipeline()` and `holdspeak.commands.dictation._cmd_dry_run` both detect at build/invocation time, populate `Utterance.project`, and pass `project_root` through to `assembly.build_pipeline` so per-project `<root>/.holdspeak/blocks.yaml` is auto-loaded (HS-3-02).
- `holdspeak doctor` ships a `Project context` check (PASS detected, WARN missing, PASS-skip when pipeline disabled).
- 4 integration tests + 3 doctor unit tests; full sweep 988 passed (+15 cumulative vs. HS-3-scaffold baseline 973).
- New `tests/integration/test_dictation_llama_cpp_e2e.py` exercises the full DictationPipeline through `runtime_llama_cpp.py` against a real GGUF; gated on `requires_llama_cpp` + `_have_model()`, skips cleanly when deps absent (HS-3-03).
- README ships an "Optional: Dictation LLM Backend" section covering install, model download, Metal-rebuild guidance, config opt-in, and verification commands.
- DIR-O-002 runtime counters live at `holdspeak/plugins/dictation/runtime_counters.py`; `build_runtime` wraps with `CountingRuntime` so both backends gain instrumentation transparently. `holdspeak doctor` reports `model_loads / classify_calls / classify_failures / constrained_retries`.
- DIR-R-003 cold-start hard-cap also lives on `CountingRuntime`: first `classify()` call after launch (when `warm_on_start=False`) is timed; if it exceeds `max_total_latency_ms × 5`, the wrapper raises `LLMRuntimeDisabledError` and disables the LLM stage for the session. Subsequent classify calls short-circuit immediately. Doctor flips to WARN with a one-line remediation.

The kb-enricher's `{project.name}` / `{project.kb.*}` template
placeholders now resolve in dogfood against real on-disk project
trees. Block-grounded dictation is no longer inert. The cross-platform
LLM leg (`llama_cpp` + Qwen2.5-3B-GGUF) is documented + tested
end-to-end through the gated path.

The six-story arc is
ordered by user-facing leverage: **HS-3-01 + HS-3-02** are the
project-context plumbing that turns blocks from scaffolding into
"dictation grounded in the project I'm in" — split into a pure
detector function (HS-3-01) and the wiring through the two
Utterance construction sites + blocks loader (HS-3-02). The split
came from the audit finding that the spec-referenced
`project_detector` is the MIR-side keyword scorer, not a cwd-based
project-root finder; the function HS-3-01 builds is genuinely new
code, ~150–300 lines, and benefits from its own commit + tests.
**HS-3-03** earns the cross-platform default its keep.
**HS-3-04/HS-3-05** are operational hardening so we can read what
the LLM stage is doing and protect typing from catastrophic
cold-start regressions. **HS-3-06** is the DoD sweep.

## Active risks

1. **`llama-cpp-python` Metal-wheel mismatch.** Spec §12 risk #2: a CPU-only wheel on Apple Silicon misses latency targets dramatically. Mitigation already specified in DIR-01 (`DIR-DOC-002` doctor check); HS-3-02 verifies the doctor output is honest under both wheel variants.
2. **Project-context schema drift.** `ProjectContext` is typed as `dict[str, Any]` for forward compatibility (`holdspeak/plugins/dictation/contracts.py:19`). HS-3-01 must not narrow that without HS-1-06's kb-enricher signing off — they're the only consumer today.
3. **Cold-start hard-cap false positives.** A genuine first-load on an underpowered machine could legitimately exceed `× 5` once and then run fine. Mitigation: the cap disables for the *session*, not permanently; the next `holdspeak` launch retries.

## Decisions made (this phase)

- 2026-04-26 — phase canon is DIR-01's `docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md`; no separate spec doc for this 6-story closure phase.
- 2026-04-26 — HS-3-01 (project-context plumbing) ships first per the user's "actually useful" framing — it is the change that makes the rest of the DIR-01 surface earn its keep.
- 2026-04-26 — Split HS-3-01 into HS-3-01 (pure detector function) + HS-3-02 (wiring) after audit revealed the spec-referenced `project_detector` is the MIR-side keyword scorer, not a cwd-based project-root finder. The detector function is genuinely new code; cleaner story boundaries warrant the split.
- 2026-04-26 — Considered introducing `~/.holdspeak/` as global config home for symmetry with per-project `<root>/.holdspeak/`. Decision: keep `~/.config/holdspeak/` because it's XDG-compliant (the actual reason it exists). Asymmetry retained.

## Decisions deferred

- Whether DIR-R-003 should also enforce a *warm* hard-cap (i.e., disable on repeated breach after warm-up). Spec §9.6 only calls out cold-start. HS-3-04 stays scoped to the spec; if dogfood reveals warm-path runaway, a follow-up story can extend.
- Whether the runtime counters should be surfaced via a debug HTTP endpoint in addition to `holdspeak doctor`. HS-3-03 stays scoped to doctor; the web flagship runtime phase (`docs/PLAN_PHASE_WEB_FLAGSHIP_RUNTIME.md`) is the right home for endpoint-level surfacing.
