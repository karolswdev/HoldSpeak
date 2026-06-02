# Phase 32 — Foundation Hardening & Doc Truth

**Status:** in-progress (opened 2026-06-02; runs after Phase 31).

Phase 32 closes the remaining structural and trust gaps surfaced by the 2026-06-02
engineering review, none of which are individually phase-sized but which together
determine whether the foundation calcifies or stays workable:

1. `web_runtime.py` is a 1,702-line procedural god-function (`run_web_runtime()`
   with 9+ `nonlocal` vars) — class-ify it to match the clean `controller.py` path.
2. `meeting_session.py` reaches *up* into the web layer (`self._web_server.broadcast(...)`)
   — invert it to an emit/observer so meetings can run headless.
3. Three inconsistent audio-ownership models (hotkey / device / meeting) — converge
   on the `VoiceTypingSession` single-owner contract.
4. The core promise — *press key → speak → text appears* — is tested only behind
   `metal`/`spoken_e2e` markers that never run in CI. Add a real end-to-end smoke
   test that does.
5. ~22 identical `except Exception → log → JSONResponse(500)` blocks in `activity.py`
   alone (15+ in `dictation.py`) — extract one route error-handling helper.
6. Non-PMO project docs that claim *current* state and lie — `HANDOVER.md`'s dead
   "11 stubs" section, `PLAN_*.md` "branch feature/…" headers for branches that
   don't exist, README positioning — reconcile them with reality.

## Where to look first

- `current-phase-status.md` — goal, scope, exit criteria, story table, risks.
- `../phase-26-web-runtime-decomposition/` — the web-server half of this story;
  Phase 32 finishes the *runtime* half (`web_runtime.py`) it left standing.
- `../../../holdspeak/web_runtime.py`, `../../../holdspeak/controller.py` — the
  messy runtime vs. the clean one it should resemble.
- `../../../holdspeak/meeting_session.py` — the inversion target.

## Phase boundaries

Structural + trust hardening and doc reconciliation only — **no new product
features, no API surface changes**. Behavior is preserved except where a story
explicitly removes a wrong behavior (e.g. converging audio ownership). Runs after
Phase 31 so the persistence layer is stable before the runtime is reshaped.
