# HS-40-06 — Closeout

- **Project:** holdspeak
- **Phase:** 40
- **Status:** backlog
- **Depends on:** HS-40-01, HS-40-02, HS-40-03, HS-40-04, HS-40-05
- **Unblocks:** none
- **Owner:** unassigned

## Problem

Phase 40 closes when the cockpit + persistence are proven by real use and the
tracking docs are reconciled.

## Scope

- In:
  - **Dogfood the cockpit:** configure the copilot end-to-end from the UI (no
    file editing), enable the new knobs, record a correction, restart, and
    confirm the correction **persisted**. Capture it.
  - A demo/screenshot set: the cockpit, the memory panel (pre/post restart), the
    telemetry panel.
  - **Invariant re-verification:** the dictation pipeline behavior is unchanged
    (off-by-default still byte-identical); the web bundle is rebuilt but only
    `web/src` is committed (no `_built/` tracked).
  - `final-summary.md` (roadmap-builder §2.5); README phase row → done +
    pointer advanced; HANDOVER refresh.
  - Push + open a PR to `main`; merge when CI is green.
- Out:
  - New features — closeout is verification + record only.
  - Opening Phase 41 (surface candidates in the handoff).

## Acceptance criteria

- [ ] An end-to-end UI-only setup is captured (configure → use → correct →
      restart → correction persisted).
- [ ] Demo screenshots committed (cockpit / memory / telemetry).
- [ ] `uv run pytest -q --ignore=tests/e2e/test_metal.py` green at close; count
      recorded; off-by-default byte-identity re-asserted; no `_built/` tracked.
- [ ] `final-summary.md` exists (goal-met, exit criteria, stories, lessons,
      Phase-41 handoff).
- [ ] `current-phase-status.md` frozen; README phase row → done + pointer
      advanced; HANDOVER refreshed; PR opened (merge when CI green).

## Test plan

- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py` — record counts.
- Build: `cd web && npm run build` — bundle current.
- Manual: the dogfood walkthrough above, screenshots captured.

## Notes / open questions

- Phase-41 candidates to surface (not decide): the deferred **Release & Dogfood**
  / **Growth** directions; telemetry persistence; the consolidation UI
  (Phase-39 follow-up); cross-device memory sync.
- Per memory `feedback_merge_phases_via_pr`: push + open a PR + merge (merge
  commit) when CI is green; don't leave the branch local.
