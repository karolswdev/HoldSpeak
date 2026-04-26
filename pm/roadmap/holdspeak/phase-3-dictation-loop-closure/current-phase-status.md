# Phase 3 — Dictation Loop Closure (DIR-01 deferreds)

**Last updated:** 2026-04-26 (HS-3 scaffold — phase opened with 5 backlog stories; no story shipped yet).

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
  - HS-3-01 — wire `holdspeak/plugins/project_detector.py` output into the dictation `Utterance.project` field at every construction site (`holdspeak/controller.py`, `holdspeak/commands/dictation.py`); kb-enricher (HS-1-06) already reads off it.
  - HS-3-02 — `llama_cpp` end-to-end leg: documented install path (extra + GGUF download), an integration test gated on `requires_llama_cpp`, and a verified end-to-end pipeline run on a real GGUF.
  - HS-3-03 — DIR-O-002 runtime counters (`model_loads`, `classify_calls`, `classify_failures`, `constrained_retries`) surfaced via `holdspeak doctor`.
  - HS-3-04 — DIR-R-003 cold-start hard-cap: first call after launch with `warm_on_start=false` must complete or short-circuit within `max_total_latency_ms × 5`; otherwise log and disable for the session.
  - HS-3-05 — DoD sweep + phase-exit evidence bundle (mirrors HS-1-11 / HS-2-11).
- **Out:**
  - Cloud router, multi-utterance state, additional backends beyond the existing `mlx` + `llama_cpp` pair — explicitly deferred in DIR-01 §11 and outside DIR-01's spec.
  - Web UI HTML/JS controls for DIR-01 — the JSON contract is a meeting-side concern and is part of the MIR-01 deferred set, not this phase.
  - MIR-01 follow-up items (on-segment-update wiring, etc.) — separate phase if/when the user picks that up.

## Exit criteria (evidence required)

- [ ] `Utterance.project` is populated by the controller and the CLI dictation command on every utterance, verified by an integration test that exercises both call sites.
- [ ] `llama_cpp` end-to-end test runs against a real GGUF (gated on `requires_llama_cpp`); pipeline produces a non-empty `final_text` from a fixture utterance.
- [ ] `holdspeak doctor` reports DIR-O-002 counter values (zeroed on a fresh session, non-zero after one classify call).
- [ ] DIR-R-003 hard-cap is enforced: a forced cold-start that exceeds `max_total_latency_ms × 5` short-circuits and disables the LLM stage for the session.
- [ ] Full regression clean: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py` PASS.
- [ ] Phase summary at `docs/evidence/phase-dir-loop-closure/<YYYYMMDD-HHMM>/99_phase_summary.md` enumerates what shipped + any remaining deferreds.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-3-01 | Project-context plumbing into `Utterance` | backlog | [story-01-project-context](./story-01-project-context.md) | — |
| HS-3-02 | `llama_cpp` end-to-end leg | backlog | [story-02-llama-cpp-leg](./story-02-llama-cpp-leg.md) | — |
| HS-3-03 | DIR-O-002 runtime counters | backlog | [story-03-runtime-counters](./story-03-runtime-counters.md) | — |
| HS-3-04 | DIR-R-003 cold-start hard-cap | backlog | [story-04-cold-start-cap](./story-04-cold-start-cap.md) | — |
| HS-3-05 | DoD sweep + phase exit | backlog | [story-05-dod](./story-05-dod.md) | — |

## Where we are

Phase opened. No stories shipped yet. The five-story arc is
ordered by user-facing leverage: **HS-3-01** is the change that
turns blocks from scaffolding into "dictation grounded in the
project I'm in" — it's the highest-leverage item in the phase
and ships first. **HS-3-02** earns the cross-platform default
its keep. **HS-3-03/HS-3-04** are operational hardening so we
can read what the LLM stage is doing and protect typing from
catastrophic cold-start regressions. **HS-3-05** is the DoD
sweep.

## Active risks

1. **`llama-cpp-python` Metal-wheel mismatch.** Spec §12 risk #2: a CPU-only wheel on Apple Silicon misses latency targets dramatically. Mitigation already specified in DIR-01 (`DIR-DOC-002` doctor check); HS-3-02 verifies the doctor output is honest under both wheel variants.
2. **Project-context schema drift.** `ProjectContext` is typed as `dict[str, Any]` for forward compatibility (`holdspeak/plugins/dictation/contracts.py:19`). HS-3-01 must not narrow that without HS-1-06's kb-enricher signing off — they're the only consumer today.
3. **Cold-start hard-cap false positives.** A genuine first-load on an underpowered machine could legitimately exceed `× 5` once and then run fine. Mitigation: the cap disables for the *session*, not permanently; the next `holdspeak` launch retries.

## Decisions made (this phase)

- 2026-04-26 — phase canon is DIR-01's `docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md`; no separate spec doc for this 5-story closure phase.
- 2026-04-26 — HS-3-01 (project-context plumbing) ships first per the user's "actually useful" framing — it is the change that makes the rest of the DIR-01 surface earn its keep.

## Decisions deferred

- Whether DIR-R-003 should also enforce a *warm* hard-cap (i.e., disable on repeated breach after warm-up). Spec §9.6 only calls out cold-start. HS-3-04 stays scoped to the spec; if dogfood reveals warm-path runaway, a follow-up story can extend.
- Whether the runtime counters should be surfaced via a debug HTTP endpoint in addition to `holdspeak doctor`. HS-3-03 stays scoped to doctor; the web flagship runtime phase (`docs/PLAN_PHASE_WEB_FLAGSHIP_RUNTIME.md`) is the right home for endpoint-level surfacing.
