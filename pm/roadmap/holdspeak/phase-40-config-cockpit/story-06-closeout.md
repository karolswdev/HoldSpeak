# HS-40-06 — Closeout

- **Project:** holdspeak
- **Phase:** 40
- **Status:** done (2026-06-05)
- **Depends on:** HS-40-01, HS-40-02, HS-40-03, HS-40-04, HS-40-05
- **Unblocks:** none
- **Owner:** unassigned
- **Evidence:** [evidence-story-06.md](./evidence-story-06.md)

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

- [x] An end-to-end UI-only setup is captured (configure → use → correct →
      restart → correction persisted) — `evidence/dogfood_post_restart.png` +
      the transcript in [evidence-story-06](./evidence-story-06.md).
- [x] Demo screenshots committed (cockpit / memory / telemetry / post-restart).
- [x] Full suite green at close — **2221 passed, 16 skipped**; off-by-default
      byte-identity re-asserted (25 routing/no-repo tests); no `_built/` tracked.
- [x] `final-summary.md` exists (goal-met, exit criteria, stories, metrics,
      lessons, Phase-41 handoff).
- [x] `current-phase-status.md` frozen; README phase row → done + pointer
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
