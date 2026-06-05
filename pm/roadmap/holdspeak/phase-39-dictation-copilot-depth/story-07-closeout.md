# HS-39-07 — Closeout + final-summary

- **Project:** holdspeak
- **Phase:** 39
- **Status:** done
- **Depends on:** HS-39-01, HS-39-02, HS-39-03, HS-39-04, HS-39-05, HS-39-06
- **Unblocks:** none
- **Owner:** unassigned

## Problem

Phase 39 closes only when its depth features are proven against a real
endpoint and the tracking docs are reconciled. The closeout runs a real
dogfood, captures a before/after on a messy dictation session, writes the
immutable `final-summary.md`, and flips the README phase row to done.

## Scope

- In:
  - **Real dogfood** of the new copilot depth against the `.43`
    OpenAI-compatible endpoint (per memory `reference_lan_llm_endpoint` /
    `project_intel_use_43_q6`): an utterance through multi-pass rewriting +
    correction memory + (optionally) the LLM target fallback, with the result
    captured.
  - **Before/after** on a representative messy session: the same input through
    the Phase-18/19 baseline (single-pass, no memory) vs Phase-39 depth, to
    show the qualitative improvement (mirrors the Phase-36 before/after
    headline pattern).
  - **Invariant re-verification:** with `dictation.pipeline.enabled=false`, the
    typing path is byte-identical to pre-Phase-39; the default suite makes no
    real LLM/network call.
  - `final-summary.md` per the roadmap-builder §2.5 template.
  - README phase row → done; "Current phase" pointer advanced; HANDOVER
    refresh.
- Out:
  - New features — closeout is verification + record only.
  - Opening Phase 40 (surface candidates in the handoff; the user picks the
    next direction).

## Acceptance criteria

- [ ] A real `.43`-endpoint dogfood run is captured under the phase
      `evidence/` (the dry-run output across the new depth path).
- [ ] A before/after artifact (baseline vs depth on the same messy input) is
      committed.
- [ ] `uv run pytest -q --ignore=tests/e2e/test_metal.py` is green at close;
      the count is recorded.
- [ ] Pipeline-disabled byte-identity is re-asserted and noted.
- [ ] `final-summary.md` exists with goal-met assessment, exit-criteria final
      state (each linked to its evidence), stories shipped, surprises/lessons,
      and a handoff to Phase 40 (candidate next directions).
- [ ] `current-phase-status.md` frozen; README phase row → done + pointer
      advanced; HANDOVER refreshed.

## Test plan

- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py` — record the
  passed/skipped counts in the final summary.
- Targeted: re-run the dictation unit + integration suites
  (`tests/unit/test_dictation_*`, `tests/integration/test_web_dictation_*`) and
  the doc-guards.
- Manual / device: the `.43` dogfood run + before/after capture (real
  endpoint; opt-in, not in CI).

## Notes / open questions

- Sandbox note (memory `reference_lan_llm_endpoint`): the LAN endpoint at
  `192.168.1.43:8080` is unreachable from sandboxed Bash — use
  `dangerouslyDisableSandbox` to probe it during the dogfood.
- Phase-40 candidates to surface (not decide): DIR-02 (new backends / cloud
  router / cross-session persistent memory), or pivot back to Release &
  Dogfood / Growth (the directions deferred when this track was chosen).
- This file is created **at close**, immutable afterward (roadmap-builder
  §2.5). Do not pre-write it.
