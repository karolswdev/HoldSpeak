# Phase 32 — Foundation Hardening & Doc Truth

**Status:** in-progress (opened 2026-06-02). 0/6 stories shipped.

**Last updated:** 2026-06-02 (phase opened; runs after Phase 31; HS-32-01 next).

## Goal

Close the structural, verification, and doc-integrity gaps surfaced by the
2026-06-02 engineering review — the items that are each too small for their own
phase but together decide whether the foundation stays workable. Two runtime
refactors (class-ify `web_runtime.py`; invert the meeting→web-server coupling),
one correctness consolidation (a single audio-ownership model), one trust gap
(a CI end-to-end smoke test for the core hotkey→text path that today only runs
behind never-in-CI markers), one cleanup (a route error-handling helper), and
one honesty fix (reconcile non-PMO docs that assert false current state).

## Scope

### In

- Convert `run_web_runtime()` (1,702 lines, 9+ `nonlocal` vars) into a `WebRuntime`
  class with instance state and lifecycle methods, matching `controller.py`.
- Invert `meeting_session.py:1552`'s `self._web_server.broadcast(...)` to an
  emit/callback the runtime observes — `MeetingSession` stops importing/knowing
  the web server.
- Converge the three audio-ownership paths (hotkey / device / meeting) on the
  `VoiceTypingSession` single-owner contract so there is one ownership model.
- Add a CI-runnable end-to-end smoke test of the core path (synthesized WAV → a
  tiny/real-but-small Whisper → injection seam), asserting on actual output text,
  not "didn't throw."
- Extract one route error-handling helper (decorator/middleware) and apply it to
  the duplicated `except → log → JSONResponse(500)` blocks in `activity.py` /
  `dictation.py` (and siblings).
- Reconcile non-PMO docs with reality: **delete** dead `PLAN_*.md` docs/sections
  (non-existent branches, shipped-differently features), fix `HANDOVER.md` + README
  positioning; add a lightweight guard so the worst drift (stub counts) can't rot again.

**Posture: greenfield/aggressive** — one user (the author), destructive changes
fine. The refactors (HS-32-01/02) preserve behavior because that's what a refactor
*is*, not out of compat duty; but HS-32-03 may change meeting-capture behavior to
reach the clean single model, and HS-32-06 **deletes** dead docs rather than
archiving them.

### Out

- New endpoints, payload changes, or product features.
- The PMO roadmap corpus itself — the historical record stays as-is by design;
  this phase touches **non-PMO** project docs only (`docs/`, `HANDOVER.md`, README).
- The `db.py` work (that is Phase 31) and async DB offload (settled in Phase 26).
- Building or killing the menubar/intel-streaming *features* — HS-32-06 fixes/deletes
  their stale *docs*, it does not change the code those docs describe.

## Exit criteria (evidence required)

- [ ] `web_runtime.py`'s orchestration is a `WebRuntime` class (no module-level
      `nonlocal`-threaded god-function); behavior unchanged, web suite green.
- [ ] `MeetingSession` no longer references a web server; it emits, the runtime
      observes — proven by a test constructing a `MeetingSession` with no web
      server and exercising broadcast-triggering paths.
- [ ] One audio-ownership model: hotkey / device / meeting all acquire through the
      `VoiceTypingSession` owner contract; a concurrency test shows mutual exclusion.
- [ ] A CI job runs the core hotkey→text smoke test on every push and asserts on
      the produced text; it is **not** gated behind `metal`/`spoken_e2e`.
- [ ] The route error-handling duplication is removed via a single helper, with a
      before/after handler count recorded.
- [ ] `HANDOVER.md`, the `PLAN_*.md` status headers, and README positioning state
      only true things; the stub-count guard is committed.
- [ ] `uv run pytest -q --ignore=tests/e2e/test_metal.py` green throughout.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-32-01 | Class-ify `web_runtime.py` (`WebRuntime`) | not-started | [story-01-web-runtime-classify.md](./story-01-web-runtime-classify.md) | — |
| HS-32-02 | Invert meeting→web-server coupling | not-started | [story-02-meeting-web-inversion.md](./story-02-meeting-web-inversion.md) | — |
| HS-32-03 | Converge audio ownership | not-started | [story-03-audio-ownership.md](./story-03-audio-ownership.md) | — |
| HS-32-04 | CI end-to-end smoke test (core path) | not-started | [story-04-ci-e2e-smoke.md](./story-04-ci-e2e-smoke.md) | — |
| HS-32-05 | Route error-handling helper | not-started | [story-05-route-error-helper.md](./story-05-route-error-helper.md) | — |
| HS-32-06 | Stale non-PMO doc sweep + drift guard | not-started | [story-06-doc-truth-sweep.md](./story-06-doc-truth-sweep.md) | — |

## Where we are

Opened 2026-06-02 alongside Phase 31, sequenced after it. The review found the
TUI runtime (`controller.py`) is clean and the web runtime is its messy twin;
Phase 26 decomposed `web_server.py` but left `web_runtime.py` and the meeting→web
inversion standing. This phase finishes that and closes the test-trust and
doc-truth gaps in the same pass.

## Pickup order

1. HS-32-01 — class-ify the runtime first; it is the substrate the inversion and
   audio-ownership stories build on.
2. HS-32-02 — invert meeting→web once `WebRuntime` can hold the observer.
3. HS-32-03 — converge audio ownership.
4. HS-32-04 — the CI smoke test (independent; can land any time but most valuable early).
5. HS-32-05 — the error helper (mechanical, low risk).
6. HS-32-06 — doc-truth sweep + guard; last so the docs describe the post-phase reality.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Class-ifying the runtime changes startup/shutdown ordering | Medium | Move state to instance attrs verbatim; preserve call order; web suite as gate | A lifecycle/web test fails or ordering visibly changes |
| The meeting→web inversion drops a broadcast that tests didn't cover | Medium | Add the headless-`MeetingSession` test *first*, then invert under it | A broadcast that fired before no longer fires |
| Audio-ownership convergence breaks a real capture path (meeting bypass exists for a reason) | Medium | Understand why meeting bypasses `VoiceTypingSession` before redesigning; the single model may *change* meeting capture, but every real path must still acquire | A real-audio path can no longer acquire the recorder at all |
| The CI smoke test is flaky (model size, runner speed) | Medium | Use the smallest viable model + a fixed synthesized WAV + generous tolerance on text match; assert substring, not exact | The job fails intermittently on unchanged code |

## Decisions made (this phase)

- 2026-06-02 — Doc-truth fix lives as a tracked story (HS-32-06), not an untracked
  cleanup commit — keep the change evidenced like everything else — user.
- 2026-06-02 — Scope is non-PMO docs only; the PMO historical record is kept
  verbatim by design — user.

## Decisions deferred

- Which Whisper model the CI smoke test uses (tiny vs. a checked-in fixture) —
  trigger: HS-32-04 — default: smallest model that reliably transcribes a fixed
  short phrase; substring assertion with tolerance.
- Whether the error helper is a decorator or FastAPI exception handler — trigger:
  HS-32-05 — default: a decorator, so per-route opt-in stays explicit.
