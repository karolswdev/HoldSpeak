# HS-91-03 — Arrival and configuration in React

- **Project:** holdspeak
- **Phase:** 91
- **Status:** done
- **Depends on:** HS-91-01, HS-91-02
- **Unblocks:** HS-91-09
- **Owner:** unassigned

## Problem

Welcome, Setup, Settings, and Profiles are the product's trust and model-runtime
front door, yet they currently use separate editor markup and Alpine/imperative
state. They must become one calm React configuration experience without losing
endpoint discovery, local-model discovery, or key-handling guarantees.

## Scope

- In: React `/welcome`, `/setup`, `/settings`, `/profiles`; runtime/model
  discovery; context presets and manual values; validation/status grammar;
  settings navigation/search/save; profile CRUD; setup doctor and first
  dictation; preserved secret boundary and environment-variable guidance.
- Out: backend setup/profile semantics; storing API keys in the browser;
  redesign of the runtime-profile wire.

## Acceptance criteria

- [x] All four routes satisfy every verb/state row in the parity ledger,
      including empty, partial, unreachable and single/multiple-model results.
- [x] Discovery presents actual choices without debug-count narration; adjacent
      field/actions align through shared layout primitives.
- [x] Settings and Profiles use only Signal React controls and one validation/
      save-feedback model.
- [x] API keys never enter browser storage or response bodies; tests pin the
      existing security boundary.
- [x] Direct links, back/forward navigation, refresh and setup redirects work
      without losing state incorrectly.
- [x] Astro/Alpine/page scripts for this cohort are deleted when the cohort cuts.

## Test plan

- Unit: route reducers/hooks and validation tests.
- Integration: existing setup/profile pytest plus React/Playwright flows.
- Manual / device: first-run, returning healthy user, dead endpoint, `.43`
  single-model endpoint, local MLX/GGUF discovery, and profile edit/delete.

## Notes / open questions

The current July 10 welcome design is the baseline to preserve and refine, not
throw away during the framework change.
